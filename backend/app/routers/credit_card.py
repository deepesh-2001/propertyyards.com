"""
Credit Card Router
Handles credit card management, reward points, cashback, and card recommendations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.schemas import (
    CreditCardCreate,
    CreditCardResponse,
    RewardTransactionCreate,
    RewardTransactionResponse,
    CashbackCreate,
    CashbackResponse,
    CreditCardRecommendation,
    CreditCardComparison,
    BestCreditCardCashback,
    PointsRedemptionCreate,
    PointsRedemptionResponse,
    RewardAnalytics,
    CreditCardType,
    CreditCardTier,
    RewardCategory,
    RewardTransactionType,
    CreditCardApplicationCreate,
    CreditCardApplicationResponse,
    PhoneVerification,
    PhoneVerificationResponse,
    OTPVerification,
    OTPVerificationResponse
)
from app.credit_card import credit_card_manager, credit_card_comparator
from app.auth import get_current_user
from app.feature_flags import require_feature_flag

router = APIRouter(prefix="/api/credit-cards", tags=["credit-cards"])


# ========== Credit Card Management Endpoints ==========

@router.post("/cards", response_model=CreditCardResponse, status_code=status.HTTP_201_CREATED)
@require_feature_flag("credit_card_management")
async def add_credit_card(
    card: CreditCardCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Add a new credit card"""
    try:
        card_data = card.dict()
        result = await credit_card_manager.add_credit_card(card_data, database)
        return CreditCardResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/{card_id}", response_model=CreditCardResponse)
@require_feature_flag("credit_card_management")
async def get_credit_card(
    card_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific credit card"""
    card = await database.credit_cards.find_one({"_id": card_id})
    if not card:
        raise HTTPException(status_code=404, detail="Credit card not found")
    
    card["id"] = str(card["_id"])
    del card["_id"]
    
    return CreditCardResponse(**card)


@router.get("/users/{user_id}/cards", response_model=List[CreditCardResponse])
@require_feature_flag("credit_card_management")
async def get_user_credit_cards(
    user_id: str,
    is_active: Optional[bool] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all credit cards for a user"""
    query = {"user_id": user_id}
    if is_active is not None:
        query["is_active"] = is_active
    
    cursor = database.credit_cards.find(query).sort("created_at", -1)
    cards = await cursor.to_list(length=20)
    
    for card in cards:
        card["id"] = str(card["_id"])
        del card["_id"]
    
    return [CreditCardResponse(**c) for c in cards]


# ========== Credit Card Application Endpoints ==========

@router.post("/applications", response_model=CreditCardApplicationResponse, status_code=status.HTTP_201_CREATED)
@require_feature_flag("credit_card_management")
async def apply_credit_card(
    application: CreditCardApplicationCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Apply for a new credit card"""
    try:
        # Check if user has access to apply for credit cards
        user = await database.users.find_one({"_id": current_user["user_id"]})
        if not user.get("can_apply_credit_cards", True):
            raise HTTPException(status_code=403, detail="Credit card application access restricted")
        
        application_data = application.dict()
        application_data["user_name"] = f"{user.get('first_name', '')} {user.get('last_name', '')}"
        application_data["status"] = "pending"
        application_data["phone_verified"] = False
        application_data["email_verified"] = False
        application_data["created_at"] = datetime.utcnow()
        application_data["updated_at"] = datetime.utcnow()
        
        result = await database.credit_card_applications.insert_one(application_data)
        application_data["id"] = str(result.inserted_id)
        
        return CreditCardApplicationResponse(**application_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-phone", response_model=PhoneVerificationResponse)
@require_feature_flag("credit_card_management")
async def verify_phone(
    verification: PhoneVerification,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Initiate phone verification with OTP"""
    try:
        import random
        
        verification_id = f"verify_{datetime.utcnow().timestamp()}"
        otp = str(random.randint(100000, 999999))
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Store verification record
        verification_record = {
            "verification_id": verification_id,
            "phone_number": verification.phone_number,
            "country_code": verification.country_code,
            "otp": otp,
            "expires_at": expires_at,
            "verified": False,
            "created_at": datetime.utcnow()
        }
        
        await database.phone_verifications.insert_one(verification_record)
        
        # In production, send OTP via SMS service
        # For now, log it (in production, use Twilio or similar)
        print(f"OTP for {verification.phone_number}: {otp}")
        
        return PhoneVerificationResponse(
            verification_id=verification_id,
            phone_number=verification.phone_number,
            status="pending",
            otp_sent=True,
            expires_at=expires_at,
            created_at=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-otp", response_model=OTPVerificationResponse)
@require_feature_flag("credit_card_management")
async def verify_otp(
    verification: OTPVerification,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Verify OTP for phone number"""
    try:
        # Get verification record
        verification_record = await database.phone_verifications.find_one({
            "verification_id": verification.verification_id
        })
        
        if not verification_record:
            raise HTTPException(status_code=404, detail="Verification record not found")
        
        # Check if expired
        if verification_record["expires_at"] < datetime.utcnow():
            raise HTTPException(status_code=400, detail="OTP has expired")
        
        # Verify OTP
        if verification_record["otp"] != verification.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        
        # Mark as verified
        await database.phone_verifications.update_one(
            {"verification_id": verification.verification_id},
            {
                "$set": {
                    "verified": True,
                    "verified_at": datetime.utcnow()
                }
            }
        )
        
        return OTPVerificationResponse(
            verified=True,
            phone_number=verification_record["phone_number"],
            verified_at=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/{application_id}", response_model=CreditCardApplicationResponse)
@require_feature_flag("credit_card_management")
async def get_credit_card_application(
    application_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get credit card application status"""
    application = await database.credit_card_applications.find_one({"_id": application_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application["id"] = str(application["_id"])
    del application["_id"]
    
    return CreditCardApplicationResponse(**application)


# ========== Reward Transaction Endpoints ==========

@router.post("/transactions", response_model=RewardTransactionResponse, status_code=status.HTTP_201_CREATED)
@require_feature_flag("credit_card_management")
async def record_reward_transaction(
    transaction: RewardTransactionCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Record a reward transaction"""
    try:
        transaction_data = transaction.dict()
        result = await credit_card_manager.record_reward_transaction(transaction_data, database)
        return RewardTransactionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/{card_id}/transactions", response_model=List[RewardTransactionResponse])
@require_feature_flag("credit_card_management")
async def get_card_transactions(
    card_id: str,
    transaction_type: Optional[RewardTransactionType] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all reward transactions for a card"""
    query = {"credit_card_id": card_id}
    if transaction_type:
        query["transaction_type"] = transaction_type
    
    cursor = database.reward_transactions.find(query).sort("transaction_date", -1)
    transactions = await cursor.to_list(length=100)
    
    for transaction in transactions:
        transaction["id"] = str(transaction["_id"])
        del transaction["_id"]
    
    return [RewardTransactionResponse(**t) for t in transactions]


# ========== Cashback Endpoints ==========

@router.post("/cashback", response_model=CashbackResponse, status_code=status.HTTP_201_CREATED)
@require_feature_flag("credit_card_management")
async def process_cashback(
    cashback: CashbackCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Process cashback using reward points"""
    try:
        cashback_data = cashback.dict()
        result = await credit_card_manager.process_cashback(cashback_data, database)
        return CashbackResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/{card_id}/cashback", response_model=List[CashbackResponse])
@require_feature_flag("credit_card_management")
async def get_card_cashback(
    card_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all cashback transactions for a card"""
    cursor = database.cashbacks.find({"credit_card_id": card_id}).sort("created_at", -1)
    cashbacks = await cursor.to_list(length=100)
    
    for cashback in cashbacks:
        cashback["id"] = str(cashback["_id"])
        del cashback["_id"]
    
    return [CashbackResponse(**c) for c in cashbacks]


# ========== Points Redemption Endpoints ==========

@router.post("/redemptions", response_model=PointsRedemptionResponse, status_code=status.HTTP_201_CREATED)
@require_feature_flag("credit_card_management")
async def redeem_points(
    redemption: PointsRedemptionCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Redeem reward points"""
    try:
        # Get credit card
        card = await database.credit_cards.find_one({"_id": redemption.credit_card_id})
        if not card:
            raise HTTPException(status_code=404, detail="Credit card not found")
        
        if card["points_balance"] < redemption.points:
            raise HTTPException(status_code=400, detail="Insufficient points balance")
        
        # Calculate points value
        from app.credit_card import reward_calculator
        points_value = reward_calculator.calculate_points_value(redemption.points)
        
        redemption_data = {
            **redemption.dict(),
            "card_name": card["card_name"],
            "points_value": points_value,
            "status": "processed",
            "processed_date": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        
        result = await database.points_redemptions.insert_one(redemption_data)
        redemption_data["id"] = str(result.inserted_id)
        
        # Update card points balance
        await database.credit_cards.update_one(
            {"_id": redemption.credit_card_id},
            {
                "$inc": {
                    "points_balance": -redemption.points,
                    "total_points_redeemed": redemption.points
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return PointsRedemptionResponse(**redemption_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/{card_id}/redemptions", response_model=List[PointsRedemptionResponse])
@require_feature_flag("credit_card_management")
async def get_card_redemptions(
    card_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all points redemptions for a card"""
    cursor = database.points_redemptions.find({"credit_card_id": card_id}).sort("created_at", -1)
    redemptions = await cursor.to_list(length=100)
    
    for redemption in redemptions:
        redemption["id"] = str(redemption["_id"])
        del redemption["_id"]
    
    return [PointsRedemptionResponse(**r) for r in redemptions]


# ========== Credit Card Comparison Endpoints ==========

@router.post("/compare", response_model=CreditCardComparison)
@require_feature_flag("credit_card_comparison")
async def compare_credit_cards(
    preferences: dict,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Compare credit cards based on preferences"""
    try:
        result = credit_card_comparator.compare_cards(preferences)
        return CreditCardComparison(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/best-card/{category}", response_model=CreditCardRecommendation)
@require_feature_flag("credit_card_comparison")
async def get_best_card_for_category(
    category: RewardCategory,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the best credit card for a specific category"""
    try:
        result = credit_card_comparator.get_best_card_for_category(category)
        if not result:
            raise HTTPException(status_code=404, detail="No card found for this category")
        return CreditCardRecommendation(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/best-cashback", response_model=List[BestCreditCardCashback])
@require_feature_flag("credit_card_comparison")
async def get_best_credit_cards_for_cashback(
    spend_amount: float = 2000,
    category: Optional[RewardCategory] = None,
    cashback_rate: float = 1.0,
    limit: int = 3,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        if spend_amount <= 0:
            raise HTTPException(status_code=400, detail="spend_amount must be greater than 0")
        if cashback_rate < 0:
            raise HTTPException(status_code=400, detail="cashback_rate must be greater than or equal to 0")
        if limit <= 0:
            raise HTTPException(status_code=400, detail="limit must be greater than 0")
        
        result = credit_card_comparator.get_best_cards_for_cashback(
            spend_amount=spend_amount,
            category=category,
            cashback_rate=cashback_rate
        )
        return [BestCreditCardCashback(**card) for card in result[:limit]]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations")
@require_feature_flag("credit_card_comparison")
async def get_card_recommendations(
    monthly_spend: float = 2000,
    max_annual_fee: float = 500,
    wants_welcome_bonus: bool = True,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get credit card recommendations based on spending habits"""
    try:
        preferences = {
            "monthly_spend": monthly_spend,
            "max_annual_fee": max_annual_fee,
            "wants_welcome_bonus": wants_welcome_bonus,
            "categories": [RewardCategory.SHOPPING, RewardCategory.DINING, RewardCategory.TRAVEL]
        }
        result = credit_card_comparator.compare_cards(preferences)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Reward Analytics Endpoints ==========

@router.get("/users/{user_id}/analytics", response_model=RewardAnalytics)
@require_feature_flag("reward_analytics")
async def get_reward_analytics(
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get reward analytics for a user"""
    try:
        analytics = await credit_card_manager.get_reward_analytics(
            user_id=user_id,
            database=database,
            start_date=start_date,
            end_date=end_date
        )
        return RewardAnalytics(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/returns/monthly")
@require_feature_flag("reward_analytics")
async def get_monthly_cashback_returns(
    user_id: str,
    year: Optional[int] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get monthly cashback returns for a user"""
    try:
        cards = await database.credit_cards.find({"user_id": user_id}).to_list(length=10)
        card_ids = [str(c["_id"]) for c in cards]
        
        query = {"credit_card_id": {"$in": card_ids}}
        if year:
            query["created_at"] = {"$gte": datetime(year, 1, 1), "$lte": datetime(year, 12, 31)}
        
        cashbacks = await database.cashbacks.find(query).to_list(length=1000)
        monthly_returns = credit_card_manager._calculate_monthly_cashback_returns(cashbacks)
        
        return {"monthly_returns": monthly_returns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/returns/quarterly")
async def get_quarterly_cashback_returns(
    user_id: str,
    year: Optional[int] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get quarterly cashback returns for a user"""
    try:
        cards = await database.credit_cards.find({"user_id": user_id}).to_list(length=10)
        card_ids = [str(c["_id"]) for c in cards]
        
        query = {"credit_card_id": {"$in": card_ids}}
        if year:
            query["created_at"] = {"$gte": datetime(year, 1, 1), "$lte": datetime(year, 12, 31)}
        
        cashbacks = await database.cashbacks.find(query).to_list(length=1000)
        quarterly_returns = credit_card_manager._calculate_quarterly_cashback_returns(cashbacks)
        
        return {"quarterly_returns": quarterly_returns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/returns/yearly")
async def get_yearly_cashback_returns(
    user_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get yearly cashback returns for a user"""
    try:
        cards = await database.credit_cards.find({"user_id": user_id}).to_list(length=10)
        card_ids = [str(c["_id"]) for c in cards]
        
        cashbacks = await database.cashbacks.find({"credit_card_id": {"$in": card_ids}}).to_list(length=1000)
        yearly_returns = credit_card_manager._calculate_yearly_cashback_returns(cashbacks)
        
        return {"yearly_returns": yearly_returns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/returns/total")
async def get_total_cashback_returns(
    user_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get total cashback returns for a user"""
    try:
        cards = await database.credit_cards.find({"user_id": user_id}).to_list(length=10)
        card_ids = [str(c["_id"]) for c in cards]
        
        cashbacks = await database.cashbacks.find({"credit_card_id": {"$in": card_ids}}).to_list(length=1000)
        total_returns = await credit_card_manager._calculate_total_returns(user_id, cards, cashbacks, database)
        
        return total_returns
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
