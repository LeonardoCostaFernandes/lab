# ste_bench matrix run

- Date (UTC): 2026-11-19T23:52:06Z
- Command: `python bin/ste_bench.py --fixtures fixtures/ste/lawyer_pt.txt|fixtures/ste/expected_pt.txt|pt --fixtures fixtures/ste/lawyer_pt_2.txt|fixtures/ste/expected_pt_2.txt|pt --fixtures fixtures/ste/lawyer_en.txt|fixtures/ste/expected_en.txt|en --endpoints 3b=http://127.0.0.1:8080=qwen2.5-3b-instruct-q4_k_m --endpoints 7b=http://127.0.0.1:8081=qwen2.5-7b-instruct-q4_k_m --modes text --modes structured --runs 2 --out benchmarks/2026-11-19-ste-matrix`
- Machine: consumer laptop, 4 GB GPU; 3B on GPU, 7B CPU-only (8 threads)

## Results table

| model | fixture | mode | run | steps | violations | retries | covered/total | ratio | latency_ms | status |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen2.5-3b-instruct-q4_k_m | lawyer_pt.txt | text | 0 | 2 | 3 | 1 | 0/4 | 0.0000 | 1701.2 | DEVICE_TESTED |
| qwen2.5-3b-instruct-q4_k_m | lawyer_pt.txt | text | 1 | 2 | 3 | 1 | 0/4 | 0.0000 | 1322.3 | DEVICE_TESTED |
| qwen2.5-3b-instruct-q4_k_m | lawyer_pt.txt | structured | 0 | 3 | 3 | 1 | 0/4 | 0.0000 | 4419.6 | DEVICE_TESTED |
| qwen2.5-3b-instruct-q4_k_m | lawyer_pt.txt | structured | 1 | 3 | 3 | 1 | 0/4 | 0.0000 | 4376.7 | DEVICE_TESTED |
| qwen2.5-7b-instruct-q4_k_m | lawyer_pt.txt | text | 0 | 4 | 2 | 1 | 0/4 | 0.0000 | 17924.4 | DEVICE_TESTED |
| qwen2.5-7b-instruct-q4_k_m | lawyer_pt.txt | text | 1 | 4 | 2 | 1 | 0/4 | 0.0000 | 17246.5 | DEVICE_TESTED |
| qwen2.5-7b-instruct-q4_k_m | lawyer_pt.txt | structured | 0 | 4 | 2 | 1 | 1/4 | 0.2500 | 52916.1 | DEVICE_TESTED |
| qwen2.5-7b-instruct-q4_k_m | lawyer_pt.txt | structured | 1 | 4 | 2 | 1 | 1/4 | 0.2500 | 51890.6 | DEVICE_TESTED |
| qwen2.5-3b-instruct-q4_k_m | lawyer_pt_2.txt | text | 0 | 2 | 0 | 0 | 2/4 | 0.5000 | 1030.4 | DEVICE_TESTED |
| qwen2.5-3b-instruct-q4_k_m | lawyer_pt_2.txt | text | 1 | 2 | 0 | 0 | 2/4 | 0.5000 | 726.3 | DEVICE_TESTED |
| qwen2.5-3b-instruct-q4_k_m | lawyer_pt_2.txt | structured | 0 | 2 | 0 | 0 | 2/4 | 0.5000 | 2156.8 | DEVICE_TESTED |
| qwen2.5-3b-instruct-q4_k_m | lawyer_pt_2.txt | structured | 1 | 2 | 0 | 0 | 2/4 | 0.5000 | 2134.5 | DEVICE_TESTED |
| qwen2.5-7b-instruct-q4_k_m | lawyer_pt_2.txt | text | 0 | 6 | 0 | 0 | 3/4 | 0.7500 | 12149.4 | DEVICE_TESTED |
| qwen2.5-7b-instruct-q4_k_m | lawyer_pt_2.txt | text | 1 | 6 | 0 | 0 | 3/4 | 0.7500 | 11516.3 | DEVICE_TESTED |
| qwen2.5-7b-instruct-q4_k_m | lawyer_pt_2.txt | structured | 0 | 2 | 0 | 0 | 1/4 | 0.2500 | 10897.4 | DEVICE_TESTED |
| qwen2.5-7b-instruct-q4_k_m | lawyer_pt_2.txt | structured | 1 | 2 | 0 | 0 | 1/4 | 0.2500 | 10107.8 | DEVICE_TESTED |
| qwen2.5-3b-instruct-q4_k_m | lawyer_en.txt | text | 0 | 3 | 0 | 0 | 1/4 | 0.2500 | 894.6 | DEVICE_TESTED |
| qwen2.5-3b-instruct-q4_k_m | lawyer_en.txt | text | 1 | 3 | 0 | 0 | 1/4 | 0.2500 | 557.4 | DEVICE_TESTED |
| qwen2.5-3b-instruct-q4_k_m | lawyer_en.txt | structured | 0 | 6 | 0 | 0 | 3/4 | 0.7500 | 4064.7 | DEVICE_TESTED |
| qwen2.5-3b-instruct-q4_k_m | lawyer_en.txt | structured | 1 | 6 | 0 | 0 | 3/4 | 0.7500 | 3919.6 | DEVICE_TESTED |
| qwen2.5-7b-instruct-q4_k_m | lawyer_en.txt | text | 0 | 3 | 0 | 0 | 2/4 | 0.5000 | 6317.4 | DEVICE_TESTED |
| qwen2.5-7b-instruct-q4_k_m | lawyer_en.txt | text | 1 | 3 | 0 | 0 | 2/4 | 0.5000 | 5627.3 | DEVICE_TESTED |
| qwen2.5-7b-instruct-q4_k_m | lawyer_en.txt | structured | 0 | 1 | 0 | 0 | 1/4 | 0.2500 | 9240.2 | DEVICE_TESTED |
| qwen2.5-7b-instruct-q4_k_m | lawyer_en.txt | structured | 1 | 1 | 0 | 0 | 1/4 | 0.2500 | 8293.4 | DEVICE_TESTED |

## Means per model + mode

Formula: `mean(x) = sum(x_i) / n`  where n = number of successful rows used.

| model | mode | runs | n | mean_ratio | mean_violation_count | mean_latency_ms |
|---|---|---|---|---|---|---|
| qwen2.5-3b-instruct-q4_k_m | structured | 6 | 6 | 0.4167 | 1.0 | 3512.0 |
| qwen2.5-3b-instruct-q4_k_m | text | 6 | 6 | 0.25 | 1.0 | 1038.7 |
| qwen2.5-7b-instruct-q4_k_m | structured | 6 | 6 | 0.25 | 0.67 | 23890.9 |
| qwen2.5-7b-instruct-q4_k_m | text | 6 | 6 | 0.4167 | 0.67 | 11796.9 |
