"""
Reports Router
Endpoints for generating and downloading Excel reports
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from app.database import get_database
from app.reports import ReportGenerator, ReportType
from app.info_collection import InfoCollection, InfoType
from app.auth import decode_token
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def get_current_user(authorization: str = None) -> dict:
    """Extract current user from authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token = authorization.split(" ")[1]
        token_data = decode_token(token)
        if token_data:
            return {"user_id": token_data.user_id, "email": token_data.email, "role": token_data.role}
    except Exception:
        pass

    raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/daily-summary")
async def get_daily_summary_report(
    date: str = None,
    authorization: str = None,
    db = Depends(get_database)
):
    """Generate daily summary report as Excel"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    report_generator = ReportGenerator(db)
    
    report_date = None
    if date:
        try:
            report_date = datetime.fromisoformat(date)
        except:
            pass
    
    report_data = await report_generator.generate_daily_summary_report(report_date)
    
    filename = f"daily_summary_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return Response(
        content=report_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/property-listings")
async def get_property_listings_report(
    start_date: str = None,
    end_date: str = None,
    authorization: str = None,
    db = Depends(get_database)
):
    """Generate property listings report as Excel"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    report_generator = ReportGenerator(db)
    
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except:
            pass
    
    report_data = await report_generator.generate_property_listings_report(start_dt, end_dt)
    
    filename = f"property_listings_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return Response(
        content=report_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/user-activity")
async def get_user_activity_report(
    start_date: str = None,
    end_date: str = None,
    authorization: str = None,
    db = Depends(get_database)
):
    """Generate user activity report as Excel"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    report_generator = ReportGenerator(db)
    
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except:
            pass
    
    report_data = await report_generator.generate_user_activity_report(start_dt, end_dt)
    
    filename = f"user_activity_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return Response(
        content=report_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/inquiries")
async def get_inquiries_report(
    start_date: str = None,
    end_date: str = None,
    authorization: str = None,
    db = Depends(get_database)
):
    """Generate inquiries report as Excel"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    report_generator = ReportGenerator(db)
    
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except:
            pass
    
    report_data = await report_generator.generate_inquiries_report(start_dt, end_dt)
    
    filename = f"inquiries_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return Response(
        content=report_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/leads")
async def get_leads_report(
    start_date: str = None,
    end_date: str = None,
    authorization: str = None,
    db = Depends(get_database)
):
    """Generate CRM leads report as Excel"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    report_generator = ReportGenerator(db)
    
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except:
            pass
    
    report_data = await report_generator.generate_leads_report(start_dt, end_dt)
    
    filename = f"crm_leads_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return Response(
        content=report_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/broker-performance")
async def get_broker_performance_report(
    start_date: str = None,
    end_date: str = None,
    authorization: str = None,
    db = Depends(get_database)
):
    """Generate broker performance report as Excel"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    report_generator = ReportGenerator(db)
    
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except:
            pass
    
    report_data = await report_generator.generate_broker_performance_report(start_dt, end_dt)
    
    filename = f"broker_performance_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return Response(
        content=report_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/rental")
async def get_rental_report(
    start_date: str = None,
    end_date: str = None,
    authorization: str = None,
    db = Depends(get_database)
):
    """Generate rental properties report as Excel"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    report_generator = ReportGenerator(db)
    
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except:
            pass
    
    report_data = await report_generator.generate_rental_report(start_dt, end_dt)
    
    filename = f"rental_properties_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return Response(
        content=report_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/info")
async def collect_info(
    info_type: str,
    data: dict,
    source: str = "manual",
    authorization: str = None,
    db = Depends(get_database)
):
    """Collect and store user information"""
    current_user = get_current_user(authorization)
    
    info_collection = InfoCollection(db)
    
    try:
        info_type_enum = InfoType(info_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid info type")
    
    info_id = await info_collection.collect_info(
        user_id=current_user["user_id"],
        info_type=info_type_enum,
        data=data,
        source=source
    )
    
    return {"message": "Information collected successfully", "info_id": info_id}


@router.get("/info")
async def get_user_info(
    info_type: str = None,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get collected information for current user"""
    current_user = get_current_user(authorization)
    
    info_collection = InfoCollection(db)
    
    info_type_enum = None
    if info_type:
        try:
            info_type_enum = InfoType(info_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid info type")
    
    info_list = await info_collection.get_user_info(current_user["user_id"], info_type_enum)
    
    return {"items": info_list, "count": len(info_list)}


@router.get("/info/summary")
async def get_info_summary(
    authorization: str = None,
    db = Depends(get_database)
):
    """Get summary statistics of collected information"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    info_collection = InfoCollection(db)
    
    stats = await info_collection.get_summary_stats()

    return stats


# ========== Stakeholder CSV/PDF Reports ==========

from app.report_generator import report_generator, ReportConfig, ReportType, ReportFormat
from fastapi.responses import StreamingResponse


@router.post("/stakeholder/generate")
async def generate_stakeholder_report(
    report_type: str,  # usage_analytics, cost_analysis, property_listings, user_activity, financial_summary, ai_performance, system_health
    format: str,  # csv, pdf, json
    date_range_days: int = 30,
    title: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
    stakeholder_level: str = "executive",  # executive, manager, technical
    current_user: dict = Depends(get_current_user),
    database=Depends(get_db)
):
    """Generate stakeholder report in CSV or PDF format"""
    if current_user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Admin or Manager access required")

    try:
        # Map report type
        report_type_enum = ReportType(report_type)
        format_enum = ReportFormat(format)

        # Set default title if not provided
        if not title:
            title = f"{report_type_enum.value.replace('_', ' ').title()} Report"

        # Create config
        config = ReportConfig(
            report_type=report_type_enum,
            format=format_enum,
            title=title,
            description=f"Generated for {stakeholder_level} stakeholders",
            date_range_days=date_range_days,
            filters=filters or {},
            include_charts=True,
            stakeholder_level=stakeholder_level
        )

        # Generate report
        report = await report_generator.generate_report(config, database)

        if not report:
            raise HTTPException(status_code=500, detail="Report generation failed")

        # Store report metadata
        await database.stakeholder_reports.insert_one({
            "report_id": report.id,
            "generated_by": current_user.get("_id"),
            "report_type": report_type,
            "format": format,
            "title": title,
            "created_at": report.created_at,
            "file_name": report.file_name,
            "file_size": report.file_size_bytes,
            "row_count": report.row_count,
            "stakeholder_level": stakeholder_level
        })

        # Return as downloadable file
        media_type = "text/csv" if format == "csv" else "application/pdf" if format == "pdf" else "application/json"

        return StreamingResponse(
            io.BytesIO(report.file_data),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={report.file_name}"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid report type or format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stakeholder/list")
async def list_stakeholder_reports(
    report_type: Optional[str] = None,
    format: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    database=Depends(get_db)
):
    """List generated stakeholder reports"""
    if current_user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Admin or Manager access required")

    try:
        query = {}
        if report_type:
            query["report_type"] = report_type
        if format:
            query["format"] = format

        reports = await database.stakeholder_reports.find(query).sort(
            "created_at", -1
        ).limit(limit).to_list(length=limit)

        return {
            "reports": [
                {
                    "report_id": r["report_id"],
                    "title": r["title"],
                    "report_type": r["report_type"],
                    "format": r["format"],
                    "created_at": r["created_at"],
                    "file_name": r["file_name"],
                    "file_size_kb": round(r["file_size"] / 1024, 2),
                    "row_count": r["row_count"],
                    "stakeholder_level": r.get("stakeholder_level", "executive")
                }
                for r in reports
            ],
            "count": len(reports)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stakeholder/download/{report_id}")
async def download_stakeholder_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    database=Depends(get_db)
):
    """Download a previously generated stakeholder report"""
    if current_user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Admin or Manager access required")

    try:
        # Find report metadata
        report_meta = await database.stakeholder_reports.find_one({"report_id": report_id})

        if not report_meta:
            raise HTTPException(status_code=404, detail="Report not found")

        # For now, regenerate the report (in production, store files in S3/local storage)
        # This ensures the data is fresh
        config = ReportConfig(
            report_type=ReportType(report_meta["report_type"]),
            format=ReportFormat(report_meta["format"]),
            title=report_meta["title"],
            description="",
            date_range_days=30,
            stakeholder_level=report_meta.get("stakeholder_level", "executive")
        )

        report = await report_generator.generate_report(config, database)

        if not report:
            raise HTTPException(status_code=500, detail="Could not regenerate report")

        media_type = "text/csv" if report_meta["format"] == "csv" else "application/pdf" if report_meta["format"] == "pdf" else "application/json"

        return StreamingResponse(
            io.BytesIO(report.file_data),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={report.file_name}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stakeholder/schedule")
async def schedule_stakeholder_report(
    report_type: str,
    format: str,
    frequency_days: int,  # 1, 7, 14, 30
    emails: List[str],
    title: str,
    date_range_days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Schedule automated stakeholder reports"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.report_generator import report_scheduler

        report_scheduler.schedule_report(
            report_type=report_type,
            format=format,
            title=title,
            frequency_days=frequency_days,
            emails=emails,
            date_range_days=date_range_days
        )

        return {
            "message": "Report scheduled successfully",
            "report_type": report_type,
            "format": format,
            "frequency_days": frequency_days,
            "emails": emails,
            "next_run": (datetime.utcnow() + timedelta(days=frequency_days)).isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stakeholder/report-types")
async def get_stakeholder_report_types(
    current_user: dict = Depends(get_current_user)
):
    """Get available stakeholder report types and formats"""
    if current_user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Admin or Manager access required")

    return {
        "report_types": [
            {"value": "usage_analytics", "name": "Usage Analytics", "description": "API usage, endpoints, response times"},
            {"value": "cost_analysis", "name": "Cost Analysis", "description": "AI costs, service breakdown, savings"},
            {"value": "property_listings", "name": "Property Listings", "description": "Properties, prices, performance"},
            {"value": "user_activity", "name": "User Activity", "description": "User growth, engagement, activity"},
            {"value": "financial_summary", "name": "Financial Summary", "description": "Revenue, transactions, payments"},
            {"value": "ai_performance", "name": "AI Performance", "description": "AI metrics, optimization, recommendations"},
            {"value": "system_health", "name": "System Health", "description": "Service status, health, uptime"}
        ],
        "formats": [
            {"value": "csv", "name": "CSV", "description": "Spreadsheet format for Excel/Google Sheets"},
            {"value": "pdf", "name": "PDF", "description": "Document format for presentations"},
            {"value": "json", "name": "JSON", "description": "Machine-readable format for integrations"}
        ],
        "stakeholder_levels": [
            {"value": "executive", "name": "Executive", "description": "High-level summary for C-suite"},
            {"value": "manager", "name": "Manager", "description": "Operational metrics for team leads"},
            {"value": "technical", "name": "Technical", "description": "Detailed data for engineers"}
        ]
    }

import io
