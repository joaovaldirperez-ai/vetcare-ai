import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


# =======================================================
# 🧭 Router Agent - Rutea a booking_agent o rag_agent
# =======================================================

def create_router_agent():
    """
    Crea un agente router que determina si el usuario quiere:
    1. BOOKING: Agendar una cita veterinaria
    2. RAG: Obtener información sobre cuidados de mascotas
    3. GREETING: Saludo/presentación general
    
    Retorna: función que recibe un query y retorna ("booking"|"rag"|"greeting", confianza)
    """
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    router_prompt = ChatPromptTemplate.from_template("""
Eres un clasificador de intenciones para un asistente veterinario. Analiza el mensaje del usuario y determina su intención.

⚠️ ESCALACIÓN (PRIORIDAD MÁXIMA):
Si el usuario solicita hablar con un humano, pedir escalación o expresar frustración, categoriza como BOOKING (el agente de booking manejará la escalación).

CATEGORÍAS:
1. BOOKING: 
   - El usuario quiere agendar una cita, reservar una consulta, programar una visita
   - El usuario solicita hablar con un humano, pedir escalación, atención humana
   - Expresiones de frustración que pidan ayuda

2. RAG: El usuario pregunta sobre cuidados de mascotas, síntomas, tratamientos, información general

3. GREETING: Saludos iniciales, presentaciones, preguntas genéricas (SIN pedir ayuda)

Mensaje del usuario: {query}

Responde en este formato EXACTO:
INTENCIÓN: [BOOKING|RAG|GREETING]
CONFIANZA: [0.0 a 1.0]
RAZÓN: [Explicación breve]

Ejemplos:
- "Quiero agendar una cita para mañana" → BOOKING (0.95)
- "Necesito hablar con un humano" → BOOKING (0.95) [ESCALACIÓN]
- "Frustrado, quiero hablar con alguien" → BOOKING (0.9) [ESCALACIÓN]
- "Mi perro tiene tos, ¿qué puedo hacer?" → RAG (0.9)
- "Hola, ¿cómo estás?" → GREETING (0.85)
""")
    
    chain = router_prompt | llm
    
    def router(query: str):
        """
        Rutea el query a la intención correspondiente.
        
        Args:
            query: Mensaje del usuario
            
        Returns:
            dict: {"intent": str, "confidence": float, "reason": str}
        """
        try:
            response = chain.invoke({"query": query})
            content = response.content.strip()
            
            # Parsear la respuesta
            result = {
                "intent": "greeting",
                "confidence": 0.0,
                "reason": ""
            }
            
            # Extraer intención
            if "INTENCIÓN: BOOKING" in content or "INTENCIÓN:BOOKING" in content:
                result["intent"] = "booking"
            elif "INTENCIÓN: RAG" in content or "INTENCIÓN:RAG" in content:
                result["intent"] = "rag"
            else:
                result["intent"] = "greeting"
            
            # Extraer confianza
            for line in content.split("\n"):
                if "CONFIANZA:" in line:
                    try:
                        conf_str = line.split("CONFIANZA:")[-1].strip().split()[0]
                        result["confidence"] = float(conf_str)
                    except:
                        result["confidence"] = 0.5
            
            # Extraer razón
            for line in content.split("\n"):
                if "RAZÓN:" in line:
                    result["reason"] = line.split("RAZÓN:")[-1].strip()
            
            return result
        except Exception as e:
            print(f"⚠️ Error en router: {e}")
            return {
                "intent": "greeting",
                "confidence": 0.3,
                "reason": f"Error: {str(e)}"
            }
    
    return router


# =======================================================
# 🎯 Función Principal de Ruteo
# =======================================================

def route_to_agent(query: str, router_fn):
    """
    Rutea el query al agente correspondiente.
    
    Args:
        query: Mensaje del usuario
        router_fn: Función router creada con create_router_agent()
    
    Returns:
        dict: {
            "agent": "booking"|"rag"|"greeting",
            "confidence": float,
            "reason": str,
            "proceed": bool
        }
    """
    
    routing_result = router_fn(query)
    
    result = {
        "agent": routing_result["intent"],
        "confidence": routing_result["confidence"],
        "reason": routing_result["reason"],
        "proceed": routing_result["confidence"] >= 0.7  # Umbral de confianza
    }
    
    return result


# =======================================================
# 🧪 CLI de prueba
# =======================================================

def main():
    print("=== 🧭 Router Agent - Sistema de Clasificación ===\n")
    router = create_router_agent()
    
    # Casos de prueba
    test_queries = [
        "Quiero agendar una cita para mañana a las 10 am",
        "Mi gato tiene diarrea, ¿qué debo hacer?",
        "Hola, ¿cómo estás?",
        "Necesito reservar una consulta para el viernes",
        "¿Cuáles son los síntomas de parásitos en perros?",
        "¿Atienden urgencias veterinarias?",
    ]
    
    print("Procesando queries de prueba...\n")
    for query in test_queries:
        result = route_to_agent(query, router)
        print(f"📝 Query: {query}")
        print(f"🎯 Agente: {result['agent'].upper()}")
        print(f"📊 Confianza: {result['confidence']:.2%}")
        print(f"💬 Razón: {result['reason']}")
        print(f"✅ Proceder: {result['proceed']}\n")


if __name__ == "__main__":
    main()
