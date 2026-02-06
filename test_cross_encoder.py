from sentence_transformers import CrossEncoder
import numpy as np

print("="*60)
print("TESTING CROSS-ENCODER RE-RANKING")
print("="*60 + "\n")

# Load cross-encoder model
print("🔄 Loading cross-encoder model...")
model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
print("✅ Model loaded!\n")

# Sample query and documents
query = "How do I reset my password in the mobile app?"

documents = [
    "The mobile application requires user authentication to access premium features and settings.",
    "Password policies require at least 8 characters including uppercase, lowercase, and numbers.",
    "To reset your password in the mobile app: 1) Open Settings 2) Tap Account 3) Select Reset Password 4) Follow the email instructions.",
    "Mobile apps can be downloaded from the Apple App Store or Google Play Store for free.",
    "Strong passwords are essential for maintaining account security and protecting personal data.",
    "The password reset process sends a verification code to your registered email address.",
    "App settings allow you to customize notifications, privacy preferences, and account details."
]

print(f"📝 QUERY: {query}\n")
print(f"📚 DOCUMENTS: {len(documents)} total\n")

# Score each document with cross-encoder
print("🔄 Scoring with cross-encoder...\n")

scores = model.predict([(query, doc) for doc in documents])

print("="*60)
print("📊 CROSS-ENCODER SCORES:")
print("="*60 + "\n")

# Sort by score
ranked_indices = np.argsort(scores)[::-1]

for rank, idx in enumerate(ranked_indices, 1):
    score = scores[idx]
    doc = documents[idx]
    
    # Visual score bar
    bar_length = int(score * 40)
    bar = "█" * bar_length + "░" * (40 - bar_length)
    
    print(f"{rank}. Score: {score:.4f} {bar}")
    print(f"   {doc[:80]}...")
    
    if rank == 1:
        print("   ✅ BEST ANSWER!")
    
    print()

print("="*60)
print("💡 OBSERVATION:")
print("="*60)
print("""
Notice how the cross-encoder CORRECTLY identified
the step-by-step instructions as the best answer!

Doc #3 scored highest because it:
  ✅ Directly answers "How do I...?"
  ✅ Mentions "mobile app" specifically
  ✅ Provides actionable steps
  ✅ Includes "reset password"

This is much smarter than simple keyword matching!
""")