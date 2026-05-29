"""
Property Layout Service
Handles property layout management and Vastu Shastra validation
"""
import math
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class Direction(Enum):
    """Cardinal directions for Vastu analysis"""
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    NORTHEAST = "northeast"
    NORTHWEST = "northwest"
    SOUTHEAST = "southeast"
    SOUTHWEST = "southwest"

class RoomType(Enum):
    """Types of rooms for layout planning"""
    LIVING_ROOM = "living_room"
    BEDROOM = "bedroom"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    PUJA_ROOM = "puja_room"
    STUDY_ROOM = "study_room"
    DINING_ROOM = "dining_room"
    STORE_ROOM = "store_room"
    BALCONY = "balcony"
    GARDEN = "garden"
    GARAGE = "garage"
    STAIRS = "stairs"

class VastuCompliance(Enum):
    """Vastu compliance levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    VIOLATION = "violation"

@dataclass
class Room:
    """Room definition for layout"""
    id: str
    name: str
    room_type: RoomType
    x: float  # Position from left (percentage 0-100)
    y: float  # Position from top (percentage 0-100)
    width: float  # Width (percentage 0-100)
    height: float  # Height (percentage 0-100)
    area_sqft: float

@dataclass
class LayoutAnalysis:
    """Layout analysis results"""
    overall_score: float
    vastu_compliance: VastuCompliance
    room_placements: Dict[str, Dict[str, Any]]
    recommendations: List[str]
    violations: List[str]

class PropertyLayoutService:
    """Service for property layout analysis and Vastu validation"""
    
    def __init__(self):
        # Vastu guidelines for ideal room placements
        self.ideal_placements = {
            RoomType.LIVING_ROOM: {
                Direction.NORTH,
                Direction.EAST,
                Direction.NORTHEAST
            },
            RoomType.BEDROOM: {
                Direction.SOUTHWEST,
                Direction.SOUTH,
                Direction.WEST
            },
            RoomType.KITCHEN: {
                Direction.SOUTHEAST,
                Direction.SOUTH
            },
            RoomType.BATHROOM: {
                Direction.SOUTHEAST,
                Direction.NORTHWEST,
                Direction.WEST
            },
            RoomType.PUJA_ROOM: {
                Direction.NORTHEAST,
                Direction.NORTH,
                Direction.EAST
            },
            RoomType.STUDY_ROOM: {
                Direction.NORTH,
                Direction.EAST,
                Direction.NORTHEAST
            },
            RoomType.DINING_ROOM: {
                Direction.WEST,
                Direction.SOUTH,
                Direction.EAST
            },
            RoomType.STORE_ROOM: {
                Direction.SOUTHWEST,
                Direction.SOUTH,
                Direction.WEST
            },
            RoomType.BALCONY: {
                Direction.NORTH,
                Direction.EAST,
                Direction.NORTHEAST
            },
            RoomType.GARDEN: {
                Direction.NORTH,
                Direction.EAST,
                Direction.NORTHEAST
            },
            RoomType.GARAGE: {
                Direction.SOUTHEAST,
                Direction.NORTHWEST,
                Direction.WEST
            },
            RoomType.STAIRS: {
                Direction.SOUTH,
                Direction.WEST,
                Direction.SOUTHWEST
            }
        }
        
        # Direction weights for scoring
        self.direction_weights = {
            Direction.NORTH: 0.9,
            Direction.SOUTH: 0.8,
            Direction.EAST: 0.9,
            Direction.WEST: 0.7,
            Direction.NORTHEAST: 1.0,
            Direction.NORTHWEST: 0.6,
            Direction.SOUTHEAST: 0.7,
            Direction.SOUTHWEST: 0.5
        }
        
        # Minimum area requirements (sqft)
        self.min_areas = {
            RoomType.LIVING_ROOM: 120,
            RoomType.BEDROOM: 80,
            RoomType.KITCHEN: 60,
            RoomType.BATHROOM: 35,
            RoomType.PUJA_ROOM: 25,
            RoomType.STUDY_ROOM: 60,
            RoomType.DINING_ROOM: 80,
            RoomType.STORE_ROOM: 40
        }

    def get_room_direction(self, room: Room, total_width: float, total_height: float) -> Direction:
        """Determine the primary direction of a room"""
        # Calculate room center
        center_x = room.x + (room.width / 2)
        center_y = room.y + (room.height / 2)
        
        # Convert to relative position (0-1)
        rel_x = center_x / 100
        rel_y = center_y / 100
        
        # Determine direction based on position
        if rel_x < 0.33 and rel_y < 0.33:
            return Direction.NORTHWEST
        elif rel_x < 0.33 and rel_y > 0.67:
            return Direction.SOUTHWEST
        elif rel_x > 0.67 and rel_y < 0.33:
            return Direction.NORTHEAST
        elif rel_x > 0.67 and rel_y > 0.67:
            return Direction.SOUTHEAST
        elif rel_x < 0.33:
            return Direction.WEST
        elif rel_x > 0.67:
            return Direction.EAST
        elif rel_y < 0.33:
            return Direction.NORTH
        else:
            return Direction.SOUTH

    def calculate_room_score(self, room: Room, total_width: float, total_height: float) -> Tuple[float, Dict[str, Any]]:
        """Calculate Vastu score for a room"""
        direction = self.get_room_direction(room, total_width, total_height)
        ideal_directions = self.ideal_placements.get(room.room_type, set())
        
        # Check if direction is ideal
        is_ideal = direction in ideal_directions
        base_score = self.direction_weights.get(direction, 0.5)
        
        # Adjust score based on ideal placement
        if is_ideal:
            score = base_score * 1.0
        else:
            # Find closest ideal direction
            closest_score = 0
            for ideal_dir in ideal_directions:
                closest_score = max(closest_score, self.direction_weights.get(ideal_dir, 0.5))
            score = base_score * 0.7  # Penalty for non-ideal placement
        
        # Area validation
        area_score = 1.0
        min_area = self.min_areas.get(room.room_type, 0)
        if room.area_sqft < min_area:
            area_score = room.area_sqft / min_area if min_area > 0 else 0.5
        
        # Proportions validation (avoid odd shapes)
        aspect_ratio = room.width / room.height if room.height > 0 else 1
        proportion_score = 1.0
        if aspect_ratio < 0.5 or aspect_ratio > 2.0:
            proportion_score = 0.7
        
        final_score = score * area_score * proportion_score
        
        analysis = {
            "direction": direction.value,
            "is_ideal": is_ideal,
            "ideal_directions": [d.value for d in ideal_directions],
            "area_score": area_score,
            "proportion_score": proportion_score,
            "aspect_ratio": aspect_ratio,
            "base_score": base_score
        }
        
        return final_score, analysis

    def analyze_layout(self, rooms: List[Dict[str, Any]], total_width: float, total_height: float) -> LayoutAnalysis:
        """Analyze complete property layout"""
        room_objects = []
        total_score = 0.0
        room_analyses = {}
        recommendations = []
        violations = []
        
        # Convert room dictionaries to Room objects
        for room_data in rooms:
            try:
                room = Room(
                    id=room_data.get("id", f"room_{len(room_objects)}"),
                    name=room_data.get("name", "Unknown Room"),
                    room_type=RoomType(room_data.get("room_type")),
                    x=room_data.get("x", 0),
                    y=room_data.get("y", 0),
                    width=room_data.get("width", 10),
                    height=room_data.get("height", 10),
                    area_sqft=room_data.get("area_sqft", 100)
                )
                room_objects.append(room)
            except (ValueError, KeyError) as e:
                logger.warning(f"Invalid room data: {room_data}, error: {e}")
                continue
        
        # Analyze each room
        for room in room_objects:
            score, analysis = self.calculate_room_score(room, total_width, total_height)
            total_score += score
            room_analyses[room.id] = analysis
            
            # Generate recommendations and violations
            if not analysis["is_ideal"]:
                ideal_dirs = analysis["ideal_directions"]
                recommendations.append(
                    f"Move {room.name} from {analysis['direction']} to ideal direction: {', '.join(ideal_dirs)}"
                )
            
            if analysis["area_score"] < 0.8:
                min_area = self.min_areas.get(room.room_type, 0)
                recommendations.append(
                    f"Increase {room.name} area to at least {min_area} sqft (current: {room.area_sqft} sqft)"
                )
            
            if analysis["proportion_score"] < 0.8:
                recommendations.append(
                    f"Improve {room.name} proportions (current ratio: {analysis['aspect_ratio']:.2f})"
                )
        
        # Calculate overall score
        if room_objects:
            overall_score = total_score / len(room_objects)
        else:
            overall_score = 0.0
        
        # Determine compliance level
        if overall_score >= 0.9:
            compliance = VastuCompliance.EXCELLENT
        elif overall_score >= 0.8:
            compliance = VastuCompliance.GOOD
        elif overall_score >= 0.6:
            compliance = VastuCompliance.AVERAGE
        elif overall_score >= 0.4:
            compliance = VastuCompliance.POOR
        else:
            compliance = VastuCompliance.VIOLATION
            violations.append("Major Vastu principles violated - consult Vastu expert")
        
        # Add general recommendations
        if overall_score < 0.7:
            recommendations.append("Consider consulting a Vastu expert for major improvements")
        
        if len(room_objects) < 5:
            recommendations.append("Add more essential rooms for complete Vastu compliance")
        
        return LayoutAnalysis(
            overall_score=overall_score,
            vastu_compliance=compliance,
            room_placements=room_analyses,
            recommendations=recommendations,
            violations=violations
        )

    def generate_optimal_layout(self, property_type: str, total_area: float, rooms_required: List[str]) -> Dict[str, Any]:
        """Generate optimal Vastu-compliant layout"""
        layout = {
            "property_type": property_type,
            "total_area": total_area,
            "rooms": [],
            "vastu_score": 0.0
        }
        
        # Define room sizes based on total area
        room_sizes = self._calculate_room_sizes(total_area, rooms_required)
        
        # Place rooms according to Vastu principles
        room_placements = self._place_rooms_vastu(room_sizes)
        
        layout["rooms"] = room_placements
        
        # Calculate expected Vastu score
        expected_score = sum(placement["vastu_score"] for placement in room_placements) / len(room_placements)
        layout["vastu_score"] = expected_score
        
        return layout

    def _calculate_room_sizes(self, total_area: float, rooms_required: List[str]) -> Dict[str, float]:
        """Calculate optimal room sizes based on total area"""
        # Standard room size percentages
        size_percentages = {
            "living_room": 0.20,
            "bedroom": 0.15,
            "kitchen": 0.12,
            "bathroom": 0.08,
            "puja_room": 0.05,
            "study_room": 0.10,
            "dining_room": 0.12,
            "store_room": 0.06,
            "balcony": 0.08,
            "garden": 0.10,
            "garage": 0.15,
            "stairs": 0.06
        }
        
        room_sizes = {}
        available_area = total_area * 0.85  # 85% usable area
        
        for room_type in rooms_required:
            percentage = size_percentages.get(room_type, 0.10)
            room_sizes[room_type] = available_area * percentage
        
        return room_sizes

    def _place_rooms_vastu(self, room_sizes: Dict[str, float]) -> List[Dict[str, Any]]:
        """Place rooms according to Vastu principles"""
        placements = []
        
        # Define optimal positions (x, y, width, height as percentages)
        optimal_positions = {
            "living_room": {"x": 20, "y": 40, "width": 40, "height": 30},
            "bedroom": {"x": 60, "y": 60, "width": 35, "height": 30},
            "kitchen": {"x": 60, "y": 20, "width": 30, "height": 25},
            "bathroom": {"x": 10, "y": 70, "width": 20, "height": 20},
            "puja_room": {"x": 35, "y": 10, "width": 25, "height": 20},
            "study_room": {"x": 10, "y": 20, "width": 25, "height": 25},
            "dining_room": {"x": 35, "y": 70, "width": 30, "height": 20},
            "store_room": {"x": 70, "y": 85, "width": 20, "height": 10},
            "balcony": {"x": 5, "y": 40, "width": 15, "height": 20},
            "garden": {"x": 5, "y": 5, "width": 25, "height": 15},
            "garage": {"x": 75, "y": 5, "width": 20, "height": 15},
            "stairs": {"x": 85, "y": 40, "width": 10, "height": 40}
        }
        
        for room_type, area in room_sizes.items():
            if room_type in optimal_positions:
                position = optimal_positions[room_type]
                placement = {
                    "room_type": room_type,
                    "area_sqft": area,
                    "position": position,
                    "vastu_score": 0.9,  # High score for optimal placement
                    "direction": self._get_direction_from_position(position)
                }
                placements.append(placement)
        
        return placements

    def _get_direction_from_position(self, position: Dict[str, float]) -> str:
        """Get direction from position coordinates"""
        center_x = position["x"] + (position["width"] / 2)
        center_y = position["y"] + (position["height"] / 2)
        
        if center_x < 33 and center_y < 33:
            return "northwest"
        elif center_x < 33 and center_y > 67:
            return "southwest"
        elif center_x > 67 and center_y < 33:
            return "northeast"
        elif center_x > 67 and center_y > 67:
            return "southeast"
        elif center_x < 33:
            return "west"
        elif center_x > 67:
            return "east"
        elif center_y < 33:
            return "north"
        else:
            return "south"

    def validate_vastu_compliance(self, layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate layout against Vastu principles"""
        try:
            rooms = layout_data.get("rooms", [])
            total_width = layout_data.get("total_width", 100)
            total_height = layout_data.get("total_height", 100)
            
            analysis = self.analyze_layout(rooms, total_width, total_height)
            
            return {
                "is_vastu_compliant": analysis.vastu_compliance in [VastuCompliance.EXCELLENT, VastuCompliance.GOOD],
                "compliance_level": analysis.vastu_compliance.value,
                "overall_score": analysis.overall_score,
                "room_analysis": analysis.room_placements,
                "recommendations": analysis.recommendations,
                "violations": analysis.violations,
                "vastu_tips": self._get_vastu_tips(analysis)
            }
            
        except Exception as e:
            logger.error(f"Vastu validation error: {e}")
            return {
                "is_vastu_compliant": False,
                "error": str(e),
                "compliance_level": "error"
            }

    def _get_vastu_tips(self, analysis: LayoutAnalysis) -> List[str]:
        """Get Vastu improvement tips based on analysis"""
        tips = []
        
        if analysis.overall_score < 0.8:
            tips.append("Ensure main entrance is in North, East, or Northeast direction")
            tips.append("Keep the center of the house open and clutter-free")
            tips.append("Place heavy furniture in South or West directions")
        
        if analysis.overall_score < 0.6:
            tips.append("Avoid having bedrooms in Northeast direction")
            tips.append("Kitchen should be in Southeast with cooking facing East")
            tips.append("Bathrooms are best in Northwest or Southeast")
        
        # Add specific tips based on room placements
        for room_id, room_analysis in analysis.room_placements.items():
            if not room_analysis["is_ideal"]:
                room_type = room_id.replace("_", " ").title()
                current_dir = room_analysis["direction"]
                ideal_dirs = room_analysis["ideal_directions"]
                tips.append(f"{room_type} in {current_dir} - consider moving to {', '.join(ideal_dirs)}")
        
        return tips

# Global instance
property_layout_service = PropertyLayoutService()
