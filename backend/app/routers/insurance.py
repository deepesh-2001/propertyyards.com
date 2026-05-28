"""
Insurance Router
API endpoints for insurance scraping, quotes, and sales integration
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user
from app.insurance_scraper import (
    InsuranceScraper, InsuranceSalesIntegration,
    InsuranceType, InsuranceProvider, InsurancePlan, InsuranceQuote
)
from app.server_monitoring import structured_logger

router = APIRouter(prefix="/api/insurance", tags=["Insurance"])

# Global instances
scraper = InsuranceScraper()
integration = InsuranceSalesIntegration()


@router.get("/plans")
async def get_insurance_plans(
    insurance_type: str = Query(..., description="Type: health, life, property, home, motor, travel"),
    provider: Optional[str] = Query(None, description="Insurance provider"),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get scraped insurance plans by type"""
    try:
        ins_type = InsuranceType(insurance_type.lower())
        prov = InsuranceProvider(provider.lower()) if provider else None

        plans = await scraper.scrape_insurance_plans(ins_type, prov)

        return {
            "type": insurance_type,
            "provider": provider,
            "count": len(plans),
            "plans": [
                {
                    "id": plan.id,
                    "provider": plan.provider,
                    "plan_name": plan.plan_name,
                    "description": plan.description,
                    "coverage_amount": plan.coverage_amount,
                    "premium_monthly": plan.premium_monthly,
                    "premium_yearly": plan.premium_yearly,
                    "entry_age_min": plan.entry_age_min,
                    "entry_age_max": plan.entry_age_max,
                    "benefits": plan.benefits[:5],  # Top 5 benefits
                    "claim_settlement_ratio": plan.claim_settlement_ratio,
                    "network_hospitals": plan.network_hospitals,
                    "rating": plan.rating,
                    "reviews_count": plan.reviews_count,
                    "maternity_cover": plan.maternity_cover,
                    "dental_cover": plan.dental_cover,
                    "vision_cover": plan.vision_cover,
                    "cashless_facility": plan.cashless_facility
                }
                for plan in plans
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid insurance type: {e}")
    except Exception as e:
        structured_logger.error("Insurance plans fetch failed", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def get_insurance_providers(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get list of supported insurance providers"""
    providers = [
        {
            "id": p.value,
            "name": p.name.replace("_", " ").title(),
            "types": _get_provider_types(p)
        }
        for p in InsuranceProvider
    ]

    return {"providers": providers}


def _get_provider_types(provider: InsuranceProvider) -> List[str]:
    """Get insurance types supported by provider"""
    type_mapping = {
        InsuranceProvider.LIC: ["life"],
        InsuranceProvider.HDFC_ERGO: ["health", "home", "motor", "travel"],
        InsuranceProvider.ICICI_LOMBARD: ["health", "home", "motor", "travel"],
        InsuranceProvider.STAR_HEALTH: ["health"],
        InsuranceProvider.MAX_BUPA: ["health"],
        InsuranceProvider.NEW_INDIA: ["health", "motor", "travel"],
        InsuranceProvider.BAJAJ_ALLIANZ: ["health", "home", "motor", "travel"],
        InsuranceProvider.TATA_AIG: ["health", "home", "motor", "travel"],
        InsuranceProvider.RELIANCE: ["health", "home", "motor"],
        InsuranceProvider.SBI_GENERAL: ["health", "home", "motor"]
    }
    return type_mapping.get(provider, ["health"])


@router.post("/recommend")
async def get_recommended_plans(
    insurance_type: str,
    customer_age: int,
    budget_monthly: float,
    required_coverage: float,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get AI-recommended insurance plans based on customer profile"""
    try:
        ins_type = InsuranceType(insurance_type.lower())

        plans = await scraper.get_recommended_plans(
            ins_type, customer_age, budget_monthly, required_coverage
        )

        return {
            "profile": {
                "age": customer_age,
                "budget_monthly": budget_monthly,
                "required_coverage": required_coverage
            },
            "recommendations": [
                {
                    "id": plan.id,
                    "provider": plan.provider,
                    "plan_name": plan.plan_name,
                    "coverage_amount": plan.coverage_amount,
                    "premium_monthly": plan.premium_monthly,
                    "premium_yearly": plan.premium_yearly,
                    "match_score": _calculate_match_score(plan, budget_monthly, required_coverage),
                    "key_benefits": plan.benefits[:3],
                    "why_recommended": _get_recommendation_reason(plan, ins_type)
                }
                for plan in plans
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _calculate_match_score(plan: InsurancePlan, budget: float, coverage: float) -> float:
    """Calculate how well a plan matches customer requirements"""
    budget_score = 1.0 if plan.premium_monthly <= budget else budget / plan.premium_monthly
    coverage_score = min(plan.coverage_amount / coverage, 1.5) / 1.5
    rating_score = plan.rating / 5.0
    claims_score = plan.claim_settlement_ratio / 100.0

    return round((budget_score * 0.3 + coverage_score * 0.3 + rating_score * 0.2 + claims_score * 0.2) * 100, 1)


def _get_recommendation_reason(plan: InsurancePlan, ins_type: InsuranceType) -> str:
    """Generate recommendation reason text"""
    reasons = []

    if plan.claim_settlement_ratio >= 95:
        reasons.append("Excellent claim settlement ratio")
    if plan.network_hospitals >= 5000:
        reasons.append("Wide network coverage")
    if plan.rating >= 4.5:
        reasons.append("Highly rated by customers")
    if plan.maternity_cover and ins_type == InsuranceType.HEALTH:
        reasons.append("Includes maternity coverage")
    if plan.cashless_facility:
        reasons.append("Cashless facility available")

    return "; ".join(reasons) if reasons else "Good overall coverage"


@router.post("/compare")
async def compare_plans(
    plan_ids: List[str],
    insurance_type: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Compare multiple insurance plans side by side"""
    try:
        ins_type = InsuranceType(insurance_type.lower())
        comparison = await scraper.compare_plans(plan_ids, ins_type)

        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sales/{sale_id}/quotes")
async def generate_sale_insurance_quotes(
    sale_id: str,
    property_value: float,
    customer_id: str,
    customer_age: int,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate insurance quotes for a property sale"""
    try:
        quotes = await integration.generate_sale_insurance_quotes(
            sale_id, property_value, customer_id, customer_age
        )

        # Save quotes to database
        for quote in quotes:
            await integration.save_quote_to_database(quote, db)

        return {
            "sale_id": sale_id,
            "quotes_generated": len(quotes),
            "total_potential_commission": sum(q.commission_amount for q in quotes),
            "quotes": [
                {
                    "id": q.id,
                    "insurance_type": q.insurance_type.value,
                    "plan_id": q.selected_plan_id,
                    "coverage_amount": q.coverage_amount,
                    "premium_amount": q.premium_amount,
                    "premium_frequency": q.premium_frequency,
                    "commission_amount": q.commission_amount,
                    "status": q.status
                }
                for q in quotes
            ]
        }
    except Exception as e:
        structured_logger.error(
            "Insurance quote generation failed",
            {"sale_id": sale_id, "error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sales/{sale_id}/summary")
async def get_sale_insurance_summary(
    sale_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get insurance summary for a property sale"""
    try:
        summary = await integration.get_sale_insurance_summary(sale_id, db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_insurance_types(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get available insurance types with descriptions"""
    types_info = [
        {
            "id": InsuranceType.HEALTH.value,
            "name": "Health Insurance",
            "description": "Covers medical expenses, hospitalization, and treatments",
            "typical_coverage": "₹5-50 Lakhs",
            "who_should_buy": "Everyone, especially those with dependents",
            "tax_benefit": "Section 80D - Up to ₹25,000-50,000"
        },
        {
            "id": InsuranceType.LIFE.value,
            "name": "Life Insurance",
            "description": "Financial protection for family in case of death",
            "typical_coverage": "10-20x annual income",
            "who_should_buy": "Primary earners with dependents",
            "tax_benefit": "Section 80C - Up to ₹1.5 Lakhs"
        },
        {
            "id": InsuranceType.PROPERTY.value,
            "name": "Property Insurance",
            "description": "Covers building structure and contents against damage",
            "typical_coverage": "Property value + 10-20%",
            "who_should_buy": "All property owners",
            "tax_benefit": "Business expense deduction"
        },
        {
            "id": InsuranceType.HOME.value,
            "name": "Home Insurance",
            "description": "Comprehensive cover for home structure and belongings",
            "typical_coverage": "₹10-100 Lakhs",
            "who_should_buy": "Homeowners and renters",
            "tax_benefit": "Available for rented properties"
        },
        {
            "id": InsuranceType.MOTOR.value,
            "name": "Motor Insurance",
            "description": "Covers vehicles against damage and third-party liability",
            "typical_coverage": "Vehicle IDV + Third party",
            "who_should_buy": "All vehicle owners (mandatory)",
            "tax_benefit": "Business vehicle deduction"
        },
        {
            "id": InsuranceType.CRITICAL_ILLNESS.value,
            "name": "Critical Illness",
            "description": "Lump sum payout on diagnosis of critical diseases",
            "typical_coverage": "₹10-50 Lakhs",
            "who_should_buy": "Those with family history of critical illnesses",
            "tax_benefit": "Section 80D"
        },
        {
            "id": InsuranceType.PERSONAL_ACCIDENT.value,
            "name": "Personal Accident",
            "description": "Coverage for accidental death and disability",
            "typical_coverage": "₹10-100 Lakhs",
            "who_should_buy": "Working professionals",
            "tax_benefit": "Section 80D"
        },
        {
            "id": InsuranceType.TRAVEL.value,
            "name": "Travel Insurance",
            "description": "Covers trip cancellations, medical emergencies abroad",
            "typical_coverage": "$50,000-500,000",
            "who_should_buy": "International travelers",
            "tax_benefit": "Business travel expense"
        }
    ]

    return {"types": types_info}


@router.post("/refresh")
async def refresh_insurance_data(
    insurance_type: Optional[str] = None,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Refresh scraped insurance data (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        types_to_refresh = [InsuranceType(insurance_type.lower())] if insurance_type else list(InsuranceType)

        refreshed = []
        for ins_type in types_to_refresh:
            plans = await scraper.scrape_insurance_plans(ins_type)
            refreshed.append({
                "type": ins_type.value,
                "plans_count": len(plans)
            })

        structured_logger.info(
            "Insurance data refreshed",
            {"refreshed_types": len(refreshed)}
        )

        return {
            "refreshed": True,
            "types": refreshed,
            "refreshed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quotes/pending")
async def get_pending_quotes(
    limit: int = 50,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get pending insurance quotes (for sales team)"""
    try:
        quotes = await db.insurance_quotes.find(
            {"status": "quoted"}
        ).sort("created_at", -1).limit(limit).to_list(length=limit)

        return {
            "pending_quotes": len(quotes),
            "quotes": quotes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/metrics")
async def get_insurance_dashboard(
    days: int = 30,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get insurance sales dashboard metrics"""
    try:
        from datetime import timedelta

        start_date = datetime.utcnow() - timedelta(days=days)

        # Get quotes in period
        quotes = await db.insurance_quotes.find(
            {"created_at": {"$gte": start_date}}
        ).to_list(length=1000)

        # Calculate metrics
        total_quotes = len(quotes)
        purchased = [q for q in quotes if q.get("status") == "purchased"]
        conversion_rate = (len(purchased) / total_quotes * 100) if total_quotes > 0 else 0

        total_commission = sum(q.get("commission_amount", 0) for q in purchased)
        total_premium = sum(q.get("premium_amount", 0) for q in purchased)

        # By type
        by_type = {}
        for q in quotes:
            t = q.get("insurance_type", "unknown")
            if t not in by_type:
                by_type[t] = {"quoted": 0, "purchased": 0, "commission": 0}
            by_type[t]["quoted"] += 1
            if q.get("status") == "purchased":
                by_type[t]["purchased"] += 1
                by_type[t]["commission"] += q.get("commission_amount", 0)

        return {
            "period_days": days,
            "total_quotes": total_quotes,
            "purchased": len(purchased),
            "conversion_rate": round(conversion_rate, 2),
            "total_commission": total_commission,
            "total_premium": total_premium,
            "by_type": by_type,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
