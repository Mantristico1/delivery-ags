import streamlit as st
import folium
from streamlit_folium import st_folium
import datetime
import pandas as pd
from PIL import Image
import io
import base64

# --- 1. CONFIGURACIÓN COMPARTIDA ---
st.set_page_config(page_title="AGS Delivery - Sistema Integral", layout="wide")

@st.cache_resource
def obtener_db():
    return {
        "usuarios": {
            "admin@delivery.com": {"clave": "1234", "rol": "Administrador", "nombre": "Manuel Montes", "foto": None, "activo": True},
        },
        "menu": [
            {"id": 1, "nombre": "Hamburguesa AGS", "desc": "Carne premium y queso", "precio": 120.0, "foto": None}
        ],
        "pedidos": [],
        "chats": {} 
    }

db = obtener_db()

# --- 2. LOGUEO Y SESIÓN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.email = ""

if not st.session_state.auth:
    izq, centro, der = st.columns([1, 2, 1])
    with centro:
        st.title("🚚 AGS Delivery")
        # Quitamos pestañas de registro, solo login directo
        e = st.text_input("Email")
        p = st.text_input("Contraseña", type="password")
        if st.button("Entrar", use_container_width=True):
            user = db["usuarios"].get(e)
            if user and user["clave"] == p and user["activo"]:
                st.session_state.auth = True
                st.session_state.email = e
                st.rerun()
            else: st.error("Acceso incorrecto o cuenta desactivada.")
        
        with st.expander("¿No tienes cuenta? Regístrate aquí"):
            ne = st.text_input("Nuevo Email")
            nn = st.text_input("Tu Nombre")
            np = st.text_input("Tu Clave", type="password")
            if st.button("Crear Cuenta de Cliente"):
                db["usuarios"][ne] = {"clave": np, "rol": "Cliente", "nombre": nn, "foto": None, "activo": True}
                st.success("¡Listo! Ya puedes iniciar sesión.")
    st.stop()

u_info = db["usuarios"][st.session_state.email]
u_rol = u_info["rol"]

# --- 3. BARRA LATERAL (NAVEGACIÓN) ---
with st.sidebar:
    st.image(u_info["foto"] if u_info["foto"] else "https://cdn-icons-png.flaticon.com/512/149/149071.png", width=80)
    st.subheader(u_info["nombre"])
    
    # Navegación por Rol
    if u_rol == "Cliente":
        menu = st.radio("Menú", ["🏠 Inicio (Menú)", "🛒 Mi Carrito y Rastreo", "👤 Perfil"])
    elif u_rol == "Trabajador":
        menu = st.radio("Menú", ["🏠 Pedidos Staff", "🍴 Gestionar Menú", "💬 Chats", "👤 Perfil"])
    elif u_rol == "Administrador":
        menu = st.radio("Menú", ["🏠 Panel Staff", "👥 Usuarios", "🍴 Menú", "👤 Perfil"])

    if st.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

# --- 4. VISTA: CONFIGURACIÓN DE PERFIL (BOTÓN APARTE) ---
if menu == "👤 Perfil":
    st.title("👤 Mi Perfil")
    col_v, col_e = st.columns([1, 2])
    with col_v:
        st.image(u_info["foto"] if u_info["foto"] else "https://cdn-icons-png.flaticon.com/512/149/149071.png", width=150)
    
    with st.expander("⚙️ Configuración y Edición de Cuenta"):
        archivo = st.file_uploader("Subir foto de galería", type=['jpg','png'])
        if archivo:
            # Lógica de procesamiento de imagen mantenida
            img = Image.open(archivo)
            img.thumbnail((300, 300))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            u_info["foto"] = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
            st.success("Foto cargada")
        
        u_info["nombre"] = st.text_input("Nombre", value=u_info["nombre"])
        u_info["clave"] = st.text_input("Contraseña", value=u_info["clave"], type="password")
        if st.button("Guardar Cambios"): st.rerun()

# --- 5. VISTA: CLIENTE (MENU E INICIO) ---
elif menu == "🏠 Inicio (Menú)" and u_rol == "Cliente":
    st.title("🍕 Menú del Día")
    if 'carrito' not in st.session_state: st.session_state.carrito = []
    
    for item in db["menu"]:
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1: 
                if item["foto"]: st.image(item["foto"], width=100)
            with c2: 
                st.subheader(item["nombre"])
                st.write(item["desc"])
            with c3:
                st.write(f"**${item['precio']}**")
                if st.button("🛒 Agregar", key=f"buy_{item['id']}"):
                    st.session_state.carrito.append(item)
                    st.toast("Agregado al carrito")

elif menu == "🛒 Mi Carrito y Rastreo":
    st.title("🛒 Estado de mi Pedido")
    # Carrito actual
    if st.session_state.carrito:
        st.write("### Productos seleccionados")
        df_car = pd.DataFrame(st.session_state.carrito)
        st.table(df_car[['nombre', 'precio']])
        total = sum(i['precio'] for i in st.session_state.carrito)
        if st.button(f"Confirmar Pedido (${total}) - Pago Efectivo"):
            # Generar Pedido
            np = {
                "id": len(db["pedidos"])+1, "cl_e": st.session_state.email, "cl_n": u_info["nombre"],
                "items": st.session_state.carrito.copy(), "total": total, "estado": "Recibido",
                "rep": None, "fecha": datetime.datetime.now(), "eta": "30-45 min"
            }
            db["pedidos"].append(np)
            st.session_state.carrito = []
            st.success("Pedido realizado con éxito")
            st.rerun()
    
    # Rastreo y Ticket
    st.divider()
    mi_p = next((p for p in db["pedidos"] if p["cl_e"] == st.session_state.email and p["estado"] != "Entregado"), None)
    if mi_p:
        st.subheader("🎫 Ticket de Seguimiento")
        st.info(f"Estado: {mi_p['estado']} | Tiempo estimado: {mi_p['eta']}")
        # Mapa de rastreo mantenido
        m = folium.Map(location=[21.88, -102.29], zoom_start=14)
        folium.Marker([21.88, -102.29], popup="Tu Repartidor", icon=folium.Icon(color='orange', icon='motorcycle', prefix='fa')).add_to(m)
        st_folium(m, height=300, key="mapa_cliente")

# --- 6. VISTA: TRABAJADOR Y STAFF (PEDIDOS Y MENU) ---
elif menu in ["🏠 Pedidos Staff", "🏠 Panel Staff"]:
    st.title("📑 Gestión de Pedidos Generados")
    for p in db["pedidos"]:
        with st.expander(f"Pedido #{p['id']} - {p['cl_n']} ({p['estado']})"):
            st.write(f"Dirección: {p.get('dir', 'No especificada')}")
            st.write(f"Total: ${p['total']}")
            # Solo admin puede asignar
            if u_rol == "Administrador" and not p["rep"]:
                reps = {u['nombre']: k for k, u in db["usuarios"].items() if u['rol'] == 'Repartidor'}
                rs = st.selectbox("Asignar Repartidor", list(reps.keys()), key=f"rep_{p['id']}")
                if st.button("Confirmar Repartidor", key=f"btn_{p['id']}"):
                    p["rep"] = reps[rs]
                    p["estado"] = "En camino"
                    st.rerun()

elif menu == "🍴 Gestionar Menú":
    st.title("🍴 Administración del Menú")
    # Agregar
    with st.expander("➕ Añadir Nuevo Platillo"):
        nom = st.text_input("Nombre")
        pre = st.number_input("Precio", min_value=0.0)
        des = st.text_area("Descripción")
        if st.button("Guardar"):
            db["menu"].append({"id": len(db["menu"])+1, "nombre": nom, "precio": pre, "desc": des, "foto": None})
            st.rerun()
    
    # Editar/Borrar
    for i, item in enumerate(db["menu"]):
        with st.container(border=True):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                item["nombre"] = st.text_input("Editar Nombre", value=item["nombre"], key=f"en_{i}")
                item["precio"] = st.number_input("Editar Precio", value=item["precio"], key=f"ep_{i}")
            with col_b:
                if st.button("🗑️ Quitar", key=f"rb_{i}"):
                    db["menu"].pop(i)
                    st.rerun()

# --- 7. VISTA: ADMIN (GESTIÓN USUARIOS DIVIDIDA) ---
elif menu == "👥 Usuarios" and u_rol == "Administrador":
    st.title("👥 Control de Usuarios")
    sub_admin = st.radio("Acción:", ["Registrar Staff", "Gestión de Usuarios Activos"], horizontal=True)
    
    if sub_admin == "Registrar Staff":
        with st.form("reg_staff"):
            se = st.text_input("Email Staff")
            sn = st.text_input("Nombre Staff")
            sp = st.text_input("Clave")
            sr = st.selectbox("Rol", ["Trabajador", "Repartidor"])
            if st.form_submit_button("Dar de Alta"):
                db["usuarios"][se] = {"clave": sp, "rol": sr, "nombre": sn, "foto": None, "activo": True}
                st.success("Staff creado con éxito")
                
    else:
        filtro_rol = st.selectbox("Ver por tipo:", ["Todos", "Cliente", "Repartidor", "Trabajador"])
        for email, info in db["usuarios"].items():
            if filtro_rol == "Todos" or info["rol"] == filtro_rol:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"**{info['nombre']}** ({email})")
                    c2.write(f"Rol: {info['rol']}")
                    label_baja = "Dar de Baja" if info["activo"] else "Reactivar"
                    if c3.button(label_baja, key=f"acc_{email}"):
                        info["activo"] = not info["activo"]
                        st.rerun()
