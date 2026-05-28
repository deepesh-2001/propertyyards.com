"""
Architecture & 3D Model Generation Service
AI-powered building design, 3D modeling, and architectural visualization
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import aiohttp
import base64
import json

logger = logging.getLogger(__name__)


class BuildingType(Enum):
    """Types of buildings"""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    APARTMENT = "apartment"
    VILLA = "villa"
    PENTHOUSE = "penthouse"
    OFFICE = "office"
    RETAIL = "retail"
    MIXED_USE = "mixed_use"


class ArchitectureStyle(Enum):
    """Architecture styles"""
    MODERN = "modern"
    CONTEMPORARY = "contemporary"
    TRADITIONAL = "traditional"
    MINIMALIST = "minimalist"
    LUXURY = "luxury"
    SMART_HOME = "smart_home"
    SUSTAINABLE = "sustainable"
    CLASSIC = "classic"
    ART_DECO = "art_deco"
    MEDITERRANEAN = "mediterranean"


@dataclass
class BuildingSpecs:
    """Building specifications"""
    floors: int
    bedrooms: int
    bathrooms: int
    total_area_sqft: float
    built_up_area_sqft: float
    carpet_area_sqft: float
    parking_slots: int
    balconies: int
    facing_direction: str
    vastu_compliant: bool


@dataclass
class Generated3DModel:
    """3D model metadata"""
    id: str
    property_id: Optional[str]
    building_type: BuildingType
    style: ArchitectureStyle
    specs: BuildingSpecs
    model_data: Dict[str, Any]  # Can be GLTF, OBJ, or reference to external storage
    render_images: List[str]  # URLs to rendered views
    floor_plans: List[Dict[str, Any]]
    created_at: datetime
    is_ai_generated: bool = True
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ArchitectureGenerator:
    """Generate architectural designs and 3D models"""

    def __init__(self):
        self.api_key = None
        self.use_gemini = True
        self.model_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent"
        self.imagen_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict"
        self.shap_e_endpoint = "https://api.openai.com/v1/images/generations"  # Fallback for 3D
        self.generation_queue = asyncio.Queue()

    async def initialize(self, api_key: str, use_gemini: bool = True):
        """Initialize with API key"""
        self.api_key = api_key
        self.use_gemini = use_gemini
        logger.info(f"Architecture Generator initialized (Gemini: {use_gemini})")

    async def generate_building_design(
        self,
        building_type: BuildingType,
        style: ArchitectureStyle,
        specs: BuildingSpecs,
        location: str,
        budget_range: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Optional[Generated3DModel]:
        """Generate complete building design with 3D model"""
        try:
            # Generate architectural description
            design_prompt = self._create_design_prompt(
                building_type, style, specs, location, budget_range, preferences
            )

            # Generate 2D floor plans
            floor_plans = await self._generate_floor_plans(specs, style)

            # Generate 3D renders (multiple views)
            render_images = await self._generate_building_renders(
                building_type, style, specs, design_prompt
            )

            # Create 3D model data (GLTF format reference)
            model_data = await self._generate_3d_model_data(
                building_type, style, specs, floor_plans
            )

            return Generated3DModel(
                id=f"arch_{datetime.utcnow().timestamp()}",
                property_id=None,
                building_type=building_type,
                style=style,
                specs=specs,
                model_data=model_data,
                render_images=render_images,
                floor_plans=floor_plans,
                created_at=datetime.utcnow(),
                is_ai_generated=True,
                metadata={
                    "location": location,
                    "budget_range": budget_range,
                    "design_prompt": design_prompt,
                    "ai_model": "gemini-pro-vision"
                }
            )

        except Exception as e:
            logger.error(f"Building design generation failed: {e}")
            return None

    def _create_design_prompt(
        self,
        building_type: BuildingType,
        style: ArchitectureStyle,
        specs: BuildingSpecs,
        location: str,
        budget_range: str,
        preferences: Optional[Dict[str, Any]]
    ) -> str:
        """Create detailed design prompt"""
        prompt_parts = [
            f"Design a {building_type.value} building in {style.value} style.",
            f"Location: {location}",
            f"Floors: {specs.floors}",
            f"Bedrooms: {specs.bedrooms}",
            f"Bathrooms: {specs.bathrooms}",
            f"Total Area: {specs.total_area_sqft} sq ft",
            f"Facing: {specs.facing_direction}",
        ]

        if specs.vastu_compliant:
            prompt_parts.append("Vastu compliant design")

        if preferences:
            if preferences.get("sustainable"):
                prompt_parts.append("Sustainable/eco-friendly features")
            if preferences.get("smart_home"):
                prompt_parts.append("Smart home integration")
            if preferences.get("luxury_features"):
                prompt_parts.append("Luxury amenities")
            if preferences.get("garden"):
                prompt_parts.append("Garden/landscaping")
            if preferences.get("pool"):
                prompt_parts.append("Swimming pool")

        return " ".join(prompt_parts)

    async def _generate_floor_plans(
        self,
        specs: BuildingSpecs,
        style: ArchitectureStyle
    ) -> List[Dict[str, Any]]:
        """Generate floor plans for each level"""
        floor_plans = []

        for floor in range(1, specs.floors + 1):
            try:
                # Generate floor plan description
                plan_description = self._create_floor_plan_description(floor, specs, style)

                # Generate floor plan image
                floor_plan_image = await self._generate_architecture_image(
                    f"Technical architectural floor plan for floor {floor}: {plan_description}. "
                    f"Top-down 2D view with room labels, measurements, and dimensions. "
                    f"Professional CAD style drawing.",
                    "floor_plan"
                )

                floor_plans.append({
                    "floor": floor,
                    "description": plan_description,
                    "image_url": floor_plan_image,
                    "rooms": self._allocate_rooms(floor, specs),
                    "area_distribution": self._calculate_area_distribution(floor, specs)
                })

            except Exception as e:
                logger.error(f"Floor plan generation failed for floor {floor}: {e}")

        return floor_plans

    def _create_floor_plan_description(
        self,
        floor: int,
        specs: BuildingSpecs,
        style: ArchitectureStyle
    ) -> str:
        """Create description for floor plan"""
        if floor == 1:
            return (
                f"Ground floor with living room, kitchen, dining area, "
                f"{specs.bathrooms // specs.floors} bathrooms, and entrance. "
                f"Modern {style.value} layout with open spaces."
            )
        elif floor == specs.floors:
            return (
                f"Top floor with {specs.bedrooms} bedrooms, "
                f"{specs.bathrooms} bathrooms, master suite, and terraces."
            )
        else:
            return (
                f"Floor {floor} with mixed living spaces, "
                f"bedrooms and utility areas."
            )

    def _allocate_rooms(self, floor: int, specs: BuildingSpecs) -> List[Dict[str, Any]]:
        """Allocate rooms for a floor"""
        rooms = []

        if floor == 1:
            rooms = [
                {"name": "Living Room", "area": specs.total_area_sqft * 0.15},
                {"name": "Kitchen", "area": specs.total_area_sqft * 0.10},
                {"name": "Dining Area", "area": specs.total_area_sqft * 0.08},
                {"name": "Entrance Lobby", "area": specs.total_area_sqft * 0.05},
                {"name": "Powder Room", "area": specs.total_area_sqft * 0.03},
            ]
        elif floor == specs.floors:
            bedroom_area = specs.total_area_sqft * 0.12
            rooms = [
                {"name": "Master Bedroom", "area": bedroom_area},
                {"name": "Master Bathroom", "area": bedroom_area * 0.25},
                {"name": "Bedroom 2", "area": bedroom_area * 0.8},
                {"name": "Bedroom 3", "area": bedroom_area * 0.7},
            ]
        else:
            rooms = [
                {"name": f"Room {floor}-A", "area": specs.total_area_sqft * 0.10},
                {"name": f"Room {floor}-B", "area": specs.total_area_sqft * 0.10},
            ]

        return rooms

    def _calculate_area_distribution(
        self,
        floor: int,
        specs: BuildingSpecs
    ) -> Dict[str, float]:
        """Calculate area distribution for a floor"""
        floor_area = specs.total_area_sqft / specs.floors

        return {
            "built_up": floor_area * 0.85,
            "carpet": floor_area * 0.70,
            "common_areas": floor_area * 0.15,
            "walls": floor_area * 0.15
        }

    async def _generate_building_renders(
        self,
        building_type: BuildingType,
        style: ArchitectureStyle,
        specs: BuildingSpecs,
        design_prompt: str
    ) -> List[str]:
        """Generate multiple rendered views of the building"""
        renders = []

        views = [
            ("front_exterior", f"Front exterior view of {design_prompt}. Street view, daylight, photorealistic architectural visualization."),
            ("rear_exterior", f"Rear exterior view showing backyard/garden of {design_prompt}. Landscaping visible."),
            ("aerial", f"Aerial/bird's eye view of {design_prompt}. Full building and surroundings visible."),
            ("interior_living", f"Interior living room of {design_prompt}. Modern furniture, natural lighting, spacious."),
            ("night_view", f"Night view of {design_prompt}. Exterior with lights on, dramatic evening lighting."),
        ]

        for view_name, prompt in views:
            try:
                image_url = await self._generate_architecture_image(prompt, view_name)
                if image_url:
                    renders.append(image_url)
            except Exception as e:
                logger.error(f"Render generation failed for {view_name}: {e}")

        return renders

    async def _generate_architecture_image(
        self,
        prompt: str,
        image_type: str
    ) -> Optional[str]:
        """Generate architectural image using AI"""
        if not self.api_key:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.imagen_endpoint}?key={self.api_key}"

                payload = {
                    "instances": [{"prompt": prompt}],
                    "parameters": {
                        "aspectRatio": "16:9",
                        "sampleCount": 1,
                        "personGeneration": "allow_adult"
                    }
                }

                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "predictions" in data and data["predictions"]:
                            return f"data:image/png;base64,{data['predictions'][0].get('bytesBase64Encoded', '')}"

                    logger.error(f"Image generation failed: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Architecture image generation error: {e}")
            return None

    async def _generate_3d_model_data(
        self,
        building_type: BuildingType,
        style: ArchitectureStyle,
        specs: BuildingSpecs,
        floor_plans: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate 3D model data (GLTF format structure)"""
        # Create simplified GLTF-like structure
        model_data = {
            "asset": {
                "version": "2.0",
                "generator": "PropertyYards AI Architecture Generator"
            },
            "scene": 0,
            "scenes": [{
                "nodes": list(range(specs.floors))
            }],
            "nodes": [],
            "meshes": [],
            "materials": [],
            "buffers": [],
            "bufferViews": [],
            "accessors": [],
            "building_info": {
                "type": building_type.value,
                "style": style.value,
                "floors": specs.floors,
                "total_height_m": specs.floors * 3.5,  # Approx 3.5m per floor
                "footprint_area_sqm": specs.total_area_sqft * 0.0929,
                "floor_plans": floor_plans
            }
        }

        # Add simplified geometry for each floor
        for floor in range(specs.floors):
            model_data["nodes"].append({
                "mesh": floor,
                "translation": [0, floor * 3.5, 0]
            })

            # Simple box mesh for each floor
            model_data["meshes"].append({
                "primitives": [{
                    "attributes": {"POSITION": floor},
                    "material": 0
                }]
            })

        # Add material
        model_data["materials"].append({
            "name": f"{style.value}_material",
            "pbrMetallicRoughness": {
                "baseColorFactor": self._get_style_colors(style),
                "metallicFactor": 0.1,
                "roughnessFactor": 0.5
            }
        })

        return model_data

    def _get_style_colors(self, style: ArchitectureStyle) -> List[float]:
        """Get color palette for architecture style"""
        colors = {
            ArchitectureStyle.MODERN: [0.9, 0.9, 0.9, 1.0],  # White/gray
            ArchitectureStyle.TRADITIONAL: [0.8, 0.7, 0.6, 1.0],  # Warm beige
            ArchitectureStyle.LUXURY: [0.2, 0.2, 0.3, 1.0],  # Deep blue
            ArchitectureStyle.SUSTAINABLE: [0.6, 0.8, 0.6, 1.0],  # Green
            ArchitectureStyle.MINIMALIST: [1.0, 1.0, 1.0, 1.0],  # Pure white
        }
        return colors.get(style, [0.8, 0.8, 0.8, 1.0])

    async def generate_property_visualization(
        self,
        property_data: Dict[str, Any],
        views: List[str] = None
    ) -> Dict[str, Any]:
        """Generate visualization for existing property"""
        if views is None:
            views = ["exterior", "interior", "floor_plan"]

        try:
            results = {}

            for view in views:
                if view == "exterior":
                    results["exterior"] = await self._generate_architecture_image(
                        f"Beautiful {property_data.get('property_type', 'residential')} "
                        f"property in {property_data.get('locality', 'urban area')}. "
                        f"{property_data.get('bedrooms', 3)} BHK, "
                        f"{property_data.get('area', 1500)} sq ft. "
                        f"Photorealistic architectural exterior rendering.",
                        "exterior"
                    )

                elif view == "interior":
                    results["interior"] = await self._generate_architecture_image(
                        f"Modern interior design for {property_data.get('bedrooms', 3)} bedroom "
                        f"{property_data.get('property_type', 'apartment')}. "
                        f"Spacious living area, contemporary furniture, natural lighting. "
                        f"High-end real estate photography style.",
                        "interior"
                    )

                elif view == "floor_plan":
                    results["floor_plan"] = await self._generate_architecture_image(
                        f"Professional 2D floor plan for {property_data.get('bedrooms', 3)} BHK "
                        f"{property_data.get('property_type', 'apartment')}, "
                        f"{property_data.get('area', 1500)} sq ft. "
                        f"CAD technical drawing with measurements and room labels.",
                        "floor_plan"
                    )

            return results

        except Exception as e:
            logger.error(f"Property visualization failed: {e}")
            return {}


class Model3DStorage:
    """Storage and management for 3D models"""

    def __init__(self):
        self.collection_name = "architecture_models"

    async def save_model(
        self,
        model: Generated3DModel,
        database
    ) -> str:
        """Save 3D model to database"""
        try:
            doc = {
                "id": model.id,
                "property_id": model.property_id,
                "building_type": model.building_type.value,
                "style": model.style.value,
                "specs": {
                    "floors": model.specs.floors,
                    "bedrooms": model.specs.bedrooms,
                    "bathrooms": model.specs.bathrooms,
                    "total_area_sqft": model.specs.total_area_sqft,
                    "carpet_area_sqft": model.specs.carpet_area_sqft,
                    "facing_direction": model.specs.facing_direction,
                    "vastu_compliant": model.specs.vastu_compliant
                },
                "model_data": model.model_data,
                "render_images": model.render_images,
                "floor_plans": model.floor_plans,
                "created_at": model.created_at,
                "is_ai_generated": model.is_ai_generated,
                "metadata": model.metadata
            }

            await database[self.collection_name].insert_one(doc)
            logger.info(f"3D model saved: {model.id}")
            return model.id

        except Exception as e:
            logger.error(f"Failed to save 3D model: {e}")
            return None

    async def get_model(
        self,
        model_id: str,
        database
    ) -> Optional[Generated3DModel]:
        """Get 3D model by ID"""
        try:
            doc = await database[self.collection_name].find_one({"id": model_id})
            if doc:
                return self._doc_to_model(doc)
            return None
        except Exception as e:
            logger.error(f"Failed to get 3D model: {e}")
            return None

    async def get_models_by_property(
        self,
        property_id: str,
        database
    ) -> List[Generated3DModel]:
        """Get all models for a property"""
        try:
            cursor = database[self.collection_name].find(
                {"property_id": property_id}
            ).sort("created_at", -1)

            docs = await cursor.to_list(length=50)
            return [self._doc_to_model(doc) for doc in docs]

        except Exception as e:
            logger.error(f"Failed to get property models: {e}")
            return []

    def _doc_to_model(self, doc: Dict) -> Generated3DModel:
        """Convert document to model"""
        specs = BuildingSpecs(
            floors=doc["specs"]["floors"],
            bedrooms=doc["specs"]["bedrooms"],
            bathrooms=doc["specs"]["bathrooms"],
            total_area_sqft=doc["specs"]["total_area_sqft"],
            built_up_area_sqft=doc["specs"].get("built_up_area_sqft", 0),
            carpet_area_sqft=doc["specs"]["carpet_area_sqft"],
            parking_slots=doc["specs"].get("parking_slots", 0),
            balconies=doc["specs"].get("balconies", 0),
            facing_direction=doc["specs"]["facing_direction"],
            vastu_compliant=doc["specs"]["vastu_compliant"]
        )

        return Generated3DModel(
            id=doc["id"],
            property_id=doc.get("property_id"),
            building_type=BuildingType(doc["building_type"]),
            style=ArchitectureStyle(doc["style"]),
            specs=specs,
            model_data=doc["model_data"],
            render_images=doc["render_images"],
            floor_plans=doc["floor_plans"],
            created_at=doc["created_at"],
            is_ai_generated=doc["is_ai_generated"],
            metadata=doc.get("metadata", {})
        )


# Global instances
architecture_generator = ArchitectureGenerator()
model_3d_storage = Model3DStorage()
