"""
Credit Card Reward Module
Handles credit card management, reward points tracking, cashback, and card recommendations
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from app.schemas import (
    CreditCardType,
    CreditCardTier,
    RewardCategory,
    RewardTransactionType
)

logger = logging.getLogger(__name__)


class RewardCalculator:
    """Reward points calculation engine"""
    
    def __init__(self):
        self.point_value = 0.01  # 1 point = $0.01 (default)
        self.category_multipliers = {
            RewardCategory.TRAVEL: 2.0,
            RewardCategory.DINING: 1.5,
            RewardCategory.SHOPPING: 1.2,
            RewardCategory.FUEL: 1.5,
            RewardCategory.GROCERY: 1.0,
            RewardCategory.ENTERTAINMENT: 1.3,
            RewardCategory.UTILITIES: 0.5,
            RewardCategory.INSURANCE: 1.0,
            RewardCategory.EDUCATION: 1.0,
            RewardCategory.HEALTHCARE: 1.0,
            RewardCategory.ONLINE: 1.5,
            RewardCategory.INTERNATIONAL: 2.0
        }
    
    def calculate_points(
        self,
        amount: float,
        base_reward_rate: float,
        category: Optional[RewardCategory] = None
    ) -> int:
        """Calculate reward points for a transaction"""
        # Apply category multiplier if applicable
        multiplier = self.category_multipliers.get(category, 1.0)
        
        # Calculate points (points per dollar * amount * multiplier)
        points_per_dollar = base_reward_rate
        points = int(amount * points_per_dollar * multiplier)
        
        return points
    
    def calculate_cashback(
        self,
        points: int,
        cashback_rate: float
    ) -> float:
        """Calculate cashback value from points"""
        return points * self.point_value * cashback_rate
    
    def calculate_points_value(self, points: int) -> float:
        """Calculate monetary value of points"""
        return points * self.point_value


class CreditCardManager:
    """Credit card management engine"""
    
    def __init__(self):
        self.calculator = RewardCalculator()
    
    async def add_credit_card(
        self,
        card_data: Dict[str, Any],
        database
    ) -> Dict[str, Any]:
        """Add a new credit card for a user"""
        try:
            # Get user details
            user = await database.users.find_one({"_id": card_data["user_id"]})
            if not user:
                raise ValueError("User not found")
            
            # Calculate expiry date (5 years from issue)
            issued_date = datetime.utcnow()
            expiry_date = issued_date + timedelta(days=365 * 5)
            
            card = {
                **card_data,
                "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "current_balance": 0.0,
                "available_credit": card_data["credit_limit"],
                "total_points_earned": 0,
                "total_points_redeemed": 0,
                "points_balance": 0,
                "issued_date": issued_date,
                "expiry_date": expiry_date,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await database.credit_cards.insert_one(card)
            card["id"] = str(result.inserted_id)
            
            return card
            
        except Exception as e:
            logger.error(f"Credit card addition error: {e}")
            raise
    
    async def record_reward_transaction(
        self,
        transaction_data: Dict[str, Any],
        database
    ) -> Dict[str, Any]:
        """Record a reward transaction (earned/redeemed)"""
        try:
            # Get credit card
            card = await database.credit_cards.find_one({"_id": transaction_data["credit_card_id"]})
            if not card:
                raise ValueError("Credit card not found")
            
            # Calculate points value
            points_value = self.calculator.calculate_points_value(transaction_data["points"])
            
            transaction = {
                **transaction_data,
                "card_name": card["card_name"],
                "points_value": points_value,
                "transaction_date": datetime.utcnow(),
                "created_at": datetime.utcnow()
            }
            
            result = await database.reward_transactions.insert_one(transaction)
            transaction["id"] = str(result.inserted_id)
            
            # Update card points balance
            transaction_type = transaction_data["transaction_type"]
            new_earned = card["total_points_earned"]
            new_redeemed = card["total_points_redeemed"]
            new_balance = card["points_balance"]
            if transaction_type in (RewardTransactionType.EARNED, RewardTransactionType.BONUS):
                new_balance += transaction_data["points"]
                new_earned += transaction_data["points"]
            elif transaction_type == RewardTransactionType.REDEEMED:
                new_balance -= transaction_data["points"]
                new_redeemed += transaction_data["points"]
            
            update_data = {
                "points_balance": new_balance,
                "total_points_earned": new_earned,
                "total_points_redeemed": new_redeemed,
                "updated_at": datetime.utcnow()
            }
            
            await database.credit_cards.update_one(
                {"_id": transaction_data["credit_card_id"]},
                {"$set": update_data}
            )
            
            return transaction
            
        except Exception as e:
            logger.error(f"Reward transaction recording error: {e}")
            raise
    
    async def process_cashback(
        self,
        cashback_data: Dict[str, Any],
        database
    ) -> Dict[str, Any]:
        """Process cashback using reward points"""
        try:
            # Get credit card
            card = await database.credit_cards.find_one({"_id": cashback_data["credit_card_id"]})
            if not card:
                raise ValueError("Credit card not found")
            
            # Calculate points needed for cashback
            cashback_amount = cashback_data["amount"]
            points_needed = int(cashback_amount / self.calculator.point_value)
            
            if card["points_balance"] < points_needed:
                raise ValueError("Insufficient points balance")
            
            # Calculate cashback with rate
            actual_cashback = self.calculator.calculate_cashback(
                points_needed,
                cashback_data["cashback_rate"]
            )
            
            cashback = {
                **cashback_data,
                "card_name": card["card_name"],
                "points_used": points_needed,
                "points_value": actual_cashback,
                "status": "processed",
                "processed_date": datetime.utcnow(),
                "created_at": datetime.utcnow()
            }
            
            result = await database.cashbacks.insert_one(cashback)
            cashback["id"] = str(result.inserted_id)
            
            # Debit points and record the redemption transaction atomically through the helper
            # (record_reward_transaction already updates the card balance, so we do NOT also $inc here)
            await self.record_reward_transaction({
                "credit_card_id": cashback_data["credit_card_id"],
                "transaction_type": RewardTransactionType.REDEEMED,
                "points": points_needed,
                "amount": cashback_amount,
                "category": cashback_data["category"],
                "description": f"Cashback redemption: {cashback_data.get('description', '')}"
            }, database)

            # Create commission entry for credit card cashback
            from app.schemas import CommissionType, CommissionStatus
            commission = {
                "recipient_id": card["user_id"],
                "recipient_type": "user",
                "recipient_name": card.get("user_name", ""),
                "commission_rule_id": None,
                "rule_name": "Credit Card Cashback Commission",
                "deal_id": str(result.inserted_id),
                "deal_type": "credit_card_cashback",
                "deal_amount": actual_cashback,
                "calculated_amount": actual_cashback,
                "currency": "INR",
                "status": CommissionStatus.PENDING,
                "due_date": datetime.utcnow() + timedelta(days=30),
                "notes": f"Cashback from {card['card_name']} - {cashback_data.get('description', '')}",
                "approved_by": None,
                "approved_at": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await database.commissions.insert_one(commission)

            return cashback
            
        except Exception as e:
            logger.error(f"Cashback processing error: {e}")
            raise
    
    async def get_reward_analytics(
        self,
        user_id: str,
        database,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get reward analytics for a user"""
        try:
            # Get user's credit cards
            cards = await database.credit_cards.find({"user_id": user_id}).to_list(length=10)
            
            total_points_earned = sum(c["total_points_earned"] for c in cards)
            total_points_redeemed = sum(c["total_points_redeemed"] for c in cards)
            points_balance = sum(c["points_balance"] for c in cards)
            
            # Get transactions
            card_ids = [str(c["_id"]) for c in cards]
            tx_query: Dict[str, Any] = {"credit_card_id": {"$in": card_ids}}
            date_filter: Dict[str, Any] = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            if date_filter:
                tx_query["transaction_date"] = date_filter
            
            transactions = await database.reward_transactions.find(tx_query).to_list(length=1000)
            
            # Calculate total cashback earned
            cashbacks = await database.cashbacks.find({
                "credit_card_id": {"$in": card_ids}
            }).to_list(length=1000)
            total_cashback_earned = sum(c["points_value"] for c in cashbacks)
            
            # Average points per transaction
            earned_transactions = [t for t in transactions if t["transaction_type"] == RewardTransactionType.EARNED]
            average_points = sum(t["points"] for t in earned_transactions) / len(earned_transactions) if earned_transactions else 0
            
            # Top spending categories
            category_totals = {}
            for t in earned_transactions:
                category = t.get("category", "other")
                category_totals[category] = category_totals.get(category, 0) + t["points"]
            
            top_spending_categories = sorted(
                [{"category": k, "points": v} for k, v in category_totals.items()],
                key=lambda x: x["points"],
                reverse=True
            )[:5]
            
            # Monthly trend
            monthly_trend = []
            for i in range(6):
                month_start = datetime.utcnow() - timedelta(days=30 * (i + 1))
                month_end = datetime.utcnow() - timedelta(days=30 * i)
                month_transactions = [t for t in earned_transactions 
                                   if month_start <= t["transaction_date"] <= month_end]
                monthly_trend.append({
                    "month": month_start.strftime("%Y-%m"),
                    "points_earned": sum(t["points"] for t in month_transactions)
                })
            
            # Best card for rewards
            best_card = max(cards, key=lambda c: c["total_points_earned"]) if cards else None
            
            # Calculate monthly returns
            monthly_returns = self._calculate_monthly_cashback_returns(cashbacks)
            
            # Calculate quarterly returns
            quarterly_returns = self._calculate_quarterly_cashback_returns(cashbacks)
            
            # Calculate yearly returns
            yearly_returns = self._calculate_yearly_cashback_returns(cashbacks)
            
            # Calculate total returns
            total_returns = await self._calculate_total_returns(user_id, cards, cashbacks, database)
            
            return {
                "total_points_earned": total_points_earned,
                "total_points_redeemed": total_points_redeemed,
                "points_balance": points_balance,
                "total_cashback_earned": total_cashback_earned,
                "average_points_per_transaction": average_points,
                "top_spending_categories": top_spending_categories,
                "monthly_trend": monthly_trend,
                "best_card_for_rewards": best_card["card_name"] if best_card else None,
                "monthly_returns": monthly_returns,
                "quarterly_returns": quarterly_returns,
                "yearly_returns": yearly_returns,
                "total_returns": total_returns,
                "period_start": start_date,
                "period_end": end_date
            }
            
        except Exception as e:
            logger.error(f"Reward analytics error: {e}")
            raise
    
    def _calculate_monthly_cashback_returns(self, cashbacks: List[Dict]) -> List[Dict[str, Any]]:
        """Calculate monthly cashback returns"""
        monthly_data = {}
        
        for cashback in cashbacks:
            month_key = cashback["created_at"].strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"amount": 0, "count": 0}
            monthly_data[month_key]["amount"] += cashback["points_value"]
            monthly_data[month_key]["count"] += 1
        
        monthly_returns = []
        sorted_months = sorted(monthly_data.keys())
        
        for i, month in enumerate(sorted_months):
            current_amount = monthly_data[month]["amount"]
            previous_amount = monthly_data[sorted_months[i-1]]["amount"] if i > 0 else 0
            growth_rate = ((current_amount - previous_amount) / previous_amount * 100) if previous_amount > 0 else 0
            
            monthly_returns.append({
                "month": month,
                "cashback_returns": current_amount,
                "total_returns": current_amount,
                "growth_rate": growth_rate,
                "transaction_count": monthly_data[month]["count"]
            })
        
        return monthly_returns
    
    def _calculate_quarterly_cashback_returns(self, cashbacks: List[Dict]) -> List[Dict[str, Any]]:
        """Calculate quarterly cashback returns"""
        quarterly_data = {}
        
        for cashback in cashbacks:
            date = cashback["created_at"]
            year = date.year
            quarter = (date.month - 1) // 3 + 1
            quarter_key = f"{year}-Q{quarter}"
            
            if quarter_key not in quarterly_data:
                quarterly_data[quarter_key] = {"amount": 0, "count": 0, "year": year, "quarter": quarter}
            quarterly_data[quarter_key]["amount"] += cashback["points_value"]
            quarterly_data[quarter_key]["count"] += 1
        
        quarterly_returns = []
        sorted_quarters = sorted(quarterly_data.keys())
        
        for i, quarter in enumerate(sorted_quarters):
            current_amount = quarterly_data[quarter]["amount"]
            previous_amount = quarterly_data[sorted_quarters[i-1]]["amount"] if i > 0 else 0
            growth_rate = ((current_amount - previous_amount) / previous_amount * 100) if previous_amount > 0 else 0
            
            quarterly_returns.append({
                "quarter": quarter,
                "year": quarterly_data[quarter]["year"],
                "quarter_number": quarterly_data[quarter]["quarter"],
                "cashback_returns": current_amount,
                "total_returns": current_amount,
                "growth_rate": growth_rate,
                "transaction_count": quarterly_data[quarter]["count"]
            })
        
        return quarterly_returns
    
    def _calculate_yearly_cashback_returns(self, cashbacks: List[Dict]) -> List[Dict[str, Any]]:
        """Calculate yearly cashback returns"""
        yearly_data = {}
        
        for cashback in cashbacks:
            year = cashback["created_at"].year
            if year not in yearly_data:
                yearly_data[year] = {"amount": 0, "count": 0}
            yearly_data[year]["amount"] += cashback["points_value"]
            yearly_data[year]["count"] += 1
        
        yearly_returns = []
        sorted_years = sorted(yearly_data.keys())
        
        for i, year in enumerate(sorted_years):
            current_amount = yearly_data[year]["amount"]
            previous_amount = yearly_data[sorted_years[i-1]]["amount"] if i > 0 else 0
            growth_rate = ((current_amount - previous_amount) / previous_amount * 100) if previous_amount > 0 else 0
            average_monthly = current_amount / 12
            
            yearly_returns.append({
                "year": year,
                "cashback_returns": current_amount,
                "total_returns": current_amount,
                "growth_rate": growth_rate,
                "transaction_count": yearly_data[year]["count"],
                "average_monthly_returns": average_monthly
            })
        
        return yearly_returns
    
    async def _calculate_total_returns(self, user_id: str, cards: List[Dict], cashbacks: List[Dict], database) -> Dict[str, Any]:
        """Calculate total returns for a user"""
        try:
            # Get user details
            user = await database.users.find_one({"_id": user_id})
            user_name = f"{user.get('first_name', '')} {user.get('last_name', '')}" if user else ""
            
            # Calculate totals
            total_cashback_returns = sum(c["points_value"] for c in cashbacks)
            total_reward_points = sum(c["points_balance"] for c in cards)
            
            # Get first and last return dates
            if cashbacks:
                first_return_date = min(c["created_at"] for c in cashbacks)
                last_return_date = max(c["created_at"] for c in cashbacks)
            else:
                first_return_date = datetime.utcnow()
                last_return_date = datetime.utcnow()
            
            # Calculate average monthly returns
            months = max(1, (last_return_date - first_return_date).days / 30)
            average_monthly_returns = total_cashback_returns / months
            
            # Calculate average quarterly returns
            quarters = max(1, months / 3)
            average_quarterly_returns = total_cashback_returns / quarters
            
            # Calculate CAGR (Compound Annual Growth Rate)
            years = max(1, months / 12)
            if total_cashback_returns > 0 and years > 1:
                cagr = ((total_cashback_returns / 1000) ** (1 / years) - 1) * 100  # Assuming initial investment of $1000
            else:
                cagr = 0
            
            return {
                "user_id": user_id,
                "user_name": user_name,
                "total_commission_returns": 0,  # Will be calculated separately
                "total_cashback_returns": total_cashback_returns,
                "total_investment_returns": 0,
                "total_reward_points": total_reward_points,
                "total_returns": total_cashback_returns,
                "first_return_date": first_return_date,
                "last_return_date": last_return_date,
                "average_monthly_returns": average_monthly_returns,
                "average_quarterly_returns": average_quarterly_returns,
                "cagr": cagr,
                "created_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Total returns calculation error: {e}")
            raise


class CreditCardComparator:
    """Credit card comparison and recommendation engine"""
    
    def __init__(self):
        self.sample_cards = [
            {
                "card_name": "Chase Sapphire Preferred",
                "bank_name": "Chase",
                "card_type": CreditCardType.TRAVEL,
                "tier": CreditCardTier.SIGNATURE,
                "annual_fee": 95,
                "reward_rate": 2.0,
                "reward_categories": [RewardCategory.TRAVEL, RewardCategory.DINING, RewardCategory.ONLINE],
                "welcome_bonus_points": 60000,
                "welcome_bonus_spend": 4000,
                "pros": ["Excellent travel rewards", "No foreign transaction fees", "Flexible redemption"],
                "cons": ["Annual fee", "Requires good credit"],
                "best_for": ["Frequent travelers", "Dining enthusiasts"]
            },
            {
                "card_name": "American Express Gold",
                "bank_name": "American Express",
                "card_type": CreditCardType.DINING,
                "tier": CreditCardTier.GOLD,
                "annual_fee": 250,
                "reward_rate": 4.0,
                "reward_categories": [RewardCategory.DINING, RewardCategory.GROCERY, RewardCategory.TRAVEL],
                "welcome_bonus_points": 60000,
                "welcome_bonus_spend": 4000,
                "pros": ["High dining rewards", "Grocery bonuses", "Uber credits"],
                "cons": ["High annual fee", "Amex acceptance"],
                "best_for": ["Foodies", "Urban dwellers"]
            },
            {
                "card_name": "Citi Double Cash",
                "bank_name": "Citi",
                "card_type": CreditCardType.CASHBACK,
                "tier": CreditCardTier.BASIC,
                "annual_fee": 0,
                "reward_rate": 2.0,
                "reward_categories": [RewardCategory.SHOPPING, RewardCategory.GROCERY, RewardCategory.UTILITIES],
                "welcome_bonus_points": 0,
                "welcome_bonus_spend": 0,
                "pros": ["No annual fee", "Simple 2% cashback", "No categories to track"],
                "cons": ["No signup bonus", "Lower premium perks"],
                "best_for": ["Simplicity seekers", "Everyday spenders"]
            },
            {
                "card_name": "Capital One Venture X",
                "bank_name": "Capital One",
                "card_type": CreditCardType.TRAVEL,
                "tier": CreditCardTier.INFINITE,
                "annual_fee": 395,
                "reward_rate": 2.0,
                "reward_categories": [RewardCategory.TRAVEL, RewardCategory.INTERNATIONAL, RewardCategory.RENTAL],
                "welcome_bonus_points": 100000,
                "welcome_bonus_spend": 4000,
                "pros": ["High signup bonus", "Travel credits", "Lounge access"],
                "cons": ["High annual fee", "Premium travel focus"],
                "best_for": ["Premium travelers", "Frequent flyers"]
            },
            {
                "card_name": "Discover it Cash Back",
                "bank_name": "Discover",
                "card_type": CreditCardType.CASHBACK,
                "tier": CreditCardTier.BASIC,
                "annual_fee": 0,
                "reward_rate": 5.0,
                "reward_categories": [RewardCategory.SHOPPING, RewardCategory.GROCERY, RewardCategory.ONLINE],
                "welcome_bonus_points": 0,
                "welcome_bonus_spend": 0,
                "pros": ["5% rotating categories", "No annual fee", "Cashback match first year"],
                "cons": ["Rotating categories", "Discover acceptance"],
                "best_for": ["Category maximizers", "No-fee seekers"]
            }
        ]
    
    def compare_cards(
        self,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare credit cards based on user preferences"""
        try:
            scored_cards = []
            
            for card in self.sample_cards:
                score = 0
                
                # Match reward categories
                preferred_categories = preferences.get("categories", [])
                category_match = len(set(card["reward_categories"]) & set(preferred_categories))
                score += category_match * 15
                
                # Annual fee preference
                max_annual_fee = preferences.get("max_annual_fee", 1000)
                if card["annual_fee"] <= max_annual_fee:
                    score += 20
                else:
                    score -= 10
                
                # Reward rate preference
                min_reward_rate = preferences.get("min_reward_rate", 0)
                if card["reward_rate"] >= min_reward_rate:
                    score += card["reward_rate"] * 5
                
                # Card type preference
                preferred_type = preferences.get("card_type")
                if preferred_type and card["card_type"] == preferred_type:
                    score += 25
                
                # Welcome bonus consideration
                if preferences.get("wants_welcome_bonus", True):
                    score += min(card["welcome_bonus_points"] / 1000, 20)
                
                # Calculate estimated annual rewards
                monthly_spend = preferences.get("monthly_spend", 2000)
                estimated_annual_rewards = monthly_spend * 12 * (card["reward_rate"] / 100)
                
                scored_cards.append({
                    **card,
                    "match_score": min(score, 100),
                    "estimated_annual_rewards": estimated_annual_rewards
                })
            
            # Sort by match score
            scored_cards.sort(key=lambda x: x["match_score"], reverse=True)
            
            # Get top 3 recommendations
            recommendations = scored_cards[:3]
            
            # Determine best card
            best_card = recommendations[0] if recommendations else None
            
            return {
                "cards": recommendations,
                "comparison_criteria": ["reward_categories", "annual_fee", "reward_rate", "welcome_bonus"],
                "recommendation": f"Based on your preferences, we recommend {best_card['card_name'] if best_card else 'no card'}",
                "best_card": best_card
            }
            
        except Exception as e:
            logger.error(f"Card comparison error: {e}")
            raise
    
    def get_best_card_for_category(
        self,
        category: RewardCategory
    ) -> Dict[str, Any]:
        """Get the best credit card for a specific spending category"""
        try:
            scored_cards = []
            
            for card in self.sample_cards:
                score = 0
                
                # Check if card offers rewards in this category
                if category in card["reward_categories"]:
                    score += 50
                    score += card["reward_rate"] * 10
                else:
                    score += card["reward_rate"] * 5
                
                # Consider annual fee
                score -= card["annual_fee"] / 10
                
                scored_cards.append({
                    **card,
                    "match_score": max(score, 0),
                    "estimated_annual_rewards": 2000 * 12 * (card["reward_rate"] / 100)
                })
            
            scored_cards.sort(key=lambda x: x["match_score"], reverse=True)
            
            return scored_cards[0] if scored_cards else None
            
        except Exception as e:
            logger.error(f"Best card for category error: {e}")
            raise
    
    def get_best_cards_for_cashback(
        self,
        spend_amount: float,
        category: Optional[RewardCategory] = None,
        cashback_rate: float = 1.0
    ) -> List[Dict[str, Any]]:
        try:
            scored_cards = []
            
            for card in self.sample_cards:
                category_multiplier = self.calculator.category_multipliers.get(category, 1.0)
                category_match = category in card["reward_categories"] if category else True
                effective_reward_rate = card["reward_rate"] * (category_multiplier if category_match else 1.0)
                estimated_points = int(spend_amount * effective_reward_rate)
                estimated_cashback = self.calculator.calculate_cashback(estimated_points, cashback_rate)
                net_cashback_after_fee = estimated_cashback - card["annual_fee"]
                match_score = max(0, min(100, (effective_reward_rate * 10) + (30 if category_match else 0) - (card["annual_fee"] / 20)))
                
                scored_cards.append({
                    "card_name": card["card_name"],
                    "bank_name": card["bank_name"],
                    "card_type": card["card_type"],
                    "tier": card["tier"],
                    "reward_rate": card["reward_rate"],
                    "reward_categories": card["reward_categories"],
                    "estimated_points": estimated_points,
                    "estimated_cashback": estimated_cashback,
                    "net_cashback_after_fee": net_cashback_after_fee,
                    "match_score": match_score
                })
            
            scored_cards.sort(key=lambda x: (x["net_cashback_after_fee"], x["estimated_points"], x["match_score"]), reverse=True)
            return scored_cards
            
        except Exception as e:
            logger.error(f"Best cards for cashback error: {e}")
            raise


# Global manager instances
reward_calculator = RewardCalculator()
credit_card_manager = CreditCardManager()
credit_card_comparator = CreditCardComparator()
