# xhigh 过度思考 / 循环问题 —— 实测有效的解决方案

> Qwen3.8-27B 在 xhigh 档有已知的"想太多停不下来"问题（官方 HF 讨论 #76 确认为 SSM 层结构缺陷，非设置问题）。本文是**实测验证**的修复方案（2026-09-13）。

## 🏆 有效方案：加一句系统提示词（思考量 -46%）

在请求的 `messages` 开头加：

```json
{
  "role": "system",
  "content": "Think through the problem once, then provide your answer. Do not repeatedly re-verify or second-guess yourself. Keep reasoning concise."
}
```

### 实测对比（同一道代码题 · xhigh · max_tokens 6000）

| 配置 | 耗时 | 思考量 | 正文 | 结束方式 |
|---|---|---|---|---|
| 无系统提示（基线）| 93 s | 19,859 字符 | **0** ❌ | length（撞上限）|
| **+ 系统提示词** | **50 s** | **10,708（−46%）** | **1,286 字符** ✅ | **stop（正常）** |

**效果**：思考减半、正文从零到正常输出、速度快一倍。

## 组合推荐（双保险）

| 层 | 措施 | 作用 |
|---|---|---|
| 客户端 | 系统提示词（上面那段）| 软引导（实测主力）|
| 服务端 | `--reasoning-budget 12000` | 硬止损（保险丝）|

客户端设置：WorkBuddy / Cherry Studio / LobeChat 等，在模型配置的"系统提示"里填上面那段即可。

## 已测试无效的方案（避免重复踩坑）

| 方案 | 实测结果 |
|---|---|
| `presence_penalty 1.0` | ❌ 思考反增（19,859 → 20,580 字符）|
| 148K 上下文（减显存压力）| ❌ 无变化（20,144 字符）|
| [froggeric v22.5 修复模板](https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates) | ❌ 无变化（18,164 字符）|

> froggeric 模板针对的是"KV cache 失效 / 长会话循环"，不是单题过度思考——但值得保留（对长 agent 会话可能有帮助）。

## 问题根因（为什么需要缓解）

| 层面 | 来源 | 说明 |
|---|---|---|
| 模型 | [HF 官方讨论 #76](https://huggingface.co/Qwen/Qwen3.8-27B/discussions/76) | SSM 层（blk.52-62）scale 偏移（α≈0.48-0.65）——"推理不在正确时间停止、token 5 倍消耗" |
| 引擎 | [llama.cpp #23577](https://github.com/ggml-org/llama.cpp/issues/23577)（32 条讨论）| Qwen3.x + MTP + 长会话 + 显存贴边 → 循环输出 |

**结论**：现象是"模型级缺陷 + 引擎触发条件"叠加；用上面的组合方案可以**缓解到日常可用**，根治需等官方模型更新。
