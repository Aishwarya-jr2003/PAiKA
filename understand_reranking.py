print("="*60)
print("UNDERSTANDING RE-RANKING")
print("="*60)

print("""
SCENARIO: Customer support knowledge base search

Query: "How do I return a defective product?"

Documents in knowledge base:
1. "Our return policy allows returns within 30 days of purchase."
2. "Defective products can be returned for a full refund or exchange."
3. "To return a defective product: 1) Contact support 2) Get RMA number 3) Ship item"
4. "Product defects are covered under our warranty program."
5. "Returns must include original packaging and receipt."

─────────────────────────────────────────────────────────────

INITIAL RETRIEVAL (Hybrid Search):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ranking by hybrid scores:
1. Doc 1 (0.85) - "return policy allows returns within 30 days"
2. Doc 2 (0.83) - "Defective products can be returned"
3. Doc 4 (0.81) - "Product defects covered under warranty"
4. Doc 3 (0.79) - "To return defective product: steps..."  ← BEST ANSWER!
5. Doc 5 (0.77) - "Returns must include packaging"

Problem: Best answer is #4, not #1!
Why? "return policy" matches keywords strongly, but isn't the ANSWER.

─────────────────────────────────────────────────────────────

AFTER RE-RANKING (Cross-Encoder):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Deep analysis of query + document relationship:
1. Doc 3 (0.96) - "To return defective product: steps..." ✅ PERFECT!
2. Doc 2 (0.89) - "Defective products can be returned"
3. Doc 4 (0.78) - "Product defects covered under warranty"
4. Doc 1 (0.71) - "return policy allows returns"
5. Doc 5 (0.65) - "Returns must include packaging"

Success! Best answer is now #1!
Cross-encoder understood that step-by-step instructions ANSWER the "how" question.

─────────────────────────────────────────────────────────────

KEY INSIGHT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Initial retrieval: BROAD NET (find candidates)
  - Fast: search millions of docs
  - Good: finds relevant topics
  - Limitation: shallow understanding

Re-ranking: DEEP ANALYSIS (find best answer)
  - Slow: can only process dozens
  - Excellent: understands query intent
  - Result: perfect answer at the top

Together: Fast + Accurate! 🚀
""")

print("="*60)
print("Let's implement this!")
print("="*60 + "\n")