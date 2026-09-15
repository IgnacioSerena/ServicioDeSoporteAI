import sys
import os

# Añadimos la raíz del proyecto al path para poder importar los módulos de app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_core.documents import Document
from app.services.vector_store import get_vector_store

def run_ingestion():
    print("Inicializando la conexión con la base de datos vectorial en Supabase...")
    vector_store = get_vector_store()

    # Documentos de prueba simulando un sistema de soporte técnico
    documents = [
        Document(
            page_content="Para solucionar errores de conexión con la API, asegúrate de enviar el token de autorización en las cabeceras HTTP.",
            metadata={"source": "manual_usuario", "category": "autenticacion"}
        ),
        Document(
            page_content="El sistema de Rate Limiting restringe temporalmente las peticiones si superas el límite de 5 solicitudes por minuto por dirección IP.",
            metadata={"source": "manual_usuario", "category": "seguridad"}
        ),
        Document(
            page_content="Si experimentas problemas con la base de datos Supabase, verifica que las credenciales en el archivo .env sean correctas.",
            metadata={"source": "faq", "category": "base_de_datos"}
        )
    ]

    print(f"Generando embeddings e insertando {len(documents)} documentos en Supabase...")
    
    # Añadimos los documentos al vector store (esto genera automáticamente los vectores de 384 dimensiones)
    vector_store.add_documents(documents)
    
    print("¡Ingesta de prueba completada con éxito!")

if __name__ == "__main__":
    run_ingestion()