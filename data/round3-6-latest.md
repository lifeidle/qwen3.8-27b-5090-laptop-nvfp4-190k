# Rounds 3–6: Latest Results (2026-09-11 → 09-13)

> This file **supersedes earlier data** for engine / context / thinking-control questions.
> Full history: `speed-results.md` (rounds 1–2) and `round2-new-results.md`.
> All measurements: RTX 5090 Laptop 24GB · Windows 11 · Qwen3.8-27B-NVFP4-MTP-LOW.

---

## Round 3 — Thinking control (xhigh fixed)

Same runaway code prompt, xhigh, max_tokens 6000:

| Config | Time | finish | Thinking | Content |
|---|---|---|---|---|
| baseline (no control) | 93 s | length | 19,859 chars | **0** ❌ |
| **client system prompt** | **50 s** | **stop** | **10,708 (−46%)** | **1,286 chars** ✅ |
| server-side template injection | 77 s | stop | 18,499 | 1,180 chars ✅ |
| presence_penalty 1.0 | 99 s | length | 20,580 | 0 ❌ |
| 148K context | 92 s | length | 20,144 | 0 ❌ |
| froggeric v22.5 template | 93 s | length | 18,164 | 0 ❌ |

**Winner**: the system-prompt line (also built into the shipped chat template). The other four are excluded.

## Round 4 — Self-built engine (CUDA 13.3 pairing)

| Build | prefill 4K | decode | vision |
|---|---|---|---|
| official b10889 | 1482 | 51.7 | 6.1 s |
| official b10917 | 1344.9 | 50.3 | — |
| self-built, nvcc 12.8 | **32.7** ❌ | 77.1 | — |
| **self-built, nvcc 13.3** | **1675.7** | **80~87** | **4.2 s** |

Also: 23,112-token prompt processed at 1405 tok/s (16.9 s wall). Upstream bug: [ggml-org/llama.cpp#28790](https://github.com/ggml-org/llama.cpp/issues/28790).

## Round 5 — Context breakthrough (150K → 180K)

**Key correction**: the earlier "152K/160K collapse" was an artifact of the default `-np 4` config (only 158 MB VRAM free).

Production config (`-np 1` + template + budget), decode medians:

| Context | 150K | 152K | 155K | 158K | 160K | 170K | 180K | 192K |
|---|---|---|---|---|---|---|---|---|
| decode | 81.4 | 82.0 | 86.8 | 86.5 | 82.7 | 85.7 | **83.9** | 63.1 |
| VRAM free | 1314 | 1224 | 1096 | 956 | 881 | 567 | 545 | 472 |

**180K + vision verified**: decode 80.2 · prefill 1692 · vision 4.2 s · 531 MB free.

## Round 5b — Fine sweep inside 180–192K (non-monotonic!)

| Context | 182K | 184K | 186K | 188K | 190K |
|---|---|---|---|---|---|
| decode | **59.2** ↓ | 61.0 | 62.2 | 81.2 | **86.7** ↑ |

- **182–186K is an oscillation valley — avoid it.**
- **190K is the text-only optimum**, but **190K + a vision request collapses to 53.9 tok/s** → vision ceiling stays at 180K.

## Round 6 — Exhaustive parameter sweep (all rejected)

| Candidate | Result vs 180K baseline |
|---|---|
| `-np 2` | −1.5%, +95 MB VRAM |
| `--spec-draft-p-min 0.2` | +1.8% (noise) |
| `-b 512 -ub 512` | −1.4% |
| `--checkpoint-min-step 256` | −2.9% |
| `--kv-unified` | −4.2% |
| `--ctx-checkpoints 8` | −2.9% |
| `--spec-draft-n-max 4` | +0.1% |

Also re-confirmed (earlier rounds): `-ub 1024` (−16%), `--spec-default` (−39%), iMatrix mixed quant (−27%), `n-max 8` (−84%), q4_0 KV (−28× long-input), 148K (no change).

## Final recipe (shipped)

```
-p ng 99 -fa on -fit off -c 180000 -np 1
--cache-type-k q8_0 --cache-type-v q8_0 --ctx-checkpoints 4
--spec-type draft-mtp --spec-draft-n-max 3
--reasoning-effort xhigh --reasoning-budget 12000
--chat-template-file custom_template.jinja
--temp 1.0 --top-p 0.95 --top-k 20 --min-p 0.0
--load-mode none --jinja
```
