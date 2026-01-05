import streamlit as st
import folium
from streamlit_folium import st_folium
import urllib.parse
import re

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Delivery AGS - Privacy Pro", layout="wide")

def es_correo_valido(correo):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', correo) is not None

# 2. BASE DE DATOS COMPARTIDA (Cache para todos los usuarios)
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

# 3. ESTADO DE SESIÓN LOCAL
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
            e_l = st.text_input("Correo:", key="login_email")
            p_l = st.text_input("Contraseña:", type="password", key="login_pass")
            if st.button("Iniciar Sesión", use_container_width=True):
                if e_l in db["usuarios"] and db["usuarios"][e_l]["clave"] == p_l:
                    st.session_state.autenticado = True
                    st.session_state.user_email = e_l
                    st.session_state.user_rol = db["usuarios"][e_l]["rol"]
                    st.rerun()
                else:
                    st.error("Datos incorrectos")

        with tab_reg:
            r_r = st.selectbox("Rol", ["Cliente", "Repartidor"], key="reg_rol")
            e_r = st.text_input("Correo electrónico (Será tu ID):", key="reg_email")
            n_r = st.text_input("Nombre Público (Cómo te verán):", key="reg_name")
            p_r = st.text_input("Contraseña:", type="password", key="reg_pass")
            if st.button("Crear Cuenta", use_container_width=True):
                if es_correo_valido(e_r) and n_r and p_r:
                    if e_r not in db["usuarios"]:
                        db["usuarios"][e_r] = {"clave": p_r, "rol": r_r, "nombre": n_r, "foto": "https://cdn-icons-png.flaticon.com/512/149/149071.png"}
                        st.success("¡Listo! Ya puedes iniciar sesión.")
                    else: st.error("El correo ya existe.")
                else: st.warning("Revisa tus datos.")
    st.stop()

# --- BARRA LATERAL ---
u_info = db["usuarios"][st.session_state.user_email]
with st.sidebar:
    st.image(u_info["foto"], width=80)
    st.title(u_info["nombre"])
    st.caption(f"Rol: {st.session_state.user_rol}")
    
    with st.expander("⚙️ Editar Mi Información"):
        nuevo_nombre = st.text_input("Cambiar Nombre", value=u_info["nombre"], key="edit_name")
        nueva_foto = st.text_input("URL nueva foto perfil", key="edit_photo")
        nueva_clv = st.text_input("Cambiar Contraseña", type="password", key="edit_pass")
        if st.button("Actualizar Perfil", key="btn_update"):
            u_info["nombre"] = nuevo_nombre
            if nueva_foto: u_info["foto"] = nueva_foto
            if nueva_clv: u_info["clave"] = nueva_clv
            st.success("¡Cambios guardados!")
            st.rerun()

    if st.button("Cerrar Sesión", key="logout_btn"):
        st.session_state.autenticado = False
        st.rerun()

# --- VISTA: ADMINISTRADOR (MANUEL MONTES) ---
if st.session_state.user_rol == "Administrador":
    st.title("🛠 Gestión de Delivery")
    t1, t2 = st.tabs(["📋 Pedidos", "👥 Usuarios"])
    
    with t1:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.subheader("Crear Pedido")
            clientes_dict = {info["nombre"]: email for email, info in db["usuarios"].items() if info["rol"] == "Cliente"}
            reps_dict = {info["nombre"]: email for email, info in db["usuarios"].items() if info["rol"] == "Repartidor"}
            
            with st.form("nuevo_pedido_form"):
                nom_c = st.selectbox("Seleccionar Cliente", list(clientes_dict.keys()) if clientes_dict else ["No hay clientes"])
                dir_p = st.text_input("Dirección")
                nom_r = st.selectbox("Asignar Repartidor", list(reps_dict.keys()) if reps_dict else ["No hay repartidores"])
                if st.form_submit_button("Lanzar Pedido"):
                    if clientes_dict and reps_dict:
                        db["pedidos"].append({
                            "id": len(db["pedidos"])+1,
                            "cliente_email": clientes_dict[nom_c],
                            "cliente_nombre": nom_c,
                            "direccion": dir_p,
                            "rep_email": reps_dict[nom_r],
                            "estado": "En camino",
                            "lat": 21.88, "lon": -102.29
                        })
                        st.rerun()
        with c2:
            st.subheader("Rutas Activas")
            m = folium.Map(location=[21.88, -102.29], zoom_start=12)
            for p in db["pedidos"]:
                if p["estado"] == "En camino":
                    folium.Marker([p['lat'], p['lon']], popup=f"Para: {p['cliente_nombre']}").add_to(m)
            st_folium(m, height=350, key="mapa_admin_final")

    with t2:
        st.subheader("Control de Usuarios")
        for email, info in db["usuarios"].items():
            with st.expander(f"👤 {info['nombre']} ({info['rol']})"):
                st.write(f"**Correo:** {email}")
                st.write(f"**Clave:** {info['clave']}")

# --- VISTA: REPARTIDOR ---
elif st.session_state.user_rol == "Repartidor":
    st.title("🛵 Mis Rutas")
    mis_p = [p for p in db["pedidos"] if p["rep_email"] == st.session_state.user_email and p["estado"] == "En camino"]
    if not mis_p:
        st.info("No tienes pedidos pendientes.")
    for p in mis_p:
        st.info(f"Pedido #{p['id']} para **{p['cliente_nombre']}**")
        st.write(f"📍 {p['direccion']}")
        if st.button("Finalizar Entrega", key=f"f_final_{p['id']}"):
            p["estado"] = "Entregado"
            st.rerun()

# --- VISTA: CLIENTE ---
elif st.session_state.user_rol == "Cliente":
    st.title(f"🏠 Pedidos de {u_info['nombre']}")
    mis_pedidos = [p for p in db["pedidos"] if p["cliente_email"] == st.session_state.user_email]
    if mis_pedidos:
        activo = next((p for p in mis_pedidos if p["estado"] == "En camino"), None)
        if activo:
            st.success("Tu pedido está en ruta.")
            m_c = folium.Map(location=[activo['lat'], activo['lon']], zoom_start=14)
            folium.Marker([activo['lat'], activo['lon']], icon=folium.Icon(color='orange', icon='motorcycle', prefix='fa')).add_to(m_c)
            st_folium(m_c, height=400, key="mapa_cli_final")
        st.table(mis_pedidos)
    else:
        st.info("No tienes pedidos activos.")
