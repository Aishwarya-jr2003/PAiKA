import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("Checking available Gemini models...\n")
print("=" * 60)

try:
    models = genai.list_models()
    
    print("\n✅ Models that support generateContent:\n")
    
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f"Model Name: {model.name}")
            print(f"Display Name: {model.display_name}")
            print(f"Description: {model.description}")
            print("-" * 60)
    
except Exception as e:
    print(f"Error: {e}")