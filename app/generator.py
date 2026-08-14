import os
from groq import Groq

# Custom env loader
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

load_env()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL_NAME = "llama-3.3-70b-versatile"

# Prohibited advisory response templates
REFUSAL_ADVISORY = (
    "I am a facts-only FAQ assistant and cannot provide investment advice, comparisons, or recommendations. "
    "For official guidelines and educational resources, please refer to the AMFI Investor Education portal."
)
REFUSAL_ADVISORY_LINK = "https://www.amfiindia.com/investor-corner"

REFUSAL_PERFORMANCE = (
    "I can only provide static scheme information and do not perform return comparisons or return projections. "
    "Please refer to the official HDFC Mutual Fund factsheets for verified performance data."
)
REFUSAL_PERFORMANCE_LINK = "https://www.hdfcfund.com/downloads/factsheets"

def get_groq_client():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in the environment or .env file.")
    return Groq(api_key=GROQ_API_KEY)

def generate_answer(query: str, chunks: list) -> str:
    """
    Calls the Groq API using Llama 3.3 70B to generate a factual, 3-sentence grounded answer.
    """
    client = get_groq_client()
    
    # Construct context from retrieved chunks
    context_texts = []
    for c in chunks:
        sec = c["metadata"].get("section", "general")
        context_texts.append(f"[{sec.upper()}] (Source: {c['metadata'].get('scheme_name')}):\n{c['text']}")
        
    context_payload = "\n\n".join(context_texts)
    
    system_prompt = (
        "You are a strict facts-only assistant for HDFC Mutual Fund schemes.\n"
        "Your task is to answer the user's query using ONLY the provided Context below.\n"
        "Follow these rules precisely:\n"
        "1. Keep your answer strictly under or equal to 3 sentences.\n"
        "2. Do not offer any investment recommendations, opinions, or advice (e.g. do not say 'it is a good choice' or 'you should buy').\n"
        "3. Do not perform return projections or return comparison calculations.\n"
        "4. Base your answers ONLY on the objective facts provided in the Context. If the context is insufficient, state: "
        "'I do not have that information based on the official documents.'\n"
        "5. Do not include any HTML links, markdown links, or external URLs in your answer body."
    )
    
    user_prompt = f"Context:\n{context_payload}\n\nQuery: {query}"
    
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0, # Deterministic factual answers
        max_tokens=250
    )
    
    return completion.choices[0].message.content.strip()
