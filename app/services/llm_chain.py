import logging
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

logger = logging.getLogger(__name__)

# Configuración del LLM principal y de respaldo con lógica de fallback
# para asegurar la disponibilidad del servicio si el modelo falla.
primary_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0.2,
    api_key=SecretStr(GOOGLE_API_KEY),
    max_retries=2
)

backup_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0.2,
    api_key=SecretStr(GOOGLE_API_KEY),
    max_retries=2
)

robust_llm = primary_llm.with_fallbacks([backup_llm])

# Definición del comportamiento del asistente
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

# Recortador de historial para evitar exceder la ventana de contexto del LLM
trimmer = trim_messages(
    max_tokens=4000,
    strategy="last",
    include_system=True,
    allow_partial=False,
    token_counter=robust_llm
)

def format_docs(docs: List[Any]) -> str:
    """Formatea los documentos recuperados en un único string de texto."""
    return "\n\n".join(doc.page_content for doc in docs)

def get_rag_chain():
    """
    Construye y retorna la cadena RAG completa usando LCEL con tipado nativo.
    """
    retriever = get_retriever(k=4, fetch_k=20)
    
    def get_trimmed_history(data: Dict[str, Any]) -> List[BaseMessage]:
        """Recorta el historial dinámicamente de forma segura para el tipado estático."""
        return trimmer.invoke(data["chat_history"])

    # LCEL: Mapea los tipos de entrada/salida para RunnableWithMessageHistory
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

# Almacenamiento en memoria para el historial de sesiones
store: Dict[str, ChatMessageHistory] = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    """Recupera o inicializa el historial de chat para una sesión específica."""
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Instancias globales exportadas para el uso en la API
base_rag_chain = get_rag_chain()

rag_chain_with_history = RunnableWithMessageHistory(
    base_rag_chain,
    get_session_history,
    input_messages_key="query",
    history_messages_key="chat_history",
)