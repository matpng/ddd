"""
Shared extensions and global objects for the application.
Avoids circular imports between app factory/main and blueprints.
"""
from config import Config
from app.utils.cache import LRUCache
from discovery_manager import DiscoveryManager
from ml_integration import initialize_ml_integration
from daemon_monitor import daemon_monitor

# Initialize LRU Cache for analysis results
analysis_cache = LRUCache(max_size=Config.CACHE_MAX_SIZE) if Config.CACHE_ENABLED else {}

# Initialize discovery manager
discovery_manager = DiscoveryManager()

# Initialize ML integration
ml_integration = initialize_ml_integration(discovery_manager)
