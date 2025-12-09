import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Cargar variables desde .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Falta OPENAI_API_KEY en el archivo .env")

def get_llm(model: str = "gpt-4.1-mini", temperature: float = 0.2):
    """
    Retorna un modelo LLM de OpenAI para toda la app.
    """
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=OPENAI_API_KEY,
    )

def get_embeddings():
    """
    Retorna el modelo de embeddings para el RAG.
    """
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=OPENAI_API_KEY,
    )
