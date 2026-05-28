"""
Feedback Module
Handles feedback collection, review management, and analytics
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.schemas import (
    FeedbackType,
    FeedbackCategory,
    FeedbackStatus
)

logger = logging.getLogger(__name__)


class FeedbackManager:
    """Feedback management engine"""
    
    def __init__(self):
        self.auto_response_rules = {
            FeedbackCategory.COMPLAINT: {"priority": "high", "auto_assign": True},
            FeedbackCategory.BUG_REPORT: {"priority": "high", "auto_assign": True},
            FeedbackCategory.FEATURE_REQUEST: {"priority": "medium", "auto_assign": False},
            FeedbackCategory.SUGGESTION: {"priority": "low", "auto_assign": False}
        }
    
    async def create_feedback(
        self,
        feedback_data: Dict[str, Any],
        database
    ) -> Dict[str, Any]:
        """Create a new feedback entry"""
        try:
            # Get user name if not anonymous
            user_name = None
            if not feedback_data.get("is_anonymous"):
                user = await database.users.find_one({"_id": feedback_data["user_id"]})
                if user:
                    user_name = f"{user.get('first_name', '')} {user.get('last_name', '')}"
            
            # Apply auto-response rules
            category = feedback_data["category"]
            rules = self.auto_response_rules.get(category, {"priority": "medium", "auto_assign": False})
            
            feedback = {
                **feedback_data,
                "user_name": user_name,
                "status": FeedbackStatus.PENDING,
                "admin_response": None,
                "responded_by": None,
                "responded_at": None,
                "priority": rules["priority"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await database.feedbacks.insert_one(feedback)
            feedback["id"] = str(result.inserted_id)
            
            # Auto-assign if needed
            if rules["auto_assign"]:
                await self._auto_assign_feedback(str(result.inserted_id), database)
            
            return feedback
            
        except Exception as e:
            logger.error(f"Feedback creation error: {e}")
            raise
    
    async def _auto_assign_feedback(self, feedback_id: str, database):
        """Auto-assign feedback to appropriate team member"""
        try:
            # Find available admin/support staff
            staff = await database.users.find_one(
                {"role": {"$in": ["admin", "support"]}, "is_active": True}
            )
            
            if staff:
                await database.feedbacks.update_one(
                    {"_id": feedback_id},
                    {"$set": {"assigned_to": str(staff["_id"])}}
                )
        except Exception as e:
            logger.error(f"Auto-assign error: {e}")
    
    async def respond_to_feedback(
        self,
        feedback_id: str,
        response: str,
        responded_by: str,
        database
    ) -> Dict[str, Any]:
        """Respond to feedback"""
        try:
            await database.feedbacks.update_one(
                {"_id": feedback_id},
                {
                    "$set": {
                        "admin_response": response,
                        "responded_by": responded_by,
                        "responded_at": datetime.utcnow(),
                        "status": FeedbackStatus.RESPONDED,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            feedback = await database.feedbacks.find_one({"_id": feedback_id})
            feedback["id"] = str(feedback["_id"])
            del feedback["_id"]
            
            return feedback
            
        except Exception as e:
            logger.error(f"Feedback response error: {e}")
            raise
    
    async def get_feedback_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        database
    ) -> Dict[str, Any]:
        """Get feedback analytics"""
        try:
            query = {}
            if start_date:
                query["created_at"] = {"$gte": start_date}
            if end_date:
                query["created_at"] = query.get("created_at", {})
                query["created_at"]["$lte"] = end_date
            
            feedbacks = await database.feedbacks.find(query).to_list(length=1000)
            
            total_feedback = len(feedbacks)
            
            # By type
            by_type = {}
            for f in feedbacks:
                feedback_type = f.get("feedback_type")
                by_type[feedback_type] = by_type.get(feedback_type, 0) + 1
            
            # By category
            by_category = {}
            for f in feedbacks:
                category = f.get("category")
                by_category[category] = by_category.get(category, 0) + 1
            
            # By status
            by_status = {}
            for f in feedbacks:
                status = f.get("status")
                by_status[status] = by_status.get(status, 0) + 1
            
            # Average rating
            ratings = [f.get("rating") for f in feedbacks if f.get("rating")]
            average_rating = sum(ratings) / len(ratings) if ratings else 0
            
            # Rating distribution
            rating_distribution = {}
            for r in ratings:
                rating_distribution[r] = rating_distribution.get(r, 0) + 1
            
            # Response rate
            responded = sum(1 for f in feedbacks if f.get("status") == FeedbackStatus.RESPONDED)
            response_rate = (responded / total_feedback * 100) if total_feedback > 0 else 0
            
            # Average response time
            response_times = []
            for f in feedbacks:
                if f.get("responded_at") and f.get("created_at"):
                    response_time = (f["responded_at"] - f["created_at"]).total_seconds() / 3600
                    response_times.append(response_time)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            return {
                "total_feedback": total_feedback,
                "by_type": by_type,
                "by_category": by_category,
                "by_status": by_status,
                "average_rating": average_rating,
                "rating_distribution": rating_distribution,
                "response_rate": response_rate,
                "average_response_time_hours": avg_response_time,
                "period_start": start_date,
                "period_end": end_date
            }
            
        except Exception as e:
            logger.error(f"Feedback analytics error: {e}")
            raise


class ReviewManager:
    """Review management engine"""
    
    def __init__(self):
        self.moderation_keywords = ["spam", "fake", "scam", "fraud"]
    
    async def create_review(
        self,
        review_data: Dict[str, Any],
        database
    ) -> Dict[str, Any]:
        """Create a new property review"""
        try:
            # Get user and property details
            user = await database.users.find_one({"_id": review_data["user_id"]})
            property_data = await database.properties.find_one({"_id": review_data["property_id"]})
            
            # Check for moderation
            review_text = review_data.get("review", "").lower()
            needs_moderation = any(keyword in review_text for keyword in self.moderation_keywords)
            
            review = {
                **review_data,
                "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}" if user else "Anonymous",
                "property_title": property_data.get("title", "") if property_data else "",
                "broker_name": None,
                "is_verified": False,
                "helpful_count": 0,
                "needs_moderation": needs_moderation,
                "status": "pending" if needs_moderation else "published",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Get broker name if provided
            if review_data.get("broker_id"):
                broker = await database.brokers.find_one({"_id": review_data["broker_id"]})
                if broker:
                    review["broker_name"] = broker.get("name", "")
            
            result = await database.reviews.insert_one(review)
            review["id"] = str(result.inserted_id)
            
            # Update property rating
            await self._update_property_rating(review_data["property_id"], database)
            
            return review
            
        except Exception as e:
            logger.error(f"Review creation error: {e}")
            raise
    
    async def _update_property_rating(self, property_id: str, database):
        """Update property average rating"""
        try:
            reviews = await database.reviews.find({"property_id": property_id, "status": "published"}).to_list(length=1000)
            
            if reviews:
                avg_rating = sum(r.get("rating", 0) for r in reviews) / len(reviews)
                await database.properties.update_one(
                    {"_id": property_id},
                    {"$set": {"average_rating": round(avg_rating, 1), "review_count": len(reviews)}}
                )
        except Exception as e:
            logger.error(f"Property rating update error: {e}")
    
    async def mark_review_helpful(
        self,
        review_id: str,
        user_id: str,
        database
    ) -> Dict[str, Any]:
        """Mark review as helpful"""
        try:
            # Check if user already marked it
            existing = await database.review_helpful.find_one({
                "review_id": review_id,
                "user_id": user_id
            })
            
            if existing:
                await database.review_helpful.delete_one({"_id": existing["_id"]})
                await database.reviews.update_one(
                    {"_id": review_id},
                    {"$inc": {"helpful_count": -1}}
                )
                return {"action": "unmarked", "helpful_count": -1}
            else:
                await database.review_helpful.insert_one({
                    "review_id": review_id,
                    "user_id": user_id,
                    "created_at": datetime.utcnow()
                })
                await database.reviews.update_one(
                    {"_id": review_id},
                    {"$inc": {"helpful_count": 1}}
                )
                return {"action": "marked", "helpful_count": 1}
                
        except Exception as e:
            logger.error(f"Mark helpful error: {e}")
            raise
    
    async def moderate_review(
        self,
        review_id: str,
        action: str,  # approve, reject
        moderator_id: str,
        database
    ) -> Dict[str, Any]:
        """Moderate a review"""
        try:
            status = "published" if action == "approve" else "rejected"
            
            await database.reviews.update_one(
                {"_id": review_id},
                {
                    "$set": {
                        "status": status,
                        "moderated_by": moderator_id,
                        "moderated_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            review = await database.reviews.find_one({"_id": review_id})
            
            # Update property rating if approved
            if action == "approve":
                await self._update_property_rating(review["property_id"], database)
            
            review["id"] = str(review["_id"])
            del review["_id"]
            
            return review
            
        except Exception as e:
            logger.error(f"Review moderation error: {e}")
            raise
    
    async def get_property_reviews(
        self,
        property_id: str,
        min_rating: Optional[int] = None,
        verified_only: bool = False,
        database
    ) -> List[Dict[str, Any]]:
        """Get reviews for a property"""
        try:
            query = {"property_id": property_id, "status": "published"}
            
            if min_rating:
                query["rating"] = {"$gte": min_rating}
            
            if verified_only:
                query["is_verified"] = True
            
            reviews = await database.reviews.find(query).sort("created_at", -1).to_list(length=100)
            
            for review in reviews:
                review["id"] = str(review["_id"])
                del review["_id"]
            
            return reviews
            
        except Exception as e:
            logger.error(f"Get property reviews error: {e}")
            raise


class SentimentAnalyzer:
    """Simple sentiment analysis for feedback"""
    
    def __init__(self):
        self.positive_words = [
            "good", "great", "excellent", "amazing", "wonderful", "fantastic",
            "helpful", "friendly", "professional", "efficient", "quick",
            "satisfied", "happy", "love", "recommend", "best"
        ]
        self.negative_words = [
            "bad", "poor", "terrible", "awful", "horrible", "disappointing",
            "slow", "rude", "unprofessional", "inefficient", "frustrating",
            "unsatisfied", "unhappy", "hate", "worst", "never", "avoid"
        ]
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        words = text.lower().split()
        
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        total_words = len(words)
        if total_words == 0:
            return {"sentiment": "neutral", "score": 0, "confidence": 0}
        
        score = (positive_count - negative_count) / total_words
        
        if score > 0.1:
            sentiment = "positive"
        elif score < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        confidence = min(abs(score) * 10, 1)
        
        return {
            "sentiment": sentiment,
            "score": score,
            "confidence": confidence,
            "positive_words": positive_count,
            "negative_words": negative_count
        }


# Global manager instances
feedback_manager = FeedbackManager()
review_manager = ReviewManager()
sentiment_analyzer = SentimentAnalyzer()
