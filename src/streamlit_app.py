# Standard library imports
import os
import re
import time
import json
import random
import warnings
import requests  # Keep this import at the top level
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Union, Any

# Third-party imports (lazy load heavy libraries)
import streamlit as st
import pandas as pd
import numpy as np

# Configure warnings and logging
warnings.filterwarnings('ignore')

# Lazy imports for heavy libraries
lazy_imports = {}

def lazy_import(module_name, from_imports=None):
    """Lazy import helper function"""
    if module_name not in lazy_imports:
        if from_imports:
            module = __import__(module_name, fromlist=from_imports)
            lazy_imports[module_name] = module
        else:
            module = __import__(module_name)
            lazy_imports[module_name] = module
    return lazy_imports[module_name]

# Function to get lazy imports
def get_import(module_name, from_imports=None):
    """Get a lazy imported module"""
    return lambda: lazy_import(module_name, from_imports)

# Define lazy imports
plotly_go = get_import('plotly.graph_objects')
plt = get_import('matplotlib.pyplot')
px = get_import('plotly.express')
make_subplots = get_import('plotly.subplots', ['make_subplots'])
arch_model = get_import('arch', ['arch_model'])
scipy_stats = get_import('scipy.stats')
scipy_optimize = get_import('scipy.optimize')
minimize = get_import('scipy.optimize', ['minimize'])
gaussian_kde = get_import('scipy.stats', ['gaussian_kde'])
yf = get_import('yfinance')
components = get_import('streamlit.components.v1')

# Ensure requests is available in the global scope
requests = requests

# Import scipy.stats as stats for statistical functions
from scipy import stats
import scipy.optimize as op

# Caching configuration
CACHE_TTL = 3600  # 1 hour cache
try:
    # Try to import from pyfolio-reloaded first
    from pyfolio_reloaded import timeseries
    from pyfolio_reloaded.plotting import plot_rolling_returns, plot_annual_returns, plot_monthly_returns_heatmap
    import pyfolio_reloaded as pf
except ImportError:
    # Fall back to original pyfolio if pyfolio-reloaded is not available
    try:
        import pyfolio as pf
        from pyfolio import timeseries
        from pyfolio.plotting import plot_rolling_returns, plot_annual_returns, plot_monthly_returns_heatmap
    except ImportError:
        # If both fail, create mock objects to prevent errors
        class MockPf:
            pass
        pf = MockPf()
        pf.timeseries = type('MockTimeseries', (), {})()
        pf.plotting = type('MockPlotting', (), {})()
        plot_rolling_returns = plot_annual_returns = plot_monthly_returns_heatmap = lambda *args, **kwargs: None

warnings.filterwarnings('ignore')

# Configuración global para Plotly
@st.cache_resource
def setup_plotly():
    import plotly.io as pio
    pio.templates.default = "plotly_dark"
    return pio

# Initialize plotly with caching
pio = setup_plotly()

# Configuración de la página con tema oscuro profesional
st.set_page_config(
    page_title="IOL Portfolio Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para tema oscuro
st.markdown("""
<style>
    /* Estilos generales dark theme */
    .stApp, 
    .stApp > div[data-testid="stAppViewContainer"],
    .stApp > div[data-testid="stAppViewContainer"] > div {
        background-color: #0f172a !important;
        color: #f8f9fa !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Asegurar que todo el texto sea claro */
    body, p, div, span, h1, h2, h3, h4, h5, h6, label, input, select, textarea, button,
    .stSelectbox div[data-baseweb="select"] div,
    .stDateInput div[data-baseweb="input"] input,
    .stTextInput div[data-baseweb="input"] input,
    .stNumberInput div[data-baseweb="input"] input,
    .stTextArea div[data-baseweb="textarea"] textarea,
    .stAlert,
    .stAlert p,
    .stAlert div,
    .stAlert span,
    .stTooltip,
    .stTooltip p,
    .stTooltip div,
    .stTooltip span,
    .stMarkdown,
    .stMarkdown p,
    .stMarkdown div,
    .stMarkdown span,
    a,
    a:visited,
    a:hover,
    .st-bb,
    .st-bj,
    .st-bk,
    .st-bn,
    .st-bo,
    .st-bp,
    .st-bq,
    .st-br,
    .st-bs,
    .st-bt {
        color: #f8f9fa !important;
    }
    
    /* Asegurar que los enlaces sean visibles */
    a {
        color: #4CAF50 !important;
        text-decoration: none;
    }
    
    a:hover {
        color: #45a049 !important;
        text-decoration: underline;
    }
    
    /* Mejorar la visibilidad de los placeholders */
    ::placeholder {
        color: #94a3b8 !important;
        opacity: 1;
    }
    
    /* Mejorar la visibilidad de los tooltips */
    .stTooltip {
        background-color: #1e293b !important;
        border: 1px solid #4CAF50 !important;
        color: #f8f9fa !important;
    }
    
    /* Estilos para menús desplegables y listas */
    /* Select principal */
    div[data-baseweb="select"],
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] input,
    div[data-baseweb="select"] div[role="button"],
    div[data-baseweb="select"] div[role="listbox"],
    div[data-baseweb="select"] div[role="combobox"],
    div[data-baseweb="select"] div[data-baseweb="select"] {
        background-color: #1e293b !important;
        color: #f8f9fa !important;
        border-color: #4CAF50 !important;
    }
    
    /* Opciones del menú desplegable */
    div[role="listbox"],
    div[role="listbox"] ul,
    div[role="listbox"] li,
    div[role="option"],
    div[role="option"] > div,
    div[role="option"] > span,
    div[role="listbox"] > div,
    div[role="listbox"] > div > div,
    div[data-baseweb*="popover"] *,
    div[data-baseweb*="popover"] div,
    div[data-baseweb*="popover"] span,
    div[data-baseweb*="popover"] li,
    div[data-baseweb*="popover"] ul,
    div[data-baseweb*="popover"] p,
    div[data-baseweb*="popover"] a,
    div[data-baseweb*="popover"] button,
    div[data-baseweb*="popover"] input,
    div[data-baseweb*="popover"] select,
    div[data-baseweb*="popover"] option {
        background-color: #1e293b !important;
        color: #f8f9fa !important;
    }
    
    /* Asegurar que el texto dentro de los popovers sea visible */
    div[data-baseweb*="popover"] {
        background-color: #1e293b !important;
        border: 1px solid #4CAF50 !important;
    }
    
    /* Asegurar que el texto de las opciones sea visible */
    div[role="option"] *,
    div[role="option"] span,
    div[role="option"] div {
        color: #f8f9fa !important;
    }
    
    /* Efecto hover en opciones */
    div[role="option"]:hover,
    div[role="option"]:hover > div,
    div[role="option"]:hover > span,
    div[role="listbox"] > div:hover,
    div[role="listbox"] > div > div:hover {
        background-color: #2d3748 !important;
        color: #ffffff !important;
    }
    
    /* Opción seleccionada */
    div[aria-selected="true"],
    div[aria-selected="true"] > div,
    div[aria-selected="true"] > span {
        background-color: #4CAF50 !important;
        color: #ffffff !important;
    }
    
    /* Estilos para los elementos de entrada */
    input[type="text"],
    input[type="number"],
    input[type="date"],
    input[type="time"],
    input[type="password"],
    input[type="email"],
    input[type="search"],
    select,
    textarea {
        background-color: #1e293b !important;
        color: #f8f9fa !important;
        border-color: #4CAF50 !important;
    }
    
    /* Placeholder */
    input::placeholder,
    textarea::placeholder {
        color: #94a3b8 !important;
        opacity: 1;
    }
    
    /* Estilos para las listas de selección múltiple */
    .stMultiSelect [role="button"],
    .stMultiSelect [role="button"]:hover,
    .stMultiSelect [role="button"]:focus {
        background-color: #1e293b !important;
        color: #f8f9fa !important;
        border-color: #4CAF50 !important;
    }
    
    .stMultiSelect [role="option"] {
        background-color: #1e293b !important;
        color: #f8f9fa !important;
    }
    
    .stMultiSelect [role="option"]:hover {
        background-color: #2d3748 !important;
    }
    
    /* Mejorar la visibilidad de los mensajes */
    .stAlert {
        background-color: rgba(30, 41, 59, 0.9) !important;
        border-left: 4px solid #4CAF50 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    /* Ajustes para gráficos */
    .stPlotlyChart {
        background-color: #1e293b !important;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Asegurar que los checkboxes y radio buttons sean visibles */
    .stCheckbox > label,
    .stRadio > label,
    .stCheckbox > div,
    .stRadio > div {
        color: #f8f9fa !important;
    }
    
    /* Estilos para las pestañas activas */
    [data-baseweb="tab"] {
        color: #f8f9fa !important;
    }
    
    [data-baseweb="tab"]:hover {
        background-color: #2d3748 !important;
    }
    
    /* Estilos para los mensajes de error */
    .stAlert.stAlert-warning {
        border-left: 4px solid #ff9800 !important;
    }
    
    .stAlert.stAlert-error {
        border-left: 4px solid #f44336 !important;
    }
    
    .stAlert.stAlert-success {
        border-left: 4px solid #4CAF50 !important;
    }
    
    .stAlert.stAlert-info {
        border-left: 4px solid #2196F3 !important;
    }
    
    /* Mejora de tarjetas y métricas */
    .stMetric, 
    .stMetric > div > div,
    .stMetric > div > div > div {
        background-color: #1e293b !important;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        border-left: 4px solid #4CAF50;
        color: #f8f9fa !important;
    }
    
    .stMetric > div > div {
        color: #94a3b8 !important;
    }
    
    /* Mejora de pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
        background-color: #0f172a;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        padding: 0 20px;
        background-color: #1e293b;
        border-radius: 8px !important;
        font-weight: 500;
        color: #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50 !important;
        color: white !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #334155 !important;
    }
    
    /* Mejora de inputs */
    .stTextInput, .stNumberInput, .stDateInput, .stSelectbox, .stTextArea {
        background-color: #1e293b;
        border-radius: 8px;
        color: #e2e8f0;
        border: 1px solid #334155;
    }
    
    /* Estilos para las etiquetas de los inputs */
    .stTextInput > label, .stNumberInput > label, 
    .stDateInput > label, .stSelectbox > label,
    .stTextArea > label {
        color: #94a3b8 !important;
    }
    
    /* Botones */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        background-color: #4CAF50;
        color: white;
        border: none;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background-color: #45a049;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    /* Barra lateral */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a, #0c1424);
        color: white;
    }
    
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stNumberInput label {
        color: #94a3b8 !important;
    }
    
    /* Títulos */
    h1, h2, h3, h4, h5, h6 {
        color: #4CAF50;
        font-weight: 600;
    }
    
    /* Tablas */
    .dataframe {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    .dataframe th {
        background-color: #334155 !important;
        color: #e2e8f0 !important;
    }
    
    .dataframe tr:nth-child(even) {
        background-color: #1a2233 !important;
    }
    
    .dataframe tr:hover {
        background-color: #2c3a58 !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #4CAF50;
    }
    
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0f172a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #4CAF50;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #45a049;
    }
    
    /* Efectos hover para tarjetas */
    div[data-testid="stExpander"] {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stExpander"]:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transform: translateY(-2px);
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

@st.cache_data(ttl=300, show_spinner=False)
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

@st.cache_data(ttl=300, show_spinner=False)
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

@st.cache_data(ttl=300, show_spinner=False)
def obtener_precio_actual(token_portador, mercado, simbolo):
    """Obtiene el último precio de un título puntual (endpoint estándar de IOL)."""
    url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion"
    headers = obtener_encabezado_autorizacion(token_portador)
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, (int, float)):
                return float(data)
            elif isinstance(data, dict):
                # La API suele devolver 'ultimoPrecio'
                for k in [
                    'ultimoPrecio', 'ultimo_precio', 'ultimoPrecioComprador', 'ultimoPrecioVendedor',
                    'precio', 'precioActual', 'valor'
                ]:
                    if k in data and data[k] is not None:
                        try:
                            return float(data[k])
                        except ValueError:
                            continue
        return None
    except Exception:
        return None

@st.cache_data(ttl=300, show_spinner=False)
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
            resultado = respuesta.json()
            # Asegurarse de que siempre devolvemos un diccionario
            if isinstance(resultado, (int, float)):
                return {'precio': resultado, 'simbolo': simbolo}
            elif isinstance(resultado, dict):
                return resultado
            else:
                return {'precio': None, 'simbolo': simbolo, 'error': 'Formato de respuesta inesperado'}
        else:
            return {'precio': None, 'simbolo': simbolo, 'error': f'Error HTTP {respuesta.status_code}'}
    except Exception as e:
        st.error(f'Error al obtener cotización MEP: {str(e)}')
        return {'precio': None, 'simbolo': simbolo, 'error': str(e)}

@st.cache_data(ttl=300, show_spinner=False)
def obtener_movimientos_asesor(token_portador, clientes, fecha_desde, fecha_hasta, tipo_fecha="fechaOperacion", 
                             estado=None, tipo_operacion=None, pais=None, moneda=None, cuenta_comitente=None):
    """
    Obtiene los movimientos de los clientes de un asesor
    
    Args:
        token_portador (str): Token de autenticación
        clientes (list): Lista de IDs de clientes
        fecha_desde (str): Fecha de inicio (formato ISO)
        fecha_hasta (str): Fecha de fin (formato ISO)
        tipo_fecha (str): Tipo de fecha a filtrar ('fechaOperacion' o 'fechaLiquidacion')
        estado (str, optional): Estado de la operación
        tipo_operacion (str, optional): Tipo de operación
        pais (str, optional): País de la operación
        moneda (str, optional): Moneda de la operación
        cuenta_comitente (str, optional): Número de cuenta comitente
        
    Returns:
        dict: Diccionario con los movimientos o None en caso de error
    """
    url = "https://api.invertironline.com/api/v2/Asesor/Movimientos"
    headers = {
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'application/json'
    }
    
    # Preparar el cuerpo de la solicitud
    payload = {
        "clientes": clientes,
        "from": fecha_desde,
        "to": fecha_hasta,
        "dateType": tipo_fecha,
        "status": estado or "",
        "type": tipo_operacion or "",
        "country": pais or "",
        "currency": moneda or "",
        "cuentaComitente": cuenta_comitente or ""
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener movimientos: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

@st.cache_data(ttl=300, show_spinner=False)
def obtener_tasas_caucion(token_portador):
    """
    Obtiene todas las tasas de caución para todos los plazos desde la API de IOL.
    
    Args:
        token_portador (str): Token de autenticación Bearer
    
    Returns:
        DataFrame: DataFrame con la información de todas las cauciones/plazos o None en caso de error
    """
    url = "https://api.invertironline.com/api/v2/Cotizaciones/cauciones/argentina/Todos"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_portador}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # Lanza una excepción para códigos de error HTTP
        
        data = response.json()
        if not data or 'titulos' not in data or not data['titulos']:
            st.warning("No se encontraron datos de tasas de caución en la respuesta")
            return None
            
        # Crear DataFrame con los datos de las cauciones
        df = pd.DataFrame(data['titulos'])
        
        # Procesar los datos para mejor legibilidad
        if 'plazo' in df.columns:
            # Extraer el número de días del plazo (ej: "7 días" -> 7)
            df['plazo_dias'] = df['plazo'].str.extract(r'(\d+)').astype(float)
        
        # Asegurarse de que tenemos los precios como números
        if 'ultimoPrecio' in df.columns:
            df['tasa'] = pd.to_numeric(df['ultimoPrecio'], errors='coerce')
        
        # Ordenar por plazo si está disponible
        if 'plazo_dias' in df.columns:
            df = df.sort_values('plazo_dias')
        
        # Seleccionar y renombrar columnas relevantes
        column_mapping = {
            'simbolo': 'símbolo',
            'descripcion': 'descripción',
            'ultimoPrecio': 'tasa',
            'volumen': 'volumen_operado',
            'cantidadOperaciones': 'operaciones'
        }
        
        # Mantener solo las columnas que existen en el DataFrame
        available_columns = [col for col in column_mapping.keys() if col in df.columns]
        df = df[available_columns].rename(columns=column_mapping)
        
        # Agregar columnas calculadas si es necesario
        if 'tasa' in df.columns:
            df['tasa_anual'] = df['tasa'] * 365 / (df.get('plazo_dias', 1) if 'plazo_dias' in df.columns else 1)
        
        return df
        
    except requests.exceptions.HTTPError as http_err:
        error_msg = f"Error HTTP al obtener tasas de caución: {http_err}"
        if hasattr(http_err, 'response') and hasattr(http_err.response, 'text'):
            try:
                error_data = http_err.response.json()
                error_msg += f" - {error_data.get('message', '')}"
            except:
                error_msg += f" - {http_err.response.text}"
        st.error(error_msg)
        return None
        
    except requests.exceptions.RequestException as req_err:
        st.error(f"Error de conexión al obtener tasas de caución: {str(req_err)}")
        return None
        
    except Exception as e:
        st.error(f"Error inesperado al procesar tasas de caución: {str(e)}")
        return None

@st.cache_data(ttl=300, show_spinner=False)
def mostrar_tasas_caucion(token_portador):
    """
    Muestra las tasas de caución en una tabla y gráfico de curva de tasas optimizado
    con soporte para múltiples tipos de activos
    """
    st.subheader("📊 Curva de Tasas de Caución")
    
    try:
        # Obtener datos de caución
        df_cauciones = obtener_tasas_caucion(token_portador)
        
        # Verificar si se obtuvieron datos
        if df_cauciones is None or df_cauciones.empty:
            st.warning("No se encontraron datos de tasas de caución.")
            return
            
        # Verificar columnas requeridas
        required_columns = ['símbolo', 'plazo', 'tasa', 'plazo_dias', 'tasa_anual', 'tipo_activo']
        missing_columns = [col for col in required_columns if col not in df_cauciones.columns]
        if missing_columns:
            st.error(f"Faltan columnas requeridas en los datos: {', '.join(missing_columns)}")
            st.dataframe(df_cauciones.head())  # Mostrar datos disponibles para depuración
            return
            
        # Obtener lista única de tipos de activos
        tipos_activos = sorted(df_cauciones['tipo_activo'].unique().tolist())
        
        # Selector múltiple de tipos de activos
        tipos_seleccionados = st.multiselect(
            'Seleccione tipos de activos a visualizar',
            options=tipos_activos,
            default=tipos_activos,  # Por defecto seleccionar todos
            key='tipo_activo_selector'
        )
        
        # Filtrar datos por tipos de activos seleccionados
        if tipos_seleccionados:
            df_filtrado = df_cauciones[df_cauciones['tipo_activo'].isin(tipos_seleccionados)].copy()
        else:
            st.warning("Seleccione al menos un tipo de activo para visualizar")
            return
        
        # Crear pestañas para diferentes vistas
        tab1, tab2 = st.tabs(["📈 Gráfico", "📊 Datos"])
        
        with tab1:
            # Crear gráfico de curva de tasas
            fig = go.Figure()
            
            # Definir colores para cada tipo de activo
            colors = px.colors.qualitative.Plotly
            
            # Agrupar por tipo de activo y agregar una traza para cada tipo
            for i, (tipo_activo, group) in enumerate(df_filtrado.groupby('tipo_activo')):
                color_idx = i % len(colors)
                
                # Ordenar por plazo para una línea más suave
                group = group.sort_values('plazo_dias')
                
                # Añadir línea para este tipo de activo
                fig.add_trace(go.Scatter(
                    x=group['plazo_dias'],
                    y=group['tasa_anual'],
                    mode='lines+markers',
                    name=tipo_activo,
                    line=dict(color=colors[color_idx], width=2),
                    marker=dict(size=10, color=colors[color_idx]),
                    text=group['plazo'].astype(str) + ' días',
                    hovertemplate=
                        '<b>Tipo:</b> ' + tipo_activo + '<br>' +
                        '<b>Plazo:</b> %{x} días<br>' +
                        '<b>Tasa Anual:</b> %{y:.2f}%<br>' +
                        '<b>Descripción:</b> ' + group['descripción'].astype(str) +
                        '<extra></extra>',
                    showlegend=True
                ))
                
                # Añadir línea de tendencia para este tipo de activo
                if len(group) > 1:  # Necesitamos al menos 2 puntos para una línea de tendencia
                    z = np.polyfit(group['plazo_dias'], group['tasa_anual'], 1)
                    p = np.poly1d(z)
                    
                    fig.add_trace(go.Scatter(
                        x=group['plazo_dias'],
                        y=p(group['plazo_dias']),
                        mode='lines',
                        name=f'Tendencia {tipo_activo}',
                        line=dict(color=colors[color_idx], width=1, dash='dash'),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
            
            # Configuración del layout
            fig.update_layout(
                title='Curva de Tasas de Caución por Plazo y Tipo de Activo',
                xaxis_title='Plazo (días)',
                yaxis_title='Tasa Anual Efectiva (%)',
                template='plotly_dark',
                height=600,
                hovermode='closest',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis=dict(
                    tickmode='linear',
                    tick0=0,
                    dtick=1,
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(128,128,128,0.2)',
                    showspikes=True,
                    spikethickness=1,
                    spikedash='dot',
                    spikecolor='#999999',
                    spikemode='across',
                ),
                yaxis=dict(
                    tickformat=".2f%",
                    gridcolor='rgba(128,128,128,0.2)',
                    showspikes=True,
                    spikethickness=1,
                    spikedash='dot',
                    spikecolor='#999999',
                ),
                margin=dict(l=50, r=50, t=80, b=50),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                hoverlabel=dict(
                    bgcolor='rgba(0,0,0,0.8)',
                    font_size=12,
                    font_family="Arial"
                )
            )
            
            # Mostrar el gráfico
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
            
            # Mostrar métricas clave por tipo de activo
            st.subheader("📊 Resumen de Tasas")
            
            # Calcular métricas generales
            tasa_min = df_filtrado['tasa_anual'].min()
            tasa_max = df_filtrado['tasa_anual'].max()
            tasa_prom = df_filtrado['tasa_anual'].mean()
            plazo_prom = df_filtrado['plazo_dias'].mean()
            
            # Mostrar métricas generales
            st.markdown("**Métricas Generales (todos los tipos seleccionados):**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Tasa Mínima", f"{tasa_min:.2f}%", delta=None)
            with col2:
                st.metric("Tasa Máxima", f"{tasa_max:.2f}%", delta=None)
            with col3:
                st.metric("Tasa Promedio", f"{tasa_prom:.2f}%", delta=None)
            with col4:
                st.metric("Plazo Promedio", f"{plazo_prom:.1f} días", delta=None)
            
            # Mostrar métricas por tipo de activo
            st.markdown("**Métricas por Tipo de Activo:**")
            
            # Crear un DataFrame con las métricas por tipo de activo
            metrics_by_type = []
            for tipo_activo, group in df_filtrado.groupby('tipo_activo'):
                metrics_by_type.append({
                    'Tipo de Activo': tipo_activo,
                    'Cantidad': len(group),
                    'Tasa Mínima': f"{group['tasa_anual'].min():.2f}%",
                    'Tasa Máxima': f"{group['tasa_anual'].max():.2f}%",
                    'Tasa Promedio': f"{group['tasa_anual'].mean():.2f}%",
                    'Plazo Promedio': f"{group['plazo_dias'].mean():.1f} días"
                })
            
            if metrics_by_type:
                df_metrics = pd.DataFrame(metrics_by_type)
                st.dataframe(
                    df_metrics,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Tipo de Activo': st.column_config.TextColumn("Tipo de Activo"),
                        'Cantidad': st.column_config.NumberColumn("Cantidad"),
                        'Tasa Mínima': st.column_config.TextColumn("Tasa Mínima"),
                        'Tasa Máxima': st.column_config.TextColumn("Tasa Máxima"),
                        'Tasa Promedio': st.column_config.TextColumn("Tasa Promedio"),
                        'Plazo Promedio': st.column_config.TextColumn("Plazo Promedio")
                    }
                )
            
            # Mostrar tendencia
            st.markdown("""
            **Análisis de Tendencia:**
            - Línea naranja punteada: Muestra la tendencia general de las tasas
            - Círculos coloreados: Representan las tasas de cada plazo
            - El color más oscuro indica tasas más bajas, más claro indica tasas más altas
            """)
            
        with tab2:
            # Mostrar tabla con los datos filtrados
            st.dataframe(
                df_filtrado[['tipo_activo', 'símbolo', 'descripción', 'plazo', 'plazo_dias', 'tasa_anual']]
                .sort_values(['tipo_activo', 'plazo_dias'])
                .assign(tasa_anual=lambda x: x['tasa_anual'].round(2).astype(str) + '%')
                .rename(columns={
                    'tipo_activo': 'Tipo de Activo',
                    'símbolo': 'Símbolo',
                    'descripción': 'Descripción',
                    'plazo': 'Plazo',
                    'plazo_dias': 'Días',
                    'tasa_anual': 'Tasa Anual'
                }),
                use_container_width=True,
                height=min(600, 50 + len(df_filtrado) * 35),
                hide_index=True,
                column_config={
                    'Tipo de Activo': st.column_config.TextColumn("Tipo de Activo"),
                    'Símbolo': st.column_config.TextColumn("Símbolo"),
                    'Descripción': st.column_config.TextColumn("Descripción"),
                    'Plazo': st.column_config.TextColumn("Plazo"),
                    'Días': st.column_config.NumberColumn("Días"),
                    'Tasa Anual': st.column_config.TextColumn("Tasa Anual")
                }
            )
            
            # Botón para descargar datos
            csv = df_filtrado.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Descargar datos en CSV",
                data=csv,
                file_name=f'tasas_caucion_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
                mime='text/csv',
                help="Descargar los datos mostrados en formato CSV"
            )
            
    except Exception as e:
        st.error(f"Error al mostrar las tasas de caución: {str(e)}")
        # Mostrar solo el error sin el traceback completo para mejor experiencia de usuario
        if st.button("Mostrar detalles del error"):
            st.exception(e)
    formats_to_try = [
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "ISO8601",
        "mixed"
    ]
    
    for fmt in formats_to_try:
        try:
            if fmt == "ISO8601":
                return pd.to_datetime(datetime_string, format='ISO8601')
            elif fmt == "mixed":
                return pd.to_datetime(datetime_string, format='mixed')
            else:
                return pd.to_datetime(datetime_string, format=fmt)
        except Exception:
            continue

    try:
        return pd.to_datetime(datetime_string, infer_datetime_format=True)
    except Exception:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def obtener_endpoint_historico(mercado, simbolo, fecha_desde, fecha_hasta, ajustada="SinAjustar"):
    """Devuelve la URL correcta para la serie histórica del símbolo indicado.

    La prioridad es:
    1. Usar el mercado recibido (ya normalizado por la llamada superior)
       si existe en el mapeo de casos especiales.
    2. Caso contrario, construir la ruta estándar
       "{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/...".

    No se aplican heurísticas sobre el símbolo: la función que invoque debe
    pasar el mercado correcto (por ejemplo: 'Bonos', 'Cedears', 'BCBA').
    """
    base_url = "https://api.invertironline.com/api/v2"

    # Cubrir alias frecuentes para que el mapeo sea coherente
    alias = {
        'TITULOSPUBLICOS': 'TitulosPublicos',
        'TITULOS PUBLICOS': 'TitulosPublicos'
    }
    mercado_norm = alias.get(mercado.upper(), mercado)

    especiales = {
        'Opciones': f"{base_url}/Opciones/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'FCI': f"{base_url}/Titulos/FCI/{simbolo}/cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'MEP': f"{base_url}/Cotizaciones/MEP/{simbolo}",
        'Caucion': f"{base_url}/Cotizaciones/Cauciones/Todas/Argentina",
        'TitulosPublicos': f"{base_url}/TitulosPublicos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'Cedears': f"{base_url}/Cedears/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'ADRs': f"{base_url}/ADRs/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'Bonos': f"{base_url}/Bonos/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
    }

    if mercado_norm in especiales:
        return especiales[mercado_norm]

    # Ruta genérica (acciones BCBA, NYSE, NASDAQ, etc.)
    return f"{base_url}/{mercado_norm}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"

@st.cache_data(ttl=300, show_spinner=False)
def parse_datetime_flexible(date_str: str):
    """
    Parses a datetime string that may or may not include microseconds or timezone info.
    Handles both formats: with and without milliseconds.
    """
    if not isinstance(date_str, str):
        return None
    try:
        # First try parsing with the exact format that matches the error
        try:
            # Handle format without milliseconds: "2024-12-10T17:11:04"
            if len(date_str) == 19 and 'T' in date_str and date_str.count(':') == 2:
                return pd.to_datetime(date_str, format='%Y-%m-%dT%H:%M:%S', utc=True)
            # Handle format with milliseconds: "2024-12-10T17:11:04.123"
            elif '.' in date_str and 'T' in date_str:
                return pd.to_datetime(date_str, format='%Y-%m-%dT%H:%M:%S.%f', utc=True)
        except (ValueError, TypeError):
            pass
            
        # Fall back to pandas' built-in parser if specific formats don't match
        return pd.to_datetime(date_str, errors='coerce', utc=True)
    except Exception as e:
        st.warning(f"Error parsing date '{date_str}': {str(e)}")
        return None

@st.cache_data(ttl=300, show_spinner=False)
def procesar_respuesta_historico(data, tipo_activo):
    """
    Procesa la respuesta de la API según el tipo de activo
    """
    if not data:
        return None
    
    try:
        # Para series históricas estándar
        if isinstance(data, list):
            precios = []
            fechas = []
            
            for item in data:
                try:
                    # Manejar diferentes estructuras de respuesta
                    if isinstance(item, dict):
                        precio = item.get('ultimoPrecio') or item.get('precio') or item.get('valor')
                        if not precio or precio == 0:
                            precio = item.get('cierreAnterior') or item.get('precioPromedio') or item.get('apertura')
                        
                        fecha_str = item.get('fechaHora') or item.get('fecha')
                        
                        if precio is not None and precio > 0 and fecha_str:
                            fecha_parsed = parse_datetime_flexible(fecha_str)
                            if pd.notna(fecha_parsed):
                                precios.append(float(precio))
                                fechas.append(fecha_parsed)
                except (ValueError, AttributeError) as e:
                    continue
            
            if precios and fechas:
                df = pd.DataFrame({'fecha': fechas, 'precio': precios})
                # Eliminar duplicados manteniendo el último
                df = df.drop_duplicates(subset=['fecha'], keep='last')
                df = df.sort_values('fecha')
                return df
        
        # Para respuestas que son un solo valor (ej: MEP)
        elif isinstance(data, (int, float)):
            df = pd.DataFrame({'fecha': [pd.Timestamp.now(tz='UTC').date()], 'precio': [float(data)]})
            return df
            
        return None
        
    except Exception as e:
        st.error(f"Error al procesar respuesta histórica: {str(e)}")
        return None

@st.cache_data(ttl=300, show_spinner=False)
def obtener_fondos_comunes(token_portador):
    """
    Obtiene la lista de fondos comunes de inversión disponibles
    """
    url = 'https://api.invertironline.com/api/v2/Titulos/FCI'
    headers = {
        'Authorization': f'Bearer {token_portador}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error al obtener fondos comunes: {str(e)}")
        return []

@st.cache_data(ttl=300, show_spinner=False)
def obtener_serie_historica_fci(token_portador, simbolo, fecha_desde, fecha_hasta):
    """
    Obtiene la serie histórica de un fondo común de inversión
    """
    url = f'https://api.invertironline.com/api/v2/Titulos/FCI/{simbolo}/cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/ajustada'
    headers = {
        'Authorization': f'Bearer {token_portador}',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        # Procesar la respuesta para convertirla al formato esperado
        if isinstance(data, list):
            fechas = []
            precios = []
            for item in data:
                if 'fecha' in item and 'valorCuota' in item:
                    fechas.append(pd.to_datetime(item['fecha']))
                    precios.append(float(item['valorCuota']))
            if fechas and precios:
                return pd.DataFrame({'fecha': fechas, 'precio': precios}).sort_values('fecha')
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error al obtener serie histórica del FCI {simbolo}: {str(e)}")
        return None

@st.cache_data(ttl=300, show_spinner=False)
def obtener_serie_historica_iol(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="SinAjustar"):
    """
    Obtiene la serie histórica de precios para un activo específico desde la API de InvertirOnline.
    
    Args:
        token_portador (str): Token de autenticación de la API
        mercado (str): Mercado del activo (ej: 'BCBA', 'NYSE', 'NASDAQ')
        simbolo (str): Símbolo del activo
        fecha_desde (str): Fecha de inicio en formato 'YYYY-MM-DD'
        fecha_hasta (str): Fecha de fin en formato 'YYYY-MM-DD'
        ajustada (str): Tipo de ajuste ('Ajustada' o 'SinAjustar')
        
    Returns:
        pd.DataFrame: DataFrame con las columnas 'fecha' y 'precio', o None en caso de error
    """
    try:
        print(f"Obteniendo datos para {simbolo} en {mercado} desde {fecha_desde} hasta {fecha_hasta}")
        
        # Endpoint para FCIs (manejo especial)
        if mercado.upper() == 'FCI':
            print("Es un FCI, usando función específica")
            return obtener_serie_historica_fci(token_portador, simbolo, fecha_desde, fecha_hasta)
        
        # Construir URL según el tipo de activo y mercado
        url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
        print(f"URL de la API: {url.split('?')[0]}")  # Mostrar URL sin parámetros sensibles
        
        headers = {
            'Authorization': 'Bearer [TOKEN]',  # No mostrar el token real
            'Accept': 'application/json'
        }
        
        # Realizar la solicitud
        response = requests.get(url, headers={
            'Authorization': f'Bearer {token_portador}',
            'Accept': 'application/json'
        }, timeout=30)
        
        # Verificar el estado de la respuesta
        print(f"Estado de la respuesta: {response.status_code}")
        response.raise_for_status()
        
        # Procesar la respuesta
        data = response.json()
        print(f"Tipo de datos recibidos: {type(data)}")
        
        # Procesar la respuesta según el formato esperado
        if isinstance(data, list):
            print(f"Se recibió una lista con {len(data)} elementos")
            if data:
                print(f"Primer elemento: {data[0]}")
                
            # Formato estándar para series históricas
            fechas = []
            precios = []
            
            for item in data:
                try:
                    # Manejar diferentes formatos de fecha
                    fecha_str = item.get('fecha') or item.get('fechaHora')
                    if not fecha_str:
                        print(f"  - Item sin fecha: {item}")
                        continue
                        
                    # Manejar diferentes formatos de precio
                    precio = item.get('ultimoPrecio') or item.get('precioCierre') or item.get('precio')
                    if precio is None:
                        print(f"  - Item sin precio: {item}")
                        continue
                        
                    # Convertir fecha
                    try:
                        fecha = parse_datetime_flexible(fecha_str)
                        if pd.isna(fecha):
                            print(f"  - Fecha inválida: {fecha_str}")
                            continue
                            
                        precio_float = float(precio)
                        if precio_float <= 0:
                            print(f"  - Precio inválido: {precio}")
                            continue
                            
                        fechas.append(fecha)
                        precios.append(precio_float)
                        
                    except (ValueError, TypeError) as e:
                        print(f"  - Error al convertir datos: {e}")
                        continue
                        
                except Exception as e:
                    print(f"  - Error inesperado al procesar item: {e}")
                    continue
            
            if fechas and precios:
                df = pd.DataFrame({'fecha': fechas, 'precio': precios})
                df = df.drop_duplicates(subset=['fecha'], keep='last')
                df = df.sort_values('fecha')
                print(f"Datos procesados: {len(df)} registros válidos")
                return df
            else:
                print("No se encontraron datos válidos en la respuesta")
                return None
                
        elif isinstance(data, dict):
            print(f"Se recibió un diccionario: {data.keys()}")
            # Para respuestas que son un solo valor (ej: MEP)
            precio = data.get('ultimoPrecio') or data.get('precioCierre') or data.get('precio')
            if precio is not None:
                print(f"Datos de un solo punto: precio={precio}")
                return pd.DataFrame({
                    'fecha': [pd.Timestamp.now(tz='UTC')],
                    'precio': [float(precio)]
                })
            else:
                print("No se encontró precio en la respuesta")
        else:
            print(f"Tipo de respuesta no manejado: {type(data)}")
            
        print(f"No se pudieron procesar los datos para {simbolo} en {mercado}")
        return None
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error de conexión para {simbolo} en {mercado}: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" - Status: {e.response.status_code}"
            try:
                error_msg += f" - Respuesta: {e.response.text[:200]}"
            except:
                pass
        print(error_msg)
        st.warning(error_msg)
        return None
    except Exception as e:
        error_msg = f"Error inesperado al procesar {simbolo} en {mercado}: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        st.error(error_msg)
        return None
        return None

@st.cache_data(ttl=300, show_spinner=False)
def obtener_serie_historica_fci(token_portador, simbolo, fecha_desde, fecha_hasta):
    """
    Obtiene la serie histórica de un Fondo Común de Inversión.
    
    Args:
        token_portador (str): Token de autenticación
        simbolo (str): Símbolo del FCI
        fecha_desde (str): Fecha de inicio (YYYY-MM-DD)
        fecha_hasta (str): Fecha de fin (YYYY-MM-DD)
        
    Returns:
        pd.DataFrame: DataFrame con columnas 'fecha' y 'precio', o None si hay error
    """
    try:
        # Primero intentar obtener directamente la serie histórica
        url_serie = f"https://api.invertironline.com/api/v2/Titulos/FCI/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/SinAjustar"
        headers = {
            'Authorization': f'Bearer {token_portador}',
            'Accept': 'application/json'
        }
        
        response = requests.get(url_serie, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Procesar la respuesta según el formato esperado
        if isinstance(data, list):
            fechas = []
            precios = []
            
            for item in data:
                try:
                    # Manejar diferentes formatos de fecha
                    fecha_str = item.get('fecha') or item.get('fechaHora')
                    if not fecha_str:
                        continue
                        
                    # Obtener el valor de la cuota (puede venir en diferentes campos)
                    precio = item.get('valorCuota') or item.get('precio') or item.get('ultimoPrecio')
                    if not precio:
                        continue
                        
                    # Convertir fecha
                    fecha = parse_datetime_flexible(fecha_str)
                    if not pd.isna(fecha):
                        fechas.append(fecha)
                        precios.append(float(precio))
                        
                except (ValueError, TypeError, AttributeError) as e:
                    continue
            
            if fechas and precios:
                df = pd.DataFrame({'fecha': fechas, 'precio': precios})
                df = df.drop_duplicates(subset=['fecha'], keep='last')
                df = df.sort_values('fecha')
                return df
        
        # Si no se pudo obtener la serie histórica, intentar obtener el último valor
        try:
            # Obtener información del FCI
            url_fci = "https://api.invertironline.com/api/v2/Titulos/FCI"
            response = requests.get(url_fci, headers=headers, timeout=30)
            response.raise_for_status()
            fc_data = response.json()
            
            # Buscar el FCI por símbolo
            fci = next((f for f in fc_data if f.get('simbolo') == simbolo), None)
            if fci and 'ultimoValorCuotaParte' in fci:
                return pd.DataFrame({
                    'fecha': [pd.Timestamp.now(tz='UTC')],
                    'precio': [float(fci['ultimoValorCuotaParte'])]
                })
        except Exception:
            pass
        
        st.warning(f"No se pudieron obtener datos históricos para el FCI {simbolo}")
        return None
        
    except requests.exceptions.RequestException as e:
        st.warning(f"Error de conexión al obtener datos del FCI {simbolo}: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error inesperado al procesar el FCI {simbolo}: {str(e)}")
        return None

@st.cache_data(ttl=300, show_spinner=False)
def get_historical_data_for_optimization(token_portador, activos, fecha_desde, fecha_hasta):
    """
    Obtiene datos históricos para optimización usando el mercado específico de cada activo.
    
    Args:
        token_portador: Token de autenticación Bearer
        activos: Lista de diccionarios, cada uno con {'simbolo': str, 'mercado': str}
        fecha_desde: Fecha inicio (YYYY-MM-DD)
        fecha_hasta: Fecha fin (YYYY-MM-DD)
    
    Returns:
        Dict con DataFrames históricos por símbolo
    """
    datos_historicos = {}
    
    with st.spinner('Obteniendo datos históricos...'):
        for activo in activos:
            simbolo = activo.get('simbolo')
            mercado = activo.get('mercado')

            if not simbolo or not mercado:
                st.warning(f"Activo inválido, se omite: {activo}")
                continue

            df = obtener_serie_historica_iol(
                token_portador,
                mercado.upper(),
                simbolo,
                fecha_desde,
                fecha_hasta
            )
            
            if df is not None and not df.empty:
                datos_historicos[simbolo] = df
            else:
                st.warning(f"No se pudieron obtener datos para {simbolo} en el mercado {mercado}")
                
    return datos_historicos if datos_historicos else None

# --- Enhanced Portfolio Management Classes ---
class manager:
    def __init__(self, rics, notional, data):
        self.rics = rics
        self.notional = notional
        self.data = data
        self.timeseries = None
        self.returns = None
        self.cov_matrix = None
        self.mean_returns = None
        self.risk_free_rate = 0.40  # Tasa libre de riesgo anual para Argentina

    def load_intraday_timeseries(self, ticker):
        return self.data[ticker]

    def synchronise_timeseries(self):
        dic_timeseries = {}
        for ric in self.rics:
            if ric in self.data:
                dic_timeseries[ric] = self.load_intraday_timeseries(ric)
        self.timeseries = dic_timeseries

    def compute_covariance(self):
        self.synchronise_timeseries()
        # Calcular retornos logarítmicos
        returns_matrix = {}
        for ric in self.rics:
            if ric in self.timeseries:
                prices = self.timeseries[ric]
                returns_matrix[ric] = np.log(prices / prices.shift(1)).dropna()
        
        # Convertir a DataFrame para alinear fechas
        self.returns = pd.DataFrame(returns_matrix)
        
        # Calcular matriz de covarianza y retornos medios
        self.cov_matrix = self.returns.cov() * 252  # Anualizar
        self.mean_returns = self.returns.mean() * 252  # Anualizar
        
        return self.cov_matrix, self.mean_returns

    def compute_portfolio(self, portfolio_type=None, target_return=None):
        if self.cov_matrix is None:
            self.compute_covariance()
            
        n_assets = len(self.rics)
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        if portfolio_type == 'min-variance-l1':
            # Minimizar varianza con restricción L1
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'ineq', 'fun': lambda x: 1 - np.sum(np.abs(x))}
            ]
            
        elif portfolio_type == 'min-variance-l2':
            # Minimizar varianza con restricción L2
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'ineq', 'fun': lambda x: 1 - np.sum(x**2)}
            ]
            
        elif portfolio_type == 'equi-weight':
            # Pesos iguales
            weights = np.ones(n_assets) / n_assets
            return self._create_output(weights)
            
        elif portfolio_type == 'long-only':
            # Optimización long-only estándar
            constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
            
        elif portfolio_type == 'markowitz':
            if target_return is not None:
                # Optimización con retorno objetivo
                constraints = [
                    {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                    {'type': 'eq', 'fun': lambda x: np.sum(self.mean_returns * x) - target_return}
                ]
            else:
                # Maximizar Sharpe Ratio
                constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
                def neg_sharpe_ratio(weights):
                    port_ret = np.sum(self.mean_returns * weights)
                    port_vol = np.sqrt(portfolio_variance(weights, self.cov_matrix))
                    if port_vol == 0:
                        return np.inf
                    return -(port_ret - self.risk_free_rate) / port_vol
                result = op.minimize(
                    neg_sharpe_ratio,
                    x0=np.ones(n_assets)/n_assets,
                    method='SLSQP',
                    bounds=bounds,
                    constraints=constraints
                )
                return self._create_output(result.x)

        # Si constraints no está definido, lanzar error
        if 'constraints' not in locals():
            raise ValueError(f"Tipo de portafolio no soportado o constraints no definidos para: {portfolio_type}")

        # Optimización general de varianza mínima
        result = op.minimize(
            lambda x: portfolio_variance(x, self.cov_matrix),
            x0=np.ones(n_assets)/n_assets,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        return self._create_output(result.x)
        
    def _create_output(self, weights):
        """
        Crea un objeto de salida para la cartera con los pesos dados.
        
        Args:
            weights (np.array): Vector de pesos de la cartera
            
        Returns:
            output: Objeto con la cartera optimizada
        """
        # Calcular retornos de la cartera
        portfolio_returns = self.returns.dot(weights)
        
        # Crear objeto de salida
        port_output = output(portfolio_returns, self.notional)
        port_output.weights = dict(zip(self.rics, weights))
        
        # Crear DataFrame con la asignación
        allocation = pd.DataFrame({
            'Activo': self.rics,
            'Peso': weights,
            'Retorno Anual': self.mean_returns * 252 if self.mean_returns is not None else [0] * len(weights)
        })
        port_output.dataframe_allocation = allocation
        
        return port_output

class output:
    def __init__(self, returns, notional):
        self.returns = returns
        self.notional = notional
        self.mean_daily = np.mean(returns)
        self.volatility_daily = np.std(returns)
        self.sharpe_ratio = self.mean_daily / self.volatility_daily if self.volatility_daily > 0 else 0
        self.var_95 = np.percentile(returns, 5)
        self.skewness = stats.skew(returns)
        self.kurtosis = stats.kurtosis(returns)
        self.jb_stat, self.p_value = stats.jarque_bera(returns)
        self.is_normal = self.p_value > 0.05
        self.decimals = 4
        self.str_title = 'Portfolio Returns'
        self.volatility_annual = self.volatility_daily * np.sqrt(252)
        self.return_annual = self.mean_daily * 252
        
        # Placeholders que serán actualizados por el manager
        self.weights = None
        self.dataframe_allocation = None

    def get_metrics_dict(self):
        """Retorna métricas del portafolio en formato diccionario"""
        return {
            'Mean Daily': self.mean_daily,
            'Volatility Daily': self.volatility_daily,
            'Sharpe Ratio': self.sharpe_ratio,
            'VaR 95%': self.var_95,
            'Skewness': self.skewness,
            'Kurtosis': self.kurtosis,
            'JB Statistic': self.jb_stat,
            'P-Value': self.p_value,
            'Is Normal': self.is_normal,
            'Annual Return': self.return_annual,
            'Annual Volatility': self.volatility_annual
        }

    def plot_histogram_streamlit(self, title="Distribución de Retornos"):
        """Crea un histograma de retornos usando Plotly para Streamlit"""
        if self.returns is None or len(self.returns) == 0:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos suficientes para mostrar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(title=title)
            return fig
        
        fig = go.Figure(data=[go.Histogram(
            x=self.returns,
            nbinsx=30,
            name="Retornos del Portafolio",
            marker_color='#0d6efd'
        )])
        
        # Agregar líneas de métricas importantes
        fig.add_vline(x=self.mean_daily, line_dash="dash", line_color="red", 
                     annotation_text=f"Media: {self.mean_daily:.4f}")
        fig.add_vline(x=self.var_95, line_dash="dash", line_color="orange", 
                     annotation_text=f"VaR 95%: {self.var_95:.4f}")
        
        fig.update_layout(
            title=f"{title}",
            xaxis_title="Retorno",
            yaxis_title="Frecuencia",
            showlegend=False,
            template='plotly_white'
        )
        
        return fig

def portfolio_variance(x, mtx_var_covar):
    """Calcula la varianza del portafolio"""
    variance = np.matmul(np.transpose(x), np.matmul(mtx_var_covar, x))
    return variance

def compute_efficient_frontier(rics, notional, target_return, include_min_variance, data):
    """
    Computa la frontera eficiente y portafolios especiales
    
    Args:
        rics: Lista de símbolos de activos
        notional: Valor nominal del portafolio
        target_return: Retorno objetivo para el portafolio de Markowitz
        include_min_variance: Si incluir el portafolio de mínima varianza
        data: Datos históricos de precios
        
    Returns:
        tuple: (portfolios, valid_returns, volatilities) donde:
            - portfolios: Diccionario con los portafolios especiales
            - valid_returns: Lista de retornos válidos para la frontera eficiente
            - volatilities: Lista de volatilidades correspondientes a los retornos válidos
    """
    # Etiquetas para los portafolios especiales
    label1 = 'min-variance-l1'
    label2 = 'min-variance-l2'
    label3 = 'equi-weight'
    label4 = 'long-only'
    label5 = 'markowitz-max-sharpe'
    label6 = 'markowitz-target'
    
    try:
        # Inicializar el gestor de portafolio
        port_mgr = manager(rics, notional, data)
        port_mgr.compute_covariance()
        
        # Calcular retornos y volatilidades para la frontera eficiente
        min_returns = np.min(port_mgr.mean_returns)
        max_returns = np.max(port_mgr.mean_returns)
        target_returns = min_returns + np.linspace(0.05, 0.95, 20) * (max_returns - min_returns)
        
        volatilities = []
        valid_returns = []
        
        # Calcular la frontera eficiente
        for ret in target_returns:
            try:
                port = port_mgr.compute_portfolio('markowitz', ret)
                if port and hasattr(port, 'volatility_annual'):
                    volatilities.append(port.volatility_annual)
                    valid_returns.append(ret)
            except Exception as e:
                print(f"Error calculando portafolio para retorno {ret}: {str(e)}")
                continue
        
        # Calcular portafolios especiales
        portfolios = {}
        
        # 1. Portafolio de mínima varianza L1
        try:
            portfolios[label1] = port_mgr.compute_portfolio('min-variance-l1')
        except Exception as e:
            print(f"Error calculando {label1}: {str(e)}")
            portfolios[label1] = None
            
        # 2. Portafolio de mínima varianza L2
        try:
            portfolios[label2] = port_mgr.compute_portfolio('min-variance-l2')
        except Exception as e:
            print(f"Error calculando {label2}: {str(e)}")
            portfolios[label2] = None
            
        # 3. Portafolio de pesos iguales
        try:
            portfolios[label3] = port_mgr.compute_portfolio('equi-weight')
        except Exception as e:
            print(f"Error calculando {label3}: {str(e)}")
            portfolios[label3] = None
            
        # 4. Portafolio long-only
        try:
            portfolios[label4] = port_mgr.compute_portfolio('long-only')
        except Exception as e:
            print(f"Error calculando {label4}: {str(e)}")
            portfolios[label4] = None
            
        # 5. Portafolio de máximo ratio de Sharpe
        try:
            portfolios[label5] = port_mgr.compute_portfolio('markowitz')  # Max Sharpe
        except Exception as e:
            print(f"Error calculando {label5}: {str(e)}")
            portfolios[label5] = None
            
        # 6. Portafolio de Markowitz con retorno objetivo
        try:
            if target_return is not None:
                portfolios[label6] = port_mgr.compute_portfolio('markowitz', target_return)
            else:
                portfolios[label6] = None
        except Exception as e:
            print(f"Error calculando {label6}: {str(e)}")
            portfolios[label6] = None
            
        return portfolios, valid_returns, volatilities
        
    except Exception as e:
        print(f"Error en compute_efficient_frontier: {str(e)}")
        # Devolver valores por defecto en caso de error
        return {
            label1: None,
            label2: None,
            label3: None,
            label4: None,
            label5: None,
            label6: None
        }, [], []
    
    return portfolios, valid_returns, volatilities

class PortfolioManager:
    def __init__(self, activos, token, fecha_desde, fecha_hasta, capital=100000):
        self.activos = activos
        self.token = token
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.data_loaded = False
        self.returns = None
        self.prices = None
        self.volumes = None
        self.notional = capital  # Valor nominal definido por el usuario
        self.manager = None
        self.garch_models = {}
        self.monte_carlo_results = {}
        self.volatility_forecasts = {}
    
    def analyze_volatility(self, symbol, returns, volumes=None, n_simulations=1000, n_days=30):
        """
        Analiza la volatilidad usando GARCH y simulación de Monte Carlo
        
        Args:
            symbol (str): Símbolo del activo
            returns (pd.Series): Serie de retornos
            volumes (pd.Series, optional): Serie de volúmenes
            n_simulations (int): Número de simulaciones Monte Carlo (default: 1000)
            n_days (int): Número de días a pronosticar (default: 30)
            
        Returns:
            dict: Resultados del análisis de volatilidad
        """
        try:
            # Asegurarse de que no haya valores NaN
            returns = returns.dropna()
            if len(returns) < 30:  # Mínimo de datos para un análisis significativo
                st.warning(f"No hay suficientes datos para analizar la volatilidad de {symbol}")
                return None
                
            # 1. Ajustar modelo GARCH(1,1)
            garch_model = arch_model(
                returns * 100,  # Multiplicar por 100 para mejorar la convergencia
                vol='Garch',
                p=1,
                q=1,
                dist='normal'
            )
            
            # Ajustar el modelo con supresión de salida
            with st.spinner(f"Ajustando modelo GARCH para {symbol}..."):
                garch_fit = garch_model.fit(disp='off')
                
            self.garch_models[symbol] = garch_fit
            
            # 2. Pronóstico de volatilidad
            forecast = garch_fit.forecast(horizon=5)
            forecast_volatility = np.sqrt(forecast.variance.iloc[-1] / 100)  # Deshacer el escalado
            
            # 3. Simulación de Monte Carlo
            last_price = returns.iloc[-1] if hasattr(returns, 'iloc') else 1.0
            last_vol = np.sqrt(garch_fit.conditional_volatility.iloc[-1] / 100)
            
            # Inicializar matrices para almacenar resultados
            price_paths = np.zeros((n_simulations, n_days))
            returns_paths = np.zeros((n_simulations, n_days))
            
            # Mostrar barra de progreso para simulaciones
            progress_bar = st.progress(0)
            progress_text = st.empty()
            
            # Simular trayectorias de precios
            for i in range(n_simulations):
                # Actualizar barra de progreso
                if i % 100 == 0:
                    progress = (i + 1) / n_simulations
                    progress_bar.progress(progress)
                    progress_text.text(f"Simulando trayectorias: {i+1}/{n_simulations}")
                
                # Generar retornos aleatorios con la volatilidad estimada
                daily_returns = np.random.normal(
                    loc=returns.mean(),
                    scale=last_vol,
                    size=n_days
                )
                
                # Asegurar que los retornos sean razonables
                daily_returns = np.clip(daily_returns, -0.3, 0.3)
                
                # Calcular trayectoria de precios
                price_path = last_price * (1 + daily_returns).cumprod()
                
                # Almacenar resultados
                price_paths[i] = price_path
                returns_paths[i] = daily_returns
            
            # Limpiar barra de progreso
            progress_bar.empty()
            progress_text.empty()
            
            # Calcular métricas de la simulación
            final_prices = price_paths[:, -1]
            expected_return = final_prices.mean() / last_price - 1
            expected_volatility = returns_paths.std(axis=1).mean()
            
            # Calcular métricas de riesgo
            var_95 = np.percentile(returns_paths, 5)
            cvar_95 = returns_paths[returns_paths <= var_95].mean()
            
            # Calcular drawdowns simulados
            max_drawdowns = []
            for path in price_paths:
                peak = path[0]
                max_dd = 0
                for price in path:
                    if price > peak:
                        peak = price
                    dd = (peak - price) / peak
                    if dd > max_dd:
                        max_dd = dd
                max_drawdowns.append(max_dd)
            
            avg_max_drawdown = np.mean(max_drawdowns)
            
            # Almacenar resultados
            self.monte_carlo_results[symbol] = {
                'price_paths': price_paths,
                'returns_paths': returns_paths,
                'expected_return': expected_return,
                'expected_volatility': expected_volatility,
                'var_95': var_95,
                'cvar_95': cvar_95,
                'max_drawdown': avg_max_drawdown,
                'last_price': last_price,
                'forecast_dates': [pd.Timestamp.now() + pd.Timedelta(days=i+1) for i in range(n_days)],
                'simulation_date': pd.Timestamp.now()
            }
            
            # Mostrar resumen de métricas
            st.success(f"Análisis de volatilidad completado para {symbol}")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Retorno Esperado", f"{expected_return*100:.2f}%")
            with col2:
                st.metric("Volatilidad Esperada", f"{expected_volatility*100:.2f}%")
            with col3:
                st.metric("VaR 95% (1 día)", f"{var_95*100:.2f}%")
            with col4:
                st.metric("Drawdown Máx. Promedio", f"{avg_max_drawdown*100:.2f}%")
            
            return {
                'garch_model': garch_fit,
                'forecast_volatility': forecast_volatility,
                'monte_carlo': self.monte_carlo_results[symbol]
            }
            
        except Exception as e:
            st.error(f"Error en el análisis de volatilidad para {symbol}: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return None

    def plot_volatility_analysis(self, symbol):
        """
        Genera gráficos para el análisis de volatilidad
        """
        if symbol not in self.monte_carlo_results:
            st.warning(f"No hay datos de análisis de volatilidad para {symbol}")
            return
            
        mc_result = self.monte_carlo_results[symbol]
        
        # Crear figura con subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Trayectorias de Precio Simuladas',
                'Distribución de Retornos Esperados',
                'Volatilidad Pronosticada',
                'Riesgo (VaR)'
            ),
            specs=[[{"secondary_y": True}, {}],
                 [{"secondary_y": True}, {}]]
        )
        
        # 1. Trayectorias de precios simuladas
        for i in range(min(100, len(mc_result['price_paths']))):
            fig.add_trace(
                go.Scatter(
                    x=mc_result['forecast_dates'],
                    y=mc_result['price_paths'][i],
                    line=dict(color='rgba(0, 100, 255, 0.1)'),
                    showlegend=False
                ),
                row=1, col=1
            )
        
        # Añadir media y percentiles
        mean_prices = np.mean(mc_result['price_paths'], axis=0)
        p5 = np.percentile(mc_result['price_paths'], 5, axis=0)
        p95 = np.percentile(mc_result['price_paths'], 95, axis=0)
        
        fig.add_trace(
            go.Scatter(
                x=mc_result['forecast_dates'],
                y=mean_prices,
                line=dict(color='red', width=2),
                name='Media'
            ),
            row=1, col=1, secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=mc_result['forecast_dates'],
                y=p5,
                line=dict(color='green', width=1, dash='dash'),
                name='Percentil 5%'
            ),
            row=1, col=1, secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=mc_result['forecast_dates'],
                y=p95,
                line=dict(color='blue', width=1, dash='dash'),
                name='Percentil 95%'
            ),
            row=1, col=1, secondary_y=False
        )
        
        # 2. Histograma de retornos
        final_returns = (mc_result['price_paths'][:, -1] / mc_result['last_price'] - 1) * 100
        fig.add_trace(
            go.Histogram(
                x=final_returns,
                nbinsx=50,
                name='Distribución de Retornos',
                marker_color='#1f77b4',
                opacity=0.7
            ),
            row=1, col=2
        )
        
        # Añadir línea para el VaR
        var_95 = np.percentile(final_returns, 5)
        fig.add_vline(
            x=var_95,
            line=dict(color='red', width=2, dash='dash'),
            row=1, col=2,
            annotation_text=f'VaR 95%: {var_95:.2f}%',
            annotation_position='top right'
        )
        
        # 3. Volatilidad pronosticada
        if symbol in self.garch_models:
            garch_fit = self.garch_models[symbol]
            volatilities = np.sqrt(garch_fit.conditional_volatility / 100)  # Deshacer escalado
            
            fig.add_trace(
                go.Scatter(
                    x=self.prices.index[-len(volatilities):],
                    y=volatilities * 100,  # Convertir a porcentaje
                    line=dict(color='purple', width=2),
                    name='Volatilidad Condicional',
                    yaxis='y2'
                ),
                row=2, col=1, secondary_y=False
            )
        
        # 4. Riesgo (VaR)
        var_levels = np.arange(1, 11) * 10  # 10% a 100%
        var_values = [np.percentile(final_returns, level) for level in var_levels]
        
        fig.add_trace(
            go.Bar(
                x=var_levels,
                y=var_values,
                name='Value at Risk',
                marker_color='#ff7f0e'
            ),
            row=2, col=2
        )
        
        # Actualizar diseño
        fig.update_layout(
            title=f'Análisis de Volatilidad - {symbol}',
            showlegend=True,
            height=800,
            template='plotly_dark'
        )
        
        # Actualizar ejes
        fig.update_xaxes(title_text='Fecha', row=1, col=1)
        fig.update_yaxes(title_text='Precio', row=1, col=1)
        fig.update_xaxes(title_text='Retorno (%)', row=1, col=2)
        fig.update_yaxes(title_text='Frecuencia', row=1, col=2)
        fig.update_xaxes(title_text='Fecha', row=2, col=1)
        fig.update_yaxes(title_text='Volatilidad Anualizada (%)', row=2, col=1)
        fig.update_xaxes(title_text='Nivel de Confianza (%)', row=2, col=2)
        fig.update_yaxes(title_text='Pérdida Máxima Esperada (%)', row=2, col=2)
        
        return fig
        
    def load_data(self):
        # Convertir lista de activos a formato adecuado
        symbols = []
        markets = []
        tipos = []
        
        # Función auxiliar para detectar mercado
        def detectar_mercado(tipo_raw: str, mercado_raw: str) -> str:
            """
            Determina el mercado basado en la información proporcionada.
            
            Args:
                tipo_raw: Tipo de activo (ej: 'Acciones', 'Bonos', 'Cedears')
                mercado_raw: Mercado del activo (ej: 'BCBA', 'NYSE', 'NASDAQ')
                
            Returns:
                str: Mercado normalizado para la API
            """
            # Mapeo de mercados comunes
            mercado = str(mercado_raw).upper()
            
            # Si el mercado está vacío, intentar deducirlo del tipo
            if not mercado or mercado == 'NONE':
                tipo = str(tipo_raw).lower()
                if 'cedear' in tipo:
                    return 'BCBA'  # Asumir que los CEDEARs son de BCBA
                elif 'bono' in tipo or 'letra' in tipo or 'obligacion' in tipo:
                    return 'BCBA'  # Asumir bonos en BCBA
                elif 'accion' in tipo:
                    return 'BCBA'  # Asumir acciones en BCBA por defecto
                else:
                    return 'BCBA'  # Valor por defecto
                    
            # Normalizar mercados conocidos
            mercado_map = {
                'BCBA': 'BCBA',
                'BYMA': 'BCBA',
                'ROFEX': 'ROFEX',
                'NYSE': 'NYSE',
                'NASDAQ': 'NASDAQ',
                'AMEX': 'AMEX',
                'BME': 'BME',
                'BVC': 'BVC',
                'BVL': 'BVL',
                'B3': 'B3',
                'BVMF': 'BVMF',
                'EURONEXT': 'EURONEXT',
                'LSE': 'LSE',
                'FWB': 'FWB',
                'SWX': 'SWX',
                'TSX': 'TSX',
                'TSXV': 'TSXV',
                'ASX': 'ASX',
                'NSE': 'NSE',
                'BSE': 'BSE',
                'TSE': 'TSE',
                'HKEX': 'HKEX',
                'SSE': 'SSE',
                'SZSE': 'SZSE',
                'KRX': 'KRX',
                'TASE': 'TASE',
                'MOEX': 'MOEX',
                'JSE': 'JSE'
            }
            
            return mercado_map.get(mercado, 'BCBA')  # Default a BCBA si no se reconoce
            
        # Procesar cada activo
        for activo in self.activos:
            if 'simbolo' not in activo:
                continue
                
            simbolo = activo['simbolo']
            tipo = activo.get('tipo', '')
            mercado = activo.get('mercado', '')
            
            # Determinar mercado
            mercado_normalizado = detectar_mercado(tipo, mercado)
            
            # Agregar a las listas
            symbols.append(simbolo)
            markets.append(mercado_normalizado)
            tipos.append(tipo)
        
        # Obtener datos históricos
        try:
            historical_data = get_historical_data_for_optimization(
                self.token,
                [{'simbolo': s, 'mercado': m} for s, m in zip(symbols, markets)],
                self.fecha_desde,
                self.fecha_hasta
            )
            
            if not historical_data:
                st.error("No se pudieron cargar los datos históricos")
                return False
                
            # Procesar datos en un DataFrame
            prices = pd.DataFrame()
            volumes = pd.DataFrame()
            
            for symbol, data in historical_data.items():
                if data is not None and not data.empty:
                    prices[symbol] = data['precio']
                    if 'volumen' in data.columns:
                        volumes[symbol] = data['volumen']
            
            # Calcular retornos
            returns = prices.pct_change().dropna()
            
            # Guardar datos
            self.prices = prices
            self.returns = returns
            if not volumes.empty:
                self.volumes = volumes
                
            self.data_loaded = True
            return True
            
        except Exception as e:
            st.error(f"Error al cargar datos: {str(e)}")
            st.exception(e)
            return False

    def compute_portfolio(self, strategy='max_sharpe', target_return=None):
        """
        Calcula la cartera óptima según la estrategia especificada.
        
        Args:
            strategy (str): Estrategia de optimización ('max_sharpe', 'min_vol', 'equi-weight')
            target_return (float, optional): Retorno objetivo para estrategias que lo requieran
            
        Returns:
            output: Objeto output con la cartera optimizada o None en caso de error
        """
        if not self.data_loaded or self.returns is None or self.returns.empty:
            st.error("No hay datos de retornos disponibles")
            return None
            
        try:
            # Inicializar el manager si no existe
            if not hasattr(self, 'manager') or not self.manager:
                self.manager = manager(
                    rics=self.returns.columns.tolist(),
                    notional=self.notional,
                    data=self.prices.to_dict('series')
                )
                
                # Cargar datos y calcular covarianzas
                self.manager.returns = self.returns
                self.manager.compute_covariance()
                
            # Calcular cartera según estrategia
            if strategy in ['max_sharpe', 'min_vol']:
                try:
                    # Asegurarse de que el manager tenga los retornos y covarianzas
                    if not hasattr(self.manager, 'mean_returns') or self.manager.mean_returns is None:
                        self.manager.mean_returns = self.returns.mean()
                    if not hasattr(self.manager, 'cov_matrix') or self.manager.cov_matrix is None:
                        self.manager.cov_matrix = self.returns.cov()
                    
                    # Mapear estrategias a los tipos de portafolio soportados por el manager
                    portfolio_type = 'markowitz' if strategy == 'max_sharpe' else 'min-variance-l1'
                    
                    # Calcular la cartera óptima
                    portfolio_output = self.manager.compute_portfolio(
                        portfolio_type=portfolio_type,
                        target_return=target_return
                    )
                    
                    if portfolio_output is None:
                        raise ValueError(f"No se pudo calcular la cartera óptima con la estrategia '{strategy}'")
                        
                except Exception as e:
                    st.warning(f"Error al calcular la cartera {strategy}: {str(e)}. Usando estrategia equi-weight.")
                    n_assets = len(self.returns.columns)
                    weights = np.array([1/n_assets] * n_assets)
                    portfolio_returns = (self.returns * weights).sum(axis=1)
                    portfolio_output = output(portfolio_returns, self.notional)
                    portfolio_output.weights = weights
                    portfolio_output.dataframe_allocation = pd.DataFrame({
                        'rics': list(self.returns.columns),
                        'weights': weights,
                        'volatilities': self.returns.std().values,
                        'returns': self.returns.mean().values
                    })
                
                return portfolio_output
                
            elif strategy == 'equi-weight':
                n_assets = len(self.returns.columns)
                weights = np.array([1/n_assets] * n_assets)
                portfolio_returns = (self.returns * weights).sum(axis=1)
                portfolio_output = output(portfolio_returns, self.notional)
                portfolio_output.weights = weights
                portfolio_output.dataframe_allocation = pd.DataFrame({
                    'rics': list(self.returns.columns),
                    'weights': weights,
                    'volatilities': self.returns.std().values,
                    'returns': self.returns.mean().values
                })
                return portfolio_output
                
            else:
                st.error(f"Estrategia no soportada: {strategy}")
                return None
                
        except Exception as e:
            st.error(f"Error al calcular la cartera: {str(e)}")
            st.exception(e)
            return None
    
    def compute_efficient_frontier(self, target_return=0.08, include_min_variance=True):
        """Computa la frontera eficiente"""
        if not self.data_loaded or not hasattr(self, 'prices') or self.prices is None:
            st.error("No hay datos de precios disponibles")
            return None, None, None
        
        try:
            portfolios, returns, volatilities = compute_efficient_frontier(
                self.prices.columns.tolist(), 
                self.notional, 
                target_return, 
                include_min_variance,
                self.prices.to_dict('series')
            )
            return portfolios, returns, volatilities
        except Exception as e:
            st.error(f"Error al calcular la frontera eficiente: {str(e)}")
            return None, None, None

# --- Historical Data Methods ---
def _deprecated_serie_historica_iol(*args, **kwargs):
    """Deprecated duplicate of `obtener_serie_historica_iol`. Kept for backward compatibility."""
    return None
    """Obtiene series históricas desde la API de IOL
    
    Args:
        token_portador: Token de autenticación Bearer
        mercado: Mercado (BCBA, NYSE, NASDAQ, ROFEX)
        simbolo: Símbolo del activo (puede ser string o dict con clave 'simbolo')
        fecha_desde: Fecha inicio (YYYY-MM-DD)
        fecha_hasta: Fecha fin (YYYY-MM-DD)
        ajustada: "Ajustada" o "SinAjustar"
    
    Returns:
        DataFrame con datos históricos o None si hay error
    """
    # Manejar caso donde simbolo es un diccionario
    if isinstance(simbolo, dict):
        simbolo = simbolo.get('simbolo', '')
    
    if not simbolo:
        st.warning("No se proporcionó un símbolo válido")
        return None
        
    # Asegurarse de que el mercado esté en mayúsculas
    mercado = mercado.upper() if mercado else 'BCBA'
    try:
        # Construir la URL de la API
        url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token_portador}'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        df = pd.DataFrame(data)
        
        if 'fechaHora' in df.columns:
            # Handle different datetime formats
            df['fecha'] = pd.to_datetime(
                df['fechaHora'], 
                format='mixed',  # Automatically infer format for each element
                utc=True,        # Ensure timezone awareness
                errors='coerce'  # Convert parsing errors to NaT
            ).dt.tz_convert(None).dt.date  # Convert to naive date
            
            # Drop rows where date parsing failed
            df = df.dropna(subset=['fecha'])
            df = df.sort_values('fecha')
            
        return df
        
    except Exception as e:
        st.error(f"Error obteniendo datos para {simbolo}: {str(e)}")
        return None

# --- Portfolio Metrics Function ---
def calcular_metricas_portafolio(portafolio, valor_total, token_portador, dias_historial=252):
    """
    Calcula métricas clave de desempeño para un portafolio de inversión usando datos históricos.
    
    Args:
        portafolio (dict): Diccionario con los activos y sus cantidades
        valor_total (float): Valor total del portafolio
        token_portador (str): Token de autenticación para la API de InvertirOnline
        dias_historial (int): Número de días de histórico a considerar (por defecto: 252 días hábiles)
        
    Returns:
        dict: Diccionario con las métricas calculadas
    """
    if not isinstance(portafolio, dict) or not portafolio or valor_total <= 0:
        return {}

    # Obtener fechas para el histórico
    fecha_hasta = datetime.now().strftime('%Y-%m-%d')
    fecha_desde = (datetime.now() - timedelta(days=dias_historial*1.5)).strftime('%Y-%m-%d')
    
    # 1. Calcular concentración del portafolio (Índice de Herfindahl-Hirschman normalizado)
    if len(portafolio) == 0:
        concentracion = 0
    elif len(portafolio) == 1:
        concentracion = 1.0
    else:
        sum_squares = sum((activo.get('Valuación', 0) / valor_total) ** 2 
                         for activo in portafolio.values())
        # Normalizar entre 0 y 1
        min_concentration = 1.0 / len(portafolio)
        concentracion = (sum_squares - min_concentration) / (1 - min_concentration)
    
    # Inicializar estructuras para cálculos
    retornos_diarios = {}
    metricas_activos = {}
    
    # 2. Obtener datos históricos y calcular métricas por activo
    for simbolo, activo in portafolio.items():
        try:
            # Obtener datos históricos usando el método estándar
            mercado = activo.get('mercado', 'BCBA')
            tipo_activo = activo.get('Tipo', 'Desconocido')
            
            # Debug: Mostrar información del activo que se está procesando
            print(f"\nProcesando activo: {simbolo} (Mercado: {mercado}, Tipo: {tipo_activo})")
            
            # Obtener la serie histórica
            try:
                df_historico = obtener_serie_historica_iol(
                    token_portador=token_portador,
                    mercado=mercado,
                    simbolo=simbolo,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                    ajustada="SinAjustar"
                )
            except Exception as e:
                print(f"Error al obtener datos históricos para {simbolo}: {str(e)}")
                continue
            
            if df_historico is None:
                print(f"No se obtuvieron datos para {simbolo} (None)")
                continue
                
            if df_historico.empty:
                print(f"Datos vacíos para {simbolo}")
                continue
            
            # Asegurarse de que tenemos las columnas necesarias
            if 'fecha' not in df_historico.columns or 'precio' not in df_historico.columns:
                print(f"Faltan columnas necesarias en los datos de {simbolo}")
                print(f"Columnas disponibles: {df_historico.columns.tolist()}")
                continue
                
            print(f"Datos obtenidos: {len(df_historico)} registros desde {df_historico['fecha'].min()} hasta {df_historico['fecha'].max()}")
                
            # Ordenar por fecha y limpiar duplicados
            df_historico = df_historico.sort_values('fecha')
            df_historico = df_historico.drop_duplicates(subset=['fecha'], keep='last')
            
            # Calcular retornos diarios
            df_historico['retorno'] = df_historico['precio'].pct_change()
            
            # Filtrar valores atípicos usando un enfoque más robusto
            if len(df_historico) > 5:  # Necesitamos suficientes puntos para el filtrado
                q_low = df_historico['retorno'].quantile(0.01)
                q_high = df_historico['retorno'].quantile(0.99)
                df_historico = df_historico[
                    (df_historico['retorno'] >= q_low) & 
                    (df_historico['retorno'] <= q_high)
                ]
            
            # Filtrar valores no finitos y asegurar suficientes datos
            retornos_validos = df_historico['retorno'].replace(
                [np.inf, -np.inf], np.nan
            ).dropna()
            
            if len(retornos_validos) < 5:  # Mínimo de datos para métricas confiables
                print(f"No hay suficientes datos válidos para {simbolo} (solo {len(retornos_validos)} registros)")
                continue
                
            # Verificar si hay suficientes variaciones de precio
            if retornos_validos.nunique() < 2:
                print(f"No hay suficiente variación en los precios de {simbolo}")
                continue
            
            # Calcular métricas básicas
            retorno_medio = retornos_validos.mean() * 252  # Anualizado
            volatilidad = retornos_validos.std() * np.sqrt(252)  # Anualizada
            
            # Asegurar valores razonables
            retorno_medio = np.clip(retorno_medio, -5, 5)  # Límite de ±500% anual
            volatilidad = min(volatilidad, 3)  # Límite de 300% de volatilidad
            
            # Calcular métricas de riesgo basadas en la distribución de retornos
            ret_pos = retornos_validos[retornos_validos > 0]
            ret_neg = retornos_validos[retornos_validos < 0]
            n_total = len(retornos_validos)
            
            # Calcular probabilidades
            prob_ganancia = len(ret_pos) / n_total if n_total > 0 else 0.5
            prob_perdida = len(ret_neg) / n_total if n_total > 0 else 0.5
            
            # Calcular probabilidades de movimientos extremos
            prob_ganancia_10 = len(ret_pos[ret_pos > 0.1]) / n_total if n_total > 0 else 0
            prob_perdida_10 = len(ret_neg[ret_neg < -0.1]) / n_total if n_total > 0 else 0
            
            # Calcular el peso del activo en el portafolio
            peso = activo.get('Valuación', 0) / valor_total if valor_total > 0 else 0
            
            # Guardar métricas
            metricas_activos[simbolo] = {
                'retorno_medio': retorno_medio,
                'volatilidad': volatilidad,
                'prob_ganancia': prob_ganancia,
                'prob_perdida': prob_perdida,
                'prob_ganancia_10': prob_ganancia_10,
                'prob_perdida_10': prob_perdida_10,
                'peso': peso
            }
            
            # Guardar retornos para cálculo de correlaciones
            retornos_diarios[simbolo] = df_historico.set_index('fecha')['retorno']
            
        except Exception as e:
            print(f"Error procesando {simbolo}: {str(e)}")
            continue
    
    if not metricas_activos:
        print("No se pudieron calcular métricas para ningún activo")
        return {
            'concentracion': concentracion,
            'std_dev_activo': 0,
            'retorno_esperado_anual': 0,
            'pl_esperado_min': 0,
            'pl_esperado_max': 0,
            'probabilidades': {'perdida': 0, 'ganancia': 0, 'perdida_mayor_10': 0, 'ganancia_mayor_10': 0},
            'riesgo_anual': 0
        }
    else:
        print(f"\nMétricas calculadas para {len(metricas_activos)} activos")
    
    # 3. Calcular métricas del portafolio
    # Retorno esperado ponderado
    retorno_esperado_anual = sum(
        m['retorno_medio'] * m['peso'] 
        for m in metricas_activos.values()
    )
    
    # Volatilidad del portafolio (considerando correlaciones)
    try:
        if len(retornos_diarios) > 1:
            # Asegurarse de que tenemos suficientes datos para calcular correlaciones
            df_retornos = pd.DataFrame(retornos_diarios).dropna()
            if len(df_retornos) < 5:  # Mínimo de datos para correlación confiable
                print("No hay suficientes datos para calcular correlaciones confiables")
                # Usar promedio ponderado simple como respaldo
                volatilidad_portafolio = sum(
                    m['volatilidad'] * m['peso'] 
                    for m in metricas_activos.values()
                )
            else:
                # Calcular matriz de correlación
                df_correlacion = df_retornos.corr()
                
                # Verificar si la matriz de correlación es válida
                if df_correlacion.isna().any().any():
                    print("Advertencia: Matriz de correlación contiene valores NaN")
                    df_correlacion = df_correlacion.fillna(0)  # Reemplazar NaN con 0
                
                # Obtener pesos y volatilidades
                activos = list(metricas_activos.keys())
                pesos = np.array([metricas_activos[a]['peso'] for a in activos])
                volatilidades = np.array([metricas_activos[a]['volatilidad'] for a in activos])
                
                # Asegurar que las dimensiones coincidan
                if len(activos) == df_correlacion.shape[0] == df_correlacion.shape[1]:
                    # Calcular matriz de covarianza
                    matriz_cov = np.diag(volatilidades) @ df_correlacion.values @ np.diag(volatilidades)
                    # Calcular varianza del portafolio
                    varianza_portafolio = pesos.T @ matriz_cov @ pesos
                    # Asegurar que la varianza no sea negativa
                    varianza_portafolio = max(0, varianza_portafolio)
                    volatilidad_portafolio = np.sqrt(varianza_portafolio)
                else:
                    print("Dimensiones no coinciden, usando promedio ponderado")
                    volatilidad_portafolio = sum(v * w for v, w in zip(volatilidades, pesos))
        else:
            # Si solo hay un activo, usar su volatilidad directamente
            volatilidad_portafolio = next(iter(metricas_activos.values()))['volatilidad']
            
        # Asegurar que la volatilidad sea un número finito
        if not np.isfinite(volatilidad_portafolio):
            print("Advertencia: Volatilidad no finita, usando valor por defecto")
            volatilidad_portafolio = 0.2  # Valor por defecto razonable
            
    except Exception as e:
        print(f"Error al calcular volatilidad del portafolio: {str(e)}")
        import traceback
        traceback.print_exc()
        # Valor por defecto seguro
        volatilidad_portafolio = sum(
            m['volatilidad'] * m['peso'] 
            for m in metricas_activos.values()
        ) if metricas_activos else 0.2
    
    # Calcular percentiles para escenarios
    retornos_simulados = []
    for _ in range(1000):  # Simulación Monte Carlo simple
        retorno_simulado = 0
        for m in metricas_activos.values():
            retorno_simulado += np.random.normal(m['retorno_medio']/252, m['volatilidad']/np.sqrt(252)) * m['peso']
        retornos_simulados.append(retorno_simulado * 252)  # Anualizado
    
    pl_esperado_min = np.percentile(retornos_simulados, 5) * valor_total / 100
    pl_esperado_max = np.percentile(retornos_simulados, 95) * valor_total / 100
    
    # Calcular probabilidades basadas en los retornos simulados
    retornos_simulados = np.array(retornos_simulados)
    total_simulaciones = len(retornos_simulados)
            
    prob_ganancia = np.sum(retornos_simulados > 0) / total_simulaciones if total_simulaciones > 0 else 0.5
    prob_perdida = np.sum(retornos_simulados < 0) / total_simulaciones if total_simulaciones > 0 else 0.5
    prob_ganancia_10 = np.sum(retornos_simulados > 0.1) / total_simulaciones
    prob_perdida_10 = np.sum(retornos_simulados < -0.1) / total_simulaciones
            
    probabilidades = {
        'perdida': prob_perdida,
        'ganancia': prob_ganancia,
        'perdida_mayor_10': prob_perdida_10,
        'ganancia_mayor_10': prob_ganancia_10
    }
    
    return {
        'concentracion': concentracion,
        'std_dev_activo': volatilidad_portafolio,
        'retorno_esperado_anual': retorno_esperado_anual,
        'pl_esperado_min': pl_esperado_min,
        'pl_esperado_max': pl_esperado_max,
        'probabilidades': probabilidades,
        'riesgo_anual': volatilidad_portafolio  # Usamos la volatilidad como proxy de riesgo
    }

# --- Funciones de Perfil de Inversor ---

def obtener_preguntas_test_inversor(token_portador: str) -> Optional[dict]:
    """
    Obtiene las preguntas y opciones para el test de perfil de inversor.
    
    Args:
        token_portador (str): Token de autenticación Bearer
        
    Returns:
        dict: Diccionario con las preguntas y opciones del test, o None en caso de error
    """
    url = "https://api.invertironline.com/api/v2/asesores/test-inversor"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_portador}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error al obtener preguntas del test de perfil: {str(e)}")
        return None

def mostrar_formulario_perfil(preguntas: dict) -> dict:
    """
    Muestra el formulario de perfil de inversor y devuelve las respuestas.
    
    Args:
        preguntas (dict): Diccionario con las preguntas y opciones del test
        
    Returns:
        dict: Respuestas del usuario al formulario
    """
    respuestas = {}
    
    st.subheader("📝 Test de Perfil de Inversor")
    
    # Instrumentos en los que ha invertido anteriormente
    if 'instrumentosInvertidosAnteriormente' in preguntas:
        pregunta = preguntas['instrumentosInvertidosAnteriormente']
        opciones = {i['nombre']: i['id'] for i in pregunta['instrumentos']}
        seleccionados = st.multiselect(
            label=pregunta['pregunta'],
            options=opciones.keys(),
            default=[]
        )
        respuestas['instrumentosInvertidosAnteriormente'] = [opciones[s] for s in seleccionados]
    
    # Niveles de conocimiento de instrumentos
    if 'nivelesConocimientoInstrumentos' in preguntas:
        pregunta = preguntas['nivelesConocimientoInstrumentos']
        st.subheader(pregunta['pregunta'])
        conocimientos = {}
        for nivel in pregunta['niveles']:
            opciones = {op['nombre']: op['id'] for op in nivel['opciones']}
            seleccion = st.radio(
                label=nivel['nombre'],
                options=opciones.keys(),
                key=f"conocimiento_{nivel['id']}",
                horizontal=True
            )
            conocimientos[nivel['id']] = opciones[seleccion]
        respuestas['nivelesConocimientoInstrumentos'] = list(conocimientos.values())
    
    # Plazo de inversión
    if 'plazosInversion' in preguntas:
        pregunta = preguntas['plazosInversion']
        opciones = {i['nombre']: i['id'] for i in pregunta['plazos']}
        seleccion = st.radio(
            label=pregunta['pregunta'],
            options=opciones.keys(),
            key="plazo_inversion"
        )
        respuestas['idPlazoElegido'] = opciones[seleccion]
    
    # Edad
    if 'edadesPosibles' in preguntas:
        pregunta = preguntas['edadesPosibles']
        opciones = {i['nombre']: i['id'] for i in pregunta['edades']}
        seleccion = st.radio(
            label=pregunta['pregunta'],
            options=opciones.keys(),
            key="edad"
        )
        respuestas['idEdadElegida'] = opciones[seleccion]
    
    # Objetivo de inversión
    if 'objetivosInversion' in preguntas:
        pregunta = preguntas['objetivosInversion']
        opciones = {i['nombre']: i['id'] for i in pregunta['objetivos']}
        seleccion = st.radio(
            label=pregunta['pregunta'],
            options=opciones.keys(),
            key="objetivo"
        )
        respuestas['idObjetivoInversionElegida'] = opciones[seleccion]
    
    # Pólizas de seguro
    if 'polizasSeguro' in preguntas:
        pregunta = preguntas['polizasSeguro']
        opciones = {i['nombre']: i['id'] for i in pregunta['polizas']}
        seleccion = st.radio(
            label=pregunta['pregunta'],
            options=opciones.keys(),
            key="poliza"
        )
        respuestas['idPolizaElegida'] = opciones[seleccion]
    
    # Capacidad de ahorro
    if 'capacidadesAhorro' in preguntas:
        pregunta = preguntas['capacidadesAhorro']
        opciones = {i['nombre']: i['id'] for i in pregunta['capacidadesAhorro']}
        seleccion = st.radio(
            label=pregunta['pregunta'],
            options=opciones.keys(),
            key="ahorro"
        )
        respuestas['idCapacidadAhorroElegida'] = opciones[seleccion]
    
    # Porcentaje de patrimonio dedicado a inversión
    if 'porcentajesPatrimonioDedicado' in preguntas:
        pregunta = preguntas['porcentajesPatrimonioDedicado']
        opciones = {i['nombre']: i['id'] for i in pregunta['porcentajesPatrimonioDedicado']}
        seleccion = st.radio(
            label=pregunta['pregunta'],
            options=opciones.keys(),
            key="patrimonio"
        )
        respuestas['idPorcentajePatrimonioDedicado'] = opciones[seleccion]
    
    return respuestas

def obtener_perfil_sugerido(token_portador: str, respuestas: dict, id_cliente_asesorado: str = None) -> Optional[dict]:
    """
    Obtiene el perfil de inversión sugerido basado en las respuestas del usuario.
    
    Args:
        token_portador (str): Token de autenticación Bearer
        respuestas (dict): Respuestas del formulario de perfil
        id_cliente_asesorado (str, optional): ID del cliente asesorado si es aplicable
        
    Returns:
        dict: Perfil de inversión sugerido, o None en caso de error
    """
    # Construir la URL según si hay un ID de cliente asesorado o no
    if id_cliente_asesorado:
        url = f"https://api.invertironline.com/api/v2/asesores/test-inversor/{id_cliente_asesorado}"
    else:
        url = "https://api.invertironline.com/api/v2/asesores/test-inversor"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_portador}'
    }
    
    # Preparar el cuerpo de la solicitud
    payload = {
        "enviarEmailCliente": False,
        **respuestas
    }

def seleccionar_activos_aleatorios(perfil: dict, activos_disponibles: Dict[str, list]) -> List[dict]:
    """
    Selecciona activos aleatorios para cada tipo de activo según el perfil.
    
    Args:
        perfil (dict): Perfil de inversión con la composición sugerida
        activos_disponibles (Dict[str, list]): Diccionario con listas de activos por tipo
        
    Returns:
        List[dict]: Lista de activos seleccionados con sus pesos
    """
    cartera = []
    
    if 'perfilSugerido' not in perfil or 'perfilComposiciones' not in perfil['perfilSugerido']:
        st.warning("No se encontró información de composición en el perfil")
        return []
    
    # Mapeo de tipos de activos a claves en activos_disponibles
    tipo_a_clave = {
        'acciones': ['acciones', 'equity', 'stocks'],
        'bonos': ['bonos', 'bonds', 'obligaciones'],
        'fondos': ['fondos', 'fci', 'fondos_comunes'],
        'cauciones': ['cauciones', 'repos', 'repos'],
        'plazo fijo': ['plazofijo', 'plazo_fijo', 'pf']
    }
    
    for composicion in perfil['perfilSugerido']['perfilComposiciones']:
        tipo_activo = composicion['nombre'].lower()
        porcentaje = composicion['porcentaje'] / 100.0  # Convertir a fracción
        
        # Buscar activos disponibles para este tipo
        activos_tipo = []
        
        # Buscar por coincidencia exacta primero
        if tipo_activo in activos_disponibles:
            activos_tipo = activos_disponibles[tipo_activo]
        else:
            # Si no hay coincidencia exacta, buscar por palabras clave
            for key, keywords in tipo_a_clave.items():
                if any(kw in tipo_activo for kw in keywords):
                    if key in activos_disponibles:
                        activos_tipo = activos_disponibles[key]
                        break
        
        # Si aún no encontramos activos, intentar coincidencias parciales
        if not activos_tipo:
            for key in activos_disponibles:
                if any(kw in tipo_activo for kw in key.lower().split()):
                    activos_tipo = activos_disponibles[key]
                    break
        
        # Si encontramos activos, seleccionar uno al azar
        if activos_tipo:
            activo_seleccionado = random.choice(activos_tipo)
            cartera.append({
                'tipo_activo': tipo_activo,
                'activo': activo_seleccionado,
                'porcentaje': porcentaje
            })
    
    return cartera

def mostrar_cartera_recomendada(cartera: List[dict], capital_total: float):
    """
    Muestra la cartera recomendada en un formato amigable.
    
    Args:
        cartera (List[dict]): Lista de activos con sus pesos
        capital_total (float): Capital total a invertir
    """
    if not cartera:
        st.warning("No se pudo generar una cartera con los parámetros proporcionados.")
        return
    
    st.subheader("📊 Cartera Recomendada")
    
    # Crear DataFrame para mostrar la cartera
    df_cartera = pd.DataFrame([{
        'Tipo de Activo': item['tipo_activo'].title(),
        'Activo': item['activo'],
        'Porcentaje': f"{item['porcentaje']*100:.1f}%",
        'Monto': f"${item['porcentaje'] * capital_total:,.2f}"
    } for item in cartera])
    
    # Mostrar tabla con la cartera
    st.dataframe(
        df_cartera,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Tipo de Activo': st.column_config.TextColumn("Tipo de Activo"),
            'Activo': st.column_config.TextColumn("Activo"),
            'Porcentaje': st.column_config.TextColumn("Asignación"),
            'Monto': st.column_config.TextColumn("Monto")
        }
    )
    
    # Mostrar gráfico de torta
    fig = px.pie(
        df_cartera, 
        values='Porcentaje', 
        names='Tipo de Activo',
        title='Distribución de la Cartera por Tipo de Activo',
        labels={'Porcentaje': 'Porcentaje', 'Tipo de Activo': 'Tipo de Activo'}
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

def mostrar_test_perfil_inversor(token_portador: str, id_cliente: str = None):
    """
    Muestra el test de perfil de inversor y la cartera recomendada.
    
    Args:
        token_portador (str): Token de autenticación
        id_cliente (str, optional): ID del cliente si es aplicable
    """
    st.header("📝 Test de Perfil de Inversor")
    
    # Obtener preguntas del test
    if 'preguntas_test' not in st.session_state:
        with st.spinner("Cargando preguntas del test..."):
            preguntas = obtener_preguntas_test_inversor(token_portador)
            if preguntas:
                st.session_state.preguntas_test = preguntas
                st.session_state.test_completado = False
            else:
                st.error("No se pudieron cargar las preguntas del test. Intente nuevamente.")
                return
    
    # Mostrar formulario si no se ha completado el test
    if not st.session_state.get('test_completado', False):
        respuestas = mostrar_formulario_perfil(st.session_state.preguntas_test)
        
        if st.button("Obtener Perfil de Inversión"):
            with st.spinner("Analizando sus respuestas..."):
                perfil = obtener_perfil_sugerido(token_portador, respuestas, id_cliente)
                
                if perfil and 'perfilSugerido' in perfil:
                    st.session_state.perfil_inversor = perfil
                    st.session_state.test_completado = True
                    
                    # Mostrar resumen del perfil
                    st.success(f"Perfil de Inversión: {perfil['perfilSugerido']['nombre']}")
                    st.write(perfil['perfilSugerido']['detalle'])
                    
                    # Mostrar composición del perfil
                    st.subheader("Composición del Perfil")
                    for comp in perfil['perfilSugerido']['perfilComposiciones']:
                        st.write(f"- {comp['nombre']}: {comp['porcentaje']}%")
    
    # Si el test está completo, permitir generar cartera
    if st.session_state.get('test_completado', False) and 'perfil_inversor' in st.session_state:
        st.subheader("Generar Cartera de Inversión")
        
        # Activos de ejemplo organizados por tipo
        activos_ejemplo = {
            # Acciones locales e internacionales
            'acciones': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'GGAL', 'YPF', 'PAMP', 'BMA', 'TEO'],
            'acciones_nyse': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'JPM', 'V', 'JNJ', 'WMT'],
            'acciones_nasdaq': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'ADBE', 'INTC', 'CSCO'],
            'acciones_bcba': ['GGAL', 'YPF', 'PAMP', 'BMA', 'TEO', 'TGS', 'COME', 'PGR', 'TGSU2', 'TXAR'],
            
            # Bonos y títulos públicos
            'bonos': ['AL30', 'GD30', 'AL35', 'GD35', 'AL41', 'GD46', 'AL29', 'GD29', 'AL30D', 'GD30D'],
            'títulos_públicos': ['AL30', 'GD30', 'AL35', 'GD35', 'AL41', 'GD46', 'AL29', 'GD29', 'TX26', 'TX28'],
            
            # Fondos comunes de inversión
            'fondos': ['FCI1', 'FCI2', 'FCI3', 'FCI4', 'FCI5', 'FCI6', 'FCI7', 'FCI8', 'FCI9', 'FCI10'],
            'fci_renta_variable': ['FCIRV1', 'FCIRV2', 'FCIRV3', 'FCIRV4', 'FCIRV5'],
            'fci_renta_fija': ['FCIRF1', 'FCIRF2', 'FCIRF3', 'FCIRF4', 'FCIRF5'],
            'fci_mixto': ['FCIM1', 'FCIM2', 'FCIM3', 'FCIM4', 'FCIM5'],
            
            # Instrumentos de corto plazo
            'cauciones': ['CAU1', 'CAU2', 'CAU3', 'CAU4', 'CAU5', 'CAU7', 'CAU14', 'CAU28', 'CAU42', 'CAU56'],
            'plazo_fijo': ['PF1', 'PF2', 'PF3', 'PF4', 'PF5', 'PF30', 'PF60', 'PF90', 'PF120', 'PF180'],
            'plazofijo': ['PF1', 'PF2', 'PF3', 'PF4', 'PF5', 'PF30', 'PF60', 'PF90', 'PF120', 'PF180'],
            
            # Otros instrumentos
            'cedears': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'BABA', 'MELI', 'VIST'],
            'obligaciones_negociables': ['ON1', 'ON2', 'ON3', 'ON4', 'ON5', 'ON6', 'ON7', 'ON8', 'ON9', 'ON10'],
            'futuros': ['RFX20MAR24', 'RFX20JUN24', 'RFX20SEP24', 'RFX20DIC24', 'DLR/MAE24']
        }
        
        capital = st.number_input(
            "Capital total a invertir:", 
            min_value=1000.0, 
            value=100000.0, 
            step=1000.0,
            format="%.2f"
        )
        
        if st.button("Generar Cartera Aleatoria"):
            cartera = seleccionar_activos_aleatorios(
                st.session_state.perfil_inversor, 
                activos_ejemplo
            )
            mostrar_cartera_recomendada(cartera, capital)

# --- Funciones de Visualización ---
def mostrar_analisis_portafolio(portafolio, token_portador):
    st.markdown("## 📊 Análisis de Portafolio")
    
    # Sección de análisis con PyHomeBroker
    st.markdown("### 🔄 Análisis con PyHomeBroker")
    with st.expander("Configuración de PyHomeBroker", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            host = st.number_input("Número de Broker (ej: 284 para Veta)", min_value=1, value=284, step=1, key="phb_broker")
            dni = st.text_input("DNI", value="", key="phb_dni")
            user = st.text_input("Usuario", value="", key="phb_user")
        with col2:
            password = st.text_input("Contraseña", type="password", value="", key="phb_password")
            comitente = st.number_input("Número de comitente", min_value=1, value=0, step=1, key="phb_comitente")
            
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Fecha de inicio", value=date.today() - timedelta(days=30), key="phb_fecha_inicio")
        with col2:
            use_today = st.checkbox("Usar fecha actual como fin", value=True, key="phb_use_today")
            if not use_today:
                fecha_fin = st.date_input("Fecha de fin", value=date.today(), key="phb_fecha_fin")
            else:
                fecha_fin = date.today()
    
    if st.button("🔍 Analizar con PyHomeBroker", key="phb_analyze_btn"):
        if not all([host, dni, user, password, comitente]):
            st.error("Por favor complete todos los campos de conexión")
            return
            
        with st.spinner("Conectando con PyHomeBroker..."):
            try:
                # Inicializar conexión
                hb = SHDA.SHDA(host, dni, user, password)
                
                # Obtener fechas en el rango
                fechas = pd.date_range(start=fecha_inicio, end=fecha_fin).strftime("%Y-%m-%d").tolist()
                
                # Obtener posiciones para cada fecha
                posiciones = {}
                for fecha in fechas:
                    try:
                        pos = hb.get_portfolio.by_date(comitente, fecha, "ARS")
                        if pos is not None and not pos.empty:
                            posiciones[fecha] = pos
                    except Exception as e:
                        st.warning(f"Error al obtener datos para {fecha}: {str(e)}")
                
                if not posiciones:
                    st.error("No se pudieron obtener datos del portafolio. Verifique las credenciales y fechas.")
                    return
                
                # Mostrar gráficos
                mostrar_graficos_pyhomebroker(posiciones, fecha_inicio, fecha_fin)
                
            except Exception as e:
                st.error(f"Error al conectar con PyHomeBroker: {str(e)}")
                import traceback
                st.text(traceback.format_exc())

def mostrar_graficos_pyhomebroker(posiciones, fecha_inicio, fecha_fin):
    """Muestra los gráficos de análisis de PyHomeBroker"""
    fechas = sorted(posiciones.keys())
    
    # Gráfico de torta para fechas representativas
    if len(fechas) >= 3:
        fechas_pie = [fechas[0], fechas[len(fechas)//2], fechas[-1]]
    else:
        fechas_pie = fechas
    
    # Función para crear etiquetas
    def crear_labels(pos):
        if 'description' in pos and 'position' in pos:
            return [f"{desc} ({pos_val})" for desc, pos_val in zip(pos["description"], pos["position"])]
        return []
    
    # Preparar datos para gráficos de torta
    labels_list = []
    values_list = []
    for fecha in fechas_pie:
        if fecha in posiciones:
            labels = crear_labels(posiciones[fecha])
            if labels:  # Solo agregar si hay datos
                labels_list.append(labels)
                values_list.append(posiciones[fecha]["position"].astype(float))
    
    # Mostrar gráficos de torta si hay datos
    if labels_list and values_list:
        st.markdown("### 📊 Distribución de Posiciones")
        fig_pie = make_subplots(
            rows=1, 
            cols=len(labels_list),
            specs=[[{'type':'domain'}]*len(labels_list)],
            subplot_titles=[f"Posiciones ({fecha})" for fecha in fechas_pie[:len(labels_list)]]
        )
        
        # Colores personalizados que funcionan bien en modo oscuro
        colors = ['#636EFA', '#00CC96', '#FF6F61', '#F7B7A3', '#FF9900', '#AB63FA']
        
        # Agregar cada gráfico de torta
        for i, (labels, values) in enumerate(zip(labels_list, values_list), start=1):
            fig_pie.add_trace(go.Pie(
                labels=labels,
                values=values,
                name=f"Gráfico {i}",
                textinfo='label+value',
                textposition='outside',
                marker=dict(colors=colors),
                textfont=dict(color='#f8f9fa')  # Texto blanco para mejor contraste
            ),
                row=1, col=i
            )
        
        fig_pie.update_layout(
            title_text=f"Distribución de Posiciones (Periodo: {fecha_inicio} a {fecha_fin})",
            title_x=0.5,
            showlegend=False,
            height=500,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#f8f9fa')
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Gráfico de evolución
    st.markdown("### 📈 Evolución del Portafolio")
    try:
        # Crear DataFrame con la evolución
        data = {
            "Fecha": fechas,
            "Valor Total": [posiciones[fecha]["position"].astype(float).sum() for fecha in fechas]
        }
        df = pd.DataFrame(data)
        
        # Calcular evolución porcentual
        df["Evolución %"] = df["Valor Total"].pct_change() * 100
        df.loc[0, "Evolución %"] = 0
        
        # Crear gráfico de líneas
        fig_line = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            subplot_titles=(
                f"Valor Total del Portafolio (ARS)", 
                "Evolución Porcentual (%)"
            ),
            vertical_spacing=0.1
        )
        
        # Gráfico de valor total
        fig_line.add_trace(go.Scatter(
            x=df["Fecha"],
            y=df["Valor Total"],
            mode='lines+markers',
            name="Valor Total",
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6, color='#1f77b4')
        ),
            row=1, col=1
        )
        
        # Gráfico de evolución porcentual
        fig_line.add_trace(go.Scatter(
            x=df["Fecha"],
            y=df["Evolución %"],
            mode='lines+markers',
            name="Evolución %",
            line=dict(color='#ff7f0e', width=2),
            marker=dict(size=6, color='#ff7f0e')
        ),
            row=2, col=1
        )
        
        fig_line.update_layout(
            title=f"Evolución del Portafolio ({fecha_inicio} a {fecha_fin})",
            title_x=0.5,
            height=700,
            showlegend=False
        )
        
        fig_line.update_yaxes(title_text="Valor (ARS)", row=1, col=1)
        fig_line.update_yaxes(title_text="Variación %", row=2, col=1)
        fig_line.update_xaxes(title_text="Fecha", row=2, col=1)
        
        st.plotly_chart(fig_line, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error al generar gráfico de evolución: {str(e)}")
        import traceback
        st.text(traceback.format_exc())
    
    # Sección de análisis con PyHomeBroker
    st.markdown("### 🔄 Análisis con PyHomeBroker")
    with st.expander("Configuración de PyHomeBroker", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            host = st.number_input("Número de Broker (ej: 284 para Veta)", min_value=1, value=284, step=1, key="phb_broker")
            dni = st.text_input("DNI", value="", key="phb_dni")
            user = st.text_input("Usuario", value="", key="phb_user")
        with col2:
            password = st.text_input("Contraseña", type="password", value="", key="phb_password")
            comitente = st.number_input("Número de comitente", min_value=1, value=0, step=1, key="phb_comitente")
            
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Fecha de inicio", value=date.today() - timedelta(days=30), key="phb_fecha_inicio")
        with col2:
            use_today = st.checkbox("Usar fecha actual como fin", value=True, key="phb_use_today")
            if not use_today:
                fecha_fin = st.date_input("Fecha de fin", value=date.today(), key="phb_fecha_fin")
            else:
                fecha_fin = date.today()
    
    if st.button("🔍 Analizar con PyHomeBroker", key="phb_analyze_btn"):
        if not all([host, dni, user, password, comitente]):
            st.error("Por favor complete todos los campos de conexión")
            return
            
        with st.spinner("Conectando con PyHomeBroker..."):
            try:
                # Inicializar conexión
                hb = SHDA.SHDA(host, dni, user, password)
                
                # Obtener fechas en el rango
                fechas = pd.date_range(start=fecha_inicio, end=fecha_fin).strftime("%Y-%m-%d").tolist()
                
                # Obtener posiciones para cada fecha
                posiciones = {}
                for fecha in fechas:
                    try:
                        pos = hb.get_portfolio.by_date(comitente, fecha, "ARS")
                        if pos is not None and not pos.empty:
                            posiciones[fecha] = pos
                    except Exception as e:
                        st.warning(f"Error al obtener datos para {fecha}: {str(e)}")
                
                if not posiciones:
                    st.error("No se pudieron obtener datos del portafolio. Verifique las credenciales y fechas.")
                    return
                
                # Mostrar gráficos
                mostrar_graficos_pyhomebroker(posiciones, fecha_inicio, fecha_fin)
                
            except Exception as e:
                st.error(f"Error al conectar con PyHomeBroker: {str(e)}")
                import traceback
                st.text(traceback.format_exc())

def mostrar_graficos_pyhomebroker(posiciones, fecha_inicio, fecha_fin):
    """Muestra los gráficos de análisis de PyHomeBroker"""
    fechas = sorted(posiciones.keys())
    
    # Gráfico de torta para fechas representativas
    if len(fechas) >= 3:
        fechas_pie = [fechas[0], fechas[len(fechas)//2], fechas[-1]]
    else:
        fechas_pie = fechas
    
    # Función para crear etiquetas
    def crear_labels(pos):
        if 'description' in pos and 'position' in pos:
            return [f"{desc} ({pos_val})" for desc, pos_val in zip(pos["description"], pos["position"])]
        return []
    
    # Preparar datos para gráficos de torta
    labels_list = []
    values_list = []
    for fecha in fechas_pie:
        if fecha in posiciones:
            labels = crear_labels(posiciones[fecha])
            if labels:  # Solo agregar si hay datos
                labels_list.append(labels)
                values_list.append(posiciones[fecha]["position"].astype(float))
    
    # Mostrar gráficos de torta si hay datos
    if labels_list and values_list:
        st.markdown("### 📊 Distribución de Posiciones")
        fig_pie = make_subplots(
            rows=1, 
            cols=len(labels_list),
            specs=[[{'type':'domain'}]*len(labels_list)],
            subplot_titles=[f"Posiciones ({fecha})" for fecha in fechas_pie[:len(labels_list)]]
        )
        
        # Colores personalizados
        colors = ['#636EFA', '#00CC96', '#FF6F61', '#F7B7A3', '#FF9900', '#AB63FA']
        
        # Agregar cada gráfico de torta
        for i, (labels, values) in enumerate(zip(labels_list, values_list), start=1):
            fig_pie.add_trace(go.Pie(
                labels=labels,
                values=values,
                name=f"Gráfico {i}",
                textinfo='label+value',
                textposition='outside',
                marker=dict(colors=colors)
            ),
                row=1, col=i
            )
        
        fig_pie.update_layout(
            title_text=f"Distribución de Posiciones (Periodo: {fecha_inicio} a {fecha_fin})",
            title_x=0.5,
            showlegend=False,
            height=500
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Gráfico de evolución
    st.markdown("### 📈 Evolución del Portafolio")
    try:
        # Crear DataFrame con la evolución
        data = {
            "Fecha": fechas,
            "Valor Total": [posiciones[fecha]["position"].astype(float).sum() for fecha in fechas]
        }
        df = pd.DataFrame(data)
        
        # Calcular evolución porcentual
        df["Evolución %"] = df["Valor Total"].pct_change() * 100
        df.loc[0, "Evolución %"] = 0
        
        # Crear gráfico de líneas
        fig_line = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            subplot_titles=("Valor Total del Portafolio", "Evolución Porcentual")
        )
        
        # Gráfico de valor total
        fig_line.add_trace(go.Scatter(
            x=df["Fecha"],
            y=df["Valor Total"],
            mode='lines+markers',
            name="Valor Total",
            line=dict(color='#1f77b4', width=2)
        ),
            row=1, col=1
        )
        
        # Gráfico de evolución porcentual
        fig_line.add_trace(go.Scatter(
            x=df["Fecha"],
            y=df["Evolución %"],
            mode='lines+markers',
            name="Evolución %",
            line=dict(color='#ff7f0e', width=2)
        ),
            row=2, col=1
        )
        
        fig_line.update_layout(
            title=f"Evolución del Portafolio ({fecha_inicio} a {fecha_fin})",
            title_x=0.5,
            height=700,
            showlegend=False
        )
        
        fig_line.update_yaxes(title_text="Valor (ARS)", row=1, col=1)
        fig_line.update_yaxes(title_text="Variación %", row=2, col=1)
        fig_line.update_xaxes(title_text="Fecha", row=2, col=1)
        
        st.plotly_chart(fig_line, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error al generar gráfico de evolución: {str(e)}")

def mostrar_resumen_portafolio(portafolio, token_portador):
    st.markdown("### 📈 Resumen del Portafolio")
    
    activos = portafolio.get('activos', [])
    datos_activos = []
    valor_total = 0
    
    for activo in activos:
        try:
            titulo = activo.get('titulo', {})
            simbolo = titulo.get('simbolo', 'N/A')
            descripcion = titulo.get('descripcion', 'Sin descripción')
            tipo = titulo.get('tipo', 'N/A')
            cantidad = activo.get('cantidad', 0)
            
            campos_valuacion = [
                'valuacionEnMonedaOriginal',
                'valuacionActual',
                'valorNominalEnMonedaOriginal', 
                'valorNominal',
                'valuacionDolar',
                'valuacion',
                'valorActual',
                'montoInvertido',
                'valorMercado',
                'valorTotal',
                'importe'
            ]
            
            valuacion = 0
            for campo in campos_valuacion:
                if campo in activo and activo[campo] is not None:
                    try:
                        val = float(activo[campo])
                        if val > 0:
                            valuacion = val
                            break
                    except (ValueError, TypeError):
                        continue
            
            if valuacion == 0 and cantidad:
                campos_precio = [
                    'precioPromedio',
                    'precioCompra',
                    'precioActual',
                    'precio',
                    'precioUnitario',
                    'ultimoPrecio',
                    'cotizacion'
                ]
                
                precio_unitario = 0
                for campo in campos_precio:
                    if campo in activo and activo[campo] is not None:
                        try:
                            precio = float(activo[campo])
                            if precio > 0:
                                precio_unitario = precio
                                break
                        except (ValueError, TypeError):
                            continue
                
                if precio_unitario > 0:
                    try:
                        cantidad_num = float(cantidad)
                        if tipo == 'TitulosPublicos':
                            valuacion = (cantidad_num * precio_unitario) / 100.0
                        else:
                            valuacion = cantidad_num * precio_unitario
                    except (ValueError, TypeError):
                        pass
                if precio_unitario == 0:
                    for campo in campos_precio:
                        if campo in titulo and titulo[campo] is not None:
                            try:
                                precio = float(titulo[campo])
                                if precio > 0:
                                    precio_unitario = precio
                                    break
                            except (ValueError, TypeError):
                                continue
                
                # Intento final: consultar precio actual vía API si sigue en cero
            if valuacion == 0:
                ultimo_precio = None
                if mercado := titulo.get('mercado'):
                    ultimo_precio = obtener_precio_actual(token, mercado, simbolo)
                if ultimo_precio:
                    try:
                        cantidad_num = float(cantidad)
                        if tipo == 'TitulosPublicos':
                            valuacion = (cantidad_num * ultimo_precio) / 100.0
                        else:
                            valuacion = cantidad_num * ultimo_precio
                    except (ValueError, TypeError):
                        pass
            
            datos_activos.append({
                'Símbolo': simbolo,
                'Descripción': descripcion,
                'Tipo': tipo,
                'Cantidad': cantidad,
                'Valuación': valuacion,
            })
            
            valor_total += valuacion
        except Exception as e:
            continue
    
    if datos_activos:
        df_activos = pd.DataFrame(datos_activos)
        # Convert list to dictionary with symbols as keys
        portafolio_dict = {row['Símbolo']: row for row in datos_activos}
        metricas = calcular_metricas_portafolio(portafolio_dict, valor_total, token_portador)
        
        # Inicializar métricas con valores por defecto
        metricas = {
            'retorno_esperado_anual': 0,
            'std_dev_activo': 0,
            'concentracion': 0,
            'pl_esperado_min': 0,
            'pl_esperado_max': 0,
            'probabilidades': {
                'perdida': 0,
                'ganancia': 0,
                'perdida_mayor_10': 0,
                'ganancia_mayor_10': 0
            },
            'riesgo_anual': 0
        }
        
        # Calcular métricas del portafolio si hay datos
        if datos_activos and valor_total > 0:
            try:
                portafolio_dict = {row['Símbolo']: row for row in datos_activos}
                metricas = calcular_metricas_portafolio(portafolio_dict, valor_total, token_portador)
            except Exception as e:
                st.error(f"Error al calcular métricas del portafolio: {str(e)}")
        
        # Mostrar información general
        cols = st.columns(4)
        cols[0].metric("Total de Activos", len(datos_activos))
        cols[1].metric("Símbolos Únicos", df_activos['Símbolo'].nunique())
        cols[2].metric("Tipos de Activos", df_activos['Tipo'].nunique())
        cols[3].metric("Valor Total", f"${valor_total:,.2f}")
        
        if metricas:
            # Métricas de Riesgo
            st.subheader("⚖️ Análisis de Riesgo")
            cols = st.columns(3)
            
            # Mostrar concentración como porcentaje
            concentracion_pct = metricas['concentracion'] * 100
            cols[0].metric("Concentración", 
                         f"{concentracion_pct:.1f}%",
                         help="Índice de Herfindahl normalizado: 0%=muy diversificado, 100%=muy concentrado")
            
            # Mostrar volatilidad como porcentaje anual
            volatilidad_pct = metricas['std_dev_activo'] * 100
            cols[1].metric("Volatilidad Anual", 
                         f"{volatilidad_pct:.1f}%",
                         help="Riesgo medido como desviación estándar de retornos anuales")
            
            # Nivel de concentración con colores
            if metricas['concentracion'] < 0.3:
                concentracion_status = "🟢 Baja"
            elif metricas['concentracion'] < 0.6:
                concentracion_status = "🟡 Media"
            else:
                concentracion_status = "🔴 Alta"
                
            cols[2].metric("Nivel Concentración", concentracion_status)
            
            # Proyecciones
            st.subheader("📈 Proyecciones de Rendimiento")
            cols = st.columns(3)
            
            # Mostrar retornos como porcentaje del portafolio
            retorno_anual_pct = metricas['retorno_esperado_anual'] * 100
            cols[0].metric("Retorno Esperado Anual", 
                         f"{retorno_anual_pct:+.1f}%",
                         help="Retorno anual esperado basado en datos históricos")
            
            # Mostrar escenarios como porcentaje del portafolio
            optimista_pct = (metricas['pl_esperado_max'] / valor_total) * 100 if valor_total > 0 else 0
            pesimista_pct = (metricas['pl_esperado_min'] / valor_total) * 100 if valor_total > 0 else 0
            
            cols[1].metric("Escenario Optimista (95%)", 
                         f"{optimista_pct:+.1f}%",
                         help="Mejor escenario con 95% de confianza")
            cols[2].metric("Escenario Pesimista (5%)", 
                         f"{pesimista_pct:+.1f}%",
                         help="Peor escenario con 5% de confianza")
            
            # Probabilidades
            st.subheader("🎯 Probabilidades")
            cols = st.columns(4)
            probs = metricas['probabilidades']
            cols[0].metric("Ganancia", f"{probs['ganancia']*100:.1f}%")
            cols[1].metric("Pérdida", f"{probs['perdida']*100:.1f}%")
            cols[2].metric("Ganancia >10%", f"{probs['ganancia_mayor_10']*100:.1f}%")
            cols[3].metric("Pérdida >10%", f"{probs['perdida_mayor_10']*100:.1f}%")
        
        # Gráficos
        st.subheader("📊 Distribución de Activos")
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Tipo' in df_activos.columns and df_activos['Valuación'].sum() > 0:
                tipo_stats = df_activos.groupby('Tipo')['Valuación'].sum().reset_index()
                fig_pie = go.Figure(data=[go.Pie(
                    labels=tipo_stats['Tipo'],
                    values=tipo_stats['Valuación'],
                    textinfo='label+percent',
                    hole=0.4,
                    marker=dict(colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
                )])
                fig_pie.update_layout(
                    title="Distribución por Tipo",
                    height=400
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            if len(datos_activos) > 1:
                valores_activos = [a['Valuación'] for a in datos_activos if a['Valuación'] > 0]
                if valores_activos:
                    fig_hist = go.Figure(data=[go.Histogram(
                        x=valores_activos,
                        nbinsx=min(20, len(valores_activos)),
                        marker_color='#0d6efd'
                    )])
                    fig_hist.update_layout(
                        title="Distribución de Valores",
                        xaxis_title="Valor ($)",
                        yaxis_title="Frecuencia",
                        height=400
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
        
        # Tabla de activos
        st.subheader("📋 Detalle de Activos")
        df_display = df_activos.copy()
        df_display['Valuación'] = df_display['Valuación'].apply(
            lambda x: f"${x:,.2f}" if x > 0 else "N/A"
        )
        df_display['Peso (%)'] = (df_activos['Valuación'] / valor_total * 100).round(2)
        df_display = df_display.sort_values('Peso (%)', ascending=False)
        
        st.dataframe(df_display, use_container_width=True, height=400)
        
        # Recomendaciones
        st.subheader("💡 Recomendaciones")
        if metricas:
            if metricas['concentracion'] > 0.5:
                st.warning("""
                **⚠️ Portafolio Altamente Concentrado**  
                Considere diversificar sus inversiones para reducir el riesgo.
                """)
            elif metricas['concentracion'] > 0.25:
                st.info("""
                **ℹ️ Concentración Moderada**  
                Podría mejorar su diversificación para optimizar el riesgo.
                """)
            else:
                st.success("""
                **✅ Buena Diversificación**  
                Su portafolio está bien diversificado.
                """)
            
            ratio_riesgo_retorno = metricas['retorno_esperado_anual'] / metricas['riesgo_anual'] if metricas['riesgo_anual'] > 0 else 0
            if ratio_riesgo_retorno > 0.5:
                st.success("""
                **✅ Buen Balance Riesgo-Retorno**  
                La relación entre riesgo y retorno es favorable.
                """)
            else:
                st.warning("""
                **⚠️ Revisar Balance Riesgo-Retorno**  
                El riesgo podría ser alto en relación al retorno esperado.
                """)
    else:
        st.warning("No se encontraron activos en el portafolio")

def mostrar_estado_cuenta(estado_cuenta):
    st.markdown("### 💰 Estado de Cuenta")
    
    if not estado_cuenta:
        st.warning("No hay datos de estado de cuenta disponibles")
        return
    
    total_en_pesos = estado_cuenta.get('totalEnPesos', 0)
    cuentas = estado_cuenta.get('cuentas', [])
    
    cols = st.columns(3)
    cols[0].metric("Total en Pesos", f"AR$ {total_en_pesos:,.2f}")
    cols[1].metric("Número de Cuentas", len(cuentas))
    
    if cuentas:
        st.subheader("📊 Detalle de Cuentas")
        
        datos_cuentas = []
        for cuenta in cuentas:
            datos_cuentas.append({
                'Número': cuenta.get('numero', 'N/A'),
                'Tipo': cuenta.get('tipo', 'N/A').replace('_', ' ').title(),
                'Moneda': cuenta.get('moneda', 'N/A').replace('_', ' ').title(),
                'Disponible': f"${cuenta.get('disponible', 0):,.2f}",
                'Saldo': f"${cuenta.get('saldo', 0):,.2f}",
                'Total': f"${cuenta.get('total', 0):,.2f}",
            })
        
        df_cuentas = pd.DataFrame(datos_cuentas)
        st.dataframe(df_cuentas, use_container_width=True, height=300)

def mostrar_cotizaciones_mercado(token_acceso):
    st.markdown("### 💱 Cotizaciones y Mercado")
    
    with st.expander("💰 Cotización MEP", expanded=True):
        with st.form("mep_form"):
            col1, col2, col3 = st.columns(3)
            simbolo_mep = col1.text_input("Símbolo", value="AL30", help="Ej: AL30, GD30, etc.")
            id_plazo_compra = col2.number_input("ID Plazo Compra", value=1, min_value=1)
            id_plazo_venta = col3.number_input("ID Plazo Venta", value=1, min_value=1)
            
            if st.form_submit_button("🔍 Consultar MEP"):
                if simbolo_mep:
                    with st.spinner("Consultando cotización MEP..."):
                        cotizacion_mep = obtener_cotizacion_mep(
                            token_acceso, simbolo_mep, id_plazo_compra, id_plazo_venta
                        )
                    
                    if cotizacion_mep:
                        st.success("✅ Cotización MEP obtenida")
                        precio_mep = cotizacion_mep.get('precio', 'N/A')
                        st.metric("Precio MEP", f"${precio_mep}" if precio_mep != 'N/A' else 'N/A')
                    else:
                        st.error("❌ No se pudo obtener la cotización MEP")
    
    with st.expander("🏦 Tasas de Caución", expanded=True):
        if st.button("🔄 Actualizar Tasas"):
            with st.spinner("Consultando tasas de caución..."):
                tasas_caucion = obtener_tasas_caucion(token_acceso)
            
            if tasas_caucion is not None and not tasas_caucion.empty:
                df_tasas = pd.DataFrame(tasas_caucion)
                columnas_relevantes = ['simbolo', 'tasa', 'bid', 'offer', 'ultimo']
                columnas_disponibles = [col for col in columnas_relevantes if col in df_tasas.columns]
                
                if columnas_disponibles:
                    st.dataframe(df_tasas[columnas_disponibles].head(10))
                else:
                    st.dataframe(df_tasas.head(10))
            else:
                st.error("❌ No se pudieron obtener las tasas de caución")

def simular_ejecucion(precio_objetivo, precio_actual, volatilidad, dias=1, n_simulaciones=1000):
    """
    Simula la ejecución de órdenes usando el modelo de Monte Carlo.
    
    Args:
        precio_objetivo (float): Precio objetivo de ejecución
        precio_actual (float): Precio actual del activo
        volatilidad (float): Volatilidad anualizada del activo
        dias (int): Horizonte de tiempo en días
        n_simulaciones (int): Número de simulaciones a ejecutar
        
    Returns:
        dict: Resultados de la simulación
    """
    try:
        # Convertir volatilidad diaria
        volatilidad_diaria = volatilidad / np.sqrt(252)
        
        # Generar precios simulados
        precios_simulados = []
        for _ in range(n_simulaciones):
            # Modelo de movimiento browniano geométrico
            retorno_diario = np.random.normal(0, volatilidad_diaria, dias)
            precios = precio_actual * np.exp(np.cumsum(retorno_diario))
            precios_simulados.append(pd.Series(precios, index=range(dias)))
        
        # Calcular métricas
        df_simulaciones = pd.concat(precios_simulados, axis=1)
        
        # Calcular probabilidad de ejecución
        ejecutado = df_simulaciones.le(precio_objetivo).any()
        prob_ejecucion = ejecutado.mean() * 100
        
        # Calcular tiempo medio de ejecución
        if ejecutado.any():
            tiempos_ejecucion = df_simulaciones.apply(lambda x: x[x <= precio_objetivo].index.min() if (x <= precio_objetivo).any() else dias)
            tiempo_medio = tiempos_ejecucion.mean()
        else:
            tiempo_medio = dias
        
        return {
            'probabilidad_ejecucion': prob_ejecucion,
            'tiempo_medio_ejecucion': tiempo_medio,
            'precio_medio_final': df_simulaciones.iloc[-1].mean(),
            'precio_min_final': df_simulaciones.iloc[-1].min(),
            'precio_max_final': df_simulaciones.iloc[-1].max(),
            'simulaciones': df_simulaciones
        }
        
    except Exception as e:
        st.error(f"Error en la simulación de ejecución: {str(e)}")
        return None


def mostrar_optimizacion_portafolio(token_acceso, id_cliente):
    st.title("Optimización de Portafolio")
    
    # Asegurarse de que plotly.graph_objects esté disponible globalmente
    global go
    
    with st.spinner("Obteniendo portafolio..."):
        portafolio = obtener_portafolio(token_acceso, id_cliente)
    
    if not portafolio:
        st.warning("No se pudo obtener el portafolio del cliente")
        return
    
    activos_raw = portafolio.get('activos', [])
    if not activos_raw:
        st.warning("El portafolio está vacío")
        return
    
    # Extraer símbolos, mercados y tipos de activo
    activos_para_optimizacion = []
    for activo in activos_raw:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo')
        mercado = titulo.get('mercado')
        tipo = titulo.get('tipo')
        if simbolo:
            activos_para_optimizacion.append({'simbolo': simbolo,
                                              'mercado': mercado,
                                              'tipo': tipo})
    
    if not activos_para_optimizacion:
        st.warning("No se encontraron activos con información de mercado válida para optimizar.")
        return
    
    fecha_desde = st.session_state.fecha_desde
    fecha_hasta = st.session_state.fecha_hasta
    
    st.info(f"Analizando {len(activos_para_optimizacion)} activos desde {fecha_desde} hasta {fecha_hasta}")

    # --- Función de selección aleatoria de activos respetando el capital ---
    def seleccion_aleatoria_activos_con_capital(activos, token, capital):
        '''
        Selecciona activos aleatorios de la lista sin superar el capital, usando el precio actual de cada activo.
        Retorna lista de activos seleccionados y el total invertido.
        '''
        import random
        random.shuffle(activos)
        seleccionados = []
        capital_restante = capital
        total_invertido = 0
        for activo in activos:
            simbolo = activo.get('simbolo')
            mercado = activo.get('mercado')
            if not simbolo or not mercado:
                continue
            precio = obtener_precio_actual(token, mercado, simbolo)
            if precio is not None and precio > 0 and precio <= capital_restante:
                seleccionados.append({'simbolo': simbolo, 'mercado': mercado, 'precio': precio})
                capital_restante -= precio
                total_invertido += precio
            if capital_restante < 1:
                break
        return seleccionados, total_invertido
    
    # Configuración de selección de universo y optimización
    col_sel, col1, col2, col3 = st.columns(4)

    with col_sel:
        metodo_seleccion = st.selectbox(
            "Método de Selección de Activos:",
            options=['actual', 'aleatoria'],
            format_func=lambda x: {
                'actual': 'Portafolio actual',
                'aleatoria': 'Selección aleatoria'
            }[x]
        )

    # Mostrar input de capital y filtro de tipo de activo solo si corresponde
    if metodo_seleccion == 'aleatoria':
        # Filtro de tipo de activo solo en aleatoria
        tipos_disponibles = sorted(set([a['tipo'] for a in activos_para_optimizacion if a.get('tipo')]))
        tipo_seleccionado = st.selectbox(
            "Filtrar por tipo de activo:",
            options=['Todos'] + tipos_disponibles,
            key="opt_tipo_activo",
            format_func=lambda x: "Todos" if x == 'Todos' else x
        )
        if tipo_seleccionado != 'Todos':
            activos_filtrados = [a for a in activos_para_optimizacion if a.get('tipo') == tipo_seleccionado]
        else:
            activos_filtrados = activos_para_optimizacion
            
        capital_inicial = st.number_input(
            "Capital Inicial para Optimización (ARS):",
            min_value=1000.0, max_value=1e9, value=100000.0, step=1000.0,
            help="El monto máximo a invertir en la selección aleatoria de activos",
            key="opt_capital_aleatoria"
        )
    else:
        activos_filtrados = activos_para_optimizacion
        capital_inicial = None

    # --- Métodos avanzados de optimización ---
    metodos_optimizacion = {
        'Maximizar Sharpe (Markowitz)': 'max_sharpe',
        'Mínima Varianza L1': 'min-variance-l1',
        'Mínima Varianza L2': 'min-variance-l2',
        'Pesos Iguales': 'equi-weight',
        'Solo Posiciones Largas': 'long-only',
        'Markowitz con Retorno Objetivo': 'markowitz-target'
    }
    metodo_ui = st.selectbox(
        "Método de Optimización de Portafolio:",
        options=list(metodos_optimizacion.keys()),
        key="opt_metodo_optimizacion"
    )
    metodo = metodos_optimizacion[metodo_ui]

    # Pedir retorno objetivo solo si corresponde
    target_return = None
    if metodo == 'markowitz-target':
        target_return = st.number_input(
            "Retorno Objetivo (anual, decimal, ej: 0.15 para 15%):",
            min_value=0.01, value=0.10, step=0.01, format="%.4f",
            help="No hay máximo. Si el retorno es muy alto, la simulación puede no converger."
        )

    # Checkbox moved to the top of the section for better organization

    # --- Frontera Eficiente ---
    if 'show_frontier' not in st.session_state:
        st.session_state.show_frontier = True
        
    # Toggle function for the frontier
    def toggle_frontier():
        st.session_state.show_frontier = not st.session_state.show_frontier
    
    # Single checkbox for frontier display
    show_frontier = st.checkbox(
        "Mostrar Frontera Eficiente", 
        value=st.session_state.show_frontier,
        key="frontier_checkbox",
        on_change=toggle_frontier
    )
    
    # --- Scheduling y tipo de orden ---
    scheduling_methods = {
        'TWAP (Time-Weighted)': 'twap',
        'VWAP (Volume-Weighted)': 'vwap'
    }
    scheduling_ui = st.selectbox(
        "Algoritmo de Scheduling:",
        options=list(scheduling_methods.keys()),
        key="opt_scheduling_algo"
    )
    scheduling = scheduling_methods[scheduling_ui]

    order_types = {
        'Market Order': 'mo',
        'Limit Order': 'lo',
        'Peg Order': 'peg',
        'Float Peg': 'float_peg',
        'Fill or Kill': 'fok',
        'Immediate or Cancel': 'ioc'
    }
    order_type_ui = st.selectbox(
        "Tipo de Orden:",
        options=list(order_types.keys()),
        key="opt_tipo_orden"
    )
    order_type = order_types[order_type_ui]

    # Input de capital inicial
    capital_inicial = st.number_input(
        "Capital Inicial para Optimización (ARS):",
        min_value=1000.0, max_value=1e9, value=100000.0, step=1000.0,
        help="El monto máximo a invertir en la selección y optimización de activos"
    )

    # Widget TradingView (requiere streamlit-tradingview-widget instalado)
    try:
        from streamlit_tradingview_ta import TradingViewWidget
        st.subheader("Gráfico interactivo TradingView")
        TradingViewWidget(
            symbol="NASDAQ:AAPL",  # Cambia por símbolo seleccionado
            interval="D",
            theme="dark",
            studies=["MACD@tv-basicstudies", "RSI@tv-basicstudies"],
            height=600,
            width="100%",
        )
    except ImportError:
        st.info("Instala 'streamlit-tradingview-widget' para habilitar el gráfico TradingView.")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ejecutar_optimizacion = st.button("🚀 Ejecutar Optimización", type="primary")
    with col2:
        ejecutar_frontier = st.button("📈 Calcular Frontera Eficiente")
    with col3:
        comparar_opt = st.checkbox("Comparar Actual vs Aleatoria", value=False, help="Compara la optimización sobre tu portafolio y sobre un universo aleatorio de activos.")

    def obtener_cotizaciones_cauciones(bearer_token):
        import requests
        import pandas as pd
        url = "https://api.invertironline.com/api/v2/Cotizaciones/cauciones/argentina/Todos"
        # ... (resto del código de la función)
        fig = go.Figure()
        # ... (resto del código de la función)
        fig.update_layout(
            yaxis=dict(title="Volumen"),
            yaxis2=dict(title="Precio", overlaying="y", side="right"),
            legend=dict(orientation="h")
        )
        return fig, total_ejecutado, precio_promedio

    if ejecutar_optimizacion:
        with st.spinner("Ejecutando optimización..."):
            try:
                # --- COMPARACIÓN ACTUAL VS ALEATORIA ---
                if 'comparar_opt' in locals() and comparar_opt:
                    # 1. Portafolio actual
                    universo_actual = activos_para_optimizacion
                    capital_actual = capital_inicial if capital_inicial else 100000.0
                    manager_actual = PortfolioManager(universo_actual, token_acceso, fecha_desde, fecha_hasta, capital=capital_actual)
                    portfolio_result_actual = None
                    if manager_actual.load_data():
                        portfolio_result_actual = manager_actual.compute_portfolio(strategy=metodo, target_return=target_return) if metodo == 'markowitz-target' else manager_actual.compute_portfolio(strategy=metodo)
                    # 2. Portafolio aleatorio (misma cantidad de activos)
                    st.info("🔀 Selección aleatoria de activos para benchmarking")
                    cantidad_activos = len(universo_actual)
                    seleccionados, total_invertido = seleccion_aleatoria_activos_con_capital(
                        universo_actual, token_acceso, capital_actual
                    )
                    if not seleccionados or len(seleccionados) < 2:
                        st.warning("No se pudieron seleccionar activos aleatorios dentro del capital disponible para comparar.")
                        return
                    universo_aleatorio = [a for a in universo_actual if any(
                        s['simbolo'] == a['simbolo'] and s['mercado'] == a['mercado'] for s in seleccionados
                    )]
                    manager_aleatorio = PortfolioManager(universo_aleatorio, token_acceso, fecha_desde, fecha_hasta, capital=capital_actual)
                    portfolio_result_aleatorio = None
                    if manager_aleatorio.load_data():
                        portfolio_result_aleatorio = manager_aleatorio.compute_portfolio(strategy=metodo, target_return=target_return) if metodo == 'markowitz-target' else manager_aleatorio.compute_portfolio(strategy=metodo)
                    # Mostrar resultados comparados
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### Portafolio Actual")
                        if portfolio_result_actual:
                            st.markdown("#### 📊 Pesos Optimizados")
                            if portfolio_result_actual.dataframe_allocation is not None:
                                weights_df = portfolio_result_actual.dataframe_allocation.copy()
                                weights_df['Peso (%)'] = weights_df['weights'] * 100
                                weights_df = weights_df.sort_values('Peso (%)', ascending=False)
                                st.dataframe(weights_df[['rics', 'Peso (%)']], use_container_width=True)
                            st.markdown("#### 📈 Métricas del Portafolio")
                            st.json(portfolio_result_actual.get_metrics_dict())
                    with col2:
                        st.markdown("### Portafolio Aleatorio")
                        if portfolio_result_aleatorio:
                            st.markdown("#### 📊 Pesos Optimizados")
                            if portfolio_result_aleatorio.dataframe_allocation is not None:
                                weights_df = portfolio_result_aleatorio.dataframe_allocation.copy()
                                weights_df['Peso (%)'] = weights_df['weights'] * 100
                                weights_df = weights_df.sort_values('Peso (%)', ascending=False)
                                st.dataframe(weights_df[['rics', 'Peso (%)']], use_container_width=True)
                            st.markdown("#### 📈 Métricas del Portafolio")
                            st.json(portfolio_result_aleatorio.get_metrics_dict())
                    # --- Comparación visual de retornos ---
                    st.markdown("#### 📊 Comparación de Distribución de Retornos")
                    import plotly.graph_objects as go
                    fig_hist = go.Figure()
                    if portfolio_result_actual is not None:
                        fig_hist.add_trace(go.Histogram(
                            x=portfolio_result_actual.returns,
                            name="Actual",
                            opacity=0.6,
                            marker_color="#1f77b4"
                        ))
                    if portfolio_result_aleatorio is not None:
                        fig_hist.add_trace(go.Histogram(
                            x=portfolio_result_aleatorio.returns,
                            name="Aleatorio",
                            opacity=0.6,
                            marker_color="#ff7f0e"
                        ))
                    fig_hist.update_layout(
                        barmode="overlay",
                        title="Distribución de Retornos: Actual vs Aleatorio",
                        xaxis_title="Retorno Diario",
                        yaxis_title="Frecuencia",
                        template="plotly_white"
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                    # --- Comparación visual de frontera eficiente ---
                    st.markdown("#### 📈 Comparación de Frontera Eficiente")
                    try:
                        fe_actual = None
                        fe_aleatorio = None
                        if manager_actual and manager_actual.load_data():
                            fe_actual, ret_actual, vol_actual = manager_actual.compute_efficient_frontier(target_return=target_return if target_return else 0.08)
                        if manager_aleatorio and manager_aleatorio.load_data():
                            fe_aleatorio, ret_aleatorio, vol_aleatorio = manager_aleatorio.compute_efficient_frontier(target_return=target_return if target_return else 0.08)
                        fig_fe = go.Figure()
                        if fe_actual is not None:
                            fig_fe.add_trace(go.Scatter(
                                x=vol_actual, y=ret_actual, mode='lines', name='Frontera Actual', line=dict(color='#1f77b4')
                            ))
                        if fe_aleatorio is not None:
                            fig_fe.add_trace(go.Scatter(
                                x=vol_aleatorio, y=ret_aleatorio, mode='lines', name='Frontera Aleatoria', line=dict(color='#ff7f0e')
                            ))
                        fig_fe.update_layout(
                            title="Frontera Eficiente: Actual vs Aleatorio",
                            xaxis_title="Volatilidad Anual",
                            yaxis_title="Retorno Anual",
                            template="plotly_white"
                        )
                        st.plotly_chart(fig_fe, use_container_width=True)
                    except Exception as e:
                        st.warning(f"No se pudo calcular la frontera eficiente comparada: {e}")
                    st.info("Comparación completada. Puedes analizar cuál estrategia resulta superior en tu contexto.")
                    return
                # --- Selección de universo de activos (modo tradicional) ---
                if metodo_seleccion == 'aleatoria':
                    st.info("🔀 Selección aleatoria de activos respetando el capital inicial")
                    if capital_inicial is None:
                        st.warning("Debe ingresar el capital inicial para la selección aleatoria.")
                        return
                    seleccionados, total_invertido = seleccion_aleatoria_activos_con_capital(
                        activos_filtrados, token_acceso, capital_inicial
                    )
                    if not seleccionados:
                        st.warning("No se pudieron seleccionar activos aleatorios dentro del capital disponible.")
                        return
                    else:
                        st.success(f"✅ Selección aleatoria completada. Total invertido: {total_invertido:.2f} ARS")
                        df_sel = pd.DataFrame(seleccionados)
                        df_sel['Peso (%)'] = (df_sel['precio'] / total_invertido) * 100
                        st.markdown("#### Activos seleccionados aleatoriamente:")
                        st.dataframe(df_sel[['simbolo', 'mercado', 'precio', 'Peso (%)']], use_container_width=True)
                        # Solo optimizar sobre los activos seleccionados aleatoriamente (usando símbolo y mercado)
                        universo_para_opt = [a for a in activos_filtrados if any(
                            s['simbolo'] == a['simbolo'] and s['mercado'] == a['mercado'] for s in seleccionados
                        )]
                        if not universo_para_opt:
                            st.warning("No hay activos seleccionados aleatoriamente para optimizar.")
                            return
                else:
                    universo_para_opt = activos_para_optimizacion

                # --- Optimización sobre el universo seleccionado ---
                if not universo_para_opt:
                    st.warning("No hay activos suficientes para optimizar.")
                    return
                manager_inst = PortfolioManager(universo_para_opt, token_acceso, fecha_desde, fecha_hasta, capital=capital_inicial)
                if manager_inst.load_data():
                    # Elegir método y target_return según selección
                    if metodo == 'markowitz-target':
                        max_attempts = 10
                        attempt = 0
                        portfolio_result = None
                        while attempt < max_attempts:
                            result = manager_inst.compute_portfolio(strategy='markowitz', target_return=target_return)
                            if result and abs(result.return_annual - target_return) < 0.001:
                                portfolio_result = result
                                break
                            attempt += 1
                        if not portfolio_result:
                            st.warning(f"No se logró cumplir el retorno objetivo ({target_return:.2%}) tras {max_attempts} intentos. El resultado más cercano se muestra.")
                            # Mostrar el mejor resultado aunque no cumpla exactamente
                            portfolio_result = result
                    else:
                        portfolio_result = manager_inst.compute_portfolio(strategy=metodo)
                    if portfolio_result:
                        st.success("✅ Optimización completada")
                        
                        # Calcular el total invertido de manera segura
                        try:
                            if hasattr(portfolio_result, 'weights'):
                                if isinstance(portfolio_result.weights, dict):
                                    # Si weights es un diccionario, sumar los valores
                                    total_invertido = sum(portfolio_result.weights.values()) * capital_inicial
                                else:
                                    # Si es un array o similar
                                    total_invertido = np.sum(portfolio_result.weights) * capital_inicial
                            else:
                                total_invertido = capital_inicial  # Valor por defecto
                                
                            if total_invertido > capital_inicial * 1.01:  # Tolerancia del 1%
                                st.warning(f"La suma de pesos ({total_invertido:.2f}) supera el capital inicial ({capital_inicial:.2f})")
                        except Exception as e:
                            st.warning(f"Advertencia al calcular el total invertido: {str(e)}")
                            total_invertido = capital_inicial
                                                # Mostrar resultados de la optimización
                        st.success("✅ Optimización completada")
                        
                        # Mostrar pesos optimizados
                        st.subheader("📊 Pesos Optimizados")
                        try:
                            if hasattr(portfolio_result, 'dataframe_allocation') and portfolio_result.dataframe_allocation is not None:
                                # Asegurarse de que la columna 'weights' existe
                                weights_df = portfolio_result.dataframe_allocation.copy()
                                if 'weights' not in weights_df.columns and 'Peso' in weights_df.columns:
                                    weights_df['weights'] = weights_df['Peso']
                                
                                if 'weights' in weights_df.columns:
                                    # Mostrar tabla de pesos
                                    weights_df['Peso (%)'] = (weights_df['weights'] * 100).round(2)
                                    st.dataframe(weights_df[['Activo', 'Peso (%)']].set_index('Activo').style.format({'Peso (%)': '{:.2f}%'.format}))
                                    
                                    # Mostrar gráfico de torta si hay datos
                                    if not weights_df.empty and len(weights_df) > 0:
                                        fig = px.pie(
                                            weights_df, 
                                            values='weights', 
                                            names='Activo',
                                            title='Distribución del Portafolio',
                                            hole=0.3
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.warning("No se encontró la columna 'weights' en los resultados")
                            else:
                                st.warning("No se encontró información de asignación en los resultados")
                        except Exception as e:
                            st.error(f"Error al mostrar los pesos: {str(e)}")
                        
                        with col2:
                            st.markdown("#### 📈 Métricas del Portafolio")
                            try:
                                # Obtener métricas del portafolio de manera segura
                                if hasattr(portfolio_result, 'get_metrics_dict'):
                                    metricas = portfolio_result.get_metrics_dict()
                                    
                                    # Mostrar métricas con manejo de errores
                                    def safe_metric(name, value, format_str="{:.2f}"):
                                        try:
                                            if isinstance(value, (int, float)):
                                                st.metric(name, format_str.format(value))
                                            else:
                                                st.metric(name, str(value))
                                        except Exception as e:
                                            st.error(f"Error mostrando {name}")
                                    
                                    # Mostrar métricas en columnas
                                    col_m1, col_m2 = st.columns(2)
                                    
                                    with col_m1:
                                        safe_metric("Ratio de Sharpe", metricas.get('sharpe_ratio', 'N/A'))
                                        safe_metric("VaR 95%", f"{metricas.get('var_95', 'N/A'):.2%}" if isinstance(metricas.get('var_95'), (int, float)) else 'N/A')
                                        safe_metric("Retorno Anual", f"{metricas.get('return_annual', 'N/A'):.2%}" if isinstance(metricas.get('return_annual'), (int, float)) else 'N/A')
                                    
                                    with col_m2:
                                        safe_metric("Volatilidad Anual", f"{metricas.get('volatility_annual', 'N/A'):.2%}" if isinstance(metricas.get('volatility_annual'), (int, float)) else 'N/A')
                                        safe_metric("Skewness", metricas.get('skewness', 'N/A'))
                                        safe_metric("Kurtosis", metricas.get('kurtosis', 'N/A'))
                                    
                                    # Mostrar normalidad
                                    normalidad = "✅ Normal" if metricas.get('is_normal', False) else "❌ No Normal"
                                    st.metric("Normalidad", normalidad)
                                else:
                                    st.warning("No se encontraron métricas del portafolio")
                            except Exception as e:
                                st.error(f"Error al mostrar las métricas: {str(e)}")
                        
                        # Mostrar histograma de retornos si está disponible
                        if hasattr(portfolio_result, 'returns') and portfolio_result.returns is not None:
                            st.subheader("📊 Distribución de Retornos")
                            try:
                                fig = px.histogram(
                                    x=portfolio_result.returns * 100,  # Convertir a porcentaje
                                    nbins=50,
                                    title='Distribución de Retornos Diarios',
                                    labels={'x': 'Retorno Diario (%)', 'y': 'Frecuencia'}
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            except Exception as e:
                                st.error(f"Error al generar el histograma: {str(e)}")
                        
                        # Mostrar histograma avanzado si está disponible
                        if hasattr(portfolio_result, 'plot_histogram_streamlit'):
                            st.subheader("📊 Histograma Avanzado de Retornos")
                            try:
                                fig = portfolio_result.plot_histogram_streamlit("Distribución de Retornos del Portafolio")
                                st.plotly_chart(fig, use_container_width=True)
                            except Exception as e:
                                st.error(f"Error al generar el histograma avanzado: {str(e)}")

                        # Mostrar frontera eficiente si el usuario lo solicita
                        if show_frontier:
                            st.markdown("#### 📈 Frontera Eficiente (Efficient Frontier)")
                            try:
                                frontier, valid_returns, volatilities = manager_inst.compute_efficient_frontier(target_return=target_return if target_return else 0.08)
                                fig_frontier = go.Figure()
                                fig_frontier.add_trace(go.Scatter(
                                    x=volatilities, y=valid_returns, mode='lines+markers', name='Frontera Eficiente',
                                    line=dict(color='royalblue', width=2)
                                ))
                                fig_frontier.update_layout(
                                    title="Frontera Eficiente",
                                    xaxis_title="Volatilidad Anual",
                                    yaxis_title="Retorno Anual",
                                    template="plotly_white"
                                )
                                st.plotly_chart(fig_frontier, use_container_width=True)
                            except Exception as e:
                                st.warning(f"No se pudo calcular la frontera eficiente: {e}")
                        # Simulación de ejecución
                        st.markdown("---")
                        st.subheader("Simulación de Ejecución Algorítmica")
                        volumen_total = int(capital_inicial // portfolio_result.price if hasattr(portfolio_result, 'price') and portfolio_result.price > 0 else capital_inicial // 100)
                        fig_exec, total_exec, avg_price = simular_ejecucion(volumen_total, scheduling, order_type)
                        st.plotly_chart(fig_exec, use_container_width=True)
                        st.info(f"**Volumen Total Ejecutado:** {total_exec}\n\n**Precio Promedio de Ejecución:** {avg_price:.2f}")
                    else:
                        st.error("❌ Error en la optimización")
                else:
                    st.error("❌ No se pudieron cargar los datos históricos")
                    
            except Exception as e:
                st.error(f"❌ Error durante la optimización: {str(e)}")
    
    if ejecutar_frontier and show_frontier:
        with st.spinner("Calculando frontera eficiente..."):
            try:
                manager_inst = PortfolioManager(activos_para_optimizacion, token_acceso, fecha_desde, fecha_hasta)
                
                if manager_inst.load_data():
                    portfolios, returns, volatilities = manager_inst.compute_efficient_frontier(
                        target_return=target_return, include_min_variance=True
                    )
                    
                    if portfolios and returns and volatilities:
                        st.success("✅ Frontera eficiente calculada")
                        
                        # Crear gráfico de frontera eficiente
                        fig = go.Figure()
                        
                        # Línea de frontera eficiente
                        fig.add_trace(go.Scatter(
                            x=volatilities, y=returns,
                            mode='lines+markers',
                            name='Frontera Eficiente',
                            line=dict(color='#0d6efd', width=3),
                            marker=dict(size=6)
                        ))
                        
                        # Portafolios especiales
                        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
                        labels = ['Min Var L1', 'Min Var L2', 'Pesos Iguales', 'Solo Largos', 'Markowitz', 'Markowitz Target']
                        
                        for i, (label, portfolio) in enumerate(portfolios.items()):
                            if portfolio is not None:
                                fig.add_trace(go.Scatter(
                                    x=[portfolio.volatility_annual], 
                                    y=[portfolio.return_annual],
                                    mode='markers',
                                    name=labels[i] if i < len(labels) else label,
                                    marker=dict(size=12, color=colors[i % len(colors)])
                                ))
                        
                        fig.update_layout(
                            title='Frontera Eficiente del Portafolio',
                            xaxis_title='Volatilidad Anual',
                            yaxis_title='Retorno Anual',
                            showlegend=True,
                            template='plotly_white',
                            height=500
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Tabla comparativa de portafolios
                        st.markdown("#### 📊 Comparación de Estrategias")
                        comparison_data = []
                        for label, portfolio in portfolios.items():
                            if portfolio is not None:
                                comparison_data.append({
                                    'Estrategia': label,
                                    'Retorno Anual': f"{portfolio.return_annual:.2%}",
                                    'Volatilidad Anual': f"{portfolio.volatility_annual:.2%}",
                                    'Sharpe Ratio': f"{portfolio.sharpe_ratio:.4f}",
                                    'VaR 95%': f"{portfolio.var_95:.4f}",
                                    'Skewness': f"{portfolio.skewness:.4f}",
                                    'Kurtosis': f"{portfolio.kurtosis:.4f}"
                                })
                        
                        if comparison_data:
                            df_comparison = pd.DataFrame(comparison_data)
                            st.dataframe(df_comparison, use_container_width=True)
                    
                    else:
                        st.error("❌ No se pudo calcular la frontera eficiente")
                else:
                    st.error("❌ No se pudieron cargar los datos históricos")
                    
            except Exception as e:
                st.error(f"❌ Error calculando frontera eficiente: {str(e)}")
    
    # Información adicional extendida
    with st.expander("ℹ️ Información sobre las Estrategias"):
        st.markdown("""
        **Optimización de Markowitz:**
        - Maximiza el ratio de Sharpe (retorno/riesgo)
        - Considera la correlación entre activos
        - Busca la frontera eficiente de riesgo-retorno
        
        **Pesos Iguales:**
        - Distribución uniforme entre todos los activos (1/n)
        - Estrategia simple de diversificación
        - No considera correlaciones históricas
        
        **Mínima Varianza L1:**
        - Minimiza la varianza del portafolio
        - Restricción L1 para regularización (suma de valores absolutos)
        - Tiende a generar portafolios más concentrados
        
        **Mínima Varianza L2:**
        - Minimiza la varianza del portafolio
        - Restricción L2 para regularización (suma de cuadrados)
        - Genera portafolios más diversificados que L1
        
        **Solo Posiciones Largas:**
        - Optimización estándar sin restricciones adicionales
        - Permite solo posiciones compradoras (sin ventas en corto)
        - Suma de pesos = 100%
        
        **Métricas Estadísticas:**
        - **Skewness**: Medida de asimetría de la distribución
        - **Kurtosis**: Medida de la forma de la distribución (colas)
        - **Jarque-Bera**: Test de normalidad de los retornos
        - **VaR 95%**: Valor en riesgo al 95% de confianza
        """)

def mostrar_analisis_tecnico(token_acceso, id_cliente):
    st.markdown("### 📊 Análisis Técnico")
    
    with st.spinner("Obteniendo portafolio..."):
        portafolio = obtener_portafolio(token_acceso, id_cliente)
    
    if not portafolio:
        st.warning("No se pudo obtener el portafolio del cliente")
        return
    
    activos = portafolio.get('activos', [])
    if not activos:
        st.warning("El portafolio está vacío")
        return
    
    simbolos = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', '')
        if simbolo:
            simbolos.append(simbolo)
    
    if not simbolos:
        st.warning("No se encontraron símbolos válidos")
        return
    
    simbolo_seleccionado = st.selectbox(
        "Seleccione un activo para análisis técnico:",
        options=simbolos
    )
    
    if simbolo_seleccionado:
        st.info(f"Mostrando gráfico para: {simbolo_seleccionado}")
        
        # Widget de TradingView
        tv_widget = f"""
        <div id="tradingview_{simbolo_seleccionado}" style="height:650px"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
          "container_id": "tradingview_{simbolo_seleccionado}",
          "width": "100%",
          "height": 650,
          "symbol": "{simbolo_seleccionado}",
          "interval": "D",
          "timezone": "America/Argentina/Buenos_Aires",
          "theme": "light",
          "style": "1",
          "locale": "es",
          "toolbar_bg": "#f4f7f9",
          "enable_publishing": false,
          "allow_symbol_change": true,
          "hide_side_toolbar": false,
          "studies": [
            "MACD@tv-basicstudies",
            "RSI@tv-basicstudies",
            "StochasticRSI@tv-basicstudies",
            "Volume@tv-basicstudies",
            "Moving Average@tv-basicstudies"
          ],
          "drawings_access": {{
            "type": "black",
            "tools": [
              {{"name": "Trend Line"}},
              {{"name": "Horizontal Line"}},
              {{"name": "Fibonacci Retracement"}},
              {{"name": "Rectangle"}},
              {{"name": "Text"}}
            ]
          }},
          "enabled_features": [
            "study_templates",
            "header_indicators",
            "header_compare",
            "header_screenshot",
            "header_fullscreen_button",
            "header_settings",
            "header_symbol_search"
          ]
        }});
        </script>
        """
        components.html(tv_widget, height=680)

def vender_especie_d(token_portador, id_cliente, simbolo, cantidad, precio, mercado, validez, cuenta_comitente=None):
    """
    Realiza una operación de venta de especie D a través de la API de IOL.
    
    Args:
        token_portador (str): Token de autenticación
        id_cliente (str): ID del cliente
        simbolo (str): Símbolo del activo a vender
        cantidad (int): Cantidad a vender
        precio (float): Precio de venta
        mercado (str): Mercado donde se opera (ej: 'bCBA')
        validez (str): Fecha de validez de la orden (formato 'YYYY-MM-DD')
        cuenta_comitente (str, optional): Número de cuenta comitente
        
    Returns:
        dict: Respuesta de la API o None en caso de error
    """
    url = f"https://api.invertironline.com/api/v2/asesores/operar/VenderEspecieD"
    
    headers = {
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "clientes": clientes,
        "fechaDesde": fecha_desde,
        "fechaHasta": fecha_hasta,
        "tipoFecha": tipo_fecha,
        "estado": estado,
        "tipoOperacion": tipo_operacion,
        "moneda": moneda
    }
    
    # Eliminar campos None del payload
    data = {k: v for k, v in data.items() if v is not None}
    
    st.info(f"Solicitando movimientos desde {fecha_desde} hasta {fecha_hasta}...")
    
    # Configurar timeout y realizar la petición
    try:
        response = requests.post(
            url, 
            headers=headers, 
            json=data,
            timeout=30  # 30 segundos de timeout
        )
        
        # Verificar si la respuesta es exitosa
        response.raise_for_status()
        
        # Intentar decodificar la respuesta JSON
        try:
            return response.json()
        except ValueError as json_err:
            st.error("❌ Error al decodificar la respuesta JSON")
            st.error(f"Contenido de la respuesta: {response.text[:500]}")
            return None
            
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 401:
            st.error("🔒 Error de autenticación. Por favor, inicie sesión nuevamente.")
            # Limpiar la sesión para forzar un nuevo inicio de sesión
            if 'token_acceso' in st.session_state:
                del st.session_state['token_acceso']
            if 'refresh_token' in st.session_state:
                del st.session_state['refresh_token']
        elif http_err.response.status_code == 500:
            st.error("⚠️ Error interno del servidor al procesar la solicitud.")
            st.info("Sugerencias:")
            st.info("1. Verifique que las fechas sean válidas")
            st.info("2. Intente con un rango de fechas más pequeño")
            st.info("3. Si el problema persiste, intente más tarde")
        else:
            st.error(f"❌ Error HTTP {http_err.response.status_code}: {str(http_err)}")
        
        # Mostrar detalles adicionales del error si están disponibles
        try:
            error_details = http_err.response.json()
            st.json(error_details)
        except:
            st.error(f"Detalles del error: {http_err.response.text[:500]}")
            
    except requests.exceptions.RequestException as req_err:
        st.error(f"❌ Error de conexión: {str(req_err)}")
        
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
        
    return None


def obtener_movimientos_asesor(token_portador, clientes, fecha_desde, fecha_hasta, tipo_fecha='fechaOperacion', 
                            estado=None, tipo_operacion=None, moneda='ARS'):
    """
    Obtiene los movimientos de los clientes del asesor con manejo mejorado de errores.
    
    Args:
        token_portador (str): Token de autenticación
        clientes (list): Lista de IDs de clientes
        fecha_desde (str): Fecha de inicio en formato 'YYYY-MM-DD'
        fecha_hasta (str): Fecha de fin en formato 'YYYY-MM-DD'
        tipo_fecha (str): Tipo de fecha a filtrar ('fechaOperacion' o 'fechaLiquidacion')
        estado (str, optional): Estado de las operaciones a filtrar
        tipo_operacion (str, optional): Tipo de operación a filtrar
        moneda (str, optional): Moneda de las operaciones (por defecto 'ARS')
        
    Returns:
        list or dict: Lista de movimientos o diccionario con error en caso de fallo
    """
    try:
        if not token_portador:
            st.error("🔑 No se encontró el token de acceso. Por favor inicie sesión nuevamente.")
            return None
            
        # Validar fechas
        try:
            datetime.strptime(fecha_desde, '%Y-%m-%d')
            datetime.strptime(fecha_hasta, '%Y-%m-%d')
        except ValueError:
            st.error("❌ Formato de fecha inválido. Use YYYY-MM-DD")
            return None
            
        url = "https://api.invertironline.com/api/v2/asesores/movimientos"
        headers = {
            'Authorization': f'Bearer {token_portador}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Formatear fechas en formato ISO 8601
        fecha_desde_iso = f"{fecha_desde}T00:00:00.000Z"
        fecha_hasta_iso = f"{fecha_hasta}T23:59:59.999Z"
        
        # Construir el payload según la documentación de la API
        data = {
            'clientes': clientes,
            'from': fecha_desde_iso,
            'to': fecha_hasta_iso,
            'tipoFecha': tipo_fecha,
            'pais': 'AR',
            'moneda': moneda
        }
        
        # Agregar filtros opcionales si se proporcionan
        if estado:
            data['estado'] = estado
        if tipo_operacion:
            data['tipoOperacion'] = tipo_operacion
            
        st.info(f"Solicitando movimientos desde {fecha_desde} hasta {fecha_hasta}...")
        
        # Realizar la petición con manejo de timeout
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30  # 30 segundos de timeout
        )
        
        # Verificar el estado de la respuesta
        response.raise_for_status()
        
        # Verificar si la respuesta es un JSON válido
        try:
            movimientos = response.json()
            if not movimientos:
                st.warning("No se encontraron movimientos para el período seleccionado.")
                return []
            return movimientos
            
        except ValueError as json_err:
            st.error(f"Error al procesar la respuesta del servidor: {str(json_err)}")
            st.text(f"Respuesta recibida: {response.text[:500]}...")  # Mostrar primeros 500 caracteres
            return None
            
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 401:
            st.error("🔒 Error de autenticación (401). Por favor verifica tu token de acceso y vuelve a iniciar sesión.")
            # Limpiar la sesión para forzar un nuevo inicio de sesión
            if 'token_acceso' in st.session_state:
                del st.session_state['token_acceso']
            if 'refresh_token' in st.session_state:
                del st.session_state['refresh_token']
        elif http_err.response.status_code == 500:
            st.error("⚠️ Error interno del servidor al procesar la solicitud.")
            st.info("Sugerencias para solucionar el problema:")
            st.info("1. Verifique que las fechas sean válidas")
            st.info("2. Intente con un rango de fechas más pequeño")
            st.info("3. Si el problema persiste, intente más tarde")
            
            # Mostrar detalles del error si están disponibles
            try:
                error_details = http_err.response.json()
                st.json(error_details)
            except:
                st.error(f"Detalles del error: {http_err.response.text[:500]}")
        else:
            st.error(f"❌ Error HTTP {http_err.response.status_code}: {str(http_err)}")
            try:
                st.json(http_err.response.json())
            except:
                st.error(f"Detalles: {http_err.response.text[:500]}")
        
        return None
        
    except requests.exceptions.RequestException as req_err:
        st.error(f"❌ Error de conexión: {str(req_err)}")
        if hasattr(req_err, 'response') and req_err.response is not None:
            st.error(f"Respuesta del servidor: {req_err.response.text[:500]}")
        return None
        
    except Exception as e:
        st.error(f"❌ Error inesperado al obtener movimientos: {str(e)}")
        import traceback
        st.text(traceback.format_exc())
        return None


def mostrar_venta_especie_d():
    st.title("📉 Venta de Especie D")
    # ... (rest of the code remains the same)
    
    if 'token_acceso' not in st.session_state or not st.session_state.token_acceso:
        st.error("No se encontró token de acceso. Por favor, inicie sesión.")
        return
        
    if 'cliente_seleccionado' not in st.session_state or not st.session_state.cliente_seleccionado:
        st.warning("Por favor, seleccione un cliente primero.")
        return
    
    with st.form("venta_especie_d_form"):
        st.subheader("Datos de la Operación")
        
        # Obtener datos del cliente
        cliente = st.session_state.cliente_seleccionado
        cliente_id = cliente.get('numeroCliente', cliente.get('id'))
        
        # Campos del formulario
        simbolo = st.text_input("Símbolo", placeholder="Ej: GGAL")
        cantidad = st.number_input("Cantidad", min_value=1, step=1, value=1)
        precio = st.number_input("Precio", min_value=0.0, step=0.01, format="%.2f")
        
        # Selector de mercado
        mercado = st.selectbox(
            "Mercado",
            ["bCBA", "bCBA24hs", "bCBAp", "bBYMA", "bROFX"]
        )
        
        # Fecha de validez (hoy + 1 día por defecto)
        validez = st.date_input(
            "Válido hasta",
            value=date.today() + timedelta(days=1),
            min_value=date.today()
        )
        
        # Cuenta comitente (opcional)
        cuenta_comitente = st.text_input("Cuenta Comitente (opcional)", "")
        
        # Botón de envío
        if st.form_submit_button("📤 Enviar Orden de Venta", use_container_width=True):
            if not all([simbolo, cantidad, precio, mercado, validez]):
                st.error("Por favor complete todos los campos obligatorios.")
                return
                
            with st.spinner("Procesando orden de venta..."):
                resultado = vender_especie_d(
                    token_portador=st.session_state.token_acceso,
                    id_cliente=cliente_id,
                    simbolo=simbolo.upper(),
                    cantidad=int(cantidad),
                    precio=float(precio),
                    mercado=mercado,
                    validez=validez.strftime("%Y-%m-%d"),
                    cuenta_comitente=cuenta_comitente if cuenta_comitente else None
                )
                
                if resultado:
                    st.success("✅ Orden de venta enviada correctamente")
                    st.json(resultado)


def mostrar_movimientos_asesor():
    st.title("👨‍💼 Panel del Asesor")
    
    if 'token_acceso' not in st.session_state or not st.session_state.token_acceso:
        st.error("Debe iniciar sesión primero")
        return
        
    token_acceso = st.session_state.token_acceso
    
    # Obtener lista de clientes
    clientes = obtener_lista_clientes(token_acceso)
    if not clientes:
        st.warning("No se encontraron clientes")
        return
    
    # Formulario de búsqueda
    with st.form("form_buscar_movimientos"):
        st.subheader("🔍 Buscar Movimientos")
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_desde = st.date_input("Fecha desde", value=date.today() - timedelta(days=30))
        with col2:
            fecha_hasta = st.date_input("Fecha hasta", value=date.today())
        
        # Selección múltiple de clientes
        cliente_opciones = [{"label": f"{c.get('apellidoYNombre', c.get('nombre', 'Cliente'))} ({c.get('numeroCliente', c.get('id', ''))})", 
                           "value": c.get('numeroCliente', c.get('id'))} for c in clientes]
        
        clientes_seleccionados = st.multiselect(
            "Seleccione clientes",
            options=[c['value'] for c in cliente_opciones],
            format_func=lambda x: next((c['label'] for c in cliente_opciones if c['value'] == x), x),
            default=[cliente_opciones[0]['value']] if cliente_opciones else []
        )
        
        # Filtros adicionales
        col1, col2 = st.columns(2)
        with col1:
            tipo_fecha = st.selectbox(
                "Tipo de fecha",
                ["fechaOperacion", "fechaLiquidacion"],
                index=0
            )
            estado = st.selectbox(
                "Estado",
                ["", "Pendiente", "Aprobado", "Rechazado"],
                index=0
            )
        with col2:
            tipo_operacion = st.text_input("Tipo de operación")
            moneda = st.text_input("Moneda", "ARS")
        
        buscar = st.form_submit_button("🔍 Buscar movimientos")
    
    if buscar and clientes_seleccionados:
        with st.spinner("Buscando movimientos..."):
            movimientos = obtener_movimientos_asesor(
                token_portador=token_acceso,
                clientes=clientes_seleccionados,
                fecha_desde=fecha_desde.isoformat(),
                fecha_hasta=fecha_hasta.isoformat(),
                tipo_fecha=tipo_fecha,
                estado=estado or None,
                tipo_operacion=tipo_operacion or None,
                moneda=moneda or None
            )
            
            if movimientos and isinstance(movimientos, list):
                df = pd.DataFrame(movimientos)
                if not df.empty:
                    st.subheader("📋 Resultados de la búsqueda")
                    st.dataframe(df, use_container_width=True)
                    
                    # Mostrar resumen
                    st.subheader("📊 Resumen de Movimientos")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Movimientos", len(df))
                    
                    if 'monto' in df.columns:
                        col2.metric("Monto Total", f"${df['monto'].sum():,.2f}")
                    
                    if 'estado' in df.columns:
                        estados = df['estado'].value_counts().to_dict()
                        col3.metric("Estados", ", ".join([f"{k} ({v})" for k, v in estados.items()]))
                else:
                    st.info("No se encontraron movimientos con los filtros seleccionados")
            else:
                st.warning("No se encontraron movimientos o hubo un error en la consulta")
                if movimientos and not isinstance(movimientos, list):
                    st.json(movimientos)  # Mostrar respuesta cruda para depuración

def mostrar_analisis_portafolio():
    cliente = st.session_state.cliente_seleccionado
    token_acceso = st.session_state.token_acceso

    if not cliente:
        st.error("No se ha seleccionado ningún cliente")
        return
        
    # Inicializar el gestor de portafolio en session_state si no existe
    if 'portfolio_manager' not in st.session_state:
        st.session_state.portfolio_manager = None

    id_cliente = cliente.get('numeroCliente', cliente.get('id'))
    nombre_cliente = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))

    st.title(f"Análisis de Portafolio - {nombre_cliente}")
    
    # Crear tabs con iconos
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Resumen Portafolio", 
        "💰 Estado de Cuenta", 
        "📊 Análisis Técnico",
        "💱 Cotizaciones",
        "🔄 Optimización",
        "📉 Análisis de Volatilidad"
    ])

    with tab1:
        portafolio = obtener_portafolio(token_acceso, id_cliente)
        if portafolio:
            mostrar_resumen_portafolio(portafolio, token_acceso)
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
        mostrar_optimizacion_portafolio(token_acceso, id_cliente)
        
    with tab6:
        st.header("📊 Análisis de Volatilidad")
        
        # Obtener datos históricos
        portafolio = obtener_portafolio(token_acceso, id_cliente)
        if not portafolio or 'activos' not in portafolio or not portafolio['activos']:
            st.warning("No hay activos en el portafolio para analizar")
        else:
            # Mostrar selector de activos
            activos = portafolio['activos']
            simbolos = [a['titulo']['simbolo'] for a in activos if 'titulo' in a and 'simbolo' in a['titulo']]
            
            if not simbolos:
                st.warning("No se encontraron símbolos válidos para analizar")
            else:
                simbolo_seleccionado = st.selectbox(
                    "Seleccione un activo para analizar:",
                    options=simbolos,
                    key="vol_asset_selector"
                )
                
                # Configuración del análisis
                with st.expander("⚙️ Configuración del análisis", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        n_simulaciones = st.number_input(
                            "Número de simulaciones",
                            min_value=100,
                            max_value=10000,
                            value=1000,
                            step=100,
                            help="Cantidad de trayectorias a simular en el análisis de Monte Carlo"
                        )
                    with col2:
                        dias_proyeccion = st.number_input(
                            "Días de proyección",
                            min_value=5,
                            max_value=365,
                            value=30,
                            step=5,
                            help="Horizonte temporal para las proyecciones"
                        )
                
                # Botón para ejecutar el análisis
                if st.button("🔍 Analizar Volatilidad", use_container_width=True):
                    with st.spinner("Realizando análisis de volatilidad..."):
                        try:
                            # Inicializar el gestor de portafolio si no existe
                            if st.session_state.portfolio_manager is None:
                                st.session_state.portfolio_manager = PortfolioManager(
                                    activos=[{'simbolo': s} for s in simbolos],
                                    token=token_acceso,
                                    fecha_desde=(date.today() - timedelta(days=365)).strftime('%Y-%m-%d'),
                                    fecha_hasta=date.today().strftime('%Y-%m-%d')
                                )
                                
                                # Cargar datos históricos
                                if not st.session_state.portfolio_manager.load_data():
                                    st.error("Error al cargar datos históricos")
                                    return
                            
                            # Obtener retornos del activo seleccionado
                            if simbolo_seleccionado in st.session_state.portfolio_manager.returns:
                                returns = st.session_state.portfolio_manager.returns[simbolo_seleccionado]
                                
                                # Realizar análisis de volatilidad
                                result = st.session_state.portfolio_manager.analyze_volatility(
                                    symbol=simbolo_seleccionado,
                                    returns=returns,
                                    n_simulations=n_simulaciones,
                                    n_days=dias_proyeccion
                                )
                                
                                if result is not None:
                                    # Mostrar gráficos
                                    fig = st.session_state.portfolio_manager.plot_volatility_analysis(simbolo_seleccionado)
                                    if fig is not None:
                                        st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning(f"No se encontraron datos de retornos para {simbolo_seleccionado}")
                                
                        except Exception as e:
                            st.error(f"Error en el análisis de volatilidad: {str(e)}")
                            st.exception(e)

@st.cache_data(ttl=300, show_spinner=False)
def load_initial_data():
    """Load initial data with caching"""
    return {
        'fecha_desde': date.today() - timedelta(days=365),
        'fecha_hasta': date.today()
    }

def main():
    # Initialize session state with cached data
    initial_data = load_initial_data()
    
    # Initialize session state with persistent storage
    if 'initialized' not in st.session_state:
        st.session_state.update({
            'token_acceso': None,
            'refresh_token': None,
            'clientes': [],
            'cliente_seleccionado': None,
            'fecha_desde': initial_data['fecha_desde'],
            'fecha_hasta': initial_data['fecha_hasta'],
            '_last_updated': time.time(),
            'initialized': True,
            'show_frontier': True,
            'show_efficient_frontier': False,
            'user_authenticated': False
        })
    
    # Set page config and title
    st.set_page_config(
        page_title="IOL Portfolio Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
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
                                st.session_state.update({
                                    'token_acceso': token_acceso,
                                    'refresh_token': refresh_token,
                                    'user_authenticated': True,
                                    'last_activity': time.time()
                                })
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
            
            # Cargar lista de clientes si no está en el estado de la sesión
    if not st.session_state.clientes and st.session_state.token_acceso:
        with st.spinner("Cargando clientes..."):
            try:
                clientes = obtener_lista_clientes(st.session_state.token_acceso)
                if clientes and 'error' not in clientes:
                    st.session_state.clientes = clientes
                else:
                    error_msg = clientes.get('error', 'No se pudo obtener la lista de clientes') if isinstance(clientes, dict) else 'No se encontraron clientes'
                    st.warning(f"{error_msg}. Por favor, verifique su conexión y permisos.")
            except Exception as e:
                st.error(f"Error al cargar clientes: {str(e)}")
                if "401" in str(e):
                    st.warning("Sesión expirada. Por favor, vuelva a iniciar sesión.")
                    st.session_state.token_acceso = None
                    st.session_state.refresh_token = None
                    st.rerun()

    # Contenido principal
    try:
        if st.session_state.token_acceso:
            # Mostrar selector de cliente en la barra lateral
            with st.sidebar:
                st.header("👤 Cliente")
                if st.session_state.clientes:
                    cliente_ids = [c.get('numeroCliente', c.get('id')) for c in st.session_state.clientes]
                    cliente_nombres = [c.get('apellidoYNombre', c.get('nombre', f'Cliente {i}')) for i, c in enumerate(st.session_state.clientes, 1)]
                    
                    # Mostrar el selector de cliente con el nombre completo
                    cliente_seleccionado = st.selectbox(
                        "Seleccione un cliente:",
                        options=cliente_ids,
                        format_func=lambda x: cliente_nombres[cliente_ids.index(x)],
                        key="cliente_selector"
                    )
                    
                    # Actualizar el cliente seleccionado en el estado de la sesión
                    st.session_state.cliente_seleccionado = next(
                        (c for c in st.session_state.clientes 
                         if c.get('numeroCliente', c.get('id')) == cliente_seleccionado),
                        None
                    )
                    
                    # Mostrar información del cliente seleccionado
                    if st.session_state.cliente_seleccionado:
                        cliente = st.session_state.cliente_seleccionado
                        st.caption(f"💼 {cliente.get('tipoPersona', 'Cliente')}")
                        if 'cuentas' in cliente:
                            st.caption(f"📋 {len(cliente['cuentas'])} cuentas")
                        
                        # Botón para actualizar la lista de clientes
                        if st.button("🔄 Actualizar lista de clientes", use_container_width=True):
                            with st.spinner("Actualizando..."):
                                nuevos_clientes = obtener_lista_clientes(st.session_state.token_acceso)
                                if nuevos_clientes and 'error' not in nuevos_clientes:
                                    st.session_state.clientes = nuevos_clientes
                                    st.success("✅ Lista actualizada")
                                    st.rerun()
                                else:
                                    st.error("Error al actualizar la lista de clientes")
                else:
                    st.warning("No se encontraron clientes")
                    if st.button("🔄 Reintentar carga de clientes"):
                        st.rerun()
            
            st.sidebar.header("📋 Menú")
            # Menú principal
            opciones_menu = [
                "📊 Resumen del Portafolio",
                "📈 Cotizaciones de Mercado",
                "🔍 Optimización de Portafolio",
                "📉 Análisis Técnico",
                "📊 Análisis de Portafolio",
                "📝 Test de Perfil de Inversor"
            ]
            
            # Opciones adicionales para asesores
            if st.session_state.token_acceso and st.session_state.cliente_seleccionado:
                opciones_menu.append("👤 Movimientos del Asesor")
            
            # Submenú para operaciones de Dólar MEP
            if st.session_state.token_acceso and st.session_state.cliente_seleccionado and "📈 Cotizaciones de Mercado" in opciones_menu:
                # Insertar después de Cotizaciones de Mercado
                idx = opciones_menu.index("📈 Cotizaciones de Mercado")
                if "   📉 Vender Especie D" not in opciones_menu:
                    opciones_menu.insert(idx + 1, "   📉 Vender Especie D")
            
            opcion_seleccionada = st.sidebar.radio("Navegación", opciones_menu)
            
            # Mostrar la página seleccionada
            if opcion_seleccionada == "🏠 Inicio":
                st.info("👆 Seleccione una opción del menú para comenzar")
            elif opcion_seleccionada == "📊 Resumen del Portafolio":
                st.title("Resumen del Portafolio")
                if st.session_state.token_acceso and st.session_state.cliente_seleccionado:
                    cliente_id = st.session_state.cliente_seleccionado.get('numeroCliente', st.session_state.cliente_seleccionado.get('id'))
                    portafolio = obtener_portafolio(st.session_state.token_acceso, cliente_id)
                    if portafolio:
                        mostrar_resumen_portafolio(portafolio, st.session_state.token_acceso)
                    else:
                        st.warning("No se pudo obtener el portafolio")
                else:
                    st.warning("Por favor, seleccione un cliente primero")
                
            elif opcion_seleccionada == "📈 Cotizaciones de Mercado":
                st.title("Cotizaciones de Mercado")
                if st.session_state.token_acceso:
                    mostrar_cotizaciones_mercado(st.session_state.token_acceso)
                else:
                    st.warning("No se pudo autenticar con IOL")
                    
            elif opcion_seleccionada.strip() == "📉 Vender Especie D":
                # Mostrar la interfaz de Vender Especie D
                if st.session_state.token_acceso and st.session_state.cliente_seleccionado:
                    cliente_id = st.session_state.cliente_seleccionado.get('numeroCliente', 
                                 st.session_state.cliente_seleccionado.get('id'))
                    mostrar_venta_especie_d(st.session_state.token_acceso, cliente_id)
                else:
                    st.warning("Por favor, seleccione un cliente primero")
                
            elif opcion_seleccionada == "🔍 Optimización de Portafolio":
                st.title("Optimización de Portafolio")
                if st.session_state.token_acceso and st.session_state.cliente_seleccionado:
                    cliente_id = st.session_state.cliente_seleccionado.get('numeroCliente', st.session_state.cliente_seleccionado.get('id'))
                    mostrar_optimizacion_portafolio(st.session_state.token_acceso, cliente_id)
                else:
                    st.warning("Por favor, seleccione un cliente primero")
                
            elif opcion_seleccionada == "📉 Análisis Técnico":
                st.title("Análisis Técnico")
                if st.session_state.token_acceso and st.session_state.cliente_seleccionado:
                    cliente_id = st.session_state.cliente_seleccionado.get('numeroCliente', st.session_state.cliente_seleccionado.get('id'))
                    mostrar_analisis_tecnico(st.session_state.token_acceso, cliente_id)
                else:
                    st.warning("Por favor, seleccione un cliente primero")
                
            elif opcion_seleccionada == "📊 Análisis de Portafolio":
                mostrar_analisis_portafolio()
                
            elif opcion_seleccionada == "👤 Movimientos del Asesor":
                if st.session_state.token_acceso:
                    mostrar_movimientos_asesor()
                else:
                    st.warning("No se pudo autenticar con IOL")
                    
            elif opcion_seleccionada == "📉 Vender Especie D":
                if st.session_state.token_acceso and st.session_state.cliente_seleccionado:
                    mostrar_venta_especie_d()
                else:
                    st.warning("Por favor, seleccione un cliente primero")
                
            elif opcion_seleccionada == "📝 Test de Perfil de Inversor":
                st.title("Test de Perfil de Inversor")
                if st.session_state.token_acceso and st.session_state.cliente_seleccionado:
                    cliente_id = st.session_state.cliente_seleccionado.get('numeroCliente', st.session_state.cliente_seleccionado.get('id'))
                    mostrar_test_perfil_inversor(st.session_state.token_acceso, cliente_id)
                else:
                    st.warning("Por favor, seleccione un cliente primero")
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
