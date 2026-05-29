"""
Property Layout Router
API endpoints for property layout management and Vastu validation
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.auth import get_current_user
from app.property_layout_service import property_layout_service, RoomType, VastuCompliance

router = APIRouter(prefix="/api/property-layout", tags=["property-layout"])

# ========== Request Models ==========

class RoomRequest(BaseModel):
    id: str
    name: str
    room_type: str
    x: float = Field(ge=0, le=100, description="X position as percentage")
    y: float = Field(ge=0, le=100, description="Y position as percentage")
    width: float = Field(ge=1, le=100, description="Width as percentage")
    height: float = Field(ge=1, le=100, description="Height as percentage")
    area_sqft: float = Field(gt=0, description="Area in square feet")

class LayoutAnalysisRequest(BaseModel):
    rooms: List[RoomRequest]
    total_width: float = Field(default=100, ge=10, le=1000)
    total_height: float = Field(default=100, ge=10, le=1000)

class OptimalLayoutRequest(BaseModel):
    property_type: str
    total_area: float = Field(gt=0, description="Total area in square feet")
    rooms_required: List[str]

class VastuValidationRequest(BaseModel):
    layout_data: Dict[str, Any]

# ========== Layout Analysis Endpoints ==========

@router.post("/analyze")
async def analyze_property_layout(
    request: LayoutAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyze property layout for Vastu compliance"""
    try:
        # Convert request to service format
        rooms_data = []
        for room in request.rooms:
            rooms_data.append({
                "id": room.id,
                "name": room.name,
                "room_type": room.room_type,
                "x": room.x,
                "y": room.y,
                "width": room.width,
                "height": room.height,
                "area_sqft": room.area_sqft
            })
        
        # Analyze layout
        analysis = property_layout_service.analyze_layout(
            rooms_data, 
            request.total_width, 
            request.total_height
        )
        
        return {
            "success": True,
            "data": {
                "overall_score": analysis.overall_score,
                "vastu_compliance": analysis.vastu_compliance.value,
                "room_placements": analysis.room_placements,
                "recommendations": analysis.recommendations,
                "violations": analysis.violations,
                "total_rooms": len(rooms_data)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Layout analysis failed: {str(e)}")


@router.post("/validate-vastu")
async def validate_vastu_compliance(
    request: VastuValidationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Validate layout against Vastu principles"""
    try:
        validation_result = property_layout_service.validate_vastu_compliance(request.layout_data)
        
        return {
            "success": True,
            "data": validation_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vastu validation failed: {str(e)}")


@router.post("/generate-optimal")
async def generate_optimal_layout(
    request: OptimalLayoutRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate optimal Vastu-compliant layout"""
    try:
        optimal_layout = property_layout_service.generate_optimal_layout(
            request.property_type,
            request.total_area,
            request.rooms_required
        )
        
        return {
            "success": True,
            "data": optimal_layout
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimal layout generation failed: {str(e)}")


# ========== Room Management Endpoints ==========

@router.get("/room-types")
async def get_room_types():
    """Get available room types for layout planning"""
    try:
        room_types = [
            {
                "value": room_type.value,
                "label": room_type.value.replace("_", " ").title(),
                "description": f"{room_type.value.replace('_', ' ').title()} for property layout"
            }
            for room_type in RoomType
        ]
        
        return {
            "success": True,
            "data": room_types
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get room types: {str(e)}")


@router.get("/vastu-directions")
async def get_vastu_directions():
    """Get Vastu directions and their significance"""
    try:
        directions = {
            "north": {
                "label": "North",
                "significance": "Prosperity, wealth, health",
                "ideal_for": ["living_room", "puja_room", "study_room", "balcony", "garden"],
                "avoid": ["bedroom", "bathroom", "store_room"]
            },
            "south": {
                "label": "South",
                "significance": "Name, fame, reputation",
                "ideal_for": ["bedroom", "dining_room", "store_room"],
                "avoid": ["puja_room", "study_room"]
            },
            "east": {
                "label": "East",
                "significance": "Health, wealth, prosperity",
                "ideal_for": ["living_room", "study_room", "dining room", "balcony"],
                "avoid": ["bedroom", "store room"]
            },
            "west": {
                "label": "West",
                "significance": "Name, fame, prosperity",
                "ideal_for": ["bedroom", "dining_room", "store room", "bathroom"],
                "avoid": ["puja room", "study room"]
            },
            "northeast": {
                "label": "Northeast (Ishanya)",
                "significance": "Spirituality, prosperity, divine blessings",
                "ideal_for": ["puja_room", "study room", "living room", "garden"],
                "avoid": ["bedroom", "kitchen", "bathroom", "store room"]
            },
            "northwest": {
                "label": "Northwest (Vayavya)",
                "significance": "Wealth, prosperity, social connections",
                "ideal_for": ["bathroom", "guest room", "garage"],
                "avoid": ["kitchen", "puja room", "store room"]
            },
            "southeast": {
                "label": "Southeast (Agneya)",
                "significance": "Health, wealth, digestion",
                "ideal_for": ["kitchen", "bathroom", "dining room"],
                "avoid": ["bedroom", "puja room", "study room"]
            },
            "southwest": {
                "label": "Southwest (Nairitya)",
                "significance": "Stability, strength, relationships",
                "ideal_for": ["bedroom", "store room", "master bedroom"],
                "avoid": ["kitchen", "puja room", "bathroom", "study room"]
            }
        }
        
        return {
            "success": True,
            "data": directions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Vastu directions: {str(e)}")


@router.get("/vastu-compliance-levels")
async def get_vastu_compliance_levels():
    """Get Vastu compliance levels and their meanings"""
    try:
        compliance_levels = {
            "excellent": {
                "label": "Excellent",
                "score_range": "90-100%",
                "description": "Perfect Vastu compliance with optimal energy flow",
                "color": "#10b981",
                "recommendation": "Maintain current layout"
            },
            "good": {
                "label": "Good",
                "score_range": "80-89%",
                "description": "Good Vastu compliance with minor improvements possible",
                "color": "#3b82f6",
                "recommendation": "Consider minor adjustments for better energy flow"
            },
            "average": {
                "label": "Average",
                "score_range": "60-79%",
                "description": "Moderate Vastu compliance with room for improvement",
                "color": "#f59e0b",
                "recommendation": "Several improvements recommended"
            },
            "poor": {
                "label": "Poor",
                "score_range": "40-59%",
                "description": "Low Vastu compliance requiring significant changes",
                "color": "#ef4444",
                "recommendation": "Major restructuring recommended"
            },
            "violation": {
                "label": "Violation",
                "score_range": "0-39%",
                "description": "Major Vastu violations - consult expert immediately",
                "color": "#7c2d12",
                "recommendation": "Consult Vastu expert for complete redesign"
            }
        }
        
        return {
            "success": True,
            "data": compliance_levels
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get compliance levels: {str(e)}")


# ========== Templates and Presets ==========

@router.get("/templates")
async def get_layout_templates():
    """Get pre-defined layout templates for different property types"""
    try:
        templates = {
            "1bhk_apartment": {
                "name": "1 BHK Apartment",
                "description": "Optimal layout for 1 bedroom hall kitchen apartment",
                "total_area": 600,
                "rooms": [
                    {
                        "room_type": "living_room",
                        "area_sqft": 150,
                        "position": {"x": 10, "y": 40, "width": 40, "height": 35}
                    },
                    {
                        "room_type": "bedroom",
                        "area_sqft": 120,
                        "position": {"x": 60, "y": 60, "width": 35, "height": 30}
                    },
                    {
                        "room_type": "kitchen",
                        "area_sqft": 80,
                        "position": {"x": 60, "y": 20, "width": 30, "height": 25}
                    },
                    {
                        "room_type": "bathroom",
                        "area_sqft": 40,
                        "position": {"x": 10, "y": 75, "width": 20, "height": 15}
                    }
                ],
                "expected_vastu_score": 0.85
            },
            "2bhk_apartment": {
                "name": "2 BHK Apartment",
                "description": "Optimal layout for 2 bedroom hall kitchen apartment",
                "total_area": 1000,
                "rooms": [
                    {
                        "room_type": "living_room",
                        "area_sqft": 200,
                        "position": {"x": 10, "y": 40, "width": 35, "height": 30}
                    },
                    {
                        "room_type": "bedroom",
                        "area_sqft": 150,
                        "position": {"x": 60, "y": 60, "width": 35, "height": 30}
                    },
                    {
                        "room_type": "bedroom",
                        "area_sqft": 120,
                        "position": {"x": 60, "y": 20, "width": 35, "height": 25}
                    },
                    {
                        "room_type": "kitchen",
                        "area_sqft": 100,
                        "position": {"x": 10, "y": 75, "width": 25, "height": 20}
                    },
                    {
                        "room_type": "bathroom",
                        "area_sqft": 50,
                        "position": {"x": 40, "y": 75, "width": 15, "height": 20}
                    }
                ],
                "expected_vastu_score": 0.88
            },
            "independent_house": {
                "name": "Independent House",
                "description": "Optimal layout for independent house with garden",
                "total_area": 2000,
                "rooms": [
                    {
                        "room_type": "living_room",
                        "area_sqft": 300,
                        "position": {"x": 20, "y": 40, "width": 30, "height": 25}
                    },
                    {
                        "room_type": "bedroom",
                        "area_sqft": 200,
                        "position": {"x": 60, "y": 60, "width": 30, "height": 25}
                    },
                    {
                        "room_type": "kitchen",
                        "area_sqft": 150,
                        "position": {"x": 60, "y": 20, "width": 25, "height": 20}
                    },
                    {
                        "room_type": "puja_room",
                        "area_sqft": 50,
                        "position": {"x": 35, "y": 10, "width": 20, "height": 15}
                    },
                    {
                        "room_type": "study_room",
                        "area_sqft": 100,
                        "position": {"x": 10, "y": 20, "width": 20, "height": 15}
                    },
                    {
                        "room_type": "dining_room",
                        "area_sqft": 120,
                        "position": {"x": 20, "y": 70, "width": 25, "height": 20}
                    },
                    {
                        "room_type": "garden",
                        "area_sqft": 400,
                        "position": {"x": 5, "y": 5, "width": 30, "height": 15}
                    }
                ],
                "expected_vastu_score": 0.92
            }
        }
        
        return {
            "success": True,
            "data": templates
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")


@router.post("/apply-template")
async def apply_layout_template(
    template_name: str,
    total_area: float,
    current_user: dict = Depends(get_current_user)
):
    """Apply a template to specific property area"""
    try:
        templates = await get_layout_templates()
        template_data = templates["data"].get(template_name)
        
        if not template_data:
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
        
        # Scale rooms based on actual area
        area_ratio = total_area / template_data["total_area"]
        scaled_rooms = []
        
        for room in template_data["rooms"]:
            scaled_room = room.copy()
            scaled_room["area_sqft"] = room["area_sqft"] * area_ratio
            scaled_rooms.append(scaled_room)
        
        return {
            "success": True,
            "data": {
                "template_name": template_name,
                "original_area": template_data["total_area"],
                "scaled_area": total_area,
                "area_ratio": area_ratio,
                "rooms": scaled_rooms,
                "expected_vastu_score": template_data["expected_vastu_score"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply template: {str(e)}")


# ========== Utility Endpoints ==========

@router.get("/guidelines")
async def get_vastu_guidelines():
    """Get comprehensive Vastu guidelines"""
    try:
        guidelines = {
            "general_principles": [
                "Main entrance should be in North, East, or Northeast",
                "Center of the house (Brahmasthan) should be open and clutter-free",
                "Heavy furniture should be placed in South or West",
                "Light furniture should be placed in North or East",
                "Windows should be larger in East and North compared to West and South",
                "Avoid having pillars in the center of rooms"
            ],
            "room_specific": {
                "living_room": "Best in North, East, or Northeast for positive energy",
                "bedroom": "Master bedroom should be in Southwest for stability",
                "kitchen": "Southeast is ideal, with cooking facing East",
                "bathroom": "Northwest or Southeast, never in Northeast",
                "puja_room": "Northeast is most auspicious for divine energy",
                "study_room": "North or East for concentration and knowledge"
            },
            "elements": {
                "water": "Northeast direction - fountains, water features",
                "fire": "Southeast direction - kitchen, electrical equipment",
                "earth": "Southwest direction - heavy items, storage",
                "air": "Northwest direction - ventilation, windows",
                "space": "Center of the house - open areas"
            },
            "colors": {
                "north": "Green, blue for prosperity",
                "south": "Red, orange for energy",
                "east": "White, light green for health",
                "west": "Blue, gray for stability",
                "northeast": "Yellow, white for spirituality",
                "southeast": "Red, orange for digestion",
                "northwest": "White, gray for social connections",
                "southwest": "Brown, cream for stability"
            }
        }
        
        return {
            "success": True,
            "data": guidelines
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get guidelines: {str(e)}")


@router.get("/health")
async def layout_service_health():
    """Check property layout service health"""
    try:
        # Test basic functionality
        test_rooms = [
            {
                "id": "test_room",
                "name": "Test Room",
                "room_type": "living_room",
                "x": 50,
                "y": 50,
                "width": 20,
                "height": 20,
                "area_sqft": 200
            }
        ]
        
        analysis = property_layout_service.analyze_layout(test_rooms, 100, 100)
        
        return {
            "status": "healthy",
            "service": "property_layout_service",
            "test_result": {
                "analysis_completed": True,
                "test_score": analysis.overall_score,
                "compliance_level": analysis.vastu_compliance.value
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "property_layout_service",
            "error": str(e)
        }
