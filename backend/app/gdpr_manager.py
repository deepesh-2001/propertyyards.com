"""
GDPR & Privacy Compliance Manager
Handles data privacy, consent, and user rights under GDPR/CCPA
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from bson import ObjectId

logger = logging.getLogger(__name__)


class ConsentType(Enum):
    """Types of user consent"""
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    THIRD_PARTY = "third_party"
    ESSENTIAL = "essential"
    PERSONALIZATION = "personalization"


class ConsentStatus(Enum):
    """Consent status"""
    GRANTED = "granted"
    DENIED = "denied"
    PENDING = "pending"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class DataCategory(Enum):
    """Categories of personal data"""
    CONTACT = "contact"  # email, phone, address
    IDENTITY = "identity"  # name, DOB, ID numbers
    FINANCIAL = "financial"  # payment info, salary
    BEHAVIORAL = "behavioral"  # browsing history, preferences
    LOCATION = "location"  # GPS, address
    PROFESSIONAL = "professional"  # employment, education
    SENSITIVE = "sensitive"  # race, religion, health


@dataclass
class ConsentRecord:
    """User consent record"""
    user_id: str
    consent_type: ConsentType
    status: ConsentStatus
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    version: str = "1.0"
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataProcessingRecord:
    """Record of data processing activity"""
    user_id: str
    data_category: DataCategory
    purpose: str
    legal_basis: str  # consent, contract, legal_obligation, etc.
    processed_at: datetime
    processor: str
    retention_days: int
    encryption_applied: bool = True
    anonymized: bool = False


class GDPRManager:
    """GDPR compliance manager"""

    def __init__(self):
        self.required_consents = [
            ConsentType.ESSENTIAL,
        ]
        self.optional_consents = [
            ConsentType.MARKETING,
            ConsentType.ANALYTICS,
            ConsentType.PERSONALIZATION,
            ConsentType.THIRD_PARTY,
        ]

    async def record_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        status: ConsentStatus,
        database,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_days: Optional[int] = None
    ) -> bool:
        """Record user consent"""
        try:
            expires_at = None
            if expires_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_days)

            consent = ConsentRecord(
                user_id=user_id,
                consent_type=consent_type,
                status=status,
                timestamp=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at
            )

            await database.consent_records.insert_one({
                "user_id": consent.user_id,
                "consent_type": consent.consent_type.value,
                "status": consent.status.value,
                "timestamp": consent.timestamp,
                "ip_address": consent.ip_address,
                "user_agent": consent.user_agent,
                "version": consent.version,
                "expires_at": consent.expires_at
            })

            logger.info(f"Consent recorded: {user_id} - {consent_type.value} - {status.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to record consent: {e}")
            return False

    async def check_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        database
    ) -> bool:
        """Check if user has given consent"""
        try:
            # Get latest consent record
            record = await database.consent_records.find_one(
                {
                    "user_id": user_id,
                    "consent_type": consent_type.value
                },
                sort=[("timestamp", -1)]
            )

            if not record:
                return consent_type == ConsentType.ESSENTIAL

            # Check if expired
            if record.get("expires_at") and record["expires_at"] < datetime.utcnow():
                return False

            return record["status"] == ConsentStatus.GRANTED.value

        except Exception as e:
            logger.error(f"Failed to check consent: {e}")
            return False

    async def withdraw_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        database
    ) -> bool:
        """Withdraw user consent"""
        try:
            # Record withdrawal
            await self.record_consent(
                user_id=user_id,
                consent_type=consent_type,
                status=ConsentStatus.WITHDRAWN,
                database=database
            )

            # Stop processing data under this consent
            await self._stop_processing_for_consent(user_id, consent_type, database)

            logger.info(f"Consent withdrawn: {user_id} - {consent_type.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to withdraw consent: {e}")
            return False

    async def get_user_consents(self, user_id: str, database) -> Dict[str, Any]:
        """Get all consent statuses for user"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$sort": {"timestamp": -1}},
                {"$group": {
                    "_id": "$consent_type",
                    "latest": {"$first": "$$ROOT"}
                }}
            ]

            results = await database.consent_records.aggregate(pipeline).to_list(length=10)

            consents = {}
            for result in results:
                consent_type = result["_id"]
                record = result["latest"]

                # Check if expired
                is_active = True
                if record.get("expires_at") and record["expires_at"] < datetime.utcnow():
                    is_active = False

                consents[consent_type] = {
                    "status": record["status"],
                    "granted": record["status"] == ConsentStatus.GRANTED.value and is_active,
                    "timestamp": record["timestamp"],
                    "expires_at": record.get("expires_at"),
                    "is_active": is_active
                }

            return consents

        except Exception as e:
            logger.error(f"Failed to get user consents: {e}")
            return {}

    async def _stop_processing_for_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        database
    ):
        """Stop data processing when consent is withdrawn"""
        # This would trigger various actions based on consent type
        if consent_type == ConsentType.MARKETING:
            # Unsubscribe from marketing
            await database.users.update_one(
                {"_id": user_id},
                {"$set": {"marketing_subscribed": False}}
            )
        elif consent_type == ConsentType.ANALYTICS:
            # Disable tracking
            await database.users.update_one(
                {"_id": user_id},
                {"$set": {"analytics_opt_out": True}}
            )

    async def export_user_data(self, user_id: str, database) -> Dict[str, Any]:
        """Export all user data (GDPR Right to Data Portability)"""
        try:
            export_data = {
                "user_id": user_id,
                "export_date": datetime.utcnow().isoformat(),
                "data": {}
            }

            # Get user profile
            user = await database.users.find_one({"_id": user_id})
            if user:
                export_data["data"]["profile"] = self._sanitize_export(user)

            # Get properties
            properties = await database.properties.find(
                {"user_id": user_id}
            ).to_list(length=1000)
            export_data["data"]["properties"] = [self._sanitize_export(p) for p in properties]

            # Get inquiries
            inquiries = await database.inquiries.find(
                {"user_id": user_id}
            ).to_list(length=1000)
            export_data["data"]["inquiries"] = [self._sanitize_export(i) for i in inquiries]

            # Get favorites/wishlist
            wishlist = await database.wishlists.find(
                {"user_id": user_id}
            ).to_list(length=1000)
            export_data["data"]["wishlist"] = [self._sanitize_export(w) for w in wishlist]

            # Get consent records
            consents = await database.consent_records.find(
                {"user_id": user_id}
            ).to_list(length=100)
            export_data["data"]["consents"] = consents

            # Get processing records
            processing = await database.data_processing.find(
                {"user_id": user_id}
            ).to_list(length=1000)
            export_data["data"]["processing_history"] = processing

            return export_data

        except Exception as e:
            logger.error(f"Failed to export user data: {e}")
            return {}

    def _sanitize_export(self, data: Dict) -> Dict:
        """Remove internal fields from export"""
        if not data:
            return {}

        # Remove MongoDB internal fields
        sanitized = {k: v for k, v in data.items() if not k.startswith("_")}

        # Remove sensitive internal fields
        sensitive_fields = ["password_hash", "salt", "api_keys", "tokens"]
        for field in sensitive_fields:
            sanitized.pop(field, None)

        return sanitized

    async def delete_user_data(
        self,
        user_id: str,
        database,
        hard_delete: bool = False
    ) -> bool:
        """Delete user data (GDPR Right to Erasure / Right to be Forgotten)"""
        try:
            deletion_record = {
                "user_id": user_id,
                "deletion_date": datetime.utcnow(),
                "hard_delete": hard_delete,
                "data_categories": []
            }

            if hard_delete:
                # Permanently delete all data
                collections = [
                    "users", "properties", "inquiries", "wishlists",
                    "payments", "notifications", "analytics_events",
                    "consent_records", "data_processing"
                ]

                for collection in collections:
                    result = await database[collection].delete_many({"user_id": user_id})
                    if result.deleted_count > 0:
                        deletion_record["data_categories"].append(collection)

            else:
                # Soft delete - anonymize and mark as deleted
                await database.users.update_one(
                    {"_id": user_id},
                    {
                        "$set": {
                            "deleted": True,
                            "deleted_at": datetime.utcnow(),
                            "email": f"deleted_{user_id}@deleted.user",
                            "phone": None,
                            "name": "Deleted User",
                            "profile_data": None
                        }
                    }
                )

                deletion_record["data_categories"].append("user_profile_anonymized")

            # Record deletion
            await database.deletion_records.insert_one(deletion_record)

            logger.info(f"User data deleted: {user_id} (hard={hard_delete})")
            return True

        except Exception as e:
            logger.error(f"Failed to delete user data: {e}")
            return False

    async def record_processing_activity(
        self,
        user_id: str,
        data_category: DataCategory,
        purpose: str,
        legal_basis: str,
        processor: str,
        retention_days: int,
        database
    ) -> bool:
        """Record data processing activity (GDPR Article 30)"""
        try:
            record = DataProcessingRecord(
                user_id=user_id,
                data_category=data_category,
                purpose=purpose,
                legal_basis=legal_basis,
                processed_at=datetime.utcnow(),
                processor=processor,
                retention_days=retention_days
            )

            await database.data_processing.insert_one({
                "user_id": record.user_id,
                "data_category": record.data_category.value,
                "purpose": record.purpose,
                "legal_basis": record.legal_basis,
                "processed_at": record.processed_at,
                "processor": record.processor,
                "retention_days": record.retention_days,
                "encryption_applied": record.encryption_applied,
                "anonymized": record.anonymized
            })

            return True

        except Exception as e:
            logger.error(f"Failed to record processing: {e}")
            return False

    async def anonymize_old_data(self, database, days: int = 365) -> int:
        """Anonymize data older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Find old records
            old_records = await database.data_processing.find(
                {"processed_at": {"$lt": cutoff_date}, "anonymized": False}
            ).to_list(length=1000)

            anonymized_count = 0
            for record in old_records:
                # Anonymize user_id but keep aggregate data
                await database.data_processing.update_one(
                    {"_id": record["_id"]},
                    {
                        "$set": {
                            "anonymized": True,
                            "user_id_hash": f"anon_{hash(record['user_id']) % 1000000}",
                            "user_id": None
                        }
                    }
                )
                anonymized_count += 1

            logger.info(f"Anonymized {anonymized_count} old records")
            return anonymized_count

        except Exception as e:
            logger.error(f"Failed to anonymize data: {e}")
            return 0

    async def get_privacy_dashboard(self, user_id: str, database) -> Dict[str, Any]:
        """Get privacy dashboard for user"""
        try:
            # Get consents
            consents = await self.get_user_consents(user_id, database)

            # Get data processing summary
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": "$data_category",
                    "count": {"$sum": 1},
                    "latest": {"$max": "$processed_at"}
                }}
            ]

            processing_summary = await database.data_processing.aggregate(pipeline).to_list(length=10)

            # Get data export size estimate
            user = await database.users.find_one({"_id": user_id})
            property_count = await database.properties.count_documents({"user_id": user_id})
            inquiry_count = await database.inquiries.count_documents({"user_id": user_id})

            return {
                "consents": consents,
                "processing_summary": [
                    {
                        "category": p["_id"],
                        "records": p["count"],
                        "last_processed": p["latest"]
                    }
                    for p in processing_summary
                ],
                "data_overview": {
                    "profile": user is not None,
                    "properties": property_count,
                    "inquiries": inquiry_count
                },
                "rights": {
                    "can_export": True,
                    "can_delete": True,
                    "can_rectify": True
                }
            }

        except Exception as e:
            logger.error(f"Failed to get privacy dashboard: {e}")
            return {}


# Global instance
gdpr_manager = GDPRManager()
