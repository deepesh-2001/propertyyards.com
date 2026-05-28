"""
Insurance Scraper & Integration Module
Scrapes health, life, property, and home insurance plans from the internet
and integrates with sales workflow
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import re
import json
import asyncio

from app.cache import get_from_cache, set_in_cache
from app.database import get_db
from app.server_monitoring import structured_logger

logger = logging.getLogger(__name__)

try:
    import aiohttp
    from bs4 import BeautifulSoup
    HAS_SCRAPING_DEPS = True
except ImportError:
    HAS_SCRAPING_DEPS = False
    logger.warning("Insurance scraping dependencies not available")


class InsuranceType(Enum):
    """Types of insurance"""
    HEALTH = "health"
    LIFE = "life"
    PROPERTY = "property"
    HOME = "home"
    MOTOR = "motor"
    TRAVEL = "travel"
    CRITICAL_ILLNESS = "critical_illness"
    PERSONAL_ACCIDENT = "personal_accident"


class InsuranceProvider(Enum):
    """Major insurance providers in India"""
    LIC = "lic"
    HDFC_ERGO = "hdfc_ergo"
    ICICI_LOMBARD = "icici_lombard"
    STAR_HEALTH = "star_health"
    MAX_BUPA = "max_bupa"
    NEW_INDIA = "new_india"
    ORIENTAL = "oriental"
    UNITED_INDIA = "united_india"
    BAJAJ_ALLIANZ = "bajaj_allianz"
    TATA_AIG = "tata_aig"
    RELIANCE = "reliance"
    SBI_GENERAL = "sbi_general"


@dataclass
class InsurancePlan:
    """Insurance plan data structure"""
    id: str
    provider: str
    insurance_type: InsuranceType
    plan_name: str
    description: str
    coverage_amount: float  # Sum insured
    premium_monthly: float
    premium_yearly: float
    entry_age_min: int
    entry_age_max: int
    policy_term_min: int
    policy_term_max: int
    waiting_period_days: int = 0
    coverage_details: Dict[str, Any] = field(default_factory=dict)
    benefits: List[str] = field(default_factory=list)
    exclusions: List[str] = field(default_factory=list)
    network_hospitals: int = 0
    claim_settlement_ratio: float = 0.0
    renewal_bonus: bool = True
    tax_benefit_80d: bool = True
    cashless_facility: bool = True
    room_rent_limit: Optional[str] = None
    icu_limit: Optional[str] = None
    pre_existing_disease_cover: bool = False
    maternity_cover: bool = False
    dental_cover: bool = False
    vision_cover: bool = False
    mental_health_cover: bool = False
    wellness_programs: List[str] = field(default_factory=list)
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    source_url: str = ""
    is_active: bool = True
    rating: float = 0.0
    reviews_count: int = 0


@dataclass
class InsuranceQuote:
    """Insurance quote for a customer"""
    id: str
    customer_id: str
    property_id: Optional[str] = None
    sale_id: Optional[str] = None
    insurance_type: InsuranceType = InsuranceType.PROPERTY
    selected_plan_id: str = ""
    coverage_amount: float = 0.0
    premium_amount: float = 0.0
    premium_frequency: str = "yearly"  # monthly, quarterly, half_yearly, yearly
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str = "quoted"  # quoted, purchased, cancelled, expired
    beneficiaries: List[Dict[str, Any]] = field(default_factory=list)
    nominee_details: Dict[str, Any] = field(default_factory=dict)
    medical_declarations: Dict[str, Any] = field(default_factory=dict)
    documents: List[str] = field(default_factory=list)
    commission_amount: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class InsuranceScraper:
    """Scraper for insurance plans from various providers"""

    def __init__(self):
        self.cache_prefix = "insurance:"
        self.cache_ttl = 7200  # 2 hours cache
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

        # Provider configurations
        self.providers = {
            InsuranceProvider.HDFC_ERGO: {
                "base_url": "https://www.hdfcergo.com",
                "health_url": "/health-insurance",
                "home_url": "/home-insurance",
                "motor_url": "/car-insurance",
            },
            InsuranceProvider.ICICI_LOMBARD: {
                "base_url": "https://www.icicilombard.com",
                "health_url": "/health-insurance",
                "home_url": "/home-insurance",
                "motor_url": "/motor-insurance/car-insurance",
            },
            InsuranceProvider.STAR_HEALTH: {
                "base_url": "https://www.starhealth.in",
                "health_url": "/health-insurance",
            },
            InsuranceProvider.BAJAJ_ALLIANZ: {
                "base_url": "https://www.bajajallianz.com",
                "health_url": "/health-insurance",
                "home_url": "/home-insurance",
            },
            InsuranceProvider.TATA_AIG: {
                "base_url": "https://www.tataaig.com",
                "health_url": "/health-insurance",
                "home_url": "/home-insurance",
            },
            InsuranceProvider.LIC: {
                "base_url": "https://licindia.in",
                "life_url": "/Life-Insurance",
            },
        }

        # Sample plan templates (fallback when scraping unavailable)
        self.sample_plans = self._generate_sample_plans()

    def _generate_sample_plans(self) -> List[InsurancePlan]:
        """Generate sample insurance plans as fallback"""
        plans = []
        plan_id = 1

        # Health Insurance Plans
        health_plans = [
            {
                "provider": InsuranceProvider.STAR_HEALTH.value,
                "plan_name": "Star Health Comprehensive",
                "coverage": 5000000,
                "premium_yearly": 15000,
                "benefits": [
                    "Cashless treatment at 10000+ hospitals",
                    "Pre and post hospitalization cover",
                    "Day care procedures",
                    "Annual health checkup",
                    "Ambulance charges covered"
                ]
            },
            {
                "provider": InsuranceProvider.ICICI_LOMBARD.value,
                "plan_name": "Complete Health Insurance",
                "coverage": 10000000,
                "premium_yearly": 28000,
                "benefits": [
                    "Worldwide coverage",
                    "No room rent limit",
                    "Restoration of sum insured",
                    "Maternity cover after 2 years",
                    "New born baby cover"
                ]
            },
            {
                "provider": InsuranceProvider.MAX_BUPA.value,
                "plan_name": "Health Companion",
                "coverage": 3000000,
                "premium_yearly": 12000,
                "benefits": [
                    "Direct claim settlement",
                    "Health rewards program",
                    "Alternative treatments covered",
                    "Dental and vision cover",
                    "Mental health support"
                ]
            },
            {
                "provider": InsuranceProvider.HDFC_ERGO.value,
                "plan_name": "Optima Secure",
                "coverage": 5000000,
                "premium_yearly": 18500,
                "benefits": [
                    "2x coverage from day 1",
                    "No medical checkup up to 45 years",
                    "Pre-existing disease cover after 3 years",
                    "AYUSH treatment covered",
                    "E-opinion for critical illnesses"
                ]
            }
        ]

        for plan_data in health_plans:
            plans.append(InsurancePlan(
                id=f"HI{plan_id:04d}",
                provider=plan_data["provider"],
                insurance_type=InsuranceType.HEALTH,
                plan_name=plan_data["plan_name"],
                description=f"Comprehensive health insurance with ₹{plan_data['coverage']:,.0f} coverage",
                coverage_amount=plan_data["coverage"],
                premium_monthly=plan_data["premium_yearly"] / 12,
                premium_yearly=plan_data["premium_yearly"],
                entry_age_min=18,
                entry_age_max=65,
                policy_term_min=1,
                policy_term_max=3,
                waiting_period_days=30,
                benefits=plan_data["benefits"],
                network_hospitals=10000,
                claim_settlement_ratio=95.0,
                cashless_facility=True,
                maternity_cover=True,
                dental_cover=True,
                vision_cover=True,
                mental_health_cover=True,
                rating=4.5,
                reviews_count=2500
            ))
            plan_id += 1

        # Life Insurance Plans
        life_plans = [
            {
                "provider": InsuranceProvider.LIC.value,
                "plan_name": "Jeevan Amar",
                "coverage": 10000000,
                "premium_yearly": 8500,
                "term": 20,
                "benefits": [
                    "Pure term plan with high coverage",
                    "Lower premium for non-smokers",
                    "Option to increase coverage",
                    "Tax benefits under 80C and 10(10D)",
                    "Rider options available"
                ]
            },
            {
                "provider": InsuranceProvider.HDFC_ERGO.value,
                "plan_name": "Click 2 Protect Life",
                "coverage": 20000000,
                "premium_yearly": 12000,
                "term": 25,
                "benefits": [
                    "Life cover with return of premium",
                    "Critical illness rider",
                    "Accidental death benefit",
                    "Waiver of premium on disability",
                    "Monthly income option"
                ]
            }
        ]

        for plan_data in life_plans:
            plans.append(InsurancePlan(
                id=f"LI{plan_id:04d}",
                provider=plan_data["provider"],
                insurance_type=InsuranceType.LIFE,
                plan_name=plan_data["plan_name"],
                description=f"Term life insurance with ₹{plan_data['coverage']:,.0f} death benefit",
                coverage_amount=plan_data["coverage"],
                premium_monthly=plan_data["premium_yearly"] / 12,
                premium_yearly=plan_data["premium_yearly"],
                entry_age_min=18,
                entry_age_max=55,
                policy_term_min=10,
                policy_term_max=plan_data["term"],
                benefits=plan_data["benefits"],
                claim_settlement_ratio=98.5,
                rating=4.7,
                reviews_count=5000
            ))
            plan_id += 1

        # Property/Home Insurance Plans
        home_plans = [
            {
                "provider": InsuranceProvider.ICICI_LOMBARD.value,
                "plan_name": "Home Insurance",
                "coverage": 5000000,
                "premium_yearly": 3500,
                "benefits": [
                    "Building structure cover",
                    "Contents cover",
                    "Burglary and theft protection",
                    "Natural calamities cover",
                    "Fire and allied perils"
                ]
            },
            {
                "provider": InsuranceProvider.HDFC_ERGO.value,
                "plan_name": "Property Insurance",
                "coverage": 10000000,
                "premium_yearly": 6500,
                "benefits": [
                    "Comprehensive property cover",
                    "Rent for alternative accommodation",
                    "Public liability cover",
                    "Employee compensation",
                    "24/7 claims support"
                ]
            },
            {
                "provider": InsuranceProvider.BAJAJ_ALLIANZ.value,
                "plan_name": "Home Shield",
                "coverage": 3000000,
                "premium_yearly": 2200,
                "benefits": [
                    "Structure and content cover",
                    "Portable equipment cover",
                    "Jewelry and valuables cover",
                    "Loss of rent cover",
                    "Pet insurance optional"
                ]
            }
        ]

        for plan_data in home_plans:
            plans.append(InsurancePlan(
                id=f"PI{plan_id:04d}",
                provider=plan_data["provider"],
                insurance_type=InsuranceType.PROPERTY,
                plan_name=plan_data["plan_name"],
                description=f"Property insurance with ₹{plan_data['coverage']:,.0f} coverage",
                coverage_amount=plan_data["coverage"],
                premium_monthly=plan_data["premium_yearly"] / 12,
                premium_yearly=plan_data["premium_yearly"],
                entry_age_min=18,
                entry_age_max=75,
                policy_term_min=1,
                policy_term_max=5,
                benefits=plan_data["benefits"],
                claim_settlement_ratio=92.0,
                rating=4.3,
                reviews_count=1200
            ))
            plan_id += 1

        return plans

    async def scrape_insurance_plans(
        self,
        insurance_type: InsuranceType,
        provider: Optional[InsuranceProvider] = None
    ) -> List[InsurancePlan]:
        """Scrape insurance plans from providers"""
        
        # Check cache first
        cache_key = f"{self.cache_prefix}{insurance_type.value}:plans"
        if provider:
            cache_key += f":{provider.value}"
        
        cached = await get_from_cache(cache_key)
        if cached:
            return [InsurancePlan(**plan) for plan in json.loads(cached)]

        # If scraping unavailable, return sample plans
        if not HAS_SCRAPING_DEPS:
            filtered_plans = [
                plan for plan in self.sample_plans
                if plan.insurance_type == insurance_type
            ]
            if provider:
                filtered_plans = [
                    plan for plan in filtered_plans
                    if plan.provider == provider.value
                ]
            return filtered_plans

        # Attempt to scrape from web
        scraped_plans = await self._scrape_from_web(insurance_type, provider)
        
        if scraped_plans:
            # Cache the results
            await set_in_cache(
                cache_key,
                json.dumps([self._plan_to_dict(plan) for plan in scraped_plans]),
                ttl=self.cache_ttl
            )
            return scraped_plans

        # Fallback to sample plans
        filtered_plans = [
            plan for plan in self.sample_plans
            if plan.insurance_type == insurance_type
        ]
        if provider:
            filtered_plans = [
                plan for plan in filtered_plans
                if plan.provider == provider.value
            ]
        
        return filtered_plans

    async def _scrape_from_web(
        self,
        insurance_type: InsuranceType,
        provider: Optional[InsuranceProvider]
    ) -> List[InsurancePlan]:
        """Scrape insurance plans from provider websites"""
        plans = []

        providers_to_scrape = [provider] if provider else list(self.providers.keys())

        for prov in providers_to_scrape:
            try:
                prov_plans = await self._scrape_provider(prov, insurance_type)
                plans.extend(prov_plans)
            except Exception as e:
                logger.error(f"Failed to scrape {prov.value}: {e}")
                structured_logger.error(
                    "Insurance scraping failed",
                    {"provider": prov.value, "type": insurance_type.value, "error": str(e)}
                )

        return plans

    async def _scrape_provider(
        self,
        provider: InsuranceProvider,
        insurance_type: InsuranceType
    ) -> List[InsurancePlan]:
        """Scrape plans from a specific provider"""
        plans = []
        prov_config = self.providers.get(provider, {})

        # Determine URL based on insurance type
        url_key = f"{insurance_type.value}_url"
        url = prov_config.get(url_key)

        if not url:
            return plans

        full_url = f"{prov_config['base_url']}{url}"

        try:
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(full_url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Extract plan data (provider-specific selectors would be here)
                        # This is a simplified example
                        plan_cards = soup.find_all('div', class_='plan-card')[:5]

                        for idx, card in enumerate(plan_cards):
                            try:
                                plan = self._parse_plan_card(
                                    card, provider, insurance_type, idx
                                )
                                if plan:
                                    plans.append(plan)
                            except Exception as e:
                                logger.warning(f"Failed to parse plan card: {e}")

        except Exception as e:
            logger.error(f"Provider scraping error: {e}")

        return plans

    def _parse_plan_card(
        self,
        card,
        provider: InsuranceProvider,
        insurance_type: InsuranceType,
        index: int
    ) -> Optional[InsurancePlan]:
        """Parse plan data from HTML card"""
        try:
            # Extract plan name
            name_elem = card.find('h3') or card.find('h2') or card.find('div', class_='plan-name')
            plan_name = name_elem.get_text(strip=True) if name_elem else f"Plan {index + 1}"

            # Extract coverage amount
            coverage_text = card.get_text()
            coverage_match = re.search(r'₹?\s*([\d,]+)\s*(Lacs?|Lakhs?|Cr|Crore)', coverage_text)
            if coverage_match:
                amount_str = coverage_match.group(1).replace(',', '')
                multiplier = 100000 if 'L' in coverage_match.group(2) else 10000000
                coverage = float(amount_str) * multiplier
            else:
                coverage = 500000  # Default

            # Extract premium
            premium_match = re.search(r'₹?\s*([\d,]+)\s*/?\s*(month|year)?', coverage_text)
            if premium_match:
                premium = float(premium_match.group(1).replace(',', ''))
            else:
                premium = coverage * 0.002  # Estimate 0.2% of coverage

            return InsurancePlan(
                id=f"{provider.value[:3].upper()}{index:03d}",
                provider=provider.value,
                insurance_type=insurance_type,
                plan_name=plan_name,
                description=f"{insurance_type.value.title()} insurance from {provider.value}",
                coverage_amount=coverage,
                premium_monthly=premium if 'month' in coverage_text else premium / 12,
                premium_yearly=premium if 'year' in coverage_text or 'month' not in coverage_text else premium * 12,
                entry_age_min=18,
                entry_age_max=65,
                policy_term_min=1,
                policy_term_max=3,
                scraped_at=datetime.utcnow(),
                source_url=provider.value,
                is_active=True
            )

        except Exception as e:
            logger.warning(f"Plan parsing error: {e}")
            return None

    def _plan_to_dict(self, plan: InsurancePlan) -> dict:
        """Convert InsurancePlan to dictionary"""
        return {
            "id": plan.id,
            "provider": plan.provider,
            "insurance_type": plan.insurance_type.value,
            "plan_name": plan.plan_name,
            "description": plan.description,
            "coverage_amount": plan.coverage_amount,
            "premium_monthly": plan.premium_monthly,
            "premium_yearly": plan.premium_yearly,
            "entry_age_min": plan.entry_age_min,
            "entry_age_max": plan.entry_age_max,
            "policy_term_min": plan.policy_term_min,
            "policy_term_max": plan.policy_term_max,
            "waiting_period_days": plan.waiting_period_days,
            "coverage_details": plan.coverage_details,
            "benefits": plan.benefits,
            "exclusions": plan.exclusions,
            "network_hospitals": plan.network_hospitals,
            "claim_settlement_ratio": plan.claim_settlement_ratio,
            "renewal_bonus": plan.renewal_bonus,
            "tax_benefit_80d": plan.tax_benefit_80d,
            "cashless_facility": plan.cashless_facility,
            "maternity_cover": plan.maternity_cover,
            "dental_cover": plan.dental_cover,
            "vision_cover": plan.vision_cover,
            "mental_health_cover": plan.mental_health_cover,
            "rating": plan.rating,
            "reviews_count": plan.reviews_count,
            "scraped_at": plan.scraped_at.isoformat() if plan.scraped_at else None,
            "is_active": plan.is_active
        }

    async def get_recommended_plans(
        self,
        insurance_type: InsuranceType,
        customer_age: int,
        budget_monthly: float,
        required_coverage: float
    ) -> List[InsurancePlan]:
        """Get recommended plans based on customer profile"""
        
        all_plans = await self.scrape_insurance_plans(insurance_type)

        # Filter by age eligibility
        eligible_plans = [
            plan for plan in all_plans
            if plan.entry_age_min <= customer_age <= plan.entry_age_max
        ]

        # Filter by budget (with 20% buffer)
        budget_plans = [
            plan for plan in eligible_plans
            if plan.premium_monthly <= budget_monthly * 1.2
        ]

        # Filter by minimum coverage requirement
        coverage_plans = [
            plan for plan in budget_plans
            if plan.coverage_amount >= required_coverage * 0.8
        ]

        # Sort by rating and claim settlement ratio
        sorted_plans = sorted(
            coverage_plans,
            key=lambda p: (p.rating * 0.4 + (p.claim_settlement_ratio / 100) * 0.6),
            reverse=True
        )

        return sorted_plans[:5]  # Return top 5

    async def compare_plans(
        self,
        plan_ids: List[str],
        insurance_type: InsuranceType
    ) -> Dict[str, Any]:
        """Compare multiple insurance plans"""
        all_plans = await self.scrape_insurance_plans(insurance_type)

        selected_plans = [
            plan for plan in all_plans
            if plan.id in plan_ids
        ]

        comparison = {
            "plans": [self._plan_to_dict(plan) for plan in selected_plans],
            "comparison_matrix": {
                "coverage": {plan.id: plan.coverage_amount for plan in selected_plans},
                "premium_monthly": {plan.id: plan.premium_monthly for plan in selected_plans},
                "claim_settlement": {plan.id: plan.claim_settlement_ratio for plan in selected_plans},
                "network_hospitals": {plan.id: plan.network_hospitals for plan in selected_plans},
                "rating": {plan.id: plan.rating for plan in selected_plans},
            },
            "best_for_coverage": max(selected_plans, key=lambda p: p.coverage_amount).id if selected_plans else None,
            "best_for_premium": min(selected_plans, key=lambda p: p.premium_monthly).id if selected_plans else None,
            "best_for_claims": max(selected_plans, key=lambda p: p.claim_settlement_ratio).id if selected_plans else None,
            "generated_at": datetime.utcnow().isoformat()
        }

        return comparison


class InsuranceSalesIntegration:
    """Integrate insurance with property sales workflow"""

    def __init__(self):
        self.scraper = InsuranceScraper()

    async def generate_sale_insurance_quotes(
        self,
        sale_id: str,
        property_value: float,
        customer_id: str,
        customer_age: int
    ) -> List[InsuranceQuote]:
        """Generate insurance quotes for a property sale"""
        quotes = []

        # 1. Property/Home Insurance (mandatory for property sales)
        property_plans = await self.scraper.get_recommended_plans(
            InsuranceType.PROPERTY,
            customer_age=customer_age,
            budget_monthly=property_value * 0.0002,  # 0.02% of property value monthly
            required_coverage=property_value
        )

        for plan in property_plans[:3]:
            quote = InsuranceQuote(
                id=f"Q{datetime.utcnow().timestamp():.0f}{len(quotes)}",
                customer_id=customer_id,
                sale_id=sale_id,
                insurance_type=InsuranceType.PROPERTY,
                selected_plan_id=plan.id,
                coverage_amount=plan.coverage_amount,
                premium_amount=plan.premium_yearly,
                premium_frequency="yearly",
                commission_amount=plan.premium_yearly * 0.15,  # 15% commission
                status="quoted"
            )
            quotes.append(quote)

        # 2. Health Insurance (recommended)
        health_plans = await self.scraper.get_recommended_plans(
            InsuranceType.HEALTH,
            customer_age=customer_age,
            budget_monthly=2000,  # ₹2000/month budget
            required_coverage=5000000
        )

        for plan in health_plans[:2]:
            quote = InsuranceQuote(
                id=f"Q{datetime.utcnow().timestamp():.0f}{len(quotes)}",
                customer_id=customer_id,
                sale_id=sale_id,
                insurance_type=InsuranceType.HEALTH,
                selected_plan_id=plan.id,
                coverage_amount=plan.coverage_amount,
                premium_amount=plan.premium_yearly,
                premium_frequency="yearly",
                commission_amount=plan.premium_yearly * 0.10,  # 10% commission
                status="quoted"
            )
            quotes.append(quote)

        # 3. Life Insurance (optional)
        life_plans = await self.scraper.get_recommended_plans(
            InsuranceType.LIFE,
            customer_age=customer_age,
            budget_monthly=1500,  # ₹1500/month budget
            required_coverage=property_value * 2  # 2x property value
        )

        for plan in life_plans[:2]:
            quote = InsuranceQuote(
                id=f"Q{datetime.utcnow().timestamp():.0f}{len(quotes)}",
                customer_id=customer_id,
                sale_id=sale_id,
                insurance_type=InsuranceType.LIFE,
                selected_plan_id=plan.id,
                coverage_amount=plan.coverage_amount,
                premium_amount=plan.premium_yearly,
                premium_frequency="yearly",
                commission_amount=plan.premium_yearly * 0.20,  # 20% commission
                status="quoted"
            )
            quotes.append(quote)

        structured_logger.info(
            "Insurance quotes generated for sale",
            {
                "sale_id": sale_id,
                "quotes_count": len(quotes),
                "customer_id": customer_id
            }
        )

        return quotes

    async def save_quote_to_database(
        self,
        quote: InsuranceQuote,
        database
    ) -> bool:
        """Save insurance quote to database"""
        try:
            quote_doc = {
                "id": quote.id,
                "customer_id": quote.customer_id,
                "property_id": quote.property_id,
                "sale_id": quote.sale_id,
                "insurance_type": quote.insurance_type.value,
                "selected_plan_id": quote.selected_plan_id,
                "coverage_amount": quote.coverage_amount,
                "premium_amount": quote.premium_amount,
                "premium_frequency": quote.premium_frequency,
                "start_date": quote.start_date,
                "end_date": quote.end_date,
                "status": quote.status,
                "beneficiaries": quote.beneficiaries,
                "nominee_details": quote.nominee_details,
                "commission_amount": quote.commission_amount,
                "created_at": quote.created_at,
                "updated_at": quote.updated_at
            }

            await database.insurance_quotes.insert_one(quote_doc)

            structured_logger.info(
                "Insurance quote saved",
                {"quote_id": quote.id, "sale_id": quote.sale_id}
            )

            return True

        except Exception as e:
            logger.error(f"Failed to save quote: {e}")
            return False

    async def get_sale_insurance_summary(
        self,
        sale_id: str,
        database
    ) -> Dict[str, Any]:
        """Get insurance summary for a sale"""
        try:
            quotes = await database.insurance_quotes.find(
                {"sale_id": sale_id}
            ).to_list(length=None)

            total_commission = sum(q.get("commission_amount", 0) for q in quotes)
            total_premium = sum(q.get("premium_amount", 0) for q in quotes)

            by_type = {}
            for q in quotes:
                t = q.get("insurance_type", "unknown")
                if t not in by_type:
                    by_type[t] = {"count": 0, "premium": 0, "commission": 0}
                by_type[t]["count"] += 1
                by_type[t]["premium"] += q.get("premium_amount", 0)
                by_type[t]["commission"] += q.get("commission_amount", 0)

            return {
                "sale_id": sale_id,
                "total_quotes": len(quotes),
                "total_premium": total_premium,
                "total_commission": total_commission,
                "by_type": by_type,
                "quotes": quotes
            }

        except Exception as e:
            logger.error(f"Insurance summary error: {e}")
            return {"error": str(e)}


# Global instances
insurance_scraper = InsuranceScraper()
insurance_integration = InsuranceSalesIntegration()
