# Context Limits: the 262K Ceiling, the q4_0 Breakthrough, and the YaRN Truth

> Three corrections discovered 2026-09-14/15 — **read this before trying to exceed 262K**.
> TL;DR: the real ceiling is 262,144 · q4_0 KV makes it *faster* than q8_0 · YaRN unlocks 1M but runs at 3-5 tok/s in llama.cpp.

---

## 1. The real ceiling is 262,144 — whatever `-c` claims

llama.cpp **silently caps** any `-c` above the model's training context:

```
W srv load_model: the slot context (305152) exceeds the training context of the model (262144) - capping
```

**Why it's easy to miss**: short prompts never hit the cap, so everything looks fine. Only a prompt longer than the cap reveals the truth:

```
E srv send_error: task id = 0, error: request (368270 tokens) exceeds the available context size (262144 tokens)
```

**Verification method (important)**: always test with a prompt **longer than the expected ceiling**. Our earlier "300K/400K/440K works!" results were all artifacts — the service was really running 262K, and the short test prompts could not expose it.

**Deliberately raising the cap** (advanced):
```powershell
--override-kv qwen35.context_length=int:1048576
```
(`qwen35` is this model's architecture key in the GGUF metadata, verified by inspecting the file: `general.architecture = qwen35`. MoE variants use `qwen35moe`.)

---

## 2. q4_0 KV: a genuinely free doubling (and q8_0 cannot reach 262K at all)

Same context (262,144), same model, K and V quantized identically:

| KV type | decode | VRAM free |
|---|---|---|
| q8_0 | **9.1 tok/s** ❌ | 515 MB |
| **q4_0** | **87–91 tok/s** ✅ | 1017 MB |

- **q8_0 starts fine at 262K but collapses** — this is why the q8_0-era ceiling looked like ~190K
- **q4_0 is the only way to make 262K practical**
- **Quality is lossless in our test**: needle-in-haystack (12K document, unique code buried at 60% depth) — **q4_0 and q8_0 both HIT**, with identical prefill speed

> Historical note: an early "q4_0 is 28× slower" result was a **mixed-type artifact** (`K=q8_0 + V=q4_0`) on a different model. **Full q4_0 has no such problem.**

---

## 3. YaRN can reach 1M — but llama.cpp's implementation is unusable

Correct invocation requires **two easily-missed flags**:

```powershell
--override-kv qwen35.context_length=int:1048576      # unlock the GGUF metadata cap
--rope-scaling yarn --rope-scale 4.0 --yarn-orig-ctx 262144
```

Measured (all with the full flag set):

| Config | Actual `n_ctx_slot` | decode | Cap warning |
|---|---|---|---|
| 262K (no YaRN) | 262144 | **87.2** ✅ | — |
| 512K + YaRN | **524288** ✅ unlocked | **3.1** ❌ | none |
| 1M + YaRN | **1048576** ✅ unlocked | **4.7** ❌ | none |

**The unlock works; the performance does not.** Root cause: llama.cpp's RoPE-scaling path beyond the native context is not optimized — the model runs, but each token takes hundreds of milliseconds.

---

## 4. Official position (Qwen / Alibaba Cloud guide)

The supported YaRN frameworks are **vLLM, SGLang, TokenSpeed** — **llama.cpp is not on the list**. The official guide also warns:

> "All the notable open-source frameworks implement **static YaRN** — the scaling factor remains constant regardless of input length, which can **hurt performance on shorter texts**. Only enable YaRN when you actually need long contexts. If your typical context is ~524,288 tokens, set factor to **2.0** instead of 4.0."

And a Thor + llama.cpp deployment guide acknowledges the same reality:
> "Prefilling 1M tokens under llama.cpp is extremely slow (minutes); it only suits a *load-once, ask-repeatedly* library scenario."

---

## 5. Engine comparison: why llama.cpp wins on a 24GB laptop

| | **llama.cpp (GGUF)** | **vLLM / SGLang (safetensors)** |
|---|---|---|
| NVFP4 hardware acceleration | ✅ | ✅ (ModelOpt, more "official") |
| Model file size | **14.47 GB** | 21–23 GB |
| KV cache precision | **q4_0 (~13 KB/token)** | FP8 (~19 KB/token) |
| 262K context on 24GB | ✅ **87 tok/s measured** | ❌ official docs require 32GB |
| Windows native | ✅ | ❌ WSL2/Docker required |
| First start | 7 s | JIT compile (minutes) |

**Quantization scheme difference**: the GGUF build quantizes MLP, attention, **and the vision/MTP heads**; the ModelOpt safetensors recipe keeps vision/MTP in BF16 — hence the 6–9 GB difference.

**Conclusion**: both engines support NVFP4 acceleration. On this hardware the blocker for vLLM is **VRAM**, not quantization — so **llama.cpp + GGUF + q4_0 KV remains the optimal configuration for 24 GB**.

---

## 6. Practical summary

| Goal | Solution | Speed |
|---|---|---|
| Daily use, big context | **262K + q4_0 KV** | **82 tok/s** (29.5 at full load) |
| Long-material Q&A | 262K (prefill 45K ≈ 31 s) | 49 tok/s after prefill |
| True 1M | YaRN in llama.cpp | 4–5 tok/s — batch/library use only |
| Fast 1M | switch to vLLM — needs **32GB+** | — |
