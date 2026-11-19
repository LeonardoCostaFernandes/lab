#!/usr/bin/env python3
"""ste_bridge CLI – check or normalize legal text into controlled-language steps."""
import argparse
import json
import pathlib
import sys

# Ensure the repo root is on sys.path so ste_bridge package is importable.
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

import ste_bridge.rules as rules  # noqa: E402
import ste_bridge.normalize as normalize_mod  # noqa: E402


def _cmd_check(args: argparse.Namespace) -> int:
    text = pathlib.Path(args.in_file).read_text(encoding="utf-8")
    violations = rules.check(text, args.lang)
    print(json.dumps(violations, indent=2, ensure_ascii=False))
    return 0


def _cmd_normalize(args: argparse.Namespace) -> int:
    # Validate loopback endpoint using the same helper as local_model_bench.
    sys.path.insert(0, str(_REPO_ROOT / "bin"))
    import local_model_bench as lmb  # noqa: E402
    try:
        endpoint = lmb.check_loopback(args.endpoint)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    text = pathlib.Path(args.in_file).read_text(encoding="utf-8")
    result = normalize_mod.normalize(
        text=text,
        lang=args.lang,
        endpoint=endpoint,
        model=args.model,
        timeout=args.timeout,
    )

    # Print steps to stdout.
    for step in result["steps"]:
        print(step)

    # Write receipt if requested.
    if args.receipt:
        receipt = {
            "status": result["status"],
            "step_count": len(result["steps"]),
            "violation_count": len(result["violations"]),
            "retries": result["retries"],
            "input_sha256": result["input_sha256"],
            "output_sha256": result["output_sha256"],
        }
        rp = pathlib.Path(args.receipt)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    return 0 if result["status"] == "DEVICE_TESTED" else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    # check sub-command
    p_check = sub.add_parser("check", help="Print violations as JSON")
    p_check.add_argument("--in", dest="in_file", required=True, help="Input text file")
    p_check.add_argument("--lang", required=True, choices=["pt", "en"])

    # normalize sub-command
    p_norm = sub.add_parser("normalize", help="Normalize text via local model")
    p_norm.add_argument("--in", dest="in_file", required=True, help="Input text file")
    p_norm.add_argument("--lang", required=True, choices=["pt", "en"])
    p_norm.add_argument("--endpoint", required=True, help="Loopback model URL")
    p_norm.add_argument("--model", required=True, help="Model name")
    p_norm.add_argument("--receipt", default=None, help="Receipt output path (hashes only)")
    p_norm.add_argument("--timeout", type=int, default=120)

    args = ap.parse_args(argv)

    if args.command == "check":
        return _cmd_check(args)
    elif args.command == "normalize":
        return _cmd_normalize(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
