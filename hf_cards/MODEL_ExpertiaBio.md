---
license: cc-by-nc-4.0
language:
  - es
  - en
tags:
  - biology
  - bioinformatics
  - reasoning
  - qlora
  - gguf
base_model: microsoft/Phi-4-mini-reasoning
---

# ExpertiaBio (Q4_K_M)

Spanish-first biology specialist: formal definitions + parameters + examples.
Fine-tuned from `microsoft/Phi-4-mini-reasoning` (MIT) with QLoRA r16 on ~53k pairs
(UniProt reviewed + PubMed abstracts + Wikipedia + Wikidata + GBIF taxonomy + StackExchange),
3 epochs on RTX 3070 (seq1024, BF16). `structured_knowledge` was cleaned of the
`Entity:/Properties:/P-code` scaffolding before training (anti-regurgitation).

## Evaluation (500 held-out samples)

|  | Perplexity |
|---|---|
| Base | 524.8 |
| + adapter | 10.0 (-98.1%) |

Canary (10 fixed prompts vía Ollama, 24-sep): pendiente.

## Variants in this repo

| File | Size | Needs | Use |
|---|---|---|---|
| `expertia-bio-q4_k_m.gguf` | 2.4GB | 6GB VRAM | Daily inference (Ollama) |
| `expertia-bio-f16.gguf` | 7.3GB | 16GB VRAM | Max quality inference |
| `fp16/` | ~7GB | — | Base for further fine-tuning |

## Usage (Ollama)

```
ollama create expertia-bio -f Modelfile-ExpertiaBio-Q4F
```

Note: GGUF uses `gpt-2` pre-tokenizer; set `num_ctx 8192`.

## Limitations

Narrow domain specialist (biology). Adapter weights: CC-BY-NC-4.0. Base: MIT.
