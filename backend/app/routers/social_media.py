"""
Social Media Router
API endpoints for social media management
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_user
from app.social_media_manager import social_media_manager, Platform, SocialPost
from app.ai_image_service import ai_image_generator

router = APIRouter(prefix="/api/social-media", tags=["social-media"])


class SchedulePostRequest(BaseModel):
    """Request to schedule a social media post"""
    platform: str
    content: str
    scheduled_time: datetime
    image_url: Optional[str] = None
    link: Optional[str] = None


class PostNowRequest(BaseModel):
    """Request to post immediately"""
    platforms: List[str]
    content: str
    image_url: Optional[str] = None
    link: Optional[str] = None


class ContentTemplateRequest(BaseModel):
    """Request to generate content from template"""
    template_type: str
    variables: Dict[str, str]


# ========== Social Media Management ==========

@router.get("/dashboard")
async def get_social_dashboard(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get social media dashboard"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Get analytics
        analytics = await social_media_manager.get_analytics(days=7, database=database)

        # Get scheduled posts
        upcoming_posts = await database.social_posts.find({
            "status": "scheduled",
            "scheduled_time": {"$gte": datetime.utcnow()}
        }).sort("scheduled_time", 1).limit(10).to_list(length=10)

        # Get recent posts
        recent_posts = await database.social_posts.find({
            "posted_time": {"$gte": datetime.utcnow() - timedelta(days=7)}
        }).sort("posted_time", -1).limit(10).to_list(length=10)

        return {
            "analytics": analytics,
            "upcoming_posts": [
                {
                    "id": p["id"],
                    "platform": p["platform"],
                    "content": p["content"][:100] + "..." if len(p["content"]) > 100 else p["content"],
                    "scheduled_time": p["scheduled_time"]
                }
                for p in upcoming_posts
            ],
            "recent_posts": [
                {
                    "id": p["id"],
                    "platform": p["platform"],
                    "content": p["content"][:100] + "..." if len(p["content"]) > 100 else p["content"],
                    "posted_time": p["posted_time"],
                    "engagement": p.get("engagement", {})
                }
                for p in recent_posts
            ],
            "platform_status": {
                platform.value: config.get("enabled", False)
                for platform, config in social_media_manager.platforms.items()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule")
async def schedule_post(
    request: SchedulePostRequest,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Schedule a social media post"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        platform = Platform(request.platform)

        post_id = await social_media_manager.schedule_post(
            platform=platform,
            content=request.content,
            scheduled_time=request.scheduled_time,
            image_url=request.image_url,
            link=request.link,
            database=database
        )

        if post_id:
            return {
                "message": "Post scheduled successfully",
                "post_id": post_id,
                "platform": request.platform,
                "scheduled_time": request.scheduled_time
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to schedule post")

    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid platform: {request.platform}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/post-now")
async def post_now(
    request: PostNowRequest,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Post immediately to social media"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        results = {}

        for platform_str in request.platforms:
            try:
                platform = Platform(platform_str)
                success = await social_media_manager.post_now(
                    platform=platform,
                    content=request.content,
                    image_url=request.image_url,
                    link=request.link,
                    database=database
                )
                results[platform_str] = "success" if success else "failed"
            except ValueError:
                results[platform_str] = "invalid_platform"

        return {
            "message": "Posts processed",
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-content")
async def generate_content(
    request: ContentTemplateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate content using templates"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        content = social_media_manager.generate_content(
            request.template_type,
            request.variables
        )

        return {
            "template_type": request.template_type,
            "variables": request.variables,
            "generated_content": content
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-generate")
async def auto_generate_posts(
    count: int = 5,
    background_tasks: BackgroundTasks = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Auto-generate social media posts from recent activity"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Run in background
        background_tasks.add_task(
            social_media_manager.auto_generate_posts,
            database,
            count
        )

        return {
            "message": "Auto-generation started",
            "count": count,
            "status": "processing"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts")
async def get_posts(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 50,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get social media posts"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        query = {}
        if status:
            query["status"] = status
        if platform:
            query["platform"] = platform

        posts = await database.social_posts.find(query).sort("created_at", -1).limit(limit).to_list(length=limit)

        return {
            "posts": posts,
            "count": len(posts),
            "filters": {"status": status, "platform": platform}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a scheduled post"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        result = await database.social_posts.delete_one({"id": post_id})

        if result.deleted_count > 0:
            return {"message": "Post deleted", "post_id": post_id}
        else:
            raise HTTPException(status_code=404, detail="Post not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_analytics(
    days: int = 7,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get social media analytics"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        analytics = await social_media_manager.get_analytics(days=days, database=database)
        return analytics

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-generate-image")
async def generate_social_image(
    content_type: str,
    text: str,
    theme: str = "professional",
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate AI image for social media"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        image = await ai_image_generator.generate_social_media_image(
            content_type, text, theme
        )

        if image:
            # Store image
            image_id = await image_cache_manager.store_image(image, database)

            return {
                "message": "Image generated",
                "image_id": image_id,
                "prompt": image.prompt[:100] + "..."
            }
        else:
            raise HTTPException(status_code=500, detail="Image generation failed")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
