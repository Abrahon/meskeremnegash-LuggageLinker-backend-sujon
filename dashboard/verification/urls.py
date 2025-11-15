# core/urls.py
from django.urls import path
from .views import VerificationRetrieveCreateView,DocumentUploadView,SelfieUploadView,AddressCreateView

urlpatterns = [
      path("verifications/", VerificationRetrieveCreateView.as_view(), name="verification-root"),
      # path("national-id/", NationalIDUploadView.as_view(), name="upload-national-id"),
      # path("passport/", PassportUploadView.as_view(), name="upload-passport"),
      # path("drivers-license/", DriversLicenseUploadView.as_view(), name="upload-drivers-license"),
      path("verification/upload/", DocumentUploadView.as_view(), name="document-upload"),
      path('verification/selfies/', SelfieUploadView.as_view(), name='selfie-upload'),
      path('verification/create/', AddressCreateView.as_view(), name='create_address'),

]
