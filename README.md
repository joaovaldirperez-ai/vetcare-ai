# VetCare AI - Agente Conversacional para Clínica Veterinaria Virtual

## Descripción del Proyecto

VetCare AI es un sistema de agentes conversacionales basado en inteligencia artificial que actúa como primer punto de contacto para una clínica veterinaria virtual. El sistema combina recuperación de información con generación de lenguaje natural para proporcionar respuestas precisas sobre cuidado de mascotas, gestionar el agendamiento de citas de forma conversacional, y escalar automáticamente a agentes humanos cuando es necesario.

El proyecto utiliza una arquitectura multi-agente donde cada componente se especializa en una tarea específica. Esta separación de responsabilidades permite que el sistema sea modular, mantenible y fácil de extender con nuevas funcionalidades.

## Funcionalidades Principales

El sistema implementa tres capacidades principales que trabajan de forma integrada.

En primer lugar, cuenta con un agente RAG (Retrieval-Augmented Generation) que responde preguntas sobre cuidado de mascotas consultando una base de conocimientos documentada. Este agente utiliza embeddings vectoriales para encontrar información relevante y genera respuestas en lenguaje natural. Cuando no hay información disponible, comunica claramente esta limitación al usuario.

En segundo lugar, el sistema incluye un agente especializado en agendamiento de citas que recopila información de forma conversacional. Este agente solicita datos del dueño (nombre, teléfono, email), información de la mascota (nombre, especie, raza, edad), el motivo de la consulta, y coordina la disponibilidad de horarios mediante una herramienta que simula una API de consulta de disponibilidad.

Finalmente, el sistema implementa un mecanismo de escalación que detecta cuando el usuario necesita hablar con una persona. Reconoce múltiples frases y patrones que indican frustración o necesidad de atención humana, extrae información del contexto conversacional, y genera un ticket de soporte con los datos disponibles.

## Arquitectura del Sistema

El proyecto implementa una arquitectura basada en agentes especializados coordinados por un router central. Esta decisión arquitectónica se justifica por varios motivos. Primero, permite que cada agente se enfoque en una tarea específica, lo que simplifica el desarrollo y el mantenimiento del código. Segundo, facilita el testing de componentes individuales sin dependencias complejas. Tercero, permite agregar nuevos agentes sin modificar los existentes, siguiendo el principio abierto-cerrado.

El sistema consta de cuatro componentes principales. El router agent clasifica la intención del usuario basándose en el contenido de su mensaje y delega la conversación al agente más apropiado. El RAG agent utiliza búsqueda semántica para recuperar información de la base de conocimientos y genera respuestas fundamentadas. El booking agent gestiona todo el flujo conversacional de agendamiento, incluyendo recopilación de datos y verificación de disponibilidad. El greeting agent proporciona respuestas estándar para saludos y presentaciones iniciales.

La comunicación entre componentes se realiza a través de funciones simples que pasan el contexto conversacional y reciben respuestas del agente correspondiente. Cada agente mantiene su propio historial de mensajes durante la sesión del usuario, lo que permite conversaciones coherentes y contextualizadas.

## Instalación y Ejecución

### Requisitos Previos

El proyecto requiere Python 3.9 o superior instalado en su sistema. Se recomienda ampliamente usar un entorno virtual para aislar las dependencias del proyecto y evitar conflictos con otros proyectos Python. Además, necesitará una cuenta activa con acceso a la API de OpenAI y una clave de API válida.

### Pasos de Instalación

**Paso 1: Clonar el repositorio**

Abra una terminal en el directorio donde desee guardar el proyecto y ejecute:

```bash
git clone https://github.com/joaovaldirperez-ai/vetcare-ai.git
cd vetcare-ai
```

**Paso 2: Crear y activar un entorno virtual**

En Windows (PowerShell o CMD):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

En macOS o Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

**Paso 3: Instalar dependencias**

Una vez el entorno virtual esté activado, instale todas las dependencias necesarias:

```bash
pip install -r requirements.txt
```

**Paso 4: Configurar las variables de entorno**

Cree un archivo llamado `.env` en la raíz del proyecto (al mismo nivel que app.py). El archivo debe contener su clave de API de OpenAI:

```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Reemplace `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` con su clave real de OpenAI. Puede obtener su clave en https://platform.openai.com/account/api-keys.

**Importante**: El archivo `.env` nunca debe ser compartido o subido a un repositorio público. Está incluido en el `.gitignore` del proyecto para proteger sus credenciales.

### Ejecución de la Aplicación

Con el entorno virtual activado y las dependencias instaladas, ejecute:

```bash
streamlit run app.py
```

La aplicación abrirá automáticamente en su navegador en la dirección http://localhost:8501. Si no abre automáticamente, navegue manualmente a esa dirección.

### Uso del Sistema

Una vez que la aplicación esté ejecutándose, verá una interfaz de chat donde puede:

1. **Hacer preguntas sobre cuidado de mascotas**: Escriba cualquier pregunta sobre salud, nutrición, comportamiento o cuidados de mascotas. El sistema buscará información en su base de conocimientos y proporcionará respuestas detalladas.

2. **Agendar una cita**: Indique que desea agendar una cita veterinaria. El sistema iniciará un flujo conversacional que recopilará información sobre usted, su mascota, el motivo de la consulta y la disponibilidad de horarios.

3. **Solicitar atención humana**: En cualquier momento, puede indicar que desea hablar con un agente humano. El sistema reconocerá esta solicitud y creará un ticket de soporte con su información.

### Solución de Problemas

Si encuentra el error "ModuleNotFoundError" cuando ejecuta `streamlit run app.py`, verifique que:
- El entorno virtual está correctamente activado
- Todas las dependencias de requirements.txt fueron instaladas correctamente

Si recibe errores relacionados con OpenAI, verifique que:
- El archivo `.env` existe en la raíz del proyecto
- La variable `OPENAI_API_KEY` contiene una clave válida
- Su cuenta de OpenAI tiene acceso disponible y saldo suficiente

Si la aplicación no responde, asegúrese de tener una conexión a internet estable para comunicarse con la API de OpenAI.


## Uso del Sistema

El sistema se comunica con el usuario a través de una interfaz de chat en Streamlit. El usuario puede hacer preguntas sobre cuidado de mascotas, solicitar agendar una cita, o indicar que desea hablar con un agente humano.

Para consultas sobre cuidado de mascotas, simplemente escriba su pregunta. El sistema buscará información relevante en su base de conocimientos y proporcionará una respuesta fundamentada. Si no tiene información sobre el tema, lo comunicará claramente.

Para agendar una cita, indique su intención de hacerlo. El sistema iniciará una conversación estructurada donde solicitará información del dueño, datos de la mascota, el motivo de la consulta, y disponibilidad de horarios. El sistema verificará la disponibilidad del horario solicitado y, si está disponible, confirmará la cita con un resumen de toda la información.

Si en cualquier momento necesita hablar con una persona, puede indicarlo explícitamente. El sistema reconocerá su solicitud, recopilará la información disponible del contexto conversacional, y generará un ticket de soporte con sus datos.


## Decisiones Arquitectónicas y Justificación

El tamaño de los chunks en la segmentación de documentos se estableció en 3000 caracteres. Esta decisión se basa en que los conceptos principales de la base de conocimientos tienen alrededor de 2800 caracteres. Con este tamaño, cada concepto temático principal completo queda contenido en un único chunk, lo que permite que el modelo de lenguaje vea toda la información relacionada en una sola consulta sin fragmentación. Esto mejora significativamente la calidad de las respuestas.

Para la recuperación de documentos, se utiliza k=12, es decir, se recuperan 12 documentos por consulta. Este valor equilibra dos objetivos en conflicto: tener suficiente contexto para responder preguntas complejas y evitar incluir demasiado ruido que confunda al modelo. Valores menores pueden resultar en respuestas incompletas, mientras que valores mayores introducen información irrelevante que degrada la calidad.

El sistema utiliza FAISS como almacén vectorial. Esta decisión se justifica porque FAISS es una librería madura y eficiente que no requiere dependencias externas complejas como una base de datos separada. Para un prototipo y sistema de investigación, esto reduce la complejidad operacional significativamente.

Se eligió OpenAI gpt-4o-mini como modelo de lenguaje. Este modelo ofrece un buen balance entre capacidad y costo. Es suficientemente poderoso para manejar las tareas de clasificación, generación y razonamiento que requiere el sistema, pero mucho más económico que modelos más grandes. La temperatura se configuró a 0 para garantizar respuestas determinísticas y consistentes.

Se implementó un router agent en lugar de usar directamente LangGraph. Aunque LangGraph ofrece capacidades más avanzadas, para este proyecto resulta innecesariamente complejo. El router actual proporciona suficiente control de flujo, es más fácil de entender y mantener, y cumple todos los requisitos funcionales sin agregar capas de abstracción adicionales.


## Resultados de Validación

El sistema ha sido validado con una suite de pruebas exhaustivas que cubren todos los casos de uso principales. Se ejecutaron siete pruebas del agente RAG con diferentes tipos de consultas para verificar la calidad de las respuestas.

Las pruebas incluyeron consultas sobre conceptos específicos (obteniendo seis conceptos principales correctamente enumerados), preguntas sobre riesgos en la adopción de mascotas (cuatro riesgos identificados), consultas sobre temas no cubiertos por la base de conocimientos (respondiendo apropiadamente que no hay información disponible), preguntas complejas que generaron respuestas detalladas con más de once puntos, consultas sobre deberes de propietarios (seis deberes enumerados), y preguntas sobre prevención de incidentes (cinco recomendaciones). Todas las pruebas pasaron exitosamente, confirmando que el sistema opera correctamente.

El sistema también fue validado en el flujo completo de agendamiento, demostrando la capacidad de recopilar datos conversacionalmente, verificar disponibilidad, y generar confirmaciones completas. Se verificó el mecanismo de escalación confiriendo que el sistema detecta correctamente múltiples variaciones de solicitudes para hablar con humanos, extrae información del contexto, y genera tickets de soporte apropiadamente.



## Estructura del Proyecto

El código fuente se organiza en el directorio src con módulos separados para cada componente del sistema. El archivo main_flow.py contiene la orquestación principal y el router agent. El rag_agent.py implementa toda la lógica de recuperación y generación aumentada. El booking_agent.py maneja el flujo de agendamiento con sus herramientas asociadas. El router_agent.py realiza la clasificación de intenciones. El archivo config.py centraliza la configuración del sistema.

La base de conocimientos reside en el directorio data/info-mascotas con archivos de texto y markdown que contienen la información sobre cuidado de mascotas. El archivo app.py implementa la interfaz de usuario web usando Streamlit. Los archivos de configuración como requirements.txt especifican las dependencias Python necesarias.

## Tecnologías Utilizadas

El sistema está construido sobre LangChain como marco de trabajo para la orquestación de modelos de lenguaje. OpenAI proporciona los modelos de embeddings y generación de lenguaje. FAISS maneja el almacenamiento y búsqueda vectorial. LangChain-text-splitters proporciona la lógica de segmentación de documentos. Streamlit implementa la interfaz web de conversación. Python-dotenv gestiona las variables de entorno de forma segura.

## Requisitos Funcionales Cumplidos

El sistema implementa completamente todos los requisitos especificados en la documentación del proyecto. El agente RAG recupera y sintetiza información de documentos usando generación aumentada por recuperación. El agente de agendamiento recopila información del usuario de forma conversacional, verifica disponibilidad de horarios mediante herramientas simuladas, y genera confirmaciones estructuradas. El mecanismo de escalación detecta intenciones del usuario, extrae información del contexto conversacional, y crea tickets de soporte. El sistema mantiene coherencia conversacional a través de un historial de mensajes y permite múltiples turnos de conversación. El manejo de errores es robusto, con respuestas apropiadas cuando no hay información disponible o cuando algo falla.
