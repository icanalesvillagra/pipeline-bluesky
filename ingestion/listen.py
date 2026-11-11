import asyncio, json, websockets
from datetime import datetime, timezone

# Solo pedimos posts (hay también likes, follows, etc.)
URL = "wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"

async def main(max_events=200):
    fecha = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ruta = f"data/raw/posts_{fecha}.jsonl"
    async with websockets.connect(URL) as ws:
        with open(ruta, "a", encoding="utf-8") as f:
            for i in range(max_events):
                evento = json.loads(await ws.recv())
                f.write(json.dumps(evento) + "\n")
    print(f"Guardados {max_events} eventos en {ruta}")

asyncio.run(main())