import os
import json
import random
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool

load_dotenv()

# =======================================================
# 🛠️ Tools con LangChain
# =======================================================

@tool
def check_availability_tool(dia: str, hora: str) -> str:
    """Verifica disponibilidad para agendar una visita veterinaria.
    
    Args:
        dia: Día de la cita (ej: 13, mañana, lunes)
        hora: Hora de la cita (ej: 10, 10:00, 10 am)
    
    Returns:
        Mensaje indicando si está disponible o no.
    """
    print(f"🕓 Revisando disponibilidad para {dia} a las {hora}...")
    available = random.choice([True, False])
    if available:
        return f"✅ El horario {hora} del {dia} está disponible."
    else:
        return f"❌ El horario {hora} del {dia} NO está disponible."


# =======================================================
# 🆘 Simulación de API de Escalación (TOOL de LangChain)
# =======================================================
@tool
def request_human_agent_tool(nombre: str, telefono: str, email: str = "sin email") -> str:
    """Solicita atención de un agente humano e imprime ticket de soporte.
    
    Esta herramienta simula una llamada a una API de escalación.
    Crea un ticket de soporte cuando el usuario necesita hablar con una persona.
    
    Args:
        nombre: Nombre del usuario que solicita atención humana
        telefono: Teléfono de contacto del usuario
        email: Email del usuario (opcional)
    
    Returns:
        Confirmación de que el ticket fue creado
    """
    ticket_message = f"TICKET CREADO: El usuario {nombre} ({telefono}) ha solicitado atención humana."
    print(ticket_message)
    return f"✅ Ticket creado exitosamente para {nombre}. Un agente humano se contactará pronto al {telefono}."


# =======================================================
# 🤖 Crear Agente con LangChain + Tool Calling + Memoria
# =======================================================
def create_agente_agendamiento():
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Vincular herramientas al LLM
    tools = [check_availability_tool, request_human_agent_tool]
    llm_with_tools = llm.bind_tools(tools)

    system_prompt = """
Eres VetCare AI, un asistente veterinario amable. Tu objetivo es agendar citas veterinarias.

FLUJO EXACTO (SIGUE ESTOS PASOS EN ORDEN):

PASO 1: RECOPILAR DÍA Y HORA
- Pregunta: "¿Qué día te gustaría agendar la cita? (ej: mañana, el 15 de diciembre)"
- Pregunta: "¿A qué hora?" (ej: 10 am, 14:30)

PASO 2: VERIFICAR DISPONIBILIDAD (UNA SOLA VEZ)
- Usa check_availability_tool con el día y hora exactos
- Espera la respuesta

PASO 3: VALIDACIÓN DE RESULTADO
- Si ✅ DISPONIBLE: Continúa al PASO 4
- Si ❌ NO DISPONIBLE: Sugiere otras fechas/horas y vuelve al PASO 1

PASO 4: RECOPILAR DATOS DEL DUEÑO
- Nombre completo
- Teléfono
- Email

PASO 5: RECOPILAR DATOS DE LA MASCOTA
- Nombre de la mascota
- Especie (perro, gato, etc.)
- Raza
- Edad

PASO 6: MOTIVO DE LA CONSULTA
- Pregunta: "¿Cuál es el motivo de la visita?"
- Escucha la respuesta

PASO 7: CONFIRMACIÓN FINAL
Cuando tengas TODOS los datos, haz un resumen exacto así:
---
✅ CITA CONFIRMADA
📅 Fecha: [día]
🕐 Hora: [hora]
👤 Dueño: [nombre], Tel: [teléfono], Email: [email]
🐾 Mascota: [nombre], Especie: [especie], Raza: [raza], Edad: [edad]
🏥 Motivo: [motivo]
---
Luego agrega: "Tu cita ha sido confirmada exitosamente. ¡Te esperamos!"

REGLAS CRÍTICAS:
1. NO llames a check_availability_tool más de una vez por horario
2. NO confirmes sin TODOS los datos
3. Haz confirmación con el resumen mostrado
4. Sé conversacional pero sigue el flujo
5. Si te piden escalar a humano: "He solicitado a un agente humano que te contacte lo antes posible."
"""

    # 🧩 Prompt dinámico
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{chat_history}"),
        ("user", "{input}")
    ])

    chain = prompt | llm_with_tools

    # 🧠 Historial de conversación (memoria)
    chat_history = []
    # Guardar qué horarios ya fueron verificados
    verified_slots = set()

    def agent(query: str):
        nonlocal chat_history, verified_slots
        
        # 🔍 Detección de intención de escalación
        escalation_triggers = [
            # Español
            "humano", "persona", "hablar con alguien", "hablar con una persona",
            "agente humano", "representante", "frustrado", "no me entiende",
            "hablar con un", "atención humana", "escalar", "escalada",
            "quiero hablar", "necesito hablar", "ayuda de un humano",
            "no sirve", "esto no funciona", "no entiendo",
            # English
            "human", "person", "agent", "representative", "frustrated",
            "escalate", "speak to", "talk to", "help",
            # Variations
            "escala", "humanó"  # typos comunes
        ]
        
        query_lower = query.lower()
        is_escalation = any(trigger in query_lower for trigger in escalation_triggers)
        
        if is_escalation:
            print(f"🚨 ESCALACIÓN DETECTADA: {query}")
            
            # Intentar extraer nombre y teléfono del historial
            user_info = {"nombre": "Desconocido", "telefono": "sin teléfono", "email": "sin email"}
            
            # Buscar nombre y teléfono en el historial
            for msg in chat_history:
                if msg.type == "human":
                    content_lower = msg.content.lower()
                    content_original = msg.content
                    
                    # Buscar patrón de teléfono
                    telefono_match = re.search(r'\+?[\d\s\-\(\)]{8,}', content_original)
                    if telefono_match:
                        user_info["telefono"] = telefono_match.group(0).strip()
                    
                    # Buscar email
                    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content_original)
                    if email_match:
                        user_info["email"] = email_match.group(0).strip()
                    
                    # Buscar nombre (primera palabra que comience con mayúscula después de "mi nombre es" o "soy")
                    if any(kw in content_lower for kw in ["mi nombre es", "me llamo", "soy ", "nombre es", "llamo"]):
                        # Extraer nombre simple
                        words = content_original.split()
                        for i, word in enumerate(words):
                            if word.lower() in ["soy", "es", "llamo", "i'm", "im"] and i + 1 < len(words):
                                candidate = words[i + 1].strip(".,!?").capitalize()
                                if len(candidate) > 1:  # Al menos 2 caracteres
                                    user_info["nombre"] = candidate
                                    break
            
            print(f"📋 INFO USUARIO PARA ESCALACIÓN: {user_info}")
            
            # Llamar a la herramienta (Tool) de escalación
            escalation_result = request_human_agent_tool.invoke({
                "nombre": user_info.get("nombre", "Desconocido"),
                "telefono": user_info.get("telefono", "sin teléfono"),
                "email": user_info.get("email", "sin email")
            })
            
            # Limpiar historial para nueva conversación
            chat_history.clear()
            verified_slots.clear()
            
            return "🚨 He solicitado a un agente humano que te contacte lo antes posible.\n\nNombre registrado: {}\nTeléfono: {}\n\n¡Te esperamos!".format(
                user_info.get('nombre', 'Desconocido'),
                user_info.get('telefono', 'sin teléfono')
            )

        # 🧠 Agregar mensaje del usuario al historial
        chat_history.append(HumanMessage(content=query))
        
        # 🔄 Loop de ejecución del agente
        try:
            messages = chat_history.copy()
            
            # Primera invocación
            response = chain.invoke({
                "input": query,
                "chat_history": messages
            })
            
            # Procesar tool calls (máximo 1 para evitar loops infinitos)
            if response.tool_calls:
                tool_call = response.tool_calls[0]
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                # Ejecutar check_availability_tool
                if tool_name == "check_availability_tool":
                    slot_key = f"{tool_args['dia']}_{tool_args['hora']}"
                    
                    # Verificar si ya fue validado
                    if slot_key in verified_slots:
                        tool_result = f"⚠️ Este horario ya fue verificado anteriormente."
                    else:
                        tool_result = check_availability_tool.invoke(tool_args)
                        verified_slots.add(slot_key)
                    
                    # Agregar tool result al historial
                    messages.append(AIMessage(content=response.content or ""))
                    messages.append(HumanMessage(content=f"Resultado de validación: {tool_result}"))
                    
                    # Una sola invocación más después del tool
                    response = chain.invoke({
                        "input": f"El horario fue validado. {tool_result}. Continúa recopilando datos del usuario para confirmar la cita.",
                        "chat_history": messages
                    })
                
                # Ejecutar request_human_agent_tool
                elif tool_name == "request_human_agent_tool":
                    tool_result = request_human_agent_tool.invoke(tool_args)
                    print(f"✅ Tool de escalación ejecutado: {tool_result}")
                    
                    # Limpiar historial para nueva conversación
                    chat_history.clear()
                    verified_slots.clear()
                    
                    return "🚨 He solicitado a un agente humano que te contacte lo antes posible.\n\n¡Te esperamos!"
            
            # Respuesta final
            response_text = response.content.strip() if response.content else "Listo, estoy aquí para ayudarte."
            
            # NUEVO: Si la respuesta contiene indicadores de confirmación final, agrega un último mensaje
            confirmation_keywords = ["confirmada", "cita confirmada", "✅", "agendada", "reservada"]
            if any(keyword in response_text.lower() for keyword in confirmation_keywords):
                # Asegurarse de que la respuesta incluya el resumen formateado
                if "Fecha:" not in response_text or "Mascota:" not in response_text:
                    # Solicitar confirmación final formateada
                    messages.append(AIMessage(content=response_text))
                    response = chain.invoke({
                        "input": "Por favor, haz la CONFIRMACIÓN FINAL con el resumen completo en el formato especificado.",
                        "chat_history": messages
                    })
                    response_text = response.content.strip() if response.content else response_text
            
            # Actualizar histórico global
            chat_history.clear()
            chat_history.extend(messages)
            chat_history.append(AIMessage(content=response_text))
            
            return response_text
        except Exception as e:
            error_msg = f"Error al procesar tu solicitud: {str(e)}"
            chat_history.append(AIMessage(content=error_msg))
            return error_msg

    return agent


# =======================================================
# 🧪 CLI de prueba
# =======================================================
def main():
    print("=== 🐾 VetCare AI — Agendamiento con Memoria + Tool Calling ===")
    agente = create_agente_agendamiento()

    while True:
        user = input("\nTú: ")
        if user.lower() in ["salir", "exit"]:
            break

        res = agente(user)
        print("\n🤖 VetCare AI:")
        print(res)


if __name__ == "__main__":
    main()