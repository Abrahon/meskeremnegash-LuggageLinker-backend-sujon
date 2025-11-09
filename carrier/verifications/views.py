# verifications/views.py
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import Verification
from .serializers import VerificationSerializer


class VerificationRetrieveCreateView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/verification/  -> get current user's verification (auto-create blank if none)
    POST /api/verification/  -> create verification (use CreateAPIView semantics but here we combine)
    PUT/PATCH /api/verification/ -> update verification
    """
    serializer_class = VerificationSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # allow file uploads and JSON

    def get_object(self):
        # return the Verification object for the authenticated user, if exists
        # We DO NOT auto-create a record here for GET; prefer explicit create via POST.
        return Verification.objects.filter(user=self.request.user).first()

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj:
            return Response({"success": False, "detail": "No verification found for this user."},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(obj)
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        if Verification.objects.filter(user=request.user).exists():
            return Response(
                {"success": False, "message": "Verification already exists. Use update endpoint instead."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data, context={"request": request})
        try:
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            return Response({"success": True, "data": VerificationSerializer(instance).data},
                            status=status.HTTP_201_CREATED)
        except ValidationError as ve:
            return Response({"success": False, "errors": ve.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            # In production replace with logger.exception(...)
            return Response({"success": False, "message": f"Unexpected error: {str(exc)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj:
            return Response({"success": False, "detail": "No verification record to update."},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(obj, data=request.data, partial=True, context={"request": request})
        try:
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            return Response({"success": True, "data": VerificationSerializer(instance).data},
                            status=status.HTTP_200_OK)
        except ValidationError as ve:
            return Response({"success": False, "errors": ve.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"success": False, "message": f"Unexpected error: {str(exc)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
