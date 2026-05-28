"""
Report Generator Service
Generate CSV and PDF reports for stakeholders
"""
import asyncio
import csv
import io
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

# PDF generation - using simple HTML to PDF approach
# For production, consider using WeasyPrint or ReportLab
try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False
    logger.warning("pdfkit not available, PDF generation will use HTML fallback")


class ReportFormat(Enum):
    """Report export formats"""
    CSV = "csv"
    PDF = "pdf"
    JSON = "json"
    EXCEL = "xlsx"


class ReportType(Enum):
    """Types of reports"""
    USAGE_ANALYTICS = "usage_analytics"
    COST_ANALYSIS = "cost_analysis"
    PROPERTY_LISTINGS = "property_listings"
    USER_ACTIVITY = "user_activity"
    FINANCIAL_SUMMARY = "financial_summary"
    AI_PERFORMANCE = "ai_performance"
    SYSTEM_HEALTH = "system_health"
    SALES_RECORDS = "sales_records"
    PROJECTIONS = "projections"
    FUTURE_GROWTH = "future_growth"
    FUTURE_PROJECTS = "future_projects"
    INVESTMENT_OPPORTUNITIES = "investment_opportunities"
    CUSTOM = "custom"


@dataclass
class ReportConfig:
    """Report configuration"""
    report_type: ReportType
    format: ReportFormat
    title: str
    description: str
    date_range_days: int = 30
    filters: Dict[str, Any] = None
    include_charts: bool = True
    stakeholder_level: str = "executive"  # executive, manager, technical

    def __post_init__(self):
        if self.filters is None:
            self.filters = {}


@dataclass
class GeneratedReport:
    """Generated report metadata"""
    id: str
    config: ReportConfig
    created_at: datetime
    file_data: bytes
    file_name: str
    file_size_bytes: int
    row_count: int
    download_url: Optional[str] = None


class ReportGenerator:
    """Generate stakeholder reports in multiple formats"""

    def __init__(self):
        self.templates_dir = "reports/templates"
        self.output_dir = "reports/output"

    async def generate_report(
        self,
        config: ReportConfig,
        database
    ) -> Optional[GeneratedReport]:
        """Generate report based on configuration"""
        try:
            # Gather data based on report type
            data = await self._gather_data(config, database)

            if not data:
                logger.warning(f"No data found for report: {config.report_type.value}")
                return None

            # Generate in requested format
            if config.format == ReportFormat.CSV:
                file_data, file_name = await self._generate_csv(config, data)
            elif config.format == ReportFormat.PDF:
                file_data, file_name = await self._generate_pdf(config, data)
            elif config.format == ReportFormat.JSON:
                file_data, file_name = await self._generate_json(config, data)
            else:
                logger.error(f"Unsupported format: {config.format}")
                return None

            return GeneratedReport(
                id=f"report_{datetime.utcnow().timestamp()}",
                config=config,
                created_at=datetime.utcnow(),
                file_data=file_data,
                file_name=file_name,
                file_size_bytes=len(file_data),
                row_count=len(data.get("rows", []))
            )

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return None

    async def _gather_data(
        self,
        config: ReportConfig,
        database
    ) -> Dict[str, Any]:
        """Gather data for report"""
        gather_methods = {
            ReportType.USAGE_ANALYTICS: self._gather_usage_data,
            ReportType.COST_ANALYSIS: self._gather_cost_data,
            ReportType.PROPERTY_LISTINGS: self._gather_property_data,
            ReportType.USER_ACTIVITY: self._gather_user_data,
            ReportType.FINANCIAL_SUMMARY: self._gather_financial_data,
            ReportType.AI_PERFORMANCE: self._gather_ai_performance_data,
            ReportType.SYSTEM_HEALTH: self._gather_health_data,
            ReportType.SALES_RECORDS: self._gather_sales_data,
            ReportType.PROJECTIONS: self._gather_projection_data,
            ReportType.FUTURE_GROWTH: self._gather_future_growth_data,
            ReportType.FUTURE_PROJECTS: self._gather_future_projects_data,
            ReportType.INVESTMENT_OPPORTUNITIES: self._gather_investment_data,
        }

        method = gather_methods.get(config.report_type)
        if method:
            return await method(config, database)

        return {"rows": [], "summary": {}}

    async def _gather_usage_data(
        self,
        config: ReportConfig,
        database
    ) -> Dict[str, Any]:
        """Gather usage analytics data"""
        from app.usage_tracker import usage_tracker
        from app.ai_cost_optimizer import ai_cost_optimizer

        # Get data for date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=config.date_range_days)

        # Get usage stats
        endpoint_stats = usage_tracker.get_endpoint_stats()

        # Get cost summary
        cost_summary = ai_cost_optimizer.get_cost_summary(days=config.date_range_days)

        # Format for report
        rows = []
        for endpoint, stats in endpoint_stats.items():
            rows.append({
                "endpoint": endpoint,
                "total_calls": stats["total_calls"],
                "avg_response_time_ms": stats["avg_response_time_ms"],
                "error_rate": stats["error_rate"],
                "bytes_transferred": stats["bytes_transferred"]
            })

        return {
            "title": "Usage Analytics Report",
            "generated_at": datetime.utcnow().isoformat(),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "rows": rows,
            "summary": {
                "total_api_calls": sum(r["total_calls"] for r in rows),
                "avg_response_time": sum(r["avg_response_time_ms"] for r in rows) / len(rows) if rows else 0,
                "total_cost_usd": cost_summary.get("total_cost_usd", 0),
                "cache_hit_rate": cost_summary.get("cache_stats", {}).get("hit_rate_percent", 0)
            }
        }

    async def _gather_cost_data(
        self,
        config: ReportConfig,
        database
    ) -> Dict[str, Any]:
        """Gather cost analysis data"""
        from app.ai_cost_optimizer import ai_cost_optimizer

        summary = ai_cost_optimizer.get_cost_summary(days=config.date_range_days)

        rows = []
        for service_data in summary.get("breakdown_by_service", []):
            rows.append({
                "service": service_data["service"],
                "total_calls": service_data["total_calls"],
                "total_cost_usd": service_data["total_cost_usd"],
                "avg_cost_per_call": service_data["avg_cost_per_call"],
                "cache_hit_rate": service_data["cache_hit_rate"],
                "failed_calls": service_data.get("failed_calls", 0)
            })

        return {
            "title": "AI Cost Analysis Report",
            "generated_at": datetime.utcnow().isoformat(),
            "date_range_days": config.date_range_days,
            "rows": rows,
            "summary": {
                "total_cost_usd": summary["total_cost_usd"],
                "total_api_calls": summary["total_api_calls"],
                "avg_daily_cost": summary["avg_daily_cost"],
                "cache_savings_usd": summary["cache_stats"]["estimated_savings_usd"]
            }
        }

    async def _gather_property_data(
        self,
        config: ReportConfig,
        database
    ) -> Dict[str, Any]:
        """Gather property listings data"""
        # Query properties
        query = {"status": {"$in": ["active", "sold", "pending"]}}

        # Apply filters
        if config.filters.get("city"):
            query["city"] = config.filters["city"]
        if config.filters.get("property_type"):
            query["property_type"] = config.filters["property_type"]
        if config.filters.get("status"):
            query["status"] = config.filters["status"]

        properties = await database.properties.find(query).to_list(length=10000)

        rows = []
        for prop in properties:
            rows.append({
                "property_id": str(prop.get("_id", "")),
                "title": prop.get("title", ""),
                "city": prop.get("city", ""),
                "locality": prop.get("locality", ""),
                "property_type": prop.get("property_type", ""),
                "price": prop.get("price", 0),
                "bedrooms": prop.get("bedrooms", 0),
                "bathrooms": prop.get("bathrooms", 0),
                "area_sqft": prop.get("area", 0),
                "status": prop.get("status", ""),
                "created_at": prop.get("created_at", ""),
                "views": prop.get("views", 0),
                "inquiries": prop.get("inquiry_count", 0)
            })

        # Calculate summary
        total_value = sum(r["price"] for r in rows)
        avg_price = total_value / len(rows) if rows else 0

        return {
            "title": "Property Listings Report",
            "generated_at": datetime.utcnow().isoformat(),
            "total_properties": len(rows),
            "rows": rows,
            "summary": {
                "total_properties": len(rows),
                "active_properties": len([r for r in rows if r["status"] == "active"]),
                "sold_properties": len([r for r in rows if r["status"] == "sold"]),
                "total_value": total_value,
                "average_price": avg_price,
                "total_views": sum(r["views"] for r in rows),
                "total_inquiries": sum(r["inquiries"] for r in rows)
            }
        }

    async def _gather_user_data(
        self,
        config: ReportConfig,
        database
    ) -> Dict[str, Any]:
        """Gather user activity data"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=config.date_range_days)

        # Get users created in period
        users = await database.users.find({
            "created_at": {"$gte": start_date, "$lte": end_date}
        }).to_list(length=10000)

        # Get active users
        active_users = await database.users.find({
            "last_active": {"$gte": start_date}
        }).to_list(length=10000)

        rows = []
        for user in users:
            rows.append({
                "user_id": str(user.get("_id", "")),
                "name": user.get("full_name", ""),
                "email": user.get("email", ""),
                "role": user.get("role", ""),
                "created_at": user.get("created_at", ""),
                "last_active": user.get("last_active", ""),
                "is_verified": user.get("is_verified", False),
                "properties_listed": await database.properties.count_documents({"user_id": str(user.get("_id"))}),
                "inquiries_made": await database.inquiries.count_documents({"user_id": str(user.get("_id"))})
            })

        return {
            "title": "User Activity Report",
            "generated_at": datetime.utcnow().isoformat(),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "rows": rows,
            "summary": {
                "new_users": len(users),
                "active_users": len(active_users),
                "verified_users": len([u for u in rows if u["is_verified"]]),
                "total_listings": sum(r["properties_listed"] for r in rows),
                "total_inquiries": sum(r["inquiries_made"] for r in rows)
            }
        }

    async def _gather_financial_data(
        self,
        config: ReportConfig,
        database
    ) -> Dict[str, Any]:
        """Gather financial summary data"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=config.date_range_days)

        # Get payments/transactions
        payments = await database.payments.find({
            "created_at": {"$gte": start_date, "$lte": end_date},
            "status": "completed"
        }).to_list(length=10000)

        rows = []
        for payment in payments:
            rows.append({
                "transaction_id": payment.get("transaction_id", ""),
                "amount": payment.get("amount", 0),
                "currency": payment.get("currency", "USD"),
                "type": payment.get("type", ""),
                "status": payment.get("status", ""),
                "created_at": payment.get("created_at", ""),
                "user_id": str(payment.get("user_id", "")),
                "property_id": str(payment.get("property_id", ""))
            })

        # Calculate summary
        total_revenue = sum(r["amount"] for r in rows)
        by_type = {}
        for r in rows:
            t = r["type"]
            by_type[t] = by_type.get(t, 0) + r["amount"]

        return {
            "title": "Financial Summary Report",
            "generated_at": datetime.utcnow().isoformat(),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "rows": rows,
            "summary": {
                "total_transactions": len(rows),
                "total_revenue": total_revenue,
                "average_transaction": total_revenue / len(rows) if rows else 0,
                "revenue_by_type": by_type
            }
        }

    async def _gather_ai_performance_data(
        self,
        config: ReportConfig,
        database
    ) -> Dict[str, Any]:
        """Gather AI performance metrics"""
        from app.ai_cost_optimizer import ai_cost_optimizer
        from app.architecture_service import architecture_generator

        # Get AI cost data
        cost_data = ai_cost_optimizer.get_cost_summary(days=config.date_range_days)

        # Get optimization recommendations
        recommendations = ai_cost_optimizer.get_optimization_recommendations()

        rows = cost_data.get("breakdown_by_service", [])

        return {
            "title": "AI Performance Report",
            "generated_at": datetime.utcnow().isoformat(),
            "date_range_days": config.date_range_days,
            "rows": rows,
            "summary": {
                "total_cost": cost_data["total_cost_usd"],
                "total_calls": cost_data["total_api_calls"],
                "cache_hit_rate": cost_data["cache_stats"]["hit_rate_percent"],
                "estimated_savings": cost_data["cache_stats"]["estimated_savings_usd"],
                "optimization_recommendations": len(recommendations)
            },
            "recommendations": recommendations
        }

    async def _gather_health_data(
        self,
        config: ReportConfig,
        database
    ) -> Dict[str, Any]:
        """Gather system health data"""
        from app.service_manager import service_manager
        from app.auto_healing import auto_healing

        # Get service status
        service_status = service_manager.get_all_status()

        # Get healing status
        healing_status = auto_healing.get_health_summary()

        rows = []
        for service_name, status in service_status.items():
            rows.append({
                "service": service_name,
                "status": status.get("status", "unknown"),
                "initialized_at": status.get("initialized_at", ""),
                "error": status.get("error", "")
            })

        return {
            "title": "System Health Report",
            "generated_at": datetime.utcnow().isoformat(),
            "rows": rows,
            "summary": {
                "total_services": len(rows),
                "healthy_services": len([r for r in rows if r["status"] == "ready"]),
                "failed_services": len([r for r in rows if r["status"] == "error"]),
                "auto_recovery_rate": healing_status.get("auto_recovery_rate", 0),
                "recent_failures": healing_status.get("total_failures_24h", 0)
            }
        }

    async def _gather_sales_data(
        self,
        config: ReportConfig,
        database
    ) -> Dict[str, Any]:
        """Gather sales records data"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=config.date_range_days)

        # Get sales records
        query = {"sale_date": {"$gte": start_date, "$lte": end_date}}

        if config.filters.get("status"):
            query["status"] = config.filters["status"]
        if config.filters.get("sale_type"):
            query["sale_type"] = config.filters["sale_type"]
        if config.filters.get("location"):
            query["location"] = config.filters["location"]

        sales = await database.sales_records.find(query).to_list(length=10000)

        rows = []
        for sale in sales:
            rows.append({
                "sale_id": str(sale.get("_id", "")),
                "property_id": sale.get("property_id", ""),
                "seller_id": sale.get("seller_id", ""),
                "buyer_id": sale.get("buyer_id", ""),
                "sale_type": sale.get("sale_type", ""),
                "sale_price": sale.get("sale_price", 0),
                "original_listing_price": sale.get("original_listing_price", 0),
                "commission_amount": sale.get("commission_amount", 0),
                "broker_id": sale.get("broker_id", ""),
                "broker_commission": sale.get("broker_commission", 0),
                "sale_date": sale.get("sale_date", ""),
                "closing_date": sale.get("closing_date", ""),
                "payment_method": sale.get("payment_method", ""),
                "status": sale.get("status", "")
            })

        # Calculate summary statistics
        total_sales = len(rows)
        total_value = sum(r["sale_price"] for r in rows)
        total_commission = sum(r["commission_amount"] for r in rows)
        avg_sale_price = total_value / total_sales if total_sales > 0 else 0

        # Sales by type
        sales_by_type = {}
        for r in rows:
            st = r["sale_type"]
            sales_by_type[st] = sales_by_type.get(st, 0) + 1

        # Top performing brokers
        broker_commissions = {}
        for r in rows:
            broker_id = r.get("broker_id")
            if broker_id:
                broker_commissions[broker_id] = broker_commissions.get(broker_id, 0) + r["broker_commission"]
        top_brokers = sorted(broker_commissions.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "title": "Sales Records Report",
            "generated_at": datetime.utcnow().isoformat(),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "rows": rows,
            "summary": {
                "total_sales": total_sales,
                "total_sales_value": total_value,
                "total_commission": total_commission,
                "average_sale_price": avg_sale_price,
                "sales_by_type": sales_by_type,
                "top_performing_brokers": [{"broker_id": b[0], "commission": b[1]} for b in top_brokers]
            }
        }

    async def _gather_projection_data(
        self,
        config: ReportConfig,
        database
    ) -> Dict[str, Any]:
        """Gather projections and forecasts data"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=config.date_range_days)

        # Get projections
        query = {"created_at": {"$gte": start_date, "$lte": end_date}}

        if config.filters.get("projection_type"):
            query["projection_type"] = config.filters["projection_type"]

        projections = await database.projections.find(query).to_list(length=10000)

        rows = []
        for proj in projections:
            rows.append({
                "projection_id": str(proj.get("_id", "")),
                "projection_type": proj.get("projection_type", ""),
                "title": proj.get("title", ""),
                "location_filter": proj.get("location_filter", ""),
                "property_type_filter": proj.get("property_type_filter", ""),
                "period_start": proj.get("period_start", ""),
                "period_end": proj.get("period_end", ""),
                "projected_value": proj.get("projected_value", 0),
                "confidence_level": proj.get("confidence_level", 0),
                "methodology": proj.get("methodology", ""),
                "data_points_used": proj.get("data_points_used", 0),
                "created_by": proj.get("created_by", ""),
                "created_at": proj.get("created_at", "")
            })

        # Group by projection type
        by_type = {}
        for r in rows:
            pt = r["projection_type"]
            if pt not in by_type:
                by_type[pt] = []
            by_type[pt].append(r)

        # Calculate average confidence by type
        avg_confidence = {}
        for pt, items in by_type.items():
            avg_confidence[pt] = sum(r["confidence_level"] for r in items) / len(items) if items else 0

        return {
            "title": "Projections & Forecasts Report",
            "generated_at": datetime.utcnow().isoformat(),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "rows": rows,
            "summary": {
                "total_projections": len(rows),
                "by_type_counts": {k: len(v) for k, v in by_type.items()},
                "average_confidence_by_type": avg_confidence,
                "high_confidence_projections": len([r for r in rows if r["confidence_level"] >= 0.8])
            }
        }

    async def _gather_future_growth_data(
        self,
        config: ReportConfig,
        database
    ) -> Dict[str, Any]:
        """Gather future growth analysis data"""
        # Get future growth records
        query = {}

        if config.filters.get("location"):
            query["location"] = config.filters["location"]
        if config.filters.get("time_horizon_years"):
            query["time_horizon_years"] = config.filters["time_horizon_years"]

        growth_records = await database.future_growth.find(query).to_list(length=10000)

        rows = []
        for record in growth_records:
            rows.append({
                "growth_id": str(record.get("_id", "")),
                "title": record.get("title", ""),
                "location": record.get("location", ""),
                "growth_rate_projected": record.get("growth_rate_projected", 0),
                "time_horizon_years": record.get("time_horizon_years", 0),
                "property_value_change": record.get("property_value_change", 0),
                "rental_yield_change": record.get("rental_yield_change", 0),
                "demand_index": record.get("demand_index", 0),
                "supply_index": record.get("supply_index", 0),
                "population_growth": record.get("population_growth", 0),
                "ai_confidence_score": record.get("ai_confidence_score", 0),
                "risk_factors": record.get("risk_factors", []),
                "opportunities": record.get("opportunities", []),
                "infrastructure_developments": record.get("infrastructure_developments", []),
                "created_at": record.get("created_at", "")
            })

        # Calculate averages
        avg_growth_rate = sum(r["growth_rate_projected"] for r in rows) / len(rows) if rows else 0
        avg_property_change = sum(r["property_value_change"] for r in rows) / len(rows) if rows else 0
        avg_ai_confidence = sum(r["ai_confidence_score"] for r in rows) / len(rows) if rows else 0

        # High growth locations
        high_growth = [r for r in rows if r["growth_rate_projected"] > avg_growth_rate]

        return {
            "title": "Future Growth Analysis Report",
            "generated_at": datetime.utcnow().isoformat(),
            "rows": rows,
            "summary": {
                "total_analyses": len(rows),
                "average_growth_rate": avg_growth_rate,
                "average_property_value_change": avg_property_change,
                "average_ai_confidence": avg_ai_confidence,
                "high_growth_locations": len(high_growth),
                "top_opportunities": sorted(rows, key=lambda x: x["growth_rate_projected"], reverse=True)[:10]
            }
        }

    async def _gather_future_projects_data(
        self,
        config: ReportConfig,
        database
    ) -> Dict[str, Any]:
        """Gather future/upcoming projects data"""
        # Get future projects
        query = {}

        if config.filters.get("city"):
            query["city"] = config.filters["city"]
        if config.filters.get("project_type"):
            query["project_type"] = config.filters["project_type"]
        if config.filters.get("construction_status"):
            query["construction_status"] = config.filters["construction_status"]
        if config.filters.get("is_verified"):
            query["is_verified"] = config.filters["is_verified"]

        projects = await database.future_projects.find(query).to_list(length=10000)

        rows = []
        for project in projects:
            rows.append({
                "project_id": str(project.get("_id", "")),
                "project_name": project.get("project_name", ""),
                "developer_name": project.get("developer_name", ""),
                "location": project.get("location", ""),
                "city": project.get("city", ""),
                "state": project.get("state", ""),
                "project_type": project.get("project_type", ""),
                "total_units": project.get("total_units", 0),
                "unit_types": project.get("unit_types", []),
                "price_range_min": project.get("price_range_min", 0),
                "price_range_max": project.get("price_range_max", 0),
                "launch_date": project.get("launch_date", ""),
                "completion_date": project.get("completion_date", ""),
                "construction_status": project.get("construction_status", ""),
                "amenities": project.get("amenities", []),
                "expected_roi": project.get("expected_roi", 0),
                "is_verified": project.get("is_verified", False),
                "is_featured": project.get("is_featured", False),
                "created_at": project.get("created_at", "")
            })

        # Summary by status
        by_status = {}
        for r in rows:
            status = r["construction_status"]
            by_status[status] = by_status.get(status, 0) + 1

        # By city
        by_city = {}
        for r in rows:
            city = r["city"]
            by_city[city] = by_city.get(city, 0) + 1

        # Verified vs unverified
        verified_count = len([r for r in rows if r["is_verified"]])

        return {
            "title": "Future Projects Report",
            "generated_at": datetime.utcnow().isoformat(),
            "rows": rows,
            "summary": {
                "total_projects": len(rows),
                "by_status": by_status,
                "by_city": by_city,
                "verified_projects": verified_count,
                "featured_projects": len([r for r in rows if r["is_featured"]]),
                "total_units_in_pipeline": sum(r["total_units"] for r in rows),
                "average_price_range": {
                    "min": sum(r["price_range_min"] for r in rows) / len(rows) if rows else 0,
                    "max": sum(r["price_range_max"] for r in rows) / len(rows) if rows else 0
                }
            }
        }

    async def _gather_investment_data(
        self,
        config: ReportConfig,
        database
    ) -> Dict[str, Any]:
        """Gather investment opportunities data"""
        # Get investment opportunities
        query = {}

        if config.filters.get("status"):
            query["status"] = config.filters["status"]
        if config.filters.get("investment_type"):
            query["investment_type"] = config.filters["investment_type"]
        if config.filters.get("risk_level"):
            query["risk_level"] = config.filters["risk_level"]
        if config.filters.get("location"):
            query["location"] = config.filters["location"]

        opportunities = await database.investment_opportunities.find(query).to_list(length=10000)

        rows = []
        for opp in opportunities:
            rows.append({
                "opportunity_id": str(opp.get("_id", "")),
                "title": opp.get("title", ""),
                "investment_type": opp.get("investment_type", ""),
                "location": opp.get("location", ""),
                "city": opp.get("city", ""),
                "state": opp.get("state", ""),
                "minimum_investment": opp.get("minimum_investment", 0),
                "expected_roi_annual": opp.get("expected_roi_annual", 0),
                "investment_term_months": opp.get("investment_term_months", 0),
                "risk_level": opp.get("risk_level", ""),
                "total_funding_needed": opp.get("total_funding_needed", 0),
                "funding_raised": opp.get("funding_raised", 0),
                "investors_count": opp.get("investors_count", 0),
                "status": opp.get("status", ""),
                "highlights": opp.get("highlights", []),
                "closing_date": opp.get("closing_date", ""),
                "created_at": opp.get("created_at", "")
            })

        # Summary by type
        by_type = {}
        for r in rows:
            it = r["investment_type"]
            by_type[it] = by_type.get(it, 0) + 1

        # By risk level
        by_risk = {}
        for r in rows:
            rl = r["risk_level"]
            by_risk[rl] = by_risk.get(rl, 0) + 1

        # Funding stats
        total_needed = sum(r["total_funding_needed"] or 0 for r in rows)
        total_raised = sum(r["funding_raised"] for r in rows)

        # Top opportunities by ROI
        top_roi = sorted([r for r in rows if r["status"] == "open"],
                        key=lambda x: x["expected_roi_annual"], reverse=True)[:10]

        return {
            "title": "Investment Opportunities Report",
            "generated_at": datetime.utcnow().isoformat(),
            "rows": rows,
            "summary": {
                "total_opportunities": len(rows),
                "by_investment_type": by_type,
                "by_risk_level": by_risk,
                "total_funding_needed": total_needed,
                "total_funding_raised": total_raised,
                "funding_completion_rate": (total_raised / total_needed * 100) if total_needed > 0 else 0,
                "average_roi": sum(r["expected_roi_annual"] for r in rows) / len(rows) if rows else 0,
                "top_opportunities_by_roi": top_roi,
                "open_opportunities": len([r for r in rows if r["status"] == "open"]),
                "funded_opportunities": len([r for r in rows if r["status"] == "funded"])
            }
        }

    async def _generate_csv(
        self,
        config: ReportConfig,
        data: Dict[str, Any]
    ) -> tuple[bytes, str]:
        """Generate CSV report"""
        output = io.StringIO()
        writer = csv.writer(output)

        # Write title and metadata
        writer.writerow([data.get("title", "Report")])
        writer.writerow([f"Generated: {data.get('generated_at', '')}"])
        writer.writerow([])

        # Write summary
        summary = data.get("summary", {})
        writer.writerow(["SUMMARY"])
        for key, value in summary.items():
            writer.writerow([key.replace("_", " ").title(), value])
        writer.writerow([])

        # Write data rows
        rows = data.get("rows", [])
        if rows:
            # Header
            headers = list(rows[0].keys())
            writer.writerow(headers)

            # Data
            for row in rows:
                writer.writerow([row.get(h, "") for h in headers])

        # Convert to bytes
        csv_data = output.getvalue().encode("utf-8")
        file_name = f"{config.report_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

        return csv_data, file_name

    async def _generate_pdf(
        self,
        config: ReportConfig,
        data: Dict[str, Any]
    ) -> tuple[bytes, str]:
        """Generate PDF report"""
        # Create HTML content
        html = self._create_pdf_html(config, data)

        if PDFKIT_AVAILABLE:
            # Generate PDF using pdfkit
            try:
                pdf_data = pdfkit.from_string(html, False)
                file_name = f"{config.report_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
                return pdf_data, file_name
            except Exception as e:
                logger.error(f"PDF generation failed: {e}")
                # Fall back to HTML
                html_data = html.encode("utf-8")
                file_name = f"{config.report_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html"
                return html_data, file_name
        else:
            # Return HTML as fallback
            html_data = html.encode("utf-8")
            file_name = f"{config.report_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html"
            return html_data, file_name

    def _create_pdf_html(self, config: ReportConfig, data: Dict[str, Any]) -> str:
        """Create HTML content for PDF"""
        title = data.get("title", "Report")
        generated_at = data.get("generated_at", "")
        summary = data.get("summary", {})
        rows = data.get("rows", [])

        # Build HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
                h2 {{ color: #555; margin-top: 30px; }}
                .meta {{ color: #777; font-size: 12px; margin-bottom: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #007bff; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .summary {{ background-color: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .summary-item {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #333; }}
                .value {{ color: #007bff; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="meta">Generated: {generated_at}</div>
            
            <h2>Executive Summary</h2>
            <div class="summary">
        """

        # Add summary items
        for key, value in summary.items():
            if isinstance(value, dict):
                html += f'<div class="summary-item"><span class="label">{key.replace("_", " ").title()}:</span></div>'
                for k, v in value.items():
                    html += f'<div class="summary-item" style="margin-left: 20px;">{k.replace("_", " ").title()}: <span class="value">{v}</span></div>'
            else:
                html += f'<div class="summary-item"><span class="label">{key.replace("_", " ").title()}:</span> <span class="value">{value}</span></div>'

        html += "</div>"

        # Add data table
        if rows:
            html += "<h2>Detailed Data</h2><table><thead><tr>"
            headers = list(rows[0].keys())
            for header in headers:
                html += f"<th>{header.replace('_', ' ').title()}</th>"
            html += "</tr></thead><tbody>"

            for row in rows[:100]:  # Limit to 100 rows for PDF
                html += "<tr>"
                for header in headers:
                    val = row.get(header, "")
                    # Truncate long values
                    if isinstance(val, str) and len(val) > 50:
                        val = val[:47] + "..."
                    html += f"<td>{val}</td>"
                html += "</tr>"

            html += "</tbody></table>"

        html += "</body></html>"
        return html

    async def _generate_json(
        self,
        config: ReportConfig,
        data: Dict[str, Any]
    ) -> tuple[bytes, str]:
        """Generate JSON report"""
        json_data = json.dumps(data, indent=2, default=str).encode("utf-8")
        file_name = f"{config.report_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        return json_data, file_name


class ReportScheduler:
    """Schedule automated report generation"""

    def __init__(self):
        self.scheduled_reports: List[Dict] = []
        self.is_running = False

    async def start(self):
        """Start report scheduler"""
        self.is_running = True
        asyncio.create_task(self._scheduler_loop())
        logger.info("Report scheduler started")

    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                now = datetime.utcnow()

                for report in self.scheduled_reports:
                    # Check if due
                    if report.get("next_run") and report["next_run"] <= now:
                        # Generate report
                        await self._generate_scheduled_report(report)

                        # Schedule next run
                        report["next_run"] = now + timedelta(days=report.get("frequency_days", 7))

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(3600)

    async def _generate_scheduled_report(self, report_config: Dict):
        """Generate a scheduled report"""
        try:
            from app.database import get_db
            database = get_db()

            config = ReportConfig(
                report_type=ReportType(report_config["report_type"]),
                format=ReportFormat(report_config["format"]),
                title=report_config["title"],
                description=report_config.get("description", ""),
                date_range_days=report_config.get("date_range_days", 30)
            )

            generator = ReportGenerator()
            report = await generator.generate_report(config, database)

            if report:
                # Store report
                await database.generated_reports.insert_one({
                    "report_id": report.id,
                    "config": {
                        "report_type": config.report_type.value,
                        "format": config.format.value,
                        "title": config.title
                    },
                    "created_at": report.created_at,
                    "file_name": report.file_name,
                    "file_size": report.file_size_bytes,
                    "row_count": report.row_count,
                    "stakeholder_emails": report_config.get("emails", [])
                })

                # Send email notification
                if report_config.get("emails"):
                    await self._send_report_email(report, report_config["emails"])

                logger.info(f"Scheduled report generated: {report.file_name}")

        except Exception as e:
            logger.error(f"Scheduled report generation failed: {e}")

    async def _send_report_email(self, report: GeneratedReport, emails: List[str]):
        """Send report via email"""
        try:
            from app.notification import notification_manager

            await notification_manager.send_notification(
                type="email",
                recipients=emails,
                subject=f"Scheduled Report: {report.config.title}",
                body=f"Please find attached the scheduled report: {report.file_name}",
                attachments=[{
                    "filename": report.file_name,
                    "data": report.file_data
                }]
            )

        except Exception as e:
            logger.error(f"Failed to send report email: {e}")

    def schedule_report(
        self,
        report_type: str,
        format: str,
        title: str,
        frequency_days: int,
        emails: List[str],
        date_range_days: int = 30
    ):
        """Add a scheduled report"""
        self.scheduled_reports.append({
            "report_type": report_type,
            "format": format,
            "title": title,
            "frequency_days": frequency_days,
            "emails": emails,
            "date_range_days": date_range_days,
            "next_run": datetime.utcnow() + timedelta(days=frequency_days)
        })
        logger.info(f"Report scheduled: {title} (every {frequency_days} days)")


# Global instances
report_generator = ReportGenerator()
report_scheduler = ReportScheduler()
