import json, time, urllib.parse, urllib.request, os, sys
OUT = r"D:\proyectos\expertia\training\datasets\physics_raw\wiki_physics.jsonl"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
LOCK = os.path.join(os.path.dirname(OUT), ".harvest_wiki.lock")
if os.path.exists(LOCK):
    print("lock exists, otro harvester activo. exit.")
    sys.exit(0)
open(LOCK, "w").write(str(os.getpid()))
import atexit
atexit.register(lambda: os.path.exists(LOCK) and os.remove(LOCK))
UA = {"User-Agent": "ExpertiaDataset/1.0 (research dataset harvest; local contact)"}
API = "https://en.wikipedia.org/w/api.php"
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 12000
ROOTCAT = sys.argv[2] if len(sys.argv) > 2 else "Category:Physics"
OUTNAME = sys.argv[3] if len(sys.argv) > 3 else "wiki_physics.jsonl"
OUT = os.path.join(os.path.dirname(OUT), OUTNAME)


def api(params):
    params["format"] = "json"
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            wait = 10 * (attempt + 1)
            if e.code == 429:
                try:
                    ra = e.headers.get("Retry-After")
                    if ra:
                        wait = max(wait, int(ra) + 2)
                except Exception:
                    pass
            print("http %s throttle, esperando %ds (try %d)" % (e.code, wait, attempt))
            time.sleep(wait)
        except Exception as e:
            print("retry: %s" % str(e)[:120])
            time.sleep(5 * (attempt + 1))
    return {}


seen, total = set(), 0
cats = [ROOTCAT]
depth = 0
while cats and total < LIMIT and depth < 3:
    nxt = []
    for cat in cats:
        cmc = None
        while True:
            p = {"action": "query", "list": "categorymembers", "cmtitle": cat,
                 "cmtype": "page|subcat", "cmlimit": 500}
            if cmc:
                p["cmcontinue"] = cmc
            d = api(p)
            members = d.get("query", {}).get("categorymembers", [])
            if not members:
                break
            pages = [m["title"] for m in members if m["ns"] == 0 and m["title"] not in seen]
            subcs = [(m["title"] if m["title"].startswith("Category:") else "Category:" + m["title"]) for m in members if m["ns"] == 14]
            nxt.extend(subcs)
            for i in range(0, len(pages), 50):
                if total >= LIMIT:
                    break
                e = api({"action": "query", "prop": "extracts", "exintro": 1,
                         "explaintext": 1, "titles": "|".join(pages[i:i + 50])})
                time.sleep(0.5)
                for pid, pg in (e.get("query", {}).get("pages", {}) or {}).items():
                    t = (pg.get("extract") or "").strip()
                    if len(t) < 200 or len(t) > 3000 or "may refer to" in t[:80]:
                        continue
                    if pg.get("title") in seen:
                        continue
                    seen.add(pg["title"])
                    with open(OUT, "a", encoding="utf-8") as f:
                        f.write(json.dumps({
                            "qid": "wiki-%s" % pid,
                            "label": pg.get("title", ""),
                            "formula": t,
                            "instance_of": "wikipedia-lead",
                            "source": OUTNAME.replace(".jsonl", ""),
                        }, ensure_ascii=False) + "\n")
                    total += 1
            cmc = d.get("continue", {}).get("cmcontinue")
            if not cmc:
                break
            time.sleep(0.2)
        if total >= LIMIT:
            break
    cats = list(dict.fromkeys(nxt))[:400]
    depth += 1
    print("depth %d done, total=%d, next cats=%d" % (depth, total, len(cats)))
print("DONE total=%d" % total)
