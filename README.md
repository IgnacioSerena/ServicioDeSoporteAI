# 🤖 ServicioDeSoporteAI - API RAG Resiliente

Una API REST de alto rendimiento diseñada para integrarse en el frontend de plataformas web, proporcionando un asistente de soporte al cliente automatizado. 

Este proyecto implementa un pipeline **RAG (Retrieval-Augmented Generation)** enfocado en la fiabilidad en entornos de producción, mitigando problemas comunes como los límites de cuota (Rate Limits) y la indisponibilidad de modelos de terceros.

## 🏗️ Arquitectura y Stack Tecnológico

* **Framework API:** [FastAPI](https://fastapi.tiangolo.com/) (Python)
* **Orquestación RAG:** [LangChain](https://python.langchain.com/)
* **Base de Datos & Vector Store:** PostgreSQL + `pgvector` (alojado en Supabase)
* **LLM Principal:** Groq (Llama 3) para inferencia de ultra-baja latencia.
* **LLM Fallback:** Google Gemini (Alta disponibilidad).

## ✨ Características Principales (MLOps & Resiliencia)

1. **Defensa contra Abusos:** Implementación de `SlowAPI` para limitar el número de peticiones por IP, protegiendo los endpoints de ataques y agotamiento de cuotas gratuitas.
2. **Tolerancia a Fallos (Fallbacks):** Si el LLM principal devuelve un error `429 Too Many Requests` o se cae, el sistema enruta automáticamente la consulta al modelo de respaldo sin interrumpir la experiencia del usuario.
3. **Caché Semántica en PostgreSQL:** Las respuestas generadas se almacenan en la base de datos relacional. Reduciendo la latencia y el coste computacional en preguntas frecuentes.

## 🚀 Instalación y Despliegue Local

### 1. Clonar el repositorio
\`\`\`bash
git clone https://github.com/IgnacioSerena/ServicioDeSoporteAI.git
cd ServicioDeSoporteAI
\`\`\`

### 2. Crear y activar el entorno virtual
\`\`\`bash
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/Mac:
source .venv/bin/activate
\`\`\`

### 3. Instalar dependencias
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 4. Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto basándote en el archivo `.env.example` e incluye tus claves:
\`\`\`env
SUPABASE_DB_URL="postgresql://usuario:password@host..."
GROQ_API_KEY="tu_clave_groq"
GEMINI_API_KEY="tu_clave_gemini"
\`\`\`

### 5. Iniciar el servidor
\`\`\`bash
uvicorn main:app --reload
\`\`\`
La API estará disponible en `http://localhost:8000` y la documentación interactiva (Swagger) en `http://localhost:8000/docs`.
