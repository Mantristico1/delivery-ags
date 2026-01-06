import streamlit as st
from db import (
    init_db,
    create_user,
    create_order,
    get_users_by_role,
    get_orders
)

# Inicializar DB
init_db()

st.set_page_config(page_title="Delivery AGS", layout="centered")

st.title("🚴 Delivery AGS")

menu = st.sidebar.selectbox(
    "Selecciona tu rol",
    ["Cliente", "Cocina", "Repartidor"]
)

# ---------------- CLIENTE ----------------
if menu == "Cliente":
    st.subheader("📦 Nuevo Pedido")

    nombre = st.text_input("Tu nombre")
    pedido = st.text_area("¿Qué vas a pedir?")

    if st.button("Enviar pedido"):
        if nombre and pedido:
            create_user(nombre, "cliente")
            user_id = get_users_by_role("cliente")[-1][0]
            create_order(user_id, pedido)
            st.success("Pedido enviado correctamente 🚀")
        else:
            st.warning("Completa todos los campos")

# ---------------- COCINA ----------------
elif menu == "Cocina":
    st.subheader("👨‍🍳 Pedidos entrantes")

    pedidos = get_orders()

    if pedidos:
        for p in pedidos:
            st.markdown(f"""
            **Pedido #{p[0]}**  
            Cliente: {p[1]}  
            Pedido: {p[2]}  
            Estado: {p[3]}
            ---
            """)
    else:
        st.info("No hay pedidos aún")

# ---------------- REPARTIDOR ----------------
elif menu == "Repartidor":
    st.subheader("🛵 Pedidos para entregar")

    pedidos = get_orders()

    if pedidos:
        for p in pedidos:
            st.markdown(f"""
            **Pedido #{p[0]}**  
            Cliente: {p[1]}  
            Pedido: {p[2]}  
            Estado: {p[3]}
            ---
            """)
    else:
        st.info("No hay pedidos disponibles")

        del st.session_state.chat_id
        st.rerun()
