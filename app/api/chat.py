from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
from app.services.llm_chain import rag_chain_with_history

router = APIRouter(tags=["Chat Soporte"])

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

@router.post("/ask")
async def ask_question(request: ChatRequest):
    try:
        # CASO 1: Si el cliente no manda ID (es una nueva pestaña o chat anónimo), 
        # generamos un identificador único automáticamente para esta sesión.
        # CASO 2: Si el cliente ya mandó un ID, lo respetamos para mantener la memoria.
        current_session_id = request.session_id or str(uuid.uuid4())
        
        ai_response = rag_chain_with_history.invoke(
            {
                "query": request.query
            },
            config={
                "configurable": {
                    "session_id": current_session_id
                }
            }
        )
        
        return {
            "session_id": current_session_id,  
            "query": request.query,
            "answer": ai_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando la solicitud: {str(e)}")