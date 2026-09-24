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
    "math": [
        "Define número primo y da un ejemplo.",
        "¿Qué es una ecuación de segundo grado? Fórmula de resolución.",
        "Define integral definida: fórmula y significado.",
        "¿Qué es un límite? Definición intuitiva y notación.",
        "Define matriz identidad y sus propiedades.",
        "¿Qué es el teorema de Pitágoras? Fórmula.",
        "Define derivada: fórmula del cociente incremental.",
        "¿Qué es un número irracional? Ejemplos.",
        "Define logaritmo: propiedades básicas.",
        "¿Qué es una serie geométrica? Fórmula de la suma.",
    ],
    "physics": [
        "Ley de Ohm: fórmula y parámetros.",
        "Define la segunda ley de Newton: fórmula.",
        "¿Qué es la energía cinética? Fórmula.",
        "Define longitud de onda y frecuencia: relación.",
        "¿Qué es la ley de gravitación universal? Fórmula.",
        "Define el principio de conservación de la energía.",
        "¿Qué es un campo electromagnético? Componentes.",
        "Define entropía en termodinámica.",
        "¿Qué es el efecto fotoeléctrico? Ecuación.",
        "Define momento lineal: fórmula.",
    ],
    "chemistry": [
        "Define mol: número de Avogadro.",
        "¿Qué es un enlace covalente? Ejemplo.",
        "Define pH: fórmula.",
        "¿Qué es una reacción de oxidación-reducción? Ejemplo.",
        "Define la tabla periódica: grupos y periodos.",
        "¿Qué es un ácido según Brönsted-Lowry?",
        "Define enlace iónico con un ejemplo.",
        "¿Qué es la estequiometría? Explica su uso.",
        "Define isótopo con ejemplos.",
        "¿Qué es un catalizador? ¿Se consume?",
    ],
    "electronics": [
        "Ley de Ohm: fórmula y parámetros.",
        "¿Qué es un transistor? Tipos básicos.",
        "Define resistencia y su unidad.",
        "¿Qué es un diodo? Función.",
        "Define condensador: fórmula de capacidad.",
        "¿Qué es un circuito en serie vs paralelo?",
        "Define ley de Kirchhoff de corrientes.",
        "¿Qué es un amplificador operacional? Usos.",
        "Define impedancia en corriente alterna.",
        "¿Qué es una puerta lógica AND? Tabla de verdad.",
    ],
    "swe": [
        "Define complejidad ciclomática.",
        "¿Qué es un test unitario? Propiedades.",
        "Define recursión con un ejemplo mínimo.",
        "¿Qué es un índice en bases de datos? Ventajas.",
        "Define API REST: principios.",
        "¿Qué es Big-O? Ejemplos O(n) y O(n log n).",
        "Define control de versiones: para qué sirve.",
        "¿Qué es un deadlock? Condiciones.",
        "Define función pura en programación funcional.",
        "¿Qué es integración continua? Prácticas.",
    ],
}

SYSTEMS = {
    "datascience": "Eres ExpertiaDataScience, cientifico de datos puro. Responde solo con definicion formal, parametros y ejemplo minimo cuando aplique. Sin opinion web. Responde SIEMPRE en el idioma de la pregunta. Prohibido emitir lineas Entity:, Properties:, codigos P seguidos de numero, o plantillas de ficha.",
    "bio": "Eres ExpertiaBiology, biologo puro. Responde solo con definicion formal, parametros y ejemplo cuando aplique. Sin opinion web. Responde SIEMPRE en el idioma de la pregunta. Prohibido emitir lineas Entity:, Properties:, codigos P seguidos de numero, o plantillas de ficha.",
    "math": "Eres ExpertiaMath, matematico puro. Responde solo con definicion formal y formula. Sin opinion web. Responde SIEMPRE en el idioma de la pregunta. Prohibido emitir lineas Entity:, Properties:, codigos P seguidos de numero, o plantillas de ficha.",
    "physics": "Eres ExpertiaPhysics, fisico puro. Responde solo con definicion formal y formula cuando aplique. Sin opinion web. Responde SIEMPRE en el idioma de la pregunta. Prohibido emitir lineas Entity:, Properties:, codigos P seguidos de numero, o plantillas de ficha.",
    "chemistry": "Eres ExpertiaChemistry, quimico puro. Responde solo con definicion formal y formula cuando aplique. Sin opinion web. Responde SIEMPRE en el idioma de la pregunta. Prohibido emitir lineas Entity:, Properties:, codigos P seguidos de numero, o plantillas de ficha.",
    "electronics": "Eres ExpertiaElectronics, electronico puro. Responde solo con definicion formal, parametros y formula cuando aplique. Sin opinion web. Responde SIEMPRE en el idioma de la pregunta. Prohibido emitir lineas Entity:, Properties:, codigos P seguidos de numero, o plantillas de ficha.",
    "swe": "Eres ExpertiaSoftwareEngineering, ingeniero de software puro. Responde solo con definicion formal, parametros y ejemplo minimo cuando aplique. Sin opinion web. Responde SIEMPRE en el idioma de la pregunta. Prohibido emitir lineas Entity:, Properties:, codigos P seguidos de numero, o plantillas de ficha.",
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
    if re.search(r"(?m)^source:\s*(\d+\s*){2,}", a) or re.search(r"(?m)^source:\s*https?://", a):
        f.append("SOURCE-STUB")
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
