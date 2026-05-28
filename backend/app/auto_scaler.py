"""
Auto-Scaling Manager
Automatically scale application resources based on load and demand
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ScalingTrigger(Enum):
    """Scaling trigger types"""
    CPU = "cpu"
    MEMORY = "memory"
    REQUEST_RATE = "request_rate"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    QUEUE_DEPTH = "queue_depth"
    SCHEDULE = "schedule"
    MANUAL = "manual"


class ScalingAction(Enum):
    """Scaling actions"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    NO_ACTION = "no_action"


@dataclass
class ScalingRule:
    """Auto-scaling rule"""
    name: str
    trigger: ScalingTrigger
    metric: str
    threshold_high: float
    threshold_low: float
    scale_up_step: int
    scale_down_step: int
    cooldown_minutes: int
    enabled: bool = True


@dataclass
class ScalingEvent:
    """Scaling event record"""
    timestamp: datetime
    action: ScalingAction
    reason: str
    from_instances: int
    to_instances: int
    metric_value: float
    rule_triggered: str


class AutoScaler:
    """Automatic scaling manager"""

    def __init__(self):
        self.enabled = False
        self.min_instances = 1
        self.max_instances = 10
        self.current_instances = 1
        self.target_instances = 1

        # Scaling rules
        self.rules: List[ScalingRule] = [
            ScalingRule(
                name="cpu_high",
                trigger=ScalingTrigger.CPU,
                metric="cpu_percent",
                threshold_high=75.0,
                threshold_low=30.0,
                scale_up_step=2,
                scale_down_step=1,
                cooldown_minutes=5
            ),
            ScalingRule(
                name="memory_high",
                trigger=ScalingTrigger.MEMORY,
                metric="memory_percent",
                threshold_high=80.0,
                threshold_low=40.0,
                scale_up_step=2,
                scale_down_step=1,
                cooldown_minutes=5
            ),
            ScalingRule(
                name="request_rate",
                trigger=ScalingTrigger.REQUEST_RATE,
                metric="requests_per_second",
                threshold_high=1000.0,
                threshold_low=100.0,
                scale_up_step=1,
                scale_down_step=1,
                cooldown_minutes=3
            ),
            ScalingRule(
                name="response_time",
                trigger=ScalingTrigger.RESPONSE_TIME,
                metric="avg_response_time_ms",
                threshold_high=500.0,
                threshold_low=100.0,
                scale_up_step=2,
                scale_down_step=1,
                cooldown_minutes=5
            ),
            ScalingRule(
                name="error_rate",
                trigger=ScalingTrigger.ERROR_RATE,
                metric="error_rate_percent",
                threshold_high=10.0,
                threshold_low=2.0,
                scale_up_step=2,
                scale_down_step=1,
                cooldown_minutes=5
            ),
        ]

        # Event history
        self.scaling_events: List[ScalingEvent] = []
        self.last_scaling_action: Optional[datetime] = None

        # Metrics tracking
        self.metrics_history: Dict[str, List[tuple]] = {}
        self.metrics_window_minutes = 10

        # Predictive scaling
        self.predictive_enabled = True
        self.schedule_rules: List[Dict] = []

    async def start(self):
        """Start auto-scaler"""
        self.enabled = True
        asyncio.create_task(self._scaling_loop())
        asyncio.create_task(self._predictive_scaling_loop())
        logger.info("Auto-scaler started")

    async def stop(self):
        """Stop auto-scaler"""
        self.enabled = False
        logger.info("Auto-scaler stopped")

    async def _scaling_loop(self):
        """Main scaling decision loop"""
        while self.enabled:
            try:
                # Collect metrics
                metrics = await self._collect_metrics()

                # Evaluate rules
                action, reason, rule = self._evaluate_rules(metrics)

                # Execute scaling if needed
                if action != ScalingAction.NO_ACTION:
                    await self._execute_scaling(action, reason, rule, metrics)

                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Scaling loop error: {e}")
                await asyncio.sleep(60)

    async def _collect_metrics(self) -> Dict[str, float]:
        """Collect current system metrics"""
        from app.usage_tracker import usage_tracker

        # Get current load
        load = usage_tracker.get_current_load()

        # Get response time stats
        endpoint_stats = usage_tracker.get_endpoint_stats()

        avg_response_time = 0
        total_calls = 0
        total_errors = 0

        for stats in endpoint_stats.values():
            total_calls += stats["total_calls"]
            total_errors += stats["error_count"]
            avg_response_time += stats["avg_response_time_ms"] * stats["total_calls"]

        if total_calls > 0:
            avg_response_time /= total_calls

        error_rate = (total_errors / total_calls * 100) if total_calls > 0 else 0

        # Estimate requests per second from buffer
        from app.usage_tracker import usage_tracker
        requests_per_second = len(usage_tracker.buffer) / 60  # Approximate

        metrics = {
            "cpu_percent": load.get("cpu_percent", 0),
            "memory_percent": (load.get("memory_mb", 0) / 1024) * 100,  # Assuming 1GB
            "requests_per_second": requests_per_second,
            "avg_response_time_ms": avg_response_time,
            "error_rate_percent": error_rate,
            "active_connections": load.get("active_connections", 0),
        }

        # Store in history
        timestamp = datetime.utcnow()
        for metric, value in metrics.items():
            if metric not in self.metrics_history:
                self.metrics_history[metric] = []
            self.metrics_history[metric].append((timestamp, value))

            # Trim old data
            cutoff = timestamp - timedelta(minutes=self.metrics_window_minutes)
            self.metrics_history[metric] = [
                (t, v) for t, v in self.metrics_history[metric] if t > cutoff
            ]

        return metrics

    def _evaluate_rules(self, metrics: Dict[str, float]) -> tuple[ScalingAction, str, Optional[ScalingRule]]:
        """Evaluate scaling rules and return action"""
        # Check cooldown
        if self.last_scaling_action:
            cooldown_end = self.last_scaling_action + timedelta(minutes=5)
            if datetime.utcnow() < cooldown_end:
                return ScalingAction.NO_ACTION, "In cooldown period", None

        # Check each rule
        scale_up_score = 0
        scale_down_score = 0
        triggered_rules = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            value = metrics.get(rule.metric, 0)

            if value >= rule.threshold_high:
                scale_up_score += 1
                triggered_rules.append((rule, value, "high"))
            elif value <= rule.threshold_low:
                scale_down_score += 1
                triggered_rules.append((rule, value, "low"))

        # Determine action
        if scale_up_score >= 2:  # Multiple triggers for scale up
            # Find rule with highest value
            rule, value, _ = max(triggered_rules, key=lambda x: x[1])
            return ScalingAction.SCALE_UP, f"High load: {rule.metric}={value:.1f}", rule

        if scale_down_score >= 3:  # All metrics low for scale down
            rule, value, _ = min(triggered_rules, key=lambda x: x[1])
            return ScalingAction.SCALE_DOWN, f"Low load: {rule.metric}={value:.1f}", rule

        return ScalingAction.NO_ACTION, "Load within normal range", None

    async def _execute_scaling(
        self,
        action: ScalingAction,
        reason: str,
        rule: ScalingRule,
        metrics: Dict[str, float]
    ):
        """Execute scaling action"""
        old_instances = self.current_instances

        if action == ScalingAction.SCALE_UP:
            new_instances = min(
                self.current_instances + rule.scale_up_step,
                self.max_instances
            )
        else:  # SCALE_DOWN
            new_instances = max(
                self.current_instances - rule.scale_down_step,
                self.min_instances
            )

        if new_instances == self.current_instances:
            return

        self.target_instances = new_instances

        # Log event
        event = ScalingEvent(
            timestamp=datetime.utcnow(),
            action=action,
            reason=reason,
            from_instances=old_instances,
            to_instances=new_instances,
            metric_value=metrics.get(rule.metric, 0),
            rule_triggered=rule.name
        )
        self.scaling_events.append(event)
        self.last_scaling_action = event.timestamp

        # Execute scaling (platform-specific)
        await self._scale_instances(old_instances, new_instances)

        self.current_instances = new_instances

        logger.info(
            f"Scaling {action.value}: {old_instances} -> {new_instances} instances. "
            f"Reason: {reason}"
        )

    async def _scale_instances(self, from_count: int, to_count: int):
        """Execute actual scaling (platform-specific implementation)"""
        # This would integrate with:
        # - Kubernetes: kubectl scale deployment
        # - AWS: update Auto Scaling Group
        # - Docker Swarm: docker service scale
        # - Azure: update VMSS

        platform = self._detect_platform()

        if platform == "kubernetes":
            await self._scale_kubernetes(to_count)
        elif platform == "docker":
            await self._scale_docker(to_count)
        elif platform == "aws":
            await self._scale_aws(to_count)
        else:
            # Local scaling - just update internal count
            logger.info(f"Simulating scale to {to_count} instances (local mode)")

    def _detect_platform(self) -> str:
        """Detect deployment platform"""
        import os

        # Check for Kubernetes
        if os.path.exists("/var/run/secrets/kubernetes.io"):
            return "kubernetes"

        # Check for AWS
        if os.environ.get("AWS_EXECUTION_ENV"):
            return "aws"

        # Check for Docker
        if os.path.exists("/.dockerenv"):
            return "docker"

        return "local"

    async def _scale_kubernetes(self, replicas: int):
        """Scale Kubernetes deployment"""
        import subprocess

        try:
            subprocess.run(
                ["kubectl", "scale", "deployment", "propertyyards-api",
                 f"--replicas={replicas}", "-n", "default"],
                check=True,
                capture_output=True,
                timeout=30
            )
            logger.info(f"Kubernetes scaled to {replicas} replicas")
        except Exception as e:
            logger.error(f"Kubernetes scaling failed: {e}")

    async def _scale_docker(self, replicas: int):
        """Scale Docker Swarm service"""
        import subprocess

        try:
            subprocess.run(
                ["docker", "service", "scale", f"propertyyards_api={replicas}"],
                check=True,
                capture_output=True,
                timeout=30
            )
            logger.info(f"Docker service scaled to {replicas} replicas")
        except Exception as e:
            logger.error(f"Docker scaling failed: {e}")

    async def _scale_aws(self, desired_capacity: int):
        """Scale AWS Auto Scaling Group"""
        # Would use boto3
        logger.info(f"AWS scaling to {desired_capacity} (boto3 integration needed)")

    async def _predictive_scaling_loop(self):
        """Predictive scaling based on schedule and patterns"""
        while self.enabled and self.predictive_enabled:
            try:
                now = datetime.utcnow()

                # Check scheduled scaling
                for rule in self.schedule_rules:
                    if self._is_scheduled_time(rule, now):
                        await self._apply_scheduled_scaling(rule)

                # Daily pattern prediction (simplified)
                hour = now.hour
                weekday = now.weekday()

                # Scale up before peak hours
                if weekday < 5 and hour == 8:  # Weekday morning
                    await self._predicted_scale_up("Morning peak predicted")
                elif weekday < 5 and hour == 17:  # Weekday evening
                    await self._predicted_scale_up("Evening peak predicted")
                elif hour == 2:  # Low activity time
                    await self._predicted_scale_down("Night low activity")

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Predictive scaling error: {e}")
                await asyncio.sleep(300)

    def _is_scheduled_time(self, rule: Dict, now: datetime) -> bool:
        """Check if current time matches scheduled rule"""
        scheduled_time = rule.get("time")
        if not scheduled_time:
            return False

        scheduled_dt = datetime.fromisoformat(scheduled_time)
        return (now.hour == scheduled_dt.hour and
                now.minute == scheduled_dt.minute)

    async def _apply_scheduled_scaling(self, rule: Dict):
        """Apply scheduled scaling rule"""
        target = rule.get("instances", self.current_instances)
        if target != self.current_instances:
            await self._scale_instances(self.current_instances, target)
            self.current_instances = target
            logger.info(f"Scheduled scaling applied: {target} instances")

    async def _predicted_scale_up(self, reason: str):
        """Predictive scale up"""
        if self.current_instances < self.max_instances:
            target = min(self.current_instances + 1, self.max_instances)
            await self._scale_instances(self.current_instances, target)
            self.current_instances = target
            logger.info(f"Predictive scale up: {reason}")

    async def _predicted_scale_down(self, reason: str):
        """Predictive scale down"""
        if self.current_instances > self.min_instances:
            target = max(self.current_instances - 1, self.min_instances)
            await self._scale_instances(self.current_instances, target)
            self.current_instances = target
            logger.info(f"Predictive scale down: {reason}")

    def get_status(self) -> Dict[str, Any]:
        """Get auto-scaler status"""
        return {
            "enabled": self.enabled,
            "current_instances": self.current_instances,
            "target_instances": self.target_instances,
            "min_instances": self.min_instances,
            "max_instances": self.max_instances,
            "rules": [
                {
                    "name": r.name,
                    "enabled": r.enabled,
                    "metric": r.metric,
                    "threshold_high": r.threshold_high,
                    "threshold_low": r.threshold_low
                }
                for r in self.rules
            ],
            "recent_events": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "action": e.action.value,
                    "reason": e.reason,
                    "from": e.from_instances,
                    "to": e.to_instances
                }
                for e in self.scaling_events[-10:]
            ]
        }

    def manual_scale(self, target: int) -> bool:
        """Manual scaling override"""
        if self.min_instances <= target <= self.max_instances:
            asyncio.create_task(self._scale_instances(self.current_instances, target))
            self.current_instances = target
            return True
        return False


class LoadBalancer:
    """Simple load balancing logic"""

    def __init__(self):
        self.backends: List[Dict[str, Any]] = []
        self.current_index = 0
        self.health_check_interval = 30

    async def start_health_checks(self):
        """Start backend health monitoring"""
        while True:
            await self._check_backends()
            await asyncio.sleep(self.health_check_interval)

    async def _check_backends(self):
        """Check health of all backends"""
        for backend in self.backends:
            try:
                # Simple health check
                healthy = await self._ping_backend(backend)
                backend["healthy"] = healthy
                backend["last_check"] = datetime.utcnow()
            except Exception as e:
                backend["healthy"] = False
                logger.warning(f"Backend {backend['id']} health check failed: {e}")

    async def _ping_backend(self, backend: Dict) -> bool:
        """Ping backend to check health"""
        # Would make HTTP request to health endpoint
        return True  # Placeholder

    def get_next_backend(self) -> Optional[Dict]:
        """Get next healthy backend (round-robin)"""
        healthy_backends = [b for b in self.backends if b.get("healthy", True)]

        if not healthy_backends:
            return None

        backend = healthy_backends[self.current_index % len(healthy_backends)]
        self.current_index += 1
        return backend


# Global instance
auto_scaler = AutoScaler()
load_balancer = LoadBalancer()
