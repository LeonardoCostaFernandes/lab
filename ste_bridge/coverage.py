"""Coverage metric — measure how many reference steps are covered by model steps."""
import re


_STOP_PT = {
    "o", "a", "os", "as", "um", "uma", "um", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "que",
    "se", "e", "ou", "é", "são", "foi", "foram", "ser", "ter", "será",
    "este", "esta", "estes", "estas", "esse", "essa", "esses", "essas",
    "mais", "menos", "muito", "também", "não", "sim", "mas", "como",
    "onde", "quando", "qual", "quais", "seu", "sua", "seus", "suas",
}

_STOP_EN = {
    "the", "a", "an", "of", "in", "to", "for", "with", "by", "on", "at",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "shall", "should", "may", "might",
    "can", "could", "this", "that", "these", "those", "it", "its", "as",
    "or", "and", "but", "if", "not", "no", "so", "than", "too", "very",
    "just", "about", "into", "through", "during", "before", "after",
    "above", "below", "between", "out", "up", "down", "off", "over",
}


def _normalize(text: str) -> str:
    """Lowercase and strip accents."""
    import unicodedata
    text = text.lower()
    # NFD decomposes accented chars; keep only the base letter
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text


def _tokens(text: str, lang: str) -> set[str]:
    """Return the set of meaningful tokens for *text* in the given language."""
    text = _normalize(text)
    stop = _STOP_PT if lang == "pt" else _STOP_EN
    words = re.findall(r"[a-záàâãéèêíïóôõöúçñ]+", text)
    # After normalization accents are gone; re-extract plain alpha tokens
    words = re.findall(r"[a-z]+", text)
    return {w for w in words if w not in stop and len(w) > 1}


def jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity between two token sets."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    intersection = a & b
    union = a | b
    return len(intersection) / len(union)


def coverage(steps: list[str], reference: list[str], lang: str) -> dict:
    """Measure how many reference steps are covered by the model *steps*.

    Returns a dict with keys: covered, total, ratio, missing_indexes.
    """
    step_tokens = [_tokens(s, lang) for s in steps]
    ref_tokens = [_tokens(r, lang) for r in reference]

    covered = 0
    missing_indexes: list[int] = []

    for i, rt in enumerate(ref_tokens):
        best = 0.0
        for st in step_tokens:
            sim = jaccard(rt, st)
            if sim > best:
                best = sim
        if best >= 0.3:
            covered += 1
        else:
            missing_indexes.append(i)

    total = len(reference)
    ratio = covered / total if total else 0.0

    return {
        "covered": covered,
        "total": total,
        "ratio": ratio,
        "missing_indexes": missing_indexes,
    }
