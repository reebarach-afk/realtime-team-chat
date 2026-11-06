from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Membership, Message
from .serializers import MessageSerializer

MAX_LENGTH = 2000


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.room_id = int(self.scope["url_route"]["kwargs"]["room_id"])
        self.group = f"chat_{self.room_id}"

        # 1) must be logged in (valid JWT)
        if not self.user.is_authenticated:
            await self.close(code=4401)
            return

        # 2) must be a member of this room
        if not await self.is_member():
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        text = (content.get("message") or "").strip()
        if not text or len(text) > MAX_LENGTH:
            return

        message = await self.save_message(text)
        await self.channel_layer.group_send(
            self.group, {"type": "chat.message", "message": message}
        )

    # --- handlers for group_send events ---
    async def chat_message(self, event):
        await self.send_json({"type": "message", **event["message"]})

    async def message_deleted(self, event):
        await self.send_json({"type": "deleted", "id": event["id"]})

    # --- database helpers ---
    @database_sync_to_async
    def is_member(self):
        return Membership.objects.filter(user=self.user, room_id=self.room_id).exists()

    @database_sync_to_async
    def save_message(self, text):
        msg = Message.objects.create(room_id=self.room_id, user=self.user, content=text)
        return dict(MessageSerializer(msg).data)
