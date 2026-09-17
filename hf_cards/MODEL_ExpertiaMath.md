---
license: cc-by-nc-4.0
language:
  - es
  - en
tags:
  - mathematics
  - reasoning
  - qlora
  - gguf
base_model: microsoft/Phi-4-mini-reasoning
---

# ExpertiaMath (Q4_K_M)

Spanish-first mathematics specialist: formal definitions + formulae, no web opinion.
Fine-tuned from `microsoft/Phi-4-mini-reasoning` (MIT) with QLoRA r16 on 45k
Wikidata-derived definition/formula pairs (+5k validation), 3 epochs on RTX 3070.

## Evaluation (500 held-out samples)

|  | Perplexity |
|---|---|
| Base | 827.1 |
| + adapter | 63.8 (-92.3%) |

Production: 0.89 quality, 100% cycle success, ~310 pkgs/cycle in the Expertia pipeline.

## Variants in this repo

| File | Size | Needs | Use |
|---|---|---|---|
| `expertia-math-q4_k_m.gguf` | 2.5GB | 6GB VRAM | Daily inference (Ollama) |
| `expertia-math-f16.gguf` | 7.7GB | 16GB VRAM | Max quality inference |
| `fp16/` | 7.2GB | — | Base for further fine-tuning |

## Usage (Ollama)

```
ollama create ExpertiaMath -f Modelfile-ExpertiaMath-Q4
```

Note: GGUF uses `gpt-2` pre-tokenizer (Ollama ≤0.33.3 does not know `phi-3`);
set `num_ctx 8192` (Qwen-family 256K default loads 43GB otherwise).

## Limitations

Narrow domain specialist (mathematics). Not a general assistant.
Adapter weights: CC-BY-NC-4.0. Base model: MIT (Microsoft).
