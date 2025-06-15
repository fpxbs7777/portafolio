import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
from datetime import date, timedelta, datetime
import numpy as np
import yfinance as yf
import scipy.optimize as op
from scipy import stats
import random
import warnings
import streamlit.components.v1 as components

warnings.filterwarnings('ignore')

# Configuración de la página con aspecto profesional
st.set_page_config(
    page_title="IOL Portfolio Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    /* Estilos generales */
    .stApp {
        background-color: #f8f9fa;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Mejora de tarjetas y métricas */
    .stMetric {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 4px solid #0d6efd;
    }
    
    /* Mejora de pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        padding: 0 20px;
        background-color: #e9ecef;
        border-radius: 8px !important;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #0d6efd !important;
        color: white !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #dde5ed !important;
    }
    
    /* Mejora de inputs */
    .stTextInput, .stNumberInput, .stDateInput, .stSelectbox {
        background-color: white;
        border-radius: 8px;
    }
    
    /* Botones */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Barra lateral */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c3e50, #1a1a2e);
        color: white;
    }
    
    [data-testid="stSidebar"] .stRadio label {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox label {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stTextInput label {
        color: white !important;
    }
    
    /* Títulos */
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50;
        font-weight: 600;
    }
    
    /* Tablas */
    .dataframe {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #0d6efd;
    }
</style>
""", unsafe_allow_html=True)

def obtener_encabezado_autorizacion(token_portador):
    return {
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'application/json'
    }

def obtener_tokens(usuario, contraseña):
    url_login = 'https://api.invertironline.com/token'
    datos = {
        'username': usuario,
        'password': contraseña,
        'grant_type': 'password'
    }
    try:
        respuesta = requests.post(url_login, data=datos, timeout=15)
        respuesta.raise_for_status()
        respuesta_json = respuesta.json()
        return respuesta_json['access_token'], respuesta_json['refresh_token']
    except requests.exceptions.HTTPError as http_err:
        st.error(f'Error HTTP al obtener tokens: {http_err}')
        if respuesta.status_code == 400:
            st.warning("Verifique sus credenciales (usuario/contraseña). El servidor indicó 'Bad Request'.")
        elif respuesta.status_code == 401:
            st.warning("No autorizado. Verifique sus credenciales o permisos.")
        else:
            st.warning(f"El servidor de IOL devolvió un error. Código de estado: {respuesta.status_code}.")
        return None, None
    except Exception as e:
        st.error(f'Error inesperado al obtener tokens: {str(e)}')
        return None, None

def obtener_lista_clientes(token_portador):
    url_clientes = 'https://api.invertironline.com/api/v2/Asesores/Clientes'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    try:
        respuesta = requests.get(url_clientes, headers=encabezados)
        if respuesta.status_code == 200:
            clientes_data = respuesta.json()
            if isinstance(clientes_data, list):
                return clientes_data
            elif isinstance(clientes_data, dict) and 'clientes' in clientes_data:
                return clientes_data['clientes']
            else:
                return []
        else:
            st.error(f'Error al obtener la lista de clientes: {respuesta.status_code}')
            return []
    except Exception as e:
        st.error(f'Error de conexión al obtener clientes: {str(e)}')
        return []

def obtener_estado_cuenta(token_portador, id_cliente=None):
    if id_cliente:
        url_estado_cuenta = f'https://api.invertironline.com/api/v2/Asesores/EstadoDeCuenta/{id_cliente}'
    else:
        url_estado_cuenta = 'https://api.invertironline.com/api/v2/estadocuenta'
    
    encabezados = obtener_encabezado_autorizacion(token_portador)
    try:
        respuesta = requests.get(url_estado_cuenta, headers=encabezados)
        if respuesta.status_code == 200:
            return respuesta.json()
        elif respuesta.status_code == 401:
            return obtener_estado_cuenta(token_portador, None)
        else:
            return None
    except Exception as e:
        st.error(f'Error al obtener estado de cuenta: {str(e)}')
        return None

def obtener_portafolio(token_portador, id_cliente, pais='Argentina'):
    url_portafolio = f'https://api.invertironline.com/api/v2/Asesores/Portafolio/{id_cliente}/{pais}'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    try:
        respuesta = requests.get(url_portafolio, headers=encabezados)
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            return None
    except Exception as e:
        st.error(f'Error al obtener portafolio: {str(e)}')
        return None

def obtener_cotizacion_mep(token_portador, simbolo, id_plazo_compra, id_plazo_venta):
    url_cotizacion_mep = 'https://api.invertironline.com/api/v2/Cotizaciones/MEP'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    datos = {
        "simbolo": simbolo,
        "idPlazoOperatoriaCompra": id_plazo_compra,
        "idPlazoOperatoriaVenta": id_plazo_venta
    }
    try:
        respuesta = requests.post(url_cotizacion_mep, headers=encabezados, json=datos)
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            return None
    except Exception as e:
        st.error(f'Error al obtener cotización MEP: {str(e)}')
        return None

def obtener_tasas_caucion(token_portador, instrumento="Cauciones", panel="Todas", pais="Argentina"):
    url = f"https://api.invertironline.com/api/v2/Cotizaciones/{instrumento}/{panel}/{pais}"
    headers = {
        "Authorization": f"Bearer {token_portador}"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f'Error al obtener tasas de caución: {str(e)}')
        return None

# --- NUEVAS FUNCIONALIDADES INTEGRADAS ---
def obtener_serie_historica(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="Ajustada"):
    """
    Obtiene la serie histórica de precios con formato mejorado y manejo de errores
    """
    # Mapeo de mercados para compatibilidad con la API
    mercados_map = {
        'BCBA': 'bCBA',
        'NYSE': 'nYSE',
        'NASDAQ': 'nASDAQ',
        'ROFEX': 'rOFEX'
    }
    
    mercado_normalizado = mercados_map.get(mercado, mercado)
    url = f"https://api.invertironline.com/api/v2/{mercado_normalizado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if not data:
                return None
            
            # Procesar datos en un DataFrame
            df = pd.DataFrame(data)
            
            # Convertir y formatear campos importantes
            if 'fechaHora' in df:
                df['fecha'] = pd.to_datetime(df['fechaHora'])
                df = df.sort_values('fecha')
            
            # Seleccionar campos relevantes
            campos_relevantes = ['fecha', 'ultimoPrecio', 'apertura', 'maximo', 'minimo', 'cierreAnterior', 'volumen']
            campos_disponibles = [c for c in campos_relevantes if c in df.columns]
            
            return df[campos_disponibles].set_index('fecha')
        else:
            st.error(f"Error al obtener serie histórica: {response.status_code}")
            return None
    except Exception as e:
        st.error(f'Error de conexión al obtener serie histórica: {str(e)}')
        return None

def obtener_panel_cotizaciones(token_portador, instrumento, panel, pais):
    """
    Obtiene panel de cotizaciones con manejo de errores mejorado
    """
    url = f"https://api.invertironline.com/api/v2/Cotizaciones/{instrumento}/{panel}/{pais}"
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            # Normalizar estructura de respuesta
            if 'titulos' in data:
                df = pd.DataFrame(data['titulos'])
                
                # Campos relevantes para diferentes instrumentos
                campos_comunes = ['simbolo', 'ultimoPrecio', 'variacionPorcentual', 'apertura', 'maximo', 'minimo', 'volumen']
                campos_bonos = ['fechaVencimiento', 'tasa'] + campos_comunes
                campos_acciones = ['cantidadOperaciones', 'moneda'] + campos_comunes
                
                # Seleccionar campos según instrumento
                if instrumento == 'Bonos':
                    campos = [c for c in campos_bonos if c in df.columns]
                elif instrumento == 'Acciones':
                    campos = [c for c in campos_acciones if c in df.columns]
                else:
                    campos = campos_comunes
                
                return df[campos] if campos else df
            return pd.DataFrame()
        else:
            st.error(f"Error al obtener panel de cotizaciones: {response.status_code}")
            return None
    except Exception as e:
        st.error(f'Error de conexión al obtener panel de cotizaciones: {str(e)}')
        return None

def obtener_cotizacion_actual(token_portador, mercado, simbolo, plazo='T2'):
    """
    Obtiene cotización actual con manejo de errores mejorado
    """
    # Mapeo de mercados para compatibilidad con la API
    mercados_map = {
        'BCBA': 'bCBA',
        'NYSE': 'nYSE',
        'NASDAQ': 'nASDAQ',
        'ROFEX': 'rOFEX'
    }
    
    mercado_normalizado = mercados_map.get(mercado, mercado)
    url = f"https://api.invertironline.com/api/v2/{mercado_normalizado}/Titulos/{simbolo}/Cotizacion"
    params = {'plazo': plazo}
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener cotización actual: {response.status_code}")
            return None
    except Exception as e:
        st.error(f'Error de conexión al obtener cotización actual: {str(e)}')
        return None

def obtener_cotizacion_detalle(token_portador, mercado, simbolo):
    """
    Obtiene detalle de cotización con manejo de errores mejorado
    """
    # Mapeo de mercados para compatibilidad con la API
    mercados_map = {
        'BCBA': 'bCBA',
        'NYSE': 'nYSE',
        'NASDAQ': 'nASDAQ',
        'ROFEX': 'rOFEX'
    }
    
    mercado_normalizado = mercados_map.get(mercado, mercado)
    url = f"https://api.invertironline.com/api/v2/{mercado_normalizado}/Titulos/{simbolo}/CotizacionDetalle"
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener detalle de cotización: {response.status_code}")
            return None
    except Exception as e:
        st.error(f'Error de conexión al obtener detalle de cotización: {str(e)}')
        return None

# --- FUNCIONES DE VISUALIZACIÓN MEJORADAS ---
def mostrar_serie_historica_interactiva(df_serie, simbolo):
    """Muestra gráfico interactivo de serie histórica con Plotly"""
    if df_serie is None or df_serie.empty:
        st.warning("No hay datos disponibles para mostrar la serie histórica")
        return
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05,
                        row_heights=[0.7, 0.3])
    
    # Gráfico de precios
    fig.add_trace(go.Candlestick(
        x=df_serie.index,
        open=df_serie['apertura'] if 'apertura' in df_serie else df_serie['ultimoPrecio'],
        high=df_serie['maximo'] if 'maximo' in df_serie else df_serie['ultimoPrecio'],
        low=df_serie['minimo'] if 'minimo' in df_serie else df_serie['ultimoPrecio'],
        close=df_serie['ultimoPrecio'],
        name='Precio'
    ), row=1, col=1)
    
    # Volumen
    if 'volumen' in df_serie:
        fig.add_trace(go.Bar(
            x=df_serie.index,
            y=df_serie['volumen'],
            name='Volumen',
            marker_color='#1f77b4'
        ), row=2, col=1)
    
    # Actualizar diseño
    fig.update_layout(
        title=f'Serie Histórica de {simbolo}',
        height=600,
        showlegend=False,
        xaxis_rangeslider_visible=False,
        template='plotly_white'
    )
    
    fig.update_yaxes(title_text="Precio", row=1, col=1)
    if 'volumen' in df_serie:
        fig.update_yaxes(title_text="Volumen", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)

def mostrar_panel_cotizaciones(df_panel, instrumento):
    """Muestra panel de cotizaciones con filtros interactivos"""
    if df_panel is None or df_panel.empty:
        st.warning("No hay datos disponibles para el panel seleccionado")
        return
    
    st.markdown(f"### 📊 Panel de {instrumento} ({len(df_panel)} instrumentos)")
    
    # Filtros interactivos
    col1, col2 = st.columns([2, 1])
    with col1:
        filtro_simbolo = st.text_input("Filtrar por símbolo", "")
    
    with col2:
        if 'variacionPorcentual' in df_panel:
            variacion_min = df_panel['variacionPorcentual'].min()
            variacion_max = df_panel['variacionPorcentual'].max()
            rango_variacion = st.slider(
                "Rango de variación (%)", 
                float(variacion_min), float(variacion_max), 
                (float(variacion_min), float(variacion_max))
            )
    
    # Aplicar filtros
    if filtro_simbolo:
        df_panel = df_panel[df_panel['simbolo'].str.contains(filtro_simbolo, case=False)]
    
    if 'variacionPorcentual' in df_panel:
        df_panel = df_panel[
            (df_panel['variacionPorcentual'] >= rango_variacion[0]) & 
            (df_panel['variacionPorcentual'] <= rango_variacion[1])
        ]
    
    # Mostrar tabla con estilo
    st.dataframe(df_panel.style.format({
        'ultimoPrecio': '{:.2f}',
        'variacionPorcentual': '{:.2f}%',
        'apertura': '{:.2f}',
        'maximo': '{:.2f}',
        'minimo': '{:.2f}',
        'volumen': '{:,.0f}'
    }) if 'volumen' in df_panel else df_panel, 
    height=600, use_container_width=True)

def mostrar_detalle_cotizacion(detalle, simbolo):
    """Muestra detalle de cotización con formato mejorado"""
    if not detalle:
        st.warning("No hay detalles disponibles para esta cotización")
        return
    
    st.markdown(f"### 📈 Detalle de Cotización - {simbolo}")
    
    # Organizar la información en columnas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Último Precio", f"${detalle.get('ultimoPrecio', 'N/A'):,.2f}")
        st.metric("Apertura", f"${detalle.get('apertura', 'N/A'):,.2f}")
        st.metric("Cierre Anterior", f"${detalle.get('cierreAnterior', 'N/A'):,.2f}")
    
    with col2:
        st.metric("Máximo", f"${detalle.get('maximo', 'N/A'):,.2f}")
        st.metric("Mínimo", f"${detalle.get('minimo', 'N/A'):,.2f}")
        st.metric("Variación", f"{detalle.get('variacion', 'N/A'):,.2f}%")
    
    with col3:
        st.metric("Volumen", f"{detalle.get('volumenNominal', 'N/A'):,.0f}")
        st.metric("Operaciones", detalle.get('cantidadOperaciones', 'N/A'))
        st.metric("Tendencia", detalle.get('tendencia', 'N/A'))
    
    # Mostrar puntas si están disponibles
    if 'puntas' in detalle and detalle['puntas']:
        st.markdown("#### 📌 Puntas de Mercado")
        puntas = detalle['puntas']
        
        if isinstance(puntas, list) and len(puntas) > 0:
            cols = st.columns(len(puntas))
            for i, punta in enumerate(puntas[:3]):  # Mostrar máximo 3 puntas
                with cols[i]:
                    st.markdown(f"**Punta {i+1}**")
                    st.metric("Compra", f"{punta.get('cantidadCompra', 'N/A')} @ ${punta.get('precioCompra', 'N/A'):,.2f}")
                    st.metric("Venta", f"{punta.get('cantidadVenta', 'N/A')} @ ${punta.get('precioVenta', 'N/A'):,.2f}")

# --- INTEGRACIÓN EN LA APLICACIÓN PRINCIPAL ---
def mostrar_mercado_avanzado(token_acceso):
    """Muestra sección avanzada de datos de mercado"""
    st.markdown("## 📈 Mercado Avanzado")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Serie Histórica", 
        "📊 Panel de Mercado", 
        "💹 Cotización Actual",
        "🔍 Detalle de Cotización"
    ])
    
    with tab1:
        st.markdown("### 📅 Consultar Serie Histórica")
        col1, col2 = st.columns(2)
        with col1:
            mercado = st.selectbox("Mercado", ['BCBA', 'NYSE', 'NASDAQ', 'ROFEX'], key='hist_mercado')
            simbolo = st.text_input("Símbolo", "GGAL", key='hist_simbolo')
            ajustada = st.radio("Tipo de ajuste", ['Ajustada', 'SinAjustar'], horizontal=True)
        
        with col2:
            fecha_desde = st.date_input("Fecha desde", value=date.today() - timedelta(days=365))
            fecha_hasta = st.date_input("Fecha hasta", value=date.today())
        
        if st.button("Obtener Serie Histórica", key='btn_hist'):
            with st.spinner("Obteniendo datos históricos..."):
                df_serie = obtener_serie_historica(
                    token_acceso, mercado, simbolo, 
                    fecha_desde.strftime('%Y-%m-%d'), 
                    fecha_hasta.strftime('%Y-%m-%d'),
                    ajustada
                )
                if df_serie is not None:
                    mostrar_serie_historica_interactiva(df_serie, simbolo)
    
    with tab2:
        st.markdown("### 📊 Panel de Mercado")
        col1, col2, col3 = st.columns(3)
        with col1:
            instrumento = st.selectbox("Instrumento", 
                                      ['Acciones', 'Bonos', 'Opciones', 'Monedas', 'Cauciones', 'Futuros', 'ADRs'],
                                      key='panel_instrumento')
        with col2:
            panel = st.selectbox("Panel", ['Todas', 'Panel General', 'Burcap'], key='panel_tipo')
        with col3:
            pais = st.selectbox("País", ['Argentina', 'Estados_Unidos'], key='panel_pais')
        
        if st.button("Obtener Panel", key='btn_panel'):
            with st.spinner("Cargando panel de mercado..."):
                df_panel = obtener_panel_cotizaciones(token_acceso, instrumento, panel, pais)
                if df_panel is not None:
                    mostrar_panel_cotizaciones(df_panel, instrumento)
    
    with tab3:
        st.markdown("### 💹 Consultar Cotización Actual")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            mercado = st.selectbox("Mercado", ['BCBA', 'NYSE', 'NASDAQ', 'ROFEX'], key='cot_mercado')
        with col2:
            simbolo = st.text_input("Símbolo", "GGAL", key='cot_simbolo')
        with col3:
            plazo = st.selectbox("Plazo", ['T0', 'T1', 'T2', 'T3'], key='cot_plazo')
        
        if st.button("Obtener Cotización", key='btn_cot'):
            with st.spinner("Obteniendo cotización actual..."):
                cotizacion = obtener_cotizacion_actual(token_acceso, mercado, simbolo, plazo)
                if cotizacion:
                    st.subheader(f"Detalles de {simbolo}")
                    st.json(cotizacion)
    
    with tab4:
        st.markdown("### 🔍 Consultar Detalle de Cotización")
        col1, col2 = st.columns(2)
        with col1:
            mercado = st.selectbox("Mercado", ['BCBA', 'NYSE', 'NASDAQ', 'ROFEX'], key='det_mercado')
        with col2:
            simbolo = st.text_input("Símbolo", "GGAL", key='det_simbolo')
        
        if st.button("Obtener Detalle", key='btn_det'):
            with st.spinner("Obteniendo detalles..."):
                detalle = obtener_cotizacion_detalle(token_acceso, mercado, simbolo)
                if detalle:
                    mostrar_detalle_cotizacion(detalle, simbolo)

def mostrar_analisis_portafolio():
    cliente = st.session_state.cliente_seleccionado
    token_acceso = st.session_state.token_acceso

    if not cliente:
        st.error("No hay cliente seleccionado")
        return

    id_cliente = cliente.get('numeroCliente', cliente.get('id'))
    nombre_cliente = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))

    st.title(f"📊 Análisis de Portafolio - {nombre_cliente}")
    
    # Crear tabs con iconos
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Resumen Portafolio", 
        "💰 Estado de Cuenta", 
        "📊 Análisis Técnico",
        "💱 Cotizaciones",
        "📈 Mercado Avanzado"  # Nueva pestaña
    ])

    with tab1:
        portafolio = obtener_portafolio(token_acceso, id_cliente)
        if portafolio:
            mostrar_resumen_portafolio(portafolio)
        else:
            st.warning("No se pudo obtener el portafolio del cliente")
    
    with tab2:
        estado_cuenta = obtener_estado_cuenta(token_acceso, id_cliente)
        if estado_cuenta:
            mostrar_estado_cuenta(estado_cuenta)
        else:
            st.warning("No se pudo obtener el estado de cuenta")
    
    with tab3:
        mostrar_analisis_tecnico(token_acceso, id_cliente)
    
    with tab4:
        mostrar_cotizaciones_mercado(token_acceso)
    
    with tab5:
        mostrar_mercado_avanzado(token_acceso)

# ... (El resto del código de funciones auxiliares y main se mantiene igual que en la versión anterior) ...

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
            if not st.session_state.clientes:
                with st.spinner("Cargando clientes..."):
                    clientes = obtener_lista_clientes(st.session_state.token_acceso)
                    st.session_state.clientes = clientes
            
            clientes = st.session_state.clientes
            
            if clientes:
                st.subheader("Selección de Cliente")
                cliente_ids = [c.get('numeroCliente', c.get('id')) for c in clientes]
                cliente_nombres = [c.get('apellidoYNombre', c.get('nombre', 'Cliente')) for c in clientes]
                
                cliente_seleccionado = st.selectbox(
                    "Seleccione un cliente:",
                    options=cliente_ids,
                    format_func=lambda x: cliente_nombres[cliente_ids.index(x)] if x in cliente_ids else "Cliente",
                    label_visibility="collapsed"
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
        if st.session_state.token_acceso and st.session_state.cliente_seleccionado:
            mostrar_analisis_portafolio()
        elif st.session_state.token_acceso:
            st.info("👆 Seleccione un cliente en la barra lateral para comenzar")
        else:
            st.info("👆 Ingrese sus credenciales para comenzar")
            
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
    except Exception as e:
        st.error(f"❌ Error en la aplicación: {str(e)}")

if __name__ == "__main__":
    main()
