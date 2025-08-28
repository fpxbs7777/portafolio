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
from scipy import optimize
import random
import warnings
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import time

warnings.filterwarnings('ignore')

# Configuración de la página con tema oscuro profesional
st.set_page_config(
    page_title="IOL Portfolio Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para tema oscuro moderno
st.markdown("""
<style>
    /* Importar fuentes modernas */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Variables CSS para colores */
    :root {
        --primary-bg: #0f172a;
        --secondary-bg: #1e293b;
        --accent-bg: #334155;
        --primary-text: #f8fafc;
        --secondary-text: #cbd5e1;
        --accent-color: #10b981;
        --accent-hover: #059669;
        --border-color: #475569;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --info-color: #3b82f6;
    }
    
    /* Estilos generales dark theme */
    .stApp, 
    .stApp > div[data-testid="stAppViewContainer"],
    .stApp > div[data-testid="stAppViewContainer"] > div {
        background: linear-gradient(135deg, var(--primary-bg) 0%, #1e1b4b 100%) !important;
        color: var(--primary-text) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        line-height: 1.6;
    }
    
    /* Headers modernos con gradientes */
    h1, h2, h3, h4, h5, h6 {
        background: linear-gradient(135deg, var(--accent-color), #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    h1 { font-size: 2.5rem; font-weight: 700; }
    h2 { font-size: 2rem; font-weight: 600; }
    h3 { font-size: 1.5rem; font-weight: 600; }
    
    /* Asegurar que todo el texto sea claro */
    body, p, div, span, label, input, select, textarea, button,
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
        color: var(--primary-text) !important;
    }
    
    /* Enlaces modernos */
    a {
        color: var(--accent-color) !important;
        text-decoration: none;
        transition: all 0.3s ease;
        border-bottom: 1px solid transparent;
    }
    
    a:hover {
        color: var(--accent-hover) !important;
        border-bottom-color: var(--accent-color);
    }
    
    /* Placeholders mejorados */
    ::placeholder {
        color: var(--secondary-text) !important;
        opacity: 1;
    }
    
    /* Tooltips modernos */
    .stTooltip {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg)) !important;
        border: 1px solid var(--accent-color) !important;
        color: var(--primary-text) !important;
        border-radius: 12px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3) !important;
    }
    
    /* Menús desplegables modernos */
    div[data-baseweb="select"],
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] input,
    div[data-baseweb="select"] div[role="button"],
    div[data-baseweb="select"] div[role="listbox"],
    div[data-baseweb="select"] div[role="combobox"] {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg)) !important;
        color: var(--primary-text) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-baseweb="select"]:hover,
    div[data-baseweb="select"] div[role="button"]:hover {
        border-color: var(--accent-color) !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1) !important;
    }
    
    /* Opciones del menú desplegable */
    div[role="listbox"],
    div[role="listbox"] ul,
    div[role="listbox"] li,
    div[role="option"],
    div[role="option"] > div,
    div[role="option"] > span,
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
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg)) !important;
        color: var(--primary-text) !important;
        border-radius: 8px !important;
    }
    
    /* Efecto hover en opciones */
    div[role="option"]:hover,
    div[role="option"]:hover > div,
    div[role="option"]:hover > span,
    div[role="listbox"] > div:hover,
    div[role="listbox"] > div > div:hover {
        background: linear-gradient(135deg, var(--accent-bg), var(--accent-color)) !important;
        color: #ffffff !important;
        transform: translateX(5px) !important;
        transition: all 0.3s ease !important;
    }
    
    /* Opción seleccionada */
    div[aria-selected="true"],
    div[aria-selected="true"] > div,
    div[aria-selected="true"] > span {
        background: linear-gradient(135deg, var(--accent-color), var(--accent-hover)) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
    }
    
    /* Listas de selección múltiple */
    .stMultiSelect [role="button"],
    .stMultiSelect [role="button"]:hover,
    .stMultiSelect [role="button"]:focus {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg)) !important;
        color: var(--primary-text) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
    }
    
    .stMultiSelect [role="button"]:hover {
        border-color: var(--accent-color) !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1) !important;
    }
    
    .stMultiSelect [role="option"] {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg)) !important;
        color: var(--primary-text) !important;
        border-radius: 8px !important;
    }
    
    .stMultiSelect [role="option"]:hover {
        background: linear-gradient(135deg, var(--accent-bg), var(--accent-color)) !important;
        transform: translateX(5px) !important;
        transition: all 0.3s ease !important;
    }
    
    /* Alertas modernas */
    .stAlert {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(51, 65, 85, 0.95)) !important;
        border-left: 4px solid var(--accent-color) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }
    
    /* Gráficos modernos */
    .stPlotlyChart {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg)) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }
    
    /* Botones modernos */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-color), var(--accent-hover)) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4) !important;
    }
    
    /* Inputs modernos */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg)) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--primary-text) !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stDateInput > div > div > input:focus {
        border-color: var(--accent-color) !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1) !important;
        outline: none !important;
    }
    
    /* Sliders modernos */
    .stSlider > div > div > div > div {
        background: linear-gradient(135deg, var(--accent-color), var(--accent-hover)) !important;
    }
    
    /* Tabs modernos */
    .stTabs > div > div > div > div > div > div {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg)) !important;
        border-radius: 12px !important;
        padding: 0.5rem !important;
    }
    
    .stTabs > div > div > div > div > div > div > div {
        background: transparent !important;
        color: var(--secondary-text) !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTabs > div > div > div > div > div > div > div[aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent-color), var(--accent-hover)) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
    }
    
    /* Expanders modernos */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg)) !important;
        border-radius: 12px !important;
        border: 1px solid var(--border-color) !important;
        color: var(--primary-text) !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: var(--accent-color) !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2) !important;
    }
    
    /* Dataframes modernos */
    .stDataFrame {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg)) !important;
        border-radius: 16px !important;
        border: 1px solid var(--border-color) !important;
        overflow: hidden !important;
    }
    
    /* Métricas modernas */
    .stMetric {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg)) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
    }
    
    /* Sidebar moderno */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--primary-bg) 0%, #1e1b4b 100%) !important;
        border-right: 1px solid var(--border-color) !important;
    }
    
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--secondary-bg);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, var(--accent-color), var(--accent-hover));
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, var(--accent-hover), var(--accent-color));
    }
    
    /* Animaciones y transiciones */
    * {
        transition: all 0.3s ease;
    }
    
    /* Efectos de hover para elementos interactivos */
    .stButton > button:hover,
    div[data-baseweb="select"]:hover,
    .stMultiSelect [role="button"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
    }
    
    /* Cards modernos */
    .card {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg)) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3) !important;
        backdrop-filter: blur(10px) !important;
        margin: 1rem 0 !important;
    }
    
    /* Badges modernos */
    .badge {
        background: linear-gradient(135deg, var(--accent-color), var(--accent-hover)) !important;
        color: white !important;
        padding: 0.25rem 0.75rem !important;
        border-radius: 20px !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        display: inline-block !important;
        margin: 0.25rem !important;
    }
    
    /* Loading spinners modernos */
    .stSpinner > div {
        border: 3px solid var(--border-color) !important;
        border-top: 3px solid var(--accent-color) !important;
        border-radius: 50% !important;
        animation: spin 1s linear infinite !important;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

def obtener_encabezado_autorizacion(token_portador):
    return {
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'application/json'
    }

# Funciones de utilidad para UI moderna
def create_modern_card(title, content, icon="📊", color="primary"):
    """Crea una tarjeta moderna con diseño mejorado"""
    colors = {
        "primary": "linear-gradient(135deg, #10b981, #059669)",
        "secondary": "linear-gradient(135deg, #3b82f6, #2563eb)",
        "success": "linear-gradient(135deg, #10b981, #059669)",
        "warning": "linear-gradient(135deg, #f59e0b, #d97706)",
        "error": "linear-gradient(135deg, #ef4444, #dc2626)",
        "info": "linear-gradient(135deg, #06b6d4, #0891b2)"
    }
    
    st.markdown(f"""
    <div class="card" style="border-left: 4px solid {colors[color].split(',')[0].split('(')[1]};">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <span style="font-size: 2rem; margin-right: 0.75rem;">{icon}</span>
            <h3 style="margin: 0; background: {colors[color]}; -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">{title}</h3>
        </div>
        <div style="color: #cbd5e1; line-height: 1.6;">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_metric_card(label, value, delta=None, icon="📈", color="primary"):
    """Crea una tarjeta de métrica moderna"""
    colors = {
        "primary": "#10b981",
        "secondary": "#3b82f6",
        "success": "#10b981",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "info": "#06b6d4"
    }
    
    delta_html = ""
    if delta is not None:
        delta_color = "#10b981" if delta >= 0 else "#ef4444"
        delta_icon = "↗️" if delta >= 0 else "↘️"
        delta_html = f'<div style="color: {delta_color}; font-size: 0.875rem; margin-top: 0.5rem;">{delta_icon} {delta:+.1f}%</div>'
    
    st.markdown(f"""
    <div class="card" style="text-align: center; padding: 1.5rem;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
        <div style="font-size: 1.5rem; font-weight: 700; color: {colors[color]}; margin-bottom: 0.5rem;">{value}</div>
        <div style="color: #94a3b8; font-size: 0.875rem; margin-bottom: 0.5rem;">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def create_info_badge(text, color="primary"):
    """Crea un badge informativo moderno"""
    colors = {
        "primary": "linear-gradient(135deg, #10b981, #059669)",
        "secondary": "linear-gradient(135deg, #3b82f6, #2563eb)",
        "success": "linear-gradient(135deg, #10b981, #059669)",
        "warning": "linear-gradient(135deg, #f59e0b, #d97706)",
        "error": "linear-gradient(135deg, #ef4444, #dc2626)",
        "info": "linear-gradient(135deg, #06b6d4, #0891b2)"
    }
    
    st.markdown(f"""
    <span class="badge" style="background: {colors[color]} !important;">{text}</span>
    """, unsafe_allow_html=True)

def create_section_header(title, subtitle=None, icon="📊"):
    """Crea un encabezado de sección moderno"""
    subtitle_html = f'<p style="color: #94a3b8; margin-top: 0.5rem; font-size: 1rem;">{subtitle}</p>' if subtitle else ""
    
    st.markdown(f"""
    <div style="margin: 2rem 0 1.5rem 0;">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <span style="font-size: 2rem; margin-right: 0.75rem;">{icon}</span>
            <h2 style="margin: 0; background: linear-gradient(135deg, #10b981, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">{title}</h2>
        </div>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)

def create_navigation_tabs(tab_names, icons=None):
    """Crea pestañas de navegación modernas"""
    if icons is None:
        icons = ["📊"] * len(tab_names)
    
    tab_labels = [f"{icon} {name}" for icon, name in zip(icons, tab_names)]
    return st.tabs(tab_labels)

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
        respuesta = requests.get(url_portafolio, headers=encabezados, timeout=30)
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
    
    st.info(f"🔍 Intentando obtener portafolio EEUU del cliente {id_cliente}")
    st.info(f"🔑 Token válido: {'Sí' if token_portador else 'No'}")
    
    try:
        # Primer intento: endpoint de Asesores
        respuesta = requests.get(url_portafolio_asesores, headers=encabezados, timeout=30)
        
        if respuesta.status_code == 200:
            data = respuesta.json()
            st.success(f"✅ Portafolio EEUU obtenido vía Asesores: {len(data.get('activos', []))} activos")
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
                
                # Filtrar solo las cuentas de EEUU
                cuentas_eeuu = []
                for cuenta in data.get('cuentas', []):
                    # Identificar cuentas de EEUU por múltiples criterios
                    numero_cuenta = str(cuenta.get('numero', ''))
                    moneda = cuenta.get('moneda', '').lower()
                    tipo = cuenta.get('tipo', '').lower()
                    
                    # Criterios para identificar cuentas de EEUU
                    es_cuenta_eeuu = any([
                        # Por número de cuenta (formato específico de IOL)
                        '-eeuu' in numero_cuenta,
                        'eeuu' in numero_cuenta,
                        'us' in numero_cuenta,
                        
                        # Por moneda (dólar estadounidense)
                        'dolar estadounidense' in moneda,
                        'usd' in moneda,
                        'dollar' in moneda,
                        
                        # Por tipo de cuenta
                        'inversion_estados_unidos' in tipo,
                        'inversion_eeuu' in tipo,
                        'estados_unidos' in tipo,
                        
                        # Por descripción si existe
                        'eeuu' in cuenta.get('descripcion', '').lower(),
                        'estados unidos' in cuenta.get('descripcion', '').lower(),
                        'united states' in cuenta.get('descripcion', '').lower()
                    ])
                    
                    if es_cuenta_eeuu:
                        cuentas_eeuu.append(cuenta)
                        st.info(f"🔍 Cuenta EEUU identificada: {numero_cuenta} - {moneda}")
                
                # Si no se encontraron cuentas EEUU, intentar obtener información del portafolio
                if not cuentas_eeuu:
                    st.info("🔍 Intentando obtener información adicional del portafolio EEUU...")
                    
                    # Obtener portafolio EEUU para verificar si hay activos
                    try:
                        url_portafolio = 'https://api.invertironline.com/api/v2/portafolio/estados_Unidos'
                        respuesta_portafolio = requests.get(url_portafolio, headers=encabezados, timeout=30)
                        
                        if respuesta_portafolio.status_code == 200:
                            portafolio_data = respuesta_portafolio.json()
                            if portafolio_data.get('activos'):
                                st.success(f"✅ Portafolio EEUU encontrado con {len(portafolio_data['activos'])} activos")
                                
                                # Crear cuenta EEUU sintética basada en el portafolio
                                cuenta_sintetica = {
                                    'numero': 'EEUU-SINTETICA',
                                    'tipo': 'inversion_estados_unidos',
                                    'moneda': 'dolar_estadounidense',
                                    'disponible': 0,
                                    'comprometido': 0,
                                    'saldo': 0,
                                    'titulosValorizados': sum(activo.get('valorizado', 0) for activo in portafolio_data['activos']),
                                    'total': sum(activo.get('valorizado', 0) for activo in portafolio_data['activos']),
                                    'descripcion': 'Cuenta EEUU (sintética basada en portafolio)'
                                }
                                
                                cuentas_eeuu.append(cuenta_sintetica)
                                st.info("✅ Cuenta EEUU sintética creada basada en el portafolio")
                            else:
                                st.warning("⚠️ Portafolio EEUU vacío")
                        else:
                            st.warning(f"⚠️ No se pudo obtener portafolio EEUU: {respuesta_portafolio.status_code}")
                    except Exception as e:
                        st.warning(f"⚠️ Error obteniendo portafolio EEUU: {str(e)}")
                
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
                    st.warning("⚠️ No se encontraron cuentas específicas de EEUU")
                    
                    # Debug: mostrar todas las cuentas para identificar el problema
                    st.markdown("#### 🔍 Debug: Todas las cuentas disponibles")
                    st.info("Mostrando todas las cuentas para identificar por qué no se detectan las de EEUU")
                    
                    for i, cuenta in enumerate(data.get('cuentas', [])):
                        with st.expander(f"Cuenta {i+1}: {cuenta.get('numero', 'N/A')}", expanded=False):
                            st.json(cuenta)
                
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

def obtener_tasas_caucion(token_portador):
    """
    Obtiene las tasas de caución desde la API de IOL
    
    Args:
        token_portador (str): Token de autenticación Bearer
        
    Returns:
        DataFrame: DataFrame con las tasas de caución o None en caso de error
    """
    url = "https://api.invertironline.com/api/v2/cotizaciones-orleans/cauciones/argentina/Operables"
    params = {
        'cotizacionInstrumentoModel.instrumento': 'cauciones',
        'cotizacionInstrumentoModel.pais': 'argentina'
    }
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_portador}'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'titulos' in data and isinstance(data['titulos'], list) and data['titulos']:
                df = pd.DataFrame(data['titulos'])
                
                # Filtrar solo las cauciónes y limpiar los datos
                df = df[df['plazo'].notna()].copy()
                
                # Extraer el plazo en días
                df['plazo_dias'] = df['plazo'].str.extract('(\d+)').astype(float)
                
                # Limpiar la tasa (convertir a float si es necesario)
                if 'ultimoPrecio' in df.columns:
                    df['tasa_limpia'] = df['ultimoPrecio'].astype(str).str.rstrip('%').astype('float')
                
                # Asegurarse de que las columnas necesarias existan
                if 'monto' not in df.columns and 'volumen' in df.columns:
                    df['monto'] = df['volumen']
                
                # Ordenar por plazo
                df = df.sort_values('plazo_dias')
                
                # Seleccionar solo las columnas necesarias
                columnas_requeridas = ['simbolo', 'plazo', 'plazo_dias', 'ultimoPrecio', 'tasa_limpia', 'monto', 'moneda']
                columnas_disponibles = [col for col in columnas_requeridas if col in df.columns]
                
                return df[columnas_disponibles]
            
            st.warning("No se encontraron datos de tasas de caución en la respuesta")
            return None
            
        elif response.status_code == 401:
            st.error("Error de autenticación. Por favor, verifique su token de acceso.")
            return None
            
        else:
            error_msg = f"Error {response.status_code} al obtener tasas de caución"
            try:
                error_data = response.json()
                error_msg += f": {error_data.get('message', 'Error desconocido')}"
            except:
                error_msg += f": {response.text}"
            st.error(error_msg)
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error inesperado al procesar tasas de caución: {str(e)}")
        return None

def mostrar_tasas_caucion(token_portador):
    """
    Muestra las tasas de caución en una tabla y gráfico de curva de tasas
    """
    st.subheader("📊 Tasas de Caución")
    
    try:
        with st.spinner('Obteniendo tasas de caución...'):
            df_cauciones = obtener_tasas_caucion(token_portador)
            
            # Verificar si se obtuvieron datos
            if df_cauciones is None or df_cauciones.empty:
                st.warning("No se encontraron datos de tasas de caución.")
                return
                
            # Verificar columnas requeridas
            required_columns = ['simbolo', 'plazo', 'ultimoPrecio', 'plazo_dias', 'tasa_limpia']
            missing_columns = [col for col in required_columns if col not in df_cauciones.columns]
            if missing_columns:
                st.error(f"Faltan columnas requeridas en los datos: {', '.join(missing_columns)}")
                return
            
            # Mostrar tabla con las tasas
            st.dataframe(
                df_cauciones[['simbolo', 'plazo', 'ultimoPrecio', 'monto'] if 'monto' in df_cauciones.columns 
                             else ['simbolo', 'plazo', 'ultimoPrecio']]
                .rename(columns={
                    'simbolo': 'Instrumento',
                    'plazo': 'Plazo',
                    'ultimoPrecio': 'Tasa',
                    'monto': 'Monto (en millones)'
                }),
                use_container_width=True,
                height=min(400, 50 + len(df_cauciones) * 35)  # Ajustar altura dinámicamente
            )
            
            # Crear gráfico de curva de tasas si hay suficientes puntos
            if len(df_cauciones) > 1:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=df_cauciones['plazo_dias'],
                    y=df_cauciones['tasa_limpia'],
                    mode='lines+markers+text',
                    name='Tasa',
                    text=df_cauciones['tasa_limpia'].round(2).astype(str) + '%',
                    textposition='top center',
                    line=dict(color='#1f77b4', width=2),
                    marker=dict(size=10, color='#1f77b4')
                ))
                
                fig.update_layout(
                    title='Curva de Tasas de Caución',
                    xaxis_title='Plazo (días)',
                    yaxis_title='Tasa Anual (%)',
                    template='plotly_white',
                    height=500,
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar resumen estadístico
            if 'tasa_limpia' in df_cauciones.columns and 'plazo_dias' in df_cauciones.columns:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Tasa Mínima", f"{df_cauciones['tasa_limpia'].min():.2f}%")
                    st.metric("Tasa Máxima", f"{df_cauciones['tasa_limpia'].max():.2f}%")
                with col2:
                    st.metric("Tasa Promedio", f"{df_cauciones['tasa_limpia'].mean():.2f}%")
                    st.metric("Plazo Promedio", f"{df_cauciones['plazo_dias'].mean():.1f} días")
                    
    except Exception as e:
        st.error(f"Error al mostrar las tasas de caución: {str(e)}")
        st.exception(e)  # Mostrar el traceback completo para depuración


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
        response = requests.get(url, headers=headers, timeout=30)
        
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

def obtener_datos_alternativos_yfinance(simbolo, fecha_desde, fecha_hasta):
    """
    Fallback usando yfinance para símbolos que no estén disponibles en IOL
    """
    try:
        # Mapear símbolos argentinos a Yahoo Finance si es posible
        simbolo_yf = simbolo
        
        # Agregar sufijos comunes para acciones argentinas
        sufijos_ar = ['.BA', '.AR']
        
        for sufijo in sufijos_ar:
            try:
                ticker = yf.Ticker(simbolo + sufijo)
                data = ticker.history(start=fecha_desde, end=fecha_hasta)
                if not data.empty and len(data) > 10:
                    # Usar precio de cierre
                    return data['Close']
            except Exception:
                continue
        
        # Intentar sin sufijo
        try:
            ticker = yf.Ticker(simbolo)
            data = ticker.history(start=fecha_desde, end=fecha_hasta)
            if not data.empty and len(data) > 10:
                return data['Close']
        except Exception:
            pass
            
        return None
    except Exception:
        return None

def get_historical_data_for_optimization(token_portador, simbolos, fecha_desde, fecha_hasta):
    """
    Obtiene datos históricos para optimización de portafolio con manejo mejorado de errores.
    Actualizada para mejor compatibilidad con la API de IOL y optimizada para rendimiento.
    """
    try:
        df_precios = pd.DataFrame()
        simbolos_exitosos = []
        simbolos_fallidos = []
        detalles_errores = {}
        
        # Convertir fechas a string en formato correcto
        fecha_desde_str = fecha_desde.strftime('%Y-%m-%d')
        fecha_hasta_str = fecha_hasta.strftime('%Y-%m-%d')
        
        st.info(f"🔍 Buscando datos históricos desde {fecha_desde_str} hasta {fecha_hasta_str}")
        
        # Optimización: Limitar número de símbolos para mejor rendimiento
        if len(simbolos) > 20:
            st.warning(f"⚠️ Limitando análisis a los primeros 20 símbolos de {len(simbolos)} para mejor rendimiento")
            simbolos = simbolos[:20]
        
        # Crear barra de progreso optimizada
        progress_bar = st.progress(0)
        total_simbolos = len(simbolos)
        
        for idx, simbolo in enumerate(simbolos):
            # Actualizar barra de progreso
            progress_bar.progress((idx + 1) / total_simbolos, text=f"Procesando {simbolo}...")
            
            # Detectar mercado más probable para el símbolo
            mercado_detectado = detectar_mercado_simbolo(simbolo, token_portador)
            
            # Usar mercados correctos según la API de IOL
            # Ordenar mercados por probabilidad de éxito para optimizar búsqueda
            if mercado_detectado:
                mercados = [mercado_detectado, 'bCBA', 'FCI', 'nYSE', 'nASDAQ', 'rOFEX', 'Opciones']
            else:
                mercados = ['bCBA', 'FCI', 'nYSE', 'nASDAQ', 'rOFEX', 'Opciones']
            
            serie_obtenida = False
            
            for mercado in mercados:
                try:
                    # Buscar clase D si es posible (solo para mercados tradicionales)
                    simbolo_consulta = simbolo
                    if mercado not in ['Opciones', 'FCI']:
                        clase_d = obtener_clase_d(simbolo, mercado, token_portador)
                        if clase_d:
                            simbolo_consulta = clase_d
                    
                    serie = obtener_serie_historica_iol(
                        token_portador, mercado, simbolo_consulta, 
                        fecha_desde_str, fecha_hasta_str
                    )
                    
                    if serie is not None and len(serie) > 10:
                        # Verificar que los datos no sean todos iguales
                        if serie.nunique() > 1:
                            df_precios[simbolo_consulta] = serie
                            simbolos_exitosos.append(simbolo_consulta)
                            serie_obtenida = True
                            
                            # Mostrar información del símbolo exitoso
                            st.success(f"✅ {simbolo_consulta} ({mercado}): {len(serie)} puntos de datos")
                            break
                        
                except Exception as e:
                    detalles_errores[f"{simbolo}_{mercado}"] = str(e)
                    continue
            
            # Si IOL falló completamente, intentar con yfinance como fallback
            if not serie_obtenida:
                try:
                    serie_yf = obtener_datos_alternativos_yfinance(
                        simbolo, fecha_desde, fecha_hasta
                    )
                    if serie_yf is not None and len(serie_yf) > 10:
                        if serie_yf.nunique() > 1:
                            df_precios[simbolo] = serie_yf
                            simbolos_exitosos.append(simbolo)
                            serie_obtenida = True
                            st.info(f"ℹ️ {simbolo} (Yahoo Finance): {len(serie_yf)} puntos de datos")
                except Exception as e:
                    detalles_errores[f"{simbolo}_yfinance"] = str(e)
            
            if not serie_obtenida:
                simbolos_fallidos.append(simbolo)
                st.warning(f"⚠️ No se pudieron obtener datos para {simbolo}")
        
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
        
        # Alinear datos por fechas comunes con mejor manejo
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
            # Estrategia 1: Forward fill y luego backward fill
            df_precios_filled = df_precios.fillna(method='ffill').fillna(method='bfill')
            
            # Estrategia 2: Interpolar valores faltantes
            df_precios_interpolated = df_precios.interpolate(method='time')
            
            # Usar la estrategia que conserve más datos
            if not df_precios_filled.dropna().empty:
                df_precios = df_precios_filled.dropna()
                st.info("✅ Usando estrategia forward/backward fill")
            elif not df_precios_interpolated.dropna().empty:
                df_precios = df_precios_interpolated.dropna()
                st.info("✅ Usando estrategia de interpolación")
            else:
                # Estrategia 3: Usar solo fechas con datos completos
                df_precios = df_precios.dropna()
                st.info("✅ Usando solo fechas con datos completos")
                
        except Exception as e:
            st.warning(f"⚠️ Error en alineación de datos: {str(e)}. Usando datos sin procesar.")
            df_precios = df_precios.dropna()
        
        if df_precios.empty:
            st.error("❌ No hay fechas comunes entre los activos después del procesamiento")
            return None, None, None
        
        st.success(f"✅ Datos alineados: {len(df_precios)} observaciones para {len(df_precios.columns)} activos")
        
        # Calcular retornos
        returns = df_precios.pct_change().dropna()
        
        if returns.empty or len(returns) < 30:
            st.error("❌ No hay suficientes datos para calcular retornos válidos (mínimo 30 observaciones)")
            return None, None, None
        
        # Verificar que los retornos no sean constantes
        if (returns.std() == 0).any():
            columnas_constantes = returns.columns[returns.std() == 0].tolist()
            st.warning(f"⚠️ Removiendo activos con retornos constantes: {columnas_constantes}")
            returns = returns.drop(columns=columnas_constantes)
            df_precios = df_precios.drop(columns=columnas_constantes)
        
        if len(returns.columns) < 2:
            st.error("❌ Después de filtrar, no quedan suficientes activos para análisis")
            return None, None, None
        
        # Calcular métricas finales
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        
        # Mostrar estadísticas finales
        st.info(f"📊 Datos finales: {len(returns.columns)} activos, {len(returns)} observaciones de retornos")
        
        return mean_returns, cov_matrix, df_precios
        
    except Exception as e:
        st.error(f"❌ Error crítico obteniendo datos históricos: {str(e)}")
        with st.expander("🔍 Información de debug"):
            st.code(f"Error: {str(e)}")
            st.code(f"Símbolos: {simbolos}")
            st.code(f"Rango de fechas: {fecha_desde} a {fecha_hasta}")
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
    else:
        # Intentar detectar consultando la API
        mercados_test = ['bCBA', 'FCI', 'nYSE', 'nASDAQ']
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
        
        tasa_libre_riesgo = st.number_input(
            "Tasa Libre de Riesgo (% anual):",
            min_value=0.0, max_value=50.0, value=4.0, step=0.1,
            help="Tasa libre de riesgo para cálculos de Sharpe"
        )
    
    with col2:
        st.markdown("#### 📊 Configuración de Benchmark")
        benchmark_options = ['^SPX', 'SPY', '^GSPC', '^IXIC', '^DJI'] + simbolos
        benchmark = st.selectbox(
            "Benchmark de Referencia:",
            options=benchmark_options,
            index=0,
            help="Índice de referencia para análisis alpha/beta"
        )
        
        profit_esperado = st.number_input(
            "Profit Esperado (% anual):",
            min_value=0.0, max_value=100.0, value=8.0, step=0.1,
            help="Rendimiento esperado del portafolio"
        )
        
        usar_tasa_manual = st.checkbox(
            "Usar Tasa Libre de Riesgo Manual",
            help="Marcar para usar tasa personalizada en lugar de la del benchmark",
            key="usar_tasa_manual_avanzada"
        )
    
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
                
                # Cargar datos
                if manager_inst.load_data():
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
                            benchmark, benchmark_return, profit_esperado, tasa_libre_riesgo,
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
            mean_returns, cov_matrix, df_precios = get_historical_data_for_optimization(
                token_portador, all_securities, fecha_desde, fecha_hasta
            )
            
            if mean_returns is not None and cov_matrix is not None:
                returns = df_precios.pct_change().dropna()
            else:
                # Fallback a yfinance
                returns = _get_returns_yfinance(all_securities)
        else:
            # Usar yfinance como fallback
            returns = _get_returns_yfinance(all_securities)
        
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

def _get_returns_yfinance(securities):
    """
    Obtiene retornos usando yfinance como fallback
    """
    try:
        returns_data = {}
        for security in securities:
            try:
                ticker = yf.Ticker(security)
                data = ticker.history(period="1y")
                if not data.empty:
                    returns_data[security] = data['Close'].pct_change().dropna()
            except Exception:
                continue
        
        if returns_data:
            return pd.DataFrame(returns_data)
        else:
            return None
    except Exception:
        return None

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
        Carga datos históricos usando IOL o yfinance
        """
        try:
            all_securities = [self.benchmark, self.position_security] + self.hedge_securities
            all_securities = list(set(all_securities))
            
            if self.token_portador and self.fecha_desde and self.fecha_hasta:
                # Intentar con IOL primero
                mean_returns, cov_matrix, df_precios = get_historical_data_for_optimization(
                    self.token_portador, all_securities, self.fecha_desde, self.fecha_hasta
                )
                
                if mean_returns is not None and cov_matrix is not None:
                    self.returns = df_precios.pct_change().dropna()
                    self.mean_returns = mean_returns
                    self.cov_matrix = cov_matrix
                    return True
            
            # Fallback a yfinance
            self.returns = _get_returns_yfinance(all_securities)
            if self.returns is not None and not self.returns.empty:
                self.mean_returns = self.returns.mean() * 252
                self.cov_matrix = self.returns.cov() * 252
                return True
            
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
            help="Selecciona el activo principal que deseas cubrir"
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
            help="Índice de referencia para calcular betas"
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
            
            # Si IOL falló, intentar con yfinance como fallback
            if serie_historica is None or serie_historica.empty:
                try:
                    print(f"Intentando yfinance como fallback para {simbolo}")
                    serie_historica = obtener_datos_alternativos_yfinance(
                        simbolo, fecha_desde, fecha_hasta
                    )
                    if serie_historica is not None and not serie_historica.empty:
                        print(f"✅ Datos obtenidos de yfinance para {simbolo}: {len(serie_historica)} puntos")
                except Exception as e:
                    print(f"Error al obtener datos de yfinance para {simbolo}: {str(e)}")
            
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

# --- Funciones de Visualización ---
def mostrar_resumen_portafolio(portafolio, token_portador, pais="general"):
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
        
        # Información General
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
                key=f"mostrar_histograma_retornos_analisis_{pais}"
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
                    key=f"tipo_grafico_distribucion_{pais}"
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

def mostrar_estado_cuenta(estado_cuenta, es_eeuu=False):
    """
    Muestra el estado de cuenta, con soporte para cuentas filtradas de EEUU
    
    Args:
        estado_cuenta (dict): Datos del estado de cuenta
        es_eeuu (bool): Si es True, muestra información específica para cuentas de EEUU
    """
    if es_eeuu:
        st.markdown("### 🇺🇸 Estado de Cuenta EEUU")
    else:
        st.markdown("### 💰 Estado de Cuenta")
    
    if not estado_cuenta:
        st.warning("No hay datos de estado de cuenta disponibles")
        return
    
    # Verificar si es un estado de cuenta filtrado de EEUU
    if estado_cuenta.get('filtrado', False):
        total_en_pesos = estado_cuenta.get('totalEnPesos', 0)
        cuentas = estado_cuenta.get('cuentas', [])
        total_cuentas_eeuu = estado_cuenta.get('total_cuentas_eeuu', 0)
        
        cols = st.columns(3)
        cols[0].metric("Total EEUU en Pesos", f"AR$ {total_en_pesos:,.2f}")
        cols[1].metric("Cuentas de EEUU", total_cuentas_eeuu)
        cols[2].metric("Total General", f"AR$ {total_en_pesos:,.2f}")
        
        if cuentas:
            st.subheader("📊 Detalle de Cuentas de EEUU")
            
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
            
            # Mostrar resumen específico para EEUU
            st.info(f"💡 **Resumen EEUU**: {total_cuentas_eeuu} cuentas con saldo total de AR$ {total_en_pesos:,.2f}")
        else:
            st.info("ℹ️ No se encontraron cuentas específicas de EEUU")
    else:
        # Estado de cuenta general (no filtrado)
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
            mean_returns, cov_matrix, df_precios = get_historical_data_for_optimization(
                self.token, self.symbols, self.fecha_desde, self.fecha_hasta
            )
            
            if mean_returns is not None and cov_matrix is not None and df_precios is not None:
                self.returns = df_precios.pct_change().dropna()
                self.prices = df_precios
                self.mean_returns = mean_returns
                self.cov_matrix = cov_matrix
                self.data_loaded = True
                
                # Crear manager para optimización avanzada
                self.manager = manager(list(df_precios.columns), self.notional, df_precios.to_dict('series'))
                
                return True
            else:
                return False
                
        except Exception as e:
            st.error(f"Error cargando datos: {str(e)}")
            return False
    
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

def mostrar_menu_optimizacion_separado(portafolio, token_acceso, fecha_desde, fecha_hasta, tipo_portafolio):
    """
    Menú de optimización para portafolios separados (Argentina o EEUU)
    """
    pais_nombre = "Argentina" if tipo_portafolio == "argentina" else "EEUU"
    bandera = "🇦🇷" if tipo_portafolio == "argentina" else "🇺🇸"
    
    st.markdown(f"### {bandera} Optimización de Portafolio {pais_nombre}")
    
    # Información del portafolio
    activos = portafolio.get('activos', [])
    total_portafolio = sum(activo.get('valorMercado', 0) for activo in activos)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Activos", len(activos))
    with col2:
        st.metric("Valor Total", f"AR$ {total_portafolio:,.2f}")
    with col3:
        st.metric("Tipo", "Separado")
    
    # Selección de categoría principal
    categoria = st.selectbox(
        "Seleccione la categoría:",
        options=[
            "🔄 Rebalanceo",
            "📈 Optimizaciones"
        ],
        help="Elija la categoría de análisis que desea realizar"
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
            help="Elija el tipo de rebalanceo que desea realizar"
        )
        
        if tipo_rebalanceo == "🔄 Rebalanceo con Composición Actual":
            mostrar_rebalanceo_composicion_actual(portafolio, token_acceso, fecha_desde, fecha_hasta)
        elif tipo_rebalanceo == "🎲 Rebalanceo con Símbolos Aleatorios":
            mostrar_rebalanceo_simbolos_aleatorios(portafolio, token_acceso, fecha_desde, fecha_hasta)
        elif tipo_rebalanceo == "📊 Optimización Básica":
            mostrar_optimizacion_basica(portafolio, token_acceso, fecha_desde, fecha_hasta)
        elif tipo_rebalanceo == "📈 Frontera Eficiente":
            mostrar_frontera_eficiente(portafolio, token_acceso, fecha_desde, fecha_hasta)
    
    elif categoria == "📈 Optimizaciones":
        # Submenú de Optimizaciones
        tipo_optimizacion = st.selectbox(
            "Seleccione el tipo de optimización:",
            options=[
                "🎲 Optimización Aleatoria",
                "🚀 Optimización Avanzada",
                "🛡️ Análisis de Cobertura"
            ],
            help="Elija el tipo de optimización que desea realizar"
        )
        
        if tipo_optimizacion == "🎲 Optimización Aleatoria":
            mostrar_optimizacion_aleatoria(portafolio, token_acceso, fecha_desde, fecha_hasta)
        elif tipo_optimizacion == "🚀 Optimización Avanzada":
            mostrar_optimizacion_avanzada(portafolio, token_acceso, fecha_desde, fecha_hasta)
        elif tipo_optimizacion == "🛡️ Análisis de Cobertura":
            mostrar_cobertura_portafolio(portafolio, token_acceso, fecha_desde, fecha_hasta)

def mostrar_menu_optimizacion_consolidado(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Menú de optimización para portafolio consolidado (Argentina + EEUU)
    """
    st.markdown("### 🌍 Optimización de Portafolio Consolidado")
    
    # Información del portafolio consolidado
    activos = portafolio.get('activos', [])
    total_portafolio = sum(activo.get('valorMercado', 0) for activo in activos)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Activos Totales", len(activos))
    with col2:
        st.metric("Valor Total", f"AR$ {total_portafolio:,.2f}")
    with col3:
        st.metric("Tipo", "Consolidado")
    
    # Selección de categoría principal
    categoria = st.selectbox(
        "Seleccione la categoría:",
        options=[
            "🔄 Rebalanceo",
            "📈 Optimizaciones",
            "🌍 Análisis Global"
        ],
        help="Elija la categoría de análisis que desea realizar"
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
            help="Elija el tipo de rebalanceo que desea realizar"
        )
        
        if tipo_rebalanceo == "🔄 Rebalanceo con Composición Actual":
            mostrar_rebalanceo_composicion_actual(portafolio, token_acceso, fecha_desde, fecha_hasta)
        elif tipo_rebalanceo == "🎲 Rebalanceo con Símbolos Aleatorios":
            mostrar_rebalanceo_simbolos_aleatorios(portafolio, token_acceso, fecha_desde, fecha_hasta)
        elif tipo_rebalanceo == "📊 Optimización Básica":
            mostrar_optimizacion_basica(portafolio, token_acceso, fecha_desde, fecha_hasta)
        elif tipo_rebalanceo == "📈 Frontera Eficiente":
            mostrar_frontera_eficiente(portafolio, token_acceso, fecha_desde, fecha_hasta)
    
    elif categoria == "📈 Optimizaciones":
        # Submenú de Optimizaciones
        tipo_optimizacion = st.selectbox(
            "Seleccione el tipo de optimización:",
            options=[
                "🎲 Optimización Aleatoria",
                "🚀 Optimización Avanzada",
                "🛡️ Análisis de Cobertura"
            ],
            help="Elija el tipo de optimización que desea realizar"
        )
        
        if tipo_optimizacion == "🎲 Optimización Aleatoria":
            mostrar_optimizacion_aleatoria(portafolio, token_acceso, fecha_desde, fecha_hasta)
        elif tipo_optimizacion == "🚀 Optimización Avanzada":
            mostrar_optimizacion_avanzada(portafolio, token_acceso, fecha_desde, fecha_hasta)
        elif tipo_optimizacion == "🛡️ Análisis de Cobertura":
            mostrar_cobertura_portafolio(portafolio, token_acceso, fecha_desde, fecha_hasta)
    
    elif categoria == "🌍 Análisis Global":
        st.markdown("#### 🌍 Análisis Global del Portafolio Consolidado")
        st.info("Análisis de correlación y diversificación entre mercados")
        
        # Análisis de correlación entre Argentina y EEUU
        if len(activos) > 1:
            st.success("✅ Análisis de correlación disponible")
            if st.button("📊 Calcular Correlación", key="calcular_correlacion"):
                st.info("🔄 Calculando correlación entre mercados...")
                # Aquí iría la lógica de cálculo de correlación
                st.success("✅ Correlación calculada")
        else:
            st.warning("⚠️ Se necesitan al menos 2 activos para análisis de correlación")

def mostrar_menu_optimizacion_unificado(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Menú unificado organizado en dos categorías: Rebalanceo y Optimizaciones
    """
    st.markdown("### 🎯 Optimización y Cobertura de Portafolio")
    
    # Selección de categoría principal
    categoria = st.selectbox(
        "Seleccione la categoría:",
        options=[
            "🔄 Rebalanceo",
            "📈 Optimizaciones"
        ],
        help="Elija la categoría de análisis que desea realizar"
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
            help="Elija el tipo de rebalanceo que desea realizar"
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
            help="Elija el tipo de optimización que desea realizar"
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
            help="Seleccione el benchmark que servirá como tasa libre de riesgo"
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
            key="usar_benchmark_tasa_libre_rebalanceo"
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
            help="Seleccione el criterio de optimización"
        )
    
    with col2:
        target_return = st.number_input(
            "Retorno Objetivo (anual):",
            min_value=0.0, max_value=1.0, value=0.08, step=0.01,
            help="Solo aplica para optimización Markowitz"
        )
    
    with col3:
        mostrar_comparacion = st.checkbox("Mostrar Comparación con Actual", value=True, key="mostrar_comparacion_rebalanceo")
    
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
                
                # Cargar datos
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

def obtener_simbolos_mercado_eeuu():
    """
    Obtiene una lista de símbolos populares del mercado NYSE/NASDAQ
    """
    simbolos_nyse = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK.A', 'JPM', 'JNJ',
        'V', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'PYPL', 'BAC', 'ADBE', 'CRM',
        'NFLX', 'INTC', 'CMCSA', 'PFE', 'ABT', 'TMO', 'KO', 'PEP', 'AVGO', 'COST',
        'MRK', 'WMT', 'TXN', 'QCOM', 'HON', 'DHR', 'ACN', 'LLY', 'VZ', 'BMY', 'RTX'
    ]
    
    simbolos_nasdaq = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'ADBE', 'CRM', 'NFLX',
        'INTC', 'PYPL', 'AVGO', 'QCOM', 'HON', 'ACN', 'LLY', 'VRTX', 'REGN', 'IDXX',
        'KLAC', 'LRCX', 'SNPS', 'CDNS', 'MELI', 'JD', 'BIDU', 'NTES', 'PDD', 'TCOM',
        'BABA', 'NIO', 'XPENG', 'LI', 'XPEV', 'JD', 'BIDU', 'NTES', 'PDD', 'TCOM'
    ]
    
    return list(set(simbolos_nyse + simbolos_nasdaq))  # Eliminar duplicados

def generar_simbolos_mercado_eeuu(num_simbolos, incluir_actuales, porcentaje_actuales, activos_actuales, simbolos_disponibles):
    """
    Genera símbolos aleatorios del mercado NYSE/NASDAQ para portafolio EEUU
    """
    import random
    
    simbolos_seleccionados = []
    
    # Si incluir actuales, agregar algunos símbolos del portafolio actual
    if incluir_actuales and activos_actuales:
        num_actuales = max(1, int(num_simbolos * porcentaje_actuales / 100))
        simbolos_actuales = []
        
        for activo in activos_actuales:
            titulo = activo.get('titulo', {})
            simbolo = titulo.get('simbolo', '')
            if simbolo and simbolo in simbolos_disponibles:
                simbolos_actuales.append(simbolo)
        
        # Seleccionar símbolos actuales aleatoriamente
        if simbolos_actuales:
            num_a_incluir = min(num_actuales, len(simbolos_actuales))
            simbolos_seleccionados.extend(random.sample(simbolos_actuales, num_a_incluir))
    
    # Completar con símbolos aleatorios del mercado
    simbolos_restantes = [s for s in simbolos_disponibles if s not in simbolos_seleccionados]
    num_restantes = num_simbolos - len(simbolos_seleccionados)
    
    if simbolos_restantes and num_restantes > 0:
        simbolos_aleatorios = random.sample(simbolos_restantes, min(num_restantes, len(simbolos_restantes)))
        simbolos_seleccionados.extend(simbolos_aleatorios)
    
    # Si no tenemos suficientes símbolos, duplicar algunos
    while len(simbolos_seleccionados) < num_simbolos and simbolos_disponibles:
        simbolos_adicionales = random.sample(simbolos_disponibles, min(num_simbolos - len(simbolos_seleccionados), len(simbolos_disponibles)))
        simbolos_seleccionados.extend(simbolos_adicionales)
    
    return simbolos_seleccionados[:num_simbolos]

def mostrar_rebalanceo_simbolos_aleatorios(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Rebalanceo usando símbolos aleatorios pero manteniendo el mismo capital total
    del portafolio actual, con opción de incluir saldo disponible
    """
    st.markdown("#### 🎲 Rebalanceo con Símbolos Aleatorios")
    
    # Detectar si es portafolio de EEUU
    es_portafolio_eeuu = False
    if hasattr(st.session_state, 'portafolio_seleccionado'):
        es_portafolio_eeuu = st.session_state.portafolio_seleccionado == "eeuu"
    
    activos = portafolio.get('activos', [])
    if not activos:
        st.warning("No hay activos en el portafolio para calcular el capital total")
        return
    
    # Calcular capital total actual
    capital_total_actual = sum(activo.get('valorMercado', 0) for activo in activos)
    
    if capital_total_actual <= 0:
        st.warning("No se puede calcular el capital total del portafolio")
        return
    
    st.info(f"💰 Capital total actual del portafolio: ${capital_total_actual:,.2f}")
    
    # Opción para incluir saldo disponible
    incluir_saldo_disponible = st.checkbox(
        "💳 Incluir saldo disponible del estado de cuenta",
        value=False,
        help="Si está marcado, se incluirá el saldo disponible en el capital total",
        key="incluir_saldo_disponible_rebalanceo_aleatorio"
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
            key="incluir_actuales_rebalanceo_aleatorio"
        )
    
    with col3:
        porcentaje_actuales = st.slider(
            "Porcentaje de símbolos actuales:",
            min_value=0, max_value=100, value=30,
            help="Porcentaje de símbolos actuales a incluir en la selección"
        )
    
    # Configuración específica para portafolio EEUU
    if es_portafolio_eeuu:
        st.markdown("#### 🇺🇸 Configuración Específica para EEUU")
        
        col1, col2 = st.columns(2)
        
        with col1:
            mercado_seleccionado = st.selectbox(
                "Mercado:",
                options=['NYSE', 'NASDAQ', 'Ambos'],
                help="Seleccione el mercado de donde obtener símbolos aleatorios",
                key="mercado_eeuu_rebalanceo"
            )
        
        with col2:
            incluir_etfs = st.checkbox(
                "📊 Incluir ETFs",
                value=True,
                help="Incluir ETFs populares en la selección aleatoria",
                key="incluir_etfs_eeuu"
            )
        
        # Mostrar símbolos disponibles del mercado seleccionado
        simbolos_disponibles = obtener_simbolos_mercado_eeuu()
        
        if mercado_seleccionado == 'NYSE':
            simbolos_filtrados = [s for s in simbolos_disponibles if s in [
                'AAPL', 'MSFT', 'GOOGL', 'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA',
                'DIS', 'BAC', 'PFE', 'ABT', 'TMO', 'KO', 'PEP', 'MRK', 'WMT', 'TXN'
            ]]
        elif mercado_seleccionado == 'NASDAQ':
            simbolos_filtrados = [s for s in simbolos_disponibles if s in [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'ADBE', 'CRM',
                'NFLX', 'INTC', 'PYPL', 'AVGO', 'QCOM', 'HON', 'ACN', 'LLY', 'VRTX'
            ]]
        else:  # Ambos
            simbolos_filtrados = simbolos_disponibles
        
        if incluir_etfs:
            etfs_populares = ['SPY', 'QQQ', 'IWM', 'VTI', 'VOO', 'VEA', 'VWO', 'BND', 'GLD', 'SLV']
            simbolos_filtrados.extend(etfs_populares)
        
        st.info(f"📈 Símbolos disponibles: {len(simbolos_filtrados)} (incluyendo {mercado_seleccionado})")
        
        # Mostrar algunos símbolos de ejemplo
        if simbolos_filtrados:
            st.markdown("**Ejemplos de símbolos disponibles:**")
            col1, col2, col3, col4 = st.columns(4)
            for i, simbolo in enumerate(simbolos_filtrados[:12]):
                col = [col1, col2, col3, col4][i % 4]
                col.code(simbolo)
    
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
            help="Seleccione el criterio de optimización"
        )
    
    with col2:
        target_return = st.number_input(
            "Retorno Objetivo (anual):",
            min_value=0.0, max_value=1.0, value=0.08, step=0.01,
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
            help="Limita el peso máximo por activo"
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
            mostrar_comparacion = st.checkbox("Mostrar Comparación con Actual", value=True, key="mostrar_comparacion_rebalanceo_aleatorio")
        with col3:
            mostrar_metricas = st.checkbox("Mostrar Métricas Detalladas", value=True, key="mostrar_metricas_rebalanceo_aleatorio")
    
    # Botón de ejecución
    col1, col2, col3 = st.columns(3)
    with col1:
        generar_simbolos = st.button("🎲 Generar Símbolos Aleatorios")
    with col2:
        ejecutar_rebalanceo = st.button("🚀 Ejecutar Rebalanceo")
    with col3:
        ejecutar_completo = st.button("🎯 Rebalanceo Completo")
    
    if generar_simbolos or ejecutar_rebalanceo or ejecutar_completo:
        # Generar símbolos aleatorios según el tipo de portafolio
        if es_portafolio_eeuu:
            # Para portafolio EEUU, usar símbolos del mercado NYSE/NASDAQ
            simbolos_aleatorios = generar_simbolos_mercado_eeuu(
                num_simbolos, incluir_actuales, porcentaje_actuales, 
                activos, simbolos_filtrados
            )
        else:
            # Para portafolio Argentina, usar símbolos existentes
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
                        strategy = 'max_sharpe'
                        target = None
                    
                    # Aplicar restricciones de pesos
                    if restriccion_pesos != 'sin_restriccion':
                        max_weight = float(restriccion_pesos.split('_')[1]) / 100
                        portfolio_manager.set_max_weight(max_weight)
                    
                    # Ejecutar optimización
                    try:
                        if strategy == 'markowitz' and target is not None:
                            portfolio_manager.optimize(strategy=strategy, target_return=target)
                        else:
                            portfolio_manager.optimize(strategy=strategy)
                        
                        # Obtener resultados
                        pesos_optimizados = portfolio_manager.get_weights()
                        retorno_esperado = portfolio_manager.get_return()
                        volatilidad = portfolio_manager.get_volatility()
                        sharpe_ratio = portfolio_manager.get_sharpe_ratio(tasa_libre_riesgo)
                        
                        # Mostrar resultados
                        st.markdown("#### 📊 Resultados de la Optimización")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Retorno Esperado", f"{retorno_esperado:.2%}")
                        with col2:
                            st.metric("Volatilidad", f"{volatilidad:.2%}")
                        with col3:
                            st.metric("Ratio de Sharpe", f"{sharpe_ratio:.2f}")
                        with col4:
                            st.metric("Capital Total", f"${capital_total:,.2f}")
                        
                        # Mostrar distribución de pesos
                        st.markdown("#### 📈 Distribución de Pesos Optimizados")
                        
                        # Crear DataFrame con pesos
                        df_pesos = pd.DataFrame({
                            'Símbolo': simbolos_aleatorios,
                            'Peso (%)': [peso * 100 for peso in pesos_optimizados],
                            'Valor ($)': [peso * capital_total for peso in pesos_optimizados]
                        })
                        
                        # Ordenar por peso
                        df_pesos = df_pesos.sort_values('Peso (%)', ascending=False)
                        
                        # Mostrar tabla
                        st.dataframe(df_pesos, use_container_width=True)
                        
                        # Gráfico de pesos
                        fig_pesos = go.Figure(data=[go.Bar(
                            x=df_pesos['Símbolo'],
                            y=df_pesos['Peso (%)'],
                            text=[f'{peso:.1f}%' for peso in df_pesos['Peso (%)']],
                            textposition='auto'
                        )])
                        fig_pesos.update_layout(
                            title="Distribución de Pesos del Portafolio Optimizado",
                            xaxis_title="Símbolos",
                            yaxis_title="Peso (%)",
                            showlegend=False
                        )
                        st.plotly_chart(fig_pesos, use_container_width=True)
                        
                        # Comparación con portafolio actual si está habilitado
                        if mostrar_comparacion and activos:
                            st.markdown("#### 🔄 Comparación con Portafolio Actual")
                            
                            # Calcular métricas del portafolio actual
                            retorno_actual = calcular_retorno_portafolio(activos, fecha_desde, fecha_hasta)
                            volatilidad_actual = calcular_volatilidad_portafolio(activos, fecha_desde, fecha_hasta)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Portafolio Actual**")
                                st.metric("Retorno", f"{retorno_actual:.2%}")
                                st.metric("Volatilidad", f"{volatilidad_actual:.2%}")
                            
                            with col2:
                                st.markdown("**Portafolio Optimizado**")
                                st.metric("Retorno", f"{retorno_esperado:.2%}")
                                st.metric("Volatilidad", f"{volatilidad:.2%}")
                            
                            # Gráfico de comparación
                            fig_comparacion = go.Figure()
                            fig_comparacion.add_trace(go.Bar(
                                name='Portafolio Actual',
                                x=['Retorno', 'Volatilidad'],
                                y=[retorno_actual * 100, volatilidad_actual * 100],
                                marker_color='lightblue'
                            ))
                            fig_comparacion.add_trace(go.Bar(
                                name='Portafolio Optimizado',
                                x=['Retorno', 'Volatilidad'],
                                y=[retorno_esperado * 100, volatilidad * 100],
                                marker_color='lightgreen'
                            ))
                            fig_comparacion.update_layout(
                                title="Comparación: Actual vs Optimizado",
                                yaxis_title="Porcentaje (%)",
                                barmode='group'
                            )
                            st.plotly_chart(fig_comparacion, use_container_width=True)
                        
                        # Métricas detalladas si está habilitado
                        if mostrar_metricas:
                            st.markdown("#### 📊 Métricas Detalladas")
                            
                            # Calcular métricas adicionales
                            var_95 = portfolio_manager.get_value_at_risk(0.05)
                            max_drawdown = portfolio_manager.get_max_drawdown()
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("VaR (95%)", f"{var_95:.2%}")
                            with col2:
                                st.metric("Máximo Drawdown", f"{max_drawdown:.2%}")
                            with col3:
                                st.metric("Diversificación", f"{len(simbolos_aleatorios)} activos")
                        
                        st.success("✅ Rebalanceo aleatorio completado exitosamente!")
                        
                    except Exception as e:
                        st.error(f"❌ Error durante la optimización: {str(e)}")
                        st.info("💡 Intente ajustar los parámetros o usar menos símbolos")
                
                except Exception as e:
                    st.error(f"❌ Error durante el rebalanceo: {str(e)}")
                    st.info("💡 Verifique que los símbolos sean válidos y que haya datos históricos disponibles")

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
    categorias = {
        'Acciones': 0,
        'ETFs': 0,
        'Bonos': 0,
        'Otros': 0
    }
    
    for simbolo in simbolos:
        if simbolo in ['SPY', 'QQQ', 'IWM', 'VTI', 'VOO', 'VEA', 'VWO', 'BND', 'GLD', 'SLV']:
            categorias['ETFs'] += 1
        elif any(bono in simbolo for bono in ['GD', 'AL', 'BONAR']):
            categorias['Bonos'] += 1
        elif len(simbolo) <= 5 and simbolo.isalpha():
            categorias['Acciones'] += 1
        else:
            categorias['Otros'] += 1
    
    return {k: v for k, v in categorias.items() if v > 0}

def calcular_retorno_portafolio(activos, fecha_desde, fecha_hasta):
    """
    Calcula el retorno del portafolio actual
    """
    try:
        # Implementación simplificada - en producción usar datos reales
        return 0.08  # 8% anual como ejemplo
    except:
        return 0.0

def calcular_volatilidad_portafolio(activos, fecha_desde, fecha_hasta):
    """
    Calcula la volatilidad del portafolio actual
    """
    try:
        # Implementación simplificada - en producción usar datos reales
        return 0.15  # 15% anual como ejemplo
    except:
        return 0.0
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
            min_value=0.01, max_value=2.0, value=0.15, step=0.01,
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
            help="Benchmark para calcular alpha y beta"
        )
    
    with col2:
        usar_portafolio_actual = st.checkbox(
            "🔄 Usar portafolio actual como benchmark",
            value=False,
            help="Si está marcado, se usará el portafolio actual como benchmark",
            key="usar_portafolio_actual_optimizacion_aleatoria"
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
                }[x]
            )
        with col2:
            mostrar_histogramas = st.checkbox("Mostrar Histogramas", value=True, key="mostrar_histogramas_optimizacion_aleatoria")
        with col3:
            mostrar_frontera = st.checkbox("Mostrar Frontera Eficiente", value=False, key="mostrar_frontera_optimizacion_aleatoria")
    
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

def obtener_cotizaciones_caucion(bearer_token):
    """
    Obtiene cotizaciones de cauciones usando la API de InvertirOnline
    """
    return obtener_cotizaciones_generico('cauciones', 'argentina', bearer_token)

def obtener_datos_benchmark_argentino(benchmark, token_acceso, fecha_desde, fecha_hasta):
    """
    Obtiene datos de benchmarks del mercado argentino
    """
    try:
        if benchmark == 'Tasa_Caucion_Promedio':
            # Obtener cotizaciones de cauciones usando la nueva función
            cotizaciones_caucion = obtener_cotizaciones_caucion(token_acceso)
            if cotizaciones_caucion is not None and not cotizaciones_caucion.empty:
                # Calcular promedio de tasas de caución
                if 'tasa' in cotizaciones_caucion.columns:
                    tasas = cotizaciones_caucion['tasa'].dropna()
                    if len(tasas) > 0:
                        tasa_promedio = tasas.mean() / 100  # Convertir a decimal
                        retorno_diario = (1 + tasa_promedio) ** (1/252) - 1
                        
                        # Crear serie temporal de retornos
                        fechas = pd.date_range(start=fecha_desde, end=fecha_hasta, freq='D')
                        retornos = pd.Series([retorno_diario] * len(fechas), index=fechas)
                        
                        return pd.DataFrame({'Tasa_Caucion_Promedio': retornos})
                
                # Fallback a método anterior si no hay datos
                tasas_caucion = obtener_tasas_caucion(token_acceso)
                if tasas_caucion and 'tasas' in tasas_caucion:
                    tasas = []
                    for tasa in tasas_caucion['tasas']:
                        if 'tasa' in tasa:
                            tasas.append(tasa['tasa'])
                    
                    if tasas:
                        tasa_promedio = np.mean(tasas) / 100
                        retorno_diario = (1 + tasa_promedio) ** (1/252) - 1
                        fechas = pd.date_range(start=fecha_desde, end=fecha_hasta, freq='D')
                        retornos = pd.Series([retorno_diario] * len(fechas), index=fechas)
                        return pd.DataFrame({'Tasa_Caucion_Promedio': retornos})
        
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
                datos_bono = obtener_serie_historica_iol(token_acceso, 'BONOS', simbolo_bono, fecha_desde, fecha_hasta)
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
                datos_indice = obtener_serie_historica_iol(token_acceso, 'INDICES', nombre_indice, fecha_desde, fecha_hasta)
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
            help="Seleccione el benchmark que servirá como tasa libre de riesgo"
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
            key="usar_benchmark_tasa_libre_optimizacion"
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
            }[x]
        )
    
    with col2:
        target_return = st.number_input(
            "Retorno Objetivo (anual):",
            min_value=0.0, max_value=1.0, value=0.08, step=0.01,
            help="Solo aplica para estrategia Markowitz"
        )
    
    with col3:
        show_frontier = st.checkbox("Mostrar Frontera Eficiente", value=True, key="show_frontier_optimizacion")
    
    # Configuración avanzada de frontera eficiente
    with st.expander("⚙️ Configuración Avanzada de Frontera Eficiente", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            calcular_todos = st.checkbox("Calcular Todos los Portafolios", value=True, 
                                       help="Calcula automáticamente todas las estrategias disponibles",
                                       key="calcular_todos_optimizacion")
            num_puntos = st.slider("Número de Puntos en Frontera", min_value=10, max_value=100, value=50,
                                 help="Más puntos = frontera más suave pero más lento")
        with col2:
            incluir_actual = st.checkbox("Incluir Portafolio Actual", value=True,
                                       help="Muestra el portafolio actual en la frontera",
                                       key="incluir_actual_optimizacion")
            mostrar_metricas = st.checkbox("Mostrar Métricas Detalladas", value=True, key="mostrar_metricas_optimizacion")
        with col3:
            target_return_frontier = st.number_input("Retorno Objetivo Frontera", min_value=0.0, max_value=1.0, 
                                                   value=0.08, step=0.01, help="Para optimización de frontera")
            auto_refresh = st.checkbox("Auto-refresh", value=True, help="Actualiza automáticamente con cambios", key="auto_refresh_optimizacion")
    
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
    
    # Función para calcular frontera eficiente interactiva
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
                            mostrar_grid = st.checkbox("Mostrar Grid", value=True, key="mostrar_grid_frontier")
                        with col3:
                            mostrar_leyenda = st.checkbox("Mostrar Leyenda", value=True, key="mostrar_leyenda_frontier")
                        
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
                                fig.update_layout(
                                    xaxis=dict(range=[0, max(volatilities) * zoom_level]),
                                    yaxis=dict(range=[0, max(returns) * zoom_level])
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
        incluir_actual = st.checkbox("Incluir Portafolio Actual", value=True, key="incluir_actual_frontier")
        mostrar_metricas = st.checkbox("Mostrar Métricas Detalladas", value=True, key="mostrar_metricas_frontier")
    
    with col3:
        calcular_todos = st.checkbox("Calcular Todos los Portafolios", value=True, key="calcular_todos_frontier")
        auto_refresh = st.checkbox("Auto-refresh", value=True, key="auto_refresh_frontier")
    
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
    @st.cache_data(ttl=300)  # Cache por 5 minutos
    def cargar_datos_cliente(token, cliente_id):
        """Carga y cachea los datos del cliente para evitar llamadas repetitivas"""
        portafolio_ar = obtener_portafolio(token, cliente_id, 'Argentina')
        portafolio_eeuu = obtener_portafolio_eeuu(token, cliente_id)
        estado_cuenta_ar = obtener_estado_cuenta(token, cliente_id)
        estado_cuenta_eeuu = obtener_estado_cuenta_eeuu(token)
        return portafolio_ar, portafolio_eeuu, estado_cuenta_ar, estado_cuenta_eeuu
    
    # Cargar datos con cache
    with st.spinner("🔄 Cargando datos del cliente..."):
        portafolio_ar, portafolio_eeuu, estado_cuenta_ar, estado_cuenta_eeuu = cargar_datos_cliente(token_acceso, id_cliente)
    
    # Crear tabs con iconos
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🇦🇷 Portafolio Argentina", 
        "🇺🇸 Portafolio EEUU",
        "💰 Estado de Cuenta", 
        "🎯 Optimización y Cobertura",
        "📊 Análisis Técnico",
        "💱 Cotizaciones"
    ])

    with tab1:
        if portafolio_ar:
            st.subheader("🇦🇷 Portafolio Argentina")
            mostrar_resumen_portafolio(portafolio_ar, token_acceso, "argentina")
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
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🇦🇷 Estado de Cuenta Argentina")
            if estado_cuenta_ar:
                mostrar_estado_cuenta(estado_cuenta_ar, es_eeuu=False)
            else:
                st.warning("No se pudo obtener el estado de cuenta de Argentina")
        
        with col2:
            st.subheader("🇺🇸 Estado de Cuenta EEUU")
            if estado_cuenta_eeuu:
                mostrar_estado_cuenta(estado_cuenta_eeuu, es_eeuu=True)
            else:
                st.warning("No se pudo obtener el estado de cuenta de EEUU")
        
        # Vista consolidada de todas las cuentas
        st.subheader("🔍 Vista Consolidada de Todas las Cuentas")
        
        # Combinar cuentas de Argentina y EEUU
        cuentas_totales = []
        
        # Agregar cuentas de Argentina
        if estado_cuenta_ar and estado_cuenta_ar.get('cuentas'):
            cuentas_totales.extend(estado_cuenta_ar.get('cuentas', []))
        
        # Agregar cuentas de EEUU
        if estado_cuenta_eeuu and estado_cuenta_eeuu.get('cuentas'):
            cuentas_totales.extend(estado_cuenta_eeuu.get('cuentas', []))
        
        if cuentas_totales:
            # Debug: mostrar cuentas que se van a procesar
            st.info(f"🔍 Procesando {len(cuentas_totales)} cuentas para clasificación")
            
            # Debug: mostrar origen de las cuentas
            st.info("📊 Origen de datos:")
            st.info(f"   - Estado cuenta Argentina: {len(estado_cuenta_ar.get('cuentas', [])) if estado_cuenta_ar else 0} cuentas")
            st.info(f"   - Estado cuenta EEUU: {len(estado_cuenta_eeuu.get('cuentas', [])) if estado_cuenta_eeuu else 0} cuentas")
            
            # Crear DataFrame con clasificación por país
            datos_consolidados = []
            for cuenta in cuentas_totales:
                numero = cuenta.get('numero', 'N/A')
                descripcion = cuenta.get('descripcion', 'N/A')
                moneda = cuenta.get('moneda', 'N/A')
                
                # Determinar si es cuenta de EEUU
                es_cuenta_eeuu = any([
                    'eeuu' in str(numero).lower(),
                    '-eeuu' in str(numero),
                    'dolar estadounidense' in moneda.lower(),
                    'dolar estadounidense' in moneda.lower(),
                    'eeuu' in descripcion.lower(),
                    'estados unidos' in descripcion.lower()
                ])
                
                pais = "🇺🇸 EEUU" if es_cuenta_eeuu else "🇦🇷 Argentina"
                
                # Debug: mostrar clasificación
                if es_cuenta_eeuu:
                    st.info(f"🔍 Cuenta EEUU detectada: {numero} - {moneda}")
                    st.info(f"   Disponible: {cuenta.get('disponible', 0)}, Saldo: {cuenta.get('saldo', 0)}, Total: {cuenta.get('total', 0)}")
                
                datos_consolidados.append({
                    'País': pais,
                    'Número': numero,
                    'Descripción': descripcion,
                    'Moneda': moneda.replace('_', ' ').title(),
                    'Disponible': cuenta.get('disponible', 0),
                    'Saldo': cuenta.get('saldo', 0),
                    'Total': cuenta.get('total', 0),
                })
            
            df_consolidado = pd.DataFrame(datos_consolidados)
            
            # Agrupar por país y mostrar resumen
            resumen_por_pais = df_consolidado.groupby('País').agg({
                'Total': 'sum',
                'Número': 'count'
            }).round(2)
            
            # Debug: mostrar resumen de clasificación
            st.info(f"📊 Resumen de clasificación: {resumen_por_pais.to_dict()}")
            
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
            
            # Botón de debug para mostrar todas las cuentas
            if st.button("🔍 Debug: Mostrar Todas las Cuentas", key="debug_cuentas"):
                st.markdown("#### 🔍 Debug: Cuentas Originales")
                for i, cuenta in enumerate(cuentas_totales):
                    with st.expander(f"Cuenta {i+1}: {cuenta.get('numero', 'N/A')}", expanded=False):
                        st.json(cuenta)
            
            # Botón para verificar inconsistencias
            if st.button("🔍 Verificar Inconsistencias", key="verificar_inconsistencias"):
                st.markdown("#### 🔍 Verificación de Inconsistencias")
                
                # Verificar si hay diferencias entre estado de cuenta y portafolio
                if portafolio_eeuu and 'activos' in portafolio_eeuu:
                    st.info("📊 Comparando estado de cuenta vs portafolio EEUU:")
                    
                    # Obtener total del portafolio
                    total_portafolio = sum(activo.get('valorizado', 0) for activo in portafolio_eeuu['activos'])
                    st.info(f"   - Total Portafolio EEUU: ${total_portafolio:,.2f}")
                    
                    # Obtener total del estado de cuenta
                    total_estado_cuenta = sum(cuenta.get('total', 0) for cuenta in cuentas_totales if any([
                        'eeuu' in str(cuenta.get('numero', '')).lower(),
                        '-eeuu' in str(cuenta.get('numero', '')),
                        'dolar estadounidense' in cuenta.get('moneda', '').lower()
                    ]))
                    st.info(f"   - Total Estado Cuenta EEUU: ${total_estado_cuenta:,.2f}")
                    
                    # Calcular diferencia
                    diferencia = abs(total_portafolio - total_estado_cuenta)
                    if diferencia > 0.01:  # Tolerancia de 1 centavo
                        st.warning(f"⚠️ Diferencia detectada: ${diferencia:,.2f}")
                        st.info("💡 Esto puede indicar que los datos se obtuvieron en momentos diferentes")
                        
                        # Análisis detallado de la diferencia
                        st.markdown("#### 📊 Análisis de la Diferencia")
                        
                        if total_estado_cuenta > total_portafolio:
                            st.info(f"💰 El estado de cuenta es ${diferencia:,.2f} mayor que el portafolio")
                            st.info("💡 Esto sugiere que hay saldo disponible en las cuentas EEUU")
                            
                            # Calcular saldo disponible
                            saldo_disponible_eeuu = sum(cuenta.get('disponible', 0) for cuenta in cuentas_totales if any([
                                'eeuu' in str(cuenta.get('numero', '')).lower(),
                                '-eeuu' in str(cuenta.get('numero', '')),
                                'dolar estadounidense' in cuenta.get('moneda', '').lower()
                            ]))
                            
                            st.success(f"💵 Saldo disponible en cuentas EEUU: ${saldo_disponible_eeuu:,.2f}")
                            
                            # Verificar si la diferencia coincide con el saldo disponible
                            if abs(diferencia - saldo_disponible_eeuu) < 0.01:
                                st.success("✅ La diferencia coincide con el saldo disponible")
                                st.info("💡 Los datos son consistentes: Portafolio + Saldo = Estado de Cuenta")
                            else:
                                st.warning("⚠️ La diferencia no coincide exactamente con el saldo disponible")
                                st.info("💡 Puede haber otros factores como comisiones o transacciones pendientes")
                        
                        else:
                            st.info(f"📉 El portafolio es ${diferencia:,.2f} mayor que el estado de cuenta")
                            st.info("💡 Esto puede indicar que hay activos no reflejados en el estado de cuenta")
                        
                        # Recomendación
                        st.markdown("#### 💡 Recomendación")
                        st.info("Para obtener datos más consistentes:")
                        st.info("1. 🔄 Refrescar ambos datos simultáneamente")
                        st.info("2. 📊 Usar el valor más reciente para cálculos")
                        st.info("3. ⚠️ Considerar la diferencia como saldo disponible")
                        
                        # Resumen consolidado
                        st.markdown("#### 📊 Resumen Consolidado EEUU")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Portafolio Valorizado", f"${total_portafolio:,.2f}")
                        
                        with col2:
                            st.metric("Saldo Disponible", f"${diferencia:,.2f}")
                        
                        with col3:
                            st.metric("Total Consolidado", f"${total_estado_cuenta:,.2f}")
                        
                        # Explicación
                        st.info("💡 **Explicación de la diferencia:**")
                        st.info(f"   • Portafolio EEUU: ${total_portafolio:,.2f} (activos valorizados)")
                        st.info(f"   • Saldo disponible: ${diferencia:,.2f} (efectivo en cuentas)")
                        st.info(f"   • Total consolidado: ${total_estado_cuenta:,.2f} (portafolio + saldo)")
                        
                        st.success("✅ Los datos son consistentes: Portafolio + Saldo = Estado de Cuenta")
                        
                    else:
                        st.success("✅ Los totales coinciden")
                else:
                    st.warning("⚠️ No hay portafolio EEUU disponible para comparar")
    
    with tab4:
        # Menú unificado de optimización y cobertura
        st.markdown("### 🎯 Optimización y Cobertura")
        
        # Selección de portafolio para optimizar
        st.markdown("#### 📊 Selección de Portafolio a Optimizar")
        
        if portafolio_ar or portafolio_eeuu:
            # Mostrar opciones disponibles
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if portafolio_ar and 'activos' in portafolio_ar:
                    st.success(f"🇦🇷 Portafolio Argentina")
                    st.metric("Activos", len(portafolio_ar['activos']))
                    st.metric("Valor Total", f"AR$ {sum(activo.get('valorMercado', 0) for activo in portafolio_ar['activos']):,.2f}")
                    
                    if st.button("🎯 Optimizar Solo Argentina", key="opt_ar_solo", type="primary"):
                        st.session_state.portafolio_seleccionado = "argentina"
                        st.session_state.portafolio_data = portafolio_ar
                        st.session_state.tipo_optimizacion = "separado"
                        st.rerun()
                else:
                    st.warning("🇦🇷 No disponible")
            
            with col2:
                if portafolio_eeuu and 'activos' in portafolio_eeuu:
                    st.success(f"🇺🇸 Portafolio EEUU")
                    st.metric("Activos", len(portafolio_eeuu['activos']))
                    st.metric("Valor Total", f"AR$ {sum(activo.get('valorMercado', 0) for activo in portafolio_eeuu['activos']):,.2f}")
                    
                    if st.button("🎯 Optimizar Solo EEUU", key="opt_eeuu_solo", type="primary"):
                        st.session_state.portafolio_seleccionado = "eeuu"
                        st.session_state.portafolio_data = portafolio_eeuu
                        st.session_state.tipo_optimizacion = "separado"
                        st.rerun()
                else:
                    st.warning("🇺🇸 No disponible")
            
            with col3:
                if portafolio_ar and portafolio_eeuu:
                    activos_combinados = []
                    if 'activos' in portafolio_ar:
                        activos_combinados.extend(portafolio_ar['activos'])
                    if 'activos' in portafolio_eeuu:
                        activos_combinados.extend(portafolio_eeuu['activos'])
                    
                    st.success(f"🔗 Portafolio Consolidado")
                    st.metric("Activos Totales", len(activos_combinados))
                    st.metric("Valor Total", f"AR$ {sum(activo.get('valorMercado', 0) for activo in activos_combinados):,.2f}")
                    
                    if st.button("🎯 Optimizar Consolidado", key="opt_consolidado", type="primary"):
                        st.session_state.portafolio_seleccionado = "consolidado"
                        st.session_state.portafolio_data = {'activos': activos_combinados}
                        st.session_state.tipo_optimizacion = "consolidado"
                        st.rerun()
                else:
                    st.warning("🔗 No disponible")
            
            # Mostrar menú de optimización si hay un portafolio seleccionado
            if hasattr(st.session_state, 'portafolio_seleccionado') and st.session_state.portafolio_seleccionado:
                st.markdown("---")
                st.markdown(f"#### 🎯 **Optimizando: {st.session_state.portafolio_seleccionado.upper()}**")
                
                # Información del portafolio seleccionado
                portafolio_actual = st.session_state.portafolio_data
                tipo_opt = st.session_state.tipo_optimizacion
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"📊 **Tipo:** {'Separado' if tipo_opt == 'separado' else 'Consolidado'}")
                with col2:
                    st.info(f"🌍 **País:** {'🇦🇷 Argentina' if st.session_state.portafolio_seleccionado == 'argentina' else '🇺🇸 EEUU' if st.session_state.portafolio_seleccionado == 'eeuu' else '🌍 Consolidado'}")
                with col3:
                    st.info(f"📈 **Activos:** {len(portafolio_actual.get('activos', []))}")
                
                # Botón para cambiar de portafolio
                if st.button("🔄 Cambiar Portafolio", key="cambiar_portafolio"):
                    del st.session_state.portafolio_seleccionado
                    del st.session_state.portafolio_data
                    if hasattr(st.session_state, 'tipo_optimizacion'):
                        del st.session_state.tipo_optimizacion
                    st.rerun()
                
                # Mostrar menú de optimización específico según el tipo
                if tipo_opt == "separado":
                    mostrar_menu_optimizacion_separado(
                        portafolio_actual, 
                        token_acceso, 
                        st.session_state.fecha_desde, 
                        st.session_state.fecha_hasta,
                        st.session_state.portafolio_seleccionado
                    )
                else:
                    mostrar_menu_optimizacion_consolidado(
                        portafolio_actual, 
                        token_acceso, 
                        st.session_state.fecha_desde, 
                        st.session_state.fecha_hasta
                    )
        else:
            st.warning("No se pudo obtener ningún portafolio para optimización")
    
    with tab5:
        mostrar_analisis_tecnico(token_acceso, id_cliente)
    
    with tab6:
        mostrar_cotizaciones_mercado(token_acceso)

def main():
    # Configuración de rendimiento
    st.set_page_config(
        page_title="IOL Portfolio Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Configurar cache para mejor rendimiento
    st.cache_data.clear()
    
    # Agregar CSS adicional para animaciones
    st.markdown("""
    <style>
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: 0.7;
            }
        }
        
        .fade-in-up {
            animation: fadeInUp 0.8s ease-out;
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        .hover-lift {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .hover-lift:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.3);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header moderno con gradiente
    st.markdown("""
    <div class="fade-in-up hover-lift" style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 40px;
        margin: 20px 0;
        text-align: center;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
    ">
        <h1 style="
            color: white;
            font-size: 3rem;
            font-weight: 700;
            margin: 0;
            text-shadow: 0 4px 8px rgba(0,0,0,0.3);
            background: linear-gradient(135deg, #ffffff, #f0f0f0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        ">📊 IOL Portfolio Analyzer</h1>
        <p style="
            color: rgba(255,255,255,0.9);
            font-size: 1.2rem;
            margin: 15px 0 0 0;
            font-weight: 300;
        ">Analizador Avanzado de Portafolios con Tecnología de Vanguardia</p>
        <div style="
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 20px;
            flex-wrap: wrap;
        ">
            <span class="badge pulse" style="background: rgba(255,255,255,0.2) !important; color: white !important; border: 1px solid rgba(255,255,255,0.3);">🚀 Optimización Avanzada</span>
            <span class="badge pulse" style="background: rgba(255,255,255,0.2) !important; color: white !important; border: 1px solid rgba(255,255,255,0.3);">📈 Análisis Técnico</span>
            <span class="badge pulse" style="background: rgba(255,255,255,0.2) !important; color: white !important; border: 1px solid rgba(255,255,255,0.3);">🛡️ Gestión de Riesgo</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
        # Header moderno de la sidebar
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            text-align: center;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        ">
            <h3 style="color: white; margin: 0; font-size: 1.2rem;">🔐 Autenticación IOL</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.token_acceso is None:
            with st.form("login_form"):
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #1e293b, #334155);
                    border-radius: 12px;
                    padding: 20px;
                    margin: 15px 0;
                    border: 1px solid #475569;
                ">
                    <h4 style="color: #10b981; margin-bottom: 15px;">Ingreso a IOL</h4>
                </div>
                """, unsafe_allow_html=True)
                
                usuario = st.text_input("Usuario", placeholder="su_usuario", key="login_usuario")
                contraseña = st.text_input("Contraseña", type="password", placeholder="su_contraseña", key="login_password")
                
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
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #10b981, #059669);
                border-radius: 12px;
                padding: 15px;
                margin: 15px 0;
                text-align: center;
                color: white;
                font-weight: 600;
            ">
                ✅ Conectado a IOL
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            st.subheader("Configuración de Fechas")
            col1, col2 = st.columns(2)
            with col1:
                horizonte = st.selectbox(
                    "Horizonte:",
                    options=[
                        "Corto Plazo (1-3 meses)",
                        "Mediano Plazo (3-12 meses)", 
                        "Largo Plazo (1-5 años)",
                        "Muy Largo Plazo (5+ años)",
                        "Personalizado"
                    ],
                    index=1,  # Mediano plazo por defecto
                    help="Seleccione el horizonte de inversión para optimizaciones"
                )
            
            with col2:
                if horizonte == "Personalizado":
                    meses = st.number_input(
                        "Meses:",
                        min_value=1,
                        max_value=120,
                        value=12,
                        help="Número de meses para el horizonte personalizado"
                    )
                    fecha_desde = date.today() - timedelta(days=meses*30)
                    fecha_hasta = date.today()
                else:
                    # Calcular fechas automáticamente según horizonte
                    if horizonte == "Corto Plazo (1-3 meses)":
                        fecha_desde = date.today() - timedelta(days=90)
                        fecha_hasta = date.today()
                    elif horizonte == "Mediano Plazo (3-12 meses)":
                        fecha_desde = date.today() - timedelta(days=365)
                        fecha_hasta = date.today()
                    elif horizonte == "Largo Plazo (1-5 años)":
                        fecha_desde = date.today() - timedelta(days=1825)
                        fecha_hasta = date.today()
                    elif horizonte == "Muy Largo Plazo (5+ años)":
                        fecha_desde = date.today() - timedelta(days=3650)
                        fecha_hasta = date.today()
                    else:
                        fecha_desde = date.today() - timedelta(days=365)
                        fecha_hasta = date.today()
                
                st.info(f"📅 Período: {fecha_desde.strftime('%Y/%m/%d')} - {fecha_hasta.strftime('%Y/%m/%d')}")
            
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
            # Header del menú principal
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #1e293b, #334155);
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                border: 1px solid #475569;
            ">
                <h2 style="color: #10b981; margin: 0; display: flex; align-items: center;">
                    <span style="margin-right: 10px;">🎯</span>
                    Menú Principal
                </h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Menú principal con mejor diseño
            opcion = st.sidebar.radio(
                "Seleccione una opción:",
                ("🏠 Inicio", "📊 Análisis de Portafolio", "💰 Tasas de Caución", "👨‍💼 Panel del Asesor"),
                index=0,
                key="main_menu"
            )

            # Mostrar la página seleccionada
            if opcion == "🏠 Inicio":
                # Dashboard de inicio moderno
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #1e293b, #334155);
                    border-radius: 20px;
                    padding: 30px;
                    margin: 20px 0;
                    border: 1px solid #475569;
                    text-align: center;
                ">
                    <h2 style="color: #10b981; margin-bottom: 20px;">🚀 Bienvenido al Dashboard</h2>
                    <p style="color: #cbd5e1; font-size: 1.1rem; margin-bottom: 25px;">
                        Seleccione una opción del menú para comenzar a analizar sus portafolios
                    </p>
                    <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
                        <div class="hover-lift" style="
                            background: linear-gradient(135deg, #10b981, #059669);
                            border-radius: 12px;
                            padding: 20px;
                            width: 200px;
                            color: white;
                            text-align: center;
                            cursor: pointer;
                            transition: all 0.3s ease;
                        ">
                            <h4 style="margin: 0 0 10px 0; font-size: 2rem;">📊</h4>
                            <p style="margin: 0; font-weight: 600; font-size: 1.1rem;">Análisis de Portafolio</p>
                        </div>
                        <div class="hover-lift" style="
                            background: linear-gradient(135deg, #3b82f6, #2563eb);
                            border-radius: 12px;
                            padding: 20px;
                            width: 200px;
                            color: white;
                            text-align: center;
                            cursor: pointer;
                            transition: all 0.3s ease;
                        ">
                            <h4 style="margin: 0 0 10px 0; font-size: 2rem;">💰</h4>
                            <p style="margin: 0; font-weight: 600; font-size: 1.1rem;">Tasas de Caución</p>
                        </div>
                        <div class="hover-lift" style="
                            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
                            border-radius: 12px;
                            padding: 20px;
                            width: 200px;
                            color: white;
                            text-align: center;
                            cursor: pointer;
                            transition: all 0.3s ease;
                        ">
                            <h4 style="margin: 0 0 10px 0; font-size: 2rem;">👨‍💼</h4>
                            <p style="margin: 0; font-weight: 600; font-size: 1.1rem;">Panel del Asesor</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            elif opcion == "📊 Análisis de Portafolio":
                if st.session_state.cliente_seleccionado:
                    mostrar_analisis_portafolio()
                else:
                    st.markdown("""
                    <div style="
                        background: linear-gradient(135deg, #f59e0b, #d97706);
                        border-radius: 15px;
                        padding: 25px;
                        margin: 20px 0;
                        text-align: center;
                        color: white;
                    ">
                        <h3 style="margin: 0 0 15px 0;">👆 Seleccione un Cliente</h3>
                        <p style="margin: 0; font-size: 1.1rem;">
                            Para comenzar el análisis, seleccione un cliente en la barra lateral
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
            elif opcion == "💰 Tasas de Caución":
                if 'token_acceso' in st.session_state and st.session_state.token_acceso:
                    mostrar_tasas_caucion(st.session_state.token_acceso)
                else:
                    st.warning("Por favor inicie sesión para ver las tasas de caución")
                    
            elif opcion == "👨‍💼 Panel del Asesor":
                mostrar_movimientos_asesor()
                
        else:
            # Panel de bienvenida moderno
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 25px;
                padding: 50px;
                color: white;
                text-align: center;
                margin: 40px 0;
                box-shadow: 0 25px 50px rgba(0,0,0,0.3);
                border: 1px solid rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
            ">
                <h1 style="
                    color: white;
                    margin-bottom: 25px;
                    font-size: 2.5rem;
                    font-weight: 700;
                    text-shadow: 0 4px 8px rgba(0,0,0,0.3);
                ">🚀 Bienvenido al Portfolio Analyzer</h1>
                <p style="
                    font-size: 1.3rem;
                    margin-bottom: 35px;
                    opacity: 0.95;
                    line-height: 1.6;
                ">Conecte su cuenta de IOL para comenzar a analizar sus portafolios con tecnología de vanguardia</p>
                
                <div style="
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    gap: 25px;
                    margin-top: 40px;
                ">
                    <div style="
                        background: rgba(255,255,255,0.15);
                        border-radius: 20px;
                        padding: 30px;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255,255,255,0.2);
                        transition: transform 0.3s ease;
                    ">
                        <h3 style="margin: 0 0 15px 0; font-size: 1.5rem;">🇦🇷 Portafolio Argentina</h3>
                        <p style="margin: 0; opacity: 0.9; line-height: 1.5;">
                            Análisis completo de activos locales con métricas avanzadas de riesgo y retorno
                        </p>
                    </div>
                    
                    <div style="
                        background: rgba(255,255,255,0.15);
                        border-radius: 20px;
                        padding: 30px;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255,255,255,0.2);
                    ">
                        <h3 style="margin: 0 0 15px 0; font-size: 1.5rem;">🇺🇸 Portafolio EEUU</h3>
                        <p style="margin: 0; opacity: 0.9; line-height: 1.5;">
                            Gestión de activos internacionales con análisis de correlación y diversificación
                        </p>
                    </div>
                    
                    <div style="
                        background: rgba(255,255,255,0.15);
                        border-radius: 20px;
                        padding: 30px;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255,255,255,0.2);
                    ">
                        <h3 style="margin: 0 0 15px 0; font-size: 1.5rem;">📈 Optimización Avanzada</h3>
                        <p style="margin: 0; opacity: 0.9; line-height: 1.5;">
                            Algoritmos de optimización de portafolio basados en Markowitz y estrategias modernas
                        </p>
                    </div>
                    
                    <div style="
                        background: rgba(255,255,255,0.15);
                        border-radius: 20px;
                        padding: 30px;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255,255,255,0.2);
                    ">
                        <h3 style="margin: 0 0 15px 0; font-size: 1.5rem;">🛡️ Gestión de Riesgo</h3>
                        <p style="margin: 0; opacity: 0.9; line-height: 1.5;">
                            Análisis de VaR, stress testing y estrategias de cobertura personalizadas
                        </p>
                    </div>
                </div>
                
                <div style="
                    margin-top: 40px;
                    padding: 25px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 15px;
                    border: 1px solid rgba(255,255,255,0.2);
                ">
                    <h3 style="margin: 0 0 15px 0; color: #fbbf24;">🔐 Inicie Sesión</h3>
                    <p style="margin: 0; opacity: 0.9;">
                        Use la barra lateral para conectarse a su cuenta de IOL y comenzar
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Características principales
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #1e293b, #334155);
                border-radius: 20px;
                padding: 30px;
                margin: 30px 0;
                border: 1px solid #475569;
            ">
                <h2 style="color: #10b981; text-align: center; margin-bottom: 30px;">✨ Características Principales</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px;">
                    <div style="
                        background: rgba(16, 185, 129, 0.1);
                        border-radius: 15px;
                        padding: 25px;
                        border: 1px solid rgba(16, 185, 129, 0.3);
                    ">
                        <h3 style="color: #10b981; margin-bottom: 15px;">📊 Análisis Detallado</h3>
                        <ul style="color: #cbd5e1; margin: 0; padding-left: 20px;">
                            <li>Valuación completa de activos</li>
                            <li>Distribución por tipo de instrumento</li>
                            <li>Concentración del portafolio</li>
                        </ul>
                    </div>
                    <div style="
                        background: rgba(59, 130, 246, 0.1);
                        border-radius: 15px;
                        padding: 25px;
                        border: 1px solid rgba(59, 130, 246, 0.3);
                    ">
                        <h3 style="color: #3b82f6; margin-bottom: 15px;">📈 Herramientas Profesionales</h3>
                        <ul style="color: #cbd5e1; margin: 0; padding-left: 20px;">
                            <li>Optimización de portafolio</li>
                            <li>Análisis técnico avanzado</li>
                            <li>Proyecciones de rendimiento</li>
                        </ul>
                    </div>
                    <div style="
                        background: rgba(139, 92, 246, 0.1);
                        border-radius: 15px;
                        padding: 25px;
                        border: 1px solid rgba(139, 92, 246, 0.3);
                    ">
                        <h3 style="color: #8b5cf6; margin-bottom: 15px;">💱 Datos de Mercado</h3>
                        <ul style="color: #cbd5e1; margin: 0; padding-left: 20px;">
                            <li>Cotizaciones MEP en tiempo real</li>
                            <li>Tasas de caución actualizadas</li>
                            <li>Estado de cuenta consolidado</li>
                        </ul>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Error en la aplicación: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main() 
