import streamlit as st
import folium
from streamlit_folium import st_folium
import datetime
import pandas as pd
from PIL import Image
import io
import base64

# --- 1. CONFIGURACIÓN DE TEMA Y ESTILO ---
st.set_page_config(page_title="AGS Delivery - Sistema Maestro", layout="wide")

# Función para convertir imágenes a Base64
def procesar_foto(subida):
    if subida:
        img = Image.open(subida)
        img.thumbnail((400, 400))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
    return None

# --- 2. BASE DE DATOS (VINCULADA Y SIN RECORTES) ---
@st.cache_resource
def inicializar_sistema():
    return {
        "usuarios": {
            "admin@delivery.com": {"clave": "1234", "rol": "Administrador", "nombre": "Manuel Montes", "foto": None, "activo": True},
        },
        "menu": [
            {"id": 1, "nombre": "Hamburguesa AGS", "desc": "Premium con papas", "precio": 120.0, "foto": None, "categoria": "Comida"}
        ],
        "pedidos": [],
        "chats": {} # {id_pedido: [{"autor": "", "rol": "", "txt": ""}]}
    }

db = inicializar_sistema()

# --- 3. GESTIÓN DE SESIÓN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.email = ""
    st.session_state.carrito = []

# --- 4. ACCESO (LOGIN) ---
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.title("🚚 AGS Delivery")
        # Registro oculto en expander para no ensuciar el inicio
        with st.expander("📝 Registro de Clientes"):
            re = st.text_input("Correo nuevo")
            rn = st.text_input("Nombre completo")
            rp = st.text_input("Crea tu contraseña", type="password")
            if st.button("Registrarme"):
                db["usuarios"][re] = {"clave": rp, "rol": "Cliente", "nombre": rn, "foto": None, "activo": True}
                st.success("¡Registrado! Ahora inicia sesión.")
        
        st.divider()
        e = st.text_input("Email")
        p = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR", use_container_width=True):
            user = db["usuarios"].get(e)
            if user and user["clave"] == p and user["activo"]:
                st.session_state.auth = True
                st.session_state.email = e
                st.rerun()
            else: st.error("Acceso denegado.")
    st.stop()

u_info = db["usuarios"][st.session_state.email]
u_rol = u_info["rol"]

# --- 5. BARRA LATERAL (NAVEGACIÓN) ---
with st.sidebar:
    st.image(u_info["foto"] if u_info["foto"] else "https://cdn-icons-png.flaticon.com/512/149/149071.png", width=100)
    st.title(u_info["nombre"])
    st.write(f"Rol: **{u_rol}**")
    
    # Navegación estricta por roles
    opciones = ["🏠 Inicio"]
    if u_rol == "Administrador": opciones += ["👥 Usuarios", "🍴 Gestión Menú"]
    if u_rol == "Trabajador": opciones += ["🍴 Gestión Menú", "💬 Chats de Pedidos"]
    if u_rol == "Repartidor": opciones += ["🛵 Mis Entregas"]
    if u_rol == "Cliente": opciones += ["🛒 Hacer Pedido", "🎫 Mis Tickets"]
    opciones += ["⚙️ Configuración"]
    
    sel = st.radio("Ir a:", opciones)
    
    st.divider()
    if st.button("🌓 Modo Claro/Oscuro"):
        pass # Streamlit maneja esto nativamente con la configuración del usuario
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

# --- 6. CONFIGURACIÓN (BOTÓN APARTE) ---
if sel == "⚙️ Configuración":
    st.header("⚙️ Ajustes de Perfil")
    u_info["nombre"] = st.text_input("Cambiar Nombre", value=u_info["nombre"])
    u_info["clave"] = st.text_input("Cambiar Clave", value=u_info["clave"], type="password")
    archivo = st.file_uploader("Actualizar foto de galería", type=['jpg','png'])
    if archivo:
        u_info["foto"] = procesar_foto(archivo)
    if st.button("Guardar Cambios"): st.success("Perfil actualizado")

# --- 7. PANEL DE USUARIOS (SOLO ADMINISTRADOR) ---
elif sel == "👥 Usuarios":
    st.header("👥 Gestión de Usuarios")
    sub = st.radio("Acción:", ["Registrar Personal (Staff)", "Gestión de Cuentas"], horizontal=True)
    
    if sub == "Registrar Personal (Staff)":
        with st.form("new_staff"):
            ne = st.text_input("Email")
            nn = st.text_input("Nombre")
            np = st.text_input("Clave")
            nr = st.selectbox("Puesto", ["Trabajador", "Repartidor"])
            if st.form_submit_button("Dar de Alta"):
                db["usuarios"][ne] = {"clave": np, "rol": nr, "nombre": nn, "foto": None, "activo": True, "disponible": True}
                st.success(f"{nr} registrado.")
    
    else:
        filtro = st.selectbox("Ver solo:", ["Trabajadores", "Repartidores", "Clientes"])
        for em, inf in db["usuarios"].items():
            if (filtro == "Clientes" and inf["rol"] == "Cliente") or \
               (filtro == "Repartidores" and inf["rol"] == "Repartidor") or \
               (filtro == "Trabajadores" and inf["rol"] == "Trabajador"):
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{inf['nombre']}** ({em})")
                estado = "ACTIVO" if inf["activo"] else "BAJA"
                if c3.button("Alta/Baja", key=em):
                    inf["activo"] = not inf["activo"]
                    st.rerun()

# --- 8. GESTIÓN DEL MENÚ (TRABAJADOR Y ADMIN) ---
elif sel == "🍴 Gestión Menú":
    st.header("🍴 Administración de Platillos")
    with st.expander("➕ Agregar / Editar Comida"):
        nom_p = st.text_input("Nombre del plato")
        pre_p = st.number_input("Precio", min_value=0.0)
        des_p = st.text_area("Descripción")
        cat_p = st.selectbox("Categoría", ["Comida", "Bebida", "Postre"])
        fot_p = st.file_uploader("Foto del plato")
        if st.button("Publicar Platillo"):
            db["menu"].append({"id": len(db["menu"])+1, "nombre": nom_p, "precio": pre_p, "desc": des_p, "foto": procesar_foto(fot_p), "categoria": cat_p})
            st.rerun()
    
    st.divider()
    for i, item in enumerate(db["menu"]):
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if item["foto"]: st.image(item["foto"], width=100)
            with col2:
                st.write(f"**{item['nombre']}** - ${item['precio']}")
                st.caption(item["desc"])
            with col3:
                if st.button("🗑️ Eliminar", key=f"del_{i}"):
                    db["menu"].pop(i)
                    st.rerun()

# --- 9. CLIENTE (UBER EATS STYLE) ---
elif sel == "🛒 Hacer Pedido":
    st.title("🍴 Menú Digital")
    # Carrito icono
    if st.session_state.carrito:
        st.sidebar.warning(f"🛒 Carrito: {len(st.session_state.carrito)} items")
        if st.sidebar.button("Ver mi Pedido"):
            sel = "🛒 Mi Carrito"
    
    cols = st.columns(2)
    for i, item in enumerate(db["menu"]):
        with cols[i % 2]:
            with st.container(border=True):
                if item["foto"]: st.image(item["foto"], use_column_width=True)
                st.subheader(item["nombre"])
                st.write(item["desc"])
                st.write(f"**${item['precio']}**")
                if st.button(f"Agregar al carrito", key=f"add_{item['id']}"):
                    st.session_state.carrito.append(item)
                    st.toast("Agregado")

    # Finalizar pedido
    if st.session_state.carrito:
        st.divider()
        st.header("🛍️ Confirmar mi Pedido")
        total = sum(i['precio'] for i in st.session_state.carrito)
        st.table(pd.DataFrame(st.session_state.carrito)[['nombre', 'precio']])
        dir_p = st.text_input("Dirección de entrega (📍 Google Maps Link o texto)")
        if st.button(f"Confirmar y Pagar ${total} (Efectivo)"):
            np = {
                "id": len(db["pedidos"])+1, "cl_e": st.session_state.email, "cl_n": u_info["nombre"],
                "items": st.session_state.carrito.copy(), "total": total, "dir": dir_p,
                "estado": "Preparando", "rep": None, "fecha": datetime.datetime.now()
            }
            db["pedidos"].append(np)
            st.session_state.carrito = []
            st.success("¡Pedido enviado a cocina!")

# --- 10. SEGUIMIENTO Y TICKET (CLIENTE) ---
elif sel == "🎫 Mis Tickets":
    st.header("📜 Historial de Pedidos")
    mis = [p for p in db["pedidos"] if p["cl_e"] == st.session_state.email]
    for p in reversed(mis):
        with st.expander(f"Pedido #{p['id']} - {p['estado']}"):
            st.write(f"**Fecha:** {p['fecha']}")
            st.write(f"**Dirección:** {p['dir']}")
            st.write("---")
            for it in p["items"]: st.write(f"- {it['nombre']} (${it['precio']})")
            st.write(f"**TOTAL:** ${p['total']}")
            
            if p["estado"] == "En camino":
                st.warning("🛵 El repartidor está en movimiento.")
                m = folium.Map(location=[21.88, -102.29], zoom_start=14)
                folium.Marker([21.88, -102.29], popup="Repartidor", icon=folium.Icon(color='orange', icon='motorcycle', prefix='fa')).add_to(m)
                st_folium(m, height=200, key=f"map_{p['id']}")
            
            if st.button("💬 Chat con Staff", key=f"chat_cli_{p['id']}"):
                st.session_state.chat_id = p['id']

# --- 11. PANEL DE STAFF (TRABAJADOR / ADMIN) ---
elif sel == "🏠 Inicio" and u_rol in ["Administrador", "Trabajador"]:
    st.header("📋 Panel de Control de Pedidos")
    for p in db["pedidos"]:
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**Pedido #{p['id']}** - {p['cl_n']}")
                st.write(f"📍 {p['dir']}")
            with col2:
                if not p["rep"]:
                    # LÓGICA DE PEDIDOS EN COLA
                    reps_dispo = {u['nombre']: k for k, u in db["usuarios"].items() if u['rol'] == 'Repartidor' and u.get('disponible', True)}
                    if reps_dispo:
                        opciones_rep = []
                        for nom, em in reps_dispo.items():
                            en_cola = len([x for x in db["pedidos"] if x['rep'] == em and x['estado'] != 'Entregado'])
                            opciones_rep.append(f"{nom} (Cola: {en_cola})")
                        
                        sr = st.selectbox("Asignar Repartidor", opciones_rep, key=f"sel_{p['id']}")
                        if st.button("Asignar y Enviar", key=f"btn_{p['id']}"):
                            nombre_limpio = sr.split(" (")[0]
                            p["rep"] = reps_dispo[nombre_limpio]
                            p["estado"] = "En camino"
                            st.rerun()
                else:
                    st.write(f"🛵 Repartidor: {db['usuarios'][p['rep']]['nombre']}")
                    st.write(f"Estado: **{p['estado']}**")
            with col3:
                if st.button("💬 Chat", key=f"chat_s_{p['id']}"):
                    st.session_state.chat_id = p['id']

# --- 12. CHAT MULTICOLOR ---
if 'chat_id' in st.session_state:
    id_p = st.session_state.chat_id
    st.divider()
    st.subheader(f"💬 Chat Pedido #{id_p}")
    if id_p not in db["chats"]: db["chats"][id_p] = []
    
    # Mostrar mensajes
    for m in db["chats"][id_p]:
        color = "#e1f5fe" if m["rol"] == "Cliente" else "#f3e5f5" if m["rol"] == "Repartidor" else "#fff3e0"
        st.markdown(f"<div style='background-color:{color}; padding:10px; border-radius:10px; margin:5px; color:black;'><b>{m['rol']} - {m['autor']}:</b> {m['txt']}</div>", unsafe_allow_html=True)
    
    txt = st.chat_input("Escribe aquí...")
    if txt:
        db["chats"][id_p].append({"autor": u_info["nombre"], "rol": u_rol, "txt": txt})
        st.rerun()
    if st.button("Cerrar Chat"):
        del st.session_state.chat_id
        st.rerun()
