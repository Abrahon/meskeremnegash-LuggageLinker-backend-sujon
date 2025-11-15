# verifications/views.py
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import Verification
from .serializers import VerificationSerializer
from .models import NationalID, Passport, DriversLicense
from .serializers import NationalIDSerializer, PassportSerializer, DriversLicenseSerializer
from .serializers import SelfieSerializer
from .models import Address
from .serializers import AddressSerializer

from rest_framework import status, generics, permissions
from rest_framework.response import Response

from .models import NationalID, Passport, DriversLicense
from .serializers import (
    NationalIDSerializer,
    PassportSerializer,
    DriversLicenseSerializer,
)
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


# id verifications 
# class DocumentUploadView(generics.GenericAPIView):
#     """
#     Handle uploading verification documents dynamically:
#     - document_type = 'national_id'
#     - document_type = 'passport'
#     - document_type = 'drivers_license'
#     """

#     permission_classes = [permissions.IsAuthenticated]
#     parser_classes = [MultiPartParser, FormParser, JSONParser]

#     serializer_classes = {
#         "national_id": NationalIDSerializer,
#         "passport": PassportSerializer,
#         "drivers_license": DriversLicenseSerializer,
#     }

#     def get_serializer_class(self):
#         document_type = self.request.data.get("document_type")
#         if not document_type:
#             return None
#         return self.serializer_classes.get(document_type.lower())

#     def post(self, request, *args, **kwargs):
#         document_type = request.data.get("document_type")
#         if not document_type:
#             return Response(
#                 {"error": "document_type is required. Options: national_id, passport, drivers_license."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         serializer_class = self.get_serializer_class()
#         if not serializer_class:
#             return Response(
#                 {"error": f"Invalid document_type '{document_type}'. Must be one of: national_id, passport, drivers_license."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # Attach the user to the serializer data
#         data = request.data.copy()
#         data["user"] = request.user.id

#         serializer = serializer_class(data=data, context={"request": request})
#         if serializer.is_valid():
#             instance = serializer.save()
#             return Response(
#                 {
#                     "message": f"{document_type.replace('_', ' ').title()} uploaded successfully.",
#                     "data": serializer.data,
#                 },
#                 status=status.HTTP_201_CREATED,
#             )

#         return Response(
#             {"errors": serializer.errors},
#             status=status.HTTP_400_BAD_REQUEST,
#         )

class DocumentUploadView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser] 

    serializer_classes = {
        "national_id": NationalIDSerializer,
        "passport": PassportSerializer,
        "drivers_license": DriversLicenseSerializer,
    }

    def get_serializer_class(self):
        doc_type = self.request.data.get("document_type")
        return self.serializer_classes.get(doc_type)

    def post(self, request, *args, **kwargs):
        document_type = request.data.get("document_type")
        if not document_type:
            return Response({"error": "document_type is required"}, status=400)

        serializer_class = self.get_serializer_class()
        if not serializer_class:
            return Response({"error": "invalid document_type"}, status=400)

        serializer = serializer_class(data=request.data, context={"request": request})

        if serializer.is_valid():
            # 👉 FIX: Attach user here
            serializer.save(user=request.user)

            return Response(
                {
                    "message": f"{document_type} uploaded successfully",
                    "data": serializer.data,
                },
                status=201
            )

        return Response(serializer.errors, status=400)




class SelfieUploadView(generics.ListCreateAPIView):
    serializer_class = SelfieSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Selfie.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def post(self, request, *args, **kwargs):
        images = request.FILES.getlist('images')
        if not images:
            return Response({"error": "No images provided"}, status=status.HTTP_400_BAD_REQUEST)

        response_data = []
        for img in images:
            serializer = self.get_serializer(data={'image': img})
            if serializer.is_valid():
                serializer.save(user=request.user)
                response_data.append(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(response_data, status=status.HTTP_201_CREATED)



class AddressCreateView(generics.CreateAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(
                {"message": "Address saved successfully.", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )

        except ValidationError as e:
            return Response(
                {"errors": e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Log the exception for debugging (production best practice)
            print(f"Unexpected error: {e}")
            return Response(
                {"error": "An unexpected error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
