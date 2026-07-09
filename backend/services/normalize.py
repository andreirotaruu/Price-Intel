import re

GPU_SERIES_RE = re.compile(r"\b(?P<series>rtx|gtx|rx|arc)\s*(?P<model>\d{3,4})\b")
GPU_MEMORY_RE = re.compile(r"\b(?P<memory>\d+)\s*gb\b")
GPU_MEMORY_COMPACT_RE = re.compile(r"\b(?P<memory>\d+)gb\b")
ACCESSORY_PATTERNS = (
    re.compile(
        r"\b(cooler|heatsink|heat sink|fan|shroud|backplate|water ?block|box|packaging|manual|cable|adapter|bracket)\s+only\b"
    ),
    re.compile(r"\b(empty box|for parts|parts only|not working)\b"),
    re.compile(
        r"\b(case|cover|screen protector|charger|cooler|heatsink|water ?block|replacement fan)\s+for\b"
    ),
)

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
    "free",
    "shipping",
    "only",
}
IDENTIFIER_FIELDS = ("epid", "gtin", "mpn")
STRICT_ASPECT_NAMES = {
    "model",
    "storage capacity",
    "memory",
    "ram size",
    "screen size",
    "processor model",
}
INVALID_IDENTIFIERS = {"", "n/a", "na", "none", "unknown", "does not apply"}

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


def _is_accessory_or_parts(text: str) -> bool:
    return any(pattern.search(text) for pattern in ACCESSORY_PATTERNS)


def _meaningful_tokens(tokens: list[str]) -> list[str]:
    return list(
        dict.fromkeys(
            token for token in tokens if token not in STOP_WORDS and len(token) > 1
        )
    )


def token_similarity_score(target: dict, candidate: dict) -> float:
    target_tokens = set(target.get("title_tokens") or [])
    candidate_tokens = set(candidate.get("title_tokens") or [])
    if not target_tokens or not candidate_tokens:
        return 0.0

    intersection = len(target_tokens & candidate_tokens)
    union = len(target_tokens | candidate_tokens)
    smaller = min(len(target_tokens), len(candidate_tokens))
    jaccard = intersection / union
    containment = intersection / smaller
    return round((jaccard * 0.6) + (containment * 0.4), 3)


def enrich_product_profile(profile: dict, item: dict | None) -> dict:
    if not item:
        return profile

    enriched = dict(profile)
    product = item.get("product") or {}
    category_ids = list(item.get("leafCategoryIds") or [])
    if item.get("categoryId"):
        category_ids.append(item["categoryId"])
    if not category_ids:
        category_ids = [
            category.get("categoryId")
            for category in item.get("categories", [])
            if category.get("categoryId")
        ][-1:]

    aspects = {}
    for aspect in item.get("localizedAspects", []):
        name = str(aspect.get("name") or aspect.get("localizedName") or "").lower()
        values = aspect.get("value") or aspect.get("localizedValues") or []
        if isinstance(values, str):
            values = [values]
        if name:
            aspects[name] = {_normalize_text(str(value)) for value in values}
    for group in product.get("aspectGroups") or []:
        for aspect in group.get("aspects") or []:
            name = str(aspect.get("localizedName") or "").lower()
            values = aspect.get("localizedValues") or []
            if name:
                aspects.setdefault(name, set()).update(
                    _normalize_text(str(value)) for value in values
                )

    identifiers = {
        "epid": {
            str(value).lower()
            for value in (item.get("epid"), item.get("inferredEpid"))
            if value and str(value).lower() not in INVALID_IDENTIFIERS
        },
        "gtin": {
            str(value).lower()
            for value in ([item.get("gtin")] + list(product.get("gtins") or []))
            if value and str(value).lower() not in INVALID_IDENTIFIERS
        },
        "mpn": {
            str(value).lower()
            for value in ([item.get("mpn")] + list(product.get("mpns") or []))
            if value and str(value).lower() not in INVALID_IDENTIFIERS
        },
    }

    condition = str(item.get("condition") or "").lower()
    condition_id = str(item.get("conditionId") or "")
    enriched.update(
        {
            "category_ids": set(category_ids),
            "identifiers": identifiers,
            "aspects": aspects,
            "condition_group": (
                "parts"
                if condition_id == "7000" or "parts" in condition or "not working" in condition
                else "working"
                if condition or condition_id
                else None
            ),
        }
    )
    return enriched


def _structured_profiles_are_compatible(target: dict, candidate: dict) -> bool:
    target_condition = target.get("condition_group")
    candidate_condition = candidate.get("condition_group")
    if target_condition and candidate_condition and target_condition != candidate_condition:
        return False

    target_categories = set(target.get("category_ids") or [])
    candidate_categories = set(candidate.get("category_ids") or [])
    if target_categories and candidate_categories and target_categories.isdisjoint(candidate_categories):
        return False

    target_identifiers = target.get("identifiers") or {}
    candidate_identifiers = candidate.get("identifiers") or {}
    shares_identifier = any(
        set(target_identifiers.get(field) or [])
        & set(candidate_identifiers.get(field) or [])
        for field in IDENTIFIER_FIELDS
    )
    if not shares_identifier:
        for field in IDENTIFIER_FIELDS:
            target_values = set(target_identifiers.get(field) or [])
            candidate_values = set(candidate_identifiers.get(field) or [])
            if target_values and candidate_values and target_values.isdisjoint(candidate_values):
                return False

    target_aspects = target.get("aspects") or {}
    candidate_aspects = candidate.get("aspects") or {}
    for name in STRICT_ASPECT_NAMES:
        target_values = set(target_aspects.get(name) or [])
        candidate_values = set(candidate_aspects.get(name) or [])
        if target_values and candidate_values and target_values.isdisjoint(candidate_values):
            return False

    return True


def _profiles_share_identifier(target: dict, candidate: dict) -> bool:
    target_identifiers = target.get("identifiers") or {}
    candidate_identifiers = candidate.get("identifiers") or {}
    return any(
        set(target_identifiers.get(field) or [])
        & set(candidate_identifiers.get(field) or [])
        for field in IDENTIFIER_FIELDS
    )


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
    title_tokens = _meaningful_tokens(tokens)
    is_accessory_or_parts = _is_accessory_or_parts(text)
    gpu_attributes = _extract_gpu_attributes(text, tokens)
    if gpu_attributes:
        gpu_attributes["title_tokens"] = title_tokens
        gpu_attributes["is_accessory_or_parts"] = is_accessory_or_parts
        return gpu_attributes

    words = title_tokens
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
        "title_tokens": title_tokens,
        "is_accessory_or_parts": is_accessory_or_parts,
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

    if target.get("is_accessory_or_parts") != candidate.get("is_accessory_or_parts"):
        return False

    if not _structured_profiles_are_compatible(target, candidate):
        return False

    if target.get("product_type") != "gpu":
        if _profiles_share_identifier(target, candidate):
            return True
        return token_similarity_score(target, candidate) >= 0.62

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
