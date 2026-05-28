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
