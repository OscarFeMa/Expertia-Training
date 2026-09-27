"""Scout de datasets en Hugging Face por dominio: busca, filtra por licencia,
muestrea contenido y puntúa utilidad para Expertia.
Uso: python hf_dataset_scout.py --domain math|electronics [--max 40]
Salida: training/logs/hf_scout_<domain>.json + .md + stub de harvester top-N.
Procedimiento reutilizable: añadir perfil en DOMAIN_PROFILES para el resto.
"""
import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

LOGS = Path(r"D:\proyectos\expertia\training\logs")
HDRS = {"User-Agent": "Expertia/1.0 (dataset scout)"}

LICENSE_OK = {"mit", "apache-2.0", "cc-by-4.0", "cc-by-3.0", "cc0-1.0",
              "bsd-3-clause", "bsd-2-clause", "unlicense", "artistic-2.0"}

GARBAGE = ("cookie", "sign in", "captcha", "subscribe", "javascript",
           "lorem ipsum")

DOMAIN_PROFILES = {
    # Activos hoy:
    "math": {"keywords": ["mathematics problems", "math word problems",
                          "algebra geometry", "calculus theorems"],
             "need": ("$", "\\frac", "equation", "theorem", "proof", "solve"),
             "avoid": ("code", "poetry", "lyrics")},
    "electronics": {"keywords": ["electronics circuits", "arduino",
                                 "microcontroller embedded",
                                 "electrical engineering"],
                    "need": ("volt", "circuit", "resistor", "arduino", "pin",
                             "current", "sensor"),
                    "avoid": ("poetry", "lyrics", "recipes")},
    # Plantilla para el resto (a la vuelta):
    # "physics": {"keywords": [...], "need": (...), "avoid": (...)},
}


def get_json(url, retries=6):
    for att in range(retries):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and att < retries - 1:
                time.sleep(20 * (att + 1))
                continue
            return None
        except Exception:
            return None
    return None


def search_datasets(keywords, max_hits):
    seen, out = set(), []
    for kw in keywords:
        q = ("https://huggingface.co/api/datasets?search=" +
             urllib.parse.quote(kw) +
             "&sort=downloads&direction=-1&limit=%d" % max_hits)
        for d in get_json(q) or []:
            did = d.get("id", "")
            if did and did not in seen:
                seen.add(did)
                out.append(d)
    return out


def licenses_ok(d):
    tags = [t.lower() for t in (d.get("tags") or [])]
    lic = [t.split("license:", 1)[1] for t in tags if t.startswith("license:")]
    if not lic:
        return False, "unknown"
    good = [l for l in lic if l in LICENSE_OK]
    return (bool(good), lic[0])


def sample_rows(did):
    sp = get_json("https://datasets-server.huggingface.co/splits?dataset=" + did)
    if not sp or not sp.get("splits"):
        return None, "sin splits"
    splits = sp["splits"]
    pick = None
    for s in splits:
        if s.get("split", "").lower() == "train":
            pick = s
            break
    pick = pick or splits[0]
    cfg, spl = pick.get("config"), pick.get("split")
    url = ("https://datasets-server.huggingface.co/rows?dataset=" + did +
           "&config=" + urllib.parse.quote(cfg) + "&split=" +
           urllib.parse.quote(spl) + "&offset=0&length=20")
    rows = (get_json(url) or {}).get("rows", [])
    if not rows:
        return None, "sin filas"
    texts = []
    for rr in rows:
        for v in (rr.get("row") or {}).values():
            if isinstance(v, str) and len(v) > 20:
                texts.append(v)
    return (texts, "%s/%s" % (cfg, spl)) if texts else (None, "vacío")


def score(texts, profile):
    blob = "\n".join(texts).lower()
    if any(g in blob for g in GARBAGE):
        return 0, "basura"
    if any(a in blob for a in profile["avoid"]):
        return 0, "off-topic"
    hits = sum(1 for n in profile["need"] if n in blob)
    latex = len(re.findall(r"\$[^$]+\$|\\frac|\\sqrt|\\times", blob))
    avglen = sum(len(t) for t in texts) / max(1, len(texts))
    s = min(40, hits * 10) + min(30, latex) + (20 if 100 < avglen < 3000 else 5)
    why = "need=%d/6 latex=%d avglen=%d" % (hits, latex, avglen)
    return s, why


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--domain", required=True, choices=list(DOMAIN_PROFILES))
    p.add_argument("--max", type=int, default=40)
    args = p.parse_args()
    prof = DOMAIN_PROFILES[args.domain]
    cands = search_datasets(prof["keywords"], args.max)
    print("candidatos: %d" % len(cands), flush=True)
    ranked = []
    for i, d in enumerate(cands):
        did = d["id"]
        ok, lic = licenses_ok(d)
        if not ok:
            continue
        texts, where = sample_rows(did)
        if not texts:
            continue
        s, why = score(texts, prof)
        if s <= 0:
            continue
        rows = d.get("downloads", 0)
        ranked.append({"id": did, "score": s, "why": why, "license": lic,
                       "downloads": rows, "split": where,
                       "card": "https://huggingface.co/datasets/" + did})
        print("[%d/%d] %s score=%d (%s)" % (i + 1, len(cands), did, s, why),
              flush=True)
    ranked.sort(key=lambda r: -r["score"])
    LOGS.mkdir(parents=True, exist_ok=True)
    with open(LOGS / ("hf_scout_%s.json" % args.domain), "w", encoding="utf-8") as f:
        json.dump(ranked, f, ensure_ascii=False, indent=1)
    md = ["# Scout HF — %s (%d candidatos útiles)" % (args.domain, len(ranked)), ""]
    for r in ranked[:20]:
        md.append("- **%s** (score %d, %s, ↓%s) — %s — `%s`" %
                  (r["id"], r["score"], r["license"], r["downloads"],
                   r["why"], r["split"]))
    (LOGS / ("hf_scout_%s.md" % args.domain)).write_text("\n".join(md),
                                                         encoding="utf-8")
    print("SCOUT-DONE %s útiles=%d" % (args.domain, len(ranked)))


if __name__ == "__main__":
    main()
