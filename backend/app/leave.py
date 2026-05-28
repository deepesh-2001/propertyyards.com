"""
Leave Management Module
Handles leave requests, approvals, balances, and recruitment leaves
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import json

from app.schemas import (
    LeaveType,
    LeaveStatus,
    RecruitmentLeaveType
)
from app.cache import get_cache

logger = logging.getLogger(__name__)


class LeaveManager:
    """Leave management engine"""
    
    def __init__(self):
        self.default_leave_policies = {
            LeaveType.SICK_LEAVE: {"days_per_year": 10, "accrual_rate": "monthly", "carry_forward": 5},
            LeaveType.CASUAL_LEAVE: {"days_per_year": 12, "accrual_rate": "monthly", "carry_forward": 5},
            LeaveType.EARNED_LEAVE: {"days_per_year": 15, "accrual_rate": "quarterly", "carry_forward": 10},
            LeaveType.MATERNITY_LEAVE: {"days_per_year": 90, "accrual_rate": "yearly", "carry_forward": 0},
            LeaveType.PATERNITY_LEAVE: {"days_per_year": 15, "accrual_rate": "yearly", "carry_forward": 0},
            LeaveType.COMPENSATORY_OFF: {"days_per_year": 0, "accrual_rate": "as_earned", "carry_forward": 0},
            LeaveType.UNPAID_LEAVE: {"days_per_year": 0, "accrual_rate": "none", "carry_forward": 0},
            LeaveType.EMERGENCY_LEAVE: {"days_per_year": 5, "accrual_rate": "yearly", "carry_forward": 0},
            LeaveType.STUDY_LEAVE: {"days_per_year": 0, "accrual_rate": "none", "carry_forward": 0},
            LeaveType.MARRIAGE_LEAVE: {"days_per_year": 5, "accrual_rate": "yearly", "carry_forward": 0},
            LeaveType.BEREAVEMENT_LEAVE: {"days_per_year": 5, "accrual_rate": "yearly", "carry_forward": 0}
        }
    
    async def create_leave_request(
        self,
        leave_data: Dict[str, Any],
        database
    ) -> Dict[str, Any]:
        """Create a new leave request"""
        try:
            user = await database.users.find_one({"_id": leave_data["user_id"]})
            if not user:
                raise ValueError("User not found")
            
            balance = await self._get_leave_balance(leave_data["user_id"], leave_data["leave_type"], database)
            if balance < leave_data["total_days"]:
                raise ValueError(f"Insufficient leave balance. Available: {balance}, Requested: {leave_data['total_days']}")
            
            handover_name = None
            if leave_data.get("work_handover_to"):
                handover_user = await database.users.find_one({"_id": leave_data["work_handover_to"]})
                handover_name = f"{handover_user.get('first_name', '')} {handover_user.get('last_name', '')}" if handover_user else None
            
            leave = {
                **leave_data,
                "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "handover_person_name": handover_name,
                "status": LeaveStatus.PENDING,
                "approved_by": None,
                "approved_by_name": None,
                "approved_at": None,
                "rejection_reason": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await database.leave_requests.insert_one(leave)
            leave["id"] = str(result.inserted_id)
            return leave
        except Exception as e:
            logger.error(f"Leave request creation error: {e}")
            raise
    
    async def _get_leave_balance(self, user_id: str, leave_type: LeaveType, database) -> int:
        """Get leave balance for a user and leave type with caching"""
        try:
            cache = get_cache()
            cache_key = f"leave_balance:{user_id}:{leave_type.value}"
            
            # Try to get from cache
            cached_balance = await cache.get(cache_key)
            if cached_balance:
                return int(cached_balance)
            
            # Get from database
            balance_record = await database.leave_balances.find_one({
                "user_id": user_id,
                "leave_type": leave_type
            })
            if balance_record:
                balance = balance_record["balance"]
                # Cache for 1 hour
                await cache.set(cache_key, str(balance), ex=3600)
                return balance
            
            # Create default balance if not exists
            policy = self.default_leave_policies.get(leave_type, {"days_per_year": 0})
            default_balance = {
                "user_id": user_id,
                "leave_type": leave_type,
                "total_allocated": policy["days_per_year"],
                "used": 0,
                "balance": policy["days_per_year"],
                "carry_forward": 0,
                "expiry_date": datetime.utcnow() + timedelta(days=365),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await database.leave_balances.insert_one(default_balance)
            
            # Cache the new balance
            await cache.set(cache_key, str(default_balance["balance"]), ex=3600)
            return default_balance["balance"]
        except Exception as e:
            logger.error(f"Leave balance check error: {e}")
            raise
    
    async def approve_leave_request(self, leave_request_id: str, approved_by: str, database, notes: Optional[str] = None) -> Dict[str, Any]:
        """Approve a leave request with cache invalidation"""
        try:
            leave_request = await database.leave_requests.find_one({"_id": leave_request_id})
            if not leave_request:
                raise ValueError("Leave request not found")
            
            approver = await database.users.find_one({"_id": approved_by})
            approver_name = f"{approver.get('first_name', '')} {approver.get('last_name', '')}" if approver else ""
            
            await database.leave_requests.update_one(
                {"_id": leave_request_id},
                {
                    "$set": {
                        "status": LeaveStatus.APPROVED,
                        "approved_by": approved_by,
                        "approved_by_name": approver_name,
                        "approved_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            await database.leave_balances.update_one(
                {"user_id": leave_request["user_id"], "leave_type": leave_request["leave_type"]},
                {"$inc": {"used": leave_request["total_days"], "balance": -leave_request["total_days"]}, "$set": {"updated_at": datetime.utcnow()}}
            )
            
            # Invalidate cache for this user's leave balance
            cache = get_cache()
            cache_key = f"leave_balance:{leave_request['user_id']}:{leave_request['leave_type'].value}"
            await cache.delete(cache_key)
            
            await self._create_leave_attendance(leave_request, database)
            
            updated = await database.leave_requests.find_one({"_id": leave_request_id})
            updated["id"] = str(updated["_id"])
            del updated["_id"]
            return updated
        except Exception as e:
            logger.error(f"Leave approval error: {e}")
            raise
    
    async def reject_leave_request(self, leave_request_id: str, approved_by: str, rejection_reason: str, database) -> Dict[str, Any]:
        """Reject a leave request"""
        try:
            approver = await database.users.find_one({"_id": approved_by})
            approver_name = f"{approver.get('first_name', '')} {approver.get('last_name', '')}" if approver else ""
            
            await database.leave_requests.update_one(
                {"_id": leave_request_id},
                {
                    "$set": {
                        "status": LeaveStatus.REJECTED,
                        "approved_by": approved_by,
                        "approved_by_name": approver_name,
                        "approved_at": datetime.utcnow(),
                        "rejection_reason": rejection_reason,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            updated = await database.leave_requests.find_one({"_id": leave_request_id})
            updated["id"] = str(updated["_id"])
            del updated["_id"]
            return updated
        except Exception as e:
            logger.error(f"Leave rejection error: {e}")
            raise
    
    async def _create_leave_attendance(self, leave_request: Dict[str, Any], database):
        """Create attendance records for leave days"""
        try:
            start_date = leave_request["start_date"]
            end_date = leave_request["end_date"]
            current_date = start_date
            
            while current_date <= end_date:
                if current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                    continue
                
                attendance = {
                    "user_id": leave_request["user_id"],
                    "user_name": leave_request["user_name"],
                    "date": current_date,
                    "check_in_time": None,
                    "check_out_time": None,
                    "status": "on_leave",
                    "shift_type": "flexible",
                    "work_hours": 0,
                    "overtime_hours": 0,
                    "notes": f"Leave: {leave_request['leave_type']}",
                    "location": None,
                    "device_id": None,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                await database.attendance_records.insert_one(attendance)
                current_date += timedelta(days=1)
        except Exception as e:
            logger.error(f"Leave attendance creation error: {e}")
            raise


class RecruitmentLeaveManager:
    """Recruitment leave management engine"""
    
    async def create_recruitment_leave(
        self,
        leave_data: Dict[str, Any],
        database
    ) -> Dict[str, Any]:
        """Create a recruitment leave"""
        try:
            recruiter = await database.users.find_one({"_id": leave_data["recruiter_id"]})
            recruiter_name = f"{recruiter.get('first_name', '')} {recruiter.get('last_name', '')}" if recruiter else ""
            
            interviewer_name = None
            if leave_data.get("interviewer_id"):
                interviewer = await database.users.find_one({"_id": leave_data["interviewer_id"]})
                interviewer_name = f"{interviewer.get('first_name', '')} {interviewer.get('last_name', '')}" if interviewer else ""
            
            leave = {
                **leave_data,
                "recruiter_name": recruiter_name,
                "interviewer_name": interviewer_name,
                "status": "scheduled",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await database.recruitment_leaves.insert_one(leave)
            leave["id"] = str(result.inserted_id)
            return leave
        except Exception as e:
            logger.error(f"Recruitment leave creation error: {e}")
            raise
    
    async def get_recruitment_calendar(
        self,
        start_date: datetime,
        end_date: datetime,
        database
    ) -> List[Dict[str, Any]]:
        """Get recruitment leave calendar"""
        try:
            leaves = await database.recruitment_leaves.find({
                "start_date": {"$lte": end_date},
                "end_date": {"$gte": start_date}
            }).to_list(length=1000)
            
            calendar = []
            for leave in leaves:
                calendar.append({
                    "date": leave["start_date"],
                    "candidate_id": leave["candidate_id"],
                    "candidate_name": leave["candidate_name"],
                    "leave_type": leave["leave_type"],
                    "start_time": leave["start_date"],
                    "end_time": leave["end_date"],
                    "location": leave.get("location"),
                    "recruiter_id": leave["recruiter_id"],
                    "interviewer_id": leave.get("interviewer_id")
                })
            return calendar
        except Exception as e:
            logger.error(f"Recruitment calendar error: {e}")
            raise


# Global manager instances
leave_manager = LeaveManager()
recruitment_leave_manager = RecruitmentLeaveManager()
