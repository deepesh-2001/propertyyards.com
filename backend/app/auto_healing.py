"""
Auto-Healing Service
Self-healing capabilities for automatic recovery from failures
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """Types of failures"""
    SERVICE_DOWN = "service_down"
    HIGH_ERROR_RATE = "high_error_rate"
    HIGH_LATENCY = "high_latency"
    MEMORY_LEAK = "memory_leak"
    DATABASE_CONNECTION = "database_connection"
    CACHE_FAILURE = "cache_failure"
    DISK_FULL = "disk_full"
    NETWORK_ISSUE = "network_issue"


class RecoveryAction(Enum):
    """Recovery actions"""
    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE = "clear_cache"
    RECONNECT_DATABASE = "reconnect_database"
    SCALE_UP = "scale_up"
    KILL_PROCESS = "kill_process"
    SEND_ALERT = "send_alert"
    NO_ACTION = "no_action"


@dataclass
class FailureEvent:
    """Failure event record"""
    timestamp: datetime
    failure_type: FailureType
    service: str
    severity: str  # low, medium, high, critical
    description: str
    metric_value: Optional[float] = None
    auto_recovered: bool = False
    recovery_time_ms: Optional[int] = None


@dataclass
class RecoveryRule:
    """Recovery rule definition"""
    name: str
    failure_type: FailureType
    condition: str
    threshold: float
    actions: List[RecoveryAction]
    cooldown_minutes: int
    max_attempts: int
    enabled: bool = True


class AutoHealingService:
    """Self-healing service manager"""

    def __init__(self):
        self.enabled = False
        self.is_monitoring = False

        # Recovery rules
        self.recovery_rules: List[RecoveryRule] = [
            RecoveryRule(
                name="high_error_rate",
                failure_type=FailureType.HIGH_ERROR_RATE,
                condition="error_rate >",
                threshold=10.0,  # 10% error rate
                actions=[RecoveryAction.CLEAR_CACHE, RecoveryAction.RESTART_SERVICE],
                cooldown_minutes=5,
                max_attempts=3
            ),
            RecoveryRule(
                name="high_latency",
                failure_type=FailureType.HIGH_LATENCY,
                condition="response_time >",
                threshold=2000.0,  # 2 seconds
                actions=[RecoveryAction.SCALE_UP, RecoveryAction.CLEAR_CACHE],
                cooldown_minutes=10,
                max_attempts=2
            ),
            RecoveryRule(
                name="memory_leak",
                failure_type=FailureType.MEMORY_LEAK,
                condition="memory_growth >",
                threshold=100.0,  # 100MB growth per hour
                actions=[RecoveryAction.RESTART_SERVICE],
                cooldown_minutes=30,
                max_attempts=1
            ),
            RecoveryRule(
                name="cache_failure",
                failure_type=FailureType.CACHE_FAILURE,
                condition="cache_errors >",
                threshold=5.0,
                actions=[RecoveryAction.RECONNECT_DATABASE, RecoveryAction.CLEAR_CACHE],
                cooldown_minutes=3,
                max_attempts=5
            ),
            RecoveryRule(
                name="database_connection",
                failure_type=FailureType.DATABASE_CONNECTION,
                condition="db_errors >",
                threshold=3.0,
                actions=[RecoveryAction.RECONNECT_DATABASE, RecoveryAction.SEND_ALERT],
                cooldown_minutes=5,
                max_attempts=3
            ),
        ]

        # Failure history
        self.failure_events: List[FailureEvent] = []
        self.recent_failures: Dict[str, List[datetime]] = {}  # rule -> timestamps
        self.max_events = 1000

        # Health check config
        self.health_check_interval = 30  # seconds
        self.healthy_services: Dict[str, bool] = {}

        # Recovery handlers
        self.recovery_handlers: Dict[RecoveryAction, Callable] = {
            RecoveryAction.RESTART_SERVICE: self._restart_service,
            RecoveryAction.CLEAR_CACHE: self._clear_cache,
            RecoveryAction.RECONNECT_DATABASE: self._reconnect_database,
            RecoveryAction.SCALE_UP: self._scale_up,
            RecoveryAction.KILL_PROCESS: self._kill_process,
            RecoveryAction.SEND_ALERT: self._send_alert,
        }

    async def start(self):
        """Start auto-healing service"""
        self.enabled = True
        self.is_monitoring = True
        asyncio.create_task(self._health_monitoring_loop())
        asyncio.create_task(self._failure_detection_loop())
        logger.info("Auto-healing service started")

    async def stop(self):
        """Stop auto-healing service"""
        self.enabled = False
        self.is_monitoring = False
        logger.info("Auto-healing service stopped")

    async def _health_monitoring_loop(self):
        """Monitor service health"""
        while self.is_monitoring:
            try:
                # Check all services
                services = [
                    "api", "database", "cache", "background_tasks",
                    "ai_image_service", "social_media", "telegram_bot"
                ]

                for service in services:
                    healthy = await self._check_service_health(service)
                    self.healthy_services[service] = healthy

                    if not healthy and self.enabled:
                        await self._handle_failure(
                            FailureType.SERVICE_DOWN,
                            service,
                            "high",
                            f"Service {service} is not responding"
                        )

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)

    async def _failure_detection_loop(self):
        """Detect failures from metrics"""
        while self.is_monitoring:
            try:
                # Get current metrics
                metrics = await self._collect_metrics()

                # Check each rule
                for rule in self.recovery_rules:
                    if not rule.enabled:
                        continue

                    if self._check_failure_condition(rule, metrics):
                        if self._should_attempt_recovery(rule):
                            await self._handle_failure(
                                rule.failure_type,
                                "api",
                                "high",
                                f"{rule.name} threshold exceeded: {metrics.get(rule.failure_type.value, 0)}",
                                metrics.get(rule.failure_type.value)
                            )

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Failure detection error: {e}")
                await asyncio.sleep(30)

    async def _check_service_health(self, service: str) -> bool:
        """Check health of a specific service"""
        try:
            from app.service_manager import service_manager

            status = service_manager.get_service_status(service)
            if status:
                return status.status.value == "ready"

            # Fallback checks
            if service == "database":
                return await self._check_database_health()
            elif service == "cache":
                return await self._check_cache_health()

            return True

        except Exception as e:
            logger.warning(f"Health check failed for {service}: {e}")
            return False

    async def _check_database_health(self) -> bool:
        """Check database connectivity"""
        try:
            from app.database import get_db
            database = get_db()
            await database.command("ping")
            return True
        except:
            return False

    async def _check_cache_health(self) -> bool:
        """Check cache connectivity"""
        try:
            from app.cache import cache
            await cache.ping()
            return True
        except:
            return False

    async def _collect_metrics(self) -> Dict[str, float]:
        """Collect system metrics"""
        from app.usage_tracker import usage_tracker

        # Get current metrics
        load = usage_tracker.get_current_load()
        endpoint_stats = usage_tracker.get_endpoint_stats()

        # Calculate error rate
        total_calls = 0
        total_errors = 0
        total_response_time = 0

        for stats in endpoint_stats.values():
            total_calls += stats["total_calls"]
            total_errors += stats["error_count"]
            total_response_time += stats["avg_response_time_ms"] * stats["total_calls"]

        error_rate = (total_errors / total_calls * 100) if total_calls > 0 else 0
        avg_response_time = total_response_time / total_calls if total_calls > 0 else 0

        # Get resource metrics
        import psutil
        memory = psutil.virtual_memory()
        memory_growth = self._calculate_memory_growth(memory.used)

        return {
            "error_rate": error_rate,
            "response_time": avg_response_time,
            "cpu_percent": load.get("cpu_percent", 0),
            "memory_percent": memory.percent,
            "memory_growth": memory_growth,
            "cache_errors": 0,  # Would track cache errors
            "db_errors": 0,  # Would track DB errors
        }

    def _calculate_memory_growth(self, current_memory: int) -> float:
        """Calculate memory growth rate"""
        # Simplified - would track over time
        return 0.0

    def _check_failure_condition(self, rule: RecoveryRule, metrics: Dict[str, float]) -> bool:
        """Check if failure condition is met"""
        metric_value = metrics.get(rule.failure_type.value, 0)

        if rule.condition == "error_rate >":
            return metric_value > rule.threshold
        elif rule.condition == "response_time >":
            return metric_value > rule.threshold
        elif rule.condition == "memory_growth >":
            return metric_value > rule.threshold
        elif rule.condition == "cache_errors >":
            return metric_value > rule.threshold
        elif rule.condition == "db_errors >":
            return metric_value > rule.threshold

        return False

    def _should_attempt_recovery(self, rule: RecoveryRule) -> bool:
        """Check if recovery should be attempted"""
        # Check cooldown
        now = datetime.utcnow()
        recent = self.recent_failures.get(rule.name, [])

        # Clean old failures
        cutoff = now - timedelta(minutes=rule.cooldown_minutes)
        recent = [t for t in recent if t > cutoff]
        self.recent_failures[rule.name] = recent

        # Check max attempts
        if len(recent) >= rule.max_attempts:
            logger.warning(f"Max recovery attempts reached for {rule.name}")
            return False

        return True

    async def _handle_failure(
        self,
        failure_type: FailureType,
        service: str,
        severity: str,
        description: str,
        metric_value: Optional[float] = None
    ):
        """Handle a failure event"""
        start_time = datetime.utcnow()

        event = FailureEvent(
            timestamp=start_time,
            failure_type=failure_type,
            service=service,
            severity=severity,
            description=description,
            metric_value=metric_value
        )

        self.failure_events.append(event)
        if len(self.failure_events) > self.max_events:
            self.failure_events = self.failure_events[-self.max_events:]

        logger.warning(f"Failure detected: {failure_type.value} - {description}")

        if not self.enabled:
            return

        # Find recovery rule
        rule = self._find_recovery_rule(failure_type)
        if not rule:
            return

        # Execute recovery actions
        recovered = False
        for action in rule.actions:
            try:
                handler = self.recovery_handlers.get(action)
                if handler:
                    success = await handler(service)
                    if success:
                        recovered = True
                        logger.info(f"Recovery action {action.value} succeeded for {service}")
                        break
            except Exception as e:
                logger.error(f"Recovery action {action.value} failed: {e}")

        # Update event
        event.auto_recovered = recovered
        event.recovery_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Record attempt
        if rule.name not in self.recent_failures:
            self.recent_failures[rule.name] = []
        self.recent_failures[rule.name].append(datetime.utcnow())

        # Send alert if not recovered
        if not recovered:
            await self._send_alert(f"Failed to auto-recover {service}: {description}")

    def _find_recovery_rule(self, failure_type: FailureType) -> Optional[RecoveryRule]:
        """Find recovery rule for failure type"""
        for rule in self.recovery_rules:
            if rule.failure_type == failure_type and rule.enabled:
                return rule
        return None

    # Recovery action handlers
    async def _restart_service(self, service: str) -> bool:
        """Restart a service"""
        try:
            from app.service_manager import service_manager

            # Get service instance
            instance = service_manager.get_service(service)
            if not instance:
                return False

            # Restart logic depends on service type
            if hasattr(instance, 'restart'):
                await instance.restart()
            elif hasattr(instance, 'stop') and hasattr(instance, 'start'):
                await instance.stop()
                await asyncio.sleep(2)
                await instance.start()

            logger.info(f"Service {service} restarted")
            return True

        except Exception as e:
            logger.error(f"Failed to restart {service}: {e}")
            return False

    async def _clear_cache(self, service: str) -> bool:
        """Clear cache"""
        try:
            from app.cache import invalidate_cache_pattern
            from app.cache_pipeline import local_cache

            # Clear all caches
            await invalidate_cache_pattern("*")
            local_cache.clear()

            logger.info("Cache cleared")
            return True

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    async def _reconnect_database(self, service: str) -> bool:
        """Reconnect to database"""
        try:
            from app.database import close_database, init_database

            await close_database()
            await asyncio.sleep(1)
            await init_database()

            logger.info("Database reconnected")
            return True

        except Exception as e:
            logger.error(f"Failed to reconnect database: {e}")
            return False

    async def _scale_up(self, service: str) -> bool:
        """Scale up resources"""
        try:
            from app.auto_scaler import auto_scaler

            if auto_scaler.current_instances < auto_scaler.max_instances:
                auto_scaler.manual_scale(auto_scaler.current_instances + 1)
                logger.info("Scaled up resources")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to scale up: {e}")
            return False

    async def _kill_process(self, service: str) -> bool:
        """Kill and restart process"""
        try:
            import os
            import signal

            # Send restart signal
            os.kill(os.getpid(), signal.SIGTERM)
            return True

        except Exception as e:
            logger.error(f"Failed to kill process: {e}")
            return False

    async def _send_alert(self, message: str) -> bool:
        """Send alert notification"""
        try:
            from app.notification import notification_manager

            await notification_manager.send_notification(
                type="alert",
                message=message,
                priority="high",
                channels=["email", "slack"]
            )

            return True

        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary"""
        total_failures = len(self.failure_events)
        auto_recovered = sum(1 for e in self.failure_events if e.auto_recovered)

        return {
            "enabled": self.enabled,
            "is_monitoring": self.is_monitoring,
            "services_health": self.healthy_services,
            "total_failures_24h": len([
                e for e in self.failure_events
                if e.timestamp > datetime.utcnow() - timedelta(hours=24)
            ]),
            "auto_recovery_rate": (
                auto_recovered / total_failures * 100 if total_failures > 0 else 100
            ),
            "recent_failures": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "type": e.failure_type.value,
                    "service": e.service,
                    "severity": e.severity,
                    "recovered": e.auto_recovered,
                    "recovery_time_ms": e.recovery_time_ms
                }
                for e in self.failure_events[-10:]
            ]
        }

    def enable_rule(self, rule_name: str) -> bool:
        """Enable a recovery rule"""
        for rule in self.recovery_rules:
            if rule.name == rule_name:
                rule.enabled = True
                return True
        return False

    def disable_rule(self, rule_name: str) -> bool:
        """Disable a recovery rule"""
        for rule in self.recovery_rules:
            if rule.name == rule_name:
                rule.enabled = False
                return True
        return False


# Global instance
auto_healing = AutoHealingService()
