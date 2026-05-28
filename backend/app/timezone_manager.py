"""
Timezone Manager
Handle timezone conversions and user timezone preferences
"""
import pytz
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TimezoneInfo:
    """Timezone information"""
    name: str
    offset: str
    offset_hours: float
    is_dst: bool
    country_code: str
    region: str


class TimezoneManager:
    """Manage timezone conversions and preferences"""

    # Common timezones for dropdowns
    COMMON_TIMEZONES = [
        ("UTC", "UTC"),
        ("America/New_York", "Eastern Time (ET)"),
        ("America/Chicago", "Central Time (CT)"),
        ("America/Denver", "Mountain Time (MT)"),
        ("America/Los_Angeles", "Pacific Time (PT)"),
        ("Europe/London", "London (GMT)"),
        ("Europe/Paris", "Paris (CET)"),
        ("Europe/Berlin", "Berlin (CET)"),
        ("Europe/Moscow", "Moscow (MSK)"),
        ("Asia/Dubai", "Dubai (GST)"),
        ("Asia/Kolkata", "India (IST)"),
        ("Asia/Bangkok", "Bangkok (ICT)"),
        ("Asia/Singapore", "Singapore (SGT)"),
        ("Asia/Hong_Kong", "Hong Kong (HKT)"),
        ("Asia/Shanghai", "Shanghai (CST)"),
        ("Asia/Tokyo", "Tokyo (JST)"),
        ("Asia/Seoul", "Seoul (KST)"),
        ("Australia/Sydney", "Sydney (AEDT)"),
        ("Australia/Melbourne", "Melbourne (AEDT)"),
        ("Pacific/Auckland", "Auckland (NZDT)"),
        ("America/Sao_Paulo", "São Paulo (BRT)"),
        ("America/Mexico_City", "Mexico City (CST)"),
        ("Africa/Johannesburg", "Johannesburg (SAST)"),
        ("Africa/Cairo", "Cairo (EET)"),
        ("Africa/Lagos", "Lagos (WAT)"),
    ]

    def __init__(self):
        self.default_timezone = "UTC"
        self.user_timezones: Dict[str, str] = {}  # user_id -> timezone

    def get_all_timezones(self) -> List[Dict[str, str]]:
        """Get all available timezones"""
        return [
            {"value": tz, "label": label}
            for tz, label in self.COMMON_TIMEZONES
        ]

    def set_user_timezone(self, user_id: str, timezone: str):
        """Set timezone for user"""
        if timezone in pytz.all_timezones:
            self.user_timezones[user_id] = timezone
        else:
            logger.warning(f"Invalid timezone: {timezone}")

    def get_user_timezone(self, user_id: str) -> str:
        """Get user's timezone"""
        return self.user_timezones.get(user_id, self.default_timezone)

    def convert_to_user_timezone(
        self,
        utc_datetime: datetime,
        user_id: str
    ) -> datetime:
        """Convert UTC datetime to user's timezone"""
        if utc_datetime is None:
            return None

        # Ensure datetime is UTC
        if utc_datetime.tzinfo is None:
            utc_datetime = pytz.UTC.localize(utc_datetime)
        elif utc_datetime.tzinfo != pytz.UTC:
            utc_datetime = utc_datetime.astimezone(pytz.UTC)

        # Convert to user timezone
        user_tz = self.get_user_timezone(user_id)
        target_tz = pytz.timezone(user_tz)

        return utc_datetime.astimezone(target_tz)

    def convert_to_utc(
        self,
        local_datetime: datetime,
        timezone: str
    ) -> datetime:
        """Convert local datetime to UTC"""
        if local_datetime is None:
            return None

        # Localize if naive
        if local_datetime.tzinfo is None:
            tz = pytz.timezone(timezone)
            local_datetime = tz.localize(local_datetime)

        # Convert to UTC
        return local_datetime.astimezone(pytz.UTC)

    def get_current_time_in_timezone(self, timezone: str) -> datetime:
        """Get current time in specific timezone"""
        tz = pytz.timezone(timezone)
        return datetime.now(tz)

    def get_timezone_info(self, timezone: str) -> Optional[TimezoneInfo]:
        """Get detailed timezone information"""
        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)

            # Calculate offset
            offset = now.strftime("%z")
            offset_hours = now.utcoffset().total_seconds() / 3600

            # Determine if DST
            is_dst = now.dst() is not None and now.dst().total_seconds() > 0

            # Get country code from timezone name
            parts = timezone.split("/")
            country_code = parts[0] if len(parts) > 1 else ""
            region = parts[1] if len(parts) > 1 else timezone

            return TimezoneInfo(
                name=timezone,
                offset=offset,
                offset_hours=offset_hours,
                is_dst=is_dst,
                country_code=country_code,
                region=region
            )

        except Exception as e:
            logger.error(f"Error getting timezone info: {e}")
            return None

    def format_datetime(
        self,
        dt: datetime,
        timezone: str,
        format_str: str = "%Y-%m-%d %H:%M:%S"
    ) -> str:
        """Format datetime in specific timezone"""
        if dt is None:
            return ""

        # Convert to target timezone
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)

        tz = pytz.timezone(timezone)
        localized = dt.astimezone(tz)

        return localized.strftime(format_str)

    def format_relative_time(
        self,
        past_datetime: datetime,
        user_id: Optional[str] = None
    ) -> str:
        """Format relative time (e.g., '2 hours ago')"""
        if past_datetime is None:
            return ""

        # Get current time in appropriate timezone
        if user_id:
            tz_name = self.get_user_timezone(user_id)
            now = self.get_current_time_in_timezone(tz_name)
        else:
            now = datetime.now(pytz.UTC)

        # Convert past_datetime to same timezone
        if past_datetime.tzinfo is None:
            past_datetime = pytz.UTC.localize(past_datetime)

        # Calculate difference
        diff = now - past_datetime
        seconds = diff.total_seconds()

        # Format based on magnitude
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
        elif seconds < 2592000:
            weeks = int(seconds / 604800)
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        else:
            return past_datetime.strftime("%Y-%m-%d")

    def is_same_day(
        self,
        dt1: datetime,
        dt2: datetime,
        timezone: str
    ) -> bool:
        """Check if two datetimes are on the same day in given timezone"""
        tz = pytz.timezone(timezone)

        if dt1.tzinfo is None:
            dt1 = pytz.UTC.localize(dt1)
        if dt2.tzinfo is None:
            dt2 = pytz.UTC.localize(dt2)

        local1 = dt1.astimezone(tz)
        local2 = dt2.astimezone(tz)

        return local1.date() == local2.date()

    def get_business_hours_offset(
        self,
        timezone1: str,
        timezone2: str
    ) -> float:
        """Get hours difference between two timezones"""
        now = datetime.now(pytz.UTC)

        tz1 = pytz.timezone(timezone1)
        tz2 = pytz.timezone(timezone2)

        offset1 = now.astimezone(tz1).utcoffset().total_seconds() / 3600
        offset2 = now.astimezone(tz2).utcoffset().total_seconds() / 3600

        return offset2 - offset1

    def detect_timezone_from_ip(self, ip_address: str) -> Optional[str]:
        """Detect timezone from IP address (requires GeoIP service)"""
        # This is a placeholder - actual implementation would use GeoIP2
        # or similar service
        logger.info(f"Timezone detection from IP not implemented: {ip_address}")
        return None


# Global instance
timezone_manager = TimezoneManager()
