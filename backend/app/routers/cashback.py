"""
Cashback Router
API endpoints for cashback, bank offers, and rewards
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/cashback", tags=["cashback"])


class CalculateCashbackRequest(BaseModel):
    """Calculate cashback request"""
    amount: float
    payment_method: str  # cash, credit_card, debit_card, upi, net_banking, wallet, emi
    bank_name: Optional[str] = None
    card_type: Optional[str] = None  # credit, debit, visa, mastercard, rupay
    user_tier: str = "standard"  # standard, premium, gold


class RedeemCashbackRequest(BaseModel):
    """Redeem cashback request"""
    cashback_id: str
    redemption_type: str = "wallet_credit"  # wallet_credit, bank_transfer, discount


@router.post("/calculate")
async def calculate_cashback(
    request: CalculateCashbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """Calculate potential cashback for a transaction"""
    try:
        from app.cashback_service import cashback_service, PaymentMethod

        payment_method = PaymentMethod(request.payment_method)

        cashback_details = cashback_service.calculate_cashback(
            amount=request.amount,
            payment_method=payment_method,
            bank_name=request.bank_name,
            card_type=request.card_type,
            user_tier=request.user_tier
        )

        return {
            "original_amount": request.amount,
            "payment_method": request.payment_method,
            "bank_name": request.bank_name,
            "cashback_breakdown": {
                "base_cashback": round(cashback_details.get("base_cashback", 0), 2),
                "bank_offer_cashback": round(cashback_details.get("bank_offer_cashback", 0), 2),
                "tier_bonus": round(cashback_details.get("tier_bonus", 0), 2)
            },
            "total_cashback": cashback_details["total_cashback"],
            "final_amount_after_cashback": cashback_details.get("final_amount_after_cashback", request.amount),
            "cashback_percentage": round(cashback_details.get("cashback_rate", 0) * 100, 2),
            "applicable_offers": cashback_details.get("applicable_offers", [])
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid payment method: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_cashback(
    transaction_id: str,
    amount: float,
    payment_method: str,
    bank_name: Optional[str] = None,
    card_type: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user),
    database=Depends(get_db)
):
    """Process cashback for a completed transaction"""
    try:
        from app.cashback_service import cashback_service

        # Get user tier from user profile
        user_tier = current_user.get("tier", "standard")

        # Process cashback
        transaction = await cashback_service.process_cashback(
            user_id=str(current_user.get("_id")),
            transaction_id=transaction_id,
            amount=amount,
            payment_method=payment_method,
            bank_name=bank_name,
            card_type=card_type,
            user_tier=user_tier
        )

        if not transaction:
            return {
                "success": False,
                "message": "No cashback applicable for this transaction"
            }

        # Store in database
        await database.cashback_transactions.insert_one({
            "cashback_id": transaction.id,
            "user_id": transaction.user_id,
            "transaction_id": transaction.transaction_id,
            "original_amount": transaction.original_amount,
            "cashback_amount": transaction.cashback_amount,
            "cashback_percentage": transaction.cashback_percentage,
            "payment_method": transaction.payment_method.value,
            "bank_name": transaction.bank_name,
            "status": transaction.status.value,
            "created_at": transaction.created_at,
            "expires_at": transaction.expires_at,
            "metadata": transaction.metadata
        })

        return {
            "success": True,
            "cashback_id": transaction.id,
            "cashback_amount": transaction.cashback_amount,
            "status": transaction.status.value,
            "payment_method": payment_method,
            "expires_at": transaction.expires_at.isoformat() if transaction.expires_at else None,
            "message": f"₹{transaction.cashback_amount} cashback will be credited after transaction settlement"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_cashback_summary(
    current_user: dict = Depends(get_current_user)
):
    """Get user's cashback summary"""
    try:
        from app.cashback_service import cashback_service

        user_id = str(current_user.get("_id"))
        summary = cashback_service.get_user_cashback_summary(user_id)

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions")
async def get_cashback_transactions(
    status: Optional[str] = None,  # pending, confirmed, redeemed, expired
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    database=Depends(get_db)
):
    """Get user's cashback transaction history"""
    try:
        user_id = str(current_user.get("_id"))

        query = {"user_id": user_id}
        if status:
            query["status"] = status

        transactions = await database.cashback_transactions.find(
            query
        ).sort("created_at", -1).limit(limit).to_list(length=limit)

        return {
            "user_id": user_id,
            "count": len(transactions),
            "transactions": [
                {
                    "cashback_id": t["cashback_id"],
                    "transaction_id": t["transaction_id"],
                    "original_amount": t["original_amount"],
                    "cashback_amount": t["cashback_amount"],
                    "status": t["status"],
                    "payment_method": t["payment_method"],
                    "bank_name": t.get("bank_name"),
                    "created_at": t["created_at"].isoformat() if isinstance(t["created_at"], datetime) else t["created_at"],
                    "expires_at": t["expires_at"].isoformat() if isinstance(t.get("expires_at"), datetime) else t.get("expires_at")
                }
                for t in transactions
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/redeem")
async def redeem_cashback(
    request: RedeemCashbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """Redeem confirmed cashback"""
    try:
        from app.cashback_service import cashback_service

        user_id = str(current_user.get("_id"))

        result = await cashback_service.redeem_cashback(
            user_id=user_id,
            cashback_id=request.cashback_id,
            redemption_type=request.redemption_type
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Redemption failed"))

        return {
            "success": True,
            "cashback_id": request.cashback_id,
            "redemption_type": request.redemption_type,
            "amount": result["amount"],
            "message": result["message"],
            "reference_id": result.get("reference_id"),
            "coupon_code": result.get("coupon_code")
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bank-offers")
async def get_bank_offers(
    amount: Optional[float] = 0,
    bank_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get available bank and card offers"""
    try:
        from app.cashback_service import cashback_service

        offers = cashback_service.get_available_bank_offers(amount)

        # Filter by bank if specified
        if bank_name:
            offers = [o for o in offers if o["bank_name"].lower() == bank_name.lower()]

        return {
            "total_offers": len(offers),
            "amount": amount,
            "offers": offers
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommend-payment")
async def recommend_payment_method(
    amount: float,
    current_user: dict = Depends(get_current_user)
):
    """Get payment method recommendation for maximum cashback"""
    try:
        from app.cashback_service import cashback_service

        recommendation = cashback_service.get_payment_method_recommendation(amount)

        return recommendation

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cash-special")
async def get_cash_payment_offer(
    current_user: dict = Depends(get_current_user)
):
    """Get special cashback offer for cash payments (15-20%)"""
    try:
        from app.cashback_service import cashback_service

        return {
            "offer_type": "Cash Payment Special",
            "cashback_percentage_range": "15% - 20%",
            "min_cashback": f"₹{cashback_service.min_cashback}",
            "max_cashback": f"₹{cashback_service.max_cashback}",
            "validity": "365 days",
            "terms": [
                "Cashback varies between 15% and 20% randomly",
                "Minimum transaction amount: ₹100",
                "Cashback credited after transaction confirmation",
                "Valid for all property purchases and rentals"
            ],
            "example": {
                "amount": 100000,
                "cashback_range": "₹15,000 - ₹20,000",
                "final_cost": "₹80,000 - ₹85,000"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/expire-old")
async def expire_old_cashback(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Admin: Trigger expiration of old cashback (background task)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.cashback_service import cashback_service

        # Run in background
        background_tasks.add_task(cashback_service.expire_old_cashback)

        return {
            "message": "Cashback expiration task started",
            "status": "processing"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/stats")
async def get_cashback_stats(
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    database=Depends(get_db)
):
    """Admin: Get cashback statistics"""
    if current_user.get("role") not in ["admin", "finance"]:
        raise HTTPException(status_code=403, detail="Admin/Finance access required")

    try:
        from datetime import datetime, timedelta

        start_date = datetime.utcnow() - timedelta(days=days)

        # Aggregate stats
        pipeline = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total_amount": {"$sum": "$cashback_amount"}
                }
            }
        ]

        stats = await database.cashback_transactions.aggregate(pipeline).to_list(length=10)

        # Payment method breakdown
        method_pipeline = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {
                "$group": {
                    "_id": "$payment_method",
                    "count": {"$sum": 1},
                    "total_cashback": {"$sum": "$cashback_amount"}
                }
            }
        ]

        method_stats = await database.cashback_transactions.aggregate(method_pipeline).to_list(length=10)

        return {
            "period_days": days,
            "status_breakdown": {
                s["_id"]: {
                    "count": s["count"],
                    "total_amount": round(s["total_amount"], 2)
                }
                for s in stats
            },
            "payment_method_breakdown": {
                m["_id"]: {
                    "count": m["count"],
                    "total_cashback": round(m["total_cashback"], 2)
                }
                for m in method_stats
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from datetime import datetime
