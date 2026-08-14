import re

def classify_query(query: str) -> str:
    """
    Classifies a user query into one of three categories:
    - 'advisory': If the user is asking for investment advice, recommendations, or comparisons.
    - 'performance': If the user is asking for performance metrics, historical returns, or calculations.
    - 'factual': If the user is asking for objective, verifiable facts.
    """
    query_clean = query.lower().strip()
    
    # Advisory patterns
    advisory_keywords = [
        r"should\s+i\s+(invest|buy|sell|hold)",
        r"is\s+(it|this)\s+(good|better|safe|bad|worth)",
        r"which\s+(fund|scheme|one)\s+is\s+(better|best|recommended)",
        r"recommend\s+a\s+fund",
        r"suggest\s+a\s+fund",
        r"investment\s+advice",
        r"best\s+mutual\s+fund",
        r"which\s+one\s+should\s+i",
        r"advisable",
        r"opinion\s+on",
        r"compare\s+and\s+tell\s+me\s+which",
    ]
    
    for pattern in advisory_keywords:
        if re.search(pattern, query_clean):
            return "advisory"
            
    # Performance patterns
    performance_keywords = [
        r"return(s)?",
        r"perform",
        r"yield",
        r"cagr",
        r"annualized",
        r"historical\s+gain(s)?",
        r"profit(s)?",
        r"growth\s+rate",
        r"how\s+much\s+did\s+it\s+grow",
        r"return\s+comparison",
    ]
    
    for pattern in performance_keywords:
        if re.search(pattern, query_clean):
            return "performance"
            
    return "factual"
