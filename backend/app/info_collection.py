"""
Info Collection Module
Collects and stores user information in database
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class InfoType(str, Enum):
    """Types of information collected"""
    PROPERTY_PREFERENCE = "property_preference"
    BUDGET_INFO = "budget_info"
    LOCATION_PREFERENCE = "location_preference"
    CONTACT_INFO = "contact_info"
    FEEDBACK = "feedback"
    SURVEY = "survey"
    LEAD_INFO = "lead_info"


class InfoCollection:
    """Information collection service"""
    
    def __init__(self, database):
        self.db = database
        self.collection = database.info_collection
    
    async def collect_info(
        self,
        user_id: str,
        info_type: InfoType,
        data: Dict[str, Any],
        source: str = "manual"
    ) -> str:
        """Collect and store user information"""
        info_record = {
            "user_id": user_id,
            "info_type": info_type,
            "data": data,
            "source": source,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.collection.insert_one(info_record)
        logger.info(f"Info collected: {result.inserted_id} - {info_type}")
        return str(result.inserted_id)
    
    async def get_user_info(
        self,
        user_id: str,
        info_type: Optional[InfoType] = None
    ) -> List[Dict[str, Any]]:
        """Get collected information for a user"""
        query_filter = {"user_id": user_id}
        if info_type:
            query_filter["info_type"] = info_type
        
        cursor = self.collection.find(query_filter).sort("created_at", -1)
        info_list = await cursor.to_list(length=100)
        
        for info in info_list:
            info["id"] = str(info["_id"])
            del info["_id"]
        
        return info_list
    
    async def update_info(
        self,
        info_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """Update collected information"""
        result = await self.collection.update_one(
            {"_id": info_id},
            {
                "$set": {
                    "data": data,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    async def delete_info(self, info_id: str) -> bool:
        """Delete collected information"""
        result = await self.collection.delete_one({"_id": info_id})
        return result.deleted_count > 0
    
    async def get_all_info(
        self,
        info_type: Optional[InfoType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get all collected information with filters"""
        query_filter = {}
        
        if info_type:
            query_filter["info_type"] = info_type
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query_filter["created_at"] = date_filter
        
        total = await self.collection.count_documents(query_filter)
        cursor = self.collection.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
        info_list = await cursor.to_list(length=limit)
        
        for info in info_list:
            info["id"] = str(info["_id"])
            del info["_id"]
        
        return {
            "items": info_list,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    async def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics of collected information"""
        pipeline = [
            {
                "$group": {
                    "_id": "$info_type",
                    "count": {"$sum": 1},
                    "latest": {"$max": "$created_at"}
                }
            }
        ]
        
        results = await self.collection.aggregate(pipeline).to_list(length=100)
        
        stats = {}
        for result in results:
            stats[result["_id"]] = {
                "count": result["count"],
                "latest": result["latest"]
            }
        
        total_count = await self.collection.count_documents({})
        
        return {
            "total_count": total_count,
            "by_type": stats
        }
