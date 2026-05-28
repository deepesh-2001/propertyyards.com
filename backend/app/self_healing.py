"""
Self-Healing Property Module
Handles smart property monitoring, issue detection, and automated healing
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class IssueType(str, Enum):
    """Types of property issues"""
    WATER_LEAK = "water_leak"
    ELECTRICAL = "electrical"
    HVAC = "hvac"
    PLUMBING = "plumbing"
    SECURITY = "security"
    FIRE = "fire"
    STRUCTURAL = "structural"
    PEST = "pest"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    AIR_QUALITY = "air_quality"


class IssueSeverity(str, Enum):
    """Issue severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HealingAction(str, Enum):
    """Types of healing actions"""
    AUTOMATIC_FIX = "automatic_fix"
    SCHEDULED_MAINTENANCE = "scheduled_maintenance"
    ALERT_OWNER = "alert_owner"
    CONTACT_SERVICE = "contact_service"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"


class SelfHealingProperty:
    """Self-healing property management"""
    
    def __init__(self, database):
        self.db = database
        self.sensors_collection = database.property_sensors
        self.issues_collection = database.property_issues
        self.healing_actions_collection = database.healing_actions
        self.maintenance_logs_collection = database.maintenance_logs
    
    async def register_sensor(
        self,
        property_id: str,
        sensor_type: str,
        location: str,
        threshold_min: float,
        threshold_max: float,
        unit: str
    ) -> str:
        """Register a sensor for a property"""
        sensor = {
            "property_id": property_id,
            "sensor_type": sensor_type,
            "location": location,
            "threshold_min": threshold_min,
            "threshold_max": threshold_max,
            "unit": unit,
            "current_value": None,
            "last_reading": None,
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.sensors_collection.insert_one(sensor)
        logger.info(f"Sensor registered: {result.inserted_id}")
        return str(result.inserted_id)
    
    async def record_sensor_reading(
        self,
        sensor_id: str,
        value: float,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Record sensor reading"""
        sensor = await self.sensors_collection.find_one({"_id": sensor_id})
        if not sensor:
            return False
        
        # Check if value is within threshold
        is_normal = sensor["threshold_min"] <= value <= sensor["threshold_max"]
        
        await self.sensors_collection.update_one(
            {"_id": sensor_id},
            {
                "$set": {
                    "current_value": value,
                    "last_reading": timestamp or datetime.utcnow(),
                    "status": "normal" if is_normal else "alert",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # If value is outside threshold, create issue
        if not is_normal:
            await self._create_issue_from_sensor(sensor, value)
        
        return True
    
    async def _create_issue_from_sensor(self, sensor: Dict[str, Any], value: float) -> str:
        """Create issue from sensor reading"""
        issue_type = self._map_sensor_to_issue(sensor["sensor_type"])
        severity = self._determine_severity(sensor, value)
        
        issue = {
            "property_id": sensor["property_id"],
            "sensor_id": str(sensor["_id"]),
            "issue_type": issue_type,
            "severity": severity,
            "description": f"{sensor['sensor_type']} reading {value} {sensor['unit']} outside normal range ({sensor['threshold_min']}-{sensor['threshold_max']})",
            "location": sensor["location"],
            "status": "detected",
            "auto_healable": True,
            "healing_action": None,
            "created_at": datetime.utcnow(),
            "resolved_at": None
        }
        
        result = await self.issues_collection.insert_one(issue)
        logger.warning(f"Issue detected: {result.inserted_id}")
        
        # Trigger healing action
        await self._trigger_healing_action(str(result.inserted_id))
        
        return str(result.inserted_id)
    
    def _map_sensor_to_issue(self, sensor_type: str) -> IssueType:
        """Map sensor type to issue type"""
        mapping = {
            "water_sensor": IssueType.WATER_LEAK,
            "electrical_sensor": IssueType.ELECTRICAL,
            "temperature_sensor": IssueType.TEMPERATURE,
            "humidity_sensor": IssueType.HUMIDITY,
            "air_quality_sensor": IssueType.AIR_QUALITY,
            "smoke_sensor": IssueType.FIRE,
            "motion_sensor": IssueType.SECURITY,
            "vibration_sensor": IssueType.STRUCTURAL
        }
        return mapping.get(sensor_type, IssueType.STRUCTURAL)
    
    def _determine_severity(self, sensor: Dict[str, Any], value: float) -> IssueSeverity:
        """Determine issue severity based on threshold deviation"""
        threshold_min = sensor["threshold_min"]
        threshold_max = sensor["threshold_max"]
        
        deviation = max(threshold_min - value, value - threshold_max, 0)
        range_size = threshold_max - threshold_min
        
        if deviation > range_size * 0.5:
            return IssueSeverity.CRITICAL
        elif deviation > range_size * 0.3:
            return IssueSeverity.HIGH
        elif deviation > range_size * 0.1:
            return IssueSeverity.MEDIUM
        else:
            return IssueSeverity.LOW
    
    async def _trigger_healing_action(self, issue_id: str):
        """Trigger appropriate healing action for an issue"""
        issue = await self.issues_collection.find_one({"_id": issue_id})
        if not issue:
            return
        
        # Determine healing action based on issue type and severity
        healing_action = self._determine_healing_action(issue)
        
        # Execute healing action
        await self._execute_healing_action(issue, healing_action)
    
    def _determine_healing_action(self, issue: Dict[str, Any]) -> HealingAction:
        """Determine appropriate healing action"""
        if issue["severity"] == IssueSeverity.CRITICAL:
            if issue["issue_type"] in [IssueType.FIRE, IssueType.ELECTRICAL]:
                return HealingAction.EMERGENCY_SHUTDOWN
            return HealingAction.CONTACT_SERVICE
        
        elif issue["severity"] == IssueSeverity.HIGH:
            return HealingAction.CONTACT_SERVICE
        
        elif issue["auto_healable"]:
            return HealingAction.AUTOMATIC_FIX
        
        else:
            return HealingAction.SCHEDULED_MAINTENANCE
    
    async def _execute_healing_action(self, issue: Dict[str, Any], action: HealingAction):
        """Execute healing action"""
        healing_record = {
            "issue_id": str(issue["_id"]),
            "property_id": issue["property_id"],
            "action": action,
            "status": "in_progress",
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "result": None
        }
        
        result = await self.healing_actions_collection.insert_one(healing_record)
        
        # Simulate healing action execution
        if action == HealingAction.AUTOMATIC_FIX:
            await self._execute_automatic_fix(issue)
        elif action == HealingAction.ALERT_OWNER:
            await self._alert_owner(issue)
        elif action == HealingAction.CONTACT_SERVICE:
            await self._contact_service(issue)
        
        # Update healing record
        await self.healing_actions_collection.update_one(
            {"_id": result.inserted_id},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        # Update issue status
        await self.issues_collection.update_one(
            {"_id": issue["_id"]},
            {
                "$set": {
                    "status": "healing_in_progress",
                    "healing_action": action
                }
            }
        )
    
    async def _execute_automatic_fix(self, issue: Dict[str, Any]):
        """Execute automatic fix for issue"""
        # Simulate automatic fix based on issue type
        fix_actions = {
            IssueType.TEMPERATURE: "Adjusting HVAC system",
            IssueType.HUMIDITY: "Adjusting dehumidifier",
            IssueType.AIR_QUALITY: "Activating air purifier",
            IssueType.WATER_LEAK: "Closing automatic valve",
            IssueType.ELECTRICAL: "Resetting circuit breaker"
        }
        
        action = fix_actions.get(issue["issue_type"], "Executing automated fix")
        logger.info(f"Executing automatic fix: {action}")
        
        # Log maintenance
        await self._log_maintenance(
            property_id=issue["property_id"],
            action=action,
            performed_by="system",
            issue_id=str(issue["_id"])
        )
    
    async def _alert_owner(self, issue: Dict[str, Any]):
        """Alert property owner about issue"""
        logger.warning(f"Alerting owner about issue: {issue['issue_type']}")
        # In production, this would send notification via email/WhatsApp
    
    async def _contact_service(self, issue: Dict[str, Any]):
        """Contact maintenance service"""
        logger.warning(f"Contacting service for issue: {issue['issue_type']}")
        # In production, this would contact maintenance service
    
    async def _log_maintenance(
        self,
        property_id: str,
        action: str,
        performed_by: str,
        issue_id: Optional[str] = None
    ):
        """Log maintenance action"""
        log = {
            "property_id": property_id,
            "action": action,
            "performed_by": performed_by,
            "issue_id": issue_id,
            "timestamp": datetime.utcnow()
        }
        
        await self.maintenance_logs_collection.insert_one(log)
    
    async def get_property_issues(
        self,
        property_id: str,
        status: Optional[str] = None,
        severity: Optional[IssueSeverity] = None
    ) -> List[Dict[str, Any]]:
        """Get issues for a property"""
        query_filter = {"property_id": property_id}
        
        if status:
            query_filter["status"] = status
        if severity:
            query_filter["severity"] = severity
        
        cursor = self.issues_collection.find(query_filter).sort("created_at", -1)
        issues = await cursor.to_list(length=100)
        
        for issue in issues:
            issue["id"] = str(issue["_id"])
            del issue["_id"]
        
        return issues
    
    async def resolve_issue(self, issue_id: str, resolution_notes: str) -> bool:
        """Mark issue as resolved"""
        result = await self.issues_collection.update_one(
            {"_id": issue_id},
            {
                "$set": {
                    "status": "resolved",
                    "resolution_notes": resolution_notes,
                    "resolved_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    async def get_property_health_score(self, property_id: str) -> Dict[str, Any]:
        """Calculate overall property health score"""
        issues = await self.get_property_issues(property_id)
        
        # Calculate health score based on active issues
        active_issues = [i for i in issues if i["status"] not in ["resolved", "healed"]]
        
        health_score = 100
        
        for issue in active_issues:
            if issue["severity"] == IssueSeverity.CRITICAL:
                health_score -= 30
            elif issue["severity"] == IssueSeverity.HIGH:
                health_score -= 20
            elif issue["severity"] == IssueSeverity.MEDIUM:
                health_score -= 10
            elif issue["severity"] == IssueSeverity.LOW:
                health_score -= 5
        
        health_score = max(0, min(100, health_score))
        
        # Determine health status
        if health_score >= 80:
            status = "healthy"
        elif health_score >= 60:
            status = "good"
        elif health_score >= 40:
            status = "fair"
        else:
            status = "poor"
        
        return {
            "property_id": property_id,
            "health_score": health_score,
            "health_status": status,
            "active_issues": len(active_issues),
            "total_issues": len(issues),
            "timestamp": datetime.utcnow()
        }
