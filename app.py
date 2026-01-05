import streamlit as st
import folium
from streamlit_folium import st_folium

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Delivery AGS", layout="wide")

# --- 1. SELECTOR DE IDENTIDAD (Arriba a la izquierda) ---
# Usamos la barra lateral para que siempre esté accesible
with st.sidebar:
    st.title("👤 Identidad")
    rol = st.selectbox(
        "¿Quién eres?",
        ["Usuario / Cliente", "Repartidor", "Administrador"],
        help="Selecciona tu perfil para ver opciones personalizadas"
    )
    st.info(f"Sesión iniciada como: {rol}")

# --- 2. LÓGICA DEL MAPA (Para que no desaparezca) ---
# Inicializamos el estado del mapa si no existe
if 'mostrar_ruta' not in st.session_state:
    st.session_state.mostrar_ruta = False

st.title("📍 Sistema de Entrega AGS")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Configuración de Ruta")
    origen = st.text_input("Punto de origen", "Centro, Aguascalientes")
    destino = st.text_input("Punto de destino", "Norte, Aguascalientes")
    
    # Al hacer clic, cambiamos el estado a True
    if st.button("Calcular ruta"):
        st.session_state.mostrar_ruta = True

with col2:
    st.subheader("Mapa de Entrega")
    
    # Solo mostramos el mapa si el estado es True
    if st.session_state.mostrar_ruta:
        # Aquí creamos un mapa base (puedes añadir tu lógica de rutas aquí)
        m = folium.Map(location=[21.8823, -102.2826], zoom_start=13)
        
        # Ejemplo de marcador
        folium.Marker([21.8823, -102.2826], popup="Punto de Entrega").add_to(m)
        
        # Renderizamos el mapa
        st_folium(m, width=700, height=450)
    else:
        st.info("Configura los puntos y haz clic en 'Calcular ruta' para ver el mapa.")

# --- 3. INTERFAZ SEGÚN ROL ---
if rol == "Administrador":
    st.write("---")
    st.subheader("Panel de Control")
    st.write("Aquí puedes ver todas las entregas activas.")
elif rol == "Repartidor":
    st.write("---")
    st.subheader("Mis Pedidos Pendientes")
    st.checkbox("Marcar pedido #123 como entregado")
