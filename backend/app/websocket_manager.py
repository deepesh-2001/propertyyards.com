"""
WebSocket Manager for Real-Time Updates
Handles live analytics, notifications, and real-time data streams
"""
from typing import Dict, List, Set, Optional, Callable, Any
from datetime import datetime
import asyncio
import logging
import json
from fastapi import WebSocket, WebSocketDisconnect

from app.realtime_analytics import realtime_collector, alert_manager
from app.predictive_analytics import predictive_analytics

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.connection_users: Dict[str, str] = {}  # connection_id -> user_id

    async def connect(self, websocket: WebSocket, client_id: str, user_id: Optional[str] = None):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket

        if user_id:
            self.connection_users[client_id] = user_id
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(client_id)

        logger.info(f"WebSocket connected: {client_id} (user: {user_id})")

    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        # Remove from user mappings
        user_id = self.connection_users.get(client_id)
        if user_id:
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(client_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            del self.connection_users[client_id]

        logger.info(f"WebSocket disconnected: {client_id}")

    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Send error to {client_id}: {e}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []

        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast error to {client_id}: {e}")
                disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

    async def broadcast_to_user(self, message: dict, user_id: str):
        """Send message to all connections of a specific user"""
        if user_id in self.user_connections:
            for client_id in self.user_connections[user_id]:
                await self.send_personal_message(message, client_id)

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)

    def get_user_count(self) -> int:
        """Get number of unique connected users"""
        return len(self.user_connections)


class RealtimeAnalyticsWebSocket:
    """WebSocket handler for real-time analytics"""

    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager
        self.subscribers: Set[str] = set()

    async def handle_analytics_connection(
        self,
        websocket: WebSocket,
        client_id: str,
        user_id: Optional[str] = None
    ):
        """Handle analytics WebSocket connection"""
        await self.manager.connect(websocket, client_id, user_id)

        try:
            # Send initial data
            await self.send_current_analytics(client_id)

            # Subscribe to minute updates
            self.subscribers.add(client_id)

            # Handle client messages
            while True:
                try:
                    data = await websocket.receive_json()
                    await self.handle_client_message(client_id, data)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"WebSocket message error: {e}")

        finally:
            self.subscribers.discard(client_id)
            self.manager.disconnect(client_id)

    async def handle_client_message(self, client_id: str, data: dict):
        """Handle message from client"""
        action = data.get("action")

        if action == "get_current":
            await self.send_current_analytics(client_id)

        elif action == "get_history":
            minutes = data.get("minutes", 60)
            await self.send_history(client_id, minutes)

        elif action == "subscribe_alerts":
            # Subscribe to real-time alerts
            pass

    async def send_current_analytics(self, client_id: str):
        """Send current analytics data to client"""
        dashboard_data = realtime_collector.get_live_dashboard_data()

        await self.manager.send_personal_message({
            "type": "analytics_update",
            "data": dashboard_data,
            "timestamp": datetime.utcnow().isoformat()
        }, client_id)

    async def send_history(self, client_id: str, minutes: int):
        """Send historical analytics"""
        history = realtime_collector.get_history(minutes)

        await self.manager.send_personal_message({
            "type": "analytics_history",
            "data": [m.to_dict() for m in history],
            "period": f"last_{minutes}_minutes"
        }, client_id)

    async def broadcast_minute_update(self, metrics):
        """Broadcast minute update to all subscribers"""
        if not self.subscribers:
            return

        message = {
            "type": "minute_update",
            "data": metrics.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }

        for client_id in list(self.subscribers):
            await self.manager.send_personal_message(message, client_id)

    async def broadcast_alert(self, alert: dict):
        """Broadcast alert to all subscribers"""
        message = {
            "type": "alert",
            "alert": alert,
            "timestamp": datetime.utcnow().isoformat()
        }

        for client_id in list(self.subscribers):
            await self.manager.send_personal_message(message, client_id)


class NotificationWebSocket:
    """WebSocket handler for notifications"""

    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager

    async def handle_notification_connection(
        self,
        websocket: WebSocket,
        client_id: str,
        user_id: str
    ):
        """Handle notification WebSocket connection"""
        if not user_id:
            await websocket.close(code=4001, reason="Authentication required")
            return

        await self.manager.connect(websocket, client_id, user_id)

        try:
            # Send any pending notifications
            await self.send_pending_notifications(client_id, user_id)

            # Keep connection alive
            while True:
                try:
                    data = await websocket.receive_json()
                    await self.handle_client_message(client_id, user_id, data)
                except WebSocketDisconnect:
                    break

        finally:
            self.manager.disconnect(client_id)

    async def handle_client_message(self, client_id: str, user_id: str, data: dict):
        """Handle message from client"""
        action = data.get("action")

        if action == "mark_read":
            notification_id = data.get("notification_id")
            # Mark notification as read
            pass

    async def send_pending_notifications(self, client_id: str, user_id: str):
        """Send pending notifications to user"""
        # Fetch pending notifications from database
        # For now, send empty
        await self.manager.send_personal_message({
            "type": "pending_notifications",
            "notifications": [],
            "count": 0
        }, client_id)

    async def send_notification(self, user_id: str, notification: dict):
        """Send notification to specific user"""
        await self.manager.broadcast_to_user({
            "type": "notification",
            "notification": notification,
            "timestamp": datetime.utcnow().isoformat()
        }, user_id)


class LivePropertyUpdates:
    """WebSocket handler for live property updates"""

    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager
        self.property_subscribers: Dict[str, Set[str]] = {}  # property_id -> client_ids

    async def handle_property_connection(
        self,
        websocket: WebSocket,
        client_id: str,
        property_id: str,
        user_id: Optional[str] = None
    ):
        """Handle connection for live property updates"""
        await self.manager.connect(websocket, client_id, user_id)

        # Subscribe to property updates
        if property_id not in self.property_subscribers:
            self.property_subscribers[property_id] = set()
        self.property_subscribers[property_id].add(client_id)

        try:
            # Send initial property data
            await self.send_property_data(client_id, property_id)

            while True:
                try:
                    data = await websocket.receive_json()
                    await self.handle_client_message(client_id, data)
                except WebSocketDisconnect:
                    break

        finally:
            self.property_subscribers.get(property_id, set()).discard(client_id)
            self.manager.disconnect(client_id)

    async def send_property_data(self, client_id: str, property_id: str):
        """Send property data to client"""
        # Fetch property from database
        from app.database import get_db
        database = get_db()

        property_data = await database.properties.find_one({"_id": property_id})

        if property_data:
            property_data["id"] = str(property_data["_id"])
            del property_data["_id"]

            await self.manager.send_personal_message({
                "type": "property_data",
                "property": property_data
            }, client_id)

    async def broadcast_property_update(self, property_id: str, update: dict):
        """Broadcast property update to all subscribers"""
        if property_id not in self.property_subscribers:
            return

        message = {
            "type": "property_update",
            "property_id": property_id,
            "update": update,
            "timestamp": datetime.utcnow().isoformat()
        }

        for client_id in list(self.property_subscribers[property_id]):
            await self.manager.send_personal_message(message, client_id)

    async def handle_client_message(self, client_id: str, data: dict):
        """Handle message from client"""
        pass


# Global connection manager
connection_manager = ConnectionManager()
analytics_websocket = RealtimeAnalyticsWebSocket(connection_manager)
notification_websocket = NotificationWebSocket(connection_manager)
property_updates = LivePropertyUpdates(connection_manager)


# Subscribe real-time analytics to WebSocket broadcasts
def on_new_minute(metrics):
    """Callback for new minute data - broadcast to WebSocket clients"""
    asyncio.create_task(analytics_websocket.broadcast_minute_update(metrics))


def on_new_alert(alert):
    """Callback for new alert - broadcast to WebSocket clients"""
    asyncio.create_task(analytics_websocket.broadcast_alert(alert))


# Register callbacks
realtime_collector.subscribe(on_new_minute)
alert_manager.subscribe(on_new_alert)
