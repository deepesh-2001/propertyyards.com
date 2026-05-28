"""
Price Comparison Service
Compare prices across multiple platforms and providers
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import aiohttp
import json

logger = logging.getLogger(__name__)


class PriceCategory(Enum):
    """Price comparison categories"""
    PROPERTY = "property"
    FLIGHT = "flight"
    HOTEL = "hotel"
    PRODUCT = "product"
    SERVICE = "service"


@dataclass
class PriceOffer:
    """Price offer from a provider"""
    id: str
    provider: str
    provider_logo: Optional[str] = None
    price: float = 0.0
    original_price: Optional[float] = None
    currency: str = "INR"
    discount_percentage: Optional[float] = None
    url: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: int = 0
    in_stock: bool = True
    delivery_days: Optional[int] = None
    features: Optional[List[str]] = None
    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()
        if self.features is None:
            self.features = []


@dataclass
class PropertyPriceOffer(PriceOffer):
    """Property-specific price offer"""
    property_id: Optional[str] = None
    property_type: Optional[str] = None  # apartment, villa, etc.
    location: Optional[str] = None
    bedrooms: int = 0
    bathrooms: int = 0
    area_sqft: float = 0.0
    amenities: Optional[List[str]] = None
    broker_name: Optional[str] = None
    broker_contact: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        if self.amenities is None:
            self.amenities = []


class PriceComparisonService:
    """Compare prices across multiple platforms"""

    def __init__(self):
        self.enabled = True
        self.providers = {
            "99acres": {"enabled": True, "api_key": None},
            "magicbricks": {"enabled": True, "api_key": None},
            "housing": {"enabled": True, "api_key": None},
            "olx": {"enabled": False, "api_key": None},
            "amazon": {"enabled": False, "api_key": None},
            "flipkart": {"enabled": False, "api_key": None}
        }
        self.cache_ttl = 3600  # 1 hour

    async def initialize(self, provider_keys: Optional[Dict[str, str]] = None):
        """Initialize with provider API keys"""
        if provider_keys:
            for provider, key in provider_keys.items():
                if provider in self.providers:
                    self.providers[provider]["api_key"] = key
        logger.info("Price Comparison Service initialized")

    async def compare_property_prices(
        self,
        location: str,
        property_type: str = "apartment",
        bedrooms: int = 2,
        bathrooms: int = 2,
        area_range: Optional[tuple] = None,
        max_results: int = 10
    ) -> List[PropertyPriceOffer]:
        """Compare property prices across platforms"""
        try:
            # Check cache
            cache_key = f"property:{location}:{property_type}:{bedrooms}:{bathrooms}"
            cached = await self._get_cached_results(cache_key)
            if cached:
                return cached

            # Search all enabled property platforms
            search_tasks = []
            platforms = ["99acres", "magicbricks", "housing"]

            for platform in platforms:
                if self.providers[platform]["enabled"]:
                    task = self._search_property_platform(
                        platform, location, property_type, bedrooms, bathrooms, area_range
                    )
                    search_tasks.append(task)

            # If no APIs configured, use mock data
            if not search_tasks:
                results = self._generate_mock_property_results(
                    location, property_type, bedrooms, bathrooms, max_results
                )
                await self._cache_results(cache_key, results)
                return results

            # Gather results
            platform_results = await asyncio.gather(*search_tasks, return_exceptions=True)

            # Combine results
            all_offers = []
            for result in platform_results:
                if isinstance(result, list):
                    all_offers.extend(result)

            # Sort by price
            all_offers.sort(key=lambda x: x.price)

            # Limit results
            all_offers = all_offers[:max_results]

            # Cache results
            await self._cache_results(cache_key, all_offers)

            return all_offers

        except Exception as e:
            logger.error(f"Property price comparison failed: {e}")
            return self._generate_mock_property_results(
                location, property_type, bedrooms, bathrooms, max_results
            )

    async def _search_property_platform(
        self,
        platform: str,
        location: str,
        property_type: str,
        bedrooms: int,
        bathrooms: int,
        area_range: Optional[tuple]
    ) -> List[PropertyPriceOffer]:
        """Search a specific property platform"""
        try:
            if platform == "99acres":
                return await self._search_99acres(location, property_type, bedrooms, bathrooms)
            elif platform == "magicbricks":
                return await self._search_magicbricks(location, property_type, bedrooms, bathrooms)
            elif platform == "housing":
                return await self._search_housing(location, property_type, bedrooms, bathrooms)
            return []
        except Exception as e:
            logger.error(f"Platform {platform} search failed: {e}")
            return []

    async def _search_99acres(
        self,
        location: str,
        property_type: str,
        bedrooms: int,
        bathrooms: int
    ) -> List[PropertyPriceOffer]:
        """Search 99acres API"""
        # Placeholder for 99acres API integration
        return []

    async def _search_magicbricks(
        self,
        location: str,
        property_type: str,
        bedrooms: int,
        bathrooms: int
    ) -> List[PropertyPriceOffer]:
        """Search MagicBricks API"""
        # Placeholder for MagicBricks API integration
        return []

    async def _search_housing(
        self,
        location: str,
        property_type: str,
        bedrooms: int,
        bathrooms: int
    ) -> List[PropertyPriceOffer]:
        """Search Housing.com API"""
        # Placeholder for Housing API integration
        return []

    def _generate_mock_property_results(
        self,
        location: str,
        property_type: str,
        bedrooms: int,
        bathrooms: int,
        max_results: int = 10
    ) -> List[PropertyPriceOffer]:
        """Generate mock property results"""
        platforms = ["99acres", "MagicBricks", "Housing.com", "PropertyYards"]
        base_price = 8000000 if property_type == "apartment" else 15000000  # 80L or 1.5Cr

        offers = []
        for i in range(max_results):
            platform = platforms[i % len(platforms)]
            price_variation = (i - 2) * 50000  # Price varies
            price = max(7500000, base_price + price_variation)

            offer = PropertyPriceOffer(
                id=f"prop_{i}",
                provider=platform,
                price=price,
                original_price=price * 1.1 if i < 3 else None,  # First 3 have discount
                currency="INR",
                discount_percentage=10 if i < 3 else None,
                url=f"https://www.{platform.lower().replace('.', '')}.com/property/{i}",
                rating=4.2 + (i % 3) * 0.2,
                reviews_count=50 + i * 10,
                property_type=property_type,
                location=location,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                area_sqft=1200 + i * 50,
                amenities=["Parking", "Security", "Lift"] if i % 2 == 0 else ["Parking", "Garden"],
                broker_name=f"Agent {i + 1}" if platform == "PropertyYards" else None,
                features=["Verified", "Ready to Move"] if i < 5 else ["Under Construction"]
            )
            offers.append(offer)

        # Sort by price
        offers.sort(key=lambda x: x.price)
        return offers

    async def compare_product_prices(
        self,
        product_name: str,
        category: Optional[str] = None,
        max_results: int = 10
    ) -> List[PriceOffer]:
        """Compare product prices across e-commerce platforms"""
        try:
            # Check cache
            cache_key = f"product:{product_name}:{category or 'all'}"
            cached = await self._get_cached_results(cache_key)
            if cached:
                return cached

            # Search enabled platforms
            search_tasks = []
            platforms = ["amazon", "flipkart"]

            for platform in platforms:
                if self.providers[platform]["enabled"]:
                    task = self._search_product_platform(platform, product_name, category)
                    search_tasks.append(task)

            if not search_tasks:
                results = self._generate_mock_product_results(product_name, max_results)
                await self._cache_results(cache_key, results)
                return results

            platform_results = await asyncio.gather(*search_tasks, return_exceptions=True)

            all_offers = []
            for result in platform_results:
                if isinstance(result, list):
                    all_offers.extend(result)

            all_offers.sort(key=lambda x: x.price)
            all_offers = all_offers[:max_results]

            await self._cache_results(cache_key, all_offers)
            return all_offers

        except Exception as e:
            logger.error(f"Product price comparison failed: {e}")
            return self._generate_mock_product_results(product_name, max_results)

    async def _search_product_platform(
        self,
        platform: str,
        product_name: str,
        category: Optional[str]
    ) -> List[PriceOffer]:
        """Search a specific product platform"""
        # Placeholder for Amazon/Flipkart API integration
        return []

    def _generate_mock_product_results(
        self,
        product_name: str,
        max_results: int
    ) -> List[PriceOffer]:
        """Generate mock product results"""
        platforms = ["Amazon", "Flipkart", "Myntra", "Tata CLiQ"]
        base_price = 15000  # Base price

        offers = []
        for i in range(min(max_results, len(platforms))):
            platform = platforms[i]
            price_variation = (i - 1) * 500
            price = max(14000, base_price + price_variation)

            offer = PriceOffer(
                id=f"prod_{i}",
                provider=platform,
                price=price,
                original_price=price * 1.15 if i == 0 else None,
                currency="INR",
                discount_percentage=15 if i == 0 else None,
                url=f"https://www.{platform.lower().replace(' ', '')}.com/product/{i}",
                rating=4.0 + (i % 2) * 0.5,
                reviews_count=100 + i * 50,
                in_stock=i < 3,
                delivery_days=2 + i,
                features=["Free Delivery", "Cash on Delivery"] if i < 2 else ["Free Delivery"]
            )
            offers.append(offer)

        offers.sort(key=lambda x: x.price)
        return offers

    def _generate_cache_key(self, params: Dict[str, Any]) -> str:
        """Generate cache key"""
        import hashlib
        key_data = json.dumps(params, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()

    async def _get_cached_results(self, cache_key: str) -> Optional[List[Any]]:
        """Get cached results"""
        try:
            from app.cache import get_cache
            cached = await get_cache(f"price:{cache_key}")
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Price cache read error: {e}")
        return None

    async def _cache_results(self, cache_key: str, results: List[Any]):
        """Cache results"""
        try:
            from app.cache import set_cache
            data = [
                {
                    "id": r.id,
                    "provider": r.provider,
                    "price": r.price,
                    "currency": r.currency,
                    "url": r.url,
                    "rating": r.rating,
                    "features": r.features
                }
                for r in results
            ]
            await set_cache(f"price:{cache_key}", json.dumps(data), ttl=self.cache_ttl)
        except Exception as e:
            logger.warning(f"Price cache write error: {e}")

    def get_best_deal(
        self,
        offers: List[Union[PriceOffer, PropertyPriceOffer]]
    ) -> Optional[Union[PriceOffer, PropertyPriceOffer]]:
        """Get best deal based on price and rating"""
        if not offers:
            return None

        # Score based on price (lower is better) and rating (higher is better)
        def score_offer(offer):
            price_score = 1 / (offer.price / 100000)  # Normalize price
            rating_score = offer.rating if offer.rating else 3.0
            return price_score + rating_score

        return max(offers, key=score_offer)

    def calculate_savings(
        self,
        offers: List[Union[PriceOffer, PropertyPriceOffer]]
    ) -> Dict[str, Any]:
        """Calculate potential savings"""
        if not offers or len(offers) < 2:
            return {"savings": 0, "percentage": 0}

        prices = [o.price for o in offers]
        min_price = min(prices)
        max_price = max(prices)

        savings = max_price - min_price
        savings_percentage = (savings / max_price) * 100 if max_price > 0 else 0

        return {
            "min_price": min_price,
            "max_price": max_price,
            "savings": savings,
            "savings_percentage": round(savings_percentage, 2),
            "best_provider": next(o.provider for o in offers if o.price == min_price),
            "worst_provider": next(o.provider for o in offers if o.price == max_price)
        }

    def filter_by_price_range(
        self,
        offers: List[Union[PriceOffer, PropertyPriceOffer]],
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[Union[PriceOffer, PropertyPriceOffer]]:
        """Filter offers by price range"""
        filtered = offers
        if min_price is not None:
            filtered = [o for o in filtered if o.price >= min_price]
        if max_price is not None:
            filtered = [o for o in filtered if o.price <= max_price]
        return filtered

    def sort_by_value_score(
        self,
        offers: List[Union[PriceOffer, PropertyPriceOffer]]
    ) -> List[Union[PriceOffer, PropertyPriceOffer]]:
        """Sort offers by value score (price + rating)"""
        def value_score(offer):
            rating = offer.rating if offer.rating else 3.0
            # Lower price and higher rating = better value
            return (offer.price / 1000000) - (rating * 100000)

        return sorted(offers, key=value_score)


# Global instance
price_comparison = PriceComparisonService()
