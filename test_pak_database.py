#!/usr/bin/env python3
"""
Test PAK Database Methods
Verifies all newly added database methods work correctly
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pak_database import PAKDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_initialization():
    """Test that all tables are created"""
    print("\n" + "="*70)
    print("TEST 1: Database Initialization")
    print("="*70)
    
    # Remove old test database
    test_db = 'test_pak.db'
    if os.path.exists(test_db):
        os.remove(test_db)
    
    db = PAKDatabase(test_db)
    
    # Check tables exist
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = [
        'research_goals', 'research_values', 'value_conflicts',
        'world_knowledge', 'self_model', 'introspection_logs',
        'research_agendas'
    ]
    
    for table in expected_tables:
        if table in tables:
            print(f"  ✓ Table '{table}' created")
        else:
            print(f"  ✗ Table '{table}' MISSING")
            return False
    
    print("  ✓ All tables created successfully")
    return True


def test_research_agenda_methods(db):
    """Test create_research_agenda()"""
    print("\n" + "="*70)
    print("TEST 2: Research Agenda Methods")
    print("="*70)
    
    agenda_data = {
        'title': 'Test Research Agenda',
        'description': 'Testing agenda creation',
        'motivation': 'Verify database methods work',
        'domain': 'testing',
        'research_questions': ['Question 1', 'Question 2'],
        'progress_milestones': [
            {'task': 'Test 1', 'status': 'complete'},
            {'task': 'Test 2', 'status': 'pending'}
        ],
        'created_by': 'test_script'
    }
    
    agenda_id = db.create_research_agenda(agenda_data)
    print(f"  ✓ Created research agenda: {agenda_id}")
    
    # Verify it was saved
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM research_agendas WHERE id = ?", (agenda_id,))
        row = cursor.fetchone()
        
        if row:
            print(f"  ✓ Agenda retrieved from database")
            title = row['title'] if isinstance(row, dict) else row[2]
            print(f"    Title: {title}")
            return True
        else:
            print(f"  ✗ Agenda NOT found in database")
            return False


def test_introspection_methods(db):
    """Test record_introspection() and append_to_narrative()"""
    print("\n" + "="*70)
    print("TEST 3: Introspection Methods")
    print("="*70)
    
    # Test record_introspection
    log_data = {
        'trigger_event': 'test_event',
        'internal_dialogue': 'Testing introspection logging',
        'key_realizations': 'Database methods work',
        'concerns': 'None',
        'proposed_actions': 'Continue testing'
    }
    
    log_id = db.record_introspection(log_data)
    print(f"  ✓ Recorded introspection: {log_id}")
    
    # Verify it was saved
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM introspection_logs WHERE id = ?", (log_id,))
        row = cursor.fetchone()
        
        if row:
            print(f"  ✓ Introspection log retrieved from database")
        else:
            print(f"  ✗ Introspection log NOT found")
            return False
    
    # Test append_to_narrative
    db.append_to_narrative("Test narrative chunk: database methods verified")
    print(f"  ✓ Appended to narrative")
    
    # Verify narrative was updated
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT narrative_history FROM self_model WHERE id = 'ORION_OCTAVE_MIND'")
        row = cursor.fetchone()
        
        if row:
            narrative = row['narrative_history'] if isinstance(row, dict) else row[0]
            if narrative and 'database methods verified' in narrative:
                print(f"  ✓ Narrative updated successfully")
                return True
            else:
                print(f"  ✗ Narrative NOT updated")
                return False
        else:
            print(f"  ✗ Self-model not found")
            return False


def test_goal_discovery_methods(db):
    """Test increment_goal_discoveries()"""
    print("\n" + "="*70)
    print("TEST 4: Goal Discovery Methods")
    print("="*70)
    
    # Create a test goal
    goal_data = {
        'title': 'Test Goal',
        'description': 'Testing goal discovery tracking',
        'created_by': 'test_script'
    }
    
    goal_id = db.create_goal(goal_data)
    print(f"  ✓ Created test goal: {goal_id}")
    
    # Increment discoveries
    db.increment_goal_discoveries(goal_id)
    db.increment_goal_discoveries(goal_id)
    db.increment_goal_discoveries(goal_id)
    print(f"  ✓ Incremented discoveries 3 times")
    
    # Verify count
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT discoveries_found FROM research_goals WHERE id = ?", (goal_id,))
        row = cursor.fetchone()
        
        if row:
            count = row['discoveries_found'] if isinstance(row, dict) else row[0]
            if count == 3:
                print(f"  ✓ Discovery count is correct: {count}")
                return True
            else:
                print(f"  ✗ Discovery count wrong: {count} (expected 3)")
                return False
        else:
            print(f"  ✗ Goal not found")
            return False


def test_statistics_method(db):
    """Test get_statistics()"""
    print("\n" + "="*70)
    print("TEST 5: Statistics Method")
    print("="*70)
    
    stats = db.get_statistics()
    
    print(f"  Statistics retrieved:")
    print(f"    Goals by status: {stats.get('goals_by_status', {})}")
    print(f"    Total goal discoveries: {stats.get('total_goal_discoveries', 0)}")
    print(f"    World knowledge entries: {stats.get('world_knowledge_entries', 0)}")
    print(f"    Active research agendas: {stats.get('active_research_agendas', 0)}")
    print(f"    Introspection count: {stats.get('introspection_count', 0)}")
    
    # Verify structure
    expected_keys = [
        'goals_by_status', 'total_goal_discoveries',
        'world_knowledge_entries', 'active_research_agendas',
        'introspection_count'
    ]
    
    for key in expected_keys:
        if key in stats:
            print(f"  ✓ Statistic '{key}' present")
        else:
            print(f"  ✗ Statistic '{key}' MISSING")
            return False
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("PAK DATABASE TESTS")
    print("="*70)
    
    # Initialize database
    test_db = 'test_pak.db'
    
    results = []
    
    # Test 1: Database initialization
    if test_database_initialization():
        results.append(("Database Initialization", True))
    else:
        results.append(("Database Initialization", False))
        print("\n⚠️  Cannot continue - database initialization failed")
        return
    
    # Create db instance for remaining tests
    db = PAKDatabase(test_db)
    
    # Test 2: Research agenda methods
    results.append(("Research Agenda Methods", test_research_agenda_methods(db)))
    
    # Test 3: Introspection methods
    results.append(("Introspection Methods", test_introspection_methods(db)))
    
    # Test 4: Goal discovery methods
    results.append(("Goal Discovery Methods", test_goal_discovery_methods(db)))
    
    # Test 5: Statistics method
    results.append(("Statistics Method", test_statistics_method(db)))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 ALL TESTS PASSED! Database methods are working correctly.")
        return 0
    else:
        print(f"\n  ⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
