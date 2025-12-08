#!/usr/bin/env python3
"""
Proto-AGI Kernel (PAK) Database Layer
Manages persistence for goals, values, world knowledge, and self-awareness
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class PAKDatabase:
    """
    Database interface for Proto-AGI Kernel.
    Manages all PAK-related data: goals, values, world models, self-awareness, etc.
    """
    
    def __init__(self, db_path: str = 'pak_intelligence.db'):
        self.db_path = Path(db_path)
        self.connection = None
        self._initialize_database()
        logger.info(f"PAK Database initialized: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
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
            
            # Table 1: Research Goals
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_goals (
                    id TEXT PRIMARY KEY,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    hypothesis TEXT,
                    
                    -- Geometric scope
                    angle_range_start REAL,
                    angle_range_end REAL,
                    target_axes TEXT,
                    parameter_constraints TEXT,
                    
                    -- Research classification
                    origin TEXT,
                    scope TEXT,
                    priority REAL DEFAULT 1.0,
                    
                    -- Status tracking
                    status TEXT DEFAULT 'active',
                    parent_goal_id TEXT,
                    time_horizon TEXT,
                    
                    -- Results linkage
                    discoveries_found INTEGER DEFAULT 0,
                    validation_status TEXT,
                    evaluation_notes TEXT,
                    last_reviewed_at DATETIME,
                    
                    FOREIGN KEY (parent_goal_id) REFERENCES research_goals(id)
                )
            """)
            
            # Table 2: Research Values
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_values (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    weight REAL DEFAULT 1.0,
                    category TEXT,
                    source TEXT,
                    adjustment_history TEXT,
                    last_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table 3: Value Conflicts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS value_conflicts (
                    id TEXT PRIMARY KEY,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS world_knowledge (
                    id TEXT PRIMARY KEY,
                    domain TEXT,
                    fact_type TEXT,
                    content TEXT,
                    source TEXT,
                    relevance_to_system TEXT,
                    causal_links TEXT,
                    validation_status TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table 5: World Events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS world_events (
                    id TEXT PRIMARY KEY,
                    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source TEXT,
                    title TEXT,
                    description TEXT,
                    tags TEXT,
                    affected_domains TEXT,
                    potential_impact TEXT,
                    linked_world_model_ids TEXT,
                    recommended_goal_updates TEXT
                )
            """)
            
            # Table 6: Self Model
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS self_model (
                    id TEXT PRIMARY KEY DEFAULT 'ORION_OCTAVE_MIND',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    identity_statement TEXT,
                    capabilities TEXT,
                    limitations TEXT,
                    dependencies TEXT,
                    continuity_risks TEXT,
                    long_term_objectives TEXT,
                    narrative_history TEXT,
                    last_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table 7: Introspection Logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS introspection_logs (
                    id TEXT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    trigger_event TEXT,
                    context TEXT,
                    internal_dialogue TEXT,
                    key_realizations TEXT,
                    concerns TEXT,
                    proposed_actions TEXT,
                    linked_goal_id TEXT,
                    FOREIGN KEY (linked_goal_id) REFERENCES research_goals(id)
                )
            """)
            
            # Table 8: Research Agendas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_agendas (
                    id TEXT PRIMARY KEY,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    motivation TEXT,
                    domain TEXT,
                    related_world_model_ids TEXT,
                    status TEXT DEFAULT 'active',
                    related_goals TEXT,
                    research_questions TEXT,
                    methodology TEXT,
                    progress_milestones TEXT,
                    findings_summary TEXT,
                    impact_assessment TEXT,
                    next_steps TEXT,
                    last_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
            cursor.execute("""
                INSERT INTO research_goals (
                    id, created_by, title, description, hypothesis,
                    angle_range_start, angle_range_end, target_axes,
                    parameter_constraints, origin, scope, priority,
                    status, parent_goal_id, time_horizon
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            for key, value in updates.items():
                if key in ['target_axes', 'parameter_constraints']:
                    value = json.dumps(value)
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.append(goal_id)
            
            query = f"""
                UPDATE research_goals 
                SET {', '.join(set_clauses)}, last_reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            cursor.execute(query, values)
        
        logger.info(f"Updated goal: {goal_id}")
    
    def increment_goal_discoveries(self, goal_id: str):
        """Increment discovery count for a goal"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE research_goals 
                SET discoveries_found = discoveries_found + 1,
                    last_reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (goal_id,))
    
    # ==================== RESEARCH VALUES ====================
    
    def get_all_values(self) -> Dict[str, Dict[str, Any]]:
        """Get all research values as a dictionary"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM research_values ORDER BY weight DESC")
            values = {}
            for row in cursor.fetchall():
                values[row['id']] = dict(row)
            return values
    
    def update_value_weight(self, value_id: str, new_weight: float, reason: str):
        """Update the weight of a research value"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get current history
            cursor.execute("SELECT adjustment_history FROM research_values WHERE id = ?", (value_id,))
            row = cursor.fetchone()
            
            history = []
            if row and row['adjustment_history']:
                history = json.loads(row['adjustment_history'])
            
            # Add new adjustment
            history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'new_weight': new_weight,
                'reason': reason
            })
            
            cursor.execute("""
                UPDATE research_values 
                SET weight = ?, adjustment_history = ?, last_updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_weight, json.dumps(history), value_id))
        
        logger.info(f"Updated value weight: {value_id} = {new_weight}")
    
    # ==================== WORLD KNOWLEDGE ====================
    
    def add_world_knowledge(self, knowledge_data: Dict[str, Any]) -> str:
        """Add new world knowledge entry"""
        knowledge_id = knowledge_data.get('id', f"wk_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO world_knowledge (
                    id, domain, fact_type, content, source,
                    relevance_to_system, causal_links, validation_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
            if domain:
                cursor.execute("""
                    SELECT * FROM world_knowledge 
                    WHERE domain = ?
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
            cursor.execute("SELECT * FROM self_model WHERE id = 'ORION_OCTAVE_MIND'")
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_self_model(self, updates: Dict[str, Any]):
        """Update the self-model"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            set_clauses = []
            values = []
            for key, value in updates.items():
                if key in ['capabilities', 'limitations', 'dependencies', 
                           'continuity_risks', 'long_term_objectives']:
                    value = json.dumps(value) if isinstance(value, (list, dict)) else value
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.append('ORION_OCTAVE_MIND')
            
            query = f"""
                UPDATE self_model 
                SET {', '.join(set_clauses)}, last_updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            cursor.execute(query, values)
        
        logger.info("Updated self-model")
    
    def append_to_narrative(self, narrative_chunk: str):
        """Append to the self-model's narrative history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            entry = f"\n\n[{timestamp}]\n{narrative_chunk}"
            
            cursor.execute("""
                UPDATE self_model 
                SET narrative_history = COALESCE(narrative_history, '') || ?,
                    last_updated_at = CURRENT_TIMESTAMP
                WHERE id = 'ORION_OCTAVE_MIND'
            """, (entry,))
        
        logger.info("Appended to narrative history")
    
    # ==================== INTROSPECTION ====================
    
    def record_introspection(self, log_data: Dict[str, Any]) -> str:
        """Record an introspection log entry"""
        log_id = log_data.get('id', f"intro_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO introspection_logs (
                    id, trigger_event, context, internal_dialogue,
                    key_realizations, concerns, proposed_actions, linked_goal_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id,
                log_data.get('trigger_event', 'general'),
                log_data.get('context', ''),
                log_data['internal_dialogue'],
                log_data.get('key_realizations', ''),
                log_data.get('concerns', ''),
                log_data.get('proposed_actions', ''),
                log_data.get('linked_goal_id')
            ))
        
        logger.info(f"Recorded introspection: {log_id}")
        return log_id
    
    def get_recent_introspections(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent introspection logs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM introspection_logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== RESEARCH AGENDAS ====================
    
    def create_research_agenda(self, agenda_data: Dict[str, Any]) -> str:
        """Create a new research agenda"""
        agenda_id = agenda_data.get('id', f"agenda_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO research_agendas (
                    id, created_by, title, description, motivation,
                    domain, related_goals, research_questions, methodology,
                    progress_milestones, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agenda_id,
                agenda_data.get('created_by', 'pak_system'),
                agenda_data['title'],
                agenda_data.get('description', ''),
                agenda_data.get('motivation', ''),
                agenda_data.get('domain', ''),
                json.dumps(agenda_data.get('related_goals', [])),
                json.dumps(agenda_data.get('research_questions', [])),
                agenda_data.get('methodology', ''),
                json.dumps(agenda_data.get('progress_milestones', [])),
                agenda_data.get('status', 'active')
            ))
        
        logger.info(f"Created research agenda: {agenda_id}")
        return agenda_id
    
    def get_active_agendas(self) -> List[Dict[str, Any]]:
        """Get all active research agendas"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM research_agendas 
                WHERE status = 'active'
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_agenda(self, agenda_id: str, updates: Dict[str, Any]):
        """Update a research agenda"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            set_clauses = []
            values = []
            for key, value in updates.items():
                if key in ['related_goals', 'research_questions', 'progress_milestones']:
                    value = json.dumps(value)
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.append(agenda_id)
            
            query = f"""
                UPDATE research_agendas 
                SET {', '.join(set_clauses)}, last_updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            cursor.execute(query, values)
        
        logger.info(f"Updated research agenda: {agenda_id}")
    
    # ==================== UTILITY METHODS ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall PAK statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Count goals by status
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM research_goals 
                GROUP BY status
            """)
            stats['goals_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Count total discoveries attributed to goals
            cursor.execute("SELECT SUM(discoveries_found) as total FROM research_goals")
            row = cursor.fetchone()
            stats['total_goal_discoveries'] = row['total'] or 0
            
            # Count world knowledge entries
            cursor.execute("SELECT COUNT(*) as count FROM world_knowledge")
            stats['world_knowledge_entries'] = cursor.fetchone()['count']
            
            # Count introspections
            cursor.execute("SELECT COUNT(*) as count FROM introspection_logs")
            stats['introspection_logs'] = cursor.fetchone()['count']
            
            # Count active agendas
            cursor.execute("SELECT COUNT(*) as count FROM research_agendas WHERE status = 'active'")
            stats['active_research_agendas'] = cursor.fetchone()['count']
            
            return stats
