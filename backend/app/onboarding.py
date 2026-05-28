"""
Onboarding & Offboarding Module
Handles employee onboarding, offboarding, EPFO/ESI integration, and analytics
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from app.schemas import (
    OnboardingStatus,
    OffboardingStatus,
    EPFOStatus,
    EPFODetails,
    ESIDetails,
    BankAccountDetails,
    DocumentSubmission,
    OnboardingChecklist,
    EmployeeOnboardingCreate,
    EmployeeOnboardingUpdate,
    EmployeeOffboardingCreate,
    EmployeeOffboardingUpdate
)
from app.notification import notification_manager

logger = logging.getLogger(__name__)


class OnboardingManager:
    """Employee onboarding lifecycle manager"""

    def __init__(self):
        self.default_checklist = [
            {"task_name": "Submit Aadhar Card", "description": "Upload Aadhar card copy", "due_days": 3},
            {"task_name": "Submit PAN Card", "description": "Upload PAN card copy", "due_days": 3},
            {"task_name": "Submit Educational Certificates", "description": "Upload degree certificates", "due_days": 5},
            {"task_name": "Submit Experience Certificates", "description": "Upload previous employment letters", "due_days": 5},
            {"task_name": "Submit Photograph", "description": "Upload passport size photo", "due_days": 3},
            {"task_name": "Submit Address Proof", "description": "Upload address proof document", "due_days": 5},
            {"task_name": "EPFO Registration", "description": "Complete EPFO registration", "due_days": 7},
            {"task_name": "ESI Registration", "description": "Complete ESI registration if applicable", "due_days": 7},
            {"task_name": "Bank Account Setup", "description": "Submit bank account details", "due_days": 3},
            {"task_name": "IT Equipment Allocation", "description": "Receive laptop and accessories", "due_days": 1},
            {"task_name": "Email Account Setup", "description": "Corporate email account creation", "due_days": 1},
            {"task_name": "Access Card Issuance", "description": "Receive office access card", "due_days": 1},
            {"task_name": "HR Orientation", "description": "Attend HR orientation session", "due_days": 1},
            {"task_name": "Team Introduction", "description": "Meet team members", "due_days": 2},
            {"task_name": "System Access Setup", "description": "Configure system access", "due_days": 2}
        ]

    async def create_onboarding(
        self,
        onboarding_data: Dict[str, Any],
        database
    ) -> Dict[str, Any]:
        """Create a new employee onboarding record"""
        try:
            # Get reporting manager name if provided
            reporting_manager_name = None
            if onboarding_data.get("reporting_manager_id"):
                manager = await database.users.find_one({"_id": onboarding_data["reporting_manager_id"]})
                if manager:
                    reporting_manager_name = f"{manager.get('first_name', '')} {manager.get('last_name', '')}"

            # Initialize checklist with due dates
            date_of_joining = onboarding_data["date_of_joining"]
            checklist = []
            for task in self.default_checklist:
                due_date = date_of_joining - timedelta(days=task["due_days"])
                checklist.append({
                    "task_name": task["task_name"],
                    "description": task.get("description"),
                    "completed": False,
                    "completed_at": None,
                    "completed_by": None,
                    "due_date": due_date
                })

            onboarding = {
                **onboarding_data,
                "reporting_manager_name": reporting_manager_name,
                "status": OnboardingStatus.PENDING,
                "checklist": checklist,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "completed_at": None
            }

            result = await database.employee_onboardings.insert_one(onboarding)
            onboarding["id"] = str(result.inserted_id)

            # Send welcome email
            try:
                await notification_manager.email_service.send_onboarding_welcome(
                    employee_name=onboarding_data["employee_name"],
                    employee_email=onboarding_data["email"],
                    employee_phone=onboarding_data["phone_number"],
                    designation=onboarding_data["designation"],
                    department=onboarding_data["department"],
                    date_of_joining=onboarding_data["date_of_joining"],
                    reporting_manager_name=reporting_manager_name
                )
            except Exception as e:
                logger.warning(f"Failed to send welcome email: {e}")

            # Send welcome WhatsApp
            try:
                await notification_manager.whatsapp_service.send_onboarding_welcome_whatsapp(
                    employee_name=onboarding_data["employee_name"],
                    employee_phone=onboarding_data["phone_number"],
                    designation=onboarding_data["designation"],
                    department=onboarding_data["department"],
                    date_of_joining=onboarding_data["date_of_joining"],
                    reporting_manager_name=reporting_manager_name
                )
            except Exception as e:
                logger.warning(f"Failed to send welcome WhatsApp: {e}")

            logger.info(f"Onboarding created for employee {onboarding_data['employee_id']}")
            return onboarding

        except Exception as e:
            logger.error(f"Onboarding creation error: {e}")
            raise

    async def update_onboarding(
        self,
        onboarding_id: str,
        update_data: Dict[str, Any],
        database
    ) -> Dict[str, Any]:
        """Update an onboarding record"""
        try:
            # Get existing onboarding
            existing = await database.employee_onboardings.find_one({"_id": onboarding_id})
            if not existing:
                raise ValueError("Onboarding not found")

            # Update reporting manager name if changed
            if update_data.get("reporting_manager_id"):
                manager = await database.users.find_one({"_id": update_data["reporting_manager_id"]})
                if manager:
                    update_data["reporting_manager_name"] = f"{manager.get('first_name', '')} {manager.get('last_name', '')}"

            # Check if all checklist items are completed
            if update_data.get("checklist"):
                all_completed = all(item.get("completed", False) for item in update_data["checklist"])
                if all_completed and existing["status"] not in (OnboardingStatus.COMPLETED, OnboardingStatus.REJECTED):
                    update_data["status"] = OnboardingStatus.APPROVED
                    update_data["completed_at"] = datetime.utcnow()

            # Set completed_at if status is completed
            if update_data.get("status") == OnboardingStatus.COMPLETED and not existing.get("completed_at"):
                update_data["completed_at"] = datetime.utcnow()

            update_data["updated_at"] = datetime.utcnow()

            result = await database.employee_onboardings.update_one(
                {"_id": onboarding_id},
                {"$set": update_data}
            )

            if result.modified_count == 0:
                raise ValueError("Onboarding update failed")

            updated = await database.employee_onboardings.find_one({"_id": onboarding_id})
            updated["id"] = str(updated["_id"])
            del updated["_id"]

            # Send status update notifications if status changed
            if update_data.get("status") and update_data["status"] != existing.get("status"):
                try:
                    await notification_manager.email_service.send_onboarding_status_update(
                        employee_name=updated["employee_name"],
                        employee_email=updated["email"],
                        status=update_data["status"],
                        notes=update_data.get("notes")
                    )
                except Exception as e:
                    logger.warning(f"Failed to send status update email: {e}")

                try:
                    await notification_manager.whatsapp_service.send_onboarding_status_whatsapp(
                        employee_name=updated["employee_name"],
                        employee_phone=updated["phone_number"],
                        status=update_data["status"],
                        notes=update_data.get("notes")
                    )
                except Exception as e:
                    logger.warning(f"Failed to send status update WhatsApp: {e}")

            logger.info(f"Onboarding {onboarding_id} updated")
            return updated

        except Exception as e:
            logger.error(f"Onboarding update error: {e}")
            raise

    async def get_onboarding(
        self,
        onboarding_id: str,
        database
    ) -> Optional[Dict[str, Any]]:
        """Get a specific onboarding record"""
        onboarding = await database.employee_onboardings.find_one({"_id": onboarding_id})
        if onboarding:
            onboarding["id"] = str(onboarding["_id"])
            del onboarding["_id"]
        return onboarding

    async def get_employee_onboardings(
        self,
        employee_id: str,
        database
    ) -> List[Dict[str, Any]]:
        """Get all onboardings for an employee"""
        cursor = database.employee_onboardings.find({"employee_id": employee_id}).sort("created_at", -1)
        onboardings = await cursor.to_list(length=10)
        for onboarding in onboardings:
            onboarding["id"] = str(onboarding["_id"])
            del onboarding["_id"]
        return onboardings

    async def approve_onboarding(
        self,
        onboarding_id: str,
        approved_by: str,
        database
    ) -> Dict[str, Any]:
        """Approve an onboarding"""
        return await self.update_onboarding(
            onboarding_id,
            {"status": OnboardingStatus.APPROVED, "completed_at": datetime.utcnow()},
            database
        )

    async def reject_onboarding(
        self,
        onboarding_id: str,
        rejection_reason: str,
        database
    ) -> Dict[str, Any]:
        """Reject an onboarding"""
        return await self.update_onboarding(
            onboarding_id,
            {"status": OnboardingStatus.REJECTED, "rejection_reason": rejection_reason},
            database
        )

    async def get_onboarding_analytics(
        self,
        database,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get onboarding analytics"""
        try:
            query = {}
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            if date_filter:
                query["created_at"] = date_filter

            onboardings = await database.employee_onboardings.find(query).to_list(length=1000)

            total = len(onboardings)
            pending = sum(1 for o in onboardings if o["status"] == OnboardingStatus.PENDING)
            in_progress = sum(1 for o in onboardings if o["status"] == OnboardingStatus.IN_PROGRESS)
            documents_submitted = sum(1 for o in onboardings if o["status"] == OnboardingStatus.DOCUMENTS_SUBMITTED)
            verification_pending = sum(1 for o in onboardings if o["status"] == OnboardingStatus.VERIFICATION_PENDING)
            approved = sum(1 for o in onboardings if o["status"] == OnboardingStatus.APPROVED)
            completed = sum(1 for o in onboardings if o["status"] == OnboardingStatus.COMPLETED)
            rejected = sum(1 for o in onboardings if o["status"] == OnboardingStatus.REJECTED)

            # Calculate average onboarding days
            completed_onboardings = [o for o in onboardings if o.get("completed_at")]
            if completed_onboardings:
                avg_days = sum(
                    (o["completed_at"] - o["created_at"]).days
                    for o in completed_onboardings
                ) / len(completed_onboardings)
            else:
                avg_days = 0

            # By department
            by_department = {}
            for o in onboardings:
                dept = o.get("department", "unknown")
                by_department[dept] = by_department.get(dept, 0) + 1

            # By status
            by_status = {
                "pending": pending,
                "in_progress": in_progress,
                "documents_submitted": documents_submitted,
                "verification_pending": verification_pending,
                "approved": approved,
                "completed": completed,
                "rejected": rejected
            }

            # Monthly trend
            monthly_trend = []
            for i in range(6):
                month_start = datetime.utcnow() - timedelta(days=30 * (i + 1))
                month_end = datetime.utcnow() - timedelta(days=30 * i)
                month_onboardings = [o for o in onboardings
                                   if month_start <= o["created_at"] <= month_end]
                monthly_trend.append({
                    "month": month_start.strftime("%Y-%m"),
                    "count": len(month_onboardings)
                })

            return {
                "total_onboardings": total,
                "pending_onboardings": pending,
                "in_progress_onboardings": in_progress,
                "completed_onboardings": completed,
                "rejected_onboardings": rejected,
                "average_onboarding_days": avg_days,
                "by_department": by_department,
                "by_status": by_status,
                "monthly_trend": monthly_trend
            }

        except Exception as e:
            logger.error(f"Onboarding analytics error: {e}")
            raise


class OffboardingManager:
    """Employee offboarding lifecycle manager"""

    def __init__(self):
        self.default_clearance_checklist = [
            {"task_name": "Return Laptop", "description": "Return company laptop and accessories", "due_days": 1},
            {"task_name": "Return Access Card", "description": "Return office access card", "due_days": 1},
            {"task_name": "Clear Email Account", "description": "Forward emails and archive account", "due_days": 2},
            {"task_name": "Clear System Access", "description": "Revoke system access", "due_days": 2},
            {"task_name": "Knowledge Handover", "description": "Complete knowledge transfer", "due_days": 3},
            {"task_name": "Clear Dues", "description": "Clear all financial dues", "due_days": 2},
            {"task_name": "Submit Resignation Letter", "description": "Submit formal resignation", "due_days": 1},
            {"task_name": "Exit Interview", "description": "Attend exit interview", "due_days": 1},
            {"task_name": "EPFO Withdrawal/Transfer", "description": "Process EPFO withdrawal or transfer", "due_days": 7},
            {"task_name": "ESI Withdrawal", "description": "Process ESI withdrawal if applicable", "due_days": 7}
        ]

    async def create_offboarding(
        self,
        offboarding_data: Dict[str, Any],
        database
    ) -> Dict[str, Any]:
        """Create a new employee offboarding record"""
        try:
            # Get handover to name if provided
            handover_to_name = None
            if offboarding_data.get("handover_to"):
                handover = await database.users.find_one({"_id": offboarding_data["handover_to"]})
                if handover:
                    handover_to_name = f"{handover.get('first_name', '')} {handover.get('last_name', '')}"

            # Initialize clearance checklist with due dates
            last_working_day = offboarding_data["last_working_day"]
            clearance_checklist = []
            for task in self.default_clearance_checklist:
                due_date = last_working_day - timedelta(days=task["due_days"])
                clearance_checklist.append({
                    "task_name": task["task_name"],
                    "description": task.get("description"),
                    "completed": False,
                    "completed_at": None,
                    "completed_by": None,
                    "due_date": due_date
                })

            offboarding = {
                **offboarding_data,
                "handover_to_name": handover_to_name,
                "status": OffboardingStatus.PENDING,
                "clearance_checklist": clearance_checklist,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "completed_at": None
            }

            result = await database.employee_offboardings.insert_one(offboarding)
            offboarding["id"] = str(result.inserted_id)

            # Send offboarding email
            try:
                await notification_manager.email_service.send_offboarding_notification(
                    employee_name=offboarding_data["employee_name"],
                    employee_email=offboarding_data["email"],
                    last_working_day=offboarding_data["last_working_day"],
                    reason_for_leaving=offboarding_data["reason_for_leaving"]
                )
            except Exception as e:
                logger.warning(f"Failed to send offboarding email: {e}")

            # Send offboarding WhatsApp
            try:
                await notification_manager.whatsapp_service.send_offboarding_whatsapp(
                    employee_name=offboarding_data["employee_name"],
                    employee_phone=offboarding_data["phone_number"],
                    last_working_day=offboarding_data["last_working_day"],
                    reason_for_leaving=offboarding_data["reason_for_leaving"]
                )
            except Exception as e:
                logger.warning(f"Failed to send offboarding WhatsApp: {e}")

            logger.info(f"Offboarding created for employee {offboarding_data['employee_id']}")
            return offboarding

        except Exception as e:
            logger.error(f"Offboarding creation error: {e}")
            raise

    async def update_offboarding(
        self,
        offboarding_id: str,
        update_data: Dict[str, Any],
        database
    ) -> Dict[str, Any]:
        """Update an offboarding record"""
        try:
            existing = await database.employee_offboardings.find_one({"_id": offboarding_id})
            if not existing:
                raise ValueError("Offboarding not found")

            # Update handover to name if changed
            if update_data.get("handover_to"):
                handover = await database.users.find_one({"_id": update_data["handover_to"]})
                if handover:
                    update_data["handover_to_name"] = f"{handover.get('first_name', '')} {handover.get('last_name', '')}"

            # Check if all clearance items are completed
            if update_data.get("clearance_checklist"):
                all_completed = all(item.get("completed", False) for item in update_data["clearance_checklist"])
                if all_completed and existing["status"] not in (OffboardingStatus.COMPLETED, OffboardingStatus.CANCELLED):
                    update_data["status"] = OffboardingStatus.APPROVED

            # Set completed_at if status is completed
            if update_data.get("status") == OffboardingStatus.COMPLETED and not existing.get("completed_at"):
                update_data["completed_at"] = datetime.utcnow()

            update_data["updated_at"] = datetime.utcnow()

            result = await database.employee_offboardings.update_one(
                {"_id": offboarding_id},
                {"$set": update_data}
            )

            if result.modified_count == 0:
                raise ValueError("Offboarding update failed")

            updated = await database.employee_offboardings.find_one({"_id": offboarding_id})
            updated["id"] = str(updated["_id"])
            del updated["_id"]

            logger.info(f"Offboarding {offboarding_id} updated")
            return updated

        except Exception as e:
            logger.error(f"Offboarding update error: {e}")
            raise

    async def get_offboarding(
        self,
        offboarding_id: str,
        database
    ) -> Optional[Dict[str, Any]]:
        """Get a specific offboarding record"""
        offboarding = await database.employee_offboardings.find_one({"_id": offboarding_id})
        if offboarding:
            offboarding["id"] = str(offboarding["_id"])
            del offboarding["_id"]
        return offboarding

    async def get_employee_offboardings(
        self,
        employee_id: str,
        database
    ) -> List[Dict[str, Any]]:
        """Get all offboardings for an employee"""
        cursor = database.employee_offboardings.find({"employee_id": employee_id}).sort("created_at", -1)
        offboardings = await cursor.to_list(length=10)
        for offboarding in offboardings:
            offboarding["id"] = str(offboarding["_id"])
            del offboarding["_id"]
        return offboardings

    async def approve_offboarding(
        self,
        offboarding_id: str,
        approved_by: str,
        database
    ) -> Dict[str, Any]:
        """Approve an offboarding"""
        return await self.update_offboarding(
            offboarding_id,
            {"status": OffboardingStatus.APPROVED},
            database
        )

    async def complete_offboarding(
        self,
        offboarding_id: str,
        database
    ) -> Dict[str, Any]:
        """Complete an offboarding"""
        return await self.update_offboarding(
            offboarding_id,
            {"status": OffboardingStatus.COMPLETED, "completed_at": datetime.utcnow()},
            database
        )

    async def get_offboarding_analytics(
        self,
        database,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get offboarding analytics"""
        try:
            query = {}
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            if date_filter:
                query["created_at"] = date_filter

            offboardings = await database.employee_offboardings.find(query).to_list(length=1000)

            total = len(offboardings)
            pending = sum(1 for o in offboardings if o["status"] == OffboardingStatus.PENDING)
            in_progress = sum(1 for o in offboardings if o["status"] == OffboardingStatus.IN_PROGRESS)
            assets_returned = sum(1 for o in offboardings if o["status"] == OffboardingStatus.ASSETS_RETURNED)
            clearance_pending = sum(1 for o in offboardings if o["status"] == OffboardingStatus.CLEARANCE_PENDING)
            approved = sum(1 for o in offboardings if o["status"] == OffboardingStatus.APPROVED)
            completed = sum(1 for o in offboardings if o["status"] == OffboardingStatus.COMPLETED)

            # Calculate average tenure
            completed_offboardings = [o for o in offboardings if o.get("completed_at")]
            if completed_offboardings:
                avg_tenure = sum(
                    (o["completed_at"] - o["date_of_resignation"]).days
                    for o in completed_offboardings
                ) / len(completed_offboardings)
            else:
                avg_tenure = 0

            # Attrition rate (completed offboardings / total employees in last 12 months)
            total_employees = await database.users.count_documents({"role": "employee", "is_active": True})
            attrition_rate = (completed / total_employees * 100) if total_employees > 0 else 0

            # By department
            by_department = {}
            for o in offboardings:
                dept = o.get("department", "unknown")
                by_department[dept] = by_department.get(dept, 0) + 1

            # By reason
            by_reason = {}
            for o in offboardings:
                reason = o.get("reason_for_leaving", "unknown")
                by_reason[reason] = by_reason.get(reason, 0) + 1

            # By exit type
            by_exit_type = {}
            for o in offboardings:
                exit_type = o.get("exit_type", "unknown")
                by_exit_type[exit_type] = by_exit_type.get(exit_type, 0) + 1

            # Monthly trend
            monthly_trend = []
            for i in range(6):
                month_start = datetime.utcnow() - timedelta(days=30 * (i + 1))
                month_end = datetime.utcnow() - timedelta(days=30 * i)
                month_offboardings = [o for o in offboardings
                                     if month_start <= o["created_at"] <= month_end]
                monthly_trend.append({
                    "month": month_start.strftime("%Y-%m"),
                    "count": len(month_offboardings)
                })

            return {
                "total_offboardings": total,
                "pending_offboardings": pending,
                "in_progress_offboardings": in_progress,
                "completed_offboardings": completed,
                "average_tenure_days": avg_tenure,
                "attrition_rate": attrition_rate,
                "by_department": by_department,
                "by_reason": by_reason,
                "by_exit_type": by_exit_type,
                "monthly_trend": monthly_trend
            }

        except Exception as e:
            logger.error(f"Offboarding analytics error: {e}")
            raise


class EPFOManager:
    """EPFO/ESI integration manager"""

    async def register_epfo(
        self,
        employee_id: str,
        epfo_details: EPFODetails,
        database
    ) -> Dict[str, Any]:
        """Register employee with EPFO"""
        try:
            # In production, this would call EPFO API
            # For now, we simulate registration
            epfo_data = epfo_details.dict()
            epfo_data["status"] = EPFOStatus.REGISTERED
            epfo_data["employee_id"] = employee_id
            epfo_data["registered_at"] = datetime.utcnow()

            result = await database.epfo_records.insert_one(epfo_data)
            epfo_data["id"] = str(result.inserted_id)

            logger.info(f"EPFO registration for employee {employee_id}")
            return epfo_data

        except Exception as e:
            logger.error(f"EPFO registration error: {e}")
            raise

    async def register_esi(
        self,
        employee_id: str,
        esi_details: ESIDetails,
        database
    ) -> Dict[str, Any]:
        """Register employee with ESI"""
        try:
            esi_data = esi_details.dict()
            esi_data["status"] = EPFOStatus.REGISTERED
            esi_data["employee_id"] = employee_id
            esi_data["registered_at"] = datetime.utcnow()

            result = await database.esi_records.insert_one(esi_data)
            esi_data["id"] = str(result.inserted_id)

            logger.info(f"ESI registration for employee {employee_id}")
            return esi_data

        except Exception as e:
            logger.error(f"ESI registration error: {e}")
            raise

    async def withdraw_epfo(
        self,
        employee_id: str,
        database
    ) -> Dict[str, Any]:
        """Process EPFO withdrawal"""
        try:
            result = await database.epfo_records.update_one(
                {"employee_id": employee_id},
                {
                    "$set": {
                        "status": EPFOStatus.WITHDRAWN,
                        "date_of_exit": datetime.utcnow(),
                        "withdrawn_at": datetime.utcnow()
                    }
                }
            )

            if result.modified_count == 0:
                raise ValueError("EPFO record not found")

            logger.info(f"EPFO withdrawal for employee {employee_id}")
            return {"success": True, "employee_id": employee_id, "status": EPFOStatus.WITHDRAWN}

        except Exception as e:
            logger.error(f"EPFO withdrawal error: {e}")
            raise

    async def transfer_epfo(
        self,
        employee_id: str,
        new_establishment_id: str,
        database
    ) -> Dict[str, Any]:
        """Transfer EPFO account to new establishment"""
        try:
            result = await database.epfo_records.update_one(
                {"employee_id": employee_id},
                {
                    "$set": {
                        "status": EPFOStatus.TRANSFERRED,
                        "establishment_id": new_establishment_id,
                        "transferred_at": datetime.utcnow()
                    }
                }
            )

            if result.modified_count == 0:
                raise ValueError("EPFO record not found")

            logger.info(f"EPFO transfer for employee {employee_id} to {new_establishment_id}")
            return {"success": True, "employee_id": employee_id, "new_establishment_id": new_establishment_id}

        except Exception as e:
            logger.error(f"EPFO transfer error: {e}")
            raise

    async def get_epfo_details(
        self,
        employee_id: str,
        database
    ) -> Optional[Dict[str, Any]]:
        """Get EPFO details for an employee"""
        epfo = await database.epfo_records.find_one({"employee_id": employee_id})
        if epfo:
            epfo["id"] = str(epfo["_id"])
            del epfo["_id"]
        return epfo

    async def get_esi_details(
        self,
        employee_id: str,
        database
    ) -> Optional[Dict[str, Any]]:
        """Get ESI details for an employee"""
        esi = await database.esi_records.find_one({"employee_id": employee_id})
        if esi:
            esi["id"] = str(esi["_id"])
            del esi["_id"]
        return esi


# Global manager instances
onboarding_manager = OnboardingManager()
offboarding_manager = OffboardingManager()
epfo_manager = EPFOManager()
