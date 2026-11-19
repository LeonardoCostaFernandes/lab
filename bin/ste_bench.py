#!/usr/bin/env python3
"""ste_bench — run the ste_bridge benchmark matrix and write receipts.

Standard library only.  Calls normalize (text mode) or structured.extract + render
(structured mode) in-process.  Measures wall-clock latency with time.perf_counter.

Usage:
    python bin/ste_bench.py \
        --fixtures fixtures/ste/lawyer_pt.txt|fixtures/ste/expected_pt.txt|pt \
        --endpoints test=http://127.0.0.1:8080=qwen2.5-3b \
        --modes text structured \
        --runs 3 \
        --out benchmarks/2026-11-19-ste-matrix
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import sys
import time

# Ensure the repo root is on sys.path so ste_bridge package is importable.
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

import ste_bridge.normalize as normalize_mod  # noqa: E402
import ste_bridge.structured as structured_mod  # noqa: E402
import ste_bridge.coverage as coverage_mod  # noqa: E402


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_fixtures(raw: list[str]) -> list[dict]:
    """Parse fixture strings into dicts.

    Accepts two delimiter forms:
    - 'input|reference|lang'  (pipe separator)
    - 'input:reference:lang'  (colon separator; paths must not contain colons)
    """
    fixtures = []
    for s in raw:
        if "|" in s:
            parts = s.split("|")
        else:
            parts = s.split(":")
        if len(parts) != 3:
            raise ValueError(
                f"fixture must be input|reference|lang or input:reference:lang, got: {s!r}"
            )
        inp, ref, lang = parts
        if lang not in ("pt", "en"):
            raise ValueError(f"lang must be pt or en, got: {lang!r}")
        fixtures.append({"input": inp, "reference": ref, "lang": lang})
    return fixtures


def _parse_endpoints(raw: list[str]) -> list[dict]:
    """Parse 'name=url=model' strings into dicts."""
    endpoints = []
    for s in raw:
        eq_parts = s.split("=", 2)
        if len(eq_parts) != 3:
            raise ValueError(f"endpoint must be name=url=model, got: {s!r}")
        name, url, model = eq_parts
        endpoints.append({"name": name, "url": url, "model": model})
    return endpoints


def _run_one(fixture: dict, endpoint: dict, mode: str, runs: int) -> list[dict]:
    """Run one fixture × one endpoint × one mode × N runs. Return list of row dicts."""
    input_text = pathlib.Path(fixture["input"]).read_text(encoding="utf-8")
    ref_text = pathlib.Path(fixture["reference"]).read_text(encoding="utf-8")
    ref_steps = normalize_mod._parse_steps(ref_text)
    lang = fixture["lang"]

    rows = []
    for run_idx in range(runs):
        row = {
            "model": endpoint["model"],
            "fixture": os.path.basename(fixture["input"]),
            "mode": mode,
            "run": run_idx,
            "step_count": 0,
            "violation_count": 0,
            "retries": 0,
            "covered": 0,
            "total": len(ref_steps),
            "ratio": 0.0,
            "latency_ms": 0.0,
            "output_sha256": "",
            "status": "DEVICE_TESTED",
        }

        try:
            t0 = time.perf_counter()
            if mode == "text":
                result = normalize_mod.normalize(
                    text=input_text,
                    lang=lang,
                    endpoint=endpoint["url"],
                    model=endpoint["model"],
                    timeout=120,
                )
            else:
                result = structured_mod.extract(
                    text=input_text,
                    lang=lang,
                    endpoint=endpoint["url"],
                    model=endpoint["model"],
                    timeout=120,
                )
            elapsed_ms = (time.perf_counter() - t0) * 1000

            if result["status"].startswith("NO_DATA("):
                row["status"] = result["status"]
                row["latency_ms"] = round(elapsed_ms, 1)
                rows.append(row)
                continue

            steps = result["steps"]
            cov = coverage_mod.coverage(steps, ref_steps, lang)

            row["step_count"] = len(steps)
            row["violation_count"] = len(result["violations"])
            row["retries"] = result["retries"]
            row["covered"] = cov["covered"]
            row["total"] = cov["total"]
            row["ratio"] = cov["ratio"]
            row["latency_ms"] = round(elapsed_ms, 1)
            row["output_sha256"] = result["output_sha256"]
            row["status"] = result["status"]

        except Exception as e:
            row["status"] = f"NO_DATA({type(e).__name__})"

        rows.append(row)

    return rows


def _compute_means(rows: list[dict]) -> dict:
    """Compute per (model, mode) means of ratio, violation_count, latency_ms."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        key = (r["model"], r["mode"])
        groups.setdefault(key, []).append(r)

    means = {}
    for (model, mode), group in groups.items():
        n = len(group)
        ok = [r for r in group if not r["status"].startswith("NO_DATA(")]
        if ok:
            means[(model, mode)] = {
                "model": model,
                "mode": mode,
                "runs": n,
                "ok_runs": len(ok),
                "mean_ratio": round(sum(r["ratio"] for r in ok) / len(ok), 4),
                "mean_violation_count": round(sum(r["violation_count"] for r in ok) / len(ok), 2),
                "mean_latency_ms": round(sum(r["latency_ms"] for r in ok) / len(ok), 1),
            }
        else:
            means[(model, mode)] = {
                "model": model,
                "mode": mode,
                "runs": n,
                "ok_runs": 0,
                "mean_ratio": "NO_DATA(all_runs_failed)",
                "mean_violation_count": "NO_DATA(all_runs_failed)",
                "mean_latency_ms": "NO_DATA(all_runs_failed)",
            }
    return means


def _write_readme(out_dir: pathlib.Path, args: argparse.Namespace,
                  rows: list[dict], means: dict, machine: str) -> None:
    """Write DIR/README.md with metadata, table and means."""
    date_utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cmd_parts = ["python bin/ste_bench.py"]
    for f in args.fixtures:
        cmd_parts.append(f"--fixtures {f}")
    for e in args.endpoints:
        cmd_parts.append(f"--endpoints {e}")
    for m in args.modes:
        cmd_parts.append(f"--modes {m}")
    cmd_parts.append(f"--runs {args.runs}")
    cmd_parts.append(f"--out {args.out}")
    command_line = " ".join(cmd_parts)

    lines = [
        "# ste_bench matrix run",
        "",
        f"- Date (UTC): {date_utc}",
        f"- Command: `{command_line}`",
        f"- Machine: {machine}",
        "",
        "## Results table",
        "",
        "| model | fixture | mode | run | steps | violations | retries | covered/total | ratio | latency_ms | status |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        if r["status"].startswith("NO_DATA("):
            cause = r["status"]
            lines.append(
                f"| {r['model']} | {r['fixture']} | {r['mode']} | {r['run']} | "
                f"NO_DATA({cause}) | NO_DATA({cause}) | NO_DATA({cause}) | "
                f"NO_DATA({cause}) | NO_DATA({cause}) | NO_DATA({cause}) | "
                f"{r['status']} |"
            )
        else:
            lines.append(
                f"| {r['model']} | {r['fixture']} | {r['mode']} | {r['run']} | "
                f"{r['step_count']} | {r['violation_count']} | {r['retries']} | "
                f"{r['covered']}/{r['total']} | {r['ratio']:.4f} | {r['latency_ms']:.1f} | "
                f"{r['status']} |"
            )

    lines.append("")
    lines.append("## Means per model + mode")
    lines.append("")
    lines.append(
        "Formula: `mean(x) = sum(x_i) / n`  where n = number of successful rows used."
    )
    lines.append("")
    lines.append(
        "| model | mode | runs | n | mean_ratio | mean_violation_count | mean_latency_ms |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for key in sorted(means):
        m = means[key]
        n_label = m["ok_runs"]
        lines.append(
            f"| {m['model']} | {m['mode']} | {m['runs']} | {n_label} | "
            f"{m['mean_ratio']} | {m['mean_violation_count']} | {m['mean_latency_ms']} |"
        )

    (out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fixtures", required=True, nargs="+",
                    help="List of input|reference|lang")
    ap.add_argument("--endpoints", required=True, nargs="+",
                    help="List of name=url=model")
    ap.add_argument("--modes", required=True, nargs="+", choices=["text", "structured"],
                    help="Modes to run")
    ap.add_argument("--runs", type=int, default=2, help="Runs per combination (default: 2)")
    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--machine", default="NO_DATA(machine_not_declared)",
                    help="Machine description")
    args = ap.parse_args(argv)

    fixtures = _parse_fixtures(args.fixtures)
    endpoints = _parse_endpoints(args.endpoints)

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for fixture in fixtures:
        for endpoint in endpoints:
            for mode in args.modes:
                combo_rows = _run_one(fixture, endpoint, mode, args.runs)
                rows.extend(combo_rows)

    # Write receipts.jsonl
    receipts_path = out_dir / "receipts.jsonl"
    with open(receipts_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # Compute means and write README
    means = _compute_means(rows)
    _write_readme(out_dir, args, rows, means, args.machine)

    print(f"Wrote {len(rows)} rows to {receipts_path}")
    print(f"Wrote {out_dir / 'README.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
