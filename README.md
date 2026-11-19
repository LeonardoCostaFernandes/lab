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

## Status

Proposal. Unsigned. Nothing here is a LIVE node or a public service.
