from urllib.parse import urlencode, unquote
from .serializers import UserSerializer
import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from .serializers import SignupSerializer, LoginSerializer, ResetPasswordSerializer
from .models import User, OTP


from .serializers import (
    SendOTPSerializer, VerifyOTPSerializer, ResetPasswordSerializer
)



# class SignupView(generics.CreateAPIView):
#     serializer_class = SignupSerializer
#     permission_classes = [AllowAny]
#     parser_classes = (MultiPartParser, FormParser)

#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.save()

#         return Response({
#             "message": "User created successfully",
#             "user": {
#                 "id": user.id,
#                 "email": user.email,
#                 "name": user.name,
#                 "role": user.role,
#             }
#         }, status=status.HTTP_201_CREATED)
from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from .serializers import SignupSerializer, UserSerializer


class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # Validate & create user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # If you want to send OTP/email here, do it now (send_otp_email or similar).
        # Example: send_otp_email(user.email, code)

        # Return serialized user (read-only fields) — keeps API consistent
        user_data = UserSerializer(user).data

        return Response(
            {
                "message": "User created successfully",
                "user": user_data,
            },
            status=status.HTTP_201_CREATED,
        )



def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['role'] = user.role
    refresh['name'] = user.name 
    refresh['email'] = user.email 
     # optional
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        print("user",user)

        tokens = get_tokens_for_user(user)  # generate tokens with role

        return Response({
            "message": "Login successful",
            "token": tokens,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
            }
        }, status=status.HTTP_200_OK)



class SendOTPView(generics.CreateAPIView):
    serializer_class = SendOTPSerializer
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = serializer.save()  # result is a dict {"message": "..."}
        print("serializer.save() returned:", result)

        # Extract email from validated_data instead of assuming .email exists
        email = serializer.validated_data.get("email")
        if email and hasattr(request, "session"):
            request.session['otp_user_email'] = email
            print("Stored in session:", email)

        return Response(
            {"message": result.get("message", "OTP sent successfully"), "email": email},
            status=200
        )


class VerifyOTPView(generics.GenericAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # OTP verified → keep email in session for password reset
        request.session['verified_email'] = serializer.validated_data["user"].email

        return Response({"message": "OTP verified successfully."})




class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        """
        Request body must include:
        {
            "email": "user@example.com",
            "otp": "123456",
            "new_password": "newStrongPassword123",
            "confirm_password": "newStrongPassword123"
        }
        """
        email = request.data.get("email")
        otp_code = request.data.get("otp")
        print("otp_code",otp_code)

        if not email or not otp_code:
            return Response(
                {"detail": "Email and OTP are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1️⃣ Verify user exists
        user = User.objects.filter(email=email).first()
        print("user", user)

        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # 2️⃣ Verify OTP
        # otp = OTP.objects.filter(user=user, code=str(otp_code)).order_by("-created_at").first()
        otp = OTP.objects.filter(user=user, code=str(otp_code).strip()).order_by("-created_at").first()
        print("otp", otp)
        if not otp:
            return Response({"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_expired():
            return Response({"detail": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)

        # 3️⃣ OTP valid → delete OTP to prevent reuse
        otp.delete()

        # 4️⃣ Reset password
        serializer = self.get_serializer(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)






class AdminCreateView(generics.CreateAPIView):
    permission_classes = [IsAdminUser]  # Only admins can access

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('name')

        if not email or not password or not name:
            return Response({"detail": "Name, email, and password are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.create_superuser(
                email=email,
                password=password,
                name=name
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Admin user created successfully"},
                        status=status.HTTP_201_CREATED) 


# check token valiude orn inavlid
class CheckTokenView(APIView):
    """
    Check if a JWT access token is valid or invalid.
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request, *args, **kwargs):
        # Extract token from the "Authorization" header
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({"detail": "Authorization header missing or invalid format."},
                            status=status.HTTP_400_BAD_REQUEST)

        token = auth_header.split(' ')[1]

        jwt_auth = JWTAuthentication()
        try:
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            return Response({
                "valid": True,
                "message": "Token is valid.",
                "user": user.email
            }, status=status.HTTP_200_OK)
        except (InvalidToken, TokenError) as e:
            return Response({
                "valid": False,
                "message": "Invalid or expired token.",
                "error": str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)


# google login 
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Step 1: Redirect user to Google Auth URL
        """
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",      
        }
        google_auth_url = f"{base_url}?{urlencode(params)}"
        return Response({"auth_url": google_auth_url})


class GoogleCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Step 2: Google redirects here with ?code=...
        We exchange code for token, fetch user info, create user, return JWT
        """
        code = request.GET.get("code")
        if not code:
            return redirect(f"{settings.FRONTEND_REDIRECT_URL}?error=NoCode")

        # Exchange code for access token
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        token_response = requests.post(token_url, data=data).json()
        access_token = token_response.get("access_token")

        if not access_token:
            return redirect(f"{settings.FRONTEND_REDIRECT_URL}?error=InvalidToken")

        # Fetch user info from Google
        user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        user_info = requests.get(user_info_url, params={"access_token": access_token}).json()

        email = user_info.get("email")
        name = user_info.get("name", "")

        if not email:
            return redirect(f"{settings.FRONTEND_REDIRECT_URL}?error=EmailNotFound")

        # Create or get user
        user, _ = User.objects.get_or_create(
            email=email,
            defaults={"username": email.split("@")[0], "first_name": name},
        )

        # Generate JWT
        refresh = RefreshToken.for_user(user)
        jwt_token = str(refresh.access_token)

        # Redirect back to frontend with JWT
        return redirect(f"{settings.FRONTEND_REDIRECT_URL}?token={jwt_token}")
    

class GoogleExchangeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"error": "Code is required"}, status=400)

        # ⚠️ 1️⃣ Common cause of invalid_grant: The 'redirect_uri' here must match EXACTLY
        #     the one used during the frontend Google OAuth authorization request.
        #     Even a trailing slash mismatch causes 'invalid_grant'.
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": unquote(code),  # ✅ Decode URL-encoded code
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,  # ⚠️ MUST match frontend redirect
            "grant_type": "authorization_code",
        }

        # Exchange code for access token
        r = requests.post(token_url, data=data)

        # ⚠️ 2️⃣ If the code is already used or expired, Google returns invalid_grant
        #     Each code can only be used once and expires quickly (within ~60s)
        if r.status_code != 200:
            return Response({
                "error": r.json(),
                "hint": "Check redirect_uri and ensure you're using a fresh code."
            }, status=400)
        
        token_data = r.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return Response({"error": "Invalid access token"}, status=400)

        # ✅ Fetch user info from Google
        user_info = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()

        email = user_info.get("email")
        name = user_info.get("name", "")

        if not email:
            return Response({"error": "No email from Google"}, status=400)

        # ✅ Create or get existing user
        user, _ = User.objects.get_or_create(
            email=email,
            defaults={"name": name}
        )

        # ✅ Generate JWT
        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role  # add role in token claims

        return Response({
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
            },
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })



class GoogleSignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Sign up a user using Google OAuth code
        """
        code = request.data.get("code")
        if not code:
            return Response({"error": "Code is required"}, status=400)

        # Exchange code for access token
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": unquote(code),
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        token_response = requests.post(token_url, data=data)
        if token_response.status_code != 200:
            return Response({"error": "Failed to get token", "details": token_response.json()}, status=400)

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return Response({"error": "Invalid access token"}, status=400)

        # Fetch user info from Google
        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        user_info = requests.get(
            user_info_url, headers={"Authorization": f"Bearer {access_token}"}
        ).json()

        email = user_info.get("email")
        name = user_info.get("name", "")

        if not email:
            return Response({"error": "No email returned from Google"}, status=400)

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response({"error": "User already exists. Please login."}, status=400)

        # Create new user (signup)
        user = User.objects.create(
            email=email,
            username=email.split("@")[0],
            first_name=name
        )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token_jwt = str(refresh.access_token)

        return Response({
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.first_name,
            },
            "refresh": str(refresh),
            "access": access_token_jwt,
            "message": "Signup successful"
        }, status=201)


class UserListView(APIView):
    permission_classes = [IsAuthenticated]  # only logged-in users can access
    # or use [permissions.AllowAny] if you want it public

    def get(self, request):
        try:
            users = User.objects.all()
            serializer = UserSerializer(users, many=True)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
