# verifications/serializers.py
from rest_framework import serializers
from django.db import transaction
from django.core.validators import EmailValidator
from .models import Verification, VerificationStatus
from .validators import validate_phone, validate_age_at_least
from django.utils import timezone
from rest_framework import serializers
from .models import NationalID, Passport, DriversLicense, Address
from .models import Selfie


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



# Allowed file extensions and size limit (10 MB)
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf"}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def validate_file(file):
    if not file:
        raise serializers.ValidationError("File is required.")

    # Validate file size
    if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise serializers.ValidationError(f"File size must be under {MAX_FILE_SIZE_MB} MB.")

    # Validate file extension
    extension = file.name.split(".")[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise serializers.ValidationError(
            f"Invalid file type: .{extension}. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}."
        )

    return file


# -----------------------
# National ID Serializer
# -----------------------
# class NationalIDSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = NationalID
#         fields = ["id", "user", "front_image", "back_image", "status"]
#         read_only_fields = ["id", "status"]

#     def validate(self, attrs):
#         front = attrs.get("front_image")
#         back = attrs.get("back_image")

#         if not front or not back:
#             raise serializers.ValidationError("Both front and back images are required.")

#         validate_file(front)
#         validate_file(back)

#         return attrs

class NationalIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = NationalID
        fields = [ "user", "front_image", "back_image", "status"]
        read_only_fields = ["id", "status", "user"]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Convert Cloudinary paths to FULL URLs
        if instance.front_image:
            data["front_image"] = instance.front_image.url

        if instance.back_image:
            data["back_image"] = instance.back_image.url

        return data


# -----------------------
# Passport Serializer
# -----------------------
class PassportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passport
        fields = ["id", "user", "document", "status"]
        read_only_fields = ["id", "status"]

    def validate(self, attrs):
        document = attrs.get("document")
        if not document:
            raise serializers.ValidationError("Passport document is required.")
        validate_file(document)
        return attrs


# -----------------------
# Driver’s License Serializer
# -----------------------
class DriversLicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriversLicense
        fields = ["id", "user", "front_image", "back_image", "status"]
        read_only_fields = ["id", "status"]

    def validate(self, attrs):
        front = attrs.get("front_image")
        back = attrs.get("back_image")

        if not front or not back:
            raise serializers.ValidationError("Both front and back images are required.")

        validate_file(front)
        validate_file(back)

        return attrs




class SelfieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Selfie
        fields = ['id', 'user', 'image', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at', 'user']

    def validate_image(self, value):
        max_size = 10 * 1024 * 1024  # 10 MB
        if value.size > max_size:
            raise serializers.ValidationError("Image size should not exceed 10 MB")
        if not value.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            raise serializers.ValidationError("Only JPG, JPEG, PNG files are allowed")
        return value


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id',
            'address_line_1',
            'address_line_2',
            'city',
            'state_province',
            'zip_postal_code',
            'country'
        ]

    def validate(self, attrs):
        errors = {}
        required_fields = ['address_line_1', 'city', 'state_province', 'zip_postal_code', 'country']

        for field in required_fields:
            if not attrs.get(field):
                errors[field] = f"{field.replace('_', ' ').capitalize()} is required."

        if len(attrs.get('zip_postal_code', '')) < 3:
            errors['zip_postal_code'] = "Zip/Postal Code must be at least 3 characters long."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs
