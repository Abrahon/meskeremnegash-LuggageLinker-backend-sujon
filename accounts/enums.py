# accounts/enums.py
from django.db.models import TextChoices

class RoleChoices(TextChoices):
    ADMIN = 'admin', 'Admin'
    CARRIER = 'carrier', 'Carrier'
    SENDER = 'sender', 'Sender'
