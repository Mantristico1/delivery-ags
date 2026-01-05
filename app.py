import streamlit as st
import folium
from streamlit_folium import st_folium
import urllib.parse

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Delivery AGS", layout="wide")

# 2. MEMORIA DE RUTAS
if 'lista_rutas' not in st.session_state:
    st.session_state.lista_rutas = []

# 3. BARRA LATERAL
with st.sidebar:
    st.title("👤 Acceso")
    rol = st.selectbox("¿Quién eres?", ["Administrador", "Repartidor", "Cliente"])
    st.divider()
    if st.button("🗑️ Resetear Sistema"):
        st.session_state.lista_rutas = []
        st.rerun()

# --- VISTA: ADMINISTRADOR (Mapa Global y Gestión) ---
if rol == "Administrador":
    st.title("🛠 Panel de Control - Administrador")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Nueva Entrega")
        with st.form("admin_form", clear_on_submit=True):
            cliente = st.text_input("Nombre del Cliente")
            direccion = st.text_input("Dirección de Destino")
            crear = st.form_submit_button("Registrar Pedido")
            
            if crear and cliente and direccion:
                nueva = {
                    "id": len(st.session_state.lista_rutas) + 1,
                    "cliente": cliente,
                    "direccion": direccion,
                    "estado": "En Proceso"
                }
                st.session_state.lista_rutas.append(nueva)
                st.rerun()

    with col2:
        st.subheader("Mapa de Seguimiento Global")
        # Mapa que muestra a todos los repartidores (Simulado)
        m_admin = folium.Map(location=[21.8853, -102.2916], zoom_start=13)
        for r in st.session_state.lista_rutas:
            # Marcador por cada pedido
            folium.Marker(
                [21.8853 + (r['id']*0.005), -102.2916], 
                popup=f"Pedido #{r['id']} - {r['cliente']}",
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m_admin)
        
        st_folium(m_admin, width=800, height=400, key="mapa_admin")
        
        st.write("### Lista de Pedidos Actuales")
        st.table(st.session_state.lista_rutas)

# --- VISTA: REPARTIDOR (Dirección + Google Maps) ---
elif rol == "Repartidor":
    st.title("🛵 Mis Entregas")
    if not st.session_state.lista_rutas:
        st.info("No hay pedidos pendientes.")
    else:
        for r in st.session_state.lista_rutas:
            with st.expander(f"📦 PEDIDO #{r['id']} - {r['cliente']}", expanded=True):
                st.write(f"📍 **Dirección:** {r['direccion']}")
                
                # CREAR LINK DE GOOGLE MAPS
                query = urllib.parse.quote(r['direccion'])
                google_maps_url = f"https://www.google.com/maps/search/?api=1&query={query}"
                
                st.markdown(f"""
                    <a href="{google_maps_url}" target="_blank">
                        <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">
                            📍 Abrir en Google Maps
                        </button>
                    </a>
                """, unsafe_allow_html=True)
                
                if st.button(f"Finalizar Entrega #{r['id']}", key=f"btn_{r['id']}"):
                    st.success(f"Pedido #{r['id']} entregado.")

# --- VISTA: CLIENTE (Búsqueda por nombre) ---
elif rol == "Cliente":
    st.title("🏠 Rastrea tu Pedido")
    nombre_buscar = st.text_input("Introduce tu nombre para buscar tu pedido:")
    
    if nombre_buscar:
        # Buscamos el pedido que coincida con el nombre
        pedido_encontrado = next((r for r in st.session_state.lista_rutas if nombre_buscar.lower() in r['cliente'].lower()), None)
        
        if pedido_encontrado:
            st.success(f"¡Hola {pedido_encontrado['cliente']}! Encontramos tu pedido.")
            col_c1, col_c2 = st.columns(2)
            
            with col_c1:
                st.metric("Estado", pedido_encontrado['estado'])
                st.write("⏳ **Tiempo estimado:** 15 min")
                st.progress(60)
            
            with col_c2:
                st.subheader("Ubicación del repartidor")
                m_cliente = folium.Map(location=[21.8853, -102.2916], zoom_start=15)
                folium.Marker([21.8853, -102.2916], icon=folium.Icon(color='orange', icon='motorcycle', prefix='fa')).add_to(m_cliente)
                st_folium(m_cliente, height=300, key="mapa_cliente")
        else:
            st.error("No se encontró ningún pedido con ese nombre.")
