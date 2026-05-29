"""
Cache Layer Tests
Covers: get/set/delete, TTL, pattern invalidation,
        Redis-down fallback, key generation, concurrent writes, cache warming.
"""
import sys
import json
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, 'C:/Users/deepe/PyCharmMiscProject/housing_platform/backend')

from app.cache import (
    get_from_cache,
    set_in_cache,
    delete_from_cache,
    invalidate_cache_pattern,
    generate_cache_key,
    get_cache,
    set_cache,
)


# ────────────────────────────────────────────────────────────────────────────
# get / set / delete
# ────────────────────────────────────────────────────────────────────────────
class TestCacheGetSet:

    @pytest.mark.asyncio
    async def test_set_and_get_string(self, mock_cache):
        await set_in_cache("key:str", "hello world", ttl=60)
        result = await get_from_cache("key:str")
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_set_and_get_dict(self, mock_cache):
        data = {"city": "Gurgaon", "price": 9500000, "bedrooms": 3}
        await set_in_cache("key:dict", data, ttl=60)
        result = await get_from_cache("key:dict")
        assert result == data

    @pytest.mark.asyncio
    async def test_set_and_get_list(self, mock_cache):
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        await set_in_cache("key:list", data, ttl=60)
        result = await get_from_cache("key:list")
        assert result == data

    @pytest.mark.asyncio
    async def test_get_nonexistent_key_returns_none(self, mock_cache):
        result = await get_from_cache("key:does:not:exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_removes_key(self, mock_cache):
        await set_in_cache("key:to:delete", {"val": 1}, ttl=60)
        await delete_from_cache("key:to:delete")
        result = await get_from_cache("key:to:delete")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key_is_safe(self, mock_cache):
        """Deleting a non-existent key must not raise."""
        result = await delete_from_cache("key:phantom")
        # Should return False or True — just must not throw
        assert result in (True, False)

    @pytest.mark.asyncio
    async def test_overwrite_existing_key(self, mock_cache):
        await set_in_cache("key:overwrite", {"v": 1}, ttl=60)
        await set_in_cache("key:overwrite", {"v": 2}, ttl=60)
        result = await get_from_cache("key:overwrite")
        assert result["v"] == 2

    @pytest.mark.asyncio
    async def test_alias_get_cache_works(self, mock_cache):
        await set_cache("alias:key", "aliased", ttl=60)
        result = await get_cache("alias:key")
        assert result == "aliased"

    @pytest.mark.asyncio
    async def test_nested_dict_preserved(self, mock_cache):
        data = {"user": {"id": "u1", "meta": {"score": 42}}}
        await set_in_cache("key:nested", data, ttl=60)
        result = await get_from_cache("key:nested")
        assert result["user"]["meta"]["score"] == 42

    @pytest.mark.asyncio
    async def test_unicode_value_preserved(self, mock_cache):
        data = {"title": "3BHK मकान गुरुग्राम में"}
        await set_in_cache("key:unicode", data, ttl=60)
        result = await get_from_cache("key:unicode")
        assert result["title"] == data["title"]


# ────────────────────────────────────────────────────────────────────────────
# Pattern invalidation
# ────────────────────────────────────────────────────────────────────────────
class TestCachePatternInvalidation:

    @pytest.mark.asyncio
    async def test_invalidate_matching_keys(self, mock_cache):
        await set_in_cache("properties:1:20:all",    {"items": []}, ttl=60)
        await set_in_cache("properties:2:20:all",    {"items": []}, ttl=60)
        await set_in_cache("properties:1:20:active", {"items": []}, ttl=60)
        await set_in_cache("users:profile:u1",       {"name": "X"}, ttl=60)

        await invalidate_cache_pattern("properties:*")

        assert await get_from_cache("properties:1:20:all")    is None
        assert await get_from_cache("properties:2:20:all")    is None
        assert await get_from_cache("properties:1:20:active") is None
        # unrelated key must survive
        assert await get_from_cache("users:profile:u1") is not None

    @pytest.mark.asyncio
    async def test_invalidate_user_pattern(self, mock_cache):
        await set_in_cache("user:u1:profile",   {"email": "a@b.com"}, ttl=60)
        await set_in_cache("user:u1:wishlist",  {"items": []},        ttl=60)
        await set_in_cache("properties:list",   {"items": []},        ttl=60)

        await invalidate_cache_pattern("user:u1:*")

        assert await get_from_cache("user:u1:profile")  is None
        assert await get_from_cache("user:u1:wishlist") is None
        assert await get_from_cache("properties:list")  is not None

    @pytest.mark.asyncio
    async def test_invalidate_empty_pattern_is_safe(self, mock_cache):
        await set_in_cache("safe:key", {"v": 1}, ttl=60)
        await invalidate_cache_pattern("nomatch:*")
        assert await get_from_cache("safe:key") is not None

    @pytest.mark.asyncio
    async def test_invalidate_all_pattern(self, mock_cache):
        for i in range(5):
            await set_in_cache(f"key:{i}", {"i": i}, ttl=60)
        await invalidate_cache_pattern("key:*")
        for i in range(5):
            assert await get_from_cache(f"key:{i}") is None


# ────────────────────────────────────────────────────────────────────────────
# Redis-down fallback (cache=None scenario)
# ────────────────────────────────────────────────────────────────────────────
class TestCacheFallback:

    @pytest.mark.asyncio
    async def test_get_returns_none_when_cache_unavailable(self):
        with patch('app.cache.cache', None):
            result = await get_from_cache("any:key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_returns_false_when_cache_unavailable(self):
        with patch('app.cache.cache', None):
            result = await set_in_cache("any:key", {"v": 1}, ttl=60)
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_cache_unavailable(self):
        with patch('app.cache.cache', None):
            result = await delete_from_cache("any:key")
        assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_returns_zero_when_cache_unavailable(self):
        with patch('app.cache.cache', None):
            result = await invalidate_cache_pattern("any:*")
        assert result == 0

    @pytest.mark.asyncio
    async def test_redis_exception_returns_none(self):
        """Simulate Redis throwing an exception on get."""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis connection refused"))
        with patch('app.cache.cache', mock_redis):
            result = await get_from_cache("key:error")
        assert result is None

    @pytest.mark.asyncio
    async def test_redis_exception_on_set_returns_false(self):
        mock_redis = MagicMock()
        mock_redis.setex = AsyncMock(side_effect=Exception("Redis connection refused"))
        with patch('app.cache.cache', mock_redis):
            result = await set_in_cache("key:error", {"v": 1})
        assert result is False


# ────────────────────────────────────────────────────────────────────────────
# Cache key generation
# ────────────────────────────────────────────────────────────────────────────
class TestCacheKeyGeneration:

    def test_single_arg(self):
        key = generate_cache_key("properties")
        assert key == "properties"

    def test_multiple_args_joined(self):
        key = generate_cache_key("properties", 1, 20, "all")
        parts = key.split(":")
        assert parts[0] == "properties"
        assert "1" in parts
        assert "20" in parts
        assert "all" in parts

    def test_none_arg_included_as_none(self):
        key = generate_cache_key("search", None, "active")
        assert "None" in key

    def test_different_page_produces_different_key(self):
        k1 = generate_cache_key("props", 1, 20)
        k2 = generate_cache_key("props", 2, 20)
        assert k1 != k2

    def test_key_is_string(self):
        key = generate_cache_key("a", "b", 1)
        assert isinstance(key, str)

    def test_user_scoped_key(self):
        key = generate_cache_key("user", "uid_001", "profile")
        assert "uid_001" in key
        assert "profile" in key

    def test_empty_args(self):
        key = generate_cache_key()
        assert key == ""

    def test_special_chars_in_args(self):
        key = generate_cache_key("search", "gurgaon:sector-56", "apartment")
        assert "gurgaon:sector-56" in key


# ────────────────────────────────────────────────────────────────────────────
# Concurrent cache operations
# ────────────────────────────────────────────────────────────────────────────
class TestConcurrentCacheOps:

    @pytest.mark.asyncio
    async def test_concurrent_writes_do_not_corrupt(self, mock_cache):
        """Multiple concurrent writes to different keys must all succeed."""
        async def write(i):
            await set_in_cache(f"concurrent:{i}", {"val": i}, ttl=60)

        await asyncio.gather(*[write(i) for i in range(20)])

        for i in range(20):
            result = await get_from_cache(f"concurrent:{i}")
            assert result is not None
            assert result["val"] == i

    @pytest.mark.asyncio
    async def test_concurrent_reads_return_same_value(self, mock_cache):
        await set_in_cache("shared:key", {"shared": True}, ttl=60)

        async def read():
            return await get_from_cache("shared:key")

        results = await asyncio.gather(*[read() for _ in range(10)])
        assert all(r is not None and r["shared"] is True for r in results)


# ────────────────────────────────────────────────────────────────────────────
# Domain-specific cache scenarios
# ────────────────────────────────────────────────────────────────────────────
class TestDomainCacheScenarios:

    @pytest.mark.asyncio
    async def test_property_listing_cache(self, mock_cache, sample_property):
        key = generate_cache_key("properties", 1, 20, "all")
        payload = {"items": [sample_property], "total": 1, "page": 1, "limit": 20, "pages": 1}
        await set_in_cache(key, payload, ttl=300)
        result = await get_from_cache(key)
        assert result["total"] == 1
        assert result["items"][0]["title"] == sample_property["title"]

    @pytest.mark.asyncio
    async def test_user_profile_cache(self, mock_cache, sample_user):
        key = generate_cache_key("user", sample_user["id"])
        await set_in_cache(key, sample_user, ttl=3600)
        result = await get_from_cache(key)
        assert result["email"] == sample_user["email"]

    @pytest.mark.asyncio
    async def test_search_results_cache(self, mock_cache, sample_property):
        key = generate_cache_key("search", "gurgaon", "", "", "apartment", 1, 20)
        payload = {"items": [sample_property], "total": 1, "page": 1, "limit": 20, "pages": 1}
        await set_in_cache(key, payload, ttl=120)
        result = await get_from_cache(key)
        assert result["items"][0]["city"] == "Gurgaon"

    @pytest.mark.asyncio
    async def test_cache_invalidated_after_property_update(self, mock_cache, sample_property):
        key = generate_cache_key("properties", 1, 20, "all")
        payload = {"items": [sample_property], "total": 1}
        await set_in_cache(key, payload, ttl=300)

        # Simulate update — invalidate pattern
        await invalidate_cache_pattern("properties:*")

        result = await get_from_cache(key)
        assert result is None

    @pytest.mark.asyncio
    async def test_payment_cache(self, mock_cache):
        key = generate_cache_key("payments", "user_001", "history")
        data = {"transactions": [{"id": "tx1", "amount": 5000}]}
        await set_in_cache(key, data, ttl=60)
        result = await get_from_cache(key)
        assert len(result["transactions"]) == 1

    @pytest.mark.asyncio
    async def test_analytics_cache(self, mock_cache):
        key = generate_cache_key("analytics", "price_trends", "gurgaon", "2025")
        data = {"trend": [{"month": "Jan", "avg_price": 8500000}]}
        await set_in_cache(key, data, ttl=900)
        result = await get_from_cache(key)
        assert result["trend"][0]["avg_price"] == 8500000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
