from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Membership, Message, Room
from .serializers import MembershipSerializer, MessageSerializer, RoomSerializer


def get_membership(user, room_id):
    return Membership.objects.filter(user=user, room_id=room_id).first()


def not_member():
    return Response({"detail": "You are not a member of this room."}, status=403)


class RoomListCreateView(generics.ListCreateAPIView):
    serializer_class = RoomSerializer
    queryset = Room.objects.all().order_by("name")

    def perform_create(self, serializer):
        room = serializer.save(created_by=self.request.user)
        # Whoever creates a room becomes its admin.
        Membership.objects.create(
            user=self.request.user, room=room, role=Membership.ADMIN
        )


class JoinRoomView(APIView):
    def post(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)
        membership, created = Membership.objects.get_or_create(
            user=request.user, room=room
        )
        return Response(
            {"role": membership.role},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class MessageListView(APIView):
    def get(self, request, room_id):
        if not get_membership(request.user, room_id):
            return not_member()
        latest = (
            Message.objects.filter(room_id=room_id)
            .select_related("user")
            .order_by("-created_at")[:50]
        )
        return Response(MessageSerializer(reversed(list(latest)), many=True).data)


class MessageDeleteView(APIView):
    def delete(self, request, message_id):
        message = get_object_or_404(Message, id=message_id)
        membership = get_membership(request.user, message.room_id)
        if not membership:
            return not_member()
        # Admins can delete anything; members only their own messages.
        if message.user_id != request.user.id and membership.role != Membership.ADMIN:
            return Response({"detail": "You can only delete your own messages."}, status=403)

        room_id, msg_id = message.room_id, message.id
        message.delete()
        async_to_sync(get_channel_layer().group_send)(
            f"chat_{room_id}", {"type": "message.deleted", "id": msg_id}
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MemberListView(APIView):
    def get(self, request, room_id):
        if not get_membership(request.user, room_id):
            return not_member()
        members = Membership.objects.filter(room_id=room_id).select_related("user")
        return Response(MembershipSerializer(members, many=True).data)


class MemberDetailView(APIView):
    def _is_last_admin(self, target):
        return (
            target.role == Membership.ADMIN
            and Membership.objects.filter(
                room=target.room, role=Membership.ADMIN
            ).count()
            == 1
        )

    def patch(self, request, room_id, user_id):
        me = get_membership(request.user, room_id)
        if not me:
            return not_member()
        if me.role != Membership.ADMIN:
            return Response({"detail": "Only admins can change roles."}, status=403)

        target = get_object_or_404(Membership, room_id=room_id, user_id=user_id)
        role = request.data.get("role")
        if role not in (Membership.ADMIN, Membership.MEMBER):
            return Response({"detail": "Role must be 'admin' or 'member'."}, status=400)
        if role == Membership.MEMBER and self._is_last_admin(target):
            return Response({"detail": "A room needs at least one admin."}, status=400)

        target.role = role
        target.save()
        return Response(MembershipSerializer(target).data)

    def delete(self, request, room_id, user_id):
        me = get_membership(request.user, room_id)
        if not me:
            return not_member()
        # Admins can remove anyone; anyone can remove themselves (leave).
        if me.role != Membership.ADMIN and request.user.id != user_id:
            return Response({"detail": "Only admins can remove other members."}, status=403)

        target = get_object_or_404(Membership, room_id=room_id, user_id=user_id)
        if self._is_last_admin(target):
            return Response({"detail": "A room needs at least one admin."}, status=400)
        target.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
