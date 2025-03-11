import os
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

# Load environment variables if required
load_dotenv()

# Define the ChromaDB directory path
CHROMA_DB_PATH = "db/vstore"  # Change this to your actual path

# Initialize embeddings model
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# Load the existing vector store
vector_store = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embeddings)

# Fetch all stored documents
docs = vector_store.get()
if not docs["documents"]:
    print("No documents found in the ChromaDB.")
else:
    print(f"Found {len(docs['documents'])} documents in the ChromaDB:\n")
    for i, content in enumerate(docs["documents"]):
        print(f"Document {i+1}:")
        print(f"Content: {content}")
        print(f"Metadata: {docs['metadatas'][i]}")
        print("-" * 80)
