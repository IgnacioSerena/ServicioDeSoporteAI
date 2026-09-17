import logging
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import ConfigurableField
from langchain_postgres import PGVector

from app.core.config import SUPABASE_DB_URL

logger = logging.getLogger(__name__)

# Configuración del modelo de embeddings ligero para ejecución eficiente en CPU
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'} 
)

COLLECTION_NAME = "vector_store"

# Instancia global de PGVector.
# Al mantenerla a nivel de módulo, se reutilizan las conexiones a la base 
# de datos (connection pooling implícito), mejorando el rendimiento general.
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
    Construye un recuperador (retriever) basado en Maximum Marginal Relevance (MMR)
    para asegurar diversidad en los fragmentos de contexto recuperados.
    
    Permite la inyección dinámica de filtros de metadatos en tiempo de ejecución.
    """
    base_retriever = get_vector_store().as_retriever(
        search_type="mmr",
        search_kwargs={"k": k, "fetch_k": fetch_k}
    )
    
    configurable_retriever = base_retriever.configurable_fields(
        search_kwargs=ConfigurableField(
            id="search_filters",
            name="Filtros de Búsqueda",
            description="Permite inyectar filtros de metadatos como la categoría al vuelo"
        )
    )
    
    return configurable_retriever