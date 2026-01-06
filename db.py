import sqlite3

DB_NAME = "ags_delivery.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        role TEXT
    )
    """)

    # Pedidos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        status TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def create_user(name, role):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, role) VALUES (?, ?)",
        (name, role)
    )
    conn.commit()
    conn.close()

def get_users_by_role(role):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE role = ?",
        (role,)
    )
    data = cursor.fetchall()
    conn.close()
    return data

def create_order(user_id, description):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (user_id, status, description) VALUES (?, 'pendiente', ?)",
        (user_id, description)
    )
    conn.commit()
    conn.close()

def get_orders():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT orders.id, users.name, orders.description, orders.status
        FROM orders
        JOIN users ON users.id = orders.user_id
        ORDER BY orders.created_at DESC
    """)
    data = cursor.fetchall()
    conn.close()
    return data
