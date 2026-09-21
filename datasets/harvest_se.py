import json, time, urllib.parse, urllib.request, os, sys
SITE = sys.argv[3] if len(sys.argv) > 3 else "physics"
TAG = "se_" + SITE
OUT = r"D:\proyectos\expertia\training\datasets\physics_raw\%s.jsonl" % TAG
os.makedirs(os.path.dirname(OUT), exist_ok=True)
LOCK = os.path.join(os.path.dirname(OUT), ".harvest_se.lock")
if os.path.exists(LOCK):
    print("lock exists, otro harvester activo. exit.")
    sys.exit(0)
open(LOCK, "w").write(str(os.getpid()))
import atexit
atexit.register(lambda: os.path.exists(LOCK) and os.remove(LOCK))
BASE = "https://api.stackexchange.com/2.3"
UA = {"User-Agent": "Expertia/1.0 (physics dataset harvest)"}
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 50
START = int(sys.argv[2]) if len(sys.argv) > 2 else 1
# API key opcional: 4º arg "site=.." o 5º arg, o env STACKEXCHANGE_KEY.
# Sin key: 300 req/dia + throttle agresivo. Con key: 10k req/dia.
KEY = os.environ.get("STACKEXCHANGE_KEY", "")
_extra = sys.argv[4:] if len(sys.argv) > 4 else []
for a in _extra:
    if a.startswith("site="):
        SITE = a.split("=", 1)[1]
        TAG = "se_" + SITE
        OUT = r"D:\proyectos\expertia\training\datasets\physics_raw\%s.jsonl" % TAG
    elif len(a) > 10:
        KEY = a
reqs, total = 0, 0


def get(path, params):
    global reqs
    params["site"] = SITE
    if KEY:
        params["key"] = KEY
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    for attempt in range(7):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                reqs += 1
                d = json.load(r)
                if d.get("backoff"):
                    time.sleep(int(d["backoff"]) + 1)
                return d
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode()[:200]
            except Exception:
                pass
            print("http %s (try %d): %s" % (e.code, attempt, body), flush=True)
            time.sleep(60 if e.code in (400, 502, 503) else 5 * (attempt + 1))
        except Exception as e:
            print("retry: %s" % str(e)[:120], flush=True)
            time.sleep(5 * (attempt + 1))
    return {}


def clean(html):
    import re
    t = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", t).strip()


with open(OUT, "a", encoding="utf-8") as f:
    for page in range(START, START + PAGES):
        if reqs > 240:
            print("quota guard, stop at page %d" % page)
            break
        d = get("/questions", {"order": "desc", "sort": "votes",
                               "pagesize": 100, "page": page, "filter": "withbody"})
        items = d.get("items", [])
        if not items:
            print("empty page %d, stop" % page)
            break
        acc = {}
        qids = ";".join(str(q["question_id"]) for q in items)
        a = get("/questions/" + qids + "/answers", {"filter": "withbody"})
        for ans in a.get("items", []):
            if ans.get("is_accepted"):
                acc[ans.get("question_id")] = ans.get("body", "")
        time.sleep(0.2)
        for q in items:
            if q["question_id"] not in acc:
                continue
            body = clean(acc[q["question_id"]])
            if len(body) < 150 or len(body) > 8000:
                continue
            if len(body) > 1800:
                cut = body.rfind(". ", 200, 1800)
                body = body[:cut + 1] if cut > 0 else body[:1800]
            f.write(json.dumps({
                "qid": "%s-%d" % (TAG, q["question_id"]),
                "label": q.get("title", ""),
                "formula": body,
                "instance_of": "stackexchange-accepted",
                "source": TAG,
                "score": q.get("score", 0),
            }, ensure_ascii=False) + "\n")
            total += 1
        print("page %d: +%d (total %d, reqs %d, backoff %s)" % (page, 0, total, reqs, d.get("backoff", 0)))
        if d.get("backoff"):
            time.sleep(int(d["backoff"]) + 1)
        time.sleep(0.3)
print("DONE total=%d reqs=%d" % (total, reqs))
