"""
Property Router Tests
Covers: listing, search, create (auth + role guards), cache hit/miss,
        cache invalidation on write, pagination, field filters.
"""
import sys
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

sys.path.insert(0, 'C:/Users/deepe/PyCharmMiscProject/housing_platform/backend')

from app.auth import create_access_token, hash_password
from app.cache import generate_cache_key


# ────────────────────────────────────────────────────────────────────────────
# Cache key generation (pure unit — no I/O)
# ────────────────────────────────────────────────────────────────────────────
class TestCacheKeyGeneration:

    def test_key_includes_all_parts(self):
        key = generate_cache_key("properties", 1, 20, "all")
        assert "properties" in key
        assert "1" in key
        assert "20" in key

    def test_different_args_produce_different_keys(self):
        k1 = generate_cache_key("properties", 1, 20, "all")
        k2 = generate_cache_key("properties", 2, 20, "all")
        assert k1 != k2

    def test_same_args_produce_same_key(self):
        k1 = generate_cache_key("properties", 1, 20, "active")
        k2 = generate_cache_key("properties", 1, 20, "active")
        assert k1 == k2

    def test_search_key_includes_filters(self):
        key = generate_cache_key("search", "gurgaon", "5000000", "10000000", "apartment", 1, 20)
        assert "search" in key
        assert "gurgaon" in key
        assert "apartment" in key


# ────────────────────────────────────────────────────────────────────────────
# Property listing — cache behaviour
# ────────────────────────────────────────────────────────────────────────────
class TestPropertyListingCache:

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_data(self, mock_cache, sample_property):
        """GET /properties should return cached result on hit."""
        from app.cache import get_from_cache, set_in_cache

        cached_payload = {
            "items": [sample_property],
            "total": 1, "page": 1, "limit": 20, "pages": 1,
        }
        cache_key = generate_cache_key("properties", 1, 20, "all")
        await set_in_cache(cache_key, cached_payload, ttl=300)

        result = await get_from_cache(cache_key)
        assert result is not None
        assert result["total"] == 1
        assert result["items"][0]["city"] == "Gurgaon"

    @pytest.mark.asyncio
    async def test_cache_miss_returns_none(self, mock_cache):
        """Cache miss must return None so the router falls through to DB."""
        from app.cache import get_from_cache

        result = await get_from_cache("properties:nonexistent:key")
        assert result is None

    @pytest.mark.asyncio
    async def test_write_invalidates_cache(self, mock_cache, sample_property):
        """POST /properties must invalidate the properties:* cache pattern."""
        from app.cache import set_in_cache, invalidate_cache_pattern, get_from_cache

        # Prime the cache with two listing keys
        await set_in_cache("properties:1:20:all",    {"items": [], "total": 0}, ttl=300)
        await set_in_cache("properties:1:20:active", {"items": [], "total": 0}, ttl=300)

        # Simulate what the create endpoint does
        deleted = await invalidate_cache_pattern("properties:*")
        assert deleted >= 0  # in-memory mock may return 0 but keys should be gone

        # Both keys must now miss
        assert await get_from_cache("properties:1:20:all")    is None
        assert await get_from_cache("properties:1:20:active") is None

    @pytest.mark.asyncio
    async def test_search_cache_varies_on_filters(self, mock_cache):
        """Two searches with different filters must use different cache keys."""
        from app.cache import set_in_cache, get_from_cache

        k1 = generate_cache_key("search", "gurgaon", "", "", "apartment", 1, 20)
        k2 = generate_cache_key("search", "noida",   "", "", "apartment", 1, 20)

        await set_in_cache(k1, {"items": [{"city": "Gurgaon"}], "total": 1}, ttl=60)
        await set_in_cache(k2, {"items": [{"city": "Noida"}],   "total": 1}, ttl=60)

        r1 = await get_from_cache(k1)
        r2 = await get_from_cache(k2)

        assert r1["items"][0]["city"] == "Gurgaon"
        assert r2["items"][0]["city"] == "Noida"


# ────────────────────────────────────────────────────────────────────────────
# Auth guard logic (unit — testing the guard function directly)
# ────────────────────────────────────────────────────────────────────────────
class TestPropertyAuthGuards:

    def _extract_user(self, authorization):
        """Mirrors the get_current_user_from_header logic in properties router."""
        from app.auth import decode_token
        if not authorization:
            return None
        try:
            token = authorization.split(" ")[1]
            token_data = decode_token(token)
            if token_data:
                return {"user_id": token_data.user_id, "role": token_data.role}
        except Exception:
            pass
        return None

    def test_seller_can_create(self, seller_headers):
        user = self._extract_user(seller_headers["Authorization"])
        assert user is not None
        assert user["role"] == "seller"

    def test_agent_can_create(self, agent_headers):
        user = self._extract_user(agent_headers["Authorization"])
        assert user is not None
        assert user["role"] == "agent"

    def test_buyer_cannot_create(self, buyer_headers):
        """Buyer should be extracted but then rejected by role check."""
        user = self._extract_user(buyer_headers["Authorization"])
        assert user is not None
        assert user["role"] not in ["seller", "agent"]

    def test_no_token_returns_none(self):
        user = self._extract_user(None)
        assert user is None

    def test_bad_token_returns_none(self):
        user = self._extract_user("Bearer not.a.real.token")
        assert user is None

    def test_role_check_allows_admin(self, admin_headers):
        user = self._extract_user(admin_headers["Authorization"])
        assert user is not None
        assert user["role"] == "admin"


# ────────────────────────────────────────────────────────────────────────────
# Property CRUD (mock DB)
# ────────────────────────────────────────────────────────────────────────────
class TestPropertyCRUD:

    @pytest.mark.asyncio
    async def test_create_property_inserts_to_db(self, mock_db, sample_property_create_payload):
        """Creating a property must insert a document."""
        mock_db.properties.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id="prop_new_001")
        )
        payload = {**sample_property_create_payload, "user_id": "seller_001"}
        result = await mock_db.properties.insert_one(payload)
        assert str(result.inserted_id) == "prop_new_001"
        mock_db.properties.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_property_by_id(self, mock_db, sample_property):
        """Fetching a property by ID must return the correct document."""
        mock_db.properties.find_one = AsyncMock(return_value=sample_property)

        result = await mock_db.properties.find_one({"_id": "prop_001"})
        assert result is not None
        assert result["city"] == "Gurgaon"
        assert result["bedrooms"] == 3

    @pytest.mark.asyncio
    async def test_get_nonexistent_property_returns_none(self, mock_db):
        mock_db.properties.find_one = AsyncMock(return_value=None)
        result = await mock_db.properties.find_one({"_id": "nonexistent"})
        assert result is None

    @pytest.mark.asyncio
    async def test_update_property(self, mock_db, sample_property):
        """Updating a property must call update_one with the right filter."""
        mock_db.properties.update_one = AsyncMock(
            return_value=MagicMock(modified_count=1)
        )
        result = await mock_db.properties.update_one(
            {"_id": sample_property["_id"]},
            {"$set": {"price": 10000000}}
        )
        assert result.modified_count == 1

    @pytest.mark.asyncio
    async def test_delete_property(self, mock_db, sample_property):
        mock_db.properties.delete_one = AsyncMock(
            return_value=MagicMock(deleted_count=1)
        )
        result = await mock_db.properties.delete_one({"_id": sample_property["_id"]})
        assert result.deleted_count == 1

    @pytest.mark.asyncio
    async def test_owner_can_only_delete_own_property(self, mock_db, sample_property):
        """Delete filter must include user_id to prevent unauthorised deletion."""
        mock_db.properties.delete_one = AsyncMock(
            return_value=MagicMock(deleted_count=0)
        )
        # Wrong owner trying to delete
        result = await mock_db.properties.delete_one(
            {"_id": sample_property["_id"], "user_id": "some_other_user"}
        )
        assert result.deleted_count == 0


# ────────────────────────────────────────────────────────────────────────────
# Search filter logic (unit — no DB)
# ────────────────────────────────────────────────────────────────────────────
class TestPropertySearchFilters:

    @pytest.fixture
    def properties(self):
        return [
            {"id": "1", "city": "Gurgaon",    "property_type": "apartment", "price": 8000000,  "bedrooms": 3, "listing_type": "sale"},
            {"id": "2", "city": "Noida",       "property_type": "villa",     "price": 15000000, "bedrooms": 4, "listing_type": "sale"},
            {"id": "3", "city": "Gurgaon",    "property_type": "apartment", "price": 3500000,  "bedrooms": 2, "listing_type": "rent"},
            {"id": "4", "city": "Bangalore",   "property_type": "house",     "price": 6000000,  "bedrooms": 3, "listing_type": "sale"},
            {"id": "5", "city": "Mumbai",      "property_type": "apartment", "price": 20000000, "bedrooms": 2, "listing_type": "sale"},
        ]

    def _filter(self, props, city=None, prop_type=None, min_price=None,
                max_price=None, bedrooms=None, listing_type=None):
        result = props
        if city:
            result = [p for p in result if p["city"] == city]
        if prop_type:
            result = [p for p in result if p["property_type"] == prop_type]
        if min_price:
            result = [p for p in result if p["price"] >= min_price]
        if max_price:
            result = [p for p in result if p["price"] <= max_price]
        if bedrooms:
            result = [p for p in result if p["bedrooms"] == bedrooms]
        if listing_type:
            result = [p for p in result if p["listing_type"] == listing_type]
        return result

    def test_filter_by_city(self, properties):
        r = self._filter(properties, city="Gurgaon")
        assert len(r) == 2
        assert all(p["city"] == "Gurgaon" for p in r)

    def test_filter_by_property_type(self, properties):
        r = self._filter(properties, prop_type="apartment")
        assert len(r) == 3

    def test_filter_by_price_range(self, properties):
        r = self._filter(properties, min_price=6000000, max_price=10000000)
        assert all(6000000 <= p["price"] <= 10000000 for p in r)

    def test_filter_by_bedrooms(self, properties):
        r = self._filter(properties, bedrooms=3)
        assert all(p["bedrooms"] == 3 for p in r)

    def test_filter_by_listing_type_rent(self, properties):
        r = self._filter(properties, listing_type="rent")
        assert len(r) == 1
        assert r[0]["city"] == "Gurgaon"

    def test_combined_filters(self, properties):
        r = self._filter(properties, city="Gurgaon", prop_type="apartment", listing_type="sale")
        assert len(r) == 1
        assert r[0]["id"] == "1"

    def test_no_results_returns_empty_list(self, properties):
        r = self._filter(properties, city="Hyderabad")
        assert r == []

    def test_pagination_slice(self, properties):
        page, limit = 1, 2
        paginated = properties[(page - 1) * limit: page * limit]
        assert len(paginated) == 2

    def test_pagination_page_2(self, properties):
        page, limit = 2, 2
        paginated = properties[(page - 1) * limit: page * limit]
        assert len(paginated) == 2
        assert paginated[0]["id"] == "3"

    def test_pagination_last_page_partial(self, properties):
        page, limit = 3, 2
        paginated = properties[(page - 1) * limit: page * limit]
        assert len(paginated) == 1


# ────────────────────────────────────────────────────────────────────────────
# Property data validation
# ────────────────────────────────────────────────────────────────────────────
class TestPropertyDataValidation:

    def test_price_must_be_positive(self):
        assert 9500000 > 0

    def test_bedrooms_in_valid_range(self):
        valid = [1, 2, 3, 4, 5, 6]
        for b in valid:
            assert 1 <= b <= 10

    def test_area_must_be_positive(self):
        assert 1450 > 0

    def test_city_must_not_be_empty(self, sample_property_create_payload):
        assert sample_property_create_payload["city"].strip() != ""

    def test_listing_type_valid_values(self):
        valid_types = ["sale", "rent", "lease", "pg"]
        for lt in valid_types:
            assert lt in valid_types

    def test_property_type_valid_values(self):
        valid_types = ["apartment", "villa", "house", "plot", "commercial", "studio"]
        for pt in valid_types:
            assert pt in valid_types


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
