import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(page_title="App Delivery Aguascalientes", layout="wide")

# Barra lateral para configuraciones
st.sidebar.title("Configuración de Ruta")
num_puntos = st.sidebar.slider("¿Cuántas entregas?", 1, 10, 5)
icon_style = st.sidebar.selectbox("Icono", ["shopping-cart", "gift", "home"])

# Coordenadas de inicio (Base en Aguascalientes)
st.sidebar.subheader("Punto de Salida")
lat0 = st.sidebar.number_input("Latitud Base", value=21.8853)
lon0 = st.sidebar.number_input("Longitud Base", value=-102.2916)

puntos = [[lat0, lon0]]

# Entradas para los pedidos
for i in range(num_puntos):
    st.sidebar.subheader(f"Pedido {i+1}")
    lat = st.sidebar.number_input(f"Latitud {i+1}", value=21.88 + (i*0.005), key=f"la{i}")
    lon = st.sidebar.number_input(f"Longitud {i+1}", value=-102.29 - (i*0.005), key=f"lo{i}")
    puntos.append([lat, lon])

def obtener_ruta(coords):
    url_coords = ";".join([f"{c[1]},{c[0]}" for c in coords])
    url = f"http://router.project-osrm.org/trip/v1/driving/{url_coords}?source=first&overview=full&geometries=geojson"
    r = requests.get(url)
    return r.json()

if st.button("Calcular Ruta Optimizada"):
    data = obtener_ruta(puntos)
    if data.get('code') == 'Ok':
        m = folium.Map(location=[lat0, lon0], zoom_start=13)
        
        # Ruta por calles
        linea = [[p[1], p[0]] for p in data['trips'][0]['geometry']['coordinates']]
        folium.PolyLine(linea, color="blue", weight=5).add_to(m)
        
        # Marcadores
        for wp in data['waypoints']:
            idx = wp['trips_index']
            pos = [wp['location'][1], wp['location'][0]]
            folium.Marker(pos, popup=f"Punto {idx}", 
                          icon=folium.Icon(color="green" if idx > 0 else "red", icon=icon_style)).add_to(m)
        
        st_folium(m, width=1000, height=600)
    else:
        st.error("Error al calcular. Revisa las coordenadas.")
