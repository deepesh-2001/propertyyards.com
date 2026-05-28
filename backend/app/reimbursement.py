"""
Reimbursement Module
Handles employee expense reimbursement lifecycle: submit → review → approve/reject → pay via payroll.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.schemas import ReimbursementStatus, ReimbursementCategory

logger = logging.getLogger(__name__)


class ReimbursementManager:
    """Business logic for expense reimbursements."""

    # ── Submission ──────────────────────────────────────────────────────────

    async def submit_reimbursement(
        self,
        data: Dict[str, Any],
        database,
    ) -> Dict[str, Any]:
        """Create and immediately submit a reimbursement request."""
        try:
            employee = await database.users.find_one({"_id": data["employee_id"]})
            employee_name = (
                f"{employee.get('first_name', '')} {employee.get('last_name', '')}"
                if employee
                else ""
            )

            now = datetime.utcnow()
            record = {
                **data,
                "employee_name": employee_name,
                "approved_amount": None,
                "status": ReimbursementStatus.SUBMITTED,
                "submitted_at": now,
                "reviewed_by": None,
                "reviewed_at": None,
                "rejection_reason": None,
                "paid_at": None,
                "payroll_period_id": None,
                "receipt_urls": data.get("receipt_urls") or [],
                "created_at": now,
                "updated_at": now,
            }

            result = await database.reimbursements.insert_one(record)
            record["id"] = str(result.inserted_id)
            logger.info(f"Reimbursement submitted: {record['id']} by {data['employee_id']}")
            return record
        except Exception as e:
            logger.error(f"Reimbursement submission error: {e}")
            raise

    # ── Review ───────────────────────────────────────────────────────────────

    async def approve_reimbursement(
        self,
        reimbursement_id: str,
        approved_amount: float,
        reviewed_by: str,
        database,
    ) -> Dict[str, Any]:
        """Approve a reimbursement with a (possibly partial) amount."""
        try:
            record = await database.reimbursements.find_one({"_id": reimbursement_id})
            if not record:
                raise ValueError("Reimbursement not found")
            if record["status"] not in (
                ReimbursementStatus.SUBMITTED, ReimbursementStatus.UNDER_REVIEW
            ):
                raise ValueError(f"Cannot approve reimbursement in status '{record['status']}'")

            now = datetime.utcnow()
            await database.reimbursements.update_one(
                {"_id": reimbursement_id},
                {
                    "$set": {
                        "status": ReimbursementStatus.APPROVED,
                        "approved_amount": approved_amount,
                        "reviewed_by": reviewed_by,
                        "reviewed_at": now,
                        "updated_at": now,
                    }
                },
            )
            record.update(
                status=ReimbursementStatus.APPROVED,
                approved_amount=approved_amount,
                reviewed_by=reviewed_by,
                reviewed_at=now,
                updated_at=now,
            )
            record["id"] = str(record["_id"])
            del record["_id"]
            return record
        except Exception as e:
            logger.error(f"Reimbursement approval error: {e}")
            raise

    async def reject_reimbursement(
        self,
        reimbursement_id: str,
        reviewed_by: str,
        rejection_reason: str,
        database,
    ) -> Dict[str, Any]:
        """Reject a reimbursement."""
        try:
            record = await database.reimbursements.find_one({"_id": reimbursement_id})
            if not record:
                raise ValueError("Reimbursement not found")

            now = datetime.utcnow()
            await database.reimbursements.update_one(
                {"_id": reimbursement_id},
                {
                    "$set": {
                        "status": ReimbursementStatus.REJECTED,
                        "reviewed_by": reviewed_by,
                        "reviewed_at": now,
                        "rejection_reason": rejection_reason,
                        "updated_at": now,
                    }
                },
            )
            record.update(
                status=ReimbursementStatus.REJECTED,
                reviewed_by=reviewed_by,
                reviewed_at=now,
                rejection_reason=rejection_reason,
                updated_at=now,
            )
            record["id"] = str(record["_id"])
            del record["_id"]
            return record
        except Exception as e:
            logger.error(f"Reimbursement rejection error: {e}")
            raise

    # ── Payroll integration ──────────────────────────────────────────────────

    async def mark_paid_via_payroll(
        self,
        reimbursement_ids: List[str],
        payroll_period_id: str,
        database,
    ) -> int:
        """Mark approved reimbursements as paid when the payroll run completes."""
        now = datetime.utcnow()
        result = await database.reimbursements.update_many(
            {
                "_id": {"$in": reimbursement_ids},
                "status": ReimbursementStatus.APPROVED,
            },
            {
                "$set": {
                    "status": ReimbursementStatus.PAID,
                    "paid_at": now,
                    "payroll_period_id": payroll_period_id,
                    "updated_at": now,
                }
            },
        )
        return result.modified_count

    async def get_approved_for_employee(
        self, employee_id: str, database
    ) -> List[Dict[str, Any]]:
        """Return approved-but-unpaid reimbursements for an employee (used in payroll)."""
        cursor = database.reimbursements.find(
            {"employee_id": employee_id, "status": ReimbursementStatus.APPROVED}
        )
        records = await cursor.to_list(length=500)
        for r in records:
            r["id"] = str(r["_id"])
            del r["_id"]
        return records

    # ── Analytics ────────────────────────────────────────────────────────────

    async def get_analytics(
        self,
        employee_id: Optional[str],
        database,
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = {}
        if employee_id:
            query["employee_id"] = employee_id

        records = await database.reimbursements.find(query).to_list(length=5000)

        total_submitted = sum(r["amount"] for r in records)
        total_approved = sum(
            r.get("approved_amount") or 0
            for r in records
            if r["status"] in (ReimbursementStatus.APPROVED, ReimbursementStatus.PAID)
        )
        total_paid = sum(
            r.get("approved_amount") or 0
            for r in records
            if r["status"] == ReimbursementStatus.PAID
        )
        total_pending = sum(
            r["amount"]
            for r in records
            if r["status"] in (ReimbursementStatus.SUBMITTED, ReimbursementStatus.UNDER_REVIEW)
        )

        by_category: Dict[str, float] = {}
        for r in records:
            cat = r.get("category", "other")
            by_category[cat] = by_category.get(cat, 0) + r["amount"]

        by_status: Dict[str, int] = {}
        for r in records:
            s = r["status"]
            by_status[s] = by_status.get(s, 0) + 1

        # Average processing days (submitted → reviewed)
        processing_days: List[float] = []
        for r in records:
            if r.get("submitted_at") and r.get("reviewed_at"):
                delta = (r["reviewed_at"] - r["submitted_at"]).total_seconds() / 86400
                processing_days.append(delta)
        avg_days = sum(processing_days) / len(processing_days) if processing_days else 0.0

        return {
            "total_submitted": total_submitted,
            "total_approved": total_approved,
            "total_paid": total_paid,
            "total_pending": total_pending,
            "by_category": by_category,
            "by_status": by_status,
            "average_processing_days": round(avg_days, 2),
        }


reimbursement_manager = ReimbursementManager()
