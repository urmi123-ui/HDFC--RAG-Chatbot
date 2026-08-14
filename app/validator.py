import re

def count_sentences(text: str) -> int:
    """
    Splits text into sentences by looking for sentence-ending punctuation.
    Avoids splitting on common abbreviations like 'Rs.', 'Min.', 'Mr.', 'Dr.'.
    """
    # Replace common abbreviations
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
        
    # Split by '.', '!', or '?' followed by spaces or string end
    sentences = re.split(r'[.!?]+(?:\s+|$)', cleaned.strip())
    sentences = [s for s in sentences if s.strip()]
    return len(sentences)

def has_advisory_language(text: str) -> bool:
    """
    Checks if the generated response contains financial advice or recommendation language.
    """
    text_lower = text.lower()
    
    # Strictly prohibited advisory phrases/patterns
    advisory_patterns = [
        r"should\s+(invest|buy|sell|hold)",
        r"i\s+(recommend|suggest|advise)",
        r"(good|better|best)\s+to\s+(invest|buy)",
        r"recommend\s+you\s+to",
        r"investment\s+advice",
        r"you\s+should\s+choose",
        r"highly\s+recommended",
    ]
    
    for pattern in advisory_patterns:
        if re.search(pattern, text_lower):
            return True
            
    return False

def validate_response(answer: str) -> tuple[bool, str]:
    """
    Validates that the generated answer is compliant:
    1. It is <= 3 sentences.
    2. It does not contain advisory language.
    
    Returns (is_valid, error_message).
    """
    # 1. Check sentence count
    num_sentences = count_sentences(answer)
    if num_sentences > 3:
        return False, f"Response exceeds 3 sentences (found {num_sentences} sentences)."
        
    # 2. Check advisory language
    if has_advisory_language(answer):
        return False, "Response contains non-factual or advisory language."
        
    return True, ""
