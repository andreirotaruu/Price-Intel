import re

STOP_WORDS = {
    "nvidia",
    "geforce",
    "graphics",
    "graphic",
    "card",
    "used",
    "new",
    "excellent",
    "condition",
    "tested",
    "working",
    "gddr6",
    "gddr6x",
    "with",
    "and",
    "for",
    "the",
}

def normalize_name(name: str) -> str:
    text = name.lower()

    # Remove punctuation
    text = re.sub(r"[^a-z0-9+\s-]", " ", text)

    # Normalize common abbreviations
    text = re.sub(r"\bfe\b", " founders edition ", text)
    text = re.sub(r"\bfounders?\s+editions?\b", " founders edition ", text)

    # Normalize "12 GB" -> "12gb"
    text = re.sub(r"\b(\d+)\s*gb\b", r"\1gb", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    tokens = text.replace("-", " ").split()
    token_set = set(tokens)

    parts = []

    # GPU model
    gpu = re.search(r"\brtx\s*(\d{4})\b", text)
    if gpu:
        parts.extend(["rtx", gpu.group(1)])

    # Variant
    if "ti" in token_set:
        parts.append("ti")

    if "super" in token_set:
        parts.append("super")

    # Memory
    memory = re.search(r"\b(\d+)gb\b", text)
    if memory:
        parts.append(f"{memory.group(1)}gb")

    # Edition
    if "founders" in token_set and "edition" in token_set:
        parts.extend(["founders", "edition"])

    # If we identified a GPU, use the structured name
    if parts:
        return " ".join(parts)

    # Generic fallback
    words = [w for w in tokens if w not in STOP_WORDS]

    return " ".join(words)
