"""
Feature Flag System
Manages feature flags for controlling access to features and UI elements
"""
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from functools import wraps
import logging

from app.cache import get_from_cache, set_in_cache, delete_from_cache, generate_cache_key

logger = logging.getLogger(__name__)


class FeatureFlag:
    """Feature flag model"""

    def __init__(
        self,
        key: str,
        name: str,
        description: str,
        is_enabled: bool = False,
        enabled_for_roles: Optional[List[str]] = None,
        enabled_for_users: Optional[List[str]] = None,
        percentage: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.key = key
        self.name = name
        self.description = description
        self.is_enabled = is_enabled
        self.enabled_for_roles = enabled_for_roles or []
        self.enabled_for_users = enabled_for_users or []
        self.percentage = percentage  # For gradual rollout (0-100)
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "is_enabled": self.is_enabled,
            "enabled_for_roles": self.enabled_for_roles,
            "enabled_for_users": self.enabled_for_users,
            "percentage": self.percentage,
            "metadata": self.metadata
        }


class FeatureFlagManager:
    """Manager for feature flags with database and cache backing"""

    def __init__(self):
        self.cache_prefix = "feature_flag:"
        self.cache_ttl = 300  # 5 minutes

        # Default feature flags
        self.default_flags = {
            # Onboarding features
            "onboarding_enabled": FeatureFlag(
                key="onboarding_enabled",
                name="Employee Onboarding",
                description="Enable employee onboarding and offboarding features",
                is_enabled=True,
                enabled_for_roles=["admin", "hr"]
            ),
            "onboarding_notifications": FeatureFlag(
                key="onboarding_notifications",
                name="Onboarding Notifications",
                description="Enable email and WhatsApp notifications for onboarding",
                is_enabled=True,
                enabled_for_roles=["admin", "hr"]
            ),
            "epfo_integration": FeatureFlag(
                key="epfo_integration",
                name="EPFO Integration",
                description="Enable EPFO/ESI registration and management",
                is_enabled=True,
                enabled_for_roles=["admin", "hr"]
            ),

            # Scraper features
            "property_scraper": FeatureFlag(
                key="property_scraper",
                name="Property Scraper",
                description="Enable property scraping from external websites",
                is_enabled=True,
                enabled_for_roles=["admin", "agent", "seller"]
            ),
            "scraper_auto_enrich": FeatureFlag(
                key="scraper_auto_enrich",
                name="Auto Property Enrichment",
                description="Automatically enrich property data with scraped info",
                is_enabled=True,
                enabled_for_roles=["admin", "agent"]
            ),

            # Property onboarding features
            "property_onboarding": FeatureFlag(
                key="property_onboarding",
                name="Easy Property Onboarding",
                description="Enable easy property onboarding with multiple import methods",
                is_enabled=True,
                enabled_for_roles=["admin", "agent", "seller"]
            ),
            "property_url_import": FeatureFlag(
                key="property_url_import",
                name="URL Property Import",
                description="Enable importing properties from external URLs",
                is_enabled=True,
                enabled_for_roles=["admin", "agent", "seller"]
            ),
            "property_text_import": FeatureFlag(
                key="property_text_import",
                name="Text Property Import",
                description="Enable extracting properties from text descriptions",
                is_enabled=True,
                enabled_for_roles=["admin", "agent", "seller"]
            ),
            "property_bulk_import": FeatureFlag(
                key="property_bulk_import",
                name="Bulk Property Import",
                description="Enable bulk property import from CSV/JSON",
                is_enabled=True,
                enabled_for_roles=["admin", "agent"]
            ),
            "property_auto_publish": FeatureFlag(
                key="property_auto_publish",
                name="Auto Property Publish",
                description="Auto-publish properties that meet criteria",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),

            # Commission features
            "commission_system": FeatureFlag(
                key="commission_system",
                name="Commission System",
                description="Enable commission calculation and payouts",
                is_enabled=True,
                enabled_for_roles=["admin", "agent"]
            ),
            "credit_card_cashback": FeatureFlag(
                key="credit_card_cashback",
                name="Credit Card Cashback",
                description="Enable credit card cashback tracking and commissions",
                is_enabled=True,
                enabled_for_roles=["admin", "agent"]
            ),

            # Payment features
            "stripe_payments": FeatureFlag(
                key="stripe_payments",
                name="Stripe Payments",
                description="Enable Stripe payment gateway",
                is_enabled=True,
                enabled_for_roles=["admin", "buyer", "seller"]
            ),
            "razorpay_payments": FeatureFlag(
                key="razorpay_payments",
                name="Razorpay Payments",
                description="Enable Razorpay payment gateway",
                is_enabled=False,
                enabled_for_roles=["admin"]
            ),

            # Analytics features
            "advanced_analytics": FeatureFlag(
                key="advanced_analytics",
                name="Advanced Analytics",
                description="Enable advanced analytics and reporting",
                is_enabled=True,
                enabled_for_roles=["admin", "agent"]
            ),
            "real_time_analytics": FeatureFlag(
                key="real_time_analytics",
                name="Real-time Analytics",
                description="Enable real-time analytics dashboard",
                is_enabled=False,
                enabled_for_roles=["admin"]
            ),

            # UI features
            "dark_mode": FeatureFlag(
                key="dark_mode",
                name="Dark Mode",
                description="Enable dark mode in UI",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),
            "property_map_view": FeatureFlag(
                key="property_map_view",
                name="Property Map View",
                description="Enable map view for property listings",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),
            "property_3d_tour": FeatureFlag(
                key="property_3d_tour",
                name="Property 3D Tour",
                description="Enable 3D virtual tours for properties",
                is_enabled=False,
                enabled_for_roles=["all"]
            ),
            "ai_property_recommendations": FeatureFlag(
                key="ai_property_recommendations",
                name="AI Property Recommendations",
                description="Enable AI-powered property recommendations",
                is_enabled=False,
                enabled_for_roles=["buyer"]
            ),

            # Security features
            "two_factor_auth": FeatureFlag(
                key="two_factor_auth",
                name="Two-Factor Authentication",
                description="Enable 2FA for user accounts",
                is_enabled=False,
                enabled_for_roles=["all"]
            ),
            "session_management": FeatureFlag(
                key="session_management",
                name="Session Management",
                description="Enable session management and tracking",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),

            # Whiteboard features
            "whiteboard_enabled": FeatureFlag(
                key="whiteboard_enabled",
                name="Collaborative Whiteboard",
                description="Enable collaborative whiteboard functionality",
                is_enabled=True,
                enabled_for_roles=["admin", "agent", "seller", "buyer"]
            ),
            "whiteboard_sharing": FeatureFlag(
                key="whiteboard_sharing",
                name="Whiteboard Sharing",
                description="Enable whiteboard sharing with other users",
                is_enabled=True,
                enabled_for_roles=["admin", "agent", "seller"]
            ),
            "whiteboard_public": FeatureFlag(
                key="whiteboard_public",
                name="Public Whiteboards",
                description="Enable creating public whiteboards",
                is_enabled=True,
                enabled_for_roles=["admin", "agent"]
            ),

            # User management features
            "user_management": FeatureFlag(
                key="user_management",
                name="User Management",
                description="Enable user profile management",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),
            "user_registration": FeatureFlag(
                key="user_registration",
                name="User Registration",
                description="Enable new user registration",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),

            # Property management features
            "property_management": FeatureFlag(
                key="property_management",
                name="Property Management",
                description="Enable property listing management",
                is_enabled=True,
                enabled_for_roles=["admin", "agent", "seller"]
            ),
            "property_search": FeatureFlag(
                key="property_search",
                name="Property Search",
                description="Enable property search and filtering",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),
            "property_wishlist": FeatureFlag(
                key="property_wishlist",
                name="Property Wishlist",
                description="Enable property wishlist functionality",
                is_enabled=True,
                enabled_for_roles=["buyer"]
            ),

            # CRM features
            "crm_system": FeatureFlag(
                key="crm_system",
                name="CRM System",
                description="Enable CRM lead management",
                is_enabled=True,
                enabled_for_roles=["admin", "agent"]
            ),
            "crm_pipeline": FeatureFlag(
                key="crm_pipeline",
                name="CRM Pipeline",
                description="Enable CRM pipeline tracking",
                is_enabled=True,
                enabled_for_roles=["admin", "agent"]
            ),

            # Additional payment features
            "payment_conditions": FeatureFlag(
                key="payment_conditions",
                name="Payment Conditions",
                description="Enable payment condition management",
                is_enabled=True,
                enabled_for_roles=["admin", "seller", "buyer"]
            ),
            "payment_methods": FeatureFlag(
                key="payment_methods",
                name="Payment Methods",
                description="Enable payment method management",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),
            "payment_analytics": FeatureFlag(
                key="payment_analytics",
                name="Payment Analytics",
                description="Enable payment analytics and reporting",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),
            "subscriptions": FeatureFlag(
                key="subscriptions",
                name="Subscriptions",
                description="Enable subscription management",
                is_enabled=True,
                enabled_for_roles=["admin", "buyer"]
            ),

            # Additional credit card features
            "credit_card_management": FeatureFlag(
                key="credit_card_management",
                name="Credit Card Management",
                description="Enable credit card management",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),
            "credit_card_comparison": FeatureFlag(
                key="credit_card_comparison",
                name="Credit Card Comparison",
                description="Enable credit card comparison tools",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),
            "reward_analytics": FeatureFlag(
                key="reward_analytics",
                name="Reward Analytics",
                description="Enable reward points analytics",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),

            # Broker features
            "broker_management": FeatureFlag(
                key="broker_management",
                name="Broker Management",
                description="Enable broker profile management",
                is_enabled=True,
                enabled_for_roles=["admin", "agent"]
            ),

            # Inquiry features
            "inquiry_management": FeatureFlag(
                key="inquiry_management",
                name="Inquiry Management",
                description="Enable property inquiry management",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),

            # Feedback and reviews
            "feedback_system": FeatureFlag(
                key="feedback_system",
                name="Feedback System",
                description="Enable user feedback system",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),
            "review_system": FeatureFlag(
                key="review_system",
                name="Review System",
                description="Enable property and broker reviews",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),

            # Claims and reimbursement
            "claims_management": FeatureFlag(
                key="claims_management",
                name="Claims Management",
                description="Enable claims management",
                is_enabled=True,
                enabled_for_roles=["admin", "hr"]
            ),
            "reimbursement_system": FeatureFlag(
                key="reimbursement_system",
                name="Reimbursement System",
                description="Enable reimbursement management",
                is_enabled=True,
                enabled_for_roles=["admin", "hr"]
            ),

            # Recruitment features
            "recruitment_system": FeatureFlag(
                key="recruitment_system",
                name="Recruitment System",
                description="Enable recruitment management",
                is_enabled=True,
                enabled_for_roles=["admin", "hr"]
            ),
            "interview_scheduling": FeatureFlag(
                key="interview_scheduling",
                name="Interview Scheduling",
                description="Enable interview scheduling",
                is_enabled=True,
                enabled_for_roles=["admin", "hr"]
            ),

            # Attendance and performance
            "attendance_tracking": FeatureFlag(
                key="attendance_tracking",
                name="Attendance Tracking",
                description="Enable attendance tracking",
                is_enabled=True,
                enabled_for_roles=["admin", "hr"]
            ),
            "performance_tracking": FeatureFlag(
                key="performance_tracking",
                name="Performance Tracking",
                description="Enable performance tracking",
                is_enabled=True,
                enabled_for_roles=["admin", "hr"]
            ),

            # Reports and analytics
            "reporting_system": FeatureFlag(
                key="reporting_system",
                name="Reporting System",
                description="Enable reporting system",
                is_enabled=True,
                enabled_for_roles=["admin", "hr"]
            ),

            # Loan calculator
            "loan_calculator": FeatureFlag(
                key="loan_calculator",
                name="Loan Calculator",
                description="Enable loan calculator",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),

            # Chatbot
            "chatbot": FeatureFlag(
                key="chatbot",
                name="AI Chatbot",
                description="Enable AI chatbot assistance",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),

            # Fraud detection
            "fraud_detection": FeatureFlag(
                key="fraud_detection",
                name="Fraud Detection",
                description="Enable fraud detection system",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),

            # Self healing
            "self_healing": FeatureFlag(
                key="self_healing",
                name="Self Healing",
                description="Enable self-healing system",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),

            # Monitoring
            "system_monitoring": FeatureFlag(
                key="system_monitoring",
                name="System Monitoring",
                description="Enable system monitoring",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),

            # Notifications
            "notification_system": FeatureFlag(
                key="notification_system",
                name="Notification System",
                description="Enable notification system",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),

            # Referral system
            "referral_system": FeatureFlag(
                key="referral_system",
                name="Referral System",
                description="Enable referral system",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),

            # Tax management
            "tax_management": FeatureFlag(
                key="tax_management",
                name="Tax Management",
                description="Enable tax management",
                is_enabled=True,
                enabled_for_roles=["admin", "hr"]
            ),

            # Salary management
            "salary_management": FeatureFlag(
                key="salary_management",
                name="Salary Management",
                description="Enable salary management",
                is_enabled=True,
                enabled_for_roles=["admin", "hr"]
            ),

            # Prediction and AI
            "price_prediction": FeatureFlag(
                key="price_prediction",
                name="Price Prediction",
                description="Enable AI price prediction",
                is_enabled=True,
                enabled_for_roles=["admin", "agent"]
            ),

            # Access control
            "access_control": FeatureFlag(
                key="access_control",
                name="Access Control",
                description="Enable advanced access control",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),

            # Contact management
            "contact_management": FeatureFlag(
                key="contact_management",
                name="Contact Management",
                description="Enable contact management",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),

            # Privacy features
            "privacy_settings": FeatureFlag(
                key="privacy_settings",
                name="Privacy Settings",
                description="Enable user privacy settings management",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),
            "data_export": FeatureFlag(
                key="data_export",
                name="Data Export",
                description="Enable user data export functionality",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),
            "data_deletion": FeatureFlag(
                key="data_deletion",
                name="Data Deletion",
                description="Enable user data deletion (GDPR compliance)",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),
            "privacy_dashboard": FeatureFlag(
                key="privacy_dashboard",
                name="Privacy Dashboard",
                description="Enable privacy dashboard for users",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),

            # Content security features
            "content_moderation": FeatureFlag(
                key="content_moderation",
                name="Content Moderation",
                description="Enable content moderation system",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),
            "spam_detection": FeatureFlag(
                key="spam_detection",
                name="Spam Detection",
                description="Enable spam detection and filtering",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),
            "content_filtering": FeatureFlag(
                key="content_filtering",
                name="Content Filtering",
                description="Enable content filtering for inappropriate content",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),
            "rate_limiting": FeatureFlag(
                key="rate_limiting",
                name="Rate Limiting",
                description="Enable API rate limiting",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),

            # User permissions features
            "role_management": FeatureFlag(
                key="role_management",
                name="Role Management",
                description="Enable role-based access control management",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),
            "permission_management": FeatureFlag(
                key="permission_management",
                name="Permission Management",
                description="Enable granular permission management",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),
            "user_audit_logs": FeatureFlag(
                key="user_audit_logs",
                name="User Audit Logs",
                description="Enable user activity audit logs",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),
            "access_control": FeatureFlag(
                key="access_control",
                name="Access Control",
                description="Enable advanced access control",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),

            # Future projects features
            "beta_features": FeatureFlag(
                key="beta_features",
                name="Beta Features",
                description="Enable beta features for testing",
                is_enabled=False,
                enabled_for_roles=["admin"]
            ),
            "experimental_features": FeatureFlag(
                key="experimental_features",
                name="Experimental Features",
                description="Enable experimental features",
                is_enabled=False,
                enabled_for_roles=["admin"]
            ),
            "future_projects": FeatureFlag(
                key="future_projects",
                name="Future Projects",
                description="Enable access to future project previews",
                is_enabled=False,
                enabled_for_roles=["admin"]
            ),
            "early_access": FeatureFlag(
                key="early_access",
                name="Early Access",
                description="Enable early access to new features",
                is_enabled=False,
                enabled_for_roles=["admin", "premium"]
            ),

            # Admin analytics features
            "admin_analytics": FeatureFlag(
                key="admin_analytics",
                name="Admin Analytics",
                description="Enable comprehensive admin analytics dashboard",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),
            "user_activity_analytics": FeatureFlag(
                key="user_activity_analytics",
                name="User Activity Analytics",
                description="Enable user activity tracking and analytics",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),
            "revenue_analytics": FeatureFlag(
                key="revenue_analytics",
                name="Revenue Analytics",
                description="Enable revenue and financial analytics",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),
            "performance_analytics": FeatureFlag(
                key="performance_analytics",
                name="Performance Analytics",
                description="Enable system performance analytics",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),
            "security_analytics": FeatureFlag(
                key="security_analytics",
                name="Security Analytics",
                description="Enable security event analytics",
                is_enabled=True,
                enabled_for_roles=["admin"]
            ),

            # User analytics features
            "user_analytics": FeatureFlag(
                key="user_analytics",
                name="User Analytics",
                description="Enable personal user analytics dashboard",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),
            "usage_analytics": FeatureFlag(
                key="usage_analytics",
                name="Usage Analytics",
                description="Enable usage statistics for users",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),
            "engagement_analytics": FeatureFlag(
                key="engagement_analytics",
                name="Engagement Analytics",
                description="Enable engagement metrics for users",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),
            "personal_insights": FeatureFlag(
                key="personal_insights",
                name="Personal Insights",
                description="Enable AI-powered personal insights",
                is_enabled=True,
                enabled_for_roles=["all"]
            ),
        }

    async def get_flag(self, key: str, database) -> Optional[FeatureFlag]:
        """Get a feature flag by key"""
        try:
            # Check cache first
            cache_key = generate_cache_key(self.cache_prefix, key)
            cached = await get_from_cache(cache_key)
            if cached:
                return FeatureFlag(**cached)

            # Check database
            flag_doc = await database.feature_flags.find_one({"key": key})
            if flag_doc:
                flag = FeatureFlag(
                    key=flag_doc["key"],
                    name=flag_doc["name"],
                    description=flag_doc["description"],
                    is_enabled=flag_doc["is_enabled"],
                    enabled_for_roles=flag_doc.get("enabled_for_roles", []),
                    enabled_for_users=flag_doc.get("enabled_for_users", []),
                    percentage=flag_doc.get("percentage"),
                    metadata=flag_doc.get("metadata", {})
                )
                await set_in_cache(cache_key, flag.to_dict(), ttl=self.cache_ttl)
                return flag

            # Return default if not in database
            if key in self.default_flags:
                return self.default_flags[key]

            return None

        except Exception as e:
            logger.error(f"Error getting feature flag {key}: {e}")
            return None

    async def is_enabled(
        self,
        key: str,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        database = None
    ) -> bool:
        """Check if a feature flag is enabled for a user"""
        try:
            flag = await self.get_flag(key, database)
            if not flag:
                return False

            # Check if globally enabled
            if not flag.is_enabled:
                return False

            # Check role-based access
            if flag.enabled_for_roles and user_role:
                if "all" in flag.enabled_for_roles:
                    return True
                if user_role not in flag.enabled_for_roles:
                    return False

            # Check user-based access
            if flag.enabled_for_users and user_id:
                if user_id not in flag.enabled_for_users:
                    return False

            # Check percentage rollout (if no specific user/role restriction)
            if flag.percentage and not flag.enabled_for_users and not flag.enabled_for_roles:
                import hashlib
                hash_val = int(hashlib.md5(f"{key}_{user_id}".encode()).hexdigest(), 16)
                return (hash_val % 100) < flag.percentage

            return True

        except Exception as e:
            logger.error(f"Error checking feature flag {key}: {e}")
            return False

    async def set_flag(
        self,
        key: str,
        is_enabled: bool,
        enabled_for_roles: Optional[List[str]] = None,
        enabled_for_users: Optional[List[str]] = None,
        percentage: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        database = None
    ) -> FeatureFlag:
        """Set/update a feature flag"""
        try:
            flag = await self.get_flag(key, database)
            if not flag:
                raise ValueError(f"Feature flag {key} not found")

            flag.is_enabled = is_enabled
            if enabled_for_roles is not None:
                flag.enabled_for_roles = enabled_for_roles
            if enabled_for_users is not None:
                flag.enabled_for_users = enabled_for_users
            if percentage is not None:
                flag.percentage = percentage
            if metadata is not None:
                flag.metadata = metadata

            # Update in database
            flag_doc = flag.to_dict()
            flag_doc["updated_at"] = datetime.utcnow()

            await database.feature_flags.update_one(
                {"key": key},
                {"$set": flag_doc},
                upsert=True
            )

            # Invalidate cache
            cache_key = generate_cache_key(self.cache_prefix, key)
            await delete_from_cache(cache_key)

            logger.info(f"Feature flag {key} updated: enabled={is_enabled}")
            return flag

        except Exception as e:
            logger.error(f"Error setting feature flag {key}: {e}")
            raise

    async def get_all_flags(self, database) -> List[Dict[str, Any]]:
        """Get all feature flags"""
        try:
            # Check cache
            cache_key = generate_cache_key(self.cache_prefix, "all")
            cached = await get_from_cache(cache_key)
            if cached:
                return cached

            # Get from database
            cursor = database.feature_flags.find()
            db_flags = await cursor.to_list(length=100)

            flags_dict = {f["key"]: f for f in db_flags}

            # Merge with defaults
            all_flags = []
            for key, default_flag in self.default_flags.items():
                if key in flags_dict:
                    flag_data = flags_dict[key]
                    flag = FeatureFlag(
                        key=flag_data["key"],
                        name=flag_data["name"],
                        description=flag_data["description"],
                        is_enabled=flag_data["is_enabled"],
                        enabled_for_roles=flag_data.get("enabled_for_roles", []),
                        enabled_for_users=flag_data.get("enabled_for_users", []),
                        percentage=flag_data.get("percentage"),
                        metadata=flag_data.get("metadata", {})
                    )
                else:
                    flag = default_flag

                all_flags.append(flag.to_dict())

            # Cache the result
            await set_in_cache(cache_key, all_flags, ttl=self.cache_ttl)

            return all_flags

        except Exception as e:
            logger.error(f"Error getting all feature flags: {e}")
            return []

    async def get_flags_for_ui(
        self,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        database = None
    ) -> Dict[str, bool]:
        """Get enabled flags for UI (simplified format)"""
        try:
            all_flags = await self.get_all_flags(database)
            enabled_flags = {}

            for flag_data in all_flags:
                key = flag_data["key"]
                is_enabled = await self.is_enabled(key, user_id, user_role, database)
                enabled_flags[key] = is_enabled

            return enabled_flags

        except Exception as e:
            logger.error(f"Error getting flags for UI: {e}")
            return {}

    async def initialize_default_flags(self, database):
        """Initialize default flags in database"""
        try:
            for flag in self.default_flags.values():
                flag_doc = flag.to_dict()
                flag_doc["created_at"] = datetime.utcnow()
                flag_doc["updated_at"] = datetime.utcnow()

                await database.feature_flags.update_one(
                    {"key": flag.key},
                    {"$setOnInsert": flag_doc},
                    upsert=True
                )

            logger.info("Default feature flags initialized")

        except Exception as e:
            logger.error(f"Error initializing default flags: {e}")


# Global manager instance
feature_flag_manager = FeatureFlagManager()


# ========== Feature Flag Decorators ==========

def require_feature_flag(flag_key: str):
    """
    Decorator to require a feature flag to be enabled for endpoint access
    Usage:
        @require_feature_flag("onboarding_enabled")
        async def my_endpoint(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract database and current_user from kwargs
            database = kwargs.get('database')
            current_user = kwargs.get('current_user')

            if not database:
                from fastapi import HTTPException
                raise HTTPException(status_code=500, detail="Database not available")

            if not current_user:
                from fastapi import HTTPException
                raise HTTPException(status_code=401, detail="Authentication required")

            user_id = str(current_user.get("_id"))
            user_role = current_user.get("role")

            is_enabled = await feature_flag_manager.is_enabled(
                key=flag_key,
                user_id=user_id,
                user_role=user_role,
                database=database
            )

            if not is_enabled:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=403,
                    detail=f"Feature '{flag_key}' is not enabled"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def with_feature_flag(flag_key: str, default_return: Any = None):
    """
    Decorator to conditionally execute endpoint based on feature flag
    If flag is disabled, returns default_return instead of executing
    Usage:
        @with_feature_flag("new_feature", default_return={"message": "Feature disabled"})
        async def my_endpoint(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            database = kwargs.get('database')
            current_user = kwargs.get('current_user')

            if not database or not current_user:
                return default_return

            user_id = str(current_user.get("_id"))
            user_role = current_user.get("role")

            is_enabled = await feature_flag_manager.is_enabled(
                key=flag_key,
                user_id=user_id,
                user_role=user_role,
                database=database
            )

            if not is_enabled:
                return default_return

            return await func(*args, **kwargs)
        return wrapper
    return decorator
