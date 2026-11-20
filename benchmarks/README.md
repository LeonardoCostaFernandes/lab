# benchmarks

One folder per run: `YYYY-MM-DD-<model-slug>/` with `README.md` (what, why, command, limits) and `receipt.json` (schema `contracts/receipt.schema.json`).

Prompts live in `local/` (gitignored). Only their SHA-256 enters the receipt.

Quality (is the answer good?) is `NO_DATA(no_human_gold_labels)` until a labeled set exists.

## ste_bench — matrix runner

Runs the ste_bridge benchmark matrix (fixtures × endpoints × modes × runs) and writes `receipts.jsonl` + `README.md`.

```sh
python bin/ste_bench.py \
    --fixtures fixtures/ste/lawyer_pt.txt|fixtures/ste/expected_pt.txt|pt \
    --endpoints qwen=http://127.0.0.1:8080=qwen2.5-3b \
    --modes text structured \
    --runs 3 \
    --machine "Ryzen 7 5800H / RTX 3050 4GB" \
    --out benchmarks/2026-11-19-ste-matrix
```

Arguments:

- `--fixtures` — one or more `input|reference|lang` or `input:reference:lang` (lang = pt or en).
- `--endpoints` — one or more `name=url=model`.
- `--modes` — `text`, `structured`, or both.
- `--runs` — repetitions per combination (default 2).
- `--out` — output directory (receives `receipts.jsonl` and `README.md`).
- `--machine` — machine description (default `NO_DATA(machine_not_declared)`).

Output files contain only counts, hashes and latencies — never raw prompts or answers.
