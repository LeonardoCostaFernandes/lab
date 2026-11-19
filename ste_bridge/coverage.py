"""Coverage metric — measure how many reference steps are covered by model steps."""
import re
import unicodedata


# Stop-word lists capped at 40 entries; accents removed via _normalize for comparison.
_STOP_PT = {
    "o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
    "em", "no", "na", "por", "para", "com", "que",
    "se", "e", "ou", "e", "sao", "foi", "foram", "ser", "ter",
    "este", "esta", "esse", "essa",
    "mais", "menos", "muito", "tambem", "nao", "sim", "mas",
}

_STOP_EN = {
    "the", "a", "an", "of", "in", "to", "for", "with", "by", "on", "at",
    "is", "are", "was", "were", "be", "been", "have", "has", "had",
    "do", "does", "did", "will", "would", "should", "can", "could",
    "this", "that", "it", "its", "as",
    "or", "and", "but", "if", "not", "no",
}


def _normalize(text: str) -> str:
    """Lowercase and strip accents."""
    text = text.lower()
    # NFD decomposes accented chars; keep only the base letter
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text


def _tokens(text: str, lang: str) -> set[str]:
    """Return the set of meaningful tokens for *text* in the given language."""
    text = _normalize(text)
    stop = _STOP_PT if lang == "pt" else _STOP_EN
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

    One-to-one matching: each model step can cover at most one reference step.
    Uses greedy matching on the highest Jaccard similarity first.

    Returns a dict with keys: covered, total, ratio, missing_indexes.
    """
    step_tokens = [_tokens(s, lang) for s in steps]
    ref_tokens = [_tokens(r, lang) for r in reference]

    # Build all (jaccard, ref_index, step_index) pairs above threshold
    pairs: list[tuple[float, int, int]] = []
    for ri, rt in enumerate(ref_tokens):
        for si, st in enumerate(step_tokens):
            sim = jaccard(rt, st)
            if sim >= 0.3:
                pairs.append((sim, ri, si))

    # Sort by similarity descending — greedy: best match first
    pairs.sort(key=lambda x: -x[0])

    used_steps: set[int] = set()
    covered_refs: set[int] = set()

    for sim, ri, si in pairs:
        if si not in used_steps and ri not in covered_refs:
            used_steps.add(si)
            covered_refs.add(ri)

    covered = len(covered_refs)
    missing_indexes = [i for i in range(len(reference)) if i not in covered_refs]

    total = len(reference)
    ratio = covered / total if total else 0.0

    return {
        "covered": covered,
        "total": total,
        "ratio": ratio,
        "missing_indexes": missing_indexes,
    }
