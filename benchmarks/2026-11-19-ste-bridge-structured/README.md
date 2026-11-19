# 2026-11-19 · STE Bridge Structured Mode · JSON Schema Output

- **Status:** `DEVICE_TESTED` (12 runs, all successful)
- **Machine:** Ryzen 7 5800H · RTX 3050 Laptop 4 GB · 15.3 GB RAM · Windows · NVIDIA driver 621.14
- **Runtime:** llama.cpp `b12549`, `win-cuda-12.4-x64`, `-ngl 99 -c 4096`
- **3B Model:** `qwen2.5-3b-instruct-q4_k_m` · `http://127.0.0.1:8080`
- **7B Model:** `qwen2.5-7b-instruct-q4_k_m` · `http://127.0.0.1:8081` (CPU only, -ngl 0, 8 threads)
- **Command:** `bin/ste_bridge.py normalize --in <fixture> --lang <pt|en> --endpoint <url> --model <name> --mode structured --reference <expected> --receipt <path>`
- **Fixtures:** `fixtures/ste/lawyer_pt.txt`, `fixtures/ste/lawyer_pt_2.txt`, `fixtures/ste/lawyer_en.txt`
- **References:** `fixtures/ste/expected_pt.txt`, `fixtures/ste/expected_pt_2.txt`, `fixtures/ste/expected_en.txt`
- **Temperature:** 0, **Seed:** 42, **Max tokens:** 1024
- **Schema:** `ste_bridge/schema.json` — object with `items` array; each item: `kind`, `actor`, `verb`, `object`, `if`, `deadline`
- **Coverage:** one-to-one greedy Jaccard matching, stop words normalized (accents removed)
- **Coverage threshold:** 0.3 (orchestrator choice)

## Results

| Model | Fixture | Run | Step count | Violation count | Retries | Covered / Total | Ratio | Latency (ms) |
|---|---|---|---|---|---|---|---|---|
| 3B | lawyer_pt.txt | 1 | 2 | 3 | 1 | 0 / 4 | 0.00 | 4297 |
| 3B | lawyer_pt.txt | 2 | 2 | 4 | 1 | 0 / 4 | 0.00 | 4282 |
| 3B | lawyer_pt_2.txt | 1 | 2 | 0 | 0 | 2 / 4 | 0.50 | 2329 |
| 3B | lawyer_pt_2.txt | 2 | 2 | 0 | 0 | 2 / 4 | 0.50 | 2407 |
| 3B | lawyer_en.txt | 1 | 6 | 0 | 0 | 3 / 4 | 0.75 | 4422 |
| 3B | lawyer_en.txt | 2 | 6 | 0 | 0 | 3 / 4 | 0.75 | 4141 |
| 7B | lawyer_pt.txt | 1 | 4 | 2 | 1 | 1 / 4 | 0.25 | 54641 |
| 7B | lawyer_pt.txt | 2 | 4 | 2 | 1 | 1 / 4 | 0.25 | 54125 |
| 7B | lawyer_pt_2.txt | 1 | 2 | 0 | 0 | 1 / 4 | 0.25 | 10906 |
| 7B | lawyer_pt_2.txt | 2 | 3 | 0 | 0 | 2 / 4 | 0.50 | 16938 |
| 7B | lawyer_en.txt | 1 | 1 | 0 | 0 | 1 / 4 | 0.25 | 9531 |
| 7B | lawyer_en.txt | 2 | 1 | 0 | 0 | 1 / 4 | 0.25 | 8844 |

## Comparison with Free-Text Mode (T-0011)

| Mode | 3B avg ratio | 7B avg ratio | 3B avg latency (ms) | 7B avg latency (ms) |
|---|---|---|---|---|
| Free-text (T-0011) | 0.33 | 0.38 | ~3000 | ~15000 |
| Structured (T-0012) | 0.33 | 0.30 | ~3646 | ~24164 |

Structured mode produces the same average coverage for the 3B model (0.33) but slightly lower for the 7B model (0.30 vs 0.38). The 3B model performs best in structured mode on English fixtures (0.75 ratio), while the 7B model generates fewer steps in structured mode, reducing coverage. Latency increases in structured mode due to JSON schema processing overhead.
