import sqlite3

DB_NAME = "ags_delivery.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    def get_user(email):
    """Fetches a user and their store context."""
    cursor = conn.cursor()
    cursor.execute("SELECT email, password, role, name, is_active, store_id FROM users WHERE email=?", (email,))
    return cursor.fetchone()

def get_menu_by_store(store_id):
    """Retrieves only the menu items for the specific store."""
    query = "SELECT id, name, price, description, image_64 FROM menu WHERE store_id = ?"
    return pd.read_sql_query(query, conn, params=(store_id,))

def create_store(name, slug):
    """Utility to register a new store in the SaaS."""
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO stores (name, slug) VALUES (?, ?)", (name, slug))
    conn.commit()
    return cursor.lastrowid
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
