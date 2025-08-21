"""
Test Advanced Context Understanding
Tests for entity extraction, conversation memory, and semantic understanding.
"""
import unittest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from nlcli.advanced_context import (
    ContextEntity, ConversationTurn, SemanticRelation, EntityExtractor,
    ConversationMemory, AdvancedContextManager, get_advanced_context_manager
)


class TestContextEntity(unittest.TestCase):
    """Test context entity functionality."""
    
    def test_entity_creation(self):
        """Test creating a context entity."""
        entity = ContextEntity(
            name="test.txt",
            entity_type="file",
            confidence=0.8
        )
        
        self.assertEqual(entity.name, "test.txt")
        self.assertEqual(entity.entity_type, "file")
        self.assertEqual(entity.confidence, 0.8)
        self.assertEqual(entity.reference_count, 0)
    
    def test_entity_reference_update(self):
        """Test updating entity reference."""
        entity = ContextEntity(name="test.txt", entity_type="file")
        initial_time = entity.last_referenced
        
        entity.update_reference()
        
        self.assertEqual(entity.reference_count, 1)
        self.assertGreater(entity.last_referenced, initial_time)


class TestEntityExtractor(unittest.TestCase):
    """Test entity extraction functionality."""
    
    def setUp(self):
        self.extractor = EntityExtractor()
    
    def test_file_extraction(self):
        """Test extracting file entities."""
        text = "find all .txt files and show document.pdf"
        entities = self.extractor.extract_entities(text)
        
        file_entities = [e for e in entities if e.entity_type == "file"]
        self.assertGreater(len(file_entities), 0)
        
        file_names = [e.name for e in file_entities]
        self.assertTrue(any(".txt" in name for name in file_names))
    
    def test_directory_extraction(self):
        """Test extracting directory entities."""
        text = "list contents of home directory and check tmp folder"
        entities = self.extractor.extract_entities(text)
        
        dir_entities = [e for e in entities if e.entity_type == "directory"]
        self.assertGreater(len(dir_entities), 0)
    
    def test_size_extraction(self):
        """Test extracting size entities."""
        text = "find files larger than 100MB and smaller than 1GB"
        entities = self.extractor.extract_entities(text)
        
        size_entities = [e for e in entities if e.entity_type == "size"]
        self.assertGreater(len(size_entities), 0)
    
    def test_time_extraction(self):
        """Test extracting time entities."""
        text = "show files modified in the last 7 days"
        entities = self.extractor.extract_entities(text)
        
        time_entities = [e for e in entities if e.entity_type == "time"]
        self.assertGreater(len(time_entities), 0)
    
    def test_process_extraction(self):
        """Test extracting process entities."""
        text = "kill nginx process and stop docker"
        entities = self.extractor.extract_entities(text)
        
        process_entities = [e for e in entities if e.entity_type == "process"]
        self.assertGreater(len(process_entities), 0)
        
        process_names = [e.name for e in process_entities]
        self.assertIn("nginx", process_names)


class TestConversationMemory(unittest.TestCase):
    """Test conversation memory functionality."""
    
    def setUp(self):
        self.memory = ConversationMemory(max_turns=10)
    
    def test_add_entity(self):
        """Test adding entities to memory."""
        entity = ContextEntity(name="test.txt", entity_type="file")
        self.memory.add_entity(entity)
        
        self.assertIn("test.txt", self.memory.entities)
        self.assertEqual(self.memory.entities["test.txt"].entity_type, "file")
    
    def test_update_existing_entity(self):
        """Test updating an existing entity."""
        entity1 = ContextEntity(name="test.txt", entity_type="file", confidence=0.7)
        entity2 = ContextEntity(name="test.txt", entity_type="file", confidence=0.9)
        
        self.memory.add_entity(entity1)
        self.memory.add_entity(entity2)
        
        # Should have higher confidence from second entity
        self.assertEqual(self.memory.entities["test.txt"].confidence, 0.9)
        self.assertEqual(self.memory.entities["test.txt"].reference_count, 1)
    
    def test_add_conversation_turn(self):
        """Test adding conversation turns."""
        turn = ConversationTurn(
            user_input="find large files",
            normalized_input="find large files",
            intent_detected="file_search",
            entities_mentioned=["large", "files"],
            command_generated="find . -size +100M",
            success=True
        )
        
        self.memory.add_turn(turn)
        self.assertEqual(len(self.memory.turns), 1)
    
    def test_get_recent_turns(self):
        """Test getting recent conversation turns."""
        # Add multiple turns
        for i in range(5):
            turn = ConversationTurn(
                user_input=f"command {i}",
                normalized_input=f"command {i}",
                intent_detected="test",
                entities_mentioned=[],
                command_generated=f"echo {i}",
                success=True
            )
            self.memory.add_turn(turn)
        
        recent = self.memory.get_recent_turns(3)
        self.assertEqual(len(recent), 3)
        self.assertEqual(recent[-1].user_input, "command 4")
    
    def test_pronoun_resolution(self):
        """Test pronoun resolution."""
        # Add some entities
        self.memory.add_entity(ContextEntity(name="file1.txt", entity_type="file"))
        self.memory.add_entity(ContextEntity(name="file2.txt", entity_type="file"))
        
        # Add a turn mentioning these entities
        turn = ConversationTurn(
            user_input="list files",
            normalized_input="list files", 
            intent_detected="file_list",
            entities_mentioned=["file1.txt", "file2.txt"],
            command_generated="ls",
            success=True
        )
        self.memory.add_turn(turn)
        
        # Test pronoun resolution
        resolved = self.memory.resolve_pronoun("those", "file")
        self.assertIn("file1.txt", resolved)
        self.assertIn("file2.txt", resolved)
    
    def test_get_relevant_entities(self):
        """Test getting relevant entities."""
        # Add entities with different reference patterns
        entity1 = ContextEntity(name="important.txt", entity_type="file")
        entity2 = ContextEntity(name="old.txt", entity_type="file")
        
        # Make entity1 more relevant
        entity1.reference_count = 5
        entity1.last_referenced = datetime.now()
        
        entity2.reference_count = 1
        entity2.last_referenced = datetime.now() - timedelta(hours=1)
        
        self.memory.add_entity(entity1)
        self.memory.add_entity(entity2)
        
        relevant = self.memory.get_relevant_entities("work with important.txt", limit=5)
        
        # Should prioritize the more relevant entity
        self.assertGreater(len(relevant), 0)
        self.assertEqual(relevant[0].name, "important.txt")


class TestAdvancedContextManager(unittest.TestCase):
    """Test advanced context manager."""
    
    def setUp(self):
        self.manager = AdvancedContextManager()
    
    def test_process_input(self):
        """Test processing user input."""
        basic_context = {"cwd": "/home/user"}
        
        enhanced = self.manager.process_input("find large .txt files", basic_context)
        
        self.assertIn("original_input", enhanced)
        self.assertIn("enhanced_input", enhanced)
        self.assertIn("extracted_entities", enhanced)
        self.assertIn("relevant_entities", enhanced)
        self.assertIn("conversation_context", enhanced)
    
    def test_record_turn(self):
        """Test recording conversation turns."""
        context = {"relevant_entities": [{"name": "test.txt", "type": "file"}]}
        
        self.manager.record_turn(
            user_input="find test.txt",
            enhanced_input="find test.txt",
            intent="file_find",
            command="find . -name test.txt",
            success=True,
            context=context
        )
        
        turns = self.manager.conversation_memory.get_recent_turns(1)
        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0].user_input, "find test.txt")
    
    def test_focus_management(self):
        """Test conversation focus management."""
        self.manager.update_focus("file_operations")
        self.assertEqual(self.manager.current_focus, "file_operations")
    
    def test_context_stack(self):
        """Test context stack operations."""
        context1 = {"operation": "find"}
        context2 = {"operation": "list"}
        
        self.manager.push_context(context1)
        self.manager.push_context(context2)
        
        popped = self.manager.pop_context()
        self.assertEqual(popped["operation"], "list")
        
        popped = self.manager.pop_context()
        self.assertEqual(popped["operation"], "find")
        
        # Stack should be empty now
        self.assertIsNone(self.manager.pop_context())
    
    def test_conversation_history(self):
        """Test getting conversation history."""
        # Record multiple turns
        for i in range(3):
            self.manager.record_turn(
                user_input=f"command {i}",
                enhanced_input=f"command {i}",
                intent=f"intent_{i}",
                command=f"echo {i}",
                success=True,
                context={}
            )
        
        history = self.manager.get_conversation_history(5)
        self.assertEqual(len(history), 3)
        self.assertTrue(all("input" in turn for turn in history))
        self.assertTrue(all("timestamp" in turn for turn in history))
    
    def test_pattern_analysis(self):
        """Test conversation pattern analysis."""
        # Record some turns with different patterns
        for i in range(5):
            success = i % 2 == 0  # Alternate success/failure
            self.manager.record_turn(
                user_input=f"find files {i}",
                enhanced_input=f"find files {i}",
                intent="file_find",
                command=f"find . -name '*{i}*'",
                success=success,
                context={}
            )
        
        patterns = self.manager.analyze_patterns()
        
        self.assertIn("patterns", patterns)
        self.assertIn("insights", patterns)
        self.assertIn("success_rate", patterns["patterns"])
        self.assertIn("total_turns", patterns["patterns"])
    
    def test_global_manager_singleton(self):
        """Test global manager singleton."""
        manager1 = get_advanced_context_manager()
        manager2 = get_advanced_context_manager()
        
        self.assertIs(manager1, manager2)


if __name__ == '__main__':
    unittest.main()