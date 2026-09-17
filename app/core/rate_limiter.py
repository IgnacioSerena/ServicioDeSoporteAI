from slowapi import Limiter
from slowapi.util import get_remote_address

# Instancia global del limitador de peticiones (rate limiter) para la API.
# Utiliza la IP del cliente (get_remote_address) como identificador único para llevar 
# la cuenta del tráfico, protegiendo los endpoints contra abusos o ataques automatizados.
limiter = Limiter(key_func=get_remote_address)