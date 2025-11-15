import uuid
from django.db import models
from django.conf import settings
from common. models import TimeStampedModel
from cloudinary.models import CloudinaryField

class CarrierProfile(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    profile_image = CloudinaryField('profile', null=True, blank=True)

    def __str__(self):
        return f"Profile for {getattr(self.user, 'email', self.user.email)}"

        
