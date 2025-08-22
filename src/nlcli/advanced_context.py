"""
Advanced Context Understanding
Enhanced context management with semantic understanding.
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class ContextEntity:
    """Represents an entity mentioned in conversation."""

    name: str
    entity_type: str  # file, directory, process, container, etc.
    attributes: Dict[str, Any] = field(default_factory=dict)
    first_mentioned: datetime = field(default_factory=datetime.now)
    last_referenced: datetime = field(default_factory=datetime.now)
    reference_count: int = 0
    confidence: float = 1.0

    def update_reference(self):
        """Update when entity was last referenced."""
        self.last_referenced = datetime.now()
        self.reference_count += 1


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation."""

    user_input: str
    normalized_input: str
    intent_detected: Optional[str]
    entities_mentioned: List[str]
    command_generated: Optional[str]
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    context_used: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticRelation:
    """Represents a semantic relationship between entities or concepts."""

    source: str
    target: str
    relation_type: str  # contains, parent_of, similar_to, follows, etc.
    strength: float = 1.0
    created: datetime = field(default_factory=datetime.now)


class EntityExtractor:
    """Extracts entities from user input."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Patterns for different entity types
        self.entity_patterns = {
            "file": [
                r"\b([^\s]+\.(?:txt|pdf|doc|docx|py|js|html|css|json|xml|"
                r"log|md))\b",
                r"(?:file|document)s?\s+(?:named|called)?\s*([^\s]+\."
                r"[a-zA-Z]{1,4})",
                r"([^\s]+\.[a-zA-Z]{1,4})\s+(?:file|document)s?",
                r"(?:all\s+)?(\.[a-zA-Z]{2,4})\s+files?",  # ".txt files"
            ],
            "directory": [
                r"(?:directory|folder|dir)\s+(?:named|called)?\s*([^\s]+)",
                r"([^\s]+)\s+(?:directory|folder|dir)",
                r"\bin\s+(?:the\s+)?([^\s/]+)/?(?:\s|$)",
            ],
            "process": [
                r"(?:process|pid)\s+(?:named|called)?\s*([^\s]+)",
                r"([^\s]+)\s+(?:process|pid)",
                r"(?:kill|stop|terminate)\s+([^\s]+)",
            ],
            "container": [
                r"(?:container|docker)\s+(?:named|called)?\s*([^\s]+)",
                r"([^\s]+)\s+(?:container)",
            ],
            "size": [
                r"(\d+(?:\.\d+)?\s*(?:b|kb|mb|gb|tb))",
                r"(?:larger|bigger|greater)\s+than\s+"
                r"(\d+(?:\.\d+)?\s*(?:b|kb|mb|gb|tb))",
                r"(?:smaller|less)\s+than\s+" r"(\d+(?:\.\d+)?\s*(?:b|kb|mb|gb|tb))",
            ],
            "time": [
                r"(?:in\s+the\s+)?(?:last|past)\s+(\d+)\s+"
                r"(seconds?|minutes?|hours?|days?|weeks?|months?)",
                r"(?:modified|changed|created)\s+(?:in\s+the\s+)?"
                r"(?:last\s+)?(\w+(?:\s+\w+)?)",
                r"(today|yesterday|this\s+week|last\s+week|this\s+month)",
            ],
        }

    def extract_entities(self, text: str) -> List[ContextEntity]:
        """Extract entities from text."""
        entities = []
        text_lower = text.lower()

        import re

        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match else ""

                    if match and len(match.strip()) > 0:
                        entity = ContextEntity(
                            name=match.strip(),
                            entity_type=entity_type,
                            confidence=0.7,  # Pattern-based extraction
                        )
                        entities.append(entity)

        return entities


class ConversationMemory:
    """Manages conversation history and context."""

    def __init__(self, max_turns: int = 50):
        self.max_turns = max_turns
        self.turns: deque = deque(maxlen=max_turns)
        self.entities: Dict[str, ContextEntity] = {}
        self.relations: List[SemanticRelation] = []
        self.logger = logging.getLogger(__name__)

    def add_turn(self, turn: ConversationTurn) -> None:
        """Add a conversation turn."""
        self.turns.append(turn)

        # Update entity references
        for entity_name in turn.entities_mentioned:
            if entity_name in self.entities:
                self.entities[entity_name].update_reference()

    def add_entity(self, entity: ContextEntity) -> None:
        """Add or update an entity."""
        if entity.name in self.entities:
            # Update existing entity
            existing = self.entities[entity.name]
            existing.update_reference()
            existing.confidence = max(existing.confidence, entity.confidence)
            existing.attributes.update(entity.attributes)
        else:
            self.entities[entity.name] = entity

    def add_relation(self, relation: SemanticRelation) -> None:
        """Add a semantic relation."""
        self.relations.append(relation)

    def get_recent_turns(self, count: int = 5) -> List[ConversationTurn]:
        """Get recent conversation turns."""
        return list(self.turns)[-count:]

    def get_relevant_entities(self, text: str, limit: int = 10) -> List[ContextEntity]:
        """Get entities relevant to the current text."""
        text_lower = text.lower()
        scored_entities = []

        for entity in self.entities.values():
            score = 0.0

            # Direct mention
            if entity.name.lower() in text_lower:
                score += 1.0

            # Recent reference bonus
            time_since_reference = datetime.now() - entity.last_referenced
            if time_since_reference < timedelta(minutes=5):
                score += 0.5
            elif time_since_reference < timedelta(minutes=30):
                score += 0.2

            # Frequency bonus
            score += min(entity.reference_count * 0.1, 0.5)

            # Confidence factor
            score *= entity.confidence

            if score > 0:
                scored_entities.append((entity, score))

        # Sort by score and return top entities
        scored_entities.sort(key=lambda x: x[1], reverse=True)
        return [entity for entity, score in scored_entities[:limit]]

    def resolve_pronoun(
        self, pronoun: str, context_type: Optional[str] = None
    ) -> List[str]:
        """Resolve pronouns to specific entities."""
        pronoun_lower = pronoun.lower()

        # Get recently mentioned entities
        recent_entities = []

        # Look at last few turns
        recent_turns = self.get_recent_turns(3)
        for turn in reversed(recent_turns):
            recent_entities.extend(turn.entities_mentioned)

        # Filter by type if specified
        if context_type:
            filtered_entities = []
            for entity_name in recent_entities:
                if entity_name in self.entities:
                    entity = self.entities[entity_name]
                    if entity.entity_type == context_type:
                        filtered_entities.append(entity_name)
            recent_entities = filtered_entities

        # Return based on pronoun type
        if pronoun_lower in ["those", "them", "these"]:
            return recent_entities[:5]  # Multiple entities
        elif pronoun_lower in ["that", "it", "this"]:
            return recent_entities[:1]  # Single entity
        elif pronoun_lower == "same":
            return recent_entities[:3]  # Same as before

        return recent_entities[:3]

    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of current context."""
        return {
            "total_turns": len(self.turns),
            "total_entities": len(self.entities),
            "recent_entities": [e.name for e in self.get_relevant_entities("", 5)],
            "entity_types": list(set(e.entity_type for e in self.entities.values())),
            "relations_count": len(self.relations),
        }


class AdvancedContextManager:
    """Advanced context manager with semantic understanding."""

    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.conversation_memory = ConversationMemory()
        self.current_focus: Optional[str] = None
        self.context_stack: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)

    def process_input(
        self, user_input: str, basic_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process user input and enhance with advanced context understanding."""
        # Extract entities from input
        entities = self.entity_extractor.extract_entities(user_input)

        # Add entities to memory
        for entity in entities:
            self.conversation_memory.add_entity(entity)

        # Resolve pronouns
        enhanced_input = self._resolve_pronouns_advanced(user_input)

        # Get relevant entities
        relevant_entities = self.conversation_memory.get_relevant_entities(user_input)

        # Build enhanced context
        enhanced_context = basic_context.copy()
        enhanced_context.update(
            {
                "original_input": user_input,
                "enhanced_input": enhanced_input,
                "extracted_entities": [e.name for e in entities],
                "relevant_entities": [
                    {
                        "name": e.name,
                        "type": e.entity_type,
                        "confidence": e.confidence,
                        "attributes": e.attributes,
                    }
                    for e in relevant_entities
                ],
                "conversation_context": self.conversation_memory.get_context_summary(),
                "current_focus": self.current_focus,
            }
        )

        return enhanced_context

    def record_turn(
        self,
        user_input: str,
        enhanced_input: str,
        intent: Optional[str],
        command: Optional[str],
        success: bool,
        context: Dict[str, Any],
    ) -> None:
        """Record a conversation turn."""
        entities_mentioned = [e["name"] for e in context.get("relevant_entities", [])]

        turn = ConversationTurn(
            user_input=user_input,
            normalized_input=enhanced_input,
            intent_detected=intent,
            entities_mentioned=entities_mentioned,
            command_generated=command,
            success=success,
            context_used=context,
        )

        self.conversation_memory.add_turn(turn)

    def _resolve_pronouns_advanced(self, text: str) -> str:
        """Advanced pronoun resolution using conversation memory."""
        # Simple pronoun mapping
        pronouns = {
            "those": "file",
            "them": "file",
            "these": "file",
            "that": "file",
            "it": "file",
            "this": "file",
        }

        enhanced_text = text

        for pronoun, entity_type in pronouns.items():
            if pronoun in text.lower():
                resolved_entities = self.conversation_memory.resolve_pronoun(
                    pronoun, entity_type
                )
                if resolved_entities:
                    # Replace pronoun with resolved entities
                    replacement = " ".join(resolved_entities[:3])  # Max 3 entities
                    enhanced_text = enhanced_text.replace(pronoun, replacement)

        return enhanced_text

    def update_focus(self, focus: str) -> None:
        """Update current conversation focus."""
        self.current_focus = focus
        self.logger.info(f"Updated conversation focus to: {focus}")

    def push_context(self, context: Dict[str, Any]) -> None:
        """Push context onto the stack for nested operations."""
        self.context_stack.append(context)

    def pop_context(self) -> Optional[Dict[str, Any]]:
        """Pop context from the stack."""
        return self.context_stack.pop() if self.context_stack else None

    def get_conversation_history(self, turns: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for analysis."""
        recent_turns = self.conversation_memory.get_recent_turns(turns)
        return [
            {
                "input": turn.user_input,
                "enhanced_input": turn.normalized_input,
                "intent": turn.intent_detected,
                "command": turn.command_generated,
                "success": turn.success,
                "timestamp": turn.timestamp.isoformat(),
            }
            for turn in recent_turns
        ]

    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze conversation patterns for insights."""
        turns = list(self.conversation_memory.turns)

        if not turns:
            return {"patterns": [], "insights": []}

        # Analyze command patterns
        commands = [turn.command_generated for turn in turns if turn.command_generated]
        command_frequency = {}
        for cmd in commands:
            base_cmd = cmd.split()[0] if cmd else ""
            command_frequency[base_cmd] = command_frequency.get(base_cmd, 0) + 1

        # Analyze entity patterns
        entity_types = {}
        for entity in self.conversation_memory.entities.values():
            entity_types[entity.entity_type] = (
                entity_types.get(entity.entity_type, 0) + 1
            )

        # Success rate
        successful_turns = sum(1 for turn in turns if turn.success)
        success_rate = successful_turns / len(turns) if turns else 0

        insights = []
        if success_rate < 0.7:
            insights.append("Consider providing more specific commands")

        most_used_cmd = (
            max(command_frequency.items(), key=lambda x: x[1])
            if command_frequency
            else None
        )
        if most_used_cmd:
            insights.append(f"Most frequently used command: {most_used_cmd[0]}")

        return {
            "patterns": {
                "command_frequency": command_frequency,
                "entity_types": entity_types,
                "success_rate": success_rate,
                "total_turns": len(turns),
            },
            "insights": insights,
        }


# Global advanced context manager
_advanced_context_manager: Optional[AdvancedContextManager] = None


def get_advanced_context_manager() -> AdvancedContextManager:
    """Get the global advanced context manager instance."""
    global _advanced_context_manager
    if _advanced_context_manager is None:
        _advanced_context_manager = AdvancedContextManager()
    return _advanced_context_manager
