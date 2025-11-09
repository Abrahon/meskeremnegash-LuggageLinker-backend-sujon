# from django.apps import AppConfig


# class MessagesConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'carrier.messages' 
from django.apps import AppConfig

class MessagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'carrier.messages'      # full python path (keep as-is)
    label = 'carrier_messages'     # <<< unique label to avoid collision
