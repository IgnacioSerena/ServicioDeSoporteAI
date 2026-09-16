import os
from dotenv import load_dotenv

load_dotenv()

_supa_raw_url = os.getenv("SUPABASE_DB_URL")

if not _supa_raw_url:
    raise ValueError("Falta la variable de entorno SUPABASE_DB_URL en el archivo .env")

SUPABASE_DB_URL: str = _supa_raw_url

_google_api_key = os.getenv("GOOGLE_API_KEY")

if not _google_api_key:
    raise ValueError("Falta la variable de entorno GOOGLE_API_KEY en el archivo .env")

GOOGLE_API_KEY: str = _google_api_key