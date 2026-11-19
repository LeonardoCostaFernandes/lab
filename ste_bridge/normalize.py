"""Normalize legal text into controlled-language steps via a local model."""
import hashlib
import ipaddress
import json
import pathlib
import re
import time
import urllib.error
import urllib.parse
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


def _check_loopback(endpoint: str) -> str:
    """Return normalized endpoint or raise ValueError if not numeric loopback http."""
    u = urllib.parse.urlsplit(endpoint)
    if u.scheme != "http" or u.port is None or u.path not in ("", "/"):
        raise ValueError("endpoint must be http://<loopback-ip>:<port>")
    host = u.hostname or ""
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        raise ValueError("endpoint host must be a numeric IP, not a name")
    if not ip.is_loopback:
        raise ValueError("endpoint must be loopback")
    shown = f"[{host}]" if ip.version == 6 else host
    return f"http://{shown}:{u.port}"


def normalize(text: str, lang: str, endpoint: str, model: str, timeout: int = 120) -> dict:
    """Rewrite *text* into controlled-language steps using a local model.

    Returns a dict with keys: status, steps, violations, retries, input_sha256, output_sha256, latency_ms.
    """
    # Enforce loopback-only inside normalize(), not just in CLI
    try:
        endpoint = _check_loopback(endpoint)
    except ValueError as e:
        raise ValueError(str(e)) from e

    system_prompt = _prompt_path(lang).read_text(encoding="utf-8")
    input_hash = _sha256(text)
    retries = 0
    output_text = ""
    violations = []
    total_latency_ms = 0.0

    user_message = text
    for attempt in range(2):
        try:
            t0 = time.monotonic()
            output_text = _chat_request(endpoint, model, system_prompt, user_message, timeout)
            elapsed_ms = (time.monotonic() - t0) * 1000
            total_latency_ms += elapsed_ms
        except (urllib.error.URLError, OSError, KeyError, ValueError) as e:
            return {
                "status": f"NO_DATA({type(e).__name__})",
                "steps": [],
                "violations": [],
                "retries": retries,
                "input_sha256": input_hash,
                "output_sha256": "",
                "latency_ms": round(total_latency_ms, 1),
            }

        violations = rules.check(output_text, lang)
        if violations:
            if attempt == 0:
                retries = 1
                user_message = (
                    text
                    + "\n\nThe previous output had violations:\n"
                    + json.dumps(violations, ensure_ascii=False)
                    + "\nPlease fix the violations and output corrected steps."
                )
                continue
            else:
                # Already retried once; max retries = 1
                break
        else:
            break

    # Parse steps from model output: accept "1.", "1)" or "- " prefixed lines
    steps = _parse_steps(output_text)

    return {
        "status": "DEVICE_TESTED",
        "steps": steps,
        "violations": violations,
        "retries": retries,
        "input_sha256": input_hash,
        "output_sha256": _sha256(output_text),
        "latency_ms": round(total_latency_ms, 1),
    }


def _parse_steps(text: str) -> list[str]:
    """Parse steps from model output.

    Accepts lines starting with '1.', '1)' or '- '. Returns the text without the prefix.
    """
    steps = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Match "1. text", "1) text", or "- text"
        m = re.match(r"^\d+[.)]\s*(.*)", line)
        if m:
            step = m.group(1).strip()
            if step:
                steps.append(step)
            continue
        m = re.match(r"^-\s+(.*)", line)
        if m:
            step = m.group(1).strip()
            if step:
                steps.append(step)
    return steps


def re_match_numbered(line: str) -> bool:
    """Check if a line looks like a numbered step (e.g. '1. Do something')."""
    return bool(re.match(r"^\d+[.)]\s+\S", line))
