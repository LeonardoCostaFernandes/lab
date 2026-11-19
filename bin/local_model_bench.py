#!/usr/bin/env python3
"""Benchmark a local OpenAI-compatible chat endpoint (llama.cpp server, Ollama).

Loopback only. Writes a receipt with hashes and timings, never raw text.
Prompts come from a local file (one prompt per line) that stays out of Git.

Example:
  python3 bin/local_model_bench.py --endpoint http://127.0.0.1:8080 \
      --model qwen2.5-3b-instruct-q4_k_m --prompts local/prompts.txt \
      --machine "Ryzen 7 5800H / RTX 3050 4GB" --out benchmarks/2026-11-19-qwen3b/receipt.json
"""
import argparse
import datetime as dt
import hashlib
import ipaddress
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SCHEMA = "lab.receipt/1"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_loopback(endpoint: str) -> str:
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


def call(endpoint, model, prompt, max_tokens, seed, timeout):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "seed": seed,
        "max_tokens": max_tokens,
        "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(endpoint + "/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    # No proxy: loopback must never leave the machine.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    t0 = time.perf_counter()
    with opener.open(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    latency_ms = (time.perf_counter() - t0) * 1000
    text = data["choices"][0]["message"]["content"] or ""
    usage = data.get("usage") or {}
    return text, latency_ms, usage


def run(args):
    endpoint = check_loopback(args.endpoint)
    with open(args.prompts, encoding="utf-8") as f:
        prompts = [line.strip() for line in f if line.strip()]
    if not prompts:
        raise ValueError("prompt file is empty")
    runs = []
    for p in prompts:
        entry = {"prompt_sha256": sha256(p), "output_sha256": None, "output_chars": None,
                 "latency_ms": None, "prompt_tokens": None, "completion_tokens": None,
                 "tokens_per_s": None, "error": None}
        try:
            text, ms, usage = call(endpoint, args.model, p, args.max_tokens, args.seed, args.timeout)
            ct = usage.get("completion_tokens")
            entry.update(output_sha256=sha256(text), output_chars=len(text), latency_ms=round(ms, 1),
                         prompt_tokens=usage.get("prompt_tokens"), completion_tokens=ct,
                         tokens_per_s=round(ct / (ms / 1000), 2) if ct and ms > 0 else None)
        except (urllib.error.URLError, OSError, KeyError, ValueError) as e:
            entry["error"] = type(e).__name__
        runs.append(entry)
    ok = [r for r in runs if r["error"] is None]
    status = "DEVICE_TESTED" if ok else "NO_DATA(endpoint_unreachable_or_invalid_response)"
    return {
        "schema": SCHEMA,
        "status": status,
        "date_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "machine": args.machine,
        "endpoint": endpoint,
        "model": args.model,
        "command": "bin/local_model_bench.py",
        "params": {"temperature": 0, "seed": args.seed, "max_tokens": args.max_tokens,
                   "n_prompts": len(prompts)},
        "runs": runs,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--endpoint", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--machine", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-tokens", type=int, default=128)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--timeout", type=float, default=120)
    args = ap.parse_args(argv)
    try:
        receipt = run(args)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    import os
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)
        f.write("\n")
    print(receipt["status"])
    return 0 if receipt["status"] == "DEVICE_TESTED" else 1


if __name__ == "__main__":
    sys.exit(main())
