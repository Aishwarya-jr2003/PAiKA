import chromadb
from rank_bm25 import BM25Okapi
import numpy as np
from pathlib import Path

class HybridSearchEngine:
    """
    Combines semantic search (ChromaDB) with keyword search (BM25)
    """
    
    def __init__(self, chroma_collection):
        self.collection = chroma_collection
        self.bm25 = None
        self.doc_ids = []
        self.tokenized_docs = []
        
    def index_documents(self):
        """Build BM25 index from ChromaDB collection"""
        
        if self.collection.count() == 0:
            print("⚠️  No documents to index!")
            return
        
        print(f"🔄 Building BM25 index for {self.collection.count()} chunks...")
        
        # Get all documents from ChromaDB
        all_data = self.collection.get()
        
        documents = all_data['documents']
        self.doc_ids = all_data['ids']
        
        # Tokenize documents for BM25
        self.tokenized_docs = [doc.lower().split() for doc in documents]
        
        # Create BM25 index
        self.bm25 = BM25Okapi(self.tokenized_docs)
        
        print(f"✅ BM25 index built with {len(documents)} documents\n")
    
    def semantic_search(self, query, n_results=10):
        """Semantic search using ChromaDB"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Extract scores and IDs
        scores = {}
        for doc_id, distance in zip(results['ids'][0], results['distances'][0]):
            # Convert distance to similarity (0-1)
            similarity = 1 - distance
            scores[doc_id] = similarity
        
        return scores
    
    def keyword_search(self, query, n_results=10):
        """Keyword search using BM25"""
        if self.bm25 is None:
            return {}
        
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get BM25 scores
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # Normalize scores to 0-1
        if np.max(bm25_scores) > 0:
            normalized_scores = bm25_scores / np.max(bm25_scores)
        else:
            normalized_scores = bm25_scores
        
        # Create dict of scores by doc ID
        scores = {}
        for doc_id, score in zip(self.doc_ids, normalized_scores):
            scores[doc_id] = score
        
        # Get top N
        top_indices = np.argsort(bm25_scores)[::-1][:n_results]
        top_scores = {self.doc_ids[i]: normalized_scores[i] for i in top_indices}
        
        return top_scores
    
    def hybrid_search(self, query, n_results=5, semantic_weight=0.5):
        """
        Hybrid search combining semantic and keyword
        
        Args:
            query: Search query
            n_results: Number of results to return
            semantic_weight: Weight for semantic search (0-1)
                           keyword_weight = 1 - semantic_weight
        """
        
        keyword_weight = 1 - semantic_weight
        
        print(f"🔍 HYBRID SEARCH")
        print(f"   Semantic weight: {semantic_weight:.1f}")
        print(f"   Keyword weight: {keyword_weight:.1f}\n")
        
        # Get results from both methods
        semantic_scores = self.semantic_search(query, n_results=n_results*2)
        keyword_scores = self.keyword_search(query, n_results=n_results*2)
        
        print(f"📊 Semantic search found: {len(semantic_scores)} results")
        print(f"📊 Keyword search found: {len(keyword_scores)} results\n")
        
        # Combine scores
        combined_scores = {}
        
        # Get all unique doc IDs
        all_doc_ids = set(semantic_scores.keys()) | set(keyword_scores.keys())
        
        for doc_id in all_doc_ids:
            sem_score = semantic_scores.get(doc_id, 0.0)
            key_score = keyword_scores.get(doc_id, 0.0)
            
            # Weighted combination
            combined_scores[doc_id] = (
                semantic_weight * sem_score + 
                keyword_weight * key_score
            )
        
        # Sort by combined score
        sorted_ids = sorted(
            combined_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:n_results]
        
        # Get full documents
        results = []
        for doc_id, combined_score in sorted_ids:
            # Get document from ChromaDB
            doc_data = self.collection.get(ids=[doc_id])
            
            if doc_data['documents']:
                results.append({
                    'id': doc_id,
                    'content': doc_data['documents'][0],
                    'metadata': doc_data['metadatas'][0],
                    'semantic_score': semantic_scores.get(doc_id, 0.0),
                    'keyword_score': keyword_scores.get(doc_id, 0.0),
                    'combined_score': combined_score
                })
        
        return results

# Test the hybrid search
if __name__ == "__main__":
    print("="*60)
    print("HYBRID SEARCH ENGINE TEST")
    print("="*60 + "\n")
    
    # Create test ChromaDB collection
    client = chromadb.Client()
    collection = client.create_collection("test_hybrid")
    
    # Add test documents
    documents = [
        "Alice Johnson is the lead developer for the RAG project using ChromaDB",
        "The Retrieval-Augmented Generation system uses vector databases for semantic search",
        "Our main engineer, Alice, works on AI architectures and machine learning",
        "The project lead handles all technical decisions about the system",
        "Machine learning and RAG are important technologies for modern AI applications"
    ]
    
    collection.add(
        documents=documents,
        ids=[f"doc_{i}" for i in range(len(documents))],
        metadatas=[{"source": f"test_{i}"} for i in range(len(documents))]
    )
    
    print(f"✅ Created test collection with {len(documents)} documents\n")
    
    # Create hybrid search engine
    hybrid_engine = HybridSearchEngine(collection)
    hybrid_engine.index_documents()
    
    # Test query
    query = "Who is the RAG project lead?"
    
    print("="*60)
    print(f"QUERY: {query}")
    print("="*60 + "\n")
    
    # Compare different search methods
    print("METHOD 1: Semantic Only (100% semantic)")
    print("-"*60)
    results_semantic = hybrid_engine.hybrid_search(query, n_results=3, semantic_weight=1.0)
    for i, result in enumerate(results_semantic, 1):
        print(f"{i}. {result['content'][:60]}...")
        print(f"   Score: {result['combined_score']:.4f}\n")
    
    print("METHOD 2: Keyword Only (100% keyword)")
    print("-"*60)
    results_keyword = hybrid_engine.hybrid_search(query, n_results=3, semantic_weight=0.0)
    for i, result in enumerate(results_keyword, 1):
        print(f"{i}. {result['content'][:60]}...")
        print(f"   Score: {result['combined_score']:.4f}\n")
    
    print("METHOD 3: Hybrid (50/50)")
    print("-"*60)
    results_hybrid = hybrid_engine.hybrid_search(query, n_results=3, semantic_weight=0.5)
    for i, result in enumerate(results_hybrid, 1):
        print(f"{i}. {result['content'][:60]}...")
        print(f"   Semantic: {result['semantic_score']:.3f} | Keyword: {result['keyword_score']:.3f} | Combined: {result['combined_score']:.3f}")
        print()
    
    print("="*60)
    print("✅ HYBRID SEARCH WORKING!")
    print("="*60)
    
    # Cleanup
    client.delete_collection("test_hybrid")