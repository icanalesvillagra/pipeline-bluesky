import json
from pathlib import Path
import duckdb
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
FACET_TAG = "app.bsky.richtext.facet#tag"

def leer_eventos():
    archivos = sorted((RAIZ / "data" / "raw").glob("posts_*.jsonl"))
    if not archivos:
        raise FileNotFoundError("No hay datos crudos. Ejecuta primero ingestion/listen.py")
    eventos, malformadas = [], 0
    for archivo in archivos:
        with open(archivo, encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea:
                    continue
                try:
                    eventos.append(json.loads(linea))
                except json.JSONDecodeError:
                    malformadas += 1   # una línea cortada no debe tumbar todo
    return eventos, malformadas

def extraer_hashtags(record):
    tags = []
    for facet in record.get("facets") or []:
        for rasgo in facet.get("features") or []:
            if rasgo.get("$type") == FACET_TAG and rasgo.get("tag"):
                tags.append(rasgo["tag"].lower())
    return list(dict.fromkeys(tags))   # sin repetidos, conservando el orden

def transformar():
    eventos, malformadas = leer_eventos()
    print(f"Eventos leídos: {len(eventos)} (líneas dañadas: {malformadas})")

    creados, borrados, ignorados = [], [], 0
    for e in eventos:
        commit = e.get("commit")
        if e.get("kind") != "commit" or not commit \
           or commit.get("collection") != "app.bsky.feed.post":
            ignorados += 1          # eventos de cuenta, identidad, etc.
            continue

        base = {"did": e["did"], "rkey": commit["rkey"], "time_us": e["time_us"]}
        if commit["operation"] == "create":
            r = commit.get("record") or {}
            langs = r.get("langs") or []
            creados.append({
                **base,
                "texto": r.get("text"),
                "idioma": langs[0] if langs else None,
                "es_respuesta": "reply" in r,
                "tiene_adjunto": "embed" in r,
                "hashtags": extraer_hashtags(r),
            })
        elif commit["operation"] == "delete":
            borrados.append(base)
        else:
            ignorados += 1          # por ejemplo, "update"

    # Posts: sin duplicados (la reconexión puede repetir eventos)
    posts = pd.DataFrame(creados)
    antes = len(posts)
    posts = posts.drop_duplicates(subset=["did", "rkey"])
    print(f"Posts: {len(posts)} (duplicados eliminados: {antes - len(posts)})")

    # La hora confiable es la que registra Bluesky (time_us), no la que declara el cliente
    posts["publicado_en"] = pd.to_datetime(posts["time_us"], unit="us", utc=True)
    posts["n_hashtags"] = posts["hashtags"].str.len()

    hashtags = (posts[["did", "rkey", "hashtags"]]
                .explode("hashtags").dropna(subset=["hashtags"])
                .rename(columns={"hashtags": "hashtag"}))
    posts = posts.drop(columns=["hashtags"])

    df_borrados = pd.DataFrame(borrados).drop_duplicates(subset=["did", "rkey"])
    df_borrados["borrado_en"] = pd.to_datetime(df_borrados["time_us"], unit="us", utc=True)

    carpeta = RAIZ / "data" / "clean"
    carpeta.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()   # DuckDB escribe Parquet sin instalar nada extra
    for nombre, tabla in [("posts", posts), ("hashtags", hashtags), ("borrados", df_borrados)]:
        con.register("tabla", tabla)
        destino = (carpeta / f"{nombre}.parquet").as_posix()
        con.execute(f"COPY tabla TO '{destino}' (FORMAT PARQUET)")
        con.unregister("tabla")
        print(f"  {nombre}: {len(tabla)} filas")

    print(f"Ignorados (cuenta, identidad, otros): {ignorados}")
    print(f"Posts sin idioma: {posts['idioma'].isna().mean():.1%}")
    print(f"Posts con hashtags: {(posts['n_hashtags'] > 0).mean():.1%}")

if __name__ == "__main__":
    transformar()