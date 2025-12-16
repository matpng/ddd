"""
Unit tests for LRU Cache implementation
"""
import pytest


class TestLRUCache:
    """Tests for LRU Cache in app.py"""
    
    def test_cache_creation(self):
        """Test cache can be created with max size"""
        from app.utils.cache import LRUCache
        
        cache = LRUCache(max_size=5)
        assert cache.max_size == 5
        assert len(cache.cache) == 0
    
    def test_cache_set_and_get(self):
        """Test setting and getting values"""
        from app.utils.cache import LRUCache
        
        cache = LRUCache(max_size=3)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        from app.utils.cache import LRUCache
        
        cache = LRUCache(max_size=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should evict key1
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
    
    def test_cache_get_updates_order(self):
        """Test that getting a key updates its position (LRU)"""
        from app.utils.cache import LRUCache
        
        cache = LRUCache(max_size=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Access key1 to refresh it
        _ = cache.get("key1")
        
        # Add key3, should evict key2 (not key1)
        cache.set("key3", "value3")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"
    
    def test_cache_contains(self):
        """Test __contains__ method"""
        from app.utils.cache import LRUCache
        
        cache = LRUCache(max_size=3)
        cache.set("key1", "value1")
        
        assert "key1" in cache
        assert "key2" not in cache
    
    def test_cache_getitem_setitem(self):
        """Test dictionary-style access"""
        from app.utils.cache import LRUCache
        
        cache = LRUCache(max_size=3)
        cache["key1"] = "value1"
        
        assert cache["key1"] == "value1"
        assert cache.get("nonexistent") is None
    
    def test_cache_overwrite(self):
        """Test overwriting existing key"""
        from app.utils.cache import LRUCache
        
        cache = LRUCache(max_size=3)
        cache.set("key1", "value1")
        cache.set("key1", "value2")
        
        assert cache.get("key1") == "value2"
        assert len(cache.cache) == 1
    
    def test_cache_none_value(self):
        """Test caching None values"""
        from app.utils.cache import LRUCache
        
        cache = LRUCache(max_size=3)
        cache.set("key1", None)
        
        assert "key1" in cache
        assert cache.get("key1") is None
