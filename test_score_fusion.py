import numpy as np

print("="*60)
print("UNDERSTANDING SCORE FUSION")
print("="*60 + "\n")

# Example scores from two search methods
semantic_scores = np.array([0.85, 0.78, 0.72, 0.65, 0.58])  # 0-1 range
keyword_scores = np.array([12.5, 9.3, 7.1, 3.2, 1.5])       # 0-15 range

print("PROBLEM: Different score ranges!")
print("-"*60)
print(f"Semantic scores: {semantic_scores}")
print(f"Keyword scores:  {keyword_scores}")
print("\nCan't combine directly - different scales!\n")

# Method 1: Min-Max Normalization
print("="*60)
print("METHOD 1: Min-Max Normalization")
print("="*60)
print("Formula: (score - min) / (max - min)\n")

def normalize_minmax(scores):
    min_score = np.min(scores)
    max_score = np.max(scores)
    if max_score - min_score == 0:
        return scores
    return (scores - min_score) / (max_score - min_score)

keyword_normalized = normalize_minmax(keyword_scores)

print(f"Before: {keyword_scores}")
print(f"After:  {keyword_normalized}")
print(f"Range:  0 to 1 ✅\n")

# Method 2: Reciprocal Rank Fusion (RRF)
print("="*60)
print("METHOD 2: Reciprocal Rank Fusion")
print("="*60)
print("Formula: 1 / (rank + k), where k=60 typically\n")

def reciprocal_rank_fusion(scores, k=60):
    # Get ranks (0 = best)
    ranks = np.argsort(scores)[::-1]
    rrf_scores = np.zeros(len(scores))
    
    for rank, idx in enumerate(ranks):
        rrf_scores[idx] = 1 / (rank + k)
    
    return rrf_scores

keyword_rrf = reciprocal_rank_fusion(keyword_scores)

print(f"Original scores: {keyword_scores}")
print(f"RRF scores:      {keyword_rrf}")
print(f"Focus on RANK not absolute score ✅\n")

# Combine scores
print("="*60)
print("COMBINING SCORES")
print("="*60 + "\n")

# Method 1: Simple average
combined_avg = (semantic_scores + keyword_normalized) / 2

print("METHOD 1: Simple Average (50/50 weight)")
print("-"*60)
print(f"Semantic (norm):  {semantic_scores}")
print(f"Keyword (norm):   {keyword_normalized}")
print(f"Combined:         {combined_avg}")
print()

# Method 2: Weighted average
weight_semantic = 0.6
weight_keyword = 0.4
combined_weighted = (semantic_scores * weight_semantic + 
                     keyword_normalized * weight_keyword)

print("METHOD 2: Weighted Average (60% semantic, 40% keyword)")
print("-"*60)
print(f"Combined: {combined_weighted}")
print()

# Show final ranking
final_ranks = np.argsort(combined_weighted)[::-1]

print("="*60)
print("🎯 FINAL RANKING:")
print("="*60)
for i, idx in enumerate(final_ranks, 1):
    print(f"{i}. Document {idx+1}")
    print(f"   Semantic: {semantic_scores[idx]:.3f}")
    print(f"   Keyword:  {keyword_normalized[idx]:.3f}")
    print(f"   Combined: {combined_weighted[idx]:.3f}")
    print()

print("="*60)
print("💡 KEY INSIGHT:")
print("="*60)
print("""
Hybrid search combines TWO rankings:
  1. Normalize scores to same range (0-1)
  2. Combine with weights (e.g., 50/50 or 60/40)
  3. Use combined score for final ranking

This captures BOTH meaning and exact terms!
""")