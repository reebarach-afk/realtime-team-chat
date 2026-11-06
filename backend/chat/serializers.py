from rest_framework import serializers

from .models import Membership, Message, Room


class RoomSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    my_role = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ("id", "name", "created_at", "member_count", "my_role")
        read_only_fields = ("id", "created_at")

    def get_member_count(self, obj):
        return obj.memberships.count()

    def get_my_role(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        m = obj.memberships.filter(user=request.user).first()
        return m.role if m else None


class MessageSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Message
        fields = ("id", "user_id", "username", "content", "created_at")


class MembershipSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Membership
        fields = ("id", "user_id", "username", "role")
