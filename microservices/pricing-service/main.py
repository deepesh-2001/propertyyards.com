"""
Pricing Service Microservice
Manages dynamic pricing for properties, subscriptions, and services
Provides admin controls for price updates with real-time propagation
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import redis.asyncio as redis
from bson import ObjectId
import motor.motor_asyncio

app = FastAPI(title="Pricing Service", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB
mongo_client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = mongo_client.pricing_db

# Redis
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)


class PricingType(str, Enum):
    PROPERTY = "property"
    SUBSCRIPTION = "subscription"
    COMMISSION = "commission"
    SERVICE_FEE = "service_fee"
    REFERRAL_BONUS = "referral_bonus"


class PricingTier(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class PricingRule(BaseModel):
    id: Optional[str] = None
    name: str
    type: PricingType
    tier: Optional[PricingTier] = None
    base_price: float = Field(..., ge=0)
    currency: str = "USD"
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    discount_percent: float = Field(0, ge=0, le=100)
    dynamic_multiplier: float = Field(1.0, ge=0)
    valid_from: datetime
    valid_until: Optional[datetime] = None
    is_active: bool = True
    conditions: Dict[str, Any] = {}  # e.g., {"location": "Mumbai", "property_type": "apartment"}
    metadata: Dict[str, Any] = {}
    created_by: str
    updated_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    version: int = 1

    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class PriceCalculationRequest(BaseModel):
    type: PricingType
    base_value: float
    tier: Optional[PricingTier] = None
    location: Optional[str] = None
    property_type: Optional[str] = None
    user_type: Optional[str] = None
    conditions: Dict[str, Any] = {}


class PriceCalculationResponse(BaseModel):
    base_price: float
    adjustments: List[Dict[str, Any]]
    final_price: float
    currency: str
    applied_rules: List[str]
    valid_until: Optional[datetime]


class PriceHistoryEntry(BaseModel):
    price: float
    timestamp: datetime
    reason: str
    changed_by: str


# In-memory cache for hot pricing data
pricing_cache: Dict[str, Any] = {}


@app.on_event("startup")
async def startup():
    """Initialize service"""
    # Create indexes
    await db.pricing_rules.create_index("type")
    await db.pricing_rules.create_index("is_active")
    await db.pricing_rules.create_index("valid_from")
    await db.pricing_rules.create_index("valid_until")
    
    # Load active pricing into cache
    await refresh_pricing_cache()
    
    # Start background tasks
    asyncio.create_task(cache_refresh_loop())
    
    print("✅ Pricing Service started")


async def refresh_pricing_cache():
    """Refresh pricing cache from database"""
    global pricing_cache
    
    cursor = db.pricing_rules.find({"is_active": True})
    rules = await cursor.to_list(length=1000)
    
    pricing_cache = {}
    for rule in rules:
        key = f"{rule['type']}:{rule.get('tier', 'default')}"
        pricing_cache[key] = rule
    
    # Also cache in Redis for distributed access
    await redis_client.setex(
        "pricing:active_rules",
        300,  # 5 minutes
        json.dumps(rules, default=str)
    )


async def cache_refresh_loop():
    """Periodically refresh cache"""
    while True:
        await asyncio.sleep(60)  # Refresh every minute
        await refresh_pricing_cache()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "pricing", "cache_size": len(pricing_cache)}


@app.post("/rules", response_model=PricingRule)
async def create_pricing_rule(
    rule: PricingRule,
    background_tasks: BackgroundTasks
):
    """Create new pricing rule (Admin only)"""
    rule_dict = rule.dict(exclude={'id'})
    rule_dict["created_at"] = datetime.utcnow()
    rule_dict["version"] = 1
    
    result = await db.pricing_rules.insert_one(rule_dict)
    rule_dict["id"] = str(result.inserted_id)
    
    # Refresh cache
    background_tasks.add_task(refresh_pricing_cache)
    
    # Notify other services
    background_tasks.add_task(notify_price_change, rule_dict)
    
    return PricingRule(**rule_dict)


@app.put("/rules/{rule_id}", response_model=PricingRule)
async def update_pricing_rule(
    rule_id: str,
    rule_update: PricingRule,
    background_tasks: BackgroundTasks
):
    """Update pricing rule (Admin only)"""
    # Get existing rule for history
    existing = await db.pricing_rules.find_one({"_id": ObjectId(rule_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # Update fields
    update_data = rule_update.dict(exclude={'id', 'created_at', 'version'}, exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    update_data["version"] = existing.get("version", 1) + 1
    
    # Add to price history
    history_entry = {
        "price": existing.get("base_price"),
        "timestamp": datetime.utcnow(),
        "reason": f"Updated to {rule_update.base_price}",
        "changed_by": rule_update.updated_by or rule_update.created_by
    }
    
    await db.pricing_rules.update_one(
        {"_id": ObjectId(rule_id)},
        {
            "$set": update_data,
            "$push": {"price_history": history_entry}
        }
    )
    
    # Get updated rule
    updated = await db.pricing_rules.find_one({"_id": ObjectId(rule_id)})
    updated["id"] = str(updated.pop("_id"))
    
    # Refresh cache and notify
    background_tasks.add_task(refresh_pricing_cache)
    background_tasks.add_task(notify_price_change, updated)
    
    return PricingRule(**updated)


@app.delete("/rules/{rule_id}")
async def delete_pricing_rule(
    rule_id: str,
    background_tasks: BackgroundTasks
):
    """Delete pricing rule (Admin only)"""
    result = await db.pricing_rules.update_one(
        {"_id": ObjectId(rule_id)},
        {"$set": {"is_active": False, "deleted_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    background_tasks.add_task(refresh_pricing_cache)
    
    return {"message": "Pricing rule deactivated"}


@app.get("/rules", response_model=List[PricingRule])
async def list_pricing_rules(
    type: Optional[PricingType] = None,
    tier: Optional[PricingTier] = None,
    is_active: Optional[bool] = True
):
    """List all pricing rules with optional filtering"""
    query = {}
    if type:
        query["type"] = type
    if tier:
        query["tier"] = tier
    if is_active is not None:
        query["is_active"] = is_active
    
    cursor = db.pricing_rules.find(query).sort("created_at", -1)
    rules = await cursor.to_list(length=100)
    
    for rule in rules:
        rule["id"] = str(rule.pop("_id"))
    
    return [PricingRule(**rule) for rule in rules]


@app.get("/rules/{rule_id}", response_model=PricingRule)
async def get_pricing_rule(rule_id: str):
    """Get specific pricing rule"""
    rule = await db.pricing_rules.find_one({"_id": ObjectId(rule_id)})
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rule["id"] = str(rule.pop("_id"))
    return PricingRule(**rule)


@app.post("/calculate", response_model=PriceCalculationResponse)
async def calculate_price(request: PriceCalculationRequest):
    """Calculate price based on rules and conditions"""
    
    # Find applicable rules
    query = {
        "type": request.type,
        "is_active": True,
        "valid_from": {"$lte": datetime.utcnow()},
        "$or": [
            {"valid_until": None},
            {"valid_until": {"$gte": datetime.utcnow()}}
        ]
    }
    
    if request.tier:
        query["tier"] = request.tier
    
    # Get rules from cache or database
    rules = []
    cache_key = f"{request.type}:{request.tier or 'default'}"
    
    if cache_key in pricing_cache:
        rules = [pricing_cache[cache_key]]
    else:
        cursor = db.pricing_rules.find(query)
        rules = await cursor.to_list(length=10)
    
    if not rules:
        # Return default pricing
        return PriceCalculationResponse(
            base_price=request.base_value,
            adjustments=[],
            final_price=request.base_value,
            currency="USD",
            applied_rules=[],
            valid_until=None
        )
    
    # Apply best matching rule
    best_rule = rules[0]  # Simplified - could use more complex matching
    
    base_price = best_rule.get("base_price", request.base_value)
    adjustments = []
    
    # Apply dynamic multiplier
    multiplier = best_rule.get("dynamic_multiplier", 1.0)
    if multiplier != 1.0:
        adjustments.append({
            "type": "dynamic_multiplier",
            "value": multiplier,
            "amount": base_price * (multiplier - 1)
        })
    
    # Apply discount
    discount = best_rule.get("discount_percent", 0)
    if discount > 0:
        adjustments.append({
            "type": "discount",
            "value": discount,
            "amount": -(base_price * multiplier * discount / 100)
        })
    
    # Calculate final price
    final_price = base_price * multiplier * (1 - discount / 100)
    
    # Apply min/max constraints
    min_price = best_rule.get("min_price")
    max_price = best_rule.get("max_price")
    
    if min_price and final_price < min_price:
        final_price = min_price
        adjustments.append({
            "type": "min_price_floor",
            "value": min_price,
            "amount": min_price - final_price
        })
    
    if max_price and final_price > max_price:
        final_price = max_price
        adjustments.append({
            "type": "max_price_cap",
            "value": max_price,
            "amount": max_price - final_price
        })
    
    return PriceCalculationResponse(
        base_price=base_price,
        adjustments=adjustments,
        final_price=round(final_price, 2),
        currency=best_rule.get("currency", "USD"),
        applied_rules=[str(best_rule.get("_id"))],
        valid_until=best_rule.get("valid_until")
    )


@app.get("/current/{pricing_type}")
async def get_current_pricing(pricing_type: PricingType):
    """Get current active pricing for a type"""
    query = {
        "type": pricing_type,
        "is_active": True,
        "valid_from": {"$lte": datetime.utcnow()},
        "$or": [
            {"valid_until": None},
            {"valid_until": {"$gte": datetime.utcnow()}}
        ]
    }
    
    cursor = db.pricing_rules.find(query)
    rules = await cursor.to_list(length=100)
    
    for rule in rules:
        rule["id"] = str(rule.pop("_id"))
    
    return {
        "type": pricing_type,
        "rules": rules,
        "count": len(rules),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/bulk-update")
async def bulk_update_prices(
    updates: List[Dict[str, Any]],
    changed_by: str,
    background_tasks: BackgroundTasks
):
    """Bulk update multiple pricing rules (Admin only)"""
    results = []
    
    for update in updates:
        rule_id = update.get("id")
        if not rule_id:
            continue
        
        update_data = {
            k: v for k, v in update.items()
            if k not in ["id", "created_at", "version"]
        }
        update_data["updated_at"] = datetime.utcnow()
        update_data["updated_by"] = changed_by
        
        result = await db.pricing_rules.update_one(
            {"_id": ObjectId(rule_id)},
            {
                "$set": update_data,
                "$inc": {"version": 1}
            }
        )
        
        results.append({
            "id": rule_id,
            "matched": result.matched_count,
            "modified": result.modified_count
        })
    
    background_tasks.add_task(refresh_pricing_cache)
    background_tasks.add_task(notify_bulk_price_change, updates, changed_by)
    
    return {
        "message": "Bulk update completed",
        "results": results,
        "total": len(updates),
        "successful": sum(1 for r in results if r["modified"] > 0)
    }


@app.get("/history/{rule_id}")
async def get_price_history(rule_id: str):
    """Get price change history for a rule"""
    rule = await db.pricing_rules.find_one(
        {"_id": ObjectId(rule_id)},
        {"price_history": 1, "name": 1}
    )
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    history = rule.get("price_history", [])
    
    return {
        "rule_id": rule_id,
        "rule_name": rule.get("name"),
        "history": history,
        "count": len(history)
    }


async def notify_price_change(rule: Dict):
    """Notify other services of price change"""
    message = {
        "event": "price_change",
        "rule_id": str(rule.get("_id")),
        "type": rule.get("type"),
        "base_price": rule.get("base_price"),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await redis_client.publish("pricing:changes", json.dumps(message))


async def notify_bulk_price_change(updates: List[Dict], changed_by: str):
    """Notify of bulk price changes"""
    message = {
        "event": "bulk_price_change",
        "count": len(updates),
        "changed_by": changed_by,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await redis_client.publish("pricing:bulk_changes", json.dumps(message))


@app.get("/subscription-plans")
async def get_subscription_plans():
    """Get current subscription pricing plans"""
    plans = await db.pricing_rules.find({
        "type": PricingType.SUBSCRIPTION,
        "is_active": True
    }).to_list(length=10)
    
    return {
        "plans": [
            {
                "id": str(p.get("_id")),
                "name": p.get("name"),
                "tier": p.get("tier"),
                "price": p.get("base_price"),
                "currency": p.get("currency", "USD"),
                "discount": p.get("discount_percent", 0),
                "features": p.get("metadata", {}).get("features", [])
            }
            for p in plans
        ]
    }


@app.get("/commission-rates")
async def get_commission_rates():
    """Get current commission rates for referrals"""
    rates = await db.pricing_rules.find({
        "type": PricingType.COMMISSION,
        "is_active": True
    }).to_list(length=10)
    
    return {
        "rates": [
            {
                "id": str(r.get("_id")),
                "name": r.get("name"),
                "percentage": r.get("base_price"),  # Stored as percentage
                "min_amount": r.get("conditions", {}).get("min_amount"),
                "max_amount": r.get("conditions", {}).get("max_amount")
            }
            for r in rates
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
