# carrier/profile/views.py
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .serializers import CarrierProfileSerializer,UpdatePasswordSerializer
from .models import CarrierProfile
from rest_framework.views import APIView
from rest_framework import generics, status, serializers
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class CarrierProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/profile/       -> retrieve current user's profile (auto-create if none)
    PUT  /api/profile/       -> replace profile fields
    PATCH /api/profile/      -> partial update (recommended for image uploads)
    """
    serializer_class = CarrierProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        try:
            profile, created = CarrierProfile.objects.get_or_create(user=self.request.user)
            return profile
        except Exception as e:
            raise serializers.ValidationError({"detail": f"Error retrieving profile: {str(e)}"})

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', True)  
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)

            # Manual field validation
            data = request.data
            errors = {}

            # Example: validate phone number (digits only, length 10-15)
            phone = data.get('phone')
            if phone:
                if not re.match(r'^\d{10,15}$', str(phone)):
                    errors['phone'] = "Phone number must contain 10-15 digits only."

            # Example: validate age (if provided)
            age = data.get('age')
            if age:
                try:
                    age_int = int(age)
                    if age_int < 0 or age_int > 120:
                        errors['age'] = "Age must be between 0 and 120."
                except ValueError:
                    errors['age'] = "Age must be a valid number."

            # Example: validate username (if provided)
            username = data.get('username')
            if username:
                if len(username) < 3:
                    errors['username'] = "Username must be at least 3 characters long."

            if errors:
                return Response({"success": False, "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                "success": True,
                "message": "Profile updated successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except serializers.ValidationError as ve:
            return Response({"success": False, "errors": ve.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"success": False, "message": f"Error updating profile: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)



class UpdatePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser] 

    def post(self, request):
        serializer = UpdatePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password updated successfully."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)