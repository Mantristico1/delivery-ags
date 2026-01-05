import streamlit as st
import folium
from streamlit_folium import st_folium
import urllib.parse

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Delivery AGS Pro", layout="wide")

# 2. BASE DE DATOS EN MEMORIA
if 'pedidos' not in st.session_state:
    st.session_state.pedidos = []

# 3. BARRA LATERAL
with st.sidebar:
    st.title("🚀 Delivery AGS")
    rol = st.selectbox("Acceder como:", ["Administrador", "Repartidor", "Cliente"])
    st.divider()

# --- VISTA: ADMINISTRADOR ---
if rol == "Administrador":
    st.title("🛠 Panel de Administración")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Registrar Nuevo Pedido")
        with st.form("form_admin", clear_on_submit=True):
            cliente = st.text_input("Nombre del Cliente")
            direccion = st.text_input("Dirección de Destino")
            id_rep = st.number_input("Asignar a Repartidor #", min_value=1, step=1)
            submit = st.form_submit_button("Crear Pedido")
            
            if submit and cliente and direccion:
                nuevo = {
                    "id": len(st.session_state.pedidos) + 1,
                    "cliente": cliente,
                    "direccion": direccion,
                    "repartidor": id_rep,
                    "lat": 21.8853 + (len(st.session_state.pedidos) * 0.005),
                    "lon": -102.2916 + (len(st.session_state.pedidos) * 0.005)
                }
                st.session_state.pedidos.append(nuevo)
                st.rerun()

    with col2:
        st.subheader("Mapa Global de Entregas")
        m_admin = folium.Map(location=[21.8853, -102.2916], zoom_start=13)
        for p in st.session_state.pedidos:
            folium.Marker([p['lat'], p['lon']], 
                          popup=f"Pedido {p['id']} - Rep {p['repartidor']}",
                          icon=folium.Icon(color="blue", icon="motorcycle", prefix="fa")).add_to(m_admin)
        st_folium(m_admin, width=700, height=400, key="admin_map")

    st.subheader("Lista de Pedidos (Gestión)")
    for i, p in enumerate(st.session_state.pedidos):
        c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
        c1.write(f"**ID:** {p['id']}")
        c2.write(f"**Cliente:** {p['cliente']}")
        c3.write(f"**Repartidor:** {p['repartidor']}")
        if c4.button("❌ Borrar", key=f"del_{p['id']}"):
            st.session_state.pedidos.pop(i)
            st.rerun()

# --- VISTA: REPARTIDOR ---
elif rol == "Repartidor":
    st.title("🛵 Mis Entregas")
    mi_id = st.number_input("Tu Número de Repartidor:", min_value=1, step=1)
    
    mis_entregas = [p for p in st.session_state.pedidos if p['repartidor'] == mi_id]
    
    if not mis_entregas:
        st.warning("No tienes pedidos asignados.")
    else:
        for p in mis_entregas:
            with st.expander(f"📦 Pedido #{p['id']} - {p['cliente']}", expanded=True):
                st.write(f"📍 **Destino:** {p['direccion']}")
                query = urllib.parse.quote(p['direccion'])
                url = f"https://www.google.com/maps/search/?api=1&query={query}"
                st.markdown(f'<a href="{url}" target="_blank"><button style="width:100%; background-color:#4CAF50; color:white; padding:10px; border:none; border-radius:5px; cursor:pointer;">📍 Abrir Google Maps</button></a>', unsafe_allow_html=True)
                
                if st.button(f"Confirmar Entrega #{p['id']}"):
                    st.session_state.pedidos = [pedido for pedido in st.session_state.pedidos if pedido['id'] != p['id']]
                    st.success("¡Entregado!")
                    st.rerun()

# --- VISTA: CLIENTE ---
elif rol == "Cliente":
    st.title("🏠 Rastreo de Pedido")
    nombre = st.text_input("Ingresa tu nombre para rastrear:")
    
    if nombre:
        pedido = next((p for p in st.session_state.pedidos if nombre.lower() in p['cliente'].lower()), None)
        if pedido:
            st.success(f"Pedido encontrado. Tu repartidor #{pedido['repartidor']} está en camino.")
            st.metric("Tiempo estimado de llegada", "12 - 15 min")
            
            m_cli = folium.Map(location=[pedido['lat'], pedido['lon']], zoom_start=14)
            # Casa del cliente (estática para el ejemplo)
            folium.Marker([21.8810, -102.2920], popup="Tu Casa", icon=folium.Icon(color="red", icon="home")).add_to(m_cli)
            # Moto del repartidor
            folium.Marker([pedido['lat'], pedido['lon']], popup="Repartidor", icon=folium.Icon(color="orange", icon="motorcycle", prefix="fa")).add_to(m_cli)
            st_folium(m_cli, width=700, height=400, key="cli_map")
        else:
            st.error("No se encontró ningún pedido con ese nombre.")
