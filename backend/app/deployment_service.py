"""
Deployment Automation Service
Automated deployment, health checks, and rollback for all services
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import subprocess
import json
import os

logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """Deployment status"""
    PENDING = "pending"
    BUILDING = "building"
    DEPLOYING = "deploying"
    HEALTH_CHECKING = "health_checking"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ServiceType(Enum):
    """Types of deployable services"""
    API = "api"
    WORKER = "worker"
    SCHEDULER = "scheduler"
    BOT = "bot"
    FRONTEND = "frontend"


@dataclass
class DeploymentConfig:
    """Service deployment configuration"""
    service_name: str
    service_type: ServiceType
    dockerfile_path: str
    image_name: str
    replicas: int = 1
    cpu_limit: str = "500m"
    memory_limit: str = "512Mi"
    env_vars: Dict[str, str] = None
    health_check_url: str = "/health"
    port: int = 8000

    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = {}


@dataclass
class DeploymentRecord:
    """Deployment record"""
    id: str
    service_name: str
    version: str
    status: DeploymentStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    build_logs: List[str] = None
    error_message: Optional[str] = None
    rollback_version: Optional[str] = None

    def __post_init__(self):
        if self.build_logs is None:
            self.build_logs = []


class DeploymentService:
    """Automated deployment service"""

    def __init__(self):
        self.enabled = True
        self.deployments: Dict[str, DeploymentRecord] = {}
        self.service_configs: Dict[str, DeploymentConfig] = {}
        self.deployment_history: List[DeploymentRecord] = []
        self.max_history = 100

        # Initialize service configs for all our services
        self._init_service_configs()

    def _init_service_configs(self):
        """Initialize deployment configs for all services"""
        self.service_configs = {
            "api": DeploymentConfig(
                service_name="propertyyards-api",
                service_type=ServiceType.API,
                dockerfile_path="backend/Dockerfile",
                image_name="propertyyards/api",
                replicas=3,
                cpu_limit="1000m",
                memory_limit="1Gi",
                port=8000,
                health_check_url="/api/health"
            ),
            "telegram-bot": DeploymentConfig(
                service_name="telegram-bot",
                service_type=ServiceType.BOT,
                dockerfile_path="backend/Dockerfile.bot",
                image_name="propertyyards/telegram-bot",
                replicas=1,
                cpu_limit="200m",
                memory_limit="256Mi",
                port=8001
            ),
            "idle-processor": DeploymentConfig(
                service_name="idle-processor",
                service_type=ServiceType.WORKER,
                dockerfile_path="backend/Dockerfile.worker",
                image_name="propertyyards/idle-processor",
                replicas=2,
                cpu_limit="300m",
                memory_limit="512Mi",
                port=8002
            ),
            "cron-service": DeploymentConfig(
                service_name="cron-service",
                service_type=ServiceType.SCHEDULER,
                dockerfile_path="backend/Dockerfile.cron",
                image_name="propertyyards/cron-service",
                replicas=1,
                cpu_limit="200m",
                memory_limit="256Mi",
                port=8003
            ),
            "frontend": DeploymentConfig(
                service_name="frontend",
                service_type=ServiceType.FRONTEND,
                dockerfile_path="frontend/Dockerfile",
                image_name="propertyyards/frontend",
                replicas=2,
                cpu_limit="200m",
                memory_limit="128Mi",
                port=3000
            )
        }

    async def initialize(self):
        """Initialize deployment service"""
        logger.info("Deployment Service initialized")
        logger.info(f"Configured services: {list(self.service_configs.keys())}")

    async def deploy_service(
        self,
        service_name: str,
        version: str,
        environment: str = "production"
    ) -> DeploymentRecord:
        """Deploy a service with full automation"""
        config = self.service_configs.get(service_name)
        if not config:
            raise ValueError(f"Unknown service: {service_name}")

        deployment_id = f"deploy_{service_name}_{datetime.utcnow().timestamp()}"

        record = DeploymentRecord(
            id=deployment_id,
            service_name=service_name,
            version=version,
            status=DeploymentStatus.PENDING,
            started_at=datetime.utcnow()
        )

        self.deployments[deployment_id] = record

        try:
            # 1. Build Docker image
            record.status = DeploymentStatus.BUILDING
            await self._build_docker_image(config, version, record)

            # 2. Push to registry
            await self._push_to_registry(config, version, record)

            # 3. Deploy to Kubernetes
            record.status = DeploymentStatus.DEPLOYING
            await self._deploy_to_k8s(config, version, environment, record)

            # 4. Health check
            record.status = DeploymentStatus.HEALTH_CHECKING
            healthy = await self._health_check(config, environment)

            if healthy:
                record.status = DeploymentStatus.SUCCESS
                record.completed_at = datetime.utcnow()
                logger.info(f"Deployment successful: {deployment_id}")
            else:
                raise Exception("Health check failed")

        except Exception as e:
            record.status = DeploymentStatus.FAILED
            record.error_message = str(e)
            logger.error(f"Deployment failed: {deployment_id} - {e}")

            # Auto-rollback on failure
            await self.rollback_service(service_name, environment)

        # Save to history
        self.deployment_history.append(record)
        if len(self.deployment_history) > self.max_history:
            self.deployment_history = self.deployment_history[-self.max_history:]

        return record

    async def _build_docker_image(
        self,
        config: DeploymentConfig,
        version: str,
        record: DeploymentRecord
    ):
        """Build Docker image"""
        try:
            logger.info(f"Building Docker image: {config.image_name}:{version}")

            # Run docker build
            cmd = [
                "docker", "build",
                "-t", f"{config.image_name}:{version}",
                "-t", f"{config.image_name}:latest",
                "-f", config.dockerfile_path,
                "."
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )

            if result.returncode != 0:
                raise Exception(f"Docker build failed: {result.stderr}")

            record.build_logs.append(f"Built image: {config.image_name}:{version}")
            logger.info(f"Docker image built successfully")

        except subprocess.TimeoutExpired:
            raise Exception("Docker build timeout")
        except Exception as e:
            raise Exception(f"Build failed: {e}")

    async def _push_to_registry(
        self,
        config: DeploymentConfig,
        version: str,
        record: DeploymentRecord
    ):
        """Push image to container registry"""
        try:
            logger.info(f"Pushing to registry: {config.image_name}:{version}")

            # Push both versioned and latest tags
            for tag in [version, "latest"]:
                cmd = ["docker", "push", f"{config.image_name}:{tag}"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

                if result.returncode != 0:
                    raise Exception(f"Push failed: {result.stderr}")

            record.build_logs.append(f"Pushed to registry")
            logger.info(f"Image pushed successfully")

        except Exception as e:
            raise Exception(f"Registry push failed: {e}")

    async def _deploy_to_k8s(
        self,
        config: DeploymentConfig,
        version: str,
        environment: str,
        record: DeploymentRecord
    ):
        """Deploy to Kubernetes"""
        try:
            logger.info(f"Deploying to Kubernetes: {config.service_name}")

            namespace = f"propertyyards-{environment}"

            # Create namespace if doesn't exist
            subprocess.run(
                ["kubectl", "create", "namespace", namespace, "--dry-run=client", "-o", "yaml"],
                capture_output=True
            )

            # Update deployment with new image
            cmd = [
                "kubectl", "set", "image",
                f"deployment/{config.service_name}",
                f"{config.service_name}={config.image_name}:{version}",
                f"-n", namespace
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                # If deployment doesn't exist, create it
                await self._create_k8s_deployment(config, version, namespace)

            # Wait for rollout
            rollout_cmd = [
                "kubectl", "rollout", "status",
                f"deployment/{config.service_name}",
                f"-n", namespace,
                "--timeout=300s"
            ]

            result = subprocess.run(rollout_cmd, capture_output=True, text=True, timeout=320)

            if result.returncode != 0:
                raise Exception(f"Rollout failed: {result.stderr}")

            record.build_logs.append(f"Deployed to {environment}")
            logger.info(f"Kubernetes deployment successful")

        except Exception as e:
            raise Exception(f"K8s deployment failed: {e}")

    async def _create_k8s_deployment(
        self,
        config: DeploymentConfig,
        version: str,
        namespace: str
    ):
        """Create Kubernetes deployment manifest"""
        deployment_manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": config.service_name,
                "namespace": namespace,
                "labels": {
                    "app": config.service_name,
                    "version": version
                }
            },
            "spec": {
                "replicas": config.replicas,
                "selector": {
                    "matchLabels": {"app": config.service_name}
                },
                "template": {
                    "metadata": {
                        "labels": {"app": config.service_name}
                    },
                    "spec": {
                        "containers": [{
                            "name": config.service_name,
                            "image": f"{config.image_name}:{version}",
                            "ports": [{"containerPort": config.port}],
                            "resources": {
                                "limits": {
                                    "cpu": config.cpu_limit,
                                    "memory": config.memory_limit
                                },
                                "requests": {
                                    "cpu": "100m",
                                    "memory": "128Mi"
                                }
                            },
                            "env": [
                                {"name": k, "value": v}
                                for k, v in config.env_vars.items()
                            ],
                            "livenessProbe": {
                                "httpGet": {
                                    "path": config.health_check_url,
                                    "port": config.port
                                },
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10
                            },
                            "readinessProbe": {
                                "httpGet": {
                                    "path": config.health_check_url,
                                    "port": config.port
                                },
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5
                            }
                        }]
                    }
                }
            }
        }

        # Write manifest to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            json.dump(deployment_manifest, f)
            manifest_path = f.name

        try:
            # Apply manifest
            result = subprocess.run(
                ["kubectl", "apply", "-f", manifest_path, "-n", namespace],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                raise Exception(f"Manifest apply failed: {result.stderr}")

        finally:
            os.unlink(manifest_path)

    async def _health_check(
        self,
        config: DeploymentConfig,
        environment: str
    ) -> bool:
        """Perform health check on deployed service"""
        try:
            import aiohttp

            namespace = f"propertyyards-{environment}"

            # Get service endpoint
            cmd = [
                "kubectl", "get", "svc", config.service_name,
                "-n", namespace,
                "-o", "jsonpath={.status.loadBalancer.ingress[0].ip}"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            endpoint = result.stdout.strip()

            if not endpoint:
                # Use internal cluster URL
                endpoint = f"{config.service_name}.{namespace}.svc.cluster.local"

            health_url = f"http://{endpoint}:{config.port}{config.health_check_url}"

            # Try health check multiple times
            for attempt in range(5):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(health_url, timeout=10) as response:
                            if response.status == 200:
                                logger.info(f"Health check passed: {health_url}")
                                return True
                except Exception as e:
                    logger.warning(f"Health check attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(5)

            return False

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def rollback_service(
        self,
        service_name: str,
        environment: str = "production"
    ) -> bool:
        """Rollback service to previous version"""
        try:
            logger.info(f"Rolling back {service_name} in {environment}")

            namespace = f"propertyyards-{environment}"

            # Find previous deployment
            previous_deployments = [
                d for d in self.deployment_history
                if d.service_name == service_name
                and d.status == DeploymentStatus.SUCCESS
            ]

            if not previous_deployments:
                logger.error(f"No previous successful deployment found for {service_name}")
                return False

            # Get previous version (before the last one)
            previous_version = previous_deployments[-2].version if len(previous_deployments) > 1 else previous_deployments[-1].version

            config = self.service_configs.get(service_name)
            if not config:
                return False

            # Rollback using kubectl
            cmd = [
                "kubectl", "rollout", "undo",
                f"deployment/{config.service_name}",
                f"-n", namespace
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                # Try manual rollback with previous version
                await self._deploy_to_k8s(config, previous_version, environment, DeploymentRecord(
                    id=f"rollback_{service_name}",
                    service_name=service_name,
                    version=previous_version,
                    status=DeploymentStatus.PENDING,
                    started_at=datetime.utcnow()
                ))

            logger.info(f"Rollback completed: {service_name}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    async def deploy_all_services(
        self,
        version: str,
        environment: str = "production"
    ) -> Dict[str, DeploymentRecord]:
        """Deploy all services at once"""
        results = {}

        # Deploy in dependency order
        deploy_order = ["api", "worker", "scheduler", "bot", "frontend"]

        for service_name in deploy_order:
            if service_name in self.service_configs:
                logger.info(f"Deploying {service_name}...")
                result = await self.deploy_service(service_name, version, environment)
                results[service_name] = result

                # Wait a bit between deployments
                await asyncio.sleep(10)

        return results

    def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentRecord]:
        """Get deployment status by ID"""
        return self.deployments.get(deployment_id)

    def get_service_status(self, service_name: str, environment: str = "production") -> Dict[str, Any]:
        """Get current status of a deployed service"""
        try:
            namespace = f"propertyyards-{environment}"

            # Get deployment status from kubectl
            cmd = [
                "kubectl", "get", "deployment", service_name,
                "-n", namespace,
                "-o", "json"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                deployment_info = json.loads(result.stdout)
                status = deployment_info.get("status", {})

                return {
                    "service_name": service_name,
                    "replicas": status.get("replicas", 0),
                    "ready_replicas": status.get("readyReplicas", 0),
                    "available_replicas": status.get("availableReplicas", 0),
                    "updated_replicas": status.get("updatedReplicas", 0),
                    "conditions": status.get("conditions", []),
                    "healthy": status.get("readyReplicas", 0) == status.get("replicas", 0)
                }

            return {"error": "Service not found", "healthy": False}

        except Exception as e:
            return {"error": str(e), "healthy": False}

    async def scale_service(
        self,
        service_name: str,
        replicas: int,
        environment: str = "production"
    ) -> bool:
        """Scale a service to specified replicas"""
        try:
            namespace = f"propertyyards-{environment}"

            cmd = [
                "kubectl", "scale",
                f"deployment/{service_name}",
                f"--replicas={replicas}",
                f"-n", namespace
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Scale failed: {e}")
            return False


# Global instance
deployment_service = DeploymentService()
