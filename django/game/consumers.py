import json
import asyncio
from django.contrib.auth import get_user_model
from channels.generic.websocket import AsyncWebsocketConsumer
import random

User = get_user_model()

class PongGameConsumer(AsyncWebsocketConsumer):
    ball_position = {'x': 50, 'y': 50}  # Start position at the center
    ball_velocity = {'vx': 2, 'vy': 1}  # Initial velocity
    score = {'player1': 0, 'player2': 0}
    paddle_positions = {'player1': 50, 'player2': 50}  # Mid-point of the paddles as percentages

    async def connect(self):
        self.room_group_name = 'pong_room'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        # Start the game loop
        self.game_loop_task = asyncio.create_task(self.game_loop())

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        self.game_loop_task.cancel()  # Cancel the game loop when client disconnects

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        user_id = data.get('user_id')

        if action == 'move_paddle':
            position = float(data.get('position'))
            await self.move_paddle(user_id, position)

    async def move_paddle(self, user_id, position):
        username = f'player{user_id}'
        # Clamp the position between 0 and 100
        new_position = max(0, min(position, 100))
        self.paddle_positions[username] = new_position
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_paddle_position',
                'paddle_positions': self.paddle_positions,
                'user_id': user_id
            }
        )

    async def send_paddle_position(self, event):
        paddle_position = event['paddle_positions']
        user_id = event['user_id']
        await self.send(text_data=json.dumps({
            'paddle_positions': paddle_position,
            'user_id': user_id
        }))

    async def game_loop(self):
        while True:
            self.update_ball_position()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'ball_movement',
                    'ball_position': self.ball_position,
                    'score': self.score,
                    'paddle_positions': self.paddle_positions
                }
            )
            await asyncio.sleep(0.016)  # Frame update (~60fps)

    def update_ball_position(self):
        # Update ball position based on current velocity
        self.ball_position['x'] = (self.ball_position['x'] + self.ball_velocity['vx']) % 100
        self.ball_position['y'] = (self.ball_position['y'] + self.ball_velocity['vy']) % 100
        self.handle_collisions()

    def handle_collisions(self):
        # Reverses the y-velocity if ball hits the top or bottom boundary
        if self.ball_position['y'] <= 0 or self.ball_position['y'] >= 100:
            self.ball_velocity['vy'] *= -1

        # Handle paddle collisions
        if (self.ball_position['x'] <= 10 and self.paddle_positions['player1'] <= self.ball_position['y'] <= self.paddle_positions['player1'] + 15) or \
           (self.ball_position['x'] >= 90 and self.paddle_positions['player2'] <= self.ball_position['y'] <= self.paddle_positions['player2'] + 15):
            self.ball_velocity['vx'] *= -1

        # Check for ball passing left or right boundaries (past paddles)
        if self.ball_position['x'] <= 0:
            self.score['player2'] += 1
            self.reset_ball()
        elif self.ball_position['x'] >= 100:
            self.score['player1'] += 1
            self.reset_ball()

    def reset_ball(self):
        # Reset ball position to center and randomize the direction
        self.ball_position = {'x': 50, 'y': 50}
        self.ball_velocity = {'vx': random.choice([-2, 2]), 'vy': random.choice([-1, 1])}

    async def ball_movement(self, event):
        ball_position = event['ball_position']
        score = event['score']
        await self.send(text_data=json.dumps({
            'ball_position': ball_position,
            'score': score,
            'paddle_positions': self.paddle_positions
        }))
