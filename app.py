import streamlit as st
import folium
from streamlit_folium import st_folium

# 1. Configuración de la página
st.set_page_config(page_title="Delivery AGS", layout="wide")

# 2. Inicializar el estado del mapa (ESTO ES LO QUE FALTA)
# Esto hace que Streamlit "recuerde" si el mapa debe estar visible
if 'ver_mapa' not in st.session_state:
    st.session_state.ver_mapa = False

# 3. BARRA LATERAL (Tu selector de rol)
with st.sidebar:
    st.title("Configuración")
    rol = st.selectbox("Selecciona tu rol:", ["Administrador", "Repartidor", "Cliente"])
    st.write(f"Conectado como: **{rol}**")

# 4. CUERPO PRINCIPAL
st.title("📍 Sistema de Rutas Delivery AGS")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Datos de entrega")
    origen = st.text_input("Origen", "Tu ubicación")
    destino = st.text_input("Destino", "Punto de entrega")
    
    # Al hacer clic, activamos el estado
    if st.button("Calcular Ruta"):
        st.session_state.ver_mapa = True

with col2:
    if st.session_state.ver_mapa:
        st.subheader("Mapa de Ruta")
        # Creamos el mapa (Coordenadas de Aguascalientes)
        m = folium.Map(location=[21.8853, -102.2916], zoom_start=13)
        folium.Marker([21.8853, -102.2916], popup="Punto A").add_to(m)
        
        # Mostrar el mapa usando st_folium
        st_folium(m, width=700, height=500)
    else:
        st.info("Haz clic en 'Calcular Ruta' para visualizar el mapa.")

# 5. Interfaz para celular (ajuste visual)
st.markdown("""
    <style>
    /* Esto ayuda a que en celular los elementos no se vean amontonados */
    @media (max-width: 600px) {
        .main {
            padding: 10px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
