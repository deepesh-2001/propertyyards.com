"""
Commission Tracking Module
Handles commission calculations, rules, and payouts
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.schemas import (
    CommissionType,
    CommissionStatus,
    NotificationChannel,
    InvestmentNotificationCreate
)
from app.notification import notification_manager

logger = logging.getLogger(__name__)


class CommissionCalculator:
    """Commission calculation engine"""
    
    def __init__(self):
        self.default_rates = {
            CommissionType.PROPERTY_SALE: 2.0,  # 2% of deal amount
            CommissionType.PROPERTY_RENTAL: 1.0,  # 1 month rent
            CommissionType.REFERRAL: 0.5,  # 0.5% of deal amount
            CommissionType.BROKERAGE: 1.5,  # 1.5% of deal amount
            CommissionType.PERFORMANCE: 0.0,  # Calculated based on targets
            CommissionType.TARGET_BONUS: 0.0,  # Calculated based on targets
            CommissionType.BUILDER_PROPERTY: 3.0,  # 3% of property value for builder properties
            CommissionType.LOAN_COMMISSION: 0.5  # 0.5% of loan amount
        }
    
    def calculate_commission(
        self,
        deal_amount: float,
        commission_type: CommissionType,
        tier_rates: Optional[List[Dict[str, Any]]] = None,
        conditions: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate commission based on deal amount and rules"""
        if tier_rates:
            return self._calculate_tiered_commission(deal_amount, tier_rates)
        
        base_rate = self.default_rates.get(commission_type, 0)
        
        # Apply conditions if any
        if conditions:
            base_rate = self._apply_conditions(base_rate, conditions)
        
        return deal_amount * (base_rate / 100)
    
    def _calculate_tiered_commission(
        self,
        deal_amount: float,
        tier_rates: List[Dict[str, Any]]
    ) -> float:
        """Calculate commission using tiered rates"""
        total_commission = 0
        remaining_amount = deal_amount
        
        # Sort tiers by min_amount
        sorted_tiers = sorted(tier_rates, key=lambda x: x["min_amount"])
        
        for i, tier in enumerate(sorted_tiers):
            min_amount = tier["min_amount"]
            rate = tier["rate"]
            
            # Get max amount for this tier
            if i + 1 < len(sorted_tiers):
                max_amount = sorted_tiers[i + 1]["min_amount"]
            else:
                max_amount = float('inf')
            
            # Calculate amount in this tier
            if remaining_amount <= 0:
                break
            
            tier_amount = min(remaining_amount, max_amount - min_amount)
            if tier_amount > 0:
                total_commission += tier_amount * (rate / 100)
                remaining_amount -= tier_amount
        
        return total_commission
    
    def _apply_conditions(self, base_rate: float, conditions: Dict[str, Any]) -> float:
        """Apply conditional modifiers to commission rate"""
        adjusted_rate = base_rate
        
        if conditions.get("multiplier"):
            adjusted_rate *= conditions["multiplier"]
        
        if conditions.get("bonus"):
            adjusted_rate += conditions["bonus"]
        
        if conditions.get("cap"):
            adjusted_rate = min(adjusted_rate, conditions["cap"])
        
        return adjusted_rate
    
    def calculate_performance_bonus(
        self,
        targets: Dict[str, float],
        achievements: Dict[str, float],
        bonus_rates: Dict[str, float]
    ) -> float:
        """Calculate performance-based bonus"""
        total_bonus = 0
        
        for metric, target in targets.items():
            achievement = achievements.get(metric, 0)
            rate = bonus_rates.get(metric, 0)
            
            if achievement >= target:
                excess = achievement - target
                total_bonus += excess * (rate / 100)
        
        return total_bonus


class CommissionProcessor:
    """Commission processing engine"""
    
    def __init__(self):
        self.calculator = CommissionCalculator()
    
    async def calculate_deal_commission(
        self,
        deal_id: str,
        deal_type: str,
        deal_amount: float,
        recipient_id: str,
        recipient_type: str,
        commission_rule_id: str,
        database
    ) -> Dict[str, Any]:
        """Calculate commission for a deal"""
        try:
            # Get commission rule
            rule = await database.commission_rules.find_one({"_id": commission_rule_id})
            if not rule:
                raise ValueError("Commission rule not found")
            
            # Calculate commission amount
            calculated_amount = self.calculator.calculate_commission(
                deal_amount=deal_amount,
                commission_type=rule["commission_type"],
                tier_rates=rule.get("tier_rates"),
                conditions=rule.get("conditions")
            )
            
            # Get recipient name
            recipient_name = ""
            if recipient_type == "employee":
                employee = await database.users.find_one({"_id": recipient_id})
                recipient_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}"
            elif recipient_type == "broker":
                broker = await database.brokers.find_one({"_id": recipient_id})
                recipient_name = broker.get("name", "")
            
            # Create commission record
            commission = {
                "recipient_id": recipient_id,
                "recipient_type": recipient_type,
                "recipient_name": recipient_name,
                "commission_rule_id": commission_rule_id,
                "rule_name": rule["name"],
                "deal_id": deal_id,
                "deal_type": deal_type,
                "deal_amount": deal_amount,
                "calculated_amount": calculated_amount,
                "currency": "USD",
                "status": CommissionStatus.PENDING,
                "due_date": datetime.utcnow() + timedelta(days=30),
                "notes": None,
                "approved_by": None,
                "approved_at": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await database.commissions.insert_one(commission)
            commission["id"] = str(result.inserted_id)
            
            return commission
            
        except Exception as e:
            logger.error(f"Commission calculation error: {e}")
            raise
    
    async def approve_commission(
        self,
        commission_id: str,
        approved_by: str,
        database
    ) -> Dict[str, Any]:
        """Approve a commission"""
        try:
            result = await database.commissions.update_one(
                {"_id": commission_id},
                {
                    "$set": {
                        "status": CommissionStatus.APPROVED,
                        "approved_by": approved_by,
                        "approved_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                raise ValueError("Commission not found")
            
            commission = await database.commissions.find_one({"_id": commission_id})
            commission["id"] = str(commission["_id"])
            del commission["_id"]
            
            return commission
            
        except Exception as e:
            logger.error(f"Commission approval error: {e}")
            raise
    
    async def process_payout(
        self,
        commission_ids: List[str],
        payment_method_id: str,
        gateway: str,
        database
    ) -> Dict[str, Any]:
        """Process commission payout"""
        try:
            # Get commissions
            commissions = await database.commissions.find({
                "_id": {"$in": commission_ids},
                "status": CommissionStatus.APPROVED
            }).to_list(length=100)
            
            if not commissions:
                raise ValueError("No approved commissions found")
            
            total_amount = sum(c["calculated_amount"] for c in commissions)
            
            # Create payout record
            payout = {
                "commission_ids": commission_ids,
                "total_amount": total_amount,
                "currency": "USD",
                "payment_method_id": payment_method_id,
                "gateway": gateway,
                "status": "processing",
                "transaction_id": None,
                "notes": None,
                "processed_at": None,
                "created_at": datetime.utcnow()
            }
            
            result = await database.commission_payouts.insert_one(payout)
            payout["id"] = str(result.inserted_id)
            
            # Update commission statuses
            await database.commissions.update_many(
                {"_id": {"$in": commission_ids}},
                {
                    "$set": {
                        "status": CommissionStatus.PAID,
                        "paid_date": datetime.utcnow(),
                        "payment_method": payment_method_id,
                        "transaction_id": str(result.inserted_id),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Update payout status
            await database.commission_payouts.update_one(
                {"_id": result.inserted_id},
                {
                    "$set": {
                        "status": "completed",
                        "processed_at": datetime.utcnow(),
                        "transaction_id": str(result.inserted_id)
                    }
                }
            )
            
            # Send investment notification for each commission
            for commission in commissions:
                await self._send_investment_notification(commission, database)
            
            return payout
            
        except Exception as e:
            logger.error(f"Payout processing error: {e}")
            raise
    
    async def _send_investment_notification(
        self,
        commission: Dict[str, Any],
        database
    ):
        """Send investment notification after commission payout"""
        try:
            # Get user details
            user = await database.users.find_one({"_id": commission["recipient_id"]})
            if not user:
                logger.warning(f"User not found for commission {commission['_id']}")
                return
            
            # Get property details if available
            property_name = "Investment"
            property_image = None
            property_size = None
            property_location = None
            
            if commission.get("property_id"):
                property_data = await database.properties.find_one({"_id": commission["property_id"]})
                if property_data:
                    property_name = property_data.get("title", "Investment")
                    property_image = property_data.get("images", [None])[0]
                    property_size = property_data.get("area")
                    property_location = property_data.get("location")
            
            # Create investment notification
            notification = InvestmentNotificationCreate(
                user_id=commission["recipient_id"],
                investment_id=str(commission["_id"]),
                investment_type=commission.get("commission_type", "investment"),
                amount=commission["calculated_amount"],
                property_name=property_name,
                property_image=property_image,
                property_size=property_size,
                property_location=property_location,
                investor_name=f"{user.get('first_name', '')} {user.get('last_name', '')}",
                investor_email=user.get("email", ""),
                investor_phone=user.get("phone_number", ""),
                channels=[NotificationChannel.EMAIL, NotificationChannel.WHATSAPP]
            )
            
            # Send notification
            await notification_manager.send_investment_notification(notification, database)
            
            logger.info(f"Investment notification sent for commission {commission['_id']}")
            
        except Exception as e:
            logger.error(f"Investment notification sending error: {e}")
            # Don't raise error, allow payout to complete even if notification fails
    
    async def get_commission_analytics(
        self,
        recipient_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        database
    ) -> Dict[str, Any]:
        """Get commission analytics"""
        try:
            query = {}
            if recipient_id:
                query["recipient_id"] = recipient_id
            if start_date:
                query["created_at"] = {"$gte": start_date}
            if end_date:
                query["created_at"] = query.get("created_at", {})
                query["created_at"]["$lte"] = end_date
            
            commissions = await database.commissions.find(query).to_list(length=1000)
            
            total_commissions = sum(c["calculated_amount"] for c in commissions)
            paid_commissions = sum(c["calculated_amount"] for c in commissions if c["status"] == CommissionStatus.PAID)
            pending_commissions = sum(c["calculated_amount"] for c in commissions if c["status"] == CommissionStatus.PENDING)
            
            average_commission = total_commissions / len(commissions) if commissions else 0
            
            # Commission by type
            commission_by_type = {}
            for c in commissions:
                rule = await database.commission_rules.find_one({"_id": c["commission_rule_id"]})
                if rule:
                    commission_type = rule["commission_type"]
                    commission_by_type[commission_type] = commission_by_type.get(commission_type, 0) + c["calculated_amount"]
            
            # Top performers
            performer_totals = {}
            for c in commissions:
                performer_totals[c["recipient_id"]] = performer_totals.get(c["recipient_id"], 0) + c["calculated_amount"]
            
            top_performers = sorted(performer_totals.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Monthly returns
            monthly_returns = await self._calculate_monthly_returns(commissions, database)
            
            # Quarterly returns
            quarterly_returns = await self._calculate_quarterly_returns(commissions, database)
            
            # Yearly returns
            yearly_returns = await self._calculate_yearly_returns(commissions, database)
            
            return {
                "total_commissions": total_commissions,
                "paid_commissions": paid_commissions,
                "pending_commissions": pending_commissions,
                "average_commission": average_commission,
                "commission_by_type": commission_by_type,
                "top_performers": [{"recipient_id": k, "total": v} for k, v in top_performers],
                "monthly_returns": monthly_returns,
                "quarterly_returns": quarterly_returns,
                "yearly_returns": yearly_returns,
                "period_start": start_date,
                "period_end": end_date
            }
            
        except Exception as e:
            logger.error(f"Commission analytics error: {e}")
            raise
    
    async def _calculate_monthly_returns(self, commissions: List[Dict], database) -> List[Dict[str, Any]]:
        """Calculate monthly commission returns"""
        monthly_data = {}
        
        for commission in commissions:
            month_key = commission["created_at"].strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"amount": 0, "count": 0}
            monthly_data[month_key]["amount"] += commission["calculated_amount"]
            monthly_data[month_key]["count"] += 1
        
        # Calculate growth rates
        monthly_returns = []
        sorted_months = sorted(monthly_data.keys())
        
        for i, month in enumerate(sorted_months):
            current_amount = monthly_data[month]["amount"]
            previous_amount = monthly_data[sorted_months[i-1]]["amount"] if i > 0 else 0
            growth_rate = ((current_amount - previous_amount) / previous_amount * 100) if previous_amount > 0 else 0
            
            monthly_returns.append({
                "month": month,
                "commission_returns": current_amount,
                "total_returns": current_amount,
                "growth_rate": growth_rate,
                "transaction_count": monthly_data[month]["count"]
            })
        
        return monthly_returns
    
    async def _calculate_quarterly_returns(self, commissions: List[Dict], database) -> List[Dict[str, Any]]:
        """Calculate quarterly commission returns"""
        quarterly_data = {}
        
        for commission in commissions:
            date = commission["created_at"]
            year = date.year
            quarter = (date.month - 1) // 3 + 1
            quarter_key = f"{year}-Q{quarter}"
            
            if quarter_key not in quarterly_data:
                quarterly_data[quarter_key] = {"amount": 0, "count": 0, "year": year, "quarter": quarter}
            quarterly_data[quarter_key]["amount"] += commission["calculated_amount"]
            quarterly_data[quarter_key]["count"] += 1
        
        # Calculate growth rates
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
                "commission_returns": current_amount,
                "total_returns": current_amount,
                "growth_rate": growth_rate,
                "transaction_count": quarterly_data[quarter]["count"]
            })
        
        return quarterly_returns
    
    async def _calculate_yearly_returns(self, commissions: List[Dict], database) -> List[Dict[str, Any]]:
        """Calculate yearly commission returns"""
        yearly_data = {}
        
        for commission in commissions:
            year = commission["created_at"].year
            if year not in yearly_data:
                yearly_data[year] = {"amount": 0, "count": 0}
            yearly_data[year]["amount"] += commission["calculated_amount"]
            yearly_data[year]["count"] += 1
        
        # Calculate growth rates and averages
        yearly_returns = []
        sorted_years = sorted(yearly_data.keys())
        
        for i, year in enumerate(sorted_years):
            current_amount = yearly_data[year]["amount"]
            previous_amount = yearly_data[sorted_years[i-1]]["amount"] if i > 0 else 0
            growth_rate = ((current_amount - previous_amount) / previous_amount * 100) if previous_amount > 0 else 0
            average_monthly = current_amount / 12
            
            yearly_returns.append({
                "year": year,
                "commission_returns": current_amount,
                "total_returns": current_amount,
                "growth_rate": growth_rate,
                "transaction_count": yearly_data[year]["count"],
                "average_monthly_returns": average_monthly
            })
        
        return yearly_returns


# Global commission processor instance
commission_processor = CommissionProcessor()
