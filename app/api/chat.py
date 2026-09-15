from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.llm_chain import rag_chain

router = APIRouter(tags=["Chat Soporte"])

# Modelo de validación de entrada
class ChatRequest(BaseModel):
    query: str

@router.post("/ask")
async def ask_question(request: ChatRequest):
    try:
        # Al usar RunnablePassthrough en tu cadena, solo necesitas pasarle el string directamente
        ai_response = rag_chain.invoke(request.query)
        
        return {
            "query": request.query,
            "answer": ai_response
        }
    except Exception as e:
        # Capturamos cualquier error no previsto (ej. si tanto Gemini como Groq fallan)
        raise HTTPException(status_code=500, detail=f"Error procesando la solicitud: {str(e)}")