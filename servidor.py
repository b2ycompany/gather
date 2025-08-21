# servidor.py
import asyncio
import websockets
import json
import os # <-- Nova importação para aceder a variáveis de ambiente

CLIENTS = {}

# --- NOVA FUNÇÃO: Health Check HTTP ---
# Esta função vai intercetar os pedidos. Se for um pedido HTTP normal,
# ela responde com "OK". Se não, ela deixa o WebSocket continuar.
async def health_check_handler(path, request_headers):
    if "Upgrade" not in request_headers or request_headers["Upgrade"] != "websocket":
        # Isto é um pedido HTTP normal (o teste de saúde do Render)
        headers = {
            "Content-Type": "text/plain",
            "Access-Control-Allow-Origin": "*" # Permite que o browser aceda
        }
        return (200, headers, b"Server is alive and running!")
    # Se for um pedido WebSocket, não fazemos nada e deixamos a biblioteca continuar
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
    # O Render define a porta através de uma variável de ambiente.
    # Se não estiver no Render, usamos a porta 8765 por padrão.
    port = int(os.environ.get("PORT", 8765))
    
    # Adicionamos o 'process_request' para lidar com o teste de saúde
    async with websockets.serve(handler, host, port, process_request=health_check_handler):
        print(f"Servidor iniciado em ws://{host}:{port} (acessível na rede e compatível com health checks)")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())