import streamlit as st
import folium
from streamlit_folium import st_folium
import urllib.parse

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Delivery AGS - Pro System", layout="wide")

# 2. BASE DE DATOS COMPARTIDA
@st.cache_resource
def obtener_db():
    return {
        "pedidos": [],
        "usuarios": {
            "Manuel Montes": {"clave": "1234", "rol": "Administrador", "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"}
        }
    }

db = obtener_db()

# 3. ESTADO DE SESIÓN
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.user_name = ""
    st.session_state.user_rol = ""

# --- PANTALLA DE ACCESO ---
if not st.session_state.autenticado:
    izq, centro, der = st.columns([1, 2, 1])
    with centro:
        st.markdown("<h1 style='text-align: center;'>🚚 Delivery AGS</h1>", unsafe_allow_html=True)
        tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Registro"])
        
        with tab_login:
            u_log = st.text_input("Usuario:", key="log_u")
            p_log = st.text_input("Contraseña:", type="password", key="log_p")
            if st.button("Entrar", use_container_width=True):
                if u_log in db["usuarios"] and db["usuarios"][u_log]["clave"] == p_log:
                    st.session_state.autenticado = True
                    st.session_state.user_name = u_log
                    st.session_state.user_rol = db["usuarios"][u_log]["rol"]
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

        with tab_registro:
            rol_reg = st.selectbox("Rol", ["Cliente", "Repartidor"])
            u_reg = st.text_input("Nuevo Usuario:", key="reg_u")
            p_reg = st.text_input("Nueva Contraseña:", type="password", key="reg_p")
            if st.button("Crear Cuenta", use_container_width=True):
                if u_reg and p_reg and u_reg not in db["usuarios"]:
                    db["usuarios"][u_reg] = {"clave": p_reg, "rol": rol_reg, "foto": "https://cdn-icons-png.flaticon.com/512/149/149071.png"}
                    st.success("¡Cuenta creada! Inicia sesión.")
                else:
                    st.error("Error en el registro.")
    st.stop()

# --- BARRA LATERAL (Perfil y Navegación) ---
with st.sidebar:
    # Mostrar foto de perfil
    foto_actual = db["usuarios"][st.session_state.user_name].get("foto", "https://via.placeholder.com/150")
    st.image(foto_actual, width=100)
    st.title(f"Hola, {st.session_state.user_name}")
    st.caption(f"Rol: {st.session_state.user_rol}")
    
    with st.expander("⚙️ Editar Perfil"):
        nuevo_nom = st.text_input("Cambiar Nombre", value=st.session_state.user_name)
        nueva_clv = st.text_input("Nueva Contraseña", type="password")
        nueva_fot = st.text_input("URL de Foto de Perfil")
        if st.button("Guardar Cambios"):
            if nueva_clv: db["usuarios"][st.session_state.user_name]["clave"] = nueva_clv
            if nueva_fot: db["usuarios"][st.session_state.user_name]["foto"] = nueva_fot
            st.success("Datos actualizados")
            st.rerun()
            
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# --- VISTAS ---
if st.session_state.user_rol == "Administrador":
    st.title("🛠 Panel de Administración")
    tab_p, tab_u = st.tabs(["📦 Pedidos", "👥 Usuarios Registrados"])
    
    with tab_p:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.subheader("Nuevo Pedido")
            with st.form("crear"):
                cl = st.text_input("Cliente")
                dr = st.text_input("Dirección")
                re = st.selectbox("Asignar Repartidor", [u for u in db["usuarios"] if db["usuarios"][u]["rol"] == "Repartidor"])
                if st.form_submit_button("Crear"):
                    db["pedidos"].append({"id": len(db["pedidos"])+1, "cliente": cl, "direccion": dr, "repartidor": re, "estado": "En camino", "lat": 21.88, "lon": -102.29})
                    st.rerun()
        with c2:
            st.subheader("Mapa Global")
            m = folium.Map(location=[21.88, -102.29], zoom_start=12)
            for p in db["pedidos"]:
                folium.Marker([p['lat'], p['lon']], popup=p['cliente']).add_to(m)
            st_folium(m, height=300)

    with tab_u:
        st.subheader("Base de Datos de Usuarios")
        for user, info in db["usuarios"].items():
            st.write(f"👤 **{user}** | Rol: `{info['rol']}`")
            if st.button(f"Reiniciar Clave a {user}", key=f"res_{user}"):
                db["usuarios"][user]["clave"] = "1234"
                st.warning(f"Clave de {user} cambiada a 1234")

elif st.session_state.user_rol == "Repartidor":
    st.title("🛵 Panel de Reparto")
    pedidos_mios = [p for p in db["pedidos"] if p["repartidor"] == st.session_state.user_name and p["estado"] == "En camino"]
    
    for p in pedidos_mios:
        with st.expander(f"Pedido #{p['id']} - {p['cliente']}", expanded=True):
            st.write(f"📍 {p['direccion']}")
            if st.button("⚠️ Alerta: El cliente olvidó su contraseña / Ayuda", key=f"alt_{p['id']}"):
                st.error("ALERTA ENVIADA: Se ha notificado al sistema sobre este usuario.")
            if st.button("✅ Finalizar Entrega", key=f"fin_{p['id']}"):
                p["estado"] = "Entregado"
                st.rerun()

elif st.session_state.user_rol == "Cliente":
    st.title("🏠 Mi Seguimiento")
    # Mostrar solo sus pedidos
    mios = [p for p in db["pedidos"] if st.session_state.user_name.lower() in p['cliente'].lower()]
    if mios:
        activo = next((p for p in mios if p["estado"] == "En camino"), None)
        if activo:
            st.success("Tu pedido viene en camino")
            m_c = folium.Map(location=[activo['lat'], activo['lon']], zoom_start=14)
            folium.Marker([activo['lat'], activo['lon']], icon=folium.Icon(color='orange', icon='motorcycle', prefix='fa')).add_to(m_c)
            st_folium(m_c, height=300)
        st.table(mios)
