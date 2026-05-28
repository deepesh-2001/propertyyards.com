"""
Enhanced Analytics Manager
Handles comprehensive analytics aggregations with materialized views and caching
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from app.cache import get_from_cache, set_in_cache, delete_from_cache, generate_cache_key, invalidate_cache_pattern
from app.persistent_cache import persistent_cache
from app.cache_pipeline import redis_pipeline, local_cache
from app.db_optimized import query_optimizer, fast_analytics

logger = logging.getLogger(__name__)


class AnalyticsManager:
    """Manager for enhanced analytics"""

    def __init__(self):
        self.cache_prefix = "analytics:"
        self.cache_ttl = 300  # 5 minutes

    async def get_property_analytics(
        self,
        database,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive property analytics with optimized caching"""
        try:
            # Use persistent cache with materialized view fallback
            cache_key = generate_cache_key(
                self.cache_prefix,
                "property",
                start_date.isoformat() if start_date else "none",
                end_date.isoformat() if end_date else "none"
            )

            # Try local cache first (ultra-fast)
            local_result = local_cache.get(cache_key)
            if local_result:
                return local_result

            # Use optimized query with read replica
            async def _compute_analytics():
                return await self._compute_property_analytics(database, start_date, end_date)

            result = await persistent_cache.get_or_compute(
                cache_key,
                _compute_analytics,
                database=database,
                ttl=self.cache_ttl,
                persist=True
            )

            # Store in local cache for ultra-fast access
            local_cache.set(cache_key, result, ttl=60)

            return result

        except Exception as e:
            logger.error(f"Property analytics error: {e}")
            raise

    async def _compute_property_analytics(
        self,
        database,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Compute property analytics (internal method)"""
        # Build date filter
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        if date_filter:
            query = {"created_at": date_filter}
        else:
            query = {}

        # Use fast analytics if no date filter
        if not start_date and not end_date:
            fast_stats = await fast_analytics.get_property_stats_fast(database)
            if fast_stats:
                return fast_stats

        # Total properties
        total_properties = await database.properties.count_documents(query)

        # By status
        active_properties = await database.properties.count_documents({**query, "status": "active"})
        sold_properties = await database.properties.count_documents({**query, "status": "sold"})
        pending_properties = await database.properties.count_documents({**query, "status": "pending"})

            # By type
            type_pipeline = [
                {"$match": query},
                {"$group": {"_id": "$property_type", "count": {"$sum": 1}}}
            ]
            type_result = await database.properties.aggregate(type_pipeline).to_list(length=20)
            by_type = {r["_id"]: r["count"] for r in type_result}

            # By city
            city_pipeline = [
                {"$match": query},
                {"$group": {"_id": "$city", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 20}
            ]
            city_result = await database.properties.aggregate(city_pipeline).to_list(length=20)
            by_city = {r["_id"]: r["count"] for r in city_result}

            # By price range
            price_ranges = {
                "0-10L": 0, "10L-25L": 0, "25L-50L": 0, "50L-1Cr": 0, "1Cr-2Cr": 0, "2Cr+": 0
            }
            price_pipeline = [
                {"$match": query},
                {"$project": {"price": 1}}
            ]
            properties_with_price = await database.properties.aggregate(price_pipeline).to_list(length=10000)
            for prop in properties_with_price:
                price = prop.get("price", 0)
                if price < 1000000:
                    price_ranges["0-10L"] += 1
                elif price < 2500000:
                    price_ranges["10L-25L"] += 1
                elif price < 5000000:
                    price_ranges["25L-50L"] += 1
                elif price < 10000000:
                    price_ranges["50L-1Cr"] += 1
                elif price < 20000000:
                    price_ranges["1Cr-2Cr"] += 1
                else:
                    price_ranges["2Cr+"] += 1

            # Average and median price
            avg_price_pipeline = [
                {"$match": query},
                {"$group": {"_id": None, "avg_price": {"$avg": "$price"}}}
            ]
            avg_result = await database.properties.aggregate(avg_price_pipeline).to_list(length=1)
            average_price = avg_result[0]["avg_price"] if avg_result else 0

            # Median price (approximate)
            sorted_pipeline = [
                {"$match": query},
                {"$sort": {"price": 1}},
                {"$skip": max(0, total_properties // 2 - 1)},
                {"$limit": 2}
            ]
            median_result = await database.properties.aggregate(sorted_pipeline).to_list(length=2)
            if median_result:
                median_price = sum(r.get("price", 0) for r in median_result) / len(median_result)
            else:
                median_price = 0

            # Monthly listings trend
            monthly_pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$created_at"},
                            "month": {"$month": "$created_at"}
                        },
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id.year": -1, "_id.month": -1}},
                {"$limit": 12}
            ]
            monthly_result = await database.properties.aggregate(monthly_pipeline).to_list(length=12)
            monthly_listings = [
                {
                    "year": r["_id"]["year"],
                    "month": r["_id"]["month"],
                    "count": r["count"]
                }
                for r in monthly_result
            ]

            # Top cities
            top_cities = [
                {"city": city, "count": count}
                for city, count in sorted(by_city.items(), key=lambda x: x[1], reverse=True)[:10]
            ]

            # Conversion rate (sold / total)
            conversion_rate = (sold_properties / total_properties * 100) if total_properties > 0 else 0

            # Average days to sell
            sold_pipeline = [
                {"$match": {**query, "status": "sold"}},
                {
                    "$project": {
                        "days_to_sell": {
                            "$divide": [
                                {"$subtract": ["$updated_at", "$created_at"]},
                                86400000  # milliseconds to days
                            ]
                        }
                    }
                }
            ]
            sold_properties_data = await database.properties.aggregate(sold_pipeline).to_list(length=1000)
            if sold_properties_data:
                avg_days_to_sell = sum(p.get("days_to_sell", 0) for p in sold_properties_data) / len(sold_properties_data)
            else:
                avg_days_to_sell = 0

            # Price trend
            price_trend_pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$created_at"},
                            "month": {"$month": "$created_at"}
                        },
                        "avg_price": {"$avg": "$price"}
                    }
                },
                {"$sort": {"_id.year": -1, "_id.month": -1}},
                {"$limit": 12}
            ]
            price_trend_result = await database.properties.aggregate(price_trend_pipeline).to_list(length=12)
            price_trend = [
                {
                    "year": r["_id"]["year"],
                    "month": r["_id"]["month"],
                    "avg_price": r["avg_price"]
                }
                for r in price_trend_result
            ]

            result = {
                "total_properties": total_properties,
                "active_properties": active_properties,
                "sold_properties": sold_properties,
                "pending_properties": pending_properties,
                "by_type": by_type,
                "by_city": by_city,
                "by_price_range": price_ranges,
                "average_price": average_price,
                "median_price": median_price,
                "price_trend": price_trend,
                "monthly_listings": monthly_listings,
                "top_cities": top_cities,
                "conversion_rate": conversion_rate,
                "average_days_to_sell": avg_days_to_sell
            }

            # Cache the result
            await set_in_cache(cache_key, result, ttl=self.cache_ttl)

            return result

        except Exception as e:
            logger.error(f"Property analytics error: {e}")
            raise

    async def get_user_analytics(
        self,
        database,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive user analytics"""
        try:
            cache_key = generate_cache_key(
                self.cache_prefix,
                "user",
                start_date.isoformat() if start_date else "none",
                end_date.isoformat() if end_date else "none"
            )
            cached = await get_from_cache(cache_key)
            if cached:
                return cached

            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            if date_filter:
                query = {"created_at": date_filter}
            else:
                query = {}

            # Total users
            total_users = await database.users.count_documents(query)

            # Active users (logged in last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            active_users = await database.users.count_documents({
                "last_login": {"$gte": thirty_days_ago}
            })

            # New users this month
            this_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            new_users_this_month = await database.users.count_documents({
                "created_at": {"$gte": this_month_start}
            })

            # By role
            role_pipeline = [
                {"$match": query},
                {"$group": {"_id": "$role", "count": {"$sum": 1}}}
            ]
            role_result = await database.users.aggregate(role_pipeline).to_list(length=20)
            by_role = {r["_id"]: r["count"] for r in role_result}

            # By city
            city_pipeline = [
                {"$match": query},
                {"$group": {"_id": "$city", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 20}
            ]
            city_result = await database.users.aggregate(city_pipeline).to_list(length=20)
            by_city = {r["_id"]: r["count"] for r in city_result}

            # User growth trend
            growth_pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$created_at"},
                            "month": {"$month": "$created_at"}
                        },
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id.year": -1, "_id.month": -1}},
                {"$limit": 12}
            ]
            growth_result = await database.users.aggregate(growth_pipeline).to_list(length=12)
            user_growth_trend = [
                {
                    "year": r["_id"]["year"],
                    "month": r["_id"]["month"],
                    "count": r["count"]
                }
                for r in growth_result
            ]

            # Active sessions (from session cache - approximate)
            active_sessions = 0  # Would need Redis session count

            # Average session duration (placeholder)
            average_session_duration = 0  # Would need session tracking

            result = {
                "total_users": total_users,
                "active_users": active_users,
                "new_users_this_month": new_users_this_month,
                "by_role": by_role,
                "by_city": by_city,
                "user_growth_trend": user_growth_trend,
                "active_sessions": active_sessions,
                "average_session_duration": average_session_duration
            }

            await set_in_cache(cache_key, result, ttl=self.cache_ttl)

            return result

        except Exception as e:
            logger.error(f"User analytics error: {e}")
            raise

    async def get_revenue_analytics(
        self,
        database,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive revenue analytics"""
        try:
            cache_key = generate_cache_key(
                self.cache_prefix,
                "revenue",
                start_date.isoformat() if start_date else "none",
                end_date.isoformat() if end_date else "none"
            )
            cached = await get_from_cache(cache_key)
            if cached:
                return cached

            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date

            # Total revenue from commissions
            commission_pipeline = [
                {"$match": {**date_filter, "status": "paid"} if date_filter else {"status": "paid"}},
                {"$group": {"_id": None, "total": {"$sum": "$calculated_amount"}}}
            ]
            commission_result = await database.commissions.aggregate(commission_pipeline).to_list(length=1)
            total_revenue = commission_result[0]["total"] if commission_result else 0

            # Revenue this month
            this_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            this_month_pipeline = [
                {"$match": {"status": "paid", "created_at": {"$gte": this_month_start}}},
                {"$group": {"_id": None, "total": {"$sum": "$calculated_amount"}}}
            ]
            this_month_result = await database.commissions.aggregate(this_month_pipeline).to_list(length=1)
            revenue_this_month = this_month_result[0]["total"] if this_month_result else 0

            # Revenue this quarter
            quarter_start = datetime.utcnow().replace(
                month=((datetime.utcnow().month - 1) // 3) * 3 + 1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            )
            quarter_pipeline = [
                {"$match": {"status": "paid", "created_at": {"$gte": quarter_start}}},
                {"$group": {"_id": None, "total": {"$sum": "$calculated_amount"}}}
            ]
            quarter_result = await database.commissions.aggregate(quarter_pipeline).to_list(length=1)
            revenue_this_quarter = quarter_result[0]["total"] if quarter_result else 0

            # Revenue this year
            year_start = datetime.utcnow().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            year_pipeline = [
                {"$match": {"status": "paid", "created_at": {"$gte": year_start}}},
                {"$group": {"_id": None, "total": {"$sum": "$calculated_amount"}}}
            ]
            year_result = await database.commissions.aggregate(year_pipeline).to_list(length=1)
            revenue_this_year = year_result[0]["total"] if year_result else 0

            # By source (deal type)
            source_pipeline = [
                {"$match": {"status": "paid"} if not date_filter else {"status": "paid", **date_filter}},
                {"$group": {"_id": "$deal_type", "total": {"$sum": "$calculated_amount"}}}
            ]
            source_result = await database.commissions.aggregate(source_pipeline).to_list(length=20)
            by_source = {r["_id"]: r["total"] for r in source_result}

            # Monthly revenue trend
            monthly_pipeline = [
                {"$match": {"status": "paid"} if not date_filter else {"status": "paid", **date_filter}},
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$created_at"},
                            "month": {"$month": "$created_at"}
                        },
                        "total": {"$sum": "$calculated_amount"}
                    }
                },
                {"$sort": {"_id.year": -1, "_id.month": -1}},
                {"$limit": 12}
            ]
            monthly_result = await database.commissions.aggregate(monthly_pipeline).to_list(length=12)
            monthly_revenue_trend = [
                {
                    "year": r["_id"]["year"],
                    "month": r["_id"]["month"],
                    "total": r["total"]
                }
                for r in monthly_result
            ]

            # Average transaction value
            avg_pipeline = [
                {"$match": {"status": "paid"} if not date_filter else {"status": "paid", **date_filter}},
                {"$group": {"_id": None, "avg": {"$avg": "$calculated_amount"}}}
            ]
            avg_result = await database.commissions.aggregate(avg_pipeline).to_list(length=1)
            average_transaction_value = avg_result[0]["avg"] if avg_result else 0

            # Growth rate (month over month)
            if len(monthly_revenue_trend) >= 2:
                current_month = monthly_revenue_trend[0]["total"]
                previous_month = monthly_revenue_trend[1]["total"]
                growth_rate = ((current_month - previous_month) / previous_month * 100) if previous_month > 0 else 0
            else:
                growth_rate = 0

            result = {
                "total_revenue": total_revenue,
                "revenue_this_month": revenue_this_month,
                "revenue_this_quarter": revenue_this_quarter,
                "revenue_this_year": revenue_this_year,
                "by_source": by_source,
                "by_payment_method": {},  # Would need payment data
                "monthly_revenue_trend": monthly_revenue_trend,
                "average_transaction_value": average_transaction_value,
                "growth_rate": growth_rate
            }

            await set_in_cache(cache_key, result, ttl=self.cache_ttl)

            return result

        except Exception as e:
            logger.error(f"Revenue analytics error: {e}")
            raise

    async def get_commission_analytics(
        self,
        database,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive commission analytics"""
        try:
            cache_key = generate_cache_key(
                self.cache_prefix,
                "commission",
                start_date.isoformat() if start_date else "none",
                end_date.isoformat() if end_date else "none"
            )
            cached = await get_from_cache(cache_key)
            if cached:
                return cached

            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date

            # Total commissions
            total_pipeline = [
                {"$match": date_filter if date_filter else {}},
                {"$group": {"_id": None, "total": {"$sum": "$calculated_amount"}}}
            ]
            total_result = await database.commissions.aggregate(total_pipeline).to_list(length=1)
            total_commissions = total_result[0]["total"] if total_result else 0

            # Pending commissions
            pending_pipeline = [
                {"$match": {**date_filter, "status": "pending"} if date_filter else {"status": "pending"}},
                {"$group": {"_id": None, "total": {"$sum": "$calculated_amount"}}}
            ]
            pending_result = await database.commissions.aggregate(pending_pipeline).to_list(length=1)
            pending_commissions = pending_result[0]["total"] if pending_result else 0

            # Paid commissions
            paid_pipeline = [
                {"$match": {**date_filter, "status": "paid"} if date_filter else {"status": "paid"}},
                {"$group": {"_id": None, "total": {"$sum": "$calculated_amount"}}}
            ]
            paid_result = await database.commissions.aggregate(paid_pipeline).to_list(length=1)
            paid_commissions = paid_result[0]["total"] if paid_result else 0

            # By recipient
            recipient_pipeline = [
                {"$match": date_filter if date_filter else {}},
                {
                    "$group": {
                        "_id": "$recipient_id",
                        "total": {"$sum": "$calculated_amount"},
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"total": -1}},
                {"$limit": 20}
            ]
            recipient_result = await database.commissions.aggregate(recipient_pipeline).to_list(length=20)
            by_recipient = [
                {"recipient_id": r["_id"], "total": r["total"], "count": r["count"]}
                for r in recipient_result
            ]

            # By type
            type_pipeline = [
                {"$match": date_filter if date_filter else {}},
                {
                    "$group": {
                        "_id": "$deal_type",
                        "total": {"$sum": "$calculated_amount"}
                    }
                }
            ]
            type_result = await database.commissions.aggregate(type_pipeline).to_list(length=20)
            by_type = {r["_id"]: r["total"] for r in type_result}

            # Monthly commission trend
            monthly_pipeline = [
                {"$match": date_filter if date_filter else {}},
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$created_at"},
                            "month": {"$month": "$created_at"}
                        },
                        "total": {"$sum": "$calculated_amount"}
                    }
                },
                {"$sort": {"_id.year": -1, "_id.month": -1}},
                {"$limit": 12}
            ]
            monthly_result = await database.commissions.aggregate(monthly_pipeline).to_list(length=12)
            monthly_commission_trend = [
                {
                    "year": r["_id"]["year"],
                    "month": r["_id"]["month"],
                    "total": r["total"]
                }
                for r in monthly_result
            ]

            # Top performers
            top_performers = by_recipient[:10]

            # Average commission
            avg_pipeline = [
                {"$match": date_filter if date_filter else {}},
                {"$group": {"_id": None, "avg": {"$avg": "$calculated_amount"}}}
            ]
            avg_result = await database.commissions.aggregate(avg_pipeline).to_list(length=1)
            average_commission = avg_result[0]["avg"] if avg_result else 0

            result = {
                "total_commissions": total_commissions,
                "pending_commissions": pending_commissions,
                "paid_commissions": paid_commissions,
                "by_recipient": by_recipient,
                "by_type": by_type,
                "monthly_commission_trend": monthly_commission_trend,
                "top_performers": top_performers,
                "average_commission": average_commission
            }

            await set_in_cache(cache_key, result, ttl=self.cache_ttl)

            return result

        except Exception as e:
            logger.error(f"Commission analytics error: {e}")
            raise

    async def get_inquiry_analytics(
        self,
        database,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive inquiry analytics"""
        try:
            cache_key = generate_cache_key(
                self.cache_prefix,
                "inquiry",
                start_date.isoformat() if start_date else "none",
                end_date.isoformat() if end_date else "none"
            )
            cached = await get_from_cache(cache_key)
            if cached:
                return cached

            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date

            # Total inquiries
            total_inquiries = await database.inquiries.count_documents(date_filter if date_filter else {})

            # Inquiries this month
            this_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            inquiries_this_month = await database.inquiries.count_documents({
                "created_at": {"$gte": this_month_start}
            })

            # By status
            status_pipeline = [
                {"$match": date_filter if date_filter else {}},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            status_result = await database.inquiries.aggregate(status_pipeline).to_list(length=20)
            by_status = {r["_id"]: r["count"] for r in status_result}

            # By property
            property_pipeline = [
                {"$match": date_filter if date_filter else {}},
                {
                    "$group": {
                        "_id": "$property_id",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": 20}
            ]
            property_result = await database.inquiries.aggregate(property_pipeline).to_list(length=20)
            by_property = [
                {"property_id": r["_id"], "count": r["count"]}
                for r in property_result
            ]

            # Response rate (responded / total)
            responded_count = by_status.get("responded", 0) + by_status.get("closed", 0)
            response_rate = (responded_count / total_inquiries * 100) if total_inquiries > 0 else 0

            # Average response time (placeholder - would need response timestamp)
            average_response_time_hours = 0

            # Conversion to sale (inquiries that led to sale)
            conversion_to_sale = 0  # Would need tracking

            # Monthly inquiry trend
            monthly_pipeline = [
                {"$match": date_filter if date_filter else {}},
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$created_at"},
                            "month": {"$month": "$created_at"}
                        },
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id.year": -1, "_id.month": -1}},
                {"$limit": 12}
            ]
            monthly_result = await database.inquiries.aggregate(monthly_pipeline).to_list(length=12)
            monthly_inquiry_trend = [
                {
                    "year": r["_id"]["year"],
                    "month": r["_id"]["month"],
                    "count": r["count"]
                }
                for r in monthly_result
            ]

            result = {
                "total_inquiries": total_inquiries,
                "inquiries_this_month": inquiries_this_month,
                "response_rate": response_rate,
                "average_response_time_hours": average_response_time_hours,
                "by_status": by_status,
                "by_property": by_property,
                "conversion_to_sale": conversion_to_sale,
                "monthly_inquiry_trend": monthly_inquiry_trend
            }

            await set_in_cache(cache_key, result, ttl=self.cache_ttl)

            return result

        except Exception as e:
            logger.error(f"Inquiry analytics error: {e}")
            raise

    async def get_dashboard_analytics(
        self,
        database,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get combined dashboard analytics"""
        try:
            cache_key = generate_cache_key(
                self.cache_prefix,
                "dashboard",
                start_date.isoformat() if start_date else "none",
                end_date.isoformat() if end_date else "none"
            )
            cached = await get_from_cache(cache_key)
            if cached:
                return cached

            # Get all analytics
            property_analytics = await self.get_property_analytics(database, start_date, end_date)
            user_analytics = await self.get_user_analytics(database, start_date, end_date)
            revenue_analytics = await self.get_revenue_analytics(database, start_date, end_date)
            commission_analytics = await self.get_commission_analytics(database, start_date, end_date)
            inquiry_analytics = await self.get_inquiry_analytics(database, start_date, end_date)

            result = {
                "property_analytics": property_analytics,
                "user_analytics": user_analytics,
                "revenue_analytics": revenue_analytics,
                "commission_analytics": commission_analytics,
                "inquiry_analytics": inquiry_analytics,
                "generated_at": datetime.utcnow()
            }

            await set_in_cache(cache_key, result, ttl=self.cache_ttl)

            return result

        except Exception as e:
            logger.error(f"Dashboard analytics error: {e}")
            raise


# Global manager instance
analytics_manager = AnalyticsManager()
