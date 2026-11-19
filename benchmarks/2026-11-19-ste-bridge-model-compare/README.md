# 2026-11-19 · STE Bridge Model Comparison · Qwen2.5 3B vs 7B

- **Status:** `DEVICE_TESTED` (12 runs, all successful)
- **Machine:** Ryzen 7 5800H · RTX 3050 Laptop 4 GB · 15.3 GB RAM · Windows · NVIDIA driver 621.14
- **Runtime:** llama.cpp `b12549`, `win-cuda-12.4-x64`, `-ngl 99 -c 4096`
- **3B Model:** `qwen2.5-3b-instruct-q4_k_m` · `http://127.0.0.1:8080`
- **7B Model:** `qwen2.5-7b-instruct-q4_k_m` · `http://127.0.0.1:8081` (CPU only, -ngl 0, 8 threads)
- **Command:** `bin/ste_bridge.py normalize --in <fixture> --lang <pt|en> --endpoint <url> --model <name> --reference <expected> --receipt <path>`
- **Fixtures:** `fixtures/ste/lawyer_pt.txt`, `fixtures/ste/lawyer_pt_2.txt`, `fixtures/ste/lawyer_en.txt`
- **References:** `fixtures/ste/expected_pt.txt`, `fixtures/ste/expected_pt_2.txt`, `fixtures/ste/expected_en.txt`
- **Temperature:** 0, **Seed:** 42, **Max tokens:** 1024
- **Coverage:** one-to-one greedy Jaccard matching, stop words normalized (accents removed)
- **Coverage threshold:** 0.3 (orchestrator choice)

## Results

| Model | Fixture | Run | Step count | Violation count | Retries | Covered / Total | Ratio |
|---|---|---|---|---|---|---|---|
| 3B | lawyer_pt.txt | 1 | 2 | 3 | 1 | 0 / 4 | 0.00 |
| 3B | lawyer_pt.txt | 2 | 2 | 3 | 1 | 0 / 4 | 0.00 |
| 3B | lawyer_pt_2.txt | 1 | 2 | 0 | 0 | 2 / 4 | 0.50 |
| 3B | lawyer_pt_2.txt | 2 | 2 | 0 | 0 | 2 / 4 | 0.50 |
| 3B | lawyer_en.txt | 1 | 3 | 0 | 0 | 2 / 4 | 0.50 |
| 3B | lawyer_en.txt | 2 | 3 | 0 | 0 | 2 / 4 | 0.50 |
| 7B | lawyer_pt.txt | 1 | 3 | 2 | 1 | 0 / 4 | 0.00 |
| 7B | lawyer_pt.txt | 2 | 3 | 2 | 1 | 0 / 4 | 0.00 |
| 7B | lawyer_pt_2.txt | 1 | 6 | 0 | 0 | 3 / 4 | 0.75 |
| 7B | lawyer_pt_2.txt | 2 | 6 | 0 | 0 | 3 / 4 | 0.75 |
| 7B | lawyer_en.txt | 1 | 4 | 0 | 1 | 2 / 4 | 0.50 |
| 7B | lawyer_en.txt | 2 | 3 | 0 | 0 | 2 / 4 | 0.50 |

## Conclusion

The 7B model produces higher coverage on lawyer_pt_2 (0.75 vs 0.50) by generating more steps (6 vs 2), but both models fail to cover lawyer_pt (0.00) because the model outputs only 2–3 steps against 4 reference steps. Average coverage: 3B = 0.33, 7B = 0.38. The 7B model reduces violation_count on lawyer_pt (2 vs 3) but generates more steps overall, increasing the chance of one-to-one matches.
