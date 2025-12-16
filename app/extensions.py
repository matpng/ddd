"""
Shared extensions and global objects for the application.
Avoids circular imports between app factory/main and blueprints.
"""
from config import Config
from app.utils.cache import LRUCache

# Initialize LRU Cache for analysis results
analysis_cache = LRUCache(max_size=Config.CACHE_MAX_SIZE) if Config.CACHE_ENABLED else {}
