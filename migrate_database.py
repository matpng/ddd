"""
Database Migration - SQLite to PostgreSQL
Migrates PAK intelligence data from SQLite to PostgreSQL with pgvector
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2 import sql
from typing import List, Tuple
import json
from datetime import datetime

# Configuration
SQLITE_DB = 'pak_intelligence.db'
POSTGRES_URL = os.environ.get('DATABASE_URL', 
    'postgresql://agi_user:changeme@localhost:5432/agi_system')

def connect_sqlite():
    """Connect to SQLite database"""
    if not os.path.exists(SQLITE_DB):
        print(f"❌ SQLite database not found: {SQLITE_DB}")
        return None
    return sqlite3.connect(SQLITE_DB)

def connect_postgres():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        return conn
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return None

def create_postgres_schema(pg_conn):
    """Create PostgreSQL schema with pgvector support"""
    cursor = pg_conn.cursor()
    
    print("Creating PostgreSQL schema...")
    
    # Enable pgvector extension
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # Goals table
    cursor.execute("""
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
    """)
    
    # Values table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_values (
            id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            weight FLOAT DEFAULT 1.0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            update_reason TEXT
        );
    """)
    
    # Value conflicts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS value_conflicts (
            id VARCHAR(255) PRIMARY KEY,
            scenario_description TEXT,
            options_considered JSONB,
            decision_taken TEXT,
            rationale TEXT,
            values_in_conflict TEXT[],
            occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # World knowledge table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS world_knowledge (
            id VARCHAR(255) PRIMARY KEY,
            domain VARCHAR(100),
            content TEXT,
            source VARCHAR(255),
            confidence FLOAT DEFAULT 0.8,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_verified TIMESTAMP
        );
    """)
    
    # Discoveries table (from discovery_manager)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discoveries (
            id VARCHAR(255) PRIMARY KEY,
            timestamp TIMESTAMP,
            type VARCHAR(50),
            data JSONB,
            title TEXT,
            significance FLOAT
        );
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_priority ON goals(priority DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_discoveries_timestamp ON discoveries(timestamp DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_discoveries_type ON discoveries(type);")
    
    pg_conn.commit()
    print("✅ PostgreSQL schema created")

def migrate_goals(sqlite_conn, pg_conn):
    """Migrate goals from SQLite to PostgreSQL"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    try:
        sqlite_cursor.execute("SELECT * FROM goals")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print("ℹ️  No goals to migrate")
            return 0
        
        columns = [desc[0] for desc in sqlite_cursor.description]
        migrated = 0
        
        for row in rows:
            data = dict(zip(columns, row))
            
            pg_cursor.execute("""
                INSERT INTO goals (
                    id, title, description, hypothesis,
                    angle_range_start, angle_range_end, target_axes,
                    parameter_constraints, origin, scope, priority,
                    time_horizon, created_by, status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                data['id'], data['title'], data.get('description'),
                data.get('hypothesis'), data.get('angle_range_start'),
                data.get('angle_range_end'), 
                json.loads(data.get('target_axes', '[]')),
                data.get('parameter_constraints'),
                data.get('origin'), data.get('scope'), data.get('priority', 5.0),
                data.get('time_horizon'), data.get('created_by'),
                data.get('status', 'active'), data.get('created_at')
            ))
            migrated += 1
        
        pg_conn.commit()
        print(f"✅ Migrated {migrated} goals")
        return migrated
        
    except sqlite3.OperationalError:
        print("ℹ️  Goals table doesn't exist in SQLite")
        return 0

def migrate_values(sqlite_conn, pg_conn):
    """Migrate research values"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    try:
        sqlite_cursor.execute("SELECT * FROM research_values")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print("ℹ️  No values to migrate")
            return 0
        
        columns = [desc[0] for desc in sqlite_cursor.description]
        migrated = 0
        
        for row in rows:
            data = dict(zip(columns, row))
            
            pg_cursor.execute("""
                INSERT INTO research_values (id, name, description, weight, last_updated, update_reason)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    weight = EXCLUDED.weight,
                    last_updated = EXCLUDED.last_updated,
                    update_reason = EXCLUDED.update_reason
            """, (
                data['id'], data['name'], data.get('description'),
                data.get('weight', 1.0), data.get('last_updated'),
                data.get('update_reason')
            ))
            migrated += 1
        
        pg_conn.commit()
        print(f"✅ Migrated {migrated} values")
        return migrated
        
    except sqlite3.OperationalError:
        print("ℹ️  Values table doesn't exist in SQLite")
        return 0

def run_migration():
    """Run the complete migration"""
    print("="*70)
    print("PAK Intelligence Database Migration")
    print("SQLite → PostgreSQL")
    print("="*70)
    print()
    
    # Connect to databases
    sqlite_conn = connect_sqlite()
    if not sqlite_conn:
        return False
    
    pg_conn = connect_postgres()
    if not pg_conn:
        sqlite_conn.close()
        return False
    
    try:
        # Create schema
        create_postgres_schema(pg_conn)
        
        # Migrate data
        print("\nMigrating data...")
        goals_count = migrate_goals(sqlite_conn, pg_conn)
        values_count = migrate_values(sqlite_conn, pg_conn)
        
        print("\n" + "="*70)
        print("Migration Complete!")
        print(f"  Goals: {goals_count}")
        print(f"  Values: {values_count}")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        pg_conn.rollback()
        return False
        
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
