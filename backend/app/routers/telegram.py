"""
Telegram Router
Webhook and API endpoints for Telegram bot
"""
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user
from app.telegram_bot import telegram_bot

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Receive webhook updates from Telegram"""
    try:
        update = await request.json()

        # Process update
        await telegram_bot.handle_update(update)

        return {"status": "ok"}

    except Exception as e:
        # Still return 200 to Telegram to prevent retries
        return {"status": "error", "message": str(e)}


@router.get("/status")
async def get_bot_status(
    current_user: dict = Depends(get_current_user)
):
    """Get Telegram bot status"""
    if current_user.get("role") not in ["admin", "agent"]:
        raise HTTPException(status_code=403, detail="Admin or agent access required")

    return {
        "initialized": telegram_bot.token is not None,
        "subscribers_count": len(telegram_bot.subscribed_users),
        "webhook_url": telegram_bot.webhook_url
    }


@router.post("/send-message")
async def send_message(
    chat_id: str,
    message: str,
    current_user: dict = Depends(get_current_user)
):
    """Send message via Telegram bot (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        success = await telegram_bot.send_message(chat_id, message)

        if success:
            return {"message": "Message sent", "chat_id": chat_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to send message")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broadcast")
async def broadcast_message(
    message: str,
    background_tasks: BackgroundTasks = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Broadcast message to all subscribers (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Get all subscribers
        subscribers = await database.telegram_subscribers.find(
            {"subscribed": True}
        ).to_list(length=1000)

        # Send in background
        for subscriber in subscribers:
            chat_id = subscriber.get("chat_id")
            if chat_id:
                await telegram_bot.send_message(chat_id, message)

        return {
            "message": "Broadcast initiated",
            "recipient_count": len(subscribers)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscribers")
async def get_subscribers(
    page: int = 1,
    limit: int = 50,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get Telegram subscribers (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        skip = (page - 1) * limit

        subscribers = await database.telegram_subscribers.find().skip(skip).limit(limit).to_list(length=limit)
        total = await database.telegram_subscribers.count_documents({})

        return {
            "subscribers": subscribers,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup-webhook")
async def setup_webhook(
    webhook_url: str,
    current_user: dict = Depends(get_current_user)
):
    """Setup Telegram webhook (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        success = await telegram_bot.set_webhook(webhook_url)

        if success:
            telegram_bot.webhook_url = webhook_url
            return {"message": "Webhook set successfully", "url": webhook_url}
        else:
            raise HTTPException(status_code=500, detail="Failed to set webhook")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_telegram_stats(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get Telegram bot statistics (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Get stats
        total_subscribers = await database.telegram_subscribers.count_documents({})
        active_subscribers = await database.telegram_subscribers.count_documents({"subscribed": True})
        recent_subscribers = await database.telegram_subscribers.count_documents({
            "subscribed_at": {"$gte": datetime.utcnow().replace(day=1)}
        })

        return {
            "total_subscribers": total_subscribers,
            "active_subscribers": active_subscribers,
            "recent_subscribers": recent_subscribers,
            "bot_status": "active" if telegram_bot.token else "not_configured"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
