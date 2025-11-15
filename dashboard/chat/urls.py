# chat/urls.py
from django.urls import path
from .views import RoomListCreateView, MessageListView, MessageCreateView, MessageUpdateView, MessageDeleteView

urlpatterns = [
    path("chat/rooms/", RoomListCreateView.as_view(), name="room-list"),
    path("chat/rooms/<str:room_name>/messages/", MessageListView.as_view(), name="message-list"),
    path("chat/messages/", MessageCreateView.as_view(), name="message-create"),
    path("chat/messages/<int:pk>/", MessageUpdateView.as_view(), name="message-update"),
    path("messages/<int:pk>/delete/", MessageDeleteView.as_view(), name="message-delete"),
]
