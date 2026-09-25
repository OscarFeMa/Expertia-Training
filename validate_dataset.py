"""Valida un dataset puro.jsonl: distingue HECHO de corrupto/incompleto.
Uso: python training/validate_dataset.py <fichero> [--min-train 40000]
Exit 0 = OK, 1 = FAIL (motivo en stdout). Para puerta automatica post-build.
"""
import json
import sys
from pathlib import Path

METADATA_MARKERS = ("scientific article published", "language of work",
                    "instance of:", "author: Q", "source url:",
                    "country of origin", "official website", "inception: +",
                    "subclass of:", "taxon rank:")


def main():
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    min_train = int(sys.argv[2]) if len(sys.argv) > 2 else 40000
    if not p or not p.exists():
        print("FAIL: no existe %s" % p)
        return 1
    if p.stat().st_size < 1024 * 1024:
        print("FAIL: %s demasiado pequeno (%d bytes), probable corte" % (p.name, p.stat().st_size))
        return 1
    n = 0
    bad_meta = 0
    domains = set()
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                n += 1
                low = (r.get("output") or "").lower()
                if any(m in low for m in METADATA_MARKERS):
                    bad_meta += 1
                domains.add(((r.get("metadata") or {}).get("domain")) or "?")
    except Exception as e:
        print("FAIL: %s JSON roto en fila %d: %s" % (p.name, n + 1, e))
        return 1
    vpath = p.with_name(p.stem + "_val.jsonl")
    nv = 0
    if vpath.exists():
        with open(vpath, encoding="utf-8") as f:
            for _ in f:
                nv += 1
    errs = []
    if n < min_train:
        errs.append("train %d < %d" % (n, min_train))
    if not (n * 0.05 <= nv <= n * 0.2):
        errs.append("val %d fuera de ratio 5-20%% de train %d" % (nv, n))
    if bad_meta:
        errs.append("metadata %d filas" % bad_meta)
    if len(domains) != 1:
        errs.append("dominios mezclados: %s" % domains)
    if errs:
        print("FAIL %s: %s" % (p.name, "; ".join(errs)))
        return 1
    print("OK %s: train=%d val=%d dominio=%s" % (p.name, n, nv, next(iter(domains))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
