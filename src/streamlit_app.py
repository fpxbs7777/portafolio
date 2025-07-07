import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def obtener_variables_bcra():
    """
    Scrapea las principales variables del BCRA desde la web oficial.
    Devuelve un diccionario con los valores más recientes de reservas, dólar oficial, etc.
    Los nombres de variables se normalizan para facilitar el acceso.
    """
    url = "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp"
    variables = {}
    try:
        response = requests.get(url, verify=False, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            rows = soup.find_all('tr')
            for row in rows:
                columns = row.find_all('td')
                if len(columns) == 3:
                    variable = columns[0].get_text(strip=True)
                    fecha = columns[1].get_text(strip=True)
                    valor = columns[2].get_text(strip=True)
                    # Normalización de nombres para acceso sencillo
                    nombre = variable.lower()
                    if "reservas internacionales" in nombre:
                        key = "reservas_internacionales"
                    elif "tipo de cambio mayorista" in nombre:
                        key = "dolar_mayorista"
                    elif "tipo de cambio minorista" in nombre:
                        key = "dolar_minorista"
                    elif "tasa de política monetaria" in nombre and "n.a." in nombre:
                        key = "tasa_monetaria_na"
                    elif "tasa de política monetaria" in nombre and "e.a." in nombre:
                        key = "tasa_monetaria_ea"
                    elif "inflación mensual" in nombre:
                        key = "inflacion_mensual"
                    elif "inflación interanual" in nombre:
                        key = "inflacion_interanual"
                    elif "cer | base" in nombre:
                        key = "cer"
                    else:
                        key = variable  # fallback
                    variables[key] = {"fecha": fecha, "valor": valor, "nombre_original": variable}
        else:
            print(f"Error al acceder a la página del BCRA: {response.status_code}")
    except Exception as e:
        print(f"Error al scrapear BCRA: {str(e)}")
    return variables

def obtener_reservas_bcra():
    """
    Obtiene el valor de reservas internacionales del BCRA usando scraping.
    """
    variables = obtener_variables_bcra()
    # Buscar por clave normalizada
    reservas = variables.get("reservas_internacionales", None)
    if reservas:
        valor = reservas["valor"]
        fecha = reservas["fecha"]
        return {
            "titulo": f"Reservas BCRA ({fecha})",
            "valor": valor,
            "delta": None
        }
    else:
        return {
            "titulo": "Reservas BCRA",
            "valor": "No disponible",
            "delta": None
        }

def obtener_cotizacion_iol(token_acceso, simbolo, mercado='BCBA'):
    """
    Obtiene la cotización real de un instrumento usando la API de InvertirOnline.
    """
    try:
        headers = {
            'Authorization': f'Bearer {token_acceso}'
        }
        url = f'https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/CotizacionDetalle'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error al obtener cotización para {simbolo}: {str(e)}")
        return None

def obtener_cotizacion_detalle(token_acceso, simbolo, mercado='BCBA'):
    """
    Obtiene el detalle de la cotización real de un instrumento usando la API de InvertirOnline.
    Devuelve un diccionario con los datos principales del instrumento.
    """
    try:
        headers = {
            'Authorization': f'Bearer {token_acceso}'
        }
        url = f'https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/CotizacionDetalle'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        # Extraemos los campos principales del ejemplo de la documentación
        return {
            "simbolo": simbolo,
            "ultimoPrecio": data.get("ultimoPrecio"),
            "variacion": data.get("variacion"),
            "apertura": data.get("apertura"),
            "maximo": data.get("maximo"),
            "minimo": data.get("minimo"),
            "fechaHora": data.get("fechaHora"),
            "tendencia": data.get("tendencia"),
            "cierreAnterior": data.get("cierreAnterior"),
            "montoOperado": data.get("montoOperado"),
            "volumenNominal": data.get("volumenNominal"),
            "precioPromedio": data.get("precioPromedio")
        }
    except Exception as e:
        print(f"Error al obtener detalle de cotización para {simbolo}: {str(e)}")
        return None

def obtener_resumen_rueda():
    """
    Obtiene y resume datos reales del mercado usando la API de IOL y scraping del BCRA.
    Incluye reservas, dólar mayorista, inflación, tasas, etc.
    """
    if 'token_acceso' not in st.session_state or not st.session_state.token_acceso:
        st.warning("Se requiere autenticación para obtener datos en tiempo real")
        return {
            "reservas": {"titulo": "Autenticación requerida", "valor": "Inicie sesión", "delta": None},
            "dolar_mayorista": {"valor": 0, "variacion": 0},
            "volumen_operado": "No disponible",
            "dolares_financieros": {
                "MEP": {"valor": 0, "variacion": 0},
                "CCL": {"valor": 0, "variacion": 0},
                "Canje": {"valor": 0, "variacion": None}
            },
            "merval": {"valor": 0, "bajas": [], "subas": []},
            "deuda_soberana": {
                "AL30D": 0,
                "GD35D": 0,
                "GD38D": 0
            },
            "riesgo_pais": {"valor": 0, "delta": 0},
            "bonos_cer": {
                "corto_plazo": [],
                "largo_plazo": []
            },
            "letras": [],
            "dolar_linked": {
                "futuros": "No disponible",
                "bonos": []
            },
            "caucion": {"plazo": "No disponible", "tasa": 0}
        }
    
    token_acceso = st.session_state.token_acceso

    try:
        # Reservas BCRA reales
        reservas = obtener_reservas_bcra()

        # Datos reales de instrumentos principales
        gd30 = obtener_cotizacion_detalle(token_acceso, 'GD30', 'BCBA')
        al30 = obtener_cotizacion_detalle(token_acceso, 'AL30', 'BCBA')
        gd35 = obtener_cotizacion_detalle(token_acceso, 'GD35', 'BCBA')
        gd38 = obtener_cotizacion_detalle(token_acceso, 'GD38', 'BCBA')
        merval = obtener_cotizacion_detalle(token_acceso, 'MERVAL', 'BCBA')
        dolar_mayorista_iol = obtener_cotizacion_detalle(token_acceso, 'DOLAR', 'BCBA')

        # Datos BCRA adicionales
        variables_bcra = obtener_variables_bcra()
        dolar_mayorista_bcra = variables_bcra.get("dolar_mayorista", {}).get("valor", None)
        inflacion_mensual = variables_bcra.get("inflacion_mensual", {}).get("valor", None)
        inflacion_interanual = variables_bcra.get("inflacion_interanual", {}).get("valor", None)
        tasa_monetaria_na = variables_bcra.get("tasa_monetaria_na", {}).get("valor", None)
        cer = variables_bcra.get("cer", {}).get("valor", None)

        # MEP y CCL reales (usando precios de bonos)
        mep = {"valor": None, "variacion": None}
        ccl = {"valor": None, "variacion": None}
        if al30 and al30["ultimoPrecio"] and al30["apertura"]:
            mep['valor'] = al30["ultimoPrecio"] / 100
            variacion = ((mep['valor'] - (al30["apertura"] / 100)) / (al30["apertura"] / 100)) * 100
            mep['variacion'] = round(variacion, 2)
        if gd30 and gd30["ultimoPrecio"] and gd30["apertura"]:
            ccl['valor'] = gd30["ultimoPrecio"] / 100
            variacion = ((ccl['valor'] - (gd30["apertura"] / 100)) / (gd30["apertura"] / 100)) * 100
            ccl['variacion'] = round(variacion, 2)

        # Caución (scraping BCRA)
        tasa_caucion = tasa_monetaria_na if tasa_monetaria_na else "No disponible"
        plazo_caucion = "7 días"

        # Resumen de bajas y subas del MERVAL (no disponible por API pública)
        bajas = ["No disponible por API pública"]
        subas = ["No disponible por API pública"]

        return {
            "reservas": reservas,
            "dolar_mayorista": {
                # Prioriza el valor de la API de IOL, si no hay, usa el BCRA
                "valor": dolar_mayorista_iol["ultimoPrecio"] if dolar_mayorista_iol and dolar_mayorista_iol["ultimoPrecio"] else dolar_mayorista_bcra,
                "variacion": dolar_mayorista_iol["variacion"] if dolar_mayorista_iol else None
            },
            "volumen_operado": f"USD {merval['volumenNominal']/1e6:.1f}M" if merval and merval.get('volumenNominal') else "No disponible",
            "dolares_financieros": {
                "MEP": mep,
                "CCL": ccl,
                "Canje": {"valor": 0, "variacion": None}
            },
            "merval": {
                "valor": merval["variacion"] if merval else None,
                "bajas": bajas,
                "subas": subas
            },
            "deuda_soberana": {
                "AL30D": al30["variacion"] if al30 else None,
                "GD35D": gd35["variacion"] if gd35 else None,
                "GD38D": gd38["variacion"] if gd38 else None
            },
            "riesgo_pais": {
                "valor": variables_bcra.get("Riesgo País EMBI+ Argentina", {}).get("valor", "No disponible"),
                "delta": None
            },
            "bonos_cer": {
                "corto_plazo": [f"CER: {cer}" if cer else "No disponible por API pública"],
                "largo_plazo": ["No disponible por API pública"]
            },
            "letras": ["No disponible por API pública"],
            "dolar_linked": {
                "futuros": "No disponible por API pública",
                "bonos": ["No disponible por API pública"]
            },
            "caucion": {
                "plazo": plazo_caucion,
                "tasa": tasa_caucion
            },
            "inflacion": {
                "mensual": inflacion_mensual,
                "interanual": inflacion_interanual
            }
        }
    except Exception as e:
        st.error(f"Error al obtener datos de mercado: {str(e)}")
        # Retornar estructura vacía en caso de error
        return {
            "reservas": {"titulo": "Error", "valor": "Error al cargar", "delta": None},
            "dolar_mayorista": {"valor": 0, "variacion": 0},
            "volumen_operado": "Error",
            "dolares_financieros": {
                "MEP": {"valor": 0, "variacion": 0},
                "CCL": {"valor": 0, "variacion": 0},
                "Canje": {"valor": 0, "variacion": None}
            },
            "merval": {"valor": 0, "bajas": ["Error"], "subas": ["Error"]},
            "deuda_soberana": {"AL30D": 0, "GD35D": 0, "GD38D": 0},
            "riesgo_pais": {"valor": 0, "delta": 0},
            "bonos_cer": {"corto_plazo": ["Error"], "largo_plazo": ["Error"]},
            "letras": ["Error"],
            "dolar_linked": {"futuros": "Error", "bonos": ["Error"]},
            "caucion": {"plazo": "Error", "tasa": 0}
        }

def mostrar_resumen_rueda():
    """Muestra el resumen de la rueda del día con validación de datos reales."""
    st.markdown("## 🔔 Resumen de la Rueda del Día")
    st.caption(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    resumen = obtener_resumen_rueda()
    
    # Utilidad para mostrar "No disponible" si el valor es 0, None o vacío
    def mostrar_valor(valor, formato="${:,.2f}", nd="No disponible"):
        if valor is None or (isinstance(valor, (int, float)) and valor == 0):
            return nd
        if isinstance(valor, (int, float)):
            return formato.format(valor)
        return valor

    # Sección 1: Reservas y Dólar
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label=resumen["reservas"]["titulo"],
            value=mostrar_valor(resumen["reservas"]["valor"], formato="{}", nd="No disponible"),
            delta=resumen["reservas"]["delta"]
        )
    with col2:
        st.metric(
            label="Dólar Mayorista (A3500)",
            value=mostrar_valor(resumen['dolar_mayorista']['valor']),
            delta=f"{resumen['dolar_mayorista']['variacion']}%" if resumen['dolar_mayorista']['variacion'] not in [None, 0] else None
        )
    with col3:
        st.metric(
            label="Volumen Operado A3",
            value=mostrar_valor(resumen["volumen_operado"], formato="{}", nd="No disponible"),
            delta=None
        )
    st.divider()
    
    # Sección 2: Dólares Financieros
    st.subheader("💸 Dólares Financieros")
    cols = st.columns(3)
    with cols[0]:
        st.metric("MEP", mostrar_valor(resumen['dolares_financieros']['MEP']['valor']), 
                 f"{resumen['dolares_financieros']['MEP']['variacion']}%" if resumen['dolares_financieros']['MEP']['variacion'] not in [None, 0] else None)
    with cols[1]:
        st.metric("CCL", mostrar_valor(resumen['dolares_financieros']['CCL']['valor']), 
                 f"{resumen['dolares_financieros']['CCL']['variacion']}%" if resumen['dolares_financieros']['CCL']['variacion'] not in [None, 0] else None)
    with cols[2]:
        st.metric("Canje", mostrar_valor(resumen['dolares_financieros']['Canje']['valor'], formato="{}%", nd="No disponible"), None)
    st.caption("🔹 Suba tras el fallo de la jueza Preska")
    st.divider()
    
    # Sección 3: Merval
    st.subheader(f"📉 S&P Merval: {mostrar_valor(resumen['merval']['valor'], formato='{}%', nd='No disponible')}")
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
        st.metric("AL30D", mostrar_valor(resumen['deuda_soberana']['AL30D'], formato="{}%", nd="No disponible"))
    with cols[1]:
        st.metric("GD35D", mostrar_valor(resumen['deuda_soberana']['GD35D'], formato="{}%", nd="No disponible"))
    with cols[2]:
        st.metric("GD38D", mostrar_valor(resumen['deuda_soberana']['GD38D'], formato="{}%", nd="No disponible"))
    with cols[3]:
        st.metric("Riesgo País", mostrar_valor(resumen['riesgo_pais']['valor'], formato="{}", nd="No disponible"), 
                 f"{resumen['riesgo_pais']['delta']} puntos" if resumen['riesgo_pais']['delta'] else None)
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
        st.markdown(f"▫️ Futuros suben entre {mostrar_valor(resumen['dolar_linked']['futuros'], formato='{}', nd='No disponible')}")
        st.markdown("▫️ Bonos:")
        for bono in resumen["dolar_linked"]["bonos"]:
            st.markdown(f"  - {bono}")
    st.divider()
    
    # Sección 7: Caución
    st.subheader(f"📌 Caución a {mostrar_valor(resumen['caucion']['plazo'], formato='{}', nd='No disponible')}: {mostrar_valor(resumen['caucion']['tasa'], formato='{}%', nd='No disponible')}")
    
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

def obtener_tokens(usuario, contraseña):
    """
    Realiza la autenticación contra la API de IOL y devuelve el token de acceso y refresh token.
    """
    try:
        url = "https://api.invertironline.com/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "username": usuario,
            "password": contraseña,
            "grant_type": "password"
        }
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        tokens = response.json()
        return tokens.get("access_token"), tokens.get("refresh_token")
    except Exception as e:
        print(f"Error al obtener tokens: {str(e)}")
        return None, None

def obtener_lista_clientes(token_acceso):
    """
    Obtiene la lista de clientes asociados al usuario autenticado en IOL.
    """
    try:
        headers = {
            'Authorization': f'Bearer {token_acceso}'
        }
        url = "https://api.invertironline.com/api/v2/estadocuenta"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        # Si la API devuelve una lista de cuentas, adaptamos el formato
        if isinstance(data, list):
            return data
        # Si devuelve un solo cliente, lo envolvemos en una lista
        elif isinstance(data, dict):
            return [data]
        else:
            return []
    except Exception as e:
        print(f"Error al obtener lista de clientes: {str(e)}")
        return []

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
