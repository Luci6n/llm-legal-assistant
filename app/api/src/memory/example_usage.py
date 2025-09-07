"""
Example usage of the memory system for the legal assistant.
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory import MemoryManager


def example_usage():
    """Demonstrate how to use the memory system."""
    
    # Initialize memory manager
    print("Initializing memory manager...")
    memory_manager = MemoryManager(
        storage_path="./example_memory",
        user_id="example_user_123"
    )
    
    print("Memory manager initialized successfully!")
    
    # Simulate a legal conversation
    print("\n--- Starting Legal Consultation ---")
    
    # First interaction - contract law question
    print("\nUser asks about contract law...")
    turn_id_1 = memory_manager.add_conversation_turn(
        user_input="What are the essential elements of a valid contract?",
        ai_response="A valid contract requires four essential elements: 1) Offer - a clear proposal by one party, 2) Acceptance - agreement to the offer by the other party, 3) Consideration - something of value exchanged, and 4) Legal capacity - parties must be legally able to enter contracts.",
        legal_domain="contract law",
        case_type="general inquiry",
        topics=["contract elements", "offer", "acceptance", "consideration"],
        satisfaction_score=0.9
    )
    
    # Second interaction - follow-up question
    print("User asks follow-up question...")
    turn_id_2 = memory_manager.add_conversation_turn(
        user_input="Can you explain consideration in more detail?",
        ai_response="Consideration is the exchange of something of value between parties. It can be money, goods, services, or even a promise to do or not do something. For example, in a sales contract, the buyer's money is consideration for the seller's goods. Consideration must be legally sufficient but doesn't need to be economically adequate.",
        legal_domain="contract law",
        case_type="clarification",
        topics=["consideration", "contract law", "value exchange"],
        satisfaction_score=0.95
    )
    
    # Third interaction - different domain
    print("User asks about criminal law...")
    turn_id_3 = memory_manager.add_conversation_turn(
        user_input="What is the difference between assault and battery?",
        ai_response="Assault and battery are often confused but are distinct: Assault is the intentional threat or attempt to cause harmful contact with another person, creating fear of imminent harm. Battery is the actual intentional harmful or offensive physical contact. You can have assault without battery (threatening someone) or battery without assault (hitting someone from behind).",
        legal_domain="criminal law",
        case_type="definition inquiry",
        topics=["assault", "battery", "criminal law", "physical contact"],
        satisfaction_score=0.85
    )
    
    # Demonstrate memory search capabilities
    print("\n--- Testing Memory Search ---")
    
    # Search for contract-related information
    print("\nSearching for 'contract elements'...")
    search_results = memory_manager.search_memory(
        query="contract elements",
        k_short=2,
        k_long=3
    )
    
    print(f"Short-term results: {len(search_results['short_term'])}")
    if search_results['short_term']:
        print(f"Most relevant: {search_results['short_term'][0]['content'][:100]}...")
    
    print(f"Long-term results: {len(search_results['long_term'])}")
    
    # Store a legal concept
    print("\nStoring legal concept...")
    memory_manager.store_legal_concept(
        concept_name="Consideration",
        definition="Something of value exchanged between parties in a contract",
        legal_domain="contract law",
        examples=[
            "Money paid for goods",
            "Promise to provide services",
            "Agreement not to compete"
        ],
        related_concepts=["offer", "acceptance", "contract formation"]
    )
    
    # Search legal knowledge
    print("\nSearching legal knowledge...")
    knowledge_results = memory_manager.search_legal_knowledge("consideration contract")
    print(f"Found {len(knowledge_results)} knowledge results")
    
    # Get contextual information for a new query
    print("\n--- Getting Contextual Information ---")
    context = memory_manager.get_contextual_information("What makes a contract enforceable?")
    
    print(f"Recent conversation length: {len(context['recent_conversation'])}")
    print(f"Relevant interactions: {len(context['relevant_interactions']['short_term'])} short, {len(context['relevant_interactions']['long_term'])} long")
    print(f"Legal knowledge results: {len(context['legal_knowledge'])}")
    print(f"User expertise level: {context['user_profile']['expertise_level']}")
    
    # Get memory summary
    print("\n--- Memory Summary ---")
    summary = memory_manager.get_memory_summary()
    
    print(f"Session turns: {summary['session']['conversation_turns']}")
    print(f"Session duration: {summary['session']['session_duration']}")
    print(f"User total interactions: {summary['user_profile']['total_interactions']}")
    print(f"Legal domains: {summary['user_profile']['legal_domains']}")
    
    # Update user preferences
    print("\n--- Updating User Preferences ---")
    memory_manager.update_user_preferences({
        "preferred_explanation_style": "detailed",
        "jurisdiction_focus": "US Federal",
        "notification_preferences": {"email": True, "sms": False}
    })
    
    # Update expertise
    memory_manager.update_user_expertise(
        expertise_level="intermediate",
        legal_domains=["contract law", "criminal law"]
    )
    
    print("User preferences and expertise updated!")
    
    # Demonstrate temporary data storage
    print("\n--- Temporary Data Storage ---")
    memory_manager.store_temporary_data("draft_contract", {
        "parties": ["Alice Corp", "Bob LLC"],
        "subject": "Software licensing",
        "key_terms": ["exclusive license", "5-year term", "$50,000 annual fee"]
    }, ttl_minutes=60)
    
    draft = memory_manager.get_temporary_data("draft_contract")
    print(f"Stored draft contract: {draft['subject']}")
    
    # Get conversation history
    print("\n--- Conversation History ---")
    history = memory_manager.get_conversation_history(num_turns=2)
    print(f"Recent conversation ({len(history.split('User:')) - 1} turns):")
    print(history[:200] + "..." if len(history) > 200 else history)
    
    print("\n--- Memory System Demo Complete ---")
    print("The memory system successfully:")
    print("✓ Stored conversation turns with metadata")
    print("✓ Performed semantic search across conversations")
    print("✓ Stored and retrieved legal concepts")
    print("✓ Managed user profiles and preferences")
    print("✓ Provided contextual information for queries")
    print("✓ Handled temporary data with expiration")
    

if __name__ == "__main__":
    try:
        example_usage()
    except Exception as e:
        print(f"Error running example: {e}")
        import traceback
        traceback.print_exc()
