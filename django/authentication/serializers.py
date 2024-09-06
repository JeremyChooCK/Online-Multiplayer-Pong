from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['twofa', 'profile_picture', 'wins', 'losses', 'match_history']

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    profile = UserProfileSerializer()

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        UserProfile.objects.create(user=user, **profile_data)
        return user

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'profile')
