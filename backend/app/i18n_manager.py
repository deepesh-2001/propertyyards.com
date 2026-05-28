"""
Internationalization (i18n) Manager
Multi-language support with translation, formatting, and localization
"""
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    HINDI = "hi"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    CHINESE_SIMPLIFIED = "zh_CN"
    CHINESE_TRADITIONAL = "zh_TW"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    ITALIAN = "it"
    DUTCH = "nl"
    TURKISH = "tr"
    VIETNAMESE = "vi"
    THAI = "th"
    INDONESIAN = "id"
    MALAY = "ms"


@dataclass
class LocaleConfig:
    """Locale configuration"""
    language: Language
    currency: str
    timezone: str
    date_format: str
    time_format: str
    number_format: str
    first_day_of_week: int  # 0=Monday, 6=Sunday
    measurement_system: str  # metric/imperial


class I18nManager:
    """Internationalization manager"""

    # Default translations (embedded for core messages)
    DEFAULT_TRANSLATIONS = {
        "en": {
            "welcome": "Welcome to PropertyYards",
            "login": "Login",
            "register": "Register",
            "property": "Property",
            "search": "Search",
            "price": "Price",
            "bedrooms": "Bedrooms",
            "bathrooms": "Bathrooms",
            "area": "Area",
            "location": "Location",
            "contact": "Contact",
            "send": "Send",
            "cancel": "Cancel",
            "save": "Save",
            "delete": "Delete",
            "edit": "Edit",
            "view": "View",
            "loading": "Loading...",
            "error": "Error",
            "success": "Success",
            "not_found": "Not Found",
            "unauthorized": "Unauthorized",
            "forbidden": "Forbidden",
            "invalid_input": "Invalid Input",
            "required_field": "This field is required",
            "invalid_email": "Invalid email address",
            "invalid_phone": "Invalid phone number",
            "password_too_short": "Password must be at least 8 characters",
            "property_listed": "Property listed successfully",
            "inquiry_sent": "Inquiry sent successfully",
            "profile_updated": "Profile updated successfully",
            "logged_in": "Logged in successfully",
            "logged_out": "Logged out successfully",
            "account_created": "Account created successfully",
            "verification_sent": "Verification email sent",
            "password_reset": "Password reset successfully",
            "payment_successful": "Payment successful",
            "payment_failed": "Payment failed",
            "commission_paid": "Commission paid",
            "salary_processed": "Salary processed",
            "form16_generated": "Form-16 generated",
            "newsletter_subscribed": "Newsletter subscribed",
            "alerts_enabled": "Alerts enabled",
            "property_saved": "Property saved",
            "property_removed": "Property removed from favorites",
            "cache_cleared": "Cache cleared successfully",
            "ai_image_generated": "AI image generated",
            "article_published": "Article published",
            "social_post_scheduled": "Social post scheduled",
        },
        "hi": {
            "welcome": "PropertyYards में आपका स्वागत है",
            "login": "लॉग इन",
            "register": "रजिस्टर",
            "property": "संपत्ति",
            "search": "खोजें",
            "price": "कीमत",
            "bedrooms": "बेडरूम",
            "bathrooms": "बाथरूम",
            "area": "क्षेत्र",
            "location": "स्थान",
            "contact": "संपर्क",
            "send": "भेजें",
            "cancel": "रद्द करें",
            "save": "सहेजें",
            "delete": "हटाएं",
            "edit": "संपादित करें",
            "view": "देखें",
            "loading": "लोड हो रहा है...",
            "error": "त्रुटि",
            "success": "सफल",
            "not_found": "नहीं मिला",
            "unauthorized": "अनधिकृत",
            "forbidden": "प्रतिबंधित",
            "invalid_input": "अमान्य इनपुट",
            "required_field": "यह फ़ील्ड आवश्यक है",
            "invalid_email": "अमान्य ईमेल पता",
            "invalid_phone": "अमान्य फोन नंबर",
            "password_too_short": "पासवर्ड कम से कम 8 अक्षरों का होना चाहिए",
            "property_listed": "संपत्ति सफलतापूर्वक सूचीबद्ध",
            "inquiry_sent": "पूछताछ सफलतापूर्वक भेजी गई",
            "profile_updated": "प्रोफ़ाइल सफलतापूर्वक अपडेट की गई",
            "logged_in": "सफलतापूर्वक लॉग इन किया",
            "logged_out": "सफलतापूर्वक लॉग आउट किया",
            "account_created": "खाता सफलतापूर्वक बनाया गया",
            "verification_sent": "सत्यापन ईमेल भेजा गया",
            "password_reset": "पासवर्ड सफलतापूर्वक रीसेट किया गया",
            "payment_successful": "भुगतान सफल",
            "payment_failed": "भुगतान विफल",
            "commission_paid": "कमीशन का भुगतान किया गया",
            "salary_processed": "वेतन संसाधित",
            "form16_generated": "Form-16 जनरेट किया गया",
            "newsletter_subscribed": "न्यूज़लेटर सदस्यता ली गई",
            "alerts_enabled": "अलर्ट सक्षम किए गए",
            "property_saved": "संपत्ति सहेजी गई",
            "property_removed": "पसंदीदा से संपत्ति हटाई गई",
            "cache_cleared": "कैश सफलतापूर्वक साफ़ किया गया",
            "ai_image_generated": "AI छवि जनरेट की गई",
            "article_published": "लेख प्रकाशित",
            "social_post_scheduled": "सोशल पोस्ट शेड्यूल किया गया",
        },
        "es": {
            "welcome": "Bienvenido a PropertyYards",
            "login": "Iniciar sesión",
            "register": "Registrarse",
            "property": "Propiedad",
            "search": "Buscar",
            "price": "Precio",
            "bedrooms": "Dormitorios",
            "bathrooms": "Baños",
            "area": "Área",
            "location": "Ubicación",
            "contact": "Contacto",
            "send": "Enviar",
            "cancel": "Cancelar",
            "save": "Guardar",
            "delete": "Eliminar",
            "edit": "Editar",
            "view": "Ver",
            "loading": "Cargando...",
            "error": "Error",
            "success": "Éxito",
            "not_found": "No encontrado",
            "unauthorized": "No autorizado",
            "forbidden": "Prohibido",
            "invalid_input": "Entrada inválida",
            "required_field": "Este campo es obligatorio",
            "invalid_email": "Dirección de correo inválida",
            "invalid_phone": "Número de teléfono inválido",
            "password_too_short": "La contraseña debe tener al menos 8 caracteres",
            "property_listed": "Propiedad listada exitosamente",
            "inquiry_sent": "Consulta enviada exitosamente",
            "profile_updated": "Perfil actualizado exitosamente",
            "logged_in": "Sesión iniciada exitosamente",
            "logged_out": "Sesión cerrada exitosamente",
            "account_created": "Cuenta creada exitosamente",
            "verification_sent": "Correo de verificación enviado",
            "password_reset": "Contraseña restablecida exitosamente",
            "payment_successful": "Pago exitoso",
            "payment_failed": "Pago fallido",
            "commission_paid": "Comisión pagada",
            "salary_processed": "Salario procesado",
            "form16_generated": "Form-16 generado",
            "newsletter_subscribed": "Suscripción al boletín confirmada",
            "alerts_enabled": "Alertas habilitadas",
            "property_saved": "Propiedad guardada",
            "property_removed": "Propiedad eliminada de favoritos",
            "cache_cleared": "Caché limpiado exitosamente",
            "ai_image_generated": "Imagen AI generada",
            "article_published": "Artículo publicado",
            "social_post_scheduled": "Publicación social programada",
        },
    }

    # Locale configurations
    LOCALE_CONFIGS = {
        "en": LocaleConfig(
            language=Language.ENGLISH,
            currency="USD",
            timezone="UTC",
            date_format="%Y-%m-%d",
            time_format="%H:%M:%S",
            number_format="#,##0.00",
            first_day_of_week=0,
            measurement_system="imperial"
        ),
        "hi": LocaleConfig(
            language=Language.HINDI,
            currency="INR",
            timezone="Asia/Kolkata",
            date_format="%d-%m-%Y",
            time_format="%H:%M:%S",
            number_format="#,##,##0.00",
            first_day_of_week=0,
            measurement_system="metric"
        ),
        "es": LocaleConfig(
            language=Language.SPANISH,
            currency="EUR",
            timezone="Europe/Madrid",
            date_format="%d/%m/%Y",
            time_format="%H:%M:%S",
            number_format="#.##0,00",
            first_day_of_week=1,
            measurement_system="metric"
        ),
        "fr": LocaleConfig(
            language=Language.FRENCH,
            currency="EUR",
            timezone="Europe/Paris",
            date_format="%d/%m/%Y",
            time_format="%H:%M:%S",
            number_format="#.##0,00",
            first_day_of_week=1,
            measurement_system="metric"
        ),
        "de": LocaleConfig(
            language=Language.GERMAN,
            currency="EUR",
            timezone="Europe/Berlin",
            date_format="%d.%m.%Y",
            time_format="%H:%M:%S",
            number_format="#.##0,00",
            first_day_of_week=1,
            measurement_system="metric"
        ),
        "zh_CN": LocaleConfig(
            language=Language.CHINESE_SIMPLIFIED,
            currency="CNY",
            timezone="Asia/Shanghai",
            date_format="%Y年%m月%d日",
            time_format="%H:%M:%S",
            number_format="#,##0.00",
            first_day_of_week=1,
            measurement_system="metric"
        ),
        "ja": LocaleConfig(
            language=Language.JAPANESE,
            currency="JPY",
            timezone="Asia/Tokyo",
            date_format="%Y/%m/%d",
            time_format="%H:%M:%S",
            number_format="#,##0",
            first_day_of_week=0,
            measurement_system="metric"
        ),
        "ar": LocaleConfig(
            language=Language.ARABIC,
            currency="SAR",
            timezone="Asia/Riyadh",
            date_format="%d/%m/%Y",
            time_format="%H:%M:%S",
            number_format="#,##0.00",
            first_day_of_week=6,
            measurement_system="metric"
        ),
        "pt": LocaleConfig(
            language=Language.PORTUGUESE,
            currency="BRL",
            timezone="America/Sao_Paulo",
            date_format="%d/%m/%Y",
            time_format="%H:%M:%S",
            number_format="#.##0,00",
            first_day_of_week=0,
            measurement_system="metric"
        ),
    }

    def __init__(self):
        self.translations = dict(self.DEFAULT_TRANSLATIONS)
        self.current_locale = "en"
        self.user_locales: Dict[str, str] = {}  # user_id -> locale

    def set_locale(self, locale_code: str) -> bool:
        """Set current locale"""
        if locale_code in self.translations:
            self.current_locale = locale_code
            return True
        return False

    def get_locale(self) -> str:
        """Get current locale"""
        return self.current_locale

    def set_user_locale(self, user_id: str, locale_code: str):
        """Set locale for specific user"""
        self.user_locales[user_id] = locale_code

    def get_user_locale(self, user_id: str) -> str:
        """Get locale for specific user"""
        return self.user_locales.get(user_id, self.current_locale)

    def translate(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        """Translate a key to the specified locale"""
        target_locale = locale or self.current_locale

        # Get translation
        translation = self.translations.get(target_locale, {}).get(key)

        # Fallback to English
        if not translation:
            translation = self.translations.get("en", {}).get(key, key)

        # Format with kwargs
        try:
            return translation.format(**kwargs)
        except:
            return translation

    def t(self, key: str, **kwargs) -> str:
        """Shorthand for translate"""
        return self.translate(key, **kwargs)

    def add_translation(self, locale: str, key: str, value: str):
        """Add a new translation"""
        if locale not in self.translations:
            self.translations[locale] = {}
        self.translations[locale][key] = value

    def load_translations_from_file(self, file_path: str, locale: str):
        """Load translations from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if locale not in self.translations:
                    self.translations[locale] = {}
                self.translations[locale].update(data)
        except Exception as e:
            logger.error(f"Failed to load translations: {e}")

    def get_locale_config(self, locale: Optional[str] = None) -> LocaleConfig:
        """Get locale configuration"""
        target = locale or self.current_locale
        return self.LOCALE_CONFIGS.get(target, self.LOCALE_CONFIGS["en"])

    def format_date(self, date: datetime, locale: Optional[str] = None) -> str:
        """Format date according to locale"""
        config = self.get_locale_config(locale)
        return date.strftime(config.date_format)

    def format_time(self, time: datetime, locale: Optional[str] = None) -> str:
        """Format time according to locale"""
        config = self.get_locale_config(locale)
        return time.strftime(config.time_format)

    def format_datetime(self, dt: datetime, locale: Optional[str] = None) -> str:
        """Format datetime according to locale"""
        config = self.get_locale_config(locale)
        return dt.strftime(f"{config.date_format} {config.time_format}")

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages"""
        return [
            {"code": lang.value, "name": lang.name.replace("_", " ")}
            for lang in Language
        ]

    def is_rtl(self, locale: Optional[str] = None) -> bool:
        """Check if locale is right-to-left"""
        target = locale or self.current_locale
        return target in ["ar", "he", "ur"]


# Global i18n instance
i18n = I18nManager()


def translate(key: str, **kwargs) -> str:
    """Global translate function"""
    return i18n.translate(key, **kwargs)


def t(key: str, **kwargs) -> str:
    """Global shorthand translate"""
    return i18n.t(key, **kwargs)
