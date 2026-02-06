class SourceAttribution:
    """
    Tracks and formats source citations
    """
    
    def __init__(self):
        self.sources = []
    
    def add_source(self, filename, chunk_index, score, snippet):
        """Add a source citation"""
        self.sources.append({
            'filename': filename,
            'chunk': chunk_index,
            'relevance': score,
            'snippet': snippet[:100]
        })
    
    def format_citations(self):
        """Format sources as citations"""
        if not self.sources:
            return ""
        
        citations = "\n\n📚 **Sources:**\n"
        
        for i, source in enumerate(self.sources, 1):
            citations += f"\n[{i}] {source['filename']} (chunk {source['chunk']})"
            citations += f"\n    Relevance: {source['relevance']:.2%}"
            citations += f"\n    \"{source['snippet']}...\"\n"
        
        return citations
    
    def get_source_files(self):
        """Get unique list of source files"""
        return list(set(s['filename'] for s in self.sources))

# Test
if __name__ == "__main__":
    print("="*60)
    print("SOURCE ATTRIBUTION TEST")
    print("="*60 + "\n")
    
    attribution = SourceAttribution()
    
    # Add sources
    attribution.add_source(
        "python_guide.pdf",
        chunk_index=5,
        score=0.95,
        snippet="List comprehensions provide a concise way to create lists in Python"
    )
    
    attribution.add_source(
        "coding_tips.txt",
        chunk_index=12,
        score=0.87,
        snippet="Using list comprehensions can make your code more readable and Pythonic"
    )
    
    # Format
    print("Answer: List comprehensions are a Pythonic way to create lists...")
    print(attribution.format_citations())
    
    print("="*60)
    print("📄 Unique source files:")
    for file in attribution.get_source_files():
        print(f"  - {file}")