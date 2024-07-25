from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Game(models.Model):
    player1 = models.ForeignKey(User, related_name='games_player1', on_delete=models.CASCADE)
    player2 = models.ForeignKey(User, related_name='games_player2', on_delete=models.CASCADE)
    score1 = models.IntegerField(default=0)
    score2 = models.IntegerField(default=0)
    in_progress = models.BooleanField(default=True)

class Paddle(models.Model):
    game = models.ForeignKey(Game, related_name='paddles', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    position = models.IntegerField(default=50)  # Y position on the screen

class Ball(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    position_x = models.IntegerField(default=50)
    position_y = models.IntegerField(default=50)
    velocity_x = models.IntegerField(default=1)
    velocity_y = models.IntegerField(default=1)
