import os
import yaml
import chromadb
from chromadb.utils import embedding_functions

# Load corpus config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "corpus.yaml")
INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "index")

def load_schemes():
    if not os.path.exists(CONFIG_PATH):
        return []
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config.get("schemes", [])

SCHEMES = load_schemes()

def resolve_scheme(query: str) -> dict:
    """
    Tries to map a user query to one of the 12 schemes defined in corpus.yaml.
    """
    query_clean = query.lower()
    
    # Specific keywords mapping for each scheme slug
    scheme_keywords = {
        "hdfc-pharma-and-healthcare-fund-direct-growth": ["pharma", "healthcare"],
        "hdfc-nifty-50-index-fund-direct-growth": ["nifty 50", "nifty50", "nifty"],
        "hdfc-balanced-advantage-fund-direct-growth": ["balanced advantage", "baf", "balanced"],
        "hdfc-gold-etf-fund-of-fund-direct-plan-growth": ["gold"],
        "hdfc-small-cap-fund-direct-growth": ["small cap", "smallcap"],
        "hdfc-defence-fund-direct-growth": ["defence", "defense"],
        "hdfc-mid-cap-fund-direct-growth": ["mid cap", "midcap"],
        "hdfc-silver-etf-fof-direct-growth": ["silver"],
        "hdfc-short-term-opportunities-fund-direct-growth": ["short term", "shortterm", "opportunities"],
        "hdfc-focused-fund-direct-growth": ["focused"],
        "hdfc-multi-cap-fund-direct-growth": ["multi cap", "multicap"],
        "hdfc-equity-fund-direct-growth": ["equity fund", "equity"]
    }
    
    # Iterate and look for matched keyword
    for slug, keywords in scheme_keywords.items():
        for kw in keywords:
            if kw in query_clean:
                for s in SCHEMES:
                    if s["slug"] == slug:
                        return s
                        
    # General fallback matching of slug or name parts
    for s in SCHEMES:
        name_clean = s["name"].lower()
        slug_clean = s["slug"].lower()
        if slug_clean in query_clean or name_clean in query_clean:
            return s
            
    return None

def detect_section_intent(query: str) -> str:
    """
    Identifies target section intent in query.
    """
    query_clean = query.lower()
    
    intents = {
        "expense_ratio": ["expense", "ratio", "fee", "cost"],
        "exit_load": ["exit", "load", "redeem", "redemption"],
        "minimum_investment": ["minimum", "sip", "lumpsum", "invest", "limit"],
        "benchmark": ["benchmark", "index"],
        "fund_management": ["manager", "management", "managed by", "education", "experience", "bio"],
        "tax": ["tax", "taxation", "stcg", "ltcg"],
        "investment_objective": ["objective", "goal"],
        "fund_house": ["fund house", "amc", "mutual fund house"]
    }
    
    for section, keywords in intents.items():
        if any(kw in query_clean for kw in keywords):
            return section
            
    return None

def retrieve_chunks(query: str, top_k: int = 3) -> list:
    """
    Queries ChromaDB to retrieve relevant chunks.
    Uses metadata filtering if a scheme is resolved in the query.
    """
    if not os.path.exists(INDEX_DIR):
        return []
        
    client = chromadb.PersistentClient(path=INDEX_DIR)
    
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-small-en-v1.5"
    )
    
    collection = client.get_or_create_collection(
        name="mutual_funds_faq",
        embedding_function=emb_fn
    )
    
    scheme = resolve_scheme(query)
    section = detect_section_intent(query)
    
    where_filter = {}
    if scheme:
        where_filter["slug"] = scheme["slug"]
        
    # Query Chroma
    # If a filter is specified, apply it
    kwargs = {}
    if where_filter:
        kwargs["where"] = where_filter
        
    results = collection.query(
        query_texts=[query],
        n_results=6 if scheme else 5, # broader search to capture all candidate sections
        **kwargs
    )
    
    # Process results into structured list of chunk dicts
    chunks = []
    if results and results.get("documents"):
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        ids = results["ids"][0]
        distances = results.get("distances", [[0]*len(ids)])[0]
        
        for doc, meta, cid, dist in zip(documents, metadatas, ids, distances):
            chunks.append({
                "id": cid,
                "text": doc,
                "metadata": meta,
                "distance": dist
            })
            
    # Boost chunks that match the section intent if detected
    if section:
        # Sort chunks prioritizing those where metadata section matches intent
        chunks.sort(key=lambda x: 0 if x["metadata"].get("section") == section else 1)
        
    return chunks
