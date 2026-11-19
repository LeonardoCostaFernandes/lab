# benchmarks

One folder per run: `YYYY-MM-DD-<model-slug>/` with `README.md` (what, why, command, limits) and `receipt.json` (schema `contracts/receipt.schema.json`).

Prompts live in `local/` (gitignored). Only their SHA-256 enters the receipt.

Quality (is the answer good?) is `NO_DATA(no_human_gold_labels)` until a labeled set exists.
