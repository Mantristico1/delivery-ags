import streamlit as st
import folium
from streamlit_folium import st_folium
import urllib.parse

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Delivery AGS - Login System", layout="wide")

# 2. MEMORIA GLOBAL COMPARTIDA (Base de datos simulada)
@st.cache_resource
def obtener_datos():
    return {
        "pedidos": [],
        "usuarios": {
            "admin": "1234", # Contraseña del administrador
        }
    }

db = obtener_datos()

# 3. SISTEMA DE SESIÓN (Login local)
if 'user_rol' not in st.session_state:
    st.session_state.user_rol = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

# --- PANTALLA DE LOGIN ---
if st.session_state.user_rol is None:
    st.title("🔐 Acceso al Sistema Delivery AGS")
    col_l, col_r = st.columns(2)
    
    with col_l:
        rol = st.selectbox("Tipo de Usuario", ["Cliente", "Repartidor", "Administrador"])
        nombre = st.text_input("Nombre de Usuario / ID")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Entrar"):
            if rol == "Administrador" and password == db["usuarios"]["admin"]:
                st.session_state.user_rol = "Administrador"
                st.session_state.user_name = "Admin"
                st.rerun()
            elif rol == "Administrador":
                st.error("Contraseña de Admin incorrecta")
            else:
                # Registro simple para Cliente y Repartidor
                st.session_state.user_rol = rol
                st.session_state.user_name = nombre
                st.rerun()
    st.stop() # Detiene el código aquí si no hay login

# --- BARRA LATERAL (Salir) ---
with st.sidebar:
    st.write(f"👤 Usuario: **{st.session_state.user_name}**")
    st.write(f"🔰 Rol: **{st.session_state.user_rol}**")
    if st.button("Cerrar Sesión"):
        st.session_state.user_rol = None
        st.session_state.user_name = None
        st.rerun()

# --- VISTA: ADMINISTRADOR ---
if st.session_state.user_rol == "Administrador":
    st.title("🛠 Panel Maestro")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Registrar Nuevo Pedido")
        with st.form("nuevo_p"):
            c_nombre = st.text_input("Nombre del Cliente")
            c_dir = st.text_input("Dirección")
            id_r = st.number_input("ID Repartidor", min_value=1, step=1)
            if st.form_submit_button("Crear"):
                nuevo = {
                    "id": len(db["pedidos"]) + 1,
                    "cliente": c_nombre,
                    "direccion": c_dir,
                    "repartidor": id_r,
                    "estado": "En Proceso",
                    "lat": 21.8853, "lon": -102.2916
                }
                db["pedidos"].append(nuevo)
                st.rerun()

    with col2:
        st.subheader("Mapa Global")
        m = folium.Map(location=[21.8853, -102.2916], zoom_start=13)
        for p in db["pedidos"]:
            if p["estado"] == "En Proceso":
                folium.Marker([p['lat'], p['lon']], popup=p['cliente']).add_to(m)
        st_folium(m, height=300, key="m_admin")

    st.write("### Todos los Pedidos")
    for i, p in enumerate(db["pedidos"]):
        c1, c2, c3, c4 = st.columns(4)
        c1.write(f"#{p['id']} {p['cliente']}")
        c2.write(f"Rep: {p['repartidor']}")
        c3.write(f"Estado: {p['estado']}")
        if c4.button("❌ Borrar", key=f"del_{i}"):
            db["pedidos"].pop(i)
            st.rerun()

# --- VISTA: REPARTIDOR ---
elif st.session_state.user_rol == "Repartidor":
    st.title(f"🛵 Entregas - Repartidor #{st.session_state.user_name}")
    try:
        mi_id = int(st.session_state.user_name)
        entregas = [p for p in db["pedidos"] if p["repartidor"] == mi_id and p["estado"] == "En Proceso"]
        
        if not entregas:
            st.info("No tienes rutas pendientes.")
        else:
            for p in entregas:
                st.subheader(f"Pedido #{p['id']}")
                st.write(f"Cliente: {p['cliente']} | Dir: {p['direccion']}")
                
                # Google Maps
                q = urllib.parse.quote(p['direccion'])
                st.markdown(f'[📍 Navegar](http://maps.google.com/?q={q})')
                
                if st.button("✅ Finalizar Entrega", key=f"fin_{p['id']}"):
                    p["estado"] = "Entregado"
                    st.rerun()
    except:
        st.error("Por favor, ingresa un número en tu nombre de usuario al entrar.")

# --- VISTA: CLIENTE (Con Historial) ---
elif st.session_state.user_rol == "Cliente":
    st.title(f"🏠 Mis Pedidos - {st.session_state.user_name}")
    
    mis_pedidos = [p for p in db["pedidos"] if st.session_state.user_name.lower() in p["cliente"].lower()]
    
    if not mis_pedidos:
        st.warning("No tienes historial de pedidos.")
    else:
        # Pestañas: Activo vs Historial
        tab1, tab2 = st.tabs(["📍 Rastreo Actual", "📜 Historial"])
        
        with tab1:
            activo = next((p for p in mis_pedidos if p["estado"] == "En Proceso"), None)
            if activo:
                st.success("¡Tu pedido está en camino!")
                m_c = folium.Map(location=[activo['lat'], activo['lon']], zoom_start=15)
                folium.Marker([activo['lat'], activo['lon']], icon=folium.Icon(color='orange', icon='motorcycle', prefix='fa')).add_to(m_c)
                st_folium(m_c, height=300, key="m_cli")
            else:
                st.info("No tienes pedidos activos ahora mismo.")
                
        with tab2:
            st.write("### Tus pedidos anteriores")
            for p in mis_pedidos:
                st.write(f"✅ Pedido #{p['id']} - Fecha: 05/01/24 - **{p['estado']}**")
