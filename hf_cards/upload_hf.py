"""Upload Expertia models + datasets to Hugging Face. Needs HF_TOKEN env + account.
Run: set HF_TOKEN=... && set HF_USER=... && python upload_hf.py
Nothing runs without a token (safe to keep; it only prepares)."""
import os
from pathlib import Path

TOKEN = os.environ.get("HF_TOKEN", "") or None
USER = os.environ.get("HF_USER", "") or "OscarFeMa"
DRY = False if (TOKEN or os.path.exists(os.path.expanduser("~/.cache/huggingface/token"))) else True
TRAIN = Path(r"F:\expertia\proyecto\training")

DISK = Path(r"F:\expertia\training-disk\merged")
MODELS = [
    ("ExpertiaMath-Q4", DISK / "expertia-math-q4_k_m.gguf", TRAIN / "hf_cards" / "MODEL_ExpertiaMath.md"),
    ("ExpertiaPhysics-Q4", DISK / "expertia-physics-q4_k_m.gguf", TRAIN / "hf_cards" / "MODEL_ExpertiaPhysics.md"),
    ("ExpertiaChemistry-Q4", DISK / "expertia-chemistry-q4_k_m.gguf", TRAIN / "hf_cards" / "MODEL_ExpertiaChemistry.md"),
    ("ExpertiaElectronics-Q4", DISK / "expertia-electronics-q4_k_m.gguf", TRAIN / "hf_cards" / "MODEL_ExpertiaElectronics.md"),
    ("ExpertiaSWE-Q4", DISK / "expertia-swe-q4_k_m.gguf", TRAIN / "hf_cards" / "MODEL_ExpertiaSWE.md"),
    ("ExpertiaDataScience-Q4", DISK / "expertia-datascience-q4_k_m.gguf", TRAIN / "hf_cards" / "MODEL_ExpertiaDataScience.md"),
    ("ExpertiaBio-Q4", DISK / "expertia-bio-q4_k_m.gguf", TRAIN / "hf_cards" / "MODEL_ExpertiaBio.md"),
]
ADAPTERS = [
    ("ExpertiaMath-r16", TRAIN / "adapters" / "expertia-math-r16",
     TRAIN / "hf_cards" / "MODEL_ExpertiaMath.md"),
    ("ExpertiaPhysics-r16", TRAIN / "adapters" / "expertia-physics-r16",
     TRAIN / "hf_cards" / "MODEL_ExpertiaPhysics.md"),
    ("ExpertiaChemistry-r16", TRAIN / "adapters" / "expertia-chemistry-r16",
     TRAIN / "hf_cards" / "MODEL_ExpertiaChemistry.md"),
    ("ExpertiaElectronics-r16", TRAIN / "adapters" / "expertia-electronics-r16",
     TRAIN / "hf_cards" / "MODEL_ExpertiaElectronics.md"),
    ("ExpertiaSWE-r16", TRAIN / "adapters" / "expertia-swe-r16",
     TRAIN / "hf_cards" / "MODEL_ExpertiaSWE.md"),
    ("ExpertiaDataScience-r16", TRAIN / "adapters" / "expertia-datascience-r16",
     TRAIN / "hf_cards" / "MODEL_ExpertiaDataScience.md"),
    ("ExpertiaBio-r16", TRAIN / "adapters" / "expertia-bio-r16",
     TRAIN / "hf_cards" / "MODEL_ExpertiaBio.md"),
]
PROJ = Path(r"F:\expertia\proyecto\training")
VARIANTS = [
    ("ExpertiaMath-Q4", PROJ / "merged" / "expertia-math-f16.gguf", "expertia-math-f16.gguf", False),
    ("ExpertiaMath-Q4", PROJ / "merged" / "expertia-math-fp16", "fp16", True),
    ("ExpertiaPhysics-Q4", DISK / "expertia-physics-f16.gguf", "expertia-physics-f16.gguf", False),
    ("ExpertiaPhysics-Q4", DISK / "expertia-physics-fp16", "fp16", True),
    ("ExpertiaChemistry-Q4", DISK / "expertia-chemistry-f16.gguf", "expertia-chemistry-f16.gguf", False),
    ("ExpertiaChemistry-Q4", DISK / "expertia-chemistry-fp16", "fp16", True),
    ("ExpertiaElectronics-Q4", DISK / "expertia-electronics-f16.gguf", "expertia-electronics-f16.gguf", False),
    ("ExpertiaElectronics-Q4", DISK / "expertia-electronics-fp16", "fp16", True),
    ("ExpertiaSWE-Q4", DISK / "expertia-swe-f16.gguf", "expertia-swe-f16.gguf", False),
    ("ExpertiaSWE-Q4", DISK / "expertia-swe-fp16", "fp16", True),
    ("ExpertiaDataScience-Q4", DISK / "expertia-datascience-f16.gguf", "expertia-datascience-f16.gguf", False),
    ("ExpertiaDataScience-Q4", DISK / "expertia-datascience-fp16", "fp16", True),
    ("ExpertiaBio-Q4", DISK / "expertia-bio-f16.gguf", "expertia-bio-f16.gguf", False),
    ("ExpertiaBio-Q4", DISK / "expertia-bio-fp16", "fp16", True),
]
DATASETS = [
    "expertia-math-puro.jsonl", "expertia-math-puro_val.jsonl",
    "expertia-physics-puro.jsonl", "expertia-physics-puro_val.jsonl",
    "expertia-chemistry-puro.jsonl", "expertia-chemistry-puro_val.jsonl",
    "expertia-electronics-puro.jsonl", "expertia-electronics-puro_val.jsonl",
    "expertia-swe-puro.jsonl", "expertia-swe-puro_val.jsonl",
    "expertia-datascience-puro.jsonl", "expertia-datascience-puro_val.jsonl",
    "expertia-bio-puro.jsonl", "expertia-bio-puro_val.jsonl",
]

if DRY:
    print("DRY-RUN (sin HF_TOKEN). Pendiente:")
    for repo, gguf, card in MODELS:
        print(" modelo %s/%s <- %s (%s) + card" % (USER or "<user>", repo, gguf, "OK" if gguf.exists() else "FALTA"))
    for repo, path, card in ADAPTERS:
        print(" adapter %s/%s <- %s" % (USER or "<user>", repo, path if path else "3070:C:/training/adapters/..."))
    for ds in DATASETS:
        p = TRAIN / "datasets" / ds
        print(" dataset %s <- %s" % (ds, "OK" if p.exists() else "FALTA"))
else:
    from huggingface_hub import HfApi, upload_file, upload_folder
    api = HfApi(token=TOKEN)
    for repo, gguf, card in MODELS:
        rid = "%s/%s" % (USER, repo)
        api.create_repo(rid, exist_ok=True, private=False)
        upload_file(path_or_fileobj=str(gguf), path_in_repo=gguf.name, repo_id=rid)
        upload_file(path_or_fileobj=str(card), path_in_repo="README.md", repo_id=rid)
        print("subido", rid)
    for repo, path, card in ADAPTERS:
        if not path:
            print("OMITIDO %s (traer de 3070 primero)" % repo)
            continue
        rid = "%s/%s" % (USER, repo)
        api.create_repo(rid, exist_ok=True, private=False)
        upload_folder(folder_path=str(path), path_in_repo=".", repo_id=rid,
                      ignore_patterns=["checkpoint-*", "*.pt", "*.pth", "*.bin", "README.md"])
        upload_file(path_or_fileobj=str(card), path_in_repo="README.md", repo_id=rid)
        print("subido", rid)
    for repo, src, dest, is_dir in VARIANTS:
        if not src.exists():
            print("OMITIDO %s (falta %s)" % (dest, src))
            continue
        rid = "%s/%s" % (USER, repo)
        if is_dir:
            upload_folder(folder_path=str(src), path_in_repo=dest, repo_id=rid)
        else:
            upload_file(path_or_fileobj=str(src), path_in_repo=dest, repo_id=rid)
        print("subida variante", rid, dest)
    did = "%s/expertia-domain-datasets" % USER
    api.create_repo(did, repo_type="dataset", exist_ok=True, private=False)
    for ds in DATASETS:
        p = TRAIN / "datasets" / ds
        if p.exists():
            upload_file(path_or_fileobj=str(p), path_in_repo=ds, repo_id=did, repo_type="dataset")
    upload_file(path_or_fileobj=str(TRAIN / "hf_cards" / "DATASET_expertia.md"), path_in_repo="README.md", repo_id=did, repo_type="dataset")
    print("datasets subidos", did)
