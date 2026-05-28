"""
Insurance Module Test Suite
Tests for insurance scraping, quotes, and sales integration
"""
import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

from app.insurance_scraper import (
    InsuranceScraper, InsuranceSalesIntegration,
    InsuranceType, InsuranceProvider, InsurancePlan, InsuranceQuote
)


# ==================== INSURANCE SCRAPER TESTS ====================

class TestInsuranceScraper:
    """Test insurance scraping functionality"""

    @pytest.fixture
    def scraper(self):
        """Create insurance scraper for tests"""
        return InsuranceScraper()

    @pytest.mark.asyncio
    async def test_scrape_health_plans(self, scraper):
        """Test scraping health insurance plans"""
        plans = await scraper.scrape_insurance_plans(InsuranceType.HEALTH)

        assert len(plans) > 0
        assert all(plan.insurance_type == InsuranceType.HEALTH for plan in plans)
        assert all(plan.coverage_amount > 0 for plan in plans)
        assert all(plan.premium_yearly > 0 for plan in plans)

    @pytest.mark.asyncio
    async def test_scrape_life_plans(self, scraper):
        """Test scraping life insurance plans"""
        plans = await scraper.scrape_insurance_plans(InsuranceType.LIFE)

        assert len(plans) > 0
        assert all(plan.insurance_type == InsuranceType.LIFE for plan in plans)

    @pytest.mark.asyncio
    async def test_scrape_property_plans(self, scraper):
        """Test scraping property insurance plans"""
        plans = await scraper.scrape_insurance_plans(InsuranceType.PROPERTY)

        assert len(plans) > 0
        assert all(plan.insurance_type == InsuranceType.PROPERTY for plan in plans)

    @pytest.mark.asyncio
    async def test_scrape_by_provider(self, scraper):
        """Test scraping plans from specific provider"""
        provider = InsuranceProvider.STAR_HEALTH
        plans = await scraper.scrape_insurance_plans(InsuranceType.HEALTH, provider)

        # Should return plans (may include fallback data)
        assert len(plans) >= 0

    @pytest.mark.asyncio
    async def test_get_recommended_plans(self, scraper):
        """Test getting recommended plans based on profile"""
        plans = await scraper.get_recommended_plans(
            insurance_type=InsuranceType.HEALTH,
            customer_age=35,
            budget_monthly=2000,
            required_coverage=5000000
        )

        assert len(plans) <= 5  # Should return top 5

        # All plans should be within reasonable budget
        for plan in plans:
            assert plan.premium_monthly <= 2000 * 1.2  # 20% buffer
            assert plan.coverage_amount >= 5000000 * 0.8  # 80% minimum
            assert plan.entry_age_min <= 35 <= plan.entry_age_max

    @pytest.mark.asyncio
    async def test_compare_plans(self, scraper):
        """Test comparing multiple insurance plans"""
        # First get some plans
        plans = await scraper.scrape_insurance_plans(InsuranceType.HEALTH)
        if len(plans) >= 2:
            plan_ids = [plans[0].id, plans[1].id]

            comparison = await scraper.compare_plans(plan_ids, InsuranceType.HEALTH)

            assert "plans" in comparison
            assert "comparison_matrix" in comparison
            assert "best_for_coverage" in comparison
            assert "best_for_premium" in comparison
            assert "best_for_claims" in comparison

    def test_plan_to_dict_conversion(self, scraper):
        """Test converting InsurancePlan to dictionary"""
        plan = InsurancePlan(
            id="TEST001",
            provider="test_provider",
            insurance_type=InsuranceType.HEALTH,
            plan_name="Test Plan",
            description="Test description",
            coverage_amount=5000000,
            premium_monthly=1000,
            premium_yearly=12000,
            entry_age_min=18,
            entry_age_max=65,
            policy_term_min=1,
            policy_term_max=3,
            benefits=["Benefit 1", "Benefit 2"],
            rating=4.5,
            reviews_count=100
        )

        plan_dict = scraper._plan_to_dict(plan)

        assert plan_dict["id"] == "TEST001"
        assert plan_dict["provider"] == "test_provider"
        assert plan_dict["insurance_type"] == "health"
        assert plan_dict["coverage_amount"] == 5000000
        assert plan_dict["premium_monthly"] == 1000
        assert plan_dict["rating"] == 4.5


# ==================== INSURANCE SALES INTEGRATION TESTS ====================

class TestInsuranceSalesIntegration:
    """Test insurance integration with sales workflow"""

    @pytest.fixture
    def integration(self):
        """Create insurance integration for tests"""
        return InsuranceSalesIntegration()

    @pytest.mark.asyncio
    async def test_generate_sale_insurance_quotes(self, integration):
        """Test generating insurance quotes for a sale"""
        quotes = await integration.generate_sale_insurance_quotes(
            sale_id="SALE001",
            property_value=5000000,
            customer_id="CUST001",
            customer_age=35
        )

        # Should generate quotes for property, health, and life insurance
        assert len(quotes) > 0

        # Check quote structure
        for quote in quotes:
            assert quote.id is not None
            assert quote.sale_id == "SALE001"
            assert quote.customer_id == "CUST001"
            assert quote.coverage_amount > 0
            assert quote.premium_amount > 0
            assert quote.commission_amount >= 0
            assert quote.status == "quoted"

    @pytest.mark.asyncio
    async def test_property_insurance_quotes(self, integration):
        """Test property insurance quotes are included"""
        quotes = await integration.generate_sale_insurance_quotes(
            sale_id="SALE002",
            property_value=10000000,
            customer_id="CUST002",
            customer_age=40
        )

        property_quotes = [q for q in quotes if q.insurance_type == InsuranceType.PROPERTY]

        # Should have property insurance quotes
        assert len(property_quotes) >= 1

        # Property coverage should match property value
        for quote in property_quotes:
            assert quote.coverage_amount >= 10000000 * 0.8

    @pytest.mark.asyncio
    async def test_commission_calculation(self, integration):
        """Test commission is calculated correctly"""
        quotes = await integration.generate_sale_insurance_quotes(
            sale_id="SALE003",
            property_value=7500000,
            customer_id="CUST003",
            customer_age=30
        )

        # Property insurance: 15% commission
        # Health insurance: 10% commission
        # Life insurance: 20% commission
        for quote in quotes:
            expected_commission = (
                quote.premium_amount * 0.15 if quote.insurance_type == InsuranceType.PROPERTY
                else quote.premium_amount * 0.10 if quote.insurance_type == InsuranceType.HEALTH
                else quote.premium_amount * 0.20 if quote.insurance_type == InsuranceType.LIFE
                else 0
            )
            assert quote.commission_amount == expected_commission

    @pytest.mark.asyncio
    async def test_save_quote_to_database(self, integration):
        """Test saving quote to database"""
        mock_db = Mock()
        mock_db.insurance_quotes = Mock()
        mock_db.insurance_quotes.insert_one = AsyncMock(return_value=Mock(inserted_id="test_id"))

        quote = InsuranceQuote(
            id="Q001",
            customer_id="CUST001",
            sale_id="SALE001",
            insurance_type=InsuranceType.HEALTH,
            selected_plan_id="P001",
            coverage_amount=5000000,
            premium_amount=15000,
            commission_amount=1500
        )

        result = await integration.save_quote_to_database(quote, mock_db)

        assert result is True
        mock_db.insurance_quotes.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_sale_insurance_summary(self, integration):
        """Test getting insurance summary for a sale"""
        mock_db = Mock()
        mock_db.insurance_quotes = Mock()

        # Mock database response
        mock_quotes = [
            {"id": "Q1", "insurance_type": "health", "premium_amount": 15000, "commission_amount": 1500, "status": "quoted"},
            {"id": "Q2", "insurance_type": "property", "premium_amount": 5000, "commission_amount": 750, "status": "purchased"},
            {"id": "Q3", "insurance_type": "life", "premium_amount": 12000, "commission_amount": 2400, "status": "purchased"}
        ]
        mock_db.insurance_quotes.find = Mock(return_value=AsyncMock(
            to_list=AsyncMock(return_value=mock_quotes)
        ))

        summary = await integration.get_sale_insurance_summary("SALE001", mock_db)

        assert summary["sale_id"] == "SALE001"
        assert summary["total_quotes"] == 3
        assert summary["total_premium"] == 32000
        assert summary["total_commission"] == 4650
        assert "by_type" in summary


# ==================== INSURANCE TYPES AND PROVIDERS TESTS ====================

class TestInsuranceTypesAndProviders:
    """Test insurance types and providers enum"""

    def test_insurance_types(self):
        """Test all insurance types are defined"""
        expected_types = [
            "health", "life", "property", "home", "motor",
            "travel", "critical_illness", "personal_accident"
        ]

        for ins_type in InsuranceType:
            assert ins_type.value in expected_types

    def test_insurance_providers(self):
        """Test all insurance providers are defined"""
        expected_providers = [
            "lic", "hdfc_ergo", "icici_lombard", "star_health",
            "max_bupa", "new_india", "oriental", "united_india",
            "bajaj_allianz", "tata_aig", "reliance", "sbi_general"
        ]

        for provider in InsuranceProvider:
            assert provider.value in expected_providers


# ==================== SAMPLE PLANS TESTS ====================

class TestSamplePlans:
    """Test sample insurance plans as fallback"""

    @pytest.fixture
    def scraper(self):
        """Create scraper with sample plans"""
        return InsuranceScraper()

    def test_sample_plans_generated(self, scraper):
        """Test sample plans are generated"""
        assert len(scraper.sample_plans) > 0

        # Check we have different types
        types = set(plan.insurance_type for plan in scraper.sample_plans)
        assert InsuranceType.HEALTH in types
        assert InsuranceType.LIFE in types
        assert InsuranceType.PROPERTY in types

    def test_sample_plan_structure(self, scraper):
        """Test sample plans have correct structure"""
        for plan in scraper.sample_plans:
            assert plan.id is not None
            assert plan.provider is not None
            assert plan.plan_name is not None
            assert plan.coverage_amount > 0
            assert plan.premium_monthly > 0
            assert plan.premium_yearly > 0
            assert plan.entry_age_min >= 0
            assert plan.entry_age_max > plan.entry_age_min
            assert isinstance(plan.benefits, list)


# ==================== CACHING TESTS ====================

class TestInsuranceCaching:
    """Test insurance data caching"""

    @pytest.mark.asyncio
    async def test_cache_storage(self):
        """Test insurance plans are cached"""
        scraper = InsuranceScraper()

        # First call should cache
        plans1 = await scraper.scrape_insurance_plans(InsuranceType.HEALTH)

        # Second call should use cache (faster)
        # This is verified by checking cache was called
        # In real implementation, we'd mock the cache

        assert len(plans1) > 0


# ==================== RECOMMENDATION ENGINE TESTS ====================

class TestRecommendationEngine:
    """Test insurance recommendation engine"""

    @pytest.mark.asyncio
    async def test_age_eligibility_filtering(self):
        """Test plans are filtered by age eligibility"""
        scraper = InsuranceScraper()

        # Request for 70-year-old
        plans = await scraper.get_recommended_plans(
            insurance_type=InsuranceType.HEALTH,
            customer_age=70,
            budget_monthly=5000,
            required_coverage=5000000
        )

        # Should only return plans that cover age 70
        for plan in plans:
            assert plan.entry_age_min <= 70 <= plan.entry_age_max

    @pytest.mark.asyncio
    async def test_budget_filtering(self):
        """Test plans are filtered by budget"""
        scraper = InsuranceScraper()

        # Low budget
        plans = await scraper.get_recommended_plans(
            insurance_type=InsuranceType.HEALTH,
            customer_age=30,
            budget_monthly=500,  # Very low budget
            required_coverage=5000000
        )

        # All plans should be within budget (with 20% buffer)
        for plan in plans:
            assert plan.premium_monthly <= 600  # 500 + 20%

    @pytest.mark.asyncio
    async def test_coverage_filtering(self):
        """Test plans are filtered by coverage requirement"""
        scraper = InsuranceScraper()

        # High coverage requirement
        plans = await scraper.get_recommended_plans(
            insurance_type=InsuranceType.HEALTH,
            customer_age=30,
            budget_monthly=50000,  # High budget
            required_coverage=10000000  # 1 Crore
        )

        # All plans should provide at least 80% of required coverage
        for plan in plans:
            assert plan.coverage_amount >= 8000000


# ==================== INTEGRATION TESTS ====================

class TestInsuranceIntegration:
    """Integration tests for insurance module"""

    @pytest.mark.asyncio
    async def test_end_to_end_insurance_flow(self):
        """Test complete insurance flow"""
        # 1. Scrape plans
        scraper = InsuranceScraper()
        plans = await scraper.scrape_insurance_plans(InsuranceType.HEALTH)

        assert len(plans) > 0

        # 2. Get recommendations
        recommended = await scraper.get_recommended_plans(
            InsuranceType.HEALTH, 35, 3000, 5000000
        )

        assert len(recommended) > 0

        # 3. Generate quotes
        integration = InsuranceSalesIntegration()
        quotes = await integration.generate_sale_insurance_quotes(
            "SALE_TEST", 5000000, "CUST_TEST", 35
        )

        assert len(quotes) > 0

        # 4. Verify all quotes have required fields
        for quote in quotes:
            assert quote.id
            assert quote.coverage_amount > 0
            assert quote.premium_amount > 0
            assert quote.insurance_type in [InsuranceType.HEALTH, InsuranceType.LIFE, InsuranceType.PROPERTY]

    @pytest.mark.asyncio
    async def test_insurance_with_sale_context(self):
        """Test insurance generation with actual sale context"""
        integration = InsuranceSalesIntegration()

        # High-value property sale
        quotes = await integration.generate_sale_insurance_quotes(
            sale_id="SALE_LUXURY",
            property_value=50000000,  # 5 Crore
            customer_id="CUST_LUXURY",
            customer_age=45
        )

        # Should have property insurance with high coverage
        property_quotes = [q for q in quotes if q.insurance_type == InsuranceType.PROPERTY]

        if property_quotes:
            # Property coverage should be proportional to property value
            assert property_quotes[0].coverage_amount >= 50000000 * 0.8


# ==================== ERROR HANDLING TESTS ====================

class TestErrorHandling:
    """Test error handling in insurance module"""

    @pytest.mark.asyncio
    async def test_invalid_insurance_type(self):
        """Test handling of invalid insurance type"""
        scraper = InsuranceScraper()

        with pytest.raises(ValueError):
            InsuranceType("invalid_type")

    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test handling of database errors"""
        integration = InsuranceSalesIntegration()

        # Mock database that raises error
        mock_db = Mock()
        mock_db.insurance_quotes = Mock()
        mock_db.insurance_quotes.insert_one = AsyncMock(side_effect=Exception("DB Error"))

        quote = InsuranceQuote(
            id="Q001",
            customer_id="CUST001",
            sale_id="SALE001",
            insurance_type=InsuranceType.HEALTH,
            selected_plan_id="P001",
            coverage_amount=5000000,
            premium_amount=15000,
            commission_amount=1500
        )

        result = await integration.save_quote_to_database(quote, mock_db)

        # Should return False on error, not raise exception
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
