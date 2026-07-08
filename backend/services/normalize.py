import re

GPU_SERIES_RE = re.compile(r"\b(?P<series>rtx|gtx|rx|arc)\s*(?P<model>\d{3,4})\b")
GPU_MEMORY_RE = re.compile(r"\b(?P<memory>\d+)\s*gb\b")
GPU_MEMORY_COMPACT_RE = re.compile(r"\b(?P<memory>\d+)gb\b")

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
    return build_product_profile(name)["match_key"]


def _normalize_text(name: str) -> str:
    text = name.lower()
    text = re.sub(r"[^a-z0-9+\s-]", " ", text)
    text = re.sub(r"\b(\d{3,4})(ti)\b", r"\1 \2", text)
    text = re.sub(r"\bfe\b", " founders edition ", text)
    text = re.sub(r"\bfounders?\s+editions?\b", " founders edition ", text)
    text = re.sub(r"\b(\d+)\s*gb\b", r"\1gb", text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_gpu_attributes(text: str, tokens: list[str]) -> dict:
    token_set = set(tokens)
    series_match = GPU_SERIES_RE.search(text)

    if not series_match:
        return {}

    series = series_match.group("series")
    model = series_match.group("model")
    memory_match = GPU_MEMORY_COMPACT_RE.search(text) or GPU_MEMORY_RE.search(text)
    memory = f"{memory_match.group('memory')}gb" if memory_match else None

    variant = None
    if "ti" in token_set and "super" in token_set:
        variant = "ti super"
    elif "super" in token_set:
        variant = "super"
    elif "ti" in token_set:
        variant = "ti"

    edition = None
    if "founders" in token_set and "edition" in token_set:
        edition = "founders edition"

    brand = None
    if "nvidia" in token_set or "geforce" in token_set or series in {"rtx", "gtx"}:
        brand = "nvidia"
    elif series == "rx":
        brand = "amd"
    elif series == "arc":
        brand = "intel"

    attributes = {
        "product_type": "gpu",
        "brand": brand,
        "series": series,
        "model": model,
        "variant": variant,
        "edition": edition,
        "memory": memory,
    }

    attributes["normalized_name"] = " ".join(
        part
        for part in [
            brand,
            series,
            model,
            variant,
            edition,
            memory,
        ]
        if part
    )
    attributes["match_key"] = "|".join(
        f"{key}:{value}"
        for key, value in [
            ("product_type", attributes["product_type"]),
            ("brand", attributes["brand"]),
            ("series", attributes["series"]),
            ("model", attributes["model"]),
            ("variant", attributes["variant"]),
            ("edition", attributes["edition"]),
            ("memory", attributes["memory"]),
        ]
        if value
    )
    return attributes


def build_product_profile(name: str) -> dict:
    text = _normalize_text(name)
    tokens = text.replace("-", " ").split()
    gpu_attributes = _extract_gpu_attributes(text, tokens)
    if gpu_attributes:
        return gpu_attributes

    words = [w for w in tokens if w not in STOP_WORDS]
    normalized_name = " ".join(words)
    return {
        "product_type": "generic",
        "normalized_name": normalized_name,
        "match_key": normalized_name,
        "brand": None,
        "series": None,
        "model": None,
        "variant": None,
        "edition": None,
        "memory": None,
    }


def build_market_search_query(profile: dict, fallback_name: str) -> str:
    if profile.get("product_type") != "gpu":
        return profile.get("normalized_name") or fallback_name

    return " ".join(
        part
        for part in [
            profile.get("series", "").upper(),
            profile.get("model"),
            profile.get("variant"),
            profile.get("edition"),
            profile.get("memory", "").upper(),
        ]
        if part
    )


def products_are_comparable(target: dict, candidate: dict) -> bool:
    if target.get("product_type") != candidate.get("product_type"):
        return False

    if target.get("product_type") != "gpu":
        return target.get("match_key") == candidate.get("match_key")

    for field in ("brand", "series", "model"):
        target_value = target.get(field)
        candidate_value = candidate.get(field)
        if target_value and not candidate_value:
            return False
        if target_value and candidate_value and target_value != candidate_value:
            return False

    target_memory = target.get("memory")
    candidate_memory = candidate.get("memory")
    if target_memory and candidate_memory and target_memory != candidate_memory:
        return False

    target_variant = target.get("variant")
    candidate_variant = candidate.get("variant")
    if target_variant or candidate_variant:
        if not target_variant or not candidate_variant:
            return False
        if candidate_variant != target_variant:
            return False

    target_edition = target.get("edition")
    candidate_edition = candidate.get("edition")
    if target_edition or candidate_edition:
        if not target_edition or not candidate_edition:
            return False
        if candidate_edition != target_edition:
            return False

    return True
