# trips/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import Trip


class TripSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    # transportation_type = serializers.ChoiceField(choices=TransportationType.choices, default=TransportationType.AIR)

    class Meta:
        model = Trip
        fields = [
            "id", "user", "origin", "destination",
            "departure_date", "return_date",
            "available_luggage_space","transportation_type","price",
            "notes", "created_at", "updated_at",
        ]
        read_only_fields = ("id", "user", "created_at", "updated_at")

    def validate_available_luggage_space(self, value):
        if value <= 0:
            raise serializers.ValidationError("available_luggage_space must be a positive integer.")
        if value > 10000:
            raise serializers.ValidationError("available_luggage_space seems unreasonably large.")
        return value

    def validate_departure_date(self, value):
        # prevent past departure (allow same-day)
        today = timezone.localdate()
        if value < today:
            raise serializers.ValidationError("departure_date cannot be in the past.")
        return value

    def validate(self, attrs):
        dep = attrs.get("departure_date", getattr(self.instance, "departure_date", None))
        ret = attrs.get("return_date", getattr(self.instance, "return_date", None))

        if ret:
            if dep and ret < dep:
                raise serializers.ValidationError({"return_date": "return_date cannot be before departure_date."})

        origin = attrs.get("origin") or getattr(self.instance, "origin", "")
        destination = attrs.get("destination") or getattr(self.instance, "destination", "")
        if origin and destination and origin.strip().lower() == destination.strip().lower():
            raise serializers.ValidationError({"destination": "origin and destination must be different."})

        # optional additional business rules can be added here
        return attrs
