import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
import random
import uuid
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from time import sleep

waiting_players = []
total_players = 0
active_connections = {}

class PongGameConsumer(AsyncWebsocketConsumer):
    ball_position = {'x': 50, 'y': 50}
    ball_velocity = {'vx': 1, 'vy': 1}
    speed_multiplier = 1  # Default speed multiplier
    # score = {'player1': 0, 'player2': 0}
    paddle_positions = [{'player1': 50, 'player2': 50}, {'player1': 50, 'player2': 50}]
    room_group_name = None  # We'll assign this dynamically based on session
    active_games = 0
    
    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # self.ball_position = {'x': 50, 'y': 50}
            # self.ball_velocity = {'vx': 2, 'vy': 1}
            self.score = {'player1': 0, 'player2': 0}
            # self.paddle_positions = {'player1': 50, 'player2': 50}
            # self.room_group_name = None  # Dynamically assigned based on session

    async def connect(self):
        await self.accept()  # Accept the WebSocket connection
        global total_players
        print("Active connections", active_connections, "total players", total_players)
        # Retrieve the token from query params or headers
        token = self.scope['query_string'].decode().split('=')[1]  # Assuming token is passed as a query parameter
        print(f"Token: {token}")
        # Validate and decode the JWT
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']  # Assuming the payload has 'user_id'
            print(f"User ID: {user_id}")
        except TokenError as e:
            await self.send(json.dumps({'error': 'Invalid token', 'details': str(e)}))
            await self.close()
            return

        # Check if the user is already connected
        if user_id in active_connections:
            # await active_connections[user_id].close()  # Close the old connection
            await self.send(json.dumps({'type': 'notify', 'message': 'You are already connected.'}))
            await self.close()
            print(f"Closed old connection for user {user_id}")
            return

        # Register new connection
        active_connections[user_id] = self
        print(f"New connection registered for user {user_id}")

        # Add to game queue or perform other actions
        if total_players >= 4:
            await self.send(json.dumps({'type': 'notify', 'message': 'Game is full. Please try again later.'}))
            if user_id in active_connections:
                del active_connections[user_id]
            await self.close()
            return

        # TODO check if the player is already in the queue
        # print("Player connected", self, "waiting players", waiting_players)
        print("Player connected", self)
        
        if self in waiting_players:
            print("Player already in queue")
            await self.send(json.dumps({'type': 'notify', 'message': 'You are already in the queue.'}))
            await self.close()
            return

        waiting_players.append(self)
        # print("waiting players", waiting_players)
        total_players += 1
        print(f"Player added to queue. Total players: {total_players}")
        # print(f"Player added to queue. Total players: {total_players}")
        
        await self.send(json.dumps({'type': 'setup', 'player_number': 'player' + str(len(waiting_players))}))
        
        # Check if we have enough players to start a new game
        if len(waiting_players) >= 4:  # Start the game when there are at least 4 players
            # Dequeue four players
            players = [waiting_players.pop(0) for _ in range(4)]
            
            # Assign player numbers and create a unique room name
            game_id1 = str(uuid.uuid4())
            room_group_name1 = f'pong_room_{game_id1}'
            game_id2 = str(uuid.uuid4())
            room_group_name2 = f'pong_room_{game_id2}'
            
            for i, player in enumerate(players):
                
                if i % 2 == 0:
                    player.player_number = 'player1'
                else:
                    player.player_number = 'player2'
                if i < 2:
                    player.room_group_name = room_group_name1
                    player.paddle_positions = self.paddle_positions[0]
                else:
                    player.paddle_positions = self.paddle_positions[1]
                    player.room_group_name = room_group_name2
                
                # Add player to the group
                await self.channel_layer.group_add(player.room_group_name, player.channel_name)
                print(f"Sent setup to {player.player_number} in group {player.room_group_name}")
                
                # Send setup information to the player
                await player.send(json.dumps({
                    'type': 'setup', 
                    'player_number': player.player_number, 
                    'room_group_name': player.room_group_name
                }))
            
            # Notify all players in the room that the game is starting
            await self.channel_layer.group_send(
                room_group_name1, 
                {'type': 'notify', 'message': 'Game is starting!'}
            )
            await self.channel_layer.group_send(
                room_group_name2, 
                {'type': 'notify', 'message': 'Game is starting!'}
            )
            
            # Start the game
            print("players", players)
            await players[0].start_game()  # You can call start_game on any of the player instances
            await players[2].start_game()

    async def disconnect(self, close_code):
        # Remove this player from the queue if they're still waiting
        if self in waiting_players:
            waiting_players.remove(self)
        # Discard from group if already in a game
        if self.room_group_name:
            # sleep(1)  # Wait for a second before discarding the player from the group
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)



    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        if action == 'move_paddle' and self.room_group_name:
            position = float(data.get('position'))
            # print(f"Move paddle request from {self.player_number} with position {position}")
            await self.move_paddle(self.player_number, position)


    async def move_paddle(self, player_number, position):
        # print(f"Received move_paddle request from {player_number} with position {position}")
        # Assuming the game field height is 100 units
        paddle_height = 15  # Paddle height might need to be factored into position calculations
        min_position = 1
        max_position = 100 - paddle_height  # Ensure paddle stays within the game field

        new_position = max(min_position, min(position, max_position))
        self.paddle_positions[player_number] = new_position
        # print(f"Updated paddle positions: Player 1: {self.paddle_positions['player1']}, Player 2: {self.paddle_positions['player2']}")
        # print("Room group name", self.room_group_name)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_paddle_position',
                'paddle_positions': self.paddle_positions
            }
        )


    
    async def send_paddle_position(self, event):
        # print(f"Sending paddle position update: {event['paddle_positions']}")
        # print(self.room_group_name)
        paddle_position = event['paddle_positions']
        await self.send(text_data=json.dumps({
            'paddle_positions': paddle_position,
        }))

    async def start_game(self):
        # Increment the counter when a game starts
        PongGameConsumer.active_games += 1
        self.game_loop_task = asyncio.create_task(self.game_loop())

    async def end_game(self, winner):
        # Send a game over message to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'notify',
                'message': f'Game over! {winner} wins!'
            }
        )
        # Close the connection
        sleep(1)  # Wait for a second before closing the connection
        await self.close()

        # Decrement the counter when a game ends
        PongGameConsumer.active_games -= 1
        print("total players", total_players)
        # Check if it's the last game to end
        if PongGameConsumer.active_games == 0:
            await self.cleanup_connections()

    async def cleanup_connections(self):
        # Clear all active connections
        global total_players
        active_connections.clear()
        total_players = 0
        print("Cleared all active connections after the last game ended.", active_connections, total_players)

    async def game_loop(self):
        # Game loop logic here
        while True:
            await self.update_ball_position()
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

    async def update_ball_position(self):
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
        await self.handle_collisions(new_x, new_y)

    async def handle_collisions(self, new_x, new_y):
        # Handle paddle collisions
        if (new_x <= 10 and self.paddle_positions['player1'] <= new_y <= self.paddle_positions['player1'] + 15) or \
        (new_x >= 90 and self.paddle_positions['player2'] <= new_y <= self.paddle_positions['player2'] + 15):
            self.ball_velocity['vx'] *= -1

        # Check for scoring
        if new_x <= 0:
            self.score['player2'] += 1
            if self.score['player2'] >= 5:
                await self.end_game(winner='player2')  # Correctly await the coroutine
                return
            self.reset_ball()
        elif new_x >= 100:
            self.score['player1'] += 1
            if self.score['player1'] >= 5:
                await self.end_game(winner='player1')  # Correctly await the coroutine
                return
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
