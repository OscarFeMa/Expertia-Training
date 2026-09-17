import json, time, urllib.parse, urllib.request, os
OUT = r"D:\proyectos\expertia\training\datasets\physics_raw\sparql_p274.jsonl"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
LOCK = os.path.join(os.path.dirname(OUT), ".harvest_p274.lock")
if os.path.exists(LOCK):
    print("lock exists, exit.")
    import sys as _s
    _s.exit(0)
open(LOCK, "w").write(str(os.getpid()))
import atexit as _a
_atexit_register = _a.register(lambda: os.path.exists(LOCK) and os.remove(LOCK))
UA = {"User-Agent": "Expertia/1.0 (chemistry dataset harvest)"}
seen, total = set(), 0
off = 0
while True:
    q = ("SELECT ?s ?sLabel ?f ?tLabel WHERE { ?s wdt:P274 ?f . "
         "OPTIONAL { ?s wdt:P31 ?t } "
         'SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". } } '
         "LIMIT 2000 OFFSET %d" % off)
    url = "https://query.wikidata.org/sparql?query=" + urllib.parse.quote(q) + "&format=json"
    rows = None
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                rows = json.load(r)["results"]["bindings"]
            break
        except Exception as e:
            print("retry %d: %s" % (attempt, e))
            time.sleep(5 * (attempt + 1))
    if not rows:
        print("empty at offset %d, stop" % off)
        break
    with open(OUT, "a", encoding="utf-8") as f:
        for b in rows:
            s = b["s"]["value"]
            if s in seen:
                continue
            seen.add(s)
            f.write(json.dumps({
                "qid": s.rsplit("/", 1)[-1],
                "label": b.get("sLabel", {}).get("value", ""),
                "formula": b.get("f", {}).get("value", "")[:2000],
                "instance_of": b.get("tLabel", {}).get("value", ""),
                "source": "wikidata_p274",
            }, ensure_ascii=False) + "\n")
            total += 1
    print("offset %d: +%d (total %d)" % (off, len(rows), total))
    if len(rows) < 2000:
        break
    off += 2000
    time.sleep(2)
print("DONE total=%d" % total)
