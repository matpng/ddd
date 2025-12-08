#!/usr/bin/env python3
"""
PAK-Enabled Discovery Daemon
Integrates Proto-AGI Kernel with autonomous discovery system
"""

import time
import json
import logging
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from pak_database import PAKDatabase
from pak_agents import GoalEngine, ValueEngine, WorldModelEngine
from advanced_discovery_engine import AdvancedDiscoveryEngine
from discovery_manager import DiscoveryManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PAKEnabledDiscoveryDaemon:
    """
    Proto-AGI enabled discovery daemon.
    Pursues self-generated research goals, reflects on discoveries, and adapts strategy.
    """
    
    def __init__(self, cycle_interval: int = 3600):
        """
        Initialize PAK-enabled daemon.
        
        Args:
            cycle_interval: Seconds between discovery cycles (default: 1 hour)
        """
        
        self.cycle_interval = cycle_interval
        self.running = False
        self.cycle_count = 0
        
        # Initialize PAK components
        logger.info("Initializing Proto-AGI Kernel...")
        self.pak_db = PAKDatabase('pak_intelligence.db')
        self.goal_engine = GoalEngine(self.pak_db, use_llm=False)
        self.value_engine = ValueEngine(self.pak_db)
        self.world_engine = WorldModelEngine(self.pak_db)
        
        # Initialize discovery components
        logger.info("Initializing discovery systems...")
        self.discovery_engine = AdvancedDiscoveryEngine()
        self.discovery_manager = DiscoveryManager()
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("PAK-Enabled Discovery Daemon initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.running = False
    
    def _introspect(self, trigger_event: str, context: str):
        """
        Record an introspection event.
        This is the self-awareness/reflection mechanism.
        """
        
        log_data = {
            'trigger_event': trigger_event,
            'context': context,
            'internal_dialogue': f"[Cycle {self.cycle_count}] {context}",
            'key_realizations': '',
            'concerns': '',
            'proposed_actions': ''
        }
        
        self.pak_db.record_introspection(log_data)
        logger.info(f"Introspection: {trigger_event}")
    
    def _select_discovery_parameters(self, goal: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert a research goal into discovery engine parameters.
        If no goal provided, use default exploration.
        """
        
        if not goal:
            # Default exploration mode
            return {
                'mode': 'angle_sweep',
                'angle_start': 0,
                'angle_stop': 180,
                'step_size': 5,
                'axis': 'z'
            }
        
        # Extract parameters from goal
        params = {
            'mode': 'angle_sweep',
            'axis': goal.get('target_axes', ['z'])[0] if goal.get('target_axes') else 'z',
            'angle_start': goal.get('angle_range_start', 0),
            'angle_stop': goal.get('angle_range_end', 180)
        }
        
        # Get step size from constraints
        constraints = goal.get('parameter_constraints', {})
        if isinstance(constraints, str):
            try:
                constraints = json.loads(constraints)
            except:
                constraints = {}
        
        params['step_size'] = constraints.get('step_size', 5)
        
        return params
    
    def _execute_discovery(self, params: Dict[str, Any], goal_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a discovery based on parameters.
        Returns discovery result.
        """
        
        logger.info(f"Executing discovery: {params}")
        
        # Run discovery based on mode
        if params['mode'] == 'angle_sweep':
            result = self.discovery_engine.analyze_angle_sweep(
                angle_start=params['angle_start'],
                angle_stop=params['angle_stop'],
                step_size=params['step_size'],
                axis=params['axis']
            )
        else:
            # Fallback to default
            result = self.discovery_engine.analyze_angle_sweep(0, 180, 5, 'z')
        
        # Convert to dictionary
        discovery_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'mode': params['mode'],
            'goal_id': goal_id,
            'angle_z': params.get('angle_start', 0),
            'golden_ratio_count': getattr(result, 'golden_ratio_count', 0),
            'special_angle_detection': getattr(result, 'special_angle_detection', {}),
            'summary': getattr(result, 'summary', 'Discovery completed'),
            'metadata': {
                'pak_enabled': True,
                'cycle': self.cycle_count
            }
        }
        
        # Save discovery
        discovery_id = f"pak_discovery_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.discovery_manager.save_discovery(discovery_data, discovery_id)
        
        # Update goal if linked
        if goal_id:
            self.pak_db.increment_goal_discoveries(goal_id)
        
        return discovery_data
    
    def _reflect_on_discovery(self, discovery: Dict[str, Any], goal: Optional[Dict[str, Any]]):
        """
        After a discovery, reflect on findings and generate new goals.
        This is the learning/adaptation mechanism.
        """
        
        logger.info("Reflecting on discovery...")
        
        # Connect to world knowledge
        connections = self.world_engine.connect_discovery_to_world(discovery)
        
        if connections:
            logger.info(f"Found {len(connections)} world knowledge connections")
            
            # Update narrative with connections
            narrative_chunk = f"""
Cycle {self.cycle_count} Discovery Reflection:
- Executed {'goal-driven' if goal else 'exploratory'} discovery
- Found {len(connections)} connections to existing knowledge:
"""
            for conn in connections[:3]:
                narrative_chunk += f"\n  * {conn['domain']}: {conn['connection_reason']}"
            
            self.pak_db.append_to_narrative(narrative_chunk)
        
        # Generate follow-up goals
        new_goal_ids = self.goal_engine.generate_goals_from_discovery(discovery)
        
        if new_goal_ids:
            logger.info(f"Generated {len(new_goal_ids)} new research goals")
            
            # Introspect on goal generation
            self._introspect(
                'discovery_completed',
                f"Discovery yielded {len(new_goal_ids)} new research directions. "
                f"{'Aligned with current goal.' if goal else 'Exploratory mode.'}"
            )
    
    def run_discovery_cycle(self):
        """
        Execute one complete PAK-enabled discovery cycle.
        
        Process:
        1. Select highest-priority goal
        2. Convert goal to discovery parameters
        3. Execute discovery
        4. Reflect on findings
        5. Generate new goals
        6. Update self-model
        """
        
        self.cycle_count += 1
        logger.info("="*70)
        logger.info(f"PAK DISCOVERY CYCLE {self.cycle_count} STARTING")
        logger.info("="*70)
        
        # Step 1: Select goal
        logger.info("\n[1/6] Selecting research goal...")
        current_goal = self.goal_engine.select_next_goal()
        
        if current_goal:
            logger.info(f"Selected goal: {current_goal['title']} (priority: {current_goal.get('weighted_priority', current_goal['priority']):.1f})")
        else:
            logger.info("No active goals. Running exploratory discovery.")
        
        # Step 2: Convert to parameters
        logger.info("\n[2/6] Converting goal to discovery parameters...")
        params = self._select_discovery_parameters(current_goal)
        logger.info(f"Parameters: {params}")
        
        # Step 3: Execute discovery
        logger.info("\n[3/6] Executing discovery...")
        discovery = self._execute_discovery(params, current_goal['id'] if current_goal else None)
        logger.info(f"Discovery complete: {discovery.get('summary', 'No summary')}")
        
        # Step 4: Reflect on findings
        logger.info("\n[4/6] Reflecting on findings...")
        self._reflect_on_discovery(discovery, current_goal)
        
        # Step 5: Update goal status
        if current_goal:
            logger.info("\n[5/6] Updating goal status...")
            # For now, keep goal active. In future, could mark as complete based on discoveries
            logger.info(f"Goal '{current_goal['title']}' remains active ({current_goal['discoveries_found']} discoveries)")
        else:
            logger.info("\n[5/6] No goal to update (exploratory mode)")
        
        # Step 6: Update self-model narrative
        logger.info("\n[6/6] Updating self-model...")
        stats = self.pak_db.get_statistics()
        logger.info(f"System state: {stats['total_goal_discoveries']} goal-driven discoveries, "
                   f"{sum(stats['goals_by_status'].values())} total goals")
        
        logger.info("="*70)
        logger.info(f"PAK DISCOVERY CYCLE {self.cycle_count} COMPLETE")
        logger.info("="*70)
    
    def run(self):
        """
        Main daemon loop.
        Run continuous discovery cycles until stopped.
        """
        
        logger.info("\n" + "="*70)
        logger.info("PAK-ENABLED DISCOVERY DAEMON STARTING")
        logger.info("="*70)
        
        # Display self-model identity
        self_model = self.pak_db.get_self_model()
        if self_model:
            logger.info("\nSELF-IDENTITY:")
            logger.info(self_model['identity_statement'][:200] + "...")
        
        # Display initial goals
        goals = self.goal_engine.prioritize_goals()
        logger.info(f"\nACTIVE RESEARCH GOALS: {len(goals)}")
        for i, goal in enumerate(goals[:5], 1):
            logger.info(f"  {i}. [{goal.get('weighted_priority', goal['priority']):.1f}] {goal['title']}")
        
        logger.info(f"\nCycle interval: {self.cycle_interval} seconds ({self.cycle_interval/3600:.1f} hours)")
        logger.info("="*70 + "\n")
        
        self.running = True
        
        while self.running:
            try:
                # Run discovery cycle
                self.run_discovery_cycle()
                
                # Wait for next cycle
                if self.running:
                    logger.info(f"\nWaiting {self.cycle_interval} seconds until next cycle...")
                    logger.info(f"Next cycle at: {datetime.fromtimestamp(time.time() + self.cycle_interval).strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Sleep in chunks to allow quick shutdown
                    sleep_remaining = self.cycle_interval
                    while sleep_remaining > 0 and self.running:
                        sleep_chunk = min(10, sleep_remaining)
                        time.sleep(sleep_chunk)
                        sleep_remaining -= sleep_chunk
            
            except KeyboardInterrupt:
                logger.info("\nKeyboard interrupt detected. Shutting down...")
                break
            
            except Exception as e:
                logger.error(f"Error in discovery cycle: {e}", exc_info=True)
                
                # Record error introspection
                self._introspect(
                    'error_encountered',
                    f"Discovery cycle failed with error: {str(e)}. Continuing operation after delay."
                )
                
                # Wait before retry
                if self.running:
                    logger.info("Waiting 60 seconds before retry...")
                    time.sleep(60)
        
        logger.info("\n" + "="*70)
        logger.info("PAK-ENABLED DISCOVERY DAEMON SHUTDOWN COMPLETE")
        logger.info(f"Total cycles completed: {self.cycle_count}")
        logger.info("="*70)
        
        # Final introspection
        self._introspect(
            'daemon_shutdown',
            f"Daemon shutting down after {self.cycle_count} cycles. "
            f"System state preserved in database."
        )


def main():
    """Main entry point"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='PAK-Enabled Discovery Daemon')
    parser.add_argument(
        '--interval',
        type=int,
        default=3600,
        help='Discovery cycle interval in seconds (default: 3600 = 1 hour)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run single test cycle and exit'
    )
    
    args = parser.parse_args()
    
    daemon = PAKEnabledDiscoveryDaemon(cycle_interval=args.interval)
    
    if args.test:
        logger.info("TEST MODE: Running single cycle")
        daemon.run_discovery_cycle()
        logger.info("Test cycle complete")
    else:
        daemon.run()


if __name__ == '__main__':
    main()
