import streamlit as st
import folium
from streamlit_folium import st_folium
import urllib.parse
import re
from PIL import Image
import io
import base64

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="Delivery AGS - Sistema Integral", layout="wide")

# Función para validar email
def es_correo_valido(correo):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', correo) is not None

# Función para procesar foto de galería
def procesar_foto(subida):
    if subida is not None:
        img = Image.open(subida)
        img.thumbnail((300, 300))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
    return None

# --- MEMORIA COMPARTIDA (EL VÍNCULO TOTAL) ---
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
        "chats": {} # {email_cliente: [lista_mensajes]}
    }

db = obtener_db()

# --- ESTADO DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.u_email = ""
    st.session_state.u_rol = ""

# --- PANTALLA DE ACCESO (LOGIN/REGISTRO) ---
if not st.session_state.autenticado:
    izq, centro, der = st.columns([1, 2, 1])
    with centro:
        st.markdown("<h1 style='text-align: center;'>🚚 Delivery AGS</h1>", unsafe_allow_html=True)
        t_log, t_reg = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
        
        with t_log:
            e_l = st.text_input("Correo:", key="l_e")
            p_l = st.text_input("Contraseña:", type="password", key="l_p")
            if st.button("Entrar", use_container_width=True):
                if e_l in db["usuarios"] and db["usuarios"][e_l]["clave"] == p_l:
                    st.session_state.autenticado = True
                    st.session_state.u_email = e_l
                    st.session_state.u_rol = db["usuarios"][e_l]["rol"]
                    st.rerun()
                else: st.error("Datos incorrectos")

        with t_reg:
            st.info("Clientes y Repartidores: Regístrense aquí")
            r_r = st.selectbox("¿Qué serás?", ["Cliente", "Repartidor"], key="r_r")
            e_r = st.text_input("Correo:", key="r_e")
            n_r = st.text_input("Nombre Público:", key="r_n")
            p_r = st.text_input("Contraseña:", type="password", key="r_p")
            if st.button("Crear Cuenta", use_container_width=True):
                if es_correo_valido(e_r) and n_r and p_r:
                    db["usuarios"][e_r] = {"clave": p_r, "rol": r_r, "nombre": n_r, "foto": "https://cdn-icons-png.flaticon.com/512/149/149071.png", "disponible": True}
                    st.success("¡Cuenta creada! Ya puedes entrar.")
                else: st.error("Datos inválidos.")
    st.stop()

# --- NAVEGACIÓN SEGÚN ROL ---
u_info = db["usuarios"][st.session_state.u_email]

with st.sidebar:
    st.image(u_info["foto"], width=100)
    st.title(u_info["nombre"])
    st.write(f"💼 {st.session_state.u_rol}")
    st.divider()
    
    # Menú inteligente: El cliente no ve las opciones del staff
    opciones = ["🏠 Inicio", "💬 Chat de Soporte", "👤 Mi Perfil"]
    menu = st.radio("Ir a:", opciones)
    
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- SECCIÓN: MI PERFIL (GESTIÓN DE CUENTA) ---
if menu == "👤 Mi Perfil":
    st.header("Configuración de Cuenta")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Foto de Perfil")
        archivo = st.file_uploader("Subir desde galería", type=['jpg', 'png', 'jpeg'])
        if archivo:
            u_info["foto"] = procesar_foto(archivo)
            st.success("¡Foto actualizada!")
            st.rerun()
    with col2:
        st.subheader("Datos Personales")
        u_info["nombre"] = st.text_input("Nombre de Usuario", value=u_info["nombre"])
        u_info["clave"] = st.text_input("Cambiar Contraseña", value=u_info["clave"], type="password")
        if st.session_state.u_rol == "Repartidor":
            u_info["disponible"] = st.toggle("Estoy Disponible", value=u_info.get("disponible", True))
        st.button("Guardar Cambios")

# --- SECCIÓN: CHAT (VINCULADO) ---
elif menu == "💬 Chat de Soporte":
    st.header("Chat de Ayuda")
    # Si es cliente, habla con el admin. Si es admin, ve todos los chats.
    if st.session_state.u_rol == "Cliente":
        cl_email = st.session_state.u_email
        if cl_email not in db["chats"]: db["chats"][cl_email] = []
        
        for m in db["chats"][cl_email]:
            st.chat_message("user" if m['autor'] == "Cliente" else "assistant").write(f"**{m['autor']}:** {m['txt']}")
        
        msg = st.chat_input("Escribe tu mensaje al administrador...")
        if msg:
            db["chats"][cl_email].append({"autor": "Cliente", "txt": msg})
            st.rerun()
            
    elif st.session_state.u_rol == "Administrador":
        if not db["chats"]: st.info("No hay mensajes de clientes.")
        for cl_email, msgs in db["chats"].items():
            with st.expander(f"Chat con {db['usuarios'][cl_email]['nombre']}"):
                for m in msgs: st.write(f"**{m['autor']}:** {m['txt']}")
                resp = st.text_input("Responder:", key=f"res_{cl_email}")
                if st.button("Enviar", key=f"btn_{cl_email}"):
                    db["chats"][cl_email].append({"autor": "Admin", "txt": resp})
                    st.rerun()

# --- SECCIÓN: INICIO (ESTRATEGIA STAFF vs CLIENTE) ---
elif menu == "🏠 Inicio":
    if st.session_state.u_rol == "Administrador":
        st.title("Panel de Control Staff")
        # Aquí el Admin crea pedidos (SÓLO VE NOMBRES)
        clientes_nombres = {u['nombre']: k for k, u in db["usuarios"].items() if u['rol'] == 'Cliente'}
        reps_nombres = {u['nombre']: k for k, u in db["usuarios"].items() if u['rol'] == 'Repartidor' and u.get('disponible', True)}
        
        with st.form("crear_pedido"):
            c_sel = st.selectbox("Cliente", list(clientes_nombres.keys()))
            dire = st.text_input("Dirección de Entrega")
            r_sel = st.selectbox("Repartidor", list(reps_nombres.keys()))
            if st.form_submit_button("Lanzar Pedido"):
                db["pedidos"].append({
                    "id": len(db["pedidos"])+1, "cliente_email": clientes_nombres[c_sel],
                    "cliente_nombre": c_sel, "direccion": dire, "rep_email": reps_nombres[r_sel], "estado": "En camino"
                })
                st.rerun()
        st.write("### Pedidos Activos")
        st.table(db["pedidos"])

    elif st.session_state.u_rol == "Repartidor":
        st.title("Mis Entregas")
        mis_v = [p for p in db["pedidos"] if p["rep_email"] == st.session_state.u_email and p["estado"] == "En camino"]
        for p in mis_v:
            st.info(f"Pedido #{p['id']} para {p['cliente_nombre']}")
            if st.button(f"Entregado #{p['id']}"):
                p["estado"] = "Entregado"
                st.rerun()

    elif st.session_state.u_rol == "Cliente":
        st.title("Rastreo de mi Pedido")
        mi_p = next((p for p in db["pedidos"] if p["cliente_email"] == st.session_state.u_email and p["estado"] == "En camino"), None)
        if mi_p:
            st.success(f"Tu pedido va hacia: {mi_p['direccion']}")
            st.metric("Estado", mi_p['estado'])
        else:
            st.info("No tienes pedidos activos en este momento.")
