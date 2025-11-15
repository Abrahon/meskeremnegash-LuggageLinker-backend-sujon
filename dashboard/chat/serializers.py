# chat/serializers.py
from rest_framework import serializers
from .models import Room, Message, Notification
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id","email","name")

class RoomSerializer(serializers.ModelSerializer):
    participants = UserSimpleSerializer(many=True, read_only=True)
    class Meta:
        model = Room
        fields = ("id","name","participants","created_at")

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSimpleSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ("id","room","sender","content","file_url","message_type","edited","deleted","created_at","updated_at")

    def get_file_url(self, obj):
        request = self.context.get("request")
        return obj.file_url(request=request)

    def validate(self, data):
        # ensure either content or file present for non-edit create
        if self.instance is None:
            content = data.get("content")
            file = data.get("file")
            if not content and not file:
                raise serializers.ValidationError("Message must have text or file.")
        return data

class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSimpleSerializer(read_only=True)
    target_room = serializers.CharField(source="target_room.name", read_only=True)
    class Meta:
        model = Notification
        fields = ("id","recipient","actor","verb","target_message","target_room","read","timestamp")
