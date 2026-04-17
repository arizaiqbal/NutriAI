import os
from dotenv import load_dotenv

load_dotenv()  # reads the .env file and loads variables into environment

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Groq LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# External APIs
SPOONACULAR_KEY = os.getenv("SPOONACULAR_KEY")
USDA_KEY        = os.getenv("USDA_KEY")

# Gmail
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
