import streamlit as st
import folium
from streamlit_folium import st_folium
import re
from PIL import Image
import io
import base64

# --- 1. CONFIGURACIÓN Y BASE DE DATOS VINCULADA ---
st.set_page_config(page_title="Delivery AGS - Sistema Seguro", layout="wide")

@st.cache_resource
def obtener_db():
    return {
        "pedidos": [],
        "usuarios": {
            "admin@delivery.com": {
                "clave": "1234", "rol": "Administrador", "nombre": "Manuel Montes", 
                "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
            }
        },
        "chats": {} 
    }

db = obtener_db()
LLAVE_STAFF = "AGS2024" # <-- Esta es la clave que solo tú sabes para nuevos trabajadores

# --- 2. FUNCIONES DE APOYO ---
def procesar_foto(subida):
    if subida:
        img = Image.open(subida)
        img.thumbnail((300, 300))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
    return None

# --- 3. ACCESO SEGURO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.u_email = ""

if not st.session_state.autenticado:
    izq, centro, der = st.columns([1, 2, 1])
    with centro:
        st.markdown("<h1 style='text-align: center;'>🚚 Delivery AGS</h1>", unsafe_allow_html=True)
        tab_log, tab_reg_cli, tab_reg_staff = st.tabs(["🔑 Entrar", "📱 Registro Cliente", "🛠 Registro Staff"])
        
        with tab_log:
            e_l = st.text_input("Correo:")
            p_l = st.text_input("Contraseña:", type="password")
            if st.button("Iniciar Sesión", use_container_width=True):
                if e_l in db["usuarios"] and db["usuarios"][e_l]["clave"] == p_l:
                    st.session_state.autenticado = True
                    st.session_state.u_email = e_l
                    st.rerun()
                else: st.error("Datos incorrectos")

        with tab_reg_cli:
            st.subheader("Cuenta para Clientes")
            e_c = st.text_input("Correo electrónico:", key="reg_e_c")
            n_c = st.text_input("Nombre completo:", key="reg_n_c")
            p_c = st.text_input("Contraseña:", type="password", key="reg_p_c")
            if st.button("Crear Cuenta Cliente", use_container_width=True):
                if e_c and n_c and p_c and e_c not in db["usuarios"]:
                    db["usuarios"][e_c] = {"clave": p_c, "rol": "Cliente", "nombre": n_c, "foto": "https://cdn-icons-png.flaticon.com/512/149/149071.png"}
                    st.success("¡Cliente registrado! Ya puedes entrar.")
                else: st.error("Error: Revisa los datos o el correo ya existe.")

        with tab_reg_staff:
            st.subheader("Solo Personal Autorizado")
            clave_maestra = st.text_input("Introduce la Llave de Invitación:", type="password")
            if clave_maestra == LLAVE_STAFF:
                e_s = st.text_input("Correo Staff:", key="reg_e_s")
                n_s = st.text_input("Nombre Staff:", key="reg_n_s")
                p_s = st.text_input("Contraseña Staff:", type="password", key="reg_p_s")
                if st.button("Crear Cuenta Repartidor"):
                    db["usuarios"][e_s] = {"clave": p_s, "rol": "Repartidor", "nombre": n_s, "foto": "https://cdn-icons-png.flaticon.com/512/149/149071.png", "disponible": True}
                    st.success("¡Repartidor registrado!")
            else:
                st.warning("Necesitas la llave del administrador para registrarte como staff.")
    st.stop()

# --- 4. INTERFAZ YA LOGUEADO ---
u_info = db["usuarios"][st.session_state.u_email]
u_rol = u_info["rol"]

with st.sidebar:
    st.image(u_info["foto"], width=100)
    st.title(u_info["nombre"])
    st.write(f"Rol: `{u_rol}`")
    menu = st.radio("Menú", ["🏠 Inicio", "💬 Chat", "⚙️ Configuración"])
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- VISTA: CONFIGURACIÓN (TODOS) ---
if menu == "⚙️ Configuración":
    st.header("Administrar Perfil")
    archivo = st.file_uploader("Cambiar mi foto (Galería)", type=['jpg', 'png', 'jpeg'])
    if archivo:
        u_info["foto"] = procesar_foto(archivo)
        st.success("Foto actualizada")
    u_info["nombre"] = st.text_input("Nombre público", value=u_info["nombre"])
    u_info["clave"] = st.text_input("Cambiar contraseña", value=u_info["clave"], type="password")
    if u_rol == "Repartidor":
        u_info["disponible"] = st.toggle("Estado: Disponible", value=u_info.get("disponible", True))
    st.button("Guardar todo")

# --- VISTA: CHAT (VINCULADO) ---
elif menu == "💬 Chat":
    st.header("Soporte y Mensajes")
    if u_rol == "Cliente":
        # Chat Cliente -> Admin
        cl_e = st.session_state.u_email
        if cl_e not in db["chats"]: db["chats"][cl_e] = []
        for m in db["chats"][cl_e]: st.chat_message("user" if m['a']=="Cliente" else "assistant").write(m['t'])
        msg = st.chat_input("Escribe al administrador...")
        if msg:
            db["chats"][cl_e].append({"a": "Cliente", "t": msg})
            st.rerun()
    elif u_rol == "Administrador":
        # Admin ve todos los chats
        for cl_e, msgs in db["chats"].items():
            with st.expander(f"Chat con {db['usuarios'][cl_e]['nombre']}"):
                for m in msgs: st.write(f"**{m['a']}:** {m['t']}")
                resp = st.text_input("Responder:", key=f"r_{cl_e}")
                if st.button("Enviar", key=f"b_{cl_e}"):
                    db["chats"][cl_e].append({"a": "Admin", "t": resp})
                    st.rerun()

# --- VISTA: INICIO (FUNCIONALIDAD) ---
elif menu == "🏠 Inicio":
    if u_rol == "Administrador":
        st.title("Panel Maestro")
        clientes = {u['nombre']: k for k, u in db["usuarios"].items() if u['rol'] == 'Cliente'}
        reps = {u['nombre']: k for k, u in db["usuarios"].items() if u['rol'] == 'Repartidor' and u.get('disponible', True)}
        with st.form("p"):
            c = st.selectbox("Cliente", list(clientes.keys()))
            d = st.text_input("Dirección")
            r = st.selectbox("Repartidor", list(reps.keys()))
            if st.form_submit_button("Crear Pedido"):
                db["pedidos"].append({"id": len(db["pedidos"])+1, "cl_e": clientes[c], "cl_n": c, "rep_e": reps[r], "dir": d, "est": "En camino"})
                st.rerun()
        st.write("### Pedidos")
        st.table(db["pedidos"])

    elif u_rol == "Repartidor":
        st.title("Mis Entregas")
        mis = [p for p in db["pedidos"] if p["rep_e"] == st.session_state.u_email and p["est"] == "En camino"]
        for p in mis:
            st.info(f"Pedido #{p['id']} para {p['cl_n']} en {p['dir']}")
            if st.button("✅ Finalizar"):
                p["est"] = "Entregado"
                st.rerun()

    elif u_rol == "Cliente":
        st.title("Mi Pedido")
        mi = next((p for p in db["pedidos"] if p["cl_e"] == st.session_state.u_email and p["est"] == "En camino"), None)
        if mi: st.success(f"Tu pedido va en camino a: {mi['dir']}")
        else: st.info("No tienes pedidos activos.")
