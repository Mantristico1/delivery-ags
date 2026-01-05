import streamlit as st
import folium
from streamlit_folium import st_folium
import datetime
import pandas as pd
from PIL import Image
import io
import base64

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="AGS Food & Delivery", layout="wide")

# Lógica de Modo Claro/Oscuro (Sencilla para Streamlit)
if 'tema_oscuro' not in st.session_state:
    st.session_state.tema_oscuro = False

def alternar_tema():
    st.session_state.tema_oscuro = not st.session_state.tema_oscuro

# --- 2. BASE DE DATOS MAESTRA (VINCULADA) ---
@st.cache_resource
def inicializar_sistema():
    return {
        "usuarios": {
            "admin@delivery.com": {"clave": "1234", "rol": "Administrador", "nombre": "Manuel Montes", "foto": None, "activo": True},
        },
        "menu": [
            {"id": 1, "nombre": "Hamburguesa AGS", "desc": "Carne premium y queso", "precio": 120.0, "foto": None},
            {"id": 2, "nombre": "Tacos al Pastor", "desc": "Orden de 5 tacos", "precio": 85.0, "foto": None}
        ],
        "pedidos": [],
        "chats": {}, # {id_pedido: [{"autor": "", "rol": "", "txt": ""}]}
        "carrito": {} # {email_cliente: [items]}
    }

db = inicializar_sistema()

# --- 3. FUNCIONES DE UTILIDAD ---
def procesar_imagen(archivo):
    if archivo:
        img = Image.open(archivo)
        img.thumbnail((400, 400))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
    return None

# --- 4. SISTEMA DE AUTENTICACIÓN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.email = ""

if not st.session_state.auth:
    st.title("🚚 AGS Delivery System")
    t1, t2 = st.tabs(["Ingresar", "Registrarse (Solo Clientes)"])
    with t1:
        e = st.text_input("Email")
        p = st.text_input("Clave", type="password")
        if st.button("Entrar"):
            user = db["usuarios"].get(e)
            if user and user["clave"] == p and user["activo"]:
                st.session_state.auth = True
                st.session_state.email = e
                st.rerun()
            else: st.error("Acceso denegado o cuenta desactivada.")
    with t2:
        st.write("Crea tu cuenta de cliente")
        new_e = st.text_input("Tu Email")
        new_n = st.text_input("Tu Nombre")
        new_p = st.text_input("Tu Clave", type="password")
        if st.button("Crear Cuenta"):
            if new_e and new_n and new_p:
                db["usuarios"][new_e] = {"clave": new_p, "rol": "Cliente", "nombre": new_n, "foto": None, "activo": True}
                st.success("¡Registrado!")
    st.stop()

u_info = db["usuarios"][st.session_state.email]
u_rol = u_info["rol"]

# --- 5. SIDEBAR Y MODO OSCURO ---
with st.sidebar:
    st.image(u_info["foto"] if u_info["foto"] else "https://cdn-icons-png.flaticon.com/512/149/149071.png", width=100)
    st.title(u_info["nombre"])
    st.write(f"Rol: **{u_rol}**")
    
    # Selector de Navegación según Rol
    paginas = ["🏠 Inicio", "⚙️ Mi Perfil"]
    if u_rol in ["Administrador", "Trabajador"]:
        paginas += ["🍴 Gestionar Menú", "📊 Panel Staff", "👥 Usuarios"]
    elif u_rol == "Cliente":
        paginas += ["🛒 Comprar Comida", "📜 Mis Tickets"]
    
    opcion = st.radio("Navegar", paginas)
    
    st.divider()
    if st.button("🌓 Cambiar Tema"):
        alternar_tema()
    if st.button("🚪 Salir"):
        st.session_state.auth = False
        st.rerun()

# --- 6. LÓGICA DE ROLES ---

# A. CLIENTE: COMPRA Y TICKET
if opcion == "🛒 Comprar Comida":
    st.title("🍴 Menú Digital")
    cols = st.columns(len(db["menu"]))
    if st.session_state.email not in db["carrito"]: db["carrito"][st.session_state.email] = []
    
    for i, item in enumerate(db["menu"]):
        with cols[i]:
            if item["foto"]: st.image(item["foto"])
            st.subheader(item["nombre"])
            st.write(f"{item['desc']}")
            st.write(f"**${item['precio']}**")
            if st.button(f"Añadir", key=f"add_{item['id']}"):
                db["carrito"][st.session_state.email].append(item)
                st.toast(f"{item['nombre']} agregado")

    st.divider()
    st.header("🛒 Tu Carrito")
    carrito_actual = db["carrito"][st.session_state.email]
    if carrito_actual:
        total = sum(i['precio'] for i in carrito_actual)
        st.table(pd.DataFrame(carrito_actual))
        st.write(f"### Total a pagar: ${total}")
        direc = st.text_input("¿A dónde lo enviamos? (Dirección exacta)")
        if st.button("Confirmar Pedido (Efectivo)"):
            nuevo_p = {
                "id": len(db["pedidos"]) + 1,
                "cliente": st.session_state.email,
                "nombre_cliente": u_info["nombre"],
                "items": carrito_actual.copy(),
                "total": total,
                "direccion": direc,
                "estado": "Recibido",
                "repartidor": None,
                "fecha": datetime.datetime.now().strftime("%H:%M"),
                "lat": 21.88, "lon": -102.29
            }
            db["pedidos"].append(nuevo_p)
            db["carrito"][st.session_state.email] = []
            st.success("¡Pedido enviado! Generando ticket...")
            st.rerun()

# B. TRABAJADOR Y ADMIN: GESTIÓN DE MENÚ Y STAFF
elif opcion == "🍴 Gestionar Menú":
    st.title("🥘 Administración de Platillos")
    with st.expander("➕ Agregar nuevo platillo"):
        n = st.text_input("Nombre")
        d = st.text_area("Descripción")
        p = st.number_input("Precio", min_value=0.0)
        f = st.file_uploader("Foto del platillo")
        if st.button("Guardar en Menú"):
            db["menu"].append({"id": len(db["menu"])+1, "nombre": n, "desc": d, "precio": p, "foto": procesar_imagen(f)})
            st.rerun()
    
    st.write("### Menú Actual")
    for i, item in enumerate(db["menu"]):
        col_n, col_p, col_acc = st.columns([3, 1, 1])
        col_n.write(item["nombre"])
        col_p.write(f"${item['precio']}")
        if col_acc.button("Eliminar", key=f"del_m_{i}"):
            db["menu"].pop(i)
            st.rerun()

elif opcion == "📊 Panel Staff":
    st.title("📋 Control de Pedidos y Logística")
    
    for p in db["pedidos"]:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 2])
            with c1:
                st.write(f"**Pedido #{p['id']}** - {p['nombre_cliente']}")
                st.write(f"📍 {p['direccion']}")
                st.write(f"💰 Total: ${p['total']}")
            with c2:
                # Lógica de asignación inteligente
                reps_dispo = {u['nombre']: k for k, u in db["usuarios"].items() if u['rol'] == 'Repartidor' and u.get('disponible', True)}
                if not p["repartidor"]:
                    rep_sel = st.selectbox("Asignar Repartidor", list(reps_dispo.keys()), key=f"sel_{p['id']}")
                    if st.button("Asignar y Enviar", key=f"asig_{p['id']}"):
                        # Calcular pedidos pendientes del repartidor
                        pendientes = len([x for x in db["pedidos"] if x['repartidor'] == reps_dispo[rep_sel] and x['estado'] != "Entregado"])
                        p["repartidor"] = reps_dispo[rep_sel]
                        p["estado"] = "En camino"
                        st.info(f"Asignado a {rep_sel}. Tiene {pendientes} pedidos antes.")
                        st.rerun()
                else:
                    st.write(f"🚚 Repartidor: {db['usuarios'][p['repartidor']]['nombre']}")
                    st.write(f"Estado: **{p['estado']}**")
            with c3:
                # Chat específico del pedido
                if st.button("💬 Abrir Chat Pedido", key=f"chat_{p['id']}"):
                    st.session_state.chat_abierto = p['id']

# C. ADMINISTRADOR: GESTIÓN DE USUARIOS
elif opcion == "👥 Usuarios":
    st.title("👤 Gestión de Usuarios (Manuel Montes)")
    if u_rol == "Administrador":
        for email, info in db["usuarios"].items():
            col_u, col_r, col_a = st.columns([2, 2, 1])
            col_u.write(f"**{info['nombre']}** ({email})")
            col_r.write(f"Rol: {info['rol']}")
            if info["activo"]:
                if col_a.button("Dar de Baja", key=f"baja_{email}"):
                    info["activo"] = False
                    st.rerun()
            else:
                if col_a.button("Activar", key=f"alta_{email}"):
                    info["activo"] = True
                    st.rerun()
        
        st.divider()
        st.subheader("Registrar Nuevo Trabajador/Repartidor")
        with st.form("new_staff"):
            ne = st.text_input("Email Staff")
            nn = st.text_input("Nombre Staff")
            np = st.text_input("Clave Staff")
            nr = st.selectbox("Rol", ["Trabajador", "Repartidor"])
            if st.form_submit_button("Crear Staff"):
                db["usuarios"][ne] = {"clave": np, "rol": nr, "nombre": nn, "foto": None, "activo": True, "disponible": True}
                st.success("Staff creado.")
    else:
        st.error("Solo Manuel Montes tiene acceso aquí.")

# --- 7. SISTEMA DE CHAT DIFERENCIADO ---
if 'chat_abierto' in st.session_state:
    id_p = st.session_state.chat_abierto
    st.divider()
    st.subheader(f"💬 Chat del Pedido #{id_p}")
    if id_p not in db["chats"]: db["chats"][id_p] = []
    
    for m in db["chats"][id_p]:
        color = "blue" if m["rol"] == "Cliente" else "green" if m["rol"] == "Repartidor" else "orange"
        st.markdown(f"<span style='color:{color}'>**[{m['rol']}] {m['autor']}:**</span> {m['txt']}", unsafe_allow_html=True)
    
    msg = st.chat_input("Escribe tu mensaje...")
    if msg:
        db["chats"][id_p].append({"autor": u_info["nombre"], "rol": u_rol, "txt": msg})
        st.rerun()
    if st.button("Cerrar Ventana de Chat"):
        del st.session_state.chat_abierto
        st.rerun()
