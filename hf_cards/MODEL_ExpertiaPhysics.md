---
license: cc-by-nc-4.0
language:
  - es
  - en
tags:
  - physics
  - reasoning
  - qlora
  - gguf
base_model: microsoft/Phi-4-mini-reasoning
---

# ExpertiaPhysics (Q4_K_M)

Spanish-first physics specialist: formal definitions + formulae where applicable.
Fine-tuned from `microsoft/Phi-4-mini-reasoning` (MIT) with QLoRA r16 on 45k
pairs (Wikidata definitional bulk + SPARQL P2534 formulae + StackExchange accepted
answers + Wikipedia leads + PubChem), 3 epochs on RTX 3070 (seq1024, BF16).

## Evaluation (500 held-out samples)

|  | Perplexity |
|---|---|
| Base | 741.8 |
| + adapter | 48.9 (-93.4%) |

Production: 0.90 quality, 100% cycle success in the Expertia pipeline.

## Variants in this repo

| File | Size | Needs | Use |
|---|---|---|---|
| `expertia-physics-q4_k_m.gguf` | 2.5GB | 6GB VRAM | Daily inference (Ollama) |
| `expertia-physics-f16.gguf` | 7.7GB | 16GB VRAM | Max quality inference |
| `fp16/` | 7.2GB | — | Base for further fine-tuning |

## Usage (Ollama)

```
ollama create expertia-physics -f Modelfile-ExpertiaPhysics-Q4F
```

Note: GGUF uses `gpt-2` pre-tokenizer; set `num_ctx 8192`.

## Limitations

Narrow domain specialist (physics). Adapter weights: CC-BY-NC-4.0. Base: MIT.
