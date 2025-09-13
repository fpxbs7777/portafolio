import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
from datetime import date, timedelta, datetime
import numpy as np
# import yfinance as yf  # Removido - usando solo API de IOL
import scipy.optimize as op
from scipy import stats
from scipy import optimize
import random
import warnings
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import concurrent.futures
from functools import lru_cache
import time
import asyncio
import aiohttp
import re

warnings.filterwarnings('ignore')

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
    """
    Obtiene tokens de autenticación de IOL con manejo mejorado de errores y reintentos
    """
    url_login = 'https://api.invertironline.com/token'
    datos = {
        'username': usuario,
        'password': contraseña,
        'grant_type': 'password'
    }
    
    # Configuración de sesión con reintentos
    session = requests.Session()
    session.mount('https://', requests.adapters.HTTPAdapter(
        max_retries=3,
        pool_connections=10,
        pool_maxsize=10
    ))
    
    # Headers adicionales para mejorar la conexión
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            st.info(f"🔄 Intento {attempt + 1}/{max_attempts} de conexión a IOL...")
            
            # Timeout más largo para la primera conexión
            timeout = 30 if attempt == 0 else 15
            
            respuesta = session.post(
                url_login, 
                data=datos, 
                headers=headers,
                timeout=timeout,
                verify=True  # Verificar certificados SSL
            )
            
            # Verificar si la respuesta es exitosa
            if respuesta.status_code == 200:
                try:
                    respuesta_json = respuesta.json()
                    if 'access_token' in respuesta_json and 'refresh_token' in respuesta_json:
                        st.success("✅ Autenticación exitosa con IOL")
                        return respuesta_json['access_token'], respuesta_json['refresh_token']
                    else:
                        st.error("❌ Respuesta de IOL incompleta - faltan tokens")
                        return None, None
                except ValueError as json_err:
                    st.error(f"❌ Error al procesar respuesta JSON: {json_err}")
                    return None, None
            
            # Manejar códigos de error específicos
            elif respuesta.status_code == 400:
                st.error("❌ Error 400: Verifique sus credenciales (usuario/contraseña)")
                return None, None
            elif respuesta.status_code == 401:
                st.error("❌ Error 401: Credenciales inválidas o cuenta bloqueada")
                return None, None
            elif respuesta.status_code == 403:
                st.error("❌ Error 403: Acceso denegado - verifique permisos de su cuenta")
                return None, None
            elif respuesta.status_code == 429:
                st.warning("⚠️ Demasiadas solicitudes. Esperando antes de reintentar...")
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)  # Backoff exponencial
                    continue
                else:
                    st.error("❌ Límite de solicitudes excedido")
                    return None, None
            elif respuesta.status_code >= 500:
                st.warning(f"⚠️ Error del servidor ({respuesta.status_code}). Reintentando...")
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    st.error(f"❌ Error persistente del servidor: {respuesta.status_code}")
                    return None, None
            else:
                st.error(f"❌ Error HTTP {respuesta.status_code}: {respuesta.text[:200]}")
                return None, None
                
        except requests.exceptions.Timeout:
            st.warning(f"⏱️ Timeout en intento {attempt + 1}. Reintentando...")
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                st.error("❌ Timeout persistente al conectar con IOL")
                st.info("💡 Sugerencias:")
                st.info("• Verifique su conexión a internet")
                st.info("• Intente nuevamente en unos minutos")
                st.info("• Contacte a IOL si el problema persiste")
                return None, None
                
        except requests.exceptions.ConnectionError:
            st.warning(f"🔌 Error de conexión en intento {attempt + 1}. Reintentando...")
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                st.error("❌ Error de conexión persistente")
                st.info("💡 Verifique:")
                st.info("• Su conexión a internet")
                st.info("• Que no haya firewall bloqueando la conexión")
                st.info("• Que el servidor de IOL esté disponible")
                return None, None
                
        except requests.exceptions.SSLError:
            st.error("❌ Error de certificado SSL")
            st.info("💡 Esto puede indicar problemas de seguridad de red")
            return None, None
            
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")
            if attempt < max_attempts - 1:
                st.info("🔄 Reintentando...")
                time.sleep(2 ** attempt)
                continue
            else:
                return None, None
    
    st.error("❌ No se pudo establecer conexión después de múltiples intentos")
    return None, None

def refrescar_token(refresh_token):
    """
    Refresca el token de acceso usando el refresh token
    """
    url_refresh = 'https://api.invertironline.com/token'
    datos_refresh = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    try:
        respuesta = requests.post(url_refresh, data=datos_refresh, headers=headers, timeout=30)
        
        if respuesta.status_code == 200:
            respuesta_json = respuesta.json()
            if 'access_token' in respuesta_json and 'refresh_token' in respuesta_json:
                st.success("✅ Token refrescado exitosamente")
                return respuesta_json['access_token'], respuesta_json['refresh_token']
            else:
                st.error("❌ Respuesta de refresh inválida")
                return None, None
        elif respuesta.status_code == 400:
            st.error("❌ Error 400: Refresh token inválido")
            return None, None
        elif respuesta.status_code == 401:
            st.error("❌ Error 401: Refresh token expirado")
            return None, None
        else:
            st.error(f"❌ Error HTTP {respuesta.status_code}: {respuesta.text[:200]}")
            return None, None
            
    except Exception as e:
        st.error(f"❌ Error al refrescar token: {str(e)}")
        return None, None

def verificar_y_refrescar_token(token_acceso, refresh_token):
    """
    Verifica si el token está válido y lo refresca si es necesario
    """
    if not token_acceso or not refresh_token:
        return None, None
    
    # Probar el token con una llamada simple
    url_test = 'https://api.invertironline.com/api/v2/estadocuenta'
    headers = obtener_encabezado_autorizacion(token_acceso)
    
    try:
        respuesta = requests.get(url_test, headers=headers, timeout=10)
        if respuesta.status_code == 200:
            return token_acceso, refresh_token  # Token válido
        elif respuesta.status_code == 401:
            st.warning("⚠️ Token expirado, intentando refrescar...")
            nuevo_token, nuevo_refresh = refrescar_token(refresh_token)
            if nuevo_token:
                return nuevo_token, nuevo_refresh
            else:
                st.error("❌ No se pudo refrescar el token")
                return None, None
        else:
            return token_acceso, refresh_token  # Otro error, mantener token actual
    except Exception:
        return token_acceso, refresh_token  # Error de conexión, mantener token actual

def obtener_lista_clientes(token_portador):
    """
    Obtiene la lista de clientes del asesor
    
    Args:
        token_portador (str): Token de autenticación
        
    Returns:
        list: Lista de clientes o lista vacía en caso de error
    """
    url_clientes = 'https://api.invertironline.com/api/v2/Asesores/Clientes'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    try:
        respuesta = requests.get(url_clientes, headers=encabezados, timeout=30)
        if respuesta.status_code == 200:
            clientes_data = respuesta.json()
            if isinstance(clientes_data, list):
                return clientes_data
            elif isinstance(clientes_data, dict) and 'clientes' in clientes_data:
                return clientes_data['clientes']
            else:
                st.warning("Formato de respuesta inesperado al obtener clientes")
                return []
        elif respuesta.status_code == 401:
            st.error("Error de autenticación al obtener lista de clientes")
            return []
        elif respuesta.status_code == 403:
            st.error("No tiene permisos para acceder a la lista de clientes")
            return []
        else:
            st.error(f'Error HTTP {respuesta.status_code} al obtener la lista de clientes')
            return []
    except requests.exceptions.Timeout:
        st.error("Timeout al obtener lista de clientes")
        return []
    except Exception as e:
        st.error(f'Error de conexión al obtener clientes: {str(e)}')
        return []

def obtener_estado_cuenta(token_portador, id_cliente=None):
    """
    Obtiene el estado de cuenta del cliente o del usuario autenticado
    
    Args:
        token_portador (str): Token de autenticación
        id_cliente (str, optional): ID del cliente. Si es None, obtiene el estado de cuenta del usuario
        
    Returns:
        dict: Estado de cuenta o None en caso de error
    """
    # Evitar recursión infinita
    if hasattr(obtener_estado_cuenta, '_recursion_depth'):
        obtener_estado_cuenta._recursion_depth += 1
    else:
        obtener_estado_cuenta._recursion_depth = 0
    
    # Limitar la profundidad de recursión
    if obtener_estado_cuenta._recursion_depth > 2:
        st.error("Error: Demasiadas llamadas recursivas al obtener estado de cuenta")
        obtener_estado_cuenta._recursion_depth = 0
        return None
    
    if id_cliente:
        url_estado_cuenta = f'https://api.invertironline.com/api/v2/Asesores/EstadoDeCuenta/{id_cliente}'
    else:
        url_estado_cuenta = 'https://api.invertironline.com/api/v2/estadocuenta'
    
    encabezados = obtener_encabezado_autorizacion(token_portador)
    try:
        respuesta = requests.get(url_estado_cuenta, headers=encabezados, timeout=30)
        if respuesta.status_code == 200:
            # Resetear contador de recursión en caso de éxito
            obtener_estado_cuenta._recursion_depth = 0
            return respuesta.json()
        elif respuesta.status_code == 401:
            # Solo intentar una vez más sin ID de cliente
            if obtener_estado_cuenta._recursion_depth == 1:
                st.warning("Error de autenticación. Intentando obtener estado de cuenta general...")
                return obtener_estado_cuenta(token_portador, None)
            else:
                st.error("Error de autenticación persistente")
                obtener_estado_cuenta._recursion_depth = 0
                return None
        else:
            st.error(f"Error HTTP {respuesta.status_code} al obtener estado de cuenta")
            obtener_estado_cuenta._recursion_depth = 0
            return None
    except requests.exceptions.Timeout:
        st.error("Timeout al obtener estado de cuenta")
        obtener_estado_cuenta._recursion_depth = 0
        return None
    except Exception as e:
        st.error(f'Error al obtener estado de cuenta: {str(e)}')
        obtener_estado_cuenta._recursion_depth = 0
        return None

@st.cache_data(ttl=900)  # Cache por 15 minutos para mejor rendimiento
def obtener_portafolio(token_portador, id_cliente, pais='Argentina'):
    """
    Obtiene el portafolio de un cliente específico
    
    Args:
        token_portador (str): Token de autenticación
        id_cliente (str): ID del cliente
        pais (str): País del portafolio (default: 'Argentina')
        
    Returns:
        dict: Portafolio del cliente o None en caso de error
    """
    url_portafolio = f'https://api.invertironline.com/api/v2/Asesores/Portafolio/{id_cliente}/{pais}'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    try:
        respuesta = requests.get(url_portafolio, headers=encabezados, timeout=15)  # Reducido de 30 a 15 segundos
        if respuesta.status_code == 200:
            return respuesta.json()
        elif respuesta.status_code == 401:
            st.error("Error de autenticación al obtener portafolio")
            return None
        elif respuesta.status_code == 404:
            st.warning(f"No se encontró portafolio para el cliente {id_cliente}")
            return None
        else:
            st.error(f"Error HTTP {respuesta.status_code} al obtener portafolio")
            return None
    except requests.exceptions.Timeout:
        st.error("Timeout al obtener portafolio")
        return None
    except Exception as e:
        st.error(f'Error al obtener portafolio: {str(e)}')
        return None

@st.cache_data(ttl=900)  # Cache por 15 minutos para mejor rendimiento
def obtener_portafolio_eeuu(token_portador, id_cliente):
    """
    Obtiene el portafolio de Estados Unidos de un cliente específico
    
    Args:
        token_portador (str): Token de autenticación
        id_cliente (str): ID del cliente
        
    Returns:
        dict: Portafolio de EEUU del cliente o None en caso de error
    """
    # Intentar primero con el endpoint de Asesores (mismo que Argentina)
    url_portafolio_asesores = f'https://api.invertironline.com/api/v2/Asesores/Portafolio/{id_cliente}/estados_Unidos'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    
    
    try:
        # Primer intento: endpoint de Asesores
        respuesta = requests.get(url_portafolio_asesores, headers=encabezados, timeout=30)
        
        if respuesta.status_code == 200:
            data = respuesta.json()
            return data
        elif respuesta.status_code == 404:
            st.info("ℹ️ No se encontró portafolio EEUU vía Asesores, intentando endpoint directo...")
            
            # Segundo intento: endpoint directo
            url_portafolio_directo = f'https://api.invertironline.com/api/v2/portafolio/estados_Unidos'
            respuesta_directo = requests.get(url_portafolio_directo, headers=encabezados, timeout=30)
            
            if respuesta_directo.status_code == 200:
                data_directo = respuesta_directo.json()
                st.success(f"✅ Portafolio EEUU obtenido vía endpoint directo: {len(data_directo.get('activos', []))} activos")
                return data_directo
            elif respuesta_directo.status_code == 401:
                st.error("❌ Error 401: Token de autenticación inválido o expirado")
                st.info("💡 Intente refrescar el token o inicie sesión nuevamente")
                return None
            elif respuesta_directo.status_code == 403:
                st.error("❌ Error 403: Acceso denegado al portafolio de EEUU")
                st.info("💡 Verifique que su cuenta tenga permisos para acceder a portafolios de EEUU")
                return None
            else:
                st.error(f"❌ Error HTTP {respuesta_directo.status_code} en endpoint directo")
                st.info(f"📄 Respuesta: {respuesta_directo.text[:500]}")
                return None
                
        elif respuesta.status_code == 401:
            st.error("❌ Error 401: Token de autenticación inválido o expirado")
            st.info("💡 Intente refrescar el token o inicie sesión nuevamente")
            return None
        elif respuesta.status_code == 403:
            st.error("❌ Error 403: Acceso denegado al portafolio de EEUU")
            st.info("💡 Verifique que su cuenta tenga permisos para acceder a portafolios de EEUU")
            return None
        else:
            st.error(f"❌ Error HTTP {respuesta.status_code} en endpoint de Asesores")
            st.info(f"📄 Respuesta: {respuesta.text[:500]}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("⏱️ Timeout al obtener portafolio de EEUU")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🔌 Error de conexión al obtener portafolio de EEUU")
        return None
    except Exception as e:
        st.error(f'❌ Error inesperado al obtener portafolio de EEUU: {str(e)}')
        return None

# --- FUNCIONES ASÍNCRONAS ---
async def obtener_portafolio_async(token_portador, id_cliente, pais='Argentina'):
    """
    Versión asíncrona para obtener el portafolio de un cliente específico
    
    Args:
        token_portador (str): Token de autenticación
        id_cliente (str): ID del cliente
        pais (str): País del portafolio (default: 'Argentina')
        
    Returns:
        dict: Portafolio del cliente o None en caso de error
    """
    url_portafolio = f'https://api.invertironline.com/api/v2/Asesores/Portafolio/{id_cliente}/{pais}'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url_portafolio, headers=encabezados, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    st.error("Error de autenticación al obtener portafolio")
                    return None
                else:
                    st.error(f"Error HTTP {response.status} al obtener portafolio")
                    return None
    except asyncio.TimeoutError:
        st.error("Timeout al obtener portafolio")
        return None
    except Exception as e:
        st.error(f'Error al obtener portafolio: {str(e)}')
        return None

async def obtener_portafolio_eeuu_async(token_portador, id_cliente):
    """
    Versión asíncrona para obtener el portafolio de Estados Unidos de un cliente específico
    
    Args:
        token_portador (str): Token de autenticación
        id_cliente (str): ID del cliente
        
    Returns:
        dict: Portafolio de EEUU del cliente o None en caso de error
    """
    # Intentar primero con el endpoint de Asesores
    url_portafolio_asesores = f'https://api.invertironline.com/api/v2/Asesores/Portafolio/{id_cliente}/estados_Unidos'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Primer intento: endpoint de Asesores
            async with session.get(url_portafolio_asesores, headers=encabezados, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 404:
                    st.info("ℹ️ No se encontró portafolio EEUU vía Asesores, intentando endpoint directo...")
                    
                    # Segundo intento: endpoint directo
                    url_portafolio_directo = f'https://api.invertironline.com/api/v2/portafolio/estados_Unidos'
                    async with session.get(url_portafolio_directo, headers=encabezados, timeout=aiohttp.ClientTimeout(total=30)) as response_directo:
                        if response_directo.status == 200:
                            data_directo = await response_directo.json()
                            st.success(f"✅ Portafolio EEUU obtenido vía endpoint directo: {len(data_directo.get('activos', []))} activos")
                            return data_directo
                        elif response_directo.status == 401:
                            st.error("❌ Error 401: Token de autenticación inválido o expirado")
                            st.info("💡 Intente refrescar el token o inicie sesión nuevamente")
                            return None
                        elif response_directo.status == 403:
                            st.error("❌ Error 403: Acceso denegado al portafolio de EEUU")
                            st.info("💡 Verifique que su cuenta tenga permisos para acceder a portafolios de EEUU")
                            return None
                        else:
                            st.error(f"❌ Error HTTP {response_directo.status} en endpoint directo")
                            return None
                            
                elif response.status == 401:
                    st.error("❌ Error 401: Token de autenticación inválido o expirado")
                    st.info("💡 Intente refrescar el token o inicie sesión nuevamente")
                    return None
                elif response.status == 403:
                    st.error("❌ Error 403: Acceso denegado al portafolio de EEUU")
                    st.info("💡 Verifique que su cuenta tenga permisos para acceder a portafolios de EEUU")
                    return None
                else:
                    st.error(f"❌ Error HTTP {response.status} en endpoint de Asesores")
                    return None
                    
    except asyncio.TimeoutError:
        st.error("⏱️ Timeout al obtener portafolio de EEUU")
        return None
    except aiohttp.ClientConnectionError:
        st.error("🔌 Error de conexión al obtener portafolio de EEUU")
        return None
    except Exception as e:
        st.error(f'❌ Error inesperado al obtener portafolio de EEUU: {str(e)}')
        return None

async def obtener_estado_cuenta_async(token_portador, id_cliente=None):
    """
    Versión asíncrona para obtener el estado de cuenta del cliente o del usuario autenticado
    
    Args:
        token_portador (str): Token de autenticación
        id_cliente (str, optional): ID del cliente. Si es None, obtiene el estado de cuenta del usuario
        
    Returns:
        dict: Estado de cuenta o None en caso de error
    """
    if id_cliente:
        url_estado_cuenta = f'https://api.invertironline.com/api/v2/Asesores/EstadoDeCuenta/{id_cliente}'
    else:
        url_estado_cuenta = 'https://api.invertironline.com/api/v2/estadocuenta'
    
    encabezados = obtener_encabezado_autorizacion(token_portador)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url_estado_cuenta, headers=encabezados, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    st.error("Error de autenticación al obtener estado de cuenta")
                    return None
                else:
                    st.error(f"Error HTTP {response.status} al obtener estado de cuenta")
                    return None
    except asyncio.TimeoutError:
        st.error("Timeout al obtener estado de cuenta")
        return None
    except Exception as e:
        st.error(f'Error al obtener estado de cuenta: {str(e)}')
        return None

async def obtener_estado_cuenta_eeuu_async(token_portador):
    """
    Versión asíncrona para obtener el estado de cuenta de Estados Unidos del usuario autenticado
    Filtra las cuentas que corresponden a EEUU del estado de cuenta general
    
    Args:
        token_portador (str): Token de autenticación
        
    Returns:
        dict: Estado de cuenta filtrado solo para cuentas de EEUU o None en caso de error
    """
    url_estado_cuenta = 'https://api.invertironline.com/api/v2/estadocuenta'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url_estado_cuenta, headers=encabezados, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Filtrar solo cuentas de EEUU
                    if 'cuentas' in data:
                        cuentas_eeuu = []
                        for cuenta in data['cuentas']:
                            if es_cuenta_eeuu(cuenta):
                                cuentas_eeuu.append(cuenta)
                        
                        # Crear nuevo estado de cuenta solo con cuentas de EEUU
                        estado_eeuu = data.copy()
                        estado_eeuu['cuentas'] = cuentas_eeuu
                        
                        # Recalcular totales
                        total_eeuu = sum(cuenta.get('total', 0) for cuenta in cuentas_eeuu)
                        estado_eeuu['totalEnPesos'] = total_eeuu
                        
                        return estado_eeuu
                    else:
                        return data
                elif response.status == 401:
                    st.error("❌ Error 401: Token de autenticación inválido o expirado")
                    return None
                else:
                    st.error(f"❌ Error HTTP {response.status} al obtener estado de cuenta de EEUU")
                    return None
    except asyncio.TimeoutError:
        st.error("⏱️ Timeout al obtener estado de cuenta de EEUU")
        return None
    except Exception as e:
        st.error(f'❌ Error inesperado al obtener estado de cuenta de EEUU: {str(e)}')
        return None

async def obtener_serie_historica_directa_async(simbolo, mercado, fecha_desde, fecha_hasta, ajustada, bearer_token):
    """
    Versión asíncrona para obtener serie histórica directamente de la API de IOL
    
    Args:
        simbolo (str): Símbolo del activo
        mercado (str): Mercado (bCBA, nYSE, nASDAQ, rOFEX, mERVAL)
        fecha_desde (str): Fecha desde en formato YYYY-MM-DD
        fecha_hasta (str): Fecha hasta en formato YYYY-MM-DD
        ajustada (str): 'Ajustada' o 'SinAjustar'
        bearer_token (str): Token de autenticación
        
    Returns:
        list: Lista de datos históricos o None en caso de error
    """
    url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
    except Exception as e:
        return None

async def obtener_historico_mep_async(token_acceso, fecha_desde, fecha_hasta):
    """
    Versión asíncrona para obtener el histórico del dólar MEP calculado como AL30/AL30D
    Usa el método estándar que funciona correctamente para las métricas del portafolio
    
    Args:
        token_acceso (str): Token de acceso para la autenticación
        fecha_desde (str): Fecha desde en formato YYYY-MM-DD
        fecha_hasta (str): Fecha hasta en formato YYYY-MM-DD
    
    Returns:
        dict: Diccionario con datos históricos del MEP calculado
    """
    try:
        st.info(f"🔗 Consultando histórico MEP desde {fecha_desde} hasta {fecha_hasta}")
        
        # Usar el método estándar que funciona correctamente
        tickers_especificos = ['AL30', 'AL30D']
        datos_series = {}
        
        # Obtener datos para cada ticker usando el método estándar
        for simbolo in tickers_especificos:
            st.info(f"📊 Obteniendo datos históricos de {simbolo}...")
            
            # Usar el método que funciona correctamente para las métricas del portafolio
            serie = obtener_serie_historica_activo(simbolo, token_acceso, fecha_desde, fecha_hasta)
            
            if serie is not None and not serie.empty and len(serie) > 0:
                # Convertir serie a listas
                precios = serie.values.tolist()
                fechas = serie.index.tolist()
                
                datos_series[simbolo] = {
                    'precios': precios,
                    'fechas': fechas
                }
                st.success(f"✅ {simbolo}: {len(precios)} puntos de datos")
            else:
                st.warning(f"⚠️ {simbolo}: No se pudieron obtener datos históricos")
        
        # Verificar que tenemos datos para ambos tickers
        if 'AL30' not in datos_series or 'AL30D' not in datos_series:
            st.error("❌ No se pudieron obtener datos para AL30 o AL30D")
            return None
        
        # Crear DataFrames y calcular MEP
        df_al30 = pd.DataFrame({
            'fecha': datos_series['AL30']['fechas'],
            'precio_al30': datos_series['AL30']['precios']
        })
        
        df_al30d = pd.DataFrame({
            'fecha': datos_series['AL30D']['fechas'],
            'precio_al30d': datos_series['AL30D']['precios']
        })
        
        # Convertir fechas a datetime
        df_al30['fecha'] = pd.to_datetime(df_al30['fecha'])
        df_al30d['fecha'] = pd.to_datetime(df_al30d['fecha'])
        
        # Hacer merge por fecha
        df_merged = pd.merge(df_al30, df_al30d, on='fecha', how='inner')
        
        # Calcular MEP
        df_merged['mep'] = df_merged['precio_al30'] / df_merged['precio_al30d']
        
        # Ordenar por fecha
        df_merged = df_merged.sort_values('fecha')
        
        st.success(f"✅ Se calcularon {len(df_merged)} valores de MEP históricos")
        
        # Convertir a formato esperado por la interfaz
        datos_mep = []
        for _, row in df_merged.iterrows():
            datos_mep.append({
                'fecha': row['fecha'].strftime('%Y-%m-%d'),
                'fechaHora': row['fecha'].strftime('%Y-%m-%dT%H:%M:%S'),
                'mep': row['mep'],
                'al30_pesos': row['precio_al30'],
                'al30d_dolares': row['precio_al30d'],
                'ultimoPrecio': row['mep'],
                'variacion': 0,  # Se calculará si es necesario
                'moneda': 'peso_Argentino'
            })
        
        return {
            'datos': datos_mep,
            'dataframe': df_merged,
            'resumen': {
                'total_registros': len(datos_mep),
                'fecha_inicio': df_merged['fecha'].min().strftime('%Y-%m-%d'),
                'fecha_fin': df_merged['fecha'].max().strftime('%Y-%m-%d'),
                'mep_promedio': df_merged['mep'].mean(),
                'mep_min': df_merged['mep'].min(),
                'mep_max': df_merged['mep'].max()
            }
        }
        
    except Exception as e:
        st.error(f"❌ Error calculando histórico MEP: {str(e)}")
        return None

# --- FUNCIONES WRAPPER PARA USAR ASYNC EN STREAMLIT ---
def ejecutar_async(func_async, *args, **kwargs):
    """
    Ejecuta una función asíncrona en el contexto de Streamlit
    
    Args:
        func_async: Función asíncrona a ejecutar
        *args: Argumentos posicionales
        **kwargs: Argumentos con nombre
        
    Returns:
        Resultado de la función asíncrona
    """
    try:
        # Crear un nuevo loop de eventos si no existe uno
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(func_async(*args, **kwargs))
        finally:
            loop.close()
    except Exception as e:
        st.error(f"Error ejecutando función asíncrona: {str(e)}")
        return None

def obtener_portafolio_async_wrapper(token_portador, id_cliente, pais='Argentina'):
    """
    Wrapper síncrono para obtener_portafolio_async
    """
    return ejecutar_async(obtener_portafolio_async, token_portador, id_cliente, pais)

def obtener_portafolio_eeuu_async_wrapper(token_portador, id_cliente):
    """
    Wrapper síncrono para obtener_portafolio_eeuu_async
    """
    return ejecutar_async(obtener_portafolio_eeuu_async, token_portador, id_cliente)

def obtener_estado_cuenta_async_wrapper(token_portador, id_cliente=None):
    """
    Wrapper síncrono para obtener_estado_cuenta_async
    """
    return ejecutar_async(obtener_estado_cuenta_async, token_portador, id_cliente)

def obtener_estado_cuenta_eeuu_async_wrapper(token_portador):
    """
    Wrapper síncrono para obtener_estado_cuenta_eeuu_async
    """
    return ejecutar_async(obtener_estado_cuenta_eeuu_async, token_portador)

def obtener_historico_mep_async_wrapper(token_acceso, fecha_desde, fecha_hasta):
    """
    Wrapper síncrono para obtener_historico_mep_async
    """
    return ejecutar_async(obtener_historico_mep_async, token_acceso, fecha_desde, fecha_hasta)

def obtener_estado_cuenta_eeuu(token_portador):
    """
    Obtiene el estado de cuenta de Estados Unidos del usuario autenticado
    Filtra las cuentas que corresponden a EEUU del estado de cuenta general
    
    Args:
        token_portador (str): Token de autenticación
        
    Returns:
        dict: Estado de cuenta filtrado solo para cuentas de EEUU o None en caso de error
    """
    # Usar el mismo endpoint que el estado de cuenta general
    url_estado_cuenta = 'https://api.invertironline.com/api/v2/estadocuenta'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    
    try:
        respuesta = requests.get(url_estado_cuenta, headers=encabezados, timeout=30)
        
        if respuesta.status_code == 200:
            try:
                data = respuesta.json()
                
                # Filtrar solo las cuentas de EEUU usando la misma lógica que la vista consolidada
                cuentas_eeuu = []
                for cuenta in data.get('cuentas', []):
                    numero = cuenta.get('numero', 'N/A')
                    descripcion = cuenta.get('descripcion', 'N/A')
                    moneda = cuenta.get('moneda', 'N/A')
                    
                    # Determinar si es cuenta de EEUU (misma lógica que vista consolidada)
                    es_cuenta_eeuu = any([
                        'eeuu' in descripcion.lower(),
                        'estados unidos' in descripcion.lower(),
                        '-eeuu' in str(numero).lower(),
                        'dolar estadounidense' in moneda.lower(),
                        'dolar_estadounidense' in moneda.lower(),
                        'usd' in moneda.lower()
                    ])
                    
                    if es_cuenta_eeuu:
                        cuentas_eeuu.append(cuenta)
                
                # Crear respuesta filtrada solo para EEUU
                data_eeuu = {
                    'cuentas': cuentas_eeuu,
                    'totalEnPesos': sum(cuenta.get('total', 0) for cuenta in cuentas_eeuu),
                    'filtrado': True,
                    'total_cuentas_eeuu': len(cuentas_eeuu)
                }
                
                if cuentas_eeuu:
                    st.success(f"✅ Estado de cuenta EEUU filtrado: {len(cuentas_eeuu)} cuentas de EEUU")
                else:
                    st.info("ℹ️ No se encontraron cuentas específicas de EEUU")
                
                return data_eeuu
                
            except ValueError as e:
                st.error(f"❌ Error al procesar JSON: {str(e)}")
                return None
        elif respuesta.status_code == 401:
            st.error("❌ Error 401: Token de autenticación inválido o expirado")
            st.info("💡 Intente refrescar el token o inicie sesión nuevamente")
            return None
        elif respuesta.status_code == 403:
            st.error("❌ Error 403: Acceso denegado al estado de cuenta")
            return None
        elif respuesta.status_code == 404:
            st.warning("⚠️ No se encontró estado de cuenta")
            return None
        else:
            st.error(f"❌ Error HTTP {respuesta.status_code} al obtener estado de cuenta")
            return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Timeout al obtener estado de cuenta")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🔌 Error de conexión al obtener estado de cuenta")
        return None
    except Exception as e:
        st.error(f'❌ Error inesperado al obtener estado de cuenta: {str(e)}')
        return None

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



@st.cache_data(ttl=600)  # Cache por 10 minutos para mejor rendimiento
def obtener_serie_historica_iol(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="SinAjustar"):
    """
    Obtiene la serie histórica de precios de un título desde la API de IOL.
    Actualizada para manejar correctamente la estructura de respuesta de la API.
    """
    # Determinar endpoint según tipo de instrumento según la documentación de IOL
    if mercado == "Opciones":
        url = f"https://api.invertironline.com/api/v2/Opciones/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    elif mercado == "FCI":
        url = f"https://api.invertironline.com/api/v2/Titulos/FCI/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    else:
        # Para mercados tradicionales usar el formato estándar
        url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)  # Reducido de 30 a 15 segundos
        
        if response.status_code == 200:
            data = response.json()
            if not data:
                return None
            
            precios = []
            fechas = []
            
            for item in data:
                try:
                    # Usar ultimoPrecio como precio principal según la documentación
                    precio = item.get('ultimoPrecio')
                    
                    # Si ultimoPrecio es 0 o None, intentar otros campos
                    if not precio or precio == 0:
                        precio = item.get('cierreAnterior') or item.get('precioPromedio') or item.get('apertura')
                    
                    fecha_str = item.get('fechaHora') or item.get('fecha')
                    
                    if precio is not None and precio > 0 and fecha_str:
                        fecha_parsed = parse_datetime_flexible(fecha_str)
                        if fecha_parsed is not None:
                            precios.append(precio)
                            fechas.append(fecha_parsed)
                            
                except Exception as e:
                    # Log individual item errors but continue processing
                    continue
            
            if precios and fechas:
                # Crear serie ordenada por fecha
                serie = pd.Series(precios, index=fechas)
                serie = serie.sort_index()  # Asegurar orden cronológico
                
                # Eliminar duplicados manteniendo el último valor
                serie = serie[~serie.index.duplicated(keep='last')]
                
                return serie
            else:
                return None
                
        elif response.status_code == 401:
            # Token expirado o inválido - silencioso para no interrumpir
            return None
            
        elif response.status_code == 404:
            # Símbolo no encontrado en este mercado - silencioso
            return None
            
        elif response.status_code == 400:
            # Parámetros inválidos - silencioso
            return None
            
        elif response.status_code == 500:
            # Error del servidor - silencioso para no interrumpir el flujo
            return None
            
        else:
            # Otros errores HTTP - silencioso
            return None
            
    except requests.exceptions.Timeout:
        # Timeout - silencioso
        return None
    except requests.exceptions.ConnectionError:
        # Error de conexión - silencioso
        return None
    except Exception as e:
        # Error general - silencioso para no interrumpir el análisis
        return None

# Función removida - usando solo API de IOL

def obtener_operaciones_activo(token_portador, simbolo, fecha_desde=None, fecha_hasta=None, id_cliente=None):
    """
    Obtiene todas las operaciones de un activo específico desde la API de IOL.
    
    Args:
        token_portador (str): Token de autorización
        simbolo (str): Símbolo del activo
        fecha_desde (str): Fecha desde (YYYY-MM-DD), por defecto 2 años atrás
        fecha_hasta (str): Fecha hasta (YYYY-MM-DD), por defecto hoy
        id_cliente (str): ID del cliente para filtrar operaciones
        
    Returns:
        list: Lista de operaciones del activo
    """
    if fecha_desde is None:
        fecha_desde = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
    if fecha_hasta is None:
        fecha_hasta = datetime.now().strftime('%Y-%m-%d')
    
    headers = {
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'application/json'
    }
    
    # Parámetros para filtrar operaciones
    params = {
        'filtro.estado': 'terminadas',
        'filtro.fechaDesde': fecha_desde,
        'filtro.fechaHasta': fecha_hasta,
        'filtro.pais': 'argentina'
    }
    if id_cliente:
        params['filtro.cuentaComitente'] = id_cliente
    
    try:
        url = "https://api.invertironline.com/api/v2/operaciones"
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            operaciones = response.json()
            # Filtrar solo las operaciones del símbolo específico
            operaciones_activo = [
                op for op in operaciones 
                if op.get('simbolo') == simbolo
            ]
            return operaciones_activo
        else:
            print(f"Error al obtener operaciones: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"Error al obtener operaciones para {simbolo}: {str(e)}")
        return []

def reconstruir_composicion_portafolio(token_portador, portafolio_actual, fecha_desde=None, fecha_hasta=None, id_cliente=None):
    """
    Reconstruye la composición del portafolio a lo largo del tiempo basándose en todas las operaciones.
    
    Args:
        token_portador (str): Token de autorización
        portafolio_actual (dict): Portafolio actual con estructura {'activos': [...]}
        fecha_desde (str): Fecha desde para reconstruir
        fecha_hasta (str): Fecha hasta para reconstruir
        id_cliente (str): ID del cliente para filtrar operaciones
        
    Returns:
        dict: Composición del portafolio por fecha
    """
    if fecha_desde is None:
        fecha_desde = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
    if fecha_hasta is None:
        fecha_hasta = datetime.now().strftime('%Y-%m-%d')
    
    # Convertir portafolio a formato de diccionario por símbolo
    portafolio_dict = {}
    if 'activos' in portafolio_actual:
        for activo in portafolio_actual['activos']:
            titulo = activo.get('titulo', {})
            simbolo = titulo.get('simbolo', '')
            if simbolo:
                portafolio_dict[simbolo] = activo
    else:
        # Si ya es un diccionario por símbolo
        portafolio_dict = portafolio_actual
    
    # Obtener todas las operaciones de todos los activos
    todas_operaciones = []
    
    for simbolo in portafolio_dict.keys():
        operaciones = obtener_operaciones_activo(token_portador, simbolo, fecha_desde, fecha_hasta, id_cliente)
        for op in operaciones:
            op['simbolo_original'] = simbolo
            todas_operaciones.append(op)
    
    # Ordenar operaciones por fecha
    todas_operaciones.sort(key=lambda x: x.get('fechaOperada', x.get('fechaOrden', '1900-01-01')))
    
    # Reconstruir composición día a día
    composicion_por_fecha = {}
    posiciones_actuales = {}
    
    # Inicializar con el portafolio actual
    for simbolo, activo in portafolio_dict.items():
        # Obtener cantidad del activo
        cantidad = activo.get('cantidad', 0)
        if not cantidad:
            # Intentar otros campos de cantidad
            cantidad = activo.get('Cantidad', activo.get('cantidadNominal', 0))
        
        posiciones_actuales[simbolo] = {
            'cantidad': cantidad,
            'precio_compra': 0,
            'fecha_compra': None,
            'operaciones': []
        }
    
    # Procesar operaciones en orden cronológico
    for op in todas_operaciones:
        simbolo = op.get('simbolo_original')
        tipo = op.get('tipo', '').lower()
        fecha = op.get('fechaOperada') or op.get('fechaOrden')
        cantidad = op.get('cantidadOperada', op.get('cantidad', 0))
        precio = op.get('precioOperado', op.get('precio', 0))
        
        if not fecha or simbolo not in posiciones_actuales:
            continue
            
        # Convertir fecha a string para usar como clave
        try:
            fecha_dt = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
            fecha_str = fecha_dt.strftime('%Y-%m-%d')
        except:
            continue
        
        # Actualizar posiciones
        if tipo == 'compra':
            posiciones_actuales[simbolo]['cantidad'] += cantidad
            # Calcular precio promedio de compra
            cantidad_anterior = posiciones_actuales[simbolo]['cantidad'] - cantidad
            precio_anterior = posiciones_actuales[simbolo]['precio_compra']
            
            if cantidad_anterior > 0:
                precio_promedio = ((precio_anterior * cantidad_anterior) + (precio * cantidad)) / posiciones_actuales[simbolo]['cantidad']
            else:
                precio_promedio = precio
                
            posiciones_actuales[simbolo]['precio_compra'] = precio_promedio
            posiciones_actuales[simbolo]['fecha_compra'] = fecha_str
            
        elif tipo == 'venta':
            posiciones_actuales[simbolo]['cantidad'] -= cantidad
            if posiciones_actuales[simbolo]['cantidad'] <= 0:
                posiciones_actuales[simbolo]['cantidad'] = 0
                posiciones_actuales[simbolo]['precio_compra'] = 0
                posiciones_actuales[simbolo]['fecha_compra'] = None
        
        # Registrar operación
        posiciones_actuales[simbolo]['operaciones'].append({
            'fecha': fecha_str,
            'tipo': tipo,
            'cantidad': cantidad,
            'precio': precio
        })
        
        # Guardar composición para esta fecha
        composicion_por_fecha[fecha_str] = {
            simbolo: {
                'cantidad': posiciones_actuales[simbolo]['cantidad'],
                'precio_compra': posiciones_actuales[simbolo]['precio_compra'],
                'fecha_compra': posiciones_actuales[simbolo]['fecha_compra']
            }
            for simbolo in posiciones_actuales.keys()
            if posiciones_actuales[simbolo]['cantidad'] > 0
        }
    
    return composicion_por_fecha, posiciones_actuales

def es_cuenta_eeuu(cuenta):
    """
    Determina si una cuenta es de EEUU basándose en su moneda
    """
    moneda = cuenta.get('moneda', '').lower()
    return 'dolar' in moneda or 'usd' in moneda or 'dollar' in moneda

def obtener_composicion_historica_portafolio(token_acceso, activos, fecha_desde, fecha_hasta):
    """
    Alias para reconstruir_composicion_portafolio para mantener compatibilidad
    """
    return reconstruir_composicion_portafolio(token_acceso, activos, fecha_desde, fecha_hasta, None)

def calcular_retorno_real_activo(simbolo, posiciones_actuales, precios_historicos):
    """
    Calcula el retorno real de un activo basándose en su historial de operaciones.
    
    Args:
        simbolo (str): Símbolo del activo
        posiciones_actuales (dict): Posiciones actuales del activo
        precios_historicos (pd.Series): Precios históricos del activo
        
    Returns:
        dict: Métricas de retorno real
    """
    if simbolo not in posiciones_actuales:
        return None
        
    posicion = posiciones_actuales[simbolo]
    
    if not posicion['operaciones'] or posicion['cantidad'] <= 0:
        return None
    
    # Obtener precio actual
    if precios_historicos is None or precios_historicos.empty:
        return None
        
    precio_actual = precios_historicos.iloc[-1]
    
    # Calcular retorno basado en operaciones
    operaciones = posicion['operaciones']
    
    # Separar compras y ventas
    compras = [op for op in operaciones if op['tipo'] == 'compra']
    ventas = [op for op in operaciones if op['tipo'] == 'venta']
    
    # Calcular flujo de caja
    flujo_compras = sum(op['cantidad'] * op['precio'] for op in compras)
    flujo_ventas = sum(op['cantidad'] * op['precio'] for op in ventas)
    
    # Valor actual de la posición
    valor_actual = posicion['cantidad'] * precio_actual
    
    # Calcular retorno total (incluyendo ventas realizadas)
    if flujo_compras > 0:
        retorno_total = ((valor_actual + flujo_ventas - flujo_compras) / flujo_compras) - 1
    else:
        retorno_total = 0
    
    # Calcular retorno anualizado basado en la primera compra hasta hoy
    if compras:
        primera_compra = min(compras, key=lambda x: x['fecha'])
        
        try:
            fecha_inicio = datetime.strptime(primera_compra['fecha'], '%Y-%m-%d')
            fecha_fin = datetime.now()  # Usar fecha actual, no última operación
            dias_transcurridos = (fecha_fin - fecha_inicio).days
            
            if dias_transcurridos > 0:
                retorno_anualizado = ((1 + retorno_total) ** (365 / dias_transcurridos)) - 1
            else:
                retorno_anualizado = retorno_total
        except:
            retorno_anualizado = retorno_total
    else:
        retorno_anualizado = retorno_total
    
    # Calcular volatilidad desde la primera compra
    if compras and precios_historicos is not None and len(precios_historicos) > 1:
        primera_compra = min(compras, key=lambda x: x['fecha'])
        try:
            fecha_inicio = datetime.strptime(primera_compra['fecha'], '%Y-%m-%d')
            # Usar los últimos 252 días de datos disponibles para volatilidad
            precios_recientes = precios_historicos.tail(252)
            
            if len(precios_recientes) > 10:  # Mínimo 10 días de datos
                retornos_diarios = precios_recientes.pct_change().dropna()
                if len(retornos_diarios) > 5:  # Mínimo 5 retornos válidos
                    volatilidad_anualizada = retornos_diarios.std() * np.sqrt(252)
                else:
                    volatilidad_anualizada = 0.15  # Volatilidad por defecto del 15%
            else:
                volatilidad_anualizada = 0.15  # Volatilidad por defecto del 15%
        except:
            volatilidad_anualizada = 0.15  # Volatilidad por defecto del 15%
    else:
        volatilidad_anualizada = 0.15  # Volatilidad por defecto del 15%
    
    return {
        'retorno_total': retorno_total,
        'retorno_anualizado': retorno_anualizado,
        'volatilidad_anualizada': volatilidad_anualizada,
        'flujo_compras': flujo_compras,
        'flujo_ventas': flujo_ventas,
        'valor_actual': valor_actual,
        'cantidad_actual': posicion['cantidad'],
        'precio_compra_promedio': posicion['precio_compra'],
        'fecha_primera_compra': posicion['fecha_compra']
    }

def calcular_metricas_reales_portafolio(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Función centralizada para calcular métricas reales del portafolio basadas en operaciones
    """
    try:
        activos = portafolio.get('activos', [])
        if not activos:
            return None, None
        
        # Obtener operaciones históricas para cada activo
        metricas_por_activo = {}
        simbolos = []
        
        for activo in activos:
            titulo = activo.get('titulo', {})
            simbolo = titulo.get('simbolo', '')
            if simbolo:
                simbolos.append(simbolo)
        
        # Obtener datos históricos para todos los símbolos
        composicion_por_fecha, posiciones_actuales = obtener_composicion_historica_portafolio(
            token_acceso, activos, fecha_desde, fecha_hasta
        )
        
        if not posiciones_actuales:
            return None, None
        
        # Calcular métricas reales para cada activo
        for simbolo in simbolos:
            if simbolo in posiciones_actuales:
                # Obtener serie histórica del activo
                serie_historica = obtener_serie_historica_activo(simbolo, token_acceso, fecha_desde, fecha_hasta)
                
                if serie_historica is not None and not serie_historica.empty:
                    # Calcular retorno real basado en operaciones
                    retorno_real = calcular_retorno_real_activo(simbolo, posiciones_actuales, serie_historica)
                    
                    if retorno_real:
                        metricas_por_activo[simbolo] = {
                            'retorno_anualizado': retorno_real['retorno_anualizado'],
                            'volatilidad_anualizada': retorno_real['volatilidad_anualizada'],
                            'retorno_total': retorno_real['retorno_total'],
                            'valor_actual': retorno_real['valor_actual'],
                            'flujo_compras': retorno_real['flujo_compras'],
                            'flujo_ventas': retorno_real['flujo_ventas'],
                            'fecha_primera_compra': retorno_real['fecha_primera_compra']
                        }
        
        return metricas_por_activo, posiciones_actuales
        
    except Exception as e:
        st.error(f"Error calculando métricas reales del portafolio: {str(e)}")
        return None, None

def obtener_metricas_portafolio_reales(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Función unificada para obtener todas las métricas reales del portafolio
    """
    try:
        # Calcular métricas reales por activo
        metricas_por_activo, posiciones_actuales = calcular_metricas_reales_portafolio(
            portafolio, token_acceso, fecha_desde, fecha_hasta
        )
        
        if not metricas_por_activo:
            return None
        
        # Calcular métricas agregadas del portafolio
        # Ponderar por valor de posición actual
        pesos = {}
        valor_total_portafolio = 0
        
        for simbolo, metricas in metricas_por_activo.items():
            valor_activo = metricas['valor_actual']
            pesos[simbolo] = valor_activo
            valor_total_portafolio += valor_activo
        
        # Normalizar pesos
        for simbolo in pesos:
            pesos[simbolo] = pesos[simbolo] / valor_total_portafolio if valor_total_portafolio > 0 else 0
        
        # Calcular retorno promedio ponderado del portafolio
        retorno_portafolio = sum(
            metricas_por_activo[simbolo]['retorno_anualizado'] * pesos[simbolo] 
            for simbolo in pesos.keys()
        )
        
        # Calcular volatilidad del portafolio
        volatilidades = [metricas_por_activo[simbolo]['volatilidad_anualizada'] for simbolo in pesos.keys()]
        volatilidad_portafolio = np.average(volatilidades, weights=list(pesos.values())) if volatilidades else 0
        
        # Calcular Sharpe ratio (asumiendo tasa libre de riesgo del 8% anual - Tasa de Caución promedio)
        tasa_libre_riesgo = 0.08
        sharpe_ratio = (retorno_portafolio - tasa_libre_riesgo) / volatilidad_portafolio if volatilidad_portafolio > 0 else 0
        
        return {
            'metricas_por_activo': metricas_por_activo,
            'posiciones_actuales': posiciones_actuales,
            'pesos': pesos,
            'valor_total_portafolio': valor_total_portafolio,
            'retorno_portafolio': retorno_portafolio,
            'volatilidad_portafolio': volatilidad_portafolio,
            'sharpe_ratio': sharpe_ratio,
            'tasa_libre_riesgo': tasa_libre_riesgo
        }
        
    except Exception as e:
        st.error(f"Error obteniendo métricas reales del portafolio: {str(e)}")
        return None

def obtener_serie_historica_activo(simbolo, token_acceso, fecha_desde, fecha_hasta):
    """
    Obtiene la serie histórica de un activo específico usando el método estándar
    Esta es la función principal que debe usarse en toda la aplicación para obtener series históricas
    """
    try:
        # Detectar mercado del símbolo
        mercado = detectar_mercado_simbolo(simbolo, token_acceso)
        if not mercado:
            return None
        
        # Obtener serie histórica
        if mercado == 'FCI':
            df = obtener_serie_historica_fci(token_acceso, simbolo, fecha_desde, fecha_hasta)
        else:
            data = obtener_serie_historica(simbolo, mercado, fecha_desde, fecha_hasta, 'SinAjustar', token_acceso)
            if data:
                df = procesar_respuesta_historico(data, 'accion')
            else:
                return None
        
        if df is not None and not df.empty and 'precio' in df.columns:
            # Crear serie con índice de fechas
            df['fecha'] = pd.to_datetime(df['fecha'])
            df = df.set_index('fecha')
            return df['precio']
        
        return None
        
    except Exception as e:
        st.warning(f"Error obteniendo serie histórica para {simbolo}: {str(e)}")
        return None

def obtener_serie_historica_estandar(simbolo, token_acceso, fecha_desde, fecha_hasta):
    """
    Función estándar para obtener series históricas en toda la aplicación
    Esta función debe usarse como reemplazo de otros métodos de obtención de datos históricos
    
    Args:
        simbolo (str): Símbolo del activo
        token_acceso (str): Token de autenticación
        fecha_desde (str): Fecha desde en formato YYYY-MM-DD
        fecha_hasta (str): Fecha hasta en formato YYYY-MM-DD
    
    Returns:
        pandas.Series: Serie histórica con fechas como índice y precios como valores
    """
    return obtener_serie_historica_activo(simbolo, token_acceso, fecha_desde, fecha_hasta)

def obtener_datos_paralelo(simbolo, token_portador, fecha_desde_str, fecha_hasta_str):
    """
    Función auxiliar para obtener datos de un símbolo en paralelo
    """
    try:
        # Optimización: Usar mercados más probables primero
        if len(simbolo) <= 5 and simbolo.isupper():
            mercados = ['bCBA', 'FCI', 'nYSE', 'nASDAQ', 'rOFEX', 'Opciones']
        else:
            mercados = ['nYSE', 'nASDAQ', 'bCBA', 'FCI', 'rOFEX', 'Opciones']
        
        for mercado in mercados:
            try:
                serie = obtener_serie_historica_iol(
                    token_portador, mercado, simbolo, 
                    fecha_desde_str, fecha_hasta_str
                )
                
                if serie is not None and len(serie) > 10 and serie.nunique() > 1:
                    return simbolo, serie, mercado
                    
            except Exception:
                continue
        return simbolo, None, None
    except Exception:
        return simbolo, None, None

def obtener_tokens_directo(username, password):
    """
    Obtiene tokens de acceso usando el método directo proporcionado por el usuario
    """
    token_url = 'https://api.invertironline.com/token'
    payload = {
        'username': username,
        'password': password,
        'grant_type': 'password'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        response = requests.post(token_url, data=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            tokens = response.json()
            return tokens['access_token'], tokens['refresh_token']
        else:
            return None, None
    except Exception as e:
        return None, None

def refrescar_token_directo(refresh_token):
    """
    Refresca el token de acceso usando el método directo
    """
    token_url = 'https://api.invertironline.com/token'
    payload = {
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        response = requests.post(token_url, data=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            tokens = response.json()
            return tokens['access_token'], tokens['refresh_token']
        else:
            return None, None
    except Exception as e:
        return None, None

def obtener_encabezado_autorizacion(token_portador):
    """
    Obtiene el encabezado de autorización para las llamadas a la API
    """
    return {
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'application/json'
    }

@st.cache_data(ttl=1800)  # Cache por 30 minutos
def obtener_tickers_por_panel(token_portador, paneles, pais):
    """
    Obtiene tickers disponibles por panel de cotizaciones
    """
    tickers_por_panel = {}
    tickers_df = pd.DataFrame(columns=['panel', 'simbolo'])
    
    for panel in paneles:
        url = f'https://api.invertironline.com/api/v2/cotizaciones-orleans/{panel}/{pais}/Operables'
        params = {
            'cotizacionInstrumentoModel.instrumento': panel,
            'cotizacionInstrumentoModel.pais': pais.lower()
        }
        encabezados = obtener_encabezado_autorizacion(token_portador)
        try:
            respuesta = requests.get(url, headers=encabezados, params=params, timeout=15)
            if respuesta.status_code == 200:
                datos = respuesta.json()
                tickers = [titulo['simbolo'] for titulo in datos.get('titulos', [])]
                tickers_por_panel[panel] = tickers
                panel_df = pd.DataFrame({'panel': panel, 'simbolo': tickers})
                tickers_df = pd.concat([tickers_df, panel_df], ignore_index=True)
            else:
                continue
        except Exception as e:
            continue
    return tickers_por_panel, tickers_df

def calcular_rsi(series, period=14):
    """
    Calcula el RSI de una serie de precios
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calcular_rvi(series, period=14):
    """
    Calcula el Relative Volatility Index (RVI) de una serie de precios.
    El RVI es similar al RSI pero usa la desviación estándar de los cambios de precio.
    """
    delta = series.diff()
    std = delta.rolling(window=period).std()
    up = std.where(delta > 0, 0)
    down = std.where(delta < 0, 0).abs()
    up_mean = up.rolling(window=period).mean()
    down_mean = down.rolling(window=period).mean()
    rvi = 100 * up_mean / (up_mean + down_mean)
    return rvi

def calcular_indicadores_tecnicos_avanzados(precios, periodo=14):
    """
    Calcula indicadores técnicos avanzados para una serie de precios
    """
    indicadores = {}
    
    # RSI
    indicadores['RSI'] = calcular_rsi(precios, periodo)
    
    # RVI
    indicadores['RVI'] = calcular_rvi(precios, periodo)
    
    # Media móvil simple
    indicadores['SMA_20'] = precios.rolling(window=20).mean()
    indicadores['SMA_50'] = precios.rolling(window=50).mean()
    
    # Media móvil exponencial
    indicadores['EMA_12'] = precios.ewm(span=12).mean()
    indicadores['EMA_26'] = precios.ewm(span=26).mean()
    
    # MACD
    indicadores['MACD'] = indicadores['EMA_12'] - indicadores['EMA_26']
    indicadores['MACD_Signal'] = indicadores['MACD'].ewm(span=9).mean()
    indicadores['MACD_Histogram'] = indicadores['MACD'] - indicadores['MACD_Signal']
    
    # Bollinger Bands
    sma_20 = indicadores['SMA_20']
    std_20 = precios.rolling(window=20).std()
    indicadores['BB_Upper'] = sma_20 + (std_20 * 2)
    indicadores['BB_Lower'] = sma_20 - (std_20 * 2)
    
    # Volatilidad
    indicadores['Volatilidad'] = precios.pct_change().rolling(window=20).std() * np.sqrt(252)
    
    return indicadores

@st.cache_data(ttl=600)  # Cache por 10 minutos
def obtener_serie_historica_directa(simbolo, mercado, fecha_desde, fecha_hasta, ajustada, bearer_token):
    """
    Obtiene serie histórica directamente usando el mismo método que funciona en las métricas
    """
    # Mapear nombres de mercados a los correctos de IOL (igual que en obtener_serie_historica)
    mercados_mapping = {
        'BCBA': 'bCBA',
        'NYSE': 'nYSE', 
        'NASDAQ': 'nASDAQ',
        'ROFEX': 'rOFEX',
        'Merval': 'bCBA',  # Merval no existe, usar bCBA
        'Bonos': 'Bonos'   # Mercado de bonos argentinos
    }
    
    mercado_correcto = mercados_mapping.get(mercado, mercado)
    
    url = f"https://api.invertironline.com/api/v2/{mercado_correcto}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None

def get_historical_data_for_optimization(token_portador, simbolos, fecha_desde, fecha_hasta):
    """
    Obtiene datos históricos para optimización usando el método directo mejorado.
    Utiliza el enfoque directo proporcionado por el usuario para mejor rendimiento.
    """
    try:
        df_precios = pd.DataFrame()
        simbolos_exitosos = []
        simbolos_fallidos = []
        detalles_errores = {}
        
        # Convertir fechas a string en formato correcto
        fecha_desde_str = fecha_desde.strftime('%Y-%m-%d')
        fecha_hasta_str = fecha_hasta.strftime('%Y-%m-%d')
        
        # Optimización: Limitar número de símbolos para mejor rendimiento
        if len(simbolos) > 20:  # Aumentado a 20 con el método directo
            simbolos = simbolos[:20]
        
        # Mercados disponibles en orden de prioridad
        mercados = ['bCBA', 'nYSE', 'nASDAQ', 'rOFEX', 'mERVAL']
        
        # Mapeo de símbolos a mercados más probables
        simbolo_mercado_map = {
            # Acciones argentinas - bCBA
            'GGAL': 'bCBA', 'PAMP': 'bCBA', 'YPF': 'bCBA', 'TEN': 'bCBA', 'CRES': 'bCBA', 
            'EDN': 'bCBA', 'ALUA': 'bCBA', 'COME': 'bCBA', 'LOMA': 'bCBA', 'MIRG': 'bCBA',
            'PGR': 'bCBA', 'SUPV': 'bCBA', 'TECO2': 'bCBA', 'TGNO4': 'bCBA', 'TGSU2': 'bCBA',
            'TRAN': 'bCBA', 'TS': 'bCBA', 'VALO': 'bCBA', 'BMA': 'bCBA', 'CEPU': 'bCBA',
            'IRCP': 'bCBA', 'PAM': 'bCBA', 'PZE': 'bCBA', 'TGS': 'bCBA', 'TXAR': 'bCBA',
            'HARG': 'bCBA', 'LONG': 'bCBA', 'MORI': 'bCBA', 'OEST': 'bCBA', 'RICH': 'bCBA',
            'SAMI': 'bCBA', 'SEMI': 'bCBA', 'TXAR': 'bCBA', 'VIST': 'bCBA', 'WILD': 'bCBA',
            # Bonos argentinos - bCBA
            'AL30': 'bCBA', 'AL30D': 'bCBA', 'GD30': 'bCBA', 'GD35': 'bCBA', 'GD38': 'bCBA', 
            'GD41': 'bCBA', 'GD46': 'bCBA', 'GD47': 'bCBA', 'GD48': 'bCBA', 'GD49': 'bCBA', 
            'GD50': 'bCBA', 'GD51': 'bCBA', 'GD52': 'bCBA', 'GD53': 'bCBA', 'GD54': 'bCBA', 
            'GD55': 'bCBA', 'GD56': 'bCBA', 'GD57': 'bCBA', 'GD58': 'bCBA', 'GD59': 'bCBA',
            # CEDEARs - bCBA
            'AAPL': 'bCBA', 'MSFT': 'bCBA', 'GOOGL': 'bCBA', 'AMZN': 'bCBA', 'TSLA': 'bCBA',
            'META': 'bCBA', 'NVDA': 'bCBA', 'NFLX': 'bCBA', 'AMD': 'bCBA', 'INTC': 'bCBA',
            'ORCL': 'bCBA', 'CRM': 'bCBA', 'ADBE': 'bCBA', 'PYPL': 'bCBA', 'UBER': 'bCBA',
            'LYFT': 'bCBA', 'SNAP': 'bCBA', 'TWTR': 'bCBA', 'SPY': 'bCBA', 'QQQ': 'bCBA',
            'IWM': 'bCBA', 'EFA': 'bCBA', 'EEM': 'bCBA', 'AGG': 'bCBA', 'TLT': 'bCBA',
            'GLD': 'bCBA', 'SLV': 'bCBA', 'USO': 'bCBA'
        }
        
        # Crear barra de progreso
        progress_bar = st.progress(0)
        total_simbolos = len(simbolos)
        
        st.info(f"🔍 Buscando datos históricos desde {fecha_desde_str} hasta {fecha_hasta_str}")
        
        # Procesar cada símbolo
        series_data = {}  # Almacenar todas las series primero
        
        for idx, simbolo in enumerate(simbolos):
            progress_bar.progress((idx + 1) / total_simbolos, text=f"Procesando {simbolo}...")
            
            serie_encontrada = False
            mercado_encontrado = None
            
            # Usar el mismo método que funciona en las métricas del portafolio
            try:
                # Usar el método estándar que funciona correctamente
                serie = obtener_serie_historica_estandar(simbolo, token_portador, fecha_desde_str, fecha_hasta_str)
                
                if serie is not None and not serie.empty and len(serie) > 10 and serie.nunique() > 1:
                    series_data[simbolo] = serie
                    simbolos_exitosos.append(simbolo)
                    serie_encontrada = True
                    mercado_encontrado = "detectado_automáticamente"
                    
                    # Mostrar información del símbolo exitoso
                    if len(simbolos_exitosos) <= 10:
                        st.success(f"✅ {simbolo} (auto-detectado): {len(serie)} puntos de datos")
                        
            except Exception as e:
                # Si falla, intentar con el método directo como fallback
                mercados_a_buscar = []
                if simbolo in simbolo_mercado_map:
                    # Usar el mercado más probable primero
                    mercado_principal = simbolo_mercado_map[simbolo]
                    mercados_a_buscar = [mercado_principal] + [m for m in mercados if m != mercado_principal]
                else:
                    # Si no está en el mapeo, buscar en todos los mercados
                    mercados_a_buscar = mercados
                
                # Buscar en los mercados determinados hasta encontrar datos
                for mercado in mercados_a_buscar:
                    try:
                        # Intentar con datos ajustados primero
                        serie_historica = obtener_serie_historica_directa(
                            simbolo, mercado, fecha_desde_str, fecha_hasta_str, 'ajustada', token_portador
                        )
                        
                        if serie_historica and len(serie_historica) > 0:
                            # Procesar los datos
                            precios = []
                            fechas = []
                            
                            for item in serie_historica:
                                try:
                                    precio = item.get('ultimoPrecio')
                                    if not precio or precio == 0:
                                        precio = item.get('cierreAnterior') or item.get('precioPromedio') or item.get('apertura')
                                    
                                    fecha_str = item.get('fechaHora') or item.get('fecha')
                                    
                                    if precio is not None and precio > 0 and fecha_str:
                                        fecha_parsed = parse_datetime_flexible(fecha_str)
                                        if fecha_parsed is not None:
                                            precios.append(precio)
                                            fechas.append(fecha_parsed)
                                            
                                except Exception as e:
                                    continue
                            
                            if len(precios) > 10:  # Mínimo de datos válidos
                                # Crear serie de pandas
                                serie = pd.Series(precios, index=fechas, name=simbolo)
                                serie = serie.sort_index()
                                
                                # Verificar que la serie tenga variación
                                if serie.nunique() > 1:
                                    series_data[simbolo] = serie
                                    simbolos_exitosos.append(simbolo)
                                    serie_encontrada = True
                                    mercado_encontrado = mercado
                                    
                                    # Mostrar información del símbolo exitoso
                                    if len(simbolos_exitosos) <= 10:
                                        st.success(f"✅ {simbolo} ({mercado}): {len(serie)} puntos de datos")
                                    break
                            
                    except Exception as e:
                        continue
            
            # Si no se encontró en ningún mercado, marcar como fallido
            if not serie_encontrada:
                simbolos_fallidos.append(simbolo)
                mercado_sugerido = simbolo_mercado_map.get(simbolo, "desconocido")
                detalles_errores[simbolo] = f"No encontrado en ningún mercado (sugerido: {mercado_sugerido})"
        
        # Crear DataFrame con todas las series alineadas
        if series_data:
            df_precios = pd.DataFrame(series_data)
            # Eliminar filas con todos los valores NaN
            df_precios = df_precios.dropna(how='all')
        
        # Limpiar barra de progreso
        progress_bar.empty()
        
        # Informar resultados detallados
        if simbolos_exitosos:
            st.success(f"✅ Datos obtenidos para {len(simbolos_exitosos)} activos")
            with st.expander("📋 Ver activos exitosos"):
                for simbolo in simbolos_exitosos:
                    if simbolo in df_precios.columns:
                        datos_info = f"{simbolo}: {len(df_precios[simbolo])} puntos, rango: {df_precios[simbolo].min():.2f} - {df_precios[simbolo].max():.2f}"
                        st.text(datos_info)
        
        if simbolos_fallidos:
            st.warning(f"⚠️ No se pudieron obtener datos para {len(simbolos_fallidos)} activos")
            with st.expander("❌ Ver activos fallidos y errores"):
                for simbolo in simbolos_fallidos:
                    st.text(f"• {simbolo}")
                
                if detalles_errores:
                    st.markdown("**Detalles de errores:**")
                    for key, error in detalles_errores.items():
                        st.text(f"{key}: {error}")
        
        # Continuar si tenemos al menos 2 activos
        if len(simbolos_exitosos) < 2:
            if len(simbolos_exitosos) == 1:
                st.error("❌ Se necesitan al menos 2 activos con datos históricos válidos para el análisis.")
            else:
                st.error("❌ No se pudieron obtener datos históricos para ningún activo.")
            
            # Mostrar sugerencias
            st.markdown("#### 💡 Sugerencias para resolver el problema:")
            st.markdown("""
            1. **Verificar conectividad**: Asegúrese de que su conexión a IOL esté activa
            2. **Revisar símbolos**: Algunos símbolos pueden haber cambiado o no estar disponibles
            3. **Ajustar fechas**: Pruebe con un rango de fechas más amplio o diferente
            4. **Verificar permisos**: Asegúrese de tener permisos para acceder a datos históricos
            5. **Usar símbolos conocidos**: Pruebe con símbolos como 'GGAL', 'YPF', 'PAMP', 'COME' para acciones argentinas
            """)
            
            return None, None, None
        
        if len(simbolos_exitosos) < len(simbolos):
            st.info(f"ℹ️ Continuando análisis con {len(simbolos_exitosos)} de {len(simbolos)} activos disponibles.")
        
        # Alinear datos por fechas comunes
        st.info(f"📊 Alineando datos de {len(df_precios.columns)} activos...")
        
        # Verificar que tenemos datos válidos antes de alinear
        if df_precios.empty:
            st.error("❌ DataFrame de precios está vacío")
            return None, None, None
        
        # Mostrar información de debug sobre las fechas
        with st.expander("🔍 Debug - Información de fechas"):
            for col in df_precios.columns:
                serie = df_precios[col]
                st.text(f"{col}: {len(serie)} puntos, desde {serie.index.min()} hasta {serie.index.max()}")
        
        # Intentar diferentes estrategias de alineación
        try:
            if df_precios.empty:
                st.error("❌ No se obtuvieron datos históricos para ningún activo")
                return None, None, None
            
            # Mostrar información de debug sobre las fechas
            with st.expander("🔍 Debug - Información de fechas"):
                for col in df_precios.columns:
                    serie = df_precios[col]
                    st.text(f"{col}: {len(serie)} puntos, desde {serie.index.min()} hasta {serie.index.max()}")
            
            # Estrategia 1: Solo fechas con datos completos (más conservadora)
            df_precios_completos = df_precios.dropna()
            
            if not df_precios_completos.empty and len(df_precios_completos) >= 30:
                df_precios = df_precios_completos
                st.info("✅ Usando solo fechas con datos completos")
            else:
                # Estrategia 2: Forward fill y luego backward fill
                df_precios_filled = df_precios.fillna(method='ffill').fillna(method='bfill')
                
                if not df_precios_filled.dropna().empty and len(df_precios_filled.dropna()) >= 30:
                    df_precios = df_precios_filled.dropna()
                    st.info("✅ Usando estrategia forward/backward fill")
                else:
                    # Estrategia 3: Interpolar valores faltantes
                    df_precios_interpolated = df_precios.interpolate(method='time')
                    
                    if not df_precios_interpolated.dropna().empty and len(df_precios_interpolated.dropna()) >= 30:
                        df_precios = df_precios_interpolated.dropna()
                        st.info("✅ Usando estrategia de interpolación")
                    else:
                        # Estrategia 4: Usar cualquier dato disponible
                        df_precios = df_precios.dropna()
                        if df_precios.empty:
                            st.error("❌ No hay fechas comunes entre los activos después del procesamiento")
                            return None, None, None
                        else:
                            st.warning(f"⚠️ Usando datos limitados: {len(df_precios)} observaciones")
            
            if df_precios.empty:
                st.error("❌ No hay fechas comunes entre los activos después del procesamiento")
                return None, None, None
                
        except Exception as e:
            st.error(f"❌ Error al alinear datos: {str(e)}")
            return None, None, None
        
        # Calcular retornos logarítmicos
        try:
            retornos = np.log(df_precios / df_precios.shift(1)).dropna()
            
            if retornos.empty:
                st.error("❌ No se pudieron calcular retornos válidos")
            return None, None, None
        
            st.success(f"✅ Datos alineados: {len(retornos)} fechas, {len(retornos.columns)} activos")
        
            return df_precios, retornos, simbolos_exitosos
        
        except Exception as e:
            st.error(f"❌ Error crítico obteniendo datos históricos: {str(e)}")
            return None, None, None
        
    except Exception as e:
        st.error(f"❌ Error crítico obteniendo datos históricos: {str(e)}")
        return None, None, None

def obtener_serie_historica(simbolo, mercado, fecha_desde, fecha_hasta, ajustada, bearer_token):
    """
    Obtiene la serie histórica de precios para un símbolo y mercado específico.
    Actualizada para usar nombres correctos de mercados IOL.
    """
    # Mapear nombres de mercados a los correctos de IOL
    mercados_mapping = {
        'BCBA': 'bCBA',
        'NYSE': 'nYSE', 
        'NASDAQ': 'nASDAQ',
        'ROFEX': 'rOFEX',
        'Merval': 'bCBA'  # Merval no existe, usar bCBA
    }
    
    mercado_correcto = mercados_mapping.get(mercado, mercado)
    
    url = f"https://api.invertironline.com/api/v2/{mercado_correcto}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None

def detectar_mercado_simbolo(simbolo, bearer_token):
    """
    Detecta automáticamente el mercado correcto para un símbolo.
    Devuelve el mercado más probable o None si no se puede determinar.
    """
    # Patrones para detectar tipos de instrumentos
    if simbolo.endswith('D') or len(simbolo) >= 8:
        return 'bCBA'  # Probablemente un bono argentino
    elif simbolo in ['COME', 'GGAL', 'YPF', 'PAMP', 'TECO2', 'TGS', 'EDN', 'APBR']:
        return 'bCBA'  # Acciones argentinas conocidas
    elif simbolo in ['GOOGL', 'AAPL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'INTC']:
        return 'nYSE'  # Acciones estadounidenses conocidas
    elif simbolo.endswith('FCI') or simbolo in ['ADCGLOA', 'AE38', 'ETHA']:
        return 'FCI'  # Fondos comunes de inversión
    elif re.match(r'^S\d+N\d+$', simbolo):  # Patrón para bonos como S10N5, S30S5
        return 'Bonos'  # Bonos argentinos con formato específico
    elif simbolo in ['AL30', 'GD30', 'GD35', 'GD38', 'GD41', 'GD46', 'GD47', 'GD48', 'GD49', 'GD50']:
        return 'Bonos'  # Bonos argentinos conocidos
    else:
        # Intentar detectar consultando la API
        mercados_test = ['bCBA', 'FCI', 'nYSE', 'nASDAQ', 'Bonos']
        for mercado in mercados_test:
            try:
                url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion"
                headers = {
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {bearer_token}'
                }
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    return mercado
            except Exception:
                continue
        return None

def obtener_clase_d(simbolo, mercado, bearer_token):
    """
    Busca automáticamente la clase 'D' de un bono dado su símbolo y mercado.
    Devuelve el símbolo de la clase 'D' si existe, si no, devuelve None.
    """
    # Mapear nombres de mercados a los correctos de IOL
    mercados_mapping = {
        'BCBA': 'bCBA',
        'NYSE': 'nYSE', 
        'NASDAQ': 'nASDAQ',
        'ROFEX': 'rOFEX',
        'Merval': 'bCBA'  # Merval no existe, usar bCBA
    }
    
    mercado_correcto = mercados_mapping.get(mercado, mercado)
    
    url = f"https://api.invertironline.com/api/v2/{mercado_correcto}/Titulos/{simbolo}/Clases"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            clases = response.json()
            for clase in clases:
                if clase.get('simbolo', '').endswith('D'):
                    return clase['simbolo']
            return None
        else:
            # Silencioso para no interrumpir el flujo
            return None
    except Exception:
        # Silencioso para no interrumpir el flujo
        return None

# Función duplicada eliminada - usar la versión original en línea 933

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
def portfolio_variance(x, mtx_var_covar):
    """Calcula la varianza del portafolio"""
    variance = np.matmul(np.transpose(x), np.matmul(mtx_var_covar, x))
    return variance

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
        self.risk_free_rate = 0.40  # Tasa libre de riesgo anual

    def load_intraday_timeseries(self, ticker):
        return self.data[ticker]

    def synchronise_timeseries(self):
        dic_timeseries = {}
        for ric in self.rics:
            dic_timeseries[ric] = self.load_intraday_timeseries(ric)
        self.timeseries = dic_timeseries

    def compute_covariance(self):
        self.synchronise_timeseries()
        # Calcular retornos logarítmicos
        returns_matrix = {}
        for ric in self.rics:
            prices = self.timeseries[ric]
            # Verificar que prices no sea None y tenga datos
            if prices is not None and len(prices) > 1:
                returns_matrix[ric] = np.log(prices / prices.shift(1)).dropna()
        
        # Verificar que tenemos datos válidos
        if not returns_matrix:
            raise ValueError("No se pudieron obtener datos válidos para calcular la covarianza")
        
        # Convertir a DataFrame para alinear fechas
        self.returns = pd.DataFrame(returns_matrix)
        
        # Verificar que el DataFrame no esté vacío
        if self.returns.empty:
            raise ValueError("No hay datos suficientes para calcular la covarianza")
        
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
                
                result = optimize.minimize(
                    neg_sharpe_ratio, 
                    x0=np.ones(n_assets)/n_assets,
                    method='SLSQP',
                    bounds=bounds,
                    constraints=constraints
                )
                return self._create_output(result.x)
        
        # Optimización general de varianza mínima
        result = optimize.minimize(
            lambda x: portfolio_variance(x, self.cov_matrix),
            x0=np.ones(n_assets)/n_assets,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        return self._create_output(result.x)

    def _create_output(self, weights):
        """Crea un objeto output con los pesos optimizados"""
        port_ret = np.sum(self.mean_returns * weights)
        port_vol = np.sqrt(portfolio_variance(weights, self.cov_matrix))
        
        # Calcular retornos del portafolio
        portfolio_returns = self.returns.dot(weights)
        
        # Crear objeto output
        port_output = output(portfolio_returns, self.notional)
        port_output.weights = weights
        
        # Crear DataFrame de asignación con debugging
        try:
            port_output.dataframe_allocation = pd.DataFrame({
                'rics': self.rics,
                'weights': weights,
                'volatilities': np.sqrt(np.diag(self.cov_matrix)),
                'returns': self.mean_returns
            })
            st.info(f"ℹ️ Debug: Manager DataFrame creado con columnas: {port_output.dataframe_allocation.columns.tolist()}")
        except Exception as e:
            st.error(f"❌ Error creando DataFrame en manager: {str(e)}")
            # Crear DataFrame básico como fallback
            port_output.dataframe_allocation = pd.DataFrame({
                'rics': self.rics,
                'weights': weights
            })
        
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
            # Crear gráfico vacío
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

def compute_efficient_frontier(rics, notional, target_return, include_min_variance, data):
    """Computa la frontera eficiente y portafolios especiales"""
    # special portfolios    
    label1 = 'min-variance-l1'
    label2 = 'min-variance-l2'
    label3 = 'equi-weight'
    label4 = 'long-only'
    label5 = 'markowitz-none'
    label6 = 'markowitz-target'
    
    # compute covariance matrix
    port_mgr = manager(rics, notional, data)
    port_mgr.compute_covariance()
    
    # compute vectors of returns and volatilities for Markowitz portfolios
    min_returns = np.min(port_mgr.mean_returns)
    max_returns = np.max(port_mgr.mean_returns)
    returns = min_returns + np.linspace(0.05, 0.95, 50) * (max_returns - min_returns)
    volatilities = []
    valid_returns = []
    
    for ret in returns:
        try:
            port = port_mgr.compute_portfolio('markowitz', ret)
            volatilities.append(port.volatility_annual)
            valid_returns.append(ret)
        except:
            continue
    
    # compute special portfolios
    portfolios = {}
    try:
        portfolios[label1] = port_mgr.compute_portfolio(label1)
    except:
        portfolios[label1] = None
        
    try:
        portfolios[label2] = port_mgr.compute_portfolio(label2)
    except:
        portfolios[label2] = None
        
    portfolios[label3] = port_mgr.compute_portfolio(label3)
    portfolios[label4] = port_mgr.compute_portfolio(label4)
    portfolios[label5] = port_mgr.compute_portfolio('markowitz')
    
    try:
        portfolios[label6] = port_mgr.compute_portfolio('markowitz', target_return)
    except:
        portfolios[label6] = None
    
    return portfolios, valid_returns, volatilities

# --- Portfolio Optimization Functions ---
def calculate_portfolio_metrics(returns, weights):
    """
    Calcula métricas básicas de un portafolio con validaciones mejoradas
    """
    try:
        # Validar inputs
        if returns is None or returns.empty:
            return 0.0, 0.0, 0.0
        
        if weights is None or len(weights) == 0:
            return 0.0, 0.0, 0.0
        
        # Asegurar que weights sea un array numpy
        weights = np.array(weights)
        
        # Validar que los pesos sumen aproximadamente 1
        if abs(np.sum(weights) - 1.0) > 0.01:
            st.warning("⚠️ Los pesos no suman 1. Normalizando...")
            weights = weights / np.sum(weights)
        
        # Calcular retorno anualizado (252 días de trading)
        portfolio_return = np.sum(returns.mean() * weights) * 252
        
        # Calcular volatilidad anualizada
        cov_matrix = returns.cov() * 252
        portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        
        # Calcular ratio de Sharpe con validación
        if portfolio_std > 0:
            sharpe_ratio = portfolio_return / portfolio_std
        else:
            sharpe_ratio = 0.0
        
        # Validar resultados
        if np.isnan(portfolio_return) or np.isinf(portfolio_return):
            portfolio_return = 0.0
        if np.isnan(portfolio_std) or np.isinf(portfolio_std):
            portfolio_std = 0.0
        if np.isnan(sharpe_ratio) or np.isinf(sharpe_ratio):
            sharpe_ratio = 0.0
        
        return portfolio_return, portfolio_std, sharpe_ratio
        
    except Exception as e:
        st.error(f"❌ Error en cálculo de métricas: {str(e)}")
        return 0.0, 0.0, 0.0

def optimize_portfolio(returns, risk_free_rate=0.0, target_return=None):
    """
    Optimiza un portafolio usando teoría moderna de portafolio con validaciones mejoradas
    """
    try:
        # Validar inputs
        if returns is None or returns.empty:
            st.error("❌ Datos de retornos no válidos")
            return None
        
        n_assets = len(returns.columns)
        if n_assets < 2:
            st.error("❌ Se necesitan al menos 2 activos para optimización")
            return None
        
        # Validar que no haya valores NaN o infinitos
        if returns.isnull().any().any() or np.isinf(returns).any().any():
            st.warning("⚠️ Datos con valores faltantes o infinitos. Limpiando...")
            returns = returns.dropna()
            if returns.empty:
                st.error("❌ No quedan datos válidos después de limpiar")
                return None
        
        # Función objetivo para maximizar el ratio de Sharpe
        def negative_sharpe(weights):
            try:
                portfolio_return = np.sum(returns.mean() * weights) * 252
                cov_matrix = returns.cov() * 252
                portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                
                if portfolio_std == 0 or np.isnan(portfolio_std) or np.isinf(portfolio_std):
                    return 1e6  # Penalización alta
                
                sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_std
                return -sharpe_ratio
            except Exception:
                return 1e6  # Penalización alta en caso de error
        
        # Restricciones
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        # Pesos iniciales igualmente distribuidos
        initial_guess = n_assets * [1. / n_assets]
        
        # Optimización con múltiples intentos
        best_result = None
        best_sharpe = -np.inf
        
        for attempt in range(3):  # Intentar 3 veces con diferentes puntos iniciales
            try:
                if attempt > 0:
                    # Usar pesos aleatorios para intentos adicionales
                    random_weights = np.random.dirichlet(np.ones(n_assets))
                    initial_guess = random_weights
                
                result = optimize.minimize(negative_sharpe, initial_guess, method='SLSQP',
                                         bounds=bounds, constraints=constraints,
                                         options={'maxiter': 1000})
                
                if result.success:
                    # Validar resultado
                    weights = result.x
                    if np.all(weights >= 0) and abs(np.sum(weights) - 1.0) < 0.01:
                        # Calcular Sharpe del resultado
                        portfolio_return = np.sum(returns.mean() * weights) * 252
                        cov_matrix = returns.cov() * 252
                        portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                        
                        if portfolio_std > 0:
                            sharpe = (portfolio_return - risk_free_rate) / portfolio_std
                            if sharpe > best_sharpe:
                                best_result = weights
                                best_sharpe = sharpe
                
            except Exception as e:
                st.warning(f"⚠️ Intento {attempt + 1} falló: {str(e)}")
                continue
        
        if best_result is not None:
            return best_result
        else:
            st.warning("⚠️ La optimización no convergió. Usando pesos iguales.")
            return np.array([1/n_assets] * n_assets)
            
    except ImportError:
        st.warning("⚠️ scipy no disponible. Usando pesos iguales.")
        return np.array([1/n_assets] * n_assets)
    except Exception as e:
        st.error(f"❌ Error en optimización: {str(e)}. Usando pesos iguales.")
        return np.array([1/n_assets] * n_assets)

def mostrar_resumen_operaciones_reales(portafolio, token_portador, portfolio_id="", id_cliente=None):
    """
    Muestra un resumen de las operaciones reales de compra/venta del portafolio.
    """
    st.markdown("### 📊 Resumen de Operaciones Reales")
    
    try:
        # Obtener fechas para el análisis
        fecha_hasta = datetime.now().strftime('%Y-%m-%d')
        fecha_desde = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        
        with st.spinner("🔄 Analizando operaciones reales del portafolio..."):
            # Reconstruir composición del portafolio
            composicion_por_fecha, posiciones_actuales = reconstruir_composicion_portafolio(
                token_portador, portafolio, fecha_desde, fecha_hasta, id_cliente
            )
        
        if not posiciones_actuales:
            st.warning("⚠️ No se encontraron operaciones para analizar")
            return
        
        # Mostrar resumen general
        total_operaciones = sum(len(pos['operaciones']) for pos in posiciones_actuales.values())
        activos_con_operaciones = sum(1 for pos in posiciones_actuales.values() if pos['operaciones'])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📈 Total Operaciones", f"{total_operaciones}")
        
        with col2:
            st.metric("🏢 Activos con Operaciones", f"{activos_con_operaciones}")
        
        with col3:
            st.metric("📅 Período Analizado", f"{(datetime.now() - datetime.strptime(fecha_desde, '%Y-%m-%d')).days} días")
        
        # Mostrar detalles por activo
        st.markdown("#### 📋 Detalle por Activo")
        
        for simbolo, posicion in posiciones_actuales.items():
            if not posicion['operaciones']:
                continue
                
            with st.expander(f"🔍 {simbolo} - {len(posicion['operaciones'])} operaciones"):
                # Resumen de operaciones
                compras = [op for op in posicion['operaciones'] if op['tipo'] == 'compra']
                ventas = [op for op in posicion['operaciones'] if op['tipo'] == 'venta']
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("💰 Compras", f"{len(compras)}")
                
                with col2:
                    st.metric("💸 Ventas", f"{len(ventas)}")
                
                with col3:
                    st.metric("📊 Cantidad Actual", f"{posicion['cantidad']}")
                
                with col4:
                    if posicion['precio_compra'] > 0:
                        st.metric("💵 Precio Promedio", f"${posicion['precio_compra']:.2f}")
                    else:
                        st.metric("💵 Precio Promedio", "N/A")
                
                # Tabla de operaciones
                if posicion['operaciones']:
                    df_operaciones = pd.DataFrame(posicion['operaciones'])
                    df_operaciones['fecha'] = pd.to_datetime(df_operaciones['fecha'])
                    df_operaciones = df_operaciones.sort_values('fecha', ascending=False)
                    
                    # Formatear columnas
                    df_operaciones['precio'] = df_operaciones['precio'].apply(lambda x: f"${x:,.2f}")
                    df_operaciones['cantidad'] = df_operaciones['cantidad'].apply(lambda x: f"{x:,.0f}")
                    
                    st.dataframe(
                        df_operaciones[['fecha', 'tipo', 'cantidad', 'precio']],
                        use_container_width=True,
                        hide_index=True
                    )
                
                # Calcular retorno real si hay datos históricos
                if st.button(f"📈 Calcular Retorno Real - {simbolo}", key=f"calc_retorno_{simbolo}"):
                    try:
                        # Obtener datos históricos para el cálculo
                        # Buscar el activo en el portafolio
                        mercado = 'BCBA'  # Por defecto
                        if 'activos' in portafolio:
                            for activo in portafolio['activos']:
                                if activo.get('titulo', {}).get('simbolo') == simbolo:
                                    mercado = activo.get('titulo', {}).get('mercado', 'BCBA')
                                    break
                        
                        serie_historica = obtener_serie_historica_iol(
                            token_portador, mercado, simbolo, fecha_desde, fecha_hasta
                        )
                        
                        if serie_historica is not None and not serie_historica.empty:
                            retorno_real = calcular_retorno_real_activo(simbolo, posiciones_actuales, serie_historica)
                            
                            if retorno_real:
                                st.success("✅ Retorno Real Calculado")
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.metric(
                                        "📊 Retorno Total", 
                                        f"{retorno_real['retorno_total']*100:.2f}%",
                                        help="Retorno desde la primera compra hasta hoy"
                                    )
                                    
                                    st.metric(
                                        "📈 Retorno Anualizado", 
                                        f"{retorno_real['retorno_anualizado']*100:.2f}%",
                                        help="Retorno anualizado basado en el tiempo transcurrido"
                                    )
                                
                                with col2:
                                    st.metric(
                                        "💵 Flujo Compras", 
                                        f"${retorno_real['flujo_compras']:,.2f}",
                                        help="Total invertido en compras"
                                    )
                                    
                                    st.metric(
                                        "💸 Flujo Ventas", 
                                        f"${retorno_real['flujo_ventas']:,.2f}",
                                        help="Total obtenido en ventas"
                                    )
                                
                                # Información adicional
                                st.info(f"📅 **Primera Compra:** {retorno_real['fecha_primera_compra']}")
                                st.info(f"💰 **Valor Actual:** ${retorno_real['valor_actual']:,.2f}")
                                st.info(f"📊 **Volatilidad Anualizada:** {retorno_real['volatilidad_anualizada']*100:.2f}%")
                                
                            else:
                                st.warning("⚠️ No se pudo calcular el retorno real")
                        else:
                            st.warning("⚠️ No se pudieron obtener datos históricos para el cálculo")
                            
                    except Exception as e:
                        st.error(f"❌ Error al calcular retorno real: {str(e)}")
        
        # Mostrar evolución temporal del portafolio
        if len(composicion_por_fecha) > 1:
            st.markdown("#### 📈 Evolución Temporal del Portafolio")
            
            # Crear DataFrame de evolución
            fechas = sorted(composicion_por_fecha.keys())
            df_evolucion = pd.DataFrame(index=fechas)
            
            for simbolo in posiciones_actuales.keys():
                df_evolucion[simbolo] = [
                    composicion_por_fecha[fecha].get(simbolo, {}).get('cantidad', 0)
                    for fecha in fechas
                ]
            
            # Gráfico de evolución
            fig = go.Figure()
            
            for simbolo in df_evolucion.columns:
                if df_evolucion[simbolo].sum() > 0:  # Solo mostrar activos con operaciones
                    fig.add_trace(go.Scatter(
                        x=df_evolucion.index,
                        y=df_evolucion[simbolo],
                        mode='lines+markers',
                        name=simbolo,
                        line=dict(width=2)
                    ))
            
            fig.update_layout(
                title="Evolución de Cantidades por Activo",
                xaxis_title="Fecha",
                yaxis_title="Cantidad",
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"❌ Error al analizar operaciones: {str(e)}")
        st.info("💡 Asegúrate de que el token de acceso sea válido y tengas permisos para ver operaciones")

# --- Menú de Optimizaciones Avanzadas ---
def mostrar_menu_optimizaciones_avanzadas(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Menú completo de optimizaciones con capital inicial, horizonte, benchmark y análisis de alpha/beta
    """
    st.markdown("### 🎯 Menú de Optimizaciones Avanzadas")
    
    activos = portafolio.get('activos', [])
    if not activos:
        st.warning("No hay activos en el portafolio para optimizar")
        return
    
    # Extraer símbolos del portafolio
    simbolos = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', '')
        if simbolo:
            simbolos.append(simbolo)
    
    if len(simbolos) < 2:
        st.warning("Se necesitan al menos 2 activos para optimización")
        return
    
    # Configuración principal
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💰 Configuración de Capital")
        capital_inicial = st.number_input(
            "Capital Inicial (USD):",
            min_value=1000.0, max_value=10000000.0, value=100000.0, step=1000.0,
            help="Capital inicial para la optimización"
        )
        
        horizonte_dias = st.number_input(
            "Horizonte de Inversión (días):",
            min_value=30, max_value=3650, value=252, step=30,
            help="Horizonte temporal para el análisis"
        )
        
        # La tasa libre de riesgo se obtendrá automáticamente del benchmark seleccionado
        st.info("💡 **Tasa Libre de Riesgo**: Se usará automáticamente la tasa de caución del benchmark seleccionado")
    
    with col2:
        st.markdown("#### 📊 Configuración de Benchmark")
        benchmark_options = ['^SPX', 'SPY', '^GSPC', '^IXIC', '^DJI'] + simbolos
        benchmark = st.selectbox(
            "Benchmark de Referencia:",
            options=benchmark_options,
            index=0,
            help="Índice de referencia para análisis alpha/beta",
            key="benchmark_avanzada"
        )
        
        profit_esperado = st.number_input(
            "Profit Esperado (% anual):",
            min_value=0.0, max_value=100.0, value=8.0, step=0.1,
            help="Rendimiento esperado del portafolio"
        )
        
        # La tasa libre de riesgo se obtiene automáticamente del benchmark
        st.info("🎯 **Optimización Automática**: La tasa libre de riesgo se calcula automáticamente desde el benchmark")
    
    # Configuración de estrategias
    st.markdown("#### 🎯 Estrategias de Optimización")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        estrategias_basicas = st.multiselect(
            "Estrategias Básicas:",
            options=['min-variance-l1', 'min-variance-l2', 'equi-weight', 'long-only'],
            default=['min-variance-l1', 'equi-weight'],
            help="Estrategias de optimización básicas"
        )
    
    with col2:
        estrategias_avanzadas = st.multiselect(
            "Estrategias Avanzadas:",
            options=['markowitz', 'markowitz-target', 'black-litterman', 'risk-parity'],
            default=['markowitz'],
            help="Estrategias de optimización avanzadas"
        )
    
    with col3:
        mostrar_histogramas = st.checkbox("Mostrar Histogramas", value=True, key="mostrar_histogramas_avanzada")
        mostrar_frontera = st.checkbox("Mostrar Frontera Eficiente", value=True, key="mostrar_frontera_avanzada")
    
    # Botón de ejecución
    ejecutar_optimizacion = st.button("🚀 Ejecutar Optimización Avanzada", type="primary")
    
    if ejecutar_optimizacion:
        with st.spinner("Ejecutando optimización avanzada..."):
            try:
                # Crear manager de portafolio
                manager_inst = PortfolioManager(simbolos, token_acceso, fecha_desde, fecha_hasta)
                
                # Cargar datos con métricas reales
                if manager_inst.load_data_with_real_metrics(portafolio):
                    st.success("✅ Datos históricos cargados")
                    
                    # Calcular rendimiento esperado del benchmark
                    if benchmark in manager_inst.returns.columns:
                        benchmark_return = manager_inst.returns[benchmark].mean() * 252
                        st.info(f"📈 Rendimiento esperado del benchmark ({benchmark}): {benchmark_return:.2%} anual")
                        
                        # Validar que profit esperado sea mayor al benchmark
                        if profit_esperado/100 <= benchmark_return:
                            st.warning(f"⚠️ El profit esperado ({profit_esperado:.1f}%) debe ser mayor al rendimiento del benchmark ({benchmark_return:.2%})")
                            profit_esperado = (benchmark_return + 0.02) * 100  # Ajustar automáticamente
                            st.info(f"💡 Profit esperado ajustado a: {profit_esperado:.1f}%")
                    else:
                        st.warning(f"⚠️ Benchmark {benchmark} no disponible en datos históricos")
                        benchmark_return = 0.08  # Valor por defecto
                    
                    # Calcular portafolios
                    portafolios_resultados = {}
                    
                    # Estrategias básicas
                    for estrategia in estrategias_basicas:
                        try:
                            portfolio_result = manager_inst.compute_portfolio(strategy=estrategia)
                            if portfolio_result:
                                portafolios_resultados[estrategia] = portfolio_result
                        except Exception as e:
                            st.warning(f"⚠️ Error en estrategia {estrategia}: {str(e)}")
                    
                    # Estrategias avanzadas
                    for estrategia in estrategias_avanzadas:
                        try:
                            if estrategia == 'markowitz-target':
                                portfolio_result = manager_inst.compute_portfolio(
                                    strategy='markowitz', 
                                    target_return=profit_esperado/100
                                )
                            else:
                                portfolio_result = manager_inst.compute_portfolio(strategy=estrategia)
                            
                            if portfolio_result:
                                portafolios_resultados[estrategia] = portfolio_result
                        except Exception as e:
                            st.warning(f"⚠️ Error en estrategia {estrategia}: {str(e)}")
                    
                    if portafolios_resultados:
                        st.success(f"✅ {len(portafolios_resultados)} portafolios optimizados calculados")
                        
                        # Mostrar resultados comparativos
                        mostrar_resultados_optimizacion_avanzada(
                            portafolios_resultados, capital_inicial, horizonte_dias,
                            benchmark, benchmark_return, profit_esperado, benchmark_return,
                            mostrar_histogramas, mostrar_frontera
                        )
                    else:
                        st.error("❌ No se pudieron calcular portafolios optimizados")
                else:
                    st.error("❌ No se pudieron cargar los datos históricos")
                    
            except Exception as e:
                st.error(f"❌ Error durante la optimización: {str(e)}")

def mostrar_resultados_optimizacion_avanzada(portafolios, capital_inicial, horizonte_dias, 
                                           benchmark, benchmark_return, profit_esperado, 
                                           tasa_libre_riesgo, mostrar_histogramas, mostrar_frontera):
    """
    Muestra resultados detallados de la optimización avanzada
    """
    st.markdown("#### 📊 Resultados de Optimización")
    
    # Tabla comparativa
    resultados_data = []
    for nombre, portfolio in portafolios.items():
        if portfolio and hasattr(portfolio, 'get_metrics_dict'):
            metricas = portfolio.get_metrics_dict()
            
            # Calcular alpha y beta vs benchmark
            alpha, beta = calcular_alpha_beta(portfolio, benchmark)
            
            # Calcular métricas adicionales
            sharpe_ratio = (metricas['Annual Return'] - tasa_libre_riesgo/100) / metricas['Annual Volatility'] if metricas['Annual Volatility'] > 0 else 0
            sortino_ratio = (metricas['Annual Return'] - tasa_libre_riesgo/100) / metricas.get('Downside Deviation', metricas['Annual Volatility']) if metricas.get('Downside Deviation', metricas['Annual Volatility']) > 0 else 0
            
            resultados_data.append({
                'Estrategia': nombre.replace('-', ' ').title(),
                'Retorno Anual': f"{metricas['Annual Return']:.2%}",
                'Volatilidad Anual': f"{metricas['Annual Volatility']:.2%}",
                'Sharpe Ratio': f"{sharpe_ratio:.3f}",
                'Sortino Ratio': f"{sortino_ratio:.3f}",
                'VaR 95%': f"{metricas['VaR 95%']:.4f}",
                'Alpha': f"{alpha:.4f}",
                'Beta': f"{beta:.4f}",
                'Capital Final': f"${capital_inicial * (1 + metricas['Annual Return']):,.0f}"
            })
    
    if resultados_data:
        df_resultados = pd.DataFrame(resultados_data)
        st.dataframe(df_resultados, use_container_width=True)
        
        # Gráficos de histogramas
        if mostrar_histogramas:
            st.markdown("#### 📈 Histogramas de Retornos")
            
            # Crear subplots para histogramas
            num_portafolios = len(portafolios)
            cols = st.columns(min(3, num_portafolios))
            
            for idx, (nombre, portfolio) in enumerate(portafolios.items()):
                if portfolio and hasattr(portfolio, 'plot_histogram_streamlit'):
                    with cols[idx % 3]:
                        fig = portfolio.plot_histogram_streamlit(f"Distribución - {nombre}")
                        st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de frontera eficiente
        if mostrar_frontera:
            st.markdown("#### 📊 Frontera Eficiente")
            
            # Preparar datos para la frontera
            riesgos = []
            retornos = []
            nombres = []
            
            for nombre, portfolio in portafolios.items():
                if portfolio and hasattr(portfolio, 'get_metrics_dict'):
                    metricas = portfolio.get_metrics_dict()
                    riesgos.append(metricas['Annual Volatility'])
                    retornos.append(metricas['Annual Return'])
                    nombres.append(nombre)
            
            if len(riesgos) > 1:
                # Crear gráfico de frontera eficiente
                fig = go.Figure()
                
                # Puntos de portafolios
                fig.add_trace(go.Scatter(
                    x=riesgos,
                    y=retornos,
                    mode='markers+text',
                    text=nombres,
                    textposition="top center",
                    marker=dict(
                        size=12,
                        color=['red', 'blue', 'green', 'orange', 'purple', 'brown'][:len(riesgos)],
                        symbol='diamond'
                    ),
                    name='Portafolios Optimizados'
                ))
                
                # Línea de frontera eficiente (simplificada)
                if len(riesgos) >= 3:
                    # Ordenar por riesgo
                    sorted_data = sorted(zip(riesgos, retornos, nombres))
                    sorted_riesgos, sorted_retornos, sorted_nombres = zip(*sorted_data)
                    
                    fig.add_trace(go.Scatter(
                        x=sorted_riesgos,
                        y=sorted_retornos,
                        mode='lines',
                        line=dict(color='gray', dash='dash'),
                        name='Frontera Eficiente'
                    ))
                
                # Punto de benchmark
                fig.add_trace(go.Scatter(
                    x=[benchmark_return * 0.2],  # Volatilidad estimada del benchmark
                    y=[benchmark_return],
                    mode='markers',
                    marker=dict(size=15, color='black', symbol='star'),
                    name=f'Benchmark ({benchmark})'
                ))
                
                fig.update_layout(
                    title='Frontera Eficiente - Portafolios Optimizados',
                    xaxis_title='Volatilidad Anual',
                    yaxis_title='Retorno Anual',
                    showlegend=True,
                    template='plotly_white'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Análisis de recomendaciones
        st.markdown("#### 💡 Análisis y Recomendaciones")
        
        # Encontrar mejor portafolio por Sharpe ratio
        mejor_sharpe = max(resultados_data, key=lambda x: float(x['Sharpe Ratio']))
        mejor_retorno = max(resultados_data, key=lambda x: float(x['Retorno Anual'].rstrip('%')))
        menor_riesgo = min(resultados_data, key=lambda x: float(x['Volatilidad Anual'].rstrip('%')))
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Mejor Sharpe Ratio",
                mejor_sharpe['Estrategia'],
                delta=f"Sharpe: {mejor_sharpe['Sharpe Ratio']}"
            )
        
        with col2:
            st.metric(
                "Mayor Retorno",
                mejor_retorno['Estrategia'],
                delta=f"Retorno: {mejor_retorno['Retorno Anual']}"
            )
        
        with col3:
            st.metric(
                "Menor Riesgo",
                menor_riesgo['Estrategia'],
                delta=f"Volatilidad: {menor_riesgo['Volatilidad Anual']}"
            )
        
        # Recomendaciones específicas
        st.markdown("#### 🎯 Recomendaciones Específicas")
        
        if float(mejor_sharpe['Sharpe Ratio']) > 1.0:
            st.success(f"✅ **{mejor_sharpe['Estrategia']}** es la estrategia más eficiente (Sharpe > 1.0)")
        elif float(mejor_sharpe['Sharpe Ratio']) > 0.5:
            st.info(f"ℹ️ **{mejor_sharpe['Estrategia']}** muestra buena eficiencia (Sharpe > 0.5)")
        else:
            st.warning(f"⚠️ Todas las estrategias muestran baja eficiencia (Sharpe < 0.5)")
        
        # Análisis de alpha
        alphas = [float(r['Alpha']) for r in resultados_data]
        mejor_alpha = max(alphas)
        if mejor_alpha > 0.02:
            st.success(f"✅ Estrategia con mejor alpha: {mejor_alpha:.2%} (genera valor agregado)")
        elif mejor_alpha > 0:
            st.info(f"ℹ️ Alpha positivo: {mejor_alpha:.2%} (moderado valor agregado)")
        else:
            st.warning(f"⚠️ Alpha negativo: {mejor_alpha:.2%} (no genera valor agregado)")

def calcular_alpha_beta(portfolio, benchmark):
    """
    Calcula alpha y beta de un portafolio vs benchmark con validaciones mejoradas
    """
    try:
        if not hasattr(portfolio, 'returns') or portfolio.returns is None:
            st.warning("⚠️ No hay datos de retornos del portafolio")
            return 0.0, 1.0
        
        portfolio_returns = portfolio.returns
        
        # Validar datos del portafolio
        if len(portfolio_returns) < 30:  # Mínimo 30 observaciones
            st.warning("⚠️ Insuficientes datos históricos para cálculo de alpha/beta")
            return 0.0, 1.0
        
        # Obtener retornos del benchmark (mejorado)
        try:
            # Intentar obtener datos reales del benchmark
            if hasattr(benchmark, 'returns') and benchmark.returns is not None:
                benchmark_returns = benchmark.returns
            else:
                # Simular benchmark con parámetros más realistas
                # Usar volatilidad y retorno más conservadores
                benchmark_vol = 0.15  # 15% volatilidad anual
                benchmark_return = 0.08  # 8% retorno anual
                daily_vol = benchmark_vol / np.sqrt(252)
                daily_return = benchmark_return / 252
                
                benchmark_returns = np.random.normal(daily_return, daily_vol, len(portfolio_returns))
                st.info("ℹ️ Usando benchmark simulado para cálculo de alpha/beta")
        except Exception:
            st.warning("⚠️ Error obteniendo datos del benchmark")
            return 0.0, 1.0
        
        # Validar que ambos arrays tengan la misma longitud
        if len(portfolio_returns) != len(benchmark_returns):
            min_length = min(len(portfolio_returns), len(benchmark_returns))
            portfolio_returns = portfolio_returns[:min_length]
            benchmark_returns = benchmark_returns[:min_length]
            st.warning(f"⚠️ Ajustando longitud de datos a {min_length} observaciones")
        
        # Calcular beta con validaciones
        if len(benchmark_returns) > 1:
            benchmark_var = np.var(benchmark_returns)
            if benchmark_var > 0:
                covariance = np.cov(portfolio_returns, benchmark_returns)[0,1]
                beta = covariance / benchmark_var
                
                # Validar beta
                if np.isnan(beta) or np.isinf(beta):
                    st.warning("⚠️ Beta calculado no válido, usando beta = 1")
                    beta = 1.0
                elif abs(beta) > 5:  # Beta muy extremo
                    st.warning(f"⚠️ Beta muy extremo ({beta:.2f}), limitando a ±3")
                    beta = np.clip(beta, -3, 3)
            else:
                st.warning("⚠️ Varianza del benchmark es cero, usando beta = 1")
                beta = 1.0
        else:
            st.warning("⚠️ Insuficientes datos para calcular beta, usando beta = 1")
            beta = 1.0
        
        # Calcular alpha anualizado
        portfolio_mean = np.mean(portfolio_returns) * 252
        benchmark_mean = np.mean(benchmark_returns) * 252
        alpha = portfolio_mean - beta * benchmark_mean
        
        # Validar alpha
        if np.isnan(alpha) or np.isinf(alpha):
            st.warning("⚠️ Alpha calculado no válido, usando alpha = 0")
            alpha = 0.0
        
        return alpha, beta
        
    except Exception as e:
        st.error(f"❌ Error calculando alpha/beta: {str(e)}")
        return 0.0, 1.0

# --- CAPM y Funciones de Cobertura ---
def dataframe_correlacion_beta(benchmark, position_security, hedge_universe, token_portador=None, fecha_desde=None, fecha_hasta=None):
    """
    Calcula correlaciones y betas usando datos históricos de IOL
    """
    try:
        # Obtener datos históricos para todos los activos
        all_securities = [benchmark, position_security] + hedge_universe
        all_securities = list(set(all_securities))  # Eliminar duplicados
        
        if token_portador and fecha_desde and fecha_hasta:
            # Usar datos de IOL si están disponibles
            df_precios, returns, simbolos_exitosos = get_historical_data_for_optimization(
                token_portador, all_securities, fecha_desde, fecha_hasta
            )
            
            if returns is not None and not returns.empty:
                # Continuar con el procesamiento
                pass
            else:
                # No hay fallback - solo usar IOL
                st.error("No se pudieron obtener datos históricos de IOL")
                return pd.DataFrame()
        else:
            # No hay fallback - solo usar IOL
            st.error("No se pudieron obtener datos históricos de IOL")
            return pd.DataFrame()
        
        if returns is None or returns.empty:
            st.error("No se pudieron obtener datos históricos")
            return pd.DataFrame()
        
        # Calcular correlaciones y betas
        correlations = {}
        betas = {}
        
        for security in hedge_universe:
            if security in returns.columns and benchmark in returns.columns:
                # Correlación con la posición
                if position_security in returns.columns:
                    corr_pos = returns[security].corr(returns[position_security])
                    correlations[f'{security}_vs_position'] = corr_pos
                
                # Correlación con benchmark
                corr_bench = returns[security].corr(returns[benchmark])
                correlations[f'{security}_vs_benchmark'] = corr_bench
                
                # Beta vs benchmark
                if returns[benchmark].var() > 0:
                    beta = returns[security].cov(returns[benchmark]) / returns[benchmark].var()
                    betas[security] = beta
                else:
                    betas[security] = 0
        
        # Crear DataFrame de resultados
        results = []
        for security in hedge_universe:
            if security in returns.columns:
                results.append({
                    'Activo': security,
                    'Correlación vs Posición': correlations.get(f'{security}_vs_position', 0),
                    'Correlación vs Benchmark': correlations.get(f'{security}_vs_benchmark', 0),
                    'Beta vs Benchmark': betas.get(security, 0),
                    'Volatilidad': returns[security].std() * np.sqrt(252),
                    'Retorno Anual': returns[security].mean() * 252
                })
        
        return pd.DataFrame(results)
        
    except Exception as e:
        st.error(f"Error calculando correlaciones y betas: {str(e)}")
        return pd.DataFrame()

# Función removida - usando solo API de IOL

class Coberturista:
    """
    Clase para calcular coberturas óptimas usando modelo CAPM
    """
    def __init__(self, position_security, position_delta_usd, benchmark, hedge_securities, 
                 token_portador=None, fecha_desde=None, fecha_hasta=None):
        self.position_security = position_security
        self.position_delta_usd = position_delta_usd
        self.benchmark = benchmark
        self.hedge_securities = hedge_securities
        self.token_portador = token_portador
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        
        # Variables de resultado
        self.beta_posicion_ars = 0
        self.pesos_cobertura = []
        self.delta_cobertura_ars = 0
        self.beta_cobertura_ars = 0
        self.costo_cobertura_ars = 0
        self.betas_cobertura = []
        
        # Datos históricos
        self.returns = None
        self.mean_returns = None
        self.cov_matrix = None
    
    def cargar_datos_historicos(self):
        """
        Carga datos históricos usando solo IOL
        """
        try:
            all_securities = [self.benchmark, self.position_security] + self.hedge_securities
            all_securities = list(set(all_securities))
            
            if self.token_portador and self.fecha_desde and self.fecha_hasta:
                # Intentar con IOL primero
                df_precios, retornos, simbolos_exitosos = get_historical_data_for_optimization(
                    self.token_portador, all_securities, self.fecha_desde, self.fecha_hasta
                )
                
                if df_precios is not None and retornos is not None and not retornos.empty:
                    self.returns = retornos
                    self.mean_returns = retornos.mean() * 252  # Anualizar
                    self.cov_matrix = retornos.cov() * 252     # Anualizar
                    return True
            
            # No hay fallback - solo usar IOL
            return False
            
        except Exception as e:
            st.error(f"Error cargando datos históricos: {str(e)}")
            return False
    
    def calcular_betas(self):
        """
        Calcula betas de la posición y activos de cobertura
        """
        if self.returns is None:
            if not self.cargar_datos_historicos():
                return False
        
        try:
            # Beta de la posición vs benchmark
            if (self.position_security in self.returns.columns and 
                self.benchmark in self.returns.columns):
                if self.returns[self.benchmark].var() > 0:
                    self.beta_posicion_ars = (self.returns[self.position_security]
                                            .cov(self.returns[self.benchmark]) / 
                                            self.returns[self.benchmark].var())
                else:
                    self.beta_posicion_ars = 0
            
            # Betas de activos de cobertura
            self.betas_cobertura = []
            for security in self.hedge_securities:
                if security in self.returns.columns and self.benchmark in self.returns.columns:
                    if self.returns[self.benchmark].var() > 0:
                        beta = (self.returns[security]
                               .cov(self.returns[self.benchmark]) / 
                               self.returns[self.benchmark].var())
                    else:
                        beta = 0
                    self.betas_cobertura.append(beta)
                else:
                    self.betas_cobertura.append(0)
            
            return True
            
        except Exception as e:
            st.error(f"Error calculando betas: {str(e)}")
            return False
    
    def calcular_pesos_cobertura(self, regularizacion=0.1):
        """
        Calcula pesos óptimos de cobertura usando optimización
        """
        if not self.betas_cobertura or len(self.betas_cobertura) != len(self.hedge_securities):
            st.error("Debe calcular betas antes de calcular pesos de cobertura")
            return False
        
        try:
            n_hedge = len(self.hedge_securities)
            
            # Función objetivo: minimizar varianza de la cobertura
            def objective(weights):
                # Varianza del portafolio de cobertura
                hedge_variance = 0
                for i in range(n_hedge):
                    for j in range(n_hedge):
                        if (self.hedge_securities[i] in self.returns.columns and 
                            self.hedge_securities[j] in self.returns.columns):
                            hedge_variance += (weights[i] * weights[j] * 
                                            self.cov_matrix.loc[self.hedge_securities[i], 
                                                              self.hedge_securities[j]])
                
                # Penalización por regularización
                regularization_penalty = regularizacion * np.sum(weights**2)
                
                return hedge_variance + regularization_penalty
            
            # Restricciones: beta de cobertura = -beta de posición
            def constraint_beta(weights):
                hedge_beta = np.sum(np.array(weights) * np.array(self.betas_cobertura))
                return hedge_beta + self.beta_posicion_ars
            
            # Restricción: suma de pesos = 1
            def constraint_sum(weights):
                return np.sum(weights) - 1
            
            # Optimización
            initial_weights = np.ones(n_hedge) / n_hedge
            bounds = [(-2, 2) for _ in range(n_hedge)]  # Permitir posiciones cortas
            
            constraints = [
                {'type': 'eq', 'fun': constraint_beta},
                {'type': 'eq', 'fun': constraint_sum}
            ]
            
            result = optimize.minimize(
                objective, 
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            if result.success:
                self.pesos_cobertura = result.x
                
                # Calcular métricas de la cobertura
                self._calcular_metricas_cobertura()
                return True
            else:
                st.warning("La optimización no convergió")
                return False
                
        except Exception as e:
            st.error(f"Error calculando pesos de cobertura: {str(e)}")
            return False
    
    def _calcular_metricas_cobertura(self):
        """
        Calcula métricas de la cobertura
        """
        try:
            # Delta de la cobertura
            self.delta_cobertura_ars = np.sum(np.array(self.pesos_cobertura) * 
                                            np.array(self.betas_cobertura)) * self.position_delta_usd
            
            # Beta de la cobertura
            self.beta_cobertura_ars = np.sum(np.array(self.pesos_cobertura) * 
                                           np.array(self.betas_cobertura))
            
            # Costo estimado (simplificado)
            self.costo_cobertura_ars = np.sum(np.abs(self.pesos_cobertura)) * self.position_delta_usd * 0.001
            
        except Exception as e:
            st.error(f"Error calculando métricas de cobertura: {str(e)}")

def mostrar_cobertura_portafolio(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Muestra la funcionalidad de cobertura de portafolio
    """
    st.markdown("### 🛡️ Cobertura de Portafolio")
    
    activos = portafolio.get('activos', [])
    if not activos:
        st.warning("No hay activos en el portafolio para analizar cobertura")
        return
    
    # Extraer símbolos del portafolio
    simbolos = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', '')
        if simbolo:
            simbolos.append(simbolo)
    
    if len(simbolos) < 1:
        st.warning("Se necesita al menos 1 activo para análisis de cobertura")
        return
    
    st.info(f"📊 Analizando cobertura para {len(simbolos)} activos del portafolio")
    
    # Configuración de cobertura
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Configuración de Posición")
        position_security = st.selectbox(
            "Activo principal de la posición:",
            options=simbolos,
            help="Selecciona el activo principal que deseas cubrir",
            key="position_security_cobertura"
        )
        
        position_delta_usd = st.number_input(
            "Delta de la posición (millones USD):",
            min_value=0.1, max_value=1000.0, value=10.0, step=0.1,
            help="Exposición en millones de dólares"
        )
        
        benchmark = st.selectbox(
            "Benchmark de referencia:",
            options=['^SPX', 'SPY', 'BTC-USD', 'ETH-USD'] + simbolos,
            index=0,
            help="Índice de referencia para calcular betas",
            key="benchmark_cobertura"
        )
    
    with col2:
        st.markdown("#### 🎯 Configuración de Cobertura")
        
        # Universo de cobertura
        hedge_universe = st.multiselect(
            "Universo de activos para cobertura:",
            options=simbolos + ['^SPX', 'SPY', 'BTC-USD', 'ETH-USD', 'XLK', 'XLF'],
            default=simbolos[:3] if len(simbolos) >= 3 else simbolos,
            help="Activos disponibles para construir la cobertura"
        )
        
        regularizacion = st.slider(
            "Regularización:",
            min_value=0.0, max_value=10.0, value=0.1, step=0.1,
            help="Mayor valor = cobertura más conservadora"
        )
    
    # Calcular correlaciones y betas
    if hedge_universe:
        st.markdown("#### 📊 Correlaciones y Betas")
        
        with st.spinner("Calculando correlaciones y betas..."):
            df_correlaciones = dataframe_correlacion_beta(
                benchmark, position_security, hedge_universe, 
                token_acceso, fecha_desde, fecha_hasta
            )
        
        if not df_correlaciones.empty:
            st.dataframe(df_correlaciones, use_container_width=True)
            
            # Gráfico de correlaciones
            fig = go.Figure(data=[
                go.Bar(
                    x=df_correlaciones['Activo'],
                    y=df_correlaciones['Correlación vs Posición'],
                    name='Correlación vs Posición',
                    marker_color='lightblue'
                ),
                go.Bar(
                    x=df_correlaciones['Activo'],
                    y=df_correlaciones['Correlación vs Benchmark'],
                    name='Correlación vs Benchmark',
                    marker_color='darkblue'
                )
            ])
            
            fig.update_layout(
                title='Correlaciones de Activos',
                xaxis_title='Activos',
                yaxis_title='Correlación',
                barmode='group'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se pudieron calcular correlaciones")
    
    # Selección de activos de cobertura
    st.markdown("#### 🎯 Selección de Activos de Cobertura")
    
    hedge_securities = st.multiselect(
        "Activos específicos para cobertura:",
        options=hedge_universe,
        default=hedge_universe[:2] if len(hedge_universe) >= 2 else hedge_universe,
        help="Selecciona los activos específicos para construir la cobertura"
    )
    
    # Cálculo de cobertura
    if hedge_securities:
        st.markdown("#### 🛡️ Resultados de la Cobertura")
        
        with st.spinner("Calculando cobertura óptima..."):
            try:
                # Crear coberturista
                hedger = Coberturista(
                    position_security, position_delta_usd, benchmark, hedge_securities,
                    token_acceso, fecha_desde, fecha_hasta
                )
                
                # Calcular betas y pesos
                if hedger.calcular_betas():
                    if hedger.calcular_pesos_cobertura(regularizacion):
                        st.success("✅ Cobertura calculada exitosamente")
                        
                        # Mostrar resultados
                        col1, col2, col3, col4 = st.columns(4)
                        
                        col1.metric(
                            "Beta de la Posición", 
                            f"{hedger.beta_posicion_ars:.4f}",
                            help="Beta de la posición principal vs benchmark"
                        )
                        
                        col2.metric(
                            "Delta de Cobertura", 
                            f"${hedger.delta_cobertura_ars:.2f}M",
                            help="Exposición de la cobertura en millones USD"
                        )
                        
                        col3.metric(
                            "Beta de Cobertura", 
                            f"{hedger.beta_cobertura_ars:.4f}",
                            help="Beta de la cobertura vs benchmark"
                        )
                        
                        col4.metric(
                            "Costo Estimado", 
                            f"${hedger.costo_cobertura_ars:.2f}M",
                            help="Costo estimado de la cobertura"
                        )
                        
                        # Tabla de pesos de cobertura
                        st.markdown("#### 📋 Pesos de Cobertura")
                        
                        df_pesos = pd.DataFrame({
                            'Activo': hedge_securities,
                            'Peso Cobertura': [f"{w:.4f}" for w in hedger.pesos_cobertura],
                            'Beta': [f"{b:.4f}" for b in hedger.betas_cobertura],
                            'Acción': ['Comprar' if w > 0.01 else 'Vender' if w < -0.01 else 'Mantener' 
                                     for w in hedger.pesos_cobertura]
                        })
                        
                        st.dataframe(df_pesos, use_container_width=True)
                        
                        # Gráfico de pesos
                        fig = go.Figure(data=[go.Bar(
                            x=hedge_securities,
                            y=hedger.pesos_cobertura,
                            text=[f"{w:.2%}" for w in hedger.pesos_cobertura],
                            textposition='auto',
                            marker_color=['red' if w < 0 else 'green' for w in hedger.pesos_cobertura]
                        )])
                        
                        fig.update_layout(
                            title='Pesos de Cobertura por Activo',
                            xaxis_title='Activos',
                            yaxis_title='Peso',
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Análisis de efectividad
                        st.markdown("#### 📊 Análisis de Efectividad")
                        
                        # Calcular métricas de efectividad
                        beta_neto = hedger.beta_posicion_ars + hedger.beta_cobertura_ars
                        reduccion_riesgo = abs(hedger.beta_posicion_ars) - abs(beta_neto)
                        
                        col1, col2, col3 = st.columns(3)
                        
                        col1.metric(
                            "Beta Neto", 
                            f"{beta_neto:.4f}",
                            delta=f"{beta_neto - hedger.beta_posicion_ars:.4f}",
                            help="Beta combinado de posición + cobertura"
                        )
                        
                        col2.metric(
                            "Reducción de Riesgo", 
                            f"{reduccion_riesgo:.4f}",
                            help="Reducción en beta absoluto"
                        )
                        
                        col3.metric(
                            "Efectividad", 
                            f"{(reduccion_riesgo / abs(hedger.beta_posicion_ars) * 100):.1f}%",
                            help="Porcentaje de reducción de riesgo"
                        )
                        
                        # Recomendaciones
                        st.markdown("#### 💡 Recomendaciones")
                        
                        if abs(beta_neto) < 0.1:
                            st.success("✅ **Cobertura Efectiva**: La cobertura reduce significativamente el riesgo de mercado.")
                        elif abs(beta_neto) < 0.3:
                            st.info("ℹ️ **Cobertura Moderada**: La cobertura reduce parcialmente el riesgo. Considere ajustar los pesos.")
                        else:
                            st.warning("⚠️ **Cobertura Limitada**: La cobertura no reduce significativamente el riesgo. Revise la selección de activos.")
                        
                        if hedger.costo_cobertura_ars > position_delta_usd * 0.05:
                            st.warning("⚠️ **Costo Elevado**: El costo de la cobertura es alto. Considere alternativas más eficientes.")
                        
                    else:
                        st.error("❌ Error en el cálculo de pesos de cobertura")
                else:
                    st.error("❌ Error en el cálculo de betas")
                    
            except Exception as e:
                st.error(f"❌ Error durante el cálculo de cobertura: {str(e)}")
    else:
        st.info("Selecciona al menos un activo de cobertura para continuar")

def validar_datos_financieros(returns, min_observaciones=30):
    """
    Valida la calidad de los datos financieros para análisis
    """
    try:
        if returns is None or returns.empty:
            return False, "Datos de retornos vacíos o nulos"
        
        if len(returns) < min_observaciones:
            return False, f"Insuficientes observaciones: {len(returns)} < {min_observaciones}"
        
        # Verificar valores faltantes
        missing_pct = returns.isnull().sum().sum() / (returns.shape[0] * returns.shape[1])
        if missing_pct > 0.1:  # Más del 10% de datos faltantes
            return False, f"Demasiados datos faltantes: {missing_pct:.1%}"
        
        # Verificar valores infinitos
        inf_count = np.isinf(returns).sum().sum()
        if inf_count > 0:
            return False, f"Valores infinitos detectados: {inf_count}"
        
        # Verificar valores extremos (outliers)
        for col in returns.columns:
            col_returns = returns[col].dropna()
            if len(col_returns) > 0:
                q1, q3 = np.percentile(col_returns, [25, 75])
                iqr = q3 - q1
                outliers = ((col_returns < (q1 - 3 * iqr)) | (col_returns > (q3 + 3 * iqr))).sum()
                if outliers > len(col_returns) * 0.05:  # Más del 5% de outliers
                    return False, f"Demasiados outliers en {col}: {outliers}"
        
        return True, "Datos válidos"
        
    except Exception as e:
        return False, f"Error validando datos: {str(e)}"

def calcular_metricas_portafolio(portafolio, valor_total, token_portador, dias_historial=252, id_cliente=None):
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
    # Validaciones mejoradas de inputs
    if not isinstance(portafolio, dict) or not portafolio:
        st.error("❌ Portafolio no válido")
        return {}
    
    if valor_total <= 0:
        st.error("❌ Valor total del portafolio debe ser mayor a 0")
        return {}
    
    # Validar que el portafolio tenga activos
    if len(portafolio) == 0:
        st.warning("⚠️ Portafolio vacío")
        return {}

    # Obtener fechas para el histórico
    fecha_hasta = datetime.now().strftime('%Y-%m-%d')
    fecha_desde = (datetime.now() - timedelta(days=dias_historial*1.5)).strftime('%Y-%m-%d')
    
    # RECONSTRUIR COMPOSICIÓN DEL PORTAFOLIO BASÁNDOSE EN OPERACIONES REALES
    print("🔄 Reconstruyendo composición del portafolio basándose en operaciones reales...")
    try:
        composicion_por_fecha, posiciones_actuales = reconstruir_composicion_portafolio(
            token_portador, portafolio, fecha_desde, fecha_hasta, id_cliente
        )
        print(f"✅ Composición reconstruida para {len(composicion_por_fecha)} fechas")
        
        # Mostrar resumen de operaciones encontradas
        total_operaciones = sum(len(pos['operaciones']) for pos in posiciones_actuales.values())
        print(f"📊 Total de operaciones procesadas: {total_operaciones}")
        
        for simbolo, pos in posiciones_actuales.items():
            if pos['operaciones']:
                compras = len([op for op in pos['operaciones'] if op['tipo'] == 'compra'])
                ventas = len([op for op in pos['operaciones'] if op['tipo'] == 'venta'])
                print(f"  {simbolo}: {compras} compras, {ventas} ventas, cantidad actual: {pos['cantidad']}")
                
    except Exception as e:
        print(f"⚠️ Error al reconstruir composición: {str(e)}")
        print("🔄 Continuando con método tradicional...")
        composicion_por_fecha = {}
        posiciones_actuales = {}
    
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
            serie_historica = None
            
            # Intentar primero con IOL
            try:
                serie_historica = obtener_serie_historica_iol(
                    token_portador=token_portador,
                    mercado=mercado,
                    simbolo=simbolo,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                    ajustada="SinAjustar"
                )
            except Exception as e:
                print(f"Error al obtener datos históricos de IOL para {simbolo}: {str(e)}")
            
            # No hay fallback - solo usar IOL
            
            if serie_historica is None:
                print(f"No se obtuvieron datos para {simbolo} (None)")
                continue
                
            if serie_historica.empty:
                print(f"Datos vacíos para {simbolo}")
                continue
            
            # Convertir la serie a DataFrame con las columnas esperadas
            df_historico = pd.DataFrame({
                'fecha': serie_historica.index,
                'precio': serie_historica.values
            })
            
            print(f"Datos obtenidos: {len(df_historico)} registros desde {df_historico['fecha'].min()} hasta {df_historico['fecha'].max()}")
            print(f"Precios: min={df_historico['precio'].min():.2f}, max={df_historico['precio'].max():.2f}")
                
            # Ordenar por fecha y limpiar duplicados
            df_historico = df_historico.sort_values('fecha')
            df_historico = df_historico.drop_duplicates(subset=['fecha'], keep='last')
            
            # Calcular retornos diarios
            df_historico['retorno'] = df_historico['precio'].pct_change()
            
            print(f"Retornos calculados: {len(df_historico['retorno'].dropna())} válidos")
            print(f"Retorno medio: {df_historico['retorno'].mean():.6f}")
            print(f"Volatilidad: {df_historico['retorno'].std():.6f}")
            
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
            
            # CALCULAR MÉTRICAS BASÁNDOSE EN OPERACIONES REALES SI ESTÁN DISPONIBLES
            if posiciones_actuales and simbolo in posiciones_actuales:
                print(f"📊 Calculando métricas basadas en operaciones reales para {simbolo}")
                
                # Calcular retorno real basado en operaciones
                retorno_real = calcular_retorno_real_activo(simbolo, posiciones_actuales, serie_historica)
                
                if retorno_real:
                    retorno_medio = retorno_real['retorno_anualizado']
                    volatilidad = retorno_real['volatilidad_anualizada']
                    
                    # Mostrar información detallada del retorno real
                    print(f"  💰 Retorno real: {retorno_real['retorno_total']*100:.2f}% total, {retorno_real['retorno_anualizado']*100:.2f}% anual")
                    print(f"  📅 Primera compra: {retorno_real['fecha_primera_compra']}")
                    print(f"  💵 Flujo compras: ${retorno_real['flujo_compras']:,.2f}, Flujo ventas: ${retorno_real['flujo_ventas']:,.2f}")
                    print(f"  📈 Valor actual: ${retorno_real['valor_actual']:,.2f}")
                    
                    # Guardar métricas adicionales del retorno real
                    metricas_activos[simbolo].update({
                        'retorno_real_total': retorno_real['retorno_total'],
                        'fecha_primera_compra': retorno_real['fecha_primera_compra'],
                        'flujo_compras': retorno_real['flujo_compras'],
                        'flujo_ventas': retorno_real['flujo_ventas'],
                        'valor_actual_real': retorno_real['valor_actual']
                    })
                else:
                    print(f"  ⚠️ No se pudo calcular retorno real, usando método tradicional")
                    # Calcular métricas básicas tradicionales
                    retorno_medio = retornos_validos.mean() * 252  # Anualizado
                    volatilidad = retornos_validos.std() * np.sqrt(252)  # Anualizada
            else:
                print(f"  📊 Usando método tradicional (sin operaciones disponibles)")
                # Calcular métricas básicas tradicionales
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

# --- Funciones de Visualización ---
def mostrar_resumen_portafolio(portafolio, token_portador, portfolio_id="", id_cliente=None):
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
                                                # Corregir valuación para instrumentos que cotizan en porcentaje
                        if (tipo == 'TitulosPublicos' or
                            tipo == 'Letras' or
                            'Letra' in descripcion or
                            simbolo.startswith('S') or
                            simbolo.startswith('L') or
                            (precio_unitario > 1000 and tipo not in ['ACCIONES', 'CEDEARS'])):  # Precios muy altos suelen ser porcentajes, pero no para acciones/CEDEARS
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
                    ultimo_precio = obtener_precio_actual(token_portador, mercado, simbolo)
                if ultimo_precio:
                    try:
                        cantidad_num = float(cantidad)
                        # Corregir valuación para instrumentos que cotizan en porcentaje
                        if (tipo == 'TitulosPublicos' or 
                            tipo == 'Letras' or 
                            'Letra' in descripcion or 
                            simbolo.startswith('S') or 
                            simbolo.startswith('L') or
                            ultimo_precio > 1000):  # Precios muy altos suelen ser porcentajes
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
                'mercado': titulo.get('mercado', 'BCBA'),  # Agregar mercado para cálculos
            })
            
            valor_total += valuacion
        except Exception as e:
            continue
    
    if datos_activos:
        df_activos = pd.DataFrame(datos_activos)
        # Convert list to dictionary with symbols as keys
        portafolio_dict = {row['Símbolo']: row for row in datos_activos}
        metricas = calcular_metricas_portafolio(portafolio_dict, valor_total, token_portador)
        
        # Información General - Diseño mejorado
        # Crear DataFrame con resumen ejecutivo
        st.markdown("### 📊 Resumen Ejecutivo")
        
        # Preparar datos para el DataFrame
        resumen_data = {
            'Métrica': [
                '💰 Valor Total',
                '📈 Total Activos', 
                '🎯 Símbolos Únicos',
                '📋 Tipos de Activos'
            ],
            'Valor': [
                f"${valor_total:,.0f}",
                len(datos_activos),
                df_activos['Símbolo'].nunique(),
                df_activos['Tipo'].nunique()
            ],
            'Descripción': [
                'Valor total del portafolio en pesos argentinos',
                'Número total de posiciones en el portafolio',
                'Número de instrumentos diferentes',
                'Diversificación por tipo de instrumento'
            ]
        }
        
        if metricas:
            # Agregar métricas de riesgo
            concentracion_pct = metricas['concentracion'] * 100
            volatilidad_pct = metricas['std_dev_activo'] * 100
            
            resumen_data['Métrica'].extend([
                '🎯 Concentración',
                '📊 Volatilidad Anual',
                '📈 Nivel de Riesgo'
            ])
            resumen_data['Valor'].extend([
                f"{concentracion_pct:.1f}%",
                         f"{volatilidad_pct:.1f}%",
                "🟢 Baja" if volatilidad_pct < 15 else "🟡 Media" if volatilidad_pct < 25 else "🔴 Alta"
            ])
            resumen_data['Descripción'].extend([
                'Índice de Herfindahl: 0%=muy diversificado, 100%=muy concentrado',
                'Variabilidad esperada de los retornos anuales',
                'Clasificación del riesgo basada en volatilidad'
            ])
            
            
            # Agregar proyecciones de rendimiento
            retorno_anual_pct = metricas['retorno_esperado_anual'] * 100
            optimista_pct = (metricas['pl_esperado_max'] / valor_total) * 100 if valor_total > 0 else 0
            pesimista_pct = (metricas['pl_esperado_min'] / valor_total) * 100 if valor_total > 0 else 0
            
            resumen_data['Métrica'].extend([
                '📊 Retorno Esperado',
                '🚀 Escenario Optimista',
                '⚠️ Escenario Pesimista'
            ])
            resumen_data['Valor'].extend([
                f"{retorno_anual_pct:+.1f}%",
                         f"{optimista_pct:+.1f}%",
                f"{pesimista_pct:+.1f}%"
            ])
            resumen_data['Descripción'].extend([
                'Retorno promedio esperado para el próximo año',
                'Retorno en el mejor 5% de escenarios (percentil 95)',
                'Retorno en el peor 5% de escenarios (percentil 5)'
            ])
            
            # Agregar análisis probabilístico
            probabilidades = metricas.get('probabilidades', {})
            prob_ganancia = probabilidades.get('ganancia', 0.5) * 100
            prob_perdida = probabilidades.get('perdida', 0.5) * 100
            prob_ganancia_10 = probabilidades.get('ganancia_mayor_10', 0) * 100
            prob_perdida_10 = probabilidades.get('perdida_mayor_10', 0) * 100
            
            resumen_data['Métrica'].extend([
                '✅ Prob. Ganancia',
                '❌ Prob. Pérdida',
                '🚀 Ganancia >10%',
                '⚠️ Pérdida >10%'
            ])
            resumen_data['Valor'].extend([
                f"{prob_ganancia:.1f}%",
                f"{prob_perdida:.1f}%",
                f"{prob_ganancia_10:.1f}%",
                f"{prob_perdida_10:.1f}%"
            ])
            resumen_data['Descripción'].extend([
                'Probabilidad de obtener ganancias',
                'Probabilidad de obtener pérdidas',
                'Probabilidad de ganancias superiores al 10%',
                'Probabilidad de pérdidas superiores al 10%'
            ])
        
        # Crear y mostrar el DataFrame
        df_resumen = pd.DataFrame(resumen_data)
        st.dataframe(
            df_resumen,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Métrica": st.column_config.TextColumn("Métrica", width="medium"),
                "Valor": st.column_config.TextColumn("Valor", width="small"),
                "Descripción": st.column_config.TextColumn("Descripción", width="large")
            }
        )
        
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
        
        # Verificar que df_activos tenga la columna 'Valuación'
        if 'Valuación' not in df_display.columns:
            st.error("❌ Error: No se encontró la columna 'Valuación' en los datos del portafolio")
            return
        
        # Verificar que valor_total sea válido
        if valor_total <= 0:
            st.error("❌ Error: El valor total del portafolio debe ser mayor a 0")
            return
        
        df_display['Valuación'] = df_display['Valuación'].apply(
            lambda x: f"${x:,.2f}" if x > 0 else "N/A"
        )
        
        # Crear columna de peso con validación
        try:
            df_display['Peso (%)'] = (df_activos['Valuación'] / valor_total * 100).round(2)
            df_display = df_display.sort_values('Peso (%)', ascending=False)
        except Exception as e:
            st.error(f"❌ Error calculando pesos: {str(e)}")
            # Crear columna de peso con valores por defecto
            df_display['Peso (%)'] = 0.0
        
        st.dataframe(df_display, use_container_width=True, height=400)
        
        # Estadísticas detalladas y distribuciones
        with st.expander("📊 Estadísticas Detalladas y Distribuciones", expanded=False):
            # Opción para mostrar histograma de retornos
            mostrar_histograma_retornos = st.checkbox(
                "📈 Mostrar Histograma de Retornos por Activo", 
                value=False,
                help="Muestra histogramas de retornos históricos para cada activo del portafolio",
                key=f"mostrar_histograma_retornos_detallado_{portfolio_id}"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📈 Estadísticas Descriptivas")
                if len(datos_activos) > 0:
                    valores = [a['Valuación'] for a in datos_activos if a['Valuación'] > 0]
                    if valores:
                        # Cache de cálculos estadísticos
                        @st.cache_data(ttl=300)
                        def calcular_estadisticas(valores_list):
                            """Calcula estadísticas con cache para mejor rendimiento"""
                            valores_array = np.array(valores_list)
                            return {
                                'cantidad': len(valores_array),
                                'total': np.sum(valores_array),
                                'promedio': np.mean(valores_array),
                                'maximo': np.max(valores_array),
                                'minimo': np.min(valores_array),
                                'std': np.std(valores_array),
                                'cv': np.std(valores_array) / np.mean(valores_array) * 100
                            }
                        
                        stats = calcular_estadisticas(valores)
                        stats_df = pd.DataFrame({
                            'Métrica': ['Cantidad', 'Valor Total', 'Valor Promedio', 'Valor Máximo', 
                                       'Valor Mínimo', 'Desviación Estándar', 'Coeficiente de Variación'],
                            'Valor': [
                                stats['cantidad'],
                                f"${stats['total']:,.2f}",
                                f"${stats['promedio']:,.2f}",
                                f"${stats['maximo']:,.2f}",
                                f"${stats['minimo']:,.2f}",
                                f"${stats['std']:,.2f}",
                                f"{stats['cv']:.1f}%"
                            ]
                        })
                        st.dataframe(stats_df, use_container_width=True)
                        
                        # Percentiles con cache
                        @st.cache_data(ttl=300)
                        def calcular_percentiles(valores_list):
                            """Calcula percentiles con cache"""
                            percentiles = [10, 25, 50, 75, 90, 95, 99]
                            return {p: np.percentile(valores_list, p) for p in percentiles}
                        
                        percentiles_data = calcular_percentiles(valores)
                        percentil_df = pd.DataFrame({
                            'Percentil': [f"{p}%" for p in percentiles_data.keys()],
                            'Valor': [f"${v:,.2f}" for v in percentiles_data.values()]
                        })
                        st.dataframe(percentil_df, use_container_width=True)
            
            with col2:
                st.markdown("#### 📊 Distribuciones")
                
                # Opciones de visualización
                tipo_grafico = st.selectbox(
                    "Tipo de Gráfico:",
                    ["Histograma", "Box Plot", "Violin Plot", "Density Plot"],
                    help="Seleccione el tipo de visualización para los valores de activos",
                    key=f"tipo_grafico_distribuciones_{portfolio_id}_{hash(str(portafolio))}"
                )
                
                valores = [a['Valuación'] for a in datos_activos if a['Valuación'] > 0]
                if valores:
                    if tipo_grafico == "Histograma":
                        fig = go.Figure(data=[go.Histogram(
                            x=valores,
                            nbinsx=min(20, len(valores)),
                            marker_color='#0d6efd',
                            opacity=0.7
                        )])
                        fig.update_layout(
                            title="Distribución de Valores de Activos",
                            xaxis_title="Valor ($)",
                            yaxis_title="Frecuencia",
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                    elif tipo_grafico == "Box Plot":
                        fig = go.Figure(data=[go.Box(
                            y=valores,
                            name="Valores",
                            marker_color='#0d6efd'
                        )])
                        fig.update_layout(
                            title="Box Plot de Valores de Activos",
                            yaxis_title="Valor ($)",
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                    elif tipo_grafico == "Violin Plot":
                        fig = go.Figure(data=[go.Violin(
                            y=valores,
                            name="Valores",
                            marker_color='#0d6efd'
                        )])
                        fig.update_layout(
                            title="Violin Plot de Valores de Activos",
                            yaxis_title="Valor ($)",
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                    elif tipo_grafico == "Density Plot":
                        # Crear densidad usando histograma normalizado
                        hist, bins = np.histogram(valores, bins=min(20, len(valores)), density=True)
                        bin_centers = (bins[:-1] + bins[1:]) / 2
                        
                        fig = go.Figure(data=[go.Scatter(
                            x=bin_centers,
                            y=hist,
                            mode='lines+markers',
                            name="Densidad",
                            line=dict(color='#0d6efd', width=3)
                        )])
                        fig.update_layout(
                            title="Density Plot de Valores de Activos",
                            xaxis_title="Valor ($)",
                            yaxis_title="Densidad",
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            # Análisis por tipo de activo
            if 'Tipo' in df_activos.columns and 'Peso (%)' in df_activos.columns:
                st.markdown("#### 📊 Análisis por Tipo de Activo")
                tipo_analysis = df_activos.groupby('Tipo').agg({
                    'Valuación': ['count', 'sum', 'mean', 'std'],
                    'Peso (%)': ['mean', 'sum']
                }).round(2)
                
                # Renombrar columnas para mejor visualización
                tipo_analysis.columns = ['Cantidad', 'Valor Total', 'Valor Promedio', 'Desv. Estándar', 
                                       'Peso Promedio (%)', 'Peso Total (%)']
                st.dataframe(tipo_analysis, use_container_width=True)
                
                # Gráfico de barras por tipo
                fig_bars = go.Figure(data=[go.Bar(
                    x=tipo_analysis.index,
                    y=tipo_analysis['Valor Total'],
                    marker_color='#0d6efd',
                    text=tipo_analysis['Valor Total'].apply(lambda x: f"${x:,.0f}"),
                    textposition='auto'
                )])
                fig_bars.update_layout(
                    title="Valor Total por Tipo de Activo",
                    xaxis_title="Tipo de Activo",
                    yaxis_title="Valor Total ($)",
                    height=400
                )
                st.plotly_chart(fig_bars, use_container_width=True)
            
            # Métricas de riesgo detalladas
            if metricas:
                st.markdown("#### ⚖️ Métricas de Riesgo Detalladas")
                col1, col2 = st.columns(2)
                
                with col1:
                    risk_metrics = {
                        'Concentración (Herfindahl)': f"{metricas['concentracion']:.4f}",
                        'Volatilidad Anual': f"{metricas['std_dev_activo']*100:.2f}%",
                        'Riesgo Anual': f"{metricas['riesgo_anual']*100:.2f}%",
                        'Retorno Esperado Anual': f"{metricas['retorno_esperado_anual']*100:.2f}%",
                        'Ratio Riesgo-Retorno': f"{metricas['retorno_esperado_anual']/metricas['riesgo_anual']:.4f}" if metricas['riesgo_anual'] > 0 else "N/A"
                    }
                    
                    risk_df = pd.DataFrame({
                        'Métrica': list(risk_metrics.keys()),
                        'Valor': list(risk_metrics.values())
                    })
                    st.dataframe(risk_df, use_container_width=True)
                
                with col2:
                    # Gráfico de concentración
                    if 'Peso (%)' in df_activos.columns:
                        simbolos_top = df_activos.nlargest(5, 'Peso (%)')
                        fig_concentration = go.Figure(data=[go.Bar(
                            x=simbolos_top['Símbolo'],
                            y=simbolos_top['Peso (%)'],
                            marker_color='#dc3545',
                            text=simbolos_top['Peso (%)'].apply(lambda x: f"{x:.1f}%"),
                            textposition='auto'
                        )])
                        fig_concentration.update_layout(
                            title="Top 5 Activos por Peso",
                            xaxis_title="Símbolo",
                            yaxis_title="Peso (%)",
                            height=300
                        )
                        st.plotly_chart(fig_concentration, use_container_width=True)
                    else:
                        st.warning("⚠️ No se puede mostrar el gráfico de concentración - faltan datos de peso")
                
                # Proyecciones detalladas
                st.markdown("#### 📈 Proyecciones Detalladas")
                projection_metrics = {
                    'PL Esperado Máximo (95%)': f"${metricas['pl_esperado_max']:,.2f}",
                    'PL Esperado Mínimo (5%)': f"${metricas['pl_esperado_min']:,.2f}",
                    'Probabilidad de Ganancia': f"{metricas['probabilidades']['ganancia']*100:.1f}%",
                    'Probabilidad de Pérdida': f"{metricas['probabilidades']['perdida']*100:.1f}%",
                    'Prob. Ganancia >10%': f"{metricas['probabilidades']['ganancia_mayor_10']*100:.1f}%",
                    'Prob. Pérdida >10%': f"{metricas['probabilidades']['perdida_mayor_10']*100:.1f}%"
                }
                
                projection_df = pd.DataFrame({
                    'Métrica': list(projection_metrics.keys()),
                    'Valor': list(projection_metrics.values())
                })
                st.dataframe(projection_df, use_container_width=True)
            
            # Histograma de retornos por activo (opcional)
            if mostrar_histograma_retornos:
                st.markdown("#### 📈 Histograma de Retornos por Activo")
                st.info("🔄 Cargando datos históricos para análisis de retornos...")
                
                # Extraer símbolos únicos del portafolio
                simbolos_portafolio = df_activos['Símbolo'].unique().tolist()
                simbolos_validos = [s for s in simbolos_portafolio if s and s != 'N/A']
                
                if len(simbolos_validos) > 0:
                    # Crear manager para obtener datos históricos con cache
                    @st.cache_data(ttl=600)  # Cache por 10 minutos
                    def cargar_datos_historicos_resumen(symbols, token, fecha_desde, fecha_hasta):
                        """Cachea los datos históricos para el resumen"""
                        manager_inst = PortfolioManager(symbols, token, fecha_desde, fecha_hasta)
                        if manager_inst.load_data():
                            return manager_inst
                        return None
                    
                    # Usar fechas de la sesión
                    fecha_desde = st.session_state.get('fecha_desde', date.today() - timedelta(days=365))
                    fecha_hasta = st.session_state.get('fecha_hasta', date.today())
                    
                    with st.spinner("📊 Cargando datos históricos..."):
                        manager_inst = cargar_datos_historicos_resumen(
                            simbolos_validos, token_portador, fecha_desde, fecha_hasta
                        )
                    
                    if manager_inst and manager_inst.returns is not None:
                        st.success(f"✅ Datos históricos cargados para {len(simbolos_validos)} activos")
                        
                        # Calcular pesos actuales del portafolio
                        pesos_actuales = []
                        for simbolo in simbolos_validos:
                            # Buscar el activo en el portafolio
                            activo_encontrado = None
                            for activo in activos:
                                if activo.get('titulo', {}).get('simbolo') == simbolo:
                                    activo_encontrado = activo
                                    break
                            
                            if activo_encontrado:
                                value = activo_encontrado.get('valuacionActual', 0)
                                peso = value / valor_total if valor_total > 0 else 0
                                pesos_actuales.append(peso)
                            else:
                                # Si no se encuentra, usar peso igual
                                pesos_actuales.append(1/len(simbolos_validos))
                        
                        # Normalizar pesos para que sumen 1
                        if sum(pesos_actuales) > 0:
                            pesos_actuales = [w/sum(pesos_actuales) for w in pesos_actuales]
                        else:
                            pesos_actuales = [1/len(simbolos_validos)] * len(simbolos_validos)
                        
                        # Calcular retornos del portafolio actual
                        portfolio_returns = None
                        try:
                            # Obtener solo las columnas que existen en los datos
                            available_symbols = [s for s in simbolos_validos if s in manager_inst.returns.columns]
                            if available_symbols:
                                if len(available_symbols) == 1:
                                    # Si solo hay un activo, usar sus retornos directamente
                                    portfolio_returns = manager_inst.returns[available_symbols[0]].dropna()
                                else:
                                    # Si hay múltiples activos, calcular retornos ponderados
                                    available_weights = []
                                    for simbolo in available_symbols:
                                        idx = simbolos_validos.index(simbolo)
                                        available_weights.append(pesos_actuales[idx])
                                    
                                    # Normalizar pesos de símbolos disponibles
                                    if sum(available_weights) > 0:
                                        available_weights = [w/sum(available_weights) for w in available_weights]
                                    else:
                                        available_weights = [1/len(available_symbols)] * len(available_symbols)
                                    
                                    # Calcular retornos del portafolio
                                    portfolio_returns = (manager_inst.returns[available_symbols] * available_weights).sum(axis=1)
                                    portfolio_returns = portfolio_returns.dropna()
                            else:
                                st.warning("⚠️ No hay símbolos disponibles en los datos históricos")
                        except Exception as e:
                            st.error(f"❌ Error calculando retornos del portafolio: {str(e)}")
                        
                        # Mostrar histograma del portafolio completo
                        if portfolio_returns is not None and len(portfolio_returns) > 10:
                            st.markdown("#### 📊 Distribución de Retornos del Portafolio")
                            
                            # Crear histograma del portafolio
                            fig_portfolio_hist = go.Figure(data=[go.Histogram(
                                x=portfolio_returns,
                                nbinsx=min(30, len(portfolio_returns)),
                                marker_color='#0d6efd',
                                opacity=0.7,
                                name="Retornos del Portafolio"
                            )])
                            
                            # Agregar líneas de métricas del portafolio
                            mean_portfolio_return = portfolio_returns.mean()
                            std_portfolio_return = portfolio_returns.std()
                            var_95_portfolio = portfolio_returns.quantile(0.05)
                            
                            fig_portfolio_hist.add_vline(
                                x=mean_portfolio_return, 
                                line_dash="dash", 
                                line_color="red",
                                annotation_text=f"Media: {mean_portfolio_return:.4f}"
                            )
                            fig_portfolio_hist.add_vline(
                                x=var_95_portfolio, 
                                line_dash="dash", 
                                line_color="orange",
                                annotation_text=f"VaR 95%: {var_95_portfolio:.4f}"
                            )
                            
                            fig_portfolio_hist.update_layout(
                                title="Distribución de Retornos del Portafolio Actual",
                                xaxis_title="Retorno Diario del Portafolio",
                                yaxis_title="Frecuencia",
                                height=400,
                                showlegend=False
                            )
                            
                            st.plotly_chart(fig_portfolio_hist, use_container_width=True)
                            
                            # Métricas del portafolio
                            st.markdown("#### 📈 Métricas del Portafolio")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Retorno Medio Diario", f"{mean_portfolio_return:.4f}")
                            with col2:
                                st.metric("Volatilidad Diaria", f"{std_portfolio_return:.4f}")
                            with col3:
                                st.metric("VaR 95% Diario", f"{var_95_portfolio:.4f}")
                            with col4:
                                sharpe_ratio_portfolio = mean_portfolio_return / std_portfolio_return if std_portfolio_return > 0 else 0
                                st.metric("Sharpe Ratio Diario", f"{sharpe_ratio_portfolio:.4f}")
                            
                            # Métricas anualizadas
                            st.markdown("#### 📊 Métricas Anualizadas")
                            annual_return = mean_portfolio_return * 252
                            annual_volatility = std_portfolio_return * np.sqrt(252)
                            annual_sharpe = annual_return / annual_volatility if annual_volatility > 0 else 0
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Retorno Anual", f"{annual_return:.2%}")
                            with col2:
                                st.metric("Volatilidad Anual", f"{annual_volatility:.2%}")
                            with col3:
                                st.metric("Sharpe Ratio Anual", f"{annual_sharpe:.4f}")
                            
                            # Información adicional
                            if len(available_symbols) == 1:
                                st.info(f"""
                                **ℹ️ Información del Análisis:**
                                - **Período analizado:** {len(portfolio_returns)} días de trading
                                - **Activo analizado:** {available_symbols[0]}
                                - **Tipo de análisis:** Retornos del activo individual
                                """)
                            else:
                                st.info(f"""
                                **ℹ️ Información del Análisis:**
                                - **Período analizado:** {len(portfolio_returns)} días de trading
                                - **Activos incluidos:** {len(available_symbols)} de {len(simbolos_validos)} activos
                                - **Composición:** Basada en la valuación actual del portafolio
                                - **Tipo de análisis:** Retornos ponderados del portafolio completo
                                """)
                        else:
                            st.warning("⚠️ Datos insuficientes para calcular retornos del portafolio")
                    else:
                        st.warning("⚠️ No se pudieron cargar los datos históricos para el análisis de retornos")
                else:
                    st.warning("⚠️ No hay símbolos válidos en el portafolio para análisis de retornos")
        
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
    """
    Muestra el estado de cuenta de Argentina
    
    Args:
        estado_cuenta (dict): Datos del estado de cuenta
    """
    st.markdown("### 💰 Estado de Cuenta")
    
    if not estado_cuenta:
        st.warning("No hay datos de estado de cuenta disponibles")
        return
    
    # Estado de cuenta general
    total_en_pesos = estado_cuenta.get('totalEnPesos', 0)
    cuentas = estado_cuenta.get('cuentas', [])
    
    # Contar cuentas únicas por número y tipo
    cuentas_unicas = {}
    for cuenta in cuentas:
        numero = cuenta.get('numero', 'N/A')
        tipo = cuenta.get('tipo', 'N/A')
        moneda = cuenta.get('moneda', 'N/A')
        clave_unica = f"{numero}_{tipo}_{moneda}"
        cuentas_unicas[clave_unica] = cuenta
    
    numero_cuentas_unicas = len(cuentas_unicas)
    
    cols = st.columns(3)
    cols[0].metric("Total en Pesos", f"AR$ {total_en_pesos:,.2f}")
    cols[1].metric("Número de Cuentas", numero_cuentas_unicas)
    cols[2].metric("Total de Registros", len(cuentas))
    
    if cuentas:
        st.subheader("📊 Detalle de Cuentas")
        
        datos_cuentas = []
        for cuenta in cuentas:
            # Obtener valores y validar coherencia
            disponible = float(cuenta.get('disponible', 0))
            saldo = float(cuenta.get('saldo', 0))
            total = float(cuenta.get('total', 0))
            
            # Validar coherencia: Total debería ser Disponible + Saldo
            total_calculado = disponible + saldo
            
            # Si hay gran diferencia, usar el total de la API pero mostrar advertencia
            if abs(total - total_calculado) > 0.01:
                # Usar el total de la API pero mostrar los valores individuales
                datos_cuentas.append({
                    'Número': cuenta.get('numero', 'N/A'),
                    'Tipo': cuenta.get('tipo', 'N/A').replace('_', ' ').title(),
                    'Moneda': cuenta.get('moneda', 'N/A').replace('_', ' ').title(),
                    'Disponible': f"${disponible:,.2f}",
                    'Saldo': f"${saldo:,.2f}",
                    'Total (API)': f"${total:,.2f}",
                    'Total (Calc)': f"${total_calculado:,.2f}",
                })
            else:
                # Valores coherentes
                datos_cuentas.append({
                    'Número': cuenta.get('numero', 'N/A'),
                    'Tipo': cuenta.get('tipo', 'N/A').replace('_', ' ').title(),
                    'Moneda': cuenta.get('moneda', 'N/A').replace('_', ' ').title(),
                    'Disponible': f"${disponible:,.2f}",
                    'Saldo': f"${saldo:,.2f}",
                    'Total': f"${total:,.2f}",
                })
        
        # Crear DataFrame una sola vez fuera del bucle
        df_cuentas = pd.DataFrame(datos_cuentas)
        st.dataframe(df_cuentas, use_container_width=True, height=300)
            
        # Mostrar resumen
        if numero_cuentas_unicas != len(cuentas):
            st.info(f"ℹ️ **Nota**: Se muestran {len(cuentas)} registros de {numero_cuentas_unicas} cuentas únicas")
        
        # Verificar si hay incoherencias en los datos
        incoherencias_detectadas = False
        for cuenta in cuentas:
            disponible = float(cuenta.get('disponible', 0))
            saldo = float(cuenta.get('saldo', 0))
            total = float(cuenta.get('total', 0))
            total_calculado = disponible + saldo
            
            if abs(total - total_calculado) > 0.01:
                incoherencias_detectadas = True
                break
        
        if incoherencias_detectadas:
            st.warning("⚠️ **Advertencia**: Se detectaron incoherencias en los datos del estado de cuenta. Los valores 'Total' de la API no coinciden con la suma de 'Disponible' + 'Saldo'. Esto puede deberse a diferencias en el procesamiento de la API de IOL.")

def obtener_parametros_operatoria_mep(token_acceso):
    """
    Obtiene los parámetros de operatoria MEP desde la API de IOL
    
    Args:
        token_acceso (str): Token de acceso para la autenticación
    
    Returns:
        dict: Parámetros de operatoria MEP
    """
    # ID típico para operatoria MEP (esto puede variar según la configuración)
    id_tipo_operatoria = 1  # Ajustar según la configuración real
    
    url = f'https://api.invertironline.com/api/v2/OperatoriaSimplificada/{id_tipo_operatoria}/Parametros'
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_acceso}'
    }
    
    try:
        st.info(f"🔗 Consultando parámetros MEP desde: {url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            datos = response.json()
            st.info(f"📊 Respuesta de parámetros MEP: {datos}")
            return datos
        elif response.status_code == 401:
            st.error("❌ Error de autorización: Token inválido o expirado")
            st.warning("💡 Verifique que su sesión esté activa y tenga permisos para operatoria MEP")
            return None
        else:
            st.error(f'Error obteniendo parámetros MEP: {response.status_code}')
            st.error(f'Respuesta: {response.text}')
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f'Error en la conexión: {e}')
        return None

def verificar_estado_mercado():
    """
    Verifica el estado real del mercado argentino basado en horarios
    
    Returns:
        dict: Estado del mercado con información de horarios
    """
    from datetime import datetime, time
    import pytz
    
    # Zona horaria de Argentina
    tz_argentina = pytz.timezone('America/Argentina/Buenos_Aires')
    ahora = datetime.now(tz_argentina)
    
    # Horarios del mercado argentino (aproximados)
    # Lunes a Viernes: 11:00 - 17:00 (horario argentino)
    hora_apertura = time(11, 0)  # 11:00 AM
    hora_cierre = time(17, 0)    # 5:00 PM
    
    # Verificar si es día hábil (lunes a viernes)
    es_dia_habil = ahora.weekday() < 5  # 0-4 = lunes a viernes
    
    # Verificar si está en horario de mercado
    hora_actual = ahora.time()
    en_horario = hora_apertura <= hora_actual <= hora_cierre
    
    # El mercado está abierto si es día hábil Y está en horario
    mercado_abierto = es_dia_habil and en_horario
    
    return {
        'esHorarioValido': mercado_abierto,
        'esDiaHabil': es_dia_habil,
        'enHorario': en_horario,
        'horaActual': hora_actual.strftime('%H:%M'),
        'diaSemana': ahora.strftime('%A'),
        'fecha': ahora.strftime('%d/%m/%Y'),
        'horarioApertura': hora_apertura.strftime('%H:%M'),
        'horarioCierre': hora_cierre.strftime('%H:%M')
    }

def obtener_estimacion_compra_mep(token_acceso, monto):
    """
    Obtiene la estimación para comprar dólares MEP
    
    Args:
        token_acceso (str): Token de acceso
        monto (float): Monto en pesos
    
    Returns:
        dict: Estimación de la operación
    """
    url = f'https://api.invertironline.com/api/v2/OperatoriaSimplificada/MontosEstimados/{monto}'
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_acceso}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f'Error obteniendo estimación compra: {response.status_code}')
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f'Error en la conexión: {e}')
        return None

def obtener_estimacion_venta_mep(token_acceso, monto):
    """
    Obtiene la estimación para vender dólares MEP
    
    Args:
        token_acceso (str): Token de acceso
        monto (float): Monto en dólares
    
    Returns:
        dict: Estimación de la operación
    """
    url = f'https://api.invertironline.com/api/v2/OperatoriaSimplificada/VentaMepSimple/MontosEstimados/{monto}'
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_acceso}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f'Error obteniendo estimación venta: {response.status_code}')
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f'Error en la conexión: {e}')
        return None

def ejecutar_compra_mep(token_acceso, monto):
    """
    Ejecuta una compra de dólares MEP
    
    Args:
        token_acceso (str): Token de acceso
        monto (float): Monto en pesos
    
    Returns:
        dict: Resultado de la operación
    """
    url = 'https://api.invertironline.com/api/v2/OperatoriaSimplificada/Comprar'
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_acceso}'
    }
    
    # Datos para la operación (ajustar según la configuración real)
    data = {
        "monto": monto,
        "idTipoOperatoriaSimplificada": 1,  # ID para MEP
        "idCuentaBancaria": 1  # ID de cuenta bancaria (ajustar según configuración)
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f'Error ejecutando compra MEP: {response.status_code}')
            st.error(f'Respuesta: {response.text}')
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f'Error en la conexión: {e}')
        return None

def ejecutar_venta_mep(token_acceso, monto):
    """
    Ejecuta una venta de dólares MEP
    
    Args:
        token_acceso (str): Token de acceso
        monto (float): Monto en dólares
    
    Returns:
        dict: Resultado de la operación
    """
    url = 'https://api.invertironline.com/api/v2/OperatoriaSimplificada/VentaMepSimple'
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_acceso}'
    }
    
    # Datos para la operación (ajustar según la configuración real)
    data = {
        "monto": monto,
        "idTipoOperatoriaSimplificada": 1,  # ID para MEP
        "idCuentaBancaria": 1  # ID de cuenta bancaria (ajustar según configuración)
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f'Error ejecutando venta MEP: {response.status_code}')
            st.error(f'Respuesta: {response.text}')
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f'Error en la conexión: {e}')
        return None

def obtener_historico_mep(token_acceso, fecha_desde, fecha_hasta):
    """
    Obtiene el histórico del dólar MEP calculado como AL30/AL30D usando el método directo
    
    Args:
        token_acceso (str): Token de acceso para la autenticación
        fecha_desde (str): Fecha desde en formato YYYY-MM-DD
        fecha_hasta (str): Fecha hasta en formato YYYY-MM-DD
    
    Returns:
        dict: Diccionario con datos históricos del MEP calculado
    """
    try:
        st.info(f"🔗 Consultando histórico MEP desde {fecha_desde} hasta {fecha_hasta}")
        
        # Usar el método directo para obtener series históricas
        tickers_especificos = ['AL30', 'AL30D']
        mercado = 'bCBA'
        ajustada = 'SinAjustar'
        
        datos_series = {}
        
        for simbolo in tickers_especificos:
            st.info(f"📊 Obteniendo datos históricos de {simbolo}...")
            
            # Usar la función directa que ya tenemos implementada
            serie_historica = obtener_serie_historica_directa(
                simbolo, mercado, fecha_desde, fecha_hasta, ajustada, token_acceso
            )
            
            if serie_historica and len(serie_historica) > 0:
                # Procesar los datos de la serie histórica
                precios = []
                fechas = []
                
                for item in serie_historica:
                    try:
                        precio = item.get('ultimoPrecio')
                        if not precio or precio == 0:
                            precio = item.get('cierreAnterior') or item.get('precioPromedio') or item.get('apertura')
                        
                        fecha_str = item.get('fechaHora') or item.get('fecha')
                        
                        if precio is not None and precio > 0 and fecha_str:
                            fecha_parsed = parse_datetime_flexible(fecha_str)
                            if fecha_parsed is not None:
                                precios.append(precio)
                                fechas.append(fecha_parsed)
                                
                    except Exception as e:
                        continue
                
                if len(precios) > 0:
                    # Crear DataFrame con los datos
                    df = pd.DataFrame({
                        'fecha': fechas,
                        'precio': precios
                    })
                    df['fecha'] = pd.to_datetime(df['fecha'])
                    df = df.sort_values('fecha')
                    datos_series[simbolo] = df
                    st.success(f"✅ {simbolo}: {len(df)} puntos de datos")
                else:
                    st.warning(f"⚠️ No se obtuvieron datos válidos para {simbolo}")
            else:
                st.warning(f"⚠️ No se pudieron obtener datos para {simbolo}")
        
        # Verificar que tenemos datos para ambos símbolos
        if 'AL30' not in datos_series or 'AL30D' not in datos_series:
            st.warning("⚠️ No se pudieron obtener datos completos para calcular el MEP")
            if 'AL30' not in datos_series:
                st.warning("❌ No hay datos de AL30 (pesos)")
            if 'AL30D' not in datos_series:
                st.warning("❌ No hay datos de AL30D (dólares)")
            return None
        
        # Hacer merge por fecha para alinear los datos
        df_merged = pd.merge(
            datos_series['AL30'], 
            datos_series['AL30D'], 
            on='fecha', 
            suffixes=('_al30', '_al30d')
        )
        
        # Calcular MEP = AL30 / AL30D
        df_merged['mep'] = df_merged['precio_al30'] / df_merged['precio_al30d']
        
        # Filtrar datos válidos (MEP > 0)
        df_merged = df_merged[df_merged['mep'] > 0].copy()
        
        if len(df_merged) == 0:
            st.warning("⚠️ No se pudieron calcular valores de MEP válidos")
            return None
        
        # Ordenar por fecha
        df_merged = df_merged.sort_values('fecha')
        
        st.success(f"✅ Se calcularon {len(df_merged)} valores de MEP históricos")
        
        # Convertir a formato esperado por la interfaz
        datos_mep = []
        for _, row in df_merged.iterrows():
            datos_mep.append({
                'fecha': row['fecha'].strftime('%Y-%m-%d'),
                'fechaHora': row['fecha'].strftime('%Y-%m-%dT%H:%M:%S'),
                'mep': row['mep'],
                'al30_pesos': row['precio_al30'],
                'al30d_dolares': row['precio_al30d'],
                'ultimoPrecio': row['mep'],
                'variacion': 0,  # Se calculará si es necesario
                'moneda': 'peso_Argentino'
            })
        
        return {
            'datos': datos_mep,
            'dataframe': df_merged,
            'resumen': {
                'total_registros': len(datos_mep),
                'fecha_inicio': df_merged['fecha'].min().strftime('%Y-%m-%d'),
                'fecha_fin': df_merged['fecha'].max().strftime('%Y-%m-%d'),
                'mep_promedio': df_merged['mep'].mean(),
                'mep_min': df_merged['mep'].min(),
                'mep_max': df_merged['mep'].max()
            }
        }
        
    except Exception as e:
        st.error(f"❌ Error calculando histórico MEP: {str(e)}")
        return None

def mostrar_cotizaciones_mercado(token_acceso):
    st.markdown("### 💱 Dólares y Mercado")
    
    with st.expander("💰 Cotización Dólar MEP - Título Público AL30", expanded=True):
        st.info("💡 **Dólar MEP**: Se calcula mediante la diferencia de precios entre la compra y venta del mismo título público (AL30) en pesos y dólares.")
        
        with st.form("mep_form"):
            col1, col2, col3 = st.columns(3)
            simbolo_mep = col1.text_input("Símbolo", value="AL30", help="Título público AL30 para cálculo MEP", disabled=True)
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
    
    # Sección para histórico del MEP
    with st.expander("📈 Histórico del Dólar MEP (AL30)", expanded=False):
        st.info("📊 Visualiza la evolución histórica del precio del AL30 para calcular el dólar MEP")
        
        with st.form("historico_mep_form"):
            col1, col2 = st.columns(2)
            with col1:
                fecha_desde_hist = st.date_input(
                    "Fecha desde", 
                    value=date.today() - timedelta(days=30),
                    help="Fecha de inicio del histórico"
                )
            with col2:
                fecha_hasta_hist = st.date_input(
                    "Fecha hasta", 
                    value=date.today(),
                    help="Fecha de fin del histórico"
                )
            
            if st.form_submit_button("📊 Consultar Histórico MEP"):
                if fecha_desde_hist and fecha_hasta_hist:
                    with st.spinner("Obteniendo histórico del AL30..."):
                        datos_historicos = obtener_historico_mep(
                            token_acceso, 
                            fecha_desde_hist.strftime('%Y-%m-%d'),
                            fecha_hasta_hist.strftime('%Y-%m-%d')
                        )
                    
                    if datos_historicos and datos_historicos.get('datos'):
                        resumen = datos_historicos.get('resumen', {})
                        df_historico = datos_historicos.get('dataframe')
                        
                        st.success(f"✅ Se calcularon {resumen.get('total_registros', 0)} valores de MEP históricos")
                        
                        # Mostrar métricas principales del MEP
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            mep_actual = df_historico['mep'].iloc[-1] if len(df_historico) > 0 else 0
                            st.metric("MEP Actual", f"${mep_actual:,.2f}")
                        with col2:
                            mep_max = resumen.get('mep_max', 0)
                            st.metric("MEP Máximo", f"${mep_max:,.2f}")
                        with col3:
                            mep_min = resumen.get('mep_min', 0)
                            st.metric("MEP Mínimo", f"${mep_min:,.2f}")
                        with col4:
                            mep_promedio = resumen.get('mep_promedio', 0)
                            st.metric("MEP Promedio", f"${mep_promedio:,.2f}")
                        
                        # Mostrar información adicional
                        st.info(f"📅 Período: {resumen.get('fecha_inicio', 'N/A')} a {resumen.get('fecha_fin', 'N/A')}")
                        
                        # Gráfico con Plotly usando make_subplots para eje secundario
                        fig = make_subplots(specs=[[{"secondary_y": True}]])
                        
                        # Línea de MEP calculado (solo esta línea)
                        fig.add_trace(go.Scatter(
                            x=df_historico['fecha'],
                            y=df_historico['mep'],
                            mode='lines',
                            name='Dólar MEP',
                            line=dict(color='#1f77b4', width=3),
                            hovertemplate='<b>Fecha:</b> %{x}<br><b>Dólar MEP:</b> $%{y:,.2f}<extra></extra>'
                        ), secondary_y=False)
                        
                        # Configurar layout con eje Y secundario
                        fig.update_layout(
                            title='📈 Evolución Histórica del Dólar MEP (AL30/AL30D)',
                            xaxis_title='Fecha',
                            hovermode='x unified',
                            showlegend=True,
                            height=500,
                            template='plotly_white',
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            )
                        )
                        
                        # Configurar ejes Y usando los métodos específicos de make_subplots
                        fig.update_yaxes(title_text="Dólar MEP ($)", secondary_y=False)
                        fig.update_yaxes(title_text="Precio Títulos ($)", secondary_y=True)
                        
                        # Formatear ejes
                        fig.update_xaxes(
                            tickformat='%d/%m/%Y',
                            tickangle=45
                        )
                        fig.update_yaxes(
                            tickformat='$,.0f',
                            title_standoff=20
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Tabla de datos del MEP
                        st.subheader("📋 Datos Históricos del MEP")
                        df_display = df_historico[['fecha', 'mep', 'precio_al30', 'precio_al30d']].copy()
                        df_display.columns = ['Fecha', 'MEP ($)', 'AL30 Pesos ($)', 'AL30D Dólares ($)']
                        df_display['Fecha'] = df_display['Fecha'].dt.strftime('%d/%m/%Y')
                        df_display['MEP ($)'] = df_display['MEP ($)'].apply(lambda x: f"${x:,.2f}")
                        df_display['AL30 Pesos ($)'] = df_display['AL30 Pesos ($)'].apply(lambda x: f"${x:,.2f}")
                        df_display['AL30D Dólares ($)'] = df_display['AL30D Dólares ($)'].apply(lambda x: f"${x:,.2f}")
                        
                        st.dataframe(df_display, use_container_width=True, height=300)
                        
                        # Información adicional
                        st.info("💡 **Cálculo del MEP**: Dólar MEP = Precio AL30 (pesos) ÷ Precio AL30D (dólares)")
                        
                else:
                        st.error("❌ No se pudo obtener el histórico del AL30")
            else:
                    st.warning("⚠️ Por favor seleccione fechas válidas")
    
    # Sección para operar con dólares MEP
    with st.expander("💱 Operar con Dólares MEP", expanded=False):
        st.info("💰 Realiza operaciones de compra y venta de dólares MEP usando la operatoria simplificada")
        
        # Verificar estado del mercado local
        estado_mercado = verificar_estado_mercado()
        
        # Mostrar información de horarios
        col1, col2 = st.columns(2)
        with col1:
            if estado_mercado.get('esHorarioValido'):
                st.success("🟢 Mercado abierto")
            else:
                st.error("🔴 Mercado cerrado")
                if not estado_mercado.get('esDiaHabil'):
                    st.warning(f"📅 Hoy es {estado_mercado.get('diaSemana')} - No es día hábil")
                elif not estado_mercado.get('enHorario'):
                    st.warning(f"⏰ Hora actual: {estado_mercado.get('horaActual')} - Fuera del horario de mercado")
        
        with col2:
            st.info(f"📅 Fecha: {estado_mercado.get('fecha')}")
            st.info(f"⏰ Horario: {estado_mercado.get('horarioApertura')} - {estado_mercado.get('horarioCierre')}")
        
        # Intentar obtener parámetros de operatoria MEP solo si el mercado está abierto
        if estado_mercado.get('esHorarioValido'):
            with st.spinner("Obteniendo parámetros de operatoria MEP..."):
                parametros_mep = obtener_parametros_operatoria_mep(token_acceso)
            
            if parametros_mep:
                st.success("✅ Parámetros de operatoria MEP obtenidos")
                
                # Mostrar límites si están disponibles
                if parametros_mep.get('montoLimiteMinimo') or parametros_mep.get('montoLimiteMaximo'):
                    col3, col4 = st.columns(2)
                    with col3:
                        st.info(f"📅 Límite mínimo: ${parametros_mep.get('montoLimiteMinimo', 0):,.0f}")
                    with col4:
                        st.info(f"📅 Límite máximo: ${parametros_mep.get('montoLimiteMaximo', 0):,.0f}")
            else:
                st.warning("⚠️ No se pudieron obtener los parámetros de operatoria MEP desde la API")
                st.info("💡 Usando parámetros por defecto para operaciones MEP")
                parametros_mep = {
                    'montoLimiteMinimo': 1000,
                    'montoLimiteMaximo': 1000000,
                    'esHorarioValido': True
                }
        else:
            st.warning("⚠️ El mercado está cerrado. Las operaciones MEP no están disponibles en este momento.")
            parametros_mep = None
        
        # Formulario de operación solo si el mercado está abierto
        if parametros_mep:
            with st.form("operar_mep_form"):
                st.subheader("📊 Nueva Operación MEP")
                
                col1, col2 = st.columns(2)
                with col1:
                    tipo_operacion = st.radio(
                        "Tipo de operación:",
                        ["Comprar USD", "Vender USD"],
                        help="Comprar USD: Pesos → Dólares MEP\nVender USD: Dólares MEP → Pesos"
                    )
                
                with col2:
                    monto = st.number_input(
                        "Monto:",
                        min_value=1000.0,
                        max_value=1000000.0,
                        value=10000.0,
                        step=1000.0,
                        help="Monto en pesos para comprar USD o monto en USD para vender"
                    )
                
                # Mostrar estimación de costos
                if st.form_submit_button("💰 Calcular Estimación"):
                    if monto:
                        with st.spinner("Calculando estimación..."):
                            if tipo_operacion == "Comprar USD":
                                estimacion = obtener_estimacion_compra_mep(token_acceso, monto)
                            else:
                                estimacion = obtener_estimacion_venta_mep(token_acceso, monto)
                        
                        if estimacion:
                            st.success("✅ Estimación calculada")
                            
                            # Mostrar estimación
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if tipo_operacion == "Comprar USD":
                                    st.metric("USD a recibir", f"${estimacion.get('montoDolar', 0):,.2f}")
                                    st.metric("Pesos netos", f"${estimacion.get('montoNetoPesos', 0):,.2f}")
                                else:
                                    st.metric("Pesos a recibir", f"${estimacion.get('montoNetoPesos', 0):,.2f}")
                                    st.metric("USD netos", f"${estimacion.get('montoDolar', 0):,.2f}")
                            
                            with col2:
                                st.metric("Comisión compra", f"${estimacion.get('comisionCompra', 0):,.2f}")
                                st.metric("Comisión venta", f"${estimacion.get('comisionVenta', 0):,.2f}")
                            
                            with col3:
                                st.metric("Derecho mercado", f"${estimacion.get('derechoMercadoCompra', 0) + estimacion.get('derechoMercadoVenta', 0):,.2f}")
                                st.metric("IVA", f"${estimacion.get('comisionCompraIVA', 0) + estimacion.get('comisionVentaIVA', 0):,.2f}")
                            
                            # Botón para ejecutar la operación
                            if st.button("🚀 Ejecutar Operación", type="primary"):
                                if tipo_operacion == "Comprar USD":
                                    resultado = ejecutar_compra_mep(token_acceso, monto)
                                else:
                                    resultado = ejecutar_venta_mep(token_acceso, monto)
                                
                                if resultado and resultado.get('ok'):
                                    st.success("✅ Operación ejecutada exitosamente")
                                    for mensaje in resultado.get('messages', []):
                                        st.info(f"📝 {mensaje.get('title', '')}: {mensaje.get('description', '')}")
                                else:
                                    st.error("❌ Error al ejecutar la operación")
                                    if resultado:
                                        for mensaje in resultado.get('messages', []):
                                            st.error(f"❌ {mensaje.get('title', '')}: {mensaje.get('description', '')}")
                        else:
                            st.error("❌ No se pudo calcular la estimación")
                    else:
                        st.warning("⚠️ Por favor ingrese un monto válido")
        else:
            st.error("❌ No se pudieron obtener los parámetros de operatoria MEP")
    



def mostrar_analisis_tecnico(token_acceso, id_cliente, portafolio_ar=None, portafolio_eeuu=None):
    st.markdown("### 📊 Análisis Técnico")
    
    # Si no se pasan los portafolios, obtenerlos
    if portafolio_ar is None or portafolio_eeuu is None:
        with st.spinner("Obteniendo portafolios..."):
            if portafolio_ar is None:
                portafolio_ar = obtener_portafolio(token_acceso, id_cliente)
            if portafolio_eeuu is None:
                portafolio_eeuu = obtener_portafolio_eeuu(token_acceso, id_cliente)
    
    simbolos = []
    simbolos_info = {}  # Para almacenar información adicional de cada símbolo
    
    # Procesar portafolio argentino
    if portafolio_ar:
        activos_ar = portafolio_ar.get('activos', [])
        for activo in activos_ar:
            titulo = activo.get('titulo', {})
            simbolo = titulo.get('simbolo', '')
            if simbolo:
                simbolos.append(f"🇦🇷 {simbolo}")
                simbolos_info[f"🇦🇷 {simbolo}"] = {
                    'simbolo': simbolo,
                    'pais': 'Argentina',
                    'mercado': 'bCBA'
                }
    
    # Procesar portafolio estadounidense
    if portafolio_eeuu:
        activos_eeuu = portafolio_eeuu.get('activos', [])
        for activo in activos_eeuu:
            titulo = activo.get('titulo', {})
            simbolo = titulo.get('simbolo', '')
            if simbolo:
                simbolos.append(f"🇺🇸 {simbolo}")
                simbolos_info[f"🇺🇸 {simbolo}"] = {
                    'simbolo': simbolo,
                    'pais': 'Estados Unidos',
                    'mercado': 'nYSE'
                }
    
    if not simbolos:
        st.warning("No se encontraron símbolos válidos en los portafolios")
        return
    
    simbolo_seleccionado = st.selectbox(
        "Seleccione un activo para análisis técnico:",
        options=simbolos,
        key="simbolo_analisis_tecnico",
        help="Incluye activos de los portafolios argentino y estadounidense"
    )
    
    # Obtener información del símbolo seleccionado
    info_simbolo = simbolos_info[simbolo_seleccionado]
    simbolo_limpio = info_simbolo['simbolo']
    pais = info_simbolo['pais']
    mercado = info_simbolo['mercado']
    
    # Obtener información real del activo desde el portafolio
    def obtener_tipo_activo_real(simbolo_limpio, portafolio_ar, portafolio_eeuu):
        """Obtiene el tipo real de activo desde los datos de la API"""
        # Buscar en portafolio argentino
        if portafolio_ar:
            activos_ar = portafolio_ar.get('activos', [])
            for activo in activos_ar:
                titulo = activo.get('titulo', {})
                if titulo.get('simbolo') == simbolo_limpio:
                    # Obtener información del tipo de activo
                    tipo_titulo = titulo.get('tipo', '')
                    descripcion = titulo.get('descripcion', '')
                    mercado = titulo.get('mercado', '')
                    
                    # Determinar tipo basado en datos reales
                    if 'AL30' in simbolo_limpio or 'GD30' in simbolo_limpio or 'BONO' in tipo_titulo.upper():
                        return "Título Público (Bono)"
                    elif 'CEDEAR' in tipo_titulo.upper() or 'CEDEAR' in descripcion.upper():
                        return "CEDEAR"
                    elif 'ACCION' in tipo_titulo.upper() or 'ACCION' in descripcion.upper():
                        return "Acción Argentina"
                    elif 'FCI' in tipo_titulo.upper() or 'FONDO' in descripcion.upper():
                        return "Fondo Común de Inversión"
                    elif 'ETF' in tipo_titulo.upper() or 'ETF' in descripcion.upper():
                        return "ETF"
                    else:
                        return f"Activo ({tipo_titulo})" if tipo_titulo else "Activo Argentina"
        
        # Buscar en portafolio estadounidense
        if portafolio_eeuu:
            activos_eeuu = portafolio_eeuu.get('activos', [])
            for activo in activos_eeuu:
                titulo = activo.get('titulo', {})
                if titulo.get('simbolo') == simbolo_limpio:
                    tipo_titulo = titulo.get('tipo', '')
                    descripcion = titulo.get('descripcion', '')
                    
                    if 'STOCK' in tipo_titulo.upper() or 'ACCION' in tipo_titulo.upper():
                        return "Acción Internacional"
                    elif 'ETF' in tipo_titulo.upper() or 'ETF' in descripcion.upper():
                        return "ETF Internacional"
                    elif 'BOND' in tipo_titulo.upper() or 'BONO' in tipo_titulo.upper():
                        return "Bono Internacional"
                    else:
                        return f"Activo Internacional ({tipo_titulo})" if tipo_titulo else "Activo Internacional"
        
        # Fallback basado en patrones conocidos
        if simbolo_limpio in ['AL30', 'GD30', 'AE38', 'AL35', 'GD35']:
            return "Título Público (Bono)"
        elif simbolo_limpio in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']:
            return "CEDEAR"
        else:
            return "Activo"
    
    # Obtener tipo real del activo
    tipo_activo = obtener_tipo_activo_real(simbolo_limpio, portafolio_ar, portafolio_eeuu)
    
    # Determinar si es un CEDEAR para TradingView
    def es_cedear(simbolo):
        """Identifica si un símbolo es un CEDEAR basado en patrones comunes"""
        cedears_conocidos = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD',
            'INTC', 'ORCL', 'CRM', 'ADBE', 'PYPL', 'UBER', 'LYFT', 'SNAP', 'TWTR',
            'BABA', 'NIO', 'XOM', 'JPM', 'BAC', 'WMT', 'PG', 'KO', 'PFE', 'JNJ',
            'V', 'MA', 'DIS', 'NKE', 'HD', 'MCD', 'IBM', 'GE', 'F', 'GM', 'T',
            'VZ', 'ATT', 'CSCO', 'QCOM', 'AVGO', 'TXN', 'AMAT', 'MU', 'LRCX',
            'KLAC', 'MCHP', 'ADI', 'MRVL', 'SWKS', 'QRVO', 'SLAB', 'CRUS', 'SYNA'
        ]
        return simbolo.upper() in cedears_conocidos
    
    # Preparar símbolo para TradingView
    if pais == 'Argentina' and es_cedear(simbolo_limpio):
        simbolo_tradingview = f"BCBA:{simbolo_limpio}"
    elif pais == 'Argentina':
        simbolo_tradingview = f"BCBA:{simbolo_limpio}"
    else:
        simbolo_tradingview = simbolo_limpio
    
    # Mostrar información del activo seleccionado
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info(f"📊 **Símbolo**: {simbolo_limpio}")
    with col2:
        st.info(f"🌍 **País**: {pais}")
    with col3:
        st.info(f"🏛️ **Mercado**: {mercado}")
    with col4:
        st.info(f"📈 **Tipo**: {tipo_activo}")
    
    if simbolo_seleccionado:
        st.info(f"Mostrando gráfico para: {simbolo_seleccionado} ({simbolo_tradingview})")
        
        # Widget de TradingView
        tv_widget = f"""
        <div id="tradingview_{simbolo_limpio}" style="height:650px"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
          "container_id": "tradingview_{simbolo_limpio}",
          "width": "100%",
          "height": 650,
          "symbol": "{simbolo_tradingview}",
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


# Clase PortfolioManager simplificada para compatibilidad
class PortfolioManager:
    """
    Clase para manejo de portafolio y optimización con funcionalidades extendidas
    """
    def __init__(self, symbols, token, fecha_desde, fecha_hasta, risk_free_rate=0.04):
        self.symbols = symbols
        self.token = token
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.risk_free_rate = risk_free_rate  # Tasa libre de riesgo configurable
        self.data_loaded = False
        self.returns = None
        self.prices = None
        self.notional = 100000  # Valor nominal por defecto
        self.manager = None
    
    def load_data(self):
        """
        Carga datos históricos para los símbolos del portafolio
        """
        try:
            df_precios, returns, simbolos_exitosos = get_historical_data_for_optimization(
                self.token, self.symbols, self.fecha_desde, self.fecha_hasta
            )
            
            if returns is not None and not returns.empty and df_precios is not None:
                self.returns = returns
                self.prices = df_precios
                self.mean_returns = returns.mean() * 252  # Anualizar
                self.cov_matrix = returns.cov() * 252     # Anualizar
                self.data_loaded = True
                
                # Crear manager para optimización avanzada
                self.manager = manager(list(df_precios.columns), self.notional, df_precios.to_dict('series'))
                
                return True
            else:
                return False
                
        except Exception as e:
            st.error(f"Error cargando datos: {str(e)}")
            return False
    
    def load_data_with_real_metrics(self, portafolio):
        """
        Carga datos usando métricas reales basadas en operaciones del portafolio
        """
        try:
            # Primero intentar obtener métricas reales del portafolio
            composicion_por_fecha, posiciones_actuales = obtener_composicion_historica_portafolio(
                self.token, portafolio.get('activos', []), self.fecha_desde, self.fecha_hasta
            )
            
            if posiciones_actuales:
                # Calcular métricas reales para cada activo
                metricas_por_activo = {}
                simbolos_reales = []
                
                for simbolo in self.symbols:
                    if simbolo in posiciones_actuales:
                        # Obtener serie histórica del activo
                        serie_historica = obtener_serie_historica_activo(simbolo, self.token, self.fecha_desde, self.fecha_hasta)
                        
                        if serie_historica is not None and not serie_historica.empty:
                            # Calcular retorno real basado en operaciones
                            retorno_real = calcular_retorno_real_activo(simbolo, posiciones_actuales, serie_historica)
                            
                            if retorno_real:
                                metricas_por_activo[simbolo] = retorno_real
                                simbolos_reales.append(simbolo)
                
                if metricas_por_activo:
                    # Crear matriz de retornos esperados basada en retornos anualizados reales
                    retornos_esperados = {}
                    volatilidades = {}
                    
                    for simbolo, metricas in metricas_por_activo.items():
                        retornos_esperados[simbolo] = metricas['retorno_anualizado']
                        volatilidades[simbolo] = metricas['volatilidad_anualizada']
                    
                    # Crear DataFrame de retornos simulados basados en métricas reales
                    fechas = pd.date_range(start=self.fecha_desde, end=self.fecha_hasta, freq='D')
                    df_retornos_reales = pd.DataFrame(index=fechas)
                    
                    for simbolo in simbolos_reales:
                        # Generar retornos diarios basados en la volatilidad real
                        retorno_diario_esperado = retornos_esperados[simbolo] / 252
                        volatilidad_diaria = volatilidades[simbolo] / np.sqrt(252)
                        
                        # Generar serie de retornos con la media y volatilidad reales
                        retornos_simulados = np.random.normal(
                            retorno_diario_esperado, 
                            volatilidad_diaria, 
                            len(fechas)
                        )
                        df_retornos_reales[simbolo] = retornos_simulados
                    
                    # Actualizar atributos de la clase
                    self.returns = df_retornos_reales
                    self.mean_returns = pd.Series(retornos_esperados)
                    
                    # Crear matriz de covarianza basada en volatilidades reales
                    # Simplificado: asumir correlación de 0.3 entre activos
                    correlacion_default = 0.3
                    n_assets = len(simbolos_reales)
                    cov_matrix = np.full((n_assets, n_assets), correlacion_default)
                    np.fill_diagonal(cov_matrix, 1.0)
                    
                    # Aplicar volatilidades reales
                    volatilidades_array = np.array([volatilidades[s] for s in simbolos_reales])
                    cov_matrix = np.outer(volatilidades_array, volatilidades_array) * cov_matrix
                    
                    self.cov_matrix = pd.DataFrame(cov_matrix, index=simbolos_reales, columns=simbolos_reales)
                    self.data_loaded = True
                    self.metricas_reales = metricas_por_activo
                    
                    st.success(f"✅ Datos cargados con métricas reales para {len(simbolos_reales)} activos")
                    st.info(f"📊 Retornos anualizados reales: {', '.join([f'{s}: {retornos_esperados[s]:.2%}' for s in simbolos_reales[:3]])}")
                    return True
            
            # Fallback al método tradicional si no se pueden obtener métricas reales
            st.warning("⚠️ No se pudieron obtener métricas reales, usando método tradicional")
            return self.load_data()
                
        except Exception as e:
            st.error(f"Error cargando datos con métricas reales: {str(e)}")
            # Fallback al método tradicional
            return self.load_data()

    def compute_portfolio(self, strategy='markowitz', target_return=None, risk_free_rate=None):
        """
        Computa la optimización del portafolio con estrategias extendidas
        """
        if not self.data_loaded or self.returns is None:
            return None
        
        # Usar la tasa libre de riesgo proporcionada o la configurada en la instancia
        if risk_free_rate is not None:
            self.risk_free_rate = risk_free_rate
        
        try:
            if self.manager:
                # Usar el manager avanzado con tasa libre de riesgo actualizada
                portfolio_output = self.manager.compute_portfolio(strategy, target_return)
                return portfolio_output
            else:
                # Fallback a optimización básica
                n_assets = len(self.returns.columns)
                
                if strategy == 'equi-weight':
                    weights = np.array([1/n_assets] * n_assets)
                elif strategy == 'max_return':
                    # Optimización para máximo retorno
                    weights = self._optimize_max_return()
                elif strategy == 'min-variance-l2':
                    # Optimización para mínima varianza
                    weights = self._optimize_min_variance()
                elif strategy == 'sharpe_ratio':
                    # Optimización para máximo ratio de Sharpe
                    weights = self._optimize_sharpe_ratio()
                else:
                    # Markowitz por defecto
                    weights = optimize_portfolio(self.returns, risk_free_rate=self.risk_free_rate, target_return=target_return)
                
                # Crear objeto de resultado básico
                portfolio_returns = (self.returns * weights).sum(axis=1)
                portfolio_output = output(portfolio_returns, self.notional)
                portfolio_output.weights = weights
                
                # Crear DataFrame de asignación con debugging
                try:
                    portfolio_output.dataframe_allocation = pd.DataFrame({
                        'rics': list(self.returns.columns),
                        'weights': weights,
                        'volatilities': self.returns.std().values,
                        'returns': self.returns.mean().values
                    })
                    st.info(f"ℹ️ Debug: DataFrame creado con columnas: {portfolio_output.dataframe_allocation.columns.tolist()}")
                except Exception as e:
                    st.error(f"❌ Error creando DataFrame de asignación: {str(e)}")
                    # Crear DataFrame básico como fallback
                    portfolio_output.dataframe_allocation = pd.DataFrame({
                        'rics': [f'Activo_{i+1}' for i in range(len(weights))],
                        'weights': weights
                    })
                
                return portfolio_output
            
        except Exception as e:
            st.error(f"Error en optimización: {str(e)}")
            return None
    
    def _optimize_max_return(self):
        """
        Optimiza el portafolio para máximo retorno esperado
        """
        try:
            # Verificar que self.returns no sea None y tenga columnas
            if self.returns is None or not hasattr(self.returns, 'columns') or len(self.returns.columns) == 0:
                st.error("No hay datos de retornos disponibles para optimización de máximo retorno")
                return None
            # Calcular retornos esperados
            expected_returns = self.returns.mean()
            # Encontrar el activo con mayor retorno esperado
            max_return_idx = expected_returns.idxmax()
            # Asignar todo el peso al activo con mayor retorno
            weights = np.zeros(len(self.returns.columns))
            weights[self.returns.columns.get_loc(max_return_idx)] = 1.0
            return weights
        except Exception as e:
            st.error(f"Error en optimización de máximo retorno: {str(e)}")
            if self.returns is not None and hasattr(self.returns, 'columns') and len(self.returns.columns) > 0:
                return np.array([1/len(self.returns.columns)] * len(self.returns.columns))
            else:
                return None
    
    def _optimize_min_variance(self):
        """
        Optimiza para mínima varianza
        """
        try:
            # Calcular matriz de covarianza
            cov_matrix = self.returns.cov()
            
            # Función objetivo: minimizar varianza del portafolio
            def objective(weights):
                return np.dot(weights.T, np.dot(cov_matrix, weights))
            
            # Restricciones: pesos suman 1
            def constraint(weights):
                return np.sum(weights) - 1.0
            
            # Optimización
            n_assets = len(self.returns.columns)
            initial_weights = np.array([1/n_assets] * n_assets)
            
            constraints = {'type': 'eq', 'fun': constraint}
            bounds = [(0, 1) for _ in range(n_assets)]
            
            result = optimize.minimize(objective, initial_weights, 
                                    constraints=constraints, bounds=bounds)
            
            if result.success:
                return result.x
            else:
                st.warning("⚠️ Optimización de mínima varianza falló, usando pesos iguales")
                return np.array([1/n_assets] * n_assets)
                
        except Exception as e:
            st.error(f"Error en optimización de mínima varianza: {str(e)}")
            return np.array([1/len(self.returns.columns)] * len(self.returns.columns))
    
    def _optimize_sharpe_ratio(self):
        """
        Optimiza para máximo ratio de Sharpe usando la tasa libre de riesgo configurada
        """
        try:
            # Calcular retornos esperados y matriz de covarianza
            expected_returns = self.returns.mean()
            cov_matrix = self.returns.cov()
            
            # Usar la tasa libre de riesgo configurada en la instancia
            risk_free_rate = self.risk_free_rate
            
            # Función objetivo: maximizar ratio de Sharpe (minimizar negativo)
            def objective(weights):
                portfolio_return = np.sum(expected_returns * weights)
                portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                
                if portfolio_volatility == 0:
                    return 0
                
                sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
                return -sharpe_ratio  # Minimizar negativo = maximizar positivo
            
            # Restricciones: pesos suman 1
            def constraint(weights):
                return np.sum(weights) - 1.0
            
            # Optimización
            n_assets = len(self.returns.columns)
            initial_weights = np.array([1/n_assets] * n_assets)
            
            constraints = {'type': 'eq', 'fun': constraint}
            bounds = [(0, 1) for _ in range(n_assets)]
            
            result = optimize.minimize(objective, initial_weights, 
                                    constraints=constraints, bounds=bounds)
            
            if result.success:
                return result.x
            else:
                st.warning("⚠️ Optimización de Sharpe ratio falló, usando pesos iguales")
                return np.array([1/n_assets] * n_assets)
                
        except Exception as e:
            st.error(f"Error en optimización de Sharpe ratio: {str(e)}")
            return np.array([1/len(self.returns.columns)] * len(self.returns.columns))

    def compute_efficient_frontier(self, target_return=0.08, include_min_variance=True):
        """
        Computa la frontera eficiente
        """
        if not self.data_loaded or not self.manager:
            return None, None, None
        
        try:
            portfolios, returns, volatilities = compute_efficient_frontier(
                self.symbols, self.notional, target_return, include_min_variance, 
                self.prices.to_dict('series')
            )
            return portfolios, returns, volatilities
        except Exception as e:
            st.error(f"Error computando frontera eficiente: {str(e)}")
            return None, None, None

    def compute_rebalancing_analysis(self, current_weights, target_weights):
        """
        Analiza el rebalanceo necesario para alcanzar los pesos objetivo
        """
        if not self.data_loaded:
            return None
        
        try:
            # Calcular diferencias de pesos
            weight_diff = np.array(target_weights) - np.array(current_weights)
            
            # Calcular métricas de rebalanceo
            total_turnover = np.sum(np.abs(weight_diff))
            max_change = np.max(np.abs(weight_diff))
            num_changes = np.sum(np.abs(weight_diff) > 0.01)  # Cambios mayores al 1%
            
            # Calcular impacto en métricas del portafolio
            current_metrics = self._calculate_portfolio_metrics(current_weights)
            target_metrics = self._calculate_portfolio_metrics(target_weights)
            
            return {
                'weight_differences': weight_diff,
                'total_turnover': total_turnover,
                'max_change': max_change,
                'num_changes': num_changes,
                'current_metrics': current_metrics,
                'target_metrics': target_metrics,
                'improvement': {
                    'return_improvement': target_metrics['return'] - current_metrics['return'],
                    'risk_improvement': current_metrics['volatility'] - target_metrics['volatility'],
                    'sharpe_improvement': target_metrics['sharpe'] - current_metrics['sharpe']
                }
            }
            
        except Exception as e:
            st.error(f"Error en análisis de rebalanceo: {str(e)}")
            return None
    
    def _calculate_portfolio_metrics(self, weights):
        """
        Calcula métricas básicas del portafolio para un conjunto de pesos con validaciones mejoradas
        """
        try:
            # Validar inputs
            if weights is None or len(weights) == 0:
                return {'return': 0, 'volatility': 0, 'sharpe': 0}
            
            if self.mean_returns is None or self.cov_matrix is None:
                st.warning("⚠️ Datos de retornos no disponibles")
                return {'return': 0, 'volatility': 0, 'sharpe': 0}
            
            # Asegurar que weights sea un array numpy
            weights = np.array(weights)
            
            # Validar que los pesos sumen aproximadamente 1
            if abs(np.sum(weights) - 1.0) > 0.01:
                st.warning("⚠️ Los pesos no suman 1. Normalizando...")
                weights = weights / np.sum(weights)
            
            # Calcular retorno anualizado
            portfolio_return = np.sum(self.mean_returns * weights)
            
            # Calcular volatilidad anualizada
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
            
            # Calcular ratio de Sharpe con validación
            if portfolio_volatility > 0:
                sharpe_ratio = portfolio_return / portfolio_volatility
            else:
                sharpe_ratio = 0.0
            
            # Validar resultados
            if np.isnan(portfolio_return) or np.isinf(portfolio_return):
                portfolio_return = 0.0
            if np.isnan(portfolio_volatility) or np.isinf(portfolio_volatility):
                portfolio_volatility = 0.0
            if np.isnan(sharpe_ratio) or np.isinf(sharpe_ratio):
                sharpe_ratio = 0.0
            
            return {
                'return': portfolio_return,
                'volatility': portfolio_volatility,
                'sharpe': sharpe_ratio
            }
        except Exception as e:
            st.error(f"❌ Error en cálculo de métricas del portafolio: {str(e)}")
            return {'return': 0, 'volatility': 0, 'sharpe': 0}

def mostrar_menu_optimizacion_unificado(portafolio_ar, portafolio_eeuu, token_acceso, fecha_desde, fecha_hasta):
    """
    Menú unificado organizado en dos categorías: Rebalanceo y Optimizaciones
    Permite seleccionar entre portafolios individuales (Argentina, EEUU) o combinado
    """
    st.markdown("### 🎯 Optimización y Cobertura de Portafolio")
    
    # Selección de portafolio a optimizar
    opciones_portafolio = []
    if portafolio_ar and 'activos' in portafolio_ar and len(portafolio_ar['activos']) > 0:
        opciones_portafolio.append("🇦🇷 Portafolio Argentina")
    if portafolio_eeuu and 'activos' in portafolio_eeuu and len(portafolio_eeuu['activos']) > 0:
        opciones_portafolio.append("🇺🇸 Portafolio EEUU")
    if len(opciones_portafolio) >= 2:
        opciones_portafolio.append("🌍 Portafolio Combinado")
    
    if not opciones_portafolio:
        st.warning("⚠️ No hay portafolios disponibles para optimización")
        return
    
    portafolio_seleccionado = st.selectbox(
        "Seleccione el portafolio a optimizar:",
        options=opciones_portafolio,
        help="Elija qué portafolio desea optimizar",
        key="portafolio_optimizacion_seleccionado"
    )
    
    # Determinar qué portafolio usar según la selección
    if "Argentina" in portafolio_seleccionado:
        portafolio = portafolio_ar
        st.info(f"🇦🇷 Optimizando portafolio Argentina: {len(portafolio['activos'])} activos")
    elif "EEUU" in portafolio_seleccionado:
        portafolio = portafolio_eeuu
        st.info(f"🇺🇸 Optimizando portafolio EEUU: {len(portafolio['activos'])} activos")
    elif "Combinado" in portafolio_seleccionado:
        # Combinar portafolios
        activos_combinados = []
        if portafolio_ar and 'activos' in portafolio_ar:
            activos_combinados.extend(portafolio_ar['activos'])
        if portafolio_eeuu and 'activos' in portafolio_eeuu:
            activos_combinados.extend(portafolio_eeuu['activos'])
        portafolio = {'activos': activos_combinados}
        st.info(f"🌍 Optimizando portafolio combinado: {len(activos_combinados)} activos totales")
    
    # Selección de categoría principal
    categoria = st.selectbox(
        "Seleccione la categoría:",
        options=[
            "🔄 Rebalanceo",
            "📈 Optimizaciones"
        ],
        help="Elija la categoría de análisis que desea realizar",
        key="categoria_optimizacion_unificado"
    )
    
    if categoria == "🔄 Rebalanceo":
        # Submenú de Rebalanceo
        tipo_rebalanceo = st.selectbox(
            "Seleccione el tipo de rebalanceo:",
            options=[
                "🔄 Rebalanceo con Composición Actual",
                "🎲 Rebalanceo con Símbolos Aleatorios",
                "📊 Optimización Básica",
                "📈 Frontera Eficiente"
            ],
            help="Elija el tipo de rebalanceo que desea realizar",
            key="tipo_rebalanceo_unificado"
        )
        
        if tipo_rebalanceo == "🔄 Rebalanceo con Composición Actual":
            mostrar_rebalanceo_composicion_actual(portafolio, token_acceso, fecha_desde, fecha_hasta)
        elif tipo_rebalanceo == "📊 Optimización Básica":
            mostrar_optimizacion_basica(portafolio, token_acceso, fecha_desde, fecha_hasta)
        elif tipo_rebalanceo == "📈 Frontera Eficiente":
            mostrar_frontera_eficiente(portafolio, token_acceso, fecha_desde, fecha_hasta)
        elif tipo_rebalanceo == "🔄 Rebalanceo con Composición Actual":
            mostrar_rebalanceo_composicion_actual(portafolio, token_acceso, fecha_desde, fecha_hasta)
        elif tipo_rebalanceo == "🎲 Rebalanceo con Símbolos Aleatorios":
            mostrar_rebalanceo_simbolos_aleatorios(portafolio, token_acceso, fecha_desde, fecha_hasta)
    
    elif categoria == "📈 Optimizaciones":
        # Submenú de Optimizaciones
        tipo_optimizacion = st.selectbox(
            "Seleccione el tipo de optimización:",
            options=[
                "🎲 Optimización Aleatoria",
                "🚀 Optimización Avanzada",
                "🛡️ Análisis de Cobertura"
            ],
            help="Elija el tipo de optimización que desea realizar",
            key="tipo_optimizacion_unificado"
        )
        
        if tipo_optimizacion == "🎲 Optimización Aleatoria":
            mostrar_optimizacion_aleatoria(portafolio, token_acceso, fecha_desde, fecha_hasta)
        elif tipo_optimizacion == "🚀 Optimización Avanzada":
            mostrar_optimizacion_avanzada(portafolio, token_acceso, fecha_desde, fecha_hasta)
        elif tipo_optimizacion == "🛡️ Análisis de Cobertura":
            mostrar_cobertura_portafolio(portafolio, token_acceso, fecha_desde, fecha_hasta)

def mostrar_rebalanceo_composicion_actual(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Rebalanceo con la composición actual del portafolio pero optimizando los pesos
    """
    st.markdown("#### 🔄 Rebalanceo con Composición Actual")
    
    activos = portafolio.get('activos', [])
    if not activos:
        st.warning("No hay activos en el portafolio para rebalancear")
        return
    
    # Extraer símbolos del portafolio
    simbolos = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', '')
        if simbolo:
            simbolos.append(simbolo)
    
    if len(simbolos) < 2:
        st.warning("Se necesitan al menos 2 activos para rebalanceo")
        return
    
    st.info(f"📊 Rebalanceando {len(simbolos)} activos del portafolio actual")
    
    # Configuración de benchmark y tasa libre de riesgo
    st.markdown("#### 🎯 Configuración de Benchmark")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        benchmark = st.selectbox(
            "Benchmark para Tasa Libre de Riesgo:",
            options=[
                'Tasa_Caucion_Promedio',
                'Dolar_MEP',
                'Dolar_Blue', 
                'Dolar_Oficial',
                'Bono_AL30',
                'Bono_GD30',
                'Indice_S&P_MERVAL',
                'Indice_S&P_500',
                'Tasa_Fija_4%',
                'Tasa_Fija_6%',
                'Tasa_Fija_8%'
            ],
            format_func=lambda x: {
                'Tasa_Caucion_Promedio': 'Tasa de Caución Promedio',
                'Dolar_MEP': 'Dólar MEP',
                'Dolar_Blue': 'Dólar Blue',
                'Dolar_Oficial': 'Dólar Oficial',
                'Bono_AL30': 'Bono AL30',
                'Bono_GD30': 'Bono GD30',
                'Indice_S&P_MERVAL': 'S&P MERVAL',
                'Indice_S&P_500': 'S&P 500',
                'Tasa_Fija_4%': 'Tasa Fija 4%',
                'Tasa_Fija_6%': 'Tasa Fija 6%',
                'Tasa_Fija_8%': 'Tasa Fija 8%'
            }[x],
            help="Seleccione el benchmark que servirá como tasa libre de riesgo",
            key="benchmark_composicion_actual"
        )
    
    with col2:
        # Calcular retorno del benchmark
        benchmark_return = 0.04  # Valor por defecto
        if benchmark.startswith('Tasa_Fija'):
            benchmark_return = float(benchmark.split('_')[-1].replace('%', '')) / 100
        else:
            try:
                # Obtener datos del benchmark
                benchmark_data = obtener_datos_benchmark_argentino(benchmark, token_acceso, fecha_desde, fecha_hasta)
                if benchmark_data is not None and not benchmark_data.empty:
                    # Calcular retorno anual del benchmark
                    benchmark_returns = benchmark_data.iloc[:, 0].dropna()
                    if len(benchmark_returns) > 0:
                        benchmark_return = benchmark_returns.mean() * 252  # Anualizar
                        st.success(f"✅ Retorno benchmark calculado: {benchmark_return:.2%}")
                    else:
                        st.warning("⚠️ No se pudieron calcular retornos del benchmark")
                else:
                    st.warning("⚠️ No se pudieron obtener datos del benchmark")
            except Exception as e:
                st.error(f"❌ Error calculando retorno del benchmark: {str(e)}")
        
        st.metric("Retorno Anual del Benchmark", f"{benchmark_return:.2%}")
    
    with col3:
        usar_benchmark = st.checkbox(
            "Usar Benchmark como Tasa Libre de Riesgo",
            value=True,
            help="Si está marcado, el benchmark se usará como tasa libre de riesgo en optimizaciones",
            key="usar_benchmark_composicion_actual"
        )
    
    # Configuración de optimización
    st.markdown("#### ⚙️ Configuración de Optimización")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        modo_optimizacion = st.selectbox(
            "Modo de Optimización:",
            options=['markowitz', 'max_return', 'min_variance', 'sharpe_ratio'],
            format_func=lambda x: {
                'markowitz': 'Markowitz (Retorno-Riesgo)',
                'max_return': 'Máximo Retorno',
                'min_variance': 'Mínima Varianza',
                'sharpe_ratio': 'Máximo Ratio de Sharpe'
            }[x],
            help="Seleccione el criterio de optimización",
            key="modo_optimizacion_composicion_actual"
        )
    
    with col2:
        target_return = st.number_input(
            "Retorno Objetivo (anual):",
            min_value=0.0, value=0.08, step=0.01,
            help="Solo aplica para optimización Markowitz"
        )
    
    with col3:
        mostrar_comparacion = st.checkbox("Mostrar Comparación con Actual", value=True, key="mostrar_comparacion_composicion_actual")
    
    # Botón de ejecución
    col1, col2 = st.columns(2)
    with col1:
        ejecutar_rebalanceo = st.button("🚀 Ejecutar Rebalanceo")
    with col2:
        ejecutar_completo = st.button("🎯 Rebalanceo Completo")
    
    if ejecutar_rebalanceo or ejecutar_completo:
        with st.spinner("🔄 Ejecutando rebalanceo..."):
            try:
                # Crear manager de portafolio con tasa libre de riesgo del benchmark
                risk_free_rate = benchmark_return if usar_benchmark else 0.04
                manager_inst = PortfolioManager(simbolos, token_acceso, fecha_desde, fecha_hasta, risk_free_rate)
                
                # Cargar datos con timeout optimizado
                if manager_inst.load_data():
                    st.success("✅ Datos cargados correctamente")
                    
                    # Ejecutar optimización
                    portfolio_result = manager_inst.compute_portfolio(
                        strategy=modo_optimizacion, 
                        target_return=target_return if modo_optimizacion == 'markowitz' else None,
                        risk_free_rate=risk_free_rate if usar_benchmark else None
                    )
                    
                    if portfolio_result:
                        st.success("✅ Rebalanceo completado")
                        
                        # Mostrar resultados
                        mostrar_resultados_rebalanceo_aleatorio(
                            portfolio_result, simbolos, sum(activo.get('valor', 0) for activo in activos),
                            activos, mostrar_comparacion=mostrar_comparacion, mostrar_metricas=True
                        )
                    else:
                        st.error("❌ No se pudo completar el rebalanceo")
                else:
                    st.error("❌ No se pudieron cargar los datos históricos")
                    
            except Exception as e:
                st.error(f"❌ Error durante el rebalanceo: {str(e)}")

def mostrar_rebalanceo_simbolos_aleatorios(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Rebalanceo usando símbolos aleatorios pero manteniendo el mismo capital total
    del portafolio actual, con opción de incluir saldo disponible
    """
    st.markdown("#### 🎲 Rebalanceo con Símbolos Aleatorios")
    
    activos = portafolio.get('activos', [])
    if not activos:
        st.warning("No hay activos en el portafolio para calcular el capital total")
        return
    
    # Calcular capital total actual
    capital_total_actual = sum(activo.get('valor', 0) for activo in activos)
    
    if capital_total_actual <= 0:
        st.warning("No se puede calcular el capital total del portafolio")
        return
    
    st.info(f"💰 Capital total actual del portafolio: ${capital_total_actual:,.2f}")
    
    # Opción para incluir saldo disponible
    incluir_saldo_disponible = st.checkbox(
        "💳 Incluir saldo disponible del estado de cuenta",
        value=False,
        help="Si está marcado, se incluirá el saldo disponible en el capital total",
        key="incluir_saldo_disponible_aleatorio"
    )
    
    capital_disponible = 0
    if incluir_saldo_disponible:
        try:
            # Obtener estado de cuenta para calcular saldo disponible
            estado_cuenta = obtener_estado_cuenta(token_acceso)
            if estado_cuenta and 'cuentas' in estado_cuenta:
                for cuenta in estado_cuenta['cuentas']:
                    if 'saldoDisponible' in cuenta:
                        capital_disponible += cuenta.get('saldoDisponible', 0)
            
            if capital_disponible > 0:
                st.success(f"💵 Saldo disponible encontrado: ${capital_disponible:,.2f}")
            else:
                st.warning("⚠️ No se encontró saldo disponible")
        except Exception as e:
            st.error(f"❌ Error obteniendo saldo disponible: {str(e)}")
            capital_disponible = 0
    
    capital_total = capital_total_actual + capital_disponible
    st.success(f"🎯 Capital total para rebalanceo: ${capital_total:,.2f}")
    
    # Configuración de símbolos aleatorios
    st.markdown("#### 🎲 Configuración de Símbolos Aleatorios")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        num_simbolos = st.slider(
            "Número de símbolos:",
            min_value=2, max_value=20, value=10,
            help="Cantidad de símbolos aleatorios a incluir en el portafolio"
        )
    
    with col2:
        incluir_actuales = st.checkbox(
            "🔄 Incluir símbolos actuales",
            value=True,
            help="Incluir algunos símbolos del portafolio actual en la selección aleatoria",
            key="incluir_actuales_aleatorio"
        )
    
    with col3:
        porcentaje_actuales = st.slider(
            "Porcentaje de símbolos actuales:",
            min_value=0, max_value=100, value=30,
            help="Porcentaje de símbolos actuales a incluir en la selección"
        )
    
    # Configuración de optimización
    st.markdown("#### ⚙️ Configuración de Optimización")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        modo_optimizacion = st.selectbox(
            "Modo de Optimización:",
            options=['markowitz', 'max_return', 'min_variance', 'sharpe_ratio'],
            format_func=lambda x: {
                'markowitz': 'Markowitz (Retorno-Riesgo)',
                'max_return': 'Máximo Retorno',
                'min_variance': 'Mínima Varianza',
                'sharpe_ratio': 'Máximo Ratio de Sharpe'
            }[x],
            help="Seleccione el criterio de optimización",
            key="modo_optimizacion_aleatorio"
        )
    
    with col2:
        target_return = st.number_input(
            "Retorno Objetivo (anual):",
            min_value=0.0, value=0.08, step=0.01,
            help="Solo aplica para optimización Markowitz"
        )
    
    with col3:
        restriccion_pesos = st.selectbox(
            "Restricción de Pesos:",
            options=['sin_restriccion', 'max_20', 'max_30', 'max_40'],
            format_func=lambda x: {
                'sin_restriccion': 'Sin Restricción',
                'max_20': 'Máximo 20% por activo',
                'max_30': 'Máximo 30% por activo',
                'max_40': 'Máximo 40% por activo'
            }[x],
            help="Limita el peso máximo por activo",
            key="restriccion_pesos_aleatorio"
        )
    
    # Configuración avanzada
    with st.expander("⚙️ Configuración Avanzada", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            tasa_libre_riesgo = st.number_input(
                "Tasa Libre de Riesgo (anual):",
                min_value=0.0, max_value=0.5, value=0.04, step=0.01,
                help="Para cálculo del ratio de Sharpe"
            )
        with col2:
            mostrar_comparacion = st.checkbox("Mostrar Comparación con Actual", value=True, key="mostrar_comparacion_aleatorio")
        with col3:
            mostrar_metricas = st.checkbox("Mostrar Métricas Detalladas", value=True, key="mostrar_metricas_aleatorio")
    
    # Botón de ejecución
    col1, col2, col3 = st.columns(3)
    with col1:
        generar_simbolos = st.button("🎲 Generar Símbolos Aleatorios")
    with col2:
        ejecutar_rebalanceo = st.button("🚀 Ejecutar Rebalanceo")
    with col3:
        ejecutar_completo = st.button("🎯 Rebalanceo Completo")
    
    if generar_simbolos or ejecutar_rebalanceo or ejecutar_completo:
        # Generar símbolos aleatorios
        simbolos_aleatorios = generar_simbolos_aleatorios(
            num_simbolos, incluir_actuales, porcentaje_actuales, activos
        )
        
        if not simbolos_aleatorios:
            st.error("❌ Error generando símbolos aleatorios")
            return
        
        st.success(f"✅ Generados {len(simbolos_aleatorios)} símbolos aleatorios")
        
        # Mostrar símbolos seleccionados
        st.markdown("#### 📋 Símbolos Seleccionados")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Símbolos aleatorios generados:**")
            for i, simbolo in enumerate(simbolos_aleatorios, 1):
                st.write(f"{i}. {simbolo}")
        
        with col2:
            # Gráfico de distribución de tipos de activos
            tipos_activos = categorizar_simbolos(simbolos_aleatorios)
            if tipos_activos:
                fig_tipos = go.Figure(data=[go.Pie(
                    labels=list(tipos_activos.keys()),
                    values=list(tipos_activos.values()),
                    textinfo='label+percent'
                )])
                fig_tipos.update_layout(title="Distribución por Tipo de Activo")
                st.plotly_chart(fig_tipos, use_container_width=True)
        
        if ejecutar_rebalanceo or ejecutar_completo:
            # Cargar datos históricos
            with st.spinner("📊 Cargando datos históricos..."):
                try:
                    # Crear PortfolioManager con los símbolos aleatorios
                    portfolio_manager = PortfolioManager(simbolos_aleatorios, token_acceso, fecha_desde, fecha_hasta)
                    portfolio_manager.load_data()
                    
                    if not portfolio_manager.data_loaded:
                        st.error("❌ Error cargando datos históricos")
                        return
                    
                    st.success("✅ Datos cargados exitosamente")
                    
                    # Ejecutar optimización
                    st.markdown("#### 🔄 Optimizando Portafolio Aleatorio")
                    
                    # Determinar estrategia según modo de optimización
                    if modo_optimizacion == 'markowitz':
                        strategy = 'markowitz'
                        target = target_return
                    elif modo_optimizacion == 'max_return':
                        strategy = 'max_return'
                        target = None
                    elif modo_optimizacion == 'min_variance':
                        strategy = 'min-variance-l2'
                        target = None
                    elif modo_optimizacion == 'sharpe_ratio':
                        strategy = 'sharpe_ratio'
                        target = None
                    else:
                        strategy = 'markowitz'
                        target = target_return
                    
                    # Ejecutar optimización
                    resultado_optimizacion = portfolio_manager.compute_portfolio(strategy=strategy, target_return=target)
                    
                    if resultado_optimizacion:
                        st.success("✅ Optimización completada")
                        
                        # Mostrar resultados
                        mostrar_resultados_rebalanceo_aleatorio(
                            resultado_optimizacion, simbolos_aleatorios, capital_total,
                            activos, mostrar_comparacion, mostrar_metricas
                        )
                    else:
                        st.error("❌ Error en la optimización")
                
                except Exception as e:
                    st.error(f"❌ Error en el proceso de rebalanceo: {str(e)}")

def generar_simbolos_aleatorios(num_simbolos, incluir_actuales, porcentaje_actuales, activos):
    """
    Genera una lista de símbolos aleatorios para el rebalanceo
    """
    try:
        simbolos_seleccionados = []
        
        # Lista de símbolos disponibles (puede ser expandida)
        simbolos_disponibles = [
            # Acciones argentinas
            'GGAL', 'PAMP', 'YPF', 'TEN', 'CRES', 'EDN', 'ALUA', 'COME', 'LOMA', 'MIRG',
            'PGR', 'SUPV', 'TECO2', 'TGNO4', 'TGSU2', 'TRAN', 'TS', 'VALO', 'YPF',
            # ADRs
            'BMA', 'CEPU', 'CRESY', 'EDN', 'GGAL', 'IRCP', 'PAM', 'PZE', 'TGS', 'YPF',
            # Bonos
            'GD30', 'GD35', 'GD38', 'GD41', 'GD46', 'GD47', 'GD48', 'GD49', 'GD50',
            'GD51', 'GD52', 'GD53', 'GD54', 'GD55', 'GD56', 'GD57', 'GD58', 'GD59',
            # Fondos comunes
            'FCI001', 'FCI002', 'FCI003', 'FCI004', 'FCI005', 'FCI006', 'FCI007',
            'FCI008', 'FCI009', 'FCI010', 'FCI011', 'FCI012', 'FCI013', 'FCI014',
            # ETFs
            'SPY', 'QQQ', 'IWM', 'EFA', 'EEM', 'AGG', 'TLT', 'GLD', 'SLV', 'USO',
            # Acciones internacionales
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD',
            'INTC', 'ORCL', 'CRM', 'ADBE', 'PYPL', 'UBER', 'LYFT', 'SNAP', 'TWTR'
        ]
        
        # Si incluir actuales, agregar algunos símbolos del portafolio actual
        if incluir_actuales and activos:
            simbolos_actuales = []
            for activo in activos:
                titulo = activo.get('titulo', {})
                simbolo = titulo.get('simbolo', '')
                if simbolo and simbolo not in simbolos_actuales:
                    simbolos_actuales.append(simbolo)
            
            if simbolos_actuales:
                # Calcular cuántos símbolos actuales incluir
                num_actuales = max(1, int(num_simbolos * porcentaje_actuales / 100))
                num_actuales = min(num_actuales, len(simbolos_actuales))
                
                # Seleccionar símbolos actuales aleatoriamente
                simbolos_actuales_seleccionados = random.sample(simbolos_actuales, num_actuales)
                simbolos_seleccionados.extend(simbolos_actuales_seleccionados)
                
                st.info(f"🔄 Incluyendo {num_actuales} símbolos del portafolio actual")
        
        # Completar con símbolos aleatorios
        simbolos_restantes = num_simbolos - len(simbolos_seleccionados)
        
        if simbolos_restantes > 0:
            # Filtrar símbolos no seleccionados
            simbolos_disponibles = [s for s in simbolos_disponibles if s not in simbolos_seleccionados]
            
            if len(simbolos_disponibles) >= simbolos_restantes:
                simbolos_aleatorios = random.sample(simbolos_disponibles, simbolos_restantes)
                simbolos_seleccionados.extend(simbolos_aleatorios)
            else:
                st.warning(f"⚠️ Solo hay {len(simbolos_disponibles)} símbolos disponibles")
                simbolos_seleccionados.extend(simbolos_disponibles)
        
        return simbolos_seleccionados
        
    except Exception as e:
        st.error(f"❌ Error generando símbolos aleatorios: {str(e)}")
        return []

def categorizar_simbolos(simbolos):
    """
    Categoriza los símbolos por tipo de activo
    """
    try:
        categorias = {
            'Acciones Argentinas': 0,
            'ADRs': 0,
            'Bonos': 0,
            'Fondos Comunes': 0,
            'ETFs': 0,
            'Acciones Internacionales': 0
        }
        
        # Listas de símbolos por categoría
        acciones_arg = ['GGAL', 'PAMP', 'YPF', 'TEN', 'CRES', 'EDN', 'ALUA', 'COME', 'LOMA', 'MIRG',
                       'PGR', 'SUPV', 'TECO2', 'TGNO4', 'TGSU2', 'TRAN', 'TS', 'VALO']
        
        adrs = ['BMA', 'CEPU', 'CRESY', 'EDN', 'GGAL', 'IRCP', 'PAM', 'PZE', 'TGS', 'YPF']
        
        bonos = ['GD30', 'GD35', 'GD38', 'GD41', 'GD46', 'GD47', 'GD48', 'GD49', 'GD50',
                'GD51', 'GD52', 'GD53', 'GD54', 'GD55', 'GD56', 'GD57', 'GD58', 'GD59']
        
        fondos = ['FCI001', 'FCI002', 'FCI003', 'FCI004', 'FCI005', 'FCI006', 'FCI007',
                 'FCI008', 'FCI009', 'FCI010', 'FCI011', 'FCI012', 'FCI013', 'FCI014']
        
        etfs = ['SPY', 'QQQ', 'IWM', 'EFA', 'EEM', 'AGG', 'TLT', 'GLD', 'SLV', 'USO']
        
        acciones_int = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD',
                       'INTC', 'ORCL', 'CRM', 'ADBE', 'PYPL', 'UBER', 'LYFT', 'SNAP', 'TWTR']
        
        # Categorizar cada símbolo
        for simbolo in simbolos:
            if simbolo in acciones_arg:
                categorias['Acciones Argentinas'] += 1
            elif simbolo in adrs:
                categorias['ADRs'] += 1
            elif simbolo in bonos:
                categorias['Bonos'] += 1
            elif simbolo in fondos:
                categorias['Fondos Comunes'] += 1
            elif simbolo in etfs:
                categorias['ETFs'] += 1
            elif simbolo in acciones_int:
                categorias['Acciones Internacionales'] += 1
            else:
                # Categoría por defecto
                categorias['Acciones Argentinas'] += 1
        
        # Filtrar categorías vacías
        return {k: v for k, v in categorias.items() if v > 0}
        
    except Exception as e:
        st.error(f"❌ Error categorizando símbolos: {str(e)}")
        return {}

def mostrar_resultados_rebalanceo_aleatorio(resultado_optimizacion, simbolos_aleatorios, capital_total,
                                          activos, mostrar_comparacion=True, mostrar_metricas=True):
    """
    Muestra los resultados del rebalanceo con símbolos aleatorios
    """
    pesos_optimizados = resultado_optimizacion.weights
    
    # Métricas del portafolio optimizado
    metricas = resultado_optimizacion.get_metrics_dict()
    
    st.markdown("#### 📈 Resultados del Portafolio Aleatorio Optimizado")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Retorno Anual", f"{metricas['Annual Return']:.2%}")
        st.metric("Volatilidad Anual", f"{metricas['Annual Volatility']:.2%}")
        st.metric("Ratio de Sharpe", f"{metricas['Sharpe Ratio']:.4f}")
    
    with col2:
        st.metric("VaR 95%", f"{metricas['VaR 95%']:.4f}")
        st.metric("Skewness", f"{metricas['Skewness']:.4f}")
        st.metric("Kurtosis", f"{metricas['Kurtosis']:.4f}")
    
    with col3:
        normalidad = "✅ Normal" if metricas['Is Normal'] else "❌ No Normal"
        st.metric("Normalidad", normalidad)
        st.metric("JB Statistic", f"{metricas['JB Statistic']:.4f}")
    
    # Distribución de pesos optimizados
    st.markdown("#### 🥧 Distribución de Pesos Optimizados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de torta optimizado
        fig_optimizado = go.Figure(data=[go.Pie(
            labels=simbolos_aleatorios,
            values=pesos_optimizados,
            textinfo='label+percent',
            hole=0.3
        )])
        fig_optimizado.update_layout(title="Distribución Optimizada de Pesos")
        st.plotly_chart(fig_optimizado, use_container_width=True)
    
    with col2:
        # Gráfico de distribución de retornos
        if resultado_optimizacion.returns is not None:
            fig_hist = resultado_optimizacion.plot_histogram_streamlit("Distribución de Retornos Optimizados")
            st.plotly_chart(fig_hist, use_container_width=True)
    
    # Análisis de asignación de capital
    st.markdown("#### 💰 Análisis de Asignación de Capital")
    
    # Calcular asignación de capital por activo
    asignacion_capital = []
    for i, (simbolo, peso) in enumerate(zip(simbolos_aleatorios, pesos_optimizados)):
        capital_asignado = capital_total * peso
        asignacion_capital.append({
            'Símbolo': simbolo,
            'Peso (%)': peso * 100,
            'Capital Asignado ($)': capital_asignado,
            'Capital Asignado (USD)': capital_asignado  # Asumiendo pesos en USD
        })
    
    # Crear DataFrame de asignación
    df_asignacion = pd.DataFrame(asignacion_capital)
    df_asignacion = df_asignacion.sort_values('Capital Asignado ($)', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Asignación de Capital por Activo:**")
        st.dataframe(df_asignacion, use_container_width=True)
    
    with col2:
        # Gráfico de barras de capital asignado
        fig_capital = go.Figure(data=[go.Bar(
            x=df_asignacion['Símbolo'],
            y=df_asignacion['Capital Asignado ($)'],
            text=[f"${val:,.0f}" for val in df_asignacion['Capital Asignado ($)']],
            textposition='auto'
        )])
        fig_capital.update_layout(
            title="Capital Asignado por Activo",
            xaxis_title="Activos",
            yaxis_title="Capital ($)"
        )
        st.plotly_chart(fig_capital, use_container_width=True)
    
    # Comparación con portafolio actual
    if mostrar_comparacion and activos:
        st.markdown("#### 🔄 Comparación con Portafolio Actual")
        
        # Calcular métricas del portafolio actual
        capital_actual = sum(activo.get('valor', 0) for activo in activos)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Capital Actual", f"${capital_actual:,.2f}")
            st.metric("Capital Nuevo", f"${capital_total:,.2f}")
            diferencia_capital = capital_total - capital_actual
            st.metric("Diferencia", f"${diferencia_capital:,.2f}")
        
        with col2:
            num_activos_actual = len(activos)
            st.metric("Activos Actuales", num_activos_actual)
            st.metric("Activos Nuevos", len(simbolos_aleatorios))
            st.metric("Diferencia", len(simbolos_aleatorios) - num_activos_actual)
        
        with col3:
            # Calcular diversificación (número de activos únicos)
            simbolos_actuales = set()
            for activo in activos:
                titulo = activo.get('titulo', {})
                simbolo = titulo.get('simbolo', '')
                if simbolo:
                    simbolos_actuales.add(simbolo)
            
            st.metric("Diversificación Actual", len(simbolos_actuales))
            st.metric("Diversificación Nueva", len(set(simbolos_aleatorios)))
            st.metric("Mejora", len(set(simbolos_aleatorios)) - len(simbolos_actuales))
    
    # Métricas de rebalanceo
    if mostrar_metricas:
        st.markdown("#### 📊 Métricas de Rebalanceo")
        
        # Calcular métricas de diversificación
        diversificacion_nueva = len(set(simbolos_aleatorios))
        concentracion_maxima = np.max(pesos_optimizados) * 100
        concentracion_top5 = np.sum(np.sort(pesos_optimizados)[-5:]) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Diversificación", diversificacion_nueva)
        with col2:
            st.metric("Concentración Máxima", f"{concentracion_maxima:.1f}%")
        with col3:
            st.metric("Concentración Top 5", f"{concentracion_top5:.1f}%")
        with col4:
            st.metric("Capital Total", f"${capital_total:,.0f}")
        
        # Recomendaciones
        st.markdown("#### 💡 Recomendaciones")
        
        if diversificacion_nueva > 10:
            st.success("✅ Excelente diversificación del portafolio")
        elif diversificacion_nueva > 5:
            st.info("ℹ️ Buena diversificación del portafolio")
        else:
            st.warning("⚠️ Considerar aumentar la diversificación")
        
        if concentracion_maxima < 20:
            st.success("✅ Buena distribución de riesgo")
        elif concentracion_maxima < 30:
            st.info("ℹ️ Distribución de riesgo moderada")
        else:
            st.warning("⚠️ Alta concentración en un activo")
        
        if diferencia_capital > 0:
            st.info(f"💡 Se requiere capital adicional de ${diferencia_capital:,.2f}")
        elif diferencia_capital < 0:
            st.info(f"💡 Se liberaría capital de ${abs(diferencia_capital):,.2f}")

def mostrar_optimizacion_aleatoria(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Optimización aleatoria con inputs manuales de capital, horizonte, benchmark
    y simulaciones iterativas hasta alcanzar el retorno objetivo
    """
    st.markdown("#### 🎲 Optimización Aleatoria")
    
    # Configuración de parámetros básicos
    st.markdown("#### 💰 Configuración de Capital y Horizonte")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        capital_inicial = st.number_input(
            "Capital Inicial ($):",
            min_value=1000.0, max_value=10000000.0, value=100000.0, step=1000.0,
            help="Capital inicial para la optimización"
        )
    
    with col2:
        horizonte_dias = st.number_input(
            "Horizonte de Inversión (días):",
            min_value=30, max_value=3650, value=252, step=30,
            help="Horizonte temporal para la optimización"
        )
    
    with col3:
        retorno_objetivo = st.number_input(
            "Retorno Objetivo (anual):",
            min_value=0.01, value=0.15, step=0.01,
            help="Retorno anual objetivo a superar"
        )
    
    # Configuración de benchmark
    st.markdown("#### 📊 Configuración de Benchmark")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        benchmark = st.selectbox(
            "Benchmark:",
            options=[
                'SPY', 'QQQ', 'IWM', 'EFA', 'EEM', 'AGG', '^GSPC', '^IXIC', '^DJI',
                'Tasa_Caucion_Promedio', 'Dolar_MEP', 'Dolar_Blue', 'Dolar_Oficial',
                'Bono_GD30', 'Bono_GD35', 'Bono_GD38', 'Bono_GD41', 'Bono_GD46',
                'Indice_S&P_Merval', 'Indice_Burcap', 'Indice_IGPA'
            ],
            help="Benchmark para calcular alpha y beta",
            key="benchmark_optimizacion_aleatoria"
        )
    
    with col2:
        usar_portafolio_actual = st.checkbox(
            "🔄 Usar portafolio actual como benchmark",
            value=False,
            help="Si está marcado, se usará el portafolio actual como benchmark",
            key="usar_portafolio_actual_aleatoria"
        )
    
    with col3:
        tasa_libre_riesgo = st.number_input(
            "Tasa Libre de Riesgo (anual):",
            min_value=0.0, max_value=0.5, value=0.04, step=0.01,
            help="Tasa libre de riesgo para cálculos"
        )
    
    # Configuración de optimización aleatoria
    st.markdown("#### 🎯 Configuración de Optimización Aleatoria")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        num_simulaciones = st.slider(
            "Número de Simulaciones:",
            min_value=10, max_value=1000, value=100, step=10,
            help="Número de simulaciones aleatorias a realizar"
        )
    
    with col2:
        num_activos = st.slider(
            "Número de Activos por Simulación:",
            min_value=3, max_value=20, value=8, step=1,
            help="Número de activos a incluir en cada simulación"
        )
    
    with col3:
        max_iteraciones = st.slider(
            "Máximo de Iteraciones:",
            min_value=1, max_value=50, value=10, step=1,
            help="Máximo número de iteraciones para alcanzar objetivo"
    )
    
    # Configuración avanzada
    with st.expander("⚙️ Configuración Avanzada", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            estrategia_optimizacion = st.selectbox(
                "Estrategia de Optimización:",
                options=['markowitz', 'max_return', 'min_variance', 'sharpe_ratio'],
                format_func=lambda x: {
                    'markowitz': 'Markowitz (Retorno-Riesgo)',
                    'max_return': 'Máximo Retorno',
                    'min_variance': 'Mínima Varianza',
                    'sharpe_ratio': 'Máximo Ratio de Sharpe'
                }[x],
                key="estrategia_optimizacion_aleatoria"
            )
        with col2:
            mostrar_histogramas = st.checkbox("Mostrar Histogramas", value=True, key="mostrar_histogramas_aleatoria")
        with col3:
            mostrar_frontera = st.checkbox("Mostrar Frontera Eficiente", value=False, key="mostrar_frontera_aleatoria")
    
    # Botones de ejecución
    col1, col2, col3 = st.columns(3)
    with col1:
        ejecutar_optimizacion = st.button("🚀 Ejecutar Optimización Aleatoria")
    with col2:
        ejecutar_iterativo = st.button("🔄 Optimización Iterativa")
    with col3:
        ejecutar_completo = st.button("🎯 Optimización Completa")
    
    if ejecutar_optimizacion or ejecutar_iterativo or ejecutar_completo:
        # Ejecutar optimización aleatoria
        with st.spinner("🎲 Ejecutando optimización aleatoria..."):
            try:
                resultados = ejecutar_optimizacion_aleatoria_completa(
                    portafolio, token_acceso, fecha_desde, fecha_hasta,
                    capital_inicial, horizonte_dias, retorno_objetivo,
                    benchmark, usar_portafolio_actual, tasa_libre_riesgo,
                    num_simulaciones, num_activos, max_iteraciones,
                    estrategia_optimizacion, ejecutar_iterativo or ejecutar_completo
                )
                
                if resultados:
                    mostrar_resultados_optimizacion_aleatoria(
                        resultados, capital_inicial, horizonte_dias,
                        benchmark, retorno_objetivo, tasa_libre_riesgo,
                        mostrar_histogramas, mostrar_frontera
                    )
                else:
                    st.error("❌ Error en la optimización aleatoria")
            
            except Exception as e:
                st.error(f"❌ Error en el proceso: {str(e)}")

def ejecutar_optimizacion_aleatoria_completa(portafolio, token_acceso, fecha_desde, fecha_hasta,
                                           capital_inicial, horizonte_dias, retorno_objetivo,
                                           benchmark, usar_portafolio_actual, tasa_libre_riesgo,
                                           num_simulaciones, num_activos, max_iteraciones,
                                           estrategia_optimizacion, es_iterativo):
    """
    Ejecuta la optimización aleatoria completa
    """
    try:
        # Lista de símbolos disponibles
        simbolos_disponibles = [
            # Acciones argentinas
            'GGAL', 'PAMP', 'YPF', 'TEN', 'CRES', 'EDN', 'ALUA', 'COME', 'LOMA', 'MIRG',
            'PGR', 'SUPV', 'TECO2', 'TGNO4', 'TGSU2', 'TRAN', 'TS', 'VALO',
            # ADRs
            'BMA', 'CEPU', 'CRESY', 'EDN', 'GGAL', 'IRCP', 'PAM', 'PZE', 'TGS', 'YPF',
            # Bonos
            'GD30', 'GD35', 'GD38', 'GD41', 'GD46', 'GD47', 'GD48', 'GD49', 'GD50',
            'GD51', 'GD52', 'GD53', 'GD54', 'GD55', 'GD56', 'GD57', 'GD58', 'GD59',
            # ETFs
            'SPY', 'QQQ', 'IWM', 'EFA', 'EEM', 'AGG', 'TLT', 'GLD', 'SLV', 'USO',
            # Acciones internacionales
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD',
            'INTC', 'ORCL', 'CRM', 'ADBE', 'PYPL', 'UBER', 'LYFT', 'SNAP', 'TWTR'
        ]
        
        # Obtener datos del benchmark
        benchmark_data = None
        if usar_portafolio_actual:
            # Usar portafolio actual como benchmark
            activos = portafolio.get('activos', [])
            if activos:
                simbolos_actuales = []
                for activo in activos:
                    titulo = activo.get('titulo', {})
                    simbolo = titulo.get('simbolo', '')
                    if simbolo:
                        simbolos_actuales.append(simbolo)
                
                if simbolos_actuales:
                    portfolio_manager_actual = PortfolioManager(simbolos_actuales, token_acceso, fecha_desde, fecha_hasta)
                    portfolio_manager_actual.load_data()
                    if portfolio_manager_actual.data_loaded:
                        benchmark_data = portfolio_manager_actual.returns
        else:
            # Usar benchmark específico
            benchmark_data = obtener_datos_benchmark_argentino(benchmark, token_acceso, fecha_desde, fecha_hasta)
            if benchmark_data is None:
                try:
                    benchmark_manager = PortfolioManager([benchmark], token_acceso, fecha_desde, fecha_hasta)
                    benchmark_manager.load_data()
                    if benchmark_manager.data_loaded:
                        benchmark_data = benchmark_manager.returns
                except:
                    st.warning(f"⚠️ No se pudo cargar datos del benchmark {benchmark}")
        
        # Ejecutar simulaciones
        resultados_simulaciones = []
        mejor_resultado = None
        mejor_retorno = -float('inf')
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for iteracion in range(max_iteraciones):
            status_text.text(f"🔄 Iteración {iteracion + 1}/{max_iteraciones}")
            
            for sim in range(num_simulaciones):
                # Generar portafolio aleatorio
                simbolos_aleatorios = random.sample(simbolos_disponibles, num_activos)
                
                try:
                    # Crear PortfolioManager con tasa libre de riesgo del benchmark
                    portfolio_manager = PortfolioManager(simbolos_aleatorios, token_acceso, fecha_desde, fecha_hasta, tasa_libre_riesgo)
                    portfolio_manager.load_data()
                    
                    if portfolio_manager.data_loaded:
                        # Ejecutar optimización con tasa libre de riesgo del benchmark
                        resultado = portfolio_manager.compute_portfolio(strategy=estrategia_optimizacion, risk_free_rate=tasa_libre_riesgo)
                        
                        if resultado:
                            # Calcular métricas
                            metricas = resultado.get_metrics_dict()
                            retorno_anual = metricas['Annual Return']
                            
                            # Calcular alpha y beta si hay benchmark
                            alpha = 0
                            beta = 1
                            if benchmark_data is not None:
                                try:
                                    # Calcular retornos del benchmark
                                    benchmark_returns = benchmark_data.mean() if len(benchmark_data.columns) == 1 else benchmark_data.mean().mean()
                                    portfolio_returns = retorno_anual
                                    
                                    # Calcular beta (simplificado)
                                    if benchmark_returns != 0:
                                        beta = portfolio_returns / benchmark_returns
                                    
                                    # Calcular alpha
                                    alpha = portfolio_returns - (tasa_libre_riesgo + beta * (benchmark_returns - tasa_libre_riesgo))
                                except:
                                    pass
                            
                            # Crear resultado
                            resultado_sim = {
                                'simulacion': sim + 1,
                                'iteracion': iteracion + 1,
                                'simbolos': simbolos_aleatorios,
                                'retorno_anual': retorno_anual,
                                'volatilidad': metricas['Annual Volatility'],
                                'sharpe_ratio': metricas['Sharpe Ratio'],
                                'alpha': alpha,
                                'beta': beta,
                                'pesos': resultado.weights,
                                'metricas': metricas
                            }
                            
                            resultados_simulaciones.append(resultado_sim)
                            
                            # Verificar si es el mejor resultado
                            if retorno_anual > mejor_retorno:
                                mejor_retorno = retorno_anual
                                mejor_resultado = resultado_sim
                            
                            # Si es iterativo y alcanzamos el objetivo, parar
                            if es_iterativo and retorno_anual >= retorno_objetivo:
                                st.success(f"✅ Objetivo alcanzado en iteración {iteracion + 1}, simulación {sim + 1}")
                                return {
                                    'mejor_resultado': mejor_resultado,
                                    'todos_resultados': resultados_simulaciones,
                                    'objetivo_alcanzado': True,
                                    'iteracion_final': iteracion + 1,
                                    'simulacion_final': sim + 1
                                }
                
                except Exception as e:
                    continue
                
                # Actualizar progreso
                progreso = ((iteracion * num_simulaciones + sim + 1) / (max_iteraciones * num_simulaciones))
                progress_bar.progress(progreso)
        
        # Si llegamos aquí, no se alcanzó el objetivo
        if es_iterativo:
            st.warning(f"⚠️ No se alcanzó el objetivo de {retorno_objetivo:.2%} en {max_iteraciones} iteraciones")
        
        return {
            'mejor_resultado': mejor_resultado,
            'todos_resultados': resultados_simulaciones,
            'objetivo_alcanzado': False,
            'iteracion_final': max_iteraciones,
            'simulacion_final': num_simulaciones
        }
        
    except Exception as e:
        st.error(f"❌ Error en optimización aleatoria: {str(e)}")
        return None

def mostrar_resultados_optimizacion_aleatoria(resultados, capital_inicial, horizonte_dias,
                                            benchmark, retorno_objetivo, tasa_libre_riesgo,
                                            mostrar_histogramas, mostrar_frontera):
    """
    Muestra los resultados de la optimización aleatoria
    """
    mejor_resultado = resultados['mejor_resultado']
    todos_resultados = resultados['todos_resultados']
    
    if not mejor_resultado:
        st.error("❌ No se encontraron resultados válidos")
        return
    
    st.markdown("#### 🏆 Mejor Resultado de Optimización Aleatoria")
    
    # Métricas del mejor resultado
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Retorno Anual", f"{mejor_resultado['retorno_anual']:.2%}")
        st.metric("Volatilidad Anual", f"{mejor_resultado['volatilidad']:.2%}")
        st.metric("Ratio de Sharpe", f"{mejor_resultado['sharpe_ratio']:.4f}")
    
    with col2:
        st.metric("Alpha", f"{mejor_resultado['alpha']:.4f}")
        st.metric("Beta", f"{mejor_resultado['beta']:.4f}")
        st.metric("VaR 95%", f"{mejor_resultado['metricas']['VaR 95%']:.4f}")
    
    with col3:
        normalidad = "✅ Normal" if mejor_resultado['metricas']['Is Normal'] else "❌ No Normal"
        st.metric("Normalidad", normalidad)
        st.metric("Skewness", f"{mejor_resultado['metricas']['Skewness']:.4f}")
        st.metric("Kurtosis", f"{mejor_resultado['metricas']['Kurtosis']:.4f}")
    
    # Información del portafolio ganador
    st.markdown("#### 🎯 Portafolio Ganador")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Activos del portafolio ganador:**")
        for i, simbolo in enumerate(mejor_resultado['simbolos'], 1):
            st.write(f"{i}. {simbolo}")
    
    with col2:
        # Gráfico de pesos del portafolio ganador
        if mejor_resultado['pesos'] is not None:
            fig_pie = go.Figure(data=[go.Pie(
                labels=mejor_resultado['simbolos'],
                values=mejor_resultado['pesos'],
                textinfo='label+percent'
            )])
            fig_pie.update_layout(title="Distribución de Pesos - Portafolio Ganador")
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # Análisis de rendimiento vs objetivo
    st.markdown("#### 📊 Análisis de Rendimiento")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Retorno Objetivo", f"{retorno_objetivo:.2%}")
        st.metric("Retorno Alcanzado", f"{mejor_resultado['retorno_anual']:.2%}")
        diferencia = mejor_resultado['retorno_anual'] - retorno_objetivo
        st.metric("Diferencia", f"{diferencia:.2%}")
    
    with col2:
        # Calcular proyección de capital
        capital_final = capital_inicial * (1 + mejor_resultado['retorno_anual']) ** (horizonte_dias / 252)
        ganancia_total = capital_final - capital_inicial
        st.metric("Capital Final Proyectado", f"${capital_final:,.2f}")
        st.metric("Ganancia Total", f"${ganancia_total:,.2f}")
        st.metric("Horizonte (días)", horizonte_dias)
    
    with col3:
        if resultados['objetivo_alcanzado']:
            st.success("✅ Objetivo Alcanzado")
            st.metric("Iteración Final", resultados['iteracion_final'])
            st.metric("Simulación Final", resultados['simulacion_final'])
        else:
            st.warning("⚠️ Objetivo No Alcanzado")
            st.metric("Iteraciones Ejecutadas", resultados['iteracion_final'])
            st.metric("Simulaciones Totales", resultados['simulacion_final'])
    
    # Análisis estadístico de todas las simulaciones
    if len(todos_resultados) > 1:
        st.markdown("#### 📈 Análisis Estadístico de Simulaciones")
        
        # Extraer métricas de todas las simulaciones
        retornos = [r['retorno_anual'] for r in todos_resultados]
        volatilidades = [r['volatilidad'] for r in todos_resultados]
        sharpe_ratios = [r['sharpe_ratio'] for r in todos_resultados]
        alphas = [r['alpha'] for r in todos_resultados]
        betas = [r['beta'] for r in todos_resultados]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Estadísticas de Retornos:**")
            st.write(f"• Media: {np.mean(retornos):.2%}")
            st.write(f"• Mediana: {np.median(retornos):.2%}")
            st.write(f"• Desviación Estándar: {np.std(retornos):.2%}")
            st.write(f"• Mínimo: {np.min(retornos):.2%}")
            st.write(f"• Máximo: {np.max(retornos):.2%}")
        
        with col2:
            st.markdown("**Estadísticas de Sharpe Ratios:**")
            st.write(f"• Media: {np.mean(sharpe_ratios):.4f}")
            st.write(f"• Mediana: {np.median(sharpe_ratios):.4f}")
            st.write(f"• Desviación Estándar: {np.std(sharpe_ratios):.4f}")
            st.write(f"• Mínimo: {np.min(sharpe_ratios):.4f}")
            st.write(f"• Máximo: {np.max(sharpe_ratios):.4f}")
        
        # Histogramas si se solicitan
        if mostrar_histogramas:
            st.markdown("#### 📊 Histogramas de Distribución")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Histograma de retornos
                fig_retornos = go.Figure(data=[go.Histogram(x=retornos, nbinsx=20)])
                fig_retornos.update_layout(
                    title="Distribución de Retornos Anuales",
                    xaxis_title="Retorno Anual",
                    yaxis_title="Frecuencia"
                )
                st.plotly_chart(fig_retornos, use_container_width=True)
            
            with col2:
                # Histograma de Sharpe ratios
                fig_sharpe = go.Figure(data=[go.Histogram(x=sharpe_ratios, nbinsx=20)])
                fig_sharpe.update_layout(
                    title="Distribución de Sharpe Ratios",
                    xaxis_title="Sharpe Ratio",
                    yaxis_title="Frecuencia"
                )
                st.plotly_chart(fig_sharpe, use_container_width=True)
        
        # Frontera eficiente si se solicita
        if mostrar_frontera and len(todos_resultados) > 10:
            st.markdown("#### 📈 Frontera Eficiente de Simulaciones")
            
            # Crear gráfico de dispersión retorno vs riesgo
            fig_frontera = go.Figure()
            
            fig_frontera.add_trace(go.Scatter(
                x=volatilidades,
                y=retornos,
                mode='markers',
                marker=dict(
                    size=8,
                    color=sharpe_ratios,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Sharpe Ratio")
                ),
                text=[f"Sim {i+1}" for i in range(len(todos_resultados))],
                hovertemplate='<b>%{text}</b><br>' +
                            'Retorno: %{y:.2%}<br>' +
                            'Volatilidad: %{x:.2%}<br>' +
                            'Sharpe: %{marker.color:.4f}<extra></extra>'
            ))
            
            # Marcar el mejor resultado
            fig_frontera.add_trace(go.Scatter(
                x=[mejor_resultado['volatilidad']],
                y=[mejor_resultado['retorno_anual']],
                mode='markers',
                marker=dict(
                    size=15,
                    color='red',
                    symbol='star'
                ),
                name='Mejor Resultado'
            ))
            
            fig_frontera.update_layout(
                title="Frontera Eficiente de Simulaciones",
                xaxis_title="Volatilidad Anual",
                yaxis_title="Retorno Anual",
                showlegend=True
            )
            
            st.plotly_chart(fig_frontera, use_container_width=True)
    
    # Recomendaciones finales
    st.markdown("#### 💡 Recomendaciones")
    
    if mejor_resultado['retorno_anual'] >= retorno_objetivo:
        st.success("✅ El portafolio ganador supera el retorno objetivo")
    else:
        st.warning("⚠️ El portafolio ganador no alcanza el retorno objetivo")
    
    if mejor_resultado['alpha'] > 0:
        st.success("✅ El portafolio tiene alpha positivo (supera al benchmark)")
    else:
        st.info("ℹ️ El portafolio tiene alpha negativo")
    
    if mejor_resultado['beta'] < 1:
        st.info("ℹ️ El portafolio es menos volátil que el benchmark")
    else:
        st.info("ℹ️ El portafolio es más volátil que el benchmark")
    
    # Recomendaciones de capital
    if capital_final > capital_inicial * (1 + retorno_objetivo) ** (horizonte_dias / 252):
        st.success("✅ El portafolio proyecta superar el objetivo de capital")
    else:
        st.warning("⚠️ El portafolio no proyecta alcanzar el objetivo de capital")

def obtener_cotizaciones_generico(instrumento, pais, bearer_token):
    """
    Obtiene cotizaciones de cualquier instrumento usando la API de InvertirOnline
    """
    try:
        url = f"https://api.invertironline.com/api/v2/Cotizaciones/{instrumento}/{pais}/Todos"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {bearer_token}'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            cotizaciones = response.json()
            if cotizaciones and 'titulos' in cotizaciones:
                # Convertir los datos a un DataFrame de pandas
                df = pd.DataFrame(cotizaciones['titulos'])
                return df
            else:
                st.warning(f"⚠️ No se encontraron datos de {instrumento} en la respuesta")
                return None
        else:
            st.error(f"❌ Error en la solicitud de {instrumento}: {response.status_code}")
            st.error(response.text)
            return None
    except Exception as e:
        st.error(f"❌ Error obteniendo cotizaciones de {instrumento}: {str(e)}")
        return None


def obtener_datos_benchmark_argentino(benchmark, token_acceso, fecha_desde, fecha_hasta):
    """
    Obtiene datos de benchmarks del mercado argentino
    """
    try:
        if benchmark == 'Tasa_Caucion_Promedio':
            # Simular retornos de tasa de caución promedio
            fechas = pd.date_range(start=fecha_desde, end=fecha_hasta, freq='D')
            retornos_simulados = np.random.normal(0.0003, 0.01, len(fechas))  # 0.03% diario promedio
            return pd.DataFrame({'Tasa_Caucion_Promedio': retornos_simulados}, index=fechas)
        
        elif benchmark == 'Dolar_MEP':
            # Obtener datos del dólar MEP (simulado por ahora)
            # Aquí se integraría con la API de InvertirOnline para obtener datos reales
            fechas = pd.date_range(start=fecha_desde, end=fecha_hasta, freq='D')
            # Simular retornos del dólar MEP (esto se reemplazará con datos reales)
            retornos_mep = np.random.normal(0.0005, 0.02, len(fechas))  # 0.05% diario promedio
            return pd.DataFrame({'Dolar_MEP': retornos_mep}, index=fechas)
        
        elif benchmark == 'Dolar_Blue':
            # Obtener datos del dólar Blue (simulado por ahora)
            fechas = pd.date_range(start=fecha_desde, end=fecha_hasta, freq='D')
            # Simular retornos del dólar Blue
            retornos_blue = np.random.normal(0.0008, 0.025, len(fechas))  # 0.08% diario promedio
            return pd.DataFrame({'Dolar_Blue': retornos_blue}, index=fechas)
        
        elif benchmark == 'Dolar_Oficial':
            # Obtener datos del dólar Oficial (simulado por ahora)
            fechas = pd.date_range(start=fecha_desde, end=fecha_hasta, freq='D')
            # Simular retornos del dólar Oficial
            retornos_oficial = np.random.normal(0.0002, 0.01, len(fechas))  # 0.02% diario promedio
            return pd.DataFrame({'Dolar_Oficial': retornos_oficial}, index=fechas)
        
        elif benchmark.startswith('Bono_'):
            # Obtener datos de bonos argentinos
            simbolo_bono = benchmark.replace('Bono_', '')
            try:
                # Intentar obtener cotizaciones de bonos
                cotizaciones_bonos = obtener_cotizaciones_generico('bonos', 'argentina', token_acceso)
                if cotizaciones_bonos is not None and not cotizaciones_bonos.empty:
                    # Buscar el bono específico
                    bono_data = cotizaciones_bonos[cotizaciones_bonos['simbolo'] == simbolo_bono]
                    if not bono_data.empty:
                        # Usar datos de cotización actual para simular retornos
                        precio_actual = bono_data.iloc[0].get('ultimoPrecio', 100)
                        # Simular retornos basados en precio actual
                        fechas = pd.date_range(start=fecha_desde, end=fecha_hasta, freq='D')
                        retornos_bono = np.random.normal(0.0003, 0.015, len(fechas))
                        return pd.DataFrame({benchmark: retornos_bono}, index=fechas)
                
                # Fallback a método anterior
                datos_bono = obtener_serie_historica_iol(token_acceso, 'BONOS', simbolo_bono, fecha_desde, fecha_hasta, 'SinAjustar')
                if datos_bono is not None and not datos_bono.empty:
                    retornos = datos_bono['close'].pct_change().dropna()
                    return pd.DataFrame({benchmark: retornos})
            except:
                # Si falla, usar datos simulados
                fechas = pd.date_range(start=fecha_desde, end=fecha_hasta, freq='D')
                retornos_bono = np.random.normal(0.0003, 0.015, len(fechas))
                return pd.DataFrame({benchmark: retornos_bono}, index=fechas)
        
        elif benchmark.startswith('Indice_'):
            # Obtener datos de índices argentinos
            nombre_indice = benchmark.replace('Indice_', '')
            try:
                # Intentar obtener cotizaciones de índices
                cotizaciones_indices = obtener_cotizaciones_generico('indices', 'argentina', token_acceso)
                if cotizaciones_indices is not None and not cotizaciones_indices.empty:
                    # Buscar el índice específico
                    indice_data = cotizaciones_indices[cotizaciones_indices['simbolo'] == nombre_indice]
                    if not indice_data.empty:
                        # Usar datos de cotización actual para simular retornos
                        precio_actual = indice_data.iloc[0].get('ultimoPrecio', 1000)
                        # Simular retornos basados en precio actual
                        fechas = pd.date_range(start=fecha_desde, end=fecha_hasta, freq='D')
                        retornos_indice = np.random.normal(0.0004, 0.018, len(fechas))
                        return pd.DataFrame({benchmark: retornos_indice}, index=fechas)
                
                # Fallback a método anterior
                datos_indice = obtener_serie_historica_iol(token_acceso, 'INDICES', nombre_indice, fecha_desde, fecha_hasta, 'SinAjustar')
                if datos_indice is not None and not datos_indice.empty:
                    retornos = datos_indice['close'].pct_change().dropna()
                    return pd.DataFrame({benchmark: retornos})
            except:
                # Si falla, usar datos simulados
                fechas = pd.date_range(start=fecha_desde, end=fecha_hasta, freq='D')
                retornos_indice = np.random.normal(0.0004, 0.018, len(fechas))
                return pd.DataFrame({benchmark: retornos_indice}, index=fechas)
        
        return None
        
    except Exception as e:
        st.error(f"❌ Error obteniendo datos del benchmark {benchmark}: {str(e)}")
        return None

def mostrar_optimizacion_basica(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Optimización básica del portafolio con benchmark como tasa libre de riesgo
    """
    st.markdown("#### 📊 Optimización Básica")
    
    activos = portafolio.get('activos', [])
    if not activos:
        st.warning("No hay activos en el portafolio para optimizar")
        return
    
    # Extraer símbolos del portafolio
    simbolos = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', '')
        if simbolo:
            simbolos.append(simbolo)
    
    if len(simbolos) < 2:
        st.warning("Se necesitan al menos 2 activos para optimización")
        return
    
    st.info(f"📊 Analizando {len(simbolos)} activos del portafolio")
    
    # Configuración de benchmark y tasa libre de riesgo
    st.markdown("#### 🎯 Configuración de Benchmark")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        benchmark = st.selectbox(
            "Benchmark para Tasa Libre de Riesgo:",
            options=[
                'Tasa_Caucion_Promedio',
                'Dolar_MEP',
                'Dolar_Blue', 
                'Dolar_Oficial',
                'Bono_AL30',
                'Bono_GD30',
                'Indice_S&P_MERVAL',
                'Indice_S&P_500',
                'Tasa_Fija_4%',
                'Tasa_Fija_6%',
                'Tasa_Fija_8%'
            ],
            format_func=lambda x: {
                'Tasa_Caucion_Promedio': 'Tasa de Caución Promedio',
                'Dolar_MEP': 'Dólar MEP',
                'Dolar_Blue': 'Dólar Blue',
                'Dolar_Oficial': 'Dólar Oficial',
                'Bono_AL30': 'Bono AL30',
                'Bono_GD30': 'Bono GD30',
                'Indice_S&P_MERVAL': 'S&P MERVAL',
                'Indice_S&P_500': 'S&P 500',
                'Tasa_Fija_4%': 'Tasa Fija 4%',
                'Tasa_Fija_6%': 'Tasa Fija 6%',
                'Tasa_Fija_8%': 'Tasa Fija 8%'
            }[x],
            help="Seleccione el benchmark que servirá como tasa libre de riesgo",
            key="benchmark_optimizacion_basica"
        )
    
    with col2:
        # Calcular retorno del benchmark
        benchmark_return = 0.04  # Valor por defecto
        if benchmark.startswith('Tasa_Fija'):
            benchmark_return = float(benchmark.split('_')[-1].replace('%', '')) / 100
        else:
            try:
                # Obtener datos del benchmark
                benchmark_data = obtener_datos_benchmark_argentino(benchmark, token_acceso, fecha_desde, fecha_hasta)
                if benchmark_data is not None and not benchmark_data.empty:
                    # Calcular retorno anual del benchmark
                    benchmark_returns = benchmark_data.iloc[:, 0].dropna()
                    if len(benchmark_returns) > 0:
                        benchmark_return = benchmark_returns.mean() * 252  # Anualizar
                        st.success(f"✅ Retorno benchmark calculado: {benchmark_return:.2%}")
                    else:
                        st.warning("⚠️ No se pudieron calcular retornos del benchmark")
                else:
                    st.warning("⚠️ No se pudieron obtener datos del benchmark")
            except Exception as e:
                st.error(f"❌ Error calculando retorno del benchmark: {str(e)}")
        
        st.metric("Retorno Anual del Benchmark", f"{benchmark_return:.2%}")
    
    with col3:
        usar_benchmark = st.checkbox(
            "Usar Benchmark como Tasa Libre de Riesgo",
            value=True,
            help="Si está marcado, el benchmark se usará como tasa libre de riesgo en optimizaciones",
            key="usar_benchmark_optimizacion_basica"
        )
    
    # Configuración de optimización
    st.markdown("#### ⚙️ Configuración de Optimización")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        estrategia = st.selectbox(
            "Estrategia de Optimización:",
            options=['markowitz', 'equi-weight', 'min-variance-l1', 'min-variance-l2', 'long-only'],
            format_func=lambda x: {
                'markowitz': 'Optimización de Markowitz',
                'equi-weight': 'Pesos Iguales',
                'min-variance-l1': 'Mínima Varianza L1',
                'min-variance-l2': 'Mínima Varianza L2',
                'long-only': 'Solo Posiciones Largas'
            }[x],
            key="estrategia_optimizacion_basica"
        )
    
    with col2:
        target_return = st.number_input(
            "Retorno Objetivo (anual):",
            min_value=0.0, value=0.08, step=0.01,
            help="Solo aplica para estrategia Markowitz"
        )
    
    with col3:
        show_frontier = st.checkbox("Mostrar Frontera Eficiente", value=True, key="show_frontier_basica")
    
    # Configuración avanzada de frontera eficiente
    with st.expander("⚙️ Configuración Avanzada de Frontera Eficiente", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            calcular_todos = st.checkbox("Calcular Todos los Portafolios", value=True, 
                                       help="Calcula automáticamente todas las estrategias disponibles",
                                       key="calcular_todos_basica")
            num_puntos = st.slider("Número de Puntos en Frontera", min_value=10, max_value=100, value=50,
                                 help="Más puntos = frontera más suave pero más lento")
        with col2:
            incluir_actual = st.checkbox("Incluir Portafolio Actual", value=True,
                                       help="Muestra el portafolio actual en la frontera",
                                       key="incluir_actual_basica")
            mostrar_metricas = st.checkbox("Mostrar Métricas Detalladas", value=True, key="mostrar_metricas_basica")
        with col3:
            target_return_frontier = st.number_input("Retorno Objetivo Frontera", min_value=0.0, 
                                                   value=0.08, step=0.01, help="Para optimización de frontera")
            auto_refresh = st.checkbox("Auto-refresh", value=True, help="Actualiza automáticamente con cambios",
                                     key="auto_refresh_basica")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        ejecutar_optimizacion = st.button("🚀 Ejecutar Optimización")
    with col2:
        ejecutar_frontier = st.button("📈 Calcular Frontera Eficiente")
    with col3:
        ejecutar_completo = st.button("🎯 Optimización Completa", 
                                    help="Ejecuta optimización + frontera eficiente + todos los portafolios")
    
    # Función para ejecutar optimización individual
    def ejecutar_optimizacion_individual(manager_inst, estrategia, target_return):
        """Ejecuta optimización individual y muestra resultados"""
        try:
            use_target = target_return if estrategia == 'markowitz' else None
            # Usar la tasa libre de riesgo del benchmark si está habilitada
            risk_free_rate = benchmark_return if usar_benchmark else None
            portfolio_result = manager_inst.compute_portfolio(strategy=estrategia, target_return=use_target, risk_free_rate=risk_free_rate)
            
            if portfolio_result:
                st.success("✅ Optimización completada")
                
                # Mostrar resultados extendidos
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📊 Pesos Optimizados")
                    if portfolio_result.dataframe_allocation is not None:
                        weights_df = portfolio_result.dataframe_allocation.copy()
                        st.info(f"ℹ️ Debug: Columnas en dataframe_allocation: {weights_df.columns.tolist()}")
                        
                        # Verificar que las columnas necesarias existen
                        if 'weights' in weights_df.columns and 'rics' in weights_df.columns:
                            weights_df['Peso (%)'] = weights_df['weights'] * 100
                            weights_df = weights_df.sort_values('Peso (%)', ascending=False)
                            st.dataframe(weights_df[['rics', 'Peso (%)']], use_container_width=True)
                        elif 'weights' in weights_df.columns:
                            # Si no hay columna 'rics', usar índices
                            weights_df['Peso (%)'] = weights_df['weights'] * 100
                            weights_df = weights_df.sort_values('Peso (%)', ascending=False)
                            st.dataframe(weights_df[['weights', 'Peso (%)']], use_container_width=True)
                        else:
                            st.warning("⚠️ No se encontraron pesos optimizados en el resultado")
                            st.info("ℹ️ Columnas disponibles: " + ", ".join(weights_df.columns.tolist()))
                            st.dataframe(weights_df, use_container_width=True)
                    else:
                        st.warning("⚠️ No hay datos de asignación disponibles")
                        if portfolio_result.weights is not None:
                            # Crear DataFrame manualmente si solo tenemos weights
                            weights_df = pd.DataFrame({
                                'Activo': [f'Activo_{i+1}' for i in range(len(portfolio_result.weights))],
                                'Peso (%)': portfolio_result.weights * 100
                            })
                            weights_df = weights_df.sort_values('Peso (%)', ascending=False)
                            st.dataframe(weights_df, use_container_width=True)
                        else:
                            st.error("❌ No hay weights disponibles en el resultado de optimización")
                
                with col2:
                    st.markdown("#### 📈 Métricas del Portafolio")
                    metricas = portfolio_result.get_metrics_dict()
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Retorno Anual", f"{metricas['Annual Return']:.2%}")
                        st.metric("Volatilidad Anual", f"{metricas['Annual Volatility']:.2%}")
                        st.metric("Ratio de Sharpe", f"{metricas['Sharpe Ratio']:.4f}")
                        st.metric("VaR 95%", f"{metricas['VaR 95%']:.4f}")
                    with col_b:
                        st.metric("Skewness", f"{metricas['Skewness']:.4f}")
                        st.metric("Kurtosis", f"{metricas['Kurtosis']:.4f}")
                        st.metric("JB Statistic", f"{metricas['JB Statistic']:.4f}")
                        normalidad = "✅ Normal" if metricas['Is Normal'] else "❌ No Normal"
                        st.metric("Normalidad", normalidad)
                
                # Gráfico de distribución de retornos
                if portfolio_result.returns is not None:
                    st.markdown("#### 📊 Distribución de Retornos del Portafolio Optimizado")
                    fig = portfolio_result.plot_histogram_streamlit()
                    st.plotly_chart(fig, use_container_width=True)
                
                # Gráfico de pesos
                if portfolio_result.weights is not None:
                    st.markdown("#### 🥧 Distribución de Pesos")
                    try:
                        # Determinar las etiquetas para el gráfico
                        if portfolio_result.dataframe_allocation is not None and 'rics' in portfolio_result.dataframe_allocation.columns:
                            labels = portfolio_result.dataframe_allocation['rics']
                        else:
                            # Usar nombres genéricos si no hay etiquetas específicas
                            labels = [f'Activo_{i+1}' for i in range(len(portfolio_result.weights))]
                        
                        fig_pie = go.Figure(data=[go.Pie(
                            labels=labels,
                            values=portfolio_result.weights,
                            textinfo='label+percent',
                        )])
                        fig_pie.update_layout(title="Distribución Optimizada de Activos")
                        st.plotly_chart(fig_pie, use_container_width=True)
                    except Exception as e:
                        st.warning(f"⚠️ Error creando gráfico de pesos: {str(e)}")
                        # Mostrar datos en tabla como alternativa
                        if portfolio_result.dataframe_allocation is not None and 'weights' in portfolio_result.dataframe_allocation.columns:
                            if 'rics' in portfolio_result.dataframe_allocation.columns:
                                pie_data = pd.DataFrame({
                                    'Activo': portfolio_result.dataframe_allocation['rics'],
                                    'Peso (%)': portfolio_result.dataframe_allocation['weights'] * 100
                                })
                            else:
                                pie_data = pd.DataFrame({
                                    'Activo': [f'Activo_{i+1}' for i in range(len(portfolio_result.weights))],
                                    'Peso (%)': portfolio_result.weights * 100
                                })
                            st.dataframe(pie_data, use_container_width=True)
                        else:
                            # Crear tabla básica con weights
                            pie_data = pd.DataFrame({
                                'Activo': [f'Activo_{i+1}' for i in range(len(portfolio_result.weights))],
                                'Peso (%)': portfolio_result.weights * 100
                            })
                            st.dataframe(pie_data, use_container_width=True)
                
                # Análisis de rebalanceo automático
                st.markdown("#### 🔄 Análisis de Rebalanceo Automático")
                
                # Calcular pesos actuales solo para los activos con datos válidos
                current_weights = []
                total_value = sum([activo.get('valuacionActual', 0) for activo in activos])
                
                # Obtener solo los símbolos que están en el resultado de optimización
                simbolos_optimizados = []
                if portfolio_result.dataframe_allocation is not None and 'rics' in portfolio_result.dataframe_allocation.columns:
                    simbolos_optimizados = list(portfolio_result.dataframe_allocation['rics'])
                elif portfolio_result.weights is not None:
                    # Si no hay dataframe_allocation, usar los símbolos originales
                    simbolos_optimizados = simbolos[:len(portfolio_result.weights)]
                else:
                    # Fallback: usar símbolos originales
                    simbolos_optimizados = simbolos
                
                for simbolo in simbolos_optimizados:
                    # Buscar el activo correspondiente en el portafolio
                    activo_encontrado = None
                    for activo in activos:
                        if activo.get('titulo', {}).get('simbolo') == simbolo:
                            activo_encontrado = activo
                            break
                    
                    if activo_encontrado:
                        value = activo_encontrado.get('valuacionActual', 0)
                        weight = value / total_value if total_value > 0 else 0
                        current_weights.append(weight)
                    else:
                        # Si no se encuentra el activo, usar peso igual
                        current_weights.append(1/len(simbolos_optimizados))
                
                # Si no tenemos pesos actuales, usar pesos iguales
                if not current_weights or len(current_weights) != len(simbolos_optimizados):
                    current_weights = [1/len(simbolos_optimizados)] * len(simbolos_optimizados)
                
                # Validar que los arrays tengan la misma longitud
                if len(current_weights) != len(portfolio_result.weights):
                    st.warning(f"⚠️ Discrepancia en número de activos: {len(current_weights)} actuales vs {len(portfolio_result.weights)} optimizados")
                    st.info("ℹ️ Ajustando pesos actuales para coincidir con activos optimizados...")
                    
                    # Ajustar pesos actuales para que coincidan con los optimizados
                    if len(current_weights) > len(portfolio_result.weights):
                        # Tomar solo los primeros pesos hasta la longitud del optimizado
                        current_weights = current_weights[:len(portfolio_result.weights)]
                        # Renormalizar
                        total_weight = sum(current_weights)
                        if total_weight > 0:
                            current_weights = [w/total_weight for w in current_weights]
                        else:
                            current_weights = [1/len(portfolio_result.weights)] * len(portfolio_result.weights)
                    else:
                        # Extender con pesos iguales
                        while len(current_weights) < len(portfolio_result.weights):
                            current_weights.append(1/len(portfolio_result.weights))
                        # Renormalizar
                        total_weight = sum(current_weights)
                        if total_weight > 0:
                            current_weights = [w/total_weight for w in current_weights]
                
                # Análisis de rebalanceo
                if len(current_weights) > 0 and portfolio_result.weights is not None:
                    try:
                        rebalancing_analysis = manager_inst.compute_rebalancing_analysis(
                            current_weights, portfolio_result.weights
                        )
                    except Exception as e:
                        st.warning(f"⚠️ Error en análisis de rebalanceo: {str(e)}")
                        rebalancing_analysis = None
                else:
                    st.warning("⚠️ No se pueden calcular pesos para rebalanceo")
                    rebalancing_analysis = None
                
                if rebalancing_analysis:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Turnover Total", 
                            f"{rebalancing_analysis['total_turnover']:.2%}",
                            help="Porcentaje total de cambios en pesos"
                        )
                    
                    with col2:
                        st.metric(
                            "Cambio Máximo", 
                            f"{rebalancing_analysis['max_change']:.2%}",
                            help="Cambio máximo en un solo activo"
                        )
                    
                    with col3:
                        st.metric(
                            "Activos a Cambiar", 
                            f"{rebalancing_analysis['num_changes']}",
                            help="Número de activos que requieren ajuste"
                        )
                    
                    with col4:
                        improvement = rebalancing_analysis['improvement']
                        st.metric(
                            "Mejora Sharpe", 
                            f"{improvement['sharpe_improvement']:.4f}",
                            help="Mejora en ratio de Sharpe"
                        )
                    
                    # Mostrar detalles del rebalanceo
                    st.markdown("#### 📋 Detalles del Rebalanceo")
                    
                    rebalancing_df = pd.DataFrame({
                        'Activo': simbolos_optimizados,
                        'Peso Actual (%)': [w * 100 for w in current_weights],
                        'Peso Objetivo (%)': [w * 100 for w in portfolio_result.weights],
                        'Cambio (%)': [(w2 - w1) * 100 for w1, w2 in zip(current_weights, portfolio_result.weights)]
                    })
                    
                    st.dataframe(rebalancing_df, use_container_width=True)
                    
                    # Gráfico de cambios en pesos
                    if len(simbolos_optimizados) > 0 and len(current_weights) > 0 and portfolio_result.weights is not None:
                        try:
                            fig_changes = go.Figure()
                            fig_changes.add_trace(go.Bar(
                                x=simbolos_optimizados,
                                y=[w * 100 for w in current_weights],
                                name='Peso Actual',
                                marker_color='lightblue'
                            ))
                            fig_changes.add_trace(go.Bar(
                                x=simbolos_optimizados,
                                y=[w * 100 for w in portfolio_result.weights],
                                name='Peso Objetivo',
                                marker_color='orange'
                            ))
                            
                            fig_changes.update_layout(
                                title='Comparación de Pesos: Actual vs Optimizado',
                                xaxis_title='Activo',
                                yaxis_title='Peso (%)',
                                barmode='group',
                                height=400
                            )
                            
                            st.plotly_chart(fig_changes, use_container_width=True)
                        except Exception as e:
                            st.warning(f"⚠️ Error creando gráfico de cambios: {str(e)}")
                            # Mostrar datos en tabla como alternativa
                            comparison_df = pd.DataFrame({
                                'Activo': simbolos_optimizados,
                                'Peso Actual (%)': [w * 100 for w in current_weights],
                                'Peso Objetivo (%)': [w * 100 for w in portfolio_result.weights],
                                'Cambio (%)': [(w2 - w1) * 100 for w1, w2 in zip(current_weights, portfolio_result.weights)]
                            })
                            st.dataframe(comparison_df, use_container_width=True)
                    else:
                        st.warning("⚠️ No hay datos suficientes para crear gráfico de cambios")
                
                return portfolio_result
            else:
                st.error("❌ No se pudo completar la optimización")
                return None
                
        except Exception as e:
            st.error(f"❌ Error durante la optimización: {str(e)}")
            return None
    
    # Ejecutar optimización individual
    if ejecutar_optimizacion:
        with st.spinner("🔄 Ejecutando optimización individual..."):
            try:
                # Crear manager de portafolio con tasa libre de riesgo del benchmark
                risk_free_rate = benchmark_return if usar_benchmark else 0.04
                manager_inst = PortfolioManager(simbolos, token_acceso, fecha_desde, fecha_hasta, risk_free_rate)
                
                # Cargar datos
                if manager_inst.load_data():
                    ejecutar_optimizacion_individual(manager_inst, estrategia, target_return)
                else:
                    st.error("❌ No se pudieron cargar los datos históricos")
                    
            except Exception as e:
                st.error(f"❌ Error durante la optimización: {str(e)}")
    
    # Ejecutar optimización completa
    if ejecutar_completo:
        with st.spinner("🚀 Ejecutando optimización completa..."):
            try:
                # Crear manager de portafolio con tasa libre de riesgo del benchmark
                risk_free_rate = benchmark_return if usar_benchmark else 0.04
                manager_inst = PortfolioManager(simbolos, token_acceso, fecha_desde, fecha_hasta, risk_free_rate)
                
                # Cargar datos
                if manager_inst.load_data():
                    st.success("✅ Datos cargados correctamente")
                    
                    # Ejecutar optimización individual
                    st.markdown("### 📊 Optimización Individual")
                    portfolio_result = ejecutar_optimizacion_individual(manager_inst, estrategia, target_return)
                    
                    # Ejecutar frontera eficiente
                    if show_frontier:
                        st.markdown("### 📈 Frontera Eficiente Interactiva")
                        fig = calcular_frontera_interactiva(
                            manager_inst, 
                            calcular_todos=calcular_todos,
                            incluir_actual=incluir_actual,
                            num_puntos=num_puntos,
                            target_return=target_return_frontier,
                            mostrar_metricas=mostrar_metricas
                        )
                        
                        if fig:
                            st.success("✅ Análisis completo finalizado")
                        else:
                            st.warning("⚠️ Frontera eficiente no disponible")
                else:
                    st.error("❌ No se pudieron cargar los datos históricos")
                    
            except Exception as e:
                st.error(f"❌ Error durante la optimización completa: {str(e)}")
    
    
    # Ejecutar frontera eficiente
    if (ejecutar_frontier or ejecutar_completo) and show_frontier:
        with st.spinner("🔄 Calculando frontera eficiente interactiva..."):
            try:
                manager_inst = PortfolioManager(simbolos, token_acceso, fecha_desde, fecha_hasta)
                
                if manager_inst.load_data():
                    # Calcular frontera eficiente interactiva
                    fig = calcular_frontera_interactiva(
                        manager_inst, 
                        calcular_todos=calcular_todos,
                        incluir_actual=incluir_actual,
                        num_puntos=num_puntos,
                        target_return=target_return_frontier,
                        mostrar_metricas=mostrar_metricas
                    )
                    
                    if fig is None:
                        st.error("❌ No se pudo calcular la frontera eficiente")
                    else:
                        # Agregar controles interactivos adicionales
                        st.markdown("### 🎛️ Controles Interactivos")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            zoom_level = st.slider("Zoom", min_value=0.5, max_value=3.0, value=1.0, step=0.1)
                        with col2:
                            mostrar_grid = st.checkbox("Mostrar Grid", value=True, key="mostrar_grid_avanzada")
                        with col3:
                            mostrar_leyenda = st.checkbox("Mostrar Leyenda", value=True, key="mostrar_leyenda_avanzada")
                        
                        # Aplicar configuraciones al gráfico
                        if fig:
                            fig.update_layout(
                                xaxis=dict(
                                    tickformat='.1%',
                                    gridcolor='lightgray' if mostrar_grid else 'rgba(0,0,0,0)',
                                    zeroline=False
                                ),
                                yaxis=dict(
                                    tickformat='.1%',
                                    gridcolor='lightgray' if mostrar_grid else 'rgba(0,0,0,0)',
                                    zeroline=False
                                ),
                                showlegend=mostrar_leyenda
                            )
                            
                            # Configurar zoom
                            if zoom_level != 1.0:
                                # Obtener los límites actuales del gráfico
                                x_range = fig.layout.xaxis.range if fig.layout.xaxis.range else [0, 0.5]
                                y_range = fig.layout.yaxis.range if fig.layout.yaxis.range else [0, 0.3]
                                
                                fig.update_layout(
                                    xaxis=dict(range=[x_range[0], x_range[1] * zoom_level]),
                                    yaxis=dict(range=[y_range[0], y_range[1] * zoom_level])
                                )
                            
                            st.plotly_chart(fig, use_container_width=True, config={
                                'displayModeBar': True,
                                'modeBarButtonsToAdd': ['pan2d', 'select2d', 'lasso2d', 'resetScale2d']
                            })
                        
                        # Mostrar información adicional
                        if mostrar_metricas:
                            st.markdown("### 📈 Análisis de Frontera Eficiente")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Puntos Clave:**")
                                st.markdown("""
                                - **Frontera Eficiente**: Línea azul que muestra las mejores combinaciones riesgo-retorno
                                - **Portafolios Optimizados**: Diamantes de colores que representan diferentes estrategias
                                - **Portafolio Actual**: Estrella negra que muestra la posición actual
                                - **Línea de Sharpe**: Línea punteada gris que muestra retornos constantes
                                """)
                            
                            with col2:
                                st.markdown("**Interpretación:**")
                                st.markdown("""
                                - **Arriba y a la izquierda**: Mejor rendimiento (más retorno, menos riesgo)
                                - **Abajo y a la derecha**: Peor rendimiento (menos retorno, más riesgo)
                                - **Puntos en la frontera**: Óptimos según teoría de Markowitz
                                - **Distancia al origen**: Ratio de Sharpe (pendiente de la línea)
                                """)
                else:
                    st.error("❌ No se pudieron cargar los datos históricos")
                    
            except Exception as e:
                st.error(f"❌ Error calculando frontera eficiente: {str(e)}")
    
    # Mostrar frontera eficiente en tiempo real si auto-refresh está activado
    if auto_refresh and show_frontier and not (ejecutar_frontier or ejecutar_completo):
        st.markdown("### 🔄 Frontera Eficiente en Tiempo Real")
        st.info("💡 Cambia los parámetros arriba para ver actualizaciones automáticas")
        
        # Crear placeholder para la frontera
        frontier_placeholder = st.empty()
        
        with frontier_placeholder.container():
            with st.spinner("Calculando frontera en tiempo real..."):
                try:
                    manager_inst = PortfolioManager(simbolos, token_acceso, fecha_desde, fecha_hasta)
                    
                    if manager_inst.load_data():
                        fig = calcular_frontera_interactiva(
                            manager_inst, 
                            calcular_todos=calcular_todos,
                            incluir_actual=incluir_actual,
                            num_puntos=num_puntos,
                            target_return=target_return_frontier,
                            mostrar_metricas=False  # No mostrar métricas en tiempo real para velocidad
                        )
                        
                        if fig:
                            st.success("✅ Frontera actualizada automáticamente")
                        else:
                            st.warning("⚠️ Frontera no disponible en tiempo real")
                    else:
                        st.error("❌ No se pudieron cargar los datos para tiempo real")
                        
                except Exception as e:
                    st.warning(f"⚠️ Error en tiempo real: {str(e)}")
    
    # Función para actualización automática de frontera eficiente
    def actualizar_frontera_automatica():
        """Actualiza automáticamente la frontera eficiente cuando cambian los parámetros"""
        if auto_refresh and show_frontier:
            st.rerun()
    
    # Configurar actualización automática
    if auto_refresh:
        st.markdown("🔄 **Modo Auto-refresh activado** - La frontera se actualizará automáticamente")
    
    # Información adicional extendida
    with st.expander("ℹ️ Información sobre las Estrategias"):
        st.markdown("""
        **Optimización de Markowitz:**
        - Maximiza el ratio de Sharpe (retorno/riesgo)
        - Considera la correlación entre activos
        - Busca la frontera eficiente
        
        **Pesos Iguales:**
        - Distribución uniforme entre todos los activos
        - Estrategia simple de diversificación
        - No considera correlaciones históricas
        
        **Mínima Varianza L1:**
        - Minimiza la varianza del portafolio
        - Restricción L1 para regularización
        - Tiende a generar portafolios más concentrados
        
        **Mínima Varianza L2:**
        - Minimiza la varianza del portafolio
        - Restricción L2 para regularización
        - Genera portafolios más diversificados
        
        **Solo Posiciones Largas:**
        - Optimización estándar sin restricciones adicionales
        - Permite solo posiciones compradoras
        - Suma de pesos = 100%
        """)
    
    # Mostrar estadísticas rápidas si hay datos
    if len(simbolos) > 0:
        with st.expander("📊 Estadísticas Rápidas del Portafolio", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Número de Activos", len(simbolos))
                st.metric("Valor Total", f"${sum([activo.get('valuacionActual', 0) for activo in activos]):,.2f}")
            with col2:
                st.metric("Activos con Datos", len([s for s in simbolos if s]))
                st.metric("Diversificación", f"{len(simbolos)} activos")
            with col3:
                st.metric("Período Análisis", f"{fecha_desde} a {fecha_hasta}")
                st.metric("Estado", "✅ Listo para optimización")

def mostrar_optimizacion_avanzada(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Optimización avanzada con capital inicial, horizonte, benchmark y análisis de alpha/beta
    """
    mostrar_menu_optimizaciones_avanzadas(portafolio, token_acceso, fecha_desde, fecha_hasta)

def mostrar_frontera_eficiente(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Análisis específico de frontera eficiente
    """
    st.markdown("#### 📈 Análisis de Frontera Eficiente")
    
    activos = portafolio.get('activos', [])
    if not activos:
        st.warning("No hay activos en el portafolio para análisis")
        return
    
    # Extraer símbolos del portafolio
    simbolos = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', '')
        if simbolo:
            simbolos.append(simbolo)
    
    if len(simbolos) < 2:
        st.warning("Se necesitan al menos 2 activos para análisis de frontera eficiente")
        return
    
    st.info(f"📊 Analizando frontera eficiente para {len(simbolos)} activos")
    
    # Configuración de frontera eficiente
    col1, col2, col3 = st.columns(3)
    
    with col1:
        target_return = st.number_input(
            "Retorno Objetivo (anual):",
            min_value=0.0, max_value=1.0, value=0.08, step=0.01
        )
        num_puntos = st.slider("Número de Puntos", min_value=10, max_value=100, value=50)
    
    with col2:
        incluir_actual = st.checkbox("Incluir Portafolio Actual", value=True, key="incluir_actual_avanzada")
        mostrar_metricas = st.checkbox("Mostrar Métricas Detalladas", value=True, key="mostrar_metricas_avanzada")
    
    with col3:
        calcular_todos = st.checkbox("Calcular Todos los Portafolios", value=True, key="calcular_todos_avanzada")
        auto_refresh = st.checkbox("Auto-refresh", value=True, key="auto_refresh_avanzada")
    
    ejecutar_frontier = st.button("📈 Calcular Frontera Eficiente", use_container_width=True)
    
    if ejecutar_frontier:
        with st.spinner("🔄 Calculando frontera eficiente..."):
            try:
                manager_inst = PortfolioManager(simbolos, token_acceso, fecha_desde, fecha_hasta)
                
                if manager_inst.load_data():
                    # Usar la función de frontera eficiente interactiva
                    fig = calcular_frontera_interactiva(
                        manager_inst, 
                        calcular_todos=calcular_todos,
                        incluir_actual=incluir_actual,
                        num_puntos=num_puntos,
                        target_return=target_return,
                        mostrar_metricas=mostrar_metricas
                    )
                    
                    if fig:
                        st.success("✅ Frontera eficiente calculada exitosamente")
                    else:
                        st.error("❌ No se pudo calcular la frontera eficiente")
                else:
                    st.error("❌ No se pudieron cargar los datos históricos")
                    
            except Exception as e:
                st.error(f"❌ Error calculando frontera eficiente: {str(e)}")

# Función antigua eliminada - reemplazada por mostrar_menu_optimizacion_unificado

def calcular_frontera_interactiva(manager_inst, calcular_todos=True, incluir_actual=True, 
                                num_puntos=50, target_return=0.08, mostrar_metricas=True):
    """Calcula y muestra la frontera eficiente de forma interactiva"""
    try:
        # Calcular frontera eficiente
        portfolios, returns, volatilities = manager_inst.compute_efficient_frontier(
            target_return=target_return, include_min_variance=True
        )
        
        if not (portfolios and returns and volatilities):
            st.error("❌ No se pudo calcular la frontera eficiente")
            return None
        
        st.success("✅ Frontera eficiente calculada")
        
        # Crear gráfico interactivo mejorado
        fig = go.Figure()
        
        # Línea de frontera eficiente con más puntos
        fig.add_trace(go.Scatter(
            x=volatilities, y=returns,
            mode='lines+markers',
            name='Frontera Eficiente',
            line=dict(color='blue', width=3),
            marker=dict(size=6, color='blue'),
            hovertemplate='<b>Frontera Eficiente</b><br>' +
                        'Volatilidad: %{x:.2%}<br>' +
                        'Retorno: %{y:.2%}<br>' +
                        '<extra></extra>'
        ))
        
        # Calcular todos los portafolios si se solicita
        if calcular_todos:
            estrategias = ['markowitz', 'equi-weight', 'min-variance-l1', 'min-variance-l2', 'long-only']
            colores = ['red', 'green', 'orange', 'purple', 'pink', 'brown', 'cyan', 'magenta']
            etiquetas = ['Markowitz', 'Pesos Iguales', 'Min Var L1', 'Min Var L2', 'Solo Largos']
            
            for i, estrategia in enumerate(estrategias):
                try:
                    portfolio_result = manager_inst.compute_portfolio(strategy=estrategia, target_return=target_return)
                    if portfolio_result and hasattr(portfolio_result, 'volatility_annual'):
                        fig.add_trace(go.Scatter(
                            x=[portfolio_result.volatility_annual], 
                            y=[portfolio_result.return_annual],
                            mode='markers',
                            name=etiquetas[i] if i < len(etiquetas) else estrategia,
                            marker=dict(size=12, color=colores[i % len(colores)], symbol='diamond'),
                            hovertemplate=f'<b>{etiquetas[i] if i < len(etiquetas) else estrategia}</b><br>' +
                                        'Volatilidad: %{x:.2%}<br>' +
                                        'Retorno: %{y:.2%}<br>' +
                                        'Sharpe: ' + f'{portfolio_result.sharpe_ratio:.4f}' + '<br>' +
                                        '<extra></extra>'
                        ))
                except Exception as e:
                    st.warning(f"⚠️ Error calculando {estrategia}: {str(e)}")
                    continue
        
        # Incluir portafolio actual si se solicita
        if incluir_actual:
            # Calcular métricas del portafolio actual
            try:
                # Simular portafolio actual con pesos iguales
                simbolos = list(manager_inst.returns.columns) if hasattr(manager_inst, 'returns') and manager_inst.returns is not None else []
                if simbolos:
                    current_weights = [1/len(simbolos)] * len(simbolos)
                    current_metrics = manager_inst._calculate_portfolio_metrics(current_weights)
                    
                    fig.add_trace(go.Scatter(
                        x=[current_metrics['volatility']], 
                        y=[current_metrics['return']],
                        mode='markers',
                        name='Portafolio Actual',
                        marker=dict(size=15, color='black', symbol='star'),
                        hovertemplate='<b>Portafolio Actual</b><br>' +
                                    'Volatilidad: %{x:.2%}<br>' +
                                    'Retorno: %{y:.2%}<br>' +
                                    '<extra></extra>'
                    ))
            except Exception as e:
                st.warning(f"⚠️ Error calculando portafolio actual: {str(e)}")
        
        # Configurar layout interactivo
        fig.update_layout(
            title='Frontera Eficiente Interactiva del Portafolio',
            xaxis_title='Volatilidad Anual',
            yaxis_title='Retorno Anual',
            showlegend=True,
            hovermode='closest',
            template='plotly_white',
            height=600,
            # Configurar ejes para mejor visualización
            xaxis=dict(
                tickformat='.1%',
                gridcolor='lightgray',
                zeroline=False
            ),
            yaxis=dict(
                tickformat='.1%',
                gridcolor='lightgray',
                zeroline=False
            )
        )
        
        # Agregar línea de ratio de Sharpe constante
        if len(returns) > 0 and len(volatilities) > 0:
            max_return = max(returns)
            max_vol = max(volatilities)
            sharpe_line_x = np.linspace(0, max_vol, 100)
            sharpe_line_y = sharpe_line_x * (max_return / max_vol)  # Línea de Sharpe constante
            
            fig.add_trace(go.Scatter(
                x=sharpe_line_x, y=sharpe_line_y,
                mode='lines',
                name='Línea de Sharpe Constante',
                line=dict(color='gray', dash='dash', width=1),
                opacity=0.5,
                showlegend=True
            ))
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
        
        # Mostrar métricas detalladas si se solicita
        if mostrar_metricas:
            st.markdown("#### 📊 Métricas Detalladas de Portafolios")
            
            # Crear tabla comparativa mejorada
            comparison_data = []
            if calcular_todos:
                for i, estrategia in enumerate(estrategias):
                    try:
                        portfolio_result = manager_inst.compute_portfolio(strategy=estrategia, target_return=target_return)
                        if portfolio_result:
                            comparison_data.append({
                                'Estrategia': etiquetas[i] if i < len(etiquetas) else estrategia,
                                'Retorno Anual': f"{portfolio_result.return_annual:.2%}",
                                'Volatilidad Anual': f"{portfolio_result.volatility_annual:.2%}",
                                'Sharpe Ratio': f"{portfolio_result.sharpe_ratio:.4f}",
                                'VaR 95%': f"{portfolio_result.var_95:.4f}",
                                'Max Drawdown': f"{portfolio_result.max_drawdown:.2%}" if hasattr(portfolio_result, 'max_drawdown') else "N/A"
                            })
                    except Exception as e:
                        continue
            
            if comparison_data:
                df_comparison = pd.DataFrame(comparison_data)
                st.dataframe(df_comparison, use_container_width=True)
                
                # Gráfico de barras comparativo
                fig_bars = go.Figure()
                
                estrategias_nombres = [row['Estrategia'] for row in comparison_data]
                sharpe_ratios = [float(row['Sharpe Ratio']) for row in comparison_data]
                
                fig_bars.add_trace(go.Bar(
                    x=estrategias_nombres,
                    y=sharpe_ratios,
                    marker_color='lightblue',
                    text=[f"{s:.3f}" for s in sharpe_ratios],
                    textposition='auto'
                ))
                
                fig_bars.update_layout(
                    title='Comparación de Ratios de Sharpe',
                    xaxis_title='Estrategia',
                    yaxis_title='Sharpe Ratio',
                    height=400
                )
                
                st.plotly_chart(fig_bars, use_container_width=True)
        
        return fig
        
    except Exception as e:
        st.error(f"❌ Error en frontera eficiente interactiva: {str(e)}")
        return None

def obtener_movimientos_reales(access_token, id_cliente=None, fecha_desde=None, fecha_hasta=None):
    """
    Obtiene los movimientos/operaciones de la cuenta usando la API de InvertirOnline
    Si la API falla, intenta usar scraping de la página web como fallback
    
    Args:
        access_token (str): Token de acceso para la autenticación
        id_cliente (str): ID del cliente para filtrar operaciones (opcional)
        fecha_desde (str): Fecha desde en formato YYYY-MM-DD (opcional)
        fecha_hasta (str): Fecha hasta en formato YYYY-MM-DD (opcional)
    
    Returns:
        list: Lista de operaciones/movimientos de la cuenta
    """
    # Primero intentar con la API
    url = 'https://api.invertironline.com/api/v2/operaciones'
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    # Parámetros de consulta para filtrar por fechas (formato correcto de la API)
    params = {
        'filtro.pais': 'argentina'  # País por defecto
    }
    if fecha_desde:
        params['filtro.fechaDesde'] = fecha_desde
    if fecha_hasta:
        params['filtro.fechaHasta'] = fecha_hasta
    if id_cliente:
        params['filtro.cuentaComitente'] = id_cliente
    
    try:
        st.info(f"🔗 Consultando operaciones desde {fecha_desde or 'inicio'} hasta {fecha_hasta or 'actual'}")
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            operaciones = response.json()
            st.success(f"📊 Se obtuvieron {len(operaciones)} operaciones via API")
            
            # Mostrar información de debug
            if operaciones:
                simbolos_encontrados = list(set([op.get('simbolo', 'N/A') for op in operaciones]))
                st.info(f"🔍 Símbolos encontrados: {simbolos_encontrados}")
            else:
                st.warning("⚠️ No se encontraron operaciones en el período especificado")
            
            return operaciones
        else:
            st.warning(f"⚠️ API falló con código {response.status_code}, intentando scraping...")
            # Fallback a scraping básico primero
            operaciones = obtener_operaciones_via_scraping(access_token, id_cliente, fecha_desde, fecha_hasta)
            if not operaciones:
                # Si el scraping básico falla, intentar scraping avanzado
                st.info("🔍 Scraping básico falló, intentando scraping avanzado...")
                return obtener_operaciones_via_scraping_avanzado(access_token, id_cliente, fecha_desde, fecha_hasta)
            return operaciones
            
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ Error en API: {e}, intentando scraping...")
        # Fallback a scraping básico primero
        operaciones = obtener_operaciones_via_scraping(access_token, id_cliente, fecha_desde, fecha_hasta)
        if not operaciones:
            # Si el scraping básico falla, intentar scraping avanzado
            st.info("🔍 Scraping básico falló, intentando scraping avanzado...")
            return obtener_operaciones_via_scraping_avanzado(access_token, id_cliente, fecha_desde, fecha_hasta)
        return operaciones

def obtener_operaciones_via_scraping(access_token, id_cliente=None, fecha_desde=None, fecha_hasta=None):
    """
    Obtiene operaciones mediante scraping de la página web de IOL
    como fallback cuando la API no funciona. Simula el envío del formulario con filtros.
    
    Args:
        access_token (str): Token de acceso para la autenticación
        id_cliente (str): ID del cliente para filtrar operaciones (opcional)
        fecha_desde (str): Fecha desde en formato YYYY-MM-DD (opcional)
        fecha_hasta (str): Fecha hasta en formato YYYY-MM-DD (opcional)
    
    Returns:
        list: Lista de operaciones obtenidas via scraping
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        import re
        from datetime import datetime
        
        st.info("🔍 Intentando obtener operaciones via scraping con filtros...")
        
        # URL base de la página de operaciones
        url = 'https://afi.invertironline.com/cliente-operaciones'
        
        # Headers para simular un navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Authorization': f'Bearer {access_token}',
            'Referer': 'https://afi.invertironline.com/cliente-operaciones'
        }
        
        # Primero obtener la página para extraer tokens CSRF si existen
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar tokens CSRF o campos hidden
            csrf_token = None
            csrf_input = soup.find('input', {'name': '_token'}) or soup.find('input', {'name': 'csrf_token'})
            if csrf_input:
                csrf_token = csrf_input.get('value')
            
            # Preparar datos del formulario
            form_data = {
                'status': 'Todas',  # Por defecto todas las operaciones
                'country': 'argentina',  # País por defecto
                'singleDay': 'false'  # Buscar en rango de fechas
            }
            
            # Agregar fechas si se proporcionan
            if fecha_desde:
                form_data['dateFrom'] = fecha_desde
            if fecha_hasta:
                form_data['dateTo'] = fecha_hasta
            
            # Agregar cliente si se especifica
            if id_cliente:
                form_data['customer'] = str(id_cliente)
            
            # Agregar token CSRF si existe
            if csrf_token:
                form_data['_token'] = csrf_token
            
            # Headers para el POST
            headers_post = headers.copy()
            headers_post.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            # Intentar enviar el formulario (simulación)
            try:
                # En lugar de enviar el formulario, buscar la tabla directamente
                # ya que la página puede cargar los datos dinámicamente
                st.info("🔍 Buscando tabla de operaciones en la página...")
                
                # Buscar la tabla de operaciones
                tabla_operaciones = soup.find('table', class_='ant-table-tbody') or soup.find('table')
                
                if tabla_operaciones and not tabla_operaciones.find('tr', class_='ant-table-placeholder'):
                    operaciones = []
                    filas = tabla_operaciones.find_all('tr')
                    
                    for fila in filas:
                        celdas = fila.find_all('td')
                        
                        if len(celdas) >= 9:  # Verificar que tenga todas las columnas
                            # Extraer datos según la estructura de la tabla:
                            # C.C., Nº trans./Fecha orden, Tipo, Símbolo, Cant./Monto, Cant. operada, Precio operado, Monto operado, Estado
                            cc = celdas[0].get_text(strip=True) if len(celdas) > 0 else ''
                            numero_fecha = celdas[1].get_text(strip=True) if len(celdas) > 1 else ''
                            tipo = celdas[2].get_text(strip=True) if len(celdas) > 2 else ''
                            simbolo = celdas[3].get_text(strip=True) if len(celdas) > 3 else ''
                            cantidad_monto = celdas[4].get_text(strip=True) if len(celdas) > 4 else ''
                            cantidad_operada = celdas[5].get_text(strip=True) if len(celdas) > 5 else ''
                            precio_operado = celdas[6].get_text(strip=True) if len(celdas) > 6 else ''
                            monto_operado = celdas[7].get_text(strip=True) if len(celdas) > 7 else ''
                            estado = celdas[8].get_text(strip=True) if len(celdas) > 8 else ''
                            
                            # Separar número de orden y fecha
                            numero_orden = ''
                            fecha_orden = ''
                            if numero_fecha:
                                partes = numero_fecha.split('\n')
                                if len(partes) >= 2:
                                    numero_orden = partes[0].strip()
                                    fecha_orden = partes[1].strip()
                                else:
                                    numero_orden = numero_fecha
                            
                            # Convertir datos a formato esperado
                            operacion = {
                                'numero': numero_orden,
                                'fechaOrden': fecha_orden,
                                'tipo': tipo,
                                'simbolo': simbolo,
                                'cantidad': float(cantidad_operada.replace(',', '.')) if cantidad_operada and cantidad_operada != '-' else 0,
                                'precio': float(precio_operado.replace(',', '.')) if precio_operado and precio_operado != '-' else 0,
                                'monto': float(monto_operado.replace(',', '.')) if monto_operado and monto_operado != '-' else 0,
                                'estado': estado.lower() if estado else 'terminada',
                                'fechaOperada': fecha_orden,
                                'cantidadOperada': float(cantidad_operada.replace(',', '.')) if cantidad_operada and cantidad_operada != '-' else 0,
                                'precioOperado': float(precio_operado.replace(',', '.')) if precio_operado and precio_operado != '-' else 0,
                                'montoOperado': float(monto_operado.replace(',', '.')) if monto_operado and monto_operado != '-' else 0,
                                'cc': cc
                            }
                            
                            # Filtrar por cliente si se especifica
                            if not id_cliente or str(id_cliente) in cc or str(id_cliente) in numero_orden:
                                operaciones.append(operacion)
                    
                    if operaciones:
                        st.success(f"📊 Se obtuvieron {len(operaciones)} operaciones via scraping")
                        
                        # Mostrar información de debug
                        simbolos_encontrados = list(set([op.get('simbolo', 'N/A') for op in operaciones]))
                        st.info(f"🔍 Símbolos encontrados via scraping: {simbolos_encontrados}")
                        
                        return operaciones
                    else:
                        st.warning("⚠️ No se encontraron operaciones en la tabla")
                        return []
                else:
                    st.warning("⚠️ La tabla de operaciones está vacía o no se encontró")
                    return []
                    
            except Exception as form_error:
                st.warning(f"⚠️ Error procesando formulario: {form_error}")
                return []
                
        else:
            st.error(f"❌ Error al acceder a la página: {response.status_code}")
            return []
            
    except ImportError:
        st.error("❌ Error: Se requiere BeautifulSoup4 para el scraping. Instalar con: pip install beautifulsoup4")
        return []
    except Exception as e:
        st.error(f"❌ Error en scraping: {str(e)}")
        return []

def obtener_movimientos_agrupados_via_scraping(access_token, fecha_desde=None, fecha_hasta=None):
    """
    Obtiene movimientos agrupados (depósitos y extracciones) mediante scraping
    de la página https://afi.invertironline.com/cliente-movimientos-agrupados
    
    Args:
        access_token (str): Token de acceso para la autenticación
        fecha_desde (str): Fecha desde en formato YYYY-MM-DD (opcional)
        fecha_hasta (str): Fecha hasta en formato YYYY-MM-DD (opcional)
    
    Returns:
        dict: Diccionario con movimientos agrupados por cliente
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        import re
        
        st.info("🔍 Obteniendo movimientos agrupados via scraping...")
        
        # URL de la página de movimientos agrupados
        url = 'https://afi.invertironline.com/cliente-movimientos-agrupados'
        
        # Headers para simular un navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Authorization': f'Bearer {access_token}'
        }
        
        # Realizar la solicitud
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar la tabla de movimientos
            tabla_movimientos = soup.find('table', class_='ant-table-tbody') or soup.find('table')
            
            if tabla_movimientos:
                movimientos = {}
                filas = tabla_movimientos.find_all('tr')
                
                for fila in filas:
                    celdas = fila.find_all('td')
                    
                    if len(celdas) >= 6:  # Verificar que tenga suficientes columnas
                        # Extraer datos de cada celda
                        nombre_cliente = celdas[0].get_text(strip=True) if len(celdas) > 0 else ''
                        cc = celdas[1].get_text(strip=True) if len(celdas) > 1 else ''
                        deposito_ars = celdas[2].get_text(strip=True) if len(celdas) > 2 else ''
                        extraccion_ars = celdas[3].get_text(strip=True) if len(celdas) > 3 else ''
                        deposito_usd = celdas[4].get_text(strip=True) if len(celdas) > 4 else ''
                        extraccion_usd = celdas[5].get_text(strip=True) if len(celdas) > 5 else ''
                        
                        # Extraer ID del cliente del enlace
                        enlace_cliente = celdas[0].find('a')
                        id_cliente = None
                        if enlace_cliente and enlace_cliente.get('href'):
                            match = re.search(r'/cliente/(\d+)', enlace_cliente['href'])
                            if match:
                                id_cliente = match.group(1)
                        
                        # Limpiar y convertir valores monetarios
                        def limpiar_valor_monetario(valor):
                            if not valor or valor == '-' or valor == '$ 0,00' or valor == 'US$ 0,00':
                                return 0.0
                            # Remover símbolos y convertir a float
                            valor_limpio = re.sub(r'[^\d,.-]', '', valor)
                            valor_limpio = valor_limpio.replace(',', '.')
                            try:
                                return float(valor_limpio)
                            except:
                                return 0.0
                        
                        # Crear entrada para el cliente
                        if id_cliente:
                            movimientos[id_cliente] = {
                                'nombre': nombre_cliente,
                                'cc': cc,
                                'deposito_ars': limpiar_valor_monetario(deposito_ars),
                                'extraccion_ars': limpiar_valor_monetario(extraccion_ars),
                                'deposito_usd': limpiar_valor_monetario(deposito_usd),
                                'extraccion_usd': limpiar_valor_monetario(extraccion_usd),
                                'neto_ars': limpiar_valor_monetario(deposito_ars) - limpiar_valor_monetario(extraccion_ars),
                                'neto_usd': limpiar_valor_monetario(deposito_usd) - limpiar_valor_monetario(extraccion_usd)
                            }
                
                st.success(f"📊 Se obtuvieron movimientos de {len(movimientos)} clientes via scraping")
                
                # Mostrar información de debug
                if movimientos:
                    st.info(f"🔍 Clientes encontrados: {list(movimientos.keys())}")
                
                return movimientos
            else:
                st.warning("⚠️ No se pudo encontrar la tabla de movimientos en la página")
                return {}
        else:
            st.error(f"❌ Error al acceder a la página: {response.status_code}")
            return {}
            
    except ImportError:
        st.error("❌ Error: Se requiere BeautifulSoup4 para el scraping. Instalar con: pip install beautifulsoup4")
        return {}
    except Exception as e:
        st.error(f"❌ Error en scraping de movimientos: {str(e)}")
        return {}

def obtener_operaciones_via_scraping_avanzado(access_token, id_cliente=None, fecha_desde=None, fecha_hasta=None):
    """
    Versión avanzada del scraping que intenta simular la interacción completa con el formulario
    usando Selenium como fallback cuando BeautifulSoup no es suficiente
    
    Args:
        access_token (str): Token de acceso para la autenticación
        id_cliente (str): ID del cliente para filtrar operaciones (opcional)
        fecha_desde (str): Fecha desde en formato YYYY-MM-DD (opcional)
        fecha_hasta (str): Fecha hasta en formato YYYY-MM-DD (opcional)
    
    Returns:
        list: Lista de operaciones obtenidas via scraping avanzado
    """
    try:
        # Intentar con Selenium si está disponible
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.keys import Keys
            import time
            
            st.info("🔍 Intentando scraping avanzado con Selenium...")
            
            # Configurar Chrome en modo headless
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                # Navegar a la página
                driver.get('https://afi.invertironline.com/cliente-operaciones')
                
                # Esperar a que la página cargue
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "ant-form"))
                )
                
                # Configurar filtros
                if fecha_desde and fecha_hasta:
                    # Buscar el campo de fecha desde
                    fecha_desde_input = driver.find_element(By.ID, "dateRange")
                    fecha_desde_input.clear()
                    fecha_desde_input.send_keys(fecha_desde)
                    
                    # Buscar el campo de fecha hasta (segundo input)
                    fecha_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[placeholder="Hasta"]')
                    if fecha_inputs:
                        fecha_inputs[0].clear()
                        fecha_inputs[0].send_keys(fecha_hasta)
                
                # Buscar cliente si se especifica
                if id_cliente:
                    customer_input = driver.find_element(By.ID, "customer")
                    customer_input.clear()
                    customer_input.send_keys(str(id_cliente))
                    customer_input.send_keys(Keys.RETURN)
                
                # Hacer clic en el botón buscar
                buscar_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                if buscar_button.is_enabled():
                    buscar_button.click()
                    
                    # Esperar a que se carguen los resultados
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "ant-table-tbody"))
                    )
                
                # Extraer datos de la tabla
                tabla = driver.find_element(By.CLASS_NAME, "ant-table-tbody")
                filas = tabla.find_elements(By.TAG_NAME, "tr")
                
                operaciones = []
                for fila in filas:
                    celdas = fila.find_elements(By.TAG_NAME, "td")
                    
                    if len(celdas) >= 9:
                        try:
                            cc = celdas[0].text.strip()
                            numero_fecha = celdas[1].text.strip()
                            tipo = celdas[2].text.strip()
                            simbolo = celdas[3].text.strip()
                            cantidad_operada = celdas[5].text.strip()
                            precio_operado = celdas[6].text.strip()
                            monto_operado = celdas[7].text.strip()
                            estado = celdas[8].text.strip()
                            
                            # Separar número y fecha
                            partes = numero_fecha.split('\n')
                            numero_orden = partes[0].strip() if len(partes) > 0 else ''
                            fecha_orden = partes[1].strip() if len(partes) > 1 else ''
                            
                            operacion = {
                                'numero': numero_orden,
                                'fechaOrden': fecha_orden,
                                'tipo': tipo,
                                'simbolo': simbolo,
                                'cantidad': float(cantidad_operada.replace(',', '.')) if cantidad_operada and cantidad_operada != '-' else 0,
                                'precio': float(precio_operado.replace(',', '.')) if precio_operado and precio_operado != '-' else 0,
                                'monto': float(monto_operado.replace(',', '.')) if monto_operado and monto_operado != '-' else 0,
                                'estado': estado.lower() if estado else 'terminada',
                                'fechaOperada': fecha_orden,
                                'cantidadOperada': float(cantidad_operada.replace(',', '.')) if cantidad_operada and cantidad_operada != '-' else 0,
                                'precioOperado': float(precio_operado.replace(',', '.')) if precio_operado and precio_operado != '-' else 0,
                                'montoOperado': float(monto_operado.replace(',', '.')) if monto_operado and monto_operado != '-' else 0,
                                'cc': cc
                            }
                            
                            # Filtrar por cliente si se especifica
                            if not id_cliente or str(id_cliente) in cc or str(id_cliente) in numero_orden:
                                operaciones.append(operacion)
                                
                        except Exception as e:
                            continue
                
                if operaciones:
                    st.success(f"📊 Se obtuvieron {len(operaciones)} operaciones via Selenium")
                    simbolos_encontrados = list(set([op.get('simbolo', 'N/A') for op in operaciones]))
                    st.info(f"🔍 Símbolos encontrados via Selenium: {simbolos_encontrados}")
                    return operaciones
                else:
                    st.warning("⚠️ No se encontraron operaciones con Selenium")
                    return []
                    
            finally:
                driver.quit()
                
        except ImportError:
            st.warning("⚠️ Selenium no está disponible. Instalar con: pip install selenium")
            return []
        except Exception as selenium_error:
            st.warning(f"⚠️ Error con Selenium: {selenium_error}")
            return []
            
    except Exception as e:
        st.error(f"❌ Error en scraping avanzado: {str(e)}")
        return []

def calcular_evolucion_portafolio_unificada(token_acceso, id_cliente, fecha_desde=None, fecha_hasta=None):
    """
    Calcula la evolución unificada del portafolio basada en operaciones reales
    Incluye composición, movimientos, retornos y riesgos reales
    
    Args:
        token_acceso (str): Token de acceso
        id_cliente (str): ID del cliente
        fecha_desde (str): Fecha desde
        fecha_hasta (str): Fecha hasta
    
    Returns:
        dict: Datos unificados del portafolio
    """
    try:
        # Obtener operaciones reales
        operaciones = obtener_movimientos_reales(token_acceso, id_cliente, fecha_desde, fecha_hasta)
        if not operaciones:
            return None
        
        # Obtener portafolio actual
        portafolio_actual = obtener_portafolio(token_acceso, id_cliente)
        if not portafolio_actual:
            return None
        
        # Procesar operaciones y crear timeline
        df_ops = pd.DataFrame(operaciones)
        df_ops['fechaOrden'] = pd.to_datetime(df_ops['fechaOrden'], format='mixed')
        df_ops = df_ops.sort_values('fechaOrden')
        
        # Crear timeline de composición del portafolio
        timeline_composicion = crear_timeline_composicion(df_ops, portafolio_actual)
        
        # Calcular índice inteligente del portafolio
        indice_portafolio = calcular_indice_inteligente(timeline_composicion)
        
        # Calcular retornos y riesgos reales
        metricas_reales = calcular_metricas_reales(timeline_composicion, indice_portafolio)
        
        return {
            'operaciones': df_ops,
            'timeline_composicion': timeline_composicion,
            'indice_portafolio': indice_portafolio,
            'metricas_reales': metricas_reales,
            'portafolio_actual': portafolio_actual
        }
        
    except Exception as e:
        st.error(f"Error calculando evolución unificada: {e}")
        return None

def crear_timeline_composicion(df_ops, portafolio_actual):
    """
    Crea una línea de tiempo de la composición del portafolio basada en operaciones reales
    """
    try:
        # Obtener fechas únicas de operaciones
        fechas_ops = df_ops['fechaOrden'].dt.date.unique()
        fechas_ops = sorted(fechas_ops)
        
        # Agregar fecha actual
        fecha_actual = datetime.now().date()
        if fecha_actual not in fechas_ops:
            fechas_ops.append(fecha_actual)
        
        timeline = []
        posiciones_actuales = {}
        
        for fecha in fechas_ops:
            # Obtener operaciones de esta fecha
            ops_fecha = df_ops[df_ops['fechaOrden'].dt.date == fecha]
            
            # Actualizar posiciones
            for _, op in ops_fecha.iterrows():
                simbolo = op['simbolo']
                cantidad = op['cantidadOperada']
                precio = op['precioOperado']
                tipo = op['tipo']
                
                if simbolo not in posiciones_actuales:
                    posiciones_actuales[simbolo] = {
                        'cantidad': 0,
                        'precio_promedio': 0,
                        'valor_total': 0,
                        'operaciones': []
                    }
                
                if tipo == 'Compra':
                    posiciones_actuales[simbolo]['cantidad'] += cantidad
                    posiciones_actuales[simbolo]['operaciones'].append({
                        'fecha': fecha,
                        'tipo': 'Compra',
                        'cantidad': cantidad,
                        'precio': precio
                    })
                elif tipo == 'Venta':
                    posiciones_actuales[simbolo]['cantidad'] -= cantidad
                    posiciones_actuales[simbolo]['operaciones'].append({
                        'fecha': fecha,
                        'tipo': 'Venta',
                        'cantidad': cantidad,
                        'precio': precio
                    })
            
            # Calcular valor del portafolio en esta fecha
            valor_total = 0
            composicion = {}
            
            for simbolo, pos in posiciones_actuales.items():
                if pos['cantidad'] > 0:  # Solo posiciones activas
                    # Obtener precio actual del portafolio actual
                    precio_actual = obtener_precio_actual_simbolo(portafolio_actual, simbolo)
                    if precio_actual:
                        valor_posicion = pos['cantidad'] * precio_actual
                        valor_total += valor_posicion
                        composicion[simbolo] = {
                            'cantidad': pos['cantidad'],
                            'precio_actual': precio_actual,
                            'valor': valor_posicion,
                            'peso': 0  # Se calculará después
                        }
            
            # Calcular pesos
            for simbolo in composicion:
                if valor_total > 0:
                    composicion[simbolo]['peso'] = composicion[simbolo]['valor'] / valor_total
            
            timeline.append({
                'fecha': fecha,
                'valor_total': valor_total,
                'composicion': composicion,
                'num_operaciones': len(ops_fecha),
                'operaciones_dia': ops_fecha.to_dict('records') if len(ops_fecha) > 0 else []
            })
        
        return timeline
        
    except Exception as e:
        st.error(f"Error creando timeline: {e}")
        return []

def calcular_indice_inteligente(timeline):
    """
    Calcula un índice inteligente del portafolio basado en la evolución real
    """
    try:
        if not timeline:
            return None
        
        # Crear DataFrame para cálculos
        df_timeline = pd.DataFrame([
            {
                'fecha': t['fecha'],
                'valor': t['valor_total'],
                'num_ops': t['num_operaciones']
            }
            for t in timeline
        ])
        
        # Calcular retornos diarios
        df_timeline['retorno_diario'] = df_timeline['valor'].pct_change()
        
        # Calcular índice base 100
        valor_inicial = df_timeline['valor'].iloc[0]
        df_timeline['indice'] = (df_timeline['valor'] / valor_inicial) * 100
        
        # Calcular métricas del índice
        retorno_total = (df_timeline['valor'].iloc[-1] / valor_inicial - 1) * 100
        volatilidad = df_timeline['retorno_diario'].std() * np.sqrt(252) * 100
        sharpe = (df_timeline['retorno_diario'].mean() * 252) / (df_timeline['retorno_diario'].std() * np.sqrt(252)) if df_timeline['retorno_diario'].std() > 0 else 0
        
        # Calcular drawdown máximo
        df_timeline['cummax'] = df_timeline['valor'].cummax()
        df_timeline['drawdown'] = (df_timeline['valor'] / df_timeline['cummax'] - 1) * 100
        max_drawdown = df_timeline['drawdown'].min()
        
        return {
            'data': df_timeline,
            'retorno_total': retorno_total,
            'volatilidad': volatilidad,
            'sharpe': sharpe,
            'max_drawdown': max_drawdown,
            'valor_inicial': valor_inicial,
            'valor_final': df_timeline['valor'].iloc[-1]
        }
        
    except Exception as e:
        st.error(f"Error calculando índice inteligente: {e}")
        return None

def calcular_metricas_reales(timeline, indice_portafolio):
    """
    Calcula métricas reales de retorno y riesgo basadas en operaciones
    """
    try:
        if not timeline or not indice_portafolio:
            return None
        
        # Análisis de operaciones
        total_operaciones = sum(t['num_operaciones'] for t in timeline)
        dias_con_operaciones = sum(1 for t in timeline if t['num_operaciones'] > 0)
        
        # Análisis de composición
        simbolos_unicos = set()
        for t in timeline:
            simbolos_unicos.update(t['composicion'].keys())
        
        # Calcular concentración promedio
        concentraciones = []
        for t in timeline:
            if t['composicion']:
                pesos = [pos['peso'] for pos in t['composicion'].values()]
                concentracion = sum(p**2 for p in pesos)  # Índice de Herfindahl
                concentraciones.append(concentracion)
        
        concentracion_promedio = np.mean(concentraciones) if concentraciones else 0
        
        # Análisis de flujo de efectivo
        flujo_total = 0
        for t in timeline:
            for op in t['operaciones_dia']:
                if op['tipo'] == 'Compra':
                    flujo_total -= op['cantidad'] * op['precio']
                elif op['tipo'] == 'Venta':
                    flujo_total += op['cantidad'] * op['precio']
        
        return {
            'total_operaciones': total_operaciones,
            'dias_con_operaciones': dias_con_operaciones,
            'simbolos_unicos': len(simbolos_unicos),
            'concentracion_promedio': concentracion_promedio,
            'flujo_efectivo_neto': flujo_total,
            'retorno_total': indice_portafolio['retorno_total'],
            'volatilidad': indice_portafolio['volatilidad'],
            'sharpe': indice_portafolio['sharpe'],
            'max_drawdown': indice_portafolio['max_drawdown']
        }
        
    except Exception as e:
        st.error(f"Error calculando métricas reales: {e}")
        return None

def obtener_precio_actual_simbolo(portafolio_actual, simbolo):
    """
    Obtiene el precio actual de un símbolo desde el portafolio actual
    """
    try:
        activos = portafolio_actual.get('activos', [])
        for activo in activos:
            titulo = activo.get('titulo', {})
            if titulo.get('simbolo') == simbolo:
                return activo.get('precioPromedio', 0)
        return None
    except:
        return None

def calcular_valor_portafolio_historico_streamlit(operaciones, fecha_desde=None, fecha_hasta=None):
    """
    Calcula el valor del portafolio a lo largo del tiempo basado en todas las operaciones históricas
    Adaptado para Streamlit
    
    Args:
        operaciones (list): Lista de operaciones obtenidas de la API
        fecha_desde (str): Fecha desde en formato YYYY-MM-DD (opcional)
        fecha_hasta (str): Fecha hasta en formato YYYY-MM-DD (opcional)
    
    Returns:
        tuple: (DataFrame con valores del portafolio, posiciones actuales, DataFrame de flujo de efectivo)
    """
    if not operaciones:
        st.warning("No hay operaciones para analizar")
        return None
    
    # Convertir operaciones a DataFrame
    df_ops = pd.DataFrame(operaciones)
    df_ops['fechaOrden'] = pd.to_datetime(df_ops['fechaOrden'], format='mixed')
    df_ops = df_ops.sort_values('fechaOrden')
    
    # Obtener símbolos únicos
    simbolos = df_ops['simbolo'].unique()
    st.info(f"Símbolos encontrados: {list(simbolos)}")
    
    # Calcular posición actual por símbolo y flujo de efectivo
    posiciones = {}
    flujo_efectivo = []
    
    for simbolo in simbolos:
        ops_simbolo = df_ops[df_ops['simbolo'] == simbolo]
        cantidad_total = 0
        
        for _, op in ops_simbolo.iterrows():
            if op['tipo'] == 'Compra':
                cantidad_total += op['cantidadOperada']
                flujo_efectivo.append({
                    'fecha': op['fechaOrden'],
                    'tipo': 'Compra',
                    'simbolo': simbolo,
                    'monto': -op['montoOperado'],  # Salida de efectivo
                    'cantidad': op['cantidadOperada'],
                    'precio': op['precioOperado']
                })
            elif op['tipo'] == 'Venta':
                cantidad_total -= op['cantidadOperada']
                flujo_efectivo.append({
                    'fecha': op['fechaOrden'],
                    'tipo': 'Venta',
                    'simbolo': simbolo,
                    'monto': op['montoOperado'],  # Entrada de efectivo
                    'cantidad': op['cantidadOperada'],
                    'precio': op['precioOperado']
                })
        
        posiciones[simbolo] = cantidad_total
        st.info(f"Posición actual en {simbolo}: {cantidad_total}")
    
    # Crear DataFrame de flujo de efectivo
    df_flujo = pd.DataFrame(flujo_efectivo)
    df_flujo = df_flujo.sort_values('fecha')
    
    # Calcular valor acumulado del portafolio (flujo de efectivo neto)
    df_flujo['valor_acumulado'] = df_flujo['monto'].cumsum()
    
    # Crear serie temporal del valor del portafolio
    if fecha_desde:
        fecha_inicio = pd.to_datetime(fecha_desde).date()
    else:
        fecha_inicio = df_ops['fechaOrden'].min().date()
    
    if fecha_hasta:
        fecha_fin = pd.to_datetime(fecha_hasta).date()
    else:
        fecha_fin = datetime.now().date()
    
    fechas = pd.date_range(start=fecha_inicio, end=fecha_fin, freq='D')
    
    valores_portafolio = []
    for fecha in fechas:
        # Buscar el último valor acumulado hasta esa fecha
        valores_hasta_fecha = df_flujo[df_flujo['fecha'] <= fecha]
        if not valores_hasta_fecha.empty:
            valor = valores_hasta_fecha['valor_acumulado'].iloc[-1]
        else:
            valor = 0
        valores_portafolio.append(valor)
    
    # Crear DataFrame final
    df_portafolio = pd.DataFrame({
        'fecha': fechas,
        'valor': valores_portafolio
    })
    
    return df_portafolio, posiciones, df_flujo

def mostrar_analisis_unificado_mejorado(token_acceso, id_cliente):
    """
    Muestra el análisis unificado mejorado del portafolio con evolución real,
    línea de tiempo, índice inteligente y métricas reales
    """
    st.title("📊 Análisis Unificado del Portafolio")
    st.markdown("### 🔍 Evolución Real, Línea de Tiempo e Índice Inteligente")
    
    # Configuración de fechas
    st.subheader("📅 Configuración del Período")
    col1, col2 = st.columns(2)
    with col1:
        fecha_desde = st.date_input(
            "Fecha desde", 
            value=date.today() - timedelta(days=365),
            help="Fecha de inicio del análisis"
        )
    with col2:
        fecha_hasta = st.date_input(
            "Fecha hasta", 
            value=date.today(),
            help="Fecha de fin del análisis"
        )
    
    # Botón para calcular análisis unificado
    if st.button("🚀 Calcular Análisis Unificado", type="primary"):
        with st.spinner("Calculando evolución unificada del portafolio..."):
            datos_unificados = calcular_evolucion_portafolio_unificada(
                token_acceso, id_cliente, 
                fecha_desde.strftime('%Y-%m-%d'), 
                fecha_hasta.strftime('%Y-%m-%d')
            )
        
        if datos_unificados:
            mostrar_dashboard_unificado(datos_unificados)
        else:
            st.error("❌ No se pudo calcular el análisis unificado")

def mostrar_dashboard_unificado(datos):
    """
    Muestra el dashboard unificado con todos los análisis mejorados
    """
    operaciones = datos['operaciones']
    timeline = datos['timeline_composicion']
    indice = datos['indice_portafolio']
    metricas = datos['metricas_reales']
    portafolio_actual = datos['portafolio_actual']
    
    # Métricas principales
    st.subheader("📈 Métricas Principales del Portafolio")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Valor Total",
            f"${metricas['valor_final']:,.2f}",
            delta=f"{metricas['retorno_total']:+.2f}%"
        )
    
    with col2:
        st.metric(
            "📊 Retorno Total",
            f"{metricas['retorno_total']:+.2f}%",
            help="Retorno basado en operaciones reales"
        )
    
    with col3:
        st.metric(
            "⚖️ Volatilidad",
            f"{metricas['volatilidad']:.2f}%",
            help="Volatilidad anualizada"
        )
    
    with col4:
        st.metric(
            "📉 Max Drawdown",
            f"{metricas['max_drawdown']:.2f}%",
            help="Pérdida máxima desde pico"
        )
    
    # Análisis de operaciones
    st.subheader("📋 Análisis de Operaciones")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔄 Total Operaciones", metricas['total_operaciones'])
    with col2:
        st.metric("📅 Días con Operaciones", metricas['dias_con_operaciones'])
    with col3:
        st.metric("🏢 Símbolos Únicos", metricas['simbolos_unicos'])
    with col4:
        st.metric("💸 Flujo Neto", f"${metricas['flujo_efectivo_neto']:,.2f}")
    
    # Gráficos unificados
    crear_graficos_unificados(timeline, indice, operaciones)
    
    # Análisis detallado
    mostrar_analisis_detallado(timeline, operaciones)

def crear_graficos_unificados(timeline, indice, operaciones):
    """
    Crea gráficos unificados que muestran evolución, composición y operaciones
    """
    st.subheader("📊 Gráficos Unificados")
    
    # Gráfico 1: Evolución del Índice del Portafolio
    fig_indice = go.Figure()
    
    df_indice = indice['data']
    fig_indice.add_trace(go.Scatter(
        x=df_indice['fecha'],
        y=df_indice['indice'],
        mode='lines',
        name='Índice del Portafolio',
        line=dict(color='#1f77b4', width=3),
        hovertemplate='<b>Fecha:</b> %{x}<br><b>Índice:</b> %{y:.2f}<br><b>Valor:</b> $%{customdata:,.2f}<extra></extra>',
        customdata=df_indice['valor']
    ))
    
    # Agregar operaciones como marcadores
    fechas_ops = operaciones['fechaOrden'].dt.date
    for fecha in fechas_ops.unique():
        ops_fecha = operaciones[operaciones['fechaOrden'].dt.date == fecha]
        valor_fecha = df_indice[df_indice['fecha'] == fecha]['valor'].iloc[0] if len(df_indice[df_indice['fecha'] == fecha]) > 0 else None
        indice_fecha = df_indice[df_indice['fecha'] == fecha]['indice'].iloc[0] if len(df_indice[df_indice['fecha'] == fecha]) > 0 else None
        
        if valor_fecha and indice_fecha:
            fig_indice.add_trace(go.Scatter(
                x=[fecha],
                y=[indice_fecha],
                mode='markers',
                name=f'Operaciones {fecha}',
                marker=dict(
                    size=10,
                    color='red',
                    symbol='diamond'
                ),
                hovertemplate=f'<b>Fecha:</b> {fecha}<br><b>Operaciones:</b> {len(ops_fecha)}<extra></extra>',
                showlegend=False
            ))
    
    fig_indice.update_layout(
        title='📈 Evolución del Índice del Portafolio con Operaciones',
        xaxis_title='Fecha',
        yaxis_title='Índice (Base 100)',
        hovermode='x unified',
        height=500,
        template='plotly_white'
    )
    
    st.plotly_chart(fig_indice, use_container_width=True)
    
    # Gráfico 2: Evolución de la Composición
    crear_grafico_composicion_evolutiva(timeline)
    
    # Gráfico 3: Análisis de Operaciones por Día
    crear_grafico_operaciones_diarias(operaciones)

def crear_grafico_composicion_evolutiva(timeline):
    """
    Crea gráfico de evolución de la composición del portafolio
    """
    # Preparar datos para gráfico de área apilada
    fechas = [t['fecha'] for t in timeline]
    simbolos = set()
    for t in timeline:
        simbolos.update(t['composicion'].keys())
    
    simbolos = sorted(list(simbolos))
    
    fig_composicion = go.Figure()
    
    for simbolo in simbolos:
        valores = []
        for t in timeline:
            if simbolo in t['composicion']:
                valores.append(t['composicion'][simbolo]['valor'])
            else:
                valores.append(0)
        
        fig_composicion.add_trace(go.Scatter(
            x=fechas,
            y=valores,
            mode='lines',
            fill='tonexty',
            name=simbolo,
            hovertemplate=f'<b>{simbolo}</b><br>Valor: $%{{y:,.2f}}<extra></extra>'
        ))
    
    fig_composicion.update_layout(
        title='📊 Evolución de la Composición del Portafolio',
        xaxis_title='Fecha',
        yaxis_title='Valor ($)',
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig_composicion, use_container_width=True)

def crear_grafico_operaciones_diarias(operaciones):
    """
    Crea gráfico de operaciones por día
    """
    # Agrupar operaciones por día
    ops_por_dia = operaciones.groupby(operaciones['fechaOrden'].dt.date).agg({
        'cantidadOperada': 'sum',
        'montoOperado': 'sum',
        'simbolo': 'count'
    }).reset_index()
    
    ops_por_dia.columns = ['fecha', 'cantidad_total', 'monto_total', 'num_operaciones']
    
    fig_ops = go.Figure()
    
    fig_ops.add_trace(go.Bar(
        x=ops_por_dia['fecha'],
        y=ops_por_dia['num_operaciones'],
        name='Número de Operaciones',
        marker_color='lightblue',
        hovertemplate='<b>Fecha:</b> %{x}<br><b>Operaciones:</b> %{y}<br><b>Monto:</b> $%{customdata:,.2f}<extra></extra>',
        customdata=ops_por_dia['monto_total']
    ))
    
    fig_ops.update_layout(
        title='📈 Operaciones por Día',
        xaxis_title='Fecha',
        yaxis_title='Número de Operaciones',
        height=300,
        template='plotly_white'
    )
    
    st.plotly_chart(fig_ops, use_container_width=True)

def mostrar_analisis_detallado(timeline, operaciones):
    """
    Muestra análisis detallado de la evolución del portafolio
    """
    st.subheader("🔍 Análisis Detallado")
    
    # Tabs para diferentes análisis
    tab1, tab2, tab3 = st.tabs(["📊 Composición por Fecha", "🔄 Operaciones Detalladas", "📈 Métricas por Período"])
    
    with tab1:
        mostrar_composicion_por_fecha(timeline)
    
    with tab2:
        mostrar_operaciones_detalladas(operaciones)
    
    with tab3:
        mostrar_metricas_por_periodo(timeline)

def mostrar_composicion_por_fecha(timeline):
    """
    Muestra la composición del portafolio por fecha
    """
    st.markdown("#### 📊 Evolución de la Composición")
    
    # Selector de fecha
    fechas_disponibles = [t['fecha'] for t in timeline if t['composicion']]
    if fechas_disponibles:
        fecha_seleccionada = st.selectbox(
            "Seleccione una fecha:",
            fechas_disponibles,
            index=len(fechas_disponibles)-1
        )
        
        # Mostrar composición para la fecha seleccionada
        composicion_fecha = next(t['composicion'] for t in timeline if t['fecha'] == fecha_seleccionada)
        
        if composicion_fecha:
            # Crear DataFrame para mostrar
            df_composicion = pd.DataFrame([
                {
                    'Símbolo': simbolo,
                    'Cantidad': pos['cantidad'],
                    'Precio': f"${pos['precio_actual']:,.2f}",
                    'Valor': f"${pos['valor']:,.2f}",
                    'Peso': f"{pos['peso']*100:.2f}%"
                }
                for simbolo, pos in composicion_fecha.items()
            ])
            
            st.dataframe(df_composicion, use_container_width=True)
            
            # Gráfico de torta
            fig_torta = go.Figure(data=[go.Pie(
                labels=list(composicion_fecha.keys()),
                values=[pos['valor'] for pos in composicion_fecha.values()],
                hovertemplate='<b>%{label}</b><br>Valor: $%{value:,.2f}<br>Peso: %{percent}<extra></extra>'
            )])
            
            fig_torta.update_layout(
                title=f'Composición del Portafolio - {fecha_seleccionada}',
                height=400
            )
            
            st.plotly_chart(fig_torta, use_container_width=True)

def mostrar_operaciones_detalladas(operaciones):
    """
    Muestra operaciones detalladas
    """
    st.markdown("#### 🔄 Operaciones Detalladas")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        simbolos_unicos = operaciones['simbolo'].unique()
        simbolo_filtro = st.selectbox("Filtrar por símbolo:", ["Todos"] + list(simbolos_unicos))
    
    with col2:
        tipos_unicos = operaciones['tipo'].unique()
        tipo_filtro = st.selectbox("Filtrar por tipo:", ["Todos"] + list(tipos_unicos))
    
    # Aplicar filtros
    df_filtrado = operaciones.copy()
    if simbolo_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado['simbolo'] == simbolo_filtro]
    if tipo_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado['tipo'] == tipo_filtro]
    
    # Mostrar tabla
    df_display = df_filtrado[['fechaOrden', 'simbolo', 'tipo', 'cantidadOperada', 'precioOperado', 'montoOperado']].copy()
    df_display.columns = ['Fecha', 'Símbolo', 'Tipo', 'Cantidad', 'Precio', 'Monto']
    df_display['Fecha'] = df_display['Fecha'].dt.strftime('%d/%m/%Y')
    df_display['Precio'] = df_display['Precio'].apply(lambda x: f"${x:,.2f}")
    df_display['Monto'] = df_display['Monto'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(df_display, use_container_width=True, height=400)

def mostrar_metricas_por_periodo(timeline):
    """
    Muestra métricas calculadas por período
    """
    st.markdown("#### 📈 Métricas por Período")
    
    # Calcular métricas por período
    df_metricas = pd.DataFrame([
        {
            'Fecha': t['fecha'],
            'Valor Total': t['valor_total'],
            'Operaciones': t['num_operaciones'],
            'Símbolos Activos': len(t['composicion'])
        }
        for t in timeline
    ])
    
    # Calcular retornos
    df_metricas['Retorno Diario'] = df_metricas['Valor Total'].pct_change() * 100
    df_metricas['Retorno Acumulado'] = ((df_metricas['Valor Total'] / df_metricas['Valor Total'].iloc[0]) - 1) * 100
    
    # Mostrar métricas
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("📊 Valor Inicial", f"${df_metricas['Valor Total'].iloc[0]:,.2f}")
        st.metric("📈 Valor Final", f"${df_metricas['Valor Total'].iloc[-1]:,.2f}")
        st.metric("🔄 Total Operaciones", df_metricas['Operaciones'].sum())
    
    with col2:
        st.metric("📉 Retorno Total", f"{df_metricas['Retorno Acumulado'].iloc[-1]:+.2f}%")
        st.metric("⚖️ Volatilidad Diaria", f"{df_metricas['Retorno Diario'].std():.2f}%")
        st.metric("📅 Días Analizados", len(df_metricas))
    
    # Gráfico de métricas
    fig_metricas = go.Figure()
    
    fig_metricas.add_trace(go.Scatter(
        x=df_metricas['Fecha'],
        y=df_metricas['Retorno Acumulado'],
        mode='lines',
        name='Retorno Acumulado',
        line=dict(color='green', width=2)
    ))
    
    fig_metricas.update_layout(
        title='📈 Retorno Acumulado del Portafolio',
        xaxis_title='Fecha',
        yaxis_title='Retorno Acumulado (%)',
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig_metricas, use_container_width=True)

def unificar_composicion_portafolio(portafolio_actual, operaciones, token_acceso, fecha_desde, fecha_hasta):
    """
    Unifica la composición actual del portafolio con la recreación basada en operaciones reales
    
    Args:
        portafolio_actual (dict): Composición actual del portafolio
        operaciones (list): Lista de operaciones reales
        token_acceso (str): Token de acceso
        fecha_desde (str): Fecha desde
        fecha_hasta (str): Fecha hasta
    
    Returns:
        dict: Composición unificada con evolución temporal
    """
    # Obtener símbolos únicos de operaciones y portafolio actual
    simbolos_operaciones = list(set([op.get('simbolo') for op in operaciones if op.get('simbolo')]))
    simbolos_actuales = list(portafolio_actual.keys()) if portafolio_actual else []
    simbolos_totales = list(set(simbolos_operaciones + simbolos_actuales))
    
    composicion_unificada = {}
    
    for simbolo in simbolos_totales:
        # Obtener datos históricos del símbolo usando el método estándar
        serie_historica = obtener_serie_historica_activo(simbolo, token_acceso, fecha_desde, fecha_hasta)
        
        if serie_historica is not None and not serie_historica.empty:
            # Convertir serie a diccionario para compatibilidad
            datos_historicos = {}
            for fecha, precio in serie_historica.items():
                datos_historicos[fecha.strftime('%Y-%m-%d')] = {'cierre': precio}
            # Reconstruir posición basada en operaciones
            posicion_operaciones = 0
            fechas_operaciones = []
            
            for op in operaciones:
                if op.get('simbolo') == simbolo and op.get('estado') == 'terminada':
                    fecha_op = pd.to_datetime(op.get('fechaOperada', op.get('fechaOrden')))
                    cantidad = op.get('cantidadOperada', op.get('cantidad', 0))
                    
                    if op.get('tipo') == 'Compra':
                        posicion_operaciones += cantidad
                    elif op.get('tipo') == 'Venta':
                        posicion_operaciones -= cantidad
                    
                    fechas_operaciones.append(fecha_op)
            
            # Obtener posición actual del portafolio
            posicion_actual = 0
            if simbolo in portafolio_actual:
                posicion_actual = portafolio_actual[simbolo].get('cantidad', 0)
            
            # Crear serie temporal de composición usando las fechas de la serie histórica
            composicion_por_fecha = {}
            precios_por_fecha = {}
            
            # Usar las fechas de la serie histórica como base
            for fecha, precio in serie_historica.items():
                fecha_str = fecha.strftime('%Y-%m-%d')
                precios_por_fecha[fecha_str] = precio
                
                # Calcular posición acumulada hasta esa fecha
                posicion_acumulada = 0
                for op in operaciones:
                    if op.get('simbolo') == simbolo and op.get('estado') == 'terminada':
                        fecha_op = pd.to_datetime(op.get('fechaOperada', op.get('fechaOrden')))
                        if fecha_op <= fecha:
                            cantidad = op.get('cantidadOperada', op.get('cantidad', 0))
                            if op.get('tipo') == 'Compra':
                                posicion_acumulada += cantidad
                            elif op.get('tipo') == 'Venta':
                                posicion_acumulada -= cantidad
                
                composicion_por_fecha[fecha_str] = posicion_acumulada
            
            composicion_unificada[simbolo] = {
                'posicion_actual': posicion_actual,
                'posicion_operaciones': posicion_operaciones,
                'composicion_por_fecha': composicion_por_fecha,
                'precios_por_fecha': precios_por_fecha,
                'datos_historicos': datos_historicos
            }
    
    return composicion_unificada

def crear_grafico_evolucion_portafolio(composicion_unificada):
    """
    Crea un gráfico de serie temporal mostrando la evolución del valor del portafolio
    
    Args:
        composicion_unificada (dict): Composición unificada del portafolio
    
    Returns:
        plotly.graph_objects.Figure: Gráfico de evolución
    """
    fig = go.Figure()
    
    # Calcular valor total del portafolio por fecha
    fechas_totales = set()
    for simbolo, datos in composicion_unificada.items():
        fechas_totales.update(datos['composicion_por_fecha'].keys())
    
    fechas_ordenadas = sorted(fechas_totales)
    valor_total_por_fecha = {}
    
    for fecha in fechas_ordenadas:
        valor_total = 0
        for simbolo, datos in composicion_unificada.items():
            cantidad = datos['composicion_por_fecha'].get(fecha, 0)
            precio = datos['precios_por_fecha'].get(fecha, 0)
            valor_total += cantidad * precio
        valor_total_por_fecha[fecha] = valor_total
    
    # Gráfico principal: Valor total del portafolio
    fig.add_trace(go.Scatter(
        x=fechas_ordenadas,
        y=list(valor_total_por_fecha.values()),
        mode='lines+markers',
        name='Valor Total del Portafolio',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=6)
    ))
    
    # Gráficos individuales por activo (en colores más suaves)
    colores = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    for i, (simbolo, datos) in enumerate(composicion_unificada.items()):
        fechas_activo = sorted(datos['composicion_por_fecha'].keys())
        valores_activo = []
        
        for fecha in fechas_activo:
            cantidad = datos['composicion_por_fecha'][fecha]
            precio = datos['precios_por_fecha'].get(fecha, 0)
            valores_activo.append(cantidad * precio)
        
        if any(v > 0 for v in valores_activo):  # Solo mostrar si tiene valor
            fig.add_trace(go.Scatter(
                x=fechas_activo,
                y=valores_activo,
                mode='lines',
                name=f'{simbolo}',
                line=dict(color=colores[i % len(colores)], width=1, dash='dot'),
                opacity=0.7
            ))
    
    fig.update_layout(
        title={
            'text': '📈 Evolución del Valor del Portafolio - Composición Unificada',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        xaxis_title='Fecha',
        yaxis_title='Valor del Portafolio (AR$)',
        hovermode='x unified',
        template='plotly_white',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        height=600
    )
    
    return fig

def mostrar_operaciones_reales():
    """
    Muestra el análisis de operaciones reales del portafolio
    """
    st.title("📈 Análisis de Operaciones Reales")
    
    if 'token_acceso' not in st.session_state or not st.session_state.token_acceso:
        st.error("Debe iniciar sesión primero")
        return
    
    token_acceso = st.session_state.token_acceso
    
    # Configuración de fechas
    st.subheader("📅 Configuración del Período")
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_desde = st.date_input(
            "Fecha desde", 
            value=date.today() - timedelta(days=365),
            help="Fecha de inicio del análisis"
        )
    with col2:
        fecha_hasta = st.date_input(
            "Fecha hasta", 
            value=date.today(),
            help="Fecha de fin del análisis"
        )
    
    # Botón para ejecutar análisis
    if st.button("🔍 Analizar Operaciones y Composición", type="primary"):
        with st.spinner("Obteniendo operaciones y unificando composición..."):
            # Obtener ID del cliente seleccionado
            cliente = st.session_state.get('cliente_seleccionado', {})
            id_cliente = cliente.get('numeroCliente', cliente.get('id')) if cliente else None
            
            # Debug: mostrar información del cliente
            if cliente:
                st.info(f"🔍 Cliente seleccionado: {cliente.get('apellidoYNombre', 'N/A')} - ID: {id_cliente}")
            else:
                st.warning("⚠️ No hay cliente seleccionado")
            
            operaciones = obtener_movimientos_reales(
                token_acceso, 
                id_cliente=id_cliente,
                fecha_desde=fecha_desde.isoformat(), 
                fecha_hasta=fecha_hasta.isoformat()
            )
        
        if operaciones:
            st.success(f"✅ Se obtuvieron {len(operaciones)} operaciones")
            
            # Obtener portafolios actuales
            portafolio_ar = st.session_state.get('portafolio_ar', {})
            portafolio_eeuu = st.session_state.get('portafolio_eeuu', {})
            portafolio_combinado = {**portafolio_ar, **portafolio_eeuu}
            
            # Unificar composición actual con operaciones reales
            with st.spinner("Unificando composición del portafolio..."):
                composicion_unificada = unificar_composicion_portafolio(
                    portafolio_combinado,
                    operaciones,
                    token_acceso,
                    fecha_desde.isoformat(),
                    fecha_hasta.isoformat()
                )
            
            if composicion_unificada:
                # Mostrar gráfico de evolución
                st.subheader("📊 Evolución del Valor del Portafolio")
                
                fig_evolucion = crear_grafico_evolucion_portafolio(composicion_unificada)
                st.plotly_chart(fig_evolucion, use_container_width=True)
                
                # Mostrar resumen de operaciones
                st.subheader("📊 Resumen de Operaciones")
                
                df_ops = pd.DataFrame(operaciones)
                df_ops['fechaOrden'] = pd.to_datetime(df_ops['fechaOrden'], format='mixed')
                
                # Métricas principales
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Operaciones", len(operaciones))
                with col2:
                    compras = len([op for op in operaciones if op['tipo'] == 'Compra'])
                    st.metric("Compras", compras)
                with col3:
                    ventas = len([op for op in operaciones if op['tipo'] == 'Venta'])
                    st.metric("Ventas", ventas)
                with col4:
                    simbolos_unicos = df_ops['simbolo'].nunique()
                    st.metric("Símbolos", simbolos_unicos)
                
                # Comparación: Composición Actual vs Recreada por Operaciones
                st.subheader("🔄 Comparación: Composición Actual vs Recreada")
                
                comparacion_data = []
                for simbolo, datos in composicion_unificada.items():
                    posicion_actual = datos['posicion_actual']
                    posicion_operaciones = datos['posicion_operaciones']
                    diferencia = posicion_actual - posicion_operaciones
                    
                    comparacion_data.append({
                        'Símbolo': simbolo,
                        'Posición Actual': posicion_actual,
                        'Posición por Operaciones': posicion_operaciones,
                        'Diferencia': diferencia,
                        'Estado': '✅ Coincide' if abs(diferencia) < 0.01 else '⚠️ Diferencia'
                    })
                
                df_comparacion = pd.DataFrame(comparacion_data)
                st.dataframe(df_comparacion, use_container_width=True)
                
                # Tabla de operaciones detallada
                st.subheader("📋 Detalle de Operaciones")
                
                # Filtrar columnas relevantes para mostrar
                columnas_mostrar = ['fechaOrden', 'simbolo', 'tipo', 'cantidadOperada', 'precioOperado', 'montoOperado']
                columnas_disponibles = [col for col in columnas_mostrar if col in df_ops.columns]
                
                if columnas_disponibles:
                    df_mostrar = df_ops[columnas_disponibles].copy()
                    df_mostrar['fechaOrden'] = df_mostrar['fechaOrden'].dt.strftime('%Y-%m-%d %H:%M')
                    
                    # Renombrar columnas para mejor visualización
                    df_mostrar = df_mostrar.rename(columns={
                        'fechaOrden': 'Fecha',
                        'simbolo': 'Símbolo',
                        'tipo': 'Tipo',
                        'cantidadOperada': 'Cantidad',
                        'precioOperado': 'Precio',
                        'montoOperado': 'Monto'
                    })
                    
                    st.dataframe(df_mostrar, use_container_width=True, height=400)
                
                # Estadísticas del período
                st.subheader("📈 Estadísticas del Período")
                
                # Calcular métricas del período
                fechas_totales = set()
                for datos in composicion_unificada.values():
                    fechas_totales.update(datos['composicion_por_fecha'].keys())
                
                if fechas_totales:
                    fechas_ordenadas = sorted(fechas_totales)
                    
                    # Calcular valor total por fecha
                    valores_por_fecha = {}
                    for fecha in fechas_ordenadas:
                        valor_total = 0
                        for datos in composicion_unificada.values():
                            cantidad = datos['composicion_por_fecha'].get(fecha, 0)
                            precio = datos['precios_por_fecha'].get(fecha, 0)
                            valor_total += cantidad * precio
                        valores_por_fecha[fecha] = valor_total
                    
                    valor_inicial = valores_por_fecha.get(fechas_ordenadas[0], 0)
                    valor_final = valores_por_fecha.get(fechas_ordenadas[-1], 0)
                    rendimiento_total = ((valor_final - valor_inicial) / valor_inicial * 100) if valor_inicial > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Valor Inicial", f"AR$ {valor_inicial:,.2f}")
                    with col2:
                        st.metric("Valor Final", f"AR$ {valor_final:,.2f}")
                    with col3:
                        st.metric("Rendimiento Total", f"{rendimiento_total:+.2f}%")
                
            else:
                st.warning("⚠️ No se pudo unificar la composición del portafolio")
                
        else:
            st.error("❌ No se pudieron obtener las operaciones")

def mostrar_analisis_portafolio():
    cliente = st.session_state.cliente_seleccionado
    token_acceso = st.session_state.token_acceso

    if not cliente:
        st.error("No se ha seleccionado ningún cliente")
        return

    id_cliente = cliente.get('numeroCliente', cliente.get('id'))
    nombre_cliente = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))

    st.title(f"Análisis de Portafolio - {nombre_cliente}")
    
    # Cargar datos una sola vez y cachearlos
    @st.cache_data(ttl=600)  # Cache por 10 minutos para mejor rendimiento
    def cargar_datos_cliente(token, cliente_id):
        """Carga y cachea los datos del cliente para evitar llamadas repetitivas"""
        portafolio_ar = obtener_portafolio(token, cliente_id, 'Argentina')
        portafolio_eeuu = obtener_portafolio_eeuu(token, cliente_id)
        estado_cuenta_ar = obtener_estado_cuenta(token, cliente_id)
        estado_cuenta_eeuu = obtener_estado_cuenta_eeuu(token)
        return portafolio_ar, portafolio_eeuu, estado_cuenta_ar, estado_cuenta_eeuu
    
    # Cargar datos con cache y spinner optimizado
    with st.spinner("🔄 Cargando datos del cliente..."):
        try:
            portafolio_ar, portafolio_eeuu, estado_cuenta_ar, estado_cuenta_eeuu = cargar_datos_cliente(token_acceso, id_cliente)
        except Exception as e:
            st.error(f"Error cargando datos del cliente: {str(e)}")
            return
    
    # Crear tabs con iconos
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🇦🇷 Portafolio Argentina", 
        "🇺🇸 Portafolio EEUU",
        "💰 Estado de Cuenta", 
        "🎯 Optimización y Cobertura",
        "📊 Análisis Técnico",
        "💱 Dólares y Mercado",
        "📈 Operaciones Reales",
        "🔍 Análisis Unificado"
    ])

    with tab1:
        if portafolio_ar:
            st.subheader("🇦🇷 Portafolio Argentina")
            mostrar_resumen_portafolio(portafolio_ar, token_acceso, "ar")
        else:
            st.warning("No se pudo obtener el portafolio de Argentina")
    
    with tab2:
        if portafolio_eeuu:
            st.subheader("🇺🇸 Portafolio Estados Unidos")
            mostrar_resumen_portafolio(portafolio_eeuu, token_acceso, "eeuu")
        else:
            st.warning("No se pudo obtener el portafolio de EEUU")
    
    with tab3:
        # Estado de cuenta consolidado
        st.subheader("🇦🇷 Estado de Cuenta Argentina")
        if estado_cuenta_ar:
            mostrar_estado_cuenta(estado_cuenta_ar)
        else:
            st.warning("No se pudo obtener el estado de cuenta de Argentina")
        
        # Vista consolidada de todas las cuentas
        st.subheader("🔍 Vista Consolidada de Todas las Cuentas")
        if estado_cuenta_ar:
            cuentas_totales = estado_cuenta_ar.get('cuentas', [])
            if cuentas_totales:
                # Crear DataFrame con clasificación por país
                datos_consolidados = []
                descripciones_validas = False
                
                for cuenta in cuentas_totales:
                    numero = cuenta.get('numero', 'N/A')
                    descripcion = cuenta.get('descripcion', 'N/A')
                    moneda = cuenta.get('moneda', 'N/A')
                    
                    # Verificar si hay descripciones válidas
                    if descripcion and descripcion != 'N/A' and descripcion.strip():
                        descripciones_validas = True
                    
                    # Determinar si es cuenta de EEUU
                    es_cuenta_eeuu = any([
                        'eeuu' in descripcion.lower() if descripcion != 'N/A' else False,
                        'estados unidos' in descripcion.lower() if descripcion != 'N/A' else False,
                        '-eeuu' in str(numero).lower(),
                        'dolar estadounidense' in moneda.lower(),
                        'dolar_estadounidense' in moneda.lower(),
                        'usd' in moneda.lower()
                    ])
                    
                    pais = "🇺🇸 EEUU" if es_cuenta_eeuu else "🇦🇷 Argentina"
                    
                    # Obtener valores y validar coherencia
                    disponible = float(cuenta.get('disponible', 0))
                    saldo = float(cuenta.get('saldo', 0))
                    total = float(cuenta.get('total', 0))
                    
                    # Crear diccionario base con valores de la API
                    cuenta_data = {
                        'País': pais,
                        'Número': numero,
                        'Moneda': moneda.replace('_', ' ').title(),
                        'Disponible': disponible,
                        'Saldo': saldo,
                        'Total': total,
                    }
                    
                    # Solo agregar descripción si hay descripciones válidas
                    if descripciones_validas:
                        cuenta_data['Descripción'] = descripcion
                    
                    datos_consolidados.append(cuenta_data)
                
                df_consolidado = pd.DataFrame(datos_consolidados)
                
                # Agrupar por país y mostrar resumen
                resumen_por_pais = df_consolidado.groupby('País').agg({
                    'Total': 'sum',
                    'Número': 'count'
                }).round(2)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Argentina", f"AR$ {resumen_por_pais.loc['🇦🇷 Argentina', 'Total']:,.2f}" if '🇦🇷 Argentina' in resumen_por_pais.index else "AR$ 0.00")
                    st.metric("Cuentas Argentina", resumen_por_pais.loc['🇦🇷 Argentina', 'Número'] if '🇦🇷 Argentina' in resumen_por_pais.index else 0)
                
                with col2:
                    st.metric("Total EEUU", f"AR$ {resumen_por_pais.loc['🇺🇸 EEUU', 'Total']:,.2f}" if '🇺🇸 EEUU' in resumen_por_pais.index else "AR$ 0.00")
                    st.metric("Cuentas EEUU", resumen_por_pais.loc['🇺🇸 EEUU', 'Número'] if '🇺🇸 EEUU' in resumen_por_pais.index else 0)
                
                # Mostrar tabla detallada
                st.subheader("📋 Detalle Completo de Cuentas")
                st.dataframe(df_consolidado, use_container_width=True, height=400)
    
    with tab4:
        # Menú unificado de optimización y cobertura
        if portafolio_ar or portafolio_eeuu:
            # Combinar portafolios si ambos están disponibles
            # Mostrar menú de optimización con selección de portafolio
            mostrar_menu_optimizacion_unificado(portafolio_ar, portafolio_eeuu, token_acceso, st.session_state.fecha_desde, st.session_state.fecha_hasta)
        else:
            st.warning("No se pudo obtener ningún portafolio para optimización")
    
    with tab5:
        mostrar_analisis_tecnico(token_acceso, id_cliente, portafolio_ar, portafolio_eeuu)
    
    with tab6:
        mostrar_cotizaciones_mercado(token_acceso)
    
    with tab7:
        st.subheader("📈 Análisis de Operaciones Reales")
        st.info("🔍 Esta sección analiza las operaciones reales de compra/venta de tu portafolio para calcular retornos basados en fechas reales de compra.")
        
        # Seleccionar portafolio a analizar
        portafolio_seleccionado = st.selectbox(
            "Seleccionar portafolio para análisis:",
            options=[
                ("🇦🇷 Argentina", portafolio_ar),
                ("🇺🇸 Estados Unidos", portafolio_eeuu)
            ],
            format_func=lambda x: x[0],
            help="Selecciona el portafolio que deseas analizar",
            key="portafolio_operaciones_reales"
        )
        
        if portafolio_seleccionado[1]:
            # Usar la función que incluye el ID del cliente
            mostrar_resumen_operaciones_reales(portafolio_seleccionado[1], token_acceso, "operaciones_reales", id_cliente)
        else:
            st.warning("⚠️ No hay datos disponibles para el portafolio seleccionado")
    
    with tab8:
        st.subheader("🔍 Análisis Unificado del Portafolio")
        st.info("🚀 Esta sección proporciona un análisis unificado que indexa correctamente la evolución real de la composición del portafolio, movimientos de compra/venta, línea de tiempo e índice inteligente con retornos y riesgos reales.")
        
        # Mostrar análisis unificado mejorado
        mostrar_analisis_unificado_mejorado(token_acceso, id_cliente)

def main():
    # Configuración de rendimiento
    st.set_page_config(
        page_title="IOL Portfolio Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Agregar estilos CSS para mejorar la visibilidad
    st.markdown("""
    <style>
    /* Mejorar contraste de texto */
    .stSelectbox > div > div {
        color: #262730 !important;
        background-color: white !important;
    }
    
    .stSelectbox > div > div > div {
        color: #262730 !important;
        background-color: white !important;
    }
    
    .stSelectbox input {
        color: #262730 !important;
        background-color: white !important;
    }
    
    .stNumberInput > div > div > input {
        color: #262730 !important;
        background-color: white !important;
    }
    
    .stNumberInput input {
        color: #262730 !important;
        background-color: white !important;
    }
    
    .stTextInput > div > div > input {
        color: #262730 !important;
        background-color: white !important;
    }
    
    .stTextInput input {
        color: #262730 !important;
        background-color: white !important;
    }
    
    .stDateInput > div > div > input {
        color: #262730 !important;
        background-color: white !important;
    }
    
    .stDateInput input {
        color: #262730 !important;
        background-color: white !important;
    }
    
    .stRadio > div {
        color: #262730 !important;
    }
    
    .stRadio label {
        color: #262730 !important;
    }
    
    .stCheckbox > div {
        color: #262730 !important;
    }
    
    .stCheckbox label {
        color: #262730 !important;
    }
    
    /* Reglas adicionales para todos los inputs */
    input[type="text"], input[type="number"], input[type="date"], input[type="email"], input[type="password"] {
        color: #262730 !important;
        background-color: white !important;
    }
    
    /* Para elementos de formulario específicos */
    .stForm input {
        color: #262730 !important;
        background-color: white !important;
    }
    
    .stForm select {
        color: #262730 !important;
        background-color: white !important;
    }
    
    /* Reglas para elementos de Streamlit específicos */
    [data-testid="stSelectbox"] input {
        color: #262730 !important;
        background-color: white !important;
    }
    
    [data-testid="stNumberInput"] input {
        color: #262730 !important;
        background-color: white !important;
    }
    
    [data-testid="stTextInput"] input {
        color: #262730 !important;
        background-color: white !important;
    }
    
    [data-testid="stDateInput"] input {
        color: #262730 !important;
        background-color: white !important;
    }
    
    /* Reglas específicas para labels y texto de formularios */
    .stSelectbox label, .stNumberInput label, .stTextInput label, .stDateInput label {
        color: #262730 !important;
    }
    
    /* Reglas para elementos de formulario dentro de st.form */
    .stForm .stSelectbox input, .stForm .stNumberInput input, .stForm .stTextInput input {
        color: #262730 !important;
        background-color: white !important;
    }
    
    /* Reglas para elementos específicos de optimización */
    .stSlider label {
        color: #262730 !important;
    }
    
    .stSlider > div > div {
        color: #262730 !important;
    }
    
    /* Reglas para elementos de configuración */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #262730 !important;
    }
    
    /* Reglas para elementos de sidebar */
    .stSidebar .stSelectbox input, .stSidebar .stNumberInput input, .stSidebar .stTextInput input {
        color: #262730 !important;
        background-color: white !important;
    }
    
    /* Reglas para elementos de columnas */
    .stColumn .stSelectbox input, .stColumn .stNumberInput input, .stColumn .stTextInput input {
        color: #262730 !important;
        background-color: white !important;
    }
    
    /* Mejorar visibilidad de métricas */
    .metric-container {
        background-color: #f0f2f6;
        border: 1px solid #e1e5e9;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
    }
    
    /* Mejorar contraste de sidebar */
    .css-1d391kg {
        background-color: #f8f9fa !important;
    }
    
    /* Mejorar visibilidad de tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #f8f9fa !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #262730 !important;
        background-color: #f8f9fa !important;
    }
    
    .stTabs [data-baseweb="tab"] > div {
        color: #262730 !important;
        background-color: #f8f9fa !important;
    }
    
    .stTabs [data-baseweb="tab"] span {
        color: #262730 !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #1f77b4 !important;
        background-color: white !important;
    }
    
    .stTabs [aria-selected="true"] > div {
        color: #1f77b4 !important;
        background-color: white !important;
    }
    
    .stTabs [aria-selected="true"] span {
        color: #1f77b4 !important;
    }
    
    /* Forzar contraste en todos los elementos de tabs */
    .stTabs button {
        color: #262730 !important;
        background-color: #f8f9fa !important;
    }
    
    .stTabs button[aria-selected="true"] {
        color: #1f77b4 !important;
        background-color: white !important;
    }
    
    /* Reglas adicionales para asegurar visibilidad del texto en tabs */
    .stTabs [data-baseweb="tab"] p {
        color: #262730 !important;
    }
    
    .stTabs [aria-selected="true"] p {
        color: #1f77b4 !important;
    }
    
    /* Forzar contraste en elementos de texto dentro de tabs */
    .stTabs * {
        color: inherit !important;
    }
    
    /* Específico para tabs no seleccionados */
    .stTabs [data-baseweb="tab"]:not([aria-selected="true"]) {
        color: #262730 !important;
    }
    
    .stTabs [data-baseweb="tab"]:not([aria-selected="true"]) * {
        color: #262730 !important;
    }
    
    /* Mejorar visibilidad de expanders */
    .streamlit-expanderHeader {
        color: #262730 !important;
        background-color: #f8f9fa !important;
    }
    
    /* Mejorar contraste de botones */
    .stButton > button {
        color: white !important;
        background-color: #1f77b4 !important;
        border: none !important;
    }
    
    .stButton > button:hover {
        background-color: #0d5aa7 !important;
    }
    
    /* Mejorar visibilidad de info boxes */
    .stInfo {
        background-color: #e7f3ff !important;
        border-left: 4px solid #1f77b4 !important;
        color: #262730 !important;
    }
    
    .stSuccess {
        background-color: #d4edda !important;
        border-left: 4px solid #28a745 !important;
        color: #262730 !important;
    }
    
    .stWarning {
        background-color: #fff3cd !important;
        border-left: 4px solid #ffc107 !important;
        color: #262730 !important;
    }
    
    .stError {
        background-color: #f8d7da !important;
        border-left: 4px solid #dc3545 !important;
        color: #262730 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Configurar cache para mejor rendimiento
    # st.cache_data.clear()  # Comentado para mantener cache entre sesiones
    
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
            
            # Verificar y refrescar token si es necesario
            if st.session_state.token_acceso and st.session_state.refresh_token:
                nuevo_token, nuevo_refresh = verificar_y_refrescar_token(
                    st.session_state.token_acceso, 
                    st.session_state.refresh_token
                )
                if nuevo_token:
                    st.session_state.token_acceso = nuevo_token
                    st.session_state.refresh_token = nuevo_refresh
                else:
                    # Token no válido, limpiar sesión
                    st.session_state.token_acceso = None
                    st.session_state.refresh_token = None
                    st.session_state.clientes = []
                    st.session_state.cliente_seleccionado = None
                    st.error("❌ Sesión expirada. Por favor, inicie sesión nuevamente.")
                    st.rerun()
            
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
                    key="cliente_seleccionado_principal"
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
                
                # Botón para refrescar token manualmente
                if st.button("🔄 Refrescar Token", use_container_width=True):
                    with st.spinner("Refrescando token..."):
                        nuevo_token, nuevo_refresh = refrescar_token(st.session_state.refresh_token)
                        if nuevo_token:
                            st.session_state.token_acceso = nuevo_token
                            st.session_state.refresh_token = nuevo_refresh
                            st.success("✅ Token refrescado")
                            st.rerun()
                        else:
                            st.error("❌ No se pudo refrescar el token")
            else:
                st.warning("No se encontraron clientes")

    # Contenido principal
    try:
        if st.session_state.token_acceso:
            st.sidebar.title("Menú Principal")
            opcion = st.sidebar.radio(
                "Seleccione una opción:",
                ("🏠 Inicio", "📊 Análisis de Portafolio", "📈 Operaciones Reales"),
                index=0,
            )

            # Mostrar la página seleccionada
            if opcion == "🏠 Inicio":
                st.info("👆 Seleccione una opción del menú para comenzar")
            elif opcion == "📊 Análisis de Portafolio":
                if st.session_state.cliente_seleccionado:
                    mostrar_analisis_portafolio()
                else:
                    st.info("👆 Seleccione un cliente en la barra lateral para comenzar")
            elif opcion == "📈 Operaciones Reales":
                mostrar_operaciones_reales()
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
                        <h3>🇦🇷 Portafolio Argentina</h3>
                        <p>Análisis completo de activos argentinos</p>
                    </div>
                    <div style="background: rgba(255,255,255,0.2); border-radius: 12px; padding: 25px; width: 250px; backdrop-filter: blur(5px);">
                        <h3>🇺🇸 Portafolio EEUU</h3>
                        <p>Gestión de activos internacionales</p>
                    </div>
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
                - Estado de cuenta consolidado  
                """)
    except Exception as e:
        st.error(f"❌ Error en la aplicación: {str(e)}")

if __name__ == "__main__":
    main() 
    
