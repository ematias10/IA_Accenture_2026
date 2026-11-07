from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os

import os
from dotenv import load_dotenv
# Asegúrate de que los estudiantes tengan su API key configurada
# os.environ["GOOGLE_API_KEY"] = "tu_api_key_aqui"
load_dotenv()
# Inicializamos Gemini (recomendado usar flash para tareas rápidas)
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0)

prompt = PromptTemplate.from_template("¿Cuál es el precio de la notebook {modelo} en Chile?")

cadena = prompt | llm

respuesta = cadena.invoke({"modelo": "ASUS Vivobook 16"})
print(respuesta.content)