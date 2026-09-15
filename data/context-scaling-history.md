# Context Scaling History — How the Ceiling Moved from 88K to 262K

> A complete, honest record of every context-length conclusion we reached — **including the three that turned out to be wrong**.
> Useful if you're trying to squeeze long context out of a 24 GB card: you'll likely hit the same measurement traps.

---

## Timeline

| Date | Claim | Measured | Status |
|---|---|---|---|
| 09-10 | max ~88K (NVFP4 MID-HIGH) | 88K @ 37 tok/s | superseded |
| 09-11 | **212K** with q8_0 KV (IQ3_S model) | 212K, 15.0 s long-input | superseded (model changed) |
| 09-13 | **150K sweet spot** — "152K collapses to 63.6" | 150K = 86.2 | ❌ **WRONG** |
| 09-13 | **180K ceiling** — "150–180K is flat" | 180K = 80.2 | ❌ **WRONG** |
| 09-14 | **300K–440K possible with q4_0** | 300K = 85.2 | ❌ **WRONG** |
| 09-15 | **262,144 is the hard ceiling** | 262,144 = 91.2 | ✅ **CONFIRMED** |

---

## Trap #1 — measuring with the wrong slot configuration

**Claim**: "past 152K the model collapses (63.6 tok/s at 152K)".

**What actually happened**: the sweep ran without explicitly setting `-np`, so llama.cpp used its
default (4 slots). With 4 slots the same context needs ~1 GB more VRAM, leaving the card starved.
The "collapse" was a **VRAM-pressure artifact**, not a context-length effect.

**Re-measured with `-np 1`**:

| Context | decode | VRAM free |
|---|---|---|
| 150K | 81.4 | 1314 MB |
| 152K | 82.0 | 1224 MB |
| 155K | 86.8 | 1096 MB |
| 170K | 85.7 | 567 MB |
| 180K | 83.9 | 545 MB |

**Lesson**: always sweep with your *production* configuration. `-np 1` frees ~1.15 GB here.

---

## Trap #2 — the curve is not monotonic

Between 180K and 192K the curve oscillates:

| Context | 182K | 184K | 186K | 188K | 190K | 192K |
|---|---|---|---|---|---|---|
| decode | **59.2** ↓ | 61.0 | 62.2 | 81.2 | **86.7** | 63.1 |

182–186K sags, 188–190K recovers, 192K sags again — likely KV/compute-buffer allocation alignment.
**You cannot interpolate this curve. You must measure the exact length you plan to use.**

---

## Trap #3 — the ceiling that lies (the big one)

The "300K / 400K / 440K works!" results were **all artifacts**. llama.cpp silently caps `-c` at the
model's training context and only prints a warning nobody reads:

```
W srv load_model: the slot context (305152) exceeds the training context of the model (262144) - capping
```

Short test prompts never hit the cap, so everything looked fine. The truth only surfaced when a
**368,270-token prompt** was rejected:

```
E srv send_error: request (368270 tokens) exceeds the available context size (262144 tokens)
```

**Verification rule**: to test a context ceiling, send a prompt **longer than the claimed ceiling**.

---

## The q4_0 KV breakthrough

The real ceiling is 262,144 — but reaching it requires q4_0 KV:

| KV type | decode @ 262K | VRAM free |
|---|---|---|
| q8_0 | **9.1 tok/s** ❌ | 515 MB |
| **q4_0** | **87–91 tok/s** ✅ | 1017 MB |

q8_0 *starts* at 262K but collapses (this is why the q8_0-era "ceiling" looked like ~190K).
q4_0 is not a quality trade: a needle-in-haystack recall test (12K document, unique code at 60 %
depth) **passed identically for both**, with equal prefill speed.

> Historical note: an early "q4_0 is 28× slower" result was a **mixed-type artifact**
> (`K=q8_0 + V=q4_0`) on a different model. Full q4_0 has no such problem.

---

## Going beyond 262K: YaRN

Possible, and the unlock is real — but performance is not:

| Config | Actual `n_ctx_slot` | decode |
|---|---|---|
| 262K (no YaRN) | 262144 | **87.2** ✅ |
| 512K + YaRN 2× | 524288 (unlocked) | **3.1** ❌ |
| 1M + YaRN 4× | 1048576 (unlocked) | **4.7** ❌ |

Unlocking requires two easily-missed flags:
```powershell
--override-kv qwen35.context_length=int:1048576
--rope-scaling yarn --rope-scale 4.0 --yarn-orig-ctx 262144
```

Even with the correct flags the speed is 3–5 tok/s — llama.cpp's RoPE-scaling path beyond the native
context is unoptimized. Qwen's own guide lists **vLLM / SGLang / TokenSpeed** as the supported YaRN
frameworks; llama.cpp is not among them. See [../docs/context-limits-and-yarn.md](../docs/context-limits-and-yarn.md).

---

## Final answer

**262,144 tokens with q4_0 KV**, verified at 81.8 tok/s (median of 8 runs).

| Scenario | Speed |
|---|---|
| Idle, short prompt | 81.8 tok/s · TTFT 0.17 s |
| 4K prompt | 64.4 tok/s · TTFT 2.78 s |
| 45K prompt | 49.1 tok/s · TTFT 30.97 s |
| 137,944 tokens loaded | 29.5 tok/s |

Context length is not free: every generated token must attend over the entire KV cache.
