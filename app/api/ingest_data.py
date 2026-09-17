import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_postgres import PGVector

from app.services.vector_store import get_vector_store, COLLECTION_NAME, embeddings
from app.core.config import SUPABASE_DB_URL

# Configurar un logger para trazar errores en las operaciones de ingesta
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Ingestión de Conocimiento"])

# Centralizar el text splitter para aplicar el principio DRY en ambos endpoints
TEXT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=500, 
    chunk_overlap=50, 
    separators=["\n\n", "\n", ".", " ", ""]
)

class DocumentMetadata(BaseModel):
    """Modelo de metadatos asociados a cada fragmento de documento."""
    category: str = Field(..., description="Categoría principal del documento (ej. 'Sistemas', 'Facturación')")
    tags: List[str] = Field(default_factory=list, description="Palabras clave para filtrado")
    source: Optional[str] = Field(default="desconocido", description="Origen del dato (URL, nombre de archivo)")
    author: Optional[str] = None

class IngestionRequest(BaseModel):
    """Modelo de entrada para la ingestión de un único documento."""
    document_id: Optional[str] = Field(default=None, description="Identificador único opcional")
    title: str = Field(..., description="Título descriptivo del contenido")
    content: str = Field(..., description="El texto principal que será vectorizado")
    metadata: DocumentMetadata

class BulkIngestionRequest(BaseModel):
    """Modelo de entrada para la carga masiva de múltiples documentos."""
    clear_database: bool = Field(default=False, description="Si es True, borra TODO el conocimiento actual antes de inyectar el nuevo")
    documents: List[IngestionRequest]

class IngestionResponse(BaseModel):
    """Modelo de salida para una ingestión individual exitosa."""
    status: str
    message: str
    document_title: str

class BulkIngestionResponse(BaseModel):
    """Modelo de salida que resume los resultados de una carga masiva."""
    status: str
    message: str
    total_documents: int
    total_chunks_saved: int

@router.post("/ingest", response_model=IngestionResponse)
async def ingest_document(request: IngestionRequest):
    """
    Procesa, fragmenta y vectoriza un único documento en la base de conocimiento.
    """
    try:
        chunks = TEXT_SPLITTER.split_text(request.content)
        
        # Inyectamos el título a nivel de chunk junto con los metadatos
        doc_metadata = request.metadata.model_dump()
        doc_metadata["title"] = request.title 
        if request.document_id:
            doc_metadata["document_id"] = request.document_id
            
        docs_to_store = [
            Document(page_content=chunk, metadata=doc_metadata) 
            for chunk in chunks
        ]
        
        # Guardamos en la base de datos vectorial
        vector_store = get_vector_store()
        vector_store.add_documents(docs_to_store)
        
        logger.info(f"Documento '{request.title}' ingerido correctamente con {len(chunks)} fragmentos.")
        
        return IngestionResponse(
            status="success",
            message=f"Documento procesado. Generados {len(chunks)} fragmentos.",
            document_title=request.title
        )
        
    except Exception as e:
        # Registramos el error real en los logs
        logger.error(f"Error en la ingestión del documento '{request.title}': {str(e)}", exc_info=True)
        # Devolvemos un mensaje genérico por seguridad
        raise HTTPException(status_code=500, detail="Error interno durante la ingestión del documento.")

@router.post("/ingest/bulk", response_model=BulkIngestionResponse)
async def bulk_ingest_documents(request: BulkIngestionRequest):
    """
    Procesa y vectoriza múltiples documentos en lote.
    
    Permite opcionalmente vaciar la colección vectorial existente antes de 
    realizar la nueva inserción masiva.
    """
    try:
        if request.clear_database:
            # Operación destructiva: dejamos constancia en los logs internos
            logger.warning("Operación crítica: Vaciando la colección de la base de datos vectorial.")
            PGVector(
                embeddings=embeddings,
                collection_name=COLLECTION_NAME,
                connection=SUPABASE_DB_URL,
                use_jsonb=True,
                pre_delete_collection=True 
            )
            
        all_docs_to_store = []
        
        for doc_req in request.documents:
            chunks = TEXT_SPLITTER.split_text(doc_req.content)
            
            doc_metadata = doc_req.metadata.model_dump()
            doc_metadata["title"] = doc_req.title 
            if doc_req.document_id:
                doc_metadata["document_id"] = doc_req.document_id
                
            for chunk in chunks:
                all_docs_to_store.append(Document(page_content=chunk, metadata=doc_metadata))
                
        if all_docs_to_store:
            vector_store = get_vector_store()
            vector_store.add_documents(all_docs_to_store)
            
        logger.info(f"Ingesta masiva completada: {len(request.documents)} documentos, {len(all_docs_to_store)} chunks.")
        
        return BulkIngestionResponse(
            status="success",
            message="Base de datos vaciada y datos inyectados." if request.clear_database else "Ingesta masiva exitosa.",
            total_documents=len(request.documents),
            total_chunks_saved=len(all_docs_to_store)
        )
        
    except Exception as e:
        logger.error("Error crítico durante el proceso de ingestión masiva.", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno durante la ingestión masiva de documentos.")