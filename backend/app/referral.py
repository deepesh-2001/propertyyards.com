"""
Referral System Module
Manages user referrals, rewards, and tracking
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import logging
import secrets

logger = logging.getLogger(__name__)


class ReferralStatus(str, Enum):
    """Referral status"""
    PENDING = "pending"
    COMPLETED = "completed"
    REWARDED = "rewarded"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class RewardType(str, Enum):
    """Types of rewards"""
    CREDIT = "credit"
    DISCOUNT = "discount"
    CASHBACK = "cashback"
    PREMIUM_FEATURES = "premium_features"


class ReferralSystem:
    """Referral system management"""
    
    def __init__(self, database):
        self.db = database
        self.referrals_collection = database.referrals
        self.rewards_collection = database.referral_rewards
        self.settings_collection = database.referral_settings
    
    def generate_referral_code(self, user_id: str) -> str:
        """Generate unique referral code for user"""
        return f"REF{secrets.token_hex(4).upper()}"
    
    async def create_referral_code(self, user_id: str) -> Dict[str, Any]:
        """Create referral code for a user"""
        code = self.generate_referral_code(user_id)
        
        referral_code = {
            "user_id": user_id,
            "code": code,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow(),  # Never expires by default
            "is_active": True,
            "total_referrals": 0,
            "successful_referrals": 0,
            "total_earned": 0.0
        }
        
        # Check if user already has a referral code
        existing = await self.settings_collection.find_one({"user_id": user_id})
        if existing:
            return {"code": existing["code"], "message": "Referral code already exists"}
        
        result = await self.settings_collection.insert_one(referral_code)
        logger.info(f"Referral code created for user {user_id}: {code}")
        
        return {
            "id": str(result.inserted_id),
            "code": code,
            "message": "Referral code created successfully"
        }
    
    async def get_referral_code(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's referral code"""
        code = await self.settings_collection.find_one({"user_id": user_id})
        if code:
            code["id"] = str(code["_id"])
            del code["_id"]
        return code
    
    async def validate_referral_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Validate a referral code"""
        referral = await self.settings_collection.find_one({
            "code": code,
            "is_active": True
        })
        
        if not referral:
            return None
        
        # Check if expired
        if referral.get("expires_at") and referral["expires_at"] < datetime.utcnow():
            return None
        
        return {
            "referrer_id": referral["user_id"],
            "code": code,
            "is_valid": True
        }
    
    async def create_referral(
        self,
        referrer_id: str,
        referred_user_id: str,
        referral_code: str
    ) -> str:
        """Create a new referral record"""
        # Check if referral code is valid
        validation = await self.validate_referral_code(referral_code)
        if not validation:
            raise ValueError("Invalid or expired referral code")
        
        # Check if user was already referred
        existing = await self.referrals_collection.find_one({
            "referred_user_id": referred_user_id
        })
        if existing:
            raise ValueError("User has already been referred")
        
        referral = {
            "referrer_id": referrer_id,
            "referred_user_id": referred_user_id,
            "referral_code": referral_code,
            "status": ReferralStatus.PENDING,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "rewarded_at": None,
            "reward_amount": 0.0
        }
        
        result = await self.referrals_collection.insert_one(referral)
        
        # Update referrer's referral count
        await self.settings_collection.update_one(
            {"user_id": referrer_id},
            {"$inc": {"total_referrals": 1}}
        )
        
        logger.info(f"Referral created: {referrer_id} -> {referred_user_id}")
        return str(result.inserted_id)
    
    async def complete_referral(self, referral_id: str) -> bool:
        """Mark referral as completed (e.g., after referred user makes first purchase)"""
        referral = await self.referrals_collection.find_one({"_id": referral_id})
        if not referral:
            return False
        
        if referral["status"] != ReferralStatus.PENDING:
            return False
        
        result = await self.referrals_collection.update_one(
            {"_id": referral_id},
            {
                "$set": {
                    "status": ReferralStatus.COMPLETED,
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        # Update referrer's successful referral count
        await self.settings_collection.update_one(
            {"user_id": referral["referrer_id"]},
            {"$inc": {"successful_referrals": 1}}
        )
        
        logger.info(f"Referral completed: {referral_id}")
        return result.modified_count > 0
    
    async def reward_referral(
        self,
        referral_id: str,
        reward_type: RewardType,
        amount: float,
        description: str
    ) -> bool:
        """Reward a completed referral"""
        referral = await self.referrals_collection.find_one({"_id": referral_id})
        if not referral:
            return False
        
        if referral["status"] != ReferralStatus.COMPLETED:
            return False
        
        # Create reward record
        reward = {
            "referral_id": referral_id,
            "referrer_id": referral["referrer_id"],
            "reward_type": reward_type,
            "amount": amount,
            "description": description,
            "created_at": datetime.utcnow(),
            "is_claimed": False,
            "claimed_at": None
        }
        
        await self.rewards_collection.insert_one(reward)
        
        # Update referral status
        await self.referrals_collection.update_one(
            {"_id": referral_id},
            {
                "$set": {
                    "status": ReferralStatus.REWARDED,
                    "rewarded_at": datetime.utcnow(),
                    "reward_amount": amount
                }
            }
        )
        
        # Update referrer's total earned
        await self.settings_collection.update_one(
            {"user_id": referral["referrer_id"]},
            {"$inc": {"total_earned": amount}}
        )
        
        logger.info(f"Referral rewarded: {referral_id} - {amount}")
        return True
    
    async def get_user_referrals(
        self,
        user_id: str,
        status: Optional[ReferralStatus] = None
    ) -> List[Dict[str, Any]]:
        """Get referrals made by a user"""
        query_filter = {"referrer_id": user_id}
        if status:
            query_filter["status"] = status
        
        cursor = self.referrals_collection.find(query_filter).sort("created_at", -1)
        referrals = await cursor.to_list(length=None)
        
        for referral in referrals:
            referral["id"] = str(referral["_id"])
            del referral["_id"]
        
        return referrals
    
    async def get_user_rewards(self, user_id: str) -> List[Dict[str, Any]]:
        """Get rewards earned by a user"""
        cursor = self.rewards_collection.find({"referrer_id": user_id}).sort("created_at", -1)
        rewards = await cursor.to_list(length=None)
        
        for reward in rewards:
            reward["id"] = str(reward["_id"])
            del reward["_id"]
        
        return rewards
    
    async def claim_reward(self, reward_id: str) -> bool:
        """Claim a reward"""
        result = await self.rewards_collection.update_one(
            {"_id": reward_id, "is_claimed": False},
            {
                "$set": {
                    "is_claimed": True,
                    "claimed_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Reward claimed: {reward_id}")
        return result.modified_count > 0
    
    async def get_referral_stats(self, user_id: str) -> Dict[str, Any]:
        """Get referral statistics for a user"""
        referral_code = await self.get_referral_code(user_id)
        
        referrals = await self.get_user_referrals(user_id)
        rewards = await self.get_user_rewards(user_id)
        
        total_earned = sum(r["amount"] for r in rewards if not r.get("is_claimed"))
        claimed_rewards = sum(r["amount"] for r in rewards if r.get("is_claimed"))
        
        return {
            "referral_code": referral_code["code"] if referral_code else None,
            "total_referrals": len(referrals),
            "successful_referrals": len([r for r in referrals if r["status"] == ReferralStatus.COMPLETED]),
            "completed_referrals": len([r for r in referrals if r["status"] == ReferralStatus.REWARDED]),
            "pending_rewards": total_earned,
            "claimed_rewards": claimed_rewards,
            "available_rewards": total_earned
        }
    
    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get referral leaderboard"""
        pipeline = [
            {"$sort": {"successful_referrals": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "user_id": 1,
                    "code": 1,
                    "total_referrals": 1,
                    "successful_referrals": 1,
                    "total_earned": 1
                }
            }
        ]
        
        results = await self.settings_collection.aggregate(pipeline).to_list(length=limit)
        
        for result in results:
            result["id"] = str(result["_id"])
            del result["_id"]
        
        return results


class ReferralSettings:
    """Referral system settings"""
    
    def __init__(self, database):
        self.db = database
        self.collection = database.referral_config
    
    async def get_settings(self) -> Dict[str, Any]:
        """Get referral system settings"""
        settings = await self.collection.find_one({"_id": "config"})
        if not settings:
            # Create default settings
            default_settings = {
                "_id": "config",
                "enabled": True,
                "reward_amount": 50.0,
                "reward_type": RewardType.CREDIT,
                "min_purchase_amount": 100.0,
                "referral_bonus_percentage": 10.0,
                "max_referrals_per_user": 100,
                "referral_expiry_days": 365
            }
            await self.collection.insert_one(default_settings)
            return default_settings
        
        settings["id"] = str(settings["_id"])
        del settings["_id"]
        return settings
    
    async def update_settings(self, settings_data: Dict[str, Any]) -> bool:
        """Update referral system settings"""
        result = await self.collection.update_one(
            {"_id": "config"},
            {"$set": settings_data}
        )
        logger.info("Referral settings updated")
        return result.modified_count > 0
