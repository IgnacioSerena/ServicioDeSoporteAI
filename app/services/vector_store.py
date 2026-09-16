from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import ConfigurableField
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

def get_retriever(k=4, fetch_k=20):
    base_retriever = get_vector_store().as_retriever(
        search_type="mmr",
        search_kwargs={"k": k, "fetch_k": fetch_k}
    )
    
    # Hacemos que los parámetros de búsqueda sean configurables dinámicamente
    configurable_retriever = base_retriever.configurable_fields(
        search_kwargs=ConfigurableField(
            id="search_filters",
            name="Filtros de Búsqueda",
            description="Permite inyectar filtros de metadatos como la categoría al vuelo"
        )
    )
    
    return configurable_retriever