"""
AI SEO Router
API endpoints for AI-powered SEO optimization
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_user
from app.ai_seo_optimizer import ai_seo_optimizer, SEOCategory

router = APIRouter(prefix="/api/ai-seo", tags=["ai-seo"])


class SEOAnalyzeRequest(BaseModel):
    """SEO analysis request"""
    content: str
    content_type: str  # property_listing, location_page, blog_article, etc.
    target_keywords: List[str]
    location: Optional[str] = None


class SEOOptimizeRequest(BaseModel):
    """SEO optimization request"""
    content: str
    content_type: str
    target_keywords: List[str]
    location: Optional[str] = None


class SEOGenerateRequest(BaseModel):
    """SEO content generation request"""
    content_type: str
    topic: str
    target_keywords: List[str]
    location: str
    word_count: int = 800


@router.post("/analyze")
async def analyze_seo(
    request: SEOAnalyzeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyze content for SEO optimization"""
    if current_user.get("role") not in ["admin", "agent", "editor"]:
        raise HTTPException(status_code=403, detail="Editor access required")

    try:
        content_type = SEOCategory(request.content_type)

        result = await ai_seo_optimizer.analyze_content(
            content=request.content,
            content_type=content_type,
            target_keywords=request.target_keywords,
            location=request.location
        )

        if not result:
            raise HTTPException(status_code=500, detail="SEO analysis failed")

        return {
            "content_id": result.content_id,
            "overall_score": result.overall_score,
            "score_level": {
                "name": result.score_level.name,
                "label": result.score_level.label,
                "color": result.score_level.color
            },
            "analyzed_at": result.analyzed_at,
            "checks": result.checks,
            "recommendations": result.recommendations,
            "keyword_analysis": result.keyword_analysis
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid content type: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize")
async def optimize_content(
    request: SEOOptimizeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Optimize existing content for SEO"""
    if current_user.get("role") not in ["admin", "agent", "editor"]:
        raise HTTPException(status_code=403, detail="Editor access required")

    try:
        content_type = SEOCategory(request.content_type)

        # First analyze
        analysis = await ai_seo_optimizer.analyze_content(
            content=request.content,
            content_type=content_type,
            target_keywords=request.target_keywords,
            location=request.location
        )

        # Then optimize
        optimized_content = await ai_seo_optimizer.optimize_content(
            content=request.content,
            content_type=content_type,
            target_keywords=request.target_keywords,
            location=request.location
        )

        # Analyze optimized version
        optimized_analysis = await ai_seo_optimizer.analyze_content(
            content=optimized_content,
            content_type=content_type,
            target_keywords=request.target_keywords,
            location=request.location
        )

        return {
            "original_analysis": {
                "score": analysis.overall_score,
                "issues_count": len(analysis.recommendations)
            },
            "optimized_content": optimized_content,
            "optimized_analysis": {
                "score": optimized_analysis.overall_score,
                "score_level": {
                    "name": optimized_analysis.score_level.name,
                    "label": optimized_analysis.score_level.label
                },
                "improvement": optimized_analysis.overall_score - analysis.overall_score
            },
            "changes_applied": len(analysis.recommendations[:3])
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid content type: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_seo_content(
    request: SEOGenerateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate SEO-optimized content from scratch"""
    if current_user.get("role") not in ["admin", "agent", "editor"]:
        raise HTTPException(status_code=403, detail="Editor access required")

    try:
        content_type = SEOCategory(request.content_type)

        result = await ai_seo_optimizer.generate_seo_content(
            content_type=content_type,
            topic=request.topic,
            target_keywords=request.target_keywords,
            location=request.location,
            word_count=request.word_count
        )

        if not result:
            raise HTTPException(status_code=500, detail="Content generation failed")

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid content type: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-template/{page_type}")
async def get_audit_template(
    page_type: str,
    current_user: dict = Depends(get_current_user)
):
    """Get SEO audit checklist template"""
    if current_user.get("role") not in ["admin", "agent", "editor"]:
        raise HTTPException(status_code=403, detail="Editor access required")

    template = ai_seo_optimizer.get_seo_audit_template(page_type)

    return {
        "page_type": page_type,
        "checklist": template
    }


@router.get("/content-types")
async def get_content_types(
    current_user: dict = Depends(get_current_user)
):
    """Get available SEO content types"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    return {
        "content_types": [
            {
                "value": "property_listing",
                "name": "Property Listing",
                "description": "Individual property pages",
                "seo_importance": "high"
            },
            {
                "value": "location_page",
                "name": "Location Page",
                "description": "City/area overview pages",
                "seo_importance": "high"
            },
            {
                "value": "blog_article",
                "name": "Blog Article",
                "description": "Real estate blog posts",
                "seo_importance": "medium"
            },
            {
                "value": "landing_page",
                "name": "Landing Page",
                "description": "Marketing landing pages",
                "seo_importance": "high"
            },
            {
                "value": "agent_profile",
                "name": "Agent Profile",
                "description": "Real estate agent pages",
                "seo_importance": "medium"
            },
            {
                "value": "project_page",
                "name": "Project Page",
                "description": "New project launch pages",
                "seo_importance": "high"
            }
        ]
    }


@router.get("/real-estate-keywords")
async def get_real_estate_keywords(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get suggested real estate keywords by category"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    keywords = ai_seo_optimizer.real_estate_keywords

    if category and category in keywords:
        return {"category": category, "keywords": keywords[category]}

    return {"keywords": keywords}


@router.get("/score-levels")
async def get_score_levels(
    current_user: dict = Depends(get_current_user)
):
    """Get SEO score level definitions"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    from app.ai_seo_optimizer import SEOScoreLevel

    return {
        "score_levels": [
            {
                "name": level.name,
                "min_score": level.min_score,
                "max_score": level.max_score,
                "label": level.label,
                "color": level.color
            }
            for level in SEOScoreLevel
        ]
    }


@router.get("/health")
async def seo_optimizer_health():
    """Check AI SEO optimizer health"""
    return {
        "status": "healthy" if ai_seo_optimizer.enabled else "disabled",
        "api_configured": bool(ai_seo_optimizer.api_key),
        "enabled_features": {
            "analysis": True,
            "optimization": True,
            "content_generation": True
        }
    }
