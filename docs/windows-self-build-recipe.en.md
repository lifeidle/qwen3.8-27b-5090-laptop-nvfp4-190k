# Windows Self-Build Recipe (CUDA 13.3 + MSVC + Blackwell/sm_120)

> Battle-tested end-to-end in 2026-09. Goal: build llama.cpp from source with performance **≥ official builds**.
> Measured on RTX 5090 Laptop 24GB running Qwen3.8-27B NVFP4: the self-built engine achieves **decode 80–87 tok/s · prefill 1675 tok/s · vision 4.2 s** — the best of all builds tested.
> Related upstream issue (found an nvcc 12.8 performance bug): [ggml-org/llama.cpp#28790](https://github.com/ggml-org/llama.cpp/issues/28790)

## 1. Toolchain (★ hard requirements)

| Component | Version | Note |
|---|---|---|
| MSVC | **19.44** (VS 2022 17.14 BuildTools) | same as official Windows builds |
| **CUDA Toolkit** | **13.3.33** | ★★ must pair with MSVC 19.44 (the official pairing) |
| CMake | 4.4+ | |
| Ninja | 1.13+ | do NOT use the VS generator (CUDA integration often missing) |

### ⚠️ The most important pitfall: nvcc 12.8 + MSVC 19.44 = performance disaster

Measured (same model, same args, same machine):

| Toolchain | prefill (MTP on) | Verdict |
|---|---|---|
| nvcc 12.8 + MSVC 19.44 (forced with `-allow-unsupported-compiler`) | **32.7 tok/s** | ❌ 57× slower |
| nvcc 13.3 + MSVC 19.44 (official pairing) | **1675.7 tok/s** | ✅ normal |

- CUDA 12.8 officially does **not** support MSVC 19.44 → the force-built CUDA kernels have a broken **MTP prefill** path
- **Only prefill is affected** (decode stays healthy) → extremely hard to notice
- Full DLL-swap bisection in issue #28790

### ⚠️ CUDA 13's new directory layout

**CUDA 13.x moved its runtime DLLs to `bin\x64\`** (previously `bin\`; `bin\` now holds only tools):

```
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\x64\
    ├── cudart64_13.dll      (0.5 MB)
    ├── cublas64_13.dll      (49.5 MB)
    └── cublasLt64_13.dll    (439 MB)
```

**With `-DGGML_BACKEND_DL=ON`** (dynamic backend loading — the official config): if these 3 DLLs are not findable at runtime, `ggml-cuda.dll` fails to load **silently** → inference falls back to CPU (~3 tok/s, CPU pegged, GPU idle).

**Fix**: copy those 3 DLLs next to `llama-server.exe`.

## 2. Build commands (complete)

```powershell
# 1. Clone (or your branch/patched tree)
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

# 2. Configure (Ninja + MSVC + CUDA 13.3 + sm_120)
cmake -G Ninja -B build `
  -DCMAKE_BUILD_TYPE=Release `
  -DGGML_CUDA=ON `
  -DCMAKE_CUDA_ARCHITECTURES=120 `
  -DGGML_CUDA_FA_QUANTS=all `
  -DGGML_BACKEND_DL=ON `
  -DGGML_CPU_ALL_VARIANTS=ON `
  -DGGML_NATIVE=OFF `
  -DCMAKE_DISABLE_PRECOMPILE_HEADERS=ON `
  -DCMAKE_CUDA_COMPILER="C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\nvcc.exe"

# 3. Build
cmake --build build -j 8

# 4. Add CUDA runtime DLLs (★ critical step)
$bin = "build\bin"
$cu  = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\x64"
Copy-Item "$cu\cudart64_13.dll","$cu\cublas64_13.dll","$cu\cublasLt64_13.dll" $bin
```

**Verify** (should show double-digit tok/s, not single digits):

```powershell
.\build\bin\llama-server.exe -m your-model.gguf -ngl 99 -fa on -c 4096 --port 8080
curl.exe -X POST http://127.0.0.1:8080/completion -H "Content-Type: application/json" -d "{\"prompt\":\"hi\",\"n_predict\":64}"
# → timings.predicted_per_second should be 70-90
```

## 3. Four pitfalls and fixes (in the order we hit them)

| # | Pitfall | Symptom | Fix |
|---|---|---|---|
| 1 | Duplicate `Path`/`PATH` env keys | MSBuild crash: `ArgumentException: Item has already been added` | call CMake from a clean Python subprocess env (merge duplicate keys) |
| 2 | Do not use the VS generator | `No CUDA toolset found` | use Ninja |
| 3 | **PCH breaks DLL linking** | `exports.def : error LNK2001: unresolved external symbol __` | `-DCMAKE_DISABLE_PRECOMPILE_HEADERS=ON` |
| 4 | **CUDA 13 layout + DL mode: silent CPU fallback** | 3 tok/s, CPU pegged, GPU ~7% | copy the 3 DLLs next to the binary |

## 4. Performance baseline (RTX 5090 Laptop 24GB + Qwen3.8-27B NVFP4-LOW)

| Build | decode | prefill 4K | vision |
|---|---|---|---|
| official b10889 | 51.7 | 1482 | 6.1 s |
| official b10917 | 50.3 | 1344.9 | — |
| **self-built (nvcc 13.3 + official config)** | **80–87** | **1675.7** | **4.2 s** |

Run args: `-ngl 99 -fa on -c 180000 -np 1 --cache-type-k q8_0 --cache-type-v q8_0 --ctx-checkpoints 4 --spec-type draft-mtp --spec-draft-n-max 3 --load-mode none --jinja`
