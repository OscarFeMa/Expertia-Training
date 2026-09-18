import json
import sys
import time
import urllib.parse
import urllib.request
import os

# Cosecha acotada de taxones (especies y rangos) ordenados por modificacion
# reciente (frescura primero). Escribe raw jsonl estilo sparql_p*.jsonl.
# Uso: harvest_taxa.py [LIMIT=15000] [OUT=taxa_bio.jsonl]
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 15000
OUTNAME = sys.argv[2] if len(sys.argv) > 2 else "taxa_bio.jsonl"
OUT = os.path.join(r"D:\proyectos\expertia\training\datasets\physics_raw", OUTNAME)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
LOCK = os.path.join(os.path.dirname(OUT), ".harvest_taxa.lock")
if os.path.exists(LOCK):
    print("lock exists, otro harvester activo. exit.")
    sys.exit(0)
open(LOCK, "w").write(str(os.getpid()))
import atexit
atexit.register(lambda: os.path.exists(LOCK) and os.remove(LOCK))

UA = {"User-Agent": "ExpertiaDataset/1.0 (research dataset harvest; local contact)"}
API = "https://query.wikidata.org/sparql"
QUERY = """SELECT ?item ?itemLabel ?itemDescription WHERE {
  ?item wdt:P31/wdt:P279* wd:Q16521 .
  ?item wikibase:sitelinks ?sl .
  FILTER(?sl > 0)
  ?item wikibase:statements ?sc .
  FILTER(?sc > 10)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,es". }
}
LIMIT %d
""" % LIMIT


def sparql(q):
    for attempt in range(6):
        try:
            url = API + "?" + urllib.parse.urlencode({"format": "json", "query": q})
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r).get("results", {}).get("bindings", [])
        except Exception as e:
            wait = 20 * (attempt + 1)
            print("retry %s (%s), esperando %ds" % (type(e).__name__, str(e)[:100], wait), flush=True)
            time.sleep(wait)
    return None


rows = sparql(QUERY)
if not rows:
    print("SPARQL sin resultados, exit 1")
    sys.exit(1)
seen, total = set(), 0
with open(OUT, "a", encoding="utf-8") as f:
    for b in rows:
        uri = b.get("item", {}).get("value", "")
        qid = uri.split("/")[-1] if "/" in uri else uri
        if not qid or qid in seen:
            continue
        seen.add(qid)
        label = b.get("itemLabel", {}).get("value", "")
        desc = b.get("itemDescription", {}).get("value", "")
        if not label or label.startswith("Q"):
            continue
        f.write(json.dumps({
            "qid": qid,
            "label": label,
            "formula": desc,
            "instance_of": "taxon",
            "source": "sparql_taxa",
        }, ensure_ascii=False) + "\n")
        total += 1
print("DONE total=%d" % total)
