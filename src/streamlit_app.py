import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, date, timedelta

def obtener_resumen_rueda():
    """Simula la obtención de datos de resumen del mercado (ejemplo)"""
    # En una implementación real, esto se conectaría a una API de datos de mercado
    return {
        "reservas": {"titulo": "BCRA: Termina junio con caída mensual", "valor": "USD 39.951M", "delta": "-1.502M"},
        "dolar_mayorista": {"valor": 1194.08, "variacion": 0.36},
        "volumen_operado": "USD 611M",
        "dolares_financieros": {
            "MEP": {"valor": 1208.30, "variacion": 1.10},
            "CCL": {"valor": 1211.83, "variacion": 1.07},
            "Canje": {"valor": 0.30, "variacion": None}
        },
        "merval": {"valor": -2.27, "bajas": ["METR -5.34%", "YPFD -4.98%", "COME -4.82%"],
                  "subas": ["ALUA +1.69%", "TECO2 +0.94%", "CRES +0.38%"]},
        "deuda_soberana": {
            "AL30D": -0.94,
            "GD35D": -0.78,
            "GD38D": -0.99
        },
        "riesgo_pais": {"valor": 714, "delta": +29},
        "bonos_cer": {
            "corto_plazo": ["TX25 +1.37%", "TZX26 +0.19%", "TZXM6 +0.46%"],
            "largo_plazo": ["TZX27 -0.25%", "TX28 -1.27%", "TZX28 -0.36%"]
        },
        "letras": ["S31L5 +0.06%", "S12S5 +0.30%", "S10N5 +0.12%"],
        "dolar_linked": {
            "futuros": "0.34% a 1.55%",
            "bonos": ["TZVD5 +2.50%", "TZV26 +1.75%"]
        },
        "caucion": {"plazo": "7 días", "tasa": 28.80}
    }

def mostrar_resumen_rueda():
    """Muestra el resumen de la rueda del día"""
    st.markdown("## 🔔 Resumen de la Rueda del Día")
    st.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Obtener datos del resumen
    resumen = obtener_resumen_rueda()
    
    # Sección 1: Reservas y Dólar
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label=resumen["reservas"]["titulo"],
            value=resumen["reservas"]["valor"],
            delta=resumen["reservas"]["delta"]
        )
    
    with col2:
        st.metric(
            label="Dólar Mayorista (A3500)",
            value=f"${resumen['dolar_mayorista']['valor']:,.2f}",
            delta=f"{resumen['dolar_mayorista']['variacion']}%"
        )
    
    with col3:
        st.metric(
            label="Volumen Operado A3",
            value=resumen["volumen_operado"],
            delta=None
        )
    
    st.divider()
    
    # Sección 2: Dólares Financieros
    st.subheader("💸 Dólares Financieros")
    cols = st.columns(3)
    with cols[0]:
        st.metric("MEP", f"${resumen['dolares_financieros']['MEP']['valor']:,.2f}", 
                 f"{resumen['dolares_financieros']['MEP']['variacion']}%")
    
    with cols[1]:
        st.metric("CCL", f"${resumen['dolares_financieros']['CCL']['valor']:,.2f}", 
                 f"{resumen['dolares_financieros']['CCL']['variacion']}%")
    
    with cols[2]:
        st.metric("Canje", f"{resumen['dolares_financieros']['Canje']['valor']}%", 
                 None)
    
    st.caption("🔹 Suba tras el fallo de la jueza Preska")
    st.divider()
    
    # Sección 3: Merval
    st.subheader(f"📉 S&P Merval: {resumen['merval']['valor']}%")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Principales bajas:**")
        for baja in resumen["merval"]["bajas"]:
            st.markdown(f"- {baja}")
    
    with col2:
        st.markdown("**Principales subas:**")
        for suba in resumen["merval"]["subas"]:
            st.markdown(f"- {suba}")
    
    st.divider()
    
    # Sección 4: Deuda Soberana
    st.subheader("💵 Deuda Soberana en USD (Hard Dollar)")
    cols = st.columns(4)
    with cols[0]:
        st.metric("AL30D", f"{resumen['deuda_soberana']['AL30D']}%")
    with cols[1]:
        st.metric("GD35D", f"{resumen['deuda_soberana']['GD35D']}%")
    with cols[2]:
        st.metric("GD38D", f"{resumen['deuda_soberana']['GD38D']}%")
    with cols[3]:
        st.metric("Riesgo País", resumen['riesgo_pais']['valor'], 
                 f"{resumen['riesgo_pais']['delta']} puntos")
    
    st.divider()
    
    # Sección 5: Bonos CER
    st.subheader("📊 Bonos CER")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Corto plazo en alza:**")
        for bono in resumen["bonos_cer"]["corto_plazo"]:
            st.markdown(f"- {bono}")
    
    with col2:
        st.markdown("**Largo plazo en baja:**")
        for bono in resumen["bonos_cer"]["largo_plazo"]:
            st.markdown(f"- {bono}")
    
    st.divider()
    
    # Sección 6: Letras y Dólar Linked
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📄 Letras")
        for letra in resumen["letras"]:
            st.markdown(f"- {letra}")
    
    with col2:
        st.subheader("🔄 Dólar Linked")
        st.markdown(f"▫️ Futuros suben entre {resumen['dolar_linked']['futuros']}")
        st.markdown("▫️ Bonos:")
        for bono in resumen["dolar_linked"]["bonos"]:
            st.markdown(f"  - {bono}")
    
    st.divider()
    
    # Sección 7: Caución
    st.subheader(f"📌 Caución a {resumen['caucion']['plazo']}: {resumen['caucion']['tasa']}%")
    
    # Gráfico de tasas de caución (simulado)
    plazos = [1, 7, 14, 30, 60]
    tasas = [25.5, 28.8, 27.2, 26.5, 25.8]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=plazos, 
        y=tasas,
        mode='lines+markers',
        name='Tasas',
        line=dict(color='#4CAF50', width=3),
        marker=dict(size=10, color='#2E7D32')
    ))
    
    fig.update_layout(
        title='Curva de Tasas de Caución',
        xaxis_title='Plazo (días)',
        yaxis_title='Tasa (%)',
        template='plotly_dark',
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ... (código existente previo a la función main)

def main():
    st.title("📊 IOL Portfolio Analyzer")
    st.markdown("### Analizador Avanzado de Portafolios IOL")
    
    # Inicializar session state
    if 'token_acceso' not in st.session_state:
        st.session_state.token_acceso = None
    if 'refresh_token' not in st.session_state:
        st.session_state.refresh_token = None
    if 'clientes' not in st.session_state:
        st.session_state.clientes = []
    if 'cliente_seleccionado' not in st.session_state:
        st.session_state.cliente_seleccionado = None
    if 'fecha_desde' not in st.session_state:
        st.session_state.fecha_desde = date.today() - timedelta(days=365)
    if 'fecha_hasta' not in st.session_state:
        st.session_state.fecha_hasta = date.today()
    
    # Barra lateral - Autenticación
    with st.sidebar:
        st.header("🔐 Autenticación IOL")
        
        if st.session_state.token_acceso is None:
            with st.form("login_form"):
                st.subheader("Ingreso a IOL")
                usuario = st.text_input("Usuario", placeholder="su_usuario")
                contraseña = st.text_input("Contraseña", type="password", placeholder="su_contraseña")
                
                if st.form_submit_button("🚀 Conectar a IOL", use_container_width=True):
                    if usuario and contraseña:
                        with st.spinner("Conectando..."):
                            token_acceso, refresh_token = obtener_tokens(usuario, contraseña)
                            
                            if token_acceso:
                                st.session_state.token_acceso = token_acceso
                                st.session_state.refresh_token = refresh_token
                                st.success("✅ Conexión exitosa!")
                                st.rerun()
                            else:
                                st.error("❌ Error en la autenticación")
                    else:
                        st.warning("⚠️ Complete todos los campos")
        else:
            st.success("✅ Conectado a IOL")
            st.divider()
            
            st.subheader("Configuración de Fechas")
            col1, col2 = st.columns(2)
            with col1:
                fecha_desde = st.date_input(
                    "Desde:",
                    value=st.session_state.fecha_desde,
                    max_value=date.today()
                )
            with col2:
                fecha_hasta = st.date_input(
                    "Hasta:",
                    value=st.session_state.fecha_hasta,
                    max_value=date.today()
                )
            
            st.session_state.fecha_desde = fecha_desde
            st.session_state.fecha_hasta = fecha_hasta
            
            # Obtener lista de clientes
            if not st.session_state.clientes and st.session_state.token_acceso:
                with st.spinner("Cargando clientes..."):
                    try:
                        clientes = obtener_lista_clientes(st.session_state.token_acceso)
                        if clientes:
                            st.session_state.clientes = clientes
                        else:
                            st.warning("No se encontraron clientes")
                    except Exception as e:
                        st.error(f"Error al cargar clientes: {str(e)}")
            
            clientes = st.session_state.clientes
            
            if clientes:
                st.subheader("Selección de Cliente")
                cliente_ids = [c.get('numeroCliente', c.get('id')) for c in clientes]
                cliente_nombres = [c.get('apellidoYNombre', c.get('nombre', 'Cliente')) for c in clientes]
                
                cliente_seleccionado = st.selectbox(
                    "Seleccione un cliente:",
                    options=cliente_ids,
                    format_func=lambda x: cliente_nombres[cliente_ids.index(x)] if x in cliente_ids else "Cliente",
                    label_visibility="collapsed",
                    key="sidebar_cliente_selector"
                )
                
                st.session_state.cliente_seleccionado = next(
                    (c for c in clientes if c.get('numeroCliente', c.get('id')) == cliente_seleccionado),
                    None
                )
                
                if st.button("🔄 Actualizar lista de clientes", use_container_width=True):
                    with st.spinner("Actualizando..."):
                        nuevos_clientes = obtener_lista_clientes(st.session_state.token_acceso)
                        st.session_state.clientes = nuevos_clientes
                        st.success("✅ Lista actualizada")
                        st.rerun()
            else:
                st.warning("No se encontraron clientes")

    # Contenido principal
    try:
        if st.session_state.token_acceso:
            st.sidebar.title("Menú Principal")
            opcion = st.sidebar.radio(
                "Seleccione una opción:",
                ("🏠 Inicio", "📊 Análisis de Portafolio", "💰 Tasas de Caución", 
                 "👨‍💼 Panel del Asesor", "🔔 Resumen de la Rueda"),
                index=0,
                key="main_navigation_radio"
            )

            # Mostrar la página seleccionada
            if opcion == "🏠 Inicio":
                st.info("👆 Seleccione una opción del menú para comenzar")
                
                # Panel de bienvenida
                st.markdown("""
                <div style="background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); 
                            border-radius: 15px; 
                            padding: 40px; 
                            color: white;
                            text-align: center;
                            margin: 30px 0;">
                    <h1 style="color: white; margin-bottom: 20px;">Bienvenido al Portfolio Analyzer</h1>
                    <p style="font-size: 18px; margin-bottom: 30px;">Conecte su cuenta de IOL para comenzar a analizar sus portafolios</p>
                    <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
                        <div style="background: rgba(255,255,255,0.2); border-radius: 12px; padding: 25px; width: 250px; backdrop-filter: blur(5px);">
                            <h3>📊 Análisis Completo</h3>
                            <p>Visualice todos sus activos en un solo lugar con detalle</p>
                        </div>
                        <div style="background: rgba(255,255,255,0.2); border-radius: 12px; padding: 25px; width: 250px; backdrop-filter: blur(5px);">
                            <h3>📈 Gráficos Interactivos</h3>
                            <p>Comprenda su portafolio con visualizaciones avanzadas</p>
                        </div>
                        <div style="background: rgba(255,255,255,0.2); border-radius: 12px; padding: 25px; width: 250px; backdrop-filter: blur(5px);">
                            <h3>⚖️ Gestión de Riesgo</h3>
                            <p>Identifique concentraciones y optimice su perfil de riesgo</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Características
                st.subheader("✨ Características Principales")
                cols = st.columns(3)
                with cols[0]:
                    st.markdown("""
                    **📊 Análisis Detallado**  
                    - Valuación completa de activos  
                    - Distribución por tipo de instrumento  
                    - Concentración del portafolio  
                    """)
                with cols[1]:
                    st.markdown("""
                    **📈 Herramientas Profesionales**  
                    - Optimización de portafolio  
                    - Análisis técnico avanzado  
                    - Proyecciones de rendimiento  
                    """)
                with cols[2]:
                    st.markdown("""
                    **💱 Datos de Mercado**  
                    - Cotizaciones MEP en tiempo real  
                    - Tasas de caución actualizadas  
                    - Estado de cuenta consolidado  
                    """)
            
            elif opcion == "📊 Análisis de Portafolio":
                if st.session_state.cliente_seleccionado:
                    mostrar_analisis_portafolio()
                else:
                    st.info("👆 Seleccione un cliente en la barra lateral para comenzar")
            
            elif opcion == "💰 Tasas de Caución":
                if 'token_acceso' in st.session_state and st.session_state.token_acceso:
                    mostrar_tasas_caucion(st.session_state.token_acceso)
                else:
                    st.warning("Por favor inicie sesión para ver las tasas de caución")
            
            elif opcion == "👨‍💼 Panel del Asesor":
                mostrar_movimientos_asesor()
            
            elif opcion == "🔔 Resumen de la Rueda":
                mostrar_resumen_rueda()
        else:
            st.info("👆 Ingrese sus credenciales para comenzar")
            
    except Exception as e:
        st.error(f"❌ Error en la aplicación: {str(e)}")

if __name__ == "__main__":
    main()
