from fastapi import FastAPI
from app.api.chat import router as chat_router

app = FastAPI(
    title="API de Soporte AI",
    description="Servicio RAG con LangChain, PGVector, Gemini y Groq",
    version="1.0.0"
)

# Registramos las rutas de nuestro dominio de chat
app.include_router(chat_router, prefix="/api/v1")

@app.get("/")
async def health_check():
    """Endpoint básico para comprobar que el servidor está vivo"""
    return {"status": "ok", "message": "Servicio de Soporte AI operativo"}