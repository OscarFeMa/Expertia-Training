"""Canario guionizado via Ollama (SYSTEM del Modelfile + think:false).
Uso: python training/canario_ollama.py --model expertia-datascience --domain datascience [--out logs/canario_datascience.jsonl]
Deja transcript + auto-flags (plantilla, idioma, vacio). Veredicto final: humano (10/10).
"""
import argparse
import json
import urllib.request
from pathlib import Path

PROMPTS = {
    "datascience": [
        "Define regresión lineal: fórmula y parámetros.",
        "¿Qué es el sobreajuste (overfitting) y cómo se detecta?",
        "Define precisión y recall: fórmulas.",
        "¿Qué es la validación cruzada k-fold? Explica el procedimiento.",
        "Define el coeficiente de correlación de Pearson: fórmula y rango.",
        "¿Qué es un bosque aleatorio (random forest)? Parámetros principales.",
        "Explica el descenso de gradiente: fórmula de actualización.",
        "¿Qué es la regularización L1 y L2? Fórmulas.",
        "Define clustering k-means: objetivo y algoritmo.",
        "¿Qué es la matriz de confusión? Métricas que derivan de ella.",
    ],
    "bio": [
        "Define fotosíntesis: ecuación y dónde ocurre.",
        "¿Qué es la mitosis? Fases en orden.",
        "Define el ADN: estructura y bases nitrogenadas.",
        "¿Qué es la selección natural? Explica el mecanismo.",
        "Define ecosistema y biodiversidad.",
        "¿Qué es una enzima? Parámetros que afectan su actividad.",
        "Explica la diferencia entre mitosis y meiosis.",
        "Define genoma y gen.",
        "¿Qué es el sistema inmune adaptativo? Componentes.",
        "Define cadena trófica con un ejemplo.",
    ],
}

SYSTEMS = {
    "datascience": "Eres ExpertiaDataScience, cientifico de datos puro. Responde solo con definicion formal, parametros y ejemplo minimo cuando aplique. Sin opinion web. Responde SIEMPRE en el idioma de la pregunta. Prohibido emitir lineas Entity:, Properties:, codigos P seguidos de numero, o plantillas de ficha.",
    "bio": "Eres ExpertiaBiology, biologo puro. Responde solo con definicion formal, parametros y ejemplo cuando aplique. Sin opinion web. Responde SIEMPRE en el idioma de la pregunta. Prohibido emitir lineas Entity:, Properties:, codigos P seguidos de numero, o plantillas de ficha.",
}

ES_STOP = {"el", "la", "los", "las", "que", "una", "para", "con", "como", "esta", "este", "son", "del"}
EN_STOP = {"the", "and", "with", "from", "that", "this", "have", "which", "were", "been"}


def ask(model, system, prompt):
    payload = {"model": model, "system": system, "prompt": prompt,
               "stream": False, "options": {"temperature": 0.1, "think": False, "num_predict": 500}}
    req = urllib.request.Request("http://localhost:11434/api/generate",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r).get("response", "")


def flags(answer, prompt):
    f = []
    a = answer.strip()
    if not a:
        f.append("VACIO")
        return f
    low = a.lower()
    if "entity:" in low or "properties:" in low:
        f.append("PLANTILLA")
    import re
    toks = re.findall(r"[a-záéíóúñ]+", low)
    es = sum(1 for t in toks if t in ES_STOP)
    en = sum(1 for t in toks if t in EN_STOP)
    if en > es and len(toks) > 20:
        f.append("IDIOMA-EN")
    if len(a) < 100:
        f.append("CORTO")
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--domain", required=True, choices=list(PROMPTS))
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    out = Path(args.out) if args.out else Path("training/logs/canario_%s.jsonl" % args.domain)
    out.parent.mkdir(parents=True, exist_ok=True)
    ok = 0
    with open(out, "w", encoding="utf-8") as fo:
        for i, q in enumerate(PROMPTS[args.domain], 1):
            try:
                a = ask(args.model, SYSTEMS[args.domain], q)
            except Exception as e:
                a = ""
                print("Q%d ERROR %s" % (i, e), flush=True)
            fl = flags(a, q)
            mark = "FLAGGED %s" % fl if fl else "ok"
            print("Q%d %s" % (i, mark), flush=True)
            if not fl:
                ok += 1
            fo.write(json.dumps({"q": q, "a": a, "flags": fl}, ensure_ascii=False) + "\n")
    print("CANARIO %d/10 sin flags (veredicto humano pendiente)" % ok)


if __name__ == "__main__":
    main()
