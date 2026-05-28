"""
Cashback & Rewards Service
Automatic cashback calculation with bank and card offers
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import random

logger = logging.getLogger(__name__)


class PaymentMethod(Enum):
    """Payment methods"""
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    UPI = "upi"
    NET_BANKING = "net_banking"
    WALLET = "wallet"
    EMI = "emi"


class CashbackStatus(Enum):
    """Cashback transaction status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REDEEMED = "redeemed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class BankOffer:
    """Bank offer details"""
    id: str
    bank_name: str
    offer_type: str  # percentage_discount, cashback, reward_points
    discount_percentage: float
    max_discount: float
    min_transaction: float
    applicable_cards: List[str]  # visa, mastercard, rupay, all
    valid_from: datetime
    valid_until: datetime
    usage_limit: int = 0  # 0 = unlimited
    current_usage: int = 0
    is_active: bool = True


@dataclass
class CashbackTransaction:
    """Cashback transaction record"""
    id: str
    user_id: str
    transaction_id: str
    original_amount: float
    cashback_amount: float
    cashback_percentage: float
    payment_method: PaymentMethod
    bank_name: Optional[str] = None
    card_type: Optional[str] = None
    offer_id: Optional[str] = None
    status: CashbackStatus = CashbackStatus.PENDING
    created_at: datetime = None
    confirmed_at: Optional[datetime] = None
    redeemed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


class CashbackService:
    """Cashback and rewards management"""

    def __init__(self):
        self.enabled = True
        self.cashback_rate_cash = 0.20  # 20% for cash payments
        self.cashback_rate_card = 0.05  # 5% for card payments
        self.cashback_rate_upi = 0.03  # 3% for UPI
        self.min_cashback = 50  # Minimum ₹50
        self.max_cashback = 50000  # Maximum ₹50,000
        self.expiry_days = 365  # 1 year validity

        # Bank offers database
        self.bank_offers: Dict[str, List[BankOffer]] = {
            "HDFC Bank": [
                BankOffer(
                    id="hdfc_001",
                    bank_name="HDFC Bank",
                    offer_type="cashback",
                    discount_percentage=0.10,  # 10%
                    max_discount=2000,
                    min_transaction=5000,
                    applicable_cards=["all"],
                    valid_from=datetime.utcnow() - timedelta(days=30),
                    valid_until=datetime.utcnow() + timedelta(days=60),
                    usage_limit=1000
                )
            ],
            "ICICI Bank": [
                BankOffer(
                    id="icici_001",
                    bank_name="ICICI Bank",
                    offer_type="percentage_discount",
                    discount_percentage=0.15,  # 15%
                    max_discount=3000,
                    min_transaction=10000,
                    applicable_cards=["credit"],
                    valid_from=datetime.utcnow(),
                    valid_until=datetime.utcnow() + timedelta(days=90),
                    usage_limit=500
                )
            ],
            "SBI": [
                BankOffer(
                    id="sbi_001",
                    bank_name="SBI",
                    offer_type="cashback",
                    discount_percentage=0.05,  # 5%
                    max_discount=1000,
                    min_transaction=2000,
                    applicable_cards=["debit", "rupay"],
                    valid_from=datetime.utcnow(),
                    valid_until=datetime.utcnow() + timedelta(days=45)
                )
            ],
            "Axis Bank": [
                BankOffer(
                    id="axis_001",
                    bank_name="Axis Bank",
                    offer_type="reward_points",
                    discount_percentage=0.08,  # 8% equivalent
                    max_discount=5000,
                    min_transaction=15000,
                    applicable_cards=["credit", "visa"],
                    valid_from=datetime.utcnow(),
                    valid_until=datetime.utcnow() + timedelta(days=30),
                    usage_limit=200
                )
            ],
            "Kotak Mahindra": [
                BankOffer(
                    id="kotak_001",
                    bank_name="Kotak Mahindra",
                    offer_type="cashback",
                    discount_percentage=0.12,  # 12%
                    max_discount=2500,
                    min_transaction=8000,
                    applicable_cards=["all"],
                    valid_from=datetime.utcnow(),
                    valid_until=datetime.utcnow() + timedelta(days=60)
                )
            ]
        }

        # Cashback history
        self.transactions: Dict[str, CashbackTransaction] = {}
        self.user_cashback: Dict[str, List[str]] = {}  # user_id -> transaction_ids

    async def initialize(self):
        """Initialize cashback service"""
        logger.info("Cashback Service initialized")
        logger.info(f"Cash rates: {self.cashback_rate_cash*100}%, Card rates: {self.cashback_rate_card*100}%")

    def calculate_cashback(
        self,
        amount: float,
        payment_method: PaymentMethod,
        bank_name: Optional[str] = None,
        card_type: Optional[str] = None,
        user_tier: str = "standard"  # standard, premium, gold
    ) -> Dict[str, Any]:
        """Calculate cashback for a transaction"""
        try:
            cashback_details = {
                "base_cashback": 0,
                "bank_offer_cashback": 0,
                "tier_bonus": 0,
                "total_cashback": 0,
                "applicable_offers": []
            }

            # Base cashback based on payment method
            if payment_method == PaymentMethod.CASH:
                # 15-20% for cash payments (random variation)
                rate = random.uniform(0.15, 0.20)
                cashback_details["base_cashback"] = amount * rate
                cashback_details["cashback_rate"] = rate

            elif payment_method in [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD]:
                # 5% base for cards
                cashback_details["base_cashback"] = amount * self.cashback_rate_card
                cashback_details["cashback_rate"] = self.cashback_rate_card

                # Check bank offers
                if bank_name and bank_name in self.bank_offers:
                    bank_offer = self._get_best_bank_offer(
                        bank_name, amount, card_type
                    )
                    if bank_offer:
                        offer_cashback = min(
                            amount * bank_offer.discount_percentage,
                            bank_offer.max_discount
                        )
                        cashback_details["bank_offer_cashback"] = offer_cashback
                        cashback_details["applicable_offers"].append({
                            "offer_id": bank_offer.id,
                            "bank_name": bank_offer.bank_name,
                            "offer_type": bank_offer.offer_type,
                            "discount_percentage": bank_offer.discount_percentage * 100,
                            "max_discount": bank_offer.max_discount
                        })

            elif payment_method == PaymentMethod.UPI:
                # 3% for UPI
                cashback_details["base_cashback"] = amount * self.cashback_rate_upi
                cashback_details["cashback_rate"] = self.cashback_rate_upi

            elif payment_method == PaymentMethod.EMI:
                # Special EMI offers
                if amount >= 50000:
                    cashback_details["base_cashback"] = amount * 0.10  # 10% for high value EMI
                    cashback_details["cashback_rate"] = 0.10

            # Tier bonus
            tier_bonuses = {
                "standard": 0,
                "premium": 0.02,  # Extra 2%
                "gold": 0.05      # Extra 5%
            }
            tier_bonus_rate = tier_bonuses.get(user_tier, 0)
            cashback_details["tier_bonus"] = amount * tier_bonus_rate

            # Calculate total
            total = (
                cashback_details["base_cashback"] +
                cashback_details["bank_offer_cashback"] +
                cashback_details["tier_bonus"]
            )

            # Apply min/max limits
            total = max(self.min_cashback, min(total, self.max_cashback))
            cashback_details["total_cashback"] = round(total, 2)
            cashback_details["final_amount_after_cashback"] = round(amount - total, 2)

            return cashback_details

        except Exception as e:
            logger.error(f"Cashback calculation failed: {e}")
            return {"total_cashback": 0, "error": str(e)}

    def _get_best_bank_offer(
        self,
        bank_name: str,
        amount: float,
        card_type: Optional[str]
    ) -> Optional[BankOffer]:
        """Get best applicable bank offer"""
        offers = self.bank_offers.get(bank_name, [])
        now = datetime.utcnow()

        valid_offers = []
        for offer in offers:
            # Check validity
            if not offer.is_active:
                continue
            if offer.valid_from > now or offer.valid_until < now:
                continue

            # Check usage limit
            if offer.usage_limit > 0 and offer.current_usage >= offer.usage_limit:
                continue

            # Check minimum transaction
            if amount < offer.min_transaction:
                continue

            # Check card type
            if "all" not in offer.applicable_cards:
                if card_type and card_type.lower() not in [c.lower() for c in offer.applicable_cards]:
                    continue

            valid_offers.append(offer)

        # Return offer with highest discount percentage
        if valid_offers:
            return max(valid_offers, key=lambda x: x.discount_percentage)

        return None

    async def process_cashback(
        self,
        user_id: str,
        transaction_id: str,
        amount: float,
        payment_method: str,
        bank_name: Optional[str] = None,
        card_type: Optional[str] = None,
        user_tier: str = "standard"
    ) -> Optional[CashbackTransaction]:
        """Process and record cashback for a transaction"""
        try:
            # Calculate cashback
            payment_method_enum = PaymentMethod(payment_method)
            cashback_details = self.calculate_cashback(
                amount, payment_method_enum, bank_name, card_type, user_tier
            )

            if cashback_details["total_cashback"] <= 0:
                logger.info(f"No cashback applicable for transaction {transaction_id}")
                return None

            # Create transaction record
            transaction = CashbackTransaction(
                id=f"cb_{datetime.utcnow().timestamp()}_{transaction_id}",
                user_id=user_id,
                transaction_id=transaction_id,
                original_amount=amount,
                cashback_amount=cashback_details["total_cashback"],
                cashback_percentage=cashback_details.get("cashback_rate", 0) * 100,
                payment_method=payment_method_enum,
                bank_name=bank_name,
                card_type=card_type,
                offer_id=cashback_details["applicable_offers"][0]["offer_id"] if cashback_details["applicable_offers"] else None,
                status=CashbackStatus.PENDING,
                expires_at=datetime.utcnow() + timedelta(days=self.expiry_days),
                metadata={
                    "base_cashback": cashback_details["base_cashback"],
                    "bank_offer_cashback": cashback_details["bank_offer_cashback"],
                    "tier_bonus": cashback_details["tier_bonus"],
                    "applicable_offers": cashback_details["applicable_offers"]
                }
            )

            # Store transaction
            self.transactions[transaction.id] = transaction

            # Update user index
            if user_id not in self.user_cashback:
                self.user_cashback[user_id] = []
            self.user_cashback[user_id].append(transaction.id)

            # Increment bank offer usage
            if transaction.offer_id:
                self._increment_offer_usage(transaction.offer_id)

            logger.info(f"Cashback processed: {transaction.cashback_amount} for user {user_id}")
            return transaction

        except Exception as e:
            logger.error(f"Cashback processing failed: {e}")
            return None

    def _increment_offer_usage(self, offer_id: str):
        """Increment offer usage count"""
        for bank, offers in self.bank_offers.items():
            for offer in offers:
                if offer.id == offer_id:
                    offer.current_usage += 1
                    break

    async def confirm_cashback(self, cashback_id: str) -> bool:
        """Confirm cashback after transaction settlement"""
        try:
            transaction = self.transactions.get(cashback_id)
            if not transaction:
                return False

            if transaction.status == CashbackStatus.PENDING:
                transaction.status = CashbackStatus.CONFIRMED
                transaction.confirmed_at = datetime.utcnow()
                logger.info(f"Cashback confirmed: {cashback_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Cashback confirmation failed: {e}")
            return False

    async def redeem_cashback(
        self,
        user_id: str,
        cashback_id: str,
        redemption_type: str = "wallet_credit"  # wallet_credit, bank_transfer, discount
    ) -> Dict[str, Any]:
        """Redeem confirmed cashback"""
        try:
            transaction = self.transactions.get(cashback_id)

            if not transaction:
                return {"success": False, "error": "Cashback not found"}

            if transaction.user_id != user_id:
                return {"success": False, "error": "Unauthorized"}

            if transaction.status != CashbackStatus.CONFIRMED:
                return {"success": False, "error": "Cashback not confirmed"}

            if transaction.status == CashbackStatus.REDEEMED:
                return {"success": False, "error": "Already redeemed"}

            if transaction.expires_at and transaction.expires_at < datetime.utcnow():
                transaction.status = CashbackStatus.EXPIRED
                return {"success": False, "error": "Cashback expired"}

            # Process redemption based on type
            redemption_result = await self._process_redemption(
                transaction, redemption_type
            )

            if redemption_result["success"]:
                transaction.status = CashbackStatus.REDEEMED
                transaction.redeemed_at = datetime.utcnow()
                transaction.metadata["redemption_type"] = redemption_type
                transaction.metadata["redemption_details"] = redemption_result

                logger.info(f"Cashback redeemed: {cashback_id} via {redemption_type}")

            return redemption_result

        except Exception as e:
            logger.error(f"Cashback redemption failed: {e}")
            return {"success": False, "error": str(e)}

    async def _process_redemption(
        self,
        transaction: CashbackTransaction,
        redemption_type: str
    ) -> Dict[str, Any]:
        """Process the actual redemption"""
        try:
            if redemption_type == "wallet_credit":
                # Add to user wallet
                # This would integrate with wallet service
                return {
                    "success": True,
                    "amount": transaction.cashback_amount,
                    "method": "wallet_credit",
                    "message": f"₹{transaction.cashback_amount} credited to wallet"
                }

            elif redemption_type == "bank_transfer":
                # Transfer to bank account
                # This would integrate with payment service
                return {
                    "success": True,
                    "amount": transaction.cashback_amount,
                    "method": "bank_transfer",
                    "message": f"₹{transaction.cashback_amount} will be transferred to bank account",
                    "reference_id": f"TXN_{transaction.id}"
                }

            elif redemption_type == "discount":
                # Apply as discount on next transaction
                return {
                    "success": True,
                    "amount": transaction.cashback_amount,
                    "method": "discount",
                    "coupon_code": f"CB{transaction.id[:8].upper()}",
                    "message": f"Use coupon CB{transaction.id[:8].upper()} for ₹{transaction.cashback_amount} off"
                }

            else:
                return {"success": False, "error": "Invalid redemption type"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user_cashback_summary(self, user_id: str) -> Dict[str, Any]:
        """Get cashback summary for a user"""
        try:
            transaction_ids = self.user_cashback.get(user_id, [])
            transactions = [self.transactions[tid] for tid in transaction_ids if tid in self.transactions]

            # Calculate totals by status
            pending = sum(t.cashback_amount for t in transactions if t.status == CashbackStatus.PENDING)
            confirmed = sum(t.cashback_amount for t in transactions if t.status == CashbackStatus.CONFIRMED)
            redeemed = sum(t.cashback_amount for t in transactions if t.status == CashbackStatus.REDEEMED)
            expired = sum(t.cashback_amount for t in transactions if t.status == CashbackStatus.EXPIRED)

            # Recent transactions
            recent = sorted(
                transactions,
                key=lambda x: x.created_at,
                reverse=True
            )[:10]

            return {
                "user_id": user_id,
                "total_earned": pending + confirmed + redeemed,
                "available_balance": confirmed,  # Can be redeemed
                "pending": pending,
                "redeemed": redeemed,
                "expired": expired,
                "total_transactions": len(transactions),
                "recent_transactions": [
                    {
                        "id": t.id,
                        "amount": t.cashback_amount,
                        "status": t.status.value,
                        "created_at": t.created_at.isoformat(),
                        "payment_method": t.payment_method.value,
                        "expires_at": t.expires_at.isoformat() if t.expires_at else None
                    }
                    for t in recent
                ]
            }

        except Exception as e:
            logger.error(f"Cashback summary failed: {e}")
            return {"error": str(e)}

    def get_available_bank_offers(self, amount: float = 0) -> List[Dict[str, Any]]:
        """Get currently available bank offers"""
        try:
            offers = []
            now = datetime.utcnow()

            for bank, bank_offers in self.bank_offers.items():
                for offer in bank_offers:
                    if not offer.is_active:
                        continue
                    if offer.valid_from > now or offer.valid_until < now:
                        continue
                    if offer.usage_limit > 0 and offer.current_usage >= offer.usage_limit:
                        continue
                    if amount > 0 and amount < offer.min_transaction:
                        continue

                    offers.append({
                        "offer_id": offer.id,
                        "bank_name": offer.bank_name,
                        "offer_type": offer.offer_type,
                        "discount_percentage": offer.discount_percentage * 100,
                        "max_discount": offer.max_discount,
                        "min_transaction": offer.min_transaction,
                        "applicable_cards": offer.applicable_cards,
                        "valid_until": offer.valid_until.isoformat(),
                        "remaining_usage": max(0, offer.usage_limit - offer.current_usage) if offer.usage_limit > 0 else "unlimited"
                    })

            return sorted(offers, key=lambda x: x["discount_percentage"], reverse=True)

        except Exception as e:
            logger.error(f"Bank offers retrieval failed: {e}")
            return []

    async def expire_old_cashback(self):
        """Background task to expire old cashback"""
        try:
            now = datetime.utcnow()
            expired_count = 0

            for transaction in self.transactions.values():
                if (
                    transaction.status in [CashbackStatus.PENDING, CashbackStatus.CONFIRMED]
                    and transaction.expires_at
                    and transaction.expires_at < now
                ):
                    transaction.status = CashbackStatus.EXPIRED
                    expired_count += 1

            if expired_count > 0:
                logger.info(f"Expired {expired_count} cashback transactions")

        except Exception as e:
            logger.error(f"Cashback expiration task failed: {e}")

    def get_payment_method_recommendation(self, amount: float) -> Dict[str, Any]:
        """Recommend best payment method for maximum cashback"""
        try:
            recommendations = []

            # Calculate cashback for each method
            methods = [
                ("cash", PaymentMethod.CASH, None, None),
                ("credit_card", PaymentMethod.CREDIT_CARD, "HDFC Bank", "credit"),
                ("credit_card", PaymentMethod.CREDIT_CARD, "ICICI Bank", "credit"),
                ("upi", PaymentMethod.UPI, None, None)
            ]

            for method_key, method_enum, bank, card in methods:
                details = self.calculate_cashback(amount, method_enum, bank, card)
                recommendations.append({
                    "payment_method": method_key,
                    "bank": bank,
                    "card_type": card,
                    "cashback_amount": details["total_cashback"],
                    "cashback_percentage": details.get("cashback_rate", 0) * 100,
                    "applicable_offers": details.get("applicable_offers", [])
                })

            # Sort by cashback amount
            recommendations.sort(key=lambda x: x["cashback_amount"], reverse=True)

            return {
                "amount": amount,
                "best_option": recommendations[0] if recommendations else None,
                "all_options": recommendations
            }

        except Exception as e:
            logger.error(f"Payment recommendation failed: {e}")
            return {"error": str(e)}


# Global instance
cashback_service = CashbackService()
