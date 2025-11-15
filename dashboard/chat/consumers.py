# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Room, Message, Notification
from .serializers import MessageSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.room_name = self.scope["url_route"]["kwargs"].get("room_name")
            self.user = self.scope.get("user", AnonymousUser())
            if not self.room_name:
                await self.close(code=4001)
                return

            # fetch room or create (depending on policy)
            try:
                self.room = await database_sync_to_async(Room.objects.get)(name=self.room_name)
            except Room.DoesNotExist:
                # option: create if not exists
                self.room = await database_sync_to_async(Room.objects.create)(name=self.room_name)
                if not getattr(self.user, "is_anonymous", True):
                    await database_sync_to_async(self.room.participants.add)(self.user)

            # Security: ensure participant
            if self.user.is_anonymous or not await database_sync_to_async(self.room.participants.filter(pk=self.user.pk).exists)():
                # If you want to require being participant: close
                # Alternatively, automatically add participant:
                await database_sync_to_async(self.room.participants.add)(self.user)

            self.group_name = f"chat_{self.room.name}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            await self.send_json({"type":"connection_established","message":"connected"})
        except Exception as e:
            await self.close(code=1011)

    async def disconnect(self, code):
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        except Exception:
            pass

    async def receive(self, text_data=None, bytes_data=None):
        try:
            if text_data is None:
                return
            data = json.loads(text_data)
            action = data.get("action")

            if action == "send_message":
                await self.handle_send_message(data)
            elif action == "edit_message":
                await self.handle_edit_message(data)
            elif action == "delete_message":
                await self.handle_delete_message(data)
            elif action == "typing":
                await self.handle_typing(data)
            else:
                await self.send_json({"error":"unknown_action"})
        except json.JSONDecodeError:
            await self.send_json({"error":"invalid_json"})
        except Exception as e:
            await self.send_json({"error":"server_error", "detail": str(e)})

    async def handle_send_message(self, data):
        """
        data: { action: "send_message", content: "...", message_type: "text" }
        file uploads should be done via REST and server will broadcast file messages.
        """
        content = data.get("content", "")
        message_type = data.get("message_type", Message.TEXT)
        if not content and message_type == Message.TEXT:
            await self.send_json({"error":"empty_message"})
            return

        # create message
        msg = await database_sync_to_async(Message.objects.create)(
            room=self.room,
            sender=self.user,
            content=content,
            message_type=message_type
        )
        serialized = MessageSerializer(msg, context={"request": None}).data

        # broadcast to room
        await self.channel_layer.group_send(self.group_name, {"type":"chat.message","message":serialized})

        # notify other participants
        recipients = await database_sync_to_async(lambda: list(self.room.participants.exclude(pk=self.user.pk).all()))()
        for r in recipients:
            notif = await database_sync_to_async(Notification.objects.create)(recipient=r, actor=self.user, verb="sent_message", target_message=msg, target_room=self.room)
            # send to personal notification group
            await self.channel_layer.group_send(f"notifications_{r.pk}", {"type":"notify","notification": {"id": notif.pk,"actor": self.user.username,"verb":"sent_message","room": self.room.name,"timestamp": notif.timestamp.isoformat()}})

    async def handle_edit_message(self, data):
        """
        data: { action: "edit_message", message_id: 12, content: "new text" }
        """
        mid = data.get("message_id")
        content = data.get("content", "")
        if not mid:
            await self.send_json({"error":"message_id_required"})
            return

        try:
            msg = await database_sync_to_async(Message.objects.get)(pk=mid)
            if msg.sender_id != self.user.pk:
                await self.send_json({"error":"permission_denied"})
                return

            await database_sync_to_async(setattr)(msg, "content", content)
            await database_sync_to_async(setattr)(msg, "edited", True)
            await database_sync_to_async(msg.save)()

            serialized = MessageSerializer(msg, context={"request": None}).data
            await self.channel_layer.group_send(self.group_name, {"type":"chat.message_update","message": serialized})
        except Message.DoesNotExist:
            await self.send_json({"error":"message_not_found"})
        except Exception as e:
            await self.send_json({"error":"edit_failed","detail": str(e)})

    async def handle_delete_message(self, data):
        """
        data: { action: "delete_message", message_id: 12 }
        We'll soft-delete (deleted=True) and broadcast delete
        """
        mid = data.get("message_id")
        if not mid:
            await self.send_json({"error":"message_id_required"})
            return
        try:
            msg = await database_sync_to_async(Message.objects.get)(pk=mid)
            if msg.sender_id != self.user.pk:
                await self.send_json({"error":"permission_denied"})
                return
            await database_sync_to_async(setattr)(msg, "deleted", True)
            await database_sync_to_async(msg.save)()
            await self.channel_layer.group_send(self.group_name, {"type":"chat.message_delete","message_id": mid})
        except Message.DoesNotExist:
            await self.send_json({"error":"message_not_found"})
        except Exception as e:
            await self.send_json({"error":"delete_failed","detail": str(e)})

    async def handle_typing(self, data):
        """
        data: { action: "typing", typing: true | false }
        Broadcast typing event to other participants
        """
        is_typing = data.get("typing", False)
        username = getattr(self.user, "username", "anonymous")
        await self.channel_layer.group_send(self.group_name, {"type":"chat.typing","username": username, "typing": is_typing, "sender_id": self.user.pk})

    # Group handlers - these are called when group_send is used
    async def chat_message(self, event):
        await self.send_json({"type":"chat","payload": event["message"]})

    async def chat_message_update(self, event):
        await self.send_json({"type":"chat_update","payload": event["message"]})

    async def chat_message_delete(self, event):
        await self.send_json({"type":"chat_delete","message_id": event["message_id"]})

    async def chat_typing(self, event):
        # send typing events to clients
        await self.send_json({"type":"typing","username": event["username"], "typing": event["typing"], "sender_id": event.get("sender_id")})

    # compatibility wrappers with Channels naming
    async def chat_message(self, event):
        # event from REST or internal code might use 'message' key
        await self.send_json({"type":"chat","payload": event.get("message")})

    # If functions above are duplicated, ensure consistent handler names:
    async def chat_message(self, event):  # final handler
        await self.send_json({"type":"chat","payload": event.get("message")})

# notifications
# chat/consumers.py (continued)
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user", AnonymousUser())
        if self.user.is_anonymous:
            await self.close(code=4003)
            return
        self.group_name = f"notifications_{self.user.pk}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        # optionally send unread count
        unread_count = await database_sync_to_async(lambda: self.user.notifications.filter(read=False).count())()
        await self.send_json({"type":"notification_meta","unread": unread_count})

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # handle read/mark actions
        if text_data is None:
            return
        data = json.loads(text_data)
        action = data.get("action")
        if action == "mark_read":
            nid = data.get("notification_id")
            if nid:
                await database_sync_to_async(Notification.objects.filter(pk=nid, recipient=self.user).update)(read=True)
                await self.send_json({"type":"notification_marked","id": nid})
            else:
                await self.send_json({"error":"notification_id_required"})

    async def notify(self, event):
        await self.send_json({"type":"notification","payload": event.get("notification")})
