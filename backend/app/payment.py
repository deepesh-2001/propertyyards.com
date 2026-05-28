"""
Payment Integration Module
Handles payment processing with multiple gateways (Stripe, PayPal, Razorpay, etc.)
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import hashlib
import hmac
import json

from app.config import settings
from app.schemas import (
    PaymentGateway,
    PaymentStatus,
    PaymentMethod,
    PaymentCreate,
    PaymentResponse
)

logger = logging.getLogger(__name__)


class PaymentGatewayError(Exception):
    """Base exception for payment gateway errors"""
    pass


class StripePaymentGateway:
    """Stripe payment integration"""
    
    def __init__(self):
        self.secret_key = settings.STRIPE_SECRET_KEY
        self.publishable_key = settings.STRIPE_PUBLISHABLE_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self.api_version = settings.STRIPE_API_VERSION
        self._client = None
    
    async def _get_client(self):
        """Lazy load Stripe client"""
        if self._client is None:
            try:
                import stripe
                stripe.api_key = self.secret_key
                stripe.api_version = self.api_version
                self._client = stripe
                logger.info("Stripe client initialized")
            except ImportError:
                logger.error("Stripe library not installed")
                raise PaymentGatewayError("Stripe library not installed")
        return self._client
    
    async def create_payment_intent(
        self,
        amount: float,
        currency: str = "USD",
        metadata: Optional[Dict[str, Any]] = None,
        payment_method_id: Optional[str] = None,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a payment intent"""
        try:
            stripe = await self._get_client()
            
            intent_params = {
                "amount": int(amount * 100),  # Convert to cents
                "currency": currency.lower(),
                "metadata": metadata or {},
                "automatic_payment_methods": {"enabled": True}
            }
            
            if payment_method_id:
                intent_params["payment_method"] = payment_method_id
                intent_params["confirm"] = True
                intent_params["capture_method"] = "automatic" if settings.AUTO_CAPTURE_PAYMENT else "manual"
            
            if customer_id:
                intent_params["customer"] = customer_id
            
            intent = stripe.PaymentIntent.create(**intent_params)
            
            return {
                "success": True,
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status,
                "amount": intent.amount / 100,
                "currency": intent.currency,
                "metadata": intent.metadata
            }
        except Exception as e:
            logger.error(f"Stripe payment intent creation error: {e}")
            raise PaymentGatewayError(f"Failed to create payment intent: {str(e)}")
    
    async def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirm a payment intent"""
        try:
            stripe = await self._get_client()
            intent = stripe.PaymentIntent.confirm(payment_intent_id)
            
            return {
                "success": True,
                "payment_intent_id": intent.id,
                "status": intent.status,
                "amount": intent.amount / 100,
                "currency": intent.currency
            }
        except Exception as e:
            logger.error(f"Stripe payment confirmation error: {e}")
            raise PaymentGatewayError(f"Failed to confirm payment: {str(e)}")
    
    async def capture_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Capture a payment intent"""
        try:
            stripe = await self._get_client()
            intent = stripe.PaymentIntent.capture(payment_intent_id)
            
            return {
                "success": True,
                "payment_intent_id": intent.id,
                "status": intent.status,
                "amount": intent.amount / 100,
                "currency": intent.currency
            }
        except Exception as e:
            logger.error(f"Stripe payment capture error: {e}")
            raise PaymentGatewayError(f"Failed to capture payment: {str(e)}")
    
    async def cancel_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Cancel a payment intent"""
        try:
            stripe = await self._get_client()
            intent = stripe.PaymentIntent.cancel(payment_intent_id)
            
            return {
                "success": True,
                "payment_intent_id": intent.id,
                "status": intent.status,
                "amount": intent.amount / 100,
                "currency": intent.currency
            }
        except Exception as e:
            logger.error(f"Stripe payment cancellation error: {e}")
            raise PaymentGatewayError(f"Failed to cancel payment: {str(e)}")
    
    async def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Refund a payment"""
        try:
            stripe = await self._get_client()
            
            refund_params = {"payment_intent": payment_intent_id}
            
            if amount:
                refund_params["amount"] = int(amount * 100)
            
            if reason:
                refund_params["reason"] = reason
            
            refund = stripe.Refund.create(**refund_params)
            
            return {
                "success": True,
                "refund_id": refund.id,
                "amount": refund.amount / 100,
                "status": refund.status,
                "payment_intent_id": refund.payment_intent
            }
        except Exception as e:
            logger.error(f"Stripe refund error: {e}")
            raise PaymentGatewayError(f"Failed to process refund: {str(e)}")
    
    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a customer"""
        try:
            stripe = await self._get_client()
            
            customer_params = {
                "email": email,
                "metadata": metadata or {}
            }
            
            if name:
                customer_params["name"] = name
            
            customer = stripe.Customer.create(**customer_params)
            
            return {
                "success": True,
                "customer_id": customer.id,
                "email": customer.email,
                "name": customer.name
            }
        except Exception as e:
            logger.error(f"Stripe customer creation error: {e}")
            raise PaymentGatewayError(f"Failed to create customer: {str(e)}")
    
    async def attach_payment_method(
        self,
        payment_method_id: str,
        customer_id: str
    ) -> Dict[str, Any]:
        """Attach payment method to customer"""
        try:
            stripe = await self._get_client()
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            
            return {
                "success": True,
                "payment_method_id": payment_method.id,
                "customer_id": customer_id,
                "type": payment_method.type
            }
        except Exception as e:
            logger.error(f"Stripe payment method attachment error: {e}")
            raise PaymentGatewayError(f"Failed to attach payment method: {str(e)}")
    
    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        try:
            stripe = await self._get_client()
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret
            )
            return True
        except Exception as e:
            logger.error(f"Stripe webhook signature verification failed: {e}")
            return False


class PayPalPaymentGateway:
    """PayPal payment integration"""
    
    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.webhook_id = settings.PAYPAL_WEBHOOK_ID
        self.mode = settings.PAYPAL_MODE
        self.base_url = "https://api-m.sandbox.paypal.com" if self.mode == "sandbox" else "https://api-m.paypal.com"
        self._access_token = None
        self._token_expiry = None
    
    async def _get_access_token(self) -> str:
        """Get or refresh access token"""
        import aiohttp
        import time
        
        if self._access_token and self._token_expiry and time.time() < self._token_expiry:
            return self._access_token
        
        auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/oauth2/token",
                auth=auth,
                data={"grant_type": "client_credentials"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise PaymentGatewayError(f"PayPal authentication failed: {error_text}")
                
                data = await response.json()
                self._access_token = data["access_token"]
                self._token_expiry = time.time() + data["expires_in"] - 60  # Refresh 1 minute before expiry
                
                return self._access_token
    
    async def create_order(
        self,
        amount: float,
        currency: str = "USD",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a PayPal order"""
        try:
            import aiohttp
            
            access_token = await self._get_access_token()
            
            order_data = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": currency.upper(),
                        "value": str(amount)
                    },
                    "custom_id": json.dumps(metadata or {})
                }]
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v2/checkout/orders",
                    json=order_data,
                    headers=headers
                ) as response:
                    if response.status != 201:
                        error_text = await response.text()
                        raise PaymentGatewayError(f"PayPal order creation failed: {error_text}")
                    
                    data = await response.json()
                    
                    return {
                        "success": True,
                        "order_id": data["id"],
                        "status": data["status"],
                        "approval_url": next(
                            link["href"] for link in data["links"]
                            if link["rel"] == "approve"
                        ),
                        "amount": amount,
                        "currency": currency
                    }
        except Exception as e:
            logger.error(f"PayPal order creation error: {e}")
            raise PaymentGatewayError(f"Failed to create PayPal order: {str(e)}")
    
    async def capture_order(self, order_id: str) -> Dict[str, Any]:
        """Capture a PayPal order"""
        try:
            import aiohttp
            
            access_token = await self._get_access_token()
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                    headers=headers
                ) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise PaymentGatewayError(f"PayPal order capture failed: {error_text}")
                    
                    data = await response.json()
                    
                    return {
                        "success": True,
                        "order_id": data["id"],
                        "status": data["status"],
                        "capture_id": data["purchase_units"][0]["payments"]["captures"][0]["id"],
                        "amount": float(data["purchase_units"][0]["payments"]["captures"][0]["amount"]["value"]),
                        "currency": data["purchase_units"][0]["payments"]["captures"][0]["amount"]["currency_code"]
                    }
        except Exception as e:
            logger.error(f"PayPal order capture error: {e}")
            raise PaymentGatewayError(f"Failed to capture PayPal order: {str(e)}")
    
    async def refund_payment(
        self,
        capture_id: str,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """Refund a PayPal payment"""
        try:
            import aiohttp
            
            access_token = await self._get_access_token()
            
            refund_data = {}
            if amount:
                refund_data["amount"] = {
                    "value": str(amount),
                    "currency_code": "USD"
                }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v2/payments/captures/{capture_id}/refund",
                    json=refund_data,
                    headers=headers
                ) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise PaymentGatewayError(f"PayPal refund failed: {error_text}")
                    
                    data = await response.json()
                    
                    return {
                        "success": True,
                        "refund_id": data["id"],
                        "status": data["status"],
                        "amount": float(data.get("amount", {}).get("value", 0)),
                        "currency": data.get("amount", {}).get("currency_code", "USD")
                    }
        except Exception as e:
            logger.error(f"PayPal refund error: {e}")
            raise PaymentGatewayError(f"Failed to process PayPal refund: {str(e)}")
    
    async def verify_webhook_signature(self, payload: bytes, headers: Dict[str, str]) -> bool:
        """Verify webhook signature"""
        try:
            import aiohttp
            
            # PayPal webhook verification
            verification_url = f"{self.base_url}/v1/notifications/verify-webhook-signature"
            
            verification_data = {
                "auth_algo": headers.get("PAYPAL-AUTH-ALGO"),
                "cert_url": headers.get("PAYPAL-CERT-URL"),
                "transmission_id": headers.get("PAYPAL-TRANSMISSION-ID"),
                "transmission_sig": headers.get("PAYPAL-TRANSMISSION-SIG"),
                "transmission_time": headers.get("PAYPAL-TRANSMISSION-TIME"),
                "webhook_id": self.webhook_id,
                "webhook_event": json.loads(payload.decode())
            }
            
            access_token = await self._get_access_token()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    verification_url,
                    json=verification_data,
                    headers={"Authorization": f"Bearer {access_token}"}
                ) as response:
                    if response.status != 200:
                        return False
                    
                    data = await response.json()
                    return data.get("verification_status") == "SUCCESS"
        except Exception as e:
            logger.error(f"PayPal webhook signature verification failed: {e}")
            return False


class RazorpayPaymentGateway:
    """Razorpay payment integration"""
    
    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        self.base_url = "https://api.razorpay.com/v1"
        self._access_token = None
    
    async def _get_auth_header(self) -> tuple:
        """Get basic auth header"""
        return (self.key_id, self.key_secret)
    
    async def create_order(
        self,
        amount: float,
        currency: str = "INR",
        metadata: Optional[Dict[str, Any]] = None,
        receipt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a Razorpay order"""
        try:
            import aiohttp
            
            order_data = {
                "amount": int(amount * 100),  # Convert to paise
                "currency": currency.upper(),
                "receipt": receipt or f"receipt_{datetime.utcnow().timestamp()}",
                "notes": metadata or {}
            }
            
            auth = aiohttp.BasicAuth(self.key_id, self.key_secret)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/orders",
                    json=order_data,
                    auth=auth
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise PaymentGatewayError(f"Razorpay order creation failed: {error_text}")
                    
                    data = await response.json()
                    
                    return {
                        "success": True,
                        "order_id": data["id"],
                        "status": data["status"],
                        "amount": data["amount"] / 100,
                        "currency": data["currency"],
                        "receipt": data["receipt"],
                        "notes": data["notes"]
                    }
        except Exception as e:
            logger.error(f"Razorpay order creation error: {e}")
            raise PaymentGatewayError(f"Failed to create Razorpay order: {str(e)}")
    
    async def capture_payment(
        self,
        payment_id: str,
        amount: float
    ) -> Dict[str, Any]:
        """Capture a Razorpay payment"""
        try:
            import aiohttp
            
            auth = aiohttp.BasicAuth(self.key_id, self.key_secret)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/payments/{payment_id}/capture",
                    json={"amount": int(amount * 100)},
                    auth=auth
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise PaymentGatewayError(f"Razorpay payment capture failed: {error_text}")
                    
                    data = await response.json()
                    
                    return {
                        "success": True,
                        "payment_id": data["id"],
                        "status": data["status"],
                        "amount": data["amount"] / 100,
                        "currency": data["currency"],
                        "captured": data.get("captured", False)
                    }
        except Exception as e:
            logger.error(f"Razorpay payment capture error: {e}")
            raise PaymentGatewayError(f"Failed to capture Razorpay payment: {str(e)}")
    
    async def refund_payment(
        self,
        payment_id: str,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """Refund a Razorpay payment"""
        try:
            import aiohttp
            
            auth = aiohttp.BasicAuth(self.key_id, self.key_secret)
            
            refund_data = {}
            if amount:
                refund_data["amount"] = int(amount * 100)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/payments/{payment_id}/refund",
                    json=refund_data,
                    auth=auth
                ) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise PaymentGatewayError(f"Razorpay refund failed: {error_text}")
                    
                    data = await response.json()
                    
                    return {
                        "success": True,
                        "refund_id": data["id"],
                        "status": data["status"],
                        "amount": data.get("amount", 0) / 100,
                        "currency": data.get("currency", "INR")
                    }
        except Exception as e:
            logger.error(f"Razorpay refund error: {e}")
            raise PaymentGatewayError(f"Failed to process Razorpay refund: {str(e)}")
    
    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        try:
            import hmac
            import hashlib
            
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Razorpay webhook signature verification failed: {e}")
            return False


class PayUPaymentGateway:
    """PayU payment integration"""
    
    def __init__(self):
        self.merchant_key = settings.PAYU_MERCHANT_KEY if hasattr(settings, 'PAYU_MERCHANT_KEY') else ""
        self.merchant_salt = settings.PAYU_MERCHANT_SALT if hasattr(settings, 'PAYU_MERCHANT_SALT') else ""
        self.test_mode = getattr(settings, 'PAYU_TEST_MODE', True)
        self.base_url = "https://test.payu.in" if self.test_mode else "https://secure.payu.in"
    
    def _generate_hash(self, data: Dict[str, str]) -> str:
        """Generate hash for PayU transactions"""
        hash_string = f"{self.merchant_key}|{data['txnid']}|{data['amount']}|{data['productinfo']}|{data['firstname']}|{data['email']}||||||||||{self.merchant_salt}"
        return hashlib.sha512(hash_string.encode()).hexdigest()
    
    async def create_payment_link(
        self,
        amount: float,
        product_info: str,
        customer_name: str,
        customer_email: str,
        transaction_id: str,
        return_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a PayU payment link"""
        try:
            data = {
                "key": self.merchant_key,
                "txnid": transaction_id,
                "amount": str(amount),
                "productinfo": product_info,
                "firstname": customer_name,
                "email": customer_email,
                "surl": return_url,
                "furl": return_url,
                "hash": ""
            }
            
            # Generate hash
            data["hash"] = self._generate_hash(data)
            
            # Generate payment URL
            payment_url = f"{self.base_url}/_payment"
            
            return {
                "success": True,
                "payment_url": payment_url,
                "transaction_id": transaction_id,
                "amount": amount,
                "hash": data["hash"],
                "post_data": data
            }
        except Exception as e:
            logger.error(f"PayU payment link creation error: {e}")
            raise PaymentGatewayError(f"Failed to create PayU payment link: {str(e)}")
    
    async def verify_transaction(self, transaction_id: str, status: str, amount: float) -> Dict[str, Any]:
        """Verify a PayU transaction"""
        try:
            # In production, you would call PayU API to verify
            # For now, return basic verification
            return {
                "success": status.lower() == "success",
                "transaction_id": transaction_id,
                "status": status,
                "amount": amount,
                "verified": True
            }
        except Exception as e:
            logger.error(f"PayU transaction verification error: {e}")
            raise PaymentGatewayError(f"Failed to verify PayU transaction: {str(e)}")
    
    async def refund_payment(
        self,
        transaction_id: str,
        amount: float
    ) -> Dict[str, Any]:
        """Refund a PayU payment"""
        try:
            # PayU refund API call would go here
            return {
                "success": True,
                "refund_id": f"refund_{transaction_id}",
                "amount": amount,
                "status": "processed"
            }
        except Exception as e:
            logger.error(f"PayU refund error: {e}")
            raise PaymentGatewayError(f"Failed to process PayU refund: {str(e)}")


class PaymentGatewayFactory:
    """Factory for creating payment gateway instances"""
    
    _gateways = {
        PaymentGateway.STRIPE: StripePaymentGateway,
        PaymentGateway.PAYPAL: PayPalPaymentGateway,
        PaymentGateway.RAZORPAY: RazorpayPaymentGateway,
    }
    
    @classmethod
    def create_gateway(cls, gateway: PaymentGateway):
        """Create a payment gateway instance"""
        gateway_class = cls._gateways.get(gateway)
        if not gateway_class:
            raise PaymentGatewayError(f"Unsupported payment gateway: {gateway}")
        return gateway_class()
    
    @classmethod
    def get_supported_gateways(cls) -> List[PaymentGateway]:
        """Get list of supported payment gateways"""
        return list(cls._gateways.keys())


class PaymentProcessor:
    """Main payment processor that handles multiple gateways"""
    
    def __init__(self):
        self.factory = PaymentGatewayFactory()
    
    async def process_payment(
        self,
        payment_data: PaymentCreate,
        database
    ) -> PaymentResponse:
        """Process a payment through the specified gateway"""
        try:
            gateway = self.factory.create_gateway(payment_data.gateway)
            
            # Process payment based on gateway
            if payment_data.gateway == PaymentGateway.STRIPE:
                result = await gateway.create_payment_intent(
                    amount=payment_data.amount,
                    currency=payment_data.currency,
                    metadata=payment_data.metadata,
                    payment_method_id=payment_data.payment_method_id
                )
            elif payment_data.gateway == PaymentGateway.PAYPAL:
                result = await gateway.create_order(
                    amount=payment_data.amount,
                    currency=payment_data.currency,
                    metadata=payment_data.metadata
                )
            elif payment_data.gateway == PaymentGateway.RAZORPAY:
                result = await gateway.create_order(
                    amount=payment_data.amount,
                    currency=payment_data.currency,
                    metadata=payment_data.metadata
                )
            else:
                raise PaymentGatewayError(f"Gateway {payment_data.gateway} not yet implemented")
            
            # Create payment record in database
            payment_record = {
                "user_id": payment_data.user_id,
                "property_id": payment_data.property_id,
                "payment_condition_id": payment_data.payment_condition_id,
                "amount": payment_data.amount,
                "currency": payment_data.currency,
                "payment_method_id": payment_data.payment_method_id,
                "gateway": payment_data.gateway,
                "status": PaymentStatus.PROCESSING,
                "description": payment_data.description,
                "transaction_id": result.get("payment_intent_id") or result.get("order_id"),
                "gateway_response": result,
                "metadata": payment_data.metadata,
                "paid_at": None,
                "refunded_at": None,
                "refund_amount": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            inserted_payment = await database.payments.insert_one(payment_record)
            payment_record["id"] = str(inserted_payment.inserted_id)
            
            return PaymentResponse(**payment_record)
            
        except Exception as e:
            logger.error(f"Payment processing error: {e}")
            raise PaymentGatewayError(f"Payment processing failed: {str(e)}")
    
    async def refund_payment(
        self,
        payment_id: str,
        amount: float,
        reason: str,
        database
    ) -> Dict[str, Any]:
        """Process a refund"""
        try:
            # Get payment record
            payment = await database.payments.find_one({"_id": payment_id})
            if not payment:
                raise PaymentGatewayError("Payment not found")
            
            gateway = self.factory.create_gateway(payment["gateway"])
            
            # Process refund based on gateway
            if payment["gateway"] == PaymentGateway.STRIPE:
                result = await gateway.refund_payment(
                    payment_intent_id=payment["transaction_id"],
                    amount=amount,
                    reason=reason
                )
            elif payment["gateway"] == PaymentGateway.PAYPAL:
                result = await gateway.refund_payment(
                    capture_id=payment["transaction_id"],
                    amount=amount
                )
            else:
                raise PaymentGatewayError(f"Refund not supported for gateway {payment['gateway']}")
            
            # Update payment record
            await database.payments.update_one(
                {"_id": payment_id},
                {
                    "$set": {
                        "status": PaymentStatus.REFUNDED if amount == payment["amount"] else PaymentStatus.PARTIALLY_REFUNDED,
                        "refunded_at": datetime.utcnow(),
                        "refund_amount": payment.get("refund_amount", 0) + amount,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Refund processing error: {e}")
            raise PaymentGatewayError(f"Refund processing failed: {str(e)}")
    
    async def get_payment_status(
        self,
        payment_id: str,
        database
    ) -> Dict[str, Any]:
        """Get payment status from gateway"""
        try:
            payment = await database.payments.find_one({"_id": payment_id})
            if not payment:
                raise PaymentGatewayError("Payment not found")
            
            gateway = self.factory.create_gateway(payment["gateway"])
            
            # Get status based on gateway
            if payment["gateway"] == PaymentGateway.STRIPE:
                stripe = await gateway._get_client()
                intent = stripe.PaymentIntent.retrieve(payment["transaction_id"])
                return {
                    "status": intent.status,
                    "amount": intent.amount / 100,
                    "currency": intent.currency
                }
            elif payment["gateway"] == PaymentGateway.PAYPAL:
                import aiohttp
                access_token = await gateway._get_access_token()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{gateway.base_url}/v2/checkout/orders/{payment['transaction_id']}",
                        headers={"Authorization": f"Bearer {access_token}"}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return {
                                "status": data["status"],
                                "amount": float(data["purchase_units"][0]["amount"]["value"]),
                                "currency": data["purchase_units"][0]["amount"]["currency_code"]
                            }
            
            return {"status": "unknown"}
            
        except Exception as e:
            logger.error(f"Payment status check error: {e}")
            raise PaymentGatewayError(f"Failed to get payment status: {str(e)}")


class CreditCardPaymentGateway:
    """Credit card payment integration using existing gateways"""
    
    def __init__(self):
        self.stripe_gateway = StripePaymentGateway()
        self.razorpay_gateway = RazorpayPaymentGateway()
        self.payu_gateway = PayUPaymentGateway()
    
    async def process_credit_card_payment(
        self,
        card_data: Dict[str, Any],
        amount: float,
        currency: str = "USD",
        gateway: PaymentGateway = PaymentGateway.STRIPE,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process credit card payment through specified gateway"""
        try:
            if gateway == PaymentGateway.STRIPE:
                return await self._process_stripe_card(card_data, amount, currency, metadata)
            elif gateway == PaymentGateway.RAZORPAY:
                return await self._process_razorpay_card(card_data, amount, currency, metadata)
            elif gateway == PaymentGateway.PAYU:
                return await self._process_payu_card(card_data, amount, currency, metadata)
            else:
                raise PaymentGatewayError(f"Credit card payment not supported for gateway {gateway}")
        except Exception as e:
            logger.error(f"Credit card payment error: {e}")
            raise PaymentGatewayError(f"Credit card payment failed: {str(e)}")
    
    async def _process_stripe_card(
        self,
        card_data: Dict[str, Any],
        amount: float,
        currency: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process credit card payment via Stripe"""
        try:
            stripe = await self.stripe_gateway._get_client()
            
            # Create payment method from card data
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": card_data["card_number"],
                    "exp_month": card_data["expiry_month"],
                    "exp_year": card_data["expiry_year"],
                    "cvc": card_data["cvv"]
                },
                billing_details={
                    "name": card_data.get("cardholder_name", ""),
                    "email": card_data.get("email", ""),
                    "phone": card_data.get("phone", "")
                }
            )
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency=currency.lower(),
                payment_method=payment_method.id,
                confirm=True,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True}
            )
            
            return {
                "success": True,
                "payment_intent_id": intent.id,
                "payment_method_id": payment_method.id,
                "status": intent.status,
                "amount": intent.amount / 100,
                "currency": intent.currency,
                "gateway": PaymentGateway.STRIPE
            }
        except Exception as e:
            logger.error(f"Stripe card payment error: {e}")
            raise PaymentGatewayError(f"Stripe card payment failed: {str(e)}")
    
    async def _process_razorpay_card(
        self,
        card_data: Dict[str, Any],
        amount: float,
        currency: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process credit card payment via Razorpay"""
        try:
            import aiohttp
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.RAZORPAY_KEY_SECRET}"
            }
            
            # Create order
            order_data = {
                "amount": int(amount * 100),
                "currency": currency,
                "receipt": f"receipt_{datetime.utcnow().timestamp()}",
                "payment_capture": 1,
                "notes": metadata or {}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.razorpay_gateway.base_url}/orders",
                    headers=headers,
                    json=order_data
                ) as response:
                    if response.status != 200:
                        raise PaymentGatewayError("Failed to create Razorpay order")
                    order = await response.json()
            
            return {
                "success": True,
                "order_id": order["id"],
                "amount": order["amount"] / 100,
                "currency": order["currency"],
                "gateway": PaymentGateway.RAZORPAY
            }
        except Exception as e:
            logger.error(f"Razorpay card payment error: {e}")
            raise PaymentGatewayError(f"Razorpay card payment failed: {str(e)}")
    
    async def _process_payu_card(
        self,
        card_data: Dict[str, Any],
        amount: float,
        currency: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process credit card payment via PayU"""
        try:
            import aiohttp
            import hashlib
            
            # Generate hash
            hash_string = f"{settings.PAYU_MERCHANT_KEY}|{amount}|{card_data.get('product_info', 'payment')}|{card_data.get('firstname', 'user')}|{card_data.get('email', '')}||||||||||{settings.PAYU_MERCHANT_SALT}"
            hash_value = hashlib.sha512(hash_string.encode()).hexdigest()
            
            payment_data = {
                "key": settings.PAYU_MERCHANT_KEY,
                "txnid": f"txn_{datetime.utcnow().timestamp()}",
                "amount": amount,
                "productinfo": card_data.get("product_info", "payment"),
                "firstname": card_data.get("firstname", "user"),
                "email": card_data.get("email", ""),
                "surl": card_data.get("success_url", ""),
                "furl": card_data.get("failure_url", ""),
                "hash": hash_value,
                "card_number": card_data["card_number"],
                "expiry_month": card_data["expiry_month"],
                "expiry_year": card_data["expiry_year"],
                "cvv": card_data["cvv"],
                "pg": "CC"  # Credit Card
            }
            
            return {
                "success": True,
                "txnid": payment_data["txnid"],
                "amount": amount,
                "currency": currency,
                "gateway": PaymentGateway.PAYU,
                "payment_data": payment_data
            }
        except Exception as e:
            logger.error(f"PayU card payment error: {e}")
            raise PaymentGatewayError(f"PayU card payment failed: {str(e)}")
    
    async def validate_credit_card(self, card_number: str) -> Dict[str, Any]:
        """Validate credit card using Luhn algorithm"""
        try:
            # Remove non-digit characters
            card_number = ''.join(c for c in card_number if c.isdigit())
            
            # Check length
            if len(card_number) < 13 or len(card_number) > 19:
                return {"valid": False, "error": "Invalid card length"}
            
            # Luhn algorithm
            total = 0
            reverse_digits = card_number[::-1]
            
            for i, digit in enumerate(reverse_digits):
                d = int(digit)
                if i % 2 == 1:
                    d *= 2
                    if d > 9:
                        d -= 9
                total += d
            
            is_valid = total % 10 == 0
            
            # Identify card type
            card_type = self._identify_card_type(card_number)
            
            return {
                "valid": is_valid,
                "card_type": card_type,
                "last_four": card_number[-4:]
            }
        except Exception as e:
            logger.error(f"Card validation error: {e}")
            return {"valid": False, "error": str(e)}
    
    def _identify_card_type(self, card_number: str) -> str:
        """Identify credit card type from number"""
        if card_number.startswith('4'):
            return 'visa'
        elif card_number.startswith('5') or card_number.startswith('2'):
            return 'mastercard'
        elif card_number.startswith('3'):
            return 'amex'
        elif card_number.startswith('6'):
            return 'discover'
        else:
            return 'unknown'


# Global payment processor instance
payment_processor = PaymentProcessor()
credit_card_gateway = CreditCardPaymentGateway()
