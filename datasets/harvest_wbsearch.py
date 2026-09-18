import json
import sys
import time
import urllib.parse
import urllib.request
import os

# Busqueda de entidades por keyword via wbsearchentities (endpoint fiable,
# sin los timeouts de SPARQL). Escribe raw jsonl estilo harvest.
# Uso: harvest_wbsearch.py [OUT=wb_bio.jsonl]
OUTNAME = sys.argv[1] if len(sys.argv) > 1 else "wb_bio.jsonl"
OUT = os.path.join(r"D:\proyectos\expertia\training\datasets\physics_raw", OUTNAME)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
LOCK = os.path.join(os.path.dirname(OUT), ".harvest_wb.lock")
if os.path.exists(LOCK):
    print("lock exists, otro harvester activo. exit.")
    sys.exit(0)
open(LOCK, "w").write(str(os.getpid()))
import atexit
atexit.register(lambda: os.path.exists(LOCK) and os.remove(LOCK))

UA = {"User-Agent": "ExpertiaDataset/1.0 (research dataset harvest; local contact)"}
API = "https://www.wikidata.org/w/api.php"
KEYWORDS = [
    "genetics", "cell biology", "taxonomy", "botany", "zoology",
    "microbiology", "ecology", "evolution", "biochemistry", "molecular biology",
    "photosynthesis", "mitosis", "enzyme", "protein", "genome",
    "species", "genus", "family biology", "bacteria", "virus",
    "fungi", "mammal", "bird", "reptile", "fish",
    "insect", "plant", "flower", "tree", "ecosystem",
    "biodiversity", "natural selection", "heredity", "chromosome", "neuron",
    "immune system", "vaccine", "antibiotic", "organ", "fossil",
]
SEEN_QIDS = set()
try:
    for _line in open(OUT, encoding="utf-8"):
        try:
            SEEN_QIDS.add(json.loads(_line).get("qid"))
        except Exception:
            pass
except FileNotFoundError:
    pass


def search(kw):
    for attempt in range(5):
        try:
            params = {"action": "wbsearchentities", "search": kw,
                      "language": "en", "format": "json", "limit": 50}
            url = API + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r).get("search", [])
        except Exception as e:
            print("retry %s: %s" % (kw, str(e)[:80]), flush=True)
            time.sleep(5 * (attempt + 1))
    return []


total = 0
with open(OUT, "a", encoding="utf-8") as f:
    for kw in KEYWORDS:
        for hit in search(kw):
            qid = hit.get("id", "")
            if not qid or qid in SEEN_QIDS:
                continue
            SEEN_QIDS.add(qid)
            label = hit.get("label", "")
            desc = hit.get("description", "")
            if not label or not desc or len(desc) < 20:
                continue
            f.write(json.dumps({
                "qid": qid, "label": label, "formula": desc,
                "instance_of": "wbsearch", "source": "wbsearch_bio",
            }, ensure_ascii=False) + "\n")
            total += 1
        time.sleep(0.5)
print("DONE total=%d" % total)
