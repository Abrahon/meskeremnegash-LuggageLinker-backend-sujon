# verifications/serializers.py
from rest_framework import serializers
from django.db import transaction
from django.core.validators import EmailValidator
from .models import Verification, VerificationStatus
from .validators import validate_phone, validate_age_at_least
from django.utils import timezone


class VerificationSerializer(serializers.ModelSerializer):
    # user is read-only and bound to request.user in the view
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    email = serializers.EmailField(validators=[EmailValidator()], required=True)
    phone_number = serializers.CharField(validators=[validate_phone], required=True)
    national_id_number = serializers.CharField(required=True)
    id_document = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Verification
        fields = [
            "id",
            "user",
            "full_name",
            "date_of_birth",
            "nationality",
            "phone_number",
            "email",
            "national_id_number",
            "id_document",
            "status",
            "admin_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "user", "status", "admin_notes", "created_at", "updated_at")

    def validate_date_of_birth(self, value):
        # ensure valid date and age >= 18
        validate_age_at_least(value, min_age=18)
        return value

    def validate_national_id_number(self, value):
        # If this is a create operation and national_id_number exists -> error
        qs = Verification.objects.filter(national_id_number=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This national ID number is already registered.")
        return value

    def validate_email(self, value):
        # Additional email uniqueness check (optionally ensure not taken by other users)
        # If you want to enforce unique per verification record we already have national_id unique
        return value

    def validate(self, attrs):
        # ensure required fields exist; date_of_birth already validated
        full_name = attrs.get("full_name")
        nationality = attrs.get("nationality")
        if not full_name or not full_name.strip():
            raise serializers.ValidationError({"full_name": "Full name is required."})
        if not nationality or not nationality.strip():
            raise serializers.ValidationError({"nationality": "Nationality is required."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        validated_data["user"] = user
        # status will be default PENDING
        instance = super().create(validated_data)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        # Prevent updating status/admin_notes via user API
        validated_data.pop("status", None)
        validated_data.pop("admin_notes", None)
        return super().update(instance, validated_data)
