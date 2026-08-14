import os
import glob
import json

def get_config():
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "corpus.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def naive_chunk_text(text, max_chars=1000, overlap=200):
    """Simple character-based chunking with overlap (approx 200 tokens)."""
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        
        # Try to find a space or punctuation to break at
        if end < len(text):
            for break_char in ['. ', ' ', '\n']:
                last_break = text.rfind(break_char, start, end)
                if last_break != -1 and last_break > start + max_chars // 2:
                    end = last_break + len(break_char)
                    break
                    
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = end - overlap
        
    return chunks

def chunk_all():
    processed_dir = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
    json_files = glob.glob(os.path.join(processed_dir, "*.json"))
    # filter out all_chunks.json if it exists
    json_files = [f for f in json_files if not f.endswith("all_chunks.json")]
    
    config = get_config()
    scheme_map = {s['slug']: s for s in config.get('schemes', [])}
    
    all_chunks = []
    
    for filepath in json_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        slug = data.get("slug")
        timestamp = data.get("timestamp")
        sections = data.get("sections", {})
        
        scheme_info = scheme_map.get(slug, {})
        scheme_name = scheme_info.get("name", slug)
        source_url = scheme_info.get("url", "")
        
        for sec_name, sec_content in sections.items():
            if not sec_content:
                continue
                
            text_chunks = naive_chunk_text(sec_content)
            
            for i, text in enumerate(text_chunks):
                enriched_text = f"Scheme: {scheme_name}\nSection: {sec_name}\n{text}"
                chunk_record = {
                    "id": f"{slug}#{sec_name}#{i}",
                    "text": enriched_text,
                    "metadata": {
                        "slug": slug,
                        "scheme_name": scheme_name,
                        "source_url": source_url,
                        "section": sec_name,
                        "last_updated": timestamp
                    }
                }
                all_chunks.append(chunk_record)
                
    # Save all chunks to a single JSON for indexing
    chunks_filepath = os.path.join(processed_dir, "all_chunks.json")
    with open(chunks_filepath, "w", encoding="utf-8") as out:
        json.dump(all_chunks, out, indent=2, ensure_ascii=False)
        
    print(f"Created {len(all_chunks)} chunks and saved to {chunks_filepath}")

if __name__ == "__main__":
    chunk_all()
