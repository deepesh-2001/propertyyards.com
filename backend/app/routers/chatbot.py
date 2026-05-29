"""
Chat Bot Router
Endpoints for AI-powered chat bot
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from app.database import get_database
from app.chatbot import ChatBot, PropertySearchBot
from app.schemas import ChatRequest, ChatResponse, ChatHistoryItem
from app.auth import decode_token
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chatbot", tags=["Chat Bot"])


def get_current_user(authorization: str = None) -> dict:
    """Extract current user from authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token = authorization.split(" ")[1]
        token_data = decode_token(token)
        if token_data:
            return {"user_id": token_data.user_id, "email": token_data.email, "role": token_data.role}
    except Exception:
        pass

    raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    authorization: Optional[str] = Header(None),
    db = Depends(get_database)
):
    """Send message to chat bot and get response"""
    current_user = get_current_user(authorization)
    
    # Generate session ID if not provided
    session_id = chat_request.session_id or str(uuid.uuid4())
    
    chatbot = ChatBot(db)
    response = await chatbot.generate_response(
        message=chat_request.message,
        session_id=session_id,
        user_id=current_user["user_id"],
        context=chat_request.context
    )
    
    return ChatResponse(**response)


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    authorization: Optional[str] = Header(None),
    db = Depends(get_database)
):
    """Get chat history for a session"""
    current_user = get_current_user(authorization)
    
    chatbot = ChatBot(db)
    history = await chatbot.get_conversation_history(session_id, current_user["user_id"])
    
    return {
        "session_id": session_id,
        "messages": history
    }


@router.delete("/history/{session_id}")
async def clear_chat_history(
    session_id: str,
    authorization: Optional[str] = Header(None),
    db = Depends(get_database)
):
    """Clear chat history for a session"""
    current_user = get_current_user(authorization)
    
    chatbot = ChatBot(db)
    cleared = await chatbot.clear_conversation(session_id, current_user["user_id"])
    
    if not cleared:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Chat history cleared successfully"}


@router.post("/search")
async def search_properties_chat(
    query: str,
    authorization: Optional[str] = Header(None),
    db = Depends(get_database)
):
    """Search properties using natural language"""
    current_user = get_current_user(authorization)
    
    search_bot = PropertySearchBot(db)
    properties = await search_bot.search_properties(query)
    
    return {
        "query": query,
        "results": properties,
        "count": len(properties)
    }
