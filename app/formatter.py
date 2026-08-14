def format_response(answer: str, citation_url: str = "", last_updated: str = "") -> dict:
    """
    Formats the chatbot response into the standard structured API JSON schema.
    """
    return {
        "answer": answer.strip(),
        "citation_url": citation_url.strip() if citation_url else "",
        "last_updated": last_updated.strip() if last_updated else "",
        "disclaimer": "Facts-only. No investment advice."
    }
