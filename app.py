import streamlit as st
import folium
from streamlit_folium import st_folium
import urllib.parse
import re
from PIL import Image
import io
import base64

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Delivery AGS Pro", layout="wide")

# Función para validar email
def es_correo_valido(correo):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', correo) is not None

# Función para procesar imagen y convertirla en URL interna
def procesar_foto(subida):
    if subida is not None:
        img = Image.open(subida)
        img.thumbnail((300, 300))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        byte_im = buf.getvalue()
        return f"data:image/png;base64,{base64.b64encode(byte_im).decode()}"
    return None

# 2. BASE DE DATOS COMPARTIDA
@st.cache_resource
def obtener_db():
    return {
        "pedidos": [],
        "usuarios": {
            "admin@delivery.com": {
                "clave": "1234", 
                "rol": "Administrador", 
                "nombre": "Manuel Montes", 
                "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
                "disponible": True
            }
        }
    }

db = obtener_db()

# 3. ESTADO DE SESIÓN
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.user_email = ""
    st.session_state.user_rol = ""

# --- LOGIN / REGISTRO ---
if not st.session_state.autenticado:
    izq, centro, der = st.columns([1, 2, 1])
    with centro:
        st.markdown("<h1 style='text-align: center;'>🚚 Delivery AGS</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔑 Iniciar Sesión", "📝 Registro"])
        
        with tab_log:
            e_l = st.text_input("Correo:", key="l_email")
            p_l = st.text_input("Contraseña:", type="password", key="l_pass")
            if st.button("Entrar", use_container_width=True):
                if e_l in db["usuarios"] and db["usuarios"][e_l]["clave"] == p_l:
                    st.session_state.autenticado = True
                    st.session_state.user_email = e_l
                    st.session_state.user_rol = db["usuarios"][e_l]["rol"]
                    st.rerun()
                else: st.error("Datos incorrectos")

        with tab_reg:
            r_r = st.selectbox("Rol", ["Cliente", "Repartidor"], key="r_rol")
            e_r = st.text_input("Correo electrónico:", key="r_email")
            n_r = st.text_input("Nombre Completo:", key="r_name")
            p_r = st.text_input("Contraseña:", type="password", key="r_pass")
            if st.button("Crear Cuenta", use_container_width=True):
                if es_correo_valido(e_r) and n_r and p_r:
                    db["usuarios"][e_r] = {
                        "clave": p_r, "rol": r_r, "nombre": n_r, 
                        "foto": "https://cdn-icons-png.flaticon.com/512/149/149071.png",
                        "disponible": True
                    }
                    st.success("¡Registro exitoso! Ya puedes entrar.")
                else: st.warning("Datos incompletos o correo inválido.")
    st.stop()

# --- BARRA LATERAL (Navegación Limpia) ---
u_info = db["usuarios"][st.session_state.user_email]
with st.sidebar:
    st.image(u_info["foto"], width=100)
    st.title(u_info["nombre"])
    st.caption(f"Rol: {st.session_state.user_rol}")
    st.divider()
    
    # Navegación
    menu = st.radio("Ir a:", ["🏠 Inicio", "👤 Mi Perfil"])
    
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# --- VISTA: MI PERFIL (GESTIÓN TOTAL) ---
if menu == "👤 Mi Perfil":
    st.title("⚙️ Configuración de Mi Cuenta")
    col_f, col_d = st.columns([1, 2])
    
    with col_f:
        st.image(u_info["foto"], width=200)
        archivo_foto = st.file_uploader("Actualizar foto de perfil", type=['png', 'jpg', 'jpeg'])
        if archivo_foto:
            nueva_foto = procesar_foto(archivo_foto)
            if st.button("Guardar Nueva Foto"):
                u_info["foto"] = nueva_foto
                st.success("Foto actualizada.")
                st.rerun()
    
    with col_d:
        with st.form("perfil_form"):
            st.subheader("Datos Personales")
            nuevo_nom = st.text_input("Nombre para mostrar", value=u_info["nombre"])
            nueva_clv = st.text_input("Nueva contraseña (deja en blanco para no cambiar)", type="password")
            
            if st.session_state.user_rol == "Repartidor":
                st.divider()
                st.subheader("Estado de Trabajo")
                disp = st.toggle("Disponible para recibir pedidos", value=u_info.get("disponible", True))
                u_info["disponible"] = disp
            
            if st.form_submit_button("Guardar Cambios"):
                u_info["nombre"] = nuevo_nom
                if nueva_clv: u_info["clave"] = nueva_clv
                st.success("Información actualizada correctamente.")
                st.rerun()
        
        if st.session_state.user_rol == "Cliente":
            st.warning("⚠️ ¿Tienes problemas con un pedido?")
            if st.button("Contactar Soporte"):
                st.info("Un administrador se pondrá en contacto contigo pronto.")

# --- VISTA: INICIO (FUNCIONALIDAD SEGÚN ROL) ---
elif menu == "🏠 Inicio":
    if st.session_state.user_rol == "Administrador":
        st.title(f"🛠 Panel Maestro - {u_info['nombre']}")
        # Aquí va la lógica de crear pedidos que ya teníamos
        c1, c2 = st.columns([1, 2])
        with c1:
            st.subheader("Nuevo Pedido")
            clientes = {u['nombre']: k for k, u in db["usuarios"].items() if u['rol'] == 'Cliente'}
            reps = {u['nombre']: k for k, u in db["usuarios"].items() if u['rol'] == 'Repartidor' and u.get("disponible", True)}
            
            with st.form("p_admin_form"):
                cl_sel = st.selectbox("Seleccionar Cliente", list(clientes.keys()) if clientes else ["Sin clientes"])
                direc = st.text_input("Dirección de destino")
                rep_sel = st.selectbox("Asignar Repartidor (Solo disponibles)", list(reps.keys()) if reps else ["Sin repartidores"])
                if st.form_submit_button("Crear Envío"):
                    db["pedidos"].append({
                        "id": len(db["pedidos"])+1, "cliente_nombre": cl_sel, "cliente_email": clientes[cl_sel],
                        "direccion": direc, "rep_email": reps[rep_sel], "estado": "En camino"
                    })
                    st.rerun()
        with c2:
            st.subheader("Mapa de Operaciones")
            m = folium.Map(location=[21.88, -102.29], zoom_start=12)
            st_folium(m, height=400, key="mapa_admin")

    elif st.session_state.user_rol == "Repartidor":
        st.title("🛵 Tus Rutas Activas")
        # Mostrar pedidos asignados al email logueado
        ...

    elif st.session_state.user_rol == "Cliente":
        st.title("📦 Seguimiento de mi Pedido")
        # Mostrar mapa y estado del pedido
        ...
