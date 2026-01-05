import streamlit as st
import folium
from streamlit_folium import st_folium
import urllib.parse

# 1. CONFIGURACIÓN E INTERFAZ CELULAR
st.set_page_config(page_title="Delivery AGS Pro", layout="wide")
st.markdown("<style>div.block-container{padding-top:2rem;}</style>", unsafe_allow_html=True)

# 2. BASE DE DATOS EN MEMORIA
if 'pedidos' not in st.session_state:
    st.session_state.pedidos = []

# 3. BARRA LATERAL
with st.sidebar:
    st.title("🚀 Delivery AGS")
    rol = st.selectbox("Acceder como:", ["Administrador", "Repartidor", "Cliente"])
    st.divider()
    st.info("Sistema de logística en tiempo real")

# --- VISTA: ADMINISTRADOR ---
if rol == "Administrador":
    st.title("🛠 Panel Maestro de Administración")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Registrar Nuevo Pedido")
        with st.form("form_admin", clear_on_submit=True):
            cliente = st.text_input("Nombre del Cliente")
            direccion = st.text_input("Dirección de Destino")
            id_repartidor = st.number_input("Asignar a Repartidor #", min_value=1, step=1)
            submit = st.form_submit_button("Crear y Asignar")
            
            if submit and cliente and direccion:
                nuevo = {
                    "id": len(st.session_state.pedidos) + 1,
                    "cliente": cliente,
                    "direccion": direccion,
                    "repartidor": id_repartidor,
                    "estado": "En preparación",
                    "lat": 21.8853 + (len(st.session_state.pedidos) * 0.002), # Simulación movimiento
                    "lon": -102.2916 + (len(st.session_state.pedidos) * 0.002)
                }
                st.session_state.pedidos.append(nueva)
                st.rerun()

    with col2:
        st.subheader("Mapa de Rutas Activas")
        m_admin = folium.Map(location=[21.8853, -102.2916], zoom_start=13)
        for p in st.session_state.pedidos:
            folium.Marker(
                [p['lat'], p['lon']], 
                popup=f"Pedido {p['id']} - Repartidor {p['repartidor']}",
                icon=folium.Icon(color="blue", icon="motorcycle", prefix="fa")
            ).add_to(m_admin)
        st_folium(m_admin, width="100%", height=400, key="admin_map")

    st.subheader("Gestión de Pedidos")
    for i, p in enumerate(st.session_state.pedidos):
        c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
        c1.write(f"**ID:** {p['id']}")
        c2.write(f"**Cliente:** {p['cliente']}")
        c3.write(f"**Repartidor:** {p['repartidor']}")
        if c4.button("❌ Borrar", key=f"del_{i}"):
            st.session_state.pedidos.pop(i)
            st.rerun()

# --- VISTA: REPARTIDOR ---
elif rol == "Repartidor":
    st.title("🛵 Panel de Reparto")
    mi_id = st.number_input("Ingresa tu número de repartidor para ver tus entregas:", min_value=1, step=1)
    
    mis_entregas = [p for p in st.session_state.pedidos if p['repartidor'] == mi_id]
    
    if not mis_entregas:
        st.warning(f"Repartidor #{mi_id}, no tienes entregas asignadas.")
    else:
        for p in mis_entregas:
            with st.expander(f"📦 Pedido #{p['id']} - {p['cliente']}", expanded=True):
                st.write(f"📍 **Destino:** {p['direccion']}")
                
                # Google Maps Link
                url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(p['direccion'])}"
                st.markdown(f'<a href="{url}" target="_blank"><button style="width:100%; background-color:#4CAF50; color:white; padding:10px; border:none; border-radius:5px;">📍 Navegar en Google Maps</button></a>', unsafe_allow_html=True)
                
                if st.button(f"Marcar Entregado #{p['id']}"):
                    st.session_state.pedidos = [pedido for pedido in st.session_state.pedidos if pedido['id'] != p['id']]
                    st.success("¡Entrega confirmada!")
                    st.rerun()

# --- VISTA: CLIENTE ---
elif rol == "Cliente":
    st.title("🏠 Rastreo de Pedido")
    nombre = st.text_input("Escribe tu nombre tal cual lo registraste:")
    
    if nombre:
        pedido = next((p for p in st.session_state.pedidos if nombre.lower() in p['cliente'].lower()), None)
        
        if pedido:
            st.success(f"¡Hola {pedido['cliente']}! Tu repartidor #{pedido['repartidor']} va en camino.")
            
            # Datos de tiempo
            c1, c2 = st.columns(2)
            c1.metric("Tiempo Estimado", "12 min")
            c2.metric("Distancia", "2.4 km")
            
            # Mapa de rastreo
            st.subheader("Mapa en Tiempo Real")
            m_cli = folium.Map(location=[pedido['lat'], pedido['lon']], zoom_start=15)
            # Marcador Cliente
            folium.Marker([21.8820, -102.2900], popup="Tu Casa", icon=folium.Icon(color="red", icon="home")).add_to(m_cli)
            # Marcador Repartidor
            folium.Marker([pedido['lat'], pedido['lon']], popup="Tu Repartidor", icon=folium.Icon(color="orange", icon="motorcycle", prefix="fa")).add_to(m_cli)
            
            st_folium(m_cli, width="100
