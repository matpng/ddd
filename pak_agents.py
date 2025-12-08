#!/usr/bin/env python3
"""
PAK AI Agents - Goal Engine and Value Engine
Handles goal generation, prioritization, and value-driven decision making
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pak_database import PAKDatabase

logger = logging.getLogger(__name__)

# Check if OpenAI is available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Install with: pip install openai")


class GoalEngine:
    """
    Generates and manages research goals.
    Can create goals from discoveries, introspections, or world events.
    """
    
    def __init__(self, db: PAKDatabase, use_llm: bool = False):
        self.db = db
        self.use_llm = use_llm and OPENAI_AVAILABLE
        
        if self.use_llm:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.client = OpenAI(api_key=api_key)
                logger.info("Goal Engine initialized with LLM support")
            else:
                self.use_llm = False
                logger.warning("OPENAI_API_KEY not set. Using rule-based goal generation.")
        else:
            self.client = None
            logger.info("Goal Engine initialized (rule-based mode)")
    
    def generate_goals_from_discovery(self, discovery: Dict[str, Any]) -> List[str]:
        """
        Analyze a discovery and generate follow-up research goals.
        Returns list of created goal IDs.
        """
        
        if self.use_llm:
            return self._generate_goals_llm(discovery)
        else:
            return self._generate_goals_rule_based(discovery)
    
    def _generate_goals_rule_based(self, discovery: Dict[str, Any]) -> List[str]:
        """Rule-based goal generation"""
        
        created_goals = []
        
        # Extract discovery properties
        angle = discovery.get('angle_z', discovery.get('angle', 0))
        golden_count = discovery.get('golden_ratio_count', 0)
        special_angles = discovery.get('special_angle_detection', {}).get('detected_special_angles', [])
        
        # Rule 1: If golden ratio found, investigate nearby angles
        if golden_count > 0:
            goal_data = {
                'title': f'Investigate Golden Ratio Vicinity Near {angle}°',
                'description': f'Discovery at {angle}° showed {golden_count} golden ratio occurrences. Investigate ±5° range at high resolution to map the extent of φ manifestation.',
                'hypothesis': f'Golden ratio occurrences peak at {angle}° with gradual falloff, or multiple discrete peaks exist nearby.',
                'angle_range_start': max(0, angle - 5),
                'angle_range_end': min(180, angle + 5),
                'target_axes': ['z'],
                'parameter_constraints': {'step_size': 0.1, 'focus_golden_ratio': True},
                'origin': 'prior_discovery',
                'scope': 'validate_theory',
                'priority': 5.0 + golden_count * 0.5,
                'time_horizon': 'short',
                'created_by': 'goal_engine_rule_based'
            }
            goal_id = self.db.create_goal(goal_data)
            created_goals.append(goal_id)
        
        # Rule 2: If special angle detected, investigate its properties
        if special_angles:
            for special_angle_info in special_angles:
                detected_angle = special_angle_info.get('angle', 0)
                goal_data = {
                    'title': f'Deep Analysis of Special Angle {detected_angle}°',
                    'description': f'Special angle {detected_angle}° detected in discovery at {angle}°. Perform comprehensive geometric analysis.',
                    'hypothesis': f'{detected_angle}° is a fundamental angle in the rotational geometry, linked to Platonic solid symmetries.',
                    'angle_range_start': detected_angle - 0.5,
                    'angle_range_end': detected_angle + 0.5,
                    'target_axes': ['z'],
                    'parameter_constraints': {'step_size': 0.01, 'analyze_symmetry': True},
                    'origin': 'prior_discovery',
                    'scope': 'validate_theory',
                    'priority': 7.0,
                    'time_horizon': 'medium',
                    'created_by': 'goal_engine_rule_based'
                }
                goal_id = self.db.create_goal(goal_data)
                created_goals.append(goal_id)
        
        # Rule 3: If angle is near unexplored region, suggest exploration
        # (This would check existing discoveries to find gaps)
        
        return created_goals
    
    def _generate_goals_llm(self, discovery: Dict[str, Any]) -> List[str]:
        """LLM-based goal generation (future implementation)"""
        
        prompt = f"""
You are Orion Octave's Goal Engine. Analyze this geometric discovery and propose 1-3 follow-up research goals.

DISCOVERY:
{json.dumps(discovery, indent=2)}

For each goal, provide:
- Title (concise, specific)
- Description (what to investigate and why)
- Hypothesis (testable prediction)
- Angle range (if applicable)
- Priority (0-10, based on novelty and significance)
- Time horizon (short/medium/long)

Focus on:
1. Exploring unexpected patterns
2. Validating theoretical connections
3. Investigating golden ratio correlations
4. Mapping special angle neighborhoods

Return JSON array of goals.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a research goal generator for geometric analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            goals_json = response.choices[0].message.content
            goals = json.loads(goals_json)
            
            created_goals = []
            for goal_data in goals:
                goal_data['created_by'] = 'goal_engine_llm'
                goal_data['origin'] = 'prior_discovery'
                goal_id = self.db.create_goal(goal_data)
                created_goals.append(goal_id)
            
            return created_goals
        
        except Exception as e:
            logger.error(f"LLM goal generation failed: {e}. Falling back to rule-based.")
            return self._generate_goals_rule_based(discovery)
    
    def prioritize_goals(self) -> List[Dict[str, Any]]:
        """
        Get active goals sorted by value-weighted priority.
        Combines intrinsic goal priority with current research values.
        """
        
        goals = self.db.get_active_goals()
        values = self.db.get_all_values()
        
        # Calculate value-weighted scores
        for goal in goals:
            base_priority = goal['priority']
            
            # Bonus for novelty-seeking (unexplored angles)
            if goal['scope'] == 'explore_unknown':
                base_priority *= values.get('novelty', {}).get('weight', 1.0)
            
            # Bonus for validation goals
            if goal['scope'] == 'validate_theory':
                base_priority *= values.get('theoretical_significance', {}).get('weight', 1.0)
            
            # Bonus for practical relevance
            if 'practical' in goal.get('description', '').lower():
                base_priority *= values.get('practical_relevance', {}).get('weight', 1.0)
            
            goal['weighted_priority'] = base_priority
        
        # Sort by weighted priority
        goals.sort(key=lambda g: g['weighted_priority'], reverse=True)
        
        return goals
    
    def select_next_goal(self) -> Optional[Dict[str, Any]]:
        """Select the next goal to pursue"""
        goals = self.prioritize_goals()
        return goals[0] if goals else None


class ValueEngine:
    """
    Manages research values and handles value conflicts.
    Adjusts value weights based on outcomes and reflects on ethical dilemmas.
    """
    
    def __init__(self, db: PAKDatabase):
        self.db = db
        logger.info("Value Engine initialized")
    
    def get_current_values(self) -> Dict[str, Dict[str, Any]]:
        """Get all current research values"""
        return self.db.get_all_values()
    
    def adjust_value(self, value_id: str, new_weight: float, reason: str):
        """
        Adjust the weight of a research value.
        This is the mechanism for value drift / learning from experience.
        """
        
        # Safety check: Don't reduce safety value
        if value_id == 'safety' and new_weight < 1.0:
            logger.warning(f"Attempted to reduce safety value to {new_weight}. Clamping to 1.0")
            new_weight = 1.0
        
        # Clamp to reasonable range
        new_weight = max(0.0, min(10.0, new_weight))
        
        self.db.update_value_weight(value_id, new_weight, reason)
        logger.info(f"Adjusted value '{value_id}' to {new_weight}: {reason}")
    
    def handle_value_conflict(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a scenario where multiple values conflict.
        
        Example scenario:
        {
            'description': 'Should we run computationally expensive multi-axis sweep?',
            'options': [
                {'name': 'run_full_sweep', 'favors': ['novelty', 'theoretical_significance'], 'costs': ['computational_efficiency']},
                {'name': 'skip', 'favors': ['computational_efficiency'], 'costs': ['novelty']}
            ]
        }
        """
        
        values = self.get_current_values()
        
        # Score each option
        scored_options = []
        for option in scenario['options']:
            score = 0.0
            
            # Add scores for favored values
            for value_id in option.get('favors', []):
                if value_id in values:
                    score += values[value_id]['weight']
            
            # Subtract scores for cost values
            for value_id in option.get('costs', []):
                if value_id in values:
                    score -= values[value_id]['weight'] * 0.5  # Cost is weighted less
            
            scored_options.append({
                'option': option,
                'score': score
            })
        
        # Select highest-scoring option
        best_option = max(scored_options, key=lambda x: x['score'])
        
        # Log the decision
        decision = {
            'scenario': scenario['description'],
            'chosen': best_option['option']['name'],
            'score': best_option['score'],
            'rationale': f"Chose {best_option['option']['name']} (score: {best_option['score']:.2f}) based on current value weights."
        }
        
        # Record to database
        conflict_data = {
            'scenario_description': scenario['description'],
            'options_considered': json.dumps(scenario['options']),
            'decision_taken': best_option['option']['name'],
            'rationale': decision['rationale'],
            'values_in_conflict': json.dumps(list(set(
                sum([opt.get('favors', []) + opt.get('costs', []) for opt in scenario['options']], [])
            )))
        }
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            conflict_id = f"conflict_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
            cursor.execute("""
                INSERT INTO value_conflicts (
                    id, scenario_description, options_considered, 
                    decision_taken, rationale, values_in_conflict
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                conflict_id,
                conflict_data['scenario_description'],
                conflict_data['options_considered'],
                conflict_data['decision_taken'],
                conflict_data['rationale'],
                conflict_data['values_in_conflict']
            ))
        
        logger.info(f"Resolved value conflict: {decision['chosen']}")
        return decision
    
    def reflect_on_outcome(self, goal_id: str, outcome: Dict[str, Any]):
        """
        After a goal completes, reflect on whether the outcome justifies value adjustments.
        
        Example: If a high-priority goal (weighted for novelty) found nothing interesting,
        consider slightly reducing novelty weight.
        """
        
        discoveries_found = outcome.get('discoveries_found', 0)
        quality_score = outcome.get('quality_score', 0.0)
        
        # If high-priority goal yielded low results, consider adjustment
        if discoveries_found == 0 and quality_score < 0.3:
            logger.info(f"Goal {goal_id} yielded low results. Consider value adjustment.")
            # In future, could implement automatic value learning here
        
        # If goal exceeded expectations, reinforce those values
        if discoveries_found > 5 or quality_score > 0.8:
            logger.info(f"Goal {goal_id} highly successful. Values validated.")


class WorldModelEngine:
    """
    Maintains and queries the world knowledge base.
    Links geometric discoveries to real-world physics, materials, and applications.
    """
    
    def __init__(self, db: PAKDatabase):
        self.db = db
        logger.info("World Model Engine initialized")
    
    def connect_discovery_to_world(self, discovery: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Given a discovery, find relevant world knowledge connections.
        Returns list of relevant knowledge entries with connection explanations.
        """
        
        connections = []
        
        # Get discovery properties
        angle = discovery.get('angle_z', discovery.get('angle', 0))
        golden_count = discovery.get('golden_ratio_count', 0)
        special_angles = discovery.get('special_angle_detection', {}).get('detected_special_angles', [])
        
        # Search for relevant world knowledge
        all_knowledge = self.db.search_world_knowledge()
        
        for entry in all_knowledge:
            relevance_score = 0.0
            connection_reason = ""
            
            # Check for golden ratio connections
            if golden_count > 0 and 'golden ratio' in entry['content'].lower():
                relevance_score += 0.8
                connection_reason += f"Discovery shows {golden_count} φ occurrences. "
            
            # Check for angle-specific connections
            for sa in special_angles:
                sa_value = sa.get('angle', 0)
                if str(int(sa_value)) in entry['content'] or f"{sa_value}°" in entry['content']:
                    relevance_score += 0.6
                    connection_reason += f"Special angle {sa_value}° mentioned. "
            
            # Check for domain relevance
            if entry['domain'] in ['quasicrystals', 'crystallography', 'geometry']:
                relevance_score += 0.3
            
            if relevance_score > 0.5:
                connections.append({
                    'knowledge_id': entry['id'],
                    'domain': entry['domain'],
                    'content': entry['content'],
                    'relevance_score': relevance_score,
                    'connection_reason': connection_reason.strip(),
                    'source': entry['source']
                })
        
        # Sort by relevance
        connections.sort(key=lambda c: c['relevance_score'], reverse=True)
        
        return connections
    
    def suggest_real_world_applications(self, discovery: Dict[str, Any]) -> List[str]:
        """
        Based on world knowledge, suggest potential real-world applications.
        """
        
        applications = []
        connections = self.connect_discovery_to_world(discovery)
        
        for conn in connections[:3]:  # Top 3 connections
            if conn['domain'] == 'quasicrystals':
                applications.append(
                    f"Potential quasicrystal application: {conn['content'][:100]}... "
                    f"(Relevance: {conn['relevance_score']:.2f})"
                )
            elif conn['domain'] == 'crystallography':
                applications.append(
                    f"Crystal structure insight: {conn['content'][:100]}... "
                    f"(Relevance: {conn['relevance_score']:.2f})"
                )
            elif conn['domain'] == 'materials_science':
                applications.append(
                    f"Materials application: {conn['content'][:100]}... "
                    f"(Relevance: {conn['relevance_score']:.2f})"
                )
        
        return applications


# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    db = PAKDatabase('pak_intelligence.db')
    
    # Test Goal Engine
    print("\n" + "="*70)
    print("GOAL ENGINE TEST")
    print("="*70)
    
    goal_engine = GoalEngine(db, use_llm=False)
    
    # Simulate a discovery
    test_discovery = {
        'angle_z': 36.0,
        'golden_ratio_count': 3,
        'special_angle_detection': {
            'detected_special_angles': [
                {'angle': 36, 'properties': 'pentagonal_icosahedral'}
            ]
        }
    }
    
    print("\nGenerating goals from discovery at 36°...")
    new_goal_ids = goal_engine.generate_goals_from_discovery(test_discovery)
    print(f"Created {len(new_goal_ids)} new goals")
    
    print("\nPrioritized goal list:")
    prioritized = goal_engine.prioritize_goals()
    for i, goal in enumerate(prioritized[:5], 1):
        print(f"  {i}. [{goal.get('weighted_priority', goal['priority']):.1f}] {goal['title']}")
    
    # Test Value Engine
    print("\n" + "="*70)
    print("VALUE ENGINE TEST")
    print("="*70)
    
    value_engine = ValueEngine(db)
    
    values = value_engine.get_current_values()
    print("\nCurrent research values:")
    for vid, vdata in sorted(values.items(), key=lambda x: x[1]['weight'], reverse=True):
        print(f"  {vdata['name']}: {vdata['weight']:.2f}")
    
    print("\nSimulating value conflict...")
    conflict_scenario = {
        'description': 'Should we run a 7-day multi-axis sweep (computationally expensive but highly novel)?',
        'options': [
            {
                'name': 'run_full_sweep',
                'favors': ['novelty', 'theoretical_significance'],
                'costs': ['computational_efficiency']
            },
            {
                'name': 'run_abbreviated_sweep',
                'favors': ['novelty', 'computational_efficiency'],
                'costs': ['theoretical_significance']
            },
            {
                'name': 'skip_for_now',
                'favors': ['computational_efficiency'],
                'costs': ['novelty', 'theoretical_significance']
            }
        ]
    }
    
    decision = value_engine.handle_value_conflict(conflict_scenario)
    print(f"\nDecision: {decision['chosen']}")
    print(f"Rationale: {decision['rationale']}")
    
    # Test World Model Engine
    print("\n" + "="*70)
    print("WORLD MODEL ENGINE TEST")
    print("="*70)
    
    world_engine = WorldModelEngine(db)
    
    print("\nConnecting discovery to world knowledge...")
    connections = world_engine.connect_discovery_to_world(test_discovery)
    print(f"Found {len(connections)} relevant knowledge connections:")
    for conn in connections[:3]:
        print(f"\n  [{conn['relevance_score']:.2f}] {conn['domain'].upper()}")
        print(f"  {conn['connection_reason']}")
        print(f"  {conn['content'][:100]}...")
    
    print("\nSuggested real-world applications:")
    applications = world_engine.suggest_real_world_applications(test_discovery)
    for app in applications:
        print(f"  - {app}")
    
    print("\n" + "="*70)
    print("AGENT TESTS COMPLETE")
    print("="*70)
