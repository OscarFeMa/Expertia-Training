---
license: cc-by-nc-4.0
language:
  - es
  - en
tags:
  - electronics
  - reasoning
  - qlora
  - gguf
base_model: microsoft/Phi-4-mini-reasoning
---

# ExpertiaElectronics (Q4_K_M)

Spanish-first electronics specialist: formal definitions + parameters + formulae where applicable.
Fine-tuned from `microsoft/Phi-4-mini-reasoning` (MIT) with QLoRA r16 on 43MB
puro pairs (StackExchange + Wikipedia + TI/Sparql harvests), 3 epochs on RTX 3070 (seq1024, BF16).

## Evaluation (500 held-out samples)

|  | Perplexity |
|---|---|
| Base | 1469.4 |
| + adapter | 36.0 (-97.5%) |

## Variants in this repo

| File | Size | Needs | Use |
|---|---|---|---|
| `expertia-electronics-q4_k_m.gguf` | ~2.5GB | 6GB VRAM | Daily inference (Ollama) |
| `expertia-electronics-f16.gguf` | ~7.7GB | 16GB VRAM | Max quality inference |
| `fp16/` | ~7.2GB | — | Base for further fine-tuning |

## Usage (Ollama)

```
ollama create expertia-electronics -f Modelfile-ExpertiaElectronics-Q4F
```

Note: GGUF uses `gpt-2` pre-tokenizer; set `num_ctx 8192`.

## Limitations

Narrow domain specialist (electronics). Adapter weights: CC-BY-NC-4.0. Base: MIT.
