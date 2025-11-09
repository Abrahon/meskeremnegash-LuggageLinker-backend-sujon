# trips/models.py
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from common.models import TimeStampedModel



class Trip(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trips"
    )
    origin = models.CharField(max_length=100)       # "From"
    destination = models.CharField(max_length=100)  # "To"

    departure_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)

    available_luggage_space = models.PositiveIntegerField(
        help_text="Available luggage space in kg (or units). Must be > 0."
    )
    transportation_type = models.CharField(max_length=50, default="Air")
    
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    notes = models.TextField(max_length=1000, blank=True)


    class Meta:
        ordering = ["-departure_date", "-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["departure_date"]),
        ]

    def __str__(self):
        return f"{self.origin} → {self.destination} ({self.departure_date})"
