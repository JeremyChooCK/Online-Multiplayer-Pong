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
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from rest_framework import generics, permissions
from .models import UserProfile
from django.conf import settings

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
    # Get the 'code' parameter from the request's GET parameters, which is sent by the OAuth provider.
    code = request.GET.get('code')
    if code:
        # Exchange the authorization code for an access token using a helper function.
        access_token_response = exchange_code_for_token(code)
        
        # Check if the response contains an 'access_token'.
        if 'access_token' in access_token_response:
            # Extract the access token from the response.
            access_token = access_token_response['access_token']
            
            # Use the access token to retrieve user information from the OAuth provider.
            user_info = get_user_info(access_token)
            # Get the user model from Django's authentication framework.
            User = get_user_model()
            
            # Create or get a user in your database. Assume the user info includes 'login' and 'email'.
            user, created = User.objects.get_or_create(
                username=user_info['login'], 
                defaults={
                    'email': user_info.get('email', ''),  # Default email to empty string if not provided.
                    'first_name': user_info.get('first_name', '')  # Default first_name to empty string if not provided.
                }
            )
            
            # If the user was created, set an unusable password (since authentication is handled via OAuth).
            if created:
                user.set_unusable_password()
                user.save()
                
                # Create the UserProfile for the new user.
                import urllib.request
                
                # Download the profile picture
                profile_picture_url = user_info.get('image', {}).get('link', '')
                if profile_picture_url:
                    username = user.username
                    file_name = f'{username}.png'
                    file_path = os.path.join('profile_pictures', os.path.basename(profile_picture_url))  # Replace with the actual path where you want to save the image
                    print( "FILE PATH: ",file_path)
                    # Download the image and save it to the specified path
                    urllib.request.urlretrieve(profile_picture_url, os.path.join(settings.MEDIA_ROOT, file_path))
                    
                    # Create the UserProfile for the new user with the file path
                    UserProfile.objects.create(
                        user=user,
                        profile_picture=file_path,
                        wins=0,
                        losses=0,
                        match_history=''
                    )

            # Generate a refresh token for the user. This token can be used to get new access tokens.
            refresh = RefreshToken.for_user(user)
            
            # Customize the token to include the first_name from the OAuth provider's data.
            refresh['username'] = user_info.get('first_name', '')

            # Prepare the token data for response.
            jwt_tokens = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }

            # Redirect to a page that handles these tokens. Passing tokens via URL is not secure for production!
            redirect_url = reverse('oauth_token') + f"?access={jwt_tokens['access']}&refresh={jwt_tokens['refresh']}"
            return HttpResponseRedirect(redirect_url)
        else:
            # Handle cases where the access token is not retrieved.
            error_details = access_token_response.get('details', {})
            return HttpResponse(f"Failed to retrieve access token. Details: {json.dumps(error_details)}")
    else:
        # Handle cases where no code is provided in the request.
        error = request.GET.get('error', 'Unknown error')
        return HttpResponse(f"Failed to authorize: {error}")



def exchange_code_for_token(code):
    token_url = 'https://api.intra.42.fr/oauth/token'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'https://localhost/auth/oauth',
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
    
class UserDetailView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user