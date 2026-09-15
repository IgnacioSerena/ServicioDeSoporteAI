from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from app.core.config import SUPABASE_DB_URL

# 1. Inicializamos el modelo de embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'} 
)

COLLECTION_NAME = "vector_store"

# 2. Instanciamos PGVector UNA SOLA VEZ a nivel de módulo.
# Esto mantiene el engine de base de datos vivo y reutiliza las conexiones.
_vector_store_instance = PGVector(
    embeddings=embeddings,
    collection_name=COLLECTION_NAME,
    connection=SUPABASE_DB_URL,
    use_jsonb=True, 
)

def get_vector_store() -> PGVector:
    """
    Retorna la instancia global de PGVector conectada a Supabase.
    """
    return _vector_store_instance

def get_retriever(k: int = 4, fetch_k: int = 20):
    """
    Retorna un retriever configurado con Maximal Marginal Relevance (MMR).
    Extrae 'fetch_k' documentos de la BD y luego selecciona los 'k' más 
    relevantes y diversos para evitar pasarle contexto redundante al LLM.
    """
    return _vector_store_instance.as_retriever(
        search_type="mmr",
        search_kwargs={"k": k, "fetch_k": fetch_k}
    )