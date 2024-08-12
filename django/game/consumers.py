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
        # Assuming the paddle height is 15% of the game field
        paddle_height_percent = 15  # Half of the paddle's height in percentage
        min_position = 1  # Minimum boundary considering half paddle height
        max_position = 99 - paddle_height_percent  # Maximum boundary considering half paddle height

        # Clamp the position between min_position and max_position
        new_position = max(min_position, min(position, max_position))
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
        # Calculate new potential positions
        new_x = self.ball_position['x'] + self.ball_velocity['vx']
        new_y = self.ball_position['y'] + self.ball_velocity['vy']

        # Now apply wrapping for x-coordinate
        self.ball_position['x'] = new_x % 100

        # Check for boundary collisions before updating y-coordinate
        if new_y < 0 or new_y > 100:
            self.ball_velocity['vy'] *= -1
            # Ensure new_y stays within the game field
            new_y = max(0, min(new_y, 100))

        # Update y position after handling collisions
        self.ball_position['y'] = new_y
        self.handle_collisions(new_x, new_y)

    def handle_collisions(self, new_x, new_y):
        # Handle paddle collisions
        if (new_x <= 10 and self.paddle_positions['player1'] <= new_y <= self.paddle_positions['player1'] + 15) or \
        (new_x >= 90 and self.paddle_positions['player2'] <= new_y <= self.paddle_positions['player2'] + 15):
            self.ball_velocity['vx'] *= -1

        # Check for scoring
        if new_x <= 0:
            self.score['player2'] += 1
            self.reset_ball()
        elif new_x >= 100:
            self.score['player1'] += 1
            self.reset_ball()

    def reset_ball(self):
        # Reset ball position to center and adjust direction
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
