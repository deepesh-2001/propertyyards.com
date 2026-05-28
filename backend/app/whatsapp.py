"""
WhatsApp Integration Module
Handles WhatsApp messaging and notifications
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import logging
import httpx

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of WhatsApp messages"""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    TEMPLATE = "template"
    INTERACTIVE = "interactive"


class MessageStatus(str, Enum):
    """Message delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class WhatsAppIntegration:
    """WhatsApp Business API integration"""
    
    def __init__(self, api_key: str, phone_number_id: str, api_version: str = "v18.0"):
        self.api_key = api_key
        self.phone_number_id = phone_number_id
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{api_version}"
    
    async def send_text_message(
        self,
        to_phone: str,
        message: str,
        preview_url: bool = False
    ) -> Dict[str, Any]:
        """Send a text message via WhatsApp"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {
                "body": message,
                "preview_url": preview_url
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                logger.info(f"WhatsApp message sent to {to_phone}")
                return {
                    "success": True,
                    "message_id": result.get("messages", [{}])[0].get("id"),
                    "status": MessageStatus.SENT
                }
            except httpx.HTTPError as e:
                logger.error(f"WhatsApp message failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "status": MessageStatus.FAILED
                }
    
    async def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        components: List[Dict[str, Any]],
        language_code: str = "en_US"
    ) -> Dict[str, Any]:
        """Send a template message via WhatsApp"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                logger.info(f"WhatsApp template sent to {to_phone}")
                return {
                    "success": True,
                    "message_id": result.get("messages", [{}])[0].get("id"),
                    "status": MessageStatus.SENT
                }
            except httpx.HTTPError as e:
                logger.error(f"WhatsApp template failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "status": MessageStatus.FAILED
                }
    
    async def send_image_message(
        self,
        to_phone: str,
        image_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an image message via WhatsApp"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "image",
            "image": {
                "link": image_url
            }
        }
        
        if caption:
            payload["image"]["caption"] = caption
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                logger.info(f"WhatsApp image sent to {to_phone}")
                return {
                    "success": True,
                    "message_id": result.get("messages", [{}])[0].get("id"),
                    "status": MessageStatus.SENT
                }
            except httpx.HTTPError as e:
                logger.error(f"WhatsApp image failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "status": MessageStatus.FAILED
                }
    
    async def verify_webhook(
        self,
        mode: str,
        token: str,
        challenge: str,
        verify_token: str
    ) -> Optional[str]:
        """Verify WhatsApp webhook"""
        if mode == "subscribe" and token == verify_token:
            return challenge
        return None
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming WhatsApp webhook"""
        try:
            entry = webhook_data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            if "messages" in value:
                messages = value["messages"]
                for message in messages:
                    from_phone = value.get("contacts", [{}])[0].get("wa_id")
                    message_id = message.get("id")
                    message_type = message.get("type")
                    
                    logger.info(f"Received WhatsApp message from {from_phone}: {message_id}")
                    
                    return {
                        "from": from_phone,
                        "message_id": message_id,
                        "type": message_type,
                        "timestamp": message.get("timestamp")
                    }
            
            return {"status": "received"}
        except Exception as e:
            logger.error(f"Webhook handling error: {e}")
            return {"error": str(e)}


class WhatsAppTemplateManager:
    """Manage WhatsApp message templates"""
    
    def __init__(self, api_key: str, phone_number_id: str, api_version: str = "v18.0"):
        self.api_key = api_key
        self.phone_number_id = phone_number_id
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{api_version}"
    
    async def create_template(
        self,
        name: str,
        category: str,
        components: List[Dict[str, Any]],
        language: str = "en"
    ) -> Dict[str, Any]:
        """Create a WhatsApp message template"""
        url = f"{self.base_url}/{self.phone_number_id}/message_templates"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "name": name,
            "category": category,
            "language": language,
            "components": components
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                logger.info(f"WhatsApp template created: {name}")
                return {"success": True, "template_id": result.get("id")}
            except httpx.HTTPError as e:
                logger.error(f"Template creation failed: {e}")
                return {"success": False, "error": str(e)}
    
    async def list_templates(self) -> List[Dict[str, Any]]:
        """List all WhatsApp templates"""
        url = f"{self.base_url}/{self.phone_number_id}/message_templates"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result.get("data", [])
            except httpx.HTTPError as e:
                logger.error(f"Template listing failed: {e}")
                return []


class WhatsAppNotificationService:
    """Service for sending notifications via WhatsApp"""
    
    def __init__(self, whatsapp_integration: WhatsAppIntegration):
        self.whatsapp = whatsapp_integration
    
    async def send_property_inquiry_notification(
        self,
        to_phone: str,
        property_title: str,
        inquirer_name: str,
        message: str
    ) -> Dict[str, Any]:
        """Send property inquiry notification"""
        template_message = f"""
🏠 New Property Inquiry

Property: {property_title}
Inquirer: {inquirer_name}

Message: {message}

Please respond to this inquiry.
        """
        
        return await self.whatsapp.send_text_message(to_phone, template_message.strip())
    
    async def send_appointment_reminder(
        self,
        to_phone: str,
        property_title: str,
        appointment_date: str,
        appointment_time: str
    ) -> Dict[str, Any]:
        """Send appointment reminder"""
        template_message = f"""
📅 Appointment Reminder

Property: {property_title}
Date: {appointment_date}
Time: {appointment_time}

Don't forget your property viewing appointment!
        """
        
        return await self.whatsapp.send_text_message(to_phone, template_message.strip())
    
    async def send_offer_notification(
        self,
        to_phone: str,
        property_title: str,
        offer_amount: float,
        buyer_name: str
    ) -> Dict[str, Any]:
        """Send offer notification"""
        template_message = f"""
💰 New Offer Received

Property: {property_title}
Offer Amount: ${offer_amount:,.2f}
Buyer: {buyer_name}

Please review this offer.
        """
        
        return await self.whatsapp.send_text_message(to_phone, template_message.strip())
    
    async def send_welcome_message(
        self,
        to_phone: str,
        user_name: str
    ) -> Dict[str, Any]:
        """Send welcome message to new user"""
        template_message = f"""
🎉 Welcome to PropertyYards!

Hello {user_name},

Thank you for joining PropertyYards! We're excited to help you find your perfect property.

📱 Browse properties
❤️ Save your favorites
📝 Send inquiries
🔔 Get instant notifications

If you need any help, feel free to reach out!

Best regards,
The PropertyYards Team
        """
        
        return await self.whatsapp.send_text_message(to_phone, template_message.strip())
