"""
Region Manager
Handle region-specific content, compliance, and localization
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Region(Enum):
    """Supported regions"""
    NORTH_AMERICA = "na"
    EUROPE = "eu"
    UK = "uk"
    ASIA_PACIFIC = "apac"
    INDIA = "in"
    MIDDLE_EAST = "me"
    AFRICA = "af"
    LATIN_AMERICA = "latam"
    OCEANIA = "oc"


class ComplianceStandard(Enum):
    """Data protection standards"""
    GDPR = "gdpr"  # EU
    CCPA = "ccpa"  # California
    LGPD = "lgpd"  # Brazil
    PIPEDA = "pipeda"  # Canada
    PDPA = "pdpa"  # Singapore
    POPIA = "popia"  # South Africa
    DPDP = "dpdp"  # India
    NONE = "none"


@dataclass
class RegionConfig:
    """Configuration for a region"""
    region: Region
    name: str
    countries: List[str]
    default_language: str
    default_currency: str
    default_timezone: str
    compliance_standards: List[ComplianceStandard]
    date_format: str
    measurement_system: str  # metric/imperial
    number_format: str
    phone_format: str
    features_enabled: List[str]
    features_disabled: List[str]
    legal_notices: Dict[str, str]


class RegionManager:
    """Manage region-specific configurations and content"""

    REGION_CONFIGS = {
        Region.NORTH_AMERICA: RegionConfig(
            region=Region.NORTH_AMERICA,
            name="North America",
            countries=["US", "CA", "MX"],
            default_language="en",
            default_currency="USD",
            default_timezone="America/New_York",
            compliance_standards=[ComplianceStandard.CCPA],
            date_format="%m/%d/%Y",
            measurement_system="imperial",
            number_format="#,##0.00",
            phone_format="(###) ###-####",
            features_enabled=["credit_score", "zillow_integration", "mls_listings"],
            features_disabled=["rera_compliance"],
            legal_notices={
                "privacy_policy": "privacy_us",
                "terms_of_service": "tos_us",
                "cookie_policy": "cookies_us"
            }
        ),
        Region.EUROPE: RegionConfig(
            region=Region.EUROPE,
            name="Europe",
            countries=["GB", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "CH", "PL", "SE", "NO", "DK", "FI"],
            default_language="en",
            default_currency="EUR",
            default_timezone="Europe/Paris",
            compliance_standards=[ComplianceStandard.GDPR],
            date_format="%d/%m/%Y",
            measurement_system="metric",
            number_format="#.##0,00",
            phone_format="+## ### ## ## ##",
            features_enabled=["gdpr_export", "right_to_be_forgotten", "cookie_consent"],
            features_disabled=["credit_score"],
            legal_notices={
                "privacy_policy": "privacy_eu",
                "terms_of_service": "tos_eu",
                "cookie_policy": "cookies_eu",
                "gdpr_notice": "gdpr_notice"
            }
        ),
        Region.UK: RegionConfig(
            region=Region.UK,
            name="United Kingdom",
            countries=["GB", "IE"],
            default_language="en",
            default_currency="GBP",
            default_timezone="Europe/London",
            compliance_standards=[ComplianceStandard.GDPR],
            date_format="%d/%m/%Y",
            measurement_system="metric",
            number_format="#,##0.00",
            phone_format="+44 ## #### ####",
            features_enabled=["gdpr_export", "right_to_be_forgotten", "cookie_consent"],
            features_disabled=["credit_score"],
            legal_notices={
                "privacy_policy": "privacy_uk",
                "terms_of_service": "tos_uk",
                "cookie_policy": "cookies_uk"
            }
        ),
        Region.INDIA: RegionConfig(
            region=Region.INDIA,
            name="India",
            countries=["IN"],
            default_language="en",
            default_currency="INR",
            default_timezone="Asia/Kolkata",
            compliance_standards=[ComplianceStandard.DPDP],
            date_format="%d-%m-%Y",
            measurement_system="metric",
            number_format="#,##,##0.00",
            phone_format="+91 ##### #####",
            features_enabled=["rera_compliance", "stamp_duty_calc", "parking_search"],
            features_disabled=["credit_score", "zillow_integration"],
            legal_notices={
                "privacy_policy": "privacy_in",
                "terms_of_service": "tos_in",
                "cookie_policy": "cookies_in",
                "rera_disclaimer": "rera_disclaimer"
            }
        ),
        Region.ASIA_PACIFIC: RegionConfig(
            region=Region.ASIA_PACIFIC,
            name="Asia Pacific",
            countries=["SG", "HK", "JP", "KR", "CN", "TW", "TH", "VN", "MY", "ID", "PH", "AU", "NZ"],
            default_language="en",
            default_currency="USD",
            default_timezone="Asia/Singapore",
            compliance_standards=[ComplianceStandard.PDPA],
            date_format="%d/%m/%Y",
            measurement_system="metric",
            number_format="#,##0.00",
            phone_format="+## #### ####",
            features_enabled=["multi_currency", "multi_language"],
            features_disabled=[],
            legal_notices={
                "privacy_policy": "privacy_apac",
                "terms_of_service": "tos_apac",
                "cookie_policy": "cookies_apac"
            }
        ),
        Region.MIDDLE_EAST: RegionConfig(
            region=Region.MIDDLE_EAST,
            name="Middle East",
            countries=["AE", "SA", "QA", "KW", "BH", "OM", "EG", "JO", "LB"],
            default_language="en",
            default_currency="USD",
            default_timezone="Asia/Dubai",
            compliance_standards=[],
            date_format="%d/%m/%Y",
            measurement_system="metric",
            number_format="#,##0.00",
            phone_format="+### ## ### ####",
            features_enabled=["islamic_finance", "arabic_support"],
            features_disabled=["mortgage_calculator"],
            legal_notices={
                "privacy_policy": "privacy_me",
                "terms_of_service": "tos_me",
                "cookie_policy": "cookies_me"
            }
        ),
        Region.AFRICA: RegionConfig(
            region=Region.AFRICA,
            name="Africa",
            countries=["ZA", "NG", "KE", "EG", "GH", "TZ", "UG", "RW", "MA", "TN"],
            default_language="en",
            default_currency="USD",
            default_timezone="Africa/Johannesburg",
            compliance_standards=[ComplianceStandard.POPIA],
            date_format="%d/%m/%Y",
            measurement_system="metric",
            number_format="#,##0.00",
            phone_format="+### ## ### ####",
            features_enabled=["mobile_money", "mpesa_integration"],
            features_disabled=[],
            legal_notices={
                "privacy_policy": "privacy_af",
                "terms_of_service": "tos_af",
                "cookie_policy": "cookies_af"
            }
        ),
        Region.LATIN_AMERICA: RegionConfig(
            region=Region.LATIN_AMERICA,
            name="Latin America",
            countries=["BR", "AR", "CL", "CO", "PE", "VE", "MX", "UY", "PY", "BO", "EC"],
            default_language="es",
            default_currency="USD",
            default_timezone="America/Sao_Paulo",
            compliance_standards=[ComplianceStandard.LGPD],
            date_format="%d/%m/%Y",
            measurement_system="metric",
            number_format="#.##0,00",
            phone_format="+## (##) #####-####",
            features_enabled=["portuguese_support", "spanish_support"],
            features_disabled=[],
            legal_notices={
                "privacy_policy": "privacy_latam",
                "terms_of_service": "tos_latam",
                "cookie_policy": "cookies_latam"
            }
        ),
        Region.OCEANIA: RegionConfig(
            region=Region.OCEANIA,
            name="Oceania",
            countries=["AU", "NZ", "FJ", "PG", "SB", "VU", "NC", "PF"],
            default_language="en",
            default_currency="AUD",
            default_timezone="Australia/Sydney",
            compliance_standards=[],
            date_format="%d/%m/%Y",
            measurement_system="metric",
            number_format="#,##0.00",
            phone_format="+## # #### ####",
            features_enabled=["nz_property_search"],
            features_disabled=[],
            legal_notices={
                "privacy_policy": "privacy_oc",
                "terms_of_service": "tos_oc",
                "cookie_policy": "cookies_oc"
            }
        ),
    }

    def __init__(self):
        self.user_regions: Dict[str, Region] = {}  # user_id -> region

    def get_region_config(self, region: Region) -> Optional[RegionConfig]:
        """Get configuration for a region"""
        return self.REGION_CONFIGS.get(region)

    def detect_region_from_country(self, country_code: str) -> Optional[Region]:
        """Detect region from country code"""
        for region, config in self.REGION_CONFIGS.items():
            if country_code.upper() in config.countries:
                return region
        return None

    def detect_region_from_ip(self, ip_address: str) -> Optional[Region]:
        """Detect region from IP address (placeholder)"""
        # This would integrate with GeoIP2 or similar service
        logger.info(f"Region detection from IP not implemented: {ip_address}")
        return None

    def set_user_region(self, user_id: str, region: Region):
        """Set region for user"""
        self.user_regions[user_id] = region

    def get_user_region(self, user_id: str) -> Region:
        """Get user's region"""
        return self.user_regions.get(user_id, Region.NORTH_AMERICA)

    def get_all_regions(self) -> List[Dict[str, Any]]:
        """Get all available regions"""
        return [
            {
                "code": region.value,
                "name": config.name,
                "countries": config.countries,
                "default_currency": config.default_currency,
                "compliance": [c.value for c in config.compliance_standards]
            }
            for region, config in self.REGION_CONFIGS.items()
        ]

    def is_feature_available(self, feature: str, region: Region) -> bool:
        """Check if feature is available in region"""
        config = self.get_region_config(region)
        if not config:
            return False

        if feature in config.features_disabled:
            return False

        if feature in config.features_enabled:
            return True

        # Feature not explicitly listed - default to available
        return True

    def get_required_compliance(self, region: Region) -> List[ComplianceStandard]:
        """Get required compliance standards for region"""
        config = self.get_region_config(region)
        if not config:
            return []
        return config.compliance_standards

    def localize_content(
        self,
        content: str,
        region: Region,
        placeholders: Dict[str, Any] = None
    ) -> str:
        """Localize content for region"""
        config = self.get_region_config(region)
        if not config:
            return content

        # Replace placeholders with region-specific values
        localized = content

        if placeholders:
            for key, value in placeholders.items():
                localized = localized.replace(f"{{{key}}}", str(value))

        # Add region-specific legal notices
        if "{legal_notice}" in localized:
            notices = config.legal_notices
            notice_text = f"[Legal notices: {', '.join(notices.keys())}]"
            localized = localized.replace("{legal_notice}", notice_text)

        return localized

    def get_localized_property_fields(self, region: Region) -> Dict[str, Any]:
        """Get property field labels localized for region"""
        config = self.get_region_config(region)

        if region == Region.INDIA:
            return {
                "area_label": "Super Built-up Area (sq ft)",
                "carpet_label": "Carpet Area (sq ft)",
                "price_label": "Total Price (₹)",
                "price_per_sqft_label": "Price per sq ft",
                "stamp_duty_label": "Stamp Duty (%)",
                "registration_label": "Registration Charges",
                "maintenance_label": "Maintenance Charges (monthly)",
                "parking_label": "Parking Slots",
                "rera_label": "RERA Registration Number",
                "facing_label": "Facing Direction",
                "vastu_label": "Vastu Compliant"
            }
        elif region == Region.EUROPE or region == Region.UK:
            return {
                "area_label": "Living Area (m²)",
                "carpet_label": "Total Floor Area (m²)",
                "price_label": "Asking Price (€)",
                "price_per_sqft_label": "Price per m²",
                "council_tax_label": "Council Tax Band",
                "epc_label": "EPC Rating",
                "tenure_label": "Tenure Type",
                "leasehold_label": "Leasehold Years Remaining"
            }
        elif region == Region.NORTH_AMERICA:
            return {
                "area_label": "Square Footage",
                "lot_label": "Lot Size (sq ft)",
                "price_label": "List Price ($)",
                "price_per_sqft_label": "Price per sq ft",
                "hoa_label": "HOA Fees",
                "property_tax_label": "Annual Property Tax",
                "mls_label": "MLS Number",
                "school_district_label": "School District",
                "year_built_label": "Year Built"
            }
        else:
            return {
                "area_label": "Area",
                "price_label": "Price",
                "price_per_sqft_label": "Price per unit area"
            }

    def get_measurement_conversion(
        self,
        value: float,
        from_system: str,
        to_system: str,
        unit_type: str
    ) -> float:
        """Convert between metric and imperial"""
        if from_system == to_system:
            return value

        if unit_type == "area":
            if from_system == "metric" and to_system == "imperial":
                # m² to sq ft
                return value * 10.764
            elif from_system == "imperial" and to_system == "metric":
                # sq ft to m²
                return value / 10.764

        elif unit_type == "distance":
            if from_system == "metric" and to_system == "imperial":
                # km to miles
                return value * 0.621371
            elif from_system == "imperial" and to_system == "metric":
                # miles to km
                return value / 0.621371

        return value


# Global instance
region_manager = RegionManager()
