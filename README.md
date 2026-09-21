# 🧠 Expertia-Training — el criadero de especialistas

> *Un experto no se programa. Se destila, se evalúa, se somete a canario y,
> solo entonces, se libera.*

Este repo es la **sala de máquinas** del archivo sináptico Expertia: aquí los
18 especialistas dejan de ser prompts genéricos y se convierten en modelos
propios — QLoRA r16 sobre `microsoft/Phi-4-mini-reasoning`, entrenados en una
RTX 3070, evaluados contra su base y publicados con su card.

```
  mineral web en bruto                    especialista liberado
  (SE · Wiki · SPARQL · TI)               (GGUF Q4 + adapter r16)
           │                                        ▲
           ▼                                        │
     ┌───────────┐    ┌───────┐    ┌──────┐    ┌──────────┐    ┌────────┐
     │  HARVEST  │───▶│ BUILD │───▶│TRAIN │───▶│ MERGE +  │───▶│ CANARY │
     │ anclas de │    │45MB de│    │~26h  │    │EVAL+GGUF │    │10/10 o │
     │  calidad  │    │ pares │    │ 3070 │    │  en 3070 │    │ no sale│
     └───────────┘    └───────┘    └──────┘    └──────────┘    └────────┘
           │                                                │
           └──────── AUDITOR (juez-LLM) filtra ─────────────┘
```

## 🏆 Marcador real (perplejidad, 2000 muestras held-out, 17-sep-2026)

| Especialista | Base | + adapter | Mejora | Estado |
|---|---|---|---|---|
| Electronics | 1345.3 | **34.3** | −97.5% | ✅ liberado |
| Physics | 780.2 | **49.5** | −93.7% | ✅ liberado |
| Chemistry | 786.4 | **59.0** | −92.5% | ✅ liberado |
| Mathematics | 876.8 | **65.1** | −92.6% | ✅ liberado |
| SoftwareEngineering | — | — | — | 🥚 en harvest |

*Regla del criadero: si el adapter no baja la perplejidad >90% o el canario
falla, el modelo no sale. Sin excepciones.*

## 📦 Dónde vive cada cosa

| Qué | Dónde | En git |
|---|---|---|
| Tooling (este repo) | aquí | ✅ |
| Pesos Q4 + adapters | [HuggingFace](https://huggingface.co/OscarFeMa) (`Expertia*-Q4`, `*-r16`) | ❌ (50MB–8GB) |
| Datasets `*-puro.jsonl` | [expertia-domain-datasets](https://huggingface.co/datasets/OscarFeMa/expertia-domain-datasets) | ❌ (45MB c/u) |
| Checkpoints, logs, `merged/`, `base/` | solo disco | ❌ (ver `.gitignore`) |

Modelos verificados hoy:

| Q4 (Ollama diario) | Adapter r16 (re-entrenable) |
|---|---|
| [ExpertiaMath-Q4](https://huggingface.co/OscarFeMa/ExpertiaMath-Q4) | [ExpertiaMath-r16](https://huggingface.co/OscarFeMa/ExpertiaMath-r16) |
| [ExpertiaPhysics-Q4](https://huggingface.co/OscarFeMa/ExpertiaPhysics-Q4) | [ExpertiaPhysics-r16](https://huggingface.co/OscarFeMa/ExpertiaPhysics-r16) |
| [ExpertiaChemistry-Q4](https://huggingface.co/OscarFeMa/ExpertiaChemistry-Q4) | [ExpertiaChemistry-r16](https://huggingface.co/OscarFeMa/ExpertiaChemistry-r16) |
| [ExpertiaElectronics-Q4](https://huggingface.co/OscarFeMa/ExpertiaElectronics-Q4) | [ExpertiaElectronics-r16](https://huggingface.co/OscarFeMa/ExpertiaElectronics-r16) |

## 🔁 Criar un especialista (receta)

```powershell
# 1. Harvest (local, con key de StackApps para no sufrir throttle)
python datasets\harvest_se.py 60 1 stackoverflow TU_KEY
python datasets\harvest_wiki.py 12000 "Category:Software engineering" wiki_swe.jsonl

# 2. Auditor (3070, juez phi-4 8-bit, matable y reanudable)
#    -> C:\training\logs\audit_swe.jsonl  (umbral: score >= 6)

# 3. Build (~45MB, 90/10 train/val)
python datasets\build_expertia_swe_dataset.py

# 4. Train (3070, ~26h, reanudable desde checkpoint)
#    Start-Training-3070.ps1  (vigila Watch-Train.ps1)

# 5. Post (3070, ~1h): merge -> eval base/adapter -> GGUF f16 + Q4_K_M
#    Run-Merge-*.cmd, Run-Eval-*.cmd, Run-GGUF-*.cmd

# 6. Liberar: ollama create + canario 10/10 + upload_hf.py
ollama create expertia-swe -f Modelfile-ExpertiaSWE-Q4F
```

## ✅ Definition of Done (obligatoria antes de liberar)

1. Dataset ~45MB (90/10) → 2. entreno done → 3. eval: adapter <10% ppl base
2. merge + GGUF f16 + Q4 → **5. canario guionizado 10/10 (definición + fórmula + idioma del prompt)** → 6. `ollama create` + smoke → 7. registry + HF + card.
3. Sin puerta 5 en verde: HF queda `provisional` y el README no lo posiciona.

## ⚠️ Lecciones del canario 18-sep-2026 (10 prompts × 4 modelos, raw)

- Los adapters **regurgitan la plantilla de entrenamiento** (`Entity:/Properties:/Source:`) y a veces alucinan la entidad (Ohm→un cuadro). Causa: el `output` incluye el `structured_knowledge` crudo con su scaffolding.
- **Fix para SWE**: limpiar el sk a texto definicional plano antes del build (quitar prefijos `Entity:/Description:/Properties:`, conservar valores). No entrenar nunca con el template.
- Responden en inglés a prompts españoles sin system prompt: el canario de liberación se hace **vía Ollama (con SYSTEM + think:false)**, el raw es solo diagnóstico.
- Veredicto electronics: **provisional** (vale para destilación con SYSTEM+think:false; no para chat directo).

## 🐤 El canario

Todo modelo recién creado responde 10 preguntas fijas (definición + fórmula +
parámetros). Ejemplo real del 17-sep:

> **Q:** *Ley de Ohm: fórmula y parámetros.*
> **expertia-electronics:** *I = V/R, donde I es la corriente en amperios,
> V la diferencia de potencial en voltios y R la resistencia en ohmios.*

Si responde en otro idioma, divaga u opina → no se libera.

## 🔐 Secretos

Nada en claro en este repo, por diseño. Antes de operar:

```powershell
[Environment]::SetEnvironmentVariable("EXPERTIA_3070_PASS", "<pass>", "User")
$env:HF_TOKEN = "<token>"   # solo para upload_hf.py
```

`Acceso expertia.*`, `enable-remote-3070.ps1` e `incoming_3070/` son
solo-locales y están en `.gitignore`. Si ves un password en un diff,
el commit no sale. Así de simple.

## 🗺️ Mapa rápido

- `train_expertia.py` — el entrenador (QLoRA r16, sirve para todos).
- `datasets/` — harvesters + builders por dominio.
- `merge_expertia_*.py` — fusión adapter→fp16.
- `Run-*.cmd` — cadena post-entreno en el 3070 (merge/eval/gguf).
- `Modelfile-*` — recetas Ollama (`repeat_penalty 1.1`, `num_ctx 8192`).
- `hf_cards/` — cards + `upload_hf.py`.
- `audit_qwen3/` — auditorías de calidad históricas.
- `audit_swe.py` — el juez (corre en el 3070).

---
*Cuatro especialistas liberados. Catorce por criar. El siguiente ya está en el
cascarón: SoftwareEngineering.* 🥚
