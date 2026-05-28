"""
Currency Manager
Multi-currency support with real-time conversion rates
"""
import asyncio
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class Currency:
    """Currency definition"""
    code: str
    name: str
    symbol: str
    symbol_position: str  # 'before' or 'after'
    decimal_places: int
    thousands_separator: str
    decimal_separator: str
    is_crypto: bool = False


@dataclass
class ExchangeRate:
    """Exchange rate data"""
    from_currency: str
    to_currency: str
    rate: Decimal
    timestamp: datetime
    source: str


class CurrencyManager:
    """Multi-currency management with conversion"""

    # Default currencies
    CURRENCIES = {
        "USD": Currency("USD", "US Dollar", "$", "before", 2, ",", "."),
        "EUR": Currency("EUR", "Euro", "€", "before", 2, ".", ","),
        "GBP": Currency("GBP", "British Pound", "£", "before", 2, ",", "."),
        "INR": Currency("INR", "Indian Rupee", "₹", "before", 2, ",", "."),
        "JPY": Currency("JPY", "Japanese Yen", "¥", "before", 0, ",", "."),
        "CNY": Currency("CNY", "Chinese Yuan", "¥", "before", 2, ",", "."),
        "AUD": Currency("AUD", "Australian Dollar", "A$", "before", 2, ",", "."),
        "CAD": Currency("CAD", "Canadian Dollar", "C$", "before", 2, ",", "."),
        "CHF": Currency("CHF", "Swiss Franc", "CHF", "before", 2, "'", "."),
        "SEK": Currency("SEK", "Swedish Krona", "kr", "after", 2, " ", ","),
        "NZD": Currency("NZD", "New Zealand Dollar", "NZ$", "before", 2, ",", "."),
        "SGD": Currency("SGD", "Singapore Dollar", "S$", "before", 2, ",", "."),
        "HKD": Currency("HKD", "Hong Kong Dollar", "HK$", "before", 2, ",", "."),
        "KRW": Currency("KRW", "South Korean Won", "₩", "before", 0, ",", "."),
        "BRL": Currency("BRL", "Brazilian Real", "R$", "before", 2, ".", ","),
        "MXN": Currency("MXN", "Mexican Peso", "MX$", "before", 2, ",", "."),
        "ZAR": Currency("ZAR", "South African Rand", "R", "before", 2, " ", ","),
        "RUB": Currency("RUB", "Russian Ruble", "₽", "after", 2, " ", ","),
        "TRY": Currency("TRY", "Turkish Lira", "₺", "before", 2, ".", ","),
        "AED": Currency("AED", "UAE Dirham", "د.إ", "before", 2, ",", "."),
        "SAR": Currency("SAR", "Saudi Riyal", "﷼", "before", 2, ",", "."),
        "THB": Currency("THB", "Thai Baht", "฿", "before", 2, ",", "."),
        "IDR": Currency("IDR", "Indonesian Rupiah", "Rp", "before", 0, ".", ","),
        "MYR": Currency("MYR", "Malaysian Ringgit", "RM", "before", 2, ",", "."),
        "PHP": Currency("PHP", "Philippine Peso", "₱", "before", 2, ",", "."),
        "VND": Currency("VND", "Vietnamese Dong", "₫", "after", 0, ".", ","),
        "PKR": Currency("PKR", "Pakistani Rupee", "₨", "before", 2, ",", "."),
        "BDT": Currency("BDT", "Bangladeshi Taka", "৳", "before", 2, ",", "."),
        "EGP": Currency("EGP", "Egyptian Pound", "E£", "before", 2, ",", "."),
        "NGN": Currency("NGN", "Nigerian Naira", "₦", "before", 2, ",", "."),
        "KES": Currency("KES", "Kenyan Shilling", "KSh", "before", 2, ",", "."),
        # Cryptocurrencies
        "BTC": Currency("BTC", "Bitcoin", "₿", "before", 8, ",", ".", True),
        "ETH": Currency("ETH", "Ethereum", "Ξ", "before", 8, ",", ".", True),
        "USDT": Currency("USDT", "Tether", "₮", "before", 2, ",", ".", True),
        "USDC": Currency("USDC", "USD Coin", "", "before", 2, ",", ".", True),
    }

    def __init__(self):
        self.base_currency = "USD"
        self.exchange_rates: Dict[str, ExchangeRate] = {}
        self.user_currencies: Dict[str, str] = {}  # user_id -> currency
        self.last_update: Optional[datetime] = None
        self.api_key = None

    def set_api_key(self, api_key: str):
        """Set API key for exchange rate service"""
        self.api_key = api_key

    async def update_exchange_rates(self):
        """Fetch latest exchange rates"""
        if not self.api_key:
            logger.warning("No API key set for exchange rates")
            return

        try:
            url = f"https://api.exchangerate-api.com/v4/latest/{self.base_currency}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Update rates
                        timestamp = datetime.utcnow()
                        for currency_code, rate in data.get("rates", {}).items():
                            if currency_code in self.CURRENCIES:
                                self.exchange_rates[currency_code] = ExchangeRate(
                                    from_currency=self.base_currency,
                                    to_currency=currency_code,
                                    rate=Decimal(str(rate)),
                                    timestamp=timestamp,
                                    source="exchangerate-api"
                                )

                        self.last_update = timestamp
                        logger.info(f"Exchange rates updated: {len(self.exchange_rates)} currencies")

        except Exception as e:
            logger.error(f"Failed to update exchange rates: {e}")

    def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str
    ) -> Decimal:
        """Convert amount from one currency to another"""
        if from_currency == to_currency:
            return amount

        # Get rates relative to base currency
        from_rate = Decimal(1)
        to_rate = Decimal(1)

        if from_currency != self.base_currency:
            rate_obj = self.exchange_rates.get(from_currency)
            if rate_obj:
                from_rate = rate_obj.rate
            else:
                raise ValueError(f"Exchange rate not available for {from_currency}")

        if to_currency != self.base_currency:
            rate_obj = self.exchange_rates.get(to_currency)
            if rate_obj:
                to_rate = rate_obj.rate
            else:
                raise ValueError(f"Exchange rate not available for {to_currency}")

        # Convert to base, then to target
        base_amount = amount / from_rate
        converted = base_amount * to_rate

        return converted

    def format_amount(
        self,
        amount: Decimal,
        currency_code: str,
        show_symbol: bool = True
    ) -> str:
        """Format amount according to currency rules"""
        currency = self.CURRENCIES.get(currency_code)
        if not currency:
            return f"{amount} {currency_code}"

        # Format number
        quantizer = Decimal("0.1") ** currency.decimal_places
        rounded = amount.quantize(quantizer, rounding=ROUND_HALF_UP)

        # Format with separators
        str_amount = str(rounded)
        if "." in str_amount:
            integer_part, decimal_part = str_amount.split(".")
        else:
            integer_part, decimal_part = str_amount, ""

        # Add thousands separator
        if currency.thousands_separator:
            reversed_int = integer_part[::-1]
            chunks = [reversed_int[i:i+3] for i in range(0, len(reversed_int), 3)]
            integer_part = currency.thousands_separator.join(chunks)[::-1]

        # Combine
        if currency.decimal_places > 0 and decimal_part:
            formatted = f"{integer_part}{currency.decimal_separator}{decimal_part}"
        else:
            formatted = integer_part

        # Add symbol
        if show_symbol:
            if currency.symbol_position == "before":
                return f"{currency.symbol}{formatted}"
            else:
                return f"{formatted} {currency.symbol}"

        return formatted

    def get_currency(self, code: str) -> Optional[Currency]:
        """Get currency definition"""
        return self.CURRENCIES.get(code)

    def get_all_currencies(self) -> List[Currency]:
        """Get all supported currencies"""
        return list(self.CURRENCIES.values())

    def get_fiat_currencies(self) -> List[Currency]:
        """Get fiat currencies only"""
        return [c for c in self.CURRENCIES.values() if not c.is_crypto]

    def get_crypto_currencies(self) -> List[Currency]:
        """Get cryptocurrency only"""
        return [c for c in self.CURRENCIES.values() if c.is_crypto]

    def set_user_currency(self, user_id: str, currency_code: str):
        """Set preferred currency for user"""
        if currency_code in self.CURRENCIES:
            self.user_currencies[user_id] = currency_code

    def get_user_currency(self, user_id: str) -> str:
        """Get user's preferred currency"""
        return self.user_currencies.get(user_id, self.base_currency)

    def is_valid_currency(self, code: str) -> bool:
        """Check if currency code is valid"""
        return code in self.CURRENCIES

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]:
        """Get exchange rate between two currencies"""
        try:
            # Calculate cross rate
            if from_currency == self.base_currency:
                rate_obj = self.exchange_rates.get(to_currency)
                return rate_obj.rate if rate_obj else None
            elif to_currency == self.base_currency:
                rate_obj = self.exchange_rates.get(from_currency)
                return Decimal(1) / rate_obj.rate if rate_obj else None
            else:
                # Cross rate calculation
                from_rate = self.exchange_rates.get(from_currency)
                to_rate = self.exchange_rates.get(to_currency)
                if from_rate and to_rate:
                    return to_rate.rate / from_rate.rate
            return None
        except:
            return None

    def get_rate_age_minutes(self) -> Optional[int]:
        """Get age of exchange rates in minutes"""
        if self.last_update:
            delta = datetime.utcnow() - self.last_update
            return int(delta.total_seconds() / 60)
        return None


class PriceFormatter:
    """Helper class for formatting prices with localization"""

    def __init__(self, currency_manager: CurrencyManager, i18n_manager=None):
        self.currency_manager = currency_manager
        self.i18n_manager = i18n_manager

    def format_property_price(
        self,
        amount: Decimal,
        currency_code: str,
        locale: Optional[str] = None
    ) -> str:
        """Format property price with localization"""
        formatted = self.currency_manager.format_amount(amount, currency_code, True)

        # Add suffix based on magnitude
        if amount >= 1000000000:
            suffix = "B"
        elif amount >= 1000000:
            suffix = "M"
        elif amount >= 1000:
            suffix = "K"
        else:
            suffix = ""

        if suffix:
            # Simplified format
            if amount >= 1000000000:
                simplified = amount / 1000000000
            elif amount >= 1000000:
                simplified = amount / 1000000
            else:
                simplified = amount / 1000

            return f"{formatted} ({simplified:.1f}{suffix})"

        return formatted

    def format_price_range(
        self,
        min_price: Decimal,
        max_price: Decimal,
        currency_code: str
    ) -> str:
        """Format price range"""
        min_formatted = self.currency_manager.format_amount(min_price, currency_code, True)
        max_formatted = self.currency_manager.format_amount(max_price, currency_code, True)

        return f"{min_formatted} - {max_formatted}"


# Global instances
currency_manager = CurrencyManager()
price_formatter = PriceFormatter(currency_manager)
