"""
Time-Series Data Storage
Efficient storage for analytics trends and historical data
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TimeSeriesGranularity(str, Enum):
    """Time series data granularity"""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class TimeSeriesManager:
    """Manager for time-series data storage"""

    def __init__(self):
        self.retention_policies = {
            TimeSeriesGranularity.MINUTE: timedelta(hours=24),      # Keep 24 hours
            TimeSeriesGranularity.HOUR: timedelta(days=7),           # Keep 7 days
            TimeSeriesGranularity.DAY: timedelta(days=365),          # Keep 1 year
            TimeSeriesGranularity.WEEK: timedelta(days=730),         # Keep 2 years
            TimeSeriesGranularity.MONTH: timedelta(days=1825),       # Keep 5 years
            TimeSeriesGranularity.YEAR: timedelta(days=3650)       # Keep 10 years
        }

    async def store_metric(
        self,
        metric_name: str,
        value: float,
        tags: Dict[str, str],
        granularity: TimeSeriesGranularity,
        database
    ):
        """Store a time-series metric"""
        try:
            # Round timestamp to granularity
            timestamp = self._round_timestamp(datetime.utcnow(), granularity)

            # Create composite key for upsert
            key_filter = {
                "metric_name": metric_name,
                "timestamp": timestamp,
                "granularity": granularity.value
            }
            for tag_key, tag_value in tags.items():
                key_filter[f"tags.{tag_key}"] = tag_value

            # Upsert the metric
            await database.timeseries.update_one(
                key_filter,
                {
                    "$setOnInsert": {
                        "metric_name": metric_name,
                        "timestamp": timestamp,
                        "granularity": granularity.value,
                        "tags": tags,
                        "created_at": datetime.utcnow()
                    },
                    "$set": {
                        "value": value,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )

        except Exception as e:
            logger.error(f"Time-series store error: {e}")

    async def store_aggregated_metric(
        self,
        metric_name: str,
        values: List[float],
        tags: Dict[str, str],
        granularity: TimeSeriesGranularity,
        database
    ):
        """Store aggregated metrics (min, max, avg, sum, count)"""
        try:
            timestamp = self._round_timestamp(datetime.utcnow(), granularity)

            if not values:
                return

            aggregated = {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "sum": sum(values),
                "count": len(values)
            }

            key_filter = {
                "metric_name": metric_name,
                "timestamp": timestamp,
                "granularity": granularity.value
            }
            for tag_key, tag_value in tags.items():
                key_filter[f"tags.{tag_key}"] = tag_value

            await database.timeseries.update_one(
                key_filter,
                {
                    "$setOnInsert": {
                        "metric_name": metric_name,
                        "timestamp": timestamp,
                        "granularity": granularity.value,
                        "tags": tags,
                        "created_at": datetime.utcnow()
                    },
                    "$set": {
                        **aggregated,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )

        except Exception as e:
            logger.error(f"Time-series aggregated store error: {e}")

    async def get_metrics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        granularity: TimeSeriesGranularity,
        tags: Optional[Dict[str, str]] = None,
        database = None
    ) -> List[Dict[str, Any]]:
        """Get time-series metrics for a time range"""
        try:
            query = {
                "metric_name": metric_name,
                "granularity": granularity.value,
                "timestamp": {
                    "$gte": start_time,
                    "$lte": end_time
                }
            }

            if tags:
                for tag_key, tag_value in tags.items():
                    query[f"tags.{tag_key}"] = tag_value

            cursor = database.timeseries.find(query).sort("timestamp", 1)
            results = await cursor.to_list(length=10000)

            # Format results
            formatted = []
            for r in results:
                r["id"] = str(r["_id"])
                del r["_id"]
                formatted.append(r)

            return formatted

        except Exception as e:
            logger.error(f"Time-series get error: {e}")
            return []

    async def get_latest_metric(
        self,
        metric_name: str,
        tags: Optional[Dict[str, str]] = None,
        database = None
    ) -> Optional[Dict[str, Any]]:
        """Get the latest metric value"""
        try:
            query = {"metric_name": metric_name}

            if tags:
                for tag_key, tag_value in tags.items():
                    query[f"tags.{tag_key}"] = tag_value

            result = await database.timeseries.find_one(
                query,
                sort=[("timestamp", -1)]
            )

            if result:
                result["id"] = str(result["_id"])
                del result["_id"]

            return result

        except Exception as e:
            logger.error(f"Time-series get latest error: {e}")
            return None

    async def cleanup_old_data(self, database):
        """Clean up old time-series data based on retention policies"""
        try:
            total_deleted = 0

            for granularity, retention in self.retention_policies.items():
                cutoff_date = datetime.utcnow() - retention

                result = await database.timeseries.delete_many({
                    "granularity": granularity.value,
                    "timestamp": {"$lt": cutoff_date}
                })

                total_deleted += result.deleted_count
                logger.info(f"Cleaned up {result.deleted_count} old {granularity.value} metrics")

            return total_deleted

        except Exception as e:
            logger.error(f"Time-series cleanup error: {e}")
            return 0

    def _round_timestamp(
        self,
        timestamp: datetime,
        granularity: TimeSeriesGranularity
    ) -> datetime:
        """Round timestamp to granularity boundary"""
        if granularity == TimeSeriesGranularity.MINUTE:
            return timestamp.replace(second=0, microsecond=0)
        elif granularity == TimeSeriesGranularity.HOUR:
            return timestamp.replace(minute=0, second=0, microsecond=0)
        elif granularity == TimeSeriesGranularity.DAY:
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        elif granularity == TimeSeriesGranularity.WEEK:
            # Round to start of week (Monday)
            days_since_monday = timestamp.weekday()
            start_of_week = timestamp - timedelta(days=days_since_monday)
            return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        elif granularity == TimeSeriesGranularity.MONTH:
            return timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif granularity == TimeSeriesGranularity.YEAR:
            return timestamp.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return timestamp

    async def get_metric_summary(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        database
    ) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        try:
            pipeline = [
                {
                    "$match": {
                        "metric_name": metric_name,
                        "timestamp": {
                            "$gte": start_time,
                            "$lte": end_time
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "avg": {"$avg": "$value"},
                        "min": {"$min": "$value"},
                        "max": {"$max": "$value"},
                        "sum": {"$sum": "$value"},
                        "count": {"$sum": 1}
                    }
                }
            ]

            result = await database.timeseries.aggregate(pipeline).to_list(length=1)

            if result:
                return {
                    "average": result[0].get("avg", 0),
                    "minimum": result[0].get("min", 0),
                    "maximum": result[0].get("max", 0),
                    "total": result[0].get("sum", 0),
                    "count": result[0].get("count", 0)
                }

            return {"average": 0, "minimum": 0, "maximum": 0, "total": 0, "count": 0}

        except Exception as e:
            logger.error(f"Metric summary error: {e}")
            return {"average": 0, "minimum": 0, "maximum": 0, "total": 0, "count": 0}


# Global instance
timeseries_manager = TimeSeriesManager()
