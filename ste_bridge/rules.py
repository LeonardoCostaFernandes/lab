"""Deterministic rules for checking controlled-language (ASD-STE100) compliance."""
import json
import pathlib
import re


_VAGUE_PT = {
    "eventualmente", "célere", "tempestivo", "tempestividade", "adequado",
    "oportunamente", "breve", "razoável", "diligenciar", "conformidade",
}

_VAGUE_EN = {
    "eventually", "timely", "adequate", "reasonable", "soon",
    "appropriate", "promptly", "as needed",
}

_PASSIVE_PT = re.compile(
    r"\b(foi|foram|é|são|será|serão|seja|sejam)\s+\w+(ado|ada|ados|adas|ido|ida|idos|idas)\b",
    re.IGNORECASE,
)

_PASSIVE_EN = re.compile(
    r"\b(is|are|was|were|be|been|being)\s+\w+ed\b",
    re.IGNORECASE,
)

_MULTI_ACTION = re.compile(r"( e | and |;|, procedendo)", re.IGNORECASE)


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences on . ! ? and newlines. Strip leading list numbers like '1.'."""
    raw = re.split(r"[.!?]+|\n", text)
    sents: list[str] = []
    for s in raw:
        s = s.strip()
        # Remove leading list numbers like "1. " or "42. "
        s = re.sub(r"^\d+\.\s*", "", s).strip()
        if s:
            sents.append(s)
    return sents


def check(text: str, lang: str) -> list[dict]:
    """Return a list of violation dicts for *text* in the given language.

    Each dict has keys: ``rule``, ``sentence_index``, ``detail``.
    """
    sentences = _split_sentences(text)
    violations: list[dict] = []
    vague = _VAGUE_PT if lang == "pt" else _VAGUE_EN

    for idx, sent in enumerate(sentences):
        words = sent.split()

        # R1_LENGTH
        if len(words) > 20:
            violations.append({
                "rule": "R1_LENGTH",
                "sentence_index": idx,
                "detail": f"sentence has {len(words)} words (max 20)",
            })

        # R2_VAGUE
        sent_lower = sent.lower()
        for word in vague:
            if word in sent_lower:
                violations.append({
                    "rule": "R2_VAGUE",
                    "sentence_index": idx,
                    "detail": f"vague word found: {word}",
                })

        # R3_PASSIVE
        if lang == "pt":
            passive_re = _PASSIVE_PT
        else:
            passive_re = _PASSIVE_EN
        m = passive_re.search(sent)
        if m:
            violations.append({
                "rule": "R3_PASSIVE",
                "sentence_index": idx,
                "detail": f"passive construction: {m.group()}",
            })

        # R4_MULTI_ACTION
        if _MULTI_ACTION.search(sent) and len(words) > 8:
            violations.append({
                "rule": "R4_MULTI_ACTION",
                "sentence_index": idx,
                "detail": "multiple actions joined in one sentence",
            })

    return violations
