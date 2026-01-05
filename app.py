import streamlit as st
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Delivery AGS", layout="wide")

# 2. MEMORIA DE LA APP (Session State)
if 'lista_rutas' not in st.session_state:
    st.session_state.lista_rutas = []

# 3. BARRA LATERAL (Selector de Rol)
with st.sidebar:
    st.title("👤 Panel de Acceso")
    rol = st.selectbox("¿Quién eres?", ["Administrador", "Repartidor", "Cliente"])
    st.divider()
    if st.button("🗑️ Borrar todas las rutas"):
        st.session_state.lista_rutas = []
        st.rerun()

# --- VISTA: ADMINISTRADOR ---
if rol == "Administrador":
    st.title("🛠 Configuración de Entregas")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Añadir Nueva Ruta")
        with st.form("form_ruta", clear_on_submit=True):
            destino = st.text_input("Dirección de destino:")
            cliente = st.text_input("Nombre del cliente:")
            boton_crear = st.form_submit_button("➕ Agregar a la lista")
            
            if boton_crear and destino:
                nueva = {"id": len(st.session_state.lista_rutas)+1, "destino": destino, "cliente": cliente}
                st.session_state.lista_rutas.append(nueva)
                st.success("Ruta añadida")
                st.rerun()

    with col2:
        st.subheader("Rutas en Sistema")
        for r in st.session_state.lista_rutas:
            st.info(f"📦 **#{r['id']}** - {r['cliente']} a {r['destino']}")

# --- VISTA: REPARTIDOR ---
elif rol == "Repartidor":
    st.title("🛵 Vista del Repartidor")
    if not st.session_state.lista_rutas:
        st.warning("No tienes rutas asignadas.")
    else:
        # Mostramos la última ruta creada como prioridad
        actual = st.session_state.lista_rutas[-1]
        st.metric("Destino actual", actual['destino'])
        st.write(f"Entregar a: **{actual['cliente']}**")
        
        # Mapa simplificado para el repartidor
        m_rep = folium.Map(location=[21.8853, -102.2916], zoom_start=14)
        folium.Marker([21.8853, -102.2916], popup="Tu ubicación", icon=folium.Icon(color='blue', icon='motorcycle', prefix='fa')).add_to(m_rep)
        folium.Marker([21.8920, -102.2850], popup="Entrega", icon=folium.Icon(color='red')).add_to(m_rep)
        st_folium(m_rep, width=700, height=400, key="mapa_rep")
        
        if st.button("✅ Marcar como entregado"):
            st.success("¡Entrega completada!")

# --- VISTA: CLIENTE ---
elif rol == "Cliente":
    st.title("🏠 Seguimiento de tu pedido")
    if not st.session_state.lista_rutas:
        st.info("No hay pedidos activos para tu usuario.")
    else:
        actual = st.session_state.lista_rutas[-1]
        st.subheader(f"Hola {actual['cliente']}, tu pedido viene en camino.")
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("⏱️ **Tiempo estimado:** 12 - 18 minutos")
            st.progress(40) # Barra de progreso
        
        with c2:
            # Mapa que muestra solo el avance
            m_cli = folium.Map(location=[21.8880, -102.2880], zoom_start=14)
            folium.Marker([21.8880, -102.2880], icon=folium.Icon(color='orange', icon='bicycle', prefix='fa')).add_to(m_cli)
            st_folium(m_cli, width=400, height=250, key="mapa_cli")
