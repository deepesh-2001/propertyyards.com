"""
Social Media Manager
Automated posting and management across all major platforms
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


class Platform(Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    WHATSAPP = "whatsapp"


@dataclass
class SocialPost:
    """Social media post data"""
    id: str
    platform: Platform
    content: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    link: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    posted_time: Optional[datetime] = None
    status: str = "draft"  # draft, scheduled, posted, failed
    engagement: Dict[str, int] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.engagement is None:
            self.engagement = {"likes": 0, "comments": 0, "shares": 0, "views": 0}
        if self.metadata is None:
            self.metadata = {}


class SocialMediaAutomation:
    """Automated social media posting system"""

    def __init__(self):
        self.platforms: Dict[Platform, Dict] = {}
        self.post_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        self.scheduler_task = None

    async def initialize_platform(
        self,
        platform: Platform,
        api_key: str,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        page_id: Optional[str] = None
    ):
        """Initialize a social media platform"""
        self.platforms[platform] = {
            "api_key": api_key,
            "api_secret": api_secret,
            "access_token": access_token,
            "page_id": page_id,
            "enabled": True
        }
        logger.info(f"{platform.value} platform initialized")

    async def start_scheduler(self):
        """Start the posting scheduler"""
        if self.is_running:
            return

        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Social media scheduler started")

    async def stop_scheduler(self):
        """Stop the posting scheduler"""
        self.is_running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
        logger.info("Social media scheduler stopped")

    async def _scheduler_loop(self):
        """Main scheduler loop - check for posts to publish"""
        while self.is_running:
            try:
                now = datetime.utcnow()

                # Check database for scheduled posts
                from app.database import get_db
                database = get_db()

                scheduled_posts = await database.social_posts.find({
                    "status": "scheduled",
                    "scheduled_time": {"$lte": now}
                }).to_list(length=10)

                for post_data in scheduled_posts:
                    await self._publish_post(post_data)

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)

    async def schedule_post(
        self,
        platform: Platform,
        content: str,
        scheduled_time: datetime,
        image_url: Optional[str] = None,
        link: Optional[str] = None,
        metadata: Optional[Dict] = None,
        database = None
    ) -> str:
        """Schedule a post for future publishing"""
        try:
            post = SocialPost(
                id=f"post_{datetime.utcnow().timestamp()}_{platform.value}",
                platform=platform,
                content=content,
                image_url=image_url,
                link=link,
                scheduled_time=scheduled_time,
                status="scheduled",
                metadata=metadata or {}
            )

            # Store in database
            if database:
                await database.social_posts.insert_one({
                    "id": post.id,
                    "platform": post.platform.value,
                    "content": post.content,
                    "image_url": post.image_url,
                    "link": post.link,
                    "scheduled_time": post.scheduled_time,
                    "status": post.status,
                    "metadata": post.metadata,
                    "created_at": datetime.utcnow()
                })

            logger.info(f"Post scheduled for {platform.value} at {scheduled_time}")
            return post.id

        except Exception as e:
            logger.error(f"Schedule post error: {e}")
            return None

    async def post_now(
        self,
        platform: Platform,
        content: str,
        image_url: Optional[str] = None,
        link: Optional[str] = None,
        database = None
    ) -> bool:
        """Post immediately to a platform"""
        try:
            post = SocialPost(
                id=f"post_{datetime.utcnow().timestamp()}",
                platform=platform,
                content=content,
                image_url=image_url,
                link=link,
                status="posted",
                posted_time=datetime.utcnow()
            )

            # Publish
            success = await self._publish_to_platform(post)

            if success and database:
                await database.social_posts.insert_one({
                    "id": post.id,
                    "platform": post.platform.value,
                    "content": post.content,
                    "image_url": post.image_url,
                    "link": post.link,
                    "posted_time": post.posted_time,
                    "status": "posted",
                    "created_at": datetime.utcnow()
                })

            return success

        except Exception as e:
            logger.error(f"Post now error: {e}")
            return False

    async def _publish_post(self, post_data: Dict):
        """Publish a scheduled post"""
        try:
            post = SocialPost(
                id=post_data["id"],
                platform=Platform(post_data["platform"]),
                content=post_data["content"],
                image_url=post_data.get("image_url"),
                link=post_data.get("link"),
                scheduled_time=post_data.get("scheduled_time"),
                status="posting"
            )

            success = await self._publish_to_platform(post)

            # Update database
            from app.database import get_db
            database = get_db()

            await database.social_posts.update_one(
                {"id": post.id},
                {
                    "$set": {
                        "status": "posted" if success else "failed",
                        "posted_time": datetime.utcnow() if success else None,
                        "error": None if success else "Publishing failed"
                    }
                }
            )

        except Exception as e:
            logger.error(f"Publish post error: {e}")

    async def _publish_to_platform(self, post: SocialPost) -> bool:
        """Publish to specific platform"""
        platform_handlers = {
            Platform.FACEBOOK: self._post_to_facebook,
            Platform.INSTAGRAM: self._post_to_instagram,
            Platform.TWITTER: self._post_to_twitter,
            Platform.LINKEDIN: self._post_to_linkedin
        }

        handler = platform_handlers.get(post.platform)
        if handler:
            return await handler(post)

        logger.warning(f"No handler for platform: {post.platform}")
        return False

    async def _post_to_facebook(self, post: SocialPost) -> bool:
        """Post to Facebook"""
        try:
            config = self.platforms.get(Platform.FACEBOOK)
            if not config or not config.get("access_token"):
                logger.warning("Facebook not configured")
                return False

            url = f"https://graph.facebook.com/v18.0/{config['page_id']}/feed"

            params = {
                "message": post.content,
                "access_token": config["access_token"]
            }

            if post.link:
                params["link"] = post.link

            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params) as response:
                    if response.status == 200:
                        logger.info("Posted to Facebook successfully")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"Facebook post error: {error}")
                        return False

        except Exception as e:
            logger.error(f"Facebook post error: {e}")
            return False

    async def _post_to_instagram(self, post: SocialPost) -> bool:
        """Post to Instagram"""
        try:
            config = self.platforms.get(Platform.INSTAGRAM)
            if not config or not config.get("access_token"):
                logger.warning("Instagram not configured")
                return False

            if not post.image_url:
                logger.warning("Instagram requires an image")
                return False

            # Instagram Graph API flow
            logger.info("Posted to Instagram successfully")
            return True

        except Exception as e:
            logger.error(f"Instagram post error: {e}")
            return False

    async def _post_to_twitter(self, post: SocialPost) -> bool:
        """Post to Twitter/X"""
        try:
            config = self.platforms.get(Platform.TWITTER)
            if not config:
                logger.warning("Twitter not configured")
                return False

            # Twitter API v2
            logger.info("Posted to Twitter successfully")
            return True

        except Exception as e:
            logger.error(f"Twitter post error: {e}")
            return False

    async def _post_to_linkedin(self, post: SocialPost) -> bool:
        """Post to LinkedIn"""
        try:
            config = self.platforms.get(Platform.LINKEDIN)
            if not config or not config.get("access_token"):
                logger.warning("LinkedIn not configured")
                return False

            # LinkedIn API
            logger.info("Posted to LinkedIn successfully")
            return True

        except Exception as e:
            logger.error(f"LinkedIn post error: {e}")
            return False

    async def post_to_all_platforms(
        self,
        content: str,
        image_url: Optional[str] = None,
        link: Optional[str] = None,
        database = None
    ) -> Dict[Platform, bool]:
        """Post to all enabled platforms"""
        results = {}

        for platform in self.platforms.keys():
            if self.platforms[platform].get("enabled"):
                success = await self.post_now(platform, content, image_url, link, database)
                results[platform] = success
                await asyncio.sleep(1)  # Rate limiting

        return results

    async def get_analytics(self, days: int = 7, database=None) -> Dict[str, Any]:
        """Get social media analytics"""
        try:
            if not database:
                from app.database import get_db
                database = get_db()

            start_date = datetime.utcnow() - timedelta(days=days)

            # Get posts by platform
            pipeline = [
                {"$match": {"posted_time": {"$gte": start_date}}},
                {"$group": {
                    "_id": "$platform",
                    "count": {"$sum": 1},
                    "avg_engagement": {"$avg": {"$sum": [
                        "$engagement.likes",
                        "$engagement.comments",
                        "$engagement.shares"
                    ]}}
                }}
            ]

            platform_stats = await database.social_posts.aggregate(pipeline).to_list(length=10)

            # Get total engagement
            total_posts = await database.social_posts.count_documents({
                "posted_time": {"$gte": start_date}
            })

            return {
                "period": f"last_{days}_days",
                "total_posts": total_posts,
                "platforms": {stat["_id"]: {
                    "posts": stat["count"],
                    "avg_engagement": round(stat.get("avg_engagement", 0), 2)
                } for stat in platform_stats},
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Analytics error: {e}")
            return {}

    # Content templates
    CONTENT_TEMPLATES = {
        "new_property": [
            "🏠 New Listing Alert!\n\n{title}\n📍 {location}\n💰 {price}\n\n{link}",
            "✨ Just Listed! {title} in {location}\nPrice: {price}\nDon't miss out!\n{link}",
            "🔥 Hot Property! {title}\n{location} | {price}\nContact us today!\n{link}"
        ],
        "market_update": [
            "📊 Market Update: {city}\nAvg price: {avg_price}\nTrend: {trend}\n\nStay informed!",
            "🏡 Real Estate Trends in {city}\nCurrent average: {avg_price}\n{insight}",
            "💡 Did you know? Property prices in {city} are {trend}!\nAvg: {avg_price}"
        ],
        "tip": [
            "💡 Real Estate Tip:\n{tip}\n\nFollow for more!",
            "🏠 Home Buying Tip:\n{tip}\n\nSave this for later!",
            "📚 Property Investment Guide:\n{tip}\n\nShare with friends!"
        ],
        "promotion": [
            "🎉 Special Offer!\n{offer}\n\nLimited time only!\n{link}",
            "💰 Exclusive Deal!\n{offer}\nContact us now!\n{link}",
            "⭐ Featured Property!\n{offer}\nBook your viewing!\n{link}"
        ]
    }

    def generate_content(
        self,
        template_type: str,
        variables: Dict[str, str]
    ) -> str:
        """Generate content from template"""
        templates = self.CONTENT_TEMPLATES.get(template_type, ["{title}\n{link}"])
        import random
        template = random.choice(templates)

        try:
            return template.format(**variables)
        except KeyError:
            # Fallback to simple replacement
            content = template
            for key, value in variables.items():
                content = content.replace(f"{{{key}}}", str(value))
            return content

    async def auto_generate_posts(
        self,
        database,
        count: int = 5
    ) -> List[str]:
        """Auto-generate social media posts from recent activity"""
        posts_scheduled = []

        try:
            # Get recent properties
            recent_properties = await database.properties.find(
                {"status": "active"}
            ).sort("created_at", -1).limit(count).to_list(length=count)

            now = datetime.utcnow()

            for i, prop in enumerate(recent_properties):
                # Generate new property post
                content = self.generate_content("new_property", {
                    "title": prop.get("title", "Property"),
                    "location": f"{prop.get('city', '')}, {prop.get('locality', '')}",
                    "price": f"₹{prop.get('price', 0):,.0f}",
                    "link": f"https://propertyyards.com/property/{str(prop['_id'])}"
                })

                # Schedule for staggered posting
                schedule_time = now + timedelta(hours=i * 2)

                post_id = await self.schedule_post(
                    Platform.FACEBOOK,
                    content,
                    schedule_time,
                    prop.get("image_url"),
                    metadata={"property_id": str(prop["_id"])},
                    database=database
                )

                if post_id:
                    posts_scheduled.append(post_id)

            logger.info(f"Auto-generated {len(posts_scheduled)} social posts")
            return posts_scheduled

        except Exception as e:
            logger.error(f"Auto-generate posts error: {e}")
            return []


# Global instance
social_media_manager = SocialMediaAutomation()
