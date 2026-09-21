import re
import string

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "which", "this", "that", "these", "those", "then", "just", "so", "than",
    "such", "both", "through", "about", "for", "is", "of", "while", "during",
    "to", "from", "in", "out", "on", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "can", "will",
    "just", "don", "should", "now", "it", "its", "by", "with", "at", "be",
    "are", "was", "were", "been", "being", "have", "has", "had", "having",
    "do", "does", "did", "doing"
}

def normalize_text(text: str) -> str:
    """Lowercase, strip punctuation and extra whitespace."""
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Remove punctuation
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse multiple whitespaces
    return re.sub(r"\s+", " ", text).strip()

def tokenize(text: str, remove_stopwords: bool = True) -> set[str]:
    """Tokenize normalized text into clean words, optionally removing stop words."""
    norm = normalize_text(text)
    words = [w for w in norm.split() if len(w) > 1]
    if remove_stopwords:
        return {w for w in words if w not in STOP_WORDS}
    return set(words)
