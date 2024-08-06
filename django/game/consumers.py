from channels.generic.websocket import AsyncWebsocketConsumer
import json
import asyncio
from django.contrib.auth import get_user_model
from .models import Game, Paddle, Ball
import random

User = get_user_model()

class PongGameConsumer(AsyncWebsocketConsumer):
    ball_position = {'x': 50, 'y': 50}  # Start position at the center
    ball_velocity = {'vx': 2, 'vy': 1}  # Initial velocity
    score = {'player1': 0, 'player2': 0}
    paddle_positions = {'player1': 50, 'player2': 50}  # Mid-point of the paddles

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
            position = data.get('position')
            await self.move_paddle(user_id, position)

    async def move_paddle(self, user_id, position):
        # Update paddle position
        print(f"Received paddle move: User {user_id}, Position {position}")
        user = await self.get_user_from_id(user_id)
        if user:
            # Map user_id to username or any unique identifier
            username = f'player{user_id}'  # Assuming user_id 1 maps to player1, and so on
            self.paddle_positions[username] = position
            # Broadcast the new position
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_paddle_position',
                    'paddle_position': self.paddle_positions,
                    'user_id': user_id
                }
            )

    async def send_paddle_position(self, event):
        paddle_position = event['paddle_position']
        user_id = event['user_id']
        # Send message to WebSocket
        print(f"Broadcasting position update: {event}")
        await self.send(text_data=json.dumps({
            'paddle_positions': paddle_position,
            'user_id': event['user_id']
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
                    'paddle_positions': self.paddle_positions  # Include paddle positions
                }
            )
            await asyncio.sleep(0.016)  # Frame update (~60fps)

    def update_ball_position(self):
        self.ball_position['x'] += self.ball_velocity['vx']
        self.ball_position['y'] += self.ball_velocity['vy']
        self.handle_collisions()

    def handle_collisions(self):
        # Reverses the y-velocity if ball hits the top or bottom boundary
        if self.ball_position['y'] <= 0 or self.ball_position['y'] >= 100:
            self.ball_velocity['vy'] *= -1

        # Handle paddle collisions
        if self.ball_position['x'] <= 10 and self.ball_position['y'] in range(self.paddle_positions['player1'] - 30, self.paddle_positions['player1'] + 30):
            self.ball_velocity['vx'] *= -1
        elif self.ball_position['x'] >= 90 and self.ball_position['y'] in range(self.paddle_positions['player2'] - 30, self.paddle_positions['player2'] + 30):
            self.ball_velocity['vx'] *= -1

        # Check for ball passing left or right boundaries (past paddles)
        if self.ball_position['x'] <= 0:
            self.score['player2'] += 1
            self.reset_ball()
        elif self.ball_position['x'] >= 100:
            self.score['player1'] += 1
            self.reset_ball()
        if self.ball_position['x'] <= 0:
            self.score['player2'] += 1
            self.reset_ball()
        elif self.ball_position['x'] >= 100:
            self.score['player1'] += 1
            self.reset_ball()
        print(f"Score: {self.score}")
        if self.score['player1'] >= 3 or self.score['player2'] >= 3:
            self.game_active = False  # Stop the game loop
            print("Game Over!")
            asyncio.create_task(self.game_over())  # Properly call the asynchronous game_over method

    async def game_over(self):
        if self.score['player1'] > self.score['player2']:
            winner = 'player1'
        else:
            winner = 'player2'
        message = f'Game Over! {winner} wins!'
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_message',
                'message': message
            }
        )

    async def broadcast_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'game_over',
            'message': message
        }))
        await self.close()  # Close the WebSocket connection


    def reset_ball(self):
        # Reset ball position to center and randomize start direction
        self.ball_position = {'x': 50, 'y': 50}
        self.ball_velocity = {'vx': 2 if random.choice([True, False]) else -2, 'vy': 1 if random.choice([True, False]) else -1}

    async def ball_movement(self, event):
        ball_position = event['ball_position']
        score = event['score']
        await self.send(text_data=json.dumps({
            'ball_position': ball_position,
            'score': score,
            'paddle_positions': self.paddle_positions  # Include paddle positions
        }))

    async def get_user_from_id(self, user_id):
        try:
            # Ensure user_id is an integer
            user_id = int(user_id)
            return await User.objects.aget(pk=user_id)
        except ValueError:
            # Handle case where user_id is not an integer
            print(f"Invalid user_id: {user_id}")
            return None
        except User.DoesNotExist:
            return None