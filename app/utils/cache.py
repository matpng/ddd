from collections import OrderedDict

class LRUCache:
    """Simple LRU cache with size limit."""
    def __init__(self, max_size=100):
        self.cache = OrderedDict()
        self.max_size = max_size
    
    def get(self, key):
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def set(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def __contains__(self, key):
        return key in self.cache
    
    def __getitem__(self, key):
        return self.get(key)
    
    def __setitem__(self, key, value):
        self.set(key, value)
