"""
Feedback Router
Handles feedback collection, reviews, and analytics
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.schemas import (
    FeedbackCreate,
    FeedbackResponse,
    FeedbackReplyCreate,
    FeedbackReplyResponse,
    FeedbackAnalytics,
    ReviewCreate,
    ReviewResponse,
    FeedbackType,
    FeedbackCategory,
    FeedbackStatus
)
from app.feedback import feedback_manager, review_manager, sentiment_analyzer
from app.auth import get_current_user

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


# ========== Feedback Endpoints ==========

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback: FeedbackCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new feedback"""
    try:
        feedback_data = feedback.dict()
        result = await feedback_manager.create_feedback(feedback_data, database)
        return FeedbackResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get specific feedback"""
    feedback = await database.feedbacks.find_one({"_id": feedback_id})
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    feedback["id"] = str(feedback["_id"])
    del feedback["_id"]
    
    return FeedbackResponse(**feedback)


@router.get("/feedback", response_model=List[FeedbackResponse])
async def get_feedback(
    feedback_type: Optional[FeedbackType] = None,
    category: Optional[FeedbackCategory] = None,
    status: Optional[FeedbackStatus] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all feedback with filters"""
    query = {}
    if feedback_type:
        query["feedback_type"] = feedback_type
    if category:
        query["category"] = category
    if status:
        query["status"] = status
    
    cursor = database.feedbacks.find(query).sort("created_at", -1)
    feedbacks = await cursor.to_list(length=100)
    
    for feedback in feedbacks:
        feedback["id"] = str(feedback["_id"])
        del feedback["_id"]
    
    return [FeedbackResponse(**f) for f in feedbacks]


@router.put("/feedback/{feedback_id}/respond")
async def respond_to_feedback(
    feedback_id: str,
    response: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Respond to feedback"""
    try:
        result = await feedback_manager.respond_to_feedback(
            feedback_id=feedback_id,
            response=response,
            responded_by=str(current_user.get("_id")),
            database=database
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback/{feedback_id}/replies", response_model=FeedbackReplyResponse, status_code=status.HTTP_201_CREATED)
async def add_feedback_reply(
    feedback_id: str,
    reply: FeedbackReplyCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Add reply to feedback"""
    try:
        reply_data = reply.dict()
        reply_data.update({
            "feedback_id": feedback_id,
            "user_id": str(current_user.get("_id")),
            "user_name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}",
            "created_at": datetime.utcnow()
        })
        
        result = await database.feedback_replies.insert_one(reply_data)
        reply_data["id"] = str(result.inserted_id)
        
        return FeedbackReplyResponse(**reply_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/{feedback_id}/replies", response_model=List[FeedbackReplyResponse])
async def get_feedback_replies(
    feedback_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all replies for feedback"""
    cursor = database.feedback_replies.find({"feedback_id": feedback_id}).sort("created_at", 1)
    replies = await cursor.to_list(length=100)
    
    for reply in replies:
        reply["id"] = str(reply["_id"])
        del reply["_id"]
    
    return [FeedbackReplyResponse(**r) for r in replies]


@router.get("/analytics", response_model=FeedbackAnalytics)
async def get_feedback_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get feedback analytics"""
    try:
        analytics = await feedback_manager.get_feedback_analytics(
            start_date=start_date,
            end_date=end_date,
            database=database
        )
        return FeedbackAnalytics(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Review Endpoints ==========

@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: ReviewCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new property review"""
    try:
        review_data = review.dict()
        result = await review_manager.create_review(review_data, database)
        return ReviewResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get specific review"""
    review = await database.reviews.find_one({"_id": review_id})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review["id"] = str(review["_id"])
    del review["_id"]
    
    return ReviewResponse(**review)


@router.get("/properties/{property_id}/reviews", response_model=List[ReviewResponse])
async def get_property_reviews(
    property_id: str,
    min_rating: Optional[int] = None,
    verified_only: bool = False,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get reviews for a property"""
    try:
        reviews = await review_manager.get_property_reviews(
            property_id=property_id,
            min_rating=min_rating,
            verified_only=verified_only,
            database=database
        )
        return [ReviewResponse(**r) for r in reviews]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reviews/{review_id}/helpful")
async def mark_review_helpful(
    review_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark review as helpful"""
    try:
        result = await review_manager.mark_review_helpful(
            review_id=review_id,
            user_id=str(current_user.get("_id")),
            database=database
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/reviews/{review_id}/moderate")
async def moderate_review(
    review_id: str,
    action: str,  # approve, reject
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Moderate a review"""
    try:
        result = await review_manager.moderate_review(
            review_id=review_id,
            action=action,
            moderator_id=str(current_user.get("_id")),
            database=database
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brokers/{broker_id}/reviews", response_model=List[ReviewResponse])
async def get_broker_reviews(
    broker_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get reviews for a broker"""
    cursor = database.reviews.find({"broker_id": broker_id, "status": "published"}).sort("created_at", -1)
    reviews = await cursor.to_list(length=100)
    
    for review in reviews:
        review["id"] = str(review["_id"])
        del review["_id"]
    
    return [ReviewResponse(**r) for r in reviews]


# ========== Sentiment Analysis Endpoints ==========

@router.post("/sentiment/analyze")
async def analyze_sentiment(
    text: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Analyze sentiment of text"""
    try:
        result = sentiment_analyzer.analyze_sentiment(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
