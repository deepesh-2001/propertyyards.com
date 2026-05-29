"""
Inventory Management System (IMS) Router
API endpoints for inventory operations
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field

from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


# ========== Request Models - Property ==========

class AddPropertyInventoryRequest(BaseModel):
    property_id: Optional[str] = None
    property_type: str = "apartment"  # apartment, villa, plot, commercial
    city: str
    locality: str
    address: str
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area_sqft: Optional[float] = None
    price: Optional[float] = None
    status: str = "available"
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None


class UpdatePropertyStatusRequest(BaseModel):
    status: str  # available, reserved, sold, rented, under_maintenance
    reason: Optional[str] = None
    reserved_by: Optional[str] = None
    reservation_duration_hours: Optional[int] = 48


class PropertySearchRequest(BaseModel):
    city: Optional[str] = None
    locality: Optional[str] = None
    property_type: Optional[str] = None
    status: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_bedrooms: Optional[int] = None
    available_only: bool = False


# ========== Request Models - Medicine ==========

class AddMedicineRequest(BaseModel):
    medicine_id: Optional[str] = None
    name: str
    generic_name: Optional[str] = None
    brand: Optional[str] = None
    category: str = "general"
    prescription_required: bool = False
    dosage_form: str = "tablet"
    strength: Optional[str] = None
    batch_number: str = ""
    quantity: int = Field(gt=0)
    unit: str = "pieces"
    mrp: float = Field(ge=0)
    cost_price: float = Field(ge=0)
    selling_price: float = Field(ge=0)
    gst_percentage: float = 12.0
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    reorder_level: int = 10
    max_stock_level: int = 1000
    storage_location: str = "default"
    supplier_id: Optional[str] = None


class UpdateStockRequest(BaseModel):
    quantity_change: int  # Positive for inward, negative for outward
    movement_type: str  # inward, outward, return, adjustment, transfer
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    notes: Optional[str] = None


class SellMedicineRequest(BaseModel):
    medicine_id: str
    quantity: int = Field(gt=0)


class MedicineSearchRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    prescription_required: Optional[bool] = None
    in_stock_only: bool = False
    expiring_within_days: Optional[int] = None


# ========== Property Inventory Endpoints ==========

@router.post("/property/add")
async def add_property_inventory(
    request: AddPropertyInventoryRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add new property to inventory"""
    try:
        from app.inventory_service import inventory_service
        
        property_data = request.dict()
        item = await inventory_service.add_property_inventory(property_data)
        
        return {
            "success": True,
            "property_id": item.property_id,
            "id": item.id,
            "status": item.status.value,
            "message": f"Property added to inventory: {item.city} - {item.locality}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/property/{property_id}/status")
async def update_property_status(
    property_id: str,
    request: UpdatePropertyStatusRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update property status"""
    try:
        from app.inventory_service import inventory_service, PropertyStatus
        
        new_status = PropertyStatus(request.status)
        
        item = await inventory_service.update_property_status(
            property_id=property_id,
            new_status=new_status,
            reason=request.reason,
            reserved_by=request.reserved_by,
            reservation_duration_hours=request.reservation_duration_hours
        )
        
        return {
            "success": True,
            "property_id": property_id,
            "new_status": item.status.value,
            "previous_status": request.status,
            "message": f"Property status updated to {item.status.value}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/property/search")
async def search_property_inventory(
    city: Optional[str] = None,
    locality: Optional[str] = None,
    property_type: Optional[str] = None,
    status: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_bedrooms: Optional[int] = None,
    available_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Search property inventory"""
    try:
        from app.inventory_service import inventory_service
        
        results = await inventory_service.search_property_inventory(
            city=city,
            locality=locality,
            property_type=property_type,
            status=status,
            min_price=min_price,
            max_price=max_price,
            min_bedrooms=min_bedrooms,
            available_only=available_only
        )
        
        return {
            "total": len(results),
            "properties": [
                {
                    "id": p.id,
                    "property_id": p.property_id,
                    "property_type": p.property_type,
                    "city": p.city,
                    "locality": p.locality,
                    "address": p.address,
                    "bedrooms": p.bedrooms,
                    "bathrooms": p.bathrooms,
                    "area_sqft": p.area_sqft,
                    "price": p.price,
                    "status": p.status.value,
                    "reserved_by": p.reserved_by,
                    "reserved_until": p.reserved_until.isoformat() if p.reserved_until else None,
                    "available_from": p.available_from.isoformat() if p.available_from else None
                }
                for p in results
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/property/{property_id}")
async def get_property_details(
    property_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get property inventory details"""
    try:
        from app.inventory_service import inventory_service
        
        item = None
        for p in inventory_service.property_inventory.values():
            if p.property_id == property_id:
                item = p
                break
        
        if not item:
            raise HTTPException(status_code=404, detail="Property not found")
        
        return {
            "id": item.id,
            "property_id": item.property_id,
            "property_type": item.property_type,
            "city": item.city,
            "locality": item.locality,
            "address": item.address,
            "bedrooms": item.bedrooms,
            "bathrooms": item.bathrooms,
            "area_sqft": item.area_sqft,
            "price": item.price,
            "status": item.status.value,
            "status_reason": item.status_reason,
            "reserved_by": item.reserved_by,
            "reserved_until": item.reserved_until.isoformat() if item.reserved_until else None,
            "available_from": item.available_from.isoformat() if item.available_from else None,
            "available_until": item.available_until.isoformat() if item.available_until else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Medicine Inventory Endpoints ==========

@router.post("/medicine/add")
async def add_medicine(
    request: AddMedicineRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add new medicine to inventory"""
    try:
        from app.inventory_service import inventory_service
        
        medicine_data = request.dict()
        item = await inventory_service.add_medicine_inventory(medicine_data)
        
        return {
            "success": True,
            "medicine_id": item.medicine_id,
            "id": item.id,
            "name": item.name,
            "quantity": item.quantity,
            "status": item.status.value,
            "days_until_expiry": item.days_until_expiry,
            "message": f"Medicine added: {item.name} ({item.quantity} units)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/medicine/{medicine_id}/stock")
async def update_medicine_stock(
    medicine_id: str,
    request: UpdateStockRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update medicine stock"""
    try:
        from app.inventory_service import inventory_service, StockMovementType
        
        movement_type = StockMovementType(request.movement_type)
        
        item = await inventory_service.update_medicine_stock(
            medicine_id=medicine_id,
            quantity_change=request.quantity_change,
            movement_type=movement_type,
            reference_id=request.reference_id,
            reference_type=request.reference_type,
            notes=request.notes,
            performed_by=str(current_user.get("_id"))
        )
        
        return {
            "success": True,
            "medicine_id": medicine_id,
            "name": item.name,
            "new_quantity": item.quantity,
            "status": item.status.value,
            "message": f"Stock updated: {item.name} now has {item.quantity} units"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/medicine/sell")
async def sell_medicine(
    request: SellMedicineRequest,
    current_user: dict = Depends(get_current_user)
):
    """Sell medicine and update inventory"""
    try:
        from app.inventory_service import inventory_service
        import uuid
        
        sale_id = str(uuid.uuid4())
        
        result = await inventory_service.sell_medicine(
            medicine_id=request.medicine_id,
            quantity=request.quantity,
            sale_id=sale_id,
            performed_by=str(current_user.get("_id"))
        )
        
        return {
            "success": True,
            "sale_id": sale_id,
            "medicine_name": result["medicine_name"],
            "quantity_sold": result["quantity_sold"],
            "unit_price": result["unit_price"],
            "sale_value": result["sale_value"],
            "gst_amount": result["gst_amount"],
            "total_amount": result["total_amount"],
            "remaining_stock": result["remaining_stock"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/medicine/search")
async def search_medicine(
    name: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    prescription_required: Optional[bool] = None,
    in_stock_only: bool = False,
    expiring_within_days: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Search medicine inventory"""
    try:
        from app.inventory_service import inventory_service
        
        results = await inventory_service.search_medicine_inventory(
            name=name,
            category=category,
            status=status,
            prescription_required=prescription_required,
            in_stock_only=in_stock_only,
            expiring_within_days=expiring_within_days
        )
        
        return {
            "total": len(results),
            "medicines": [
                {
                    "id": m.id,
                    "medicine_id": m.medicine_id,
                    "name": m.name,
                    "generic_name": m.generic_name,
                    "brand": m.brand,
                    "category": m.category,
                    "prescription_required": m.prescription_required,
                    "dosage_form": m.dosage_form,
                    "strength": m.strength,
                    "batch_number": m.batch_number,
                    "quantity": m.quantity,
                    "unit": m.unit,
                    "mrp": m.mrp,
                    "selling_price": m.selling_price,
                    "status": m.status.value,
                    "expiry_date": m.expiry_date.isoformat() if m.expiry_date else None,
                    "days_until_expiry": m.days_until_expiry,
                    "is_expired": m.is_expired,
                    "storage_location": m.storage_location
                }
                for m in results
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/medicine/{medicine_id}")
async def get_medicine_details(
    medicine_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get medicine inventory details"""
    try:
        from app.inventory_service import inventory_service
        
        item = None
        for m in inventory_service.medicine_inventory.values():
            if m.medicine_id == medicine_id:
                item = m
                break
        
        if not item:
            raise HTTPException(status_code=404, detail="Medicine not found")
        
        return {
            "id": item.id,
            "medicine_id": item.medicine_id,
            "name": item.name,
            "generic_name": item.generic_name,
            "brand": item.brand,
            "category": item.category,
            "prescription_required": item.prescription_required,
            "dosage_form": item.dosage_form,
            "strength": item.strength,
            "batch_number": item.batch_number,
            "quantity": item.quantity,
            "unit": item.unit,
            "mrp": item.mrp,
            "cost_price": item.cost_price,
            "selling_price": item.selling_price,
            "gst_percentage": item.gst_percentage,
            "status": item.status.value,
            "reorder_level": item.reorder_level,
            "max_stock_level": item.max_stock_level,
            "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
            "days_until_expiry": item.days_until_expiry,
            "is_expired": item.is_expired,
            "storage_location": item.storage_location,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Stock Movement Endpoints ==========

@router.get("/movements")
async def get_stock_movements(
    inventory_type: Optional[str] = None,
    item_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get stock movement history"""
    try:
        from app.inventory_service import inventory_service, InventoryType
        
        inv_type = InventoryType(inventory_type) if inventory_type else None
        
        movements = await inventory_service.get_stock_movement_history(
            inventory_type=inv_type,
            item_id=item_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "total": len(movements),
            "movements": [
                {
                    "id": m.id,
                    "inventory_type": m.inventory_type.value,
                    "item_id": m.item_id,
                    "movement_type": m.movement_type.value,
                    "quantity": m.quantity,
                    "previous_quantity": m.previous_quantity,
                    "new_quantity": m.new_quantity,
                    "reference_id": m.reference_id,
                    "reference_type": m.reference_type,
                    "notes": m.notes,
                    "performed_by": m.performed_by,
                    "created_at": m.created_at.isoformat() if m.created_at else None
                }
                for m in movements
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Alerts Endpoints ==========

@router.get("/alerts")
async def get_alerts(
    inventory_type: Optional[str] = None,
    severity: Optional[str] = None,
    is_resolved: bool = False,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get inventory alerts"""
    try:
        from app.inventory_service import inventory_service, InventoryType
        
        inv_type = InventoryType(inventory_type) if inventory_type else None
        
        alerts = await inventory_service.get_alerts(
            inventory_type=inv_type,
            severity=severity,
            is_resolved=is_resolved,
            limit=limit
        )
        
        return {
            "total": len(alerts),
            "alerts": [
                {
                    "id": a.id,
                    "inventory_type": a.inventory_type.value,
                    "item_id": a.item_id,
                    "alert_type": a.alert_type,
                    "severity": a.severity,
                    "message": a.message,
                    "is_resolved": a.is_resolved,
                    "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
                    "created_at": a.created_at.isoformat() if a.created_at else None
                }
                for a in alerts
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Resolve inventory alert"""
    try:
        from app.inventory_service import inventory_service
        
        alert = await inventory_service.resolve_alert(
            alert_id=alert_id,
            resolved_by=str(current_user.get("_id"))
        )
        
        return {
            "success": True,
            "alert_id": alert_id,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "message": "Alert resolved successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Dashboard & Reports ==========

@router.get("/dashboard")
async def get_inventory_dashboard(
    current_user: dict = Depends(get_current_user)
):
    """Get inventory dashboard summary"""
    try:
        from app.inventory_service import inventory_service
        
        dashboard = await inventory_service.get_inventory_dashboard()
        return dashboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/medicine/valuation")
async def get_medicine_valuation(
    current_user: dict = Depends(get_current_user)
):
    """Get medicine inventory valuation report"""
    try:
        from app.inventory_service import inventory_service
        
        valuation = await inventory_service.get_medicine_valuation()
        return valuation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_medicine_categories(
    current_user: dict = Depends(get_current_user)
):
    """Get medicine categories"""
    return {
        "categories": [
            "general",
            "antibiotic",
            "pain_relief",
            "vitamin",
            "supplement",
            "digestive",
            "respiratory",
            "cardiac",
            "diabetic",
            "dermatology",
            "eye_ear",
            "pediatric",
            "emergency"
        ]
    }


@router.get("/storage-locations")
async def get_storage_locations(
    current_user: dict = Depends(get_current_user)
):
    """Get medicine storage locations"""
    return {
        "locations": [
            "default",
            "refrigerator",
            "freezer",
            "room_temperature",
            "controlled_room_temperature",
            "secure_cabinet",
            "hazardous_storage"
        ]
    }


# ========== Admin Endpoints ==========

@router.get("/admin/stock-report")
async def admin_stock_report(
    inventory_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Admin: Get comprehensive stock report"""
    if current_user.get("role") not in ["admin", "inventory_manager"]:
        raise HTTPException(status_code=403, detail="Admin/Inventory Manager access required")
    
    try:
        from app.inventory_service import inventory_service
        
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "property": {},
            "medicine": {}
        }
        
        if not inventory_type or inventory_type == "property":
            report["property"] = {
                "total_count": len(inventory_service.property_inventory),
                "status_breakdown": {},
                "city_breakdown": {}
            }
            
            for item in inventory_service.property_inventory.values():
                status = item.status.value
                report["property"]["status_breakdown"][status] = report["property"]["status_breakdown"].get(status, 0) + 1
                
                city = item.city
                report["property"]["city_breakdown"][city] = report["property"]["city_breakdown"].get(city, 0) + 1
        
        if not inventory_type or inventory_type == "medicine":
            valuation = await inventory_service.get_medicine_valuation()
            report["medicine"] = valuation
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
