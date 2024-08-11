import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer): #inherits from AsyncWebsocketConsumer
# The methods connect, disconnect, and receive are predefined methods in the AsyncWebsocketConsumer class in Django Channels,
    async def connect(self):
        await self.accept()

    async def disconnect(self , close_code):
        await self.channel_layer.group_discard(
            self.roomGroupName , 
            self.channel_layer 
        )

    async def receive(self, text_data): # receiving what was typed and sent by ownself. script, user use chatSocket.send. then its own server is receiving its own message and processed it.
        text_data_json = json.loads(text_data)
        if text_data_json['type'] == 'username':
            self.roomGroupName = text_data_json['content']
            # self.roomGroupName = "chat_user_" + str(self.username)
            await self.channel_layer.group_add(
                self.roomGroupName,
                self.channel_name
            )
        else:
            message = text_data_json["message"]
            recipient_id = text_data_json["recipient_id"]
            await self.channel_layer.group_send( #triggers sendMessage method to everyone less the reciever (which is the sender itself)
                recipient_id, {
                    "type": "sendMessage",
                    "message": message,
                    "username": self.roomGroupName,
                    "recipient_id": recipient_id,
                }
            )

    async def sendMessage(self , event) : 
        message = event["message"]
        sender = event["username"]
        await self.send(text_data = json.dumps({"message":message ,"sender":sender})) # send is a method id AsyncWebsocketConsumer class
      
