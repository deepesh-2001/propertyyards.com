"""
Inventory Management System (IMS)
Comprehensive inventory tracking for:
- Property inventory (real estate listings, availability)
- Medicine inventory (pharmacy stock, expiry tracking)
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field
from enum import Enum
from bson import ObjectId
import json

logger = logging.getLogger(__name__)


class InventoryType(Enum):
    """Types of inventory"""
    PROPERTY = "property"
    MEDICINE = "medicine"


class PropertyStatus(Enum):
    """Property inventory status"""
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    RENTED = "rented"
    UNDER_MAINTENANCE = "under_maintenance"
    COMING_SOON = "coming_soon"


class MedicineStatus(Enum):
    """Medicine inventory status"""
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    EXPIRED = "expired"
    DISCONTINUED = "discontinued"


class StockMovementType(Enum):
    """Types of stock movements"""
    INWARD = "inward"          # Stock added
    OUTWARD = "outward"        # Stock removed/sold
    RETURN = "return"          # Customer return
    ADJUSTMENT = "adjustment"  # Inventory adjustment
    TRANSFER = "transfer"      # Location transfer
    EXPIRED = "expired"        # Expired stock


@dataclass
class PropertyInventoryItem:
    """Property inventory record"""
    id: str
    property_id: str
    property_type: str  # apartment, villa, plot, commercial
    
    # Location
    city: str
    locality: str
    address: str
    
    # Details
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area_sqft: Optional[float] = None
    price: Optional[float] = None
    
    # Status
    status: PropertyStatus = PropertyStatus.AVAILABLE
    status_reason: Optional[str] = None  # Why status changed
    
    # Availability
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    
    # Tracking
    reserved_by: Optional[str] = None  # User ID who reserved
    reserved_until: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = None
    updated_at: datetime = None
    last_status_change: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class MedicineInventoryItem:
    """Medicine inventory record"""
    id: str
    medicine_id: str
    name: str
    generic_name: Optional[str] = None
    brand: Optional[str] = None
    
    # Classification
    category: str = "general"  # antibiotic, pain_relief, vitamin, etc.
    prescription_required: bool = False
    dosage_form: str = "tablet"  # tablet, capsule, syrup, injection, etc.
    strength: Optional[str] = None  # 500mg, 10ml, etc.
    
    # Stock
    batch_number: str = ""
    quantity: int = 0
    unit: str = "pieces"  # pieces, strips, bottles, boxes
    
    # Pricing
    mrp: float = 0.0  # Maximum Retail Price
    cost_price: float = 0.0
    selling_price: float = 0.0
    gst_percentage: float = 12.0  # GST on medicines
    
    # Expiry
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    shelf_life_days: Optional[int] = None
    
    # Status
    status: MedicineStatus = MedicineStatus.IN_STOCK
    reorder_level: int = 10  # Alert when stock below this
    max_stock_level: int = 1000  # Maximum stock to maintain
    
    # Location
    storage_location: str = "default"  # shelf, refrigerator, etc.
    
    # Metadata
    supplier_id: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    @property
    def days_until_expiry(self) -> Optional[int]:
        """Calculate days until expiry"""
        if not self.expiry_date:
            return None
        return (self.expiry_date - date.today()).days
    
    @property
    def is_expired(self) -> bool:
        """Check if medicine is expired"""
        if not self.expiry_date:
            return False
        return self.expiry_date < date.today()


@dataclass
class StockMovement:
    """Stock movement record"""
    id: str
    inventory_type: InventoryType
    item_id: str  # Property or Medicine ID
    
    movement_type: StockMovementType
    quantity: int  # Positive for inward, negative for outward
    previous_quantity: int
    new_quantity: int
    
    # Reference
    reference_id: Optional[str] = None  # Sale ID, Purchase ID, etc.
    reference_type: Optional[str] = None  # sale, purchase, return
    
    # Details
    notes: Optional[str] = None
    performed_by: Optional[str] = None  # User ID
    
    # Timestamps
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class InventoryAlert:
    """Inventory alert record"""
    id: str
    inventory_type: InventoryType
    item_id: str
    alert_type: str  # low_stock, expired, expiring_soon, overstock
    severity: str  # low, medium, high, critical
    message: str
    
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class InventoryManagementService:
    """Comprehensive Inventory Management Service"""

    def __init__(self):
        self.enabled = True
        
        # Storage (replace with database in production)
        self.property_inventory: Dict[str, PropertyInventoryItem] = {}
        self.medicine_inventory: Dict[str, MedicineInventoryItem] = {}
        self.stock_movements: List[StockMovement] = []
        self.alerts: Dict[str, InventoryAlert] = {}
        
        # Configuration
        self.expiry_warning_days = 30  # Alert 30 days before expiry
        self.low_stock_threshold = 10
        self.auto_check_interval = 3600  # Check inventory every hour
        
        # Database reference (set during initialization)
        self.database = None

    async def initialize(self, database=None):
        """Initialize IMS with database"""
        self.database = database
        
        if database:
            # Load from database
            await self._load_from_db()
        
        logger.info("Inventory Management Service initialized")
        
        # Start background tasks
        asyncio.create_task(self._background_inventory_check())

    async def _load_from_db(self):
        """Load inventory from database"""
        try:
            if not self.database:
                return
            
            # Load property inventory
            property_collection = self.database.property_inventory
            async for doc in property_collection.find():
                item = PropertyInventoryItem(
                    id=str(doc.get("_id")),
                    property_id=doc.get("property_id"),
                    property_type=doc.get("property_type"),
                    city=doc.get("city"),
                    locality=doc.get("locality"),
                    address=doc.get("address"),
                    bedrooms=doc.get("bedrooms"),
                    bathrooms=doc.get("bathrooms"),
                    area_sqft=doc.get("area_sqft"),
                    price=doc.get("price"),
                    status=PropertyStatus(doc.get("status", "available")),
                    available_from=doc.get("available_from"),
                    available_until=doc.get("available_until")
                )
                self.property_inventory[item.id] = item
            
            # Load medicine inventory
            medicine_collection = self.database.medicine_inventory
            async for doc in medicine_collection.find():
                item = MedicineInventoryItem(
                    id=str(doc.get("_id")),
                    medicine_id=doc.get("medicine_id"),
                    name=doc.get("name"),
                    generic_name=doc.get("generic_name"),
                    brand=doc.get("brand"),
                    category=doc.get("category", "general"),
                    prescription_required=doc.get("prescription_required", False),
                    dosage_form=doc.get("dosage_form", "tablet"),
                    strength=doc.get("strength"),
                    batch_number=doc.get("batch_number", ""),
                    quantity=doc.get("quantity", 0),
                    unit=doc.get("unit", "pieces"),
                    mrp=doc.get("mrp", 0.0),
                    cost_price=doc.get("cost_price", 0.0),
                    selling_price=doc.get("selling_price", 0.0),
                    gst_percentage=doc.get("gst_percentage", 12.0),
                    manufacturing_date=doc.get("manufacturing_date"),
                    expiry_date=doc.get("expiry_date"),
                    reorder_level=doc.get("reorder_level", 10),
                    max_stock_level=doc.get("max_stock_level", 1000),
                    storage_location=doc.get("storage_location", "default"),
                    supplier_id=doc.get("supplier_id")
                )
                self.medicine_inventory[item.id] = item
            
            logger.info(f"Loaded {len(self.property_inventory)} properties, {len(self.medicine_inventory)} medicines")
            
        except Exception as e:
            logger.error(f"Failed to load inventory from DB: {e}")

    # ========== Property Inventory Operations ==========
    
    async def add_property_inventory(
        self,
        property_data: Dict[str, Any]
    ) -> PropertyInventoryItem:
        """Add new property to inventory"""
        try:
            item_id = str(ObjectId())
            
            item = PropertyInventoryItem(
                id=item_id,
                property_id=property_data.get("property_id", item_id),
                property_type=property_data.get("property_type", "apartment"),
                city=property_data.get("city", ""),
                locality=property_data.get("locality", ""),
                address=property_data.get("address", ""),
                bedrooms=property_data.get("bedrooms"),
                bathrooms=property_data.get("bathrooms"),
                area_sqft=property_data.get("area_sqft"),
                price=property_data.get("price"),
                status=PropertyStatus(property_data.get("status", "available")),
                available_from=property_data.get("available_from"),
                available_until=property_data.get("available_until")
            )
            
            self.property_inventory[item_id] = item
            
            # Save to database
            if self.database:
                await self.database.property_inventory.insert_one({
                    "_id": ObjectId(item_id),
                    **property_data,
                    "status": item.status.value,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at
                })
            
            logger.info(f"Property added to inventory: {item_id}")
            return item
            
        except Exception as e:
            logger.error(f"Failed to add property inventory: {e}")
            raise

    async def update_property_status(
        self,
        property_id: str,
        new_status: PropertyStatus,
        reason: Optional[str] = None,
        reserved_by: Optional[str] = None,
        reservation_duration_hours: Optional[int] = None
    ) -> PropertyInventoryItem:
        """Update property status"""
        try:
            # Find property
            item = None
            for p in self.property_inventory.values():
                if p.property_id == property_id:
                    item = p
                    break
            
            if not item:
                raise ValueError(f"Property not found: {property_id}")
            
            old_status = item.status
            item.status = new_status
            item.last_status_change = datetime.utcnow()
            item.status_reason = reason
            item.updated_at = datetime.utcnow()
            
            # Handle reservation
            if new_status == PropertyStatus.RESERVED and reserved_by:
                item.reserved_by = reserved_by
                item.reserved_until = datetime.utcnow() + timedelta(hours=reservation_duration_hours or 48)
            elif new_status != PropertyStatus.RESERVED:
                item.reserved_by = None
                item.reserved_until = None
            
            # Update database
            if self.database:
                await self.database.property_inventory.update_one(
                    {"property_id": property_id},
                    {
                        "$set": {
                            "status": new_status.value,
                            "status_reason": reason,
                            "reserved_by": item.reserved_by,
                            "reserved_until": item.reserved_until,
                            "last_status_change": item.last_status_change,
                            "updated_at": item.updated_at
                        }
                    }
                )
            
            logger.info(f"Property {property_id} status: {old_status.value} -> {new_status.value}")
            return item
            
        except Exception as e:
            logger.error(f"Failed to update property status: {e}")
            raise

    async def search_property_inventory(
        self,
        city: Optional[str] = None,
        locality: Optional[str] = None,
        property_type: Optional[str] = None,
        status: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_bedrooms: Optional[int] = None,
        available_only: bool = False
    ) -> List[PropertyInventoryItem]:
        """Search property inventory"""
        results = list(self.property_inventory.values())
        
        if city:
            results = [p for p in results if p.city.lower() == city.lower()]
        
        if locality:
            results = [p for p in results if locality.lower() in p.locality.lower()]
        
        if property_type:
            results = [p for p in results if p.property_type == property_type]
        
        if status:
            results = [p for p in results if p.status.value == status]
        
        if available_only:
            results = [p for p in results if p.status == PropertyStatus.AVAILABLE]
        
        if min_price:
            results = [p for p in results if p.price and p.price >= min_price]
        
        if max_price:
            results = [p for p in results if p.price and p.price <= max_price]
        
        if min_bedrooms:
            results = [p for p in results if p.bedrooms and p.bedrooms >= min_bedrooms]
        
        return sorted(results, key=lambda x: x.updated_at, reverse=True)

    # ========== Medicine Inventory Operations ==========
    
    async def add_medicine_inventory(
        self,
        medicine_data: Dict[str, Any]
    ) -> MedicineInventoryItem:
        """Add new medicine to inventory"""
        try:
            item_id = str(ObjectId())
            
            item = MedicineInventoryItem(
                id=item_id,
                medicine_id=medicine_data.get("medicine_id", item_id),
                name=medicine_data.get("name", ""),
                generic_name=medicine_data.get("generic_name"),
                brand=medicine_data.get("brand"),
                category=medicine_data.get("category", "general"),
                prescription_required=medicine_data.get("prescription_required", False),
                dosage_form=medicine_data.get("dosage_form", "tablet"),
                strength=medicine_data.get("strength"),
                batch_number=medicine_data.get("batch_number", ""),
                quantity=medicine_data.get("quantity", 0),
                unit=medicine_data.get("unit", "pieces"),
                mrp=medicine_data.get("mrp", 0.0),
                cost_price=medicine_data.get("cost_price", 0.0),
                selling_price=medicine_data.get("selling_price", 0.0),
                gst_percentage=medicine_data.get("gst_percentage", 12.0),
                manufacturing_date=medicine_data.get("manufacturing_date"),
                expiry_date=medicine_data.get("expiry_date"),
                reorder_level=medicine_data.get("reorder_level", 10),
                max_stock_level=medicine_data.get("max_stock_level", 1000),
                storage_location=medicine_data.get("storage_location", "default"),
                supplier_id=medicine_data.get("supplier_id")
            )
            
            # Check expiry
            if item.is_expired:
                item.status = MedicineStatus.EXPIRED
            elif item.quantity <= 0:
                item.status = MedicineStatus.OUT_OF_STOCK
            elif item.quantity <= item.reorder_level:
                item.status = MedicineStatus.LOW_STOCK
            else:
                item.status = MedicineStatus.IN_STOCK
            
            self.medicine_inventory[item_id] = item
            
            # Record stock movement
            await self.record_stock_movement(
                inventory_type=InventoryType.MEDICINE,
                item_id=item_id,
                movement_type=StockMovementType.INWARD,
                quantity=item.quantity,
                previous_quantity=0,
                reference_type="initial_stock",
                notes=f"Initial stock: {medicine_data.get('name')}"
            )
            
            # Save to database
            if self.database:
                await self.database.medicine_inventory.insert_one({
                    "_id": ObjectId(item_id),
                    **medicine_data,
                    "status": item.status.value,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at
                })
            
            logger.info(f"Medicine added to inventory: {item.name} ({item.quantity} units)")
            return item
            
        except Exception as e:
            logger.error(f"Failed to add medicine inventory: {e}")
            raise

    async def update_medicine_stock(
        self,
        medicine_id: str,
        quantity_change: int,
        movement_type: StockMovementType,
        reference_id: Optional[str] = None,
        reference_type: Optional[str] = None,
        notes: Optional[str] = None,
        performed_by: Optional[str] = None
    ) -> MedicineInventoryItem:
        """Update medicine stock quantity"""
        try:
            # Find medicine
            item = None
            for m in self.medicine_inventory.values():
                if m.medicine_id == medicine_id:
                    item = m
                    break
            
            if not item:
                raise ValueError(f"Medicine not found: {medicine_id}")
            
            previous_quantity = item.quantity
            new_quantity = previous_quantity + quantity_change
            
            if new_quantity < 0:
                raise ValueError(f"Insufficient stock. Available: {previous_quantity}")
            
            # Update quantity
            item.quantity = new_quantity
            item.updated_at = datetime.utcnow()
            
            # Update status based on quantity
            if item.is_expired:
                item.status = MedicineStatus.EXPIRED
            elif item.quantity <= 0:
                item.status = MedicineStatus.OUT_OF_STOCK
            elif item.quantity <= item.reorder_level:
                item.status = MedicineStatus.LOW_STOCK
            else:
                item.status = MedicineStatus.IN_STOCK
            
            # Record movement
            await self.record_stock_movement(
                inventory_type=InventoryType.MEDICINE,
                item_id=item.id,
                movement_type=movement_type,
                quantity=quantity_change,
                previous_quantity=previous_quantity,
                new_quantity=new_quantity,
                reference_id=reference_id,
                reference_type=reference_type,
                notes=notes,
                performed_by=performed_by
            )
            
            # Update database
            if self.database:
                await self.database.medicine_inventory.update_one(
                    {"medicine_id": medicine_id},
                    {
                        "$set": {
                            "quantity": new_quantity,
                            "status": item.status.value,
                            "updated_at": item.updated_at
                        }
                    }
                )
            
            logger.info(f"Medicine stock updated: {item.name} ({previous_quantity} -> {new_quantity})")
            return item
            
        except Exception as e:
            logger.error(f"Failed to update medicine stock: {e}")
            raise

    async def sell_medicine(
        self,
        medicine_id: str,
        quantity: int,
        sale_id: str,
        performed_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process medicine sale"""
        try:
            item = await self.update_medicine_stock(
                medicine_id=medicine_id,
                quantity_change=-quantity,
                movement_type=StockMovementType.OUTWARD,
                reference_id=sale_id,
                reference_type="sale",
                notes=f"Sold {quantity} units",
                performed_by=performed_by
            )
            
            # Calculate sale value
            sale_value = quantity * item.selling_price
            gst_amount = sale_value * (item.gst_percentage / 100)
            total_amount = sale_value + gst_amount
            
            return {
                "medicine_id": medicine_id,
                "medicine_name": item.name,
                "quantity_sold": quantity,
                "unit_price": item.selling_price,
                "sale_value": sale_value,
                "gst_amount": gst_amount,
                "total_amount": total_amount,
                "remaining_stock": item.quantity,
                "sale_id": sale_id
            }
            
        except Exception as e:
            logger.error(f"Failed to sell medicine: {e}")
            raise

    async def search_medicine_inventory(
        self,
        name: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        prescription_required: Optional[bool] = None,
        in_stock_only: bool = False,
        expiring_within_days: Optional[int] = None
    ) -> List[MedicineInventoryItem]:
        """Search medicine inventory"""
        results = list(self.medicine_inventory.values())
        
        if name:
            name_lower = name.lower()
            results = [
                m for m in results
                if name_lower in m.name.lower() or 
                (m.generic_name and name_lower in m.generic_name.lower())
            ]
        
        if category:
            results = [m for m in results if m.category == category]
        
        if status:
            results = [m for m in results if m.status.value == status]
        
        if prescription_required is not None:
            results = [m for m in results if m.prescription_required == prescription_required]
        
        if in_stock_only:
            results = [m for m in results if m.quantity > 0]
        
        if expiring_within_days:
            from datetime import timedelta
            cutoff_date = date.today() + timedelta(days=expiring_within_days)
            results = [
                m for m in results
                if m.expiry_date and m.expiry_date <= cutoff_date and not m.is_expired
            ]
        
        return sorted(results, key=lambda x: x.updated_at, reverse=True)

    # ========== Stock Movement Tracking ==========
    
    async def record_stock_movement(
        self,
        inventory_type: InventoryType,
        item_id: str,
        movement_type: StockMovementType,
        quantity: int,
        previous_quantity: int,
        new_quantity: Optional[int] = None,
        reference_id: Optional[str] = None,
        reference_type: Optional[str] = None,
        notes: Optional[str] = None,
        performed_by: Optional[str] = None
    ) -> StockMovement:
        """Record stock movement"""
        try:
            movement_id = str(ObjectId())
            
            if new_quantity is None:
                new_quantity = previous_quantity + quantity
            
            movement = StockMovement(
                id=movement_id,
                inventory_type=inventory_type,
                item_id=item_id,
                movement_type=movement_type,
                quantity=quantity,
                previous_quantity=previous_quantity,
                new_quantity=new_quantity,
                reference_id=reference_id,
                reference_type=reference_type,
                notes=notes,
                performed_by=performed_by
            )
            
            self.stock_movements.append(movement)
            
            # Save to database
            if self.database:
                await self.database.stock_movements.insert_one({
                    "_id": ObjectId(movement_id),
                    "inventory_type": inventory_type.value,
                    "item_id": item_id,
                    "movement_type": movement_type.value,
                    "quantity": quantity,
                    "previous_quantity": previous_quantity,
                    "new_quantity": new_quantity,
                    "reference_id": reference_id,
                    "reference_type": reference_type,
                    "notes": notes,
                    "performed_by": performed_by,
                    "created_at": movement.created_at
                })
            
            return movement
            
        except Exception as e:
            logger.error(f"Failed to record stock movement: {e}")
            raise

    async def get_stock_movement_history(
        self,
        inventory_type: Optional[InventoryType] = None,
        item_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[StockMovement]:
        """Get stock movement history"""
        movements = self.stock_movements
        
        if inventory_type:
            movements = [m for m in movements if m.inventory_type == inventory_type]
        
        if item_id:
            movements = [m for m in movements if m.item_id == item_id]
        
        if start_date:
            movements = [m for m in movements if m.created_at >= start_date]
        
        if end_date:
            movements = [m for m in movements if m.created_at <= end_date]
        
        return sorted(movements, key=lambda x: x.created_at, reverse=True)[:limit]

    # ========== Alerts & Monitoring ==========
    
    async def create_alert(
        self,
        inventory_type: InventoryType,
        item_id: str,
        alert_type: str,
        severity: str,
        message: str
    ) -> InventoryAlert:
        """Create inventory alert"""
        try:
            alert_id = str(ObjectId())
            
            alert = InventoryAlert(
                id=alert_id,
                inventory_type=inventory_type,
                item_id=item_id,
                alert_type=alert_type,
                severity=severity,
                message=message
            )
            
            self.alerts[alert_id] = alert
            
            # Save to database
            if self.database:
                await self.database.inventory_alerts.insert_one({
                    "_id": ObjectId(alert_id),
                    "inventory_type": inventory_type.value,
                    "item_id": item_id,
                    "alert_type": alert_type,
                    "severity": severity,
                    "message": message,
                    "is_resolved": False,
                    "created_at": alert.created_at
                })
            
            logger.warning(f"Inventory alert created: {alert_type} - {message}")
            return alert
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            raise

    async def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str
    ) -> InventoryAlert:
        """Resolve inventory alert"""
        try:
            alert = self.alerts.get(alert_id)
            if not alert:
                raise ValueError(f"Alert not found: {alert_id}")
            
            alert.is_resolved = True
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = resolved_by
            
            # Update database
            if self.database:
                await self.database.inventory_alerts.update_one(
                    {"_id": ObjectId(alert_id)},
                    {
                        "$set": {
                            "is_resolved": True,
                            "resolved_at": alert.resolved_at,
                            "resolved_by": resolved_by
                        }
                    }
                )
            
            logger.info(f"Alert resolved: {alert_id}")
            return alert
            
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            raise

    async def get_alerts(
        self,
        inventory_type: Optional[InventoryType] = None,
        severity: Optional[str] = None,
        is_resolved: Optional[bool] = False,
        limit: int = 50
    ) -> List[InventoryAlert]:
        """Get inventory alerts"""
        alerts = list(self.alerts.values())
        
        if inventory_type:
            alerts = [a for a in alerts if a.inventory_type == inventory_type]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if is_resolved is not None:
            alerts = [a for a in alerts if a.is_resolved == is_resolved]
        
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)[:limit]

    # ========== Background Tasks ==========
    
    async def _background_inventory_check(self):
        """Background task to check inventory periodically"""
        while True:
            try:
                await asyncio.sleep(self.auto_check_interval)
                
                # Check medicine expiry
                await self._check_medicine_expiry()
                
                # Check low stock
                await self._check_low_stock()
                
                # Check expired reservations
                await self._check_expired_property_reservations()
                
            except Exception as e:
                logger.error(f"Background inventory check failed: {e}")

    async def _check_medicine_expiry(self):
        """Check for expiring/expired medicines"""
        today = date.today()
        warning_date = today + timedelta(days=self.expiry_warning_days)
        
        for item in self.medicine_inventory.values():
            if not item.expiry_date:
                continue
            
            # Check expired
            if item.expiry_date < today and item.status != MedicineStatus.EXPIRED:
                item.status = MedicineStatus.EXPIRED
                await self.create_alert(
                    InventoryType.MEDICINE,
                    item.id,
                    "expired",
                    "critical",
                    f"Medicine {item.name} (Batch: {item.batch_number}) has expired on {item.expiry_date}"
                )
            
            # Check expiring soon
            elif today <= item.expiry_date <= warning_date:
                days_left = (item.expiry_date - today).days
                await self.create_alert(
                    InventoryType.MEDICINE,
                    item.id,
                    "expiring_soon",
                    "high" if days_left <= 7 else "medium",
                    f"Medicine {item.name} (Batch: {item.batch_number}) expires in {days_left} days"
                )

    async def _check_low_stock(self):
        """Check for low stock medicines"""
        for item in self.medicine_inventory.values():
            if item.quantity <= item.reorder_level and item.quantity > 0:
                if item.status != MedicineStatus.LOW_STOCK:
                    item.status = MedicineStatus.LOW_STOCK
                    await self.create_alert(
                        InventoryType.MEDICINE,
                        item.id,
                        "low_stock",
                        "high" if item.quantity <= item.reorder_level / 2 else "medium",
                        f"Low stock alert: {item.name} - Only {item.quantity} units remaining (Reorder level: {item.reorder_level})"
                    )
            
            # Check overstock
            elif item.quantity > item.max_stock_level:
                await self.create_alert(
                    InventoryType.MEDICINE,
                    item.id,
                    "overstock",
                    "low",
                    f"Overstock warning: {item.name} - {item.quantity} units (Max: {item.max_stock_level})"
                )

    async def _check_expired_property_reservations(self):
        """Check and release expired property reservations"""
        now = datetime.utcnow()
        
        for item in self.property_inventory.values():
            if (
                item.status == PropertyStatus.RESERVED and
                item.reserved_until and
                item.reserved_until < now
            ):
                # Release reservation
                await self.update_property_status(
                    item.property_id,
                    PropertyStatus.AVAILABLE,
                    reason="Reservation expired"
                )
                
                await self.create_alert(
                    InventoryType.PROPERTY,
                    item.id,
                    "reservation_expired",
                    "low",
                    f"Property reservation expired: {item.property_id}"
                )

    # ========== Dashboard & Reports ==========
    
    async def get_inventory_dashboard(self) -> Dict[str, Any]:
        """Get inventory dashboard summary"""
        # Property stats
        property_stats = {
            "total": len(self.property_inventory),
            "available": len([p for p in self.property_inventory.values() if p.status == PropertyStatus.AVAILABLE]),
            "reserved": len([p for p in self.property_inventory.values() if p.status == PropertyStatus.RESERVED]),
            "sold": len([p for p in self.property_inventory.values() if p.status == PropertyStatus.SOLD]),
            "rented": len([p for p in self.property_inventory.values() if p.status == PropertyStatus.RENTED]),
            "under_maintenance": len([p for p in self.property_inventory.values() if p.status == PropertyStatus.UNDER_MAINTENANCE])
        }
        
        # Medicine stats
        medicine_stats = {
            "total": len(self.medicine_inventory),
            "in_stock": len([m for m in self.medicine_inventory.values() if m.status == MedicineStatus.IN_STOCK]),
            "low_stock": len([m for m in self.medicine_inventory.values() if m.status == MedicineStatus.LOW_STOCK]),
            "out_of_stock": len([m for m in self.medicine_inventory.values() if m.status == MedicineStatus.OUT_OF_STOCK]),
            "expired": len([m for m in self.medicine_inventory.values() if m.status == MedicineStatus.EXPIRED]),
            "total_value": sum(m.quantity * m.cost_price for m in self.medicine_inventory.values())
        }
        
        # Active alerts
        active_alerts = len([a for a in self.alerts.values() if not a.is_resolved])
        
        return {
            "property": property_stats,
            "medicine": medicine_stats,
            "alerts": {
                "active": active_alerts,
                "critical": len([a for a in self.alerts.values() if not a.is_resolved and a.severity == "critical"]),
                "high": len([a for a in self.alerts.values() if not a.is_resolved and a.severity == "high"])
            },
            "last_updated": datetime.utcnow().isoformat()
        }

    async def get_medicine_valuation(self) -> Dict[str, Any]:
        """Get medicine inventory valuation"""
        total_cost = 0
        total_mrp = 0
        category_breakdown = {}
        
        for item in self.medicine_inventory.values():
            item_cost = item.quantity * item.cost_price
            item_mrp = item.quantity * item.mrp
            
            total_cost += item_cost
            total_mrp += item_mrp
            
            # Category breakdown
            if item.category not in category_breakdown:
                category_breakdown[item.category] = {
                    "count": 0,
                    "quantity": 0,
                    "cost_value": 0,
                    "mrp_value": 0
                }
            
            category_breakdown[item.category]["count"] += 1
            category_breakdown[item.category]["quantity"] += item.quantity
            category_breakdown[item.category]["cost_value"] += item_cost
            category_breakdown[item.category]["mrp_value"] += item_mrp
        
        return {
            "total_items": len(self.medicine_inventory),
            "total_quantity": sum(m.quantity for m in self.medicine_inventory.values()),
            "total_cost_value": round(total_cost, 2),
            "total_mrp_value": round(total_mrp, 2),
            "potential_profit": round(total_mrp - total_cost, 2),
            "profit_margin_percent": round(((total_mrp - total_cost) / total_cost * 100) if total_cost > 0 else 0, 2),
            "by_category": category_breakdown
        }


# Global instance
inventory_service = InventoryManagementService()
