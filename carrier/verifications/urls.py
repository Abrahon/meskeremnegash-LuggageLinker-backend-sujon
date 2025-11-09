# core/urls.py
from django.urls import path
from .views import VerificationRetrieveCreateView

urlpatterns = [
      path("verifications/", VerificationRetrieveCreateView.as_view(), name="verification-root"),
]
