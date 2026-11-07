from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# 1. Herramientas (Nota el cambio a TavilySearch)
buscador = TavilySearch(max_results=2)

@tool
def calcular_descuento(precio: float, porcentaje: float) -> float:
    """Útil para calcular el precio final tras aplicar un descuento."""
    return precio - (precio * (porcentaje / 100))

herramientas = [buscador, calcular_descuento]

# 2. Inicializamos Gemini
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# 3. Creamos el agente usando LangGraph (Reemplaza a AgentExecutor)
agente = create_react_agent(llm, herramientas)

# 4. Ejecución interactiva para la consola
consulta = "Busca el precio actual de una ASUS Vivobook 16 y dime cuánto costaría con un 15% de descuento estudiantil."

print(f"Buscando: '{consulta}'\n")

# Usamos stream_mode="values" para ver los pasos uno a uno
for evento in agente.stream({"messages": [("user", consulta)]}, stream_mode="values"):
    mensaje = evento["messages"][-1]
    
    # Si la IA decide llamar a una herramienta
    if hasattr(mensaje, 'tool_calls') and mensaje.tool_calls:
        print(f"🧠 Gemini decide usar: {mensaje.tool_calls[0]['name']}")
        print(f"   Argumentos: {mensaje.tool_calls[0]['args']}")
        
    # Si el mensaje contiene el resultado de la herramienta
    elif mensaje.type == 'tool':
        # Acortamos el output para que no inunde la consola
        recorte = str(mensaje.content)[:150] + "..."
        print(f"🔧 Resultado devuelto a Gemini: {recorte}\n")
        
    # Si es el mensaje final de la IA (sin llamadas a herramientas)
    elif mensaje.type == 'ai' and not getattr(mensaje, 'tool_calls', None):
        print(f"✅ Respuesta final:\n{mensaje.content}")