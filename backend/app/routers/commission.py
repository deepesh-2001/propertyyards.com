"""
Commission Router
Handles commission rules, calculations, and payouts
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

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
    PaymentGateway,
    IncentiveRuleCreate,
    IncentiveRuleResponse,
    IncentiveAwardCreate,
    IncentiveResponse,
    IncentiveStatus,
)
from app.commission import commission_processor, incentive_processor
from app.currency_manager import currency_manager
from app.auth import get_current_user
from app.cache import get_from_cache, set_in_cache, delete_from_cache, generate_cache_key, invalidate_cache_pattern
from app.feature_flags import require_feature_flag

router = APIRouter(prefix="/api/commissions", tags=["commissions"])

# Roles allowed to manage commission/incentive rules and approve payouts.
MANAGE_ROLES = {"admin", "manager", "finance"}


def require_manage_access(current_user: dict):
    """Raise 403 unless the user may manage commissions/incentives."""
    if current_user.get("role") not in MANAGE_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Only admin, manager, or finance roles can manage commissions and incentives"
        )


# ========== Commission Rules Endpoints ==========

@router.post("/rules", response_model=CommissionRuleResponse, status_code=status.HTTP_201_CREATED)
@require_feature_flag("commission_system")
async def create_commission_rule(
    rule: CommissionRuleCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new commission rule (admin/manager/finance only).

    Supports per-product rules (``product_category`` / ``product_id``) and
    per-user rate overrides (``user_rates``) so different users can earn
    different commission on different products.
    """
    require_manage_access(current_user)
    if not currency_manager.is_valid_currency(rule.currency):
        raise HTTPException(status_code=400, detail=f"Unsupported currency: {rule.currency}")
    try:
        rule_data = rule.dict()
        rule_data.update({
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

        result = await database.commission_rules.insert_one(rule_data)
        rule_data["id"] = str(result.inserted_id)

        # Invalidate commission rules cache
        await invalidate_cache_pattern("commission_rules:*")

        return CommissionRuleResponse(**rule_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}", response_model=CommissionRuleResponse)
@require_feature_flag("commission_system")
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
@require_feature_flag("commission_system")
async def get_commission_rules(
    commission_type: Optional[CommissionType] = None,
    is_active: Optional[bool] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all commission rules"""
    # Check cache
    cache_key = generate_cache_key("commission_rules", commission_type or "all", is_active)
    cached_result = await get_from_cache(cache_key)
    if cached_result:
        return [CommissionRuleResponse(**r) for r in cached_result]

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

    # Cache the result (15 minutes - rules don't change often)
    await set_in_cache(cache_key, rules, ttl=900)

    return [CommissionRuleResponse(**r) for r in rules]


# ========== Commission Endpoints ==========

@router.post("/calculate")
@require_feature_flag("commission_system")
async def calculate_commission(
    deal_id: str,
    deal_type: str,
    deal_amount: float,
    recipient_id: str,
    recipient_type: str,
    commission_rule_id: str,
    product_category: Optional[str] = None,
    product_id: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Calculate commission for a deal (honors per-user / per-product rates)."""
    try:
        commission = await commission_processor.calculate_deal_commission(
            deal_id=deal_id,
            deal_type=deal_type,
            deal_amount=deal_amount,
            recipient_id=recipient_id,
            recipient_type=recipient_type,
            commission_rule_id=commission_rule_id,
            database=database,
            product_category=product_category,
            product_id=product_id
        )
        return commission
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/builder-property")
@require_feature_flag("commission_system")
async def calculate_builder_property_commission(
    property_id: str,
    property_value: float,
    recipient_id: str,
    recipient_type: str,
    commission_rule_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Calculate commission for builder property sale"""
    try:
        commission = await commission_processor.calculate_deal_commission(
            deal_id=property_id,
            deal_type="builder_property",
            deal_amount=property_value,
            recipient_id=recipient_id,
            recipient_type=recipient_type,
            commission_rule_id=commission_rule_id,
            database=database
        )
        return commission
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/loan")
@require_feature_flag("commission_system")
async def calculate_loan_commission(
    loan_id: str,
    loan_amount: float,
    recipient_id: str,
    recipient_type: str,
    commission_rule_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Calculate commission for loan processing"""
    try:
        commission = await commission_processor.calculate_deal_commission(
            deal_id=loan_id,
            deal_type="loan",
            deal_amount=loan_amount,
            recipient_id=recipient_id,
            recipient_type=recipient_type,
            commission_rule_id=commission_rule_id,
            database=database
        )
        return commission
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/credit-card-cashback")
@require_feature_flag("credit_card_cashback")
async def calculate_credit_card_cashback_commission(
    cashback_id: str,
    cashback_amount: float,
    recipient_id: str,
    recipient_type: str,
    commission_rule_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Calculate commission for credit card cashback"""
    try:
        commission = await commission_processor.calculate_deal_commission(
            deal_id=cashback_id,
            deal_type="credit_card_cashback",
            deal_amount=cashback_amount,
            recipient_id=recipient_id,
            recipient_type=recipient_type,
            commission_rule_id=commission_rule_id,
            database=database
        )
        return commission
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commissions/{commission_id}", response_model=CommissionResponse)
@require_feature_flag("commission_system")
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
@require_feature_flag("commission_system")
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
@require_feature_flag("commission_system")
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
@require_feature_flag("commission_system")
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
@require_feature_flag("commission_system")
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
@require_feature_flag("commission_system")
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
@require_feature_flag("commission_system")
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
@require_feature_flag("commission_system")
async def get_commission_analytics(
    recipient_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get commission analytics"""
    try:
        # Check cache (5 minutes for analytics)
        cache_key = generate_cache_key(
            "commission_analytics",
            recipient_id or "all",
            start_date.isoformat() if start_date else "none",
            end_date.isoformat() if end_date else "none"
        )
        cached_result = await get_from_cache(cache_key)
        if cached_result:
            return CommissionAnalytics(**cached_result)

        analytics = await commission_processor.get_commission_analytics(
            database=database,
            recipient_id=recipient_id,
            start_date=start_date,
            end_date=end_date
        )

        # Cache the result
        await set_in_cache(cache_key, analytics, ttl=300)

        return CommissionAnalytics(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/returns/monthly")
@require_feature_flag("commission_system")
async def get_monthly_returns(
    recipient_id: Optional[str] = None,
    year: Optional[int] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get monthly commission returns"""
    try:
        # Check cache (10 minutes - monthly returns don't change often)
        cache_key = generate_cache_key("monthly_returns", recipient_id or "all", year or "current")
        cached_result = await get_from_cache(cache_key)
        if cached_result:
            return cached_result

        query = {}
        if recipient_id:
            query["recipient_id"] = recipient_id
        if year:
            query["created_at"] = {"$gte": datetime(year, 1, 1), "$lte": datetime(year, 12, 31, 23, 59, 59)}

        commissions = await database.commissions.find(query).to_list(length=1000)
        monthly_returns = commission_processor._calculate_monthly_returns(commissions)

        result = {"monthly_returns": monthly_returns}
        await set_in_cache(cache_key, result, ttl=600)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/returns/quarterly")
@require_feature_flag("commission_system")
async def get_quarterly_returns(
    recipient_id: Optional[str] = None,
    year: Optional[int] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get quarterly commission returns"""
    try:
        # Check cache (10 minutes)
        cache_key = generate_cache_key("quarterly_returns", recipient_id or "all", year or "current")
        cached_result = await get_from_cache(cache_key)
        if cached_result:
            return cached_result

        query = {}
        if recipient_id:
            query["recipient_id"] = recipient_id
        if year:
            query["created_at"] = {"$gte": datetime(year, 1, 1), "$lte": datetime(year, 12, 31, 23, 59, 59)}

        commissions = await database.commissions.find(query).to_list(length=1000)
        quarterly_returns = commission_processor._calculate_quarterly_returns(commissions)

        result = {"quarterly_returns": quarterly_returns}
        await set_in_cache(cache_key, result, ttl=600)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/returns/yearly")
@require_feature_flag("commission_system")
async def get_yearly_returns(
    recipient_id: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get yearly commission returns"""
    try:
        # Check cache (15 minutes - yearly returns change slowly)
        cache_key = generate_cache_key("yearly_returns", recipient_id or "all")
        cached_result = await get_from_cache(cache_key)
        if cached_result:
            return cached_result

        query = {}
        if recipient_id:
            query["recipient_id"] = recipient_id

        commissions = await database.commissions.find(query).to_list(length=1000)
        yearly_returns = commission_processor._calculate_yearly_returns(commissions)

        result = {"yearly_returns": yearly_returns}
        await set_in_cache(cache_key, result, ttl=900)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/returns/total")
@require_feature_flag("commission_system")
async def get_total_returns(
    recipient_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get total commission returns for a recipient"""
    try:
        query = {"recipient_id": recipient_id}
        commissions = await database.commissions.find(query).to_list(length=1000)
        
        total_returns = sum(c["calculated_amount"] for c in commissions if c["status"] == CommissionStatus.PAID)
        pending_returns = sum(c["calculated_amount"] for c in commissions if c["status"] == CommissionStatus.PENDING)
        
        # Get first and last commission dates
        if commissions:
            first_date = min(c["created_at"] for c in commissions)
            last_date = max(c["created_at"] for c in commissions)
        else:
            first_date = datetime.utcnow()
            last_date = datetime.utcnow()
        
        # Calculate average monthly returns
        months = max(1, (last_date - first_date).days / 30)
        average_monthly = total_returns / months
        
        # Calculate CAGR
        years = max(1, months / 12)
        if total_returns > 0 and years > 1:
            cagr = ((total_returns / 1000) ** (1 / years) - 1) * 100
        else:
            cagr = 0
        
        return {
            "total_returns": total_returns,
            "pending_returns": pending_returns,
            "average_monthly_returns": average_monthly,
            "cagr": cagr,
            "first_commission_date": first_date,
            "last_commission_date": last_date,
            "total_commissions": len(commissions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Incentive Endpoints ==========

@router.post("/incentive-rules", response_model=IncentiveRuleResponse, status_code=status.HTTP_201_CREATED)
@require_feature_flag("commission_system")
async def create_incentive_rule(
    rule: IncentiveRuleCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create an incentive rule (admin/manager/finance only)."""
    require_manage_access(current_user)
    if not currency_manager.is_valid_currency(rule.currency):
        raise HTTPException(status_code=400, detail=f"Unsupported currency: {rule.currency}")
    try:
        rule_data = rule.dict()
        rule_data.update({
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        result = await database.incentive_rules.insert_one(rule_data)
        rule_data["id"] = str(result.inserted_id)
        await invalidate_cache_pattern("incentive_rules:*")
        return IncentiveRuleResponse(**rule_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/incentive-rules", response_model=List[IncentiveRuleResponse])
@require_feature_flag("commission_system")
async def get_incentive_rules(
    is_active: Optional[bool] = None,
    product_category: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List incentive rules."""
    cache_key = generate_cache_key(
        "incentive_rules", product_category or "all", is_active
    )
    cached_result = await get_from_cache(cache_key)
    if cached_result:
        return [IncentiveRuleResponse(**r) for r in cached_result]

    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    if product_category:
        query["product_category"] = product_category

    cursor = database.incentive_rules.find(query).sort("created_at", -1)
    rules = await cursor.to_list(length=100)
    for rule in rules:
        rule["id"] = str(rule["_id"])
        del rule["_id"]

    # Cache the result (15 minutes - rules change rarely)
    await set_in_cache(cache_key, rules, ttl=900)

    return [IncentiveRuleResponse(**r) for r in rules]


@router.get("/incentive-rules/{rule_id}", response_model=IncentiveRuleResponse)
@require_feature_flag("commission_system")
async def get_incentive_rule(
    rule_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific incentive rule."""
    rule = await database.incentive_rules.find_one({"_id": rule_id})
    if not rule:
        raise HTTPException(status_code=404, detail="Incentive rule not found")
    rule["id"] = str(rule["_id"])
    del rule["_id"]
    return IncentiveRuleResponse(**rule)


@router.post("/incentives/award", response_model=IncentiveResponse, status_code=status.HTTP_201_CREATED)
@require_feature_flag("commission_system")
async def award_incentive(
    award: IncentiveAwardCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Calculate and award an incentive to a recipient (admin/manager/finance only)."""
    require_manage_access(current_user)
    if award.currency and not currency_manager.is_valid_currency(award.currency):
        raise HTTPException(status_code=400, detail=f"Unsupported currency: {award.currency}")
    try:
        incentive = await incentive_processor.award_incentive(
            recipient_id=award.recipient_id,
            recipient_type=award.recipient_type,
            incentive_rule_id=award.incentive_rule_id,
            database=database,
            product_category=award.product_category,
            units_sold=award.units_sold,
            amount=award.amount,
            achievement=award.achievement,
            currency=award.currency,
            period=award.period,
            notes=award.notes
        )
        return IncentiveResponse(**incentive)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recipients/{recipient_id}/incentives", response_model=List[IncentiveResponse])
@require_feature_flag("commission_system")
async def get_recipient_incentives(
    recipient_id: str,
    status: Optional[IncentiveStatus] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List incentives awarded to a recipient."""
    query = {"recipient_id": recipient_id}
    if status:
        query["status"] = status
    cursor = database.incentives.find(query).sort("created_at", -1)
    incentives = await cursor.to_list(length=100)
    for incentive in incentives:
        incentive["id"] = str(incentive["_id"])
        del incentive["_id"]
    return [IncentiveResponse(**i) for i in incentives]


@router.put("/incentives/{incentive_id}/approve", response_model=IncentiveResponse)
@require_feature_flag("commission_system")
async def approve_incentive(
    incentive_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Approve a pending incentive (admin/manager/finance only)."""
    require_manage_access(current_user)
    try:
        incentive = await incentive_processor.approve_incentive(
            incentive_id=incentive_id,
            approved_by=current_user.get("user_id"),
            database=database
        )
        return IncentiveResponse(**incentive)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Currency Endpoints ==========

@router.get("/currencies")
async def list_supported_currencies(
    fiat_only: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """List supported currencies for commissions/incentives (INR + foreign)."""
    currencies = (
        currency_manager.get_fiat_currencies() if fiat_only
        else currency_manager.get_all_currencies()
    )
    return {
        "default": "INR",
        "currencies": [
            {
                "code": c.code,
                "name": c.name,
                "symbol": c.symbol,
                "decimal_places": c.decimal_places,
                "is_crypto": c.is_crypto,
            }
            for c in currencies
        ],
    }


@router.get("/convert")
async def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
    current_user: dict = Depends(get_current_user)
):
    """Convert an amount between currencies (e.g. INR <-> USD).

    Requires exchange rates to be loaded; returns 503 if a rate is unavailable.
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    if not currency_manager.is_valid_currency(from_currency):
        raise HTTPException(status_code=400, detail=f"Unsupported currency: {from_currency}")
    if not currency_manager.is_valid_currency(to_currency):
        raise HTTPException(status_code=400, detail=f"Unsupported currency: {to_currency}")
    try:
        converted = currency_manager.convert(Decimal(str(amount)), from_currency, to_currency)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {
        "amount": amount,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "converted_amount": float(converted),
        "formatted": currency_manager.format_amount(converted, to_currency),
        "rate_age_minutes": currency_manager.get_rate_age_minutes(),
    }
