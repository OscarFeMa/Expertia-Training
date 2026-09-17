---
license: cc-by-nc-4.0
language:
  - es
  - en
tags:
  - chemistry
  - reasoning
  - qlora
  - gguf
base_model: microsoft/Phi-4-mini-reasoning
---

# ExpertiaChemistry (Q4_K_M)

Spanish-first chemistry specialist: formal definitions + formulae where applicable.
Fine-tuned from `microsoft/Phi-4-mini-reasoning` (MIT) with QLoRA r16 on 45k
pairs (Wikidata definitional bulk + SPARQL P274 formulae + PubChem compounds +
StackExchange accepted answers + Wikipedia leads), 3 epochs on RTX 3070
(seq1024, BF16).

## Evaluation (500 held-out samples)

|  | Perplexity |
|---|---|
| Base | 823.3 |
| + adapter | 60.1 (-92.7%) |

Production: 0.87 quality, 100% cycle success in the Expertia pipeline.

## Variants in this repo

| File | Size | Needs | Use |
|---|---|---|---|
| `expertia-chemistry-q4_k_m.gguf` | 2.5GB | 6GB VRAM | Daily inference (Ollama) |
| `expertia-chemistry-f16.gguf` | 7.7GB | 16GB VRAM | Max quality inference |
| `fp16/` | 7.2GB | — | Base for further fine-tuning |

## Usage (Ollama)

```
ollama create expertia-chemistry -f Modelfile-ExpertiaChemistry-Q4F
```

Note: GGUF uses `gpt-2` pre-tokenizer; set `num_ctx 8192`. Create with
lowercase name and real (non-junction) `FROM` path on Ollama ≥0.33.3.

## Limitations

Narrow domain specialist (chemistry). Adapter weights: CC-BY-NC-4.0. Base: MIT.
