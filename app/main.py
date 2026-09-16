from fastapi import FastAPI
from app.api.chat import router as chat_router
# 1. IMPORTAR el router de ingestión (ajusta la ruta según dónde esté tu archivo)
from app.api.ingest_data import router as ingest_router 

app = FastAPI(
    title="API de Soporte AI",
    description="Servicio RAG con LangChain, PGVector y Gemini",
    version="1.0.0"
)

# Registramos las rutas de nuestro dominio de chat
app.include_router(chat_router, prefix="/api/v1")
# 2. REGISTRAR las rutas de ingestión
app.include_router(ingest_router, prefix="/api/v1")

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Servicio de Soporte AI operativo"}