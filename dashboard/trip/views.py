# trips/views.py
from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import Trip
from .serializers import TripSerializer


class TripCreateView(generics.CreateAPIView):
    """
    POST /api/trips/  -> create new trip
    """
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            # set user from request user
            serializer.save(user=request.user)
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"success": False, "errors": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            # log.exception in real production
            return Response({"success": False, "message": f"Unexpected error: {str(exc)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TripListView(generics.ListAPIView):
    """
    GET /api/trips/ -> list trips for current user (paginated)
    """
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # only show trips owned by the current user
        return Trip.objects.filter(user=self.request.user)


class TripDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/trips/{pk}/
    """
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # only allow user to access
        return Trip.objects.filter(user=self.request.user)

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    # provide nice delete response
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"success": True, "message": "Trip deleted."}, status=status.HTTP_200_OK)
