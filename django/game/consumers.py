import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
import random
import uuid
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from urllib.parse import parse_qs
from django.contrib.auth.models import User
from channels.db import database_sync_to_async
from authentication.models import UserProfile
from datetime import datetime
import websockets

class BotPlayer:
    def __init__(self):
        self.user_id = 'ai'
        self.player_number = 'player2'
        self.game_room = None

    def predict_ball_position(self, ball_x, ball_y, ball_vx, ball_vy):
        # while ball is not in ai score area
        while (ball_x < 90):
            ball_x += ball_vx
            ball_y += ball_vy
            if ball_y < 0 or ball_y > 100:
                ball_vy *= -1
                ball_y = max(0, min(ball_y, 100))
            if ball_x <= 10: #assume player always hits the ball
                ball_vx *= -1
                ball_x = 10
        # variable difficulty based on score difference
        score_diff = self.game_room.score['player1'] - self.game_room.score['player2']
        ball_y += random.randrange(score_diff - 2, -(score_diff - 2), 1)
        return ball_x, ball_y

    async def move_ai_paddle(self):
        while self.game_room:
            ball_x = self.game_room.ball_position['x']
            ball_y = self.game_room.ball_position['y']
            ball_vx = self.game_room.ball_velocity['vx']
            ball_vy = self.game_room.ball_velocity['vy']
            pred_x, pred_y = self.predict_ball_position(ball_x, ball_y, ball_vx, ball_vy)

            #calculate how far the paddle should move
            paddle_position = self.game_room.paddle_positions[self.player_number]
            distance = pred_y - paddle_position
            # calculate how many moves of 10 units are needed to reach the predicted position
            steps = distance // 10
            # cap the number of moves to 10
            n = min(abs(steps), 10)

            for i in range(n):
                await self.game_room.move_paddle(self, 'down' if steps > 0 else 'up')
                await asyncio.sleep(0.1)
            
            #update once a second, less the number of moves * 0.1s
            await asyncio.sleep(1 - n * 0.1)

class GameRoom:
    def __init__(self):
        self.room_id = uuid.uuid4().hex
        self.players = []
        self.ball_position = {'x': 50, 'y': 50}
        self.ball_velocity = {'vx': 1, 'vy': 1}
        self.score = {'player1': 0, 'player2': 0}
        self.paddle_positions = {'player1': 50, 'player2': 50}
        self.game_active = False

    async def add_player(self, player):
        if len(self.players) < 2:
            self.players.append(player)
            player.game_room = self

            # Fetch user asynchronously
            player.user = await database_sync_to_async(User.objects.get)(id=player.user_id)
            print(f'User {player.user.username} joined the game room {self.room_id}')

            if not player.user.is_authenticated:
                await player.send(json.dumps({'error': 'Unauthorized'}))
                return

            player.player_number = 'player2' if len(self.players) == 1 else 'player1'
            await player.send(json.dumps({'type': 'setup', 'player_number': player.player_number}))

            if len(self.players) == 2:
                await self.start_game()

    async def start_game(self):
        # Send a countdown before the game starts
        for i in range(3, 0, -1):
            countdown_message = {'type': 'notify', 'message': f'Game starts in {i}...'}
            print(countdown_message)
            for player in self.players:
                await player.send(json.dumps(countdown_message))
            await asyncio.sleep(1)  # Wait for 1 second between countdown messages

        self.game_active = True
        start_message = {'type': 'notify', 'message': 'Game is starting!'}
        for player in self.players:
            await player.send(json.dumps(start_message))
        asyncio.create_task(self.game_loop())

    async def game_loop(self):
        while self.game_active:
            await asyncio.sleep(0.016)  # Simulate 60 FPS game update
            self.update_ball_position()
            await self.broadcast_game_state()

    def update_ball_position(self):
        speed_multiplier = 1  # Define a speed multiplier if needed, or use class-level attribute if intended
        new_x = self.ball_position['x'] + self.ball_velocity['vx'] * speed_multiplier
        new_y = self.ball_position['y'] + self.ball_velocity['vy'] * speed_multiplier

        # Boundary check for x-coordinate
        if new_x < 0 or new_x > 100:
            self.ball_velocity['vx'] *= -1  # Reverse the horizontal velocity
            new_x = max(0, min(new_x, 100))  # Clamp the value within the boundaries

        self.ball_position['x'] = new_x

        # Boundary check for y-coordinate
        if new_y < 0 or new_y > 100:
            self.ball_velocity['vy'] *= -1  # Reverse the vertical velocity
            new_y = max(0, min(new_y, 100))  # Clamp the value within the boundaries

        self.ball_position['y'] = new_y
        self.handle_collisions()

    def handle_collisions(self):
        # Paddle collision logic
        if (5 <= self.ball_position['x'] <= 10 and self.paddle_positions['player1'] <= self.ball_position['y'] <= self.paddle_positions['player1'] + 15) or \
        (95 >= self.ball_position['x'] >= 90 and self.paddle_positions['player2'] <= self.ball_position['y'] <= self.paddle_positions['player2'] + 15):
            self.ball_velocity['vx'] *= -1
            self.ball_position['x'] = 10 if self.ball_position['x'] < 50 else 90
        # Scoring logic
        if self.ball_position['x'] <= 0:
            self.score['player2'] += 1
            self.check_score('player2')
            self.reset_ball()
        elif self.ball_position['x'] >= 100:
            self.score['player1'] += 1
            self.check_score('player1')
            self.reset_ball()

    async def end_game(self, winner_identifier):
        # Find the player object that matches the winner identifier
        winner = next((player for player in self.players if player.player_number == winner_identifier), None)
        loser = next((player for player in self.players if player.player_number != winner_identifier), None)
        if winner is None:
            print("Error: Winner not found in the game room.")
            return
        

        self.game_active = False

        # Notify RoomManager if this room was part of a tournament
        if self in room_manager.tournament_rooms:
            await winner.send(json.dumps({'type': 'notify', 'message': 'You have won the match!, waiting for other matches to finish...'}))
            await loser.send(json.dumps({'type': 'notify', 'message': 'You have been eliminated, waiting for other matches to finish...'}))
            await room_manager.handle_semi_final_end(self, winner)
        elif self == room_manager.final_room:
            await room_manager.handle_final_end(winner)
        elif self == room_manager.third_place_room:
            await room_manager.handle_third_place_end(winner)
        else:
            # this is for 1v1 mode
            print(f'Game over! {winner.user.username} wins!')
            await winner.send(json.dumps({'type': 'game_over', 'message': 'You win!'}))
            await loser.send(json.dumps({'type': 'game_over', 'message': 'You lose!'}))
            await room_manager.handle_one_on_one_end(winner, loser)
        print("active connections", RoomManager.active_connections)

    def check_score(self, player):
        if self.score[player] >= 5:  # Assuming 5 points needed to win
            asyncio.create_task(self.end_game(player))
            self.reset_ball()

    async def broadcast_game_state(self):
        for player in self.players:
            try:
                await player.send(json.dumps({
                    'ball_position': self.ball_position,
                    'score': self.score,
                    'paddle_positions': self.paddle_positions
                }))
            except websockets.exceptions.ConnectionClosed:
                print(f'Player {player.user.username} is disconnected')
                continue  # Skip sending updates to disconnected clients

    async def remove_player(self, player):
        self.players.remove(player)
        if not self.players:
            self.game_active = False
    
    def reset_ball(self):
        # Reset ball position to center
        self.ball_position = {'x': 50, 'y': 50}
        base_velocity_x = random.choice([-1, 1])
        base_velocity_y = random.choice([-1, 1])
        self.ball_velocity = {
            'vx': base_velocity_x,
            'vy': base_velocity_y,
        }
    
    async def move_paddle(self, player, direction):
        # Ensure position is within the game boundaries
        max_height = 100  # assuming the game field height is 100 units
        paddle_height = 15  # assuming each paddle is 15 units tall
        min_position = 1
        max_position = max_height - paddle_height
        per_move = 10  # assuming each move is 10 units

        # Calculate the new position based on the direction
        position = self.paddle_positions[player.player_number]
        if direction == 'up':
            position -= per_move
        elif direction == 'down':
            position += per_move
        else:
            print(f'direction {direction} is not recognized')
            return

        # Clamp the position to stay within the boundaries
        new_position = max(min_position, min(position, max_position))
        # Determine which player is moving and update their paddle position
        if player.player_number == 'player1':
            self.paddle_positions['player1'] = new_position
        elif player.player_number == 'player2':
            self.paddle_positions['player2'] = new_position

class RoomManager:
    active_connections = {}
    def __init__(self):
        self.rooms = {}
        self.waiting_players_one_on_one = []
        self.waiting_players_tournament = []
        self.tournament_rooms = []
        self.ai_rooms = {}
        self.final_room = None
        self.third_place_room = None  # Room for third place match
        self.semi_final_losers = []  # List to keep track of the losers of the semi-finals

    async def queue_player(self, player, game_mode):
        print(f'Player {player.user_id} queued for {game_mode}')
        if game_mode == 'one_on_one':
            if self.waiting_players_one_on_one:
                room = self.create_room()
                await room.add_player(player)
                await room.add_player(self.waiting_players_one_on_one.pop(0))
            else:
                self.waiting_players_one_on_one.append(player)
                await player.send(json.dumps({'type': 'notify', 'message': 'Waiting for an opponent...'}))

        elif game_mode == 'tournament':
            self.waiting_players_tournament.append(player)
            for player in self.waiting_players_tournament:
                await player.send(json.dumps({'type': 'notify', 'message': f'Waiting for {4 - len(self.waiting_players_tournament)} more players...'}))
            if len(self.waiting_players_tournament) == 4:  # Start tournament when 4 players are ready
                # Create two rooms for semi-finals
                print('Tournament started!')
                semi_final_1 = self.create_room()
                semi_final_2 = self.create_room()
                self.tournament_rooms.append(semi_final_1)
                self.tournament_rooms.append(semi_final_2)
                
                # Add players to semi-final rooms
                await semi_final_1.add_player(self.waiting_players_tournament.pop(0))
                await semi_final_1.add_player(self.waiting_players_tournament.pop(0))
                await semi_final_2.add_player(self.waiting_players_tournament.pop(0))
                await semi_final_2.add_player(self.waiting_players_tournament.pop(0))
        
        elif game_mode == 'ai':
            ai_room = self.create_ai_room()
            await ai_room.add_player_vs_ai(player)

    def create_ai_room(self):
        room = AIGameRoom()
        self.ai_rooms[room.room_id] = room
        return room

    def create_room(self):
        room = GameRoom()
        self.rooms[room.room_id] = room
        return room
    
    async def handle_semi_final_end(self, room, winner):
        # Identify the loser in the semi-final room
        loser = next((player for player in room.players if player != winner), None)
        self.semi_final_losers.append(loser)

        # Prepare the final room if not already done
        if not self.final_room:
            self.final_room = self.create_room()

        # Add the winner to the final room
        await self.final_room.add_player(winner)
        
        # Prepare the third place match room
        if len(self.semi_final_losers) == 2:
            if not self.third_place_room:
                self.third_place_room = self.create_room()
            third_place_player1 = self.semi_final_losers.pop(0)
            third_place_player2 = self.semi_final_losers.pop(0)
            for i in range(3):
                await third_place_player1.send(json.dumps({'type': 'notify', 'message': f'You have been eliminated, starting third-place match in {3-i}...'}))
                await third_place_player2.send(json.dumps({'type': 'notify', 'message': f'You have been eliminated, starting third-place match in {3-i}...'}))
                await asyncio.sleep(1)
            await self.third_place_room.add_player(third_place_player1)
            await self.third_place_room.add_player(third_place_player2)


    async def handle_final_end(self, winner):
        loser = next((player for player in self.final_room.players if player != winner), None)
        
        # Update match histories
        date = datetime.now().isoformat()
        winner_details = {'result': 'lost', 'position': 1, 'mode' : 'tournament', 'date' : date}
        loser_details = {'result': 'lost', 'position': 2, 'mode' : 'tournament', 'date' : date}
        await update_match_history(winner.user, winner_details)
        await update_match_history(loser.user, loser_details)

        # Send notifications
        date = datetime.now().isoformat()
        print("DATE", date)
        winner_msg = {'type': 'notify', 'message': 'Congratulations! You won the tournament!', 'mode' : 'tournament', 'date' : date}
        await winner.send(json.dumps(winner_msg))
        loser_msg = {'type': 'notify', 'message': 'Great effort! You finished 2nd in the tournament!', 'mode' : 'tournament', 'date' : date}
        await loser.send(json.dumps(loser_msg))

        self.final_room = None
        self.tournament_rooms = []
        if winner.user_id in RoomManager.active_connections:
            RoomManager.active_connections.pop(winner.user_id, None)
            try:
                await winner.close()
                print("winner closed")
            except Exception as e:
                print(f"Failed to close connection: {e}")
        if loser.user_id in RoomManager.active_connections:
            RoomManager.active_connections.pop(loser.user_id, None)
            try:
                await loser.close()
                print("loser closed")
            except Exception as e:
                print(f"Failed to close connection: {e}")

    async def handle_third_place_end(self, winner):
        loser = next((player for player in self.third_place_room.players if player != winner), None)
        
        # Update match histories
        date = datetime.now().isoformat()
        winner_details = {'result': 'lost', 'position': 3,  'mode' : 'tournament', 'date' : date}
        loser_details = {'result': 'lost', 'position': 4, 'mode' : 'tournament', 'date' : date}
        await update_match_history(winner.user, winner_details)
        await update_match_history(loser.user, loser_details)

        # Send notifications
        winner_msg = {'type': 'notify', 'message': 'Congratulations! You finished 3rd in the tournament!'}
        await winner.send(json.dumps(winner_msg))
        loser_msg = {'type': 'notify', 'message': 'Great effort! You finished 4th in the tournament!'}
        await loser.send(json.dumps(loser_msg))

        self.third_place_room = None
        RoomManager.active_connections.pop(winner.user_id, None)
        RoomManager.active_connections.pop(loser.user_id, None)
        if winner.user_id in RoomManager.active_connections:
            RoomManager.active_connections.pop(winner.user_id, None)
            try:
                await winner.close()
                print("winner closed")
            except Exception as e:
                print(f"Failed to close connection: {e}")
        if loser.user_id in RoomManager.active_connections:
            RoomManager.active_connections.pop(loser.user_id, None)
            try:
                await loser.close()
                print("loser closed")
            except Exception as e:
                print(f"Failed to close connection: {e}")

    async def handle_one_on_one_end(self, winner, loser):
        print("winner", winner.user.username)
        print("loser", loser.user.username)
        # Update match histories
        date = datetime.now().isoformat()
        winner_details = {'result': 'won', 'mode' : '1v1', 'date' : date, 'winner' : winner.user.username, 'loser' : loser.user.username}
        loser_details = {'result': 'lost', 'mode' : '1v1', 'date' : date, 'winner' : winner.user.username, 'loser' : loser.user.username}
        await update_match_history(winner.user, winner_details)
        await update_match_history(loser.user, loser_details)
        if winner.user_id in RoomManager.active_connections:
            RoomManager.active_connections.pop(winner.user_id, None)
            try:
                await winner.close()
                print("winner closed")
            except Exception as e:
                print(f"Failed to close connection: {e}")
        if loser.user_id in RoomManager.active_connections:
            RoomManager.active_connections.pop(loser.user_id, None)
            try:
                await loser.close()
                print("loser closed")
            except Exception as e:
                print(f"Failed to close connection: {e}")

    def reset_game_state(self):
        self.ball_position = {'x': 50, 'y': 50}
        self.ball_velocity = {'vx': 1, 'vy': 1}
        self.score = {'player1': 0, 'player2': 0}
        self.paddle_positions = {'player1': 50, 'player2': 50}

room_manager = RoomManager()

class PongGameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        
        # Extract query parameters
        query_string = self.scope['query_string'].decode('utf-8')
        params = parse_qs(query_string)
        token = params.get('token', [None])[0]
        mode = params.get('mode', [None])[0]
        print(f'mode: {mode}')
        try:
            access_token = AccessToken(token)
            self.user_id = access_token['user_id']
        except TokenError as e:
            print(f'Invalid token: {e}')
            await self.send(json.dumps({'error': 'Invalid token', 'details': str(e)}))
            await self.close()
            return
        print("checking mode")
        # Process different game modes
        if RoomManager.active_connections.get(self.user_id):
            print(f'User {self.user_id} is already in a game')
            await self.send(json.dumps({'type': 'notify', 'message': 'You are already in a game'}))
            await self.close()
            return
        RoomManager.active_connections[self.user_id] = self
        if mode == 'tournament':
            await self.handle_tournament_mode(self.user_id)
        elif mode == 'one_on_one':
            await self.handle_one_on_one_mode(self.user_id)
        elif mode == 'ai':
            print("ai mode")
            await self.handle_ai_mode(self.user_id)
        else:
            await self.send(json.dumps({'error': 'Invalid game mode'}))
            await self.close()

    async def handle_tournament_mode(self, user_id):
        # Logic to handle tournament mode
        await room_manager.queue_player(self, game_mode='tournament')

    async def handle_one_on_one_mode(self, user_id):
        # Logic to handle one on one mode
        await room_manager.queue_player(self, game_mode='one_on_one')

    async def handle_ai_mode(self, user_id):
        # Logic to handle AI mode
        await room_manager.queue_player(self, game_mode='ai')

    async def disconnect(self, close_code):
        if hasattr(self, 'game_room'):
            await self.game_room.remove_player(self)
            if not self.game_room.players:
                room_manager.rooms.pop(self.game_room.room_id, None)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if self.game_room and 'action' in data:
            if data['action'] == 'move_paddle':
                await self.game_room.move_paddle(self, data['direction'])

    async def send_paddle_move(self, position):
        if self.game_room:
            new_position = self.game_room.calculate_paddle_position(self, position)
            await self.game_room.update_paddle_position(self, new_position)

    async def send(self, message):
        """ Override the base send to handle sending JSON messages directly """
        if isinstance(message, dict):
            message = json.dumps(message)
        await super().send(message)

@database_sync_to_async
def update_match_history(user, match_details):
    profile = UserProfile.objects.get(user=user)
    profile.match_history.append(match_details)
    profile.save()

class AIGameRoom(GameRoom):
    def __init__(self):
        super().__init__()
        self.ai_player = None

    async def add_player_vs_ai(self, player):
        self.players.append(player)
        player.game_room = self

        # Fetch user asynchronously
        player.user = await database_sync_to_async(User.objects.get)(id=player.user_id)

        if not player.user.is_authenticated:
            await player.send(json.dumps({'error': 'Unauthorized'}))
            return
        
        player.player_number = 'player1'
        await player.send(json.dumps({'type': 'setup', 'player_number': player.player_number}))

        # Add AI player
        self.ai_player = BotPlayer()
        self.ai_player.game_room = self
        self.ai_player.player_number = 'player2'
        print("starting ai game")
        await self.start_ai_game()

    async def end_game(self, winner_identifier):
        self.game_active = False
        
        message = 'You win!' if winner_identifier == 'player1' else 'You lose!'
        await self.players[0].send(json.dumps({'type': 'game_over', 'message': message}))

        date = datetime.now().isoformat()
        result = 'won' if winner_identifier == 'player1' else 'lost'
        winner = self.players[0].user.username if winner_identifier == 'player1' else 'CPU'
        loser = 'CPU' if winner_identifier == 'player1' else self.players[0].user.username
        player_details = {'result': result, 'mode': 'ai', 'date': date, 'winner': winner, 'loser': loser}
        await update_match_history(self.players[0].user, player_details)
        if self.players[0].user_id in RoomManager.active_connections:
            RoomManager.active_connections.pop(self.players[0].user_id, None)
            try:
                await self.players[0].close()
            except Exception as e:
                print(f"Failed to close connection: {e}")

    def check_score(self, player):
        if self.score[player] >= 5:
            asyncio.create_task(self.end_game(player))

    async def start_ai_game(self):
        # Send a countdown before the game starts
        for i in range(3, 0, -1):
            countdown_message = {'type': 'notify', 'message': f'Game starts in {i}...'}
            print(countdown_message)
            await self.players[0].send(json.dumps(countdown_message))
            await asyncio.sleep(1)
        
        self.game_active = True
        start_message = {'type': 'notify', 'message': 'Game is starting!'}
        await self.players[0].send(json.dumps(start_message))
        asyncio.create_task(self.game_loop())
        asyncio.create_task(self.ai_player.move_ai_paddle())