"""
CRM Integration Module
Manages customer relationships, leads, and interactions
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LeadStatus(str, Enum):
    """Lead status in CRM pipeline"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class LeadSource(str, Enum):
    """Source of the lead"""
    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    EMAIL_CAMPAIGN = "email_campaign"
    PAID_AD = "paid_ad"
    DIRECT = "direct"
    OTHER = "other"


class InteractionType(str, Enum):
    """Types of customer interactions"""
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    PROPERTY_VIEWING = "property_viewing"
    FOLLOW_UP = "follow_up"
    NOTE = "note"


class CRMLead:
    """CRM Lead management"""
    
    def __init__(self, database):
        self.db = database
        self.collection = database.crm_leads
    
    async def create_lead(self, lead_data: Dict[str, Any]) -> str:
        """Create a new CRM lead"""
        lead = {
            "name": lead_data.get("name"),
            "email": lead_data.get("email"),
            "phone": lead_data.get("phone"),
            "source": lead_data.get("source", LeadSource.WEBSITE),
            "status": lead_data.get("status", LeadStatus.NEW),
            "property_interest": lead_data.get("property_interest"),
            "budget_range": lead_data.get("budget_range"),
            "preferred_location": lead_data.get("preferred_location"),
            "notes": lead_data.get("notes", ""),
            "assigned_to": lead_data.get("assigned_to"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "interactions": [],
            "tags": lead_data.get("tags", [])
        }
        
        result = await self.collection.insert_one(lead)
        logger.info(f"CRM lead created: {result.inserted_id}")
        return str(result.inserted_id)
    
    async def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific lead by ID"""
        lead = await self.collection.find_one({"_id": lead_id})
        if lead:
            lead["id"] = str(lead["_id"])
            del lead["_id"]
        return lead
    
    async def update_lead(self, lead_id: str, update_data: Dict[str, Any]) -> bool:
        """Update lead information"""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": lead_id},
            {"$set": update_data}
        )
        logger.info(f"CRM lead updated: {lead_id}")
        return result.modified_count > 0
    
    async def delete_lead(self, lead_id: str) -> bool:
        """Delete a lead"""
        result = await self.collection.delete_one({"_id": lead_id})
        logger.info(f"CRM lead deleted: {lead_id}")
        return result.deleted_count > 0
    
    async def list_leads(
        self, 
        status: Optional[LeadStatus] = None,
        source: Optional[LeadSource] = None,
        assigned_to: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List leads with filters"""
        query_filter = {}
        if status:
            query_filter["status"] = status
        if source:
            query_filter["source"] = source
        if assigned_to:
            query_filter["assigned_to"] = assigned_to
        
        cursor = self.collection.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
        leads = await cursor.to_list(length=limit)
        
        for lead in leads:
            lead["id"] = str(lead["_id"])
            del lead["_id"]
        
        return leads
    
    async def add_interaction(
        self, 
        lead_id: str, 
        interaction_type: InteractionType,
        notes: str,
        user_id: str
    ) -> bool:
        """Add an interaction to a lead"""
        interaction = {
            "type": interaction_type,
            "notes": notes,
            "created_by": user_id,
            "created_at": datetime.utcnow()
        }
        
        result = await self.collection.update_one(
            {"_id": lead_id},
            {
                "$push": {"interactions": interaction},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        logger.info(f"Interaction added to lead {lead_id}")
        return result.modified_count > 0
    
    async def update_lead_status(self, lead_id: str, status: LeadStatus) -> bool:
        """Update lead status in pipeline"""
        result = await self.collection.update_one(
            {"_id": lead_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"Lead status updated: {lead_id} -> {status}")
        return result.modified_count > 0
    
    async def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get summary of leads by pipeline stage"""
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        
        results = await self.collection.aggregate(pipeline).to_list(length=None)
        summary = {item["_id"]: item["count"] for item in results}
        
        return {
            "total_leads": await self.collection.count_documents({}),
            "by_status": summary,
            "conversion_rate": self._calculate_conversion_rate(summary)
        }
    
    def _calculate_conversion_rate(self, summary: Dict[str, int]) -> float:
        """Calculate lead conversion rate"""
        total = sum(summary.values())
        if total == 0:
            return 0.0
        won = summary.get(LeadStatus.WON, 0)
        return round((won / total) * 100, 2)


class CRMActivity:
    """CRM Activity tracking"""
    
    def __init__(self, database):
        self.db = database
        self.collection = database.crm_activities
    
    async def log_activity(
        self,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a CRM activity"""
        activity = {
            "user_id": user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details or {},
            "created_at": datetime.utcnow()
        }
        
        result = await self.collection.insert_one(activity)
        logger.info(f"CRM activity logged: {action} on {entity_type}")
        return str(result.inserted_id)
    
    async def get_user_activities(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get activities for a specific user"""
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit)
        activities = await cursor.to_list(length=limit)
        
        for activity in activities:
            activity["id"] = str(activity["_id"])
            del activity["_id"]
        
        return activities


class CRMIntegration:
    """Main CRM Integration class"""
    
    def __init__(self, database):
        self.db = database
        self.leads = CRMLead(database)
        self.activities = CRMActivity(database)
