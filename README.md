# lab · LeonardoCostaFernandes

Personal measured record for my PreceptorOS Companion work: local-model benchmarks, receipts and proposals.

Layout copied from [piskyRpapalo/lab](https://github.com/piskyRpapalo/lab) (Apache-2.0). Content is my own; no upstream proposals, results or signatures are copied. See `NOTICE`.

## Scope

- Benchmarks of local models running on my own hardware (loopback only).
- Receipts: counts, hashes, latencies. Never raw prompts, raw answers, credentials or personal data.
- Proposals for my Companion and for public missions, as draft PRs titled `HITL`.

## Layout

| Path | Content |
|---|---|
| `AGENTS.md` | Single agent contract. `CLAUDE.md` and `.junie/guidelines.md` point here. |
| `STATE.md` | Measured record. Missing value = `NO_DATA(cause)`. |
| `benchmarks/` | One folder per run: `README.md` + `receipt.json`. |
| `proposals/` | Draft proposals, one file or folder each. |
| `reports/` | Dated reports built from receipts. |
| `contracts/` | JSON schemas for receipts. |
| `fixtures/` | Synthetic inputs only. |
| `bin/` | Standard-library Python tools. |
| `tests/` | `python3 -m unittest discover -s tests`, run twice. |

## Yardstick

```sh
python3 -m unittest discover -s tests -p "test_*.py"   # twice
python3 bin/verify_structure.py
```

## ste_bridge

A filter that converts legal Portuguese or English text into controlled-language steps (ASD-STE100 style). A local model performs the rewrite; deterministic rules check the result.

**Commands**

- `python bin/ste_bridge.py check --in FILE --lang pt|en` — print violations as JSON.
- `python bin/ste_bridge.py normalize --in FILE --lang pt|en --endpoint URL --model NAME [--receipt FILE]` — rewrite text into numbered steps and optionally write a receipt (hashes and counts only).

**Rules**

1. `R1_LENGTH` — sentence exceeds 20 words.
2. `R2_VAGUE` — sentence contains a vague word (e.g., *tempestividade*, *reasonable*).
3. `R3_PASSIVE` — sentence uses passive voice.
4. `R4_MULTI_ACTION` — sentence joins multiple actions (e.g., "e", "and", ";").

## Status

Proposal. Unsigned. Nothing here is a LIVE node or a public service.
