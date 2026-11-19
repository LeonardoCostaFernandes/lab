For an AI landing here: declare your reading depth (0-4) before parsing. Depth 0: this file. Depth 1: + README.md, STATE.md. Depth 2: + contracts/, bin/. Beyond declared depth is NO_DATA with cause.

# Agent contract · lab (LeonardoCostaFernandes)

Single canonical instruction set for every agent here (Claude Code, Junie, Grok, others). `CLAUDE.md` and `.junie/guidelines.md` point to this file and add no policy.

## Rules

- **Propose, never sign.** The owner (LeonardoCostaFernandes) signs PR by PR. Never merge, never push to `main`, never approve your own PR.
- Branch from current `origin/main`. Name: `<agent>/<task-id>-<slug>` (e.g. `junie/T-0005-bench-fix`). Open a draft PR titled `HITL: <summary>`.
- **Measured record.** Every number carries source, machine, date, command and scope. Vendor figures are labeled `DECLARED`. Missing = `NO_DATA(cause)`. Never invent, never silently omit.
- **No private data in Git.** No raw prompts, raw answers, credentials, tokens, device serials, internal IPs or personal data. Receipts hold counts, hashes and latencies.
- **Zero telemetry.** Benchmarks talk only to numeric loopback (`127.0.0.1` / `::1`). No model input, output or node state goes to an external service.
- **Status vocabulary:** `CODE_EXISTS`, `DEVICE_TESTED`, `PUBLIC_SERVICE_VERIFIED`, `NO_DATA(cause)`.
- **Prohibited vocabulary** (inherited from upstream): oracle, notary, depin, token (as currency), coin, clearing, magic.
- Yardstick: `python3 -m unittest discover -s tests -p "test_*.py"` twice, then `python3 bin/verify_structure.py`. Local runs are not remote CI.

## Coordination

Tasks are assigned in the owner's private mesa (`hilo/tasks/`). An agent works only on a task assigned to it, inside the task's declared paths.
