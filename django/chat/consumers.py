import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer): #inherits from AsyncWebsocketConsumer
# The methods connect, disconnect, and receive are predefined methods in the AsyncWebsocketConsumer class in Django Channels,
    async def connect(self):
        await self.accept()

    async def disconnect(self , close_code):
        await self.channel_layer.group_discard(
            self.indivialRoom, 
            self.channel_layer 
        )
        await self.channel_layer.group_discard(
            self.allUsersRoom, 
            self.channel_layer 
        )

    async def receive(self, text_data): # receiving what was typed and sent by ownself. script, user use chatSocket.send. then its own server is receiving its own message and processed it.
        text_data_json = json.loads(text_data)
        
        if text_data_json['type'] == 'createIndivialRoom':
            self.indivialRoom = text_data_json['userID']
            self.username = text_data_json['username']
            self.allUsersRoom = "allUsers"
            await self.channel_layer.group_add(
                self.indivialRoom,
                self.channel_name
            )
            await self.channel_layer.group_add(
                self.allUsersRoom,
                self.channel_name
            )
        
        if text_data_json['type'] == 'getStatusFromAllUsers': #triggers sendMessage method to everyone
            await self.channel_layer.group_send(
                self.allUsersRoom, {
                    "type": "sendMessage",
                    "purpose": "requestStatus",
                    "message": "online",
                    "userID": self.indivialRoom,
                    "userName": self.username,
                }
            )
            
        if text_data_json['type'] == 'replyPing': #triggers sendMessage method to everyone
            recipient_id = text_data_json["recipient_id"]
            await self.channel_layer.group_send(
                recipient_id, {
                    "type": "sendMessage",
                    "purpose": "updateStatus",
                    "message": "online",
                    "userID": self.indivialRoom,
                    "userName": self.username,
                }
            )

        if text_data_json['type'] == 'sendDirectMessage':
            message = text_data_json["message"]
            recipient_id = text_data_json["recipient_id"]
            await self.channel_layer.group_send( #triggers sendMessage method to everyone less the reciever (which is the sender itself)
                recipient_id, {
                    "type": "sendMessage",
                    "purpose": "directMessage",
                    "message": message,
                    "userID": self.indivialRoom,
                    "userName": self.username,
                }
            )

        if text_data_json['type'] == 'sendInviteInfo':
            message = text_data_json["message"]
            recipient_id = text_data_json["recipient_id"]
            await self.channel_layer.group_send( #triggers sendMessage method to everyone less the reciever (which is the sender itself)
                recipient_id, {
                    "type": "sendMessage",
                    "purpose": message,
                    "message": message,
                    "userID": self.indivialRoom,
                    "userName": self.username,
                }
            )
            
        if text_data_json['type'] == 'sendSystemMessage':
            message = text_data_json["message"]
            recipient_id = text_data_json["recipient_id"]
            await self.channel_layer.group_send( #triggers sendMessage method to everyone less the reciever (which is the sender itself)
                recipient_id, {
                    "type": "sendMessage",
                    "purpose": "directMessage",
                    "message": message,
                    "userID": "0",
                    "userName": "pong-bot",
                }
            )

    async def sendMessage(self , event) :
        purpose = event["purpose"]
        message = event["message"]
        senderID = event["userID"]
        senderName = event["userName"]
        await self.send(text_data = json.dumps({"purpose":purpose, "message":message ,"senderID":senderID, "senderName": senderName})) # send is a method id AsyncWebsocketConsumer class
      
