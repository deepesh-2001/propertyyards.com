"""
Referral Router
Endpoints for referral system
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_database
from app.referral import ReferralSystem, ReferralSettings, ReferralStatus, RewardType
from app.schemas import (
    ReferralCodeCreate, ReferralCodeResponse, ReferralCreate, ReferralResponse,
    RewardCreate, RewardResponse, ReferralStats, ReferralSettings as ReferralSettingsSchema
)
from app.auth import decode_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/referrals", tags=["Referrals"])


def get_current_user(authorization: str = None) -> dict:
    """Extract current user from authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token = authorization.split(" ")[1]
        token_data = decode_token(token)
        if token_data:
            return {"user_id": token_data.user_id, "email": token_data.email, "role": token_data.role}
    except Exception:
        pass

    raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/code", response_model=ReferralCodeResponse)
async def create_referral_code(
    authorization: str = None,
    db = Depends(get_database)
):
    """Create referral code for current user"""
    current_user = get_current_user(authorization)
    
    referral_system = ReferralSystem(db)
    result = await referral_system.create_referral_code(current_user["user_id"])
    
    if "code" in result:
        code_data = await referral_system.get_referral_code(current_user["user_id"])
        return ReferralCodeResponse(**code_data)
    
    raise HTTPException(status_code=400, detail=result.get("message", "Failed to create referral code"))


@router.get("/code", response_model=ReferralCodeResponse)
async def get_referral_code(
    authorization: str = None,
    db = Depends(get_database)
):
    """Get current user's referral code"""
    current_user = get_current_user(authorization)
    
    referral_system = ReferralSystem(db)
    code_data = await referral_system.get_referral_code(current_user["user_id"])
    
    if not code_data:
        raise HTTPException(status_code=404, detail="Referral code not found")
    
    return ReferralCodeResponse(**code_data)


@router.get("/validate/{code}")
async def validate_referral_code(
    code: str,
    db = Depends(get_database)
):
    """Validate a referral code"""
    referral_system = ReferralSystem(db)
    validation = await referral_system.validate_referral_code(code)
    
    if not validation:
        raise HTTPException(status_code=400, detail="Invalid or expired referral code")
    
    return validation


@router.post("/create", response_model=ReferralResponse)
async def create_referral(
    referral_data: ReferralCreate,
    authorization: str = None,
    db = Depends(get_database)
):
    """Create a new referral"""
    current_user = get_current_user(authorization)
    
    referral_system = ReferralSystem(db)
    try:
        referral_id = await referral_system.create_referral(
            referral_data.referrer_id,
            referral_data.referred_user_id,
            referral_data.referral_code
        )
        
        referral = await referral_system.referrals_collection.find_one({"_id": referral_id})
        referral["id"] = str(referral["_id"])
        del referral["_id"]
        
        return ReferralResponse(**referral)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{referral_id}/complete")
async def complete_referral(
    referral_id: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Mark referral as completed"""
    current_user = get_current_user(authorization)
    
    referral_system = ReferralSystem(db)
    completed = await referral_system.complete_referral(referral_id)
    
    if not completed:
        raise HTTPException(status_code=404, detail="Referral not found or cannot be completed")
    
    return {"message": "Referral completed successfully"}


@router.post("/{referral_id}/reward")
async def reward_referral(
    referral_id: str,
    reward_data: RewardCreate,
    authorization: str = None,
    db = Depends(get_database)
):
    """Reward a completed referral"""
    current_user = get_current_user(authorization)
    
    referral_system = ReferralSystem(db)
    rewarded = await referral_system.reward_referral(
        referral_id,
        reward_data.reward_type,
        reward_data.amount,
        reward_data.description
    )
    
    if not rewarded:
        raise HTTPException(status_code=400, detail="Referral cannot be rewarded")
    
    return {"message": "Referral rewarded successfully"}


@router.get("/my-referrals", response_model=list[ReferralResponse])
async def get_my_referrals(
    status: ReferralStatus = None,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get referrals made by current user"""
    current_user = get_current_user(authorization)
    
    referral_system = ReferralSystem(db)
    referrals = await referral_system.get_user_referrals(current_user["user_id"], status)
    
    return [ReferralResponse(**ref) for ref in referrals]


@router.get("/my-rewards", response_model=list[RewardResponse])
async def get_my_rewards(
    authorization: str = None,
    db = Depends(get_database)
):
    """Get rewards earned by current user"""
    current_user = get_current_user(authorization)
    
    referral_system = ReferralSystem(db)
    rewards = await referral_system.get_user_rewards(current_user["user_id"])
    
    return [RewardResponse(**reward) for reward in rewards]


@router.post("/rewards/{reward_id}/claim")
async def claim_reward(
    reward_id: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Claim a reward"""
    current_user = get_current_user(authorization)
    
    referral_system = ReferralSystem(db)
    claimed = await referral_system.claim_reward(reward_id)
    
    if not claimed:
        raise HTTPException(status_code=400, detail="Reward cannot be claimed")
    
    return {"message": "Reward claimed successfully"}


@router.get("/stats", response_model=ReferralStats)
async def get_referral_stats(
    authorization: str = None,
    db = Depends(get_database)
):
    """Get referral statistics for current user"""
    current_user = get_current_user(authorization)
    
    referral_system = ReferralSystem(db)
    stats = await referral_system.get_referral_stats(current_user["user_id"])
    
    return ReferralStats(**stats)


@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = 10,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get referral leaderboard"""
    current_user = get_current_user(authorization)
    
    referral_system = ReferralSystem(db)
    leaderboard = await referral_system.get_leaderboard(limit)
    
    return leaderboard


@router.get("/settings", response_model=ReferralSettingsSchema)
async def get_referral_settings(
    authorization: str = None,
    db = Depends(get_database)
):
    """Get referral system settings"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    referral_settings = ReferralSettings(db)
    settings = await referral_settings.get_settings()
    
    return ReferralSettingsSchema(**settings)


@router.put("/settings")
async def update_referral_settings(
    settings_data: ReferralSettingsSchema,
    authorization: str = None,
    db = Depends(get_database)
):
    """Update referral system settings"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    referral_settings = ReferralSettings(db)
    updated = await referral_settings.update_settings(settings_data.dict())
    
    if not updated:
        raise HTTPException(status_code=400, detail="Failed to update settings")
    
    return {"message": "Referral settings updated successfully"}
