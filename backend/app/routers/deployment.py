"""
Deployment Router
API endpoints for automated deployment management
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/deployment", tags=["deployment"])


class DeployServiceRequest(BaseModel):
    """Deploy service request"""
    service_name: str
    version: str
    environment: str = "production"


class ScaleServiceRequest(BaseModel):
    """Scale service request"""
    service_name: str
    replicas: int
    environment: str = "production"


@router.post("/deploy")
async def deploy_service(
    request: DeployServiceRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    database=Depends(get_db)
):
    """Deploy a service (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.deployment_service import deployment_service

        # Run deployment in background
        background_tasks.add_task(
            deployment_service.deploy_service,
            service_name=request.service_name,
            version=request.version,
            environment=request.environment
        )

        return {
            "message": "Deployment started",
            "service_name": request.service_name,
            "version": request.version,
            "environment": request.environment,
            "status": "pending"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy-all")
async def deploy_all_services(
    version: str,
    environment: str = "production",
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user)
):
    """Deploy all services at once"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.deployment_service import deployment_service

        background_tasks.add_task(
            deployment_service.deploy_all_services,
            version=version,
            environment=environment
        )

        return {
            "message": "All services deployment started",
            "version": version,
            "environment": environment,
            "services": list(deployment_service.service_configs.keys())
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rollback")
async def rollback_service(
    service_name: str,
    environment: str = "production",
    current_user: dict = Depends(get_current_user)
):
    """Rollback a service to previous version"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.deployment_service import deployment_service

        success = await deployment_service.rollback_service(service_name, environment)

        if success:
            return {
                "message": "Rollback completed",
                "service_name": service_name,
                "environment": environment
            }
        else:
            raise HTTPException(status_code=500, detail="Rollback failed")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{service_name}")
async def get_service_status(
    service_name: str,
    environment: str = "production",
    current_user: dict = Depends(get_current_user)
):
    """Get deployment status of a service"""
    if current_user.get("role") not in ["admin", "devops"]:
        raise HTTPException(status_code=403, detail="Admin/DevOps access required")

    try:
        from app.deployment_service import deployment_service

        status = deployment_service.get_service_status(service_name, environment)
        return status

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services")
async def list_services(
    current_user: dict = Depends(get_current_user)
):
    """List all configurable services"""
    if current_user.get("role") not in ["admin", "devops"]:
        raise HTTPException(status_code=403, detail="Admin/DevOps access required")

    try:
        from app.deployment_service import deployment_service

        services = []
        for name, config in deployment_service.service_configs.items():
            services.append({
                "name": name,
                "type": config.service_type.value,
                "image": config.image_name,
                "port": config.port,
                "replicas": config.replicas,
                "resources": {
                    "cpu": config.cpu_limit,
                    "memory": config.memory_limit
                }
            })

        return {"services": services}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scale")
async def scale_service(
    request: ScaleServiceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Scale a service"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.deployment_service import deployment_service

        success = await deployment_service.scale_service(
            request.service_name,
            request.replicas,
            request.environment
        )

        if success:
            return {
                "message": "Service scaled",
                "service_name": request.service_name,
                "replicas": request.replicas
            }
        else:
            raise HTTPException(status_code=500, detail="Scale failed")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_deployment_history(
    service_name: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get deployment history"""
    if current_user.get("role") not in ["admin", "devops"]:
        raise HTTPException(status_code=403, detail="Admin/DevOps access required")

    try:
        from app.deployment_service import deployment_service

        history = deployment_service.deployment_history

        if service_name:
            history = [h for h in history if h.service_name == service_name]

        history = sorted(history, key=lambda x: x.started_at, reverse=True)[:limit]

        return {
            "deployments": [
                {
                    "id": h.id,
                    "service_name": h.service_name,
                    "version": h.version,
                    "status": h.status.value,
                    "started_at": h.started_at.isoformat() if h.started_at else None,
                    "completed_at": h.completed_at.isoformat() if h.completed_at else None,
                    "error_message": h.error_message
                }
                for h in history
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def deployment_health():
    """Check deployment service health"""
    try:
        from app.deployment_service import deployment_service

        return {
            "status": "healthy" if deployment_service.enabled else "disabled",
            "services_configured": len(deployment_service.service_configs),
            "services": list(deployment_service.service_configs.keys())
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
