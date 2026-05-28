"""
Notification Service Module
Handles email, WhatsApp, SMS, and push notifications for investment greetings
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

from app.schemas import (
    NotificationChannel,
    NotificationStatus,
    InvestmentNotificationCreate,
    InvestmentNotificationResponse
)
from app.config import settings

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Email notification service"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_HOST if hasattr(settings, 'SMTP_HOST') else "smtp.gmail.com"
        self.smtp_port = settings.SMTP_PORT if hasattr(settings, 'SMTP_PORT') else 587
        self.smtp_username = settings.SMTP_USERNAME if hasattr(settings, 'SMTP_USERNAME') else ""
        self.smtp_password = settings.SMTP_PASSWORD if hasattr(settings, 'SMTP_PASSWORD') else ""
        self.from_email = settings.FROM_EMAIL if hasattr(settings, 'FROM_EMAIL') else "noreply@housingplatform.com"
    
    async def send_investment_greeting(
        self,
        notification: InvestmentNotificationCreate,
        database
    ) -> Dict[str, Any]:
        """Send investment greeting email"""
        try:
            # Create email content
            subject = f"Congratulations on Your Investment in {notification.property_name}!"
            
            # HTML email template
            html_body = self._generate_investment_email_html(notification)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = notification.investor_email
            
            # Attach HTML body
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Attach property image if available
            if notification.property_image:
                try:
                    import requests
                    response = requests.get(notification.property_image)
                    if response.status_code == 200:
                        img_data = response.content
                        image_part = MIMEImage(img_data)
                        image_part.add_header('Content-ID', '<property_image>')
                        msg.attach(image_part)
                except Exception as e:
                    logger.warning(f"Failed to attach property image: {e}")
            
            # Send email
            await self._send_email(msg)
            
            return {
                "success": True,
                "status": NotificationStatus.SENT,
                "sent_at": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Email sending error: {e}")
            return {
                "success": False,
                "status": NotificationStatus.FAILED,
                "error": str(e)
            }
    
    def _generate_investment_email_html(self, notification: InvestmentNotificationCreate) -> str:
        """Generate HTML email for investment greeting"""
        size_str = f"{notification.property_size} sq ft" if notification.property_size else "N/A"
        location_str = notification.property_location or "N/A"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .property-info {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea; }}
                .property-info h3 {{ color: #667eea; margin-top: 0; }}
                .amount {{ font-size: 32px; color: #28a745; font-weight: bold; text-align: center; margin: 20px 0; }}
                .details {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
                .detail-item {{ padding: 10px; background: #f0f0f0; border-radius: 5px; }}
                .detail-label {{ font-weight: bold; color: #666; font-size: 12px; }}
                .detail-value {{ font-size: 16px; color: #333; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
                .button {{ display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Congratulations!</h1>
                    <p>Your Investment is Successful</p>
                </div>
                <div class="content">
                    <p>Dear <strong>{notification.investor_name}</strong>,</p>
                    <p>We are thrilled to inform you that your investment in <strong>{notification.property_name}</strong> has been successfully processed.</p>
                    
                    <div class="amount">
                        ₹{notification.amount:,.2f}
                    </div>
                    
                    <div class="property-info">
                        <h3>Property Details</h3>
                        <div class="details">
                            <div class="detail-item">
                                <div class="detail-label">Property Name</div>
                                <div class="detail-value">{notification.property_name}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Location</div>
                                <div class="detail-value">{location_str}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Size</div>
                                <div class="detail-value">{size_str}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Investment Type</div>
                                <div class="detail-value">{notification.investment_type}</div>
                            </div>
                        </div>
                    </div>
                    
                    <p>Thank you for choosing our platform for your investment. We look forward to serving you and helping you grow your portfolio.</p>
                    
                    <div style="text-align: center;">
                        <a href="#" class="button">View Investment Details</a>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated email. Please do not reply.</p>
                        <p>&copy; 2026 Housing Platform. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    async def _send_email(self, msg):
        """Send email via SMTP"""
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)


class WhatsAppNotificationService:
    """WhatsApp notification service"""
    
    def __init__(self):
        self.api_url = "https://api.whatsapp.com/v1/messages"
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN if hasattr(settings, 'WHATSAPP_ACCESS_TOKEN') else ""
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID if hasattr(settings, 'WHATSAPP_PHONE_NUMBER_ID') else ""
    
    async def send_investment_greeting(
        self,
        notification: InvestmentNotificationCreate,
        database
    ) -> Dict[str, Any]:
        """Send investment greeting via WhatsApp"""
        try:
            import aiohttp
            
            # Generate WhatsApp message
            message = self._generate_whatsapp_message(notification)
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": notification.investor_phone,
                "type": "template",
                "template": {
                    "name": "investment_greeting",
                    "language": {"code": "en"},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": notification.investor_name},
                                {"type": "text", "text": notification.property_name},
                                {"type": "text", "text": f"₹{notification.amount:,.2f}"},
                                {"type": "text", "text": notification.property_location or "N/A"},
                                {"type": "text", "text": f"{notification.property_size} sq ft" if notification.property_size else "N/A"}
                            ]
                        }
                    ]
                }
            }
            
            # Send media if available
            if notification.property_image:
                payload["template"]["components"].append({
                    "type": "header",
                    "parameters": [
                        {"type": "image", "image": {"link": notification.property_image}}
                    ]
                })
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "status": NotificationStatus.SENT,
                            "message_id": data.get("messages", [{}])[0].get("id"),
                            "sent_at": datetime.utcnow()
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"WhatsApp API error: {error_text}")
                        return {
                            "success": False,
                            "status": NotificationStatus.FAILED,
                            "error": error_text
                        }
        except Exception as e:
            logger.error(f"WhatsApp sending error: {e}")
            return {
                "success": False,
                "status": NotificationStatus.FAILED,
                "error": str(e)
            }
    
    def _generate_whatsapp_message(self, notification: InvestmentNotificationCreate) -> str:
        """Generate WhatsApp message for investment greeting"""
        size_str = f"{notification.property_size} sq ft" if notification.property_size else "N/A"
        location_str = notification.property_location or "N/A"
        
        message = f"""
🎉 *Congratulations {notification.investor_name}!*

Your investment in *{notification.property_name}* has been successfully processed.

💰 *Investment Amount:* ₹{notification.amount:,.2f}
📍 *Location:* {location_str}
📏 *Size:* {size_str}
🏠 *Property:* {notification.property_name}

Thank you for choosing our platform!
        """
        return message.strip()


class NotificationManager:
    """Unified notification manager"""
    
    def __init__(self):
        self.email_service = EmailNotificationService()
        self.whatsapp_service = WhatsAppNotificationService()
    
    async def send_investment_notification(
        self,
        notification: InvestmentNotificationCreate,
        database
    ) -> InvestmentNotificationResponse:
        """Send investment notification through multiple channels"""
        try:
            email_status = NotificationStatus.PENDING
            whatsapp_status = NotificationStatus.PENDING
            sms_status = None
            push_status = None
            email_sent_at = None
            whatsapp_sent_at = None
            sms_sent_at = None
            push_sent_at = None
            error_message = None
            
            # Send email
            if NotificationChannel.EMAIL in notification.channels:
                email_result = await self.email_service.send_investment_greeting(notification, database)
                email_status = email_result.get("status", NotificationStatus.FAILED)
                if email_status == NotificationStatus.SENT:
                    email_sent_at = email_result.get("sent_at")
                if email_result.get("error"):
                    error_message = email_result.get("error")
            
            # Send WhatsApp
            if NotificationChannel.WHATSAPP in notification.channels:
                whatsapp_result = await self.whatsapp_service.send_investment_greeting(notification, database)
                whatsapp_status = whatsapp_result.get("status", NotificationStatus.FAILED)
                if whatsapp_status == NotificationStatus.SENT:
                    whatsapp_sent_at = whatsapp_result.get("sent_at")
                if whatsapp_result.get("error") and not error_message:
                    error_message = whatsapp_result.get("error")
            
            # Create notification record
            notification_record = {
                **notification.dict(),
                "email_status": email_status,
                "whatsapp_status": whatsapp_status,
                "sms_status": sms_status,
                "push_status": push_status,
                "email_sent_at": email_sent_at,
                "whatsapp_sent_at": whatsapp_sent_at,
                "sms_sent_at": sms_sent_at,
                "push_sent_at": push_sent_at,
                "error_message": error_message,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await database.investment_notifications.insert_one(notification_record)
            notification_record["id"] = str(result.inserted_id)
            
            return InvestmentNotificationResponse(**notification_record)
            
        except Exception as e:
            logger.error(f"Notification sending error: {e}")
            raise


# Global notification manager instance
notification_manager = NotificationManager()
