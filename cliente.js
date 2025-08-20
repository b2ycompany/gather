// cliente.js

// --- Configurações ---
const WEBSOCKET_URI = `ws://${window.location.hostname}:8765`;

// --- Elementos do HTML ---
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const statusText = document.querySelector('h1');

canvas.width = 800;
canvas.height = 600;

// --- Estado do Jogo ---
const player = {
    id: 'local',
    x: 50,
    y: 50,
    width: 32,
    height: 32,
    color: 'red',
    speed: 5
};

const otherPlayers = {}; // Para guardar os outros jogadores

// Controlo de Teclas
const keys = {};
document.addEventListener('keydown', (e) => { keys[e.key] = true; });
document.addEventListener('keyup', (e) => { keys[e.key] = false; });

// --- Conexão WebSocket ---
console.log(`A tentar conectar-se a ${WEBSOCKET_URI}`);
const socket = new WebSocket(WEBSOCKET_URI);

socket.onopen = () => {
    console.log("Conectado ao servidor!");
    statusText.style.display = 'none';
    canvas.style.display = 'block';
    gameLoop();
};

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.action === 'move') {
        // Atualiza ou adiciona a posição do outro jogador
        otherPlayers[data.id] = data.state;
    } else if (data.action === 'disconnect') {
        // Remove o jogador que se desconectou
        console.log(`Jogador ${data.id} desconectou-se.`);
        delete otherPlayers[data.id];
    }
};

socket.onclose = () => {
    console.log("Desconectado do servidor.");
    canvas.style.display = 'none';
    statusText.textContent = 'Desconectado. Atualize a página para reconectar.';
    statusText.style.display = 'block';
};

socket.onerror = (error) => {
    console.error("Erro no WebSocket:", error);
    statusText.textContent = 'Erro de conexão. Verifique o IP e se o servidor está a correr.';
};

// --- Loop Principal do Jogo ---
function gameLoop() {
    let hasMoved = false;
    if (keys['ArrowUp']) { player.y -= player.speed; hasMoved = true; }
    if (keys['ArrowDown']) { player.y += player.speed; hasMoved = true; }
    if (keys['ArrowLeft']) { player.x -= player.speed; hasMoved = true; }
    if (keys['ArrowRight']) { player.x += player.speed; hasMoved = true; }

    if (hasMoved && socket.readyState === WebSocket.OPEN) {
        const message = {
            action: 'move',
            state: { x: player.x, y: player.y, color: player.color }
        };
        socket.send(JSON.stringify(message));
    }

    // Limpa o ecrã
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Desenha os outros jogadores
    for (const id in otherPlayers) {
        const other = otherPlayers[id];
        ctx.fillStyle = other.color || 'blue';
        ctx.fillRect(other.x, other.y, player.width, player.height);
    }
    
    // Desenha o nosso jogador
    ctx.fillStyle = player.color;
    ctx.fillRect(player.x, player.y, player.width, player.height);

    requestAnimationFrame(gameLoop);
}