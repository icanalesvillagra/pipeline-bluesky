from pathlib import Path
import duckdb

RAIZ = Path(__file__).resolve().parent.parent
LIMPIO = RAIZ / "data" / "clean"

REGLAS = [
    ("Hay al menos 100 posts",
     "SELECT COUNT(*) >= 100 FROM posts"),
    ("(did, rkey) es único en posts",
     "SELECT COUNT(*) = COUNT(DISTINCT (did, rkey)) FROM posts"),
    ("Todos los posts tienen fecha entre 2023 y mañana",
     "SELECT COUNT(*) FILTER (WHERE publicado_en IS NULL "
     "OR publicado_en < TIMESTAMPTZ '2023-01-01' "
     "OR publicado_en > now() + INTERVAL 1 DAY) = 0 FROM posts"),
    ("Máximo 25% de posts sin idioma",
     "SELECT AVG(CASE WHEN idioma IS NULL THEN 1 ELSE 0 END) <= 0.25 FROM posts"),
    ("Todo hashtag pertenece a un post existente",
     "SELECT COUNT(*) = 0 FROM hashtags h "
     "ANTI JOIN posts p ON h.did = p.did AND h.rkey = p.rkey"),
    ("(did, rkey) es único en borrados",
     "SELECT COUNT(*) = COUNT(DISTINCT (did, rkey)) FROM borrados"),
]

def validar():
    con = duckdb.connect()
    for tabla in ["posts", "hashtags", "borrados"]:
        ruta = (LIMPIO / f"{tabla}.parquet").as_posix()
        con.execute(f"CREATE VIEW {tabla} AS SELECT * FROM read_parquet('{ruta}')")

    fallas = []
    for descripcion, sql in REGLAS:
        pasa = con.execute(sql).fetchone()[0]
        print(f"{'✔' if pasa else '✘'} {descripcion}")
        if not pasa:
            fallas.append(descripcion)
    con.close()

    if fallas:
        raise ValueError(f"Validación fallida, no se cargará el warehouse: {fallas}")

if __name__ == "__main__":
    validar()