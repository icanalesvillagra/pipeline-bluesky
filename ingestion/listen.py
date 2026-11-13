import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import websockets

RAIZ = Path(__file__).resolve().parent.parent
URL_BASE = "wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"
TAMANO_LOTE = 100   # escribimos al disco cada 100 eventos

def guardar(lote):
    if not lote:
        return
    carpeta = RAIZ / "data" / "raw"
    carpeta.mkdir(parents=True, exist_ok=True)
    hora = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H")
    with open(carpeta / f"posts_{hora}.jsonl", "a", encoding="utf-8") as f:
        f.write("\n".join(lote) + "\n")
    lote.clear()

async def escuchar(max_segundos=None):
    inicio = asyncio.get_running_loop().time()
    lote, cursor, espera, total = [], None, 1, 0
    try:
        while True:
            url = URL_BASE + (f"&cursor={cursor}" if cursor else "")
            try:
                async with websockets.connect(url) as ws:
                    print("Conectado")
                    espera = 1
                    async for mensaje in ws:
                        lote.append(mensaje.strip())
                        cursor = json.loads(mensaje)["time_us"]
                        total += 1
                        if len(lote) >= TAMANO_LOTE:
                            guardar(lote)
                            print(f"{total} eventos guardados")
                        if max_segundos and asyncio.get_running_loop().time() - inicio > max_segundos:
                            return
            except Exception as error:
                print(f"Conexión perdida ({error}). Reintentando en {espera} s...")
                guardar(lote)
                await asyncio.sleep(espera)
                espera = min(espera * 2, 60)
    finally:
        guardar(lote)   # no perder lo que quedó en memoria al terminar
        print(f"Total capturado: {total}")

if __name__ == "__main__":
    segundos = int(sys.argv[1]) if len(sys.argv) > 1 else None
    try:
        asyncio.run(escuchar(segundos))
    except KeyboardInterrupt:
        pass