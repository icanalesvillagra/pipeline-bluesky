from pathlib import Path
import duckdb

RAIZ = Path(__file__).resolve().parent.parent
con = duckdb.connect(str(RAIZ / "warehouse" / "bluesky.duckdb"), read_only=True)

print(con.sql("""
    SELECT hashtag, COUNT(*) AS posts, COUNT(DISTINCT did) AS autores
    FROM hashtags
    GROUP BY hashtag
    HAVING COUNT(DISTINCT did) >= 3
    ORDER BY autores DESC, posts DESC
    LIMIT 10
""").df())

print("\nPosts por idioma (top 8):")
print(con.sql("""
    SELECT COALESCE(idioma, 'sin_idioma') AS idioma,
           COUNT(*) AS posts,
           ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS porcentaje
    FROM posts GROUP BY 1 ORDER BY posts DESC LIMIT 8
""").df())

print("\nPosts por minuto:")
print(con.sql("""
    SELECT date_trunc('minute', publicado_en) AS minuto, COUNT(*) AS posts
    FROM posts GROUP BY 1 ORDER BY 1
""").df())

print("\nAutores más activos:")
print(con.sql("""
    SELECT did, COUNT(*) AS posts
    FROM posts GROUP BY did ORDER BY posts DESC LIMIT 5
""").df())