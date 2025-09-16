"""
Free Multi-Tenant Architecture for Enterprise Client Isolation
Implements tenant separation, resource quotas, and access control
"""

import json
import os
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import logging
from pathlib import Path
import sqlite3
from contextlib import contextmanager


class TenantStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    EXPIRED = "expired"


class ResourceType(Enum):
    CAMPAIGNS_PER_MONTH = "campaigns_per_month"
    ASSETS_PER_CAMPAIGN = "assets_per_campaign"
    STORAGE_MB = "storage_mb"
    API_CALLS_PER_DAY = "api_calls_per_day"
    CONCURRENT_CAMPAIGNS = "concurrent_campaigns"


class Permission(Enum):
    # Campaign permissions
    CREATE_CAMPAIGN = "create_campaign"
    VIEW_CAMPAIGN = "view_campaign"
    DELETE_CAMPAIGN = "delete_campaign"
    
    # Asset permissions
    GENERATE_ASSETS = "generate_assets"
    DOWNLOAD_ASSETS = "download_assets"
    
    # System permissions
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_USERS = "manage_users"
    ADMIN_ACCESS = "admin_access"
    
    # Advanced features
    BATCH_PROCESSING = "batch_processing"
    AB_TESTING = "ab_testing"
    WEBHOOK_ACCESS = "webhook_access"
    API_ACCESS = "api_access"


@dataclass
class ResourceQuota:
    """Resource quota definition for a tenant"""
    resource_type: ResourceType
    limit: int
    current_usage: int = 0
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    
    def is_exceeded(self) -> bool:
        """Check if quota is exceeded"""
        return self.current_usage >= self.limit
    
    def remaining(self) -> int:
        """Get remaining quota"""
        return max(0, self.limit - self.current_usage)
    
    def usage_percentage(self) -> float:
        """Get usage as percentage"""
        if self.limit == 0:
            return 100.0
        return (self.current_usage / self.limit) * 100


@dataclass
class TenantUser:
    """User within a tenant"""
    user_id: str
    email: str
    name: str
    permissions: Set[Permission]
    created_at: str
    last_login: Optional[str] = None
    is_active: bool = True
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions or Permission.ADMIN_ACCESS in self.permissions


@dataclass
class Tenant:
    """Multi-tenant organization definition"""
    tenant_id: str
    name: str
    plan: str  # free, starter, professional, enterprise
    status: TenantStatus
    created_at: str
    quotas: Dict[ResourceType, ResourceQuota]
    users: Dict[str, TenantUser]
    settings: Dict[str, Any]
    
    def get_quota(self, resource_type: ResourceType) -> Optional[ResourceQuota]:
        """Get quota for specific resource type"""
        return self.quotas.get(resource_type)
    
    def can_consume_resource(self, resource_type: ResourceType, amount: int = 1) -> bool:
        """Check if tenant can consume resource"""
        if self.status != TenantStatus.ACTIVE:
            return False
        
        quota = self.get_quota(resource_type)
        if not quota:
            return True  # No quota means unlimited
        
        return quota.current_usage + amount <= quota.limit
    
    def consume_resource(self, resource_type: ResourceType, amount: int = 1) -> bool:
        """Consume resource if available"""
        if not self.can_consume_resource(resource_type, amount):
            return False
        
        if resource_type in self.quotas:
            self.quotas[resource_type].current_usage += amount
        
        return True
    
    def get_user(self, user_id: str) -> Optional[TenantUser]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def add_user(self, user: TenantUser) -> bool:
        """Add user to tenant"""
        if user.user_id in self.users:
            return False
        self.users[user.user_id] = user
        return True


class TenantManager:
    """Manages multi-tenant operations and isolation"""
    
    def __init__(self, storage_path: str = "tenants.db"):
        self.storage_path = storage_path
        self.tenants: Dict[str, Tenant] = {}
        self.api_keys: Dict[str, str] = {}  # api_key -> tenant_id
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        
        # Initialize database
        self._init_database()
        self._load_tenants()
        
        # Predefined plans
        self.plans = {
            "free": {
                "name": "Free Plan",
                "quotas": {
                    ResourceType.CAMPAIGNS_PER_MONTH: 5,
                    ResourceType.ASSETS_PER_CAMPAIGN: 6,
                    ResourceType.STORAGE_MB: 100,
                    ResourceType.API_CALLS_PER_DAY: 50,
                    ResourceType.CONCURRENT_CAMPAIGNS: 1
                },
                "permissions": {
                    Permission.CREATE_CAMPAIGN,
                    Permission.VIEW_CAMPAIGN,
                    Permission.GENERATE_ASSETS,
                    Permission.DOWNLOAD_ASSETS,
                    Permission.VIEW_ANALYTICS
                }
            },
            "starter": {
                "name": "Starter Plan",
                "quotas": {
                    ResourceType.CAMPAIGNS_PER_MONTH: 25,
                    ResourceType.ASSETS_PER_CAMPAIGN: 12,
                    ResourceType.STORAGE_MB: 500,
                    ResourceType.API_CALLS_PER_DAY: 250,
                    ResourceType.CONCURRENT_CAMPAIGNS: 3
                },
                "permissions": {
                    Permission.CREATE_CAMPAIGN,
                    Permission.VIEW_CAMPAIGN,
                    Permission.DELETE_CAMPAIGN,
                    Permission.GENERATE_ASSETS,
                    Permission.DOWNLOAD_ASSETS,
                    Permission.VIEW_ANALYTICS,
                    Permission.BATCH_PROCESSING,
                    Permission.AB_TESTING
                }
            },
            "professional": {
                "name": "Professional Plan",
                "quotas": {
                    ResourceType.CAMPAIGNS_PER_MONTH: 100,
                    ResourceType.ASSETS_PER_CAMPAIGN: 25,
                    ResourceType.STORAGE_MB: 2000,
                    ResourceType.API_CALLS_PER_DAY: 1000,
                    ResourceType.CONCURRENT_CAMPAIGNS: 10
                },
                "permissions": {
                    Permission.CREATE_CAMPAIGN,
                    Permission.VIEW_CAMPAIGN,
                    Permission.DELETE_CAMPAIGN,
                    Permission.GENERATE_ASSETS,
                    Permission.DOWNLOAD_ASSETS,
                    Permission.VIEW_ANALYTICS,
                    Permission.BATCH_PROCESSING,
                    Permission.AB_TESTING,
                    Permission.WEBHOOK_ACCESS,
                    Permission.API_ACCESS
                }
            },
            "enterprise": {
                "name": "Enterprise Plan",
                "quotas": {
                    ResourceType.CAMPAIGNS_PER_MONTH: -1,  # Unlimited
                    ResourceType.ASSETS_PER_CAMPAIGN: -1,
                    ResourceType.STORAGE_MB: -1,
                    ResourceType.API_CALLS_PER_DAY: -1,
                    ResourceType.CONCURRENT_CAMPAIGNS: -1
                },
                "permissions": set(Permission)  # All permissions
            }
        }
    
    def _init_database(self):
        """Initialize SQLite database for tenant storage"""
        with sqlite3.connect(self.storage_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    tenant_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    plan TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    settings TEXT,
                    quotas TEXT,
                    users TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    api_key TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used TEXT,
                    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS resource_usage (
                    tenant_id TEXT,
                    resource_type TEXT,
                    amount INTEGER,
                    timestamp TEXT,
                    campaign_id TEXT,
                    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
                )
            """)
    
    def _load_tenants(self):
        """Load tenants from database"""
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.execute("SELECT * FROM tenants")
                for row in cursor.fetchall():
                    tenant_id, name, plan, status, created_at, settings_json, quotas_json, users_json = row
                    
                    # Parse JSON data
                    settings = json.loads(settings_json) if settings_json else {}
                    quotas_data = json.loads(quotas_json) if quotas_json else {}
                    users_data = json.loads(users_json) if users_json else {}
                    
                    # Rebuild tenant object
                    quotas = {}
                    for rt_str, quota_data in quotas_data.items():
                        resource_type = ResourceType(rt_str)
                        quotas[resource_type] = ResourceQuota(
                            resource_type=resource_type,
                            limit=quota_data["limit"],
                            current_usage=quota_data["current_usage"],
                            period_start=quota_data.get("period_start"),
                            period_end=quota_data.get("period_end")
                        )
                    
                    # Rebuild users
                    users = {}
                    for user_id, user_data in users_data.items():
                        permissions = set(Permission(p) for p in user_data["permissions"])
                        users[user_id] = TenantUser(
                            user_id=user_id,
                            email=user_data["email"],
                            name=user_data["name"],
                            permissions=permissions,
                            created_at=user_data["created_at"],
                            last_login=user_data.get("last_login"),
                            is_active=user_data.get("is_active", True)
                        )
                    
                    tenant = Tenant(
                        tenant_id=tenant_id,
                        name=name,
                        plan=plan,
                        status=TenantStatus(status),
                        created_at=created_at,
                        quotas=quotas,
                        users=users,
                        settings=settings
                    )
                    
                    self.tenants[tenant_id] = tenant
                
                # Load API keys
                cursor = conn.execute("SELECT api_key, tenant_id FROM api_keys")
                for api_key, tenant_id in cursor.fetchall():
                    self.api_keys[api_key] = tenant_id
                    
        except Exception as e:
            self.logger.error(f"Error loading tenants: {e}")
    
    def create_tenant(
        self,
        name: str,
        plan: str = "free",
        admin_email: str = None,
        admin_name: str = None
    ) -> str:
        """Create a new tenant"""
        if plan not in self.plans:
            raise ValueError(f"Invalid plan: {plan}")
        
        tenant_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        # Create quotas based on plan
        plan_config = self.plans[plan]
        quotas = {}
        
        for resource_type, limit in plan_config["quotas"].items():
            if limit == -1:  # Unlimited
                continue
            
            quotas[resource_type] = ResourceQuota(
                resource_type=resource_type,
                limit=limit,
                current_usage=0,
                period_start=created_at,
                period_end=(datetime.now() + timedelta(days=30)).isoformat()
            )
        
        # Create admin user if provided
        users = {}
        if admin_email and admin_name:
            admin_user = TenantUser(
                user_id=str(uuid.uuid4()),
                email=admin_email,
                name=admin_name,
                permissions=plan_config["permissions"].copy(),
                created_at=created_at
            )
            users[admin_user.user_id] = admin_user
        
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            plan=plan,
            status=TenantStatus.ACTIVE if plan != "free" else TenantStatus.TRIAL,
            created_at=created_at,
            quotas=quotas,
            users=users,
            settings={}
        )
        
        with self._lock:
            self.tenants[tenant_id] = tenant
            self._save_tenant(tenant)
        
        self.logger.info(f"Created tenant {name} ({tenant_id}) with plan {plan}")
        return tenant_id
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        return self.tenants.get(tenant_id)
    
    def get_tenant_by_api_key(self, api_key: str) -> Optional[Tenant]:
        """Get tenant by API key"""
        tenant_id = self.api_keys.get(api_key)
        if tenant_id:
            return self.get_tenant(tenant_id)
        return None
    
    def create_api_key(self, tenant_id: str) -> str:
        """Create API key for tenant"""
        if tenant_id not in self.tenants:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        # Generate secure API key
        api_key = f"ca_{hashlib.sha256(f'{tenant_id}{datetime.now().isoformat()}{uuid.uuid4()}'.encode()).hexdigest()[:32]}"
        
        with self._lock:
            self.api_keys[api_key] = tenant_id
            
            # Save to database
            with sqlite3.connect(self.storage_path) as conn:
                conn.execute(
                    "INSERT INTO api_keys (api_key, tenant_id, created_at) VALUES (?, ?, ?)",
                    (api_key, tenant_id, datetime.now().isoformat())
                )
        
        return api_key
    
    def validate_access(
        self,
        tenant_id: str,
        user_id: str,
        permission: Permission,
        resource_type: ResourceType = None,
        resource_amount: int = 1
    ) -> Dict[str, Any]:
        """Validate if user can perform action"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return {"allowed": False, "reason": "Tenant not found"}
        
        if tenant.status != TenantStatus.ACTIVE:
            return {"allowed": False, "reason": f"Tenant status: {tenant.status.value}"}
        
        user = tenant.get_user(user_id)
        if not user:
            return {"allowed": False, "reason": "User not found"}
        
        if not user.is_active:
            return {"allowed": False, "reason": "User is inactive"}
        
        if not user.has_permission(permission):
            return {"allowed": False, "reason": f"Missing permission: {permission.value}"}
        
        # Check resource quota if specified
        if resource_type:
            if not tenant.can_consume_resource(resource_type, resource_amount):
                quota = tenant.get_quota(resource_type)
                if quota:
                    return {
                        "allowed": False,
                        "reason": f"Resource quota exceeded: {quota.current_usage}/{quota.limit}"
                    }
        
        return {"allowed": True, "reason": "Access granted"}
    
    def consume_resource(
        self,
        tenant_id: str,
        resource_type: ResourceType,
        amount: int = 1,
        campaign_id: str = None
    ) -> bool:
        """Consume tenant resource and log usage"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False
        
        with self._lock:
            success = tenant.consume_resource(resource_type, amount)
            if success:
                self._save_tenant(tenant)
                
                # Log resource usage
                with sqlite3.connect(self.storage_path) as conn:
                    conn.execute(
                        "INSERT INTO resource_usage (tenant_id, resource_type, amount, timestamp, campaign_id) VALUES (?, ?, ?, ?, ?)",
                        (tenant_id, resource_type.value, amount, datetime.now().isoformat(), campaign_id)
                    )
        
        return success
    
    def get_tenant_usage_report(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get usage report for tenant"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return {"error": "Tenant not found"}
        
        # Get usage from database
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.storage_path) as conn:
            cursor = conn.execute("""
                SELECT resource_type, SUM(amount) as total_usage, COUNT(*) as usage_count
                FROM resource_usage 
                WHERE tenant_id = ? AND timestamp >= ?
                GROUP BY resource_type
            """, (tenant_id, since_date))
            
            usage_data = {}
            for resource_type, total_usage, usage_count in cursor.fetchall():
                usage_data[resource_type] = {
                    "total_usage": total_usage,
                    "usage_count": usage_count
                }
        
        # Build report
        report = {
            "tenant_id": tenant_id,
            "tenant_name": tenant.name,
            "plan": tenant.plan,
            "status": tenant.status.value,
            "report_period_days": days,
            "quotas": {},
            "usage": usage_data,
            "recommendations": []
        }
        
        # Add quota information
        for resource_type, quota in tenant.quotas.items():
            report["quotas"][resource_type.value] = {
                "limit": quota.limit,
                "current_usage": quota.current_usage,
                "remaining": quota.remaining(),
                "usage_percentage": quota.usage_percentage(),
                "is_exceeded": quota.is_exceeded()
            }
            
            # Generate recommendations
            usage_pct = quota.usage_percentage()
            if usage_pct > 90:
                report["recommendations"].append(f"Consider upgrading plan - {resource_type.value} usage at {usage_pct:.1f}%")
            elif usage_pct > 75:
                report["recommendations"].append(f"Monitor {resource_type.value} usage - at {usage_pct:.1f}% of quota")
        
        return report
    
    def _save_tenant(self, tenant: Tenant):
        """Save tenant to database"""
        # Serialize complex objects to JSON
        quotas_json = json.dumps({
            rt.value: {
                "limit": quota.limit,
                "current_usage": quota.current_usage,
                "period_start": quota.period_start,
                "period_end": quota.period_end
            }
            for rt, quota in tenant.quotas.items()
        })
        
        users_json = json.dumps({
            user_id: {
                "email": user.email,
                "name": user.name,
                "permissions": [p.value for p in user.permissions],
                "created_at": user.created_at,
                "last_login": user.last_login,
                "is_active": user.is_active
            }
            for user_id, user in tenant.users.items()
        })
        
        settings_json = json.dumps(tenant.settings)
        
        with sqlite3.connect(self.storage_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tenants 
                (tenant_id, name, plan, status, created_at, settings, quotas, users)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tenant.tenant_id, tenant.name, tenant.plan, tenant.status.value,
                tenant.created_at, settings_json, quotas_json, users_json
            ))
    
    def list_tenants(self, status: TenantStatus = None) -> List[Dict[str, Any]]:
        """List all tenants with summary information"""
        tenants_list = []
        
        for tenant in self.tenants.values():
            if status and tenant.status != status:
                continue
            
            # Calculate overall quota usage
            total_quotas = len(tenant.quotas)
            exceeded_quotas = sum(1 for quota in tenant.quotas.values() if quota.is_exceeded())
            avg_usage = sum(quota.usage_percentage() for quota in tenant.quotas.values()) / max(1, total_quotas)
            
            tenants_list.append({
                "tenant_id": tenant.tenant_id,
                "name": tenant.name,
                "plan": tenant.plan,
                "status": tenant.status.value,
                "created_at": tenant.created_at,
                "users_count": len(tenant.users),
                "quotas_count": total_quotas,
                "exceeded_quotas": exceeded_quotas,
                "avg_quota_usage": avg_usage
            })
        
        return sorted(tenants_list, key=lambda x: x["created_at"], reverse=True)
    
    def upgrade_tenant_plan(self, tenant_id: str, new_plan: str) -> bool:
        """Upgrade tenant to new plan"""
        if new_plan not in self.plans:
            return False
        
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False
        
        with self._lock:
            # Update plan
            tenant.plan = new_plan
            
            # Update quotas
            plan_config = self.plans[new_plan]
            for resource_type, new_limit in plan_config["quotas"].items():
                if new_limit == -1:  # Unlimited
                    if resource_type in tenant.quotas:
                        del tenant.quotas[resource_type]
                else:
                    if resource_type in tenant.quotas:
                        tenant.quotas[resource_type].limit = new_limit
                    else:
                        tenant.quotas[resource_type] = ResourceQuota(
                            resource_type=resource_type,
                            limit=new_limit,
                            current_usage=0,
                            period_start=datetime.now().isoformat(),
                            period_end=(datetime.now() + timedelta(days=30)).isoformat()
                        )
            
            # Update user permissions
            new_permissions = plan_config["permissions"]
            for user in tenant.users.values():
                user.permissions = new_permissions.copy()
            
            # Update status
            if tenant.status == TenantStatus.TRIAL:
                tenant.status = TenantStatus.ACTIVE
            
            self._save_tenant(tenant)
        
        self.logger.info(f"Upgraded tenant {tenant.name} to {new_plan}")
        return True


# Context manager for tenant-specific operations
@contextmanager
def tenant_context(tenant_manager: TenantManager, tenant_id: str, user_id: str):
    """Context manager for tenant-isolated operations"""
    tenant = tenant_manager.get_tenant(tenant_id)
    if not tenant:
        raise ValueError(f"Tenant {tenant_id} not found")
    
    user = tenant.get_user(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found in tenant {tenant_id}")
    
    # Create tenant-specific directories
    tenant_dirs = {
        "output": f"output/{tenant_id}",
        "assets": f"assets/{tenant_id}",
        "cache": f"generated_cache/{tenant_id}",
        "batch": f"batch_results/{tenant_id}"
    }
    
    for dir_path in tenant_dirs.values():
        os.makedirs(dir_path, exist_ok=True)
    
    try:
        yield {
            "tenant": tenant,
            "user": user,
            "directories": tenant_dirs
        }
    except Exception as e:
        logging.error(f"Error in tenant context {tenant_id}: {e}")
        raise


# Middleware for API request validation
class TenantMiddleware:
    """Middleware for tenant validation in API requests"""
    
    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager
    
    def validate_request(self, api_key: str, user_id: str, permission: Permission) -> Dict[str, Any]:
        """Validate API request with tenant isolation"""
        if not api_key:
            return {"valid": False, "error": "API key required"}
        
        tenant = self.tenant_manager.get_tenant_by_api_key(api_key)
        if not tenant:
            return {"valid": False, "error": "Invalid API key"}
        
        validation = self.tenant_manager.validate_access(
            tenant.tenant_id, user_id, permission
        )
        
        if validation["allowed"]:
            return {
                "valid": True,
                "tenant": tenant,
                "user": tenant.get_user(user_id)
            }
        else:
            return {"valid": False, "error": validation["reason"]}


# Global tenant manager instance
tenant_manager = TenantManager()