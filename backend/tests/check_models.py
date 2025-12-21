import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Ensure your key is set
genai.configure(api_key=os.getenv("API_KEY"))

print(f"{'Model Name':<30} | {'Methods'}")
print("-" * 50)

for m in genai.list_models():
    # We only care about models that can generate content
    if 'generateContent' in m.supported_generation_methods:
        print(f"{m.name.replace('models/', ''):<30} | {m.supported_generation_methods}")