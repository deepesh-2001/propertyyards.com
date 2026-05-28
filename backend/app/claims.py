"""
Claims Module
Handles employee/HR claims lifecycle: open → investigate → resolve (approve / reject / partial).
Supports commission disputes, salary disputes, insurance, and medical claims.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.schemas import ClaimStatus, ClaimPriority

logger = logging.getLogger(__name__)


class ClaimsManager:
    """Business logic for claims processing."""

    # ── Create ───────────────────────────────────────────────────────────────

    async def create_claim(
        self,
        data: Dict[str, Any],
        database,
    ) -> Dict[str, Any]:
        try:
            employee = await database.users.find_one({"_id": data["employee_id"]})
            employee_name = (
                f"{employee.get('first_name', '')} {employee.get('last_name', '')}"
                if employee
                else ""
            )

            now = datetime.utcnow()
            claim_count = await database.claims.count_documents({})
            claim_number = f"CLM-{now.strftime('%Y%m')}-{claim_count + 1:04d}"

            record = {
                **data,
                "claim_number": claim_number,
                "employee_name": employee_name,
                "approved_amount": None,
                "status": ClaimStatus.OPEN,
                "supporting_docs": data.get("supporting_docs") or [],
                "assigned_to": None,
                "resolution_notes": None,
                "resolved_at": None,
                "created_at": now,
                "updated_at": now,
            }

            result = await database.claims.insert_one(record)
            record["id"] = str(result.inserted_id)
            logger.info(f"Claim created: {record['id']} type={data.get('claim_type')}")
            return record
        except Exception as e:
            logger.error(f"Claim creation error: {e}")
            raise

    # ── Investigation ────────────────────────────────────────────────────────

    async def assign_claim(
        self,
        claim_id: str,
        assigned_to: str,
        database,
    ) -> Dict[str, Any]:
        now = datetime.utcnow()
        await database.claims.update_one(
            {"_id": claim_id},
            {
                "$set": {
                    "assigned_to": assigned_to,
                    "status": ClaimStatus.UNDER_INVESTIGATION,
                    "updated_at": now,
                }
            },
        )
        record = await database.claims.find_one({"_id": claim_id})
        if not record:
            raise ValueError("Claim not found")
        record["id"] = str(record["_id"])
        del record["_id"]
        return record

    # ── Resolution ───────────────────────────────────────────────────────────

    async def resolve_claim(
        self,
        claim_id: str,
        status: ClaimStatus,
        resolution_notes: str,
        approved_amount: Optional[float],
        database,
    ) -> Dict[str, Any]:
        try:
            record = await database.claims.find_one({"_id": claim_id})
            if not record:
                raise ValueError("Claim not found")
            if record["status"] == ClaimStatus.CLOSED:
                raise ValueError("Claim is already closed")

            if status not in (
                ClaimStatus.APPROVED,
                ClaimStatus.PARTIALLY_APPROVED,
                ClaimStatus.REJECTED,
                ClaimStatus.CLOSED,
            ):
                raise ValueError(f"Invalid resolution status: {status}")

            now = datetime.utcnow()
            update: Dict[str, Any] = {
                "status": status,
                "resolution_notes": resolution_notes,
                "resolved_at": now,
                "updated_at": now,
            }
            if approved_amount is not None:
                update["approved_amount"] = approved_amount

            await database.claims.update_one({"_id": claim_id}, {"$set": update})
            record.update(update)
            record["id"] = str(record["_id"])
            del record["_id"]
            logger.info(f"Claim {claim_id} resolved as {status}")
            return record
        except Exception as e:
            logger.error(f"Claim resolution error: {e}")
            raise

    # ── Query ────────────────────────────────────────────────────────────────

    async def get_employee_claims(
        self,
        employee_id: str,
        status: Optional[ClaimStatus],
        database,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {"employee_id": employee_id}
        if status:
            query["status"] = status
        cursor = database.claims.find(query).sort("created_at", -1)
        records = await cursor.to_list(length=200)
        for r in records:
            r["id"] = str(r["_id"])
            del r["_id"]
        return records

    # ── Analytics ────────────────────────────────────────────────────────────

    async def get_analytics(
        self,
        database,
        employee_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = {}
        if employee_id:
            query["employee_id"] = employee_id

        records = await database.claims.find(query).to_list(length=5000)

        total_claims = len(records)
        open_claims = sum(1 for r in records if r["status"] == ClaimStatus.OPEN)
        approved_claims = sum(
            1 for r in records if r["status"] in (ClaimStatus.APPROVED, ClaimStatus.PARTIALLY_APPROVED)
        )
        rejected_claims = sum(1 for r in records if r["status"] == ClaimStatus.REJECTED)

        total_claimed = sum(r["claimed_amount"] for r in records)
        total_approved = sum(r.get("approved_amount") or 0 for r in records)

        by_type: Dict[str, int] = {}
        by_priority: Dict[str, int] = {}
        for r in records:
            t = r.get("claim_type", "other")
            p = r.get("priority", "medium")
            by_type[t] = by_type.get(t, 0) + 1
            by_priority[p] = by_priority.get(p, 0) + 1

        resolution_days: List[float] = []
        for r in records:
            if r.get("created_at") and r.get("resolved_at"):
                delta = (r["resolved_at"] - r["created_at"]).total_seconds() / 86400
                resolution_days.append(delta)
        avg_days = sum(resolution_days) / len(resolution_days) if resolution_days else 0.0

        return {
            "total_claims": total_claims,
            "open_claims": open_claims,
            "approved_claims": approved_claims,
            "rejected_claims": rejected_claims,
            "total_claimed_amount": total_claimed,
            "total_approved_amount": total_approved,
            "by_type": by_type,
            "by_priority": by_priority,
            "average_resolution_days": round(avg_days, 2),
        }


claims_manager = ClaimsManager()
