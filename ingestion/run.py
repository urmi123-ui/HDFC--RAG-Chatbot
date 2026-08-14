import sys
import os

# Add parent dir to path so we can import from ingestion
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from ingestion.fetch import fetch_all
from ingestion.parse import parse_all
from ingestion.chunk import chunk_all
from ingestion.index import index_all

def clear_directory(dir_path):
    if os.path.exists(dir_path):
        import glob
        import shutil
        for name in os.listdir(dir_path):
            path = os.path.join(dir_path, name)
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)

def main():
    print("--- Starting Phase 2 Offline Ingestion Pipeline ---")
    
    raw_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    processed_dir = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
    index_dir = os.path.join(os.path.dirname(__file__), "..", "data", "index")
    
    print("\nCleaning old data directories...")
    clear_directory(raw_dir)
    clear_directory(processed_dir)
    clear_directory(index_dir)
    
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(index_dir, exist_ok=True)
    
    print("\n[1/4] Fetching HTML from URLs...")
    fetch_all()
    
    print("\n[2/4] Parsing HTML into sections...")
    parse_all()
    
    print("\n[3/4] Chunking sections...")
    chunk_all()
    
    print("\n[4/4] Indexing chunks into ChromaDB with BGE-small...")
    index_all()
    
    print("\n--- Pipeline Complete ---")

if __name__ == "__main__":
    main()
