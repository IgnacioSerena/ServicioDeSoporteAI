from typing import cast
from fastapi import FastAPI, Request, Response
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.chat import router as chat_router
from app.api.ingest_data import router as ingest_router 
from app.core.rate_limiter import limiter 

app = FastAPI(
    title="API de Soporte AI",
    description="Servicio RAG con LangChain, PGVector y Gemini para soporte técnico inteligente.",
    version="1.0.0"
)

# Wrapper para adaptar la firma de la función y eliminar el error estático de Pylance
def custom_rate_limit_handler(request: Request, exc: Exception) -> Response:
    # Usamos cast para que Pylance entienda que 'exc' es el tipo correcto
    return _rate_limit_exceeded_handler(request, cast(RateLimitExceeded, exc))

# --- CONFIGURACIÓN DEL RATE LIMITER ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

app.include_router(chat_router, prefix="/api/v1")
app.include_router(ingest_router, prefix="/api/v1")

@app.get("/", tags=["Health"])
async def health_check():
    """Endpoint de comprobación de estado."""
    return {"status": "ok", "message": "Servicio de Soporte AI operativo"}