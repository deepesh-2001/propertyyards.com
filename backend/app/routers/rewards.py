"""
Rewards Router
API endpoints for rewards, commission, and referral system
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/rewards", tags=["rewards"])


# ========== Request Models ==========

class BankDetails(BaseModel):
    account_number: str
    ifsc_code: str
    account_holder_name: str
    bank_name: Optional[str] = None


class ConvertPointsRequest(BaseModel):
    points: float
    conversion_type: str = "wallet_credit"  # wallet_credit, bank_transfer, gift_card
    bank_details: Optional[BankDetails] = None  # Required for bank_transfer
    gift_card_type: Optional[str] = None  # Required for gift_card: amazon, flipkart, myntra, swiggy, zomato, bigbasket, uber


class ConvertCashbackRequest(BaseModel):
    cashback_amount: float


class ReferralSignupRequest(BaseModel):
    referral_code: str


# ========== Commission & Points Endpoints ==========

@router.get("/wallet")
async def get_wallet(
    current_user: dict = Depends(get_current_user)
):
    """Get user's rewards wallet summary"""
    try:
        from app.rewards_service import rewards_service
        
        user_id = str(current_user.get("_id"))
        summary = rewards_service.get_wallet_summary(user_id)
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions")
async def get_transactions(
    transaction_type: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get reward transaction history"""
    try:
        from app.rewards_service import rewards_service
        
        user_id = str(current_user.get("_id"))
        history = rewards_service.get_transaction_history(
            user_id=user_id,
            transaction_type=transaction_type,
            limit=limit
        )
        
        return {
            "user_id": user_id,
            "count": len(history),
            "transactions": history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/convert-points")
async def convert_points_to_cash(
    request: ConvertPointsRequest,
    current_user: dict = Depends(get_current_user)
):
    """Convert reward points to wallet credit, bank transfer, or gift card"""
    try:
        from app.rewards_service import rewards_service
        
        user_id = str(current_user.get("_id"))
        
        # Convert bank_details to dict if provided
        bank_details = None
        if request.bank_details:
            bank_details = {
                "account_number": request.bank_details.account_number,
                "ifsc_code": request.bank_details.ifsc_code,
                "account_holder_name": request.bank_details.account_holder_name,
                "bank_name": request.bank_details.bank_name
            }
        
        result = await rewards_service.convert_points_to_cash(
            user_id=user_id,
            points=request.points,
            conversion_type=request.conversion_type,
            bank_details=bank_details,
            gift_card_type=request.gift_card_type
        )
        
        # Custom message based on conversion type
        if request.conversion_type == "gift_card":
            message = f"{request.points} points converted to {result['gift_card_name']} worth ₹{result['gift_card_value']}"
        elif request.conversion_type == "bank_transfer":
            message = f"{request.points} points queued for bank transfer (₹{result['cash_value']}). Will be processed within 2-3 business days."
        else:
            message = f"{request.points} points converted to ₹{result['cash_value']} wallet credit"
        
        return {
            "success": True,
            "conversion": result,
            "message": message
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview-conversion")
async def preview_conversion(
    points: float,
    conversion_type: str = "wallet_credit",
    gift_card_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Preview conversion result before confirming"""
    try:
        from app.rewards_service import rewards_service
        
        user_id = str(current_user.get("_id"))
        wallet = rewards_service.get_or_create_wallet(user_id)
        tier_config = rewards_service.tier_config[wallet.tier]
        
        # Check available points
        if wallet.available_points < points:
            raise ValueError(f"Insufficient points. Available: {wallet.available_points}")
        
        # Calculate fees and value
        conversion_fee_rate = tier_config["conversion_fee"]
        
        if conversion_type == "bank_transfer":
            conversion_fee_rate += 0.02  # 2% bank fee
            
        conversion_fee = points * conversion_fee_rate
        net_points = points - conversion_fee
        base_value = net_points * rewards_service.points_to_inr_rate
        
        # Gift card value multiplier
        gift_cards = {
            "amazon": 1.0, "flipkart": 1.0, "myntra": 0.95,
            "swiggy": 1.0, "zomato": 1.0, "bigbasket": 0.98, "uber": 1.0
        }
        
        final_value = base_value
        if conversion_type == "gift_card" and gift_card_type:
            multiplier = gift_cards.get(gift_card_type, 1.0)
            final_value = base_value * multiplier
        
        return {
            "points": points,
            "conversion_type": conversion_type,
            "tier": wallet.tier.value,
            "conversion_fee_rate": conversion_fee_rate,
            "conversion_fee": round(conversion_fee, 2),
            "net_points": round(net_points, 2),
            "final_value": round(final_value, 2),
            "gift_card_type": gift_card_type,
            "available_points": wallet.available_points,
            "remaining_after_conversion": wallet.available_points - points
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/convert-cashback")
async def convert_cashback_to_points(
    request: ConvertCashbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """Convert cashback amount to reward points"""
    try:
        from app.rewards_service import rewards_service
        
        user_id = str(current_user.get("_id"))
        
        transaction = await rewards_service.convert_cashback_to_points(
            user_id=user_id,
            cashback_amount=request.cashback_amount
        )
        
        return {
            "success": True,
            "points_earned": transaction.points,
            "cashback_converted": request.cashback_amount,
            "message": f"₹{request.cashback_amount} cashback converted to {transaction.points} points"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Referral Endpoints ==========

@router.get("/referral/code")
async def get_referral_code(
    current_user: dict = Depends(get_current_user)
):
    """Get user's referral code"""
    try:
        from app.rewards_service import rewards_service
        
        user_id = str(current_user.get("_id"))
        code = rewards_service._get_user_referral_code(user_id)
        
        # Get referral stats
        wallet_summary = rewards_service.get_wallet_summary(user_id)
        
        return {
            "referral_code": code,
            "referral_link": f"https://propertyyards.com/signup?ref={code}",
            "stats": wallet_summary["referral"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/referral/signup")
async def process_referral_signup(
    request: ReferralSignupRequest,
    current_user: dict = Depends(get_current_user)
):
    """Process referral signup (called when new user signs up with referral code)"""
    try:
        from app.rewards_service import rewards_service
        
        user_id = str(current_user.get("_id"))
        
        # Find referrer from code
        if request.referral_code not in rewards_service.referral_codes:
            raise HTTPException(status_code=400, detail="Invalid referral code")
        
        referrer_id = rewards_service.referral_codes[request.referral_code]
        
        # Can't refer yourself
        if referrer_id == user_id:
            raise HTTPException(status_code=400, detail="Cannot use your own referral code")
        
        result = await rewards_service.process_referral_signup(
            referrer_id=referrer_id,
            referred_id=user_id,
            referral_code=request.referral_code
        )
        
        return {
            "success": True,
            "referrer_id": referrer_id,
            "referred_id": user_id,
            "referrer_points": result["referrer_points_earned"],
            "your_bonus": result["referred_points_earned"],
            "message": f"Referral processed! You received {result['referred_points_earned']} bonus points"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/referral/stats")
async def get_referral_stats(
    current_user: dict = Depends(get_current_user)
):
    """Get detailed referral statistics"""
    try:
        from app.rewards_service import rewards_service
        
        user_id = str(current_user.get("_id"))
        
        referrals = [
            r for r in rewards_service.referrals.values()
            if r.referrer_id == user_id
        ]
        
        return {
            "total_referrals": len(referrals),
            "active_referrals": len([r for r in referrals if r.status == "active"]),
            "total_earned": sum(r.reward_points for r in referrals),
            "referrals": [
                {
                    "referred_id": r.referred_id,
                    "status": r.status,
                    "points_earned": r.reward_points,
                    "date": r.created_at.isoformat() if r.created_at else None
                }
                for r in sorted(referrals, key=lambda x: x.created_at, reverse=True)
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Tier & Benefits Endpoints ==========

@router.get("/gift-cards")
async def get_gift_card_options(
    current_user: dict = Depends(get_current_user)
):
    """Get available gift card conversion options"""
    return {
        "gift_cards": [
            {"type": "amazon", "name": "Amazon Gift Card", "min_points": 500, "value_multiplier": 1.0},
            {"type": "flipkart", "name": "Flipkart Gift Card", "min_points": 500, "value_multiplier": 1.0},
            {"type": "myntra", "name": "Myntra Gift Card", "min_points": 300, "value_multiplier": 0.95},
            {"type": "swiggy", "name": "Swiggy Gift Card", "min_points": 200, "value_multiplier": 1.0},
            {"type": "zomato", "name": "Zomato Gift Card", "min_points": 200, "value_multiplier": 1.0},
            {"type": "bigbasket", "name": "BigBasket Gift Card", "min_points": 300, "value_multiplier": 0.98},
            {"type": "uber", "name": "Uber Gift Card", "min_points": 300, "value_multiplier": 1.0}
        ],
        "conversion_rate": "1 point = ₹1 (before fees)",
        "validity": "365 days from issue"
    }


@router.get("/tiers")
async def get_tier_info(
    current_user: dict = Depends(get_current_user)
):
    """Get information about all tiers and benefits"""
    try:
        from app.rewards_service import rewards_service, UserTier
        
        tiers = []
        for tier in UserTier:
            config = rewards_service.tier_config[tier]
            tiers.append({
                "name": tier.value,
                "min_points": config["min_points"],
                "commission_multiplier": config["commission_multiplier"],
                "cashback_bonus": config["cashback_bonus"],
                "referral_bonus_percent": config["referral_bonus_percent"],
                "conversion_fee": config["conversion_fee"],
                "max_monthly_conversion": config["max_monthly_conversion"]
            })
        
        # Sort by min_points
        tiers.sort(key=lambda x: x["min_points"])
        
        return {
            "tiers": tiers,
            "points_to_inr_rate": rewards_service.points_to_inr_rate,
            "inr_to_points_rate": rewards_service.inr_to_points_rate
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calculate-commission")
async def calculate_commission(
    amount: float,
    current_user: dict = Depends(get_current_user)
):
    """Calculate commission for a given transaction amount"""
    try:
        from app.rewards_service import rewards_service
        
        user_id = str(current_user.get("_id"))
        wallet = rewards_service.get_or_create_wallet(user_id)
        tier_config = rewards_service.tier_config[wallet.tier]
        
        base_commission = amount * rewards_service.commission_rate
        total_points = base_commission * tier_config["commission_multiplier"]
        
        return {
            "transaction_amount": amount,
            "base_commission_rate": rewards_service.commission_rate * 100,
            "base_commission_points": round(base_commission, 2),
            "tier": wallet.tier.value,
            "tier_multiplier": tier_config["commission_multiplier"],
            "total_points": round(total_points, 2),
            "effective_rate": (total_points / amount) * 100
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Admin Endpoints ==========

@router.post("/admin/process-commission")
async def admin_process_commission(
    user_id: str,
    transaction_id: str,
    transaction_type: str,
    amount: float,
    current_user: dict = Depends(get_current_user)
):
    """Admin: Manually process commission for a transaction"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        from app.rewards_service import rewards_service, TransactionType
        
        tx_type = TransactionType(transaction_type)
        
        reward_tx = await rewards_service.process_transaction_commission(
            user_id=user_id,
            transaction_id=transaction_id,
            transaction_type=tx_type,
            amount=amount
        )
        
        return {
            "success": True,
            "transaction_id": reward_tx.id,
            "points_awarded": reward_tx.points,
            "user_id": user_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/stats")
async def admin_stats(
    current_user: dict = Depends(get_current_user)
):
    """Admin: Get overall rewards statistics"""
    if current_user.get("role") not in ["admin", "finance"]:
        raise HTTPException(status_code=403, detail="Admin/Finance access required")
    
    try:
        from app.rewards_service import rewards_service
        from collections import defaultdict
        
        # Aggregate stats
        total_points_issued = sum(w.lifetime_earned for w in rewards_service.wallets.values())
        total_points_redeemed = sum(w.lifetime_redeemed for w in rewards_service.wallets.values())
        
        points_by_type = defaultdict(float)
        for tx in rewards_service.transactions.values():
            if tx.points > 0:
                points_by_type[tx.points_type.value] += tx.points
        
        return {
            "total_users": len(rewards_service.wallets),
            "total_referrals": len(rewards_service.referrals),
            "total_points_issued": round(total_points_issued, 2),
            "total_points_redeemed": round(total_points_redeemed, 2),
            "points_by_type": dict(points_by_type),
            "commission_rate": rewards_service.commission_rate * 100,
            "referral_signup_bonus": rewards_service.referral_signup_points
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/expire-points")
async def admin_expire_points(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Admin: Trigger points expiration (background task)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        from app.rewards_service import rewards_service
        
        background_tasks.add_task(rewards_service.expire_old_points)
        
        return {
            "message": "Points expiration task started",
            "status": "processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Webhook/Integration Endpoints ==========

@router.post("/webhook/transaction")
async def webhook_transaction_completed(
    user_id: str,
    transaction_id: str,
    transaction_type: str,
    amount: float,
    current_user: dict = Depends(get_current_user)
):
    """Webhook: Called when a transaction is completed to award commission"""
    # This should be secured with API key in production
    try:
        from app.rewards_service import rewards_service, TransactionType
        
        tx_type = TransactionType(transaction_type)
        
        reward_tx = await rewards_service.process_transaction_commission(
            user_id=user_id,
            transaction_id=transaction_id,
            transaction_type=tx_type,
            amount=amount
        )
        
        return {
            "success": True,
            "commission_processed": True,
            "points_awarded": reward_tx.points
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
