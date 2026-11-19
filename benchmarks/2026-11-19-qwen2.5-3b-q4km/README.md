# 2026-11-19 · Qwen2.5-3B-Instruct Q4_K_M · owner PC

- **Status:** `DEVICE_TESTED` (2 runs, both successful)
- **Machine:** Ryzen 7 5800H · RTX 3050 Laptop 4 GB · 15.3 GB RAM · Windows · NVIDIA driver 621.14
- **Runtime:** llama.cpp `b12549`, `win-cuda-12.4-x64` (SHA-256 `05053794…a6849b`), `-ngl 99 -c 4096`, `--host 127.0.0.1`
- **Model:** `Qwen/Qwen2.5-3B-Instruct-GGUF` · `qwen2.5-3b-instruct-q4_k_m.gguf` · 2,104,932,768 bytes · SHA-256 `626b4a66…15c62d` (verified)
- **Prompts:** `fixtures/synthetic-prompts.txt` (synthetic; hashes match receipts)
- **Command:** `bin/local_model_bench.ps1`, temperature 0, seed 42, max_tokens 128

| Run | Prompt | Latency ms | Completion tokens | Tokens/s |
|---|---|---|---|---|
| 1 | P1 | 1162.5 | 36 | 30.97 |
| 1 | P2 | 740.9 | 48 | 64.79 |
| 2 | P1 | 546.9 | 36 | 65.83 |
| 2 | P2 | 694.2 | 48 | 69.14 |

- Output SHA-256 identical across runs for both prompts: deterministic at temperature 0, seed 42.
- Run 1 P1 includes first-request warm-up.
- tokens/s = completion tokens / wall-clock request time (includes prompt processing).
- GPU memory in use after load: 3219 MiB (nvidia-smi).
- Answer quality: `NO_DATA(no_human_gold_labels)`.
- Energy per token: `NO_DATA(no_power_meter)`.
