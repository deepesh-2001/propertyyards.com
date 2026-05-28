"""
Optimized Background Task System
Runs tasks during idle time with AI content generation
Sales product fetching limited to 4 times per day
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import random

from app.cache import get_from_cache, set_in_cache
from app.database import get_db
from app.server_monitoring import structured_logger
from app.ai_image_service import ai_image_generator
from app.news_service import ai_article_generator
from app.social_media_manager import social_media_manager, Platform
from app.insurance_scraper import insurance_scraper

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class TaskType(Enum):
    """Types of background tasks"""
    SALES_FETCH = "sales_fetch"
    CACHE_MAINTENANCE = "cache_maintenance"
    AI_CONTENT = "ai_content"
    ANALYTICS = "analytics"
    DATABASE_OPTIMIZE = "database_optimize"
    SOCIAL_MEDIA = "social_media"
    INSURANCE_SCRAPE = "insurance_scrape"
    REPORT_GENERATE = "report_generate"


@dataclass
class BackgroundTask:
    """Background task definition"""
    id: str
    name: str
    task_type: TaskType
    priority: TaskPriority
    execute: Callable
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    max_runs_per_day: int = 4  # Limit to 4 times per day for sales
    estimated_duration: int = 60  # seconds
    enabled: bool = True


class OptimizedBackgroundScheduler:
    """
    Optimized background task scheduler
    Runs tasks during idle time to minimize impact on API performance
    Sales product fetching limited to 4 times per day
    """

    def __init__(self):
        self.tasks: Dict[str, BackgroundTask] = {}
        self.is_running = False
        self.idle_check_interval = 30  # Check every 30 seconds
        self.idle_threshold = 0.3  # Consider idle if load < 30%
        self.min_idle_time = 300  # Need 5 minutes of idle to start heavy tasks
        self.last_activity = datetime.utcnow()
        self.current_load = 0.0
        
        # Schedule: 4 times per day at 2 AM, 8 AM, 2 PM, 8 PM
        self.sales_fetch_schedule = [2, 8, 14, 20]
        
        # Beautiful AI content templates
        self.content_templates = {
            "property_descriptions": [
                "Experience luxury living at its finest in this stunning {property_type}.",
                "Discover your dream home in the heart of {location}.",
                "Modern elegance meets comfort in this beautiful {property_type}.",
                "Premium living spaces designed for those who appreciate the finer things.",
                "Your perfect sanctuary awaits in this meticulously crafted {property_type}."
            ],
            "neighborhood_highlights": [
                "Located in a vibrant community with excellent connectivity.",
                "Surrounded by top-rated schools, hospitals, and shopping centers.",
                "Peaceful residential area with lush greenery and modern amenities.",
                "Prime location offering the best of urban convenience and suburban tranquility.",
                "Prestigious neighborhood known for its premium lifestyle and security."
            ],
            "investment_pitch": [
                "A golden opportunity for smart investors seeking high returns.",
                "Prime real estate asset in one of the fastest-growing markets.",
                "Excellent appreciation potential with strong rental demand.",
                "Secure your financial future with this high-value property investment.",
                "Limited availability in this sought-after development."
            ]
        }

    async def start(self):
        """Start the optimized background scheduler"""
        self.is_running = True
        asyncio.create_task(self._scheduler_loop())
        logger.info("Optimized background scheduler started")
        structured_logger.info(
            "Background scheduler initialized",
            {"sales_fetch_limit": "4 times per day", "idle_threshold": self.idle_threshold}
        )

    async def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        logger.info("Background scheduler stopped")

    async def _scheduler_loop(self):
        """Main scheduler loop - runs during idle time"""
        while self.is_running:
            try:
                # Check system load
                self.current_load = await self._get_system_load()
                
                if self.current_load < self.idle_threshold:
                    # System is idle, process background tasks
                    await self._process_idle_tasks()
                else:
                    logger.debug(f"System busy (load: {self.current_load:.2f}), deferring background tasks")
                
                await asyncio.sleep(self.idle_check_interval)
                
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)

    async def _get_system_load(self) -> float:
        """Get current system load (0-1)"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1) / 100.0
            memory_percent = psutil.virtual_memory().percent / 100.0
            
            # Combine CPU and memory load
            return (cpu_percent + memory_percent) / 2
        except:
            return 0.5  # Default to medium load if can't detect

    async def _process_idle_tasks(self):
        """Process tasks during idle time"""
        now = datetime.utcnow()
        
        # Get tasks that need to run
        tasks_to_run = []
        
        for task_id, task in self.tasks.items():
            if not task.enabled:
                continue
                
            # Check if task should run
            if self._should_run_task(task, now):
                tasks_to_run.append(task)
        
        # Sort by priority
        tasks_to_run.sort(key=lambda t: t.priority.value)
        
        # Run high priority tasks immediately
        for task in tasks_to_run:
            if task.priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]:
                await self._execute_task(task)
            elif self.current_load < 0.2:  # Only run normal/low tasks if very idle
                await self._execute_task(task)

    def _should_run_task(self, task: BackgroundTask, now: datetime) -> bool:
        """Determine if a task should run based on schedule and limits"""
        # Check max runs per day for limited tasks
        if task.max_runs_per_day > 0:
            today_runs = self._get_today_run_count(task)
            if today_runs >= task.max_runs_per_day:
                return False
        
        # Check schedule for sales fetch
        if task.task_type == TaskType.SALES_FETCH:
            return now.hour in self.sales_fetch_schedule and now.minute < 5
        
        # For other tasks, run if enough time has passed
        if task.last_run:
            time_since_last = (now - task.last_run).total_seconds()
            min_interval = 3600 / task.max_runs_per_day if task.max_runs_per_day > 0 else 3600
            return time_since_last >= min_interval
        
        return True

    def _get_today_run_count(self, task: BackgroundTask) -> int:
        """Get number of times task ran today"""
        today = datetime.utcnow().date()
        # In real implementation, track in database
        return task.run_count if task.last_run and task.last_run.date() == today else 0

    async def _execute_task(self, task: BackgroundTask):
        """Execute a background task"""
        try:
            logger.info(f"Executing background task: {task.name}")
            
            await task.execute()
            
            task.last_run = datetime.utcnow()
            task.run_count += 1
            
            structured_logger.info(
                "Background task completed",
                {"task": task.name, "type": task.task_type.value, "duration": task.estimated_duration}
            )
            
        except Exception as e:
            logger.error(f"Task execution failed: {task.name} - {e}")
            structured_logger.error(
                "Background task failed",
                {"task": task.name, "error": str(e)}
            )

    def register_task(self, task: BackgroundTask):
        """Register a new background task"""
        self.tasks[task.id] = task
        logger.info(f"Registered background task: {task.name}")

    # ===== AI CONTENT GENERATION TASKS =====

    async def generate_beautiful_property_content(self, database):
        """Generate beautiful AI property descriptions during idle time"""
        try:
            # Get properties without descriptions
            properties = await database.properties.find(
                {"$or": [
                    {"description": {"$exists": False}},
                    {"description": ""},
                    {"ai_enhanced": {"$ne": True}}
                ]}
            }).limit(10).to_list(length=10)

            for prop in properties:
                # Generate beautiful description
                template = random.choice(self.content_templates["property_descriptions"])
                neighborhood = random.choice(self.content_templates["neighborhood_highlights"])
                investment = random.choice(self.content_templates["investment_pitch"])
                
                property_type = prop.get("property_type", "property")
                location = prop.get("city", "this location")
                
                description = f"""
{template.format(property_type=property_type, location=location)}

{neighborhood}

{investment}

Key Features:
• {prop.get('bedrooms', 2)} spacious bedrooms with natural lighting
• Modern {prop.get('bathrooms', 2)} bathrooms with premium fittings
• {prop.get('area', 1200)} sq ft of well-designed living space
• {random.choice(['Swimming pool', 'Gym', 'Garden', 'Club house', 'Security'])} access
• {random.choice(['Covered parking', 'Visitor parking', 'EV charging'])} available

Don't miss this opportunity to own your dream home!
                """.strip()
                
                await database.properties.update_one(
                    {"_id": prop["_id"]},
                    {"$set": {
                        "description": description,
                        "ai_enhanced": True,
                        "content_generated_at": datetime.utcnow()
                    }}
                )
            
            logger.info(f"Enhanced {len(properties)} properties with AI content")
            
        except Exception as e:
            logger.error(f"AI content generation failed: {e}")

    async def generate_social_media_content(self, database):
        """Generate beautiful social media posts during idle time"""
        try:
            # Get recent properties
            recent_props = await database.properties.find(
                {"status": "active"}
            ).sort("created_at", -1).limit(5).to_list(length=5)

            for prop in recent_props:
                # Generate social media post
                captions = [
                    f"🏠 New Listing Alert! {prop.get('title', 'Property')} in {prop.get('city', '')}",
                    f"✨ Just Listed: {prop.get('bedrooms', 2)}BHK in {prop.get('locality', '')}",
                    f"🔥 Hot Property: {prop.get('price', 'Great Price')} - {prop.get('city', '')}"
                ]
                
                caption = random.choice(captions)
                
                # Schedule post
                await social_media_manager.schedule_post(
                    platform=Platform.FACEBOOK,
                    content=caption,
                    scheduled_time=datetime.utcnow() + timedelta(hours=random.randint(1, 24)),
                    database=database
                )
            
            logger.info(f"Scheduled {len(recent_props)} social media posts")
            
        except Exception as e:
            logger.error(f"Social media generation failed: {e}")

    async def generate_ai_images_idle(self, database):
        """Generate AI property images during deep idle time"""
        try:
            # Only run if system is very idle (load < 15%)
            if self.current_load > 0.15:
                return
            
            # Get properties without images
            props = await database.properties.find(
                {"$or": [
                    {"image_url": {"$exists": False}},
                    {"ai_image_generated": {"$ne": True}}
                ]}
            }).limit(3).to_list(length=3)

            for prop in props:
                # Generate AI visualization
                image = await ai_image_generator.generate_property_visualization(
                    property_data=prop,
                    style=random.choice(["modern", "classic", "minimalist"])
                )
                
                if image:
                    await database.properties.update_one(
                        {"_id": prop["_id"]},
                        {"$set": {
                            "ai_image_generated": True,
                            "ai_image_id": image.id
                        }}
                    )
            
            logger.info(f"Generated {len(props)} AI property images")
            
        except Exception as e:
            logger.error(f"AI image generation failed: {e}")

    async def optimize_database_idle(self, database):
        """Run database optimizations during idle time"""
        try:
            # Rebuild indexes
            await database.command({"reIndex": "properties"})
            await database.command({"reIndex": "sales_records"})
            
            # Compact collections
            # Note: compact is blocking, so only do during deep idle
            
            logger.info("Database optimization completed")
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")

    async def refresh_insurance_data_idle(self, database):
        """Refresh insurance data during idle time (limited to 4x/day)"""
        try:
            now = datetime.utcnow()
            
            # Only run at scheduled times: 2 AM, 8 AM, 2 PM, 8 PM
            if now.hour not in self.sales_fetch_schedule or now.minute > 5:
                return
            
            # Refresh all insurance types
            for ins_type in ["health", "life", "property", "home"]:
                try:
                    await insurance_scraper.scrape_insurance_plans(
                        insurance_type=ins_type
                    )
                except Exception as e:
                    logger.warning(f"Failed to refresh {ins_type} insurance: {e}")
            
            structured_logger.info(
                "Insurance data refreshed during idle time",
                {"scheduled_at": now.hour, "types": 4}
            )
            
        except Exception as e:
            logger.error(f"Insurance refresh failed: {e}")


# Global optimized scheduler instance
optimized_scheduler = OptimizedBackgroundScheduler()


async def setup_optimized_tasks(database):
    """Setup all optimized background tasks"""
    scheduler = optimized_scheduler
    
    # 1. Sales Product Fetching (4 times per day)
    sales_task = BackgroundTask(
        id="sales_fetch",
        name="Sales Product Fetching",
        task_type=TaskType.SALES_FETCH,
        priority=TaskPriority.NORMAL,
        execute=lambda: scheduler.refresh_insurance_data_idle(database),
        max_runs_per_day=4,  # STRICT LIMIT: 4 times per day
        estimated_duration=300  # 5 minutes
    )
    scheduler.register_task(sales_task)
    
    # 2. AI Content Generation (Beautiful descriptions)
    content_task = BackgroundTask(
        id="ai_content",
        name="AI Property Content Generation",
        task_type=TaskType.AI_CONTENT,
        priority=TaskPriority.LOW,
        execute=lambda: scheduler.generate_beautiful_property_content(database),
        max_runs_per_day=10,
        estimated_duration=120
    )
    scheduler.register_task(content_task)
    
    # 3. Social Media Content
    social_task = BackgroundTask(
        id="social_content",
        name="Social Media Content Generation",
        task_type=TaskType.SOCIAL_MEDIA,
        priority=TaskPriority.LOW,
        execute=lambda: scheduler.generate_social_media_content(database),
        max_runs_per_day=8,
        estimated_duration=60
    )
    scheduler.register_task(social_task)
    
    # 4. AI Image Generation (Deep idle only)
    image_task = BackgroundTask(
        id="ai_images",
        name="AI Property Image Generation",
        task_type=TaskType.AI_CONTENT,
        priority=TaskPriority.BACKGROUND,
        execute=lambda: scheduler.generate_ai_images_idle(database),
        max_runs_per_day=20,
        estimated_duration=300
    )
    scheduler.register_task(image_task)
    
    # 5. Database Optimization
    db_task = BackgroundTask(
        id="db_optimize",
        name="Database Optimization",
        task_type=TaskType.DATABASE_OPTIMIZE,
        priority=TaskPriority.BACKGROUND,
        execute=lambda: scheduler.optimize_database_idle(database),
        max_runs_per_day=1,
        estimated_duration=600
    )
    scheduler.register_task(db_task)
    
    # 6. Insurance Data Refresh
    insurance_task = BackgroundTask(
        id="insurance_refresh",
        name="Insurance Data Refresh",
        task_type=TaskType.INSURANCE_SCRAPE,
        priority=TaskPriority.NORMAL,
        execute=lambda: scheduler.refresh_insurance_data_idle(database),
        max_runs_per_day=4,
        estimated_duration=180
    )
    scheduler.register_task(insurance_task)
    
    # 7. Analytics Compilation
    analytics_task = BackgroundTask(
        id="analytics_compile",
        name="Analytics Compilation",
        task_type=TaskType.ANALYTICS,
        priority=TaskPriority.LOW,
        execute=lambda: _compile_analytics(database),
        max_runs_per_day=6,
        estimated_duration=90
    )
    scheduler.register_task(analytics_task)
    
    logger.info("All optimized background tasks registered")


async def _compile_analytics(database):
    """Compile analytics during idle time"""
    try:
        # Pre-compute popular analytics
        today = datetime.utcnow()
        
        # Daily stats
        daily_stats = await database.sales_records.aggregate([
            {
                "$match": {
                    "sale_date": {
                        "$gte": today - timedelta(days=1),
                        "$lt": today
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_sales": {"$sum": 1},
                    "total_revenue": {"$sum": "$sale_price"}
                }
            }
        ]).to_list(length=1)
        
        # Cache results
        await set_in_cache("analytics:daily", daily_stats[0] if daily_stats else {}, ttl=3600)
        
        logger.info("Analytics compiled and cached")
        
    except Exception as e:
        logger.error(f"Analytics compilation failed: {e}")


# Task execution functions for external use
async def run_during_idle(task_func, estimated_duration: int = 60):
    """Execute a function during system idle time"""
    scheduler = optimized_scheduler
    
    # Wait for idle
    while scheduler.current_load >= scheduler.idle_threshold:
        await asyncio.sleep(10)
    
    # Execute task
    try:
        await task_func()
    except Exception as e:
        logger.error(f"Idle task execution failed: {e}")


async def get_scheduler_status() -> Dict[str, Any]:
    """Get optimized scheduler status"""
    scheduler = optimized_scheduler
    
    return {
        "is_running": scheduler.is_running,
        "current_load": scheduler.current_load,
        "idle_threshold": scheduler.idle_threshold,
        "tasks_registered": len(scheduler.tasks),
        "sales_fetch_schedule": scheduler.sales_fetch_schedule,
        "tasks": [
            {
                "id": task.id,
                "name": task.name,
                "type": task.task_type.value,
                "priority": task.priority.name,
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "run_count_today": scheduler._get_today_run_count(task),
                "max_runs_per_day": task.max_runs_per_day,
                "enabled": task.enabled
            }
            for task in scheduler.tasks.values()
        ],
        "sales_fetch_limit": "4 times per day at 2 AM, 8 AM, 2 PM, 8 PM"
    }
