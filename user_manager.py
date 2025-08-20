# user_manager.py
import sqlite3
import hashlib
import json

DB_NAME = "gather_clone.db"

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_user(username):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user_data = cursor.fetchone()
    conn.close()
    return user_data

def add_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    password_hash = hash_password(password)
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def check_user(username, password):
    user_data = get_user(username)
    if user_data:
        stored_password_hash = user_data['password_hash']
        if stored_password_hash == hash_password(password):
            return True
    return False

def add_room(owner_id, room_name, map_data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    map_data_json = json.dumps(map_data)
    try:
        cursor.execute("INSERT INTO rooms (owner_id, name, map_data) VALUES (?, ?, ?)", 
                       (owner_id, room_name, map_data_json))
        conn.commit()
        print(f"Sala '{room_name}' guardada com sucesso para o utilizador ID {owner_id}!")
        return True
    except Exception as e:
        print(f"Erro ao guardar a sala: {e}")
        return False
    finally:
        conn.close()

def get_rooms_for_user(owner_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM rooms WHERE owner_id = ?", (owner_id,))
    rooms = cursor.fetchall()
    conn.close()
    return [dict(room) for room in rooms]

# --- NOVA FUNÇÃO ---
def get_room_data(room_id):
    """Obtém os dados completos de um mapa de uma sala específica."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT map_data FROM rooms WHERE id = ?", (room_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        # Converte a string JSON de volta para um dicionário Python
        return json.loads(result['map_data'])
    return None

# O bloco de teste não é mais necessário, pode ser removido ou comentado
# if __name__ == "__main__":
#     ...