import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from common.models import TimeStampedModel
from .enums import VerificationStatus
from cloudinary.models import CloudinaryField


def id_document_upload_to(instance, filename):
    # Files will go into: media/verification/<user_id>/<uuid>_<filename>
    return f"verification/{instance.user.id}/{uuid.uuid4().hex}_{filename}"

def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return f'user_{instance.user.id}/{filename}'


class Verification(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="verification"
    )

    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField()
    nationality = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    national_id_number = models.CharField(max_length=100, unique=True)

    id_document = models.FileField(upload_to=id_document_upload_to, null=True, blank=True)

    status = models.CharField(
        max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.PENDING
    )
    admin_notes = models.TextField(blank=True, default="")


    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["national_id_number"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Verification({self.user}, {self.status})"


# ------------------------------
# Additional Models for Each ID
# ------------------------------

class NationalID(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    front_image = CloudinaryField('Front NID', null=True, blank=True)
    back_image = CloudinaryField('Back NID', null=True, blank=True)

    status = models.CharField(
        max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.PENDING
    )

    def __str__(self):
        return f"NationalID({self.user})"


class Passport(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    document = CloudinaryField('Passport', null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.PENDING
    )

    def __str__(self):
        return f"Passport({self.user})"


class DriversLicense(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    front_image = CloudinaryField(
        'Front License Image',
        null=True,
        blank=True,
    )
    back_image = CloudinaryField(
        'Back License Image',
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.PENDING
    )

    def __str__(self):
        return f"DriversLicense({self.user})"



class Selfie(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='selfies')
    image = CloudinaryField("upload selfie", null=True, blank=True)

    def __str__(self):
        return f"Selfie {self.id} by {self.user.name}"

class Address(TimeStampedModel):
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    zip_postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.address_line_1}, {self.city}, {self.country}"
