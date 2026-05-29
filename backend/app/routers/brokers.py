"""
Broker Router
Endpoints for broker management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from app.database import get_database
from app.schemas import BrokerCreate, BrokerUpdate, BrokerResponse, PaginatedResponse
from app.auth import decode_token
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/brokers", tags=["Brokers"])


def get_current_user(authorization: str = Header(None)) -> dict:
    """Extract current user from authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token = authorization.split(" ")[1]
        token_data = decode_token(token)
        if token_data:
            return {"user_id": token_data.user_id, "email": token_data.email, "role": token_data.role}
    except Exception:
        pass

    raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/", response_model=BrokerResponse)
async def create_broker(
    broker_data: BrokerCreate,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Create a new broker profile"""
    current_user = get_current_user(authorization)
    
    # Check if broker profile already exists for user
    existing = await db.brokers.find_one({"user_id": current_user["user_id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Broker profile already exists for this user")
    
    broker_dict = broker_data.dict()
    broker_dict["user_id"] = current_user["user_id"]
    broker_dict["rating"] = 0.0
    broker_dict["total_deals"] = 0
    broker_dict["is_verified"] = False
    broker_dict["is_active"] = True
    
    result = await db.brokers.insert_one(broker_dict)
    broker_dict["id"] = str(result.inserted_id)
    
    logger.info(f"Broker profile created: {result.inserted_id}")
    return BrokerResponse(**broker_dict)


@router.get("/{broker_id}", response_model=BrokerResponse)
async def get_broker(
    broker_id: str,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Get broker by ID"""
    current_user = get_current_user(authorization)
    
    broker = await db.brokers.find_one({"_id": broker_id})
    if not broker:
        raise HTTPException(status_code=404, detail="Broker not found")
    
    broker["id"] = str(broker["_id"])
    del broker["_id"]
    
    return BrokerResponse(**broker)


@router.get("/user/{user_id}", response_model=BrokerResponse)
async def get_broker_by_user(
    user_id: str,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Get broker profile by user ID"""
    current_user = get_current_user(authorization)
    
    broker = await db.brokers.find_one({"user_id": user_id})
    if not broker:
        raise HTTPException(status_code=404, detail="Broker profile not found")
    
    broker["id"] = str(broker["_id"])
    del broker["_id"]
    
    return BrokerResponse(**broker)


@router.put("/{broker_id}", response_model=BrokerResponse)
async def update_broker(
    broker_id: str,
    broker_update: BrokerUpdate,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Update broker profile"""
    current_user = get_current_user(authorization)
    
    broker = await db.brokers.find_one({"_id": broker_id})
    if not broker:
        raise HTTPException(status_code=404, detail="Broker not found")
    
    # Check if user owns this broker profile or is admin
    if broker["user_id"] != current_user["user_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this broker profile")
    
    update_data = broker_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.brokers.update_one({"_id": broker_id}, {"$set": update_data})
    
    updated_broker = await db.brokers.find_one({"_id": broker_id})
    updated_broker["id"] = str(updated_broker["_id"])
    del updated_broker["_id"]
    
    return BrokerResponse(**updated_broker)


@router.delete("/{broker_id}")
async def delete_broker(
    broker_id: str,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Delete broker profile"""
    current_user = get_current_user(authorization)
    
    broker = await db.brokers.find_one({"_id": broker_id})
    if not broker:
        raise HTTPException(status_code=404, detail="Broker not found")
    
    # Check if user owns this broker profile or is admin
    if broker["user_id"] != current_user["user_id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this broker profile")
    
    await db.brokers.delete_one({"_id": broker_id})
    
    return {"message": "Broker profile deleted successfully"}


@router.get("/", response_model=PaginatedResponse)
async def list_brokers(
    specialization: str = None,
    agency_name: str = None,
    is_verified: bool = None,
    is_active: bool = None,
    page: int = 1,
    limit: int = 50,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """List brokers with filters"""
    current_user = get_current_user(authorization)
    
    query_filter = {}
    if specialization:
        query_filter["specialization"] = specialization
    if agency_name:
        query_filter["agency_name"] = {"$regex": agency_name, "$options": "i"}
    if is_verified is not None:
        query_filter["is_verified"] = is_verified
    if is_active is not None:
        query_filter["is_active"] = is_active
    
    total = await db.brokers.count_documents(query_filter)
    skip = (page - 1) * limit
    
    cursor = db.brokers.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
    brokers = await cursor.to_list(length=limit)
    
    for broker in brokers:
        broker["id"] = str(broker["_id"])
        del broker["_id"]
    
    return {
        "items": brokers,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.put("/{broker_id}/verify")
async def verify_broker(
    broker_id: str,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Verify broker (admin only)"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    broker = await db.brokers.find_one({"_id": broker_id})
    if not broker:
        raise HTTPException(status_code=404, detail="Broker not found")
    
    await db.brokers.update_one(
        {"_id": broker_id},
        {"$set": {"is_verified": True, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Broker verified successfully"}


@router.put("/{broker_id}/rating")
async def update_broker_rating(
    broker_id: str,
    rating: float,
    authorization: str = Header(None),
    db = Depends(get_database)
):
    """Update broker rating"""
    current_user = get_current_user(authorization)
    
    if not (0 <= rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 0 and 5")
    
    broker = await db.brokers.find_one({"_id": broker_id})
    if not broker:
        raise HTTPException(status_code=404, detail="Broker not found")
    
    # Calculate new average rating
    current_rating = broker.get("rating", 0.0)
    total_deals = broker.get("total_deals", 0)
    
    new_total_deals = total_deals + 1
    new_rating = ((current_rating * total_deals) + rating) / new_total_deals
    
    await db.brokers.update_one(
        {"_id": broker_id},
        {
            "$set": {
                "rating": round(new_rating, 2),
                "total_deals": new_total_deals,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Broker rating updated successfully"}
