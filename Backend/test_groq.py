import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

print("API Key found:", bool(api_key))

client = Groq(api_key=api_key)

try:
    models = client.models.list()

    print("\nAVAILABLE MODELS:\n")

    for model in models.data:
        print(model.id)

except Exception as e:
    print("ERROR:", e)