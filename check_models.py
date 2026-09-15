import os
from dotenv import load_dotenv
from google import genai

# Carga las variables del entorno desde el archivo .env
load_dotenv()

# Inicializa el cliente oficial de Google GenAI
client = genai.Client()

print("Modelos disponibles compatibles con generateContent:")
print("-" * 50)

# Llama al ModelService/Client para listar los modelos
for model in client.models.list():
    # Filtramos para mostrar los que soportan generación de contenido
    if model.supported_actions and "generateContent" in model.supported_actions:
        print(f"- {model.name}")