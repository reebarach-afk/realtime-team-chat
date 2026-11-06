from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from config.asgi import application

from .models import Membership, Message, Room

User = get_user_model()


def auth_client(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


class RestTests(TransactionTestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pass1234")
        self.bob = User.objects.create_user("bob", password="pass1234")

    def test_register_and_login(self):
        c = APIClient()
        r = c.post("/api/auth/register/", {"username": "carol", "password": "secret1"})
        self.assertEqual(r.status_code, 201)
        r = c.post("/api/auth/login/", {"username": "carol", "password": "secret1"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)

    def test_creator_becomes_admin(self):
        r = auth_client(self.alice).post("/api/rooms/", {"name": "general"})
        self.assertEqual(r.status_code, 201)
        m = Membership.objects.get(user=self.alice, room_id=r.data["id"])
        self.assertEqual(m.role, Membership.ADMIN)

    def test_non_member_cannot_read_messages(self):
        room = Room.objects.create(name="private", created_by=self.alice)
        Membership.objects.create(user=self.alice, room=room, role="admin")
        r = auth_client(self.bob).get(f"/api/rooms/{room.id}/messages/")
        self.assertEqual(r.status_code, 403)

    def test_member_cannot_change_roles_but_admin_can(self):
        room = Room.objects.create(name="r", created_by=self.alice)
        Membership.objects.create(user=self.alice, room=room, role="admin")
        Membership.objects.create(user=self.bob, room=room, role="member")
        url = f"/api/rooms/{room.id}/members/{self.bob.id}/"
        self.assertEqual(auth_client(self.bob).patch(url, {"role": "admin"}).status_code, 403)
        self.assertEqual(auth_client(self.alice).patch(url, {"role": "admin"}).status_code, 200)

    def test_last_admin_cannot_be_demoted(self):
        room = Room.objects.create(name="r2", created_by=self.alice)
        Membership.objects.create(user=self.alice, room=room, role="admin")
        url = f"/api/rooms/{room.id}/members/{self.alice.id}/"
        self.assertEqual(auth_client(self.alice).patch(url, {"role": "member"}).status_code, 400)

    def test_member_cannot_delete_others_message(self):
        room = Room.objects.create(name="r3", created_by=self.alice)
        Membership.objects.create(user=self.alice, room=room, role="admin")
        Membership.objects.create(user=self.bob, room=room, role="member")
        msg = Message.objects.create(room=room, user=self.alice, content="hi")
        r = auth_client(self.bob).delete(f"/api/messages/{msg.id}/")
        self.assertEqual(r.status_code, 403)


class WebSocketTests(TransactionTestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pass1234")
        self.bob = User.objects.create_user("bob", password="pass1234")
        self.room = Room.objects.create(name="ws-room", created_by=self.alice)
        Membership.objects.create(user=self.alice, room=self.room, role="admin")
        Membership.objects.create(user=self.bob, room=self.room, role="member")

    def communicator(self, user=None, token=None):
        if user is not None:
            token = str(AccessToken.for_user(user))
        path = f"/ws/chat/{self.room.id}/" + (f"?token={token}" if token else "")
        return WebsocketCommunicator(application, path, headers=[(b"origin", b"http://localhost:5173")])

    async def test_message_is_broadcast_and_saved(self):
        a, b = self.communicator(self.alice), self.communicator(self.bob)
        self.assertTrue((await a.connect())[0])
        self.assertTrue((await b.connect())[0])

        await a.send_json_to({"message": "hello team"})
        got_a = await a.receive_json_from()
        got_b = await b.receive_json_from()
        self.assertEqual(got_b["content"], "hello team")
        self.assertEqual(got_b["username"], "alice")
        self.assertEqual(got_a["id"], got_b["id"])

        count = await database_sync_to_async(Message.objects.count)()
        self.assertEqual(count, 1)
        await a.disconnect()
        await b.disconnect()

    async def test_rejects_missing_or_bad_token(self):
        self.assertFalse((await self.communicator().connect())[0])
        self.assertFalse((await self.communicator(token="garbage").connect())[0])

    async def test_rejects_non_member(self):
        carol = await database_sync_to_async(User.objects.create_user)("carol", password="x12345")
        self.assertFalse((await self.communicator(carol).connect())[0])
