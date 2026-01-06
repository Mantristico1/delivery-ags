import streamlit as st
import folium
from streamlit_folium import st_folium
import datetime
import pandas as pd
from PIL import Image
import io
import base64

import sqlite3

def init_db():
    """Initializes the SQLite database with multi-store support."""
    conn = sqlite3.connect('ags_delivery.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # 1. Stores Table (The Tenant)
    cursor.execute('''CREATE TABLE IF NOT EXISTS stores 
                      (id INTEGER PRIMARY KEY, name TEXT, slug TEXT UNIQUE)''')
    
    # 2. Users Table (Linked to Store)
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, store_id INTEGER, email TEXT, 
                       password TEXT, role TEXT, name TEXT, is_active INTEGER,
                       FOREIGN KEY(store_id) REFERENCES stores(id))''')
    
    # 3. Menu Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS menu 
                      (id INTEGER PRIMARY KEY, store_id INTEGER, name TEXT, 
                       price REAL, description TEXT, image_64 TEXT,
                       FOREIGN KEY(store_id) REFERENCES stores(id))''')
    
    # 4. Orders Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders 
                      (id INTEGER PRIMARY KEY, store_id INTEGER, client_id TEXT, 
                       driver_id TEXT, total REAL, address TEXT, status TEXT, 
                       timestamp DATETIME, FOREIGN KEY(store_id) REFERENCES stores(id))''')

    conn.commit()
    return conn

# Singleton Connection
conn = init_db()

# --- 1. CONFIGURACIÓN E INTERFAZ MAESTRA ---
st.set_page_config(page_title="AGS Delivery - Sistema Maestro", layout="wide", initial_sidebar_state="expanded")

# Función para codificar imágenes de la galería
def procesar_imagen_binaria(archivo):
    if archivo:
        img = Image.open(archivo)
        img.thumbnail((500, 500))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
    return None

# --- 2. BASE DE DATOS (PERSISTENCIA EN SESSION STATE) ---
if 'db' not in st.session_state:
    st.session_state.db = {
        "usuarios": {
            "admin@delivery.com": {
                "clave": "1234", "rol": "Administrador", "nombre": "Manuel Montes", 
                "foto": None, "activo": True
            }
        },
        "menu": [
            {"id": 1, "nombre": "Hamburguesa Especial", "desc": "Carne Angus, tocino y papas", "precio": 145.0, "foto": None}
        ],
        "pedidos": [],
        "chats": {}
    }

db = st.session_state.db

# --- 3. CONTROL DE ACCESO (LOGIN Y REGISTRO) ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.usuario_actual = ""
    st.session_state.carrito = []

if not st.session_state.auth:
    col_a, col_b, col_c = st.columns([1, 1.5, 1])
    with col_b:
        st.markdown("<h1 style='text-align: center;'>🚚 AGS Delivery</h1>", unsafe_allow_html=True)
        tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Registro Cliente"])
        
        with tab_login:
            correo_ingreso = st.text_input("Correo electrónico")
            clave_ingreso = st.text_input("Contraseña", type="password")
            if st.button("ENTRAR AL SISTEMA", use_container_width=True):
                user = db["usuarios"].get(correo_ingreso)
                if user and user["clave"] == clave_ingreso:
                    if user["activo"]:
                        st.session_state.auth = True
                        st.session_state.usuario_actual = correo_ingreso
                        st.rerun()
                    else: st.error("Cuenta suspendida. Contacte al administrador.")
                else: st.error("Credenciales inválidas.")
        
        with tab_registro:
            st.info("Crea tu cuenta para pedir comida a domicilio.")
            nuevo_correo = st.text_input("Email para tu cuenta")
            nuevo_nombre = st.text_input("Nombre completo")
            nueva_clave = st.text_input("Contraseña nueva", type="password")
            if st.button("CREAR MI CUENTA"):
                if nuevo_correo and nuevo_nombre and nueva_clave:
                    db["usuarios"][nuevo_correo] = {
                        "clave": nueva_clave, "rol": "Cliente", "nombre": nuevo_nombre, 
                        "foto": None, "activo": True
                    }
                    st.success("¡Registro exitoso! Ya puedes iniciar sesión.")
                else: st.warning("Por favor rellena todos los campos.")
    st.stop()

# --- 4. DATOS DEL USUARIO LOGUEADO ---
u_data = db["usuarios"][st.session_state.usuario_actual]
u_rol = u_data["rol"]

# --- 5. SIDEBAR DE NAVEGACIÓN ---
with st.sidebar:
    if u_data["foto"]:
        st.image(u_data["foto"], width=120)
    else:
        st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=120)
    
    st.title(u_data["nombre"])
    st.markdown(f"📍 **Modo: {u_rol}**")
    st.divider()
    
    # Menú dinámico por Rol
    if u_rol == "Cliente":
        menu = st.radio("NAVEGACIÓN", ["🍴 Menú Digital", "🛒 Mi Carrito", "🎫 Mis Pedidos", "👤 Perfil"])
    elif u_rol == "Trabajador":
        menu = st.radio("NAVEGACIÓN", ["📋 Pedidos Entrantes", "🍱 Gestionar Menú", "👤 Perfil"])
    elif u_rol == "Repartidor":
        menu = st.radio("NAVEGACIÓN", ["🛵 Mis Entregas", "👤 Perfil"])
    elif u_rol == "Administrador":
        menu = st.radio("NAVEGACIÓN", ["📊 Panel de Control", "👥 Usuarios", "🍱 Gestionar Menú", "👤 Perfil"])

    st.divider()
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# --- 6. FUNCIONALIDAD: PERFIL (COMÚN) ---
if menu == "👤 Perfil":
    st.header("👤 Mi Perfil de Usuario")
    c1, c2 = st.columns(2)
    with c1:
        u_data["nombre"] = st.text_input("Nombre de Usuario", value=u_data["nombre"])
        u_data["clave"] = st.text_input("Contraseña", value=u_data["clave"], type="password")
    with c2:
        archivo_foto = st.file_uploader("Actualizar foto de perfil", type=['jpg', 'png'])
        if archivo_foto:
            u_data["foto"] = procesar_imagen_binaria(archivo_foto)
    if st.button("Guardar Cambios"):
        st.success("Perfil actualizado correctamente.")

# --- 7. FUNCIONALIDAD: CLIENTE (UBER EATS EXPERIENCE) ---
elif menu == "🍴 Menú Digital":
    st.title("🍴 ¿Qué deseas comer hoy?")
    st.markdown("---")
    cols = st.columns(2)
    for i, platillo in enumerate(db["menu"]):
        with cols[i % 2]:
            with st.container(border=True):
                if platillo["foto"]:
                    st.image(platillo["foto"], use_column_width=True)
                st.subheader(platillo["nombre"])
                st.write(platillo["desc"])
                st.markdown(f"### **${platillo['precio']}**")
                if st.button(f"Añadir al Carrito", key=f"add_{platillo['id']}"):
                    st.session_state.carrito.append(platillo)
                    st.toast(f"¡{platillo['nombre']} añadido!")

elif menu == "🛒 Mi Carrito":
    st.title("🛒 Tu Carrito de Compras")
    if not st.session_state.carrito:
        st.info("Tu carrito está vacío. ¡Ve al menú y elige algo rico!")
    else:
        total = 0
        for i, it in enumerate(st.session_state.carrito):
            col_a, col_b = st.columns([4, 1])
            col_a.write(f"**{it['nombre']}** - ${it['precio']}")
            total += it['precio']
            if col_b.button("❌", key=f"del_car_{i}"):
                st.session_state.carrito.pop(i)
                st.rerun()
        
        st.divider()
        st.write(f"## Total a pagar: ${total}")
        direccion = st.text_input("Dirección de entrega (Ej. Calle Juárez #123 o Link de Maps)")
        
        if st.button("CONFIRMAR PEDIDO", use_container_width=True):
            if direccion:
                nuevo_p = {
                    "id": len(db["pedidos"]) + 1,
                    "email_cliente": st.session_state.usuario_actual,
                    "nombre_cliente": u_data["nombre"],
                    "productos": st.session_state.carrito.copy(),
                    "total": total,
                    "direccion": direccion,
                    "estado": "Preparando",
                    "repartidor_asignado": None,
                    "fecha": datetime.datetime.now(),
                    "lat": 21.88, "lon": -102.29 # Simulación de Aguascalientes
                }
                db["pedidos"].append(nuevo_p)
                st.session_state.carrito = []
                st.success("¡Pedido enviado con éxito! Puedes rastrearlo en 'Mis Pedidos'.")
            else:
                st.error("Por favor, ingresa una dirección de entrega.")

elif menu == "🎫 Mis Pedidos":
    st.title("🎫 Mis Tickets y Rastreo")
    mis_pedidos = [p for p in db["pedidos"] if p["email_cliente"] == st.session_state.usuario_actual]
    for p in reversed(mis_pedidos):
        with st.expander(f"Pedido #{p['id']} - {p['estado']} ({p['fecha'].strftime('%d/%m %H:%M')})"):
            st.write(f"**Dirección:** {p['direccion']}")
            st.write(f"**Total:** ${p['total']}")
            st.write("**Productos:** " + ", ".join([x['nombre'] for x in p['productos']]))
            
            if p["estado"] == "En camino":
                st.warning("🛵 El repartidor está cerca de tu ubicación.")
                m = folium.Map(location=[p['lat'], p['lon']], zoom_start=15)
                folium.Marker([p['lat'], p['lon']], popup="Tu repartidor", icon=folium.Icon(color='orange', icon='motorcycle', prefix='fa')).add_to(m)
                st_folium(m, height=250, key=f"mapa_cl_{p['id']}")
            
            if st.button("💬 Chat con Soporte/Repartidor", key=f"chat_cl_{p['id']}"):
                st.session_state.active_chat = p['id']

# --- 8. FUNCIONALIDAD: REPARTIDOR (SISTEMA DE ENTREGAS) ---
elif menu == "🛵 Mis Entregas":
    st.title("🛵 Panel de Reparto")
    mis_viajes = [p for p in db["pedidos"] if p["repartidor_asignado"] == st.session_state.usuario_actual and p["estado"] != "Entregado"]
    
    if not mis_viajes:
        st.info("No tienes pedidos asignados por ahora.")
    else:
        for v in mis_viajes:
            with st.container(border=True):
                col_i, col_d = st.columns([3, 1])
                with col_i:
                    st.subheader(f"Pedido #{v['id']} - {v['nombre_cliente']}")
                    st.write(f"📍 **Dirección:** {v['direccion']}")
                with col_d:
                    st.link_button("🗺️ Ver en Maps", f"https://www.google.com/maps/search/?api=1&query={v['direccion'].replace(' ', '+')}")
                    if st.button("✅ Finalizar", key=f"fin_{v['id']}"):
                        v["estado"] = "Entregado"
                        st.rerun()
                if st.button("💬 Chat", key=f"chat_rep_{v['id']}"):
                    st.session_state.active_chat = v['id']

# --- 9. FUNCIONALIDAD: TRABAJADOR Y ADMIN (GESTIÓN) ---
elif menu in ["📋 Pedidos Entrantes", "📊 Panel de Control"]:
    st.title("📋 Gestión Logística")
    for ped in db["pedidos"]:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                st.write(f"**#{ped['id']} - {ped['nombre_cliente']}**")
                st.write(f"💰 ${ped['total']} | 📍 {ped['direccion']}")
            with c2:
                if not ped["repartidor_asignado"]:
                    reps_disp = {u['nombre']: k for k, u in db["usuarios"].items() if u['rol'] == 'Repartidor' and u['activo']}
                    if reps_disp:
                        opciones_reps = []
                        for n, em in reps_disp.items():
                            cola = len([x for x in db["pedidos"] if x['repartidor_asignado'] == em and x['estado'] != 'Entregado'])
                            opciones_reps.append(f"{n} (Cola: {cola})")
                        
                        seleccion = st.selectbox("Asignar Repartidor", opciones_reps, key=f"sel_{ped['id']}")
                        if st.button("ENVIAR PEDIDO", key=f"btn_send_{ped['id']}"):
                            nombre_limpio = seleccion.split(" (")[0]
                            ped["repartidor_asignado"] = reps_disp[nombre_limpio]
                            ped["estado"] = "En camino"
                            st.rerun()
                    else: st.warning("No hay repartidores activos.")
                else:
                    st.write(f"Estado: **{ped['estado']}**")
                    st.write(f"Asignado a: {db['usuarios'][ped['repartidor_asignado']]['nombre']}")
            with c3:
                if st.button("💬 Chat", key=f"chat_admin_{ped['id']}"):
                    st.session_state.active_chat = ped['id']

elif menu == "🍱 Gestionar Menú":
    st.title("🍱 Administración del Menú")
    with st.expander("➕ Añadir Platillo Nuevo"):
        n_p = st.text_input("Nombre del plato")
        d_p = st.text_area("Descripción")
        p_p = st.number_input("Precio", min_value=0.0)
        f_p = st.file_uploader("Foto del platillo")
        if st.button("Subir al Menú Digital"):
            db["menu"].append({"id": len(db["menu"])+1, "nombre": n_p, "desc": d_p, "precio": p_p, "foto": procesar_imagen_binaria(f_p)})
            st.success("Platillo agregado.")
            st.rerun()
    
    st.divider()
    for i, platillo in enumerate(db["menu"]):
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                if platillo["foto"]: st.image(platillo["foto"], width=80)
            with col2:
                st.write(f"**{platillo['nombre']}** (${platillo['precio']})")
                st.caption(platillo["desc"])
            with col3:
                if st.button("🗑️", key=f"del_menu_{i}"):
                    db["menu"].pop(i)
                    st.rerun()

elif menu == "👥 Usuarios" and u_rol == "Administrador":
    st.title("👥 Control de Usuarios - Manuel Montes")
    tab_n, tab_g = st.tabs(["🆕 Registrar Staff", "📂 Gestionar Cuentas"])
    
    with tab_n:
        with st.form("registro_staff"):
            s_email = st.text_input("Email")
            s_nombre = st.text_input("Nombre")
            s_clave = st.text_input("Clave")
            s_rol = st.selectbox("Rol", ["Trabajador", "Repartidor"])
            if st.form_submit_button("Dar de Alta"):
                db["usuarios"][s_email] = {"clave": s_clave, "rol": s_rol, "nombre": s_nombre, "foto": None, "activo": True}
                st.success(f"{s_rol} registrado con éxito.")
    
    with tab_g:
        filtro_rol = st.selectbox("Filtrar por puesto:", ["Todos", "Cliente", "Repartidor", "Trabajador"])
        for em, inf in db["usuarios"].items():
            if filtro_rol == "Todos" or inf["rol"] == filtro_rol:
                col_u, col_r, col_b = st.columns([2, 1, 1])
                col_u.write(f"**{inf['nombre']}** ({em})")
                col_r.write(inf["rol"])
                txt_b = "BAJA" if inf["activo"] else "ALTA"
                if col_b.button(txt_b, key=f"status_{em}"):
                    inf["activo"] = not inf["activo"]
                    st.rerun()

# --- 10. VENTANA DE CHAT INTEGRADA (MULTICOLOR) ---
if 'active_chat' in st.session_state:
    id_chat = st.session_state.active_chat
    st.divider()
    st.subheader(f"💬 Chat del Pedido #{id_chat}")
    if id_chat not in db["chats"]: db["chats"][id_chat] = []
    
    with st.container(height=300):
        for msg in db["chats"][id_chat]:
            color = "#D1E8FF" if msg["rol"] == "Cliente" else "#D1FFD7" if msg["rol"] == "Repartidor" else "#FFE0D1"
            st.markdown(f"""<div style='background-color:{color}; padding:10px; border-radius:10px; margin-bottom:5px; color:black;'>
            <b>[{msg['rol']}] {msg['nombre']}:</b> {msg['texto']}</div>""", unsafe_allow_html=True)
    
    input_chat = st.chat_input("Escribe tu mensaje...")
    if input_chat:
        db["chats"][id_chat].append({"nombre": u_data["nombre"], "rol": u_rol, "texto": input_chat})
        st.rerun()
    if st.button("Cerrar Chat"):
        del st.session_state.active_chat
        st.rerun()
