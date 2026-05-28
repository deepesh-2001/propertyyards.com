"""
Real-Time Analytics & Predictions Router
WebSocket and REST endpoints for live analytics and forecasts
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, timedelta

from app.auth import get_current_user
from app.database import get_db
from app.realtime_analytics import realtime_collector, alert_manager, change_detector
from app.predictive_analytics import predictive_analytics
from app.websocket_manager import (
    connection_manager,
    analytics_websocket,
    notification_websocket,
    property_updates
)

router = APIRouter(prefix="/api/realtime", tags=["realtime"])


# ========== REST Endpoints ==========

@router.get("/dashboard")
async def get_realtime_dashboard(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get real-time dashboard data"""
    try:
        dashboard_data = realtime_collector.get_live_dashboard_data()

        # Get recent alerts
        recent_alerts = alert_manager.get_recent_alerts(10)

        # Get active connections
        connection_stats = {
            "active_connections": connection_manager.get_connection_count(),
            "active_users": connection_manager.get_user_count()
        }

        return {
            **dashboard_data,
            "recent_alerts": recent_alerts,
            "connection_stats": connection_stats,
            "server_time": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_minute_history(
    minutes: int = Query(60, ge=1, le=120),
    current_user: dict = Depends(get_current_user)
):
    """Get minute-by-minute history"""
    try:
        history = realtime_collector.get_history(minutes)
        return {
            "period": f"last_{minutes}_minutes",
            "data": [m.to_dict() for m in history],
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_recent_alerts(
    count: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get recent alerts"""
    try:
        alerts = alert_manager.get_recent_alerts(count)
        return {
            "alerts": alerts,
            "count": len(alerts),
            "unacknowledged": len([a for a in alerts if not a.get("acknowledged")])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecasts")
async def get_predictions(
    period: int = Query(30, ge=7, le=90),
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get future predictions and forecasts"""
    try:
        forecasts = await predictive_analytics.generate_dashboard_forecasts(database)

        return {
            **forecasts,
            "forecast_days": period,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-outlook")
async def get_market_outlook(
    city: Optional[str] = None,
    property_type: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get market outlook for next 30 days"""
    try:
        # Get historical data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=60)

        # Build query
        query = {"status": "active"}
        if city:
            query["city"] = city
        if property_type:
            query["property_type"] = property_type

        # Get price history (simplified)
        pipeline = [
            {"$match": {**query, "created_at": {"$gte": start_date}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "avg_price": {"$avg": "$price"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]

        price_history = await database.properties.aggregate(pipeline).to_list(length=60)
        prices = [p["avg_price"] for p in price_history if p["avg_price"]]

        inquiries_pipeline = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]

        inquiry_history = await database.inquiries.aggregate(inquiries_pipeline).to_list(length=60)
        inquiries = [i["count"] for i in inquiry_history]

        views = [i * 10 for i in inquiries]  # Estimate views

        # Generate predictions
        from app.predictive_analytics import MarketPredictor
        predictor = MarketPredictor()

        demand_forecast = await predictor.predict_property_demand(inquiries, views, 30)
        price_forecast = await predictor.predict_price_trends(prices, 30) if prices else None

        return {
            "filters": {"city": city, "property_type": property_type},
            "demand_forecast": demand_forecast,
            "price_forecast": price_forecast,
            "historical_data_points": len(prices),
            "outlook_period": "30 days",
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record-event")
async def record_analytics_event(
    event_type: str,
    value: Optional[float] = None,
    current_user: dict = Depends(get_current_user)
):
    """Record a real-time analytics event"""
    try:
        if event_type == "page_view":
            await realtime_collector.record_page_view(1)
        elif event_type == "api_call":
            await realtime_collector.record_api_call(value or 100.0)
        elif event_type == "new_user":
            await realtime_collector.record_new_user()
        elif event_type == "new_property":
            await realtime_collector.record_new_property()
        elif event_type == "new_inquiry":
            await realtime_collector.record_new_inquiry()
        elif event_type == "error":
            await realtime_collector.record_error()
        elif event_type == "revenue":
            await realtime_collector.record_revenue(value or 0)

        return {"message": "Event recorded", "type": event_type}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== WebSocket Endpoints ==========

@router.websocket("/ws/analytics")
async def websocket_analytics(
    websocket: WebSocket,
    client_id: Optional[str] = None
):
    """WebSocket for real-time analytics updates"""
    client_id = client_id or f"anon_{id(websocket)}"

    await analytics_websocket.handle_analytics_connection(
        websocket, client_id
    )


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: str
):
    """WebSocket for user notifications"""
    client_id = f"user_{user_id}_{id(websocket)}"

    await notification_websocket.handle_notification_connection(
        websocket, client_id, user_id
    )


@router.websocket("/ws/property/{property_id}")
async def websocket_property(
    websocket: WebSocket,
    property_id: str,
    user_id: Optional[str] = None
):
    """WebSocket for live property updates"""
    client_id = f"prop_{property_id}_{id(websocket)}"

    await property_updates.handle_property_connection(
        websocket, client_id, property_id, user_id
    )


# ========== Admin Endpoints ==========

@router.get("/admin/connections")
async def get_connection_stats(
    current_user: dict = Depends(get_current_user)
):
    """Get WebSocket connection statistics (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return {
        "active_connections": connection_manager.get_connection_count(),
        "active_users": connection_manager.get_user_count(),
        "analytics_subscribers": len(analytics_websocket.subscribers),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/admin/broadcast")
async def broadcast_message(
    message: dict,
    current_user: dict = Depends(get_current_user)
):
    """Broadcast message to all connected clients (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    await connection_manager.broadcast({
        "type": "admin_broadcast",
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    })

    return {"message": "Broadcast sent", "connections": connection_manager.get_connection_count()}
