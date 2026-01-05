import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(page_title="Delivery AGS Pro", layout="wide")

st.title("🚚 Navegador de Reparto - Aguascalientes")

# --- CONFIGURACIÓN ---
st.sidebar.header("Panel de Control")
num_pedidos = st.sidebar.slider("Número de entregas", 1, 10, 5)
tipo_icono = st.sidebar.selectbox("Estilo de marcador", ["shopping-cart", "home", "info-sign"])

# Punto de Inicio
st.sidebar.subheader("📍 Ubicación de Salida")
lat_inicio = st.sidebar.number_input("Latitud", value=21.8853, format="%.6f")
lon_inicio = st.sidebar.number_input("Longitud", value=-102.2916, format="%.6f")
puntos = [[lat_inicio, lon_inicio]]

# Entradas para Pedidos
for i in range(num_pedidos):
    st.sidebar.subheader(f"Pedido #{i+1}")
    lat = st.sidebar.number_input(f"Latitud {i+1}", value=21.88+(i*0.005), format="%.6f", key=f"lat{i}")
    lon = st.sidebar.number_input(f"Longitud {i+1}", value=-102.29-(i*0.005), format="%.6f", key=f"lon{i}")
    puntos.append([lat, lon])

# --- FUNCIÓN DE RUTA ---
def obtener_ruta(coords):
    string_coords = ";".join([f"{c[1]},{c[0]}" for c in coords])
    url = f"http://router.project-osrm.org/trip/v1/driving/{string_coords}?source=first&overview=full&geometries=geojson"
    return requests.get(url).json()

# --- BOTÓN PRINCIPAL ---
if st.button("🗺️ Generar Ruta de Trabajo"):
    res = obtener_ruta(puntos)
    
    if res.get('code') == 'Ok':
        viaje = res['trips'][0]
        geometria = viaje['geometry']['coordinates']
        orden_puntos = res['waypoints']
        
        st.success(f"Ruta calculada. Total: {viaje['distance']/1000:.2f} km aproximados.")

        # MAPA
        m = folium.Map(location=[lat_inicio, lon_inicio], zoom_start=13)
        camino = [[p[1], p[0]] for p in geometria]
        folium.PolyLine(camino, color="blue", weight=5).add_to(m)

        # SECCIÓN DE NAVEGACIÓN (Lo nuevo)
        st.subheader("📋 Orden de Entregas y Navegación GPS")
        cols = st.columns(3) # Para poner los botones en columnas
        
        for wp in orden_puntos:
            idx = wp['trips_index']
            pos = [wp['location'][1], wp['location'][0]]
            es_base = (wp['waypoint_index'] == 0)
            
            # Marcador en el mapa
            folium.Marker(pos, popup=f"Punto {idx}", icon=folium.Icon(color="red" if es_base else "green", icon=tipo_icono)).add_to(m)
            
            # Botón de Google Maps para cada punto
            if not es_base:
                with cols[(idx-1) % 3]:
                    url_gmaps = f"https://www.google.com/maps/dir/?api=1&destination={pos[0]},{pos[1]}&travelmode=driving"
                    st.link_button(f"📍 Ir a Entrega {idx}", url_gmaps)

        st_folium(m, width=1100, height=500)
    else:
        st.error("Error al conectar con el mapa.")

st.info("💡 Consejo: Abre esta página en tu celular, pulsa el botón de una entrega y Google Maps se abrirá automáticamente para guiarte.")
