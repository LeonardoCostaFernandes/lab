# 2026-11-19 · STE Bridge Quality · Qwen2.5-3B-Instruct Q4_K_M

- **Status:** `DEVICE_TESTED` (6 runs, all successful)
- **Machine:** Ryzen 7 5800H · RTX 3050 Laptop 4 GB · 15.3 GB RAM · Windows · NVIDIA driver 621.14
- **Runtime:** llama.cpp `b12549`, `win-cuda-12.4-x64`, `-ngl 99 -c 4096`, `--host 127.0.0.1`
- **Model:** `Qwen/Qwen2.5-3B-Instruct-GGUF` · `qwen2.5-3b-instruct-q4_k_m.gguf` · SHA-256 `626b4a66…15c62d`
- **Endpoint:** `http://127.0.0.1:8080`
- **Command:** `bin/ste_bridge.py normalize --in <fixture> --lang <pt|en> --endpoint http://127.0.0.1:8080 --model qwen2.5-3b-instruct-q4_k_m`
- **Prompts:** `ste_bridge/prompt_pt.txt` (with few-shot examples), `ste_bridge/prompt_en.txt` (with few-shot examples)
- **Fixtures:** `fixtures/ste/lawyer_pt.txt`, `fixtures/ste/lawyer_pt_2.txt`, `fixtures/ste/lawyer_en.txt` (all synthetic)
- **Temperature:** 0, **Seed:** 42, **Max tokens:** 1024

## Results

| Fixture | Run | Step count | Violation count | Retries | Output SHA-256 (prefix) |
|---|---|---|---|---|---|
| lawyer_pt.txt | 1 | 2 | 1 | 1 | 93eb8e7f009e |
| lawyer_pt.txt | 2 | 2 | 1 | 1 | 93eb8e7f009e |
| lawyer_pt_2.txt | 1 | 2 | 0 | 0 | 2045ce729bfb |
| lawyer_pt_2.txt | 2 | 2 | 0 | 0 | 2045ce729bfb |
| lawyer_en.txt | 1 | 3 | 0 | 0 | 82abd5902466 |
| lawyer_en.txt | 2 | 3 | 0 | 0 | 10d051630eb3 |
| **Baseline (lawyer_pt)** | — | 2 | 5 | 1 | — |

## T-0008 — Coverage metric

New runs with `--reference` flag and updated prompts (completeness rule added).

| Fixture | Run | Step count | Violation count | Retries | Covered / Total | Ratio | Output SHA-256 (prefix) |
|---|---|---|---|---|---|---|---|
| lawyer_pt.txt | 1 | 2 | 3 | 1 | 0 / 4 | 0.00 | 479647e68a8e |
| lawyer_pt.txt | 2 | 2 | 1 | 1 | 1 / 4 | 0.25 | 5c8465b4f380 |
| lawyer_pt_2.txt | 1 | 2 | 0 | 0 | 4 / 4 | 1.00 | 4b73355b99de |
| lawyer_pt_2.txt | 2 | 2 | 0 | 0 | 4 / 4 | 1.00 | 4b73355b99de |
| lawyer_en.txt | 1 | 3 | 0 | 0 | 2 / 4 | 0.50 | 614959bb04f0 |
| lawyer_en.txt | 2 | 3 | 0 | 0 | 2 / 4 | 0.50 | 91482a8c8d91 |

## Notes

- lawyer_pt.txt: deterministic output across runs (identical SHA). 1 violation remains after retry (R2_VAGUE: "breve").
- lawyer_pt_2.txt: deterministic output, 0 violations, no retry needed.
- lawyer_en.txt: different output SHA between runs despite temperature=0 and seed=42 — the model may not honor seed strictly. Both runs have 0 violations.
- Baseline row: from the task description (lawyer_pt gives step_count 2, violation_count 5, retries 1). The few-shot examples reduced violations from 5 to 1.
- No raw model output stored — only counts, hashes and latencies per the measured record policy.
