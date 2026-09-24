import argparse
import json
import random
import sqlite3
import sys
from pathlib import Path

RAW = Path(r"D:\proyectos\expertia\training\datasets\physics_raw")
DEFAULT_DB = r"E:\expertia-data\incubator.db"
DEFAULT_OUT = r"D:\proyectos\expertia\training\datasets\expertia-chemistry-puro.jsonl"
SYSTEM_PROMPT = "Eres ExpertiaChemistry, quimico puro. Responde solo con definicion formal y formula cuando aplique. Sin opinion web."
BATCH = 2000
GARBAGE_MARKERS = ("cookie", "sign in", "captcha", "subscribe", "javascript")
# Sopa de metadatos scholarly: se descarta (canario DS 7/10).
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


def to_record(topic, output, qid, source_url, origin):
    topic = (topic or "").strip()
    output = (output or "").strip()
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
        "metadata": {"domain": "Chemistry", "qid": qid, "source_url": source_url, "origin": origin},
    }


def load_raw(limit_each=15000):
    recs, seen = [], set()
    f = RAW / "sparql_p274.jsonl"
    if f.exists():
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            key = ("q", r.get("qid"))
            if key in seen:
                continue
            seen.add(key)
            rec = to_record(r.get("label"), r.get("formula"),
                            r.get("qid"), "https://www.wikidata.org/entity/" + (r.get("qid") or ""),
                            "sparql_p274")
            if rec:
                recs.append(rec)
            if len(recs) >= limit_each:
                break
    for name, origin in (("pubchem_chem.jsonl", "pubchem"), ("se_chemistry.jsonl", "se_chemistry"),
                         ("wiki_chem.jsonl", "wiki_chem")):
        f = RAW / name
        if not f.exists():
            continue
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            key = ("q", r.get("qid"))
            if key in seen:
                continue
            seen.add(key)
            rec = to_record(r.get("label"), r.get("formula"), r.get("qid"), "", origin)
            if rec:
                recs.append(rec)
    return recs, seen


def fetch_db_batch(db_path, max_id, batch):
    uri = "file:%s?mode=ro" % db_path
    con = sqlite3.connect(uri, uri=True, timeout=30)
    try:
        if max_id is None:
            rows = con.execute(
                "SELECT id, qid, topic, structured_knowledge, source_url FROM knowledge_packages "
                "WHERE domain='Chemistry' AND qid IS NOT NULL "
                "ORDER BY id DESC LIMIT ?", (batch,)).fetchall()
        else:
            rows = con.execute(
                "SELECT id, qid, topic, structured_knowledge, source_url FROM knowledge_packages "
                "WHERE domain='Chemistry' AND qid IS NOT NULL AND id < ? "
                "ORDER BY id DESC LIMIT ?", (max_id, batch)).fetchall()
        return rows
    finally:
        con.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=50000)
    p.add_argument("--val-split", type=float, default=0.1)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--out", default=DEFAULT_OUT)
    args = p.parse_args()
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
