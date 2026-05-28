"""
Observer Module
Monitors system metrics, logs, and performance
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics"""
    REQUEST_COUNT = "request_count"
    RESPONSE_TIME = "response_time"
    ERROR_COUNT = "error_count"
    DATABASE_QUERY_TIME = "database_query_time"
    CACHE_HIT_RATE = "cache_hit_rate"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Observer:
    """System observer for monitoring and alerting"""
    
    def __init__(self, database):
        self.db = database
        self.metrics_collection = database.metrics
        self.alerts_collection = database.alerts
        self.logs_collection = database.system_logs
    
    async def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        tags: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> str:
        """Record a metric"""
        metric = {
            "metric_type": metric_type,
            "value": value,
            "tags": tags or {},
            "timestamp": timestamp or datetime.utcnow()
        }
        
        result = await self.metrics_collection.insert_one(metric)
        logger.debug(f"Metric recorded: {metric_type} = {value}")
        return str(result.inserted_id)
    
    async def get_metrics(
        self,
        metric_type: Optional[MetricType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get metrics with filters"""
        query_filter = {}
        
        if metric_type:
            query_filter["metric_type"] = metric_type
        
        if start_time or end_time:
            time_filter = {}
            if start_time:
                time_filter["$gte"] = start_time
            if end_time:
                time_filter["$lte"] = end_time
            query_filter["timestamp"] = time_filter
        
        cursor = self.metrics_collection.find(query_filter).sort("timestamp", -1).limit(limit)
        metrics = await cursor.to_list(length=limit)
        
        for metric in metrics:
            metric["id"] = str(metric["_id"])
            del metric["_id"]
        
        return metrics
    
    async def get_metric_summary(
        self,
        metric_type: MetricType,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get metric summary statistics"""
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=1)
        if not end_time:
            end_time = datetime.utcnow()
        
        pipeline = [
            {
                "$match": {
                    "metric_type": metric_type,
                    "timestamp": {"$gte": start_time, "$lte": end_time}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "count": {"$sum": 1},
                    "avg": {"$avg": "$value"},
                    "min": {"$min": "$value"},
                    "max": {"$max": "$value"},
                    "sum": {"$sum": "$value"}
                }
            }
        ]
        
        result = await self.metrics_collection.aggregate(pipeline).to_list(length=1)
        
        if result:
            summary = result[0]
            del summary["_id"]
            return summary
        
        return {
            "count": 0,
            "avg": 0,
            "min": 0,
            "max": 0,
            "sum": 0
        }
    
    async def create_alert(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        source: str = "system",
        tags: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create an alert"""
        alert = {
            "severity": severity,
            "title": title,
            "message": message,
            "source": source,
            "tags": tags or {},
            "created_at": datetime.utcnow(),
            "resolved": False,
            "resolved_at": None
        }
        
        result = await self.alerts_collection.insert_one(alert)
        logger.warning(f"Alert created: {title} - {severity}")
        return str(result.inserted_id)
    
    async def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        resolved: Optional[bool] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get alerts with filters"""
        query_filter = {}
        
        if severity:
            query_filter["severity"] = severity
        
        if resolved is not None:
            query_filter["resolved"] = resolved
        
        cursor = self.alerts_collection.find(query_filter).sort("created_at", -1).limit(limit)
        alerts = await cursor.to_list(length=limit)
        
        for alert in alerts:
            alert["id"] = str(alert["_id"])
            del alert["_id"]
        
        return alerts
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        result = await self.alerts_collection.update_one(
            {"_id": alert_id},
            {
                "$set": {
                    "resolved": True,
                    "resolved_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    async def log_event(
        self,
        level: str,
        message: str,
        source: str = "system",
        extra: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a system event"""
        log_entry = {
            "level": level,
            "message": message,
            "source": source,
            "extra": extra or {},
            "timestamp": datetime.utcnow()
        }
        
        result = await self.logs_collection.insert_one(log_entry)
        return str(result.inserted_id)
    
    async def get_logs(
        self,
        level: Optional[str] = None,
        source: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get system logs with filters"""
        query_filter = {}
        
        if level:
            query_filter["level"] = level
        
        if source:
            query_filter["source"] = source
        
        if start_time or end_time:
            time_filter = {}
            if start_time:
                time_filter["$gte"] = start_time
            if end_time:
                time_filter["$lte"] = end_time
            query_filter["timestamp"] = time_filter
        
        cursor = self.logs_collection.find(query_filter).sort("timestamp", -1).limit(limit)
        logs = await cursor.to_list(length=limit)
        
        for log in logs:
            log["id"] = str(log["_id"])
            del log["_id"]
        
        return logs
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        # Get recent error count
        error_alerts = await self.get_alerts(severity=AlertSeverity.ERROR, limit=10)
        critical_alerts = await self.get_alerts(severity=AlertSeverity.CRITICAL, limit=10)
        
        # Get recent metrics
        recent_metrics = await self.get_metrics(limit=100)
        
        # Calculate health score
        health_score = 100
        health_score -= len(critical_alerts) * 20
        health_score -= len(error_alerts) * 10
        
        health_score = max(0, min(100, health_score))
        
        # Determine health status
        if health_score >= 80:
            status = "healthy"
        elif health_score >= 50:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "health_score": health_score,
            "critical_alerts": len(critical_alerts),
            "error_alerts": len(error_alerts),
            "recent_metrics_count": len(recent_metrics),
            "timestamp": datetime.utcnow()
        }
