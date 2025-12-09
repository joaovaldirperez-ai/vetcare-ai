import os
from pathlib import Path

from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)
# Loaders
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader   # ← EL BUENO para tu caso
)

# LLM + embeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Vector store
from langchain_community.vectorstores import FAISS

# Prompting
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document


BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "data" / "info-mascotas"


# =======================================================
# 🔥 CARGA DOCUMENTOS (TXT, MD, PDF normal)
# =======================================================
def load_documents():
    docs = []

    print("[INFO] Loading documents...\n")

    for file in DOCS_DIR.glob("**/*"):
        print(f"Found: {file.name}")

        # TXT
        if file.suffix.lower() == ".txt":
            loaded = TextLoader(str(file), encoding="utf-8").load()
            loaded = [d for d in loaded if d.page_content.strip() != ""]
            print(f"    TXT loaded: {len(loaded)} chunks")
            docs.extend(loaded)

        # MD
        elif file.suffix.lower() == ".md":
            text = file.read_text(encoding="utf-8")
            if text.strip() != "":
                docs.append(Document(page_content=text, metadata={"source": file.name}))
                print("    MD loaded: 1 chunk")

        # PDF (PyPDFLoader)
        elif file.suffix.lower() == ".pdf":
            loader = PyPDFLoader(str(file))
            pages = loader.load()
            pages = [p for p in pages if p.page_content.strip() != ""]
            print(f"    PDF loaded: {len(pages)} pages")
            docs.extend(pages)

    print(f"\n[SUCCESS] Total documents: {len(docs)}\n")

    if not docs:
        raise ValueError("No se cargaron documentos con texto.")

    return docs


# =======================================================
# 🔥 CREAR VECTORSTORE (FAISS)
# =======================================================
def create_vectorstore():
    docs = load_documents()

    # Aumentar chunk_size para que quepan todos los conceptos principales juntos
    splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    vectordb = FAISS.from_documents(chunks, embedding=embeddings)
    return vectordb


# =======================================================
# 🔥 CONSTRUIR PIPELINE RAG
# =======================================================
def build_rag():
    vectordb = create_vectorstore()
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Eres VetCare AI, un asistente veterinario. Tu único trabajo es responder preguntas\n"
         "usando ÚNICAMENTE la información del contexto que se te proporciona.\n\n"
         "REGLAS IMPORTANTES:\n"
         "1. Responde SOLO con información del contexto proporcionado\n"
         "2. Si la pregunta pide enumerar (conceptos, deberes, riesgos, etc.), ENUMERA TODOS los que encuentres\n"
         "3. Usa formato claro con saltos de línea para listas\n"
         "4. Si NO encuentras información relevante, responde: 'Lo siento, no tengo información sobre ese tema específico en mi base de conocimientos.'\n"
         "5. Sé preciso y literal - no inventes información\n\n"
         "Contexto disponible:\n{context}"),
        ("human", "{question}")
    ])

    rag_chain = prompt | llm
    
    def run_rag(question):
        """Ejecuta el RAG: busca contexto relevante y genera respuesta"""
        # Buscar documentos relevantes (aumentar k para mejor cobertura)
        docs = vectordb.similarity_search(question, k=12)
        
        # Combinar contexto
        context = "\n\n---\n\n".join(doc.page_content for doc in docs)
        
        # Generar respuesta
        response = rag_chain.invoke({
            "context": context,
            "question": question
        })
        
        return response
    
    return run_rag


# =======================================================
# 🔥 CLI
# =======================================================
def main():
    rag, retriever = build_rag()

    print("\n=== VetCare AI RAG ===")

    while True:
        q = input("\nTú: ")
        if q.lower() in ["salir", "exit"]:
            break

        ans = rag.invoke(q)

        print("\n📌 Respuesta:")
        print(ans.content)

        ctx = retriever.invoke(q)
        print("\n📚 Fragmentos usados:")
        for d in ctx:
            print("-", d.page_content[:200], "...")


if __name__ == "__main__":
    main()