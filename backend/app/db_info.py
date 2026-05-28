"""
Database Info Module
Provides database status, statistics, and health information
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class DatabaseInfo:
    """Database information and statistics"""
    
    def __init__(self, database):
        self.db = database
    
    async def get_status(self) -> Dict[str, Any]:
        """Get database connection status"""
        try:
            # Ping database to check connection
            await self.db.command('ping')
            return {
                "status": "connected",
                "timestamp": datetime.utcnow(),
                "healthy": True
            }
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return {
                "status": "disconnected",
                "timestamp": datetime.utcnow(),
                "healthy": False,
                "error": str(e)
            }
    
    async def get_collections_info(self) -> List[Dict[str, Any]]:
        """Get information about all collections"""
        try:
            collections = await self.db.list_collection_names()
            collection_info = []
            
            for collection_name in collections:
                count = await self.db[collection_name].count_documents({})
                collection_info.append({
                    "name": collection_name,
                    "document_count": count
                })
            
            return collection_info
        except Exception as e:
            logger.error(f"Failed to get collections info: {e}")
            return []
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            # Get server status
            server_status = await self.db.command('serverStatus')
            
            # Get collection stats
            collections_info = await self.get_collections_info()
            total_documents = sum(col["document_count"] for col in collections_info)
            
            return {
                "collections": collections_info,
                "total_collections": len(collections_info),
                "total_documents": total_documents,
                "server_version": server_status.get("version", "unknown"),
                "uptime": server_status.get("uptime", 0),
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
    
    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a specific collection"""
        try:
            collection = self.db[collection_name]
            count = await collection.count_documents({})
            
            # Get collection stats
            stats = await collection.stats()
            
            return {
                "collection_name": collection_name,
                "document_count": count,
                "size_bytes": stats.get("size", 0),
                "index_count": stats.get("nindexes", 0),
                "avg_obj_size": stats.get("avgObjSize", 0),
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats for {collection_name}: {e}")
            return {
                "error": str(e),
                "collection_name": collection_name,
                "timestamp": datetime.utcnow()
            }
    
    async def get_recent_operations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent database operations from the profiler"""
        try:
            # Get current operations
            current_ops = await self.db.current_op()
            
            operations = []
            for op in current_ops.get("inprog", [])[:limit]:
                operations.append({
                    "op": op.get("op"),
                    "ns": op.get("ns"),
                    "query": op.get("query"),
                    "microsecs_running": op.get("microsecs_running", 0),
                    "opid": op.get("opid")
                })
            
            return operations
        except Exception as e:
            logger.error(f"Failed to get recent operations: {e}")
            return []
    
    async def get_index_info(self, collection_name: str) -> List[Dict[str, Any]]:
        """Get index information for a collection"""
        try:
            collection = self.db[collection_name]
            indexes = await collection.list_indexes()
            
            index_info = []
            for index in indexes:
                index_info.append({
                    "name": index.get("name"),
                    "keys": index.get("key"),
                    "unique": index.get("unique", False),
                    "sparse": index.get("sparse", False)
                })
            
            return index_info
        except Exception as e:
            logger.error(f"Failed to get index info for {collection_name}: {e}")
            return []
