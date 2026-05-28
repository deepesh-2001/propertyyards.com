"""
Session Management Module
Handles user sessions with Redis backend for JWT token management
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import json
import logging

from app.cache import get_from_cache, set_in_cache, delete_from_cache, invalidate_cache_pattern
from app.config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """Session manager using Redis for storing active sessions"""

    def __init__(self):
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
        self.session_ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds

    async def create_session(
        self,
        user_id: str,
        email: str,
        role: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new user session"""
        try:
            session_id = str(uuid.uuid4())
            created_at = datetime.utcnow()
            expires_at = created_at + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "email": email,
                "role": role,
                "user_agent": user_agent,
                "ip_address": ip_address,
                "metadata": metadata or {},
                "created_at": created_at.isoformat(),
                "expires_at": expires_at.isoformat(),
                "last_activity": created_at.isoformat(),
                "is_active": True
            }

            # Store session in Redis
            session_key = f"{self.session_prefix}{session_id}"
            await set_in_cache(session_key, session_data, ttl=self.session_ttl)

            # Add to user's active sessions list
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            user_sessions = await get_from_cache(user_sessions_key)
            if user_sessions:
                user_sessions = json.loads(user_sessions)
            else:
                user_sessions = []

            user_sessions.append({
                "session_id": session_id,
                "created_at": created_at.isoformat(),
                "user_agent": user_agent,
                "ip_address": ip_address
            })

            await set_in_cache(user_sessions_key, json.dumps(user_sessions), ttl=86400)  # 24 hours

            logger.info(f"Session created for user {user_id}: {session_id}")
            return session_data

        except Exception as e:
            logger.error(f"Session creation error: {e}")
            raise

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        try:
            session_key = f"{self.session_prefix}{session_id}"
            session_data = await get_from_cache(session_key)

            if session_data:
                # Check if session is expired
                expires_at = datetime.fromisoformat(session_data["expires_at"])
                if datetime.utcnow() > expires_at:
                    await self.delete_session(session_id)
                    return None

                # Update last activity
                session_data["last_activity"] = datetime.utcnow().isoformat()
                await set_in_cache(session_key, session_data, ttl=self.session_ttl)

                return session_data

            return None

        except Exception as e:
            logger.error(f"Session retrieval error: {e}")
            return None

    async def update_session(
        self,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Update session metadata"""
        try:
            session_data = await self.get_session(session_id)
            if not session_data:
                return None

            if metadata:
                session_data["metadata"].update(metadata)

            session_data["last_activity"] = datetime.utcnow().isoformat()
            session_key = f"{self.session_prefix}{session_id}"
            await set_in_cache(session_key, session_data, ttl=self.session_ttl)

            return session_data

        except Exception as e:
            logger.error(f"Session update error: {e}")
            return None

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        try:
            session_data = await self.get_session(session_id)
            if not session_data:
                return False

            user_id = session_data["user_id"]

            # Remove session from Redis
            session_key = f"{self.session_prefix}{session_id}"
            await delete_from_cache(session_key)

            # Remove from user's active sessions list
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            user_sessions = await get_from_cache(user_sessions_key)
            if user_sessions:
                user_sessions = json.loads(user_sessions)
                user_sessions = [s for s in user_sessions if s["session_id"] != session_id]
                await set_in_cache(user_sessions_key, json.dumps(user_sessions), ttl=86400)

            logger.info(f"Session deleted: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Session deletion error: {e}")
            return False

    async def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user (logout from all devices)"""
        try:
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            user_sessions = await get_from_cache(user_sessions_key)

            if not user_sessions:
                return 0

            user_sessions = json.loads(user_sessions)
            deleted_count = 0

            for session_info in user_sessions:
                session_id = session_info["session_id"]
                session_key = f"{self.session_prefix}{session_id}"
                await delete_from_cache(session_key)
                deleted_count += 1

            # Clear user sessions list
            await delete_from_cache(user_sessions_key)

            logger.info(f"Deleted {deleted_count} sessions for user {user_id}")
            return deleted_count

        except Exception as e:
            logger.error(f"User sessions deletion error: {e}")
            return 0

    async def get_user_sessions(self, user_id: str) -> list:
        """Get all active sessions for a user"""
        try:
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            user_sessions = await get_from_cache(user_sessions_key)

            if user_sessions:
                return json.loads(user_sessions)

            return []

        except Exception as e:
            logger.error(f"User sessions retrieval error: {e}")
            return []

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (should be run periodically)"""
        try:
            # This is a simplified cleanup - in production, you might want to scan all session keys
            # For now, we rely on Redis TTL to auto-expire sessions
            logger.info("Session cleanup completed (relying on Redis TTL)")
            return 0

        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
            return 0

    async def validate_session(self, session_id: str) -> bool:
        """Validate if a session is active and not expired"""
        session = await self.get_session(session_id)
        return session is not None and session.get("is_active", False)


# Global session manager instance
session_manager = SessionManager()
