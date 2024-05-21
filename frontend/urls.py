from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Make sure this points to a valid view
    path('oauth_token/', views.oauth_token, name='oauth_token'),
]