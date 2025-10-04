import os
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_core.documents import Document
import google.generativeai as genai

# --- Configuration ---
VECTORSTORE_PATH = "./chroma_db"
TEXT_SPLITTER = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

# --- LAZY INITIALIZATION GLOBALS ---
# We use placeholders here. The actual objects will be created on demand.
_vectorstore = None
_embedding_model = None

def _initialize_rag():
    """
    This function will be called the first time a RAG component is needed.
    It ensures that the GOOGLE_API_KEY is available from the environment.
    """
    global _vectorstore, _embedding_model
    
    # Check if we've already initialized
    if _vectorstore and _embedding_model:
        return
        
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set. RAG system cannot initialize.")
    
    # Configure the base library (good practice for embeddings)
    genai.configure(api_key=api_key)
    
    print("Initializing RAG components (Embedding Model and Vector Store)...")
    _embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    if not os.path.exists(VECTORSTORE_PATH):
        print("Creating new vector store.")
    _vectorstore = Chroma(persist_directory=VECTORSTORE_PATH, embedding_function=_embedding_model)
    print("RAG components initialized.")

def get_vectorstore():
    """Initializes and returns the vector store, ensuring it's a singleton."""
    _initialize_rag()
    return _vectorstore

def add_resource_to_vectorstore(resource_id, title, content_path, resource_type, domain_names, age_cohort_names):
    """Loads, chunks, and embeds a resource, then adds it to the vector store."""
    print(f"Processing resource for vector store: {title}")
    
    docs = []
    if resource_type == 'PDF' and os.path.exists(content_path):
        loader = PyPDFLoader(content_path)
        docs = loader.load()
    elif resource_type == 'Web Link':
        loader = WebBaseLoader(content_path)
        docs = loader.load()
    elif resource_type == 'Text':
        docs = [Document(page_content=content_path)]
    
    if not docs:
        print(f"Could not load document for resource: {title}. Skipping vectorization."); return

    chunks = TEXT_SPLITTER.split_documents(docs)
    for chunk in chunks:
        chunk.metadata.update({
            "resource_id": str(resource_id), "title": title,
            "domains": ",".join(domain_names),
            "age_cohorts": ",".join(age_cohort_names)
        })
    vectorstore = get_vectorstore()
    vectorstore.add_documents(chunks)
    print(f"Successfully added {len(chunks)} chunks for resource '{title}' to vector store.")

def retrieve_relevant_context(query):
    """Queries the vector store to find relevant context."""
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={'k': 4})
    
    relevant_docs = retriever.invoke(query)
    
    context = "\n\n---\n\n".join([doc.page_content for doc in relevant_docs])
    sources = list(set([doc.metadata.get('title', 'Unknown Source') for doc in relevant_docs]))

    print(f"Retrieved {len(relevant_docs)} chunks from sources: {sources}")
    return context, sources