import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from geopy.geocoders import Nominatim
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA (ESTILO BLANCO) ---
st.set_page_config(page_title="AGS Logística", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #f0f2f6; color: black; }
    .stTextInput>div>div>input { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS TEMPORAL (Simulada) ---
# Nota: Para persistencia real entre diferentes dispositivos, se usaría una DB real.
if 'rutas' not in st.session_state:
    st.session_state.rutas = []
if 'ubicacion_repartidor' not in st.session_state:
    st.session_state.ubicacion_repartidor = {"lat": 21.8853, "lon": -102.2916}

geolocator = Nominatim(user_agent="ags_delivery")

# --- SELECTOR DE ROL ---
rol = st.sidebar.radio("ACCEDER COMO:", ["Administrador", "Repartidor", "Cliente"])
st.sidebar.markdown("---")

# --- LÓGICA DE DIRECCIONES ---
def buscar_direccion(calle):
    try:
        location = geolocator.geocode(f"{calle}, Aguascalientes, Mexico")
        return (location.latitude, location.longitude) if location else None
    except:
        return None

# --- VISTA: ADMINISTRADOR ---
if rol == "Administrador":
    st.header("🏢 Panel de Control (Admin)")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Añadir Nueva Entrega")
        nueva_dir = st.text_input("Escribe la dirección (Ej: Madero 100, Centro)")
        if st.button("➕ Añadir a la Ruta"):
            coords = buscar_direccion(nueva_dir)
            if coords:
                st.session_state.rutas.append({"dir": nueva_dir, "coords": coords, "estado": "Pendiente"})
                st.success("Dirección localizada y añadida.")
            else:
                st.error("No se encontró la dirección. Intenta ser más específico.")
        
        st.subheader("Rutas Actuales")
        for i, r in enumerate(st.session_state.rutas):
            col_a, col_b = st.columns([3, 1])
            col_a.write(f"**{i+1}.** {r['dir']}")
            if col_b.button("🗑️", key=f"del{i}"):
                st.session_state.rutas.pop(i)
                st.rerun()

    with col2:
        st.subheader("Mapa Global en Tiempo Real")
        m = folium.Map(location=[21.8853, -102.2916], zoom_start=13, tiles="cartodbpositron")
        # Mostrar repartidor
        folium.Marker(
            [st.session_state.ubicacion_repartidor["lat"], st.session_state.ubicacion_repartidor["lon"]],
            icon=folium.Icon(color="red", icon="truck", prefix="fa"),
            popup="REPARTIDOR AQUÍ"
        ).add_to(m)
        # Mostrar puntos
        for r in st.session_state.rutas:
            folium.Marker(r['coords'], popup=r['dir'], icon=folium.Icon(color="blue")).add_to(m)
        st_folium(m, width=800, height=500)

# --- VISTA: REPARTIDOR ---
elif rol == "Repartidor":
    st.header("🚚 Mi Hoja de Ruta")
    
    if not st.session_state.rutas:
        st.info("No tienes rutas asignadas por el administrador.")
    else:
        prox = st.session_state.rutas[0]
        st.metric("Siguiente Parada", prox['dir'])
        
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("✅ Marcar como Entregado"):
                st.session_state.rutas.pop(0)
                st.success("¡Entrega completada!")
                st.rerun()
            
            # Botón GPS real
            url_gps = f"https://www.google.com/maps/dir/?api=1&destination={prox['coords'][0]},{prox['coords'][1]}"
            st.link_button("🚀 Abrir GPS (Google Maps)", url_gps)

        with col2:
            # Cálculo de ruta por calles con OSRM
            coords_ruta = f"{st.session_state.ubicacion_repartidor['lon']},{st.session_state.ubicacion_repartidor['lat']};{prox['coords'][1]},{prox['coords'][0]}"
            res = requests.get(f"http://router.project-osrm.org/route/v1/driving/{coords_ruta}?overview=full&geometries=geojson").json()
            
            m = folium.Map(location=prox['coords'], zoom_start=14, tiles="cartodbpositron")
            if res.get('code') == 'Ok':
                linea = [[p[1], p[0]] for p in res['routes'][0]['geometry']['coordinates']]
                folium.PolyLine(linea, color="green", weight=5).add_to(m)
            folium.Marker(prox['coords'], icon=folium.Icon(color="green")).add_to(m)
            st_folium(m, width=700, height=400)

# --- VISTA: CLIENTE ---
else:
    st.header("📦 Rastreo de mi pedido")
    st.write("Consulta dónde viene tu repartidor en Aguascalientes.")
    
    m = folium.Map(location=[st.session_state.ubicacion_repartidor["lat"], st.session_state.ubicacion_repartidor["lon"]], zoom_start=15, tiles="cartodbpositron")
    folium.Marker(
        [st.session_state.ubicacion_repartidor["lat"], st.session_state.ubicacion_repartidor["lon"]],
        icon=folium.Icon(color="red", icon="truck", prefix="fa"),
        popup="Tu repartidor está aquí"
    ).add_to(m)
    st_folium(m, width=1000, height=500)
    st.info("El mapa se actualiza automáticamente cuando el administrador modifica la ruta.")
