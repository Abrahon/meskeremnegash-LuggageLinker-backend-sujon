# chat/models.py
from django.db import models
from django.conf import settings
from common.models import TimeStampedModel
from cloudinary.models import CloudinaryField

User = settings.AUTH_USER_MODEL

class Room(TimeStampedModel):
    """Chat room (one per conversation, or group)."""
    name = models.CharField(max_length=255, unique=True)
    participants = models.ManyToManyField(User, related_name="rooms", blank=True)
 

    def __str__(self):
        return self.name

class Message(TimeStampedModel):
    TEXT = "text"
    FILE = "file"

    MESSAGE_TYPES = [(TEXT, "Text"), (FILE, "File")]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    content = models.TextField(blank=True, null=True)
    file = CloudinaryField('image upload',null=True, blank=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default=TEXT)
    edited = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    # optional: add read receipts per user later

    class Meta:
        ordering = ("created_at",)

    def file_url(self, request=None):
        if not self.file:
            return None
        if request:
            return request.build_absolute_uri(self.file.url)
        return self.file.url

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="actor_notifications")
    verb = models.CharField(max_length=255)
    target_message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    target_room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-timestamp",)
