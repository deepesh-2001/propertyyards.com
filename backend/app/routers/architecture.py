"""
Architecture Router
API endpoints for 3D building models and architectural design
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_user
from app.architecture_service import (
    architecture_generator, model_3d_storage,
    BuildingType, ArchitectureStyle, BuildingSpecs, Generated3DModel
)

router = APIRouter(prefix="/api/architecture", tags=["architecture"])


class BuildingSpecsRequest(BaseModel):
    """Building specifications request"""
    floors: int = 2
    bedrooms: int = 3
    bathrooms: int = 3
    total_area_sqft: float = 2000
    carpet_area_sqft: float = 1600
    parking_slots: int = 2
    balconies: int = 2
    facing_direction: str = "North"
    vastu_compliant: bool = True


class GenerateDesignRequest(BaseModel):
    """Request to generate building design"""
    building_type: str  # residential, commercial, villa, apartment, etc.
    style: str  # modern, contemporary, traditional, luxury, etc.
    specs: BuildingSpecsRequest
    location: str
    budget_range: str = "medium"  # low, medium, high, luxury
    preferences: Optional[Dict[str, Any]] = None


class PropertyVisualizationRequest(BaseModel):
    """Request to visualize existing property"""
    property_id: str
    views: List[str] = ["exterior", "interior", "floor_plan"]


# ========== 3D Model & Design Generation ==========

@router.post("/generate-design")
async def generate_building_design(
    request: GenerateDesignRequest,
    background_tasks: BackgroundTasks = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate complete building design with 3D model, floor plans, and renders"""
    if current_user.get("role") not in ["admin", "agent"]:
        raise HTTPException(status_code=403, detail="Admin or Agent access required")

    try:
        # Convert request to enums
        building_type = BuildingType(request.building_type)
        style = ArchitectureStyle(request.style)

        specs = BuildingSpecs(
            floors=request.specs.floors,
            bedrooms=request.specs.bedrooms,
            bathrooms=request.specs.bathrooms,
            total_area_sqft=request.specs.total_area_sqft,
            built_up_area_sqft=request.specs.total_area_sqft * 0.85,
            carpet_area_sqft=request.specs.carpet_area_sqft,
            parking_slots=request.specs.parking_slots,
            balconies=request.specs.balconies,
            facing_direction=request.specs.facing_direction,
            vastu_compliant=request.specs.vastu_compliant
        )

        # Generate design
        design = await architecture_generator.generate_building_design(
            building_type=building_type,
            style=style,
            specs=specs,
            location=request.location,
            budget_range=request.budget_range,
            preferences=request.preferences
        )

        if not design:
            raise HTTPException(status_code=500, detail="Design generation failed")

        # Save to database
        model_id = await model_3d_storage.save_model(design, database)

        return {
            "model_id": model_id,
            "building_type": design.building_type.value,
            "style": design.style.value,
            "specs": {
                "floors": design.specs.floors,
                "bedrooms": design.specs.bedrooms,
                "bathrooms": design.specs.bathrooms,
                "total_area_sqft": design.specs.total_area_sqft
            },
            "render_images": design.render_images[:3] if design.render_images else [],
            "floor_count": len(design.floor_plans),
            "created_at": design.created_at,
            "message": "Building design generated successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid building type or style: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visualize-property")
async def visualize_property(
    request: PropertyVisualizationRequest,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate AI visualization for existing property"""
    try:
        # Get property data
        property_data = await database.properties.find_one(
            {"_id": request.property_id}
        )

        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")

        # Generate visualizations
        visualizations = await architecture_generator.generate_property_visualization(
            property_data,
            request.views
        )

        return {
            "property_id": request.property_id,
            "visualizations": visualizations,
            "generated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_id}")
async def get_3d_model(
    model_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get 3D model by ID"""
    try:
        model = await model_3d_storage.get_model(model_id, database)

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        return {
            "model_id": model.id,
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
            "metadata": model.metadata,
            "created_at": model.created_at
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/property/{property_id}/models")
async def get_property_models(
    property_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all 3D models for a property"""
    try:
        models = await model_3d_storage.get_models_by_property(property_id, database)

        return {
            "property_id": property_id,
            "models": [
                {
                    "model_id": m.id,
                    "building_type": m.building_type.value,
                    "style": m.style.value,
                    "floors": m.specs.floors,
                    "preview_image": m.render_images[0] if m.render_images else None,
                    "created_at": m.created_at
                }
                for m in models
            ],
            "count": len(models)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/styles")
async def get_architecture_styles():
    """Get available architecture styles"""
    styles = [
        {"value": s.value, "name": s.name, "description": _get_style_description(s)}
        for s in ArchitectureStyle
    ]
    return {"styles": styles}


@router.get("/building-types")
async def get_building_types():
    """Get available building types"""
    types = [
        {"value": t.value, "name": t.name.replace("_", " ").title()}
        for t in BuildingType
    ]
    return {"building_types": types}


@router.get("/model/{model_id}/floor-plan/{floor}")
async def get_floor_plan(
    model_id: str,
    floor: int,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get floor plan for specific floor"""
    try:
        model = await model_3d_storage.get_model(model_id, database)

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        floor_plan = None
        for fp in model.floor_plans:
            if fp["floor"] == floor:
                floor_plan = fp
                break

        if not floor_plan:
            raise HTTPException(status_code=404, detail=f"Floor {floor} not found")

        return {
            "model_id": model_id,
            "floor": floor,
            "floor_plan": floor_plan
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/{model_id}/3d-view")
async def get_3d_view(
    model_id: str,
    view_angle: str = "isometric",  # isometric, front, side, top
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get 3D model data for viewing"""
    try:
        model = await model_3d_storage.get_model(model_id, database)

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Return GLTF-like data for 3D viewer
        return {
            "model_id": model_id,
            "view_angle": view_angle,
            "model_data": model.model_data,
            "building_info": model.model_data.get("building_info", {}),
            "viewer_config": {
                "camera_position": _get_camera_position(view_angle),
                "lighting": "daylight",
                "background": "sky"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-redesign")
async def ai_redesign(
    model_id: str,
    new_style: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """AI redesign of existing building with new style"""
    if current_user.get("role") not in ["admin", "agent"]:
        raise HTTPException(status_code=403, detail="Admin or Agent access required")

    try:
        # Get original model
        original = await model_3d_storage.get_model(model_id, database)
        if not original:
            raise HTTPException(status_code=404, detail="Model not found")

        # Convert to new style
        new_style_enum = ArchitectureStyle(new_style)

        # Generate new design with same specs but new style
        new_design = await architecture_generator.generate_building_design(
            building_type=original.building_type,
            style=new_style_enum,
            specs=original.specs,
            location=original.metadata.get("location", "Unknown"),
            budget_range=original.metadata.get("budget_range", "medium")
        )

        if not new_design:
            raise HTTPException(status_code=500, detail="Redesign failed")

        # Save new design
        new_model_id = await model_3d_storage.save_model(new_design, database)

        return {
            "original_model_id": model_id,
            "new_model_id": new_model_id,
            "original_style": original.style.value,
            "new_style": new_style,
            "message": "Building redesigned successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid style: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_style_description(style: ArchitectureStyle) -> str:
    """Get description for architecture style"""
    descriptions = {
        ArchitectureStyle.MODERN: "Clean lines, minimal ornamentation, open floor plans",
        ArchitectureStyle.CONTEMPORARY: "Current trends, innovative materials, sustainable",
        ArchitectureStyle.TRADITIONAL: "Classic elements, timeless design, cultural heritage",
        ArchitectureStyle.MINIMALIST: "Simplicity, essential elements, uncluttered spaces",
        ArchitectureStyle.LUXURY: "High-end finishes, premium amenities, exclusive design",
        ArchitectureStyle.SMART_HOME: "Technology integrated, automated systems, connected",
        ArchitectureStyle.SUSTAINABLE: "Eco-friendly materials, energy efficient, green design",
        ArchitectureStyle.CLASSIC: "Historical influences, elegant proportions, refined details",
        ArchitectureStyle.ART_DECO: "Geometric patterns, bold colors, decorative elements",
        ArchitectureStyle.MEDITERRANEAN: "Warm colors, arches, courtyards, coastal influence"
    }
    return descriptions.get(style, "")


def _get_camera_position(view_angle: str) -> List[float]:
    """Get camera position for 3D view"""
    positions = {
        "isometric": [50, 50, 50],
        "front": [0, 20, 50],
        "side": [50, 20, 0],
        "top": [0, 80, 0],
        "rear": [0, 20, -50]
    }
    return positions.get(view_angle, [50, 50, 50])


from datetime import datetime
