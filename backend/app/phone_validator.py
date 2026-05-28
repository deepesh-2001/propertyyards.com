"""
Global Phone Number Validator
Validate and format phone numbers from all countries
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PhoneType(Enum):
    MOBILE = "mobile"
    LANDLINE = "landline"
    TOLL_FREE = "toll_free"
    PREMIUM = "premium"
    VOIP = "voip"
    UNKNOWN = "unknown"


@dataclass
class CountryPhoneFormat:
    """Phone format for a country"""
    country_code: str
    country_name: str
    phone_code: str
    formats: List[str]  # Valid formats with # as digit placeholder
    min_length: int
    max_length: int
    mobile_prefixes: List[str]
    area_code_required: bool
    trunk_prefix: str  # e.g., "0" for UK
    international_prefix: str  # e.g., "00" or "011"


class GlobalPhoneValidator:
    """Validate and format phone numbers globally"""

    # Country phone formats
    COUNTRY_FORMATS = {
        "US": CountryPhoneFormat(
            country_code="US",
            country_name="United States",
            phone_code="+1",
            formats=["(###) ###-####", "###-###-####", "###.###.####", "##########"],
            min_length=10,
            max_length=10,
            mobile_prefixes=["200", "201", "202", "203", "205", "206", "207", "208", "209",
                            "210", "212", "213", "214", "215", "216", "217", "218", "219",
                            "220", "223", "224", "225", "227", "228", "229", "231", "234",
                            "239", "240", "242", "248", "251", "252", "253", "254", "256",
                            "260", "262", "267", "269", "270", "272", "274", "276", "281",
                            "283", "301", "302", "303", "304", "305", "307", "308", "309",
                            "310", "312", "313", "314", "315", "316", "317", "318", "319",
                            "320", "321", "323", "325", "327", "330", "331", "332", "334",
                            "336", "337", "339", "341", "346", "347", "351", "352", "360",
                            "361", "364", "369", "380", "385", "386", "401", "402", "404",
                            "405", "406", "407", "408", "409", "410", "412", "413", "414",
                            "415", "417", "419", "423", "424", "425", "430", "432", "434",
                            "435", "440", "442", "443", "445", "447", "458", "469", "470",
                            "475", "478", "479", "480", "484", "501", "502", "503", "504",
                            "505", "507", "508", "509", "510", "512", "513", "515", "516",
                            "517", "518", "520", "530", "531", "534", "539", "540", "541",
                            "551", "559", "561", "562", "563", "564", "567", "570", "571",
                            "572", "573", "574", "575", "580", "582", "585", "586", "601",
                            "602", "603", "605", "606", "607", "608", "609", "610", "612",
                            "614", "615", "616", "617", "618", "619", "620", "623", "626",
                            "628", "629", "630", "631", "636", "641", "646", "650", "651",
                            "657", "660", "661", "662", "667", "669", "678", "681", "682",
                            "684", "701", "702", "703", "704", "706", "707", "708", "712",
                            "713", "714", "715", "716", "717", "718", "719", "720", "724",
                            "725", "727", "731", "732", "734", "737", "740", "747", "754",
                            "757", "760", "762", "763", "765", "769", "770", "772", "773",
                            "774", "775", "779", "781", "785", "786", "801", "802", "803",
                            "804", "805", "806", "808", "810", "812", "813", "814", "815",
                            "816", "817", "818", "828", "830", "831", "832", "843", "845",
                            "847", "848", "850", "856", "857", "858", "859", "860", "862",
                            "863", "864", "865", "870", "872", "878", "901", "903", "904",
                            "906", "907", "908", "909", "910", "912", "913", "914", "915",
                            "916", "917", "918", "919", "920", "925", "928", "931", "936",
                            "937", "940", "941", "945", "947", "949", "951", "952", "954",
                            "956", "959", "970", "971", "972", "973", "975", "978", "979",
                            "980", "984", "985", "989"],
            area_code_required=True,
            trunk_prefix="1",
            international_prefix="011"
        ),
        "IN": CountryPhoneFormat(
            country_code="IN",
            country_name="India",
            phone_code="+91",
            formats=["##### #####", "##########", "+91 ##### #####"],
            min_length=10,
            max_length=10,
            mobile_prefixes=["6", "7", "8", "9"],
            area_code_required=False,
            trunk_prefix="0",
            international_prefix="00"
        ),
        "GB": CountryPhoneFormat(
            country_code="GB",
            country_name="United Kingdom",
            phone_code="+44",
            formats=["#### ######", "##########"],
            min_length=10,
            max_length=11,
            mobile_prefixes=["71", "72", "73", "74", "75", "76", "77", "78", "79"],
            area_code_required=True,
            trunk_prefix="0",
            international_prefix="00"
        ),
        "CA": CountryPhoneFormat(
            country_code="CA",
            country_name="Canada",
            phone_code="+1",
            formats=["(###) ###-####", "###-###-####"],
            min_length=10,
            max_length=10,
            mobile_prefixes=["204", "226", "236", "249", "250", "289", "306", "343", "365",
                            "403", "416", "418", "431", "437", "438", "450", "506", "514",
                            "519", "579", "581", "587", "604", "613", "639", "647", "705",
                            "709", "778", "780", "807", "819", "867", "873", "902", "905"],
            area_code_required=True,
            trunk_prefix="1",
            international_prefix="011"
        ),
        "AU": CountryPhoneFormat(
            country_code="AU",
            country_name="Australia",
            phone_code="+61",
            formats=["#### ####", "## #### ####"],
            min_length=9,
            max_length=10,
            mobile_prefixes=["4"],
            area_code_required=True,
            trunk_prefix="0",
            international_prefix="0011"
        ),
        "DE": CountryPhoneFormat(
            country_code="DE",
            country_name="Germany",
            phone_code="+49",
            formats=["### #######", "#### ########"],
            min_length=10,
            max_length=11,
            mobile_prefixes=["151", "152", "153", "155", "156", "157", "158", "159",
                            "160", "161", "162", "163", "164", "165", "166", "167", "168", "169",
                            "170", "171", "172", "173", "174", "175", "176", "177", "178", "179"],
            area_code_required=True,
            trunk_prefix="0",
            international_prefix="00"
        ),
        "FR": CountryPhoneFormat(
            country_code="FR",
            country_name="France",
            phone_code="+33",
            formats=["# ## ## ## ##"],
            min_length=9,
            max_length=9,
            mobile_prefixes=["6", "7"],
            area_code_required=False,
            trunk_prefix="0",
            international_prefix="00"
        ),
        "CN": CountryPhoneFormat(
            country_code="CN",
            country_name="China",
            phone_code="+86",
            formats=["### #### ####", "## ##### #####"],
            min_length=11,
            max_length=11,
            mobile_prefixes=["13", "14", "15", "16", "17", "18", "19"],
            area_code_required=False,
            trunk_prefix="0",
            international_prefix="00"
        ),
        "JP": CountryPhoneFormat(
            country_code="JP",
            country_name="Japan",
            phone_code="+81",
            formats=["##-####-####", "###-###-####"],
            min_length=10,
            max_length=10,
            mobile_prefixes=["70", "80", "90"],
            area_code_required=True,
            trunk_prefix="0",
            international_prefix="010"
        ),
        "BR": CountryPhoneFormat(
            country_code="BR",
            country_name="Brazil",
            phone_code="+55",
            formats=["(##) #####-####", "## #####-####"],
            min_length=11,
            max_length=11,
            mobile_prefixes=["9"],
            area_code_required=True,
            trunk_prefix="0",
            international_prefix="00"
        ),
        "MX": CountryPhoneFormat(
            country_code="MX",
            country_name="Mexico",
            phone_code="+52",
            formats=["### ### ####", "## #### ####"],
            min_length=10,
            max_length=10,
            mobile_prefixes=["1"],
            area_code_required=True,
            trunk_prefix="01",
            international_prefix="00"
        ),
        "RU": CountryPhoneFormat(
            country_code="RU",
            country_name="Russia",
            phone_code="+7",
            formats=["(###) ###-##-##", "##########"],
            min_length=10,
            max_length=10,
            mobile_prefixes=["9"],
            area_code_required=True,
            trunk_prefix="8",
            international_prefix="810"
        ),
        "ZA": CountryPhoneFormat(
            country_code="ZA",
            country_name="South Africa",
            phone_code="+27",
            formats=["## ### ####"],
            min_length=9,
            max_length=9,
            mobile_prefixes=["6", "7", "8"],
            area_code_required=True,
            trunk_prefix="0",
            international_prefix="00"
        ),
        "AE": CountryPhoneFormat(
            country_code="AE",
            country_name="United Arab Emirates",
            phone_code="+971",
            formats=["## ### ####"],
            min_length=9,
            max_length=9,
            mobile_prefixes=["5"],
            area_code_required=False,
            trunk_prefix="0",
            international_prefix="00"
        ),
        "SA": CountryPhoneFormat(
            country_code="SA",
            country_name="Saudi Arabia",
            phone_code="+966",
            formats=["# ### ####"],
            min_length=9,
            max_length=9,
            mobile_prefixes=["5"],
            area_code_required=False,
            trunk_prefix="0",
            international_prefix="00"
        ),
        "SG": CountryPhoneFormat(
            country_code="SG",
            country_name="Singapore",
            phone_code="+65",
            formats=["#### ####"],
            min_length=8,
            max_length=8,
            mobile_prefixes=["8", "9"],
            area_code_required=False,
            trunk_prefix="",
            international_prefix="001"
        ),
        "HK": CountryPhoneFormat(
            country_code="HK",
            country_name="Hong Kong",
            phone_code="+852",
            formats=["#### ####"],
            min_length=8,
            max_length=8,
            mobile_prefixes=["4", "5", "6", "9"],
            area_code_required=False,
            trunk_prefix="",
            international_prefix="001"
        ),
    }

    # Country code to format mapping
    PHONE_CODE_MAP = {
        "+1": ["US", "CA"],
        "+7": ["RU", "KZ"],
        "+20": ["EG"],
        "+27": ["ZA"],
        "+30": ["GR"],
        "+31": ["NL"],
        "+32": ["BE"],
        "+33": ["FR"],
        "+34": ["ES"],
        "+36": ["HU"],
        "+39": ["IT"],
        "+40": ["RO"],
        "+41": ["CH"],
        "+43": ["AT"],
        "+44": ["GB"],
        "+45": ["DK"],
        "+46": ["SE"],
        "+47": ["NO"],
        "+48": ["PL"],
        "+49": ["DE"],
        "+51": ["PE"],
        "+52": ["MX"],
        "+53": ["CU"],
        "+54": ["AR"],
        "+55": ["BR"],
        "+56": ["CL"],
        "+57": ["CO"],
        "+58": ["VE"],
        "+60": ["MY"],
        "+61": ["AU", "CC", "CX"],
        "+62": ["ID"],
        "+63": ["PH"],
        "+64": ["NZ"],
        "+65": ["SG"],
        "+66": ["TH"],
        "+81": ["JP"],
        "+82": ["KR"],
        "+84": ["VN"],
        "+86": ["CN"],
        "+90": ["TR"],
        "+91": ["IN"],
        "+92": ["PK"],
        "+93": ["AF"],
        "+94": ["LK"],
        "+95": ["MM"],
        "+98": ["IR"],
        "+211": ["SS"],
        "+212": ["MA", "EH"],
        "+213": ["DZ"],
        "+216": ["TN"],
        "+218": ["LY"],
        "+220": ["GM"],
        "+221": ["SN"],
        "+222": ["MR"],
        "+223": ["ML"],
        "+224": ["GN"],
        "+225": ["CI"],
        "+226": ["BF"],
        "+227": ["NE"],
        "+228": ["TG"],
        "+229": ["BJ"],
        "+230": ["MU"],
        "+231": ["LR"],
        "+232": ["SL"],
        "+233": ["GH"],
        "+234": ["NG"],
        "+235": ["TD"],
        "+236": ["CF"],
        "+237": ["CM"],
        "+238": ["CV"],
        "+239": ["ST"],
        "+240": ["GQ"],
        "+241": ["GA"],
        "+242": ["CG"],
        "+243": ["CD"],
        "+244": ["AO"],
        "+245": ["GW"],
        "+246": ["IO"],
        "+248": ["SC"],
        "+249": ["SD"],
        "+250": ["RW"],
        "+251": ["ET"],
        "+252": ["SO"],
        "+253": ["DJ"],
        "+254": ["KE"],
        "+255": ["TZ"],
        "+256": ["UG"],
        "+257": ["BI"],
        "+258": ["MZ"],
        "+260": ["ZM"],
        "+261": ["MG"],
        "+262": ["RE", "YT"],
        "+263": ["ZW"],
        "+264": ["NA"],
        "+265": ["MW"],
        "+266": ["LS"],
        "+267": ["BW"],
        "+268": ["SZ"],
        "+269": ["KM"],
        "+290": ["SH"],
        "+291": ["ER"],
        "+297": ["AW"],
        "+298": ["FO"],
        "+299": ["GL"],
        "+350": ["GI"],
        "+351": ["PT"],
        "+352": ["LU"],
        "+353": ["IE"],
        "+354": ["IS"],
        "+355": ["AL"],
        "+356": ["MT"],
        "+357": ["CY"],
        "+358": ["FI", "AX"],
        "+359": ["BG"],
        "+370": ["LT"],
        "+371": ["LV"],
        "+372": ["EE"],
        "+373": ["MD"],
        "+374": ["AM"],
        "+375": ["BY"],
        "+376": ["AD"],
        "+377": ["MC"],
        "+378": ["SM"],
        "+379": ["VA"],
        "+380": ["UA"],
        "+381": ["RS"],
        "+382": ["ME"],
        "+383": ["XK"],
        "+385": ["HR"],
        "+386": ["SI"],
        "+387": ["BA"],
        "+389": ["MK"],
        "+420": ["CZ"],
        "+421": ["SK"],
        "+423": ["LI"],
        "+500": ["FK"],
        "+501": ["BZ"],
        "+502": ["GT"],
        "+503": ["SV"],
        "+504": ["HN"],
        "+505": ["NI"],
        "+506": ["CR"],
        "+507": ["PA"],
        "+508": ["PM"],
        "+509": ["HT"],
        "+590": ["GP", "BL", "MF"],
        "+591": ["BO"],
        "+592": ["GY"],
        "+593": ["EC"],
        "+594": ["GF"],
        "+595": ["PY"],
        "+596": ["MQ"],
        "+597": ["SR"],
        "+598": ["UY"],
        "+599": ["CW", "BQ"],
        "+670": ["TL"],
        "+672": ["NF"],
        "+673": ["BN"],
        "+674": ["NR"],
        "+675": ["PG"],
        "+676": ["TO"],
        "+677": ["SB"],
        "+678": ["VU"],
        "+679": ["FJ"],
        "+680": ["PW"],
        "+681": ["WF"],
        "+682": ["CK"],
        "+683": ["NU"],
        "+685": ["WS"],
        "+686": ["KI"],
        "+687": ["NC"],
        "+688": ["TV"],
        "+689": ["PF"],
        "+690": ["TK"],
        "+691": ["FM"],
        "+692": ["MH"],
        "+850": ["KP"],
        "+852": ["HK"],
        "+853": ["MO"],
        "+855": ["KH"],
        "+856": ["LA"],
        "+880": ["BD"],
        "+886": ["TW"],
        "+960": ["MV"],
        "+961": ["LB"],
        "+962": ["JO"],
        "+963": ["SY"],
        "+964": ["IQ"],
        "+965": ["KW"],
        "+966": ["SA"],
        "+967": ["YE"],
        "+968": ["OM"],
        "+970": ["PS"],
        "+971": ["AE"],
        "+972": ["IL"],
        "+973": ["BH"],
        "+974": ["QA"],
        "+975": ["BT"],
        "+976": ["MN"],
        "+977": ["NP"],
        "+992": ["TJ"],
        "+993": ["TM"],
        "+994": ["AZ"],
        "+995": ["GE"],
        "+996": ["KG"],
        "+998": ["UZ"],
        "+1242": ["BS"],
        "+1246": ["BB"],
        "+1264": ["AI"],
        "+1268": ["AG"],
        "+1284": ["VG"],
        "+1340": ["VI"],
        "+1345": ["KY"],
        "+1441": ["BM"],
        "+1473": ["GD"],
        "+1649": ["TC"],
        "+1664": ["MS"],
        "+1670": ["MP"],
        "+1671": ["GU"],
        "+1684": ["AS"],
        "+1758": ["LC"],
        "+1767": ["DM"],
        "+1784": ["VC"],
        "+1809": ["DO"],
        "+1868": ["TT"],
        "+1869": ["KN"],
        "+1876": ["JM"],
        "+1939": ["PR"],
    }

    def __init__(self):
        self.user_phone_preferences: Dict[str, str] = {}  # user_id -> country_code

    def validate_phone(
        self,
        phone: str,
        country_code: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[CountryPhoneFormat]]:
        """
        Validate phone number
        Returns: (is_valid, error_message, country_format)
        """
        if not phone:
            return False, "Phone number is required", None

        # Clean the phone number
        cleaned = self._clean_phone(phone)

        # Try to detect country if not provided
        if not country_code:
            country_code = self._detect_country(cleaned)

        if not country_code:
            return False, "Could not detect country code", None

        country_format = self.COUNTRY_FORMATS.get(country_code)
        if not country_format:
            return False, f"Unsupported country: {country_code}", None

        # Remove country code and trunk prefix
        number_without_code = self._remove_country_code(cleaned, country_format.phone_code)
        number_without_code = self._remove_trunk_prefix(number_without_code, country_format.trunk_prefix)

        # Check length
        if len(number_without_code) < country_format.min_length:
            return False, f"Phone number too short (min {country_format.min_length} digits)", None

        if len(number_without_code) > country_format.max_length:
            return False, f"Phone number too long (max {country_format.max_length} digits)", None

        # Check if mobile (if we care about that)
        is_mobile = self._is_mobile(number_without_code, country_format)

        return True, None, country_format

    def format_phone(
        self,
        phone: str,
        country_code: str,
        format_type: str = "international"
    ) -> str:
        """Format phone number"""
        cleaned = self._clean_phone(phone)
        country_format = self.COUNTRY_FORMATS.get(country_code)

        if not country_format:
            return phone

        # Remove country code
        number = self._remove_country_code(cleaned, country_format.phone_code)
        number = self._remove_trunk_prefix(number, country_format.trunk_prefix)

        if format_type == "international":
            return f"{country_format.phone_code} {number}"
        elif format_type == "national":
            if country_format.trunk_prefix:
                return f"{country_format.trunk_prefix}{number}"
            return number
        elif format_type == "e164":
            return f"{country_format.phone_code.replace('+', '')}{number}"

        return phone

    def _clean_phone(self, phone: str) -> str:
        """Remove all non-digit characters except +"""
        # Keep only digits and +
        cleaned = re.sub(r'[^\d+]', '', phone)
        return cleaned

    def _detect_country(self, phone: str) -> Optional[str]:
        """Detect country from phone number"""
        # Check for + prefix
        if phone.startswith('+'):
            # Try to match country code
            for code, countries in sorted(self.PHONE_CODE_MAP.items(), key=lambda x: -len(x[0])):
                if phone.startswith(code):
                    # Return first country for this code
                    return countries[0]
            return None
        else:
            # Assume it might have country code without +
            # Default to US/Canada if starts with 1
            if phone.startswith('1') and len(phone) == 11:
                return "US"
            # Try other patterns
            return None

    def _remove_country_code(self, phone: str, country_code: str) -> str:
        """Remove country code from phone"""
        code_without_plus = country_code.replace('+', '')

        if phone.startswith('+' + code_without_plus):
            return phone[len(country_code):]
        elif phone.startswith(code_without_plus):
            return phone[len(code_without_plus):]

        return phone

    def _remove_trunk_prefix(self, phone: str, trunk_prefix: str) -> str:
        """Remove trunk prefix from phone"""
        if trunk_prefix and phone.startswith(trunk_prefix):
            return phone[len(trunk_prefix):]
        return phone

    def _is_mobile(self, number: str, country_format: CountryPhoneFormat) -> bool:
        """Check if number is mobile"""
        for prefix in country_format.mobile_prefixes:
            if number.startswith(prefix):
                return True
        return False

    def get_phone_type(self, phone: str, country_code: str) -> PhoneType:
        """Determine phone number type"""
        country_format = self.COUNTRY_FORMATS.get(country_code)
        if not country_format:
            return PhoneType.UNKNOWN

        cleaned = self._clean_phone(phone)
        number = self._remove_country_code(cleaned, country_format.phone_code)
        number = self._remove_trunk_prefix(number, country_format.trunk_prefix)

        if self._is_mobile(number, country_format):
            return PhoneType.MOBILE

        # Check for toll-free patterns
        if country_code == "US" or country_code == "CA":
            if number.startswith("800") or number.startswith("888") or \
               number.startswith("877") or number.startswith("866") or \
               number.startswith("855") or number.startswith("844"):
                return PhoneType.TOLL_FREE

        return PhoneType.LANDLINE

    def set_user_country(self, user_id: str, country_code: str):
        """Set default country for user"""
        self.user_phone_preferences[user_id] = country_code

    def get_user_country(self, user_id: str) -> Optional[str]:
        """Get user's default country"""
        return self.user_phone_preferences.get(user_id)

    def get_supported_countries(self) -> List[Dict[str, str]]:
        """Get list of supported countries"""
        return [
            {
                "code": code,
                "name": format.country_name,
                "phone_code": format.phone_code
            }
            for code, format in sorted(self.COUNTRY_FORMATS.items())
        ]

    def parse_phone(self, phone: str) -> Dict[str, Any]:
        """Parse phone number and return details"""
        is_valid, error, country_format = self.validate_phone(phone)

        result = {
            "is_valid": is_valid,
            "error": error,
            "original": phone,
        }

        if is_valid and country_format:
            cleaned = self._clean_phone(phone)
            number = self._remove_country_code(cleaned, country_format.phone_code)
            number = self._remove_trunk_prefix(number, country_format.trunk_prefix)

            result.update({
                "country_code": country_format.country_code,
                "country_name": country_format.country_name,
                "phone_code": country_format.phone_code,
                "number": number,
                "formatted_international": self.format_phone(phone, country_format.country_code, "international"),
                "formatted_national": self.format_phone(phone, country_format.country_code, "national"),
                "type": self.get_phone_type(phone, country_format.country_code).value,
                "is_mobile": self._is_mobile(number, country_format)
            })

        return result


# Global instance
phone_validator = GlobalPhoneValidator()


def validate_phone(phone: str, country_code: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Quick validation function"""
    is_valid, error, _ = phone_validator.validate_phone(phone, country_code)
    return is_valid, error


def format_phone(phone: str, country_code: str, format_type: str = "international") -> str:
    """Quick format function"""
    return phone_validator.format_phone(phone, country_code, format_type)
