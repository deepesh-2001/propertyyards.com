"""
Commission Router
Handles commission rules, calculations, and payouts
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.schemas import (
    CommissionRuleCreate,
    CommissionRuleResponse,
    CommissionCreate,
    CommissionResponse,
    CommissionPayoutCreate,
    CommissionPayoutResponse,
    CommissionAnalytics,
    CommissionType,
    CommissionStatus,
    PaymentGateway
)
from app.commission import commission_processor
from app.auth import get_current_user

router = APIRouter(prefix="/api/commissions", tags=["commissions"])


# ========== Commission Rules Endpoints ==========

@router.post("/rules", response_model=CommissionRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_commission_rule(
    rule: CommissionRuleCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new commission rule"""
    try:
        rule_data = rule.dict()
        rule_data.update({
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        result = await database.commission_rules.insert_one(rule_data)
        rule_data["id"] = str(result.inserted_id)
        
        return CommissionRuleResponse(**rule_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}", response_model=CommissionRuleResponse)
async def get_commission_rule(
    rule_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific commission rule"""
    rule = await database.commission_rules.find_one({"_id": rule_id})
    if not rule:
        raise HTTPException(status_code=404, detail="Commission rule not found")
    
    rule["id"] = str(rule["_id"])
    del rule["_id"]
    
    return CommissionRuleResponse(**rule)


@router.get("/rules", response_model=List[CommissionRuleResponse])
async def get_commission_rules(
    commission_type: Optional[CommissionType] = None,
    is_active: Optional[bool] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all commission rules"""
    query = {}
    if commission_type:
        query["commission_type"] = commission_type
    if is_active is not None:
        query["is_active"] = is_active
    
    cursor = database.commission_rules.find(query).sort("created_at", -1)
    rules = await cursor.to_list(length=100)
    
    for rule in rules:
        rule["id"] = str(rule["_id"])
        del rule["_id"]
    
    return [CommissionRuleResponse(**r) for r in rules]


# ========== Commission Endpoints ==========

@router.post("/calculate")
async def calculate_commission(
    deal_id: str,
    deal_type: str,
    deal_amount: float,
    recipient_id: str,
    recipient_type: str,
    commission_rule_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Calculate commission for a deal"""
    try:
        commission = await commission_processor.calculate_deal_commission(
            deal_id=deal_id,
            deal_type=deal_type,
            deal_amount=deal_amount,
            recipient_id=recipient_id,
            recipient_type=recipient_type,
            commission_rule_id=commission_rule_id,
            database=database
        )
        return commission
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commissions/{commission_id}", response_model=CommissionResponse)
async def get_commission(
    commission_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific commission"""
    commission = await database.commissions.find_one({"_id": commission_id})
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")
    
    commission["id"] = str(commission["_id"])
    del commission["_id"]
    
    return CommissionResponse(**commission)


@router.get("/recipients/{recipient_id}/commissions", response_model=List[CommissionResponse])
async def get_recipient_commissions(
    recipient_id: str,
    status: Optional[CommissionStatus] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all commissions for a recipient"""
    query = {"recipient_id": recipient_id}
    if status:
        query["status"] = status
    
    cursor = database.commissions.find(query).sort("created_at", -1)
    commissions = await cursor.to_list(length=100)
    
    for commission in commissions:
        commission["id"] = str(commission["_id"])
        del commission["_id"]
    
    return [CommissionResponse(**c) for c in commissions]


@router.get("/deals/{deal_id}/commissions", response_model=List[CommissionResponse])
async def get_deal_commissions(
    deal_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all commissions for a deal"""
    cursor = database.commissions.find({"deal_id": deal_id}).sort("created_at", -1)
    commissions = await cursor.to_list(length=100)
    
    for commission in commissions:
        commission["id"] = str(commission["_id"])
        del commission["_id"]
    
    return [CommissionResponse(**c) for c in commissions]


@router.put("/commissions/{commission_id}/approve")
async def approve_commission(
    commission_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Approve a commission"""
    try:
        commission = await commission_processor.approve_commission(
            commission_id=commission_id,
            approved_by=str(current_user.get("_id")),
            database=database
        )
        return commission
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Commission Payouts Endpoints ==========

@router.post("/payouts", response_model=CommissionPayoutResponse, status_code=status.HTTP_201_CREATED)
async def create_commission_payout(
    payout: CommissionPayoutCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a commission payout"""
    try:
        payout_result = await commission_processor.process_payout(
            commission_ids=payout.commission_ids,
            payment_method_id=payout.payment_method_id,
            gateway=payout.gateway,
            database=database
        )
        return CommissionPayoutResponse(**payout_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payouts/{payout_id}", response_model=CommissionPayoutResponse)
async def get_commission_payout(
    payout_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific commission payout"""
    payout = await database.commission_payouts.find_one({"_id": payout_id})
    if not payout:
        raise HTTPException(status_code=404, detail="Commission payout not found")
    
    payout["id"] = str(payout["_id"])
    del payout["_id"]
    
    return CommissionPayoutResponse(**payout)


@router.get("/payouts", response_model=List[CommissionPayoutResponse])
async def get_commission_payouts(
    status: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all commission payouts"""
    query = {}
    if status:
        query["status"] = status
    
    cursor = database.commission_payouts.find(query).sort("created_at", -1)
    payouts = await cursor.to_list(length=100)
    
    for payout in payouts:
        payout["id"] = str(payout["_id"])
        del payout["_id"]
    
    return [CommissionPayoutResponse(**p) for p in payouts]


# ========== Commission Analytics Endpoints ==========

@router.get("/analytics", response_model=CommissionAnalytics)
async def get_commission_analytics(
    recipient_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get commission analytics"""
    try:
        analytics = await commission_processor.get_commission_analytics(
            recipient_id=recipient_id,
            start_date=start_date,
            end_date=end_date,
            database=database
        )
        return CommissionAnalytics(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
