"""
Monitoring Router
Endpoints for database info, observer, and server information
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from app.database import get_database
from app.db_info import DatabaseInfo
from app.observer import Observer, MetricType, AlertSeverity
from app.server_info import ServerInfo
from app.schemas import MetricRecord, AlertCreate, AlertResponse, HealthStatus
from app.auth import decode_token
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


def get_current_user(authorization: str = Header(None)) -> dict:
    """Extract current user from authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token = authorization.split(" ")[1]
        token_data = decode_token(token)
        if token_data:
            return {"user_id": token_data.user_id, "email": token_data.email, "role": token_data.role}
    except Exception:
        pass

    raise HTTPException(status_code=401, detail="Invalid token")


# ========== Database Info Endpoints ==========
@router.get("/db/status")
async def get_database_status(db = Depends(get_database)):
    """Get database connection status"""
    db_info = DatabaseInfo(db)
    status = await db_info.get_status()
    return status


@router.get("/db/collections")
async def get_collections_info(db = Depends(get_database)):
    """Get information about all collections"""
    db_info = DatabaseInfo(db)
    collections = await db_info.get_collections_info()
    return {"collections": collections}


@router.get("/db/stats")
async def get_database_stats(db = Depends(get_database)):
    """Get database statistics"""
    db_info = DatabaseInfo(db)
    stats = await db_info.get_database_stats()
    return stats


@router.get("/db/collections/{collection_name}/stats")
async def get_collection_stats(collection_name: str, db = Depends(get_database)):
    """Get statistics for a specific collection"""
    db_info = DatabaseInfo(db)
    stats = await db_info.get_collection_stats(collection_name)
    return stats


@router.get("/db/operations")
async def get_recent_operations(limit: int = 10, db = Depends(get_database)):
    """Get recent database operations"""
    db_info = DatabaseInfo(db)
    operations = await db_info.get_recent_operations(limit)
    return {"operations": operations}


@router.get("/db/collections/{collection_name}/indexes")
async def get_collection_indexes(collection_name: str, db = Depends(get_database)):
    """Get index information for a collection"""
    db_info = DatabaseInfo(db)
    indexes = await db_info.get_index_info(collection_name)
    return {"indexes": indexes}


# ========== Server Info Endpoints ==========
@router.get("/server/system")
async def get_system_info():
    """Get system information"""
    return ServerInfo.get_system_info()


@router.get("/server/cpu")
async def get_cpu_info():
    """Get CPU information"""
    return ServerInfo.get_cpu_info()


@router.get("/server/memory")
async def get_memory_info():
    """Get memory information"""
    return ServerInfo.get_memory_info()


@router.get("/server/disk")
async def get_disk_info():
    """Get disk information"""
    return ServerInfo.get_disk_info()


@router.get("/server/network")
async def get_network_info():
    """Get network information"""
    return ServerInfo.get_network_info()


@router.get("/server/all")
async def get_all_server_info():
    """Get all server information"""
    return {
        "system": ServerInfo.get_system_info(),
        "cpu": ServerInfo.get_cpu_info(),
        "memory": ServerInfo.get_memory_info(),
        "disk": ServerInfo.get_disk_info(),
        "network": ServerInfo.get_network_info()
    }


# ========== Observer/Monitoring Endpoints ==========
@router.post("/metrics")
async def record_metric(
    metric: MetricRecord,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Record a metric"""
    current_user = get_current_user(authorization)
    
    observer = Observer(db)
    metric_id = await observer.record_metric(
        metric_type=metric.metric_type,
        value=metric.value,
        tags=metric.tags,
        timestamp=metric.timestamp
    )
    
    return {"message": "Metric recorded successfully", "metric_id": metric_id}


@router.get("/metrics")
async def get_metrics(
    metric_type: str = None,
    start_time: str = None,
    end_time: str = None,
    limit: int = 100,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Get metrics with filters"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    observer = Observer(db)
    
    metric_type_enum = None
    if metric_type:
        try:
            metric_type_enum = MetricType(metric_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid metric type")
    
    start_dt = None
    end_dt = None
    
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time)
        except:
            pass
    
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time)
        except:
            pass
    
    metrics = await observer.get_metrics(metric_type_enum, start_dt, end_dt, limit)
    
    return {"items": metrics, "count": len(metrics)}


@router.get("/metrics/summary/{metric_type}")
async def get_metric_summary(
    metric_type: str,
    start_time: str = None,
    end_time: str = None,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Get metric summary statistics"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    observer = Observer(db)
    
    try:
        metric_type_enum = MetricType(metric_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid metric type")
    
    start_dt = None
    end_dt = None
    
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time)
        except:
            pass
    
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time)
        except:
            pass
    
    summary = await observer.get_metric_summary(metric_type_enum, start_dt, end_dt)
    
    return summary


@router.post("/alerts")
async def create_alert(
    alert: AlertCreate,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Create an alert"""
    current_user = get_current_user(authorization)
    
    observer = Observer(db)
    alert_id = await observer.create_alert(
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        source=alert.source,
        tags=alert.tags
    )
    
    return {"message": "Alert created successfully", "alert_id": alert_id}


@router.get("/alerts")
async def get_alerts(
    severity: str = None,
    resolved: bool = None,
    limit: int = 50,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Get alerts with filters"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    observer = Observer(db)
    
    severity_enum = None
    if severity:
        try:
            severity_enum = AlertSeverity(severity)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid severity")
    
    alerts = await observer.get_alerts(severity_enum, resolved, limit)
    
    return {"items": alerts, "count": len(alerts)}


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Resolve an alert"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    observer = Observer(db)
    resolved = await observer.resolve_alert(alert_id)
    
    if not resolved:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert resolved successfully"}


@router.get("/health")
async def get_system_health(db = Depends(get_database)):
    """Get overall system health status"""
    observer = Observer(db)
    health = await observer.get_system_health()
    return health


@router.get("/logs")
async def get_logs(
    level: str = None,
    source: str = None,
    start_time: str = None,
    end_time: str = None,
    limit: int = 100,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Get system logs with filters"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    observer = Observer(db)
    
    start_dt = None
    end_dt = None
    
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time)
        except:
            pass
    
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time)
        except:
            pass
    
    logs = await observer.get_logs(level, source, start_dt, end_dt, limit)
    
    return {"items": logs, "count": len(logs)}
