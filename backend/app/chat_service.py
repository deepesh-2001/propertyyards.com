"""
Chat Messaging Service
Comprehensive chat system for team, client, and vendor communication
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel
import logging
import json
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types of messages in chat system"""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    VOICE = "voice"
    VIDEO = "video"
    LOCATION = "location"
    CONTACT = "contact"
    SYSTEM = "system"
    PROPERTY = "property"
    DOCUMENT = "document"

class ChatType(Enum):
    """Types of chat conversations"""
    TEAM = "team"
    CLIENT = "client"
    VENDOR = "vendor"
    SUPPORT = "support"
    GROUP = "group"
    DIRECT = "direct"

class UserRole(Enum):
    """User roles in chat system"""
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    CLIENT = "client"
    VENDOR = "vendor"
    SUPPORT = "support"

class MessageStatus(Enum):
    """Message delivery status"""
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

@dataclass
class ChatMessage:
    """Chat message data structure"""
    id: str
    chat_id: str
    sender_id: str
    sender_name: str
    content: str
    message_type: MessageType
    timestamp: datetime
    status: MessageStatus = MessageStatus.SENT
    reply_to: Optional[str] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    reactions: Dict[str, List[str]] = field(default_factory=dict)
    edited: bool = False
    edited_at: Optional[datetime] = None

@dataclass
class ChatRoom:
    """Chat room/conversation data structure"""
    id: str
    name: str
    chat_type: ChatType
    participants: List[str]
    created_by: str
    created_at: datetime
    last_message: Optional[ChatMessage] = None
    unread_counts: Dict[str, int] = field(default_factory=dict)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    pinned: bool = False
    archived: bool = False

@dataclass
class ChatUser:
    """Chat user data structure"""
    id: str
    name: str
    email: str
    role: UserRole
    avatar: Optional[str] = None
    is_online: bool = False
    last_seen: Optional[datetime] = None
    typing_in: List[str] = field(default_factory=list)
    status_message: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)

class ChatService:
    """Service for managing chat messaging system"""
    
    def __init__(self):
        # In-memory storage (in production, use database)
        self.messages: Dict[str, List[ChatMessage]] = defaultdict(list)
        self.chat_rooms: Dict[str, ChatRoom] = {}
        self.users: Dict[str, ChatUser] = {}
        self.user_chats: Dict[str, List[str]] = defaultdict(list)
        self.typing_indicators: Dict[str, Dict[str, datetime]] = defaultdict(dict)
        
        # Initialize with some default data
        self._initialize_default_data()
    
    def _initialize_default_data(self):
        """Initialize default chat data for demo"""
        # Create default users
        default_users = [
            ChatUser("admin1", "Admin User", "admin@propertyyards.com", UserRole.ADMIN, "👨‍💼"),
            ChatUser("agent1", "John Agent", "john@propertyyards.com", UserRole.AGENT, "🤵"),
            ChatUser("agent2", "Sarah Agent", "sarah@propertyyards.com", UserRole.AGENT, "👩‍💼"),
            ChatUser("client1", "Rahul Client", "rahul@email.com", UserRole.CLIENT, "👤"),
            ChatUser("vendor1", "Vendor Partner", "vendor@partner.com", UserRole.VENDOR, "🏢"),
            ChatUser("support1", "Support Team", "support@propertyyards.com", UserRole.SUPPORT, "🎧"),
        ]
        
        for user in default_users:
            self.users[user.id] = user
        
        # Create default chat rooms
        self._create_default_chat_rooms()
    
    def _create_default_chat_rooms(self):
        """Create default chat rooms"""
        # Team chat
        team_room = ChatRoom(
            id="team_main",
            name="PropertyYards Team",
            chat_type=ChatType.TEAM,
            participants=["admin1", "agent1", "agent2", "support1"],
            created_by="admin1",
            created_at=datetime.utcnow()
        )
        self.chat_rooms[team_room.id] = team_room
        
        # Client support chat
        client_room = ChatRoom(
            id="client_support_1",
            name="Client Support - Rahul",
            chat_type=ChatType.CLIENT,
            participants=["client1", "agent1", "support1"],
            created_by="client1",
            created_at=datetime.utcnow()
        )
        self.chat_rooms[client_room.id] = client_room
        
        # Vendor coordination chat
        vendor_room = ChatRoom(
            id="vendor_coord_1",
            name="Vendor Coordination",
            chat_type=ChatType.VENDOR,
            participants=["vendor1", "agent2", "admin1"],
            created_by="vendor1",
            created_at=datetime.utcnow()
        )
        self.chat_rooms[vendor_room.id] = vendor_room
        
        # Add some initial messages
        self._add_initial_messages()
    
    def _add_initial_messages(self):
        """Add initial messages to chat rooms"""
        # Team chat messages
        team_messages = [
            {
                "sender_id": "admin1",
                "content": "Good morning team! Let's discuss today's priorities.",
                "message_type": MessageType.TEXT
            },
            {
                "sender_id": "agent1",
                "content": "Morning! I have 3 property viewings scheduled today.",
                "message_type": MessageType.TEXT
            },
            {
                "sender_id": "agent2",
                "content": "I'll be following up with the Gurgaon leads.",
                "message_type": MessageType.TEXT
            }
        ]
        
        for msg_data in team_messages:
            message = ChatMessage(
                id=str(uuid.uuid4()),
                chat_id="team_main",
                sender_id=msg_data["sender_id"],
                sender_name=self.users[msg_data["sender_id"]].name,
                content=msg_data["content"],
                message_type=msg_data["message_type"],
                timestamp=datetime.utcnow()
            )
            self.messages["team_main"].append(message)
        
        # Client support messages
        client_messages = [
            {
                "sender_id": "client1",
                "content": "Hi, I'm interested in the 2BHK apartment in Gurgaon.",
                "message_type": MessageType.TEXT
            },
            {
                "sender_id": "agent1",
                "content": "Hello Rahul! I'd be happy to help you with that property.",
                "message_type": MessageType.TEXT
            }
        ]
        
        for msg_data in client_messages:
            message = ChatMessage(
                id=str(uuid.uuid4()),
                chat_id="client_support_1",
                sender_id=msg_data["sender_id"],
                sender_name=self.users[msg_data["sender_id"]].name,
                content=msg_data["content"],
                message_type=msg_data["message_type"],
                timestamp=datetime.utcnow()
            )
            self.messages["client_support_1"].append(message)
    
    async def send_message(self, chat_id: str, sender_id: str, content: str, 
                          message_type: MessageType = MessageType.TEXT,
                          reply_to: Optional[str] = None,
                          attachments: Optional[List[Dict[str, Any]]] = None) -> ChatMessage:
        """Send a message to a chat room"""
        try:
            # Validate chat exists and user is participant
            if chat_id not in self.chat_rooms:
                raise ValueError(f"Chat room {chat_id} not found")
            
            chat_room = self.chat_rooms[chat_id]
            if sender_id not in chat_room.participants:
                raise ValueError(f"User {sender_id} is not a participant in chat {chat_id}")
            
            # Create message
            message = ChatMessage(
                id=str(uuid.uuid4()),
                chat_id=chat_id,
                sender_id=sender_id,
                sender_name=self.users[sender_id].name,
                content=content,
                message_type=message_type,
                timestamp=datetime.utcnow(),
                reply_to=reply_to,
                attachments=attachments or []
            )
            
            # Store message
            self.messages[chat_id].append(message)
            
            # Update chat room's last message
            chat_room.last_message = message
            
            # Update unread counts for other participants
            for participant_id in chat_room.participants:
                if participant_id != sender_id:
                    chat_room.unread_counts[participant_id] = chat_room.unread_counts.get(participant_id, 0) + 1
            
            # Clear typing indicator for sender
            if chat_id in self.typing_indicators and sender_id in self.typing_indicators[chat_id]:
                del self.typing_indicators[chat_id][sender_id]
            
            logger.info(f"Message sent in chat {chat_id} by {sender_id}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise
    
    async def get_chat_messages(self, chat_id: str, user_id: str, limit: int = 50, 
                               before: Optional[datetime] = None) -> List[ChatMessage]:
        """Get messages from a chat room"""
        try:
            # Validate user is participant
            if chat_id not in self.chat_rooms:
                raise ValueError(f"Chat room {chat_id} not found")
            
            chat_room = self.chat_rooms[chat_id]
            if user_id not in chat_room.participants:
                raise ValueError(f"User {user_id} is not a participant in chat {chat_id}")
            
            # Get messages
            messages = self.messages[chat_id]
            
            # Filter by timestamp if provided
            if before:
                messages = [msg for msg in messages if msg.timestamp < before]
            
            # Sort by timestamp (newest first) and limit
            messages.sort(key=lambda x: x.timestamp, reverse=True)
            messages = messages[:limit]
            
            # Mark messages as read for this user
            chat_room.unread_counts[user_id] = 0
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            raise
    
    async def get_user_chats(self, user_id: str) -> List[ChatRoom]:
        """Get all chat rooms for a user"""
        try:
            user_chats = []
            for chat_room in self.chat_rooms.values():
                if user_id in chat_room.participants and not chat_room.archived:
                    user_chats.append(chat_room)
            
            # Sort by last message timestamp
            user_chats.sort(key=lambda x: x.last_message.timestamp if x.last_message else x.created_at, reverse=True)
            
            return user_chats
            
        except Exception as e:
            logger.error(f"Failed to get user chats: {e}")
            raise
    
    async def create_chat_room(self, name: str, chat_type: ChatType, creator_id: str,
                             participants: List[str], metadata: Optional[Dict[str, Any]] = None) -> ChatRoom:
        """Create a new chat room"""
        try:
            # Validate participants
            for participant_id in participants:
                if participant_id not in self.users:
                    raise ValueError(f"User {participant_id} not found")
            
            # Create chat room
            chat_room = ChatRoom(
                id=str(uuid.uuid4()),
                name=name,
                chat_type=chat_type,
                participants=participants,
                created_by=creator_id,
                created_at=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            # Store chat room
            self.chat_rooms[chat_room.id] = chat_room
            
            # Initialize message list
            self.messages[chat_room.id] = []
            
            # Add system message
            system_message = ChatMessage(
                id=str(uuid.uuid4()),
                chat_id=chat_room.id,
                sender_id="system",
                sender_name="System",
                content=f"Chat room '{name}' created by {self.users[creator_id].name}",
                message_type=MessageType.SYSTEM,
                timestamp=datetime.utcnow()
            )
            self.messages[chat_room.id].append(system_message)
            chat_room.last_message = system_message
            
            logger.info(f"Chat room {chat_room.id} created by {creator_id}")
            return chat_room
            
        except Exception as e:
            logger.error(f"Failed to create chat room: {e}")
            raise
    
    async def add_participant(self, chat_id: str, user_id: str, added_by: str) -> bool:
        """Add a participant to a chat room"""
        try:
            if chat_id not in self.chat_rooms:
                return False
            
            chat_room = self.chat_rooms[chat_id]
            if user_id in chat_room.participants:
                return False
            
            chat_room.participants.append(user_id)
            
            # Add system message
            system_message = ChatMessage(
                id=str(uuid.uuid4()),
                chat_id=chat_id,
                sender_id="system",
                sender_name="System",
                content=f"{self.users[user_id].name} was added to the chat by {self.users[added_by].name}",
                message_type=MessageType.SYSTEM,
                timestamp=datetime.utcnow()
            )
            self.messages[chat_id].append(system_message)
            chat_room.last_message = system_message
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add participant: {e}")
            return False
    
    async def remove_participant(self, chat_id: str, user_id: str, removed_by: str) -> bool:
        """Remove a participant from a chat room"""
        try:
            if chat_id not in self.chat_rooms:
                return False
            
            chat_room = self.chat_rooms[chat_id]
            if user_id not in chat_room.participants:
                return False
            
            chat_room.participants.remove(user_id)
            
            # Add system message
            system_message = ChatMessage(
                id=str(uuid.uuid4()),
                chat_id=chat_id,
                sender_id="system",
                sender_name="System",
                content=f"{self.users[user_id].name} was removed from the chat by {self.users[removed_by].name}",
                message_type=MessageType.SYSTEM,
                timestamp=datetime.utcnow()
            )
            self.messages[chat_id].append(system_message)
            chat_room.last_message = system_message
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove participant: {e}")
            return False
    
    async def set_typing_indicator(self, chat_id: str, user_id: str) -> None:
        """Set typing indicator for a user"""
        try:
            if chat_id in self.typing_indicators:
                self.typing_indicators[chat_id][user_id] = datetime.utcnow()
        except Exception as e:
            logger.error(f"Failed to set typing indicator: {e}")
    
    async def get_typing_users(self, chat_id: str) -> List[str]:
        """Get list of users currently typing in a chat"""
        try:
            if chat_id not in self.typing_indicators:
                return []
            
            # Remove typing indicators older than 5 seconds
            current_time = datetime.utcnow()
            expired_users = []
            
            for user_id, timestamp in self.typing_indicators[chat_id].items():
                if (current_time - timestamp).total_seconds() > 5:
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                del self.typing_indicators[chat_id][user_id]
            
            return list(self.typing_indicators[chat_id].keys())
            
        except Exception as e:
            logger.error(f"Failed to get typing users: {e}")
            return []
    
    async def search_messages(self, user_id: str, query: str, chat_ids: Optional[List[str]] = None) -> List[ChatMessage]:
        """Search messages across chat rooms"""
        try:
            results = []
            search_chats = chat_ids or [chat.id for chat in await self.get_user_chats(user_id)]
            
            for chat_id in search_chats:
                if chat_id in self.messages:
                    for message in self.messages[chat_id]:
                        if query.lower() in message.content.lower():
                            results.append(message)
            
            # Sort by timestamp (newest first)
            results.sort(key=lambda x: x.timestamp, reverse=True)
            return results[:100]  # Limit to 100 results
            
        except Exception as e:
            logger.error(f"Failed to search messages: {e}")
            return []
    
    async def mark_messages_read(self, chat_id: str, user_id: str, message_ids: List[str]) -> bool:
        """Mark specific messages as read"""
        try:
            if chat_id not in self.chat_rooms:
                return False
            
            chat_room = self.chat_rooms[chat_id]
            if user_id not in chat_room.participants:
                return False
            
            # Mark messages as read
            for message in self.messages[chat_id]:
                if message.id in message_ids:
                    message.status = MessageStatus.READ
            
            # Update unread count
            unread_count = 0
            for message in self.messages[chat_id]:
                if message.sender_id != user_id and message.status != MessageStatus.READ:
                    unread_count += 1
            
            chat_room.unread_counts[user_id] = unread_count
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark messages as read: {e}")
            return False
    
    async def add_reaction(self, message_id: str, user_id: str, reaction: str) -> bool:
        """Add reaction to a message"""
        try:
            # Find message
            for chat_messages in self.messages.values():
                for message in chat_messages:
                    if message.id == message_id:
                        if reaction not in message.reactions:
                            message.reactions[reaction] = []
                        
                        if user_id not in message.reactions[reaction]:
                            message.reactions[reaction].append(user_id)
                        
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to add reaction: {e}")
            return False
    
    async def remove_reaction(self, message_id: str, user_id: str, reaction: str) -> bool:
        """Remove reaction from a message"""
        try:
            # Find message
            for chat_messages in self.messages.values():
                for message in chat_messages:
                    if message.id == message_id:
                        if reaction in message.reactions and user_id in message.reactions[reaction]:
                            message.reactions[reaction].remove(user_id)
                            
                            # Remove reaction if no users left
                            if not message.reactions[reaction]:
                                del message.reactions[reaction]
                        
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove reaction: {e}")
            return False
    
    async def edit_message(self, message_id: str, user_id: str, new_content: str) -> bool:
        """Edit a message"""
        try:
            # Find message
            for chat_messages in self.messages.values():
                for message in chat_messages:
                    if message.id == message_id and message.sender_id == user_id:
                        message.content = new_content
                        message.edited = True
                        message.edited_at = datetime.utcnow()
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
            return False
    
    async def delete_message(self, message_id: str, user_id: str) -> bool:
        """Delete a message"""
        try:
            # Find and remove message
            for chat_id, chat_messages in self.messages.items():
                for i, message in enumerate(chat_messages):
                    if message.id == message_id and (message.sender_id == user_id or self.users[user_id].role in [UserRole.ADMIN, UserRole.MANAGER]):
                        chat_messages.pop(i)
                        
                        # Update last message if needed
                        chat_room = self.chat_rooms[chat_id]
                        if chat_room.last_message and chat_room.last_message.id == message_id:
                            chat_room.last_message = chat_messages[-1] if chat_messages else None
                        
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
            return False
    
    async def get_chat_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get chat statistics for a user"""
        try:
            user_chats = await self.get_user_chats(user_id)
            
            total_messages = 0
            unread_messages = 0
            chat_stats = {}
            
            for chat_room in user_chats:
                chat_messages = self.messages[chat_room.id]
                chat_unread = chat_room.unread_counts.get(user_id, 0)
                
                chat_stats[chat_room.id] = {
                    "name": chat_room.name,
                    "type": chat_room.chat_type.value,
                    "total_messages": len(chat_messages),
                    "unread_messages": chat_unread,
                    "last_activity": chat_room.last_message.timestamp if chat_room.last_message else chat_room.created_at
                }
                
                total_messages += len(chat_messages)
                unread_messages += chat_unread
            
            return {
                "total_chats": len(user_chats),
                "total_messages": total_messages,
                "unread_messages": unread_messages,
                "chat_breakdown": chat_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get chat statistics: {e}")
            return {}

# Global instance
chat_service = ChatService()
