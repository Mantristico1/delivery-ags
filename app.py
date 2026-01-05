import streamlit as st
import folium
from streamlit_folium import st_folium
import datetime
import pandas as pd
from PIL import Image
import io
import base64

# --- 1. CONFIGURACIÓN E INTERFAZ MAESTRA ---
st.set_page_config(page_title="AGS Delivery - Sistema Integral v3", layout="wide")

# Función para convertir imágenes a Base64 para guardarlas en la DB simulada
def procesar_imagen(archivo):
    if archivo:
        img = Image.open(archivo)
        img.thumbnail((400, 400))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
    return None

# --- 2. BASE DE DATOS VINCULADA (MEMORIA COMPARTIDA) ---
@st.cache_resource
def inicializar_db():
    return {
        "usuarios": {
            "admin@delivery.com": {
                "clave": "1234", "rol": "Administrador", "nombre": "Manuel Montes", 
                "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png", "activo": True
            }
        },
        "menu": [
            {"id": 1, "nombre": "Hamburguesa AGS", "desc": "Premium con papas", "precio": 120.0, "foto": None}
        ],
        "pedidos": [],
        "chats": {} # Formato: {id_pedido: [{"autor": "", "rol": "", "txt": ""}]}
    }

db = inicializar_db()

# --- 3. GESTIÓN DE SESIÓN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.email = ""
    st.session_state.carrito = []

# --- 4. PANTALLA DE ACCESO (LOGIN / REGISTRO) ---
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🚚 AGS Delivery</h1>", unsafe_allow_html=True)
        # Login Directo
        with st.container(border=True):
            e = st.text_input("Correo electrónico")
            p = st.text_input("Contraseña", type="password")
            if st.button("Iniciar Sesión", use_container_width=True):
                user = db["usuarios"].get(e)
                if user and user["clave"] == p:
                    if user["activo"]:
                        st.session_state.auth = True
                        st.session_state.email = e
                        st.rerun()
                    else: st.error("Cuenta desactivada. Contacta al Admin.")
                else: st.error("Credenciales incorrectas.")
        
        # Registro exclusivo para clientes
        with st.expander("📝 ¿Eres nuevo cliente? Regístrate aquí"):
            re = st.text_input("Email", key="reg_e")
            rn = st.text_input("Nombre Completo", key="reg_n")
            rp = st.text_input("Contraseña", type="password", key="reg_p")
            if st.button("Crear Cuenta de Cliente"):
                if re and rn and rp and re not in db["usuarios"]:
                    db["usuarios"][re] = {"clave": rp, "rol": "Cliente", "nombre": rn, "foto": None, "activo": True}
                    st.success("¡Registro exitoso! Ya puedes iniciar sesión.")
                else: st.error("Datos inválidos o correo ya registrado.")
    st.stop()

# --- 5. ENTORNO DEL USUARIO LOGUEADO ---
u_info = db["usuarios"][st.session_state.email]
u_rol = u_info["rol"]

with st.sidebar:
    st.image(u_info["foto"] if u_info["foto"] else "https://cdn-icons-png.flaticon.com/512/149/149071.png", width=100)
    st.title(u_info["nombre"])
    st.write(f"Acceso: **{u_rol}**")
    st.divider()
    
    # Definición de Menús por Rol
    if u_rol == "Cliente":
        menu = st.radio("Menú Principal", ["🏠 Menú Digital", "🛒 Mi Carrito y Pedidos", "👤 Mi Perfil"])
    elif u_rol == "Trabajador":
        menu = st.radio("Menú Principal", ["🏠 Panel de Pedidos", "🍴 Gestionar Comida", "👤 Mi Perfil"])
    elif u_rol == "Administrador":
        menu = st.radio("Menú Principal", ["🏠 Panel de Pedidos", "👥 Control de Usuarios", "🍴 Gestionar Comida", "👤 Mi Perfil"])
    
    st.divider()
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

# --- 6. FUNCIONALIDAD: MI PERFIL (COMÚN A TODOS) ---
if menu == "👤 Mi Perfil":
    st.title("⚙️ Configuración de Cuenta")
    with st.container(border=True):
        col_img, col_data = st.columns([1, 2])
        with col_img:
            st.image(u_info["foto"] if u_info["foto"] else "https://cdn-icons-png.flaticon.com/512/149/149071.png", width=200)
            archivo = st.file_uploader("Cambiar foto (Galería)", type=['jpg', 'png', 'jpeg'])
            if archivo:
                u_info["foto"] = procesar_imagen(archivo)
                st.rerun()
        with col_data:
            u_info["nombre"] = st.text_input("Nombre de Usuario", value=u_info["nombre"])
            u_info["clave"] = st.text_input("Contraseña", value=u_info["clave"], type="password")
            if u_rol == "Repartidor":
                u_info["disponible"] = st.toggle("Disponible para trabajar", value=u_info.get("disponible", True))
            if st.button("Actualizar Información"):
                st.success("Cambios guardados.")
                st.rerun()

# --- 7. FUNCIONALIDAD: CLIENTE (TIENDA Y CARRITO) ---
elif menu == "🏠 Menú Digital" and u_rol == "Cliente":
    st.title("🍴 ¿Qué se te antoja hoy?")
    # Mostrar el menú que el trabajador/admin gestiona
    cols = st.columns(2)
    for i, platillo in enumerate(db["menu"]):
        with cols[i % 2]:
            with st.container(border=True):
                if platillo["foto"]: st.image(platillo["foto"], use_column_width=True)
                st.subheader(platillo["nombre"])
                st.write(platillo["desc"])
                st.write(f"### ${platillo['precio']}")
                if st.button(f"Añadir al Carrito", key=f"btn_{platillo['id']}"):
                    st.session_state.carrito.append(platillo)
                    st.toast(f"{platillo['nombre']} añadido")

elif menu == "🛒 Mi Carrito y Pedidos":
    st.title("🛒 Mi Carrito")
    if st.session_state.carrito:
        df_car = pd.DataFrame(st.session_state.carrito)
        st.table(df_car[["nombre", "precio"]])
        total = sum(item["precio"] for item in st.session_state.carrito)
        st.write(f"## Total: ${total}")
        dir_envio = st.text_input("Dirección de entrega")
        if st.button("Confirmar Pedido (Efectivo)"):
            if dir_envio:
                nuevo_p = {
                    "id": len(db["pedidos"]) + 1, "cliente_email": st.session_state.email, 
                    "cliente_nombre": u_info["nombre"], "productos": st.session_state.carrito.copy(),
                    "total": total, "direccion": dir_envio, "estado": "Recibido", 
                    "repartidor": None, "fecha": datetime.datetime.now(), "lat": 21.88, "lon": -102.29
                }
                db["pedidos"].append(nuevo_p)
                st.session_state.carrito = []
                st.success("¡Pedido enviado! Revisa el seguimiento abajo.")
                st.rerun()
            else: st.warning("Por favor ingresa una dirección.")
    
    st.divider()
    st.title("📜 Historial y Rastreo")
    mis_pedidos = [p for p in db["pedidos"] if p["cliente_email"] == st.session_state.email]
    for p in reversed(mis_pedidos):
        with st.expander(f"Pedido #{p['id']} - {p['fecha'].strftime('%H:%M')} ({p['estado']})"):
            st.write(f"**Total:** ${p['total']} | **Dirección:** {p['direccion']}")
            if p["estado"] == "En camino":
                st.warning("🛵 El repartidor está cerca.")
                m = folium.Map(location=[p['lat'], p['lon']], zoom_start=15)
                folium.Marker([p['lat'], p['lon']], icon=folium.Icon(color='orange', icon='motorcycle', prefix='fa')).add_to(m)
                st_folium(m, height=250, key=f"mapa_{p['id']}")
            # Botón de Chat por pedido
            if st.button("💬 Chat con Staff", key=f"chat_cli_{p['id']}"):
                st.session_state.chat_p_id = p['id']

# --- 8. FUNCIONALIDAD: STAFF (TRABAJADOR / ADMIN) ---
elif menu in ["🏠 Panel de Pedidos", "🏠 Panel Staff"]:
    st.title("📋 Gestión Logística")
    for p in db["pedidos"]:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                st.write(f"**#{p['id']} - {p['cliente_nombre']}**")
                st.write(f"📍 {p['direccion']} | 💰 ${p['total']}")
            with c2:
                if u_rol == "Administrador" and not p["repartidor"]:
                    reps = {u['nombre']: k for k, u in db["usuarios"].items() if u['rol'] == 'Repartidor' and u.get('disponible', True)}
                    if reps:
                        r_sel = st.selectbox("Asignar Repartidor", list(reps.keys()), key=f"asig_{p['id']}")
                        if st.button("Enviar Pedido", key=f"btn_asig_{p['id']}"):
                            p["repartidor"] = reps[r_sel]
                            p["estado"] = "En camino"
                            st.rerun()
                else:
                    st.write(f"Estado: **{p['estado']}**")
                    if p["repartidor"]: st.write(f"Repartidor: {db['usuarios'][p['repartidor']]['nombre']}")
            with c3:
                if st.button("💬 Chat", key=f"chat_staff_{p['id']}"):
                    st.session_state.chat_p_id = p['id']

elif menu == "🍴 Gestionar Comida":
    st.title("🍱 Administración del Menú")
    with st.expander("➕ Agregar Nuevo Platillo"):
        nom = st.text_input("Nombre del plato")
        pre = st.number_input("Precio", min_value=0.0)
        des = st.text_area("Descripción")
        fot = st.file_uploader("Imagen")
        if st.button("Subir al Menú"):
            db["menu"].append({"id": len(db["menu"])+1, "nombre": nom, "precio": pre, "desc": des, "foto": procesar_imagen(fot)})
            st.rerun()
    
    st.write("### Menú Actual (Editar o Eliminar)")
    for i, item in enumerate(db["menu"]):
        with st.container(border=True):
            col_e1, col_e2, col_e3 = st.columns([2, 1, 1])
            item["nombre"] = col_e1.text_input("Nombre", value=item["nombre"], key=f"edit_n_{i}")
            item["precio"] = col_e2.number_input("Precio", value=item["precio"], key=f"edit_p_{i}")
            if col_e3.button("🗑️ Quitar", key=f"del_{i}"):
                db["menu"].pop(i)
                st.rerun()

# --- 9. FUNCIONALIDAD: EXCLUSIVA ADMIN (USUARIOS) ---
elif menu == "👥 Control de Usuarios" and u_rol == "Administrador":
    st.title("👥 Panel de Usuarios - Manuel Montes")
    sub_tab = st.radio("Acción", ["Gestión de Cuentas", "Registrar Nuevo Staff"], horizontal=True)
    
    if sub_tab == "Registrar Nuevo Staff":
        with st.form("nuevo_staff"):
            st.write("Crea cuentas para Trabajadores o Repartidores")
            ne = st.text_input("Email")
            nn = st.text_input("Nombre")
            np = st.text_input("Clave")
            nr = st.selectbox("Rol", ["Trabajador", "Repartidor"])
            if st.form_submit_button("Dar de Alta"):
                db["usuarios"][ne] = {"clave": np, "rol": nr, "nombre": nn, "foto": None, "activo": True, "disponible": True}
                st.success(f"{nr} registrado con éxito.")
    
    else:
        filtro = st.selectbox("Filtrar por:", ["Todos", "Cliente", "Repartidor", "Trabajador"])
        for email, info in db["usuarios"].items():
            if filtro == "Todos" or info["rol"] == filtro:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"**{info['nombre']}** ({email})")
                    c2.write(f"Rol: {info['rol']}")
                    status = "Activo" if info["activo"] else "Baja"
                    if c3.button(f"Alternar: {status}", key=f"status_{email}"):
                        info["activo"] = not info["activo"]
                        st.rerun()

# --- 10. VENTANA FLOTANTE DE CHAT (COLORES POR ROL) ---
if 'chat_p_id' in st.session_state:
    id_p = st.session_state.chat_p_id
    st.divider()
    st.subheader(f"💬 Chat del Pedido #{id_p}")
    if id_p not in db["chats"]: db["chats"][id_p] = []
    
    with st.container(height=300):
        for m in db["chats"][id_p]:
            color = "#D1E8FF" if m["rol"] == "Cliente" else "#D1FFD7" if m["rol"] == "Repartidor" else "#FFE0D1"
            st.markdown(f"""<div style='background-color:{color}; padding:10px; border-radius:10px; margin-bottom:5px; color:black;'>
            <b>[{m['rol']}] {m['autor']}:</b> {m['txt']}</div>""", unsafe_allow_html=True)
    
    chat_txt = st.chat_input("Escribe tu mensaje...")
    if chat_txt:
        db["chats"][id_p].append({"autor": u_info["nombre"], "rol": u_rol, "txt": chat_txt})
        st.rerun()
    if st.button("Cerrar Chat"):
        del st.session_state.chat_p_id
        st.rerun()
