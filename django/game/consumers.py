import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
import random
import datetime

class PongGameConsumer(AsyncWebsocketConsumer):
    ball_position = {'x': 50, 'y': 50}
    ball_velocity = {'vx': 2, 'vy': 1}
    score = {'player1': 0, 'player2': 0}
    paddle_positions = {'player1': 50, 'player2': 50}
    room_group_name = 'pong_room'
    player_count = 0
    player_mapping = {}
    ai = True
    last_ai_update = None

    async def connect(self):
        await self.accept()
        PongGameConsumer.player_count += 1
        player_number = 'player1' if PongGameConsumer.player_count % 2 != 0 else 'player2'
        self.player_mapping[self.channel_name] = player_number

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.send(json.dumps({
            'type': 'setup',
            'player_number': player_number
        }))

        if PongGameConsumer.player_count == 1:  # If only one player, the second is AI
            self.player_mapping['player2'] = 'player2'
            PongGameConsumer.player_count += 1
            self.ai = True

        if PongGameConsumer.player_count % 2 == 0:  # Start game when two players are connected
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'notify', 'message': 'Game is starting!'}
            )
            await self.start_game()

    async def move_ai_paddle(self):
        print('AI Paddle task started')
        try:
            while self.ai:
                print('Start of loop iteration')
                current_time = datetime.datetime.now()
                print('Current time:', current_time)
                print('Last AI update:', self.last_ai_update)
                if self.last_ai_update:
                    time_difference = current_time - self.last_ai_update
                else:
                    time_difference = datetime.timedelta(seconds=100)
                print('Time difference:', time_difference.total_seconds())

                # Check if at least one second has passed
                if not self.last_ai_update or time_difference.total_seconds() >= 0.3:
                    print('Getting AI paddle position')
                    ai_paddle_y = self.paddle_positions['player2']
                    ball_y = self.ball_position['y']
                    # Update the last AI update time
                    self.last_ai_update = current_time

                print(f'AI paddle Y: {ai_paddle_y}, Ball Y: {ball_y}')

                if ball_y > ai_paddle_y + 10:  # +2 to prevent jittering
                    ai_paddle_y = ai_paddle_y + 5  # Move down
                elif ball_y < ai_paddle_y - 10:
                    ai_paddle_y = ai_paddle_y - 5  # Move up

                # Update the AI paddle position
                print('New AI Paddle Y:', ai_paddle_y)
                await self.move_paddle('player2', ai_paddle_y)

                print('End of loop iteration')
                await asyncio.sleep(0.1)

        except Exception as e:
            print(f'Error in move_ai_paddle: {str(e)}')
            import traceback
            print(traceback.format_exc())
        
        print('AI Paddle task ended')

    async def disconnect(self, close_code):
        player_number = self.player_mapping.get(self.channel_name)
        if player_number:
            PongGameConsumer.player_count -= 1
            del self.player_mapping[self.channel_name]
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        if action == 'move_paddle':
            position = float(data.get('position'))
            player_number = self.player_mapping.get(self.channel_name)
            await self.move_paddle(player_number, position)

    async def move_paddle(self, player_number, position):
        print('Player number', player_number, 'Paddle position:', position)
        # Paddle moving logic here
        min_position = 1
        max_position = 85  # Adjusting for paddle height
        new_position = max(min_position, min(position, max_position))
        self.paddle_positions[player_number] = new_position
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_paddle_position',
                'paddle_positions': self.paddle_positions
            }
        )
    
    async def send_paddle_position(self, event):
        paddle_position = event['paddle_positions']
        await self.send(text_data=json.dumps({
            'paddle_positions': paddle_position,
        }))

    async def start_game(self):
        # Game starting logic here
        self.game_loop_task = asyncio.create_task(self.game_loop())
        if self.ai:
            self.ai_task = asyncio.create_task(self.move_ai_paddle())

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
