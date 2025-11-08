from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import json
import os
from pathlib import Path

# Initialize embeddings model
embeddings_model = OllamaEmbeddings(model="mxbai-embed-large")

# Vector store configuration
db_location = "./chroma_db"
collection_name = "drinkware_collection"

def initialize_vector_store():
    """Initialize and populate vector store from JSONL"""
    add_documents = not os.path.exists(db_location)
    
    # Create or load vector store
    vector_store = Chroma(
        collection_name=collection_name,
        persist_directory=db_location,
        embedding_function=embeddings_model
    )
    
    if add_documents:
        print("📚 Building drinkware vector store from JSONL...")
        jsonl_file = Path(__file__).parent / "data/products_drinkware.jsonl"
        
        if not jsonl_file.exists():
            print(f"⚠️  File not found: {jsonl_file}")
            return vector_store
        
        documents = []
        ids = []
        
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for index, line in enumerate(f):
                try:
                    product = json.loads(line)
                    
                    # Extract fields safely
                    name = str(product.get("name", ""))
                    description = str(product.get("description", ""))
                    capacity = str(product.get("capacity", "") or "")
                    price = str(product.get("price_min", ""))
                    
                    # Create document with product info
                    document = Document(
                        page_content=" ".join([name, description, capacity, price]).strip(),
                        metadata={
                            "name": name,
                            "price": price,
                            "capacity": capacity,
                            "url": product.get("url", ""),
                            "vendor": product.get("vendor", ""),
                            "product_type": product.get("product_type", ""),
                            "created_at": product.get("created_at", ""),
                        },
                        id=str(product.get("id", index))
                    )
                    
                    documents.append(document)
                    ids.append(str(product.get("id", index)))
                except json.JSONDecodeError as e:
                    print(f"⚠️  Error parsing line {index + 1}: {e}")
                    continue
        
        if documents:
            vector_store.add_documents(documents=documents, ids=ids)
            print(f"✅ Added {len(documents)} drinkware products to vector store")
        else:
            print("⚠️  No documents added to vector store")
    else:
        print("✅ Using existing vector store")
    
    return vector_store

# Initialize on module load
vector_store = initialize_vector_store()

# Create retriever
retriever = vector_store.as_retriever(
    search_kwargs={"k": 10},
)

