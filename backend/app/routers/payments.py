"""
Payment Router
Handles payment-related endpoints including payment conditions, methods, transactions, and integrations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.schemas import (
    PaymentConditionCreate,
    PaymentConditionUpdate,
    PaymentConditionResponse,
    PaymentMethodCreate,
    PaymentMethodUpdate,
    PaymentMethodResponse,
    PaymentCreate,
    PaymentResponse,
    PaymentRefundCreate,
    PaymentRefundResponse,
    InstallmentCreate,
    InstallmentResponse,
    InvoiceCreate,
    InvoiceResponse,
    SubscriptionCreate,
    SubscriptionResponse,
    PaymentWebhookEvent,
    PaymentAnalytics,
    PaymentGateway,
    PaymentStatus,
    PaymentConditionType,
    PaymentFrequency,
    SubscriptionPlan
)
from app.payment import payment_processor, PaymentGatewayError
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["payments"])
security = HTTPBearer()


# ========== Payment Conditions Endpoints ==========

@router.post("/conditions", response_model=PaymentConditionResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_condition(
    condition: PaymentConditionCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new payment condition for a property"""
    try:
        condition_data = condition.dict()
        condition_data.update({
            "status": "pending",
            "paid_amount": 0.0,
            "remaining_amount": condition.amount,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        result = await database.payment_conditions.insert_one(condition_data)
        condition_data["id"] = str(result.inserted_id)
        
        # Create installments if needed
        if condition.payment_frequency != PaymentFrequency.ONE_TIME and condition.installments_count > 1:
            for i in range(1, condition.installments_count + 1):
                due_date = condition.due_date + timedelta(days=(i - 1) * condition.installment_interval_days)
                installment_amount = condition.amount / condition.installments_count
                
                installment = {
                    "payment_condition_id": str(result.inserted_id),
                    "installment_number": i,
                    "amount": installment_amount,
                    "due_date": due_date,
                    "paid_amount": 0.0,
                    "status": "pending",
                    "paid_at": None,
                    "late_fee_applied": 0.0,
                    "discount_applied": 0.0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                await database.installments.insert_one(installment)
        
        return PaymentConditionResponse(**condition_data)
    except Exception as e:
        logger.error(f"Error creating payment condition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conditions/{condition_id}", response_model=PaymentConditionResponse)
async def get_payment_condition(
    condition_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific payment condition"""
    condition = await database.payment_conditions.find_one({"_id": condition_id})
    if not condition:
        raise HTTPException(status_code=404, detail="Payment condition not found")
    
    condition["id"] = str(condition["_id"])
    del condition["_id"]
    
    return PaymentConditionResponse(**condition)


@router.get("/properties/{property_id}/conditions", response_model=List[PaymentConditionResponse])
async def get_property_payment_conditions(
    property_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all payment conditions for a property"""
    cursor = database.payment_conditions.find({"property_id": property_id}).sort("due_date", 1)
    conditions = await cursor.to_list(length=100)
    
    for condition in conditions:
        condition["id"] = str(condition["_id"])
        del condition["_id"]
    
    return [PaymentConditionResponse(**c) for c in conditions]


@router.put("/conditions/{condition_id}", response_model=PaymentConditionResponse)
async def update_payment_condition(
    condition_id: str,
    condition_update: PaymentConditionUpdate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a payment condition"""
    update_data = {k: v for k, v in condition_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await database.payment_conditions.update_one(
        {"_id": condition_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Payment condition not found")
    
    condition = await database.payment_conditions.find_one({"_id": condition_id})
    condition["id"] = str(condition["_id"])
    del condition["_id"]
    
    return PaymentConditionResponse(**condition)


@router.delete("/conditions/{condition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_condition(
    condition_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a payment condition"""
    result = await database.payment_conditions.delete_one({"_id": condition_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Payment condition not found")


# ========== Payment Methods Endpoints ==========

@router.post("/methods", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_method(
    method: PaymentMethodCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Add a new payment method for a user"""
    try:
        method_data = method.dict()
        method_data.update({
            "is_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        # If setting as default, unset other default methods
        if method.is_default:
            await database.payment_methods.update_many(
                {"user_id": method.user_id, "is_default": True},
                {"$set": {"is_default": False}}
            )
        
        result = await database.payment_methods.insert_one(method_data)
        method_data["id"] = str(result.inserted_id)
        
        return PaymentMethodResponse(**method_data)
    except Exception as e:
        logger.error(f"Error creating payment method: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/methods", response_model=List[PaymentMethodResponse])
async def get_user_payment_methods(
    user_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all payment methods for a user"""
    cursor = database.payment_methods.find({"user_id": user_id}).sort("created_at", -1)
    methods = await cursor.to_list(length=50)
    
    for method in methods:
        method["id"] = str(method["_id"])
        del method["_id"]
    
    return [PaymentMethodResponse(**m) for m in methods]


@router.get("/methods/{method_id}", response_model=PaymentMethodResponse)
async def get_payment_method(
    method_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific payment method"""
    method = await database.payment_methods.find_one({"_id": method_id})
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    method["id"] = str(method["_id"])
    del method["_id"]
    
    return PaymentMethodResponse(**method)


@router.put("/methods/{method_id}", response_model=PaymentMethodResponse)
async def update_payment_method(
    method_id: str,
    method_update: PaymentMethodUpdate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a payment method"""
    update_data = {k: v for k, v in method_update.dict().items() if v is not None}
    
    # If setting as default, unset other default methods
    if update_data.get("is_default"):
        method = await database.payment_methods.find_one({"_id": method_id})
        await database.payment_methods.update_many(
            {"user_id": method["user_id"], "is_default": True},
            {"$set": {"is_default": False}}
        )
    
    update_data["updated_at"] = datetime.utcnow()
    
    result = await database.payment_methods.update_one(
        {"_id": method_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    method = await database.payment_methods.find_one({"_id": method_id})
    method["id"] = str(method["_id"])
    del method["_id"]
    
    return PaymentMethodResponse(**method)


@router.delete("/methods/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_method(
    method_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a payment method"""
    result = await database.payment_methods.delete_one({"_id": method_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Payment method not found")


# ========== Payment Transactions Endpoints ==========

@router.post("/transactions", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment: PaymentCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Process a new payment"""
    try:
        payment_response = await payment_processor.process_payment(payment, database)
        return payment_response
    except PaymentGatewayError as e:
        logger.error(f"Payment processing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific payment transaction"""
    payment = await database.payments.find_one({"_id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment["id"] = str(payment["_id"])
    del payment["_id"]
    
    return PaymentResponse(**payment)


@router.get("/users/{user_id}/transactions", response_model=List[PaymentResponse])
async def get_user_payments(
    user_id: str,
    status: Optional[PaymentStatus] = None,
    limit: int = 50,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all payments for a user"""
    query = {"user_id": user_id}
    if status:
        query["status"] = status
    
    cursor = database.payments.find(query).sort("created_at", -1).limit(limit)
    payments = await cursor.to_list(length=limit)
    
    for payment in payments:
        payment["id"] = str(payment["_id"])
        del payment["_id"]
    
    return [PaymentResponse(**p) for p in payments]


@router.post("/transactions/{payment_id}/refund", response_model=PaymentRefundResponse)
async def refund_payment(
    payment_id: str,
    refund_data: PaymentRefundCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Process a refund for a payment"""
    try:
        result = await payment_processor.refund_payment(
            payment_id,
            refund_data.amount,
            refund_data.reason,
            database
        )
        
        refund_response = {
            "id": str(result.get("refund_id", "")),
            "payment_id": payment_id,
            "amount": refund_data.amount,
            "reason": refund_data.reason,
            "status": PaymentStatus.REFUNDED,
            "refund_id": result.get("refund_id"),
            "gateway_response": result,
            "processed_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        
        return PaymentRefundResponse(**refund_response)
    except PaymentGatewayError as e:
        logger.error(f"Refund processing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing refund: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/{payment_id}/status")
async def get_payment_status(
    payment_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get real-time payment status from gateway"""
    try:
        status = await payment_processor.get_payment_status(payment_id, database)
        return status
    except PaymentGatewayError as e:
        logger.error(f"Payment status check error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ========== Installments Endpoints ==========

@router.get("/conditions/{condition_id}/installments", response_model=List[InstallmentResponse])
async def get_installments(
    condition_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all installments for a payment condition"""
    cursor = database.installments.find({"payment_condition_id": condition_id}).sort("installment_number", 1)
    installments = await cursor.to_list(length=100)
    
    for installment in installments:
        installment["id"] = str(installment["_id"])
        del installment["_id"]
    
    return [InstallmentResponse(**i) for i in installments]


@router.put("/installments/{installment_id}/pay")
async def pay_installment(
    installment_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark an installment as paid"""
    installment = await database.installments.find_one({"_id": installment_id})
    if not installment:
        raise HTTPException(status_code=404, detail="Installment not found")
    
    await database.installments.update_one(
        {"_id": installment_id},
        {
            "$set": {
                "status": "paid",
                "paid_amount": installment["amount"],
                "paid_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Update payment condition
    await database.payment_conditions.update_one(
        {"_id": installment["payment_condition_id"]},
        {
            "$inc": {
                "paid_amount": installment["amount"],
                "remaining_amount": -installment["amount"]
            },
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {"message": "Installment paid successfully"}


# ========== Invoice Endpoints ==========

@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice: InvoiceCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new invoice"""
    try:
        # Calculate subtotal
        conditions = await database.payment_conditions.find(
            {"_id": {"$in": invoice.payment_condition_ids}}
        ).to_list(length=100)
        
        subtotal = sum(c["amount"] for c in conditions)
        tax_amount = subtotal * (invoice.tax_percentage / 100)
        discount_amount = subtotal * (invoice.discount_percentage / 100)
        total_amount = subtotal + tax_amount - discount_amount
        
        # Generate invoice number
        invoice_count = await database.invoices.count_documents({})
        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{invoice_count + 1:04d}"
        
        invoice_data = invoice.dict()
        invoice_data.update({
            "invoice_number": invoice_number,
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "discount_amount": discount_amount,
            "total_amount": total_amount,
            "paid_amount": 0.0,
            "status": "pending",
            "paid_at": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        result = await database.invoices.insert_one(invoice_data)
        invoice_data["id"] = str(result.inserted_id)
        
        return InvoiceResponse(**invoice_data)
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific invoice"""
    invoice = await database.invoices.find_one({"_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice["id"] = str(invoice["_id"])
    del invoice["_id"]
    
    return InvoiceResponse(**invoice)


@router.get("/users/{user_id}/invoices", response_model=List[InvoiceResponse])
async def get_user_invoices(
    user_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all invoices for a user"""
    cursor = database.invoices.find({"user_id": user_id}).sort("created_at", -1)
    invoices = await cursor.to_list(length=100)
    
    for invoice in invoices:
        invoice["id"] = str(invoice["_id"])
        del invoice["_id"]
    
    return [InvoiceResponse(**i) for i in invoices]


# ========== Subscription Endpoints ==========

@router.post("/subscriptions", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription: SubscriptionCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new subscription"""
    try:
        # Define plan pricing
        plan_pricing = {
            SubscriptionPlan.FREE: 0,
            SubscriptionPlan.BASIC: 9.99,
            SubscriptionPlan.PROFESSIONAL: 29.99,
            SubscriptionPlan.ENTERPRISE: 99.99
        }
        
        amount = plan_pricing.get(subscription.plan, 0)
        
        subscription_data = subscription.dict()
        subscription_data.update({
            "amount": amount,
            "currency": "USD",
            "billing_cycle": "monthly",
            "current_period_start": datetime.utcnow(),
            "current_period_end": datetime.utcnow() + timedelta(days=30),
            "trial_end_date": None,
            "cancel_at_period_end": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        result = await database.subscriptions.insert_one(subscription_data)
        subscription_data["id"] = str(result.inserted_id)
        
        return SubscriptionResponse(**subscription_data)
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific subscription"""
    subscription = await database.subscriptions.find_one({"_id": subscription_id})
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    subscription["id"] = str(subscription["_id"])
    del subscription["_id"]
    
    return SubscriptionResponse(**subscription)


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Cancel a subscription"""
    result = await database.subscriptions.update_one(
        {"_id": subscription_id},
        {
            "$set": {
                "cancel_at_period_end": True,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return {"message": "Subscription cancelled successfully"}


# ========== Webhook Endpoints ==========

@router.post("/webhooks/stripe")
async def stripe_webhook(
    payload: bytes,
    stripe_signature: str = Header(..., alias="Stripe-Signature"),
    database=Depends(get_db)
):
    """Handle Stripe webhook events"""
    try:
        from app.payment import StripePaymentGateway
        gateway = StripePaymentGateway()
        
        if not await gateway.verify_webhook_signature(payload, stripe_signature):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        # Process webhook event
        event_data = json.loads(payload.decode())
        
        # Store webhook event
        webhook_event = {
            "gateway": PaymentGateway.STRIPE,
            "event_type": event_data.get("type"),
            "event_id": event_data.get("id"),
            "data": event_data,
            "processed": False,
            "created_at": datetime.utcnow()
        }
        await database.webhook_events.insert_one(webhook_event)
        
        # Handle specific event types
        if event_data["type"] == "payment_intent.succeeded":
            await _handle_payment_success(event_data, database)
        elif event_data["type"] == "payment_intent.payment_failed":
            await _handle_payment_failure(event_data, database)
        elif event_data["type"] == "charge.refunded":
            await _handle_refund(event_data, database)
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhooks/paypal")
async def paypal_webhook(
    payload: bytes,
    database=Depends(get_db)
):
    """Handle PayPal webhook events"""
    try:
        from app.payment import PayPalPaymentGateway
        gateway = PayPalPaymentGateway()
        
        # Get PayPal headers
        headers = {
            "PAYPAL-AUTH-ALGO": Header(None, alias="PAYPAL-AUTH-ALGO"),
            "PAYPAL-CERT-URL": Header(None, alias="PAYPAL-CERT-URL"),
            "PAYPAL-TRANSMISSION-ID": Header(None, alias="PAYPAL-TRANSMISSION-ID"),
            "PAYPAL-TRANSMISSION-SIG": Header(None, alias="PAYPAL-TRANSMISSION-SIG"),
            "PAYPAL-TRANSMISSION-TIME": Header(None, alias="PAYPAL-TRANSMISSION-TIME"),
        }
        
        if not await gateway.verify_webhook_signature(payload, headers):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        event_data = json.loads(payload.decode())
        
        webhook_event = {
            "gateway": PaymentGateway.PAYPAL,
            "event_type": event_data.get("event_type"),
            "event_id": event_data.get("id"),
            "data": event_data,
            "processed": False,
            "created_at": datetime.utcnow()
        }
        await database.webhook_events.insert_one(webhook_event)
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"PayPal webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ========== Analytics Endpoints ==========

@router.get("/analytics", response_model=PaymentAnalytics)
async def get_payment_analytics(
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get payment analytics"""
    try:
        if not period_start:
            period_start = datetime.utcnow() - timedelta(days=30)
        if not period_end:
            period_end = datetime.utcnow()
        
        # Get payment statistics
        pipeline = [
            {"$match": {"created_at": {"$gte": period_start, "$lte": period_end}}},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total": {"$sum": "$amount"}
                }
            }
        ]
        
        results = await database.payments.aggregate(pipeline).to_list(length=100)
        
        total_payments = 0
        successful_payments = 0
        failed_payments = 0
        refunded_payments = 0
        
        for result in results:
            total_payments += result["total"]
            if result["_id"] == PaymentStatus.COMPLETED:
                successful_payments = result["total"]
            elif result["_id"] == PaymentStatus.FAILED:
                failed_payments = result["total"]
            elif result["_id"] == PaymentStatus.REFUNDED:
                refunded_payments = result["total"]
        
        # Payment method breakdown
        method_pipeline = [
            {"$match": {"created_at": {"$gte": period_start, "$lte": period_end}}},
            {
                "$group": {
                    "_id": "$payment_method_id",
                    "count": {"$sum": 1}
                }
            }
        ]
        method_results = await database.payments.aggregate(method_pipeline).to_list(length=100)
        payment_method_breakdown = {str(r["_id"]): r["count"] for r in method_results}
        
        # Gateway breakdown
        gateway_pipeline = [
            {"$match": {"created_at": {"$gte": period_start, "$lte": period_end}}},
            {
                "$group": {
                    "_id": "$gateway",
                    "count": {"$sum": 1}
                }
            }
        ]
        gateway_results = await database.payments.aggregate(gateway_pipeline).to_list(length=100)
        gateway_breakdown = {str(r["_id"]): r["count"] for r in gateway_results}
        
        # Daily trend
        daily_pipeline = [
            {"$match": {"created_at": {"$gte": period_start, "$lte": period_end}}},
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$created_at"},
                        "month": {"$month": "$created_at"},
                        "day": {"$dayOfMonth": "$created_at"}
                    },
                    "total": {"$sum": "$amount"},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        daily_results = await database.payments.aggregate(daily_pipeline).to_list(length=100)
        daily_payment_trend = [
            {
                "date": f"{r['_id']['year']}-{r['_id']['month']}-{r['_id']['day']}",
                "total": r["total"],
                "count": r["count"]
            }
            for r in daily_results
        ]
        
        analytics = {
            "total_payments": total_payments,
            "successful_payments": successful_payments,
            "failed_payments": failed_payments,
            "refunded_payments": refunded_payments,
            "average_payment_amount": successful_payments / (sum(r["count"] for r in results) or 1),
            "payment_method_breakdown": payment_method_breakdown,
            "gateway_breakdown": gateway_breakdown,
            "daily_payment_trend": daily_payment_trend,
            "period_start": period_start,
            "period_end": period_end
        }
        
        return PaymentAnalytics(**analytics)
    except Exception as e:
        logger.error(f"Error getting payment analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Helper Functions ==========

async def _handle_payment_success(event_data: dict, database):
    """Handle successful payment event"""
    payment_intent_id = event_data["data"]["object"]["id"]
    await database.payments.update_one(
        {"transaction_id": payment_intent_id},
        {
            "$set": {
                "status": PaymentStatus.COMPLETED,
                "paid_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )


async def _handle_payment_failure(event_data: dict, database):
    """Handle failed payment event"""
    payment_intent_id = event_data["data"]["object"]["id"]
    await database.payments.update_one(
        {"transaction_id": payment_intent_id},
        {
            "$set": {
                "status": PaymentStatus.FAILED,
                "updated_at": datetime.utcnow()
            }
        }
    )


async def _handle_refund(event_data: dict, database):
    """Handle refund event"""
    charge_id = event_data["data"]["object"]["id"]
    await database.payments.update_one(
        {"transaction_id": charge_id},
        {
            "$set": {
                "status": PaymentStatus.REFUNDED,
                "refunded_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )
