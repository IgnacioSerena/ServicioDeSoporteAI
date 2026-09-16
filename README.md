# 🤖 ServicioDeSoporteAI - API RAG Resiliente con Memoria

Una API REST de alto rendimiento diseñada para integrarse en el frontend de plataformas web, proporcionando un asistente de soporte al cliente automatizado e inteligente. 

Este proyecto implementa un pipeline **RAG (Retrieval-Augmented Generation)** enfocado en la fiabilidad en entornos de producción, mitigando problemas comunes como los límites de cuota (Rate Limits), la indisponibilidad de modelos de terceros y el desbordamiento de contexto.

## 🏗️ Arquitectura y Stack Tecnológico

* **Framework API:** [FastAPI](https://fastapi.tiangolo.com/) (Python)
* **Orquestación RAG:** [LangChain LCEL](https://python.langchain.com/)
* **Base de Datos & Vector Store:** PostgreSQL + `pgvector` (alojado en Supabase)
* **LLM Principal:** Google Gemini (`gemini-3.5-flash-lite`).
* **LLM Fallback:** Google Gemini (`gemini-3.1-flash-lite`).

## ✨ Características Principales (Ingeniería & MLOps)

1. **Tolerancia a Fallos (Zero-Downtime Fallbacks):** Si el LLM principal agota su cuota (error `429 Too Many Requests`) o experimenta caídas, el sistema enruta la consulta automáticamente al modelo de respaldo en milisegundos sin interrumpir la experiencia del usuario.
2. **Memoria Conversacional Persistente:** Soporte nativo para hilos de conversación multitenant mediante `session_id`. Permite identificar usuarios o pestañas y recordar el contexto de preguntas anteriores.
3. **Gestión Inteligente de Contexto:** Implementación de un sistema de truncado (`trim_messages`) con conteo de tokens local. Evita desbordamientos de ventana de contexto eliminando de forma segura los mensajes más antiguos de la sesión.
4. **Ingestión Estructurada y Masiva (Bulk):** Pipeline de vectorización que separa el contenido de sus metadatos (`JSONB`) y permite el borrado/sobreescritura segura de la base de datos entera de forma atómica para evitar desincronizaciones con el frontend.
5. **Defensa contra Abusos:** Implementación de `SlowAPI` para limitar el número de peticiones por IP, protegiendo los endpoints de ataques y controlando los costes de infraestructura.
6. **Caché Semántica en PostgreSQL:** Las respuestas generadas se almacenan en la base de datos relacional, reduciendo la latencia y el coste computacional en preguntas frecuentes.

## 🚀 Instalación y Despliegue Local

### 1. Clonar el repositorio
```bash
git clone [https://github.com/IgnacioSerena/ServicioDeSoporteAI.git](https://github.com/IgnacioSerena/ServicioDeSoporteAI.git)
cd ServicioDeSoporteAI
```

### 2. Crear y activar el entorno virtual
```bash
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/Mac:
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto e incluye tus claves:
```env
SUPABASE_DB_URL="postgresql://usuario:password@host..."
GOOGLE_API_KEY="tu_clave_gemini"
```

### 5. Iniciar el servidor
```bash
uvicorn app.main:app --reload
```

---

## 📖 Uso de la API (Endpoints Principales)

### 1. Ingestión de Documento Único (`POST /api/v1/ingest`)
Endpoint para añadir un documento individual a la base de datos vectorial sin alterar el resto.

**Payload de ejemplo:**
```json
{
  "document_id": "doc-001",
  "title": "Solución al Error 500",
  "content": "Verifica los logs del pod de autenticación y reinicia el servicio...",
  "metadata": {
    "category": "Backend",
    "tags": ["api", "error 500"]
  }
}
```

### 2. Ingestión Masiva y Sincronización (`POST /api/v1/ingest/bulk`)
Endpoint optimizado para inyectar múltiples documentos a la vez. Permite limpiar la base de datos antes de insertar los nuevos datos, evitando información duplicada o desactualizada.

**Payload de ejemplo:**
```json
{
  "clear_database": true,
  "documents": [
    {
      "document_id": "doc-001",
      "title": "Precios 2026",
      "content": "El plan básico cuesta 5€...",
      "metadata": { "category": "Precios" }
    }
  ]
}
```

### 3. Chat con Soporte RAG (`POST /api/v1/ask`)
Endpoint principal para interactuar con la IA manteniendo el contexto.

**Payload de ejemplo:**
```json
{
  "query": "¿Qué hago si tengo un error 500?",
  "session_id": "usuario_12345" 
}
```

---

## 🔄 Mantenimiento y Actualización de Datos

Para que el asistente responda con información precisa y al día (como cambios de precios, nuevas funcionalidades o fechas de lanzamiento), la base de datos vectorial debe actualizarse cada vez que el contenido de la página web cambie.

El sistema está diseñado para que el administrador de la web pueda sincronizar la información de forma extremadamente sencilla.

### ¿Cómo actualizar la información del bot?

#### Opción A: Automatización con cURL (Ideal para un parche rápido)
Si solo quieres añadir una corrección rápida sin borrar el resto:

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/ingest' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "document_id": "precios-v2",
  "title": "Actualización de Precios 2026",
  "content": "El nuevo producto estrella sale a la venta el 15 de noviembre.",
  "metadata": {
    "category": "Precios",
    "tags": ["lanzamiento"],
    "source": "update-script"
  }
}'
```

#### Opción B: Script de Sincronización Masiva (Recomendado para CI/CD)
Si tienes toda la información de tu web en un archivo `datos_web.json`, este script borra la base de datos antigua y sube la nueva versión limpia de un solo golpe, evitando la "trampa del bucle" y los datos duplicados:

```python
import requests
import json

API_URL = "http://localhost:8000/api/v1/ingest/bulk"
ARCHIVO_JSON = "datos_web.json" # Tu archivo con la lista de documentos

def sincronizar_conocimiento():
    # 1. Cargamos los datos del frontend
    with open(ARCHIVO_JSON, 'r', encoding='utf-8') as f:
        documentos = json.load(f)
        
    print(f"Iniciando sincronización de {len(documentos)} documentos...")
    
    # 2. Preparamos el payload masivo indicando que borre lo anterior
    payload = {
        "clear_database": True, 
        "documents": documentos
    }
    
    # 3. Disparamos la petición
    respuesta = requests.post(API_URL, json=payload)
    
    if respuesta.status_code == 200:
        datos = respuesta.json()
        print(f"✅ Éxito: {datos['message']}")
        print(f"   - Documentos procesados: {datos['total_documents']}")
        print(f"   - Vectores (chunks) guardados: {datos['total_chunks_saved']}")
    else:
        print(f"❌ Error al sincronizar: {respuesta.text}")

if __name__ == "__main__":
    sincronizar_conocimiento()
```