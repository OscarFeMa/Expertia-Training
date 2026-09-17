---
license: cc-by-nc-4.0
language:
  - es
  - en
tags:
  - mathematics
  - physics
  - instruction-tuning
  - wikidata
---

# Expertia domain datasets (Math / Physics)

Instruction-tuning pairs (`system` / `instruction` / `input` / `output` + metadata)
used to train the Expertia house specialists.

- `expertia-math-puro.jsonl` — 45k train (+5k val): Wikidata entities with
  defining formulae (P2534), formal style.
- `expertia-physics-puro.jsonl` — 45k train (+5k val): 43k Wikidata definitional
  + SPARQL P2534/P274 formulae + StackExchange accepted answers + Wikipedia leads
  + PubChem compounds.
- `expertia-chemistry-puro.jsonl` — 45k train (+5k val): Wikidata definitional
  + PubChem + SPARQL P274 + Wikipedia + StackExchange.

Format per line: `{"system","instruction","input":"","output","metadata":{domain,qid,source_url,origin}}`.
Outputs capped at 2000 chars, garbage-filtered, deduplicated by QID.

License: CC-BY-NC-4.0 (derived in part from Wikidata CC0, Wikipedia CC BY-SA,
StackExchange CC BY-SA, PubChem public data — check upstream terms for your use).
