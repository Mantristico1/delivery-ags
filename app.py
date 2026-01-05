import streamlit as st
import folium
from streamlit_folium import st_folium
import urllib.parse
import re
from PIL import Image
import io
import base64

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Delivery AGS - Pro", layout="wide")

def es_correo_valido(correo):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', correo) is not None

# Función para convertir imagen subida en algo que se pueda mostrar
def procesar_foto(subida):
    if subida is not None:
        img = Image.open(subida)
        # Redimensionar para que no pese tanto
        img.thumbnail((150, 150))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        byte_im = buf.getvalue()
        return f"data:image/png;base64,{base64.b64encode(byte_im).decode()}"
    return None

# 2. BASE DE DATOS COMPARTIDA
@st.cache_resource
def obtener_db():
    return {
        "pedidos": [],
        "usuarios": {
            "admin@delivery.com": {
                "clave": "1234", 
                "rol": "Administrador", 
                "nombre": "Manuel Montes", 
                "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
            }
        }
    }

db = obtener_db()

# 3. ESTADO DE SESIÓN
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.user_email = ""
    st.session_state.user_rol = ""

# --- LOGIN / REGISTRO ---
if not st.session_state.autenticado:
    izq, centro, der = st.columns([1, 2, 1])
    with centro:
        st.markdown("<h1 style='text-align: center;'>🚚 Delivery AGS</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔑 Entrar", "📝 Registrarse"])
        
        with tab_log:
            e_l = st.text_input("Correo:", key="l_email")
            p_l = st.text_input("Contraseña:", type="password", key="l_pass")
            if st.button("Iniciar Sesión", use_container_width=True):
                if e_l in db["usuarios"] and db["usuarios"][e_l]["clave"] == p_l:
                    st.session_state.autenticado = True
                    st.session_state.user_email = e_l
                    st.session_state.user_rol = db["usuarios"][e_l]["rol"]
                    st.rerun()
                else: st.error("Datos incorrectos")

        with tab_reg:
            r_r = st.selectbox("Rol", ["Cliente", "Repartidor"], key="r_rol")
            e_r = st.text_input("Correo electrónico:", key="r_email")
            n_r = st.text_input("Nombre Público:", key="r_name")
            p_r = st.text_input("Contraseña:", type="password", key="r_pass")
            if st.button("Crear Cuenta", use_container_width=True):
                if es_correo_valido(e_r) and n_r and p_r:
                    db["usuarios"][e_r] = {"clave": p_r, "rol": r_r, "nombre": n_r, "foto": "https://cdn-icons-png.flaticon.com/512/149/149071.png"}
                    st.success("¡Cuenta creada!")
                else: st.warning("Revisa tus datos.")
    st.stop()

# --- BARRA LATERAL ---
u_info = db["usuarios"][st.session_state.user_email]
with st.sidebar:
    st.image(u_info["foto"], width=100)
    st.title(u_info["nombre"])
    
    with st.expander("🖼️ Cambiar Foto de Perfil"):
        archivo_foto = st.file_uploader("Elige una imagen de tu galería", type=['png', 'jpg', 'jpeg'])
        if archivo_foto:
            foto_base64 = procesar_foto(archivo_foto)
            if st.button("Actualizar Foto Ahora"):
                u_info["foto"] = foto_base64
                st.rerun()

    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- VISTA: ADMINISTRADOR ---
if st.session_state.user_rol == "Administrador":
    st.title("🛠 Gestión de Pedidos")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("Nuevo Envío")
        # Diccionarios para nombres
        clientes = {u['nombre']: k for k, u in db["usuarios"].items() if u['rol'] == 'Cliente'}
        reps = {u['nombre']: k for k, u in db["usuarios"].items() if u['rol'] == 'Repartidor'}
        
        with st.form("p_form"):
            cliente_sel = st.selectbox("Cliente", list(clientes.keys()) if clientes else ["Sin clientes"])
            direccion = st.text_input("Dirección de destino")
            rep_sel = st.selectbox("Repartidor", list(reps.keys()) if reps else ["Sin repartidores"])
            if st.form_submit_button("Registrar"):
                db["pedidos"].append({
                    "id": len(db["pedidos"])+1,
                    "cliente_email": clientes[cliente_sel],
                    "cliente_nombre": cliente_sel,
                    "direccion": direccion,
                    "rep_email": reps[rep_sel],
                    "estado": "En camino"
                })
                st.rerun()
    
    with c2:
        st.subheader("Lista de Pedidos Activos")
        for p in db["pedidos"]:
            st.write(f"📦 #{p['id']} - **{p['cliente_nombre']}** -> {p['direccion']} ({p['estado']})")

# --- VISTA: REPARTIDOR / CLIENTE ---
# (Se mantienen las mismas vistas de seguimiento de mapas de la versión anterior)
