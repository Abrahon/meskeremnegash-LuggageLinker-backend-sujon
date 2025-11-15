# verifications/validators.py
import re
from datetime import date
from django.core.exceptions import ValidationError
from django.utils import timezone

PHONE_RE = re.compile(r'^\+?\d{9,15}$')  # +countrycode optional, 9-15 digits


def validate_phone(value):
    if not PHONE_RE.match(value):
        raise ValidationError("Phone number must be 9-15 digits, optional leading +.")


def validate_age_at_least(value, min_age=18):
    if not isinstance(value, date):
        raise ValidationError("Invalid date format.")
    today = timezone.localdate()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if age < min_age:
        raise ValidationError(f"User must be at least {min_age} years old.")
