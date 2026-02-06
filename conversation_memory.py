from datetime import datetime
from collections import deque

class ConversationMemory:
    """
    Manages conversation history for context-aware responses
    """
    
    def __init__(self, max_turns=5):
        """
        Args:
            max_turns: Maximum number of conversation turns to remember
        """
        self.max_turns = max_turns
        self.history = deque(maxlen=max_turns * 2)  # Q&A pairs
        self.session_start = datetime.now()
    
    def add_turn(self, question, answer):
        """Add a Q&A turn to history"""
        self.history.append({
            'role': 'user',
            'content': question,
            'timestamp': datetime.now()
        })
        self.history.append({
            'role': 'assistant',
            'content': answer,
            'timestamp': datetime.now()
        })
    
    def get_context(self):
        """Get conversation history as context string"""
        if not self.history:
            return ""
        
        context = "Previous conversation:\n"
        for turn in self.history:
            role = "User" if turn['role'] == 'user' else "Assistant"
            context += f"{role}: {turn['content']}\n"
        
        return context
    
    def get_last_question(self):
        """Get the last user question"""
        for turn in reversed(self.history):
            if turn['role'] == 'user':
                return turn['content']
        return None
    
    def clear(self):
        """Clear conversation history"""
        self.history.clear()
        self.session_start = datetime.now()
    
    def get_session_info(self):
        """Get session statistics"""
        user_turns = sum(1 for t in self.history if t['role'] == 'user')
        duration = datetime.now() - self.session_start
        
        return {
            'turns': user_turns,
            'duration': str(duration).split('.')[0],
            'messages': len(self.history)
        }

# Test
if __name__ == "__main__":
    print("="*60)
    print("CONVERSATION MEMORY TEST")
    print("="*60 + "\n")
    
    memory = ConversationMemory(max_turns=3)
    
    # Simulate conversation
    conversations = [
        ("What is RAG?", "RAG is Retrieval-Augmented Generation, a technique for improving AI responses."),
        ("How does it work?", "RAG works by retrieving relevant documents and using them as context for generation."),
        ("What are the benefits?", "Benefits include better accuracy, reduced hallucinations, and up-to-date information."),
        ("Can you give an example?", "For example, when you ask about a specific topic, RAG first searches your documents...")
    ]
    
    for i, (q, a) in enumerate(conversations, 1):
        print(f"Turn {i}:")
        print(f"User: {q}")
        print(f"Assistant: {a}\n")
        
        memory.add_turn(q, a)
        
        if i >= 2:
            print("📝 Conversation context:")
            print("-"*60)
            print(memory.get_context())
            print()
    
    # Show session info
    info = memory.get_session_info()
    print("="*60)
    print("📊 SESSION INFO:")
    print("="*60)
    print(f"Total turns: {info['turns']}")
    print(f"Total messages: {info['messages']}")
    print(f"Session duration: {info['duration']}")
    print()
    
    # Test context window
    print("="*60)
    print("🔄 TESTING CONTEXT WINDOW:")
    print("="*60)
    print(f"Max turns: {memory.max_turns}")
    print(f"Current turns: {info['turns']}")
    print("\nAdding one more turn (should drop oldest)...\n")
    
    memory.add_turn("What about disadvantages?", "Main disadvantages include complexity and computational cost.")
    
    print(memory.get_context())