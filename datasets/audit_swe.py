"""Auditor de calidad para pares raw del dataset SWE (juez-LLM local 8-bit).
Idempotente y matable en cualquier momento: salta qids ya puntuados.
Uso: python311\python.exe C:\training\audit_swe.py
In:  C:\training\swe_raw\*.jsonl  (campos: qid, label, formula)
Out: C:\training\logs\audit_swe.jsonl  (qid, score 0-10, source)
"""
import json
import re
import sys
from pathlib import Path

RAW = Path(r"C:\training\swe_raw")
OUT = Path(r"C:\training\logs\audit_swe.jsonl")

JUDGE_SYS = (
    "Eres un auditor de datasets. Vas a ver un TITULO y un CONTENIDO. "
    "Puntua de 0 a 10 su calidad como dato de entrenamiento para un "
    "especialista definicional (10 = definicion formal precisa con "
    "formula o parametros, 0 = ruido, opinion, spam o vacio). "
    "Piensa en una frase y termina con: PUNTUACION FINAL: <numero>"
)


def load_scored():
    done = set()
    if OUT.exists():
        for line in OUT.open(encoding="utf-8"):
            try:
                done.add(json.loads(line)["qid"])
            except Exception:
                pass
    return done


def main():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    base = r"C:\training\base\phi-4-mini-reasoning"
    print("audit: cargando juez 8-bit...", flush=True)
    tok = AutoTokenizer.from_pretrained(base, trust_remote_code=True, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(
        base, trust_remote_code=True, load_in_8bit=True, device_map="auto")
    model.eval()
    scored = load_scored()
    print(f"audit: {len(scored)} ya puntuados, continuando", flush=True)
    n_new = 0
    with OUT.open("a", encoding="utf-8") as fo:
        for fp in sorted(RAW.glob("*.jsonl")):
            for line in fp.open(encoding="utf-8"):
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                qid = str(r.get("qid", ""))
                if not qid or qid in scored:
                    continue
                txt = f"TITULO: {r.get('label','')}\nCONTENIDO: {(r.get('formula','') or '')[:1200]}"
                prompt = f"{JUDGE_SYS}\n\n{txt}\n\nPUNTUACION FINAL:"
                try:
                    batch = tok([prompt], return_tensors="pt",
                                truncation=True, max_length=1500).to(model.device)
                    with torch.no_grad():
                        gen = model.generate(**batch, max_new_tokens=64,
                                             temperature=0.1, do_sample=False)
                    out = tok.decode(gen[0][batch["input_ids"].shape[1]:],
                                     skip_special_tokens=True)
                    nums = re.findall(r"\d+", out)
                    score = max(0, min(10, int(nums[-1]))) if nums else -1
                except Exception as e:
                    print(f"audit WARN {qid}: {e}", flush=True)
                    continue
                fo.write(json.dumps({"qid": qid, "score": score,
                                     "source": fp.stem}, ensure_ascii=False) + "\n")
                fo.flush()
                scored.add(qid)
                n_new += 1
                if n_new % 100 == 0:
                    print(f"audit: +{n_new} nuevos", flush=True)
    print(f"audit DONE nuevos={n_new} total={len(scored)}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
