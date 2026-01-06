import streamlit as st
import datetime
import folium
from streamlit_folium import st_folium

# ===============================
# CONFIG
# ===============================
st.set_page_config(page_title="AGS Delivery", layout="wide")

# ===============================
# SESSION STATE BASE
# ===============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "cart" not in st.session_state:
    st.session_state.cart = []

# ===============================
# FAKE DATABASE (MVP)
# ===============================
if "users" not in st.session_state:
    st.session_state.users = {
        "admin@ags.com": {
            "password": "admin",
            "role": "Administrador",
            "name": "Admin"
        }
    }

if "menu" not in st.session_state:
    st.session_state.menu = [
        {"id": 1, "name": "Hamburguesa", "price": 120},
        {"id": 2, "name": "Tacos", "price": 80}
    ]

if "orders" not in st.session_state:
    st.session_state.orders = []

if "chats" not in st.session_state:
    st.session_state.chats = {}

# ===============================
# LOGIN / REGISTER
# ===============================
if not st.session_state.logged_in:
    st.title("🚚 AGS Delivery")

    tab1, tab2 = st.tabs(["Login", "Registro"])

    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")

        if st.button("Entrar"):
            user = st.session_state.users.get(email)
            if user and user["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user_role = user["role"]
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

    with tab2:
        r_email = st.text_input("Nuevo email")
        r_name = st.text_input("Nombre")
        r_pass = st.text_input("Contraseña", type="password")

        if st.button("Crear cuenta"):
            st.session_state.users[r_email] = {
                "password": r_pass,
                "role": "Cliente",
                "name": r_name
            }
            st.success("Cuenta creada, ahora inicia sesión")

    st.stop()

# ===============================
# SIDEBAR
# ===============================
with st.sidebar:
    st.subheader(st.session_state.users[st.session_state.user_email]["name"])
    st.write(st.session_state.user_role)

    nav = st.radio(
        "Menú",
        ["Inicio", "Carrito", "Pedidos", "Admin"]
        if st.session_state.user_role == "Administrador"
        else ["Inicio", "Carrito", "Pedidos"]
    )

    if st.button("Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_email = None
        st.session_state.cart = []
        st.rerun()

# ===============================
# CLIENTE - MENÚ
# ===============================
if nav == "Inicio" and st.session_state.user_role == "Cliente":
    st.title("🍴 Menú")

    for item in st.session_state.menu:
        col1, col2 = st.columns([3, 1])
        col1.write(f"**{item['name']}** - ${item['price']}")
        if col2.button("Agregar", key=item["id"]):
            st.session_state.cart.append(item)
            st.toast("Agregado")

# ===============================
# CARRITO
# ===============================
if nav == "Carrito":
    st.title("🛒 Carrito")

    if not st.session_state.cart:
        st.info("Carrito vacío")
    else:
        total = 0
        for c in st.session_state.cart:
            st.write(f"- {c['name']} ${c['price']}")
            total += c["price"]

        st.write(f"### Total: ${total}")
        address = st.text_input("Dirección (Google Maps o texto)")

        if st.button("Confirmar pedido"):
            order = {
                "id": len(st.session_state.orders) + 1,
                "client": st.session_state.user_email,
                "items": st.session_state.cart.copy(),
                "total": total,
                "address": address,
                "status": "Preparando",
                "delivery": None,
                "date": datetime.datetime.now()
            }
            st.session_state.orders.append(order)
            st.session_state.cart = []
            st.success("Pedido creado")

# ===============================
# PEDIDOS
# ===============================
if nav == "Pedidos":
    st.title("📦 Pedidos")

    for o in st.session_state.orders:
        if o["client"] == st.session_state.user_email or st.session_state.user_role != "Cliente":
            with st.expander(f"Pedido #{o['id']} - {o['status']}"):
                st.write(f"Total: ${o['total']}")
                st.write(f"Dirección: {o['address']}")

                if o["status"] == "En camino":
                    m = folium.Map(location=[21.88, -102.29], zoom_start=13)
                    folium.Marker([21.88, -102.29]).add_to(m)
                    st_folium(m, height=250)

# ===============================
# ADMIN
# ===============================
if nav == "Admin" and st.session_state.user_role == "Administrador":
    st.title("⚙️ Administración")

    st.subheader("Agregar producto")
    name = st.text_input("Nombre comida")
    price = st.number_input("Precio", min_value=1)

    if st.button("Agregar"):
        st.session_state.menu.append({
            "id": len(st.session_state.menu) + 1,
            "name": name,
            "price": price
        })
        st.success("Producto agregado")

    st.subheader("Pedidos")
    for o in st.session_state.orders:
        st.write(f"Pedido #{o['id']} - {o['status']}")
        if st.button("Marcar En camino", key=f"go{o['id']}"):
            o["status"] = "En camino"
            st.rerun()
