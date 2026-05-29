"""
Astrology Router
API endpoints for astrology talking feature with birth chart analysis and predictions
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user
from app.astrology_service import astrology_service, AstrologyCategory

router = APIRouter(prefix="/api/astrology", tags=["astrology"])

# ========== Request Models ==========

class BirthDataRequest(BaseModel):
    name: str
    birth_date: str = Field(..., description="Birth date in YYYY-MM-DD format")
    birth_time: str = Field(default="12:00", description="Birth time in HH:MM format")
    birth_place: str
    latitude: float = Field(default=28.6139, description="Latitude of birth place")
    longitude: float = Field(default=77.2090, description="Longitude of birth place")
    timezone: str = Field(default="Asia/Kolkata", description="Timezone")

class CategoryInsightRequest(BaseModel):
    categories: List[str] = Field(default_factory=list)

class DailyPredictionRequest(BaseModel):
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format")

class ChatMessageRequest(BaseModel):
    message: str
    context: Optional[str] = None

class RemediesRequest(BaseModel):
    planet: str
    issue_type: str

# ========== Birth Chart Endpoints ==========

@router.post("/birth-chart")
async def create_birth_chart(
    request: BirthDataRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create and analyze birth chart"""
    try:
        birth_data = request.dict()
        birth_data["user_id"] = str(current_user.get("_id"))
        
        # Calculate birth chart
        birth_chart = astrology_service.calculate_birth_chart(birth_data)
        
        return {
            "success": True,
            "data": {
                "user_id": birth_chart.user_id,
                "name": birth_chart.name,
                "birth_date": birth_chart.birth_date.isoformat(),
                "birth_place": birth_chart.birth_place,
                "ascendant": birth_chart.ascendant.value,
                "sun_sign": birth_chart.sun_sign.value,
                "moon_sign": birth_chart.moon_sign.value,
                "dasha_period": birth_chart.dasha_period,
                "planetary_positions": [
                    {
                        "planet": pos.planet.value,
                        "zodiac_sign": pos.zodiac_sign.value,
                        "degree": pos.degree,
                        "house": pos.house.value,
                        "is_retrograde": pos.is_retrograde
                    }
                    for pos in birth_chart.planetary_positions
                ],
                "current_transits": birth_chart.current_transits
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Birth chart creation failed: {str(e)}")


@router.get("/birth-chart/{user_id}")
async def get_birth_chart(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get existing birth chart for user"""
    try:
        # In production, this would fetch from database
        # For now, return a message indicating storage needed
        return {
            "success": True,
            "message": "Birth chart data would be retrieved from database",
            "user_id": user_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get birth chart: {str(e)}")


# ========== Insights and Predictions ==========

@router.post("/insights")
async def get_astrology_insights(
    request: CategoryInsightRequest,
    current_user: dict = Depends(get_current_user)
):
    """Get astrology insights for specific categories"""
    try:
        # For demo, create a sample birth chart
        sample_birth_data = {
            "user_id": str(current_user.get("_id")),
            "name": current_user.get("name", "User"),
            "birth_date": "1990-01-01",
            "birth_time": "12:00",
            "birth_place": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": "Asia/Kolkata"
        }
        
        birth_chart = astrology_service.calculate_birth_chart(sample_birth_data)
        categories = request.categories if request.categories else [cat.value for cat in AstrologyCategory]
        
        insights = astrology_service.generate_astrology_insights(birth_chart, categories)
        
        return {
            "success": True,
            "data": {
                "insights": [
                    {
                        "category": insight.category.value,
                        "title": insight.title,
                        "description": insight.description,
                        "prediction": insight.prediction,
                        "confidence": insight.confidence,
                        "remedies": insight.remedies,
                        "favorable_period": insight.favorable_period,
                        "challenges": insight.challenges,
                        "recommendations": insight.recommendations
                    }
                    for insight in insights
                ],
                "birth_chart_summary": {
                    "sun_sign": birth_chart.sun_sign.value,
                    "moon_sign": birth_chart.moon_sign.value,
                    "ascendant": birth_chart.ascendant.value,
                    "dasha_period": birth_chart.dasha_period
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@router.get("/daily-prediction")
async def get_daily_prediction(
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get daily prediction"""
    try:
        # Parse date or use today
        if date:
            prediction_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            prediction_date = datetime.utcnow()
        
        # Create sample birth chart for demo
        sample_birth_data = {
            "user_id": str(current_user.get("_id")),
            "name": current_user.get("name", "User"),
            "birth_date": "1990-01-01",
            "birth_time": "12:00",
            "birth_place": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": "Asia/Kolkata"
        }
        
        birth_chart = astrology_service.calculate_birth_chart(sample_birth_data)
        daily_prediction = astrology_service.get_daily_prediction(birth_chart, prediction_date)
        
        return {
            "success": True,
            "data": daily_prediction
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get daily prediction: {str(e)}")


@router.get("/weekly-predictions")
async def get_weekly_predictions(
    current_user: dict = Depends(get_current_user)
):
    """Get predictions for the week"""
    try:
        predictions = []
        current_date = datetime.utcnow()
        
        # Create sample birth chart
        sample_birth_data = {
            "user_id": str(current_user.get("_id")),
            "name": current_user.get("name", "User"),
            "birth_date": "1990-01-01",
            "birth_time": "12:00",
            "birth_place": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": "Asia/Kolkata"
        }
        
        birth_chart = astrology_service.calculate_birth_chart(sample_birth_data)
        
        # Generate predictions for each day of the week
        for i in range(7):
            date = current_date + timedelta(days=i)
            daily_pred = astrology_service.get_daily_prediction(birth_chart, date)
            predictions.append(daily_pred)
        
        return {
            "success": True,
            "data": {
                "predictions": predictions,
                "week_summary": f"Overall week looks {predictions[0]['overall_rating']} with favorable planetary positions"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get weekly predictions: {str(e)}")


# ========== Chat and Consultation ==========

@router.post("/chat")
async def astrology_chat(
    request: ChatMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """Chat with astrology AI assistant"""
    try:
        # Create sample birth chart for context
        sample_birth_data = {
            "user_id": str(current_user.get("_id")),
            "name": current_user.get("name", "User"),
            "birth_date": "1990-01-01",
            "birth_time": "12:00",
            "birth_place": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": "Asia/Kolkata"
        }
        
        birth_chart = astrology_service.calculate_birth_chart(sample_birth_data)
        
        # Generate contextual response
        response = generate_chat_response(request.message, birth_chart, request.context)
        
        return {
            "success": True,
            "data": {
                "message": response["message"],
                "category": response["category"],
                "confidence": response["confidence"],
                "follow_up_questions": response["follow_up_questions"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


def generate_chat_response(message: str, birth_chart: BirthChart, context: str = None) -> Dict[str, Any]:
    """Generate contextual chat response"""
    message_lower = message.lower()
    
    # Career-related queries
    if any(word in message_lower for word in ["career", "job", "work", "profession"]):
        insight = astrology_service._analyze_career(birth_chart)
        return {
            "message": f"Based on your birth chart, {insight.prediction} {insight.recommendations[0] if insight.recommendations else ''}",
            "category": "career",
            "confidence": insight.confidence,
            "follow_up_questions": ["What field are you considering?", "Do you want to know about business prospects?"]
        }
    
    # Relationship queries
    elif any(word in message_lower for word in ["relationship", "love", "marriage", "partner"]):
        insight = astrology_service._analyze_relationship(birth_chart)
        return {
            "message": f"Regarding relationships, {insight.prediction} {insight.recommendations[0] if insight.recommendations else ''}",
            "category": "relationship",
            "confidence": insight.confidence,
            "follow_up_questions": ["Are you currently in a relationship?", "Would you like to know about marriage timing?"]
        }
    
    # Health queries
    elif any(word in message_lower for word in ["health", "illness", "fitness", "wellness"]):
        insight = astrology_service._analyze_health(birth_chart)
        return {
            "message": f"For your health, {insight.prediction} {insight.remedies[0] if insight.remedies else ''}",
            "category": "health",
            "confidence": insight.confidence,
            "follow_up_questions": ["Do you have any specific health concerns?", "Would you like remedies for wellness?"]
        }
    
    # Finance queries
    elif any(word in message_lower for word in ["money", "finance", "investment", "wealth"]):
        insight = astrology_service._analyze_finance(birth_chart)
        return {
            "message": f"Regarding finances, {insight.prediction} {insight.recommendations[0] if insight.recommendations else ''}",
            "category": "finance",
            "confidence": insight.confidence,
            "follow_up_questions": ["Are you planning any investments?", "Would you like to know about property investment?"]
        }
    
    # General queries
    else:
        return {
            "message": f"Based on your {birth_chart.sun_sign.value} sun sign and {birth_chart.moon_sign.value} moon sign, you have a balanced personality. Your current {birth_chart.dasha_period} period brings opportunities for growth. What specific area would you like guidance on?",
            "category": "general",
            "confidence": 0.7,
            "follow_up_questions": ["Would you like career guidance?", "How about relationship advice?", "Are you interested in financial predictions?"]
        }


# ========== Remedies and Solutions ==========

@router.get("/remedies")
async def get_remedies(
    planet: Optional[str] = None,
    issue_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get astrological remedies"""
    try:
        if planet:
            # Get planet-specific remedies
            try:
                planet_enum = next(p for p in astrology_service.planet_natures.keys() if p.value == planet.lower())
                remedies = astrology_service.remedies_database.get(planet_enum, [])
            except:
                remedies = []
        else:
            # Get general remedies
            remedies = [
                "Chant Gayatri Mantra daily",
                "Meditate for 15 minutes every morning",
                "Offer water to Sun in copper vessel",
                "Feed birds and animals",
                "Donate to charities on your birthday"
            ]
        
        return {
            "success": True,
            "data": {
                "remedies": remedies,
                "planet": planet,
                "issue_type": issue_type,
                "instructions": "Perform remedies with faith and consistency for best results"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get remedies: {str(e)}")


@router.post("/remedies/custom")
async def get_custom_remedies(
    request: RemediesRequest,
    current_user: dict = Depends(get_current_user)
):
    """Get custom remedies based on planet and issue"""
    try:
        # Get planet remedies
        try:
            planet_enum = next(p for p in astrology_service.planet_natures.keys() if p.value == request.planet.lower())
            base_remedies = astrology_service.remedies_database.get(planet_enum, [])
        except:
            base_remedies = []
        
        # Add issue-specific remedies
        issue_remedies = {
            "career": ["Focus on Saturn remedies for career growth", "Chant mantras before important meetings"],
            "relationship": ["Perform Venus remedies on Fridays", "Offer flowers to deities"],
            "health": ["Practice yoga and pranayama", "Maintain regular meditation"],
            "finance": ["Donate to charities on Thursdays", "Keep money box in clean place"]
        }
        
        custom_remedies = base_remedies + issue_remedies.get(request.issue_type.lower(), [])
        
        return {
            "success": True,
            "data": {
                "custom_remedies": custom_remedies,
                "planet": request.planet,
                "issue_type": request.issue_type,
                "duration": "Perform for 40 days for best results",
                "timing": "Early morning or evening hours are most auspicious"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get custom remedies: {str(e)}")


# ========== Educational Content ==========

@router.get("/zodiac-signs")
async def get_zodiac_signs():
    """Get information about all zodiac signs"""
    try:
        zodiac_info = {}
        for sign in astrology_service.zodiac_characteristics:
            characteristics = astrology_service.zodiac_characteristics[sign]
            zodiac_info[sign.value] = {
                "element": characteristics["element"],
                "ruler": characteristics["ruler"].value,
                "nature": characteristics["nature"],
                "dates": get_zodiac_dates(sign),
                "traits": get_zodiac_traits(sign)
            }
        
        return {
            "success": True,
            "data": zodiac_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get zodiac signs: {str(e)}")


@router.get("/planets")
async def get_planets():
    """Get information about all planets"""
    try:
        planets_info = {}
        for planet in astrology_service.planet_natures:
            characteristics = astrology_service.planet_natures[planet]
            planets_info[planet.value] = {
                "element": characteristics["element"],
                "quality": characteristics["quality"],
                "ruling_house": characteristics["ruling_house"].value if characteristics["ruling_house"] else None,
                "nature": get_planet_nature(planet),
                "remedies": astrology_service.remedies_database.get(planet, [])
            }
        
        return {
            "success": True,
            "data": planets_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get planets: {str(e)}")


@router.get("/houses")
async def get_houses():
    """Get information about all houses"""
    try:
        houses_info = {}
        for house in astrology_service.house_meanings:
            houses_info[house.value] = {
                "meaning": astrology_service.house_meanings[house],
                "ruling_planet": get_house_ruler(house),
                "significance": get_house_significance(house)
            }
        
        return {
            "success": True,
            "data": houses_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get houses: {str(e)}")


# ========== Utility Functions ==========

def get_zodiac_dates(sign) -> str:
    """Get zodiac date ranges"""
    dates = {
        "aries": "March 21 - April 19",
        "taurus": "April 20 - May 20",
        "gemini": "May 21 - June 20",
        "cancer": "June 21 - July 22",
        "leo": "July 23 - August 22",
        "virgo": "August 23 - September 22",
        "libra": "September 23 - October 22",
        "scorpio": "October 23 - November 21",
        "sagittarius": "November 22 - December 21",
        "capricorn": "December 22 - January 19",
        "aquarius": "January 20 - February 18",
        "pisces": "February 19 - March 20"
    }
    return dates.get(sign.value, "Date range not available")

def get_zodiac_traits(sign) -> List[str]:
    """Get zodiac sign traits"""
    traits = {
        "aries": ["Courageous", "Energetic", "Impulsive", "Leadership"],
        "taurus": ["Reliable", "Patient", "Practical", "Stubborn"],
        "gemini": ["Adaptable", "Outgoing", "Intelligent", "Inconsistent"],
        "cancer": ["Emotional", "Intuitive", "Protective", "Moody"],
        "leo": ["Confident", "Ambitious", "Generous", "Arrogant"],
        "virgo": ["Analytical", "Helpful", "Perfectionist", "Critical"],
        "libra": ["Diplomatic", "Graceful", "Idealistic", "Indecisive"],
        "scorpio": ["Passionate", "Stubborn", "Resourceful", "Jealous"],
        "sagittarius": ["Generous", "Idealistic", "Restless", "Impatient"],
        "capricorn": ["Responsible", "Disciplined", "Know-it-all", "Unforgiving"],
        "aquarius": ["Progressive", "Original", "Independent", "Temperamental"],
        "pisces": ["Compassionate", "Artistic", "Intuitive", "Fearful"]
    }
    return traits.get(sign.value, [])

def get_planet_nature(planet) -> str:
    """Get planet nature description"""
    natures = {
        "sun": "Soul, ego, vitality, father",
        "moon": "Mind, emotions, mother, intuition",
        "mars": "Energy, action, courage, conflict",
        "mercury": "Communication, intelligence, learning",
        "jupiter": "Wisdom, expansion, fortune, teacher",
        "venus": "Love, beauty, relationships, arts",
        "saturn": "Discipline, limitation, responsibility",
        "rahu": "Ambition, innovation, foreign lands",
        "ketu": "Spirituality, detachment, past life"
    }
    return natures.get(planet.value, "Celestial body")

def get_house_ruler(house) -> str:
    """Get ruling planet for house"""
    rulers = {
        1: "mars",
        2: "venus",
        3: "mercury",
        4: "moon",
        5: "sun",
        6: "mercury",
        7: "venus",
        8: "mars",
        9: "jupiter",
        10: "saturn",
        11: "saturn",
        12: "jupiter"
    }
    return rulers.get(house.value, "Unknown")

def get_house_significance(house) -> str:
    """Get house significance"""
    significances = {
        1: "Self, personality, appearance, beginnings",
        2: "Wealth, possessions, family values, speech",
        3: "Communication, siblings, short journeys, courage",
        4: "Home, mother, roots, property, vehicles",
        5: "Children, creativity, romance, intelligence",
        6: "Health, enemies, service, obstacles",
        7: "Partnerships, marriage, business relationships",
        8: "Transformation, death, inheritance, longevity",
        9: "Higher learning, fortune, spirituality, father",
        10: "Career, reputation, achievements, authority",
        11: "Gains, social network, elder siblings, hopes",
        12: "Losses, expenses, spirituality, foreign lands"
    }
    return significances.get(house.value, "House significance")


# ========== Health Check ==========

@router.get("/health")
async def astrology_service_health():
    """Check astrology service health"""
    try:
        # Test basic functionality
        test_birth_data = {
            "user_id": "test",
            "name": "Test User",
            "birth_date": "1990-01-01",
            "birth_time": "12:00",
            "birth_place": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": "Asia/Kolkata"
        }
        
        birth_chart = astrology_service.calculate_birth_chart(test_birth_data)
        insights = astrology_service.generate_astrology_insights(birth_chart, ["career"])
        
        return {
            "status": "healthy",
            "service": "astrology_service",
            "test_result": {
                "birth_chart_created": True,
                "insights_generated": len(insights) > 0,
                "categories_available": len(AstrologyCategory)
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "astrology_service",
            "error": str(e)
        }
