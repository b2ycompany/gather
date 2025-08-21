# servidor.py
import asyncio
import websockets
import json
import os

CLIENTS = {}

# --- FUNÇÃO Health Check HTTP ---
async def health_check_handler(path, request_headers):
    if "Upgrade" not in request_headers or request_headers["Upgrade"] != "websocket":
        # --- CORREÇÃO APLICADA AQUI ---
        # Trocamos o dicionário {} por uma lista de tuplas [], como a biblioteca espera.
        headers = [
            ("Content-Type", "text/plain"),
            ("Access-Control-Allow-Origin", "*")
        ]
        return (200, headers, b"Server is alive and running!")
    return None

async def handler(websocket):
    client_id = str(id(websocket))
    CLIENTS[client_id] = websocket
    print(f"Novo cliente conectado: {client_id}")

    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")
            
            if action == 'move':
                data['id'] = client_id
                broadcast_message = json.dumps(data)
                for cid, ws in CLIENTS.items():
                    if cid != client_id:
                        await ws.send(broadcast_message)

    finally:
        print(f"Cliente desconectado: {client_id}")
        del CLIENTS[client_id]
        disconnect_message = json.dumps({"action": "disconnect", "id": client_id})
        for ws in CLIENTS.values():
            await ws.send(disconnect_message)

async def main():
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8765))
    
    async with websockets.serve(handler, host, port, process_request=health_check_handler):
        print(f"Servidor iniciado em ws://{host}:{port} (acessível na rede e compatível com health checks)")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())