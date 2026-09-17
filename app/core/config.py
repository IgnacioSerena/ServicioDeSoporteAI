import os
import logging
from dotenv import load_dotenv

# Configurar un logger para registrar problemas críticos de inicialización
logger = logging.getLogger(__name__)

# Cargar las variables definidas en el archivo .env al entorno de ejecución
load_dotenv()

def _get_required_env(var_name: str) -> str:
    """
    Extrae una variable de entorno y asegura su existencia.
    
    Sigue el principio 'Fail-Fast' (fallar rápido): si falta una credencial 
    crítica, es mejor detener el arranque de la aplicación de inmediato 
    en lugar de provocar fallos impredecibles en tiempo de ejecución más adelante.
    """
    value = os.getenv(var_name)
    if not value:
        logger.critical(f"Falta la configuración crítica: {var_name}")
        raise ValueError(f"Falta la variable de entorno {var_name} en el archivo .env")
    return value

SUPABASE_DB_URL: str = _get_required_env("SUPABASE_DB_URL")
GOOGLE_API_KEY: str = _get_required_env("GOOGLE_API_KEY")