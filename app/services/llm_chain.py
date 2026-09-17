from operator import itemgetter
from typing import Dict, Any, List
from pydantic import SecretStr
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import trim_messages, BaseMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from app.core.config import GOOGLE_API_KEY
from app.services.vector_store import get_retriever

# 1. Configurar el LLM Principal 
primary_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0.2,
    api_key=SecretStr(GOOGLE_API_KEY),
    max_retries=0
)

# 2. Configurar el LLM de Respaldo
backup_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0.2,
    api_key=SecretStr(GOOGLE_API_KEY),
    max_retries=0
)

# 3. Unir ambos modelos con la lógica de fallback
robust_llm = primary_llm.with_fallbacks([backup_llm])

# 4. Diseñar el Prompt del Sistema
system_prompt = """Eres un asistente de soporte técnico experto y amable. 
Utiliza únicamente los siguientes fragmentos de contexto recuperado y el historial de la conversación para responder a la pregunta del usuario. 
Si no sabes la respuesta o el contexto no contiene la información, di simplemente que no tienes esa información 
y sugiere contactar a un humano. No inventes respuestas.

Contexto:
{context}

Pregunta: {query}
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{query}")
])

# 5. Configurar el recortador de historial
trimmer = trim_messages(
    max_tokens=4000,
    strategy="last",
    include_system=True,
    allow_partial=False,
    token_counter=robust_llm
)

# 6. Funciones auxiliares tipadas para evitar advertencias de Pylance
def format_docs(docs: List[Any]) -> str:
    return "\n\n".join(doc.page_content for doc in docs)

def get_rag_chain():
    """
    Construye y retorna la cadena RAG completa usando LCEL con tipado nativo.
    """
    retriever = get_retriever(k=4, fetch_k=20)
    
    # Función auxiliar tipada para recortar el historial de forma segura para Pylance
    def get_trimmed_history(data: Dict[str, Any]) -> List[BaseMessage]:
        return trimmer.invoke(data["chat_history"])

    # Un diccionario en LCEL mapea perfectamente los tipos de entrada/salida 
    # que espera RunnableWithMessageHistory sin romper la inferencia estática.
    chain = (
        {
            "context": itemgetter("query") | retriever | format_docs,
            "query": itemgetter("query"),
            "chat_history": get_trimmed_history
        }
        | prompt_template
        | robust_llm
        | StrOutputParser()
    )
    
    return chain

store: Dict[str, ChatMessageHistory] = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Instancias globales tipadas correctamente
base_rag_chain = get_rag_chain()

rag_chain_with_history = RunnableWithMessageHistory(
    base_rag_chain,
    get_session_history,
    input_messages_key="query",
    history_messages_key="chat_history",
)