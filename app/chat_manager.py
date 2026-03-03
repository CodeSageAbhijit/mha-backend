# app/chat_manager.py
from typing import Dict, Set
import socketio
from datetime import datetime
from bson import ObjectId
from app.database.mongo import chat_collection, db
from app.utils.jwt_tokens import decrypt_token
from app.utils.error_response import error_response

class ChatManager:
    def __init__(self):
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins=['*'],
            logger=True,
            engineio_logger=True
        )
        self.app = socketio.ASGIApp(
            self.sio,
            socketio_path='socket.io'  
        )
        self.active_users: Dict[str, str] = {}  # user_id: socket_id
        self.user_rooms: Dict[str, Set[str]] = {}  # user_id: set of room_ids

    async def get_or_create_room(self, user1_id: str, user2_id: str) -> str:
        """Get existing room or create new one"""
        room = await db.rooms.find_one({
            'participants': {'$all': [user1_id, user2_id]}
        })
        
        if not room:
            room = {
                'participants': [user1_id, user2_id],
                'created_at': datetime.utcnow()
            }
            result = await db.rooms.insert_one(room)
            return str(result.inserted_id)
        
        return str(room['_id'])

    async def initialize_handlers(self):
        @self.sio.event
        async def connect(sid, environ, auth):
            """Handle new connection with authentication"""
            try:
                token = auth.get('token')
                if not token:
                    await self.sio.disconnect(sid)
                    return
                
                user_data = decrypt_token(token)
                user_id = user_data.get('userId')
                
                if not user_id:
                    await self.sio.disconnect(sid)
                    return
                
                self.active_users[user_id] = sid
                self.user_rooms[user_id] = set()
                
                # Send user online status
                await self.sio.emit('user_status', {
                    'user_id': user_id,
                    'status': 'online'
                }, broadcast=True)
                
                print(f"User {user_id} connected with socket {sid}")
                
                # Send pending messages
                await self.send_pending_messages(user_id)
                
            except Exception as e:
                print(f"Connection error: {e}")
                await self.sio.disconnect(sid)

        @self.sio.event
        async def disconnect(sid):
            """Handle disconnection"""
            try:
                user_id = None
                for uid, socket_id in self.active_users.items():
                    if socket_id == sid:
                        user_id = uid
                        break
                
                if user_id:
                    del self.active_users[user_id]
                    if user_id in self.user_rooms:
                        del self.user_rooms[user_id]
                    
                    await self.sio.emit('user_status', {
                        'user_id': user_id,
                        'status': 'offline'
                    }, broadcast=True)
                    
                    print(f"User {user_id} disconnected")
            except Exception as e:
                print(f"Disconnect error: {e}")

        @self.sio.event
        async def join_room(sid, data):
            """Join a chat room"""
            try:
                room_id = data.get('room_id')
                user_id = data.get('user_id')
                
                if room_id and user_id:
                    await self.sio.enter_room(sid, room_id)
                    if user_id in self.user_rooms:
                        self.user_rooms[user_id].add(room_id)
                    print(f"User {user_id} joined room {room_id}")
            except Exception as e:
                print(f"Join room error: {e}")

        @self.sio.event
        async def send_chat_request(sid, data):
            """Handle chat request"""
            try:
                sender_id = data.get('sender_id')
                receiver_id = data.get('receiver_id')
                sender_name = data.get('sender_name')
                sender_role = data.get('sender_role', 'user')
                
                if not all([sender_id, receiver_id, sender_name]):
                    return
                
                # Save request to DB
                request = {
                    'sender_id': sender_id,
                    'receiver_id': receiver_id,
                    'sender_name': sender_name,
                    'sender_role': sender_role,
                    'sent_at': datetime.utcnow(),
                    'status': 'pending'
                }
                
                result = await db.chat_requests.insert_one(request)
                request['_id'] = str(result.inserted_id)
                
                # Send request to receiver if online
                if receiver_id in self.active_users:
                    receiver_socket = self.active_users[receiver_id]
                    await self.sio.emit('chat_request', request, room=receiver_socket)
                
                print(f"Chat request sent from {sender_id} to {receiver_id}")
                
            except Exception as e:
                print(f"Send chat request error: {e}")

        @self.sio.event
        async def accept_chat_request(sid, data):
            """Accept chat request"""
            try:
                request_id = data.get('request_id')
                sender_id = data.get('sender_id')
                receiver_id = data.get('receiver_id')
                
                # Update request status
                await db.chat_requests.update_one(
                    {'_id': ObjectId(request_id)},
                    {'$set': {'status': 'accepted', 'accepted_at': datetime.utcnow()}}
                )
                
                # Create or get room
                room_id = await self.get_or_create_room(sender_id, receiver_id)
                
                # Notify both users
                request_update = {
                    '_id': request_id,
                    'status': 'accepted',
                    'room_id': room_id,
                }
                
                if sender_id in self.active_users:
                    await self.sio.emit('request_accepted', request_update, room=self.active_users[sender_id])
                if receiver_id in self.active_users:
                    await self.sio.emit('request_accepted', request_update, room=self.active_users[receiver_id])
                
                print(f"Chat request accepted between {sender_id} and {receiver_id}")
                
            except Exception as e:
                print(f"Accept chat request error: {e}")

        @self.sio.event
        async def reject_chat_request(sid, data):
            """Reject chat request"""
            try:
                request_id = data.get('request_id')
                sender_id = data.get('sender_id')
                
                # Update request status
                await db.chat_requests.update_one(
                    {'_id': ObjectId(request_id)},
                    {'$set': {'status': 'rejected', 'rejected_at': datetime.utcnow()}}
                )
                
                # Notify sender if online
                if sender_id in self.active_users:
                    await self.sio.emit('request_rejected', {
                        '_id': request_id,
                        'status': 'rejected'
                    }, room=self.active_users[sender_id])
                
                print(f"Chat request rejected: {request_id}")
                
            except Exception as e:
                print(f"Reject chat request error: {e}")

        @self.sio.event
        async def send_message(sid, data):
            """Send message in chat room"""
            try:
                room_id = data.get('room_id')
                sender_id = data.get('sender_id')
                sender_name = data.get('sender_name')
                receiver_id = data.get('receiver_id')
                content = data.get('content')
                
                if not all([room_id, sender_id, sender_name, receiver_id, content]):
                    return
                
                # Create message document
                message = {
                    'room_id': room_id,
                    'sender_id': sender_id,
                    'sender_name': sender_name,
                    'receiver_id': receiver_id,
                    'content': content,
                    'timestamp': datetime.utcnow(),
                    'delivered': False,
                    'read': False
                }
                
                result = await chat_collection.insert_one(message)
                message['_id'] = str(result.inserted_id)
                message['timestamp'] = message['timestamp'].isoformat()
                
                # Emit to room
                await self.sio.emit('new_message', message, room=room_id)
                
                # Mark as delivered if receiver is in room
                if receiver_id in self.active_users:
                    await chat_collection.update_one(
                        {'_id': ObjectId(message['_id'])},
                        {'$set': {'delivered': True}}
                    )
                
                print(f"Message sent from {sender_id} to {receiver_id}")
                
            except Exception as e:
                print(f"Send message error: {e}")

        @self.sio.event
        async def mark_as_read(sid, data):
            """Mark messages as read"""
            try:
                message_ids = data.get('message_ids', [])
                
                if message_ids:
                    await chat_collection.update_many(
                        {'_id': {'$in': [ObjectId(mid) for mid in message_ids]}},
                        {'$set': {'read': True}}
                    )
                
                print(f"Marked {len(message_ids)} messages as read")
                
            except Exception as e:
                print(f"Mark as read error: {e}")

    async def send_pending_messages(self, user_id: str):
        """Send undelivered messages to user"""
        try:
            pending = await chat_collection.find({
                'receiver_id': user_id,
                'delivered': False
            }).to_list(None)
            
            socket_id = self.active_users.get(user_id)
            if not socket_id:
                return
            
            for message in pending:
                message['_id'] = str(message['_id'])
                room_id = message['room_id']
                
                # Join room if not already joined
                if user_id in self.user_rooms and room_id not in self.user_rooms[user_id]:
                    await self.sio.enter_room(socket_id, room_id)
                    self.user_rooms[user_id].add(room_id)
                
                # Send message
                await self.sio.emit('new_message', message, room=room_id)
                
                # Mark as delivered
                await chat_collection.update_one(
                    {'_id': ObjectId(message['_id'])},
                    {'$set': {'delivered': True}}
                )
                
            print(f"Sent {len(pending)} pending messages to user {user_id}")
        except Exception as e:
            print(f"Send pending messages error: {e}")

chat_manager = ChatManager()