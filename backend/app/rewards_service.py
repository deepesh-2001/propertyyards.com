"""
Rewards, Commission & Referral Service
Comprehensive rewards system with:
- 0.1% commission on all transactions
- Referral points system
- Reward points conversion
- Tier-based multipliers
- Rewards wallet
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import random

logger = logging.getLogger(__name__)


class TransactionType(Enum):
    """Types of transactions"""
    PROPERTY_PURCHASE = "property_purchase"
    PROPERTY_RENTAL = "property_rental"
    FLIGHT_BOOKING = "flight_booking"
    SERVICE_FEE = "service_fee"
    COMMISSION = "commission"
    REFERRAL = "referral"
    POINTS_REDEMPTION = "points_redemption"
    CASHBACK = "cashback"


class PointsType(Enum):
    """Types of reward points"""
    COMMISSION_POINTS = "commission_points"  # 0.1% commission
    REFERRAL_POINTS = "referral_points"      # Points from referrals
    CASHBACK_POINTS = "cashback_points"      # Converted cashback
    BONUS_POINTS = "bonus_points"           # Promotional bonus
    TIER_BONUS = "tier_bonus"               # Tier-based bonus


class UserTier(Enum):
    """User tiers with benefits"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


@dataclass
class RewardTransaction:
    """A rewards transaction record"""
    id: str
    user_id: str
    transaction_type: TransactionType
    points_type: PointsType
    points: float
    amount: float  # Original transaction amount
    description: str
    reference_id: Optional[str] = None  # Related transaction ID
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    redeemed: bool = False
    redeemed_at: Optional[datetime] = None
    redeemed_for: Optional[str] = None  # What points were redeemed for

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class ReferralRecord:
    """Referral tracking record"""
    id: str
    referrer_id: str  # User who referred
    referred_id: str  # User who was referred
    status: str  # pending, active, inactive
    referral_code: str
    reward_points: float = 0
    created_at: datetime = None
    activated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class UserRewardsWallet:
    """User's rewards wallet"""
    user_id: str
    total_points: float = 0
    available_points: float = 0
    pending_points: float = 0
    redeemed_points: float = 0
    expired_points: float = 0
    
    # Points by type
    commission_points: float = 0
    referral_points: float = 0
    cashback_points: float = 0
    bonus_points: float = 0
    
    tier: UserTier = UserTier.BRONZE
    tier_progress: float = 0  # Progress to next tier (0-100)
    
    lifetime_earned: float = 0
    lifetime_redeemed: float = 0
    
    updated_at: datetime = None

    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


class RewardsService:
    """Comprehensive rewards and commission service"""

    def __init__(self):
        self.enabled = True
        
        # Commission rate: 0.1%
        self.commission_rate = 0.001  # 0.1%
        
        # Referral rewards
        self.referral_signup_points = 500  # Points for referrer when signup
        self.referral_first_transaction_points = 1000  # Points for first transaction
        self.referred_user_bonus = 200  # Points for new user
        
        # Points conversion rates
        self.points_to_inr_rate = 1.0  # 1 point = ₹1
        self.inr_to_points_rate = 1.0  # ₹1 = 1 point
        
        # Tier configuration
        self.tier_config = {
            UserTier.BRONZE: {
                "min_points": 0,
                "commission_multiplier": 1.0,
                "cashback_bonus": 0,
                "referral_bonus_percent": 0,
                "conversion_fee": 0.10,  # 10% fee
                "max_monthly_conversion": 10000
            },
            UserTier.SILVER: {
                "min_points": 5000,
                "commission_multiplier": 1.25,  # 25% bonus
                "cashback_bonus": 2,  # Extra 2% cashback
                "referral_bonus_percent": 10,  # 10% extra on referrals
                "conversion_fee": 0.05,  # 5% fee
                "max_monthly_conversion": 25000
            },
            UserTier.GOLD: {
                "min_points": 20000,
                "commission_multiplier": 1.5,  # 50% bonus
                "cashback_bonus": 5,  # Extra 5% cashback
                "referral_bonus_percent": 25,  # 25% extra on referrals
                "conversion_fee": 0.02,  # 2% fee
                "max_monthly_conversion": 50000
            },
            UserTier.PLATINUM: {
                "min_points": 75000,
                "commission_multiplier": 2.0,  # 100% bonus
                "cashback_bonus": 8,  # Extra 8% cashback
                "referral_bonus_percent": 50,  # 50% extra on referrals
                "conversion_fee": 0.0,  # No fee
                "max_monthly_conversion": 100000
            },
            UserTier.DIAMOND: {
                "min_points": 200000,
                "commission_multiplier": 3.0,  # 200% bonus
                "cashback_bonus": 10,  # Extra 10% cashback
                "referral_bonus_percent": 100,  # Double referrals
                "conversion_fee": 0.0,  # No fee
                "max_monthly_conversion": 250000
            }
        }
        
        # Point expiry (365 days)
        self.points_expiry_days = 365
        
        # Storage
        self.wallets: Dict[str, UserRewardsWallet] = {}
        self.transactions: Dict[str, RewardTransaction] = {}
        self.referrals: Dict[str, ReferralRecord] = {}
        self.referral_codes: Dict[str, str] = {}  # code -> user_id
        
        # Track monthly conversions per user
        self.monthly_conversions: Dict[str, float] = {}  # user_id -> amount

    async def initialize(self):
        """Initialize rewards service"""
        logger.info("Rewards Service initialized")
        logger.info(f"Commission rate: {self.commission_rate*100}%")
        logger.info(f"Referral signup bonus: {self.referral_signup_points} points")

    def get_or_create_wallet(self, user_id: str) -> UserRewardsWallet:
        """Get or create user wallet"""
        if user_id not in self.wallets:
            self.wallets[user_id] = UserRewardsWallet(user_id=user_id)
        return self.wallets[user_id]

    async def process_transaction_commission(
        self,
        user_id: str,
        transaction_id: str,
        transaction_type: TransactionType,
        amount: float
    ) -> RewardTransaction:
        """Process 0.1% commission on transaction"""
        try:
            wallet = self.get_or_create_wallet(user_id)
            tier_config = self.tier_config[wallet.tier]
            
            # Calculate base commission (0.1%)
            base_commission = amount * self.commission_rate
            
            # Apply tier multiplier
            multiplier = tier_config["commission_multiplier"]
            total_points = base_commission * multiplier
            
            # Create transaction record
            reward_tx = RewardTransaction(
                id=f"comm_{transaction_id}",
                user_id=user_id,
                transaction_type=transaction_type,
                points_type=PointsType.COMMISSION_POINTS,
                points=round(total_points, 2),
                amount=amount,
                description=f"Commission: {self.commission_rate*100}% of ₹{amount} (Tier: {wallet.tier.value}, Multiplier: {multiplier}x)",
                reference_id=transaction_id,
                expires_at=datetime.utcnow() + timedelta(days=self.points_expiry_days)
            )
            
            # Update wallet
            wallet.commission_points += total_points
            wallet.total_points += total_points
            wallet.available_points += total_points
            wallet.lifetime_earned += total_points
            wallet.updated_at = datetime.utcnow()
            
            # Store transaction
            self.transactions[reward_tx.id] = reward_tx
            
            # Check tier upgrade
            await self._check_tier_upgrade(user_id)
            
            logger.info(f"Commission processed: ₹{amount} -> {total_points} points for user {user_id}")
            return reward_tx
            
        except Exception as e:
            logger.error(f"Commission processing failed: {e}")
            raise

    async def process_referral_signup(
        self,
        referrer_id: str,
        referred_id: str,
        referral_code: str
    ) -> Dict[str, Any]:
        """Process referral signup rewards"""
        try:
            # Verify referral code
            if referral_code not in self.referral_codes:
                raise ValueError("Invalid referral code")
            
            expected_referrer = self.referral_codes[referral_code]
            if expected_referrer != referrer_id:
                raise ValueError("Referral code mismatch")
            
            # Create referral record
            referral = ReferralRecord(
                id=f"ref_{referred_id}",
                referrer_id=referrer_id,
                referred_id=referred_id,
                status="active",
                referral_code=referral_code,
                reward_points=self.referral_signup_points,
                activated_at=datetime.utcnow()
            )
            self.referrals[referred_id] = referral
            
            # Reward referrer
            referrer_wallet = self.get_or_create_wallet(referrer_id)
            referrer_config = self.tier_config[referrer_wallet.tier]
            
            # Apply referral bonus percentage
            bonus_points = self.referral_signup_points * (1 + referrer_config["referral_bonus_percent"] / 100)
            
            reward_tx = RewardTransaction(
                id=f"ref_bonus_{referred_id}",
                user_id=referrer_id,
                transaction_type=TransactionType.REFERRAL,
                points_type=PointsType.REFERRAL_POINTS,
                points=round(bonus_points, 2),
                amount=0,
                description=f"Referral bonus: User {referred_id} signed up (Tier bonus: {referrer_config['referral_bonus_percent']}%)",
                reference_id=referred_id
            )
            
            referrer_wallet.referral_points += bonus_points
            referrer_wallet.total_points += bonus_points
            referrer_wallet.available_points += bonus_points
            referrer_wallet.lifetime_earned += bonus_points
            referrer_wallet.updated_at = datetime.utcnow()
            
            self.transactions[reward_tx.id] = reward_tx
            
            # Reward new user
            referred_wallet = self.get_or_create_wallet(referred_id)
            welcome_bonus = RewardTransaction(
                id=f"welcome_{referred_id}",
                user_id=referred_id,
                transaction_type=TransactionType.REFERRAL,
                points_type=PointsType.BONUS_POINTS,
                points=self.referred_user_bonus,
                amount=0,
                description=f"Welcome bonus for using referral code"
            )
            
            referred_wallet.bonus_points += self.referred_user_bonus
            referred_wallet.total_points += self.referred_user_bonus
            referred_wallet.available_points += self.referred_user_bonus
            referred_wallet.lifetime_earned += self.referred_user_bonus
            referred_wallet.updated_at = datetime.utcnow()
            
            self.transactions[welcome_bonus.id] = welcome_bonus
            
            # Check tier upgrade for referrer
            await self._check_tier_upgrade(referrer_id)
            
            logger.info(f"Referral processed: {referrer_id} -> {referred_id}")
            
            return {
                "referrer_points_earned": bonus_points,
                "referred_points_earned": self.referred_user_bonus,
                "referral_id": referral.id
            }
            
        except Exception as e:
            logger.error(f"Referral processing failed: {e}")
            raise

    async def process_referral_transaction(
        self,
        referrer_id: str,
        referred_id: str,
        transaction_amount: float
    ) -> Optional[RewardTransaction]:
        """Reward referrer when referred user makes first transaction"""
        try:
            referral = self.referrals.get(referred_id)
            if not referral or referral.status != "active":
                return None
            
            # Check if first transaction reward already given
            if referral.reward_points > self.referral_signup_points:
                return None
            
            referrer_wallet = self.get_or_create_wallet(referrer_id)
            referrer_config = self.tier_config[referrer_wallet.tier]
            
            # First transaction bonus
            bonus_points = self.referral_first_transaction_points * (1 + referrer_config["referral_bonus_percent"] / 100)
            
            reward_tx = RewardTransaction(
                id=f"ref_tx_{referred_id}_{datetime.utcnow().timestamp()}",
                user_id=referrer_id,
                transaction_type=TransactionType.REFERRAL,
                points_type=PointsType.REFERRAL_POINTS,
                points=round(bonus_points, 2),
                amount=transaction_amount,
                description=f"First transaction bonus from referral {referred_id}: ₹{transaction_amount}"
            )
            
            referrer_wallet.referral_points += bonus_points
            referrer_wallet.total_points += bonus_points
            referrer_wallet.available_points += bonus_points
            referrer_wallet.lifetime_earned += bonus_points
            referrer_wallet.updated_at = datetime.utcnow()
            
            self.transactions[reward_tx.id] = reward_tx
            
            # Update referral record
            referral.reward_points += bonus_points
            
            logger.info(f"Referral transaction bonus: {bonus_points} points to {referrer_id}")
            return reward_tx
            
        except Exception as e:
            logger.error(f"Referral transaction processing failed: {e}")
            return None

    def generate_referral_code(self, user_id: str) -> str:
        """Generate unique referral code for user"""
        # Create code based on user_id hash
        hash_obj = hashlib.md5(user_id.encode())
        code = f"PY{hash_obj.hexdigest()[:6].upper()}"
        
        self.referral_codes[code] = user_id
        return code

    async def convert_points_to_cash(
        self,
        user_id: str,
        points: float,
        conversion_type: str = "wallet_credit",  # wallet_credit, bank_transfer, gift_card
        bank_details: Optional[Dict] = None,
        gift_card_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convert reward points to cash, bank transfer, or gift card"""
        try:
            wallet = self.get_or_create_wallet(user_id)
            tier_config = self.tier_config[wallet.tier]
            
            # Check available points
            if wallet.available_points < points:
                raise ValueError(f"Insufficient points. Available: {wallet.available_points}")
            
            # Check monthly conversion limit
            monthly_converted = self.monthly_conversions.get(user_id, 0)
            if monthly_converted + points > tier_config["max_monthly_conversion"]:
                raise ValueError(f"Monthly conversion limit exceeded. Max: {tier_config['max_monthly_conversion']}")
            
            # Calculate conversion based on type
            if conversion_type == "gift_card":
                result = await self._convert_to_gift_card(user_id, points, gift_card_type, wallet, tier_config)
            elif conversion_type == "bank_transfer":
                result = await self._convert_to_bank_transfer(user_id, points, bank_details, wallet, tier_config)
            else:  # wallet_credit
                result = await self._convert_to_wallet_credit(user_id, points, wallet, tier_config)
            
            return result
            
        except Exception as e:
            logger.error(f"Points conversion failed: {e}")
            raise

    async def _convert_to_wallet_credit(
        self,
        user_id: str,
        points: float,
        wallet: UserRewardsWallet,
        tier_config: Dict
    ) -> Dict[str, Any]:
        """Convert points to wallet credit (instant)"""
        conversion_fee = points * tier_config["conversion_fee"]
        net_points = points - conversion_fee
        cash_value = net_points * self.points_to_inr_rate
        
        # Create redemption transaction
        redemption_tx = RewardTransaction(
            id=f"redemption_wallet_{datetime.utcnow().timestamp()}_{user_id}",
            user_id=user_id,
            transaction_type=TransactionType.POINTS_REDEMPTION,
            points_type=PointsType.COMMISSION_POINTS,
            points=-points,
            amount=cash_value,
            description=f"Points converted to wallet credit: {points} points -> ₹{cash_value}",
            redeemed=True,
            redeemed_at=datetime.utcnow(),
            redeemed_for="wallet_credit"
        )
        
        # Update wallet
        wallet.available_points -= points
        wallet.redeemed_points += points
        wallet.lifetime_redeemed += points
        wallet.updated_at = datetime.utcnow()
        
        self.monthly_conversions[user_id] = self.monthly_conversions.get(user_id, 0) + points
        self.transactions[redemption_tx.id] = redemption_tx
        
        logger.info(f"Points converted to wallet: {points} -> ₹{cash_value} for user {user_id}")
        
        return {
            "points_converted": points,
            "conversion_fee": conversion_fee,
            "net_points": net_points,
            "cash_value": round(cash_value, 2),
            "conversion_type": "wallet_credit",
            "remaining_points": wallet.available_points,
            "processed_at": datetime.utcnow().isoformat(),
            "status": "completed"
        }

    async def _convert_to_bank_transfer(
        self,
        user_id: str,
        points: float,
        bank_details: Optional[Dict],
        wallet: UserRewardsWallet,
        tier_config: Dict
    ) -> Dict[str, Any]:
        """Convert points to bank transfer (2-3 business days)"""
        if not bank_details:
            raise ValueError("Bank details required for bank transfer")
        
        # Validate bank details
        required_fields = ["account_number", "ifsc_code", "account_holder_name"]
        for field in required_fields:
            if not bank_details.get(field):
                raise ValueError(f"Missing bank detail: {field}")
        
        # Bank transfers have additional fee
        bank_fee_rate = 0.02  # 2% bank processing fee
        conversion_fee = points * (tier_config["conversion_fee"] + bank_fee_rate)
        net_points = points - conversion_fee
        cash_value = net_points * self.points_to_inr_rate
        
        # Minimum bank transfer amount
        if cash_value < 500:
            raise ValueError("Minimum bank transfer amount is ₹500")
        
        # Create redemption transaction
        redemption_tx = RewardTransaction(
            id=f"redemption_bank_{datetime.utcnow().timestamp()}_{user_id}",
            user_id=user_id,
            transaction_type=TransactionType.POINTS_REDEMPTION,
            points_type=PointsType.COMMISSION_POINTS,
            points=-points,
            amount=cash_value,
            description=f"Points converted to bank transfer: {points} points -> ₹{cash_value}",
            redeemed=True,
            redeemed_at=datetime.utcnow(),
            redeemed_for="bank_transfer"
        )
        
        # Update wallet
        wallet.available_points -= points
        wallet.redeemed_points += points
        wallet.lifetime_redeemed += points
        wallet.updated_at = datetime.utcnow()
        
        self.monthly_conversions[user_id] = self.monthly_conversions.get(user_id, 0) + points
        self.transactions[redemption_tx.id] = redemption_tx
        
        # Store bank transfer request (in production, this would go to a processing queue)
        transfer_request = {
            "transaction_id": redemption_tx.id,
            "user_id": user_id,
            "amount": cash_value,
            "bank_details": {
                "account_number": bank_details["account_number"][-4:].rjust(len(bank_details["account_number"]), "*"),  # Masked
                "ifsc_code": bank_details["ifsc_code"],
                "account_holder_name": bank_details["account_holder_name"]
            },
            "status": "pending",
            "requested_at": datetime.utcnow().isoformat(),
            "estimated_completion": (datetime.utcnow() + timedelta(days=3)).isoformat()
        }
        
        logger.info(f"Bank transfer requested: {points} points -> ₹{cash_value} for user {user_id}")
        
        return {
            "points_converted": points,
            "conversion_fee": conversion_fee,
            "bank_fee": points * bank_fee_rate,
            "net_points": net_points,
            "cash_value": round(cash_value, 2),
            "conversion_type": "bank_transfer",
            "remaining_points": wallet.available_points,
            "transfer_request": transfer_request,
            "status": "pending",
            "message": "Bank transfer initiated. Will be processed within 2-3 business days."
        }

    async def _convert_to_gift_card(
        self,
        user_id: str,
        points: float,
        gift_card_type: Optional[str],
        wallet: UserRewardsWallet,
        tier_config: Dict
    ) -> Dict[str, Any]:
        """Convert points to gift card (instant)"""
        
        # Available gift cards
        gift_cards = {
            "amazon": {"name": "Amazon Gift Card", "value_multiplier": 1.0, "min_points": 500},
            "flipkart": {"name": "Flipkart Gift Card", "value_multiplier": 1.0, "min_points": 500},
            "myntra": {"name": "Myntra Gift Card", "value_multiplier": 0.95, "min_points": 300},
            "swiggy": {"name": "Swiggy Gift Card", "value_multiplier": 1.0, "min_points": 200},
            "zomato": {"name": "Zomato Gift Card", "value_multiplier": 1.0, "min_points": 200},
            "bigbasket": {"name": "BigBasket Gift Card", "value_multiplier": 0.98, "min_points": 300},
            "uber": {"name": "Uber Gift Card", "value_multiplier": 1.0, "min_points": 300},
        }
        
        if not gift_card_type or gift_card_type not in gift_cards:
            raise ValueError(f"Invalid gift card type. Available: {list(gift_cards.keys())}")
        
        card_config = gift_cards[gift_card_type]
        
        # Check minimum points
        if points < card_config["min_points"]:
            raise ValueError(f"Minimum {card_config['min_points']} points required for {card_config['name']}")
        
        # Calculate value
        conversion_fee = points * tier_config["conversion_fee"]
        net_points = points - conversion_fee
        base_value = net_points * self.points_to_inr_rate
        gift_card_value = base_value * card_config["value_multiplier"]
        
        # Create redemption transaction
        redemption_tx = RewardTransaction(
            id=f"redemption_gift_{datetime.utcnow().timestamp()}_{user_id}",
            user_id=user_id,
            transaction_type=TransactionType.POINTS_REDEMPTION,
            points_type=PointsType.COMMISSION_POINTS,
            points=-points,
            amount=gift_card_value,
            description=f"Points converted to {card_config['name']}: {points} points -> ₹{gift_card_value}",
            redeemed=True,
            redeemed_at=datetime.utcnow(),
            redeemed_for=f"gift_card_{gift_card_type}"
        )
        
        # Update wallet
        wallet.available_points -= points
        wallet.redeemed_points += points
        wallet.lifetime_redeemed += points
        wallet.updated_at = datetime.utcnow()
        
        self.monthly_conversions[user_id] = self.monthly_conversions.get(user_id, 0) + points
        self.transactions[redemption_tx.id] = redemption_tx
        
        # Generate gift card code (mock - in production, this would integrate with gift card provider)
        gift_card_code = self._generate_gift_card_code()
        
        logger.info(f"Gift card generated: {points} points -> ₹{gift_card_value} {card_config['name']} for user {user_id}")
        
        return {
            "points_converted": points,
            "conversion_fee": conversion_fee,
            "net_points": net_points,
            "gift_card_value": round(gift_card_value, 2),
            "conversion_type": "gift_card",
            "gift_card_type": gift_card_type,
            "gift_card_name": card_config["name"],
            "gift_card_code": gift_card_code,  # In production, this would be real
            "gift_card_pin": self._generate_gift_card_pin(),  # Masked in response
            "valid_until": (datetime.utcnow() + timedelta(days=365)).isoformat(),
            "remaining_points": wallet.available_points,
            "status": "completed",
            "message": f"Gift card generated! Check your email for the card details."
        }

    def _generate_gift_card_code(self) -> str:
        """Generate gift card code"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))

    def _generate_gift_card_pin(self) -> str:
        """Generate gift card PIN"""
        import random
        return ''.join(random.choices(string.digits, k=6))

    async def convert_cashback_to_points(
        self,
        user_id: str,
        cashback_amount: float
    ) -> RewardTransaction:
        """Convert cashback to reward points"""
        try:
            points = cashback_amount * self.inr_to_points_rate
            
            wallet = self.get_or_create_wallet(user_id)
            
            reward_tx = RewardTransaction(
                id=f"cb_conv_{datetime.utcnow().timestamp()}_{user_id}",
                user_id=user_id,
                transaction_type=TransactionType.CASHBACK,
                points_type=PointsType.CASHBACK_POINTS,
                points=round(points, 2),
                amount=cashback_amount,
                description=f"Cashback converted to points: ₹{cashback_amount} -> {points} points"
            )
            
            wallet.cashback_points += points
            wallet.total_points += points
            wallet.available_points += points
            wallet.lifetime_earned += points
            wallet.updated_at = datetime.utcnow()
            
            self.transactions[reward_tx.id] = reward_tx
            
            logger.info(f"Cashback converted: ₹{cashback_amount} -> {points} points for user {user_id}")
            return reward_tx
            
        except Exception as e:
            logger.error(f"Cashback conversion failed: {e}")
            raise

    async def _check_tier_upgrade(self, user_id: str):
        """Check and upgrade user tier"""
        wallet = self.get_or_create_wallet(user_id)
        current_tier = wallet.tier
        
        # Determine new tier based on lifetime earned
        new_tier = current_tier
        for tier in [UserTier.DIAMOND, UserTier.PLATINUM, UserTier.GOLD, UserTier.SILVER, UserTier.BRONZE]:
            if wallet.lifetime_earned >= self.tier_config[tier]["min_points"]:
                new_tier = tier
                break
        
        if new_tier != current_tier:
            wallet.tier = new_tier
            logger.info(f"User {user_id} upgraded to {new_tier.value}")
            
            # Add tier bonus
            tier_bonus = RewardTransaction(
                id=f"tier_bonus_{user_id}_{new_tier.value}",
                user_id=user_id,
                transaction_type=TransactionType.BONUS,
                points_type=PointsType.TIER_BONUS,
                points=1000,  # Tier upgrade bonus
                amount=0,
                description=f"Tier upgrade bonus: {current_tier.value} -> {new_tier.value}"
            )
            
            wallet.bonus_points += 1000
            wallet.total_points += 1000
            wallet.available_points += 1000
            wallet.lifetime_earned += 1000
            
            self.transactions[tier_bonus.id] = tier_bonus

    def get_wallet_summary(self, user_id: str) -> Dict[str, Any]:
        """Get user's rewards wallet summary"""
        wallet = self.get_or_create_wallet(user_id)
        tier_config = self.tier_config[wallet.tier]
        
        # Calculate progress to next tier
        next_tier = None
        tier_progress = 100
        for tier in [UserTier.SILVER, UserTier.GOLD, UserTier.PLATINUM, UserTier.DIAMOND]:
            if wallet.tier.value == tier.value:
                continue
            if wallet.lifetime_earned < self.tier_config[tier]["min_points"]:
                next_tier = tier
                tier_progress = (wallet.lifetime_earned / self.tier_config[tier]["min_points"]) * 100
                break
        
        return {
            "user_id": user_id,
            "tier": {
                "current": wallet.tier.value,
                "next": next_tier.value if next_tier else None,
                "progress": round(tier_progress, 2),
                "lifetime_earned": wallet.lifetime_earned,
                "next_tier_threshold": self.tier_config[next_tier]["min_points"] if next_tier else None
            },
            "points": {
                "total": round(wallet.total_points, 2),
                "available": round(wallet.available_points, 2),
                "pending": round(wallet.pending_points, 2),
                "redeemed": round(wallet.redeemed_points, 2),
                "expired": round(wallet.expired_points, 2)
            },
            "breakdown": {
                "commission_points": round(wallet.commission_points, 2),
                "referral_points": round(wallet.referral_points, 2),
                "cashback_points": round(wallet.cashback_points, 2),
                "bonus_points": round(wallet.bonus_points, 2)
            },
            "conversion": {
                "points_to_inr_rate": self.points_to_inr_rate,
                "inr_to_points_rate": self.inr_to_points_rate,
                "conversion_fee": tier_config["conversion_fee"],
                "max_monthly_conversion": tier_config["max_monthly_conversion"],
                "current_monthly_converted": self.monthly_conversions.get(user_id, 0)
            },
            "benefits": {
                "commission_multiplier": tier_config["commission_multiplier"],
                "cashback_bonus": tier_config["cashback_bonus"],
                "referral_bonus_percent": tier_config["referral_bonus_percent"]
            },
            "referral": {
                "code": self._get_user_referral_code(user_id),
                "total_referrals": len([r for r in self.referrals.values() if r.referrer_id == user_id]),
                "referral_earnings": sum(r.reward_points for r in self.referrals.values() if r.referrer_id == user_id)
            }
        }

    def _get_user_referral_code(self, user_id: str) -> str:
        """Get or generate referral code for user"""
        for code, uid in self.referral_codes.items():
            if uid == user_id:
                return code
        return self.generate_referral_code(user_id)

    def get_transaction_history(
        self,
        user_id: str,
        transaction_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get user's transaction history"""
        transactions = [
            tx for tx in self.transactions.values()
            if tx.user_id == user_id
        ]
        
        if transaction_type:
            transactions = [
                tx for tx in transactions
                if tx.transaction_type.value == transaction_type
            ]
        
        transactions.sort(key=lambda x: x.created_at, reverse=True)
        
        return [
            {
                "id": tx.id,
                "type": tx.transaction_type.value,
                "points_type": tx.points_type.value,
                "points": tx.points,
                "amount": tx.amount,
                "description": tx.description,
                "reference_id": tx.reference_id,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
                "redeemed": tx.redeemed,
                "expires_at": tx.expires_at.isoformat() if tx.expires_at else None
            }
            for tx in transactions[:limit]
        ]

    async def expire_old_points(self):
        """Background task to expire old points"""
        try:
            now = datetime.utcnow()
            expired_count = 0
            
            for tx_id, tx in list(self.transactions.items()):
                if (
                    not tx.redeemed
                    and tx.expires_at
                    and tx.expires_at < now
                    and tx.points > 0  # Don't expire negative (redeemed) transactions
                ):
                    # Mark as expired
                    wallet = self.wallets.get(tx.user_id)
                    if wallet:
                        wallet.available_points = max(0, wallet.available_points - tx.points)
                        wallet.expired_points += tx.points
                        wallet.updated_at = now
                    
                    expired_count += 1
            
            if expired_count > 0:
                logger.info(f"Expired {expired_count} point transactions")
                
        except Exception as e:
            logger.error(f"Points expiration failed: {e}")

    async def reset_monthly_limits(self):
        """Reset monthly conversion limits (run on 1st of month)"""
        self.monthly_conversions.clear()
        logger.info("Monthly conversion limits reset")

    async def get_conversion_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get user's conversion history"""
        conversions = [
            tx for tx in self.transactions.values()
            if tx.user_id == user_id and tx.transaction_type == TransactionType.POINTS_REDEMPTION
        ]
        
        conversions.sort(key=lambda x: x.created_at, reverse=True)
        
        return [
            {
                "id": tx.id,
                "points_converted": abs(tx.points),
                "cash_value": tx.amount,
                "conversion_type": tx.redeemed_for,
                "description": tx.description,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
                "status": "completed" if tx.redeemed else "pending"
            }
            for tx in conversions[:limit]
        ]

    async def get_conversion_summary(self, user_id: str) -> Dict[str, Any]:
        """Get user's conversion summary for current month"""
        from datetime import datetime
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        conversions = [
            tx for tx in self.transactions.values()
            if (tx.user_id == user_id and 
                tx.transaction_type == TransactionType.POINTS_REDEMPTION and
                tx.created_at and tx.created_at >= month_start)
        ]
        
        total_points_converted = sum(abs(tx.points) for tx in conversions)
        total_cash_value = sum(tx.amount for tx in conversions)
        
        # Group by conversion type
        by_type = {}
        for tx in conversions:
            conv_type = tx.redeemed_for or "unknown"
            if conv_type not in by_type:
                by_type[conv_type] = {"points": 0, "value": 0, "count": 0}
            by_type[conv_type]["points"] += abs(tx.points)
            by_type[conv_type]["value"] += tx.amount
            by_type[conv_type]["count"] += 1
        
        wallet = self.get_or_create_wallet(user_id)
        tier_config = self.tier_config[wallet.tier]
        
        return {
            "user_id": user_id,
            "current_month": {
                "total_points_converted": round(total_points_converted, 2),
                "total_cash_value": round(total_cash_value, 2),
                "conversions_count": len(conversions),
                "by_type": by_type
            },
            "limits": {
                "monthly_limit": tier_config["max_monthly_conversion"],
                "remaining": max(0, tier_config["max_monthly_conversion"] - self.monthly_conversions.get(user_id, 0)),
                "used_percentage": round((self.monthly_conversions.get(user_id, 0) / tier_config["max_monthly_conversion"]) * 100, 2)
            },
            "tier_benefits": {
                "conversion_fee": tier_config["conversion_fee"],
                "points_to_inr_rate": self.points_to_inr_rate
            }
        }

    async def bulk_convert_points(
        self,
        user_id: str,
        conversions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Bulk convert points to multiple options"""
        results = []
        wallet = self.get_or_create_wallet(user_id)
        
        # Check total points available
        total_points_needed = sum(conv["points"] for conv in conversions)
        if wallet.available_points < total_points_needed:
            raise ValueError(f"Insufficient points. Available: {wallet.available_points}, Needed: {total_points_needed}")
        
        for conv in conversions:
            try:
                result = await self.convert_points_to_cash(
                    user_id=user_id,
                    points=conv["points"],
                    conversion_type=conv["conversion_type"],
                    bank_details=conv.get("bank_details"),
                    gift_card_type=conv.get("gift_card_type")
                )
                results.append({
                    "success": True,
                    "conversion": result,
                    "request": conv
                })
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e),
                    "request": conv
                })
        
        return results

    async def schedule_auto_conversion(
        self,
        user_id: str,
        points_threshold: float,
        conversion_type: str,
        schedule: str = "monthly"  # daily, weekly, monthly
    ) -> Dict[str, Any]:
        """Schedule automatic point conversion when threshold is reached"""
        # This would integrate with a task scheduler like Celery in production
        auto_conversion = {
            "id": f"auto_conv_{user_id}_{datetime.utcnow().timestamp()}",
            "user_id": user_id,
            "points_threshold": points_threshold,
            "conversion_type": conversion_type,
            "schedule": schedule,
            "created_at": datetime.utcnow().isoformat(),
            "active": True
        }
        
        # Store in a database in production
        logger.info(f"Auto-conversion scheduled for user {user_id}: {points_threshold} points -> {conversion_type}")
        
        return {
            "success": True,
            "auto_conversion": auto_conversion,
            "message": f"Auto-conversion scheduled. Points will be converted when balance reaches {points_threshold}"
        }


# Global instance
rewards_service = RewardsService()
