# Memory System for Legal Assistant

This memory module provides comprehensive short-term and long-term memory capabilities for the legal assistant using BGE-M3 embeddings and Chroma vector storage.

## Features

### Short-Term Memory
- **Conversation History**: Maintains recent conversation turns with semantic search
- **Session Context**: Tracks legal domain, case type, jurisdiction, and topics
- **Temporary Storage**: Stores temporary data with TTL (time-to-live)
- **Semantic Search**: Find relevant conversation turns using BGE-M3 embeddings

### Long-Term Memory
- **User Profiles**: Persistent user preferences, expertise level, and legal domains
- **Interaction History**: Stores all user interactions with metadata
- **Legal Knowledge Base**: Stores and retrieves legal concepts and definitions
- **Analytics**: Provides insights into user behavior and system usage

### Memory Manager
- **Unified Interface**: Coordinates between short-term and long-term memory
- **Contextual Information**: Provides comprehensive context for queries
- **Auto-categorization**: Automatically categorizes interactions by legal domain

## Installation

Install the required dependencies:

```bash
pip install chromadb FlagEmbedding
```

## Quick Start

```python
from memory import MemoryManager

# Initialize memory manager
memory = MemoryManager(
    storage_path="./memory_data",
    user_id="user123"
)

# Add a conversation turn
memory.add_conversation_turn(
    user_input="What are the elements of a contract?",
    ai_response="A contract requires offer, acceptance, consideration, and capacity.",
    legal_domain="contract law",
    topics=["contract elements", "offer", "acceptance"]
)

# Search memory
results = memory.search_memory("contract elements")

# Get contextual information for a query
context = memory.get_contextual_information("What makes a contract valid?")
```

## Core Components

### 1. ShortTermMemory

Manages conversation context and immediate session memory.

```python
from memory import ShortTermMemory

short_memory = ShortTermMemory(window_size=10)

# Add conversation turn
turn_id = short_memory.add_message(
    user_input="Hello",
    ai_response="Hi there!",
    metadata={"topic": "greeting"}
)

# Search conversation
results = short_memory.search_conversation_semantic("greeting")

# Get conversation history
history = short_memory.get_conversation_text()
```

### 2. LongTermMemory

Handles persistent storage and retrieval.

```python
from memory import LongTermMemory

long_memory = LongTermMemory(storage_path="./storage")

# Store interaction
long_memory.store_interaction(
    user_id="user123",
    user_input="What is tort law?",
    ai_response="Tort law deals with civil wrongs...",
    legal_domain="tort law"
)

# Search similar interactions
results = long_memory.search_similar_interactions("tort law")

# Store legal concept
long_memory.store_legal_concept(
    concept_name="Negligence",
    definition="Failure to exercise reasonable care",
    legal_domain="tort law"
)
```

### 3. MemoryManager

Unified interface combining both memory systems.

```python
from memory import MemoryManager

manager = MemoryManager(user_id="user123")

# Add conversation with automatic categorization
manager.add_conversation_turn(
    user_input="Can I break this contract?",
    ai_response="Contract termination depends on several factors...",
    legal_domain="contract law",
    case_type="termination",
    satisfaction_score=0.9
)

# Get comprehensive context
context = manager.get_contextual_information("contract termination")
```

## Data Models

### ConversationTurn
```python
@dataclass
class ConversationTurn:
    timestamp: datetime
    user_input: str
    ai_response: str
    turn_id: str
    metadata: Optional[Dict[str, Any]] = None
```

### UserProfile
```python
@dataclass
class UserProfile:
    user_id: str
    creation_date: datetime
    last_active: datetime
    preferences: Dict[str, Any]
    expertise_level: str  # beginner, intermediate, expert
    legal_domains: List[str]
    interaction_count: int
    satisfaction_avg: Optional[float] = None
```

### SessionContext
```python
@dataclass
class SessionContext:
    session_id: str
    start_time: datetime
    legal_domain: Optional[str] = None
    case_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    current_topics: List[str] = None
    user_preferences: Dict[str, Any] = None
    active_documents: List[str] = None
```

## Advanced Usage

### Custom Embeddings Model
```python
# Use a different BGE model
memory = MemoryManager(
    embedding_model_path="BAAI/bge-large-en-v1.5"
)
```

### Memory Analytics
```python
# Get memory statistics
stats = memory.get_memory_summary()
print(f"Total interactions: {stats['user_profile']['total_interactions']}")
print(f"Session duration: {stats['session']['session_duration']}")
```

### Temporary Data Storage
```python
# Store temporary data with TTL
memory.store_temporary_data("draft_document", document_data, ttl_minutes=60)

# Retrieve temporary data
draft = memory.get_temporary_data("draft_document")
```

### Legal Knowledge Management
```python
# Store legal concepts
memory.store_legal_concept(
    concept_name="Strict Liability",
    definition="Liability without fault",
    legal_domain="tort law",
    examples=["Product liability", "Abnormally dangerous activities"],
    related_concepts=["negligence", "intentional torts"]
)

# Search legal knowledge
concepts = memory.search_legal_knowledge("liability")
```

### User Preference Management
```python
# Update user preferences
memory.update_user_preferences({
    "explanation_style": "detailed",
    "jurisdiction": "US Federal",
    "notification_preferences": {"email": True}
})

# Update expertise level
memory.update_user_expertise(
    expertise_level="intermediate",
    legal_domains=["contract law", "tort law"]
)
```

## Storage Structure

The memory system creates the following storage structure:

```
memory_storage/
├── memory.db                 # SQLite database for structured data
├── chroma_db/               # Chroma vector database
│   ├── interactions/        # Conversation embeddings
│   └── legal_knowledge/     # Legal concept embeddings
└── temp/                    # Temporary session data
```

## Performance Considerations

- **Embedding Model**: BGE-M3 provides excellent multilingual support
- **Vector Storage**: Chroma offers efficient similarity search
- **Memory Management**: Automatic cleanup of expired temporary data
- **Scalability**: Designed to handle thousands of interactions per user

## Example Workflow

```python
# 1. Initialize system
memory = MemoryManager(user_id="lawyer_123")

# 2. Handle user interaction
memory.add_conversation_turn(
    user_input="I need help with a breach of contract case",
    ai_response="I can help you with contract law. Let me ask some questions...",
    legal_domain="contract law",
    case_type="breach of contract"
)

# 3. Get relevant context for next response
context = memory.get_contextual_information("What damages can I claim?")

# 4. Use context to inform AI response
relevant_past = context['relevant_interactions']
user_expertise = context['user_profile']['expertise_level']
recent_conversation = context['recent_conversation']

# 5. Store the new interaction
memory.add_conversation_turn(
    user_input="What damages can I claim?",
    ai_response="For breach of contract, you may claim compensatory damages...",
    legal_domain="contract law",
    case_type="damages",
    topics=["damages", "compensation", "breach"]
)
```

## Error Handling

The memory system includes robust error handling:

```python
try:
    memory = MemoryManager(user_id="user123")
    memory.add_conversation_turn(user_input, ai_response)
except Exception as e:
    print(f"Memory error: {e}")
    # Fallback to stateless operation
```

## Testing

Run the example usage:

```bash
cd backend/memory
python example_usage.py
```

This will demonstrate all major features of the memory system.
