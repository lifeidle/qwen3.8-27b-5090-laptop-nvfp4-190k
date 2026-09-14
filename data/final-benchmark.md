# Final Benchmark — Production Config (2026-09-15)

## Configuration

| Item | Value |
|---|---|
| Model | `Qwen3.8-27B-NVFP4-MTP-LOW` (14.47 GiB) |
| Engine | self-built llama.cpp (CUDA 13.3 + master + patch) |
| Context | **262,144** — the model's training ceiling |
| KV cache | **q4_0** (K and V) |
| Slots | 1 (`-np 1`) |
| MTP | `--spec-type draft-mtp --spec-draft-n-max 3` |
| Vision | `mmproj-Q8_0` (enabled) |
| Reasoning | `xhigh` + `--reasoning-budget 12000` + template injection |
| Sampling | temp 1.0 / top-p 0.95 / top-k 20 / min-p 0.0 |

## A. Generation stability — 8 consecutive 512-token runs

| Run | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| tok/s | 79.0 | 81.6 | 84.6 | 82.0 | 90.1 | 81.5 | 83.7 | 81.1 |

**median 81.8 · mean 83.0 · min 79.0 · max 90.1 · stdev 3.3** (±4%)

## B. Time to first token (TTFT) vs prompt size

| Prompt | Tokens | **TTFT** | Prefill speed | Decode |
|---|---|---|---|---|
| short question | 89 | **167 ms** | 534 tok/s | 66.0 tok/s |
| medium document | 5,535 | **2.78 s** | 1,992 tok/s | 64.4 tok/s |
| long document | 45,143 | **30.97 s** | 1,458 tok/s | 49.1 tok/s |

## C. Vision latency (3 runs, all correct)

| Run | 1 | 2 | 3 | Median |
|---|---|---|---|---|
| seconds | 4.1 | 2.4 | 2.9 | **2.9 s** |

## D. Loaded context (137,944 tokens)

| Metric | Value |
|---|---|
| Prefill time | **185.7 s** (743 tok/s) |
| **Generation at full load** | **29.5 tok/s** (median of 3) |
| TTFT with prompt cache hit | ~2.2 s |

> Context length directly costs generation speed: the attention must read the whole KV cache every step.
> Empty 82 tok/s → 137K loaded 29.5 tok/s.

## VRAM

| State | Free VRAM |
|---|---|
| idle (after load) | 551 MB |
| after all tests | 749 MB |
| Model load time | 6.6 s (warm page cache) |

## Reproduce

```powershell
& "D:\llama.cpp\build\bin\llama-server.exe" `
  -m "D:\models\Qwen3.8-27B\Qwen3.8-27B-NVFP4-MTP-LOW.gguf" `
  --mmproj "D:\models\Qwen3.8-27B\mmproj-Q8_0.gguf" `
  -ngl 99 -fa on -fit off -np 1 -c 262144 `
  --cache-type-k q4_0 --cache-type-v q4_0 --ctx-checkpoints 4 `
  --spec-type draft-mtp --spec-draft-n-max 3 `
  --reasoning-effort xhigh --reasoning-budget 12000 `
  --chat-template-file "D:\models\Qwen3.8-27B\custom_template.jinja" `
  --temp 1.0 --top-p 0.95 --top-k 20 --min-p 0.0 `
  --host 127.0.0.1 --port 8082 --load-mode none --jinja
```
