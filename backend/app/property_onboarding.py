"""
Easy Property Onboarding Module
Handles simplified property onboarding with multiple import methods
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from app.schemas import (
    PropertyOnboardingSource,
    PropertyOnboardingStatus,
    QuickPropertyCreate,
    URLPropertyImport,
    TextPropertyImport,
    BulkPropertyImport,
    PropertyOnboardingUpdate
)
from app.scraper import content_enricher, property_scraper
from app.notification import notification_manager

logger = logging.getLogger(__name__)


class PropertyOnboardingManager:
    """Manager for easy property onboarding"""

    def __init__(self):
        self.auto_publish_threshold = 0.8  # Price comparison score threshold for auto-publish

    async def create_quick_property(
        self,
        property_data: QuickPropertyCreate,
        submitted_by: str,
        database
    ) -> Dict[str, Any]:
        """Create property from quick form"""
        try:
            # Enrich property data
            enriched_data = {
                "title": property_data.title,
                "property_type": property_data.property_type,
                "city": property_data.city,
                "state": property_data.state,
                "price": property_data.price,
                "area": property_data.area,
                "area_unit": property_data.area_unit,
                "bedrooms": property_data.bedrooms,
                "bathrooms": property_data.bathrooms,
                "description": property_data.description,
                "source_url": property_data.source_url,
                "source_site": property_data.source_site,
                "images": property_data.images,
                "is_builder_property": property_data.is_builder_property,
                "builder_name": property_data.builder_name,
                "amenities": property_data.amenities,
                "contact_name": property_data.contact_name,
                "contact_phone": property_data.contact_phone,
                "contact_email": property_data.contact_email
            }

            # Get price comparison if URL provided
            price_comparison = None
            if property_data.source_url:
                price_comparison = await property_scraper.compare_prices(
                    enriched_data,
                    property_data.city
                )

            # Determine if auto-publish eligible
            status = PropertyOnboardingStatus.PENDING_REVIEW
            if price_comparison and price_comparison.get("is_below_average"):
                status = PropertyOnboardingStatus.APPROVED

            onboarding = {
                "source": PropertyOnboardingSource.MANUAL,
                "status": status,
                "property_data": enriched_data,
                "price_comparison": price_comparison,
                "contact_name": property_data.contact_name,
                "contact_phone": property_data.contact_phone,
                "contact_email": property_data.contact_email,
                "submitted_by": submitted_by,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = await database.property_onboardings.insert_one(onboarding)
            onboarding["id"] = str(result.inserted_id)

            # If auto-approved, publish to properties
            if status == PropertyOnboardingStatus.APPROVED:
                await self._publish_property(onboarding, database)

            logger.info(f"Quick property onboarding created: {onboarding['id']}")
            return onboarding

        except Exception as e:
            logger.error(f"Quick property onboarding error: {e}")
            raise

    async def import_from_url(
        self,
        import_data: URLPropertyImport,
        submitted_by: str,
        database
    ) -> Dict[str, Any]:
        """Import property from external URL"""
        try:
            # Scrape property from URL
            scraped = await property_scraper.scrape_property(
                import_data.url,
                import_data.site
            )

            if not scraped:
                raise ValueError("Failed to scrape property from URL")

            # Apply overrides
            property_data = scraped.copy()
            if import_data.override_data:
                property_data.update(import_data.override_data)

            # Add contact info
            property_data.update({
                "contact_name": import_data.contact_name,
                "contact_phone": import_data.contact_phone,
                "contact_email": import_data.contact_email
            })

            # Get price comparison
            city = property_data.get("location", "").split(",")[-1].strip() if property_data.get("location") else "Mumbai"
            price_comparison = await property_scraper.compare_prices(property_data, city)

            # Determine status
            status = PropertyOnboardingStatus.PENDING_REVIEW
            if price_comparison and price_comparison.get("is_below_average"):
                status = PropertyOnboardingStatus.APPROVED

            onboarding = {
                "source": PropertyOnboardingSource.URL_IMPORT,
                "status": status,
                "property_data": property_data,
                "scraped_data": scraped,
                "price_comparison": price_comparison,
                "contact_name": import_data.contact_name,
                "contact_phone": import_data.contact_phone,
                "contact_email": import_data.contact_email,
                "submitted_by": submitted_by,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = await database.property_onboardings.insert_one(onboarding)
            onboarding["id"] = str(result.inserted_id)

            if status == PropertyOnboardingStatus.APPROVED:
                await self._publish_property(onboarding, database)

            logger.info(f"URL property import created: {onboarding['id']}")
            return onboarding

        except Exception as e:
            logger.error(f"URL property import error: {e}")
            raise

    async def import_from_text(
        self,
        import_data: TextPropertyImport,
        submitted_by: str,
        database
    ) -> Dict[str, Any]:
        """Extract property from text description"""
        try:
            # Extract property data from text
            extracted = await property_scraper.extract_property_from_text(import_data.text)

            # Build property data
            property_data = {
                "title": f"Property in {extracted.get('location', import_data.city)}",
                "city": import_data.city,
                "state": "Maharashtra",  # Default
                "price": extracted.get("price", "0"),
                "area": extracted.get("area", "0"),
                "bedrooms": extracted.get("bedrooms"),
                "description": import_data.text,
                "contact_name": import_data.contact_name,
                "contact_phone": import_data.contact_phone,
                "contact_email": import_data.contact_email
            }

            # Apply overrides
            if import_data.override_data:
                property_data.update(import_data.override_data)

            # Get price comparison
            price_comparison = await property_scraper.compare_prices(property_data, import_data.city)

            status = PropertyOnboardingStatus.PENDING_REVIEW
            if price_comparison and price_comparison.get("is_below_average"):
                status = PropertyOnboardingStatus.APPROVED

            onboarding = {
                "source": PropertyOnboardingSource.TEXT_IMPORT,
                "status": status,
                "property_data": property_data,
                "extracted_data": extracted,
                "price_comparison": price_comparison,
                "contact_name": import_data.contact_name,
                "contact_phone": import_data.contact_phone,
                "contact_email": import_data.contact_email,
                "submitted_by": submitted_by,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = await database.property_onboardings.insert_one(onboarding)
            onboarding["id"] = str(result.inserted_id)

            if status == PropertyOnboardingStatus.APPROVED:
                await self._publish_property(onboarding, database)

            logger.info(f"Text property import created: {onboarding['id']}")
            return onboarding

        except Exception as e:
            logger.error(f"Text property import error: {e}")
            raise

    async def bulk_import(
        self,
        import_data: BulkPropertyImport,
        submitted_by: str,
        database
    ) -> Dict[str, Any]:
        """Bulk import properties"""
        try:
            results = []
            successes = 0
            failures = 0

            for prop in import_data.properties:
                try:
                    # Convert to QuickPropertyCreate
                    quick_prop = QuickPropertyCreate(**prop)
                    result = await self.create_quick_property(quick_prop, submitted_by, database)
                    results.append({"success": True, "property_id": result["id"]})
                    successes += 1
                except Exception as e:
                    results.append({"success": False, "error": str(e)})
                    failures += 1

            summary = {
                "total": len(import_data.properties),
                "successes": successes,
                "failures": failures,
                "results": results,
                "created_at": datetime.utcnow()
            }

            logger.info(f"Bulk import completed: {successes}/{len(import_data.properties)} successful")
            return summary

        except Exception as e:
            logger.error(f"Bulk import error: {e}")
            raise

    async def update_onboarding(
        self,
        onboarding_id: str,
        update_data: PropertyOnboardingUpdate,
        reviewed_by: str,
        database
    ) -> Dict[str, Any]:
        """Update property onboarding status"""
        try:
            existing = await database.property_onboardings.find_one({"_id": onboarding_id})
            if not existing:
                raise ValueError("Onboarding not found")

            update_dict = update_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()

            if update_data.status == PropertyOnboardingStatus.APPROVED:
                update_dict["reviewed_by"] = reviewed_by
                await self._publish_property(existing, database)

            if update_data.status == PropertyOnboardingStatus.PUBLISHED:
                update_dict["published_at"] = datetime.utcnow()

            if update_data.status == PropertyOnboardingStatus.REJECTED:
                update_dict["reviewed_by"] = reviewed_by

            result = await database.property_onboardings.update_one(
                {"_id": onboarding_id},
                {"$set": update_dict}
            )

            if result.modified_count == 0:
                raise ValueError("Update failed")

            updated = await database.property_onboardings.find_one({"_id": onboarding_id})
            updated["id"] = str(updated["_id"])
            del updated["_id"]

            # Send notification if rejected
            if update_data.status == PropertyOnboardingStatus.REJECTED:
                try:
                    await notification_manager.email_service.send_onboarding_status_update(
                        employee_name=existing["contact_name"],
                        employee_email=existing["contact_email"],
                        status="rejected",
                        notes=update_data.rejection_reason
                    )
                except Exception as e:
                    logger.warning(f"Failed to send rejection email: {e}")

            logger.info(f"Onboarding {onboarding_id} updated")
            return updated

        except Exception as e:
            logger.error(f"Onboarding update error: {e}")
            raise

    async def get_onboarding_analytics(
        self,
        database,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get property onboarding analytics"""
        try:
            query = {}
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            if date_filter:
                query["created_at"] = date_filter

            onboardings = await database.property_onboardings.find(query).to_list(length=1000)

            total = len(onboardings)

            by_source = {}
            by_status = {}
            by_property_type = {}
            by_city = {}

            auto_published = 0
            manual_review = 0
            processing_times = []

            for o in onboardings:
                source = o.get("source", "unknown")
                by_source[source] = by_source.get(source, 0) + 1

                status = o.get("status", "unknown")
                by_status[status] = by_status.get(status, 0) + 1

                prop_type = o["property_data"].get("property_type", "unknown")
                by_property_type[prop_type] = by_property_type.get(prop_type, 0) + 1

                city = o["property_data"].get("city", "unknown")
                by_city[city] = by_city.get(city, 0) + 1

                if status == PropertyOnboardingStatus.APPROVED:
                    auto_published += 1
                elif status == PropertyOnboardingStatus.PENDING_REVIEW:
                    manual_review += 1

                if o.get("published_at"):
                    processing_time = (o["published_at"] - o["created_at"]).total_seconds() / 3600
                    processing_times.append(processing_time)

            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

            # Monthly trend
            monthly_trend = []
            for i in range(6):
                month_start = datetime.utcnow() - timedelta(days=30 * (i + 1))
                month_end = datetime.utcnow() - timedelta(days=30 * i)
                month_onboardings = [o for o in onboardings
                                   if month_start <= o["created_at"] <= month_end]
                monthly_trend.append({
                    "month": month_start.strftime("%Y-%m"),
                    "count": len(month_onboardings)
                })

            return {
                "total_onboardings": total,
                "by_source": by_source,
                "by_status": by_status,
                "by_property_type": by_property_type,
                "by_city": by_city,
                "average_processing_time_hours": avg_processing_time,
                "auto_published_count": auto_published,
                "manual_review_count": manual_review,
                "monthly_trend": monthly_trend
            }

        except Exception as e:
            logger.error(f"Onboarding analytics error: {e}")
            raise

    async def _publish_property(self, onboarding: Dict[str, Any], database):
        """Publish property to main properties collection"""
        try:
            prop_data = onboarding["property_data"].copy()
            prop_data["created_at"] = datetime.utcnow()
            prop_data["updated_at"] = datetime.utcnow()
            prop_data["is_active"] = True

            result = await database.properties.insert_one(prop_data)
            onboarding["original_property_id"] = str(result.inserted_id)

            # Update onboarding with property ID
            await database.property_onboardings.update_one(
                {"_id": onboarding["id"]},
                {"$set": {"original_property_id": str(result.inserted_id)}}
            )

            logger.info(f"Property published: {result.inserted_id}")

        except Exception as e:
            logger.error(f"Property publish error: {e}")
            raise


# Global manager instance
property_onboarding_manager = PropertyOnboardingManager()
