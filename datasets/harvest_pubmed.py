import json, time, urllib.parse, urllib.request, os, sys
import xml.etree.ElementTree as ET

# Cosecha de abstracts definicionales desde PubMed/Entrez.
# Usa EXPERTIA_PUBMED_API_KEY (env o incubator-root/.env): 10 req/s con clave, 3/s sin ella.
# Uso: harvest_pubmed.py [MAXREC=10000] [OUT=pubmed_bio.jsonl]
MAXREC = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
OUTNAME = sys.argv[2] if len(sys.argv) > 2 else "pubmed_bio.jsonl"
OUT = os.path.join(r"D:\proyectos\expertia\training\datasets\physics_raw", OUTNAME)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
LOCK = os.path.join(os.path.dirname(OUT), ".harvest_pubmed.lock")
if os.path.exists(LOCK):
    print("lock exists, otro harvester activo. exit.")
    sys.exit(0)
open(LOCK, "w").write(str(os.getpid()))
import atexit
atexit.register(lambda: os.path.exists(LOCK) and os.remove(LOCK))

UA = {"User-Agent": "ExpertiaDataset/1.0 (research dataset harvest; local contact)"}


def load_key():
    k = os.environ.get("EXPERTIA_PUBMED_API_KEY", "")
    if k:
        return k
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        envf = os.path.join(here, "..", "..", "incubator-root", ".env")
        for ln in open(envf, encoding="utf-8", errors="ignore"):
            ln = ln.strip()
            if ln.startswith("EXPERTIA_PUBMED_API_KEY="):
                return ln.split("=", 1)[1].strip().strip("'\"")
    except Exception:
        pass
    return ""


KEY = load_key()
RATE = 0.15 if KEY else 0.4
print("pubmed key: %s" % ("SI (10/s)" if KEY else "NO (3/s)"), flush=True)

TERMS = ["genetics", "cell biology", "taxonomy", "biochemistry",
         "molecular biology", "photosynthesis", "mitosis", "genome",
         "species", "genus", "ecosystem", "biodiversity",
         "natural selection", "immune system", "vaccine", "antibiotic"]


def eget(path, params):
    if KEY:
        params["api_key"] = KEY
    params["retmode"] = "json" if path == "/esearch.fcgi" else params.get("retmode", "xml")
    for attempt in range(6):
        try:
            params["db"] = "pubmed"
            url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils" + path + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            print("http %s (try %d)" % (e.code, attempt), flush=True)
            time.sleep(10 * (attempt + 1))
        except Exception as e:
            print("retry: %s" % str(e)[:120], flush=True)
            time.sleep(5 * (attempt + 1))
    return None


def clean(t):
    import re
    t = re.sub(r"\s+", " ", t or "").strip()
    if len(t) > 1800:
        cut = t.rfind(". ", 200, 1800)
        t = t[:cut + 1] if cut > 0 else t[:1800]
    return t


total, seen = 0, set()
per_term = max(200, MAXREC // len(TERMS))
with open(OUT, "a", encoding="utf-8") as f:
    for term in TERMS:
        if total >= MAXREC:
            break
        raw = eget("/esearch.fcgi", {"term": term + "[Title/Abstract]", "retmax": per_term,
                                     "sort": "relevance", "retmode": "json"})
        time.sleep(RATE)
        if not raw:
            continue
        try:
            ids = json.loads(raw)["esearchresult"]["idlist"]
        except Exception:
            continue
        for i in range(0, len(ids), 200):
            if total >= MAXREC:
                break
            batch = ids[i:i + 200]
            xmlb = eget("/efetch.fcgi", {"id": ",".join(batch), "rettype": "abstract", "retmode": "xml"})
            time.sleep(RATE)
            if not xmlb:
                continue
            try:
                root = ET.fromstring(xmlb)
            except Exception:
                continue
            for art in root.iter("PubmedArticle"):
                pmid = (art.findtext("MedlineCitation/PMID") or "").strip()
                title = (art.findtext("MedlineCitation/Article/ArticleTitle") or "").strip()
                ab = " ".join([t.text or "" for t in art.findall("MedlineCitation/Article/Abstract/AbstractText")]).strip()
                if not pmid or pmid in seen:
                    continue
                body = clean(ab)
                if len(body) < 150:
                    continue
                seen.add(pmid)
                f.write(json.dumps({
                    "qid": "pmid-" + pmid,
                    "label": clean(title) or ("PMID " + pmid),
                    "formula": body,
                    "instance_of": "pubmed-abstract",
                    "source": "pubmed",
                }, ensure_ascii=False) + "\n")
                total += 1
        print("term %s: total %d" % (term, total), flush=True)
print("DONE total=%d" % total)
