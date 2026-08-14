import os
import yaml
import time
import urllib.request
import urllib.error

def fetch_all():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "corpus.yaml")
    raw_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    schemes = config.get("schemes", [])
    timestamp = int(time.time())
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    fetched_files = []
    
    for scheme in schemes:
        url = scheme.get("url")
        slug = scheme.get("slug")
        print(f"Fetching {slug}...")
        
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
            filename = f"{slug}_{timestamp}.html"
            filepath = os.path.join(raw_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as out:
                out.write(html)
                
            fetched_files.append((slug, filepath))
            print(f"Saved to {filepath}")
            
        except urllib.error.URLError as e:
            print(f"Failed to fetch {url}: {e}")
            
        time.sleep(2) # Polite rate limiting
        
    return fetched_files

if __name__ == "__main__":
    fetch_all()
