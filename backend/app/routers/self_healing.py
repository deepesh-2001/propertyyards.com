"""
Self-Healing Property Router
Endpoints for smart property monitoring and self-healing
"""
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_database
from app.self_healing import SelfHealingProperty
from app.schemas import (
    SensorCreate, SensorResponse, SensorReadingCreate,
    IssueResponse, PropertyHealthScore
)
from app.auth import decode_token
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/self-healing", tags=["Self-Healing"])


def get_current_user(authorization: str = None) -> dict:
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


# ========== Sensor Endpoints ==========
@router.post("/sensors", response_model=SensorResponse)
async def register_sensor(
    sensor_data: SensorCreate,
    authorization: str = None,
    db = Depends(get_database)
):
    """Register a sensor for a property"""
    current_user = get_current_user(authorization)
    
    self_healing = SelfHealingProperty(db)
    sensor_id = await self_healing.register_sensor(
        property_id=sensor_data.property_id,
        sensor_type=sensor_data.sensor_type,
        location=sensor_data.location,
        threshold_min=sensor_data.threshold_min,
        threshold_max=sensor_data.threshold_max,
        unit=sensor_data.unit
    )
    
    sensor = await self_healing.sensors_collection.find_one({"_id": sensor_id})
    sensor["id"] = str(sensor["_id"])
    del sensor["_id"]
    
    return SensorResponse(**sensor)


@router.post("/sensors/reading")
async def record_sensor_reading(
    reading_data: SensorReadingCreate,
    db = Depends(get_database)
):
    """Record sensor reading"""
    self_healing = SelfHealingProperty(db)
    recorded = await self_healing.record_sensor_reading(
        sensor_id=reading_data.sensor_id,
        value=reading_data.value,
        timestamp=reading_data.timestamp
    )
    
    if not recorded:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    return {"message": "Sensor reading recorded successfully"}


@router.get("/sensors/{sensor_id}", response_model=SensorResponse)
async def get_sensor(
    sensor_id: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get sensor by ID"""
    current_user = get_current_user(authorization)
    
    self_healing = SelfHealingProperty(db)
    sensor = await self_healing.sensors_collection.find_one({"_id": sensor_id})
    
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    sensor["id"] = str(sensor["_id"])
    del sensor["_id"]
    
    return SensorResponse(**sensor)


@router.get("/properties/{property_id}/sensors")
async def get_property_sensors(
    property_id: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get all sensors for a property"""
    current_user = get_current_user(authorization)
    
    self_healing = SelfHealingProperty(db)
    cursor = self_healing.sensors_collection.find({"property_id": property_id})
    sensors = await cursor.to_list(length=100)
    
    for sensor in sensors:
        sensor["id"] = str(sensor["_id"])
        del sensor["_id"]
    
    return {"items": sensors, "count": len(sensors)}


# ========== Issue Endpoints ==========
@router.get("/properties/{property_id}/issues")
async def get_property_issues(
    property_id: str,
    status: str = None,
    severity: str = None,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get issues for a property"""
    current_user = get_current_user(authorization)
    
    self_healing = SelfHealingProperty(db)
    issues = await self_healing.get_property_issues(
        property_id=property_id,
        status=status,
        severity=severity
    )
    
    return {"items": issues, "count": len(issues)}


@router.put("/issues/{issue_id}/resolve")
async def resolve_issue(
    issue_id: str,
    resolution_notes: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Resolve an issue"""
    current_user = get_current_user(authorization)
    
    self_healing = SelfHealingProperty(db)
    resolved = await self_healing.resolve_issue(issue_id, resolution_notes)
    
    if not resolved:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    return {"message": "Issue resolved successfully"}


# ========== Health Score Endpoints ==========
@router.get("/properties/{property_id}/health", response_model=PropertyHealthScore)
async def get_property_health_score(
    property_id: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get property health score"""
    current_user = get_current_user(authorization)
    
    self_healing = SelfHealingProperty(db)
    health_score = await self_healing.get_property_health_score(property_id)
    
    return PropertyHealthScore(**health_score)


@router.get("/properties/{property_id}/maintenance-logs")
async def get_maintenance_logs(
    property_id: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get maintenance logs for a property"""
    current_user = get_current_user(authorization)
    
    self_healing = SelfHealingProperty(db)
    cursor = self_healing.maintenance_logs_collection.find({"property_id": property_id}).sort("timestamp", -1)
    logs = await cursor.to_list(length=100)
    
    for log in logs:
        log["id"] = str(log["_id"])
        del log["_id"]
    
    return {"items": logs, "count": len(logs)}
