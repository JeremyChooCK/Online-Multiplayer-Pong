from django.urls import path, include
from chat import views as chat_views
from django.contrib.auth.views import LoginView, LogoutView
from .views import get_all_usernames

urlpatterns = [
    path("", chat_views.chatPage, name="chat-page"),
    path('usernames/', get_all_usernames),
]
