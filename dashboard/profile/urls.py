# carrier/profile/urls.py
from django.urls import path
from .views import CarrierProfileView,UpdatePasswordView

urlpatterns = [
    path('profile/', CarrierProfileView.as_view(), name='carrier-profile'),
    path('update-password/', UpdatePasswordView.as_view(), name='carrier-profile'),
]
