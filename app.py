import streamlit as st
import folium
from streamlit_folium import st_folium
import urllib.parse

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Delivery AGS - Sistema Central", layout="wide")

# 2. MEMORIA COMPARTIDA (Para que se vea igual en PC y Celular)
@st.cache_resource
def obtener_base_datos():
    # Esta lista será la misma para todos los usuarios que entren al link
    return []

pedidos_globales = obtener_base_datos()

# 3. BARRA LATERAL (Acceso restringido)
with st.sidebar:
    st.title("🚀 Delivery AGS")
    # El usuario debe elegir su rol, pero el cliente solo verá su parte
    rol = st.selectbox("Acceso:", ["Cliente", "Repartidor", "Administrador"])
    st.divider()
    st.caption("v2.0 - Memoria en tiempo real")

# --- VISTA: ADMINISTRADOR ---
if rol == "Administrador":
    st.title("🛠 Panel Maestro (Visible solo para Admin)")
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
                    "id": len(pedidos_globales) + 1,
                    "cliente": cliente,
                    "direccion": direccion,
                    "repartidor": id_rep,
                    "lat": 21.8853 + (len(pedidos_globales) * 0.005),
                    "lon": -102.2916 + (len(pedidos_globales) * 0.005),
                    "estado": "En camino"
                }
                pedidos_globales.append(nuevo)
                st.rerun()

    with col2:
        st.subheader("Mapa Global")
        m_admin = folium.Map(location=[21.8853, -102.2916], zoom_start=13)
        for p in pedidos_globales:
            folium.Marker([p['lat'], p['lon']], 
                          popup=f"Ped {p['id']} - Rep {p['repartidor']}",
                          icon=folium.Icon(color="blue", icon="motorcycle", prefix="fa")).add_to(m_admin)
        st_folium(m_admin, width=700, height=400, key="admin_map")

    st.subheader("Gestión de Pedidos")
    for i, p in enumerate(pedidos_globales):
        c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
        c1.write(f"**ID:** {p['id']}")
        c2.write(f"**Cliente:** {p['cliente']}")
        c3.write(f"**Repartidor:** {p['repartidor']}")
        if c4.button("❌ Borrar", key=f"del_{p['id']}"):
            pedidos_globales.pop(i)
            st.rerun()

# --- VISTA: REPARTIDOR ---
elif rol == "Repartidor":
    st.title("🛵 Panel de Reparto")
    mi_id = st.number_input("Tu Número de Repartidor:", min_value=1, step=1)
    
    mis_entregas = [p for p in pedidos_globales if p['repartidor'] == mi_id]
    
    if not mis_entregas:
        st.warning("No tienes pedidos asignados en este momento.")
    else:
        for p in mis_entregas:
            with st.expander(f"📦 Pedido #{p['id']} - {p['cliente']}", expanded=True):
                st.write(f"📍 **Destino:** {p['direccion']}")
                query = urllib.parse.quote(p['direccion'])
                url = f"https://www.google.com/maps/search/?api=1&query={query}"
                st.markdown(f'<a href="{url}" target="_blank"><button style="width:100%; background-color:#4CAF50; color:white; padding:10px; border:none; border-radius:5px; cursor:pointer;">📍 Abrir Navegación GPS</button></a>', unsafe_allow_html=True)
                
                if st.button(f"Confirmar Entrega #{p['id']}"):
                    pedidos_globales.remove(p)
                    st.success("¡Pedido entregado y eliminado del sistema!")
                    st.rerun()

# --- VISTA: CLIENTE (Solo rastreo, nada más) ---
elif rol == "Cliente":
    st.title("🏠 Seguimiento de tu Entrega")
    st.write("Escribe tu nombre para localizar a tu repartidor en el mapa.")
    nombre = st.text_input("Nombre registrado:")
    
    if nombre:
        pedido = next((p for p in pedidos_globales if nombre.lower() in p['cliente'].lower()), None)
        if pedido:
            st.success(f"¡Hola {pedido['cliente']}! Tu pedido está siendo entregado por el repartidor #{pedido['repartidor']}.")
            
            c1, c2 = st.columns(2)
            c1.metric("Estatus", "En camino")
            c2.metric("Llegada estimada", "10-15 min")
            
            # Mapa de rastreo
            m_cli = folium.Map(location=[pedido['lat'], pedido['lon']], zoom_start=15)
            # Ubicación casa (fija)
            folium.Marker([21.8810, -102.2920], popup="Tu Casa", icon=folium.Icon(color="red", icon="home")).add_to(m_cli)
            # Ubicación repartidor (dinámica según admin)
            folium.Marker([pedido['lat'], pedido['lon']], popup="Tu Repartidor", icon=folium.Icon(color="orange", icon="motorcycle", prefix="fa")).add_to(m_cli)
            st_folium(m_cli, width=700, height=400, key="cli_map")
        else:
            st.error("No hay pedidos activos con ese nombre. Verifica con el administrador.")
