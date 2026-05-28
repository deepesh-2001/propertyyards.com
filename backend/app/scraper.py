"""
Content Scraper Module
Handles scraping and lookup of property data from external websites
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import re
import json

try:
    import aiohttp
    from bs4 import BeautifulSoup
    HAS_SCRAPING_DEPS = True
except ImportError:
    HAS_SCRAPING_DEPS = False
    logging.warning("Scraping dependencies (aiohttp, beautifulsoup4) not installed")

from app.cache import get_cache, set_cache
from app.config import settings

logger = logging.getLogger(__name__)


class PropertyScraper:
    """Scraper for property data from external websites"""

    def __init__(self):
        self.cache_prefix = "scraped:"
        self.cache_ttl = 3600  # 1 hour cache for scraped data
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

        # Popular Indian real estate websites
        self.sites = {
            "magicbricks": {
                "base_url": "https://www.magicbricks.com",
                "search_url": "https://www.magicbricks.com/property-for-sale/search",
                "selectors": {
                    "title": ".mb-srp__card--title",
                    "price": ".mb-srp__card__price--amount",
                    "location": ".mb-srp__card--address",
                    "bedrooms": ".mb-srp__card__bed",
                    "bathrooms": ".mb-srp__card--bath",
                    "area": ".mb-srp__card__size",
                    "image": ".mb-srp__card__img img"
                }
            },
            "99acres": {
                "base_url": "https://www.99acres.com",
                "search_url": "https://www.99acres.com/search/property/buy",
                "selectors": {
                    "title": ".srpTuple__title",
                    "price": ".srpTuple__price",
                    "location": ".srpTuple__address",
                    "bedrooms": ".srpTuple__bed",
                    "bathrooms": ".srpTuple__bath",
                    "area": ".srpTuple__area",
                    "image": ".srpTuple__img img"
                }
            },
            "housing": {
                "base_url": "https://www.housing.com",
                "search_url": "https://www.housing.com/buy",
                "selectors": {
                    "title": ".card-title",
                    "price": ".card-price",
                    "location": ".card-location",
                    "bedrooms": ".card-bed",
                    "bathrooms": ".card-bath",
                    "area": ".card-area",
                    "image": ".card-image img"
                }
            },
            "commonfloor": {
                "base_url": "https://www.commonfloor.com",
                "search_url": "https://www.commonfloor.com/listing-search",
                "selectors": {
                    "title": ".listing-title",
                    "price": ".listing-price",
                    "location": ".listing-location",
                    "bedrooms": ".listing-bed",
                    "bathrooms": ".listing-bath",
                    "area": ".listing-area",
                    "image": ".listing-image img"
                }
            }
        }

    async def scrape_property(
        self,
        url: str,
        site: str = "magicbricks"
    ) -> Optional[Dict[str, Any]]:
        """Scrape property data from a given URL"""
        if not HAS_SCRAPING_DEPS:
            logger.error("Scraping dependencies not available")
            return None

        try:
            # Check cache first
            cache_key = f"{self.cache_prefix}{url}"
            cached = await get_cache(cache_key)
            if cached:
                return json.loads(cached)

            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch {url}: {response.status}")
                        return None

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    site_config = self.sites.get(site, self.sites["magicbricks"])
                    selectors = site_config["selectors"]

                    property_data = {
                        "url": url,
                        "site": site,
                        "scraped_at": datetime.utcnow().isoformat()
                    }

                    # Extract data using selectors
                    for field, selector in selectors.items():
                        try:
                            element = soup.select_one(selector)
                            if element:
                                if field == "image":
                                    property_data[field] = element.get("src") or element.get("data-src")
                                else:
                                    property_data[field] = element.get_text(strip=True)
                        except Exception as e:
                            logger.warning(f"Failed to extract {field}: {e}")
                            property_data[field] = None

                    # Cache the result
                    await set_cache(cache_key, json.dumps(property_data), ttl=self.cache_ttl)

                    logger.info(f"Successfully scraped property from {url}")
                    return property_data

        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")
            return None

    async def search_properties(
        self,
        query: str,
        city: str = "Mumbai",
        site: str = "magicbricks",
        property_type: str = "apartment"
    ) -> List[Dict[str, Any]]:
        """Search for properties on external sites"""
        if not HAS_SCRAPING_DEPS:
            logger.error("Scraping dependencies not available")
            return []

        try:
            site_config = self.sites.get(site, self.sites["magicbricks"])
            search_url = f"{site_config['search_url']}?q={query}&city={city}&type={property_type}"

            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"Search failed: {response.status}")
                        return []

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    properties = []
                    # Extract property links from search results
                    links = soup.find_all('a', href=True)

                    for link in links[:10]:  # Limit to first 10 results
                        href = link.get('href')
                        if href and '/property/' in href:
                            full_url = href if href.startswith('http') else f"{site_config['base_url']}{href}"
                            property_data = await self.scrape_property(full_url, site)
                            if property_data:
                                properties.append(property_data)

                    logger.info(f"Found {len(properties)} properties for query: {query}")
                    return properties

        except Exception as e:
            logger.error(f"Property search error: {e}")
            return []

    async def extract_property_from_text(
        self,
        text: str
    ) -> Dict[str, Any]:
        """Extract property information from text (e.g., listing description)"""
        try:
            extracted = {
                "raw_text": text,
                "extracted_at": datetime.utcnow().isoformat()
            }

            # Extract price (e.g., ₹50,00,000, 50 Lakhs, 5 Cr)
            price_patterns = [
                r'₹[\d,]+(?:,\d{3})*',
                r'[\d.]+\s*(?:Lakhs|L|Cr|Crore|Million)',
                r'Rs\.?\s*[\d,]+(?:,\d{3})*'
            ]
            for pattern in price_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted["price"] = match.group()
                    break

            # Extract area (e.g., 1200 sq ft, 1200 sqft, 1200 sq. ft.)
            area_patterns = [
                r'[\d,]+\s*(?:sq\.?\s*ft|sqft|square\s*feet)',
                r'[\d,]+\s*(?:sq\.?\s*m|sqm|square\s*meters)'
            ]
            for pattern in area_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted["area"] = match.group()
                    break

            # Extract bedrooms (e.g., 2 BHK, 3 Bedroom)
            bedroom_patterns = [
                r'(\d+)\s*(?:BHK|Bedroom|BHK)',
                r'(\d+)\s*BHK'
            ]
            for pattern in bedroom_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted["bedrooms"] = int(match.group(1))
                    break

            # Extract location/city
            location_patterns = [
                r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            ]
            for pattern in location_patterns:
                match = re.search(pattern, text)
                if match:
                    extracted["location"] = match.group(1)
                    break

            return extracted

        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            return {"raw_text": text, "error": str(e)}

    async def compare_prices(
        self,
        property_data: Dict[str, Any],
        city: str = "Mumbai"
    ) -> Dict[str, Any]:
        """Compare property price with similar properties in the area"""
        try:
            location = property_data.get("location", "")
            area = property_data.get("area", "")
            bedrooms = property_data.get("bedrooms", 0)

            # Build search query
            query_parts = []
            if location:
                query_parts.append(location)
            if bedrooms:
                query_parts.append(f"{bedrooms} BHK")
            if area:
                query_parts.append(area)

            query = " ".join(query_parts) if query_parts else "apartment"

            # Search for similar properties
            similar_properties = await self.search_properties(query, city)

            if not similar_properties:
                return {
                    "property_price": property_data.get("price"),
                    "similar_properties": 0,
                    "average_price": None,
                    "price_range": None
                }

            # Extract prices and calculate statistics
            prices = []
            for prop in similar_properties:
                price_str = prop.get("price", "")
                if price_str:
                    # Parse price to numeric value (simplified)
                    price_match = re.search(r'[\d,]+', price_str.replace(',', ''))
                    if price_match:
                        try:
                            price = float(price_match.group())
                            prices.append(price)
                        except ValueError:
                            pass

            if prices:
                avg_price = sum(prices) / len(prices)
                min_price = min(prices)
                max_price = max(prices)

                return {
                    "property_price": property_data.get("price"),
                    "similar_properties": len(similar_properties),
                    "average_price": avg_price,
                    "price_range": {"min": min_price, "max": max_price},
                    "is_below_average": float(property_data.get("price", "0").replace(',', '').replace('₹', '')) < avg_price if property_data.get("price") else None
                }

            return {
                "property_price": property_data.get("price"),
                "similar_properties": len(similar_properties),
                "average_price": None,
                "price_range": None
            }

        except Exception as e:
            logger.error(f"Price comparison error: {e}")
            return {"error": str(e)}


class ContentEnricher:
    """Enrich property data with external content"""

    def __init__(self):
        self.scraper = PropertyScraper()

    async def enrich_property(
        self,
        property_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enrich property data with scraped information"""
        try:
            enriched = property_data.copy()

            # If URL is provided, scrape it
            if property_data.get("source_url"):
                scraped = await self.scraper.scrape_property(
                    property_data["source_url"],
                    property_data.get("source_site", "magicbricks")
                )
                if scraped:
                    enriched["scraped_data"] = scraped

            # If description is provided, extract structured data
            if property_data.get("description"):
                extracted = await self.scraper.extract_property_from_text(
                    property_data["description"]
                )
                enriched["extracted_data"] = extracted

            # Get price comparison
            if property_data.get("price") or property_data.get("location"):
                comparison = await self.scraper.compare_prices(property_data)
                enriched["price_comparison"] = comparison

            return enriched

        except Exception as e:
            logger.error(f"Property enrichment error: {e}")
            return property_data


# Global instances
property_scraper = PropertyScraper()
content_enricher = ContentEnricher()
