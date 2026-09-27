"""Cosecha GSM8K (GitHub openai, MIT) + MATH (datasets-server mirror, MIT)
a raws estilo SE {label, formula, qid} para el builder math.
Uso: python harvest_gsm8k_math.py
"""
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

RAW = Path(r"D:\proyectos\expertia\training\datasets\physics_raw")
HDRS = {"User-Agent": "Expertia/1.0"}


def get(url, timeout=120, retries=6):
    req = urllib.request.Request(url, headers=HDRS)
    for att in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and att < retries - 1:
                time.sleep(30 * (att + 1))
                continue
            raise
    raise RuntimeError("agotados reintentos %s" % url)


def harvest_gsm8k():
    out = []
    for split in ("train", "test"):
        url = ("https://raw.githubusercontent.com/openai/grade-school-math"
               f"/master/grade_school_math/data/{split}.jsonl")
        for i, line in enumerate(get(url).decode("utf-8").splitlines()):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            q, a = (r.get("question") or "").strip(), (r.get("answer") or "").strip()
            if not q or not a:
                continue
            out.append({"label": q, "formula": a,
                        "qid": f"gsm8k-{split}-{i:05d}"})
    p = RAW / "gsm8k.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("gsm8k: %d" % len(out))
    return len(out)


def harvest_math():
    def url(split, off):
        return ("https://datasets-server.huggingface.co/rows?dataset=nlile"
                "%2Fhendrycks-MATH-benchmark&config=default&split=" + split +
                "&offset=%d&length=100" % off)
    out = []
    for split in ("train", "test"):
        off = 0
        while True:
            data = json.loads(get(url(split, off)).decode("utf-8"))
            rows = data.get("rows", [])
            if not rows:
                break
            for j, rr in enumerate(rows):
                row = rr.get("row", {})
                prob = (row.get("problem") or "").strip()
                sol = (row.get("solution") or "").strip()
                if not prob or not sol:
                    continue
                out.append({"label": prob, "formula": sol,
                            "qid": "math-%s-%05d" % (split, off + j)})
            off += len(rows)
    p = RAW / "hendrycks_math.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("hendrycks_math: %d" % len(out))
    return len(out)


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    a = harvest_gsm8k()
    b = harvest_math()
    print("TOTAL", a + b)
