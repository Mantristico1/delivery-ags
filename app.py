import streamlit as st
from db import (
    init_db,
    create_user,
    create_order,
    get_users_by_role,
    get_orders
)

init_db()

import streamlit as st
import folium
from streamlit_folium import st_folium
import datetime
import pandas as pd
from PIL import Image
import io
import base64

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="AGS Delivery - Sistema Maestro", layout="wide")

def get_img_64(file):
    if file:
        img = Image.open(file)
        img.thumbnail((400, 400))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
    return None

# --- BASE DE DATOS CON PERSISTENCIA ---
if 'db' not in st.session_state:
    st.session_state.db = {
        "usuarios": {
            "admin@delivery.com": {"clave": "1234", "rol": "Administrador", "nombre": "Manuel Montes", "foto": None, "activo": True},
        },
        "menu": [
            {"id": 1, "nombre": "Hamburguesa AGS", "desc": "Premium, queso y papas", "precio": 120.0, "foto": None}
        ],
        "pedidos": [],
        "chats": {}
    }

db = st.session_state.db

# --- SISTEMA DE LOGIN / REGISTRO ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.u_email = ""
    st.session_state.carrito = []

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
                    st.rerun()
                else: st.error("Acceso denegado.")
        with t_reg:
            re = st.text_input("Nuevo Correo")
            rn = st.text_input("Nombre")
            rp = st.text_input("Contraseña", type="password")
            if st.button("Crear Cuenta"):
                db["usuarios"][re] = {"clave": rp, "rol": "Cliente", "nombre": rn, "foto": None, "activo": True}
                st.success("¡Registrado!")
    st.stop()

u_info = db["usuarios"][st.session_state.u_email]
u_rol = u_info["rol"]

# --- BARRA LATERAL ---
with st.sidebar:
    st.image(u_info["foto"] if u_info["foto"] else "https://cdn-icons-png.flaticon.com/512/149/149071.png", width=80)
    st.subheader(u_info["nombre"])
    st.write(f"Rol: **{u_rol}**")
    st.divider()
    
    opciones = ["🏠 Inicio"]
    if u_rol == "Administrador": opciones += ["👥 Gestión Usuarios", "🍴 Gestión Menú"]
    if u_rol == "Trabajador": opciones += ["🍴 Gestión Menú"]
    if u_rol == "Repartidor": opciones += ["🛵 Mis Entregas"]
    if u_rol == "Cliente": opciones += ["🛒 Mi Carrito", "🎫 Mis Tickets"]
    opciones += ["⚙️ Configuración"]
    
    nav = st.radio("Navegación", opciones)
    
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

# --- 1. CONFIGURACIÓN DE PERFIL ---
if nav == "⚙️ Configuración":
    st.header("⚙️ Ajustes de Cuenta")
    u_info["nombre"] = st.text_input("Nombre", value=u_info["nombre"])
    u_info["clave"] = st.text_input("Clave", value=u_info["clave"], type="password")
    f = st.file_uploader("Foto de perfil")
    if f: u_info["foto"] = get_img_64(f)
    if st.button("Guardar"): st.success("Actualizado")

# --- 2. CLIENTE: MENÚ AL INICIO ---
elif nav == "🏠 Inicio" and u_rol == "Cliente":
    st.title("🍴 Menú AGS Food")
    cols = st.columns(2)
    for i, item in enumerate(db["menu"]):
        with cols[i % 2]:
            with st.container(border=True):
                if item["foto"]: st.image(item["foto"], use_column_width=True)
                st.subheader(item["nombre"])
                st.write(item["desc"])
                st.write(f"### ${item['precio']}")
                if st.button("🛒 Agregar", key=f"add_{item['id']}"):
                    st.session_state.carrito.append(item)
                    st.toast("Agregado al carrito")

elif nav == "🛒 Mi Carrito":
    st.title("🛒 Tu Carrito")
    if st.session_state.carrito:
        total = sum(i['precio'] for i in st.session_state.carrito)
        st.table(pd.DataFrame(st.session_state.carrito)[['nombre', 'precio']])
        st.write(f"## Total: ${total}")
        dir_p = st.text_input("Dirección (📍 Puedes poner link de Maps)")
        if st.button("Confirmar Pedido (Efectivo)"):
            new_p = {
                "id": len(db["pedidos"]) + 1, "cl_e": st.session_state.u_email, "cl_n": u_info["nombre"],
                "items": st.session_state.carrito.copy(), "total": total, "dir": dir_p,
                "est": "Preparando", "rep": None, "fecha": datetime.datetime.now(), "eta": "45 min"
            }
            db["pedidos"].append(new_p)
            st.session_state.carrito = []
            st.success("¡Pedido enviado!")
    else: st.info("Carrito vacío.")

elif nav == "🎫 Mis Tickets":
    st.header("🎫 Mis Pedidos y Tickets")
    mis = [p for p in db["pedidos"] if p["cl_e"] == st.session_state.u_email]
    for p in reversed(mis):
        with st.expander(f"Ticket #{p['id']} - {p['est']}"):
            st.write(f"**Fecha:** {p['fecha']}")
            st.write(f"**Costo:** ${p['total']} | **Entrega en:** {p['eta']}")
            st.write("**Detalle:**")
            for it in p["items"]: st.write(f"- {it['nombre']}: {it['desc']}")
            if p["est"] == "En camino":
                st.warning("🛵 El repartidor va hacia ti.")
                m = folium.Map(location=[21.88, -102.29], zoom_start=14)
                folium.Marker([21.88, -102.29], icon=folium.Icon(color='orange', icon='motorcycle', prefix='fa')).add_to(m)
                st_folium(m, height=200, key=f"map_{p['id']}")
            if st.button("💬 Chat con Staff", key=f"chat_cl_{p['id']}"): st.session_state.chat_id = p['id']

# --- 3. REPARTIDOR: MIS ENTREGAS ---
elif nav == "🛵 Mis Entregas" and u_rol == "Repartidor":
    st.title("🛵 Mis Órdenes")
    mis_v = [p for p in db["pedidos"] if p["rep"] == st.session_state.u_email and p["est"] != "Entregado"]
    if not mis_v: st.info("Sin pedidos asignados.")
    for p in mis_v:
        with st.container(border=True):
            st.subheader(f"Pedido #{p['id']} - {p['cl_n']}")
            st.write(f"📍 {p['dir']}")
            st.link_button("🗺️ Abrir Google Maps", f"https://www.google.com/maps/search/?api=1&query={p['dir'].replace(' ', '+')}")
            if st.button("✅ Finalizar Entrega", key=f"ent_{p['id']}"):
                p["est"] = "Entregado"
                st.rerun()
            if st.button("💬 Chat con Cliente", key=f"chat_rep_{p['id']}"): st.session_state.chat_id = p['id']

# --- 4. TRABAJADOR / ADMIN: PEDIDOS Y MENÚ ---
elif nav == "🏠 Inicio" and u_rol in ["Administrador", "Trabajador"]:
    st.title("📋 Gestión de Pedidos")
    for p in db["pedidos"]:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                st.write(f"**#{p['id']} - {p['cl_n']}**")
                st.write(f"📍 {p['dir']}")
            with c2:
                if not p["rep"]:
                    reps = {u['nombre']: k for k, u in db["usuarios"].items() if u['rol'] == 'Repartidor'}
                    opc = [f"{n} (En cola: {len([x for x in db['pedidos'] if x['rep']==k and x['est']!='Entregado'])})" for n, k in reps.items()]
                    sel_r = st.selectbox("Asignar:", opc, key=f"as_{p['id']}")
                    if st.button("Enviar", key=f"send_{p['id']}"):
                        p["rep"] = reps[sel_r.split(" (")[0]]
                        p["est"] = "En camino"
                        st.rerun()
                else: st.write(f"🛵 Repartidor: {db['usuarios'][p['rep']]['nombre']} ({p['est']})")
            with c3:
                if st.button("💬 Chat", key=f"chat_st_{p['id']}"): st.session_state.chat_id = p['id']

elif nav == "🍴 Gestión Menú":
    st.title("🍴 Administración del Menú")
    with st.expander("➕ Añadir Platillo"):
        nom = st.text_input("Nombre")
        desc = st.text_area("Descripción")
        prec = st.number_input("Precio")
        foto = st.file_uploader("Foto")
        if st.button("Guardar"):
            db["menu"].append({"id": len(db["menu"])+1, "nombre": nom, "desc": desc, "precio": prec, "foto": get_img_64(foto)})
            st.rerun()
    for i, item in enumerate(db["menu"]):
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{item['nombre']}** - ${item['precio']}")
            if col2.button("🗑️ Borrar", key=f"del_{i}"):
                db["menu"].pop(i)
                st.rerun()
from db import (
    init_db,
    create_user,
    create_order,
    get_users_by_role,
    get_orders
)

# Inicializar DB
init_db()

# --- 5. ADMIN: GESTIÓN DE USUARIOS ---
elif nav == "👥 Gestión Usuarios" and u_rol == "Administrador":
    st.title("👥 Panel de Usuarios")
    t_reg, t_gest = st.tabs(["Registrar Staff", "Gestión"])
    with t_reg:
        with st.form("new_staff"):
            ne, nn, np = st.text_input("Email"), st.text_input("Nombre"), st.text_input("Clave")
            nr = st.selectbox("Rol", ["Trabajador", "Repartidor"])
            if st.form_submit_button("Dar de Alta"):
                db["usuarios"][ne] = {"clave": np, "rol": nr, "nombre": nn, "foto": None, "activo": True}
                st.success("Staff creado.")
    with t_gest:
        f_rol = st.selectbox("Filtrar:", ["Clientes", "Repartidores", "Trabajadores"])
        for em, info in db["usuarios"].items():
            if f_rol[:-1] in info["rol"]:
                c1, c2 = st.columns([3, 1])
                c1.write(f"{info['nombre']} ({em}) - {info['rol']}")
                if c2.button("Alta/Baja", key=f"stat_{em}"):
                    info["activo"] = not info["activo"]
                    st.rerun()
st.set_page_config(page_title="Delivery AGS", layout="centered")

st.title("🚴 Delivery AGS")

menu = st.sidebar.selectbox(
    "Selecciona tu rol",
    ["Cliente", "Cocina", "Repartidor"]
)
if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# ---------------- CLIENTE ----------------
if menu == "Cliente":
    st.subheader("📦 Nuevo Pedido")

    nombre = st.text_input("Tu nombre")
    pedido = st.text_area("¿Qué vas a pedir?")

    if st.button("Enviar pedido"):
        if nombre and pedido:
            create_user(nombre, "cliente")
            user_id = get_users_by_role("cliente")[-1][0]
            create_order(user_id, pedido)
            st.success("Pedido enviado correctamente 🚀")
        else:
            st.warning("Completa todos los campos")

# ---------------- COCINA ----------------
elif menu == "Cocina":
    st.subheader("👨‍🍳 Pedidos entrantes")

    pedidos = get_orders()

    if pedidos:
        for p in pedidos:
            st.markdown(f"""
            **Pedido #{p[0]}**  
            Cliente: {p[1]}  
            Pedido: {p[2]}  
            Estado: {p[3]}
            ---
            """)
    else:
        st.info("No hay pedidos aún")

# ---------------- REPARTIDOR ----------------
elif menu == "Repartidor":
    st.subheader("🛵 Pedidos para entregar")

    pedidos = get_orders()

    if pedidos:
        for p in pedidos:
            st.markdown(f"""
            **Pedido #{p[0]}**  
            Cliente: {p[1]}  
            Pedido: {p[2]}  
            Estado: {p[3]}
            ---
            """)
    else:
        st.info("No hay pedidos disponibles")

# --- CHAT MULTICOLOR ---
if 'chat_id' in st.session_state:
    id_p = st.session_state.chat_id
    st.divider()
    st.subheader(f"💬 Chat Pedido #{id_p}")
    if id_p not in db["chats"]: db["chats"][id_p] = []
    for m in db["chats"][id_p]:
        color = "#e3f2fd" if m["rol"] == "Cliente" else "#f1f8e9" if m["rol"] == "Repartidor" else "#fff3e0"
        st.markdown(f"<div style='background-color:{color}; padding:10px; border-radius:10px; margin:5px; color:black;'><b>{m['rol']} - {m['autor']}:</b> {m['txt']}</div>", unsafe_allow_html=True)
    txt = st.chat_input("Escribe...")
    if txt:
        db["chats"][id_p].append({"autor": u_info["nombre"], "rol": u_rol, "txt": txt})
        st.rerun()
    if st.button("Cerrar Chat"):
        del st.session_state.chat_id
