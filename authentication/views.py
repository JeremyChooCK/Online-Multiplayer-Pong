from django.shortcuts import render
# Create your views here.
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer
from django.http import HttpResponse
import requests
import os
import environ
import json

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        # ...

        return token
    
class MyTokenObtainPairView(TokenObtainPairView):
        serializer_class = MyTokenObtainPairSerializer

class UserCreate(APIView):
    """
    Creates the user.
    """
    def post(self, request, format='json'):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                json = serializer.data
                return Response(json, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def get_user_info(access_token):
    api_url = 'https://api.intra.42.fr/v2/me'  # Example API endpoint
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(api_url, headers=headers)
    return response.json()

def oauth_callback(request):
    code = request.GET.get('code')  # Get the authorization code from query parameters
    if code:
        access_token_response = exchange_code_for_token(code)
        if 'access_token' in access_token_response:
            access_token = access_token_response['access_token']
            user_info = get_user_info(access_token)  # Get user information using the token
            return HttpResponse(f"Authorization successful! User info: {json.dumps(user_info)}")
        else:
            # Handle the error case
            error_details = access_token_response.get('details', {})
            return HttpResponse(f"Failed to retrieve access token. Details: {error_details}")
    else:
        error = request.GET.get('error', 'Unknown error')
        return HttpResponse(f"Failed to authorize: {error}")


def exchange_code_for_token(code):
    token_url = 'https://api.intra.42.fr/oauth/token'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'http://127.0.0.1:8000/auth/oauth',
        'client_id': 'u-s4t2ud-9b0fa67cf4ac001dac948db1c08b417156de148160cb998b92520a9e9bbaef2b',
        'client_secret': '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',
    }
    response = requests.post(token_url, data=data)
    # Check if the request was successful
    if response.status_code == 200:
        return response.json()  # This should include the access token
    else:
        # Log or handle error response
        return {'error': 'Failed to retrieve token', 'details': response.json()}