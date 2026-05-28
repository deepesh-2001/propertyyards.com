"""
Email Alerting Module
Handles email notifications and alerts
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import httpx

logger = logging.getLogger(__name__)


class EmailProvider(str, Enum):
    """Email service providers"""
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    AWS_SES = "aws_ses"
    BREVO = "brevo"


class EmailPriority(str, Enum):
    """Email priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EmailStatus(str, Enum):
    """Email delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"


class SMTPEmailService:
    """SMTP email service"""
    
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        use_tls: bool = True
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.use_tls = use_tls
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str,
        from_name: str = None,
        html: bool = False,
        cc: List[str] = None,
        bcc: List[str] = None,
        attachments: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{from_name} <{from_email}>" if from_name else from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{attachment["filename"]}"'
                    )
                    msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                server.send_message(msg, from_email, recipients)
            
            logger.info(f"Email sent to {to_email}")
            return {
                "success": True,
                "status": EmailStatus.SENT,
                "to": to_email,
                "subject": subject
            }
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": EmailStatus.FAILED
            }


class SendGridService:
    """SendGrid email service"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.sendgrid.com/v3/mail/send"
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str,
        from_name: str = None,
        html: bool = False,
        cc: List[str] = None,
        bcc: List[str] = None
    ) -> Dict[str, Any]:
        """Send email via SendGrid"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        personalizations = [{
            "to": [{"email": to_email}],
            "subject": subject
        }]
        
        if cc:
            personalizations[0]["cc"] = [{"email": email} for email in cc]
        
        if bcc:
            personalizations[0]["bcc"] = [{"email": email} for email in bcc]
        
        payload = {
            "personalizations": personalizations,
            "from": {
                "email": from_email,
                "name": from_name or "PropertyYards"
            },
            "content": [{
                "type": "text/html" if html else "text/plain",
                "value": body
            }]
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.base_url, headers=headers, json=payload)
                response.raise_for_status()
                logger.info(f"SendGrid email sent to {to_email}")
                return {
                    "success": True,
                    "status": EmailStatus.SENT,
                    "to": to_email,
                    "subject": subject
                }
            except httpx.HTTPError as e:
                logger.error(f"SendGrid email failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "status": EmailStatus.FAILED
                }


class MailgunService:
    """Mailgun email service"""
    
    def __init__(self, api_key: str, domain: str):
        self.api_key = api_key
        self.domain = domain
        self.base_url = f"https://api.mailgun.net/v3/{domain}/messages"
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str,
        from_name: str = None,
        html: bool = False,
        cc: List[str] = None,
        bcc: List[str] = None
    ) -> Dict[str, Any]:
        """Send email via Mailgun"""
        auth = ("api", self.api_key)
        
        data = {
            "from": f"{from_name} <{from_email}>" if from_name else from_email,
            "to": to_email,
            "subject": subject,
            "text": body if not html else None,
            "html": body if html else None
        }
        
        if cc:
            data["cc"] = ', '.join(cc)
        
        if bcc:
            data["bcc"] = ', '.join(bcc)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.base_url, auth=auth, data=data)
                response.raise_for_status()
                logger.info(f"Mailgun email sent to {to_email}")
                return {
                    "success": True,
                    "status": EmailStatus.SENT,
                    "to": to_email,
                    "subject": subject
                }
            except httpx.HTTPError as e:
                logger.error(f"Mailgun email failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "status": EmailStatus.FAILED
                }


class EmailNotificationService:
    """Service for sending email notifications"""
    
    def __init__(self, email_service):
        self.email_service = email_service
    
    async def send_welcome_email(
        self,
        to_email: str,
        user_name: str
    ) -> Dict[str, Any]:
        """Send welcome email to new user"""
        subject = "Welcome to PropertyYards!"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">Welcome to PropertyYards!</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <p>Hello {user_name},</p>
                <p>Thank you for joining PropertyYards! We're excited to help you find your perfect property.</p>
                <h3>What you can do:</h3>
                <ul>
                    <li>📱 Browse thousands of properties</li>
                    <li>❤️ Save your favorites</li>
                    <li>📝 Send inquiries to sellers</li>
                    <li>🔔 Get instant notifications</li>
                </ul>
                <p>If you need any help, feel free to reach out!</p>
                <p>Best regards,<br>The PropertyYards Team</p>
            </div>
        </body>
        </html>
        """
        
        return await self.email_service.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            from_email="noreply@propertyyards.com",
            from_name="PropertyYards",
            html=True
        )
    
    async def send_property_inquiry_email(
        self,
        to_email: str,
        seller_name: str,
        property_title: str,
        inquirer_name: str,
        inquirer_email: str,
        message: str
    ) -> Dict[str, Any]:
        """Send property inquiry notification email"""
        subject = f"New Property Inquiry: {property_title}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #667eea; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">New Property Inquiry</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <p>Hello {seller_name},</p>
                <p>You have received a new inquiry for your property:</p>
                <div style="background: white; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0;">
                    <h3>{property_title}</h3>
                    <p><strong>Inquirer:</strong> {inquirer_name}</p>
                    <p><strong>Email:</strong> {inquirer_email}</p>
                    <p><strong>Message:</strong></p>
                    <p>{message}</p>
                </div>
                <p>Please respond to this inquiry as soon as possible.</p>
            </div>
        </body>
        </html>
        """
        
        return await self.email_service.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            from_email="inquiries@propertyyards.com",
            from_name="PropertyYards",
            html=True
        )
    
    async def send_appointment_reminder_email(
        self,
        to_email: str,
        user_name: str,
        property_title: str,
        appointment_date: str,
        appointment_time: str
    ) -> Dict[str, Any]:
        """Send appointment reminder email"""
        subject = "Property Viewing Appointment Reminder"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #667eea; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">Appointment Reminder</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <p>Hello {user_name},</p>
                <p>This is a reminder of your upcoming property viewing appointment:</p>
                <div style="background: white; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0;">
                    <h3>{property_title}</h3>
                    <p><strong>Date:</strong> {appointment_date}</p>
                    <p><strong>Time:</strong> {appointment_time}</p>
                </div>
                <p>Please arrive on time. If you need to reschedule, please contact us.</p>
            </div>
        </body>
        </html>
        """
        
        return await self.email_service.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            from_email="appointments@propertyyards.com",
            from_name="PropertyYards",
            html=True
        )
    
    async def send_offer_notification_email(
        self,
        to_email: str,
        seller_name: str,
        property_title: str,
        offer_amount: float,
        buyer_name: str,
        buyer_email: str
    ) -> Dict[str, Any]:
        """Send offer notification email"""
        subject = f"New Offer Received: ${offer_amount:,.2f}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #667eea; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">New Offer Received</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <p>Hello {seller_name},</p>
                <p>You have received a new offer for your property:</p>
                <div style="background: white; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0;">
                    <h3>{property_title}</h3>
                    <p><strong>Offer Amount:</strong> ${offer_amount:,.2f}</p>
                    <p><strong>Buyer:</strong> {buyer_name}</p>
                    <p><strong>Email:</strong> {buyer_email}</p>
                </div>
                <p>Please review this offer and respond accordingly.</p>
            </div>
        </body>
        </html>
        """
        
        return await self.email_service.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            from_email="offers@propertyyards.com",
            from_name="PropertyYards",
            html=True
        )
    
    async def send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_link: str
    ) -> Dict[str, Any]:
        """Send password reset email"""
        subject = "Password Reset Request"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #667eea; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">Password Reset</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <p>Hello {user_name},</p>
                <p>You have requested to reset your password. Click the link below to reset it:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">Reset Password</a>
                </div>
                <p>This link will expire in 1 hour. If you didn't request this, please ignore this email.</p>
            </div>
        </body>
        </html>
        """
        
        return await self.email_service.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            from_email="security@propertyyards.com",
            from_name="PropertyYards",
            html=True
        )
    
    async def send_verification_email(
        self,
        to_email: str,
        user_name: str,
        verification_link: str
    ) -> Dict[str, Any]:
        """Send email verification email"""
        subject = "Verify Your Email Address"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #667eea; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">Verify Your Email</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <p>Hello {user_name},</p>
                <p>Please verify your email address by clicking the link below:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_link}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">Verify Email</a>
                </div>
                <p>This link will expire in 24 hours. If you didn't create an account, please ignore this email.</p>
            </div>
        </body>
        </html>
        """
        
        return await self.email_service.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            from_email="verify@propertyyards.com",
            from_name="PropertyYards",
            html=True
        )


class EmailTemplateManager:
    """Manage email templates"""
    
    def __init__(self, database):
        self.db = database
        self.collection = database.email_templates
    
    async def create_template(
        self,
        name: str,
        subject: str,
        html_body: str,
        text_body: str = None,
        variables: List[str] = None
    ) -> str:
        """Create an email template"""
        template = {
            "name": name,
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body,
            "variables": variables or [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.collection.insert_one(template)
        logger.info(f"Email template created: {name}")
        return str(result.inserted_id)
    
    async def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Get an email template by name"""
        template = await self.collection.find_one({"name": name})
        if template:
            template["id"] = str(template["_id"])
            del template["_id"]
        return template
    
    async def render_template(
        self,
        name: str,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Render template with variables"""
        template = await self.get_template(name)
        if not template:
            return None
        
        # Simple variable replacement
        html_body = template["html_body"]
        subject = template["subject"]
        
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            html_body = html_body.replace(placeholder, str(value))
            subject = subject.replace(placeholder, str(value))
        
        return {
            "subject": subject,
            "html_body": html_body,
            "text_body": template.get("text_body")
        }
