# servidor.py
import asyncio
import websockets
import json

CLIENTS = {}

async def handler(websocket):
    client_id = str(id(websocket))
    CLIENTS[client_id] = websocket
    print(f"Novo cliente conectado: {client_id}")

    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")
            
            if action == 'move':
                # Reencaminha a mensagem de movimento para todos os outros clientes
                # Adiciona o ID do remetente para que os outros saibam quem se moveu
                data['id'] = client_id
                broadcast_message = json.dumps(data)
                for cid, ws in CLIENTS.items():
                    if cid != client_id:
                        await ws.send(broadcast_message)

    finally:
        print(f"Cliente desconectado: {client_id}")
        del CLIENTS[client_id]
        # Informa todos que o jogador saiu
        disconnect_message = json.dumps({"action": "disconnect", "id": client_id})
        for ws in CLIENTS.values():
            await ws.send(disconnect_message)

async def main():
    host = "0.0.0.0"
    port = 8765
    async with websockets.serve(handler, host, port):
        # Para saber o seu IP, use o comando 'ipconfig' no terminal
        print(f"Servidor iniciado em ws://{host}:{port} (acessível na rede local)")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())