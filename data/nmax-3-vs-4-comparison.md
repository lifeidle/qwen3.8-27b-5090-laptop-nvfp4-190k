# n-max 3 vs 4 — Rigorous Comparison (2026-09-15)

> **Why this file exists**: the initial MTP sweep reported `n-max 3 = 83.1` vs `n-max 4 = 81.0 tok/s`,
> but n-max 4's individual runs were `77.2 / 99.3 / 81.0` — the gap was **inside the noise**.
> Declaring a winner from that was not defensible. So we re-ran it properly.

---

## Method

| Aspect | Detail |
|---|---|
| Design | **Interleaved ABABAB** (6 blocks: 3,4,3,4,3,4) — cancels thermal/time drift |
| Samples | **15 per config** (5 runs × 3 blocks), 5 different prompts cycled |
| Config | 256K context · q4_0 KV · vision ON · self-built CUDA 13.3 |
| Metrics | decode tok/s **and** MTP draft acceptance rate (per run) |
| Second experiment | Same comparison under **loaded context** (122,920 tokens) |

---

## Results — idle (15 samples each)

| Metric | **n-max 3** | n-max 4 |
|---|---|---|
| Mean | 79.93 | **82.45** |
| Median | 77.6 | 78.9 |
| **Std dev** | **4.74** | 9.01 |
| Min–Max | 74.0–89.1 | 69.1–100.8 |
| **Acceptance rate** | **69.3%** | 61.3% |

Raw (n-max 3): 83.1 79.8 89.1 74.0 84.8 76.5 81.4 86.6 75.6 84.9 77.4 74.9 75.8 77.5 77.6
Raw (n-max 4): 81.2 69.1 90.1 78.9 75.8 77.3 77.6 91.3 75.2 91.4 82.9 72.7 100.8 78.5 94.0

## Results — loaded (122,920 tokens in context)

| Metric | n-max 3 | n-max 4 |
|---|---|---|
| Mean (valid runs) | 41.1 | **42.9** |
| Std dev | **~3.3** | ~4.8 |
| **Acceptance rate** | **67.5%** | 58.6% |

> Note: loaded-context generation is ~half the idle speed for both configs — the attention must
> read the entire KV cache on every step. This is the "full-load penalty", measured separately.

---

## Statistics

| Quantity | Value |
|---|---|
| Mean advantage of n-max 4 (idle) | **+3.2%** |
| Mean advantage of n-max 4 (loaded) | **+4.4%** |
| Effect size (Cohen's d, idle) | **0.37 → small** |
| Variance ratio (n-max 4 : n-max 3) | **≈ 2×** |

**Interpretation**: n-max 4 is *slightly* faster on average, but its distribution is "lottery-shaped" —
it hits highs like 100.8 tok/s and lows like 69.1 tok/s, while n-max 3 stays in a tight 74–89 band.
The acceptance rate also favours n-max 3 (69% vs 61%) — shallower drafts get verified more often.

---

## Decision: **keep n-max 3** (the shipped default)

| Criterion | Winner |
|---|---|
| Mean throughput | n-max 4 (+3–4%) |
| **Stability (std dev)** | **n-max 3 (2× better)** |
| **Draft acceptance / MTP efficiency** | **n-max 3** |
| VRAM footprint | n-max 3 (~73 MB better) |
| Statistical significance | tie (small effect) |

**Practical translation**: n-max 4 is ~3 seconds faster per 100 Chinese characters of output,
but stutters once every dozen or so completions. n-max 3 is marginally slower but consistently smooth.

**If you prefer average speed over smoothness**, change one number to `4`:
```
--spec-draft-n-max 4
```

---

## Also measured in the same session (single config, 9 variants)

| Variant | Median tok/s | vs n-max 3 |
|---|---|---|
| n-max 1 | 61.4 | −26% |
| n-max 2 | 77.4 | −7% |
| **n-max 3** | **83.1** | **baseline** |
| n-max 4 | 81.0 | −2.5% |
| n-max 5 | 77.9 | −6% |
| n-max 6 | 73.0 | −12% |
| n-max 3 + p-min 0.2 | 83.1 | 0% |
| n-max 3 + p-min 0.5 | 73.6 | −11% |
| **no MTP at all** | **39.6** | **−52%** |

**Key takeaway**: MTP is worth **+110%** (39.6 → 83.1). Everything else in this table is noise or worse.
