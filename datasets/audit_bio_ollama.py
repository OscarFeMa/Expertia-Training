import json, time, urllib.request
from pathlib import Path

# Auditor bio via Ollama local (juez qwen2.5:7b). Idempotente: salta qids puntuados.
# In: datasets/physics_raw/wiki_bio.jsonl. Out: physics_raw/audit_bio.jsonl
# Uso: python datasets/audit_bio_ollama.py
RAW = Path(r"D:\proyectos\expertia\training\datasets\physics_raw\wiki_bio.jsonl")
OUT = Path(r"D:\proyectos\expertia\training\datasets\physics_raw\audit_bio.jsonl")
MODEL = "qwen2.5:7b"
JUDGE_SYS = (
    "Eres un auditor de datasets. Vas a ver un TITULO y un CONTENIDO. "
    "Puntua de 0 a 10 su calidad como dato de entrenamiento para un "
    "especialista definicional de biologia (10 = definicion formal precisa, "
    "0 = ruido, opinion, spam o vacio). "
    "Piensa en una frase y termina con: PUNTUACION FINAL: <numero>"
)


def scored():
    done = set()
    if OUT.exists():
        for ln in open(OUT, encoding="utf-8"):
            try:
                done.add(json.loads(ln)["qid"])
            except Exception:
                pass
    return done


def judge(title, content):
    import re
    payload = {"model": MODEL, "system": JUDGE_SYS,
               "prompt": "TITULO: %s\nCONTENIDO: %s" % (title[:300], content[:1500]),
               "stream": False, "options": {"temperature": 0, "num_predict": 120}}
    for _ in range(3):
        try:
            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                txt = json.load(r).get("response", "")
            m = re.search(r"PUNTUACION FINAL:\s*(\d+)", txt)
            if m:
                return max(0, min(10, int(m.group(1))))
        except Exception as e:
            print("judge retry: %s" % str(e)[:100], flush=True)
            time.sleep(5)
    return -1


done = scored()
print("audit_bio: %d ya puntuados" % len(done), flush=True)
n = 0
with open(RAW, encoding="utf-8") as fin, open(OUT, "a", encoding="utf-8") as fout:
    for ln in fin:
        try:
            r = json.loads(ln)
        except Exception:
            continue
        qid = str(r.get("qid", ""))
        if not qid or qid in done:
            continue
        s = judge(r.get("label", ""), r.get("formula", ""))
        fout.write(json.dumps({"qid": qid, "score": s, "source": "ollama-" + MODEL}) + "\n")
        fout.flush()
        done.add(qid)
        n += 1
        if n % 200 == 0:
            print("audit_bio: +%d (total %d)" % (n, len(done)), flush=True)
print("DONE nuevos=%d total=%d" % (n, len(done)))
