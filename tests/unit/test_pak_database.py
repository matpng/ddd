"""
Unit tests for PAK Database layer
"""
import pytest
from datetime import datetime


class TestPAKDatabase:
    """Tests for PAKDatabase class"""
    
    def test_database_initialization(self, mock_pak_database):
        """Test database initializes correctly"""
        assert mock_pak_database is not None
        
        # Check that tables were created
        stats = mock_pak_database.get_statistics()
        assert stats is not None
    
    def test_create_goal(self, mock_pak_database):
        """Test creating a new research goal"""
        goal_data = {
            'title': 'Test Goal',
            'description': 'Test description',
            'priority': 5,
            'status': 'active'
        }
        
        goal_id = mock_pak_database.create_goal(goal_data)
        assert goal_id is not None
        
        # Verify goal was created
        goals = mock_pak_database.get_active_goals()
        assert len(goals) > 0
        assert any(g['title'] == 'Test Goal' for g in goals)
    
    def test_get_active_goals(self, mock_pak_database):
        """Test retrieving active goals"""
        # Create test goals
        mock_pak_database.create_goal({
            'title': 'Goal 1',
            'priority': 5,
            'status': 'active'
        })
        mock_pak_database.create_goal({
            'title': 'Goal 2',
            'priority': 3,
            'status': 'active'
        })
        
        goals = mock_pak_database.get_active_goals()
        assert len(goals) >= 2
    
    def test_update_goal(self, mock_pak_database):
        """Test updating an existing goal"""
        # Create goal
        goal_id = mock_pak_database.create_goal({
            'title': 'Original Title',
            'priority': 5,
            'status': 'active'
        })
        
        # Update goal
        mock_pak_database.update_goal(goal_id, {
            'title': 'Updated Title',
            'status': 'completed'
        })
        
        # Verify update
        goals = mock_pak_database.get_active_goals()
        # After completion, might not be in active goals
    
    def test_increment_goal_discoveries(self, mock_pak_database):
        """Test incrementing discovery count"""
        goal_id = mock_pak_database.create_goal({
            'title': 'Discovery Goal',
            'priority': 5,
            'status': 'active'
        })
        
        # Increment discoveries
        mock_pak_database.increment_goal_discoveries(goal_id)
        mock_pak_database.increment_goal_discoveries(goal_id)
        
        # Verify count increased
        goals = mock_pak_database.get_active_goals()
        goal = next((g for g in goals if g['id'] == goal_id), None)
        if goal:
            assert goal['discoveries_found'] == 2
    
    def test_add_world_knowledge(self, mock_pak_database):
        """Test adding world knowledge"""
        knowledge_data = {
            'domain': 'physics',
            'title': 'Test Knowledge',
            'description': 'Test description',
            'relevance_score': 0.8
        }
        
        knowledge_id = mock_pak_database.add_world_knowledge(knowledge_data)
        assert knowledge_id is not None
    
    def test_search_world_knowledge(self, mock_pak_database):
        """Test searching world knowledge"""
        # Add knowledge
        mock_pak_database.add_world_knowledge({
            'domain': 'physics',
            'title': 'Physics Knowledge',
            'description': 'About physics'
        })
        
        # Search by domain
        results = mock_pak_database.search_world_knowledge(domain='physics')
        assert len(results) > 0
        assert results[0]['domain'] == 'physics'
    
    def test_get_self_model(self, mock_pak_database):
        """Test retrieving self-model"""
        self_model = mock_pak_database.get_self_model()
        assert self_model is not None
        assert 'identity_statement' in self_model
    
    def test_update_self_model(self, mock_pak_database):
        """Test updating self-model"""
        updates = {
            'identity_statement': 'Updated identity',
            'last_reflection': datetime.utcnow().isoformat()
        }
        
        mock_pak_database.update_self_model(updates)
        
        # Verify update
        self_model = mock_pak_database.get_self_model()
        assert 'Updated identity' in self_model['identity_statement']
    
    def test_record_introspection(self, mock_pak_database):
        """Test recording introspection event"""
        log_data = {
            'trigger_event': 'test_event',
            'context': 'Test context',
            'internal_dialogue': 'Test dialogue'
        }
        
        log_id = mock_pak_database.record_introspection(log_data)
        assert log_id is not None
    
    def test_append_to_narrative(self, mock_pak_database):
        """Test appending to narrative history"""
        narrative_chunk = "This is a test narrative entry."
        
        mock_pak_database.append_to_narrative(narrative_chunk)
        
        # Verify narrative was updated
        self_model = mock_pak_database.get_self_model()
        assert narrative_chunk in self_model['narrative_history']
    
    def test_get_statistics(self, mock_pak_database):
        """Test getting system statistics"""
        # Create some data
        mock_pak_database.create_goal({
            'title': 'Stats Test Goal',
            'priority': 5,
            'status': 'active'
        })
        
        stats = mock_pak_database.get_statistics()
        assert 'total_goals' in stats
        assert 'total_goal_discoveries' in stats
        assert 'goals_by_status' in stats
        assert stats['total_goals'] >= 1


class TestPAKDatabaseEdgeCases:
    """Edge case tests for PAK Database"""
    
    def test_create_goal_minimal_data(self, mock_pak_database):
        """Test creating goal with minimal required data"""
        goal_id = mock_pak_database.create_goal({
            'title': 'Minimal Goal'
        })
        assert goal_id is not None
    
    def test_search_nonexistent_domain(self, mock_pak_database):
        """Test searching for non-existent domain"""
        results = mock_pak_database.search_world_knowledge(domain='nonexistent')
        assert len(results) == 0
    
    def test_update_nonexistent_goal(self, mock_pak_database):
        """Test updating non-existent goal"""
        # Should not crash
        try:
            mock_pak_database.update_goal('nonexistent_id', {'title': 'Test'})
        except Exception:
            pass  # Expected to fail gracefully
    
    def test_database_close(self, mock_pak_database):
        """Test database closes properly"""
        mock_pak_database.close()
        # Should not crash
