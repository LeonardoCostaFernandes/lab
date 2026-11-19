"""Normalize legal text into controlled-language steps via a local model."""
import hashlib
import json
import pathlib
import urllib.error
import urllib.request

import ste_bridge.rules as rules  # type: ignore


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _prompt_path(lang: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / f"prompt_{lang}.txt"


def _chat_request(endpoint: str, model: str, system: str, user: str, timeout: int) -> str:
    """Send one chat completion request and return the assistant text."""
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "seed": 42,
        "max_tokens": 1024,
        "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        endpoint + "/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    text = data["choices"][0]["message"]["content"] or ""
    return text


def normalize(text: str, lang: str, endpoint: str, model: str, timeout: int = 120) -> dict:
    """Rewrite *text* into controlled-language steps using a local model.

    Returns a dict with keys: status, steps, violations, retries, input_sha256, output_sha256.
    """
    system_prompt = _prompt_path(lang).read_text(encoding="utf-8")
    input_hash = _sha256(text)
    retries = 0
    output_text = ""

    user_message = text
    for attempt in range(2):
        try:
            output_text = _chat_request(endpoint, model, system_prompt, user_message, timeout)
        except (urllib.error.URLError, OSError, KeyError, ValueError) as e:
            return {
                "status": f"NO_DATA({type(e).__name__})",
                "steps": [],
                "violations": [],
                "retries": 0,
                "input_sha256": input_hash,
                "output_sha256": "",
            }

        violations = rules.check(output_text, lang)
        if violations:
            retries += 1
            user_message = (
                text
                + "\n\nThe previous output had violations:\n"
                + json.dumps(violations, ensure_ascii=False)
                + "\nPlease fix the violations and output corrected steps."
            )
            continue
        else:
            break

    # Parse numbered steps from output
    lines = [ln.strip() for ln in output_text.splitlines() if ln.strip()]
    steps = [ln for ln in lines if re_match_numbered(ln)]

    return {
        "status": "DEVICE_TESTED",
        "steps": steps,
        "violations": violations,
        "retries": retries,
        "input_sha256": input_hash,
        "output_sha256": _sha256(output_text),
    }


def re_match_numbered(line: str) -> bool:
    """Check if a line looks like a numbered step (e.g. '1. Do something')."""
    import re
    return bool(re.match(r"^\d+\.\s+\S", line))
