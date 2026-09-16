from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_postgres import PGVector
from app.services.vector_store import get_vector_store, COLLECTION_NAME, embeddings
from app.core.config import SUPABASE_DB_URL

router = APIRouter(tags=["Ingestión de Conocimiento"])

class DocumentMetadata(BaseModel):
    category: str = Field(..., description="Categoría principal del documento (ej. 'Sistemas', 'Facturación')")
    tags: List[str] = Field(default_factory=list, description="Palabras clave para filtrado")
    source: Optional[str] = Field(default="desconocido", description="Origen del dato (URL, nombre de archivo)")
    author: Optional[str] = None

class IngestionRequest(BaseModel):
    document_id: Optional[str] = Field(default=None, description="Identificador único opcional")
    title: str = Field(..., description="Título descriptivo del contenido")
    content: str = Field(..., description="El texto principal que será vectorizado")
    metadata: DocumentMetadata

class BulkIngestionRequest(BaseModel):
    clear_database: bool = Field(default=False, description="Si es True, borra TODO el conocimiento actual antes de inyectar el nuevo")
    documents: List[IngestionRequest]

@router.post("/ingest")
async def ingest_document(request: IngestionRequest):
    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50, separators=["\n\n", "\n", ".", " ", ""])
        chunks = splitter.split_text(request.content)
        
        doc_metadata = request.metadata.model_dump()
        doc_metadata["title"] = request.title 
        if request.document_id:
            doc_metadata["document_id"] = request.document_id
            
        docs_to_store = [
            Document(page_content=chunk, metadata=doc_metadata) 
            for chunk in chunks
        ]
        
        vector_store = get_vector_store()
        vector_store.add_documents(docs_to_store)
        
        return {
            "status": "success",
            "message": f"Documento procesado. Generados {len(chunks)} fragmentos.",
            "document_title": request.title
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la ingestión: {str(e)}")

@router.post("/ingest/bulk")
async def bulk_ingest_documents(request: BulkIngestionRequest):
    try:
        if request.clear_database:
            PGVector(
                embeddings=embeddings,
                collection_name=COLLECTION_NAME,
                connection=SUPABASE_DB_URL,
                use_jsonb=True,
                pre_delete_collection=True 
            )
            
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50, separators=["\n\n", "\n", ".", " ", ""])
        
        all_docs_to_store = []
        for doc_req in request.documents:
            chunks = splitter.split_text(doc_req.content)
            doc_metadata = doc_req.metadata.model_dump()
            doc_metadata["title"] = doc_req.title 
            if doc_req.document_id:
                doc_metadata["document_id"] = doc_req.document_id
                
            for chunk in chunks:
                all_docs_to_store.append(Document(page_content=chunk, metadata=doc_metadata))
                
        if all_docs_to_store:
            vector_store = get_vector_store()
            vector_store.add_documents(all_docs_to_store)
            
        return {
            "status": "success",
            "message": "Base de datos vaciada y datos inyectados." if request.clear_database else "Ingesta masiva exitosa.",
            "total_documents": len(request.documents),
            "total_chunks_saved": len(all_docs_to_store)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la ingestión masiva: {str(e)}")