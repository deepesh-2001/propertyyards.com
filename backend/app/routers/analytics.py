"""
Enhanced Analytics Router
Handles comprehensive analytics endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.schemas import (
    PropertyAnalytics,
    UserAnalytics,
    RevenueAnalytics,
    CommissionAnalytics,
    InquiryAnalytics,
    DashboardAnalytics
)
from app.analytics import analytics_manager
from app.auth import get_current_user
from app.feature_flags import require_feature_flag

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/properties", response_model=PropertyAnalytics)
@require_feature_flag("advanced_analytics")
async def get_property_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive property analytics"""
    try:
        analytics = await analytics_manager.get_property_analytics(
            database=database,
            start_date=start_date,
            end_date=end_date
        )
        return PropertyAnalytics(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users", response_model=UserAnalytics)
@require_feature_flag("advanced_analytics")
async def get_user_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive user analytics"""
    try:
        analytics = await analytics_manager.get_user_analytics(
            database=database,
            start_date=start_date,
            end_date=end_date
        )
        return UserAnalytics(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/revenue", response_model=RevenueAnalytics)
@require_feature_flag("advanced_analytics")
async def get_revenue_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive revenue analytics"""
    try:
        analytics = await analytics_manager.get_revenue_analytics(
            database=database,
            start_date=start_date,
            end_date=end_date
        )
        return RevenueAnalytics(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commissions", response_model=CommissionAnalytics)
@require_feature_flag("advanced_analytics")
async def get_commission_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive commission analytics"""
    try:
        analytics = await analytics_manager.get_commission_analytics(
            database=database,
            start_date=start_date,
            end_date=end_date
        )
        return CommissionAnalytics(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inquiries", response_model=InquiryAnalytics)
@require_feature_flag("advanced_analytics")
async def get_inquiry_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive inquiry analytics"""
    try:
        analytics = await analytics_manager.get_inquiry_analytics(
            database=database,
            start_date=start_date,
            end_date=end_date
        )
        return InquiryAnalytics(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard", response_model=DashboardAnalytics)
@require_feature_flag("advanced_analytics")
async def get_dashboard_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get combined dashboard analytics"""
    try:
        analytics = await analytics_manager.get_dashboard_analytics(
            database=database,
            start_date=start_date,
            end_date=end_date
        )
        return DashboardAnalytics(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
