# verifications/models.py
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from common.models import TimeStampedModel
from .enums import VerificationStatus

# class VerificationStatus(models.TextChoices):
#     PENDING = "pending", "Pending"
#     APPROVED = "approved", "Approved"
#     REJECTED = "rejected", "Rejected"


def id_document_upload_to(instance, filename):
    # Put files in media/verification/<user_id>/<uuid>_<filename>
    return f"verification/{instance.user.id}/{uuid.uuid4().hex}_{filename}"


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

    # Optional file - use CloudinaryField or ImageField depending on your storage
    id_document = models.FileField(upload_to=id_document_upload_to, null=True, blank=True)

    status = models.CharField(
        max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.PENDING
    )
    admin_notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["national_id_number"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Verification({self.user}, {self.status})"
