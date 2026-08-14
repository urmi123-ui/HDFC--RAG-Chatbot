import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.classifier import classify_query
from app.retriever import resolve_scheme, retrieve_chunks
from app.validator import validate_response, count_sentences
from app.formatter import format_response
from app.generator import (
    generate_answer,
    REFUSAL_ADVISORY,
    REFUSAL_ADVISORY_LINK,
    REFUSAL_PERFORMANCE,
    REFUSAL_PERFORMANCE_LINK
)

app = FastAPI(title="Mutual Fund FAQ Assistant API")

# Enable CORS for UI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

def clean_sentence_count(text: str) -> str:
    """
    Safely truncates text to the first 3 sentences if the model over-generates.
    """
    # Replace common abbreviations to avoid splitting errors
    cleaned = text
    abbreviations = {
        "Rs.": "Rs",
        "Min.": "Min",
        "Mr.": "Mr",
        "Dr.": "Dr",
        "i.e.": "ie",
        "e.g.": "eg"
    }
    for abb, repl in abbreviations.items():
        cleaned = cleaned.replace(abb, repl)
        
    # Split text on punctuation followed by space or string end
    sentences = re.split(r'[.!?]+(?:\s+|$)', cleaned.strip())
    sentences = [s for s in sentences if s.strip()]
    
    if len(sentences) <= 3:
        return text
        
    # Locate index of third sentence end to keep original punctuation
    count = 0
    idx = 0
    for m in re.finditer(r'[.!?]+(?:\s+|$)', text):
        count += 1
        if count == 3:
            idx = m.end()
            break
            
    if idx > 0:
        return text[:idx].strip()
        
    return ". ".join(sentences[:3]) + "."

@app.post("/api/chat")
async def chat(payload: ChatRequest):
    query = payload.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query message cannot be empty.")
        
    # 1. Intent Classification & Routing
    category = classify_query(query)
    
    if category == "advisory":
        return format_response(
            answer=REFUSAL_ADVISORY,
            citation_url=REFUSAL_ADVISORY_LINK,
            last_updated=""
        )
        
    if category == "performance":
        return format_response(
            answer=REFUSAL_PERFORMANCE,
            citation_url=REFUSAL_PERFORMANCE_LINK,
            last_updated=""
        )
        
    # 2. Scheme & Vector Chunk Retrieval (Factual Query)
    scheme = resolve_scheme(query)
    chunks = retrieve_chunks(query, top_k=3)
    
    if not chunks:
        # Fallback if no relevant database chunks are returned
        fallback_answer = "I do not have that information based on the official documents."
        citation = scheme["url"] if scheme else ""
        return format_response(
            answer=fallback_answer,
            citation_url=citation,
            last_updated=""
        )
        
    # 3. Answer Generation (Iterative Validation)
    answer = ""
    attempts = 2
    for attempt in range(attempts):
        try:
            answer = generate_answer(query, chunks)
            is_valid, err = validate_response(answer)
            if is_valid:
                break
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Groq generation failed: {str(e)}")
            
    # 4. Sentence Truncation Guardrail
    if count_sentences(answer) > 3:
        answer = clean_sentence_count(answer)
        
    # 5. Metadata Processing & Formatted Response
    top_chunk = chunks[0]
    citation = top_chunk["metadata"].get("source_url", "")
    last_updated = top_chunk["metadata"].get("last_updated", "")
    
    # Prefer resolved scheme URL config mapping
    if scheme:
        citation = scheme["url"]
        
    return format_response(
        answer=answer,
        citation_url=citation,
        last_updated=last_updated
    )

# Mount the static files UI directory at root '/'
ui_dir = os.path.join(os.path.dirname(__file__), "..", "ui")
if not os.path.exists(ui_dir):
    os.makedirs(ui_dir)
app.mount("/", StaticFiles(directory=ui_dir, html=True), name="ui")
