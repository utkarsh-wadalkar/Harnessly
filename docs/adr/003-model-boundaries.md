# ADR 003: Fixed inference roles and provider gates

Status: accepted configuration targets; live feasibility pending.

Decision: hosted Google AI Studio `gemma-4-26b-a4b-it` interviews developers. OpenCode and Aider compare the same hosted `Qwen3-Coder-30B-A3B-Instruct` endpoint. Official `laya-serve` provides only typed decisions on loopback port 8001, CPU-only with model caching and caps of 2 CPU/4 GiB.

Why: separating interview, coding and decision roles keeps measured performance distinct from preference inference.

Tradeoff: hosted providers require credentials, terms and budget validation; adapters may differ in capabilities. Local LAYA can fail or abstain, requiring an explicitly labeled fallback. No GPU or public LAYA service is needed.

Free-tier calls require verified eligibility and caps. Model names are targets, not availability claims. Requires tickets 03–05, 07–08.

