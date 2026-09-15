from pydantic import SecretStr
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from app.core.config import GOOGLE_API_KEY, GROQ_API_KEY
from app.services.vector_store import get_retriever

# 1. Configurar el LLM Principal (Google Gemini)
# Usamos gemini-1.5-flash por su excelente balance entre velocidad y ventana de contexto
primary_llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest",
    temperature=0.2, # Temperatura baja para respuestas de soporte precisas y no creativas
    google_api_key=GOOGLE_API_KEY,
    max_retries=2
)

# 2. Configurar el LLM de Respaldo (Groq con Llama 3)
# Entrará en acción automáticamente si Gemini da un error 500, timeout, o rate limit
backup_llm = ChatGroq(
    model="llama3-8b-8192", 
    temperature=0.2,
    api_key=SecretStr(GROQ_API_KEY),
    max_retries=2
)

# 3. Unir ambos modelos con la lógica de fallback
robust_llm = primary_llm.with_fallbacks([backup_llm])

# 4. Diseñar el Prompt del Sistema
system_prompt = """Eres un asistente de soporte técnico experto y amable. 
Utiliza únicamente los siguientes fragmentos de contexto recuperado para responder a la pregunta del usuario. 
Si no sabes la respuesta o el contexto no contiene la información, di simplemente que no tienes esa información 
y sugiere contactar a un humano. No inventes respuestas.

Contexto:
{context}

Pregunta: {query}
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{query}")
])

# 5. Función auxiliar para formatear los documentos de PGVector a texto plano
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def get_rag_chain():
    """
    Construye y retorna la cadena RAG completa usando LCEL.
    """
    retriever = get_retriever(k=4, fetch_k=20) # Usamos el retriever con MMR
    
    # Ensamblaje de la cadena LCEL
    rag_chain = (
        # El diccionario inicial mapea las variables requeridas por el prompt
        {"context": retriever | format_docs, "query": RunnablePassthrough()}
        | prompt_template
        | robust_llm
        | StrOutputParser() # Transforma el objeto AIMessage en un string limpio
    )
    
    return rag_chain

# Instancia global para importar desde otros módulos
rag_chain = get_rag_chain()