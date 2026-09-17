# Expertia-Training

Finetuning QLoRA r16 de especialistas Expertia sobre `microsoft/Phi-4-mini-reasoning`
(RTX 3070, seq 1024, BF16, 3 épocas). Modelos y datasets publicados en HuggingFace
(`OscarFeMa/Expertia*-Q4`, `*-r16`, `expertia-domain-datasets`).

## Pipeline por experto

1. **Harvest** (`datasets/harvest_*.py`): StackExchange API (requiere key),
   Wikipedia categories, SPARQL/Wikidata, fuentes de dominio (PubChem, TI).
2. **Build** (`datasets/build_expertia_*_dataset.py`): pares definicionales
   + bulk Wikidata → `expertia-<dom>-puro.jsonl` (90/10 train/val, ~45MB).
3. **Train** (3070): `train_expertia_math.py` → `adapters/expertia-<dom>-r16`
   (lanzar con `Start-Training-3070.ps1`; vigila `Watch-Train.ps1`).
4. **Post** (3070): `Run-Merge-*.cmd` → fp16, `Run-Eval-*.cmd` → ppl base/adapter,
   `Run-GGUF-*.cmd` → f16 + Q4_K_M. Transfer con `auto_post_<dom>.ps1`.
5. **Publish**: `ollama create` con `Modelfile-*` + `hf_cards/upload_hf.py`.

## Secretos

Nada en claro en este repo. Define antes de operar:

```powershell
[Environment]::SetEnvironmentVariable("EXPERTIA_3070_PASS", "<pass-3070>", "User")
$env:HF_TOKEN = "<hf-token>"; $env:HF_USER = "OscarFeMa"  # solo para upload
```

Ficheros con credenciales (`Acceso expertia.*`, `enable-remote-3070.ps1`,
`incoming_3070/cred.xml`) son solo-locales y están en `.gitignore`.

## Estado (2026-09-17)

Entrenados: math (827→64), physics (742→49), chemistry (823→60),
electronics (1469→36, ppl en 500 val). Siguiente: SoftwareEngineering
(harvest en curso: StackOverflow + softwareengineering.se + codereview + wiki).
