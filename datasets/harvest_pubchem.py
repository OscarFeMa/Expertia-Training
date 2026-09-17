import json, time, urllib.parse, urllib.request, os

OUT = r"D:\proyectos\expertia\training\datasets\physics_raw\pubchem_chem.jsonl"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
UA = {"User-Agent": "Expertia/1.0 (chemistry dataset harvest)"}

CURATED = """water|hydrogen peroxide|sulfuric acid|hydrochloric acid|nitric acid|phosphoric acid|acetic acid|citric acid|
formic acid|carbonic acid|sodium hydroxide|potassium hydroxide|calcium hydroxide|ammonia|methane|ethane|propane|butane|
ethanol|methanol|propanol|glycerol|acetone|benzene|toluene|formaldehyde|acetaldehyde|glucose|fructose|sucrose|caffeine|
aspirin|urea|sodium chloride|potassium chloride|calcium carbonate|sodium carbonate|sodium bicarbonate|calcium oxide|
magnesium oxide|aluminum oxide|silicon dioxide|iron oxide|titanium dioxide|zinc oxide|copper sulfate|silver nitrate|
sodium nitrate|potassium nitrate|calcium sulfate|barium sulfate|sodium sulfate|carbon monoxide|carbon dioxide|
nitrogen dioxide|sulfur dioxide|hydrogen sulfide|chlorine|oxygen|nitrogen|hydrogen|helium|ozone|silica gel|aspirin|
penicillin|morphine|nicotine|cholesterol|adenosine triphosphate|aminoacetic acid|alanine|methane hydrate|ethylene|
acetylene|propylene|styrene|vinyl chloride|tetrafluoroethylene|formaldehyde|phenol|aniline|toluene diisocyanate|
sodium hypochlorite|calcium hypochlorite|potassium permanganate|sodium dichromate|ferric chloride|aluminum chloride|
silicon tetrachloride|phosphorus trichloride|sulfur hexafluoride|carbon tetrachloride|chloroform|dichloromethane|
diethyl ether|tetrahydrofuran|dimethyl sulfoxide|acetonitrile|pyridine|aniline|naphthalene|anthracene|fullerene|
graphene oxide|calcium carbide|sodium cyanide|potassium cyanide|hydrofluoric acid|boric acid|silicic acid|
sodium silicate|potassium dichromate|lead nitrate|mercury chloride|silver chloride|gold chloride|platinum chloride|
ethanolamine|diethanolamine|triethanolamine|formamide|dimethylformamide|acetic anhydride|maleic anhydride|
phthalic anhydride|benzoic acid|salicylic acid|lactic acid|oxalic acid|tartaric acid|malic acid|fumaric acid|
ascorbic acid|palmitic acid|oleic acid|stearic acid|linoleic acid|glyceraldehyde|dihydroxyacetone|ribose|deoxyribose|
adenine|guanine|cytosine|thymine|uracil|ATP|NADH|coenzyme A|heme|chlorophyll a|beta-carotene|retinol|calciferol|
tocopherol|thiamine|riboflavin|niacin|pyridoxine|biotin|folic acid|cobalamin|dopamine|serotonin|adrenaline|insulin|
testosterone|estradiol|progesterone|cortisol|thyroxine|melatonin|histamine|acetylcholine|glycine|serine|threonine|
cysteine|methionine|aspartic acid|glutamic acid|lysine|arginine|histidine|phenylalanine|tyrosine|tryptophan|valine|
leucine|isoleucine|proline|asparagine|glutamine|kerosene|gasoline|diesel|biodiesel|ethanol fuel|methanol fuel|
hydrogen fuel|natural gas|propane fuel|butane fuel|acetylene fuel|coal|peat|lignite|anthracite|coke|charcoal|
activated carbon|carbon black|diamond|lonsdaleite|graphite|carbon nanotubes|buckminsterfullerene|cement|concrete|
glass|quartz|feldspar|mica|clay|kaolinite|gypsum|limestone|marble|chalk|dolomite|apatite|fluorite|halite|sylvite|
carnallite|epsomite|borax|trona|natron|urea fertilizer|ammonium nitrate|ammonium sulfate|superphosphate|potash|
pesticide|DDT|glyphosate|atrazine|parathion|malathion|carbaryl|nicotine sulfate|rotenone|pyrethrin|soap|detergent|
sodium dodecyl sulfate|benzalkonium chloride|triclosan|formalin|glutaraldehyde|ethylene oxide|propylene oxide|
epichlorohydrin|bisphenol A|polycarbonate|polyethylene|polypropylene|polystyrene|polyvinyl chloride|teflon|nylon|
kevlar|dacron|rayon|acetate fiber|spandex|rubber|neoprene|silicone|epoxy|polyurethane|bakelite|melamine|urea-formaldehyde|
casein|gelatin|agar|starch|cellulose|chitin|lignin|pectin|inulin|dextran|xanthan gum|guar gum|tragacanth|acacia gum""".replace("\n", "").split("|")

CATIONS = ["sodium", "potassium", "calcium", "magnesium", "aluminum", "iron", "copper", "zinc", "lead", "barium",
           "ammonium", "silver", "mercury", "nickel", "cobalt", "manganese", "chromium", "cadmium", "strontium",
           "lithium", "cesium", "rubidium", "tin", "antimony", "bismuth", "titanium", "vanadium", "tungsten"]
ANIONS = ["oxide", "chloride", "sulfate", "nitrate", "carbonate", "phosphate", "sulfide", "fluoride", "bromide",
          "iodide", "hydroxide", "acetate", "oxalate", "chromate"]


def pug(path, single=False):
    url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug" + path
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {}
            time.sleep(2 * (attempt + 1))
        except Exception as e:
            print("retry: %s" % str(e)[:100])
            time.sleep(2 * (attempt + 1))
    return {}


names = list(dict.fromkeys([n.strip() for n in CURATED if n.strip()]))
for cat in CATIONS:
    for an in ANIONS:
        names.append("%s %s" % (cat, an))
names = list(dict.fromkeys(names))
print("candidates: %d" % len(names))

seen, total = set(), 0
cids = []
for idx, nm in enumerate(names):
    d = pug("/compound/name/%s/cids/JSON" % urllib.parse.quote(nm))
    idlist = d.get("IdentifierList", {}).get("CID", [])
    if idlist:
        cids.append(idlist[0])
    if idx % 50 == 0:
        print("resolved %d/%d cids=%d" % (idx, len(names), len(cids)))
    time.sleep(0.15)
print("resolved cids: %d" % len(cids))
with open(OUT, "a", encoding="utf-8") as f:
    for i in range(0, len(cids), 50):
        props = pug("/compound/cid/%s/property/MolecularFormula,MolecularWeight,IUPACName,Title/JSON" % ",".join(map(str, cids[i:i + 50])))
        for p in props.get("PropertyTable", {}).get("Properties", []):
            cid = p.get("CID")
            if cid in seen:
                continue
            seen.add(cid)
            title = p.get("Title", "")
            form = p.get("MolecularFormula", "")
            mw = p.get("MolecularWeight", "")
            iupac = p.get("IUPACName", "")
            if not form:
                continue
            body = "Nombre: %s. Nombre IUPAC: %s. Formula molecular: %s. Masa molar: %s g/mol." % (title, iupac, form, mw)
            f.write(json.dumps({
                "qid": "pubchem-%d" % cid,
                "label": title,
                "formula": body,
                "instance_of": "pubchem-compound",
                "source": "pubchem",
            }, ensure_ascii=False) + "\n")
            total += 1
        print("chunk %d: total=%d" % (i // 25, total))
        time.sleep(0.4)
print("DONE total=%d" % total)
