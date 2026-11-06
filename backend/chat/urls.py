from django.urls import path

from .views import (
    JoinRoomView,
    MemberDetailView,
    MemberListView,
    MessageDeleteView,
    MessageListView,
    RoomListCreateView,
)

urlpatterns = [
    path("rooms/", RoomListCreateView.as_view()),
    path("rooms/<int:room_id>/join/", JoinRoomView.as_view()),
    path("rooms/<int:room_id>/messages/", MessageListView.as_view()),
    path("rooms/<int:room_id>/members/", MemberListView.as_view()),
    path("rooms/<int:room_id>/members/<int:user_id>/", MemberDetailView.as_view()),
    path("messages/<int:message_id>/", MessageDeleteView.as_view()),
]
