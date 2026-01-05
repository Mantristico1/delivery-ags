import streamlit as st
import folium
from streamlit_folium import st_folium
import time

# 1. Configuración de página
st.set_page_config(page_title="Delivery AGS - Sistema Real", layout="wide")

# 2. INICIALIZACIÓN DE MEMORIA (Session State)
# Esto guarda las rutas para que no se borren al interactuar
if 'lista_rutas' not in st.session_state:
    st.session_state.lista_rutas = []  # Lista vacía de rutas

# 3. BARRA LATERAL - SELECTOR DE ROL
with st.sidebar:
    st.title("👤 Acceso")
    rol = st.selectbox("Selecciona tu rol:", ["Administrador", "Repartidor", "Cliente"])
    st.divider()
    if st.button("Limpiar todos los datos"):
        st.session_state.lista_rutas = []
        st.rerun()

# --- VISTA: ADMINISTRADOR (Crea las rutas) ---
if rol == "Administrador":
    st.title("🛠 Panel de Administración")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Crear Nueva Entrega")
        with st.form("nueva_ruta_form", clear_on_submit=True):
            origen = st.text_input("Punto de Origen")
            destino = st.text_input("Punto de Destino")
            cliente = st.text_input("Nombre del Cliente")
            enviar = st.form_submit_button("Añadir Ruta")
            
            if enviar and origen and destino:
                nueva = {
                    "id": len(st.session_state.lista_rutas) + 1,
                    "origen": origen,
                    "destino": destino,
                    "cliente": cliente,
                    "estado": "En camino",
                    "tiempo_estimado": "15-20 min"
                }
                st.session_state.lista_rutas.append(nueva)
                st.success("Ruta añadida con éxito")
                st.rerun()

    with col2:
        st.subheader("Rutas Activas")
        if not st.session_state.lista_rutas:
            st.info("No hay rutas creadas.")
        for r in st.session_state.lista_rutas:
            with st.expander(f"📦 Pedido #{r['id']} - {r['cliente']}"):
                st.write(f"**De:** {r['origen']} ⮕ **A:** {r['destino']}")
                # Mapa individual por ruta
                m = folium.Map(location=[21.8853, -102.2916], zoom_start=12)
                folium.Marker([21.8853, -102.2916], tooltip="Origen").add_to(m)
                st_folium(m, height=200, key=f"map_admin_{r['id']}")

# --- VISTA: REPARTIDOR (Solo lo esencial) ---
elif rol == "Repartidor":
    st.title("🛵 Panel del Repartidor")
    if not st.session_state.lista_rutas:
        st.warning("No tienes entregas asignadas por ahora.")
    else:
        # El repartidor ve la última ruta asignada o elige una
        ruta = st.session_state.lista_rutas[-1] 
        st.metric("Siguiente Entrega", f"Cliente: {ruta['cliente']}")
        st.write(f"📍 **Destino:** {ruta['destino']}")
        
        # Mapa grande para el repartidor
        st.subheader("Mapa de Navegación")
        m_rep = folium.Map(location=[21.8853, -102.2916], zoom_start=14)
        # Aquí simulamos la ubicación del repartidor y el destino
        folium.Marker([21.8853, -102.2916], icon=folium.Icon(color='blue', icon='motorcycle', prefix='fa')).add_to(m_rep)
        folium.Marker([21.8900, -102.2800], icon=folium.Icon(color='red')).add_to(m_rep)
        
        st_folium(m_rep, width=800, height=500, key="mapa_repartidor")
        
        if st.button("Marcar como Entregado"):
            st.balloons()
            st.success("¡Entrega finalizada!")

# --- VISTA: CLIENTE (Seguimiento) ---
elif rol == "Cliente":
    st.title("🏠 Seguimiento de tu Pedido")
    if not st.session_state.lista_rutas:
        st.info("No tienes pedidos activos en este momento.")
    else:
        ruta_cliente = st.session_state.lista_rutas[-1] # Ve su pedido
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.subheader("Estado del Envío")
            st.write(f"**Estatus:** {ruta_cliente['estado']}")
            st.write(f"**Tiempo estimado de llegada:** ⏳ {ruta_cliente['tiempo_estimado']}")
            st.progress(65) # Barra de progreso visual
            
        with col_c2:
            st.subheader("¿Dónde viene mi repartidor?")
            m_cli = folium.Map(location=[21.8853, -102.2916], zoom_start=14)
            # Icono del repartidor moviéndose
            folium.Marker([21.8870, -102.2850], popup="Tu repartidor", 
                          icon=folium.Icon(color='orange', icon='bicycle', prefix='fa')).add_to(m_cli)
            st_folium(m_cli, height=300, key="mapa_cliente")
            padding: 10px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
