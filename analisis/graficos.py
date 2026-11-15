from pathlib import Path
import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

RAIZ = Path(__file__).resolve().parent.parent

def graficar():
    carpeta = RAIZ / "docs" / "img"
    carpeta.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(RAIZ / "warehouse" / "bluesky.duckdb"), read_only=True)

    # Ritmo de la captura más reciente (sin el primer y último minuto, que están incompletos)
    ritmo = con.sql("""
        SELECT date_trunc('minute', publicado_en AT TIME ZONE 'UTC') AS minuto,
               COUNT(*) AS posts
        FROM posts
        WHERE publicado_en >= (SELECT max(publicado_en) FROM posts) - INTERVAL 70 MINUTE
        GROUP BY 1 ORDER BY 1
    """).df().iloc[1:-1]

    hashtags = con.sql("""
        SELECT hashtag, COUNT(DISTINCT did) AS autores
        FROM hashtags GROUP BY hashtag
        ORDER BY autores DESC LIMIT 10
    """).df().sort_values("autores")

    idiomas = con.sql("""
        SELECT COALESCE(idioma, 'sin_idioma') AS idioma, COUNT(*) AS posts,
               100.0 * COUNT(*) / SUM(COUNT(*)) OVER () AS porcentaje
        FROM posts GROUP BY 1 ORDER BY posts DESC LIMIT 8
    """).df().sort_values("posts")
    con.close()

    # 1. Posts por minuto
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(ritmo["minuto"], ritmo["posts"], color="#1185FE")
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.set_title("Posts por minuto en Bluesky (hora UTC, fuente: Jetstream)")
    ax.set_xlabel("Hora (UTC)")
    ax.set_ylabel("Posts por minuto")
    fig.tight_layout()
    fig.savefig(carpeta / "posts_por_minuto.png", dpi=150)
    plt.close(fig)

    # 2. Hashtags con más autores distintos
    fig, ax = plt.subplots(figsize=(10, 6))
    barras = ax.barh(hashtags["hashtag"], hashtags["autores"], color="#2F4F4F")
    ax.bar_label(barras, padding=3)
    ax.set_title("Hashtags con más autores distintos (fuente: Jetstream)")
    ax.set_xlabel("Autores distintos")
    fig.tight_layout()
    fig.savefig(carpeta / "top_hashtags.png", dpi=150)
    plt.close(fig)

    # 3. Idiomas
    fig, ax = plt.subplots(figsize=(10, 6))
    barras = ax.barh(idiomas["idioma"], idiomas["posts"], color="#8B4513")
    ax.bar_label(barras, labels=[f"{p:.1f}%" for p in idiomas["porcentaje"]], padding=3)
    ax.set_title("Posts por idioma declarado (fuente: Jetstream)")
    ax.set_xlabel("Cantidad de posts")
    fig.tight_layout()
    fig.savefig(carpeta / "posts_por_idioma.png", dpi=150)
    plt.close(fig)

    print(f"Gráficos guardados en {carpeta}")

if __name__ == "__main__":
    graficar()