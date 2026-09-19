---
license: cc-by-nc-4.0
language:
  - es
  - en
tags:
  - software-engineering
  - reasoning
  - qlora
  - gguf
base_model: microsoft/Phi-4-mini-reasoning
---

# ExpertiaSWE (Q4_K_M)

Spanish-first software engineering specialist: formal definitions + parameters + minimal examples.
Fine-tuned from `microsoft/Phi-4-mini-reasoning` (MIT) with QLoRA r16 on ~45k pairs
(StackOverflow + softwareengineering.se + codereview.se + Wikipedia + Wikidata definitional bulk),
3 epochs on RTX 3070 (seq1024, BF16). `structured_knowledge` was cleaned of the
`Entity:/Properties:/P-code` scaffolding before training (anti-regurgitation).

## Evaluation (500 held-out samples)

|  | Perplexity |
|---|---|
| Base | 14892.9 |
| + adapter | 63.7 (-99.6%) |

Canary (10 fixed prompts via Ollama): 10/10 correct definitions, 0 template
regurgitations. Note: answers in English to Spanish prompts (shared with sibling
specialists) — production use is distillation with SYSTEM + `think:false`, not chat.

## Variants in this repo

| File | Size | Needs | Use |
|---|---|---|---|
| `expertia-swe-q4_k_m.gguf` | 2.4GB | 6GB VRAM | Daily inference (Ollama) |
| `expertia-swe-f16.gguf` | 7.3GB | 16GB VRAM | Max quality inference |
| `fp16/` | ~7GB | — | Base for further fine-tuning |

## Usage (Ollama)

```
ollama create expertia-swe -f Modelfile-ExpertiaSWE-Q4F
```

Note: GGUF uses `gpt-2` pre-tokenizer; set `num_ctx 8192`.

## Limitations

Narrow domain specialist (software engineering). Adapter weights: CC-BY-NC-4.0. Base: MIT.
