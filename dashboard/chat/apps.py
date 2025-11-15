# from django.apps import AppConfig


# class MessagesConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'carrier.messages' 


from django.apps import AppConfig

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard.chat'
    verbose_name = "Chat Application"


