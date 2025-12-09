#!/usr/bin/env python3
"""
Proto-AGI Kernel (PAK) Database Layer - PostgreSQL Version
Manages persistence for goals, values, world knowledge, and self-awareness
Compatible with both SQLite (dev) and PostgreSQL (production)
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

# Try PostgreSQL first, fallback to SQLite
USE_POSTGRES = os.environ.get('USE_POSTGRES', 'false').lower() == 'true'

if USE_POSTGRES:
    from postgres_db import PostgreSQLClient, get_connection
    import psycopg2
    import psycopg2.extras
else:
    import sqlite3
    from pathlib import Path

logger = logging.getLogger(__name__)


class PAKDatabase:
    """
    Database interface for Proto-AGI Kernel.
    Supports both SQLite (development) and PostgreSQL (production)
    """
    
    def __init__(self, db_path: str = 'pak_intelligence.db', use_postgres: bool = None):
        self.use_postgres = use_postgres if use_postgres is not None else USE_POSTGRES
        
        if self.use_postgres:
            # PostgreSQL mode
            self.db_url = os.environ.get('DATABASE_URL', 
                'postgresql://agi_user:changeme@localhost:5432/agi_system')
            self.pg_client = PostgreSQLClient(self.db_url)
            logger.info(f"PAK Database initialized (PostgreSQL): {self.db_url}")
        else:
            # SQLite mode
            self.db_path = Path(db_path)
            self.connection = None
            logger.info(f"PAK Database initialized (SQLite): {self.db_path}")
        
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        if self.use_postgres:
            with self.pg_client.get_connection() as conn:
                yield conn
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
    
    def _initialize_database(self):
        """Create all PAK tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Note: PostgreSQL uses SERIAL/TIMESTAMP, SQLite uses INTEGER/DATETIME
            timestamp_type = "TIMESTAMP" if self.use_postgres else "DATETIME"
            id_default = "" if self.use_postgres else "DEFAULT 'ORION_OCTAVE_MIND'"
            
            # Table 1: Research Goals
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS research_goals (
                    id TEXT PRIMARY KEY,
                    created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    hypothesis TEXT,
                    angle_range_start REAL,
                    angle_range_end REAL,
                    target_axes TEXT,
                    parameter_constraints TEXT,
                    origin TEXT,
                    scope TEXT,
                    priority REAL DEFAULT 1.0,
                    status TEXT DEFAULT 'active',
                    parent_goal_id TEXT,
                    time_horizon TEXT,
                    discoveries_found INTEGER DEFAULT 0,
                    validation_status TEXT,
                    evaluation_notes TEXT,
                    last_reviewed_at {timestamp_type}
                    {', FOREIGN KEY (parent_goal_id) REFERENCES research_goals(id)' if not self.use_postgres else ''}
                )
            """)
            
            # Table 2: Research Values
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS research_values (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    weight REAL DEFAULT 1.0,
                    category TEXT,
                    source TEXT,
                    adjustment_history TEXT,
                    last_updated_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table 3: Value Conflicts
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS value_conflicts (
                    id TEXT PRIMARY KEY,
                    created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                    goal_ids TEXT,
                    values_in_conflict TEXT,
                    scenario_description TEXT,
                    options_considered TEXT,
                    decision_taken TEXT,
                    rationale TEXT,
                    outcome_metrics TEXT,
                    follow_up_actions TEXT
                )
            """)
            
            # Table 4: World Knowledge
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS world_knowledge (
                    id TEXT PRIMARY KEY,
                    domain TEXT,
                    fact_type TEXT,
                    content TEXT,
                    source TEXT,
                    relevance_to_system TEXT,
                    causal_links TEXT,
                    validation_status TEXT,
                    created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table 5: Self Model
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS self_model (
                    id TEXT PRIMARY KEY {id_default},
                    created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                    identity_statement TEXT,
                    capabilities TEXT,
                    limitations TEXT,
                    dependencies TEXT,
                    continuity_risks TEXT,
                    long_term_objectives TEXT,
                    narrative_history TEXT,
                    last_updated_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table 6: Introspection Logs
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS introspection_logs (
                    id TEXT PRIMARY KEY,
                    timestamp {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                    trigger_event TEXT,
                    internal_dialogue TEXT,
                    key_realizations TEXT,
                    concerns TEXT,
                    proposed_actions TEXT,
                    linked_goal_id TEXT
                )
            """)
            
            # Table 7: Research Agendas
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS research_agendas (
                    id TEXT PRIMARY KEY,
                    created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                    title TEXT NOT NULL,
                    description TEXT,
                    motivation TEXT,
                    domain TEXT,
                    status TEXT DEFAULT 'active',
                    related_goals TEXT,
                    research_questions TEXT,
                    methodology TEXT,
                    progress_milestones TEXT,
                    findings_summary TEXT,
                    impact_assessment TEXT,
                    next_steps TEXT,
                    created_by TEXT,
                    last_updated_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("PAK database schema created/verified")
    
    # ==================== RESEARCH GOALS ====================
    
    def create_goal(self, goal_data: Dict[str, Any]) -> str:
        """Create a new research goal"""
        goal_id = goal_data.get('id', f"goal_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            placeholder = '%s' if self.use_postgres else '?'
            cursor.execute(f"""
                INSERT INTO research_goals (
                    id, created_by, title, description, hypothesis,
                    angle_range_start, angle_range_end, target_axes,
                    parameter_constraints, origin, scope, priority,
                    status, parent_goal_id, time_horizon
                ) VALUES ({', '.join([placeholder] * 15)})
            """, (
                goal_id,
                goal_data.get('created_by', 'pak_system'),
                goal_data['title'],
                goal_data.get('description', ''),
                goal_data.get('hypothesis', ''),
                goal_data.get('angle_range_start'),
                goal_data.get('angle_range_end'),
                json.dumps(goal_data.get('target_axes', [])),
                json.dumps(goal_data.get('parameter_constraints', {})),
                goal_data.get('origin', 'system'),
                goal_data.get('scope', 'app_local'),
                goal_data.get('priority', 1.0),
                goal_data.get('status', 'active'),
                goal_data.get('parent_goal_id'),
                goal_data.get('time_horizon', 'medium')
            ))
        
        logger.info(f"Created goal: {goal_id} - {goal_data['title']}")
        return goal_id
    
    def get_active_goals(self) -> List[Dict[str, Any]]:
        """Get all active research goals"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM research_goals 
                WHERE status = 'active'
                ORDER BY priority DESC, created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_goal(self, goal_id: str, updates: Dict[str, Any]):
        """Update an existing goal"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            set_clauses = []
            values = []
            placeholder = '%s' if self.use_postgres else '?'
            
            for key, value in updates.items():
                if key in ['target_axes', 'parameter_constraints']:
                    value = json.dumps(value)
                set_clauses.append(f"{key} = {placeholder}")
                values.append(value)
            
            values.append(goal_id)
            
            query = f"""
                UPDATE research_goals 
                SET {', '.join(set_clauses)}, last_reviewed_at = CURRENT_TIMESTAMP
                WHERE id = {placeholder}
            """
            cursor.execute(query, values)
        
        logger.info(f"Updated goal: {goal_id}")
    
    # ==================== RESEARCH VALUES ====================
    
    def get_all_values(self) -> Dict[str, Dict[str, Any]]:
        """Get all research values as a dictionary"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM research_values ORDER BY weight DESC")
            values = {}
            for row in cursor.fetchall():
                values[row['id'] if isinstance(row, dict) else row[0]] = dict(row)
            return values
    
    def update_value_weight(self, value_id: str, new_weight: float, reason: str):
        """Update the weight of a research value"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = '%s' if self.use_postgres else '?'
            
            # Get current history
            cursor.execute(f"SELECT adjustment_history FROM research_values WHERE id = {placeholder}", (value_id,))
            row = cursor.fetchone()
            
            history = []
            if row:
                hist_data = row['adjustment_history'] if isinstance(row, dict) else row[0]
                if hist_data:
                    history = json.loads(hist_data)
            
            # Add new adjustment
            history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'new_weight': new_weight,
                'reason': reason
            })
            
            cursor.execute(f"""
                UPDATE research_values 
                SET weight = {placeholder}, adjustment_history = {placeholder}, last_updated_at = CURRENT_TIMESTAMP
                WHERE id = {placeholder}
            """, (new_weight, json.dumps(history), value_id))
        
        logger.info(f"Updated value weight: {value_id} = {new_weight}")
    
    # ==================== WORLD KNOWLEDGE ====================
    
    def add_world_knowledge(self, knowledge_data: Dict[str, Any]) -> str:
        """Add new world knowledge entry"""
        knowledge_id = knowledge_data.get('id', f"wk_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = '%s' if self.use_postgres else '?'
            
            cursor.execute(f"""
                INSERT INTO world_knowledge (
                    id, domain, fact_type, content, source,
                    relevance_to_system, causal_links, validation_status
                ) VALUES ({', '.join([placeholder] * 8)})
            """, (
                knowledge_id,
                knowledge_data['domain'],
                knowledge_data.get('fact_type', 'empirical'),
                knowledge_data['content'],
                knowledge_data.get('source', 'system_inference'),
                knowledge_data.get('relevance_to_system', ''),
                json.dumps(knowledge_data.get('causal_links', [])),
                knowledge_data.get('validation_status', 'untested')
            ))
        
        logger.info(f"Added world knowledge: {knowledge_id}")
        return knowledge_id
    
    def search_world_knowledge(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search world knowledge by domain"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = '%s' if self.use_postgres else '?'
            
            if domain:
                cursor.execute(f"""
                    SELECT * FROM world_knowledge 
                    WHERE domain = {placeholder}
                    ORDER BY created_at DESC
                """, (domain,))
            else:
                cursor.execute("SELECT * FROM world_knowledge ORDER BY created_at DESC")
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== SELF MODEL ====================
    
    def get_self_model(self) -> Optional[Dict[str, Any]]:
        """Get the self-model (singleton)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = '%s' if self.use_postgres else '?'
            cursor.execute(f"SELECT * FROM self_model WHERE id = {placeholder}", ('ORION_OCTAVE_MIND',))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_self_model(self, updates: Dict[str, Any]):
        """Update the self-model"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = '%s' if self.use_postgres else '?'
            
            set_clauses = []
            values = []
            for key, value in updates.items():
                if key in ['capabilities', 'limitations', 'dependencies', 
                           'continuity_risks', 'long_term_objectives']:
                    value = json.dumps(value) if isinstance(value, (list, dict)) else value
                set_clauses.append(f"{key} = {placeholder}")
                values.append(value)
            
            values.append('ORION_OCTAVE_MIND')
            
            query = f"""
                UPDATE self_model 
                SET {', '.join(set_clauses)}, last_updated_at = CURRENT_TIMESTAMP
                WHERE id = {placeholder}
            """
            cursor.execute(query, values)
        
        logger.info("Updated self-model")
    
    # ==================== RESEARCH AGENDAS ====================
    
    def create_research_agenda(self, agenda_data: Dict[str, Any]) -> str:
        """Create a new research agenda"""
        agenda_id = agenda_data.get('id', f"agenda_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = '%s' if self.use_postgres else '?'
            
            cursor.execute(f"""
                INSERT INTO research_agendas (
                    id, title, description, motivation, domain, status,
                    related_goals, research_questions, methodology,
                    progress_milestones, findings_summary, impact_assessment,
                    next_steps, created_by
                ) VALUES ({', '.join([placeholder] * 14)})
            """, (
                agenda_id,
                agenda_data['title'],
                agenda_data.get('description', ''),
                agenda_data.get('motivation', ''),
                agenda_data.get('domain', ''),
                agenda_data.get('status', 'active'),
                json.dumps(agenda_data.get('related_goals', [])),
                json.dumps(agenda_data.get('research_questions', [])),
                agenda_data.get('methodology', ''),
                json.dumps(agenda_data.get('progress_milestones', [])),
                agenda_data.get('findings_summary', ''),
                agenda_data.get('impact_assessment', ''),
                agenda_data.get('next_steps', ''),
                agenda_data.get('created_by', 'system')
            ))
        
        logger.info(f"Created research agenda: {agenda_id} - {agenda_data['title']}")
        return agenda_id
    
    # ==================== INTROSPECTION ====================
    
    def record_introspection(self, log_data: Dict[str, Any]) -> str:
        """Record an introspection event"""
        log_id = log_data.get('id', f"introspect_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = '%s' if self.use_postgres else '?'
            
            cursor.execute(f"""
                INSERT INTO introspection_logs (
                    id, trigger_event, internal_dialogue, key_realizations,
                    concerns, proposed_actions, linked_goal_id
                ) VALUES ({', '.join([placeholder] * 7)})
            """, (
                log_id,
                log_data.get('trigger_event', 'unspecified'),
                log_data.get('internal_dialogue', ''),
                log_data.get('key_realizations', ''),
                log_data.get('concerns', ''),
                log_data.get('proposed_actions', ''),
                log_data.get('linked_goal_id')
            ))
        
        logger.info(f"Recorded introspection: {log_data.get('trigger_event', 'unspecified')}")
        return log_id
    
    def append_to_narrative(self, narrative_chunk: str):
        """Append text to the self-model's narrative history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = '%s' if self.use_postgres else '?'
            
            # Get current narrative
            cursor.execute(f"SELECT narrative_history FROM self_model WHERE id = {placeholder}", ('ORION_OCTAVE_MIND',))
            row = cursor.fetchone()
            
            current_narrative = ""
            if row:
                current_narrative = row['narrative_history'] if isinstance(row, dict) else row[0]
                if current_narrative is None:
                    current_narrative = ""
            
            # Append new chunk with timestamp
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            new_narrative = f"{current_narrative}\n\n[{timestamp}]\n{narrative_chunk}"
            
            # Update
            cursor.execute(f"""
                UPDATE self_model 
                SET narrative_history = {placeholder}, last_updated_at = CURRENT_TIMESTAMP
                WHERE id = {placeholder}
            """, (new_narrative, 'ORION_OCTAVE_MIND'))
        
        logger.info("Appended to narrative history")
    
    def increment_goal_discoveries(self, goal_id: str):
        """Increment the discoveries_found counter for a goal"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = '%s' if self.use_postgres else '?'
            
            cursor.execute(f"""
                UPDATE research_goals 
                SET discoveries_found = discoveries_found + 1,
                    last_reviewed_at = CURRENT_TIMESTAMP
                WHERE id = {placeholder}
            """, (goal_id,))
        
        logger.info(f"Incremented discoveries for goal: {goal_id}")
    
    # ==================== STATISTICS ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get PAK system statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Goal statistics
            cursor.execute("SELECT status, COUNT(*) as count FROM research_goals GROUP BY status")
            goals_by_status = {}
            for row in cursor.fetchall():
                status = row['status'] if isinstance(row, dict) else row[0]
                count = row['count'] if isinstance(row, dict) else row[1]
                goals_by_status[status] = count
            stats['goals_by_status'] = goals_by_status
            
            # Total goal discoveries
            cursor.execute("SELECT SUM(discoveries_found) as total FROM research_goals")
            row = cursor.fetchone()
            total_discoveries = row['total'] if isinstance(row, dict) else row[0]
            stats['total_goal_discoveries'] = total_discoveries if total_discoveries else 0
            
            # World knowledge count
            cursor.execute("SELECT COUNT(*) as count FROM world_knowledge")
            row = cursor.fetchone()
            stats['world_knowledge_entries'] = row['count'] if isinstance(row, dict) else row[0]
            
            # Active research agendas
            cursor.execute("SELECT COUNT(*) as count FROM research_agendas WHERE status = 'active'")
            row = cursor.fetchone()
            stats['active_research_agendas'] = row['count'] if isinstance(row, dict) else row[0]
            
            # Introspection events
            cursor.execute("SELECT COUNT(*) as count FROM introspection_logs")
            row = cursor.fetchone()
            stats['introspection_count'] = row['count'] if isinstance(row, dict) else row[0]
            
            return stats
    
    def close(self):
        """Close database connection"""
        if self.use_postgres and hasattr(self, 'pg_client'):
            self.pg_client.close()

