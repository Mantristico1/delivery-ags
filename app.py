import streamlit as st
import folium
from streamlit_folium import st_folium
import urllib.parse
import re

# 1. CONFIGURACIÓN Y ESTILO
st.set_page_config(page_title="Delivery AGS - Email Auth", layout="wide")

# Función para validar formato de correo
def es_correo_valido(correo):
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(patron, correo) is not None

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

# --- PANTALLA DE ACCESO CENTRADA ---
if not st.session_state.autenticado:
    izq, centro, der = st.columns([1, 2, 1])
    with centro:
        st.markdown("<h1 style='text-align: center;'>🚚 Delivery AGS</h1>", unsafe_allow_html=True)
        tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Registro con Correo"])
        
        with tab_login:
            email_log = st.text_input("Correo Electrónico:", key="log_e")
            pass_log = st.text_input("Contraseña:", type="password", key="log_p")
            if st.button("Entrar", use_container_width=True):
                if email_log in db["usuarios"] and db["usuarios"][email_log]["clave"] == pass_log:
                    st.session_state.autenticado = True
                    st.session_state.user_email = email_log
                    st.session_state.user_rol = db["usuarios"][email_log]["rol"]
                    st.rerun()
                else:
                    st.error("Correo o contraseña incorrectos")

        with tab_registro:
            rol_reg = st.selectbox("Registrarme como:", ["Cliente", "Repartidor"])
            email_reg = st.text_input("Tu Correo Real:", key="reg_e")
            nom_reg = st.text_input("Nombre Completo:", key="reg_n")
            pass_reg = st.text_input("Crea tu Contraseña:", type="password", key="reg_p")
            
            if st.button("Crear Cuenta con Email", use_container_width=True):
                if not es_correo_valido(email_reg):
                    st.error("Por favor ingresa un correo electrónico válido.")
                elif email_reg in db["usuarios"]:
                    st.error("Este correo ya está registrado.")
                elif email_reg and pass_reg and nom_reg:
                    db["usuarios"][email_reg] = {
                        "clave": pass_reg, 
                        "rol": rol_reg, 
                        "nombre": nom_reg,
                        "foto": "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                    }
                    st.success("¡Cuenta creada! Ahora puedes iniciar sesión.")
                else:
                    st.warning("Completa todos los campos.")
    st.stop()

# --- BARRA LATERAL (Perfil Dinámico) ---
user_data = db["usuarios"][st.session_state.user_email]
with st.sidebar:
    st.image(user_data["foto"], width=100)
    st.title(f"{user_data['nombre']}")
    st.caption(f"📧 {st.session_state.user_email}")
    st.write(f"🔰 Rol: **{st.session_state.user_rol}**")
    
    with st.expander("⚙️ Editar Mi Información"):
        nuevo_nombre = st.text_input("Cambiar Nombre", value=user_data["nombre"])
        nueva_foto = st.text_input("URL nueva foto perfil")
        nueva_clv = st.text_input("Cambiar Contraseña", type="password")
        if st.button("Actualizar Perfil"):
            user_data["nombre"] = nuevo_nombre
            if nueva_foto: user_data["foto"] = nueva_foto
            if nueva_clv: user_data["clave"] = nueva_clv
            st.success("¡Cambios guardados!")
            st.rerun()

    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- VISTAS SEGÚN ROL ---

# 1. VISTA ADMINISTRADOR
if st.session_state.user_rol == "Administrador":
    st.title("🛠 Control de Logística - Manuel Montes")
    t1, t2 = st.tabs(["📋 Gestión de Pedidos", "👥 Clientes y Repartidores"])
    
    with t1:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.subheader("Crear Pedido")
            with st.form("p_f"):
                # Lista de correos de clientes registrados
                lista_clientes = [u for u in db["usuarios"] if db["usuarios"][u]["rol"] == "Cliente"]
                c_email = st.selectbox("Seleccionar Cliente (Email)", lista_clientes)
                dir_p = st.text_input("Dirección de entrega")
                lista_reps = [u for u in db["usuarios"] if db["usuarios"][u]["rol"] == "Repartidor"]
                r_email = st.selectbox("Asignar Repartidor", lista_reps)
                if st.form_submit_button("Lanzar Pedido"):
                    db["pedidos"].append({
                        "id": len(db["pedidos"])+1, 
                        "cliente_email": c_email, 
                        "direccion": dir_p, 
                        "repartidor_email": r_email, 
                        "estado": "En camino", 
                        "lat": 21.88, "lon": -102.29
                    })
                    st.rerun()
        with c2:
            st.subheader("Mapa en Tiempo Real")
            m = folium.Map(location=[21.88, -102.29], zoom_start=13)
            for p in db["pedidos"]:
                if p["estado"] == "En camino":
                    folium.Marker([p['lat'], p['lon']], popup=f"Pedido #{p['id']}").add_to(m)
            st_folium(m, height=400)

    with t2:
        st.subheader("Base de Datos de Usuarios")
        st.write("Aquí puedes ver quién está registrado en el sistema.")
        for email, info in db["usuarios"].items():
            st.info(f"📍 **{info['nombre']}** ({email}) - Rol: {info['rol']}")

# 2. VISTA REPARTIDOR
elif st.session_state.user_rol == "Repartidor":
    st.title("🛵 Mis Rutas de Entrega")
    mios = [p for p in db["pedidos"] if p["repartidor_email"] == st.session_state.user_email and p["estado"] == "En camino"]
    
    if not mios:
        st.info("No tienes pedidos pendientes.")
    else:
        for p in mios:
            with st.expander(f"Pedido #{p['id']} - Para: {db['usuarios'][p['cliente_email']]['nombre']}", expanded=True):
                st.write(f"🏠 Dirección: {p['direccion']}")
                if st.button("🚨 Enviar alerta de contraseña al cliente", key=f"alert_{p['id']}"):
                    st.warning(f"Se ha enviado una notificación de recuperación al correo: {p['cliente_email']}")
                if st.button("✅ Confirmar Entrega", key=f"ok_{p['id']}"):
                    p["estado"] = "Entregado"
                    st.rerun()

# 3. VISTA CLIENTE
elif st.session_state.user_rol == "Cliente":
    st.title("🏠
