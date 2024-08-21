import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
import random
import uuid

waiting_players = []

class PongGameConsumer(AsyncWebsocketConsumer):
    ball_position = {'x': 50, 'y': 50}
    ball_velocity = {'vx': 1, 'vy': 1}
    speed_multiplier = 0.5  # Default speed multiplier
    # score = {'player1': 0, 'player2': 0}
    paddle_positions = {'player1': 50, 'player2': 50}
    room_group_name = None  # We'll assign this dynamically based on session
    
    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # self.ball_position = {'x': 50, 'y': 50}
            # self.ball_velocity = {'vx': 2, 'vy': 1}
            self.score = {'player1': 0, 'player2': 0}
            # self.paddle_positions = {'player1': 50, 'player2': 50}
            # self.room_group_name = None  # Dynamically assigned based on session

    async def connect(self):
        await self.accept()  # Accept all incoming connections
        
        # Add this connection to the queue
        waiting_players.append(self)
        print(f"Player added to queue. Total players: {len(waiting_players)}")
        await self.send(json.dumps({'type': 'setup', 'player_number': 'player' + str(len(waiting_players))}))
        # Check if we have enough players to start a new game
        if len(waiting_players) >= 2:
            player1 = waiting_players.pop(0)
            player2 = waiting_players.pop(0)
            player1.player_number = 'player1'
            player2.player_number = 'player2'
            # Create a unique room name
            game_id = str(uuid.uuid4())
            room_group_name = f'pong_room_{game_id}'
            player1.room_group_name = room_group_name
            player2.room_group_name = room_group_name
            print("2 players found. groupname: ", room_group_name)

            # Add both players to the same group
            await self.channel_layer.group_add(room_group_name, player1.channel_name)
            await self.channel_layer.group_add(room_group_name, player2.channel_name)

            # Send setup information to both players
            # await player1.send(json.dumps({'type': 'setup', 'player_number': 'player1', 'room_group_name': room_group_name}))
            # print("Sent setup to player 1")
            # await player2.send(json.dumps({'type': 'setup', 'player_number': 'player2', 'room_group_name': room_group_name}))
            # print("Sent setup to player 2")

            # Notify players that the game is starting
            await self.channel_layer.group_send(
                room_group_name,
                {'type': 'notify', 'message': 'Game is starting!'}
            )
            await self.start_game()

    async def disconnect(self, close_code):
        # Remove this player from the queue if they're still waiting
        if self in waiting_players:
            waiting_players.remove(self)
        
        # Discard from group if already in a game
        if self.room_group_name:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            PongGameConsumer.player_count -= 1


    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        if action == 'move_paddle' and self.room_group_name:
            position = float(data.get('position'))
            print(f"Move paddle request from {self.player_number} with position {position}")
            await self.move_paddle(self.player_number, position)


    async def move_paddle(self, player_number, position):
        print(f"Received move_paddle request from {player_number} with position {position}")
        # Assuming the game field height is 100 units
        paddle_height = 15  # Paddle height might need to be factored into position calculations
        min_position = 1
        max_position = 100 - paddle_height  # Ensure paddle stays within the game field

        new_position = max(min_position, min(position, max_position))
        self.paddle_positions[player_number] = new_position
        print(f"Updated paddle positions: Player 1: {self.paddle_positions['player1']}, Player 2: {self.paddle_positions['player2']}")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_paddle_position',
                'paddle_positions': self.paddle_positions
            }
        )


    
    async def send_paddle_position(self, event):
        print(f"Sending paddle position update: {event['paddle_positions']}")
        print(self.room_group_name)
        paddle_position = event['paddle_positions']
        await self.send(text_data=json.dumps({
            'paddle_positions': paddle_position,
        }))

    async def start_game(self):
        # Game starting logic here
        self.game_loop_task = asyncio.create_task(self.game_loop())

    async def game_loop(self):
        # Game loop logic here
        while True:
            self.update_ball_position()
            await asyncio.sleep(0.016)  # 60 FPS
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'ball_movement',
                    'ball_position': self.ball_position,
                    'score': self.score,
                    'paddle_positions': self.paddle_positions
                }
            )
    
    async def notify(self, event):
        """
        Handle 'notify' events to send a message to the WebSocket.
        This method is triggered by 'group_send' with a type of 'notify'.
        """
        # Send the notification message to WebSocket
        await self.send(json.dumps({
            'type': 'notify',
            'message': event['message']
        }))

    def update_ball_position(self):
        # Calculate new potential positions
        new_x = self.ball_position['x'] + self.ball_velocity['vx'] * self.speed_multiplier
        new_y = self.ball_position['y'] + self.ball_velocity['vy'] * self.speed_multiplier

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
        # Reset ball position to center
        self.ball_position = {'x': 50, 'y': 50}
        # Apply the speed_multiplier to the reset velocities
        base_velocity_x = random.choice([-2, 2])
        base_velocity_y = random.choice([-1, 1])
        self.ball_velocity = {
            'vx': base_velocity_x * self.speed_multiplier,
            'vy': base_velocity_y * self.speed_multiplier
        }


    async def ball_movement(self, event):
        ball_position = event['ball_position']
        score = event['score']
        await self.send(text_data=json.dumps({
            'ball_position': ball_position,
            'score': score,
            'paddle_positions': self.paddle_positions
        }))