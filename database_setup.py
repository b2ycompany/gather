# database_setup.py
import sqlite3

# Nome do ficheiro da nossa base de dados
DB_NAME = "gather_clone.db"

# Conecta-se à base de dados (se não existir, ela será criada)
conn = sqlite3.connect(DB_NAME)

# Cria um "cursor", que é o objeto que executa os comandos
cursor = conn.cursor()

# --- Criação da Tabela de Utilizadores (users) ---
# Documentação:
# id: Um número único para cada utilizador (PRIMARY KEY AUTOINCREMENT)
# username: O nome do utilizador, deve ser único (UNIQUE)
# password_hash: Onde guardaremos a palavra-passe de forma segura (nunca em texto simples!)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);
""")

# --- Criação da Tabela de Salas (rooms) ---
# Documentação:
# id: Um número único para cada sala
# owner_id: O ID do utilizador que é dono desta sala (uma FOREIGN KEY que aponta para a tabela 'users')
# name: O nome da sala (ex: "Escritório da Equipa A")
# map_data: Um campo de texto para guardar todos os dados do mapa (o conteúdo do nosso ficheiro JSON)
cursor.execute("""
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    map_data TEXT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users (id)
);
""")

# Confirma e guarda as alterações na base de dados
conn.commit()

# Fecha a conexão
conn.close()

print(f"Base de dados '{DB_NAME}' e tabelas 'users' e 'rooms' criadas ou já existentes com sucesso!")