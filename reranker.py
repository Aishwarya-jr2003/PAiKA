from sentence_transformers import CrossEncoder
import numpy as np

class Reranker:
    """
    Re-ranks search results using a cross-encoder model
    """
    
    def __init__(self, model_name='cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """
        Initialize with a cross-encoder model
        
        Popular models:
        - cross-encoder/ms-marco-MiniLM-L-6-v2 (fast, good)
        - cross-encoder/ms-marco-MiniLM-L-12-v2 (slower, better)
        """
        print(f"🔄 Loading re-ranker model: {model_name}...")
        self.model = CrossEncoder(model_name)
        print("✅ Re-ranker ready!\n")
    
    def rerank(self, query, documents, top_k=5):
        """
        Re-rank documents based on relevance to query
        
        Args:
            query: User query string
            documents: List of dicts with 'content' and other metadata
            top_k: Number of top results to return
        
        Returns:
            List of re-ranked documents with scores
        """
        
        if not documents:
            return []
        
        print(f"🔄 Re-ranking {len(documents)} candidates with cross-encoder...")
        
        # Prepare query-document pairs
        pairs = [(query, doc['content']) for doc in documents]
        
        # Score with cross-encoder
        scores = self.model.predict(pairs)
        
        # Add scores to documents
        for doc, score in zip(documents, scores):
            doc['rerank_score'] = float(score)
        
        # Sort by rerank score
        reranked = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)
        
        # Return top k
        top_results = reranked[:top_k]
        
        print(f"✅ Re-ranked! Top score: {top_results[0]['rerank_score']:.4f}\n")
        
        return top_results
    
    def filter_by_threshold(self, documents, threshold=0.5):
        """
        Filter out documents below relevance threshold
        
        Args:
            documents: List of documents with rerank_score
            threshold: Minimum score to keep (0-1)
        
        Returns:
            Filtered list
        """
        filtered = [doc for doc in documents if doc.get('rerank_score', 0) >= threshold]
        
        removed = len(documents) - len(filtered)
        if removed > 0:
            print(f"🔍 Filtered out {removed} low-relevance results (< {threshold})\n")
        
        return filtered

# Test the reranker
if __name__ == "__main__":
    print("="*60)
    print("RE-RANKER TEST")
    print("="*60 + "\n")
    
    # Initialize
    reranker = Reranker()
    
    # Sample data
    query = "What are the benefits of using ChromaDB?"
    
    documents = [
        {
            'content': "ChromaDB is an open-source vector database designed for AI applications.",
            'source': 'doc1.txt',
            'initial_score': 0.85
        },
        {
            'content': "Vector databases store embeddings efficiently for fast similarity search.",
            'source': 'doc2.txt',
            'initial_score': 0.82
        },
        {
            'content': "ChromaDB benefits include: easy setup, fast queries, automatic indexing, and Python integration.",
            'source': 'doc3.txt',
            'initial_score': 0.79
        },
        {
            'content': "Database systems are essential for modern applications and data management.",
            'source': 'doc4.txt',
            'initial_score': 0.76
        }
    ]
    
    print(f"Query: {query}\n")
    print(f"Initial ranking (by hybrid search):")
    for i, doc in enumerate(documents, 1):
        print(f"  {i}. {doc['content'][:60]}... (score: {doc['initial_score']})")
    print()
    
    # Re-rank
    reranked = reranker.rerank(query, documents, top_k=3)
    
    print("="*60)
    print("🎯 AFTER RE-RANKING:")
    print("="*60 + "\n")
    
    for i, doc in enumerate(reranked, 1):
        print(f"{i}. {doc['content'][:60]}...")
        print(f"   Initial score: {doc['initial_score']:.3f}")
        print(f"   Rerank score:  {doc['rerank_score']:.3f}")
        
        # Show improvement
        if i == 1 and doc['initial_score'] < documents[0]['initial_score']:
            print(f"   ✅ PROMOTED from position {documents.index(doc) + 1}!")
        
        print()
    
    # Test filtering
    print("="*60)
    print("🔍 TESTING RELEVANCE FILTERING")
    print("="*60 + "\n")
    
    filtered = reranker.filter_by_threshold(reranked, threshold=0.7)
    
    print(f"Kept {len(filtered)} high-relevance results\n")