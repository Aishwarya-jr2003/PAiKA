class QueryExpander:
    """
    Expands user queries to improve retrieval
    """
    
    def __init__(self):
        # Common expansions (in production, use LLM or thesaurus)
        self.expansions = {
            'ml': ['machine learning', 'AI', 'artificial intelligence'],
            'ai': ['artificial intelligence', 'machine learning', 'ML'],
            'rag': ['retrieval augmented generation', 'retrieval-augmented generation'],
            'llm': ['large language model', 'language model', 'AI model'],
            'pdf': ['document', 'file'],
            'email': ['message', 'mail', 'correspondence'],
            'db': ['database'],
            'api': ['application programming interface', 'endpoint'],
        }
    
    def expand(self, query):
        """
        Expand query with synonyms and related terms
        
        Args:
            query: Original query string
        
        Returns:
            Expanded query string
        """
        
        words = query.lower().split()
        expanded_terms = set(words)  # Start with original words
        
        for word in words:
            if word in self.expansions:
                expanded_terms.update(self.expansions[word])
        
        expanded_query = ' '.join(expanded_terms)
        
        if len(expanded_terms) > len(words):
            print(f"📝 Query expansion:")
            print(f"   Original: {query}")
            print(f"   Expanded: {expanded_query}\n")
        
        return expanded_query
    
    def add_expansion(self, term, synonyms):
        """Add custom expansion rule"""
        self.expansions[term.lower()] = synonyms

# Test
if __name__ == "__main__":
    print("="*60)
    print("QUERY EXPANSION TEST")
    print("="*60 + "\n")
    
    expander = QueryExpander()
    
    test_queries = [
        "What is ML?",
        "How to use RAG with LLMs?",
        "Send email via API",
        "Store data in DB"
    ]
    
    for query in test_queries:
        expanded = expander.expand(query)
        print()