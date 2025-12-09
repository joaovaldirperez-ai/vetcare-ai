#!/usr/bin/env python3
"""
🏥 VetCare AI - Chat Simple e Intuitivo
Asistente Veterinario Inteligente
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))

from dotenv import load_dotenv
load_dotenv()

from main_flow import create_main_flow

# ═══════════════════════════════════════════════════════════════════
# 🎨 CONFIGURACIÓN DE PÁGINA
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="🏥 VetCare AI",
    page_icon="🐾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════════════════════
# 🎯 INICIALIZAR SESSION STATE
# ═══════════════════════════════════════════════════════════════════
if "main_flow" not in st.session_state:
    st.session_state.main_flow = create_main_flow()
    st.session_state.chat_history = []
    st.session_state.messages = []  # Historial de mensajes para mostrar

# ═══════════════════════════════════════════════════════════════════
# 💬 HEADER CON SUGERENCIAS
# ═══════════════════════════════════════════════════════════════════
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
        <div style="text-align: center;">
            <h1 style="margin: 0; font-size: 32px;">🏥 VetCare AI</h1>
            <p style="color: #666; font-size: 13px; margin: 5px 0 0 0;">
                Asistente Veterinario Inteligente
            </p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div style="font-size: 12px; color: #555; line-height: 1.6;">
            <b style="color: #667eea;">💡 Ejemplos:</b><br>
            • Agendar cita<br>
            • Preguntas sobre mascotas<br>
            • Hablar con humano
        </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# 💬 MOSTRAR HISTORIAL DE MENSAJES
# ═══════════════════════════════════════════════════════════════════
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
                <div style="text-align: right; margin-bottom: 12px;">
                    <div style="
                        display: inline-block;
                        background: #e8f4f8;
                        padding: 12px 16px;
                        border-radius: 12px;
                        max-width: 70%;
                        text-align: left;
                    ">
                        <p style="margin: 0; color: #333; font-size: 15px; line-height: 1.5;">
                            {msg['content']}
                        </p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style="text-align: left; margin-bottom: 12px;">
                    <div style="
                        display: inline-block;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 12px 16px;
                        border-radius: 12px;
                        max-width: 70%;
                        color: white;
                    ">
                        <p style="margin: 0; font-size: 15px; line-height: 1.5;">
                            {msg['content']}
                        </p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# 💬 CHAT INPUT
# ═══════════════════════════════════════════════════════════════════
user_input = st.chat_input(
    placeholder="📝 Escribe tu pregunta, reserva o saludo...",
    key="chat_input"
)

if user_input:
    # Agregar mensaje del usuario al historial INMEDIATAMENTE
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Mostrar los mensajes incluyendo el del usuario (SIN rerun)
    with chat_container:
        st.markdown(f"""
            <div style="text-align: right; margin-bottom: 12px;">
                <div style="
                    display: inline-block;
                    background: #e8f4f8;
                    padding: 12px 16px;
                    border-radius: 12px;
                    max-width: 70%;
                    text-align: left;
                ">
                    <p style="margin: 0; color: #333; font-size: 15px; line-height: 1.5;">
                        {user_input}
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Procesar con el agente
    with st.spinner("..."):
        try:
            result, st.session_state.chat_history = st.session_state.main_flow(
                query=user_input,
                chat_history=st.session_state.chat_history
            )
            
            # Agregar respuesta del agente al historial
            st.session_state.messages.append({
                "role": "assistant",
                "content": result['response'],
                "agent": result['agent_used'],
                "confidence": result['confidence']
            })
            
            # Mostrar la respuesta del agente con mejor formato
            with chat_container:
                # Formatear la respuesta para mejor legibilidad
                response_text = result['response']
                
                # Si contiene números al inicio (1., 2., 3.), agregar saltos de línea
                if any(response_text.startswith(f"{i}.") for i in range(1, 10)):
                    # Es una lista enumerada - formatear con saltos
                    lines = response_text.split("\n")
                    formatted_lines = []
                    for line in lines:
                        line = line.strip()
                        if line:
                            formatted_lines.append(line)
                    response_text = "<br>".join(formatted_lines)
                    html_response = f"<div style='line-height: 1.8;'>{response_text}</div>"
                else:
                    # Texto normal - mantener párrafos
                    html_response = f"<p style='line-height: 1.6; margin: 0;'>{response_text}</p>"
                
                st.markdown(f"""
                    <div style="text-align: left; margin-bottom: 12px;">
                        <div style="
                            display: inline-block;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 16px 18px;
                            border-radius: 12px;
                            max-width: 85%;
                            color: white;
                        ">
                            {html_response}
                            <p style="margin: 10px 0 0 0; font-size: 11px; opacity: 0.8;">
                                🤖 {result['agent_used'].upper()} | 📊 Confianza: {result['confidence']:.0%}
                            </p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Recargar SOLO para limpiar el input
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ═══════════════════════════════════════════════════════════════════
# 📚 FOOTER
# ═══════════════════════════════════════════════════════════════════
st.divider()

st.markdown("""
    <div style="text-align: center; color: #999; font-size: 12px; margin-top: 20px;">
        <p style="margin: 0; font-size: 11px;">
            🐾 VetCare AI | Sistema Multi-Agente | Potenciado por LangChain + GPT-4
        </p>
    </div>
""", unsafe_allow_html=True)
