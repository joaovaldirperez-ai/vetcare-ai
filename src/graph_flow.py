"""
🏥 VetCare AI - Orquestación con LangGraph
Sistema multi-agente usando LangGraph para manejo de flujos complejos
"""

import os
import sys
from pathlib import Path
from typing import TypedDict, Literal, Annotated
from dotenv import load_dotenv

# Asegurar que podemos importar desde src
sys.path.insert(0, str(Path(__file__).parent))

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from router_agent import create_router_agent
from booking_agent import create_agente_agendamiento
from rag_agent import build_rag

load_dotenv()

# ═══════════════════════════════════════════════════════════════════
# 🤖 GREETING AGENT AUXILIAR
# ═══════════════════════════════════════════════════════════════════

def create_greeting_agent():
    """Crea un agente para responder saludos iniciales."""
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    greeting_prompt = ChatPromptTemplate.from_template("""
Eres un asistente amable de una clínica veterinaria. El usuario ha saludado.
Responde de manera cálida y ofrece tus servicios principales.

Mensaje del usuario: {query}

Mantén la respuesta breve (2-3 líneas) y en español.
Menciona que puedes: agendar citas, responder dudas sobre mascotas, o escalar a atención humana.
""")
    
    chain = greeting_prompt | llm
    
    def agent(query: str):
        response = chain.invoke({"query": query})
        return response.content
    
    return agent

# ═══════════════════════════════════════════════════════════════════
# 📊 ESTADO DEL GRAFO
# ═══════════════════════════════════════════════════════════════════

class AgentState(TypedDict):
    """Estado compartido entre nodos del grafo"""
    query: str                      # Mensaje del usuario
    chat_history: list[BaseMessage] # Historial de conversación
    agent_type: Literal["booking", "rag", "greeting", "escalation"]
    response: str                   # Respuesta final
    confidence: float               # Confianza del router
    reason: str                     # Razón de la clasificación
    agent_used: str                 # Agente que procesó
    metadata: dict                  # Información adicional


# ═══════════════════════════════════════════════════════════════════
# 🧭 NODOS DEL GRAFO
# ═══════════════════════════════════════════════════════════════════

def router_node(state: AgentState) -> AgentState:
    """
    Nodo Router: Clasifica la intención del usuario
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Estado actualizado con clasificación
    """
    print(f"\n[ROUTER] Procesando: {state['query'][:50]}...")
    
    router = create_router_agent()
    result = router(state["query"])
    
    # Actualizar estado con clasificación
    state["agent_type"] = result["intent"]
    state["confidence"] = result["confidence"]
    state["reason"] = result["reason"]
    
    print(f"[ROUTER] → {result['intent'].upper()} (confidence: {result['confidence']:.0%})")
    print(f"[ROUTER] Razón: {result['reason']}")
    
    return state


def booking_node(state: AgentState) -> AgentState:
    """
    Nodo Booking: Maneja agendamiento de citas
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Estado con respuesta de booking
    """
    print(f"\n[BOOKING] Procesando solicitud de cita...")
    
    agent = create_agente_agendamiento()
    # El agente retorna solo response
    response = agent(state["query"])
    
    state["response"] = response
    state["agent_used"] = "booking"
    
    return state


def rag_node(state: AgentState) -> AgentState:
    """
    Nodo RAG: Responde preguntas sobre cuidados de mascotas
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Estado con respuesta RAG
    """
    print(f"\n[RAG] Buscando información relevante...")
    
    # Construir la cadena RAG
    rag_func, rag_retriever = build_rag()
    
    # Invocar la función RAG con el query
    response = rag_func(state["query"])
    
    # Si la respuesta es un dict, extraer el contenido
    if isinstance(response, dict):
        response_text = str(response)
    else:
        response_text = response.content if hasattr(response, 'content') else str(response)
    
    state["response"] = response_text
    if state["chat_history"] is None:
        state["chat_history"] = []
    state["chat_history"].append(HumanMessage(content=state["query"]))
    state["chat_history"].append(AIMessage(content=response_text))
    state["agent_used"] = "rag"
    
    return state


def greeting_node(state: AgentState) -> AgentState:
    """
    Nodo Greeting: Maneja saludos y presentación
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Estado con respuesta de saludo
    """
    print(f"\n[GREETING] Respondiendo saludo...")
    
    agent = create_greeting_agent()
    response = agent(state["query"])
    
    state["response"] = response
    if state["chat_history"] is None:
        state["chat_history"] = []
    state["chat_history"].append(HumanMessage(content=state["query"]))
    state["chat_history"].append(AIMessage(content=response))
    state["agent_used"] = "greeting"
    
    return state


# ═══════════════════════════════════════════════════════════════════
# 🎯 FUNCIONES DE ROUTING CONDICIONAL
# ═══════════════════════════════════════════════════════════════════

def route_to_agent(state: AgentState) -> Literal["booking", "rag", "greeting"]:
    """
    Determina a qué agente enviar basado en la clasificación del router
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Nombre del nodo destino
    """
    agent_type = state["agent_type"]
    
    if agent_type == "booking":
        return "booking"
    elif agent_type == "rag":
        return "rag"
    else:
        return "greeting"


# ═══════════════════════════════════════════════════════════════════
# 🏗️ CONSTRUCCIÓN DEL GRAFO
# ═══════════════════════════════════════════════════════════════════

def create_graph_flow():
    """
    Crea y compila el grafo de flujo para VetCare AI
    
    Flujo:
        START → Router → [Booking|RAG|Greeting] → END
    
    Returns:
        Grafo compilado listo para invocar
    """
    
    # Crear el grafo
    graph = StateGraph(AgentState)
    
    # Agregar nodos
    graph.add_node("router", router_node)
    graph.add_node("booking", booking_node)
    graph.add_node("rag", rag_node)
    graph.add_node("greeting", greeting_node)
    
    # Agregar aristas
    # START → Router (siempre empieza en router)
    graph.add_edge(START, "router")
    
    # Router → [Booking|RAG|Greeting] (condicional)
    graph.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "booking": "booking",
            "rag": "rag",
            "greeting": "greeting"
        }
    )
    
    # Cada agente → END
    graph.add_edge("booking", END)
    graph.add_edge("rag", END)
    graph.add_edge("greeting", END)
    
    # Compilar el grafo
    compiled_graph = graph.compile()
    
    return compiled_graph


# ═══════════════════════════════════════════════════════════════════
# 🚀 FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════

def graph_flow(query: str, chat_history: list = None):
    """
    Ejecuta el flujo del sistema usando LangGraph
    
    Args:
        query: Mensaje del usuario
        chat_history: Historial de conversación anterior
        
    Returns:
        tuple: (resultado, chat_history_actualizado)
    """
    
    if chat_history is None:
        chat_history = []
    
    # Crear estado inicial
    initial_state = AgentState(
        query=query,
        chat_history=chat_history,
        agent_type="greeting",
        response="",
        confidence=0.0,
        reason="",
        agent_used="",
        metadata={}
    )
    
    # Obtener el grafo compilado
    compiled_graph = create_graph_flow()
    
    # Ejecutar el grafo
    final_state = compiled_graph.invoke(initial_state)
    
    # Agregar al historial
    chat_history.append(HumanMessage(content=query))
    chat_history.append(AIMessage(content=final_state["response"]))
    
    # Resultado
    result = {
        "response": final_state["response"],
        "agent_used": final_state["agent_used"],
        "confidence": final_state["confidence"],
        "reason": final_state["reason"]
    }
    
    return result, chat_history


def get_graph_visualization():
    """
    Retorna la representación del grafo para debugging
    
    Returns:
        str: Descripción del grafo
    """
    return """
    📊 LANGGRAPH STRUCTURE:
    
    START
      ↓
    [ROUTER NODE]
      ├─ Clasifica intención del usuario
      └─ Determina destino (Booking|RAG|Greeting)
      ↓
    ┌─────────────────────────────────────┐
    │                                     │
    ↓                ↓                    ↓
  [BOOKING]      [RAG]              [GREETING]
    │              │                    │
    │ • Agenda     │ • Busca            │ • Responde
    │ • Valida     │ • Retrieval        │ • Saludo
    │ • Confirma   │ • Genera respuesta │
    │              │                    │
    └─────────────────────────────────────┘
      ↓
    [END]
    
    Nodos: 4 (Router, Booking, RAG, Greeting)
    Edges: 4 (Router→[3 agentes], Todos→END)
    Tipo: Condicional
    """


if __name__ == "__main__":
    # Test del grafo
    print("=" * 70)
    print("🏥 VetCare AI - LangGraph Flow Test")
    print("=" * 70)
    
    # Visualizar el grafo
    print("\n📊 ESTRUCTURA DEL GRAFO:")
    print(get_graph_visualization())
    
    # Test 1: Booking
    print("\n" + "=" * 70)
    print("TEST 1: Booking Request")
    print("=" * 70)
    result, history = graph_flow("Quiero agendar una cita para mañana")
    print(f"\n✅ Resultado:")
    print(f"   Agente usado: {result['agent_used']}")
    print(f"   Confianza: {result['confidence']:.0%}")
    print(f"   Respuesta: {result['response'][:100]}...")
    
    # Test 2: RAG
    print("\n" + "=" * 70)
    print("TEST 2: RAG Request")
    print("=" * 70)
    result, history = graph_flow("Mi gato tiene diarrea, ¿qué hago?", history)
    print(f"\n✅ Resultado:")
    print(f"   Agente usado: {result['agent_used']}")
    print(f"   Confianza: {result['confidence']:.0%}")
    print(f"   Respuesta: {result['response'][:100]}...")
    
    # Test 3: Greeting
    print("\n" + "=" * 70)
    print("TEST 3: Greeting Request")
    print("=" * 70)
    result, history = graph_flow("Hola, ¿cómo estás?", history)
    print(f"\n✅ Resultado:")
    print(f"   Agente usado: {result['agent_used']}")
    print(f"   Confianza: {result['confidence']:.0%}")
    print(f"   Respuesta: {result['response'][:100]}...")
    
    print("\n" + "=" * 70)
    print("✅ TODOS LOS TESTS COMPLETADOS")
    print("=" * 70)
