"""
Access Control Module
Manages permissions, roles, and access control lists
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """System permissions"""
    # User permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # Property permissions
    PROPERTY_READ = "property:read"
    PROPERTY_WRITE = "property:write"
    PROPERTY_DELETE = "property:delete"
    PROPERTY_APPROVE = "property:approve"
    
    # Inquiry permissions
    INQUIRY_READ = "inquiry:read"
    INQUIRY_WRITE = "inquiry:write"
    INQUIRY_DELETE = "inquiry:delete"
    INQUIRY_RESPOND = "inquiry:respond"
    
    # Admin permissions
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_DELETE = "admin:delete"
    ADMIN_MANAGE_USERS = "admin:manage_users"
    ADMIN_MANAGE_ROLES = "admin:manage_roles"
    ADMIN_VIEW_ANALYTICS = "admin:view_analytics"
    
    # CRM permissions
    CRM_READ = "crm:read"
    CRM_WRITE = "crm:write"
    CRM_DELETE = "crm:delete"
    CRM_MANAGE_LEADS = "crm:manage_leads"
    
    # Referral permissions
    REFERRAL_READ = "referral:read"
    REFERRAL_WRITE = "referral:write"
    REFERRAL_MANAGE = "referral:manage"
    
    # System permissions
    SYSTEM_CONFIG = "system:config"
    SYSTEM_LOGS = "system:logs"
    SYSTEM_HEALTH = "system:health"


class ResourceType(str, Enum):
    """Types of resources for access control"""
    USER = "user"
    PROPERTY = "property"
    INQUIRY = "inquiry"
    LEAD = "lead"
    REWARD = "reward"
    ROLE = "role"
    PERMISSION = "permission"
    SETTINGS = "settings"


class AccessLevel(str, Enum):
    """Access levels"""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class Role:
    """Role definitions with permissions"""
    
    # Default role permissions
    ROLE_PERMISSIONS = {
        "admin": {
            "permissions": [
                Permission.USER_READ, Permission.USER_WRITE, Permission.USER_DELETE,
                Permission.PROPERTY_READ, Permission.PROPERTY_WRITE, Permission.PROPERTY_DELETE, Permission.PROPERTY_APPROVE,
                Permission.INQUIRY_READ, Permission.INQUIRY_WRITE, Permission.INQUIRY_DELETE, Permission.INQUIRY_RESPOND,
                Permission.ADMIN_READ, Permission.ADMIN_WRITE, Permission.ADMIN_DELETE,
                Permission.ADMIN_MANAGE_USERS, Permission.ADMIN_MANAGE_ROLES, Permission.ADMIN_VIEW_ANALYTICS,
                Permission.CRM_READ, Permission.CRM_WRITE, Permission.CRM_DELETE, Permission.CRM_MANAGE_LEADS,
                Permission.REFERRAL_READ, Permission.REFERRAL_WRITE, Permission.REFERRAL_MANAGE,
                Permission.SYSTEM_CONFIG, Permission.SYSTEM_LOGS, Permission.SYSTEM_HEALTH
            ],
            "description": "Full system access"
        },
        "seller": {
            "permissions": [
                Permission.USER_READ, Permission.USER_WRITE,
                Permission.PROPERTY_READ, Permission.PROPERTY_WRITE, Permission.PROPERTY_DELETE,
                Permission.INQUIRY_READ, Permission.INQUIRY_RESPOND,
                Permission.REFERRAL_READ, Permission.REFERRAL_WRITE
            ],
            "description": "Property seller with listing management"
        },
        "buyer": {
            "permissions": [
                Permission.USER_READ, Permission.USER_WRITE,
                Permission.PROPERTY_READ,
                Permission.INQUIRY_READ, Permission.INQUIRY_WRITE,
                Permission.REFERRAL_READ, Permission.REFERRAL_WRITE
            ],
            "description": "Property buyer with viewing and inquiry capabilities"
        },
        "agent": {
            "permissions": [
                Permission.USER_READ, Permission.USER_WRITE,
                Permission.PROPERTY_READ, Permission.PROPERTY_WRITE, Permission.PROPERTY_DELETE,
                Permission.INQUIRY_READ, Permission.INQUIRY_WRITE, Permission.INQUIRY_RESPOND,
                Permission.CRM_READ, Permission.CRM_WRITE, Permission.CRM_MANAGE_LEADS,
                Permission.REFERRAL_READ, Permission.REFERRAL_WRITE
            ],
            "description": "Real estate agent with CRM capabilities"
        }
    }


class AccessControl:
    """Access control management"""
    
    def __init__(self, database):
        self.db = database
        self.roles_collection = database.roles
        self.permissions_collection = database.permissions
        self.acl_collection = database.access_control_lists
    
    async def initialize_default_roles(self):
        """Initialize default roles in database"""
        for role_name, role_data in Role.ROLE_PERMISSIONS.items():
            existing = await self.roles_collection.find_one({"name": role_name})
            if not existing:
                role = {
                    "name": role_name,
                    "permissions": [p.value for p in role_data["permissions"]],
                    "description": role_data["description"],
                    "is_system": True,
                    "created_at": datetime.utcnow()
                }
                await self.roles_collection.insert_one(role)
                logger.info(f"Default role created: {role_name}")
    
    async def create_role(
        self,
        name: str,
        permissions: List[str],
        description: str = ""
    ) -> str:
        """Create a custom role"""
        role = {
            "name": name,
            "permissions": permissions,
            "description": description,
            "is_system": False,
            "created_at": datetime.utcnow()
        }
        
        result = await self.roles_collection.insert_one(role)
        logger.info(f"Custom role created: {name}")
        return str(result.inserted_id)
    
    async def get_role(self, role_name: str) -> Optional[Dict[str, Any]]:
        """Get role by name"""
        role = await self.roles_collection.find_one({"name": role_name})
        if role:
            role["id"] = str(role["_id"])
            del role["_id"]
        return role
    
    async def update_role_permissions(
        self,
        role_name: str,
        permissions: List[str]
    ) -> bool:
        """Update role permissions"""
        result = await self.roles_collection.update_one(
            {"name": role_name, "is_system": False},
            {"$set": {"permissions": permissions, "updated_at": datetime.utcnow()}}
        )
        logger.info(f"Role permissions updated: {role_name}")
        return result.modified_count > 0
    
    async def delete_role(self, role_name: str) -> bool:
        """Delete a custom role"""
        result = await self.roles_collection.delete_one({
            "name": role_name,
            "is_system": False
        })
        logger.info(f"Role deleted: {role_name}")
        return result.deleted_count > 0
    
    async def assign_role_to_user(self, user_id: str, role_name: str) -> bool:
        """Assign role to user"""
        result = await self.db.users.update_one(
            {"_id": user_id},
            {"$set": {"role": role_name, "updated_at": datetime.utcnow()}}
        )
        logger.info(f"Role assigned to user {user_id}: {role_name}")
        return result.modified_count > 0
    
    async def check_permission(
        self,
        user_id: str,
        required_permission: Permission
    ) -> bool:
        """Check if user has required permission"""
        user = await self.db.users.find_one({"_id": user_id})
        if not user:
            return False
        
        role = await self.get_role(user["role"])
        if not role:
            return False
        
        return required_permission.value in role["permissions"]
    
    async def check_any_permission(
        self,
        user_id: str,
        required_permissions: List[Permission]
    ) -> bool:
        """Check if user has any of the required permissions"""
        for permission in required_permissions:
            if await self.check_permission(user_id, permission):
                return True
        return False
    
    async def check_all_permissions(
        self,
        user_id: str,
        required_permissions: List[Permission]
    ) -> bool:
        """Check if user has all required permissions"""
        for permission in required_permissions:
            if not await self.check_permission(user_id, permission):
                return False
        return True
    
    async def create_acl(
        self,
        resource_type: ResourceType,
        resource_id: str,
        user_id: str,
        access_level: AccessLevel
    ) -> str:
        """Create access control list entry"""
        acl = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "access_level": access_level,
            "created_at": datetime.utcnow()
        }
        
        result = await self.acl_collection.insert_one(acl)
        logger.info(f"ACL created: {resource_type}:{resource_id} for user {user_id}")
        return str(result.inserted_id)
    
    async def check_resource_access(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        required_access: AccessLevel = AccessLevel.READ
    ) -> bool:
        """Check if user has access to a specific resource"""
        # First check if user is admin
        if await self.check_permission(user_id, Permission.ADMIN_READ):
            return True
        
        # Check ACL
        acl = await self.acl_collection.find_one({
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id
        })
        
        if not acl:
            return False
        
        # Check access level hierarchy
        access_hierarchy = {
            AccessLevel.NONE: 0,
            AccessLevel.READ: 1,
            AccessLevel.WRITE: 2,
            AccessLevel.ADMIN: 3
        }
        
        return access_hierarchy[acl["access_level"]] >= access_hierarchy[required_access]
    
    async def grant_resource_access(
        self,
        resource_type: ResourceType,
        resource_id: str,
        user_id: str,
        access_level: AccessLevel
    ) -> bool:
        """Grant or update access to a resource"""
        result = await self.acl_collection.update_one(
            {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "user_id": user_id
            },
            {
                "$set": {
                    "access_level": access_level,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        logger.info(f"Access granted: {resource_type}:{resource_id} to user {user_id}")
        return result.modified_count > 0 or result.upserted_id is not None
    
    async def revoke_resource_access(
        self,
        resource_type: ResourceType,
        resource_id: str,
        user_id: str
    ) -> bool:
        """Revoke access to a resource"""
        result = await self.acl_collection.delete_one({
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id
        })
        logger.info(f"Access revoked: {resource_type}:{resource_id} from user {user_id}")
        return result.deleted_count > 0
    
    async def get_user_permissions(self, user_id: str) -> Set[str]:
        """Get all permissions for a user"""
        user = await self.db.users.find_one({"_id": user_id})
        if not user:
            return set()
        
        role = await self.get_role(user["role"])
        if not role:
            return set()
        
        return set(role["permissions"])
    
    async def get_resource_acl(
        self,
        resource_type: ResourceType,
        resource_id: str
    ) -> List[Dict[str, Any]]:
        """Get all ACL entries for a resource"""
        cursor = self.acl_collection.find({
            "resource_type": resource_type,
            "resource_id": resource_id
        })
        acls = await cursor.to_list(length=None)
        
        for acl in acls:
            acl["id"] = str(acl["_id"])
            del acl["_id"]
        
        return acls
    
    async def get_user_resources(
        self,
        user_id: str,
        resource_type: ResourceType,
        access_level: AccessLevel = AccessLevel.READ
    ) -> List[str]:
        """Get all resources of a type that user has access to"""
        cursor = self.acl_collection.find({
            "user_id": user_id,
            "resource_type": resource_type
        })
        acls = await cursor.to_list(length=None)
        
        access_hierarchy = {
            AccessLevel.NONE: 0,
            AccessLevel.READ: 1,
            AccessLevel.WRITE: 2,
            AccessLevel.ADMIN: 3
        }
        
        resource_ids = []
        for acl in acls:
            if access_hierarchy[acl["access_level"]] >= access_hierarchy[required_access):
                resource_ids.append(acl["resource_id"])
        
        return resource_ids


class AuditLog:
    """Access control audit logging"""
    
    def __init__(self, database):
        self.db = database
        self.collection = database.access_audit_logs
    
    async def log_access_attempt(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log an access attempt"""
        log = {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "success": success,
            "details": details or {},
            "ip_address": details.get("ip_address") if details else None,
            "user_agent": details.get("user_agent") if details else None,
            "created_at": datetime.utcnow()
        }
        
        result = await self.collection.insert_one(log)
        logger.info(f"Access attempt logged: {action} by user {user_id}")
        return str(result.inserted_id)
    
    async def get_user_audit_logs(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get audit logs for a user"""
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit)
        logs = await cursor.to_list(length=limit)
        
        for log in logs:
            log["id"] = str(log["_id"])
            del log["_id"]
        
        return logs
    
    async def get_resource_audit_logs(
        self,
        resource_type: str,
        resource_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get audit logs for a resource"""
        cursor = self.collection.find({
            "resource_type": resource_type,
            "resource_id": resource_id
        }).sort("created_at", -1).skip(skip).limit(limit)
        logs = await cursor.to_list(length=limit)
        
        for log in logs:
            log["id"] = str(log["_id"])
            del log["_id"]
        
        return logs
