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
import urllib.request
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from rest_framework import generics, permissions
from .models import UserProfile
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import get_object_or_404
import random
from django.core.mail import send_mail
from django.core.cache import cache
from rest_framework.permissions import AllowAny

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        if user.profile.twofa:  # Assuming `twofa` is a BooleanField on UserProfile
            # Note: Do not send the code here; just inform the frontend that further action is required
            send_verification_code(user)
            return {
                'require_2fa': True,
                'message': '2FA verification required.',
                'user_id': user.id,
                'email': user.email  # You may want to mask this for security
            }

        # Regular token creation
        refresh = RefreshToken.for_user(user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        return data
    
class MyTokenObtainPairView(TokenObtainPairView):
        serializer_class = MyTokenObtainPairSerializer

class UserCreate(APIView):
    """
    Creates the user.
    """
    def post(self, request, format='json'):
        print("Received data:", request.data)
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
    code = request.GET.get('code')
    if code:
        access_token_response = exchange_code_for_token(code)
        if 'access_token' in access_token_response:
            access_token = access_token_response['access_token']
            user_info = get_user_info(access_token)

            User = get_user_model()
            email = user_info.get('email', '').lower()  # Normalize the email

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': user_info['login'],  # Set username here only on creation
                    'first_name': user_info.get('first_name', '')
                }
            )

            if not created:
                # Update only non-identity fields if needed, skip username if you allow users to change it
                user.first_name = user_info.get('first_name', user.first_name)
                user.save()

            # Handle user profile and picture separately to avoid repeating it
            if created:
                handle_user_profile_creation(user, user_info)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            refresh['username'] = user_info.get('first_name', '')

            jwt_tokens = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }

            redirect_url = reverse('oauth_token') + f"?access={jwt_tokens['access']}&refresh={jwt_tokens['refresh']}"
            return HttpResponseRedirect(redirect_url)
        else:
            error_details = access_token_response.get('details', {})
            return HttpResponse(f"Failed to retrieve access token. Details: {json.dumps(error_details)}", status=400)
    else:
        error = request.GET.get('error', 'Unknown error')
        return HttpResponse(f"Failed to authorize: {error}", status=400)

def handle_user_profile_creation(user, user_info):
    profile_picture_url = user_info.get('image', {}).get('link', '')
    if profile_picture_url:
        file_path = os.path.join('profile_pictures', f"{user.username}.png")
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        urllib.request.urlretrieve(profile_picture_url, full_path)

        UserProfile.objects.create(
            user=user,
            profile_picture=file_path,
            wins=0,
            losses=0,
            match_history=''
        )


def exchange_code_for_token(code):
    token_url = 'https://api.intra.42.fr/oauth/token'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'https://localhost/auth/oauth',
        'client_id': environ.get('CLIENT_ID'),
        'client_secret': environ.get('CLIENT_SECRET'),
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
        user_id = self.kwargs.get('user_id')
        return get_object_or_404(User, id=user_id)

class UpdateUsernameView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        print("Authorization Header:", request.headers.get('Authorization'))
        print("User:", request.user)  # Debug: print user information
        print("Auth:", request.auth)   # Debug: print auth information
        new_username = request.data.get('new_username')
        if not new_username:
            return Response({'error': 'New username is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.is_authenticated:
            return Response({'error': 'YOOOOOOOOOOOOOOOOO'}, status=status.HTTP_401_UNAUTHORIZED)

        user = request.user
        user.username = new_username
        user.save()
        return Response({'message': 'Username updated successfully'}, status=status.HTTP_200_OK)

class ChangeProfilePictureView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        print("in cpp")

        try:
            user_profile = UserProfile.objects.get(user=request.user)
            image_file = request.FILES.get('profile_picture')

            if not image_file:
                return Response({'error': 'No image file provided'}, status=400)
            
            # Check if the uploaded file is an image
            if not image_file.content_type.startswith('image/'):
                return Response({'error': 'File is not an image'}, status=400)

            user_profile.profile_picture.save(image_file.name, image_file, save=True)
            return Response({'message': 'Profile picture updated successfully'}, status=200)

        except UserProfile.DoesNotExist:
            return Response({'error': 'UserProfile does not exist'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class UserIdPairsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        users = User.objects.all()
        user_id_pairs = {user.id: user.username for user in users}
        return JsonResponse(user_id_pairs, status=200)
        
def get_all_usernames(request):
    usernames = User.objects.values_list('username', flat=True)
    return JsonResponse(list(usernames), safe=False)

def send_verification_code(user):
    code = random.randint(100000, 999999)
    print(user.username)
    cache.set(f'verify_code_{user.username}', str(code), timeout=600)  # Store code for 10 minutes
    print(f'Verification code for {user.username}: {code}')
    send_mail(
        'Your Verification Code',
        f'Your verification code is {code}',
        'transcendenceverifyy@gmail.com',
        [user.email],
        fail_silently=False,
    )
    
class verify_code_view(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get('username')
        code = request.data.get('code')
        if not username or not code:
            return Response({'error': 'Username and code are required'}, status=400)

        user = get_user_model().objects.filter(username=username).first()
        if not user:
            return Response({'error': 'User not found'}, status=404)

        cached_code = cache.get(f'verify_code_{username}')
        if not cached_code:
            return Response({'error': 'Verification code has expired or is incorrect'}, status=400)

        if str(cached_code) != str(code):
            return Response({'error': 'Invalid verification code'}, status=400)

        # Delete the code from cache after successful verification
        cache.delete(f'verify_code_{username}')

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=200)