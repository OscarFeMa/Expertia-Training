import argparse
import json
import random
import re
import sqlite3
import sys
from pathlib import Path

RAW = Path(r"D:\proyectos\expertia\training\datasets\physics_raw")
DEFAULT_DB = r"E:\expertia-data\incubator.db"
DEFAULT_OUT = r"D:\proyectos\expertia\training\datasets\expertia-datascience-puro.jsonl"
AUDIT = RAW / "audit_datascience.jsonl"
SYSTEM_PROMPT = "Eres ExpertiaDataScience, cientifico de datos puro. Responde solo con definicion formal, parametros y ejemplo minimo cuando aplique. Sin opinion web."
BATCH = 2000
AUDIT_MIN = 6
GARBAGE_MARKERS = ("cookie", "sign in", "captcha", "subscribe", "javascript")
# Sopa de metadatos de articulos scholarly (Wikidata): no son definiciones y el
# modelo las regurgita como plantilla (canario DS 7/10, Q3-Q5). Se descartan.
METADATA_MARKERS = ("scientific article published", "language of work",
                    "instance of:", "author: Q", "source url:",
                    "country of origin", "official website", "inception: +",
                    "subclass of:", "taxon rank:")


def is_garbage(text):
    low = (text or "").lower()
    return any(m in low for m in GARBAGE_MARKERS)


def is_metadata_soup(text):
    low = (text or "").lower()
    return any(m in low for m in METADATA_MARKERS)


# Scaffolding del structured_knowledge Wikidata que el modelo NO debe
# memorizar como plantilla (leccion canario 18-sep: regurgitacion
# "Entity:/Properties:" y alucinaciones de entidad). Se conservan los
# valores legibles (incluida Description) y se tiran cabeceras + P-codigo.


def clean_sk(text):
    lines = []
    for ln in (text or "").splitlines():
        s = ln.strip()
        low = s.lower()
        if low.startswith("description:"):
            s = s[len("description:"):].strip()  # el valor SI es definicion
        elif any(low.startswith(p) for p in ("entity:", "aliases:",
                                             "properties:", "source:")):
            continue
        elif re.match(r"^P\d+\s*:", s):
            continue
        if s:
            lines.append(s)
    return "\n".join(lines)


def to_record(topic, output, qid, source_url, origin):
    topic = (topic or "").strip()
    output = clean_sk(output).strip()
    if not topic or not output or is_garbage(output) or is_metadata_soup(output):
        return None
    if not (50 <= len(output) <= 2000):
        return None
    instruction = ("Explica %s [%s]" % (topic, qid)) if qid else ("Explica %s" % topic)
    return {
        "system": SYSTEM_PROMPT,
        "instruction": instruction[:300],
        "input": "",
        "output": output[:2000],
        "metadata": {"domain": "DataScience", "qid": qid, "source_url": source_url, "origin": origin},
    }


def load_audit():
    scores = {}
    if not AUDIT.exists():
        print("WARN sin auditoria (%s): wiki sin filtrar" % AUDIT)
        return None
    for line in open(AUDIT, encoding="utf-8"):
        try:
            r = json.loads(line)
            scores[str(r.get("qid"))] = int(r.get("score", -1))
        except Exception:
            pass
    print("audit: %d qids puntuados" % len(scores))
    return scores


def load_raw():
    recs, seen = [], set()
    audit = load_audit()

    def want(qid, label):
        key = ("q", qid)
        if key in seen:
            return False
        tkey = ("t", (label or "").strip().lower())
        if tkey in seen:
            return False
        return True

    def mark(qid, label):
        seen.add(("q", qid))
        seen.add(("t", (label or "").strip().lower()))

    for name, origin in (("se_datascience.jsonl", "se_datascience"),
                         ("se_statistics.jsonl", "se_statistics"),
                         ("se_crossvalidated.jsonl", "se_crossvalidated")):
        f = RAW / name
        if not f.exists():
            print("WARN falta %s" % name)
            continue
        n = 0
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if not want(r.get("qid"), r.get("label")):
                continue
            rec = to_record(r.get("label"), r.get("formula"), r.get("qid"), "", origin)
            if rec:
                mark(r.get("qid"), r.get("label"))
                recs.append(rec)
                n += 1
        print("%s: +%d" % (name, n))
    f = RAW / "wiki_datascience.jsonl"
    if f.exists():
        n_ok = n_drop = 0
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if not want(r.get("qid"), r.get("label")):
                continue
            if audit is not None and audit.get(str(r.get("qid")), -1) < AUDIT_MIN:
                n_drop += 1
                continue
            rec = to_record(r.get("label"), r.get("formula"), r.get("qid"), "", "wiki_datascience")
            if rec:
                mark(r.get("qid"), r.get("label"))
                recs.append(rec)
                n_ok += 1
        print("wiki_datascience: +%d (filtrados auditoria: %d)" % (n_ok, n_drop))
    else:
        print("WARN falta wiki_datascience.jsonl")
    return recs, seen


def fetch_db_batch(db_path, max_id, batch):
    uri = "file:%s?mode=ro" % db_path
    con = sqlite3.connect(uri, uri=True, timeout=30)
    try:
        if max_id is None:
            rows = con.execute(
                "SELECT id, qid, topic, structured_knowledge, source_url FROM knowledge_packages "
                "WHERE domain='DataScience' AND qid IS NOT NULL "
                "ORDER BY id DESC LIMIT ?", (batch,)).fetchall()
        else:
            rows = con.execute(
                "SELECT id, qid, topic, structured_knowledge, source_url FROM knowledge_packages "
                "WHERE domain='DataScience' AND qid IS NOT NULL AND id < ? "
                "ORDER BY id DESC LIMIT ?", (max_id, batch)).fetchall()
        return rows
    finally:
        con.close()




def _take_build_lock():
    """Evita dos builds concurrentes del mismo dataset (corrompen la salida):
    lock con PID vivo; si el dueno murio, se reclama."""
    import os as _os
    lock = Path(__file__).parent / ("." + Path(__file__).stem + ".lock")
    if lock.exists():
        try:
            old = int(lock.read_text(encoding="utf-8").strip())
            _os.kill(old, 0)
            print("lock: otro build vivo PID %d, exit." % old)
            raise SystemExit(0)
        except SystemExit:
            raise
        except Exception:
            pass
    lock.write_text(str(_os.getpid()), encoding="utf-8")
    import atexit
    atexit.register(lambda: lock.exists() and lock.unlink())

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=50000)
    p.add_argument("--val-split", type=float, default=0.1)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--out", default=DEFAULT_OUT)
    args = p.parse_args()
    _take_build_lock()
    recs, seen = load_raw()
    print("raw recs: %d" % len(recs))
    max_id, scanned = None, 0
    while len(recs) < args.limit:
        rows = fetch_db_batch(args.db, max_id, BATCH)
        if not rows:
            break
        max_id = min(r[0] for r in rows)
        scanned += len(rows)
        for _id, qid, topic, sk, url in rows:
            key = ("q", (qid or "").strip())
            if key in seen:
                continue
            if not sk or len(sk) < 100 or len(sk) > 2000:
                continue
            if "wikidata.org/entity/" not in (url or ""):
                continue
            rec = to_record(topic, sk, (qid or "").strip(), (url or "").strip(), "db_definitional")
            if not rec:
                continue
            seen.add(key)
            recs.append(rec)
            if len(recs) >= args.limit:
                break
        if len(recs) % 5000 < BATCH:
            print("collected=%d scanned=%d" % (len(recs), scanned))
    print("TOTAL collected=%d scanned=%d" % (len(recs), scanned))
    rnd = random.Random(args.seed)
    rnd.shuffle(recs)
    n_val = int(len(recs) * args.val_split)
    val, train = recs[:n_val], recs[n_val:]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in train:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    vpath = out.with_name(out.stem + "_val.jsonl")
    with open(vpath, "w", encoding="utf-8") as f:
        for r in val:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("wrote train=%d val=%d" % (len(train), len(val)))


if __name__ == "__main__":
    main()
