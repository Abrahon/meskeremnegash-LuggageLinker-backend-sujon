from django.urls import path, include
from .views import (
    SignupView, 
    LoginView, 
    SendOTPView, 
    VerifyOTPView, 
    ResetPasswordView, 
    AdminCreateView,
    GoogleCallbackView,
    GoogleLoginView,
    GoogleExchangeView,
    CheckTokenView,
    UserListView
)
urlpatterns = [
    # Your custom authentication views
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('admin/create/', AdminCreateView.as_view(), name='admin-create'),
    path('check/token/', CheckTokenView.as_view(), name='check-token'),
    path('users/', UserListView.as_view(), name='user-list'),

    # Social login URLs from django-allauth
    path('social/', include('allauth.socialaccount.urls')),         
    path("google/login/", GoogleLoginView.as_view(), name="google_login"),
    path("google/callback/", GoogleCallbackView.as_view(), name="google_callback"),
    path("google/exchange/", GoogleExchangeView.as_view(), name="google_exchange")   
]
