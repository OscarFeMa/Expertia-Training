import json, time, urllib.parse, urllib.request, os, sys

# Cosecha definicional desde UniProtKB (Swiss-Prot reviewed, CC-BY 4.0).
# Sin API key. Paginacion por cursor, 500/pag (~40 reqs por 20k).
# Uso: harvest_uniprot.py [LIMIT=20000] [OUT=uniprot_bio.jsonl]
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
OUTNAME = sys.argv[2] if len(sys.argv) > 2 else "uniprot_bio.jsonl"
OUT = os.path.join(r"D:\proyectos\expertia\training\datasets\physics_raw", OUTNAME)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
LOCK = os.path.join(os.path.dirname(OUT), ".harvest_uniprot.lock")
if os.path.exists(LOCK):
    print("lock exists, otro harvester activo. exit.")
    sys.exit(0)
open(LOCK, "w").write(str(os.getpid()))
import atexit
atexit.register(lambda: os.path.exists(LOCK) and os.remove(LOCK))

UA = {"User-Agent": "ExpertiaDataset/1.0 (research dataset harvest; local contact)"}
API = "https://rest.uniprot.org/uniprotkb/search"
QUERY = "(reviewed:true)"
FIELDS = "accession,protein_name,cc_function,organism_name"


def get(params):
    for attempt in range(6):
        try:
            url = API + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                link = r.headers.get("Link", "")
                return json.load(r), link
        except urllib.error.HTTPError as e:
            print("http %s (try %d), esperando %ds" % (e.code, attempt, 10 * (attempt + 1)), flush=True)
            time.sleep(10 * (attempt + 1))
        except Exception as e:
            print("retry: %s" % str(e)[:120], flush=True)
            time.sleep(5 * (attempt + 1))
    return {}, ""


def next_cursor(link):
    for part in link.split(","):
        if 'rel="next"' in part:
            u = part.split(";")[0].strip().strip("<>")
            q = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
            return q.get("cursor", [None])[0]
    return None


def clean(t):
    import re
    t = re.sub(r"\s+", " ", t or "").strip()
    if len(t) > 1800:
        cut = t.rfind(". ", 200, 1800)
        t = t[:cut + 1] if cut > 0 else t[:1800]
    return t


total, cursor, seen = 0, None, set()
with open(OUT, "a", encoding="utf-8") as f:
    while total < LIMIT:
        params = {"query": QUERY, "fields": FIELDS, "format": "json", "size": 500}
        if cursor:
            params["cursor"] = cursor
        d, link = get(params)
        items = (d or {}).get("results", [])
        if not items:
            print("sin resultados, stop")
            break
        for e in items:
            acc = e.get("primaryAccession", "")
            if not acc or acc in seen:
                continue
            prot = ((e.get("proteinDescription") or {}).get("recommendedName") or {})
            label = (prot.get("fullName") or {}).get("value", "") or acc
            org = ((e.get("organism") or {}).get("scientificName")) or ""
            func = ""
            for c in e.get("comments") or []:
                if c.get("commentType") == "FUNCTION":
                    texts = [t.get("value", "") for t in c.get("texts") or []]
                    func = " ".join(texts)
                    break
            body = clean(func)
            if len(body) < 150:
                continue
            if org:
                label = "%s (%s)" % (label, org)
            seen.add(acc)
            f.write(json.dumps({
                "qid": "uniprot-" + acc,
                "label": label,
                "formula": body,
                "instance_of": "uniprot-reviewed",
                "source": "uniprot",
            }, ensure_ascii=False) + "\n")
            total += 1
            if total >= LIMIT:
                break
        print("pagina: total %d" % total, flush=True)
        cursor = next_cursor(link)
        if not cursor:
            print("sin cursor next, stop")
            break
        time.sleep(0.4)
print("DONE total=%d" % total)
