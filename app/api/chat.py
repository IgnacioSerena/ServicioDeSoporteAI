import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.services.llm_chain import rag_chain_with_history
from app.core.rate_limiter import limiter

# Configurar un logger para trazar errores sin exponerlos al cliente
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat Soporte"])

class ChatRequest(BaseModel):
    """Modelo de entrada para las consultas del usuario."""
    query: str = Field(..., description="Pregunta o mensaje del usuario.")
    session_id: Optional[str] = Field(default=None, description="ID de sesión para mantener el contexto de la memoria.")

class ChatResponse(BaseModel):
    """Modelo de salida con la respuesta de la IA."""
    session_id: str
    query: str
    answer: str

@router.post("/ask", response_model=ChatResponse)
@limiter.limit("5/minute; 20/day") # 5 peticiones por minuto y 20 por día para proteger el endpoint de abusos
async def ask_question(request: Request, payload: ChatRequest): # Renombramos el body a 'payload'
    """
    Procesa una consulta del usuario y devuelve una respuesta generada mediante RAG.
    """
    try:
        # Ahora usamos payload.session_id y payload.query
        current_session_id = payload.session_id or str(uuid.uuid4())
        
        ai_response = rag_chain_with_history.invoke(
            {"query": payload.query},
            config={"configurable": {"session_id": current_session_id}}
        )
        
        return ChatResponse(
            session_id=current_session_id,
            query=payload.query,
            answer=ai_response
        )
        
    except Exception as e:
        logger.error(f"Error procesando la solicitud de chat en sesión {payload.session_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Se ha producido un error interno procesando la solicitud.")