"""
Notifications Router
Endpoints for WhatsApp and email notifications
"""
from fastapi import APIRouter, Depends, HTTPException
from app.config import settings
from app.whatsapp import WhatsAppIntegration, WhatsAppNotificationService
from app.email import SMTPEmailService, EmailNotificationService
from app.notification import notification_manager
from app.schemas import (
    WhatsAppMessageRequest, WhatsAppMessageResponse, WhatsAppTemplateRequest,
    EmailMessageRequest, EmailMessageResponse,
    NotificationRequest, NotificationResponse, NotificationPreferences,
    InvestmentNotificationCreate, InvestmentNotificationResponse
)
from app.database import get_database
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


# Initialize services
def get_whatsapp_service():
    """Get WhatsApp service instance"""
    return WhatsAppIntegration(
        api_key=getattr(settings, 'WHATSAPP_API_KEY', ''),
        phone_number_id=getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', ''),
        api_version=getattr(settings, 'WHATSAPP_API_VERSION', 'v18.0')
    )


def get_email_service():
    """Get email service instance"""
    return SMTPEmailService(
        smtp_server=getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com'),
        smtp_port=getattr(settings, 'SMTP_PORT', 587),
        smtp_username=getattr(settings, 'SMTP_USERNAME', ''),
        smtp_password=getattr(settings, 'SMTP_PASSWORD', ''),
        use_tls=getattr(settings, 'SMTP_USE_TLS', True)
    )


@router.post("/whatsapp/send", response_model=WhatsAppMessageResponse)
async def send_whatsapp_message(
    message_request: WhatsAppMessageRequest,
    whatsapp_service = Depends(get_whatsapp_service)
):
    """Send WhatsApp message"""
    result = await whatsapp_service.send_text_message(
        to_phone=message_request.to_phone,
        message=message_request.message,
        preview_url=message_request.preview_url
    )
    return WhatsAppMessageResponse(**result)


@router.post("/whatsapp/template")
async def send_whatsapp_template(
    template_request: WhatsAppTemplateRequest,
    whatsapp_service = Depends(get_whatsapp_service)
):
    """Send WhatsApp template message"""
    result = await whatsapp_service.send_template_message(
        to_phone=template_request.to_phone,
        template_name=template_request.template_name,
        components=template_request.components,
        language_code=template_request.language_code
    )
    return result


@router.post("/whatsapp/property-inquiry")
async def send_property_inquiry_whatsapp(
    to_phone: str,
    property_title: str,
    inquirer_name: str,
    message: str,
    whatsapp_service = Depends(get_whatsapp_service)
):
    """Send property inquiry notification via WhatsApp"""
    notification_service = WhatsAppNotificationService(whatsapp_service)
    result = await notification_service.send_property_inquiry_notification(
        to_phone=to_phone,
        property_title=property_title,
        inquirer_name=inquirer_name,
        message=message
    )
    return result


@router.post("/whatsapp/appointment-reminder")
async def send_appointment_reminder_whatsapp(
    to_phone: str,
    property_title: str,
    appointment_date: str,
    appointment_time: str,
    whatsapp_service = Depends(get_whatsapp_service)
):
    """Send appointment reminder via WhatsApp"""
    notification_service = WhatsAppNotificationService(whatsapp_service)
    result = await notification_service.send_appointment_reminder(
        to_phone=to_phone,
        property_title=property_title,
        appointment_date=appointment_date,
        appointment_time=appointment_time
    )
    return result


@router.post("/whatsapp/offer-notification")
async def send_offer_notification_whatsapp(
    to_phone: str,
    property_title: str,
    offer_amount: float,
    buyer_name: str,
    whatsapp_service = Depends(get_whatsapp_service)
):
    """Send offer notification via WhatsApp"""
    notification_service = WhatsAppNotificationService(whatsapp_service)
    result = await notification_service.send_offer_notification(
        to_phone=to_phone,
        property_title=property_title,
        offer_amount=offer_amount,
        buyer_name=buyer_name
    )
    return result


@router.post("/whatsapp/welcome")
async def send_welcome_whatsapp(
    to_phone: str,
    user_name: str,
    whatsapp_service = Depends(get_whatsapp_service)
):
    """Send welcome message via WhatsApp"""
    notification_service = WhatsAppNotificationService(whatsapp_service)
    result = await notification_service.send_welcome_message(
        to_phone=to_phone,
        user_name=user_name
    )
    return result


@router.post("/email/send", response_model=EmailMessageResponse)
async def send_email(
    email_request: EmailMessageRequest,
    email_service = Depends(get_email_service)
):
    """Send email"""
    result = await email_service.send_email(
        to_email=email_request.to_email,
        subject=email_request.subject,
        body=email_request.body,
        from_email=email_request.from_email,
        from_name=email_request.from_name,
        html=email_request.html,
        cc=email_request.cc,
        bcc=email_request.bcc
    )
    return EmailMessageResponse(**result)


@router.post("/email/welcome")
async def send_welcome_email(
    to_email: str,
    user_name: str,
    email_service = Depends(get_email_service)
):
    """Send welcome email"""
    notification_service = EmailNotificationService(email_service)
    result = await notification_service.send_welcome_email(
        to_email=to_email,
        user_name=user_name
    )
    return result


@router.post("/email/property-inquiry")
async def send_property_inquiry_email(
    to_email: str,
    seller_name: str,
    property_title: str,
    inquirer_name: str,
    inquirer_email: str,
    message: str,
    email_service = Depends(get_email_service)
):
    """Send property inquiry notification email"""
    notification_service = EmailNotificationService(email_service)
    result = await notification_service.send_property_inquiry_email(
        to_email=to_email,
        seller_name=seller_name,
        property_title=property_title,
        inquirer_name=inquirer_name,
        inquirer_email=inquirer_email,
        message=message
    )
    return result


@router.post("/email/appointment-reminder")
async def send_appointment_reminder_email(
    to_email: str,
    user_name: str,
    property_title: str,
    appointment_date: str,
    appointment_time: str,
    email_service = Depends(get_email_service)
):
    """Send appointment reminder email"""
    notification_service = EmailNotificationService(email_service)
    result = await notification_service.send_appointment_reminder_email(
        to_email=to_email,
        user_name=user_name,
        property_title=property_title,
        appointment_date=appointment_date,
        appointment_time=appointment_time
    )
    return result


@router.post("/email/offer-notification")
async def send_offer_notification_email(
    to_email: str,
    seller_name: str,
    property_title: str,
    offer_amount: float,
    buyer_name: str,
    buyer_email: str,
    email_service = Depends(get_email_service)
):
    """Send offer notification email"""
    notification_service = EmailNotificationService(email_service)
    result = await notification_service.send_offer_notification_email(
        to_email=to_email,
        seller_name=seller_name,
        property_title=property_title,
        offer_amount=offer_amount,
        buyer_name=buyer_name,
        buyer_email=buyer_email
    )
    return result


@router.post("/email/password-reset")
async def send_password_reset_email(
    to_email: str,
    user_name: str,
    reset_link: str,
    email_service = Depends(get_email_service)
):
    """Send password reset email"""
    notification_service = EmailNotificationService(email_service)
    result = await notification_service.send_password_reset_email(
        to_email=to_email,
        user_name=user_name,
        reset_link=reset_link
    )
    return result


@router.post("/email/verification")
async def send_verification_email(
    to_email: str,
    user_name: str,
    verification_link: str,
    email_service = Depends(get_email_service)
):
    """Send email verification email"""
    notification_service = EmailNotificationService(email_service)
    result = await notification_service.send_verification_email(
        to_email=to_email,
        user_name=user_name,
        verification_link=verification_link
    )
    return result


@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    notification_request: NotificationRequest,
    db = Depends(get_database)
):
    """Send notification via specified channel"""
    # Store notification in database
    notification_data = {
        "user_id": notification_request.user_id,
        "channel": notification_request.channel,
        "notification_type": notification_request.notification_type,
        "title": notification_request.title,
        "message": notification_request.message,
        "data": notification_request.data or {},
        "status": "pending",
        "priority": notification_request.priority,
        "created_at": datetime.utcnow(),
        "sent_at": None
    }
    
    result = await db.notifications.insert_one(notification_data)
    notification_id = str(result.inserted_id)
    
    # Send notification based on channel
    sent = False
    if notification_request.channel == "email":
        email_service = get_email_service()
        email_result = await email_service.send_email(
            to_email=notification_request.data.get("email", ""),
            subject=notification_request.title,
            body=notification_request.message,
            from_email="noreply@propertyyards.com",
            from_name="PropertyYards",
            html=True
        )
        sent = email_result.get("success", False)
    
    elif notification_request.channel == "whatsapp":
        whatsapp_service = get_whatsapp_service()
        whatsapp_result = await whatsapp_service.send_text_message(
            to_phone=notification_request.data.get("phone", ""),
            message=notification_request.message
        )
        sent = whatsapp_result.get("success", False)
    
    # Update notification status
    status = "sent" if sent else "failed"
    await db.notifications.update_one(
        {"_id": notification_id},
        {
            "$set": {
                "status": status,
                "sent_at": datetime.utcnow() if sent else None
            }
        }
    )
    
    # Return notification
    notification = await db.notifications.find_one({"_id": notification_id})
    notification["id"] = str(notification["_id"])
    del notification["_id"]
    
    return NotificationResponse(**notification)


@router.get("/preferences/{user_id}")
async def get_notification_preferences(
    user_id: str,
    db = Depends(get_database)
):
    """Get user notification preferences"""
    preferences = await db.notification_preferences.find_one({"user_id": user_id})
    
    if not preferences:
        # Create default preferences
        default_preferences = {
            "user_id": user_id,
            "email_enabled": True,
            "whatsapp_enabled": False,
            "sms_enabled": False,
            "push_enabled": True,
            "marketing_enabled": False,
            "property_inquiry_enabled": True,
            "appointment_reminder_enabled": True,
            "offer_received_enabled": True,
            "price_drop_enabled": True,
            "new_listing_enabled": False
        }
        await db.notification_preferences.insert_one(default_preferences)
        preferences = default_preferences
    
    preferences["id"] = str(preferences["_id"])
    del preferences["_id"]
    
    return preferences


@router.put("/preferences/{user_id}")
async def update_notification_preferences(
    user_id: str,
    preferences: NotificationPreferences,
    db = Depends(get_database)
):
    """Update user notification preferences"""
    update_data = preferences.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.notification_preferences.update_one(
        {"user_id": user_id},
        {"$set": update_data},
        upsert=True
    )
    
    return {"message": "Notification preferences updated successfully"}


@router.get("/history/{user_id}")
async def get_notification_history(
    user_id: str,
    channel: str = None,
    notification_type: str = None,
    skip: int = 0,
    limit: int = 50,
    db = Depends(get_database)
):
    """Get user notification history"""
    query_filter = {"user_id": user_id}
    if channel:
        query_filter["channel"] = channel
    if notification_type:
        query_filter["notification_type"] = notification_type
    
    cursor = db.notifications.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
    notifications = await cursor.to_list(length=limit)
    
    for notification in notifications:
        notification["id"] = str(notification["_id"])
        del notification["_id"]
    
    total = await db.notifications.count_documents(query_filter)
    
    return {
        "items": notifications,
        "total": total,
        "skip": skip,
        "limit": limit
    }


# ========== Investment Notification Endpoints ==========

@router.post("/investment/greeting", response_model=InvestmentNotificationResponse)
async def send_investment_greeting(
    notification: InvestmentNotificationCreate,
    db = Depends(get_database)
):
    """Send investment greeting notification via email and WhatsApp"""
    try:
        result = await notification_manager.send_investment_notification(notification, db)
        return InvestmentNotificationResponse(**result)
    except Exception as e:
        logger.error(f"Investment notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investment/{notification_id}", response_model=InvestmentNotificationResponse)
async def get_investment_notification(
    notification_id: str,
    db = Depends(get_database)
):
    """Get investment notification details"""
    notification = await db.investment_notifications.find_one({"_id": notification_id})
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification["id"] = str(notification["_id"])
    del notification["_id"]
    
    return InvestmentNotificationResponse(**notification)


@router.get("/investment/user/{user_id}")
async def get_user_investment_notifications(
    user_id: str,
    status: str = None,
    skip: int = 0,
    limit: int = 50,
    db = Depends(get_database)
):
    """Get investment notifications for a user"""
    query = {"user_id": user_id}
    if status:
        query["email_status"] = status
    
    cursor = db.investment_notifications.find(query).sort("created_at", -1).skip(skip).limit(limit)
    notifications = await cursor.to_list(length=limit)
    
    for notification in notifications:
        notification["id"] = str(notification["_id"])
        del notification["_id"]
    
    total = await db.investment_notifications.count_documents(query)
    
    return {
        "items": notifications,
        "total": total,
        "skip": skip,
        "limit": limit
    }
