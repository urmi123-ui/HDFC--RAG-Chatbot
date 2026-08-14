import os
import json
import chromadb
from chromadb.utils import embedding_functions

def index_all():
    processed_dir = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
    index_dir = os.path.join(os.path.dirname(__file__), "..", "data", "index")
    
    chunks_filepath = os.path.join(processed_dir, "all_chunks.json")
    if not os.path.exists(chunks_filepath):
        print("No chunks found to index.")
        return
        
    with open(chunks_filepath, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
        
    print(f"Loaded {len(chunks)} chunks for indexing.")
    
    # Initialize ChromaDB with persistent storage
    client = chromadb.PersistentClient(path=index_dir)
    
    # Use BGE-small-en-v1.5
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-small-en-v1.5"
    )
    
    # Create or get collection
    collection = client.get_or_create_collection(
        name="mutual_funds_faq",
        embedding_function=emb_fn
    )
    
    # Prepare data for Chroma
    ids = []
    documents = []
    metadatas = []
    
    for chunk in chunks:
        ids.append(chunk["id"])
        documents.append(chunk["text"])
        metadatas.append(chunk["metadata"])
        
    # Upsert in batches
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        print(f"Upserting batch {i} to {end}...")
        collection.upsert(
            ids=ids[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end]
        )
        
    print("Indexing complete in ChromaDB.")

if __name__ == "__main__":
    index_all()
