print("="*60)
print("UNDERSTANDING HYBRID SEARCH")
print("="*60)

print("""
SCENARIO: You have these documents in your knowledge base:

Doc 1: "Alice Johnson is the lead developer for the RAG project."
Doc 2: "The Retrieval-Augmented Generation system uses vector databases."
Doc 3: "Our main engineer, Alice, works on AI architectures."
Doc 4: "The project lead handles all technical decisions."

USER QUERY: "Who is the RAG project lead?"

─────────────────────────────────────────────────────────────

METHOD 1: SEMANTIC SEARCH ONLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Finds documents with similar MEANING:
  1. Doc 4 (0.85) - "project lead" matches "project lead" ✅
  2. Doc 2 (0.78) - mentions "Retrieval-Augmented Generation" 🤔
  3. Doc 3 (0.72) - mentions "engineer" and "AI" 🤔
  4. Doc 1 (0.68) - has "lead" and "project" separately ⚠️

PROBLEM: Doc 1 has the EXACT answer but scored lowest!
Why? "Alice Johnson" and "RAG" are treated as common words.

─────────────────────────────────────────────────────────────

METHOD 2: KEYWORD SEARCH ONLY (BM25)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Finds documents with exact WORDS:
  1. Doc 1 (12.5) - has "RAG" + "project" + "lead" ✅✅✅
  2. Doc 2 (8.3) - has "RAG" (spelled out) + "system" 🤔
  3. Doc 4 (5.2) - has "project" + "lead" 🤔
  4. Doc 3 (2.1) - only has "project" (mentioned) ⚠️

BETTER! But would miss if they said "project leader" instead of "lead"

─────────────────────────────────────────────────────────────

METHOD 3: HYBRID SEARCH (BEST!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Combines BOTH approaches:
  1. Doc 1 (0.92) - HIGH semantic + HIGH keyword = TOP! ✅✅✅
  2. Doc 4 (0.76) - MEDIUM semantic + MEDIUM keyword 🤔
  3. Doc 2 (0.71) - MEDIUM semantic + LOW keyword 🤔
  4. Doc 3 (0.65) - LOW semantic + LOW keyword ⚠️

PERFECT! Found the exact answer by combining both methods!

─────────────────────────────────────────────────────────────

💡 KEY INSIGHT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hybrid search catches:
  ✅ Exact terms (names, codes, acronyms)
  ✅ Similar meanings (synonyms, paraphrases)
  ✅ Context (both meaning AND terminology)

This is why production RAG systems use HYBRID search!
""")

print("="*60)
print("Let's build it!")
print("="*60 + "\n")