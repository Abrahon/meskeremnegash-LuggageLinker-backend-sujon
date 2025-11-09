# trips/urls.py
from django.urls import path
from .views import TripCreateView, TripListView, TripDetailView

urlpatterns = [
    path("trips/list/", TripListView.as_view(), name="trip-list"),        # GET list
    path("add-trip/", TripCreateView.as_view(), name="trip-create"),  # POST create
    path("trip/<uuid:pk>/", TripDetailView.as_view(), name="trip-detail"),  # GET/PUT/PATCH/DELETE
]
