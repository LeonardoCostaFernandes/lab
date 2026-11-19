"""Structured JSON-schema mode for ste_bridge.

The model fills a JSON object conforming to schema.json. Code renders the STE
steps from the structured output. Compare with free-text mode.
"""
import json
import pathlib
import time
import urllib.error
import urllib.request

import ste_bridge.rules as rules  # type: ignore

# Reuse loopback enforcement from normalize.
from ste_bridge.normalize import _check_loopback, _sha256  # type: ignore

_SCHEMA_PATH = pathlib.Path(__file__).parent / "schema.json"


def _prompt_path(lang: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / f"prompt_{lang}.txt"


def _chat_request_structured(endpoint: str, model: str, system: str, user: str,
                             schema: dict, timeout: int) -> str:
    """Send one chat completion request with JSON schema constraint."""
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
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "schema": schema,
            },
        },
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


def render(items: list[dict], lang: str) -> list[str]:
    """Render structured items into controlled-language step strings.

    Templates:
      - pt: "{verb} {object}."  |  with if: "Se {if}, {verb} {object}."
      - en: "{verb} {object}."  |  with if: "If {if}, {verb} {object}."
      - kind=stop: pt "Pare e alerte o humano." / en "Stop and alert the human."
    """
    steps: list[str] = []
    for item in items:
        kind = item.get("kind", "action")
        verb = item.get("verb", "")
        obj = item.get("object", "")
        cond = item.get("if")

        if kind == "stop":
            if lang == "pt":
                steps.append("Pare e alerte o humano.")
            else:
                steps.append("Stop and alert the human.")
            continue

        if cond:
            if lang == "pt":
                step = f"Se {cond}, {verb} {obj}."
            else:
                step = f"If {cond}, {verb} {obj}."
        else:
            step = f"{verb} {obj}."

        steps.append(step)
    return steps


def extract(text: str, lang: str, endpoint: str, model: str, timeout: int = 120) -> dict:
    """Extract structured steps from *text* via a local model with JSON schema.

    Returns a dict with keys: status, steps, violations, retries, input_sha256,
    output_sha256, latency_ms, raw_items.
    """
    endpoint = _check_loopback(endpoint)

    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    system_prompt = _prompt_path(lang).read_text(encoding="utf-8")

    # Append structured output instruction to system prompt
    structured_instruction = (
        "\n\nOutput a JSON object with an 'items' array. Each item has: "
        "'kind' (check|condition|action|stop), 'actor' (string), 'verb' (imperative), "
        "'object' (string), 'if' (string or null), 'deadline' (string or null)."
    )
    system_prompt += structured_instruction

    input_hash = _sha256(text)
    retries = 0
    raw_items: list[dict] = []
    output_text = ""
    violations = []
    total_latency_ms = 0.0

    user_message = text
    for attempt in range(2):
        try:
            t0 = time.monotonic()
            output_text = _chat_request_structured(
                endpoint, model, system_prompt, user_message, schema, timeout
            )
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
                "raw_items": [],
            }

        # Parse the JSON output
        try:
            parsed = json.loads(output_text)
            raw_items = parsed.get("items", [])
        except (json.JSONDecodeError, TypeError):
            return {
                "status": "NO_DATA(invalid_json)",
                "steps": [],
                "violations": [],
                "retries": retries,
                "input_sha256": input_hash,
                "output_sha256": _sha256(output_text),
                "latency_ms": round(total_latency_ms, 1),
                "raw_items": [],
            }

        # Render steps from structured items
        steps = render(raw_items, lang)

        # Run rules.check on rendered steps
        violations = rules.check("\n".join(steps), lang)
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
                break
        else:
            break

    return {
        "status": "DEVICE_TESTED",
        "steps": steps,
        "violations": violations,
        "retries": retries,
        "input_sha256": input_hash,
        "output_sha256": _sha256(output_text),
        "latency_ms": round(total_latency_ms, 1),
        "raw_items": raw_items,
    }
