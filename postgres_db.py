"""
PostgreSQL Database Client
Replaces SQLite database with PostgreSQL for production use
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2.pool import SimpleConnectionPool
from typing import List, Dict, Any, Optional
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class PostgreSQLClient:
    """PostgreSQL database client with connection pooling"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.environ.get(
            'DATABASE_URL',
            'postgresql://agi_user:changeme@localhost:5432/agi_system'
        )
        
        # Create connection pool
        try:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=self.database_url
            )
            logger.info("PostgreSQL connection pool created")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = self.pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            self.pool.putconn(conn)
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dicts"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected rows"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute query with multiple parameter sets"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                execute_values(cursor, query, params_list)
                return cursor.rowcount
    
    def close(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("PostgreSQL connection pool closed")


class DiscoveryDatabase:
    """Discovery System database operations using PostgreSQL"""
    
    def __init__(self, db_client: PostgreSQLClient):
        self.db = db_client
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Create tables if they don't exist"""
        schema_sql = """
        -- Discoveries table
        CREATE TABLE IF NOT EXISTS discoveries (
            id VARCHAR(255) PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            type VARCHAR(50),
            data JSONB,
            title TEXT,
            significance FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_discoveries_timestamp 
            ON discoveries(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_discoveries_type 
            ON discoveries(type);
        CREATE INDEX IF NOT EXISTS idx_discoveries_significance 
            ON discoveries(significance DESC);
        
        -- Goals table
        CREATE TABLE IF NOT EXISTS goals (
            id VARCHAR(255) PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            hypothesis TEXT,
            angle_range_start FLOAT,
            angle_range_end FLOAT,
            target_axes TEXT[],
            parameter_constraints JSONB,
            origin VARCHAR(50),
            scope VARCHAR(50),
            priority FLOAT DEFAULT 5.0,
            time_horizon VARCHAR(20),
            created_by VARCHAR(100),
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
        CREATE INDEX IF NOT EXISTS idx_goals_priority ON goals(priority DESC);
        
        -- Research values table
        CREATE TABLE IF NOT EXISTS research_values (
            id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            weight FLOAT DEFAULT 1.0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            update_reason TEXT
        );
        
        -- Value conflicts table
        CREATE TABLE IF NOT EXISTS value_conflicts (
            id VARCHAR(255) PRIMARY KEY,
            scenario_description TEXT,
            options_considered JSONB,
            decision_taken TEXT,
            rationale TEXT,
            values_in_conflict TEXT[],
            occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- World knowledge table
        CREATE TABLE IF NOT EXISTS world_knowledge (
            id VARCHAR(255) PRIMARY KEY,
            domain VARCHAR(100),
            content TEXT,
            source VARCHAR(255),
            confidence FLOAT DEFAULT 0.8,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_verified TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_world_knowledge_domain 
            ON world_knowledge(domain);
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
            conn.commit()
        
        logger.info("Database schema ensured")
    
    # Discovery operations
    def save_discovery(self, discovery: Dict[str, Any]) -> bool:
        """Save a discovery to the database"""
        query = """
            INSERT INTO discoveries (id, timestamp, type, data, title, significance)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                data = EXCLUDED.data,
                title = EXCLUDED.title,
                significance = EXCLUDED.significance
        """
        try:
            self.db.execute_update(query, (
                discovery['id'],
                discovery['timestamp'],
                discovery.get('type'),
                psycopg2.extras.Json(discovery.get('data', {})),
                discovery.get('title'),
                discovery.get('significance', 0.0)
            ))
            return True
        except Exception as e:
            logger.error(f"Failed to save discovery: {e}")
            return False
    
    def get_discovery(self, discovery_id: str) -> Optional[Dict[str, Any]]:
        """Get a discovery by ID"""
        query = "SELECT * FROM discoveries WHERE id = %s"
        results = self.db.execute_query(query, (discovery_id,))
        return results[0] if results else None
    
    def get_all_discoveries(self) -> List[Dict[str, Any]]:
        """Get all discoveries"""
        query = "SELECT * FROM discoveries ORDER BY timestamp DESC"
        return self.db.execute_query(query)
    
    def get_recent_discoveries(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get discoveries from the last N hours"""
        query = """
            SELECT * FROM discoveries 
            WHERE timestamp > NOW() - INTERVAL '%s hours'
            ORDER BY timestamp DESC
        """
        return self.db.execute_query(query, (hours,))
    
    def count_discoveries(self) -> int:
        """Get total discovery count"""
        query = "SELECT COUNT(*) as count FROM discoveries"
        result = self.db.execute_query(query)
        return result[0]['count'] if result else 0
    
    # Goal operations
    def save_goal(self, goal: Dict[str, Any]) -> bool:
        """Save a goal to the database"""
        query = """
            INSERT INTO goals (
                id, title, description, hypothesis, angle_range_start,
                angle_range_end, target_axes, parameter_constraints,
                origin, scope, priority, time_horizon, created_by, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                priority = EXCLUDED.priority
        """
        try:
            self.db.execute_update(query, (
                goal['id'],
                goal['title'],
                goal.get('description'),
                goal.get('hypothesis'),
                goal.get('angle_range_start'),
                goal.get('angle_range_end'),
                goal.get('target_axes', []),
                psycopg2.extras.Json(goal.get('parameter_constraints', {})),
                goal.get('origin'),
                goal.get('scope'),
                goal.get('priority', 5.0),
                goal.get('time_horizon'),
                goal.get('created_by'),
                goal.get('status', 'active')
            ))
            return True
        except Exception as e:
            logger.error(f"Failed to save goal: {e}")
            return False
    
    def get_active_goals(self) -> List[Dict[str, Any]]:
        """Get all active goals"""
        query = """
            SELECT * FROM goals 
            WHERE status = 'active' 
            ORDER BY priority DESC
        """
        return self.db.execute_query(query)
    
    # Value operations
    def save_value(self, value: Dict[str, Any]) -> bool:
        """Save a research value"""
        query = """
            INSERT INTO research_values (id, name, description, weight, update_reason)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                weight = EXCLUDED.weight,
                last_updated = CURRENT_TIMESTAMP,
                update_reason = EXCLUDED.update_reason
        """
        try:
            self.db.execute_update(query, (
                value['id'],
                value['name'],
                value.get('description'),
                value.get('weight', 1.0),
                value.get('update_reason')
            ))
            return True
        except Exception as e:
            logger.error(f"Failed to save value: {e}")
            return False
    
    def get_all_values(self) -> List[Dict[str, Any]]:
        """Get all research values"""
        query = "SELECT * FROM research_values ORDER BY weight DESC"
        return self.db.execute_query(query)


# Global database instance (initialized in app.py)
_db_client: Optional[PostgreSQLClient] = None
_discovery_db: Optional[DiscoveryDatabase] = None

def init_database(database_url: Optional[str] = None):
    """Initialize the global database connection"""
    global _db_client, _discovery_db
    _db_client = PostgreSQLClient(database_url)
    _discovery_db = DiscoveryDatabase(_db_client)
    return _discovery_db

def get_database() -> DiscoveryDatabase:
    """Get the global database instance"""
    if _discovery_db is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _discovery_db

def close_database():
    """Close the database connection"""
    if _db_client:
        _db_client.close()
