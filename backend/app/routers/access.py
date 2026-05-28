"""
Access Control Router
Endpoints for access control and permissions
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_database
from app.access import AccessControl, Permission, ResourceType, AccessLevel
from app.schemas import (
    RoleCreate, RoleResponse, RoleUpdate, ACLCreate, ACLResponse,
    PermissionCheck, PermissionCheckResponse
)
from app.auth import decode_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/access", tags=["Access Control"])


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


def require_admin(current_user: dict) -> dict:
    """Require admin role"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.post("/roles", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    authorization: str = None,
    db = Depends(get_database)
):
    """Create a custom role"""
    current_user = get_current_user(authorization)
    require_admin(current_user)
    
    access_control = AccessControl(db)
    role_id = await access_control.create_role(
        role_data.name,
        role_data.permissions,
        role_data.description
    )
    
    role = await access_control.get_role(role_data.name)
    return RoleResponse(**role)


@router.get("/roles/{role_name}", response_model=RoleResponse)
async def get_role(
    role_name: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get role by name"""
    current_user = get_current_user(authorization)
    
    access_control = AccessControl(db)
    role = await access_control.get_role(role_name)
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return RoleResponse(**role)


@router.put("/roles/{role_name}", response_model=RoleResponse)
async def update_role_permissions(
    role_name: str,
    role_update: RoleUpdate,
    authorization: str = None,
    db = Depends(get_database)
):
    """Update role permissions"""
    current_user = get_current_user(authorization)
    require_admin(current_user)
    
    access_control = AccessControl(db)
    updated = await access_control.update_role_permissions(role_name, role_update.permissions)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Role not found or cannot be updated")
    
    role = await access_control.get_role(role_name)
    return RoleResponse(**role)


@router.delete("/roles/{role_name}")
async def delete_role(
    role_name: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Delete a custom role"""
    current_user = get_current_user(authorization)
    require_admin(current_user)
    
    access_control = AccessControl(db)
    deleted = await access_control.delete_role(role_name)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Role not found or cannot be deleted")
    
    return {"message": "Role deleted successfully"}


@router.post("/users/{user_id}/roles/{role_name}")
async def assign_role_to_user(
    user_id: str,
    role_name: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Assign role to user"""
    current_user = get_current_user(authorization)
    require_admin(current_user)
    
    access_control = AccessControl(db)
    assigned = await access_control.assign_role_to_user(user_id, role_name)
    
    if not assigned:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"Role {role_name} assigned to user {user_id}"}


@router.post("/permissions/check", response_model=PermissionCheckResponse)
async def check_permission(
    permission_check: PermissionCheck,
    authorization: str = None,
    db = Depends(get_database)
):
    """Check if user has specific permission"""
    current_user = get_current_user(authorization)
    
    access_control = AccessControl(db)
    has_permission = await access_control.check_permission(
        permission_check.user_id,
        permission_check.permission
    )
    
    return PermissionCheckResponse(has_permission=has_permission)


@router.post("/acl", response_model=ACLResponse)
async def create_acl(
    acl_data: ACLCreate,
    authorization: str = None,
    db = Depends(get_database)
):
    """Create access control list entry"""
    current_user = get_current_user(authorization)
    require_admin(current_user)
    
    access_control = AccessControl(db)
    acl_id = await access_control.create_acl(
        acl_data.resource_type,
        acl_data.resource_id,
        acl_data.user_id,
        acl_data.access_level
    )
    
    acl = await access_control.acl_collection.find_one({"_id": acl_id})
    acl["id"] = str(acl["_id"])
    del acl["_id"]
    
    return ACLResponse(**acl)


@router.get("/acl/{resource_type}/{resource_id}")
async def get_resource_acl(
    resource_type: ResourceType,
    resource_id: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get all ACL entries for a resource"""
    current_user = get_current_user(authorization)
    
    access_control = AccessControl(db)
    acls = await access_control.get_resource_acl(resource_type, resource_id)
    
    return acls


@router.post("/acl/grant")
async def grant_resource_access(
    resource_type: ResourceType,
    resource_id: str,
    user_id: str,
    access_level: AccessLevel,
    authorization: str = None,
    db = Depends(get_database)
):
    """Grant or update access to a resource"""
    current_user = get_current_user(authorization)
    require_admin(current_user)
    
    access_control = AccessControl(db)
    granted = await access_control.grant_resource_access(
        resource_type,
        resource_id,
        user_id,
        access_level
    )
    
    return {"message": "Access granted successfully"}


@router.delete("/acl/{resource_type}/{resource_id}/{user_id}")
async def revoke_resource_access(
    resource_type: ResourceType,
    resource_id: str,
    user_id: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Revoke access to a resource"""
    current_user = get_current_user(authorization)
    require_admin(current_user)
    
    access_control = AccessControl(db)
    revoked = await access_control.revoke_resource_access(
        resource_type,
        resource_id,
        user_id
    )
    
    if not revoked:
        raise HTTPException(status_code=404, detail="ACL entry not found")
    
    return {"message": "Access revoked successfully"}


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get all permissions for a user"""
    current_user = get_current_user(authorization)
    
    access_control = AccessControl(db)
    permissions = await access_control.get_user_permissions(user_id)
    
    return {"permissions": list(permissions)}


@router.get("/users/{user_id}/resources/{resource_type}")
async def get_user_resources(
    user_id: str,
    resource_type: ResourceType,
    access_level: AccessLevel = AccessLevel.READ,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get all resources of a type that user has access to"""
    current_user = get_current_user(authorization)
    
    access_control = AccessControl(db)
    resources = await access_control.get_user_resources(user_id, resource_type, access_level)
    
    return {"resource_ids": resources}


@router.post("/initialize")
async def initialize_default_roles(
    authorization: str = None,
    db = Depends(get_database)
):
    """Initialize default roles in database"""
    current_user = get_current_user(authorization)
    require_admin(current_user)
    
    access_control = AccessControl(db)
    await access_control.initialize_default_roles()
    
    return {"message": "Default roles initialized successfully"}
