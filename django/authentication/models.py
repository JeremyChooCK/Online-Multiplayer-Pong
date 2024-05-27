from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True, default='profile_pictures/default.png')
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    match_history = models.TextField(blank=True)  # or use JSONField for structured data

    def __str__(self):
        return self.user.username
