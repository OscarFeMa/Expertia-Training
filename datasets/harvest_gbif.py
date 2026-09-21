import json, time, urllib.parse, urllib.request, os, sys

# Cosecha taxonomica via GBIF Species API (plan B al SPARQL de Wikidata,
# que devuelve 504/500 de forma sostenida). Sin API key, paginado por offset.
# Uso: harvest_gbif.py [OUT=taxa_bio.jsonl]
OUTNAME = sys.argv[1] if len(sys.argv) > 1 else "taxa_bio.jsonl"
OUT = os.path.join(r"D:\proyectos\expertia\training\datasets\physics_raw", OUTNAME)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
LOCK = os.path.join(os.path.dirname(OUT), ".harvest_gbif.lock")
if os.path.exists(LOCK):
    print("lock exists, otro harvester activo. exit.")
    sys.exit(0)
open(LOCK, "w").write(str(os.getpid()))
import atexit
atexit.register(lambda: os.path.exists(LOCK) and os.remove(LOCK))

UA = {"User-Agent": "ExpertiaDataset/1.0 (research dataset harvest; local contact)"}
API = "https://api.gbif.org/v1/species/search"
TERMS = ["mammal", "bird", "reptile", "fish", "insect", "tree", "flower",
         "fungi", "bacteria", "genus", "family", "ecosystem", "primate",
         "carnivore", "rodent", "shark", "whale", "eagle", "oak", "pine"]
PER_TERM = 1000
PAGE = 300


def get(params):
    for attempt in range(6):
        try:
            url = API + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            print("http %s (try %d)" % (e.code, attempt), flush=True)
            time.sleep(10 * (attempt + 1))
        except Exception as e:
            print("retry: %s" % str(e)[:120], flush=True)
            time.sleep(5 * (attempt + 1))
    return {}


def clean(t):
    import re
    return re.sub(r"\s+", " ", t or "").strip()


total, seen = 0, set()
with open(OUT, "a", encoding="utf-8") as f:
    for term in TERMS:
        for off in range(0, PER_TERM, PAGE):
            d = get({"q": term, "limit": PAGE, "offset": off})
            items = (d or {}).get("results", [])
            if not items:
                break
            for e in items:
                key = str(e.get("key", ""))
                if not key or key in seen:
                    continue
                if (e.get("taxonomicStatus") or "") != "ACCEPTED":
                    continue
                name = clean(e.get("canonicalName") or e.get("scientificName") or "")
                rank = (e.get("rank") or "").lower()
                if not name or len(name) < 3:
                    continue
                parts = [name, "es "]
                parts.append("una especie" if rank == "species" else ("un " + rank if rank else "un taxon"))
                for lvl, es in (("family", "de la familia"), ("order", "del orden"),
                                ("class", "de la clase"), ("phylum", "del filo"),
                                ("kingdom", "del reino")):
                    v = clean(e.get(lvl) or "")
                    if v:
                        parts.append("%s %s" % (es, v))
                body = clean(" ".join(parts) + ".")
                if len(body) < 50:
                    continue
                seen.add(key)
                f.write(json.dumps({
                    "qid": "gbif-" + key,
                    "label": name,
                    "formula": body,
                    "instance_of": "gbif-taxon",
                    "source": "gbif",
                }, ensure_ascii=False) + "\n")
                total += 1
            time.sleep(0.3)
        print("term %s: total %d" % (term, total), flush=True)
print("DONE total=%d" % total)
