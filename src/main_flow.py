"""
🚀 Main Flow - Integración de Router, Booking Agent y RAG Agent
Orquesta el flujo completo: Router → Booking/RAG → Response

Soporta dos modos de orquestación:
1. TRADITIONAL (main_flow_traditional) - Simple y directo
2. LANGGRAPH (main_flow_graph) - Usando LangGraph para flujos complejos
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

from router_agent import create_router_agent, route_to_agent
from booking_agent import create_agente_agendamiento
from rag_agent import build_rag  # Función RAG existente

load_dotenv()


# =======================================================
# 🎨 Greeting Agent - Maneja saludos simples
# =======================================================

def create_greeting_agent():
    """Crea un agente para responder saludos iniciales."""
    
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


# =======================================================
# 🌀 Main Flow Tradicional - Orquestación Simple
# =======================================================

def main_flow_traditional():
    """
    Crea el flujo principal que:
    1. Rutea el query según intención
    2. Delega al agente correspondiente
    3. Retorna la respuesta con metadatos
    """
    
    router = create_router_agent()
    booking_agent_fn = create_agente_agendamiento()
    greeting_agent_fn = create_greeting_agent()
    
    # Construir la cadena RAG
    try:
        rag_func = build_rag()
        has_rag = True
    except Exception as e:
        print(f"[WARNING] RAG not available: {e}")
        has_rag = False
    
    # Estado de sesión para mantener el contexto del agente activo
    session_state = {
        "active_agent": None,  # "booking", "rag", "greeting", o None
        "confirmation_pending": False  # True si espera confirmación de agendamiento
    }
    
    def flow(query: str, chat_history: list = None):
        """
        Ejecuta el flujo completo.
        
        Args:
            query: Mensaje del usuario
            chat_history: Historial de conversación (opcional)
        
        Returns:
            dict: {
                "response": str (respuesta del agente),
                "agent_used": str (booking|rag|greeting),
                "confidence": float (confianza del router),
                "reason": str (razón de la clasificación)
            }
        """
        
        if chat_history is None:
            chat_history = []
        
        print(f"\n[USER] {query}")
        
        # 🔄 LÓGICA DE SESIÓN: Si estamos en un agendamiento, mantén el agente activo
        if session_state["active_agent"] == "booking":
            # Verifica si el usuario quiere terminar o cambiar de tema
            termination_keywords = ["cancelar", "listo", "gracias", "adios", "salir", "terminar"]
            confirmation_keywords = ["confirma", "confirmo", "sí", "si", "dale", "ok", "okay"]
            
            # Si dice confirmación, podría ser confirmación final de cita
            if any(kw in query.lower() for kw in confirmation_keywords):
                # Mantén en booking para que confirme la cita
                print("[SESSION] Manteniendo Booking Agent (posible confirmación)")
                response = booking_agent_fn(query)
                
                # Si la respuesta tiene confirmación completa, libera el agente
                if "confirmada" in response.lower() or "✅" in response:
                    session_state["active_agent"] = None
                    session_state["confirmation_pending"] = False
                
                result = {
                    "response": response,
                    "agent_used": "booking",
                    "confidence": 1.0,
                    "reason": "Continuando en sesión de agendamiento"
                }
                chat_history.append(HumanMessage(content=query))
                chat_history.append(AIMessage(content=response))
                return result, chat_history
            
            # Si dice terminar, libera el agente
            elif any(kw in query.lower() for kw in termination_keywords):
                session_state["active_agent"] = None
                session_state["confirmation_pending"] = False
                print("[SESSION] Finalizando sesión de agendamiento")
            else:
                # Sigue en booking sin reclasificar
                print("[SESSION] Manteniendo Booking Agent activo")
                response = booking_agent_fn(query)
                
                result = {
                    "response": response,
                    "agent_used": "booking",
                    "confidence": 1.0,
                    "reason": "Continuando en sesión de agendamiento"
                }
                chat_history.append(HumanMessage(content=query))
                chat_history.append(AIMessage(content=response))
                return result, chat_history
        
        # 🔀 Router classification (solo si no hay agente activo)
        routing_result = route_to_agent(query, router)
        agent_to_use = routing_result["agent"]
        confidence = routing_result["confidence"]
        reason = routing_result["reason"]
        
        print(f"[ROUTER] {agent_to_use.upper()} (confidence: {confidence:.0%})")
        print(f"   Reason: {reason}")
        
        # Low confidence -> escalate
        if not routing_result["proceed"]:
            print("[WARNING] Low confidence, escalating to human...")
            response = "I don't understand your request well. Please be more specific? I can help you schedule appointments or answer questions about pet care."
            agent_to_use = "escalation"
        
        # Delegate to appropriate agent
        elif agent_to_use == "booking":
            print("[DELEGATE] Booking Agent...")
            # ✅ ACTIVAR SESIÓN DE AGENDAMIENTO
            session_state["active_agent"] = "booking"
            session_state["confirmation_pending"] = True
            response = booking_agent_fn(query)
            
            # 🚨 Si el booking agent genera una escalación, liberar sesión
            if "🚨" in response or "agente humano" in response.lower():
                print("[ESCALATION] Liberando sesión de agendamiento")
                session_state["active_agent"] = None
                session_state["confirmation_pending"] = False
        
        elif agent_to_use == "rag":
            print("[DELEGATE] RAG Agent...")
            if has_rag:
                try:
                    # Mejorar la consulta considerando historial reciente
                    # Si hay mensajes anteriores sobre un tema, incluirlo
                    enhanced_query = query
                    if len(chat_history) >= 2:
                        # Buscar contexto en últimos 2 mensajes
                        recent = [m.content for m in chat_history[-4:] if hasattr(m, 'content')]
                        recent_text = " ".join(recent)
                        # Si hay palabras clave de tema específico, enriquecer la consulta
                        if "rabia" in recent_text.lower() and "rabia" not in query.lower():
                            enhanced_query = f"{query} (en contexto de rabia en mascotas)"
                        elif "trm" in recent_text.lower() and "trm" not in query.lower().lower():
                            enhanced_query = f"{query} (sobre tenencia responsable)"
                    
                    result = rag_func(enhanced_query)
                    response = result.content if hasattr(result, 'content') else str(result)
                except Exception as e:
                    response = f"Error en RAG: {e}"
            else:
                response = "Buscando información sobre tu pregunta en nuestra base de datos veterinaria..."
        
        elif agent_to_use == "greeting":
            print("[DELEGATE] Greeting Agent...")
            response = greeting_agent_fn(query)
        
        # Return result with metadata
        result = {
            "response": response,
            "agent_used": agent_to_use,
            "confidence": confidence,
            "reason": reason
        }
        
        # Update history
        chat_history.append(HumanMessage(content=query))
        chat_history.append(AIMessage(content=response))
        
        return result, chat_history
    
    return flow


# =======================================================
# 🧪 Demostración Interactiva
# =======================================================

def demo():
    """Demostración interactiva del sistema."""
    
    print("=" * 60)
    print("🏥 VetCare AI - Sistema de Asistencia Veterinaria")
    print("=" * 60)
    print("\nEscribe 'salir' para terminar.\n")
    
    flow = create_main_flow()
    chat_history = []
    
    while True:
        try:
            user_input = input("👤 Tú: ").strip()
            
            if user_input.lower() in ["salir", "exit", "quit"]:
                print("\n👋 ¡Hasta luego!")
                break
            
            if not user_input:
                continue
            
            result, chat_history = flow(user_input, chat_history)
            
            print(f"\n🤖 Asistente ({result['agent_used']}): {result['response']}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


# =======================================================
# 🔄 WRAPPER PARA ELEGIR MODO DE ORQUESTACIÓN
# =======================================================

def create_main_flow(use_langgraph: bool = False):
    """
    Crea el flujo principal con opción de usar LangGraph o modo tradicional
    
    Args:
        use_langgraph: Si True, usa LangGraph. Si False, usa modo tradicional.
        
    Returns:
        Función que procesa queries
    """
    
    if use_langgraph:
        print("[INFO] Usando orquestación con LangGraph")
        try:
            from graph_flow import graph_flow
            return graph_flow
        except ImportError:
            print("[WARN] LangGraph no disponible, usando modo tradicional")
            return main_flow_traditional()
    else:
        print("[INFO] Usando orquestación tradicional")
        return main_flow_traditional()


# =======================================================
# 🚀 CLI Principal
# =======================================================

def main():
    """Entrada principal."""
    import sys
    
    if len(sys.argv) > 1:
        # Modo no interactivo: procesar argumentos
        query = " ".join(sys.argv[1:])
        flow = create_main_flow()
        result, _ = flow(query)
        print(f"\n{result['response']}")
    else:
        # Modo interactivo
        demo()


if __name__ == "__main__":
    main()
