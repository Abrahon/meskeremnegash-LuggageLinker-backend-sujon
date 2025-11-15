from rest_framework import serializers
from .models import CarrierProfile
import re


class CarrierProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.name", read_only=False)
    profile_image_url = serializers.SerializerMethodField()
    email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = CarrierProfile
        fields = [
            'full_name', 'profile_image', 'profile_image_url',
            'email'
        ]
        read_only_fields = ['email']

    # ---------------------------
    # ✅ Custom Image Size Validation
    # ---------------------------
    def validate_profile_image(self, image):
        max_size_mb = 5
        if image and hasattr(image, 'size'):
            size_in_mb = image.size / (1024 * 1024)
            if size_in_mb > max_size_mb:
                raise serializers.ValidationError(
                    f"Image size must be {max_size_mb}MB or less. Your file is {size_in_mb:.2f}MB."
                )
        return image

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            name = user_data.get('name')
            if name:
                instance.user.name = name
                instance.user.save()
        return super().update(instance, validated_data)

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return ""


# update password serializers
class UpdatePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user

        # Check current password
        if not user.check_password(data['current_password']):
            raise serializers.ValidationError({"current_password": "Current password is incorrect."})

        # Match new passwords
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "Passwords do not match."})

        # Prevent reusing old password
        if data['current_password'] == data['new_password']:
            raise serializers.ValidationError({"new_password": "New password cannot be the same as the old one."})

        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
