"""
Scraper Router
Handles property scraping and content enrichment endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.scraper import property_scraper, content_enricher
from app.auth import get_current_user
from app.feature_flags import require_feature_flag

router = APIRouter(prefix="/api/scraper", tags=["scraper"])


@router.post("/scrape")
@require_feature_flag("property_scraper")
async def scrape_property(
    url: str,
    site: str = "magicbricks",
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Scrape property data from a given URL"""
    try:
        result = await property_scraper.scrape_property(url, site)
        if not result:
            raise HTTPException(status_code=404, detail="Failed to scrape property")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_properties(
    query: str,
    city: str = "Mumbai",
    site: str = "magicbricks",
    property_type: str = "apartment",
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Search for properties on external real estate sites"""
    try:
        results = await property_scraper.search_properties(query, city, site, property_type)
        return {"query": query, "city": city, "site": site, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract")
async def extract_from_text(
    text: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Extract property information from text"""
    try:
        result = await property_scraper.extract_property_from_text(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare-prices")
async def compare_prices(
    property_data: dict,
    city: str = "Mumbai",
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Compare property price with similar properties"""
    try:
        result = await property_scraper.compare_prices(property_data, city)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enrich")
async def enrich_property(
    property_data: dict,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Enrich property data with scraped information"""
    try:
        result = await content_enricher.enrich_property(property_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sites")
async def get_supported_sites(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get list of supported scraping sites"""
    return {
        "sites": list(property_scraper.sites.keys()),
        "details": {
            site: {
                "base_url": config["base_url"],
                "search_url": config["search_url"]
            }
            for site, config in property_scraper.sites.items()
        }
    }
