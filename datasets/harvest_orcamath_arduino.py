"""Cosecha top-hits del scout HF a raws estilo SE {label, formula, qid}:
- orca-math 200k (21 parquets, filtro askllm_score>=0.75) -> orca_math.jsonl
- suneeldk/arduino-code-dataset + Telles1974/Arduino-1000 + gavmac00/arduino-docs
  (datasets-server paginado) -> arduino_hf.jsonl
Uso: python harvest_orcamath_arduino.py
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RAW = Path(r"D:\proyectos\expertia\training\datasets\physics_raw")
TMP = Path(r"F:\expertia\tmp_orca")
HDRS = {"User-Agent": "Expertia/1.0"}
ORCA_SCORE_MIN = 0.68


def get(url, timeout=180, retries=6):
    for att in range(retries):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and att < retries - 1:
                time.sleep(30 * (att + 1))
                continue
            raise
    raise RuntimeError("reintentos agotados " + url)


def rows_api(did, config="default", split="train", length=100):
    off = 0
    while True:
        url = ("https://datasets-server.huggingface.co/rows?dataset=" +
               urllib.parse.quote(did, safe="") + "&config=" + config +
               "&split=" + split + "&offset=%d&length=%d" % (off, length))
        rows = json.loads(get(url).decode("utf-8")).get("rows", [])
        if not rows:
            break
        for rr in rows:
            yield rr.get("row", {})
        off += len(rows)


def harvest_orca():
    import pyarrow.parquet as pq
    api = json.loads(get("https://huggingface.co/api/datasets/geniacllm"
                         "/orca-math-word-problems-200k-askllm-v1").decode("utf-8"))
    files = sorted(s["rfilename"] for s in api.get("siblings", [])
                   if s["rfilename"].endswith(".parquet"))
    TMP.mkdir(parents=True, exist_ok=True)
    out, n = [], 0
    for fn in files:
        url = ("https://huggingface.co/datasets/geniacllm/"
               "orca-math-word-problems-200k-askllm-v1/resolve/main/" + fn)
        lp = TMP / fn.replace("/", "_")
        if not lp.exists():
            lp.write_bytes(get(url, timeout=600))
        t = pq.read_table(str(lp))
        cols = {c: t.column(c).to_pylist() for c in t.column_names}
        for i in range(t.num_rows):
            try:
                sc = float(cols.get("askllm_score", [1.0])[i] or 0)
            except (TypeError, ValueError):
                sc = 0.0
            if sc < ORCA_SCORE_MIN:
                continue
            q = str(cols.get("instruction", [""])[i] or "").strip()
            a = str(cols.get("output", [""])[i] or "").strip()
            if not q or not a:
                continue
            out.append({"label": q, "formula": a, "qid": "orca-%06d" % n})
            n += 1
    p = RAW / "orca_math.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("orca_math: %d (score>=%.2f)" % (len(out), ORCA_SCORE_MIN))
    return len(out)


def harvest_arduino():
    out = []

    def add(label, formula, qid):
        label, formula = (label or "").strip(), (formula or "").strip()
        if label and formula:
            out.append({"label": label[:300], "formula": formula, "qid": qid})

    for i, r in enumerate(rows_api("suneeldk/arduino-code-dataset")):
        add(r.get("instruction"), r.get("explanation"), "suneeldk-%05d" % i)
    for i, r in enumerate(rows_api("Telles1974/Arduino-1000")):
        q = (r.get("instruction") or "") + (" " + r.get("input") if r.get("input") else "")
        add(q, r.get("output"), "telles-%05d" % i)
    for i, r in enumerate(rows_api("gavmac00/arduino-docs")):
        txt = (r.get("text") or "").strip()
        lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
        if not lines:
            continue
        add(lines[0][:120], "\n".join(lines[1:]) or txt, "ardocs-%05d" % i)
    p = RAW / "arduino_hf.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("arduino_hf: %d" % len(out))
    return len(out)


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    a = harvest_orca()
    b = harvest_arduino()
    print("TOTAL", a + b)
