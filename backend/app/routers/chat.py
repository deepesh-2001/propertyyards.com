"""
Chat Router
API endpoints for comprehensive chat messaging system
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
import asyncio

from app.database import get_db
from app.auth import get_current_user
from app.chat_service import chat_service, MessageType, ChatType, UserRole, MessageStatus

router = APIRouter(prefix="/api/chat", tags=["chat"])

# ========== Request Models ==========

class SendMessageRequest(BaseModel):
    chat_id: str
    content: str
    message_type: str = "text"
    reply_to: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None

class CreateChatRequest(BaseModel):
    name: str
    chat_type: str
    participants: List[str]
    metadata: Optional[Dict[str, Any]] = None

class AddParticipantRequest(BaseModel):
    user_id: str

class SearchMessagesRequest(BaseModel):
    query: str
    chat_ids: Optional[List[str]] = None

class ReactionRequest(BaseModel):
    message_id: str
    reaction: str

class EditMessageRequest(BaseModel):
    message_id: str
    content: str

# ========== WebSocket Manager ==========

class ConnectionManager:
    """WebSocket connection manager for real-time chat"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a WebSocket user"""
        await websocket.accept()
        connection_id = f"{user_id}_{datetime.utcnow().timestamp()}"
        self.active_connections[connection_id] = websocket
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)
        
        return connection_id
    
    def disconnect(self, connection_id: str, user_id: str):
        """Disconnect a WebSocket user"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if user_id in self.user_connections:
            if connection_id in self.user_connections[user_id]:
                self.user_connections[user_id].remove(connection_id)
            
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
    
    async def send_personal_message(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user"""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                if connection_id in self.active_connections:
                    websocket = self.active_connections[connection_id]
                    try:
                        await websocket.send_text(json.dumps(message))
                    except:
                        # Remove dead connection
                        self.disconnect(connection_id, user_id)
    
    async def broadcast_to_chat(self, chat_id: str, participants: List[str], message: Dict[str, Any]):
        """Broadcast message to all participants in a chat"""
        for participant_id in participants:
            await self.send_personal_message(participant_id, message)

manager = ConnectionManager()

# ========== Chat Endpoints ==========

@router.post("/send")
async def send_message(
    request: SendMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send a message to a chat room"""
    try:
        user_id = str(current_user.get("_id"))
        
        # Convert message type
        try:
            message_type = MessageType(request.message_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid message type")
        
        # Send message
        message = await chat_service.send_message(
            chat_id=request.chat_id,
            sender_id=user_id,
            content=request.content,
            message_type=message_type,
            reply_to=request.reply_to,
            attachments=request.attachments
        )
        
        # Get chat room participants
        chat_room = chat_service.chat_rooms.get(request.chat_id)
        if chat_room:
            # Broadcast to all participants
            message_data = {
                "type": "new_message",
                "data": {
                    "id": message.id,
                    "chat_id": message.chat_id,
                    "sender_id": message.sender_id,
                    "sender_name": message.sender_name,
                    "content": message.content,
                    "message_type": message.message_type.value,
                    "timestamp": message.timestamp.isoformat(),
                    "status": message.status.value,
                    "reply_to": message.reply_to,
                    "attachments": message.attachments
                }
            }
            await manager.broadcast_to_chat(request.chat_id, chat_room.participants, message_data)
        
        return {
            "success": True,
            "data": {
                "id": message.id,
                "chat_id": message.chat_id,
                "sender_name": message.sender_name,
                "content": message.content,
                "message_type": message.message_type.value,
                "timestamp": message.timestamp.isoformat(),
                "status": message.status.value
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@router.get("/rooms/{chat_id}/messages")
async def get_chat_messages(
    chat_id: str,
    limit: int = Query(50, ge=1, le=100),
    before: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get messages from a chat room"""
    try:
        user_id = str(current_user.get("_id"))
        
        # Parse before timestamp
        before_datetime = None
        if before:
            try:
                before_datetime = datetime.fromisoformat(before)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid before timestamp")
        
        messages = await chat_service.get_chat_messages(
            chat_id=chat_id,
            user_id=user_id,
            limit=limit,
            before=before_datetime
        )
        
        return {
            "success": True,
            "data": [
                {
                    "id": msg.id,
                    "chat_id": msg.chat_id,
                    "sender_id": msg.sender_id,
                    "sender_name": msg.sender_name,
                    "content": msg.content,
                    "message_type": msg.message_type.value,
                    "timestamp": msg.timestamp.isoformat(),
                    "status": msg.status.value,
                    "reply_to": msg.reply_to,
                    "attachments": msg.attachments,
                    "reactions": msg.reactions,
                    "edited": msg.edited,
                    "edited_at": msg.edited_at.isoformat() if msg.edited_at else None
                }
                for msg in messages
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")

@router.get("/rooms")
async def get_user_chats(current_user: dict = Depends(get_current_user)):
    """Get all chat rooms for the current user"""
    try:
        user_id = str(current_user.get("_id"))
        chats = await chat_service.get_user_chats(user_id)
        
        return {
            "success": True,
            "data": [
                {
                    "id": chat.id,
                    "name": chat.name,
                    "chat_type": chat.chat_type.value,
                    "participants": chat.participants,
                    "created_by": chat.created_by,
                    "created_at": chat.created_at.isoformat(),
                    "last_message": {
                        "id": chat.last_message.id,
                        "sender_name": chat.last_message.sender_name,
                        "content": chat.last_message.content,
                        "timestamp": chat.last_message.timestamp.isoformat()
                    } if chat.last_message else None,
                    "unread_count": chat.unread_counts.get(user_id, 0),
                    "is_active": chat.is_active,
                    "pinned": chat.pinned,
                    "archived": chat.archived,
                    "metadata": chat.metadata
                }
                for chat in chats
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user chats: {str(e)}")

@router.post("/rooms")
async def create_chat_room(
    request: CreateChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new chat room"""
    try:
        creator_id = str(current_user.get("_id"))
        
        # Convert chat type
        try:
            chat_type = ChatType(request.chat_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid chat type")
        
        # Create chat room
        chat_room = await chat_service.create_chat_room(
            name=request.name,
            chat_type=chat_type,
            creator_id=creator_id,
            participants=request.participants,
            metadata=request.metadata
        )
        
        # Broadcast to all participants
        chat_data = {
            "type": "new_chat",
            "data": {
                "id": chat_room.id,
                "name": chat_room.name,
                "chat_type": chat_room.chat_type.value,
                "participants": chat_room.participants,
                "created_by": chat_room.created_by,
                "created_at": chat_room.created_at.isoformat()
            }
        }
        await manager.broadcast_to_chat(chat_room.id, chat_room.participants, chat_data)
        
        return {
            "success": True,
            "data": {
                "id": chat_room.id,
                "name": chat_room.name,
                "chat_type": chat_room.chat_type.value,
                "participants": chat_room.participants,
                "created_by": chat_room.created_by,
                "created_at": chat_room.created_at.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create chat room: {str(e)}")

@router.post("/rooms/{chat_id}/participants")
async def add_participant(
    chat_id: str,
    request: AddParticipantRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add a participant to a chat room"""
    try:
        user_id = str(current_user.get("_id"))
        
        success = await chat_service.add_participant(
            chat_id=chat_id,
            user_id=request.user_id,
            added_by=user_id
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add participant")
        
        # Get updated chat room
        chat_room = chat_service.chat_rooms.get(chat_id)
        if chat_room:
            # Broadcast to all participants
            participant_data = {
                "type": "participant_added",
                "data": {
                    "chat_id": chat_id,
                    "user_id": request.user_id,
                    "participants": chat_room.participants
                }
            }
            await manager.broadcast_to_chat(chat_id, chat_room.participants, participant_data)
        
        return {
            "success": True,
            "message": "Participant added successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add participant: {str(e)}")

@router.delete("/rooms/{chat_id}/participants/{user_id}")
async def remove_participant(
    chat_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a participant from a chat room"""
    try:
        current_user_id = str(current_user.get("_id"))
        
        success = await chat_service.remove_participant(
            chat_id=chat_id,
            user_id=user_id,
            removed_by=current_user_id
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to remove participant")
        
        # Get updated chat room
        chat_room = chat_service.chat_rooms.get(chat_id)
        if chat_room:
            # Broadcast to remaining participants
            participant_data = {
                "type": "participant_removed",
                "data": {
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "participants": chat_room.participants
                }
            }
            await manager.broadcast_to_chat(chat_id, chat_room.participants, participant_data)
        
        return {
            "success": True,
            "message": "Participant removed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove participant: {str(e)}")

@router.post("/rooms/{chat_id}/typing")
async def set_typing_indicator(
    chat_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Set typing indicator for current user"""
    try:
        user_id = str(current_user.get("_id"))
        
        await chat_service.set_typing_indicator(chat_id, user_id)
        
        # Get typing users
        typing_users = await chat_service.get_typing_users(chat_id)
        
        # Broadcast typing indicator to all participants
        typing_data = {
            "type": "typing_indicator",
            "data": {
                "chat_id": chat_id,
                "typing_users": typing_users
            }
        }
        
        chat_room = chat_service.chat_rooms.get(chat_id)
        if chat_room:
            await manager.broadcast_to_chat(chat_id, chat_room.participants, typing_data)
        
        return {
            "success": True,
            "typing_users": typing_users
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set typing indicator: {str(e)}")

@router.post("/search")
async def search_messages(
    request: SearchMessagesRequest,
    current_user: dict = Depends(get_current_user)
):
    """Search messages across chat rooms"""
    try:
        user_id = str(current_user.get("_id"))
        
        messages = await chat_service.search_messages(
            user_id=user_id,
            query=request.query,
            chat_ids=request.chat_ids
        )
        
        return {
            "success": True,
            "data": [
                {
                    "id": msg.id,
                    "chat_id": msg.chat_id,
                    "sender_name": msg.sender_name,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "chat_name": chat_service.chat_rooms.get(msg.chat_id, {}).get("name", "Unknown Chat")
                }
                for msg in messages
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search messages: {str(e)}")

@router.post("/messages/{message_id}/read")
async def mark_messages_read(
    message_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a message as read"""
    try:
        user_id = str(current_user.get("_id"))
        
        # Find message and get chat_id
        chat_id = None
        for chat_messages in chat_service.messages.values():
            for message in chat_messages:
                if message.id == message_id:
                    chat_id = message.chat_id
                    break
            if chat_id:
                break
        
        if not chat_id:
            raise HTTPException(status_code=404, detail="Message not found")
        
        success = await chat_service.mark_messages_read(chat_id, user_id, [message_id])
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to mark message as read")
        
        return {
            "success": True,
            "message": "Message marked as read"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark message as read: {str(e)}")

@router.post("/messages/{message_id}/react")
async def add_reaction(
    message_id: str,
    request: ReactionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add reaction to a message"""
    try:
        user_id = str(current_user.get("_id"))
        
        success = await chat_service.add_reaction(
            message_id=message_id,
            user_id=user_id,
            reaction=request.reaction
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add reaction")
        
        # Find message and get chat_id
        chat_id = None
        for chat_messages in chat_service.messages.values():
            for message in chat_messages:
                if message.id == message_id:
                    chat_id = message.chat_id
                    break
            if chat_id:
                break
        
        # Broadcast reaction update
        if chat_id:
            chat_room = chat_service.chat_rooms.get(chat_id)
            if chat_room:
                reaction_data = {
                    "type": "reaction_added",
                    "data": {
                        "message_id": message_id,
                        "reaction": request.reaction,
                        "user_id": user_id
                    }
                }
                await manager.broadcast_to_chat(chat_id, chat_room.participants, reaction_data)
        
        return {
            "success": True,
            "message": "Reaction added successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add reaction: {str(e)}")

@router.delete("/messages/{message_id}/react/{reaction}")
async def remove_reaction(
    message_id: str,
    reaction: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove reaction from a message"""
    try:
        user_id = str(current_user.get("_id"))
        
        success = await chat_service.remove_reaction(
            message_id=message_id,
            user_id=user_id,
            reaction=reaction
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to remove reaction")
        
        # Find message and get chat_id
        chat_id = None
        for chat_messages in chat_service.messages.values():
            for message in chat_messages:
                if message.id == message_id:
                    chat_id = message.chat_id
                    break
            if chat_id:
                break
        
        # Broadcast reaction update
        if chat_id:
            chat_room = chat_service.chat_rooms.get(chat_id)
            if chat_room:
                reaction_data = {
                    "type": "reaction_removed",
                    "data": {
                        "message_id": message_id,
                        "reaction": reaction,
                        "user_id": user_id
                    }
                }
                await manager.broadcast_to_chat(chat_id, chat_room.participants, reaction_data)
        
        return {
            "success": True,
            "message": "Reaction removed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove reaction: {str(e)}")

@router.put("/messages/{message_id}")
async def edit_message(
    message_id: str,
    request: EditMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """Edit a message"""
    try:
        user_id = str(current_user.get("_id"))
        
        success = await chat_service.edit_message(
            message_id=message_id,
            user_id=user_id,
            new_content=request.content
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to edit message")
        
        # Find message and get chat_id
        chat_id = None
        for chat_messages in chat_service.messages.values():
            for message in chat_messages:
                if message.id == message_id:
                    chat_id = message.chat_id
                    break
            if chat_id:
                break
        
        # Broadcast edit update
        if chat_id:
            chat_room = chat_service.chat_rooms.get(chat_id)
            if chat_room:
                edit_data = {
                    "type": "message_edited",
                    "data": {
                        "message_id": message_id,
                        "content": request.content,
                        "edited_at": datetime.utcnow().isoformat()
                    }
                }
                await manager.broadcast_to_chat(chat_id, chat_room.participants, edit_data)
        
        return {
            "success": True,
            "message": "Message edited successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to edit message: {str(e)}")

@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a message"""
    try:
        user_id = str(current_user.get("_id"))
        
        success = await chat_service.delete_message(
            message_id=message_id,
            user_id=user_id
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete message")
        
        # Find chat_id
        chat_id = None
        for chat_messages in chat_service.messages.values():
            for message in chat_messages:
                if message.id == message_id:
                    chat_id = message.chat_id
                    break
            if chat_id:
                break
        
        # Broadcast delete update
        if chat_id:
            chat_room = chat_service.chat_rooms.get(chat_id)
            if chat_room:
                delete_data = {
                    "type": "message_deleted",
                    "data": {
                        "message_id": message_id
                    }
                }
                await manager.broadcast_to_chat(chat_id, chat_room.participants, delete_data)
        
        return {
            "success": True,
            "message": "Message deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete message: {str(e)}")

@router.get("/statistics")
async def get_chat_statistics(current_user: dict = Depends(get_current_user)):
    """Get chat statistics for the current user"""
    try:
        user_id = str(current_user.get("_id"))
        
        stats = await chat_service.get_chat_statistics(user_id)
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.get("/users")
async def get_chat_users():
    """Get all available chat users"""
    try:
        users = []
        for user_id, user in chat_service.users.items():
            users.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
                "avatar": user.avatar,
                "is_online": user.is_online,
                "last_seen": user.last_seen.isoformat() if user.last_seen else None,
                "status_message": user.status_message
            })
        
        return {
            "success": True,
            "data": users
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")

# ========== WebSocket Endpoint ==========

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "typing":
                await chat_service.set_typing_indicator(message["chat_id"], user_id)
                
                # Broadcast typing indicator
                typing_users = await chat_service.get_typing_users(message["chat_id"])
                
                typing_data = {
                    "type": "typing_indicator",
                    "data": {
                        "chat_id": message["chat_id"],
                        "typing_users": typing_users
                    }
                }
                
                chat_room = chat_service.chat_rooms.get(message["chat_id"])
                if chat_room:
                    await manager.broadcast_to_chat(message["chat_id"], chat_room.participants, typing_data)
            
            elif message.get("type") == "ping":
                # Keep connection alive
                await websocket.send_text(json.dumps({"type": "pong"}))
    
    except WebSocketDisconnect:
        manager.disconnect(websocket._connection_id, user_id)

# ========== Health Check ==========

@router.get("/health")
async def chat_service_health():
    """Check chat service health"""
    try:
        # Test basic functionality
        total_chats = len(chat_service.chat_rooms)
        total_messages = sum(len(messages) for messages in chat_service.messages.values())
        total_users = len(chat_service.users)
        
        return {
            "status": "healthy",
            "service": "chat_service",
            "statistics": {
                "total_chats": total_chats,
                "total_messages": total_messages,
                "total_users": total_users,
                "active_connections": len(manager.active_connections)
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "chat_service",
            "error": str(e)
        }
