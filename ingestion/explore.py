import json
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

eventos = []
for archivo in (RAIZ / "data" / "raw").glob("*.jsonl"):
    with open(archivo, encoding="utf-8") as f:
        eventos += [json.loads(linea) for linea in f]

print(f"Total de eventos: {len(eventos)}\n")

# 1. ¿Qué tipos de eventos llegan?
print("Tipos (kind):", Counter(e.get("kind") for e in eventos))

# 2. ¿Qué operaciones hay? (crear, borrar, editar)
print("Operaciones:", Counter(e.get("commit", {}).get("operation") for e in eventos))

# 3. ¿En qué idiomas se publica?
idiomas = Counter()
for e in eventos:
    langs = e.get("commit", {}).get("record", {}).get("langs") or ["sin_idioma"]
    idiomas.update(langs)
print("Top idiomas:", idiomas.most_common(5))

# 4. Un ejemplo completo
print("\nEjemplo de evento:")
print(json.dumps(eventos[0], indent=2, ensure_ascii=False))