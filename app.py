import streamlit as st
import folium
from streamlit_folium import st_folium
import datetime
import pandas as pd
from PIL import Image
import io
import base64
import pickle
import os

# ===============================
# CONFIG
# ===============================
st.set_page_config(page_title="AGS Delivery - Versión Estable", layout="wide")

DB_FILE = "db.pkl"

# ===============================
# PERSISTENCIA
# ===============================
def save_db(db):
    with open(DB_FILE, "wb") as f:
        pickle.dump(db, f)

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "rb") as f:
            return pickle.load(f)
    return {
        "usuarios": {
            "admin@delivery.com": {
                "clave": "1234",
                "rol": "Administrador",
                "nombre": "Manuel Montes",
                "foto": None,
                "activo": True
            }
        },
        "menu": [
            {
                "id": 1,
                "nombre": "Hamburguesa AGS",
                "desc": "Carne premium, doble queso y papas",
                "precio": 120.0,
                "foto": None
            }
        ],
        "pedidos": [],
        "chats": {}
    }

# ===============================
# BASE DE DATOS
# ===============================
if "db" not in st.session_state:
    st.session_state.db = load_db()

db = st.session_state.db

# ===============================
# UTILIDADES
# ===============================
def get_img_64(file):
    if file:
        img = Image.open(file)
        img.thumbnail((400, 400))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
    return None

# ===============================
# AUTH
# ===============================
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.u_email = ""
    st.session_state.carrito = []

# ===============================
# LOGIN
# ===============================
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.title("🚚 AGS Delivery")
        t_login, t_reg = st.tabs(["Ingresar", "Registro Clientes"])

        with t_login:
            e = st.text_input("Correo")
            p = st.text_input("Clave", type="password")
            if st.button("ENTRAR", use_container_width=True):
                user = db["usuarios"].get(e)
                if user and user["clave"] == p and user["activo"]:
                    st.session_state.auth = True
                    st.session_state.u_email = e
                    save_db(db)
                    st.rerun()
                else:
                    st.error("Acceso denegado o cuenta inactiva.")

        with t_reg:
            re = st.text_input("Email Nuevo")
            rn = st.text_input("Nombre Completo")
            rp = st.text_input("Contraseña", type="password")
            if st.button("Crear Cuenta"):
                db["usuarios"][re] = {
                    "clave": rp,
                    "rol": "Cliente",
                    "nombre": rn,
                    "foto": None,
                    "activo": True
                }
                save_db(db)
                st.success("Registrado correctamente.")

    st.stop()

u_info = db["usuarios"][st.session_state.u_email]
u_rol = u_info["rol"]

# ===============================
# SIDEBAR
# ===============================
with st.sidebar:
    st.image(
        u_info["foto"]
        if u_info["foto"]
        else "https://cdn-icons-png.flaticon.com/512/149/149071.png",
        width=80
    )
    st.subheader(u_info["nombre"])
    st.write(f"Rol: **{u_rol}**")
    st.divider()

    opciones = ["🏠 Inicio"]
    if u_rol == "Administrador":
        opciones += ["👥 Gestión Usuarios", "🍴 Gestión Menú"]
    if u_rol == "Trabajador":
        opciones += ["🍴 Gestión Menú"]
    if u_rol == "Repartidor":
        opciones += ["🛵 Mis Entregas"]
    if u_rol == "Cliente":
        opciones += ["🛒 Mi Carrito", "🎫 Mis Tickets"]
    opciones += ["⚙️ Configuración"]

    nav = st.radio("Navegación", opciones)

    if st.button("🚪 Cerrar Sesión"):
        st.session_state.auth = False
        save_db(db)
        st.rerun()

# ===============================
# CONFIGURACIÓN
# ===============================
if nav == "⚙️ Configuración":
    st.header("⚙️ Ajustes de Cuenta")
    u_info["nombre"] = st.text_input("Nombre", value=u_info["nombre"])
    u_info["clave"] = st.text_input("Clave", value=u_info["clave"], type="password")
    f = st.file_uploader("Foto de perfil")
    if f:
        u_info["foto"] = get_img_64(f)
    if st.button("Guardar cambios"):
        save_db(db)
        st.success("Perfil actualizado")

# ===============================
# CLIENTE - MENÚ
# ===============================
elif nav == "🏠 Inicio" and u_rol == "Cliente":
    st.title("🍴 Menú AGS")
    cols = st.columns(2)

    for i, item in enumerate(db["menu"]):
        with cols[i % 2]:
            with st.container(border=True):
                if item["foto"]:
                    st.image(item["foto"], use_column_width=True)
                st.subheader(item["nombre"])
                st.write(item["desc"])
                st.write(f"### ${item['precio']}")
                if st.button("🛒 Agregar", key=f"add_{item['id']}"):
                    st.session_state.carrito.append(item)
                    st.toast("Producto agregado")

# ===============================
# CARRITO
# ===============================
elif nav == "🛒 Mi Carrito":
    st.title("🛒 Tu Pedido")

    if st.session_state.carrito:
        total = sum(i["precio"] for i in st.session_state.carrito)
        st.table(pd.DataFrame(st.session_state.carrito)[["nombre", "precio"]])
        st.write(f"## Total: ${total}")

        dir_p = st.text_input("Dirección de entrega")

        if st.button("Confirmar Pedido"):
            db["pedidos"].append({
                "id": len(db["pedidos"]) + 1,
                "cl_e": st.session_state.u_email,
                "cl_n": u_info["nombre"],
                "items": st.session_state.carrito.copy(),
                "total": total,
                "dir": dir_p,
                "est": "Preparando",
                "rep": None,
                "fecha": datetime.datetime.now(),
                "eta": "40-50 min"
            })
            st.session_state.carrito = []
            save_db(db)
            st.success("Pedido enviado")

    else:
        st.info("Carrito vacío")

# ===============================
# LO DEMÁS (tickets, repartidor, admin, chat)
# ===============================
# 👉 NO CAMBIÓ, solo guarda con save_db(db) después de cada acción


