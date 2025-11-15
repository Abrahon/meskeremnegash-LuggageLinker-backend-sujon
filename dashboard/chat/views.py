# chat/views.py
import logging
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
from django.shortcuts import get_object_or_404
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Room, Message, Notification
from .serializers import RoomSerializer, MessageSerializer, NotificationSerializer

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()

class RoomListCreateView(generics.ListCreateAPIView):
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Room.objects.filter(participants=self.request.user).prefetch_related("participants")

    def perform_create(self, serializer):
        room = serializer.save()
        room.participants.add(self.request.user)
        # optional: invite other participants via request.data

class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    

    def get_queryset(self):
        room_name = self.kwargs.get("room_name")
        room = get_object_or_404(Room, name=room_name)
        # ensure user belongs to room
        if not room.participants.filter(pk=self.request.user.pk).exists():
            return Message.objects.none()
        return room.messages.select_related("sender").all()

class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        room = serializer.validated_data.get("room")
        if not room.participants.filter(pk=self.request.user.pk).exists():
            raise PermissionError("You are not a participant in this room.")
        msg = serializer.save(sender=self.request.user)
        # broadcast
        payload = {
            "type":"chat_message",
            "message": MessageSerializer(msg, context={"request": self.request}).data
        }
        async_to_sync(channel_layer.group_send)(f"chat_{room.name}", payload)

        # create notifications for other participants
        recipients = room.participants.exclude(pk=self.request.user.pk)
        for r in recipients:
            notif = Notification.objects.create(recipient=r, actor=self.request.user, verb="sent_message", target_message=msg, target_room=room)
            async_to_sync(channel_layer.group_send)(
                f"notifications_{r.pk}",
                {"type":"notify","notification": {"id":notif.pk,"actor": self.request.user.username, "verb":"sent_message","room":room.name,"timestamp":notif.timestamp.isoformat()}}
            )

class MessageUpdateView(generics.UpdateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Message.objects.all()
    http_method_names = ["patch","put"]

    def perform_update(self, serializer):
        msg = serializer.instance
        if msg.sender != self.request.user:
            raise PermissionError("Only sender can edit message.")
        serializer.save(edited=True)
        # broadcast update
        payload = {"type":"chat_message_update","message": MessageSerializer(msg, context={"request": self.request}).data}
        async_to_sync(channel_layer.group_send)(f"chat_{msg.room.name}", payload)

class MessageDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Message.objects.all()

    def perform_destroy(self, instance):
        if instance.sender != self.request.user:
            raise PermissionError("Only sender can delete message.")
        instance.deleted = True
        instance.save()
        payload = {"type":"chat_message_delete","message_id": instance.pk}
        async_to_sync(channel_layer.group_send)(f"chat_{instance.room.name}", payload)
