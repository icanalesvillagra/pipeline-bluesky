from pathlib import Path
import duckdb

RAIZ = Path(__file__).resolve().parent.parent
TABLAS = ["posts", "hashtags", "borrados"]

def cargar():
    carpeta = RAIZ / "warehouse"
    carpeta.mkdir(exist_ok=True)
    con = duckdb.connect(str(carpeta / "bluesky.duckdb"))
    for tabla in TABLAS:
        ruta = (RAIZ / "data" / "clean" / f"{tabla}.parquet").as_posix()
        con.execute(f"CREATE OR REPLACE TABLE {tabla} AS SELECT * FROM read_parquet('{ruta}')")
        filas = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        print(f"Tabla '{tabla}' cargada con {filas} filas")
    con.close()

if __name__ == "__main__":
    cargar()