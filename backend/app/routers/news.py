"""
News Router
API endpoints for news article management and generation
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_user
from app.news_service import (
    news_fetcher, ai_article_generator, article_manager,
    NewsArticle, ArticleCategory, ArticleStatus
)

router = APIRouter(prefix="/api/news", tags=["news"])


class GenerateArticleRequest(BaseModel):
    """Request to generate AI article"""
    topic: str
    category: str
    keywords: List[str]
    tone: str = "professional"
    word_count: int = 800
    author_name: Optional[str] = None


class RewriteArticleRequest(BaseModel):
    """Request to rewrite external article"""
    original_title: str
    original_content: str
    original_source: Optional[str] = None
    user_name: str


class UpdateArticleRequest(BaseModel):
    """Request to update article"""
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


# ========== Public Endpoints ==========

@router.get("/articles")
async def get_articles(
    category: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
    database=Depends(get_db)
):
    """Get published articles"""
    try:
        skip = (page - 1) * limit

        cat_enum = ArticleCategory(category) if category else None

        articles = await article_manager.get_articles(
            database=database,
            category=cat_enum,
            status=ArticleStatus.PUBLISHED,
            limit=limit,
            skip=skip
        )

        return {
            "articles": [
                {
                    "id": a.id,
                    "title": a.title,
                    "summary": a.summary,
                    "author": a.author,
                    "category": a.category.value,
                    "tags": a.tags,
                    "published_at": a.published_at,
                    "views": a.views,
                    "likes": a.likes,
                    "featured_image": a.featured_image
                }
                for a in articles
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(articles)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles/{article_id}")
async def get_article(
    article_id: str,
    database=Depends(get_db)
):
    """Get single article"""
    try:
        article = await article_manager.get_article(article_id, database)

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        if article.status != ArticleStatus.PUBLISHED:
            raise HTTPException(status_code=404, detail="Article not found")

        # Increment view count
        await article_manager.update_article(
            article_id,
            {"views": article.views + 1},
            database
        )

        return {
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "summary": article.summary,
            "author": article.author,
            "category": article.category.value,
            "tags": article.tags,
            "published_at": article.published_at,
            "views": article.views + 1,
            "likes": article.likes,
            "featured_image": article.featured_image,
            "seo_meta": article.seo_meta,
            "is_ai_generated": article.is_ai_generated
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_categories():
    """Get available article categories"""
    return {
        "categories": [
            {"value": c.value, "label": c.value.replace("_", " ").title()}
            for c in ArticleCategory
        ]
    }


@router.get("/trending")
async def get_trending_articles(
    limit: int = Query(5, ge=1, le=20),
    database=Depends(get_db)
):
    """Get trending articles by views"""
    try:
        articles = await article_manager.get_articles(
            database=database,
            status=ArticleStatus.PUBLISHED,
            limit=limit
        )

        # Sort by views
        articles.sort(key=lambda x: x.views, reverse=True)

        return {
            "articles": [
                {
                    "id": a.id,
                    "title": a.title,
                    "views": a.views,
                    "summary": a.summary
                }
                for a in articles
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Admin Endpoints ==========

@router.get("/admin/all")
async def get_all_articles_admin(
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    page: int = Query(1, ge=1),
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all articles (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        skip = (page - 1) * limit

        cat_enum = ArticleCategory(category) if category else None
        status_enum = ArticleStatus(status) if status else None

        articles = await article_manager.get_articles(
            database=database,
            category=cat_enum,
            status=status_enum,
            limit=limit,
            skip=skip
        )

        total_count = await database.news_articles.count_documents({})

        return {
            "articles": [
                {
                    "id": a.id,
                    "title": a.title,
                    "author": a.author,
                    "category": a.category.value,
                    "status": a.status.value,
                    "tags": a.tags,
                    "created_at": a.created_at,
                    "published_at": a.published_at,
                    "views": a.views,
                    "is_ai_generated": a.is_ai_generated
                }
                for a in articles
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/generate")
async def generate_ai_article(
    request: GenerateArticleRequest,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate AI article (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Use provided author name or default
        author_name = request.author_name or current_user.get("full_name", "PropertyYards Team")

        # Update AI generator with author name
        await ai_article_generator.initialize(
            ai_article_generator.api_key or "",
            author_name
        )

        category = ArticleCategory(request.category)

        article = await ai_article_generator.generate_article(
            topic=request.topic,
            category=category,
            keywords=request.keywords,
            tone=request.tone,
            word_count=request.word_count
        )

        if not article:
            raise HTTPException(status_code=500, detail="Article generation failed")

        # Save to database
        article_id = await article_manager.create_article(article, database)

        return {
            "message": "Article generated successfully",
            "article_id": article_id,
            "title": article.title,
            "category": article.category.value,
            "is_ai_generated": True,
            "preview": article.content[:200] + "..."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/rewrite")
async def rewrite_article(
    request: RewriteArticleRequest,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Rewrite external article with PropertyYards branding (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        original = {
            "title": request.original_title,
            "content": request.original_content,
            "link": request.original_source
        }

        article = await ai_article_generator.rewrite_for_propertyyards(
            original,
            request.user_name
        )

        if not article:
            raise HTTPException(status_code=500, detail="Article rewrite failed")

        # Save to database
        article_id = await article_manager.create_article(article, database)

        return {
            "message": "Article rewritten successfully",
            "article_id": article_id,
            "title": article.title,
            "author": article.author,
            "preview": article.content[:200] + "..."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/fetch-news")
async def fetch_external_news(
    limit: int = Query(10, ge=1, le=50),
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Fetch news from external sources (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        await news_fetcher.initialize()
        articles = await news_fetcher.fetch_all_sources()
        await news_fetcher.close()

        # Limit results
        articles = articles[:limit]

        return {
            "message": f"Fetched {len(articles)} articles",
            "articles": articles
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/publish/{article_id}")
async def publish_article(
    article_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Publish article (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        success = await article_manager.publish_article(article_id, database)

        if success:
            return {"message": "Article published", "article_id": article_id}
        else:
            raise HTTPException(status_code=404, detail="Article not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/admin/update/{article_id}")
async def update_article(
    article_id: str,
    request: UpdateArticleRequest,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update article (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        updates = {}
        if request.title:
            updates["title"] = request.title
        if request.content:
            updates["content"] = request.content
        if request.summary:
            updates["summary"] = request.summary
        if request.tags:
            updates["tags"] = request.tags
        if request.status:
            updates["status"] = request.status
            if request.status == "published" and "published_at" not in updates:
                updates["published_at"] = datetime.utcnow()

        success = await article_manager.update_article(article_id, updates, database)

        if success:
            return {"message": "Article updated", "article_id": article_id}
        else:
            raise HTTPException(status_code=404, detail="Article not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/admin/{article_id}")
async def delete_article(
    article_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete article (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        success = await article_manager.delete_article(article_id, database)

        if success:
            return {"message": "Article deleted", "article_id": article_id}
        else:
            raise HTTPException(status_code=404, detail="Article not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/dashboard")
async def get_news_dashboard(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get news dashboard stats (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Get stats
        total_articles = await database.news_articles.count_documents({})
        published = await database.news_articles.count_documents({"status": "published"})
        drafts = await database.news_articles.count_documents({"status": "draft"})
        ai_generated = await database.news_articles.count_documents({"is_ai_generated": True})

        # Get recent articles
        recent = await article_manager.get_articles(
            database=database,
            limit=5
        )

        # Get top categories
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        categories = await database.news_articles.aggregate(pipeline).to_list(length=10)

        return {
            "stats": {
                "total": total_articles,
                "published": published,
                "drafts": drafts,
                "ai_generated": ai_generated
            },
            "recent_articles": [
                {
                    "id": a.id,
                    "title": a.title,
                    "status": a.status.value,
                    "created_at": a.created_at
                }
                for a in recent
            ],
            "categories": [
                {"category": c["_id"], "count": c["count"]}
                for c in categories
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
