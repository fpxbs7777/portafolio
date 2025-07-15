import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import io
import base64
from scipy import stats
import matplotlib.pyplot as plt
import os
import google.generativeai as genai
import time
import markdown2
# Nuevas importaciones para análisis intermarket
import yfinance as yf
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Configuración de estilos personalizados
st.set_page_config(
    page_title="BCRA Analytics | Dashboard Económico",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def metric_card(title: str, value: str, change: float = None, icon: str = "chart-line", color: str = "blue") -> str:
    """Crea una tarjeta de métrica con estilo ultra-moderno"""
    color_classes = {
        "blue": {"gradient": "from-blue-500 to-blue-600", "bg": "bg-blue-50", "text": "text-blue-700", "icon": "text-blue-600"},
        "green": {"gradient": "from-emerald-500 to-green-600", "bg": "bg-emerald-50", "text": "text-emerald-700", "icon": "text-emerald-600"},
        "yellow": {"gradient": "from-amber-500 to-yellow-600", "bg": "bg-amber-50", "text": "text-amber-700", "icon": "text-amber-600"},
        "red": {"gradient": "from-red-500 to-rose-600", "bg": "bg-red-50", "text": "text-red-700", "icon": "text-red-600"},
        "purple": {"gradient": "from-purple-500 to-violet-600", "bg": "bg-purple-50", "text": "text-purple-700", "icon": "text-purple-600"},
        "indigo": {"gradient": "from-indigo-500 to-blue-600", "bg": "bg-indigo-50", "text": "text-indigo-700", "icon": "text-indigo-600"}
    }
    
    colors = color_classes.get(color, color_classes["blue"])
    
    change_html = ""
    if change is not None:
        is_positive = change >= 0
        change_icon = "↗" if is_positive else "↘"
        change_color = "text-emerald-600" if is_positive else "text-red-600"
        change_bg = "bg-emerald-100" if is_positive else "bg-red-100"
        change_html = f"""
        <div class="flex items-center gap-1 mt-3">
            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium {change_bg} {change_color}">
                {change_icon} {abs(change):.2f}%
            </span>
        </div>
        """
    
    return f"""
    <div class="metric-card group">
        <div class="flex items-start justify-between h-full">
            <div class="flex-1">
                <div class="metric-icon bg-gradient-to-br {colors['gradient']} text-white">
                    <i class="fas fa-{icon}"></i>
                </div>
                <p class="metric-label">{title}</p>
                <p class="metric-value">{value}</p>
                {change_html}
            </div>
        </div>
    </div>
    """

# Configuración de la API de Gemini por defecto
DEFAULT_GEMINI_API_KEY = "AIzaSyBFtK05ndkKgo4h0w9gl224Gn94NaWaI6E"

# Configurar genai solo si está disponible
try:
    import google.generativeai as genai
    genai.configure(api_key=DEFAULT_GEMINI_API_KEY)
except ImportError:
    pass

# Estilos CSS avanzados y diseño moderno
st.markdown("""
    <style>
    /* Importar fuentes modernas */
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@200;300;400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');
    
    /* Variables CSS globales */
    :root {
        --primary: #0f172a;
        --secondary: #334155;
        --accent: #3b82f6;
        --accent-light: #60a5fa;
        --success: #22c55e;
        --warning: #f59e0b;
        --danger: #ef4444;
        --background: #fafbfc;
        --surface: #ffffff;
        --surface-alt: #f8fafc;
        --text-primary: #0f172a;
        --text-secondary: #64748b;
        --text-muted: #94a3b8;
        --border: #e2e8f0;
        --border-light: #f1f5f9;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        --radius: 12px;
        --radius-sm: 8px;
        --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Reset y configuración base */
    .stApp {
        background: linear-gradient(135deg, var(--background) 0%, #f1f5f9 100%);
        font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: var(--text-primary);
        min-height: 100vh;
    }
    
    /* Sidebar mejorado */
    .css-1d391kg {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 50%, #334155 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.1) !important;
    }
    
    .css-1d391kg .css-17eq0hr {
        color: #e2e8f0 !important;
    }
    
    /* Header principal elegante */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 25%, #334155 50%, #475569 100%);
        color: white;
        padding: 2.5rem 2rem;
        border-radius: var(--radius);
        margin-bottom: 2rem;
        box-shadow: var(--shadow-xl);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Ccircle cx='60' cy='60' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        opacity: 0.3;
    }
    
    .main-header h1 {
        font-size: clamp(1.8rem, 4vw, 2.5rem);
        font-weight: 700;
        margin: 0;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        position: relative;
        z-index: 1;
        letter-spacing: -0.025em;
    }
    
    .main-header .subtitle {
        font-size: 1rem;
        font-weight: 300;
        text-align: center;
        margin-top: 0.5rem;
        opacity: 0.9;
        position: relative;
        z-index: 1;
        color: #cbd5e1;
    }
    
    /* Tarjetas de métricas ultra-modernas */
    .metric-card {
        background: var(--surface);
        padding: 2rem;
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        border: 1px solid var(--border-light);
        transition: var(--transition);
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
        height: 100%;
        min-height: 140px;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--accent) 0%, var(--accent-light) 100%);
        transform: scaleX(0);
        transform-origin: left;
        transition: var(--transition);
    }
    
    .metric-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: var(--shadow-xl);
        border-color: var(--accent);
    }
    
    .metric-card:hover::before {
        transform: scaleX(1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 1rem 0 0.5rem 0;
        line-height: 1.1;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    
    .metric-date {
        font-size: 0.75rem;
        color: var(--text-muted);
        font-weight: 400;
        margin-top: 0.75rem;
    }
    
    .metric-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%);
        color: white;
        box-shadow: var(--shadow);
    }
    
    /* Secciones elegantes */
    .section-header {
        background: var(--surface);
        padding: 2rem;
        border-radius: var(--radius);
        margin: 2rem 0 1.5rem 0;
        border-left: 4px solid var(--accent);
        box-shadow: var(--shadow);
        position: relative;
    }
    
    .section-header::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 100px;
        height: 100%;
        background: linear-gradient(90deg, transparent 0%, var(--accent) 100%);
        opacity: 0.05;
        border-radius: 0 var(--radius) var(--radius) 0;
    }
    
    .section-header h2 {
        margin: 0 0 0.5rem 0;
        color: var(--text-primary);
        font-size: 1.75rem;
        font-weight: 700;
        position: relative;
        z-index: 1;
    }
    
    .section-header p {
        margin: 0;
        color: var(--text-secondary);
        font-size: 1rem;
        position: relative;
        z-index: 1;
    }
    
    /* Controles modernos */
    .controls-section {
        background: var(--surface);
        padding: 2rem;
        border-radius: var(--radius);
        margin: 1.5rem 0;
        box-shadow: var(--shadow);
        border: 1px solid var(--border);
    }
    
    /* Botones premium */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.875rem 2rem !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: var(--transition) !important;
        box-shadow: var(--shadow) !important;
        text-transform: none !important;
        letter-spacing: 0.025em !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-lg) !important;
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Selectbox elegante */
    .stSelectbox > div > div {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        box-shadow: var(--shadow-sm) !important;
        transition: var(--transition) !important;
    }
    
    .stSelectbox > div > div:hover {
        border-color: var(--accent) !important;
        box-shadow: var(--shadow) !important;
    }
    
    /* Tabs ultra-modernos */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--surface) !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.5rem !important;
        box-shadow: var(--shadow) !important;
        border: 1px solid var(--border) !important;
        gap: 0.25rem !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-sm) !important;
        padding: 0.875rem 1.5rem !important;
        font-weight: 500 !important;
        transition: var(--transition) !important;
        border: none !important;
        color: var(--text-secondary) !important;
        background: transparent !important;
        font-size: 0.95rem !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: var(--surface-alt) !important;
        color: var(--text-primary) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%) !important;
        color: white !important;
        box-shadow: var(--shadow) !important;
    }
    
    /* Dataframes elegantes */
    .stDataFrame {
        border-radius: var(--radius) !important;
        overflow: hidden !important;
        box-shadow: var(--shadow) !important;
        border: 1px solid var(--border) !important;
    }
    
    .stDataFrame [data-testid="stDataFrameResizable"] {
        border-radius: var(--radius) !important;
    }
    
    /* Footer premium */
    .footer {
        background: linear-gradient(135deg, var(--surface) 0%, var(--surface-alt) 100%);
        padding: 3rem 2rem;
        border-radius: var(--radius);
        margin-top: 4rem;
        text-align: center;
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--border);
        position: relative;
        overflow: hidden;
    }
    
    .footer::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--accent) 0%, var(--success) 50%, var(--warning) 100%);
    }
    
    .footer p {
        margin: 0.75rem 0;
        color: var(--text-secondary);
        font-weight: 400;
    }
    
    .footer .footer-title {
        color: var(--text-primary);
        font-weight: 700;
        font-size: 1.25rem;
        margin-bottom: 1rem;
    }
    
    /* Indicadores de estado elegantes */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        margin: 0.25rem;
    }
    
    .status-online {
        background: rgba(34, 197, 94, 0.1);
        color: #16a34a;
        border: 1px solid rgba(34, 197, 94, 0.2);
    }
    
    .status-warning {
        background: rgba(245, 158, 11, 0.1);
        color: #d97706;
        border: 1px solid rgba(245, 158, 11, 0.2);
    }
    
    /* Indicadores de ciclo económico */
    .cycle-indicator {
        padding: 1rem;
        border-radius: var(--radius);
        text-align: center;
        font-weight: bold;
        margin: 1rem 0;
        box-shadow: var(--shadow);
        border: 2px solid;
    }
    
    .expansion {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724;
        border-color: #28a745;
    }
    
    .peak {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        color: #856404;
        border-color: #ffc107;
    }
    
    .contraction {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        color: #721c24;
        border-color: #dc3545;
    }
    
    .recession {
        background: linear-gradient(135deg, #cce5ff 0%, #b3d9ff 100%);
        color: #004085;
        border-color: #007bff;
    }
        color: #d97706;
        border: 1px solid rgba(245, 158, 11, 0.2);
    }
    
    .status-error {
        background: rgba(239, 68, 68, 0.1);
        color: #dc2626;
        border: 1px solid rgba(239, 68, 68, 0.2);
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: currentColor;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Animaciones suaves */
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Scrollbar personalizado */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--surface-alt);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border);
        border-radius: 4px;
        transition: var(--transition);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }
    
    /* Responsive design mejorado */
    @media (max-width: 768px) {
        .main-header {
            padding: 2rem 1rem;
        }
        
        .main-header h1 {
            font-size: 2rem;
            gap: 1rem;
        }
        
        .metric-card {
            padding: 1.5rem;
        }
        
        .metric-value {
            font-size: 1.75rem;
        }
        
        .section-header {
            padding: 1.5rem;
        }
        
        .controls-section {
            padding: 1.5rem;
        }
    }
    
    /* Estados de carga elegantes */
    .loading-shimmer {
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: shimmer 2s infinite;
    }
    
    @keyframes shimmer {
        0% {
            background-position: -200% 0;
        }
        100% {
            background-position: 200% 0;
        }
    }
    
    /* Mejoras en métricas */
    .metric-container {
        display: grid;
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    /* Mejoras en gráficos */
    .chart-container {
        background: var(--surface);
        border-radius: var(--radius);
        padding: 1.5rem;
        box-shadow: var(--shadow);
        border: 1px solid var(--border);
        margin: 1.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header principal mejorado
st.markdown("""
    <div class="main-header fade-in">
        <h1>📊 BCRA Analytics</h1>
        <div class="subtitle">Centro de Análisis Económico • Banco Central de la República Argentina</div>
    </div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)  # Cachear por 1 hora
def get_bcra_variables():
    url = "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        requests.packages.urllib3.disable_warnings()
        response = requests.get(url, headers=headers, verify=False, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        variables = []
        
        tables = soup.find_all('table', {'class': 'table'})
        if not tables:
            return pd.DataFrame()
            
        table = tables[0]
        rows = table.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                link = cols[0].find('a')
                href = link.get('href') if link else ''
                serie = ''
                
                if href and 'serie=' in href:
                    serie = href.split('serie=')[1].split('&')[0]
                
                variable = {
                    'Nombre': cols[0].get_text(strip=True),
                    'Fecha': cols[1].get_text(strip=True) if len(cols) > 1 else '',
                    'Valor': cols[2].get_text(strip=True) if len(cols) > 2 else '',
                    'Serie ID': serie,
                    'URL': f"https://www.bcra.gob.ar{href}" if href else ''
                }
                variables.append(variable)
        
        return pd.DataFrame(variables)
    
    except Exception as e:
        st.error(f"Error al obtener las variables del BCRA: {str(e)}")
        return pd.DataFrame()

def get_historical_data(serie_id, fecha_desde=None, fecha_hasta=None):
    if not fecha_desde:
        fecha_desde = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not fecha_hasta:
        fecha_hasta = datetime.now().strftime('%Y-%m-%d')
    
    url = "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables_datos.asp"
    params = {
        'serie': serie_id,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'primeravez': '1'
    }
    
    try:
        response = requests.get(url, params=params, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        table = soup.find('table', {'class': 'table'})
        if not table:
            return pd.DataFrame()
            
        headers = []
        header_row = table.find('tr')
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
        
        data = []
        rows = table.find_all('tr')[1:]
        
        for row in rows:
            cols = row.find_all('td')
            if cols:
                row_data = [col.get_text(strip=True) for col in cols]
                data.append(row_data)
        
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data, columns=headers)
        
        if 'Fecha' in df.columns and len(df.columns) > 1:
            value_column = df.columns[1]
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
            df[value_column] = df[value_column].str.replace('.', '').str.replace(',', '.').astype(float, errors='ignore')
            df = df.sort_values('Fecha')
            df = df.rename(columns={value_column: 'Valor'})
            df = df.dropna(subset=['Fecha', 'Valor'])
            return df
            
        return df
        
    except Exception as e:
        st.error(f"Error al obtener datos históricos: {str(e)}")
        return pd.DataFrame()

def calculate_metrics(data):
    """Calcular métricas a partir de los datos"""
    if data is None or data.empty or 'Valor' not in data.columns or 'Fecha' not in data.columns:
        return 0, 0, 0, 0, 0
    
    data = data.sort_values('Fecha')
    current_value = data['Valor'].iloc[-1]
    previous_value = data['Valor'].iloc[-2] if len(data) > 1 else current_value
    change = current_value - previous_value
    change_pct = (change / previous_value * 100) if previous_value != 0 else 0
    max_val = data['Valor'].max()
    min_val = data['Valor'].min()
    
    return current_value, change, change_pct, max_val, min_val

def create_professional_chart(data, title, variable_name):
    """Crear gráfico profesional con diseño ultra-moderno"""
    # Verificar que los datos no estén vacíos y tengan las columnas necesarias
    if data is None or data.empty or 'Valor' not in data.columns or 'Fecha' not in data.columns:
        st.error("Datos no válidos para generar el gráfico")
        return go.Figure(), 0, 0, 0, 0, 0
    
    try:
        # Asegurarse de que los valores sean numéricos
        data['Valor'] = pd.to_numeric(data['Valor'], errors='coerce')
        data = data.dropna(subset=['Valor', 'Fecha'])
        
        if len(data) < 2:
            st.error("No hay suficientes datos para generar el gráfico")
            return go.Figure(), 0, 0, 0
            
        # Ordenar por fecha
        data = data.sort_values('Fecha')
        
        # Calcular métricas iniciales
        current_value, change, change_pct, max_val, min_val = calculate_metrics(data)
        
        # Crear el gráfico principal con tema moderno
        fig = go.Figure()
        
        # Gradiente para el área bajo la curva
        fig.add_trace(go.Scatter(
            x=data['Fecha'],
            y=data['Valor'],
            mode='lines',
            name=variable_name,
            line=dict(
                color='rgba(59, 130, 246, 0)',
                width=0
            ),
            fill='tonexty',
            fillcolor='rgba(59, 130, 246, 0.05)',
            hoverinfo='skip',
            showlegend=False
        ))
        
        # Línea principal elegante
        fig.add_trace(go.Scatter(
            x=data['Fecha'],
            y=data['Valor'],
            mode='lines+markers',
            name=variable_name,
            line=dict(
                color='#3b82f6',
                width=3,
                shape='spline',
                smoothing=0.3
            ),
            marker=dict(
                size=6,
                color='#3b82f6',
                line=dict(color='white', width=2),
                opacity=0.8
            ),
            hovertemplate='<b>💰 %{y:,.2f}</b><br>📅 %{x|%d/%m/%Y}<br><extra></extra>',
            connectgaps=True
        ))
        
        # Línea de tendencia elegante (solo si hay suficientes puntos)
        if len(data) > 3:
            try:
                from scipy import stats
                x_numeric = np.arange(len(data))
                y_values = data['Valor'].values
                
                # Calcular regresión lineal
                slope, intercept, r_value, p_value, std_err = stats.linregress(x_numeric, y_values)
                trend_line = slope * x_numeric + intercept
                
                # Color de tendencia basado en la pendiente
                trend_color = '#10b981' if slope > 0 else '#ef4444' if slope < 0 else '#6b7280'
                
                fig.add_trace(go.Scatter(
                    x=data['Fecha'],
                    y=trend_line,
                    mode='lines',
                    name=f'Tendencia (R²: {r_value**2:.3f})',
                    line=dict(
                        color=trend_color,
                        width=2,
                        dash='dot'
                    ),
                    hovertemplate='<b>📈 Tendencia: %{y:,.2f}</b><br>📅 %{x|%d/%m/%Y}<extra></extra>'
                ))
            except Exception as e:
                pass  # Continuar sin línea de tendencia si hay error
        
        # Agregar marcadores para valores extremos
        max_idx = data['Valor'].idxmax()
        min_idx = data['Valor'].idxmin()
        
        # Marcador para máximo
        fig.add_trace(go.Scatter(
            x=[data.loc[max_idx, 'Fecha']],
            y=[data.loc[max_idx, 'Valor']],
            mode='markers+text',
            name='Máximo',
            marker=dict(
                size=12,
                color='#10b981',
                symbol='triangle-up',
                line=dict(color='white', width=2)
            ),
            text=['📈 MAX'],
            textposition='top center',
            textfont=dict(size=10, color='#10b981', family='Manrope'),
            hovertemplate='<b>🔝 Máximo: %{y:,.2f}</b><br>📅 %{x|%d/%m/%Y}<extra></extra>',
            showlegend=False
        ))
        
        # Marcador para mínimo
        fig.add_trace(go.Scatter(
            x=[data.loc[min_idx, 'Fecha']],
            y=[data.loc[min_idx, 'Valor']],
            mode='markers+text',
            name='Mínimo',
            marker=dict(
                size=12,
                color='#ef4444',
                symbol='triangle-down',
                line=dict(color='white', width=2)
            ),
            text=['📉 MIN'],
            textposition='bottom center',
            textfont=dict(size=10, color='#ef4444', family='Manrope'),
            hovertemplate='<b>🔻 Mínimo: %{y:,.2f}</b><br>📅 %{x|%d/%m/%Y}<extra></extra>',
            showlegend=False
        ))        
        # Diseño ultra-moderno del gráfico
        fig.update_layout(
            title=dict(
                text=f"<b>{title}</b>",
                x=0.5,
                xanchor='center',
                font=dict(size=22, family='Manrope', color='#0f172a'),
                pad=dict(t=20, b=20)
            ),
            xaxis=dict(
                title=dict(
                    text="📅 Período",
                    font=dict(size=14, family='Manrope', color='#64748b')
                ),
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(226, 232, 240, 0.6)',
                showline=True,
                linewidth=1,
                linecolor='#e2e8f0',
                tickformat='%d/%m',
                tickfont=dict(size=11, family='Manrope', color='#64748b'),
                rangeslider=dict(
                    visible=True,                    thickness=0.06,
                    bgcolor='rgba(248, 250, 252, 0.8)',
                    bordercolor='#e2e8f0'
                ),
                rangeselector=dict(
                    buttons=list([
                        dict(count=7, label="7D", step="day", stepmode="backward"),
                        dict(count=30, label="30D", step="day", stepmode="backward"),
                        dict(count=90, label="3M", step="day", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="1A", step="year", stepmode="backward"),
                        dict(step="all", label="Todos")
                    ]),
                    bgcolor='rgba(255, 255, 255, 0.9)',                    bordercolor='#e2e8f0',
                    font=dict(size=10, family='Manrope')
                )
            ),
            yaxis=dict(
                title=dict(
                    text=f"💰 {variable_name}",
                    font=dict(size=14, family='Manrope', color='#64748b')
                ),
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(226, 232, 240, 0.6)',
                showline=True,
                linewidth=1,
                linecolor='#e2e8f0',
                tickformat=',.0f',
                tickfont=dict(size=11, family='Manrope', color='#64748b'),
                zeroline=True,
                zerolinecolor='rgba(156, 163, 175, 0.5)',
                zerolinewidth=1
            ),
            plot_bgcolor='rgba(248, 250, 252, 0.4)',
            paper_bgcolor='white',
            hovermode='x unified',            hoverlabel=dict(
                bgcolor='white',
                bordercolor='#e2e8f0',
                font_size=12,
                font_family='Manrope',
                font_color='#0f172a'
            ),
            margin=dict(l=60, r=60, t=100, b=80),
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='center',
                x=0.5,
                font=dict(size=11, family='Manrope', color='#64748b'),
                bgcolor='rgba(255, 255, 255, 0.9)',                bordercolor='#e2e8f0'
            ),
            font=dict(family='Manrope', color='#0f172a'),
            dragmode='zoom',
            height=500
        )
        
        # Agregar anotaciones elegantes para contexto
        fig.add_annotation(
            text=f"Último valor: <b>{current_value:,.2f}</b>",
            xref="paper", yref="paper",
            x=0.02, y=0.98, xanchor="left", yanchor="top",
            bgcolor="rgba(59, 130, 246, 0.1)",
            bordercolor="#3b82f6",            font=dict(size=11, family='Manrope', color='#3b82f6')
        )
        
        return fig, current_value, change, change_pct, max_val, min_val        
    except Exception as e:
        st.error(f"Error al generar el gráfico: {str(e)}")
        return go.Figure(), 0, 0, 0, 0, 0

def generate_basic_analysis_report(data: pd.DataFrame, variable_name: str, variable_description: str = "") -> str:
    """
    Genera un informe básico de análisis como fallback.
    """
    try:
        data_clean = data.dropna(subset=['Valor', 'Fecha']).copy()
        data_clean['Valor'] = pd.to_numeric(data_clean['Valor'], errors='coerce')
        data_clean = data_clean.dropna(subset=['Valor'])
        
        if len(data_clean) == 0:
            return "## ⚠️ Sin datos válidos\n\nNo hay datos válidos para analizar."
        
        summary = data_clean['Valor'].describe().to_dict()
        last_value = data_clean['Valor'].iloc[-1]
        first_value = data_clean['Valor'].iloc[0]
        total_change = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0
        
        # Calcular métricas
        volatility = data_clean['Valor'].std() / data_clean['Valor'].mean() * 100 if data_clean['Valor'].mean() != 0 else 0
        x_vals = np.arange(len(data_clean))
        coeffs = np.polyfit(x_vals, data_clean['Valor'], 1)
        trend = "alcista" if coeffs[0] > 0 else "bajista" if coeffs[0] < 0 else "estable"
        
        # Determinar nivel de volatilidad
        if volatility < 5:
            volatility_level = "baja"
            volatility_emoji = "🟢"
        elif volatility < 15:
            volatility_level = "moderada"
            volatility_emoji = "🟡"
        else:
            volatility_level = "alta"
            volatility_emoji = "🔴"
        
        # Generar informe básico estructurado
        report = f"""
# 📊 Informe de Análisis Económico - {variable_name}

*Generado automáticamente el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}*  
*Período analizado: {data_clean['Fecha'].min().strftime('%d/%m/%Y')} - {data_clean['Fecha'].max().strftime('%d/%m/%Y')}*

---

## 📋 Resumen Ejecutivo

• **Variable analizada**: {variable_name}
• **Período de análisis**: {(data_clean['Fecha'].max() - data_clean['Fecha'].min()).days} días
• **Variación total**: {total_change:+.2f}%
• **Tendencia general**: {trend.upper()}
• **Volatilidad**: {volatility_emoji} {volatility_level.upper()} ({volatility:.2f}%)

## 📈 Análisis de Tendencias

### Comportamiento General
La variable **{variable_name}** mostró una tendencia **{trend}** durante el período analizado, con una variación total de **{total_change:+.2f}%**.

### Puntos Destacados
- **Valor inicial**: {first_value:,.2f}
- **Valor final**: {last_value:,.2f}
- **Valor máximo**: {summary.get('max', 0):,.2f}
- **Valor mínimo**: {summary.get('min', 0):,.2f}
- **Promedio del período**: {summary.get('mean', 0):,.2f}

## 🔍 Análisis Estadístico

| Métrica | Valor |
|---------|-------|
| **Media** | {summary.get('mean', 0):,.2f} |
| **Mediana** | {summary.get('50%', 0):,.2f} |
| **Desviación Estándar** | {summary.get('std', 0):,.2f} |
| **Rango** | {summary.get('max', 0) - summary.get('min', 0):,.2f} |
| **Coeficiente de Variación** | {volatility:.2f}% |

### Distribución de Valores
- **Q1 (25%)**: {summary.get('25%', 0):,.2f}
- **Q3 (75%)**: {summary.get('75%', 0):,.2f}
- **Rango intercuartílico**: {summary.get('75%', 0) - summary.get('25%', 0):,.2f}

## 💡 Insights Económicos

### Volatilidad {volatility_emoji}
La volatilidad de **{volatility:.2f}%** se considera **{volatility_level}**:
"""
        
        if volatility < 5:
            report += """
- ✅ **Estabilidad alta**: La variable muestra comportamiento predecible
- ✅ **Riesgo bajo**: Fluctuaciones menores en el período
- ✅ **Tendencia clara**: Patrón de movimiento bien definido
"""
        elif volatility < 15:
            report += """
- ⚠️ **Estabilidad moderada**: Algunas fluctuaciones observadas
- ⚠️ **Riesgo moderado**: Variaciones dentro de rangos esperados
- ⚠️ **Seguimiento recomendado**: Monitorear cambios significativos
"""
        else:
            report += """
- 🚨 **Alta volatilidad**: Fluctuaciones significativas detectadas
- 🚨 **Riesgo elevado**: Variaciones importantes en el período
- 🚨 **Atención especial**: Requiere monitoreo continuo
"""

        report += f"""

### Tendencia {trend.title()}
"""
        
        if trend == "alcista":
            report += f"""
- 📈 **Crecimiento sostenido**: Incremento de {abs(total_change):.2f}%
- 💹 **Momentum positivo**: Dirección ascendente confirmada
- 🎯 **Proyección favorable**: Tendencia hacia valores superiores
"""
        elif trend == "bajista":
            report += f"""
- 📉 **Declive observado**: Disminución de {abs(total_change):.2f}%
- ⬇️ **Momentum negativo**: Dirección descendente confirmada
- 🎯 **Atención requerida**: Monitorear evolución futura
"""
        else:
            report += f"""
- ➡️ **Estabilidad relativa**: Variación mínima de {abs(total_change):.2f}%
- ⚖️ **Equilibrio**: Sin tendencia dominante clara
- 🎯 **Consolidación**: Período de estabilización
"""

        report += f"""

## 📊 Conclusiones y Recomendaciones

### Hallazgos Principales
1. **Comportamiento general**: La variable mostró una tendencia **{trend}** con volatilidad **{volatility_level}**
2. **Rango de valores**: Fluctuó entre {summary.get('min', 0):,.2f} y {summary.get('max', 0):,.2f}
3. **Estabilidad**: El coeficiente de variación de {volatility:.2f}% indica {volatility_level} predictibilidad

### Recomendaciones de Seguimiento
- 📅 **Frecuencia**: Monitoreo {'diario' if volatility > 15 else 'semanal' if volatility > 5 else 'quincenal'}
- 🎯 **Niveles clave**: Vigilar quiebres de {summary.get('min', 0):,.2f} (soporte) y {summary.get('max', 0):,.2f} (resistencia)
- ⚠️ **Alertas**: Configurar notificaciones para cambios > {volatility * 1.5:.1f}%

---

## 📋 Datos Técnicos del Análisis

| Métrica Técnica | Valor |
|------------------|-------|
| **Observaciones** | {len(data_clean):,} |
| **Período (días)** | {(data_clean['Fecha'].max() - data_clean['Fecha'].min()).days} |
| **Volatilidad** | {volatility:.2f}% |
| **Tendencia** | {trend.title()} |
| **R² aproximado** | {abs(coeffs[0]) / (summary.get('std', 1) + 0.001) * 100:.2f}% |

*Análisis generado automáticamente con algoritmos estadísticos + datos oficiales del BCRA*
"""
        
        return report
        
    except Exception as e:
        return f"## ❌ Error en el análisis básico\n\nNo se pudo generar el análisis: {str(e)}"

def generate_analysis_report(data: pd.DataFrame, variable_name: str, variable_description: str = "") -> str:
    """
    Función principal para generar análisis. Usa el análisis básico como fallback.
    """
    return generate_basic_analysis_report(data, variable_name, variable_description)

# Función para verificar e instalar dependencias
def check_and_install_dependencies():
    """Verifica e instala las dependencias necesarias"""
    missing_deps = []
    
    try:
        import google.generativeai as genai
    except ImportError:
        missing_deps.append("google-generativeai")
    
    try:
        import markdown2
    except ImportError:
        missing_deps.append("markdown2")
    
    if missing_deps:
        st.error(f"⚠️ **Dependencias faltantes**: {', '.join(missing_deps)}")
        
        with st.expander("📦 **Instrucciones de instalación**", expanded=True):
            st.markdown("### Para instalar las dependencias necesarias:")
            st.code(f"pip install {' '.join(missing_deps)}", language="bash")
            
            st.markdown("### O instalar todas las dependencias:")
            st.code("pip install google-generativeai markdown2 streamlit pandas plotly requests beautifulsoup4 scipy matplotlib numpy", language="bash")
            
            st.markdown("### Después de la instalación:")
            st.markdown("1. Reinicie la aplicación")
            st.markdown("2. El análisis avanzado estará disponible")
            
            st.warning("⚠️ **Nota**: Sin estas dependencias, el análisis avanzado no funcionará, pero el análisis estadístico básico seguirá disponible.")
        
        return False
    
    return True

def create_glossary():
    """
    Crea un glosario interactivo de términos económicos y financieros.
    """
    return {
        "Volatilidad": {
            "definicion": "Medida de la variabilidad o dispersión de los rendimientos de un activo o variable económica en un período determinado.",
            "explicacion": "En términos simples, la volatilidad nos dice qué tan 'movidos' o 'estables' son los valores de una variable. Alta volatilidad = mucho movimiento/riesgo. Baja volatilidad = estabilidad/predictibilidad.",
            "ejemplo": "Si el precio del dólar varía mucho día a día, tiene alta volatilidad. Si se mantiene estable, tiene baja volatilidad."
        },
        "Tendencia": {
            "definicion": "Dirección general que sigue una variable económica durante un período de tiempo específico.",
            "explicacion": "Es como la 'dirección general' hacia donde va una variable: puede ir hacia arriba (alcista), hacia abajo (bajista) o mantenerse estable (lateral).",
            "ejemplo": "Si la inflación viene subiendo mes tras mes, tiene una tendencia alcista o ascendente."
        },
        "Alcista": {
            "definicion": "Tendencia ascendente o de crecimiento en una variable económica o financiera.",
            "explicacion": "Cuando los valores van 'para arriba' de manera consistente. Es una buena noticia para algunas variables (como el empleo) y mala para otras (como la inflación).",
            "ejemplo": "Un mercado alcista significa que los precios de las acciones están subiendo."
        },
        "Bajista": {
            "definicion": "Tendencia descendente o de declive en una variable económica o financiera.",
            "explicacion": "Cuando los valores van 'para abajo' de manera consistente. Puede ser bueno (inflación bajando) o malo (empleo bajando).",
            "ejemplo": "Un mercado bajista significa que los precios están cayendo."
        },
        "Coeficiente de Variación": {
            "definicion": "Medida estadística que relaciona la desviación estándar con la media, expresada como porcentaje.",
            "explicacion": "Es una forma de medir qué tan 'dispersos' están los datos comparado con su promedio. Nos ayuda a comparar la variabilidad entre diferentes variables.",
            "ejemplo": "Si una variable tiene un coeficiente de variación del 10%, significa que su variabilidad es moderada."
        },
        "Desviación Estándar": {
            "definicion": "Medida de dispersión que indica cuánto se alejan los valores individuales del promedio.",
            "explicacion": "Nos dice qué tan 'esparcidos' están los valores alrededor del promedio. Un número alto significa mucha dispersión.",
            "ejemplo": "Si el promedio de temperaturas es 20°C y la desviación estándar es 5°C, la mayoría de días tendrán entre 15°C y 25°C."
        },
        "Resistencia": {
            "definicion": "Nivel de precio o valor que una variable tiene dificultades para superar hacia arriba.",
            "explicacion": "Es como un 'techo' que la variable no logra romper. Cuando llega a ese nivel, tiende a bajar.",
            "ejemplo": "Si el dólar siempre baja cuando llega a $1000, ese nivel actúa como resistencia."
        },
        "Soporte": {
            "definicion": "Nivel de precio o valor donde una variable tiende a encontrar demanda y dejar de caer.",
            "explicacion": "Es como un 'piso' que sostiene a la variable. Cuando llega a ese nivel, tiende a subir o estabilizarse.",
            "ejemplo": "Si el dólar siempre sube cuando llega a $800, ese nivel actúa como soporte."
        },
        "Rango": {
            "definicion": "Diferencia entre el valor máximo y mínimo de una variable en un período determinado.",
            "explicacion": "Es la 'amplitud' de movimiento de la variable, desde su punto más bajo hasta el más alto.",
            "ejemplo": "Si una acción osciló entre $100 y $150, su rango es de $50."
        },
        "Percentil": {
            "definicion": "Valor que divide un conjunto de datos en porcentajes específicos.",
            "explicacion": "Los percentiles nos dicen en qué posición está un valor comparado con todos los demás. Por ejemplo, el percentil 75 significa que el 75% de los valores están por debajo.",
            "ejemplo": "Si tu salario está en el percentil 90, significa que ganas más que el 90% de la población."
        },
        "Media/Promedio": {
            "definicion": "Suma de todos los valores dividida por la cantidad de observaciones.",
            "explicacion": "El 'centro' o valor típico de todos los datos. Es lo que comúnmente llamamos promedio.",
            "ejemplo": "Si tengo calificaciones de 8, 9 y 10, la media es (8+9+10)/3 = 9."
        },
        "Mediana": {
            "definicion": "Valor central que divide los datos ordenados en dos mitades iguales.",
            "explicacion": "Es el valor del 'medio' cuando ordenas todos los datos de menor a mayor. A veces es más representativo que el promedio.",
            "ejemplo": "En los valores 1, 2, 3, 4, 100, la mediana es 3 (más representativa que el promedio de 22)."
        }
    }

def calculate_specific_metrics(data: pd.DataFrame, variable_name: str):
    """
    Calcula métricas específicas para análisis detallado por variable.
    """
    if data.empty or 'Valor' not in data.columns:
        return {}
    
    try:
        data_clean = data.dropna(subset=['Valor', 'Fecha']).copy()
        data_clean['Valor'] = pd.to_numeric(data_clean['Valor'], errors='coerce')
        data_clean = data_clean.dropna(subset=['Valor'])
        
        if len(data_clean) < 2:
            return {}
        
        values = data_clean['Valor']
        dates = data_clean['Fecha']
        
        # Métricas básicas
        current_value = values.iloc[-1]
        previous_value = values.iloc[-2] if len(values) > 1 else current_value
        change_absolute = current_value - previous_value
        change_percentage = (change_absolute / previous_value * 100) if previous_value != 0 else 0
        
        # Métricas estadísticas
        mean_val = values.mean()
        median_val = values.median()
        std_val = values.std()
        min_val = values.min()
        max_val = values.max()
        range_val = max_val - min_val
        
        # Volatilidad y coeficiente de variación
        volatility = (std_val / mean_val * 100) if mean_val != 0 else 0
        
        # Percentiles
        q25 = values.quantile(0.25)
        q75 = values.quantile(0.75)
        iqr = q75 - q25
        
        # Tendencia (regresión lineal simple)
        x_vals = np.arange(len(values))
        if len(x_vals) > 1:
            coeffs = np.polyfit(x_vals, values, 1)
            trend_slope = coeffs[0]
            trend_direction = "alcista" if trend_slope > 0 else "bajista" if trend_slope < 0 else "lateral"
        else:
            trend_slope = 0
            trend_direction = "lateral"
        
        # Análisis de extremos
        days_since_max = (dates.iloc[-1] - dates[values.idxmax()]).days if len(dates) > 0 else 0
        days_since_min = (dates.iloc[-1] - dates[values.idxmin()]).days if len(dates) > 0 else 0
        
        # Niveles de soporte y resistencia (aproximados)
        resistance_level = q75 + (iqr * 0.5)
        support_level = q25 - (iqr * 0.5)
        
        return {
            "valor_actual": current_value,
            "cambio_absoluto": change_absolute,
            "cambio_porcentual": change_percentage,
            "promedio": mean_val,
            "mediana": median_val,
            "desviacion_estandar": std_val,
            "volatilidad": volatility,
            "minimo": min_val,
            "maximo": max_val,
            "rango": range_val,
            "q25": q25,
            "q75": q75,
            "rango_intercuartil": iqr,
            "tendencia_direccion": trend_direction,
            "tendencia_pendiente": trend_slope,
            "dias_desde_maximo": days_since_max,
            "dias_desde_minimo": days_since_min,
            "resistencia": resistance_level,
            "soporte": support_level,
            "observaciones": len(data_clean),
            "periodo_dias": (dates.max() - dates.min()).days if len(dates) > 1 else 0
        }
        
    except Exception as e:
        st.error(f"Error calculando métricas específicas: {str(e)}")
        return {}

def generate_ai_technical_report(analyzer, variable_name: str) -> str:
    """
    Genera un informe de IA avanzado basado en el análisis técnico-estadístico.
    """
    try:
        # Verificar dependencias y configuración
        if 'GEMINI_API_KEY' not in st.session_state or not st.session_state.GEMINI_API_KEY:
            return "⚠️ API Key de Gemini no configurada para análisis avanzado."
        
        import google.generativeai as genai
        genai.configure(api_key=st.session_state.GEMINI_API_KEY)
        
        # Preparar resumen de métricas para la IA - Corregir error de formato
        autocorr_value = f"{analyzer.autocorr_lag1:.3f}" if analyzer.autocorr_lag1 is not None else 'N/A'
        stationary_value = str(analyzer.is_stationary) if analyzer.is_stationary is not None else 'N/A'
        
        metrics_summary = f"""
Variable: {variable_name}
Observaciones: {analyzer.size}
Retorno Anual: {analyzer.mean_annual*100:.2f}%
Volatilidad Anual: {analyzer.volatility_annual*100:.2f}%
Sharpe Ratio: {analyzer.sharpe_ratio:.3f}
VaR 95%: {analyzer.var_95*100:.3f}%
VaR 99%: {analyzer.var_99*100:.3f}%
Drawdown Máximo: {analyzer.drawdown_max*100:.2f}%
Skewness: {analyzer.skewness:.3f}
Kurtosis: {analyzer.kurtosis:.3f}
Es Normal (JB): {analyzer.is_normal}
P-valor JB: {analyzer.p_value:.6f}
Autocorr Lag1: {autocorr_value}
Es Estacionaria: {stationary_value}
        """
        
        # Prompt optimizado para variables económicas (no instrumentos de inversión)
        prompt = f"""Actúa como un analista económico senior del BCRA especializado en análisis de variables macroeconómicas.

Analiza los siguientes datos técnico-estadísticos de la variable económica: {variable_name}

DATOS TÉCNICOS:
{metrics_summary}

ESTRUCTURA DEL INFORME (máximo 500 palabras):

1. **DIAGNÓSTICO ECONÓMICO** (3 líneas)
- Evaluación del comportamiento de la variable económica
- Nivel de estabilidad/volatilidad observado

2. **ANÁLISIS ESTADÍSTICO** (4-5 puntos)
- Interpretación de las métricas de riesgo en contexto económico
- Evaluación de la normalidad estadística
- Análisis de patrones temporales

3. **IMPLICACIONES PARA POLÍTICA ECONÓMICA** (3-4 puntos)
- Qué indica este comportamiento sobre la economía argentina
- Relación con objetivos del BCRA
- Impacto en decisiones de política monetaria

4. **RECOMENDACIONES DE MONITOREO** (3-4 acciones específicas)
- Frecuencia de seguimiento recomendada
- Indicadores complementarios a vigilar
- Niveles de alerta económica

IMPORTANTE: Esta es una variable económica, NO un instrumento de inversión. Enfócate en análisis macroeconómico, no en señales de trading."""

        # Configuración optimizada del modelo
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=700,
                top_p=0.9,
                top_k=30
            )
        )
        
        response = model.generate_content(prompt)
        
        if response and response.text:
            # Formatear respuesta
            ai_report = f"""
# 🤖 Análisis Económico con IA: {variable_name}

*Informe generado por inteligencia artificial especializada • {datetime.now().strftime('%d/%m/%Y %H:%M')}*

---

{response.text}

---

## 📊 Métricas Técnicas de Referencia

| Métrica Clave | Valor | Interpretación Económica |
|---------------|-------|--------------------------|
| **Volatilidad Anual** | {analyzer.volatility_annual*100:.2f}% | {'🔴 Alta variabilidad' if analyzer.volatility_annual > 0.3 else '🟡 Variabilidad moderada' if analyzer.volatility_annual > 0.15 else '🟢 Comportamiento estable'} |
| **Distribución Normal** | {'✅ SÍ' if analyzer.is_normal else '❌ NO'} | {'🟢 Comportamiento predecible' if analyzer.is_normal else '🟡 Requiere modelos especializados'} |
| **VaR 95% (diario)** | {analyzer.var_95*100:.3f}% | {'🔴 Alta variabilidad diaria' if abs(analyzer.var_95) > 0.05 else '🟡 Variabilidad moderada' if abs(analyzer.var_95) > 0.02 else '🟢 Comportamiento estable'} |
| **Autocorrelación** | {autocorr_value} | {'🟡 Persistencia temporal' if analyzer.autocorr_lag1 and abs(analyzer.autocorr_lag1) > 0.2 else '🟢 Independencia temporal'} |

*Análisis técnico-estadístico aplicado a variables económicas del BCRA*
            """
            
            return ai_report
        else:
            return "❌ No se pudo generar el análisis avanzado. Intente nuevamente."
            
    except ImportError:
        return "⚠️ Dependencias de IA no disponibles. Instale google-generativeai para análisis avanzado."
    except Exception as e:
        return f"❌ Error en análisis avanzado: {str(e)}"

# Nuevas funciones para análisis intermarket
def verificar_conexion_internet():
    """Verifica si hay conexión a internet"""
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except:
        return False

@st.cache_data(ttl=300)
def descargar_datos_mercado_global(tickers, period='1y', max_reintentos=3):
    """Descarga datos del mercado global con manejo de errores mejorado"""
    datos = {}
    errores = []
    
    if not verificar_conexion_internet():
        st.error("❌ Sin conexión a internet para datos globales.")
        return {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        status_text.text(f'Descargando {ticker}... ({i+1}/{len(tickers)})')
        
        for intento in range(max_reintentos):
            try:
                time.sleep(0.2)  # Aumentar delay para evitar rate limiting
                data = yf.download(ticker, period=period, progress=False, timeout=15)
                
                if not data.empty and 'Adj Close' in data.columns:
                    datos[ticker] = data['Adj Close']
                    break
                elif not data.empty and 'Close' in data.columns:
                    datos[ticker] = data['Close']
                    break
                else:
                    if intento == max_reintentos - 1:
                        errores.append(f"{ticker}: Sin datos disponibles o ticker incorrecto")
                        
            except Exception as e:
                if intento == max_reintentos - 1:
                    errores.append(f"{ticker}: Error de conexión - {str(e)[:30]}...")
                time.sleep(1)  # Mayor espera entre intentos
        
        progress_bar.progress((i + 1) / len(tickers))
    
    progress_bar.empty()
    status_text.empty()
    
    if errores:
        st.warning("⚠️ Algunos mercados no pudieron descargarse. Esto puede deberse a:")
        st.write("• Problemas de conectividad")
        st.write("• Tickers no disponibles en Yahoo Finance")
        st.write("• Restricciones de API")
        
    return datos

def analizar_correlacion_bcra_global(datos_bcra, datos_globales):
    """Analiza correlaciones entre variables BCRA y mercados globales"""
    correlaciones = {}
    
    if not datos_bcra.empty and datos_globales:
        # Convertir datos BCRA a retornos
        retornos_bcra = datos_bcra['Valor'].pct_change().dropna()
        
        for nombre_global, precios_global in datos_globales.items():
            retornos_global = precios_global.pct_change().dropna()
            
            # Alinear fechas
            fechas_comunes = retornos_bcra.index.intersection(retornos_global.index)
            
            if len(fechas_comunes) > 20:  # Mínimo 20 observaciones
                ret_bcra_alineado = retornos_bcra.loc[fechas_comunes]
                ret_global_alineado = retornos_global.loc[fechas_comunes]
                
                corr = ret_bcra_alineado.corr(ret_global_alineado)
                
                correlaciones[nombre_global] = {
                    'correlacion': corr,
                    'observaciones': len(fechas_comunes),
                    'significancia': 'Alta' if abs(corr) > 0.5 else 'Media' if abs(corr) > 0.3 else 'Baja'
                }
    
    return correlaciones

def analizar_regimen_mercado_argentina(datos_globales):
    """Análisis específico de régimen para Argentina"""
    regimen_score = 0
    factores = []
    
    # Análisis DXY
    if 'DX-Y.NYB' in datos_globales:
        dxy_data = datos_globales['DX-Y.NYB']
        dxy_cambio = dxy_data.pct_change().tail(20).sum()
        
        if dxy_cambio < -0.03:
            regimen_score += 2
            factores.append("✅ USD débil - Favorable para Argentina")
        elif dxy_cambio > 0.03:
            regimen_score -= 2
            factores.append("🔴 USD fuerte - Desfavorable para Argentina")
        else:
            factores.append("🟡 USD neutral")
    
    # Análisis VIX
    if '^VIX' in datos_globales:
        vix_data = datos_globales['^VIX']
        vix_actual = vix_data.iloc[-1]
        
        if vix_actual < 18:
            regimen_score += 2
            factores.append(f"✅ VIX bajo ({vix_actual:.1f}) - Apetito por riesgo")
        elif vix_actual > 30:
            regimen_score -= 3
            factores.append(f"🔴 VIX alto ({vix_actual:.1f}) - Aversión al riesgo")
        else:
            factores.append(f"🟡 VIX moderado ({vix_actual:.1f})")
    
    # Análisis Commodities
    commodities_score = 0
    if 'ZS=F' in datos_globales:  # Soja
        soja_cambio = datos_globales['ZS=F'].pct_change().tail(20).sum()
        if soja_cambio > 0.05:
            commodities_score += 2
            factores.append(f"✅ Soja fuerte ({soja_cambio:.1%}) - Muy favorable")
        elif soja_cambio < -0.05:
            commodities_score -= 1
            factores.append(f"🔴 Soja débil ({soja_cambio:.1%})")
    
    regimen_score += commodities_score
    
    # Clasificación final
    if regimen_score >= 3:
        clasificacion = "🟢 FAVORABLE"
        descripcion = "Condiciones globales favorables para Argentina"
    elif regimen_score <= -3:
        clasificacion = "🔴 DESFAVORABLE"
        descripcion = "Condiciones globales adversas para Argentina"
    else:
        clasificacion = "🟡 NEUTRAL"
        descripcion = "Condiciones globales mixtas"
    
    return {
        'score': regimen_score,
        'clasificacion': clasificacion,
        'descripcion': descripcion,
        'factores': factores
    }

def generar_señales_trading_argentina(datos_bcra, datos_globales):
    """Genera señales específicas para trading en Argentina"""
    señales = []
    
    # Señal DXY-Commodities-Argentina
    if 'DX-Y.NYB' in datos_globales and 'ZS=F' in datos_globales:
        dxy_trend = datos_globales['DX-Y.NYB'].pct_change().tail(10).mean()
        soja_trend = datos_globales['ZS=F'].pct_change().tail(10).mean()
        
        if dxy_trend < -0.005 and soja_trend > 0.01:
            señales.append({
                'activo': 'Merval/Argentina',
                'señal': 'COMPRA',
                'fuerza': 'FUERTE',
                'motivo': 'USD débil + Soja fuerte → Favorable para Argentina',
                'horizonte': '4-8 semanas'
            })
    
    # Señal VIX-Risk Appetite
    if '^VIX' in datos_globales:
        vix_actual = datos_globales['^VIX'].iloc[-1]
        vix_cambio = datos_globales['^VIX'].pct_change().tail(5).sum()
        
        if vix_actual < 18 and vix_cambio < -0.1:
            señales.append({
                'activo': 'Emergentes/Argentina',
                'señal': 'COMPRA',
                'fuerza': 'MEDIA',
                'motivo': 'VIX bajando → Mayor apetito por riesgo',
                'horizonte': '2-4 semanas'
            })
        elif vix_actual > 28 and vix_cambio > 0.15:
            señales.append({
                'activo': 'Argentina',
                'señal': 'VENTA/COBERTURA',
                'fuerza': 'FUERTE',
                'motivo': 'VIX disparándose → Flight to quality',
                'horizonte': 'Inmediato'
            })
    
    return señales

def crear_dashboard_intermarket():
    """Crea el dashboard de análisis intermarket"""
    st.header("🌍 Análisis Intermarket Argentina")
    st.markdown("**Análisis de correlaciones entre variables BCRA y mercados globales**")
    
    # Configuración de mercados globales
    mercados_globales = {
        'DXY (Dólar)': 'DX-Y.NYB',
        'VIX (Volatilidad)': '^VIX',
        'S&P 500': '^GSPC',
        'Nasdaq': '^IXIC',
        'Soja': 'ZS=F',
        'Petróleo': 'CL=F',
        'Oro': 'GC=F',
        'Bonos 10Y USA': '^TNX',
        'Merval': '^MERV',
        'Real Brasileño': 'USDBRL=X'
    }
    
    # Configuración del período
    col1, col2 = st.columns(2)
    with col1:
        period_global = st.selectbox(
            "Período análisis global:",
            ['1mo', '3mo', '6mo', '1y', '2y'],
            index=2
        )
    
    with col2:
        mercados_seleccionados = st.multiselect(
            "Mercados a analizar:",
            list(mercados_globales.keys()),
            default=['DXY (Dólar)', 'VIX (Volatilidad)', 'Soja', 'S&P 500']
        )
    
    if st.button("🔄 Actualizar Análisis Intermarket"):
        if mercados_seleccionados:
            # Descargar datos globales
            tickers_seleccionados = [mercados_globales[m] for m in mercados_seleccionados]
            
            with st.spinner("Descargando datos de mercados globales..."):
                datos_globales = descargar_datos_mercado_global(tickers_seleccionados, period_global)
            
            if datos_globales:
                # Análisis de régimen
                st.subheader("🎯 Régimen de Mercado para Argentina")
                regimen = analizar_regimen_mercado_argentina(datos_globales)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Score Régimen", f"{regimen['score']}/10")
                with col2:
                    st.markdown(f"**{regimen['clasificacion']}**")
                with col3:
                    st.write(regimen['descripcion'])
                
                # Factores del régimen
                st.markdown("**Factores clave:**")
                for factor in regimen['factores']:
                    st.write(f"• {factor}")
                
                # Señales de trading
                st.subheader("📈 Señales de Trading")
                señales = generar_señales_trading_argentina({}, datos_globales)
                
                if señales:
                    for señal in señales:
                        color = {"COMPRA": "🟢", "VENTA/COBERTURA": "🔴", "VENTA": "🔴"}
                        emoji = color.get(señal['señal'], "🟡")
                        
                        st.markdown(f"""
                        **{emoji} {señal['activo']} - {señal['señal']}**
                        - **Fuerza:** {señal['fuerza']}
                        - **Motivo:** {señal['motivo']}
                        - **Horizonte:** {señal['horizonte']}
                        """)
                        st.markdown("---")
                else:
                    st.info("No hay señales claras en este momento.")
                
                # Gráficos de mercados globales
                st.subheader("📊 Evolución Mercados Globales")
                
                if len(datos_globales) > 1:
                    fig = go.Figure()
                    
                    for i, (ticker, precios) in enumerate(datos_globales.items()):
                        # Normalizar precios a base 100
                        precios_norm = (precios / precios.iloc[0]) * 100
                        
                        # Encontrar nombre legible
                        nombre_legible = next((k for k, v in mercados_globales.items() if v == ticker), ticker)
                        
                        fig.add_trace(go.Scatter(
                            x=precios_norm.index,
                            y=precios_norm,
                            mode='lines',
                            name=nombre_legible,
                            line=dict(width=2)
                        ))
                    
                    fig.update_layout(
                        title="Evolución Comparativa (Base 100)",
                        xaxis_title="Fecha",
                        yaxis_title="Precio Normalizado",
                        hovermode='x unified',
                        height=500,
                        showlegend=True
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Matriz de correlaciones si hay datos del BCRA
                if 'bcra_data' in st.session_state and not st.session_state.bcra_data.empty:
                    st.subheader("🔗 Correlaciones BCRA vs Mercados Globales")
                    correlaciones = analizar_correlacion_bcra_global(
                        st.session_state.bcra_data, 
                        datos_globales
                    )
                    
                    if correlaciones:
                        corr_df = pd.DataFrame([
                            {
                                'Mercado': mercado,
                                'Correlación': f"{data['correlacion']:.3f}",
                                'Significancia': data['significancia'],
                                'Observaciones': data['observaciones']
                            }
                                                       for mercado, data in correlaciones.items()
                        ])
                        
                        st.dataframe(corr_df, use_container_width=True)
                    else:
                        st.info("Necesitas cargar una variable del BCRA para ver correlaciones.")
            else:
                st.error("No se pudieron descargar datos de mercados globales.")
        else:
            st.warning("Selecciona al menos un mercado global para analizar.")

def crear_analisis_intermarket_integrado():
    """Crea análisis intermarket integrado en la sección principal"""
    
    with st.expander("🌍 Análisis Intermarket - Contexto Global", expanded=False):
        st.markdown("**Análisis del contexto global para interpretar las variables del BCRA**")
        
        # Verificar si hay datos del BCRA cargados
        if 'bcra_data' not in st.session_state or st.session_state.bcra_data.empty:
            st.info("💡 Carga primero una variable del BCRA para ver su contexto global")
            return
        
        # Configuración simplificada
        col1, col2 = st.columns(2)
        
        with col1:
            period_global = st.selectbox(
                "Período de contexto:",
                ['3mo', '6mo', '1y'],
                index=1,
                key="period_intermarket"
            )
        
        with col2:
            analizar_contexto = st.button("🔄 Analizar Contexto Global", type="primary")
        
        # Mercados clave para contexto argentino con tickers alternativos
        mercados_contexto = {
            'USD Index': 'UUP',  # ETF del dólar como alternativa a DXY
            'S&P 500': 'SPY',    # ETF del S&P 500
            'Emergentes': 'EEM', # ETF de mercados emergentes
            'Commodities': 'DBC', # ETF de commodities
            'Oro': 'GLD',        # ETF de oro
            'Bonos USA': 'TLT'   # ETF de bonos largos USA
        }
        
        if analizar_contexto:
            tickers_contexto = list(mercados_contexto.values())
            
            with st.spinner("📊 Analizando contexto global..."):
                datos_contexto = descargar_datos_mercado_global(tickers_contexto, period_global)
            
            if datos_contexto:
                st.success(f"✅ Contexto global analizado - {len(datos_contexto)} mercados descargados")
                
                # Análisis de contexto macro
                st.subheader("📈 Contexto Macroeconómico Global")
                
                col1, col2, col3 = st.columns(3)
                
                # Crear métricas de contexto
                contexto_metrics = {}
                for nombre, ticker in mercados_contexto.items():
                    if ticker in datos_contexto:
                        precios = datos_contexto[ticker]
                        cambio_periodo = ((precios.iloc[-1] - precios.iloc[0]) / precios.iloc[0]) * 100
                        contexto_metrics[nombre] = cambio_periodo
                
                # Mostrar métricas principales
                if 'USD Index' in contexto_metrics:
                    with col1:
                        usd_change = contexto_metrics['USD Index']
                        st.metric(
                            "Fortaleza USD", 
                            f"{usd_change:+.1f}%",
                            delta=f"{'Fuerte' if usd_change > 2 else 'Débil' if usd_change < -2 else 'Neutral'}"
                        )
                
                if 'Emergentes' in contexto_metrics:
                    with col2:
                        em_change = contexto_metrics['Emergentes']
                        st.metric(
                            "Mercados Emergentes", 
                            f"{em_change:+.1f}%",
                            delta=f"{'Positivo' if em_change > 0 else 'Negativo'}"
                        )
                
                if 'Commodities' in contexto_metrics:
                    with col3:
                        comm_change = contexto_metrics['Commodities']
                        st.metric(
                            "Commodities", 
                            f"{comm_change:+.1f}%",
                            delta=f"{'Favorable ARG' if comm_change > 0 else 'Desfavorable ARG'}"
                        )
                
                # Interpretación del contexto
                st.subheader("💡 Interpretación del Contexto")
                
                score_argentina = 0
                factores = []
                
                if 'USD Index' in contexto_metrics:
                    usd_change = contexto_metrics['USD Index']
                    if usd_change < -2:
                        score_argentina += 2
                        factores.append("✅ Dólar débil favorece a emergentes")
                    elif usd_change > 3:
                        score_argentina -= 2
                        factores.append("🔴 Dólar fuerte presiona emergentes")
                    else:
                        factores.append("🟡 Dólar en rango neutral")
                
                if 'Emergentes' in contexto_metrics:
                    em_change = contexto_metrics['Emergentes']
                    if em_change > 5:
                        score_argentina += 1
                        factores.append("✅ Buen momento para emergentes")
                    elif em_change < -5:
                        score_argentina -= 1
                        factores.append("🔴 Presión en mercados emergentes")
                
                if 'Commodities' in contexto_metrics:
                    comm_change = contexto_metrics['Commodities']
                    if comm_change > 5:
                        score_argentina += 2
                        factores.append("✅ Commodities fuertes benefician a Argentina")
                    elif comm_change < -5:
                        score_argentina -= 1
                        factores.append("🔴 Commodities débiles afectan exportaciones")
                
                # Clasificación final
                if score_argentina >= 3:
                    contexto_final = "🟢 **FAVORABLE** para Argentina"
                elif score_argentina <= -2:
                    contexto_final = "🔴 **DESFAVORABLE** para Argentina"
                else:
                    contexto_final = "🟡 **MIXTO** para Argentina"
                
                st.markdown(f"### {contexto_final}")
                
                for factor in factores:
                    st.write(f"• {factor}")
                
                # Correlaciones con variable BCRA si es posible
                if len(datos_contexto) > 0:
                    st.subheader("🔗 Análisis de Correlaciones")
                    
                    correlaciones = analizar_correlacion_bcra_global(
                        st.session_state.bcra_data, 
                        datos_contexto
                    )
                    
                    if correlaciones:
                        st.write("**Correlaciones significativas encontradas:**")
                        
                        for mercado, data in correlaciones.items():
                            if abs(data['correlacion']) > 0.3:
                                nombre = next((k for k, v in mercados_contexto.items() if v == mercado), mercado)
                                corr = data['correlacion']
                                
                                direccion = "positiva" if corr > 0 else "negativa"
                                fuerza = "fuerte" if abs(corr) > 0.5 else "moderada"
                                
                                st.write(f"• **{nombre}**: Correlación {direccion} {fuerza} ({corr:.3f})")
                    else:
                        st.info("No se encontraron correlaciones significativas con los datos disponibles")
            else:
                st.error("❌ No se pudieron obtener datos de contexto global")
                st.write("**Posibles soluciones:**")
                st.write("• Verificar conexión a internet")
                st.write("• Intentar más tarde (puede haber restricciones de API)")
                st.write("• El análisis local sigue funcionando normalmente")

# Función principal simplificada
def analyze_economic_cycle(bcra_data):
    """Analiza el ciclo económico basado en variables del BCRA para contexto argentino"""
    cycle_indicators = {}
    
    # Variables clave específicas para Argentina
    variables_clave = {
        'Tasa de política monetaria': ['LELIQ', 'TASA', 'POLITICA', 'MONETARIA'],
        'Base monetaria': ['BASE', 'MONETARIA', 'EMISION'],
        'Inflación': ['IPC', 'INFLACION', 'PRECIOS'],
        'Reservas': ['RESERVAS', 'INTERNACIONALES', 'DIVISAS'],
        'Tipo de cambio': ['TIPO', 'CAMBIO', 'OFICIAL', 'DOLAR'],
        'Actividad': ['EMAE', 'PBI', 'ACTIVIDAD', 'ECONOMICA'],
        'Riesgo país': ['RIESGO', 'PAIS', 'EMBI'],
        'Deuda pública': ['DEUDA', 'PUBLICA', 'BONOS'],
        'Masa monetaria': ['M1', 'M2', 'M3', 'MASA'],
        'Tasa de interés': ['INTERES', 'TASA', 'PASIVA'],
        'Brecha cambiaria': ['BRECHA', 'CAMBIO', 'PARALELO']
    }
    
    for categoria, keywords in variables_clave.items():
        for keyword in keywords:
            matches = bcra_data[bcra_data['Nombre'].str.contains(keyword, case=False, na=False)]
            if not matches.empty:
                cycle_indicators[categoria] = matches.iloc[0]
                break
    
    return cycle_indicators

def determine_economic_cycle(indicators):
    """Determina la fase del ciclo económico adaptado al contexto argentino"""
    cycle_score = 0
    cycle_analysis = {}
    argentina_metrics = {}
    
    # Análisis de tasa de política monetaria (LELIQ)
    if 'Tasa de política monetaria' in indicators:
        try:
            tasa_valor = float(indicators['Tasa de política monetaria']['Valor'].replace(',', '.'))
            if tasa_valor > 100:  # Tasa alta = contracción
                cycle_score -= 2
                cycle_analysis['Tasa'] = 'Alta - Contractiva'
                argentina_metrics['LELIQ'] = f"{tasa_valor:.1f}%"
            elif tasa_valor < 50:  # Tasa baja = expansión
                cycle_score += 2
                cycle_analysis['Tasa'] = 'Baja - Expansiva'
                argentina_metrics['LELIQ'] = f"{tasa_valor:.1f}%"
            else:
                cycle_analysis['Tasa'] = 'Moderada'
                argentina_metrics['LELIQ'] = f"{tasa_valor:.1f}%"
        except:
            cycle_analysis['Tasa'] = 'No disponible'
    
    # Análisis de inflación (contexto argentino)
    if 'Inflación' in indicators:
        try:
            inflacion_valor = float(indicators['Inflación']['Valor'].replace(',', '.'))
            if inflacion_valor > 50:  # Inflación alta = estrés
                cycle_score -= 1
                cycle_analysis['Inflación'] = 'Alta - Estrés'
                argentina_metrics['IPC'] = f"{inflacion_valor:.1f}%"
            elif inflacion_valor > 25:  # Inflación moderada
                cycle_analysis['Inflación'] = 'Moderada'
                argentina_metrics['IPC'] = f"{inflacion_valor:.1f}%"
            else:
                cycle_analysis['Inflación'] = 'Controlada'
                argentina_metrics['IPC'] = f"{inflacion_valor:.1f}%"
        except:
            cycle_analysis['Inflación'] = 'No disponible'
    
    # Análisis de reservas internacionales
    if 'Reservas' in indicators:
        try:
            reservas_valor = float(indicators['Reservas']['Valor'].replace(',', '.'))
            if reservas_valor > 20000:  # Reservas altas = fortaleza
                cycle_score += 1
                cycle_analysis['Reservas'] = 'Altas - Fortaleza'
                argentina_metrics['Reservas'] = f"${reservas_valor:,.0f}M"
            else:
                cycle_analysis['Reservas'] = 'Bajas - Vulnerabilidad'
                argentina_metrics['Reservas'] = f"${reservas_valor:,.0f}M"
        except:
            cycle_analysis['Reservas'] = 'No disponible'
    
    # Análisis de tipo de cambio
    if 'Tipo de cambio' in indicators:
        try:
            tc_valor = float(indicators['Tipo de cambio']['Valor'].replace(',', '.'))
            if tc_valor > 800:  # Dólar alto = presión
                cycle_score -= 1
                cycle_analysis['Tipo de cambio'] = 'Alto - Presión'
                argentina_metrics['Dólar Oficial'] = f"${tc_valor:.2f}"
            else:
                cycle_analysis['Tipo de cambio'] = 'Estable'
                argentina_metrics['Dólar Oficial'] = f"${tc_valor:.2f}"
        except:
            cycle_analysis['Tipo de cambio'] = 'No disponible'
    
    # Análisis de actividad económica (EMAE)
    if 'Actividad' in indicators:
        try:
            actividad_valor = float(indicators['Actividad']['Valor'].replace(',', '.'))
            if actividad_valor > 0:  # Crecimiento positivo
                cycle_score += 1
                cycle_analysis['Actividad'] = 'En crecimiento'
                argentina_metrics['EMAE'] = f"{actividad_valor:.1f}%"
            else:
                cycle_analysis['Actividad'] = 'En contracción'
                argentina_metrics['EMAE'] = f"{actividad_valor:.1f}%"
        except:
            cycle_analysis['Actividad'] = 'No disponible'
    
    # Análisis de masa monetaria
    if 'Masa monetaria' in indicators:
        try:
            masa_valor = float(indicators['Masa monetaria']['Valor'].replace(',', '.'))
            if masa_valor > 1000000:  # Masa monetaria alta
                cycle_score -= 1
                cycle_analysis['Masa monetaria'] = 'Alta - Presión inflacionaria'
                argentina_metrics['M2'] = f"${masa_valor:,.0f}M"
            else:
                cycle_analysis['Masa monetaria'] = 'Controlada'
                argentina_metrics['M2'] = f"${masa_valor:,.0f}M"
        except:
            cycle_analysis['Masa monetaria'] = 'No disponible'
    
    # Determinar fase del ciclo adaptado a Argentina
    if cycle_score >= 3:
        cycle_phase = "Expansión"
        cycle_class = "expansion"
        argentina_metrics['Diagnóstico'] = "Contexto favorable para activos de riesgo"
    elif cycle_score >= 1:
        cycle_phase = "Auge"
        cycle_class = "peak"
        argentina_metrics['Diagnóstico'] = "Protección ante sobrevaloración"
    elif cycle_score >= -1:
        cycle_phase = "Contracción"
        cycle_class = "contraction"
        argentina_metrics['Diagnóstico'] = "Fuga al refugio recomendada"
    else:
        cycle_phase = "Recesión"
        cycle_class = "recession"
        argentina_metrics['Diagnóstico'] = "Máxima defensa requerida"
    
    return cycle_phase, cycle_class, cycle_analysis, argentina_metrics

def get_portfolio_recommendations(cycle_phase):
    """Genera recomendaciones de portafolio adaptadas al contexto argentino"""
    recommendations = {
        "Expansión": {
            "activos_recomendados": [
                "Acciones locales (GGAL, YPF, PAMP)",
                "CEDEARs (SPY, QQQ, AAPL)",
                "Bonos CER (ajustables por inflación)",
                "Bonos ajustables por UVA",
                "FCI de renta variable local"
            ],
            "ponderacion": {"Acciones": 0.45, "Bonos": 0.35, "Dólar": 0.1, "Commodities": 0.1},
            "comentario": "Contexto favorable: LELIQ baja, inflación controlada, crecimiento económico",
            "riesgo": "Moderado",
            "estrategia": "Crecimiento agresivo con protección inflacionaria"
        },
        "Auge": {
            "activos_recomendados": [
                "Acciones value (defensivas)",
                "Activos hard (inmuebles, oro físico)",
                "Bonos de corto plazo (Letras del Tesoro)",
                "Dólar MEP y CCL",
                "FCI de renta fija en dólares"
            ],
            "ponderacion": {"Acciones": 0.25, "Bonos": 0.35, "Dólar": 0.25, "Commodities": 0.15},
            "comentario": "Protección ante sobrevaloración y presión inflacionaria",
            "riesgo": "Moderado-Alto",
            "estrategia": "Diversificación defensiva con cobertura cambiaria"
        },
        "Contracción": {
            "activos_recomendados": [
                "Bonos de tasa fija (soberanos)",
                "Dólar MEP y CCL",
                "Dólar-linked (bonos duales)",
                "Letras del Tesoro (corto plazo)",
                "FCI de renta fija en pesos"
            ],
            "ponderacion": {"Acciones": 0.1, "Bonos": 0.6, "Dólar": 0.25, "Commodities": 0.05},
            "comentario": "Fuga al refugio: LELIQ alta, inflación elevada, evitar acciones cíclicas",
            "riesgo": "Bajo",
            "estrategia": "Preservación de capital con liquidez"
        },
        "Recesión": {
            "activos_recomendados": [
                "CEDEARs defensivos (tech, consumo estable)",
                "Oro físico y ETFs de oro",
                "Bonos soberanos en dólares",
                "Dólar MEP y CCL",
                "FCI de renta fija en dólares"
            ],
            "ponderacion": {"Acciones": 0.15, "Bonos": 0.5, "Dólar": 0.25, "Commodities": 0.1},
            "comentario": "Máxima defensa: recesión económica, alta volatilidad",
            "riesgo": "Bajo",
            "estrategia": "Refugio total con activos hard"
        }
    }
    
    return recommendations.get(cycle_phase, recommendations["Contracción"])

@st.cache_data(ttl=3600)
def get_yfinance_data(symbols, period="1y"):
    """Obtiene datos de yfinance para análisis intermarket"""
    data = {}
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            if not hist.empty:
                data[symbol] = hist
        except Exception as e:
            st.warning(f"Error obteniendo datos para {symbol}: {str(e)}")
    return data

def detect_sector_with_gemini(symbol, api_key_input):
    """Detecta el sector de un activo usando Gemini AI"""
    if not api_key_input:
        return "No disponible"
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key_input)
        
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Analiza el símbolo bursátil '{symbol}' y determina su sector económico.
        
        Para símbolos argentinos (.BA):
        - GGAL: Banco Galicia (Sector Financiero)
        - YPF: Yacimientos Petrolíferos Fiscales (Sector Energético/Petróleo)
        - PAMP: Pampa Energía (Sector Energético)
        - ALUA: Aluar (Sector Industrial/Materiales)
        - TECO2: Telecom (Sector Telecomunicaciones)
        - CRES: Cresud (Sector Agropecuario/Inmobiliario)
        - BMA: Banco Macro (Sector Financiero)
        - TGS: Transportadora de Gas del Sur (Sector Energético/Utilities)
        
        Para CEDEARs y ETFs:
        - SPY: S&P 500 ETF (Sector Diversificado)
        - QQQ: NASDAQ ETF (Sector Tecnología)
        - AAPL: Apple (Sector Tecnología)
        - MSFT: Microsoft (Sector Tecnología)
        - GOOGL: Alphabet (Sector Tecnología)
        - TSLA: Tesla (Sector Automotriz/Tecnología)
        - NVDA: NVIDIA (Sector Tecnología)
        - AMZN: Amazon (Sector Consumo/Comercio Electrónico)
        
        Para activos defensivos:
        - GLD: Gold ETF (Sector Commodities/Metales Preciosos)
        - SLV: Silver ETF (Sector Commodities/Metales Preciosos)
        - TLT: Treasury Bonds ETF (Sector Renta Fija)
        - IEF: Intermediate Treasury ETF (Sector Renta Fija)
        - VNQ: Real Estate ETF (Sector Inmobiliario)
        
        Para commodities:
        - GC=F: Gold Futures (Sector Commodities/Metales Preciosos)
        - SI=F: Silver Futures (Sector Commodities/Metales Preciosos)
        - CL=F: Crude Oil Futures (Sector Energético/Petróleo)
        - ZC=F: Corn Futures (Sector Agropecuario)
        - ZS=F: Soybean Futures (Sector Agropecuario)
        - CC=F: Cocoa Futures (Sector Agropecuario)
        
        Responde únicamente con el sector principal del activo.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        return "No disponible"

def analyze_intermarket_data(yf_data, api_key_input=None):
    """Realiza análisis intermarket con datos de yfinance incluyendo sectores"""
    analysis = {}
    
    # Análisis de correlaciones
    if len(yf_data) >= 2:
        # Crear DataFrame con precios de cierre
        close_prices = pd.DataFrame()
        for symbol, data in yf_data.items():
            close_prices[symbol] = data['Close']
        
        # Calcular correlaciones
        correlations = close_prices.corr()
        analysis['correlations'] = correlations
        
        # Calcular momentum (retornos de 20 días)
        returns = close_prices.pct_change(20).dropna()
        analysis['momentum'] = returns
        
        # Detectar sectores usando Gemini
        if api_key_input:
            analysis['sectors'] = {}
            for symbol in yf_data.keys():
                sector = detect_sector_with_gemini(symbol, api_key_input)
                analysis['sectors'][symbol] = sector
    
    return analysis

def create_intermarket_charts(yf_data, analysis):
    """Crea gráficos de análisis intermarket"""
    if not yf_data:
        return None
    
    # Gráfico de precios normalizados
    fig_prices = go.Figure()
    
    for symbol, data in yf_data.items():
        normalized_prices = data['Close'] / data['Close'].iloc[0] * 100
        fig_prices.add_trace(go.Scatter(
            x=data.index,
            y=normalized_prices,
            name=symbol,
            mode='lines'
        ))
    
    fig_prices.update_layout(
        title="Evolución de Precios (Normalizado a 100)",
        xaxis_title="Fecha",
        yaxis_title="Precio Normalizado",
        hovermode="x unified"
    )
    
    # Gráfico de correlaciones
    if 'correlations' in analysis:
        fig_corr = px.imshow(
            analysis['correlations'],
            title="Matriz de Correlaciones",
            color_continuous_scale='RdBu',
            aspect="auto"
        )
        
        return fig_prices, fig_corr
    
    return fig_prices, None

def calcular_alpha_beta_capm(portfolio_returns, benchmark_returns, risk_free_rate=0.0):
    """
    Calcula el Alpha y Beta de un portafolio respecto a un benchmark usando CAPM.
    
    Args:
        portfolio_returns (pd.Series): Retornos del portafolio
        benchmark_returns (pd.Series): Retornos del benchmark (MERVAL)
        risk_free_rate (float): Tasa libre de riesgo (anualizada)
    
    Returns:
        dict: Diccionario con métricas CAPM completas
    """
    try:
        # Alinear datos
        aligned_data = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
        if len(aligned_data) < 30:  # Mínimo 30 observaciones
            return {
                'alpha': 0,
                'beta': 1.0,
                'alpha_annual': 0,
                'r_squared': 0,
                'tracking_error': 0,
                'information_ratio': 0,
                'sharpe_ratio': 0,
                'treynor_ratio': 0,
                'jensen_alpha': 0,
                'observations': len(aligned_data),
                'p_value': 1.0,
                'std_error': 0,
                'confidence_interval': (0, 0)
            }
        
        portfolio_ret = aligned_data.iloc[:, 0]
        benchmark_ret = aligned_data.iloc[:, 1]
        
        # Calcular retorno excedente (exceso sobre tasa libre de riesgo)
        excess_portfolio = portfolio_ret - risk_free_rate/252  # Diario
        excess_benchmark = benchmark_ret - risk_free_rate/252
        
        # Regresión CAPM: R_p - R_f = α + β(R_m - R_f) + ε
        model = stats.linregress(excess_benchmark, excess_portfolio)
        
        # Métricas CAPM
        alpha = model.intercept
        beta = model.slope
        r_squared = model.rvalue ** 2
        p_value = model.pvalue
        std_error = model.stderr
        
        # Anualizar métricas
        alpha_annual = alpha * 252
        beta_annual = beta
        
        # Tracking Error
        predicted_returns = alpha + beta * excess_benchmark
        tracking_error = np.std(excess_portfolio - predicted_returns) * np.sqrt(252)
        
        # Information Ratio
        information_ratio = alpha_annual / tracking_error if tracking_error > 0 else 0
        
        # Sharpe Ratio
        portfolio_volatility = portfolio_ret.std() * np.sqrt(252)
        sharpe_ratio = (portfolio_ret.mean() * 252 - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        
        # Treynor Ratio
        treynor_ratio = (portfolio_ret.mean() * 252 - risk_free_rate) / beta if beta != 0 else 0
        
        # Jensen's Alpha (mismo que alpha anual)
        jensen_alpha = alpha_annual
        
        # Intervalo de confianza para beta
        confidence_interval = (beta - 1.96 * std_error, beta + 1.96 * std_error)
        
        return {
            'alpha': alpha,
            'beta': beta,
            'alpha_annual': alpha_annual,
            'r_squared': r_squared,
            'tracking_error': tracking_error,
            'information_ratio': information_ratio,
            'sharpe_ratio': sharpe_ratio,
            'treynor_ratio': treynor_ratio,
            'jensen_alpha': jensen_alpha,
            'observations': len(aligned_data),
            'p_value': p_value,
            'std_error': std_error,
            'confidence_interval': confidence_interval
        }
    except Exception as e:
        st.error(f"Error en cálculo CAPM: {str(e)}")
        return {
            'alpha': 0,
            'beta': 1.0,
            'alpha_annual': 0,
            'r_squared': 0,
            'tracking_error': 0,
            'information_ratio': 0,
            'sharpe_ratio': 0,
            'treynor_ratio': 0,
            'jensen_alpha': 0,
            'observations': 0,
            'p_value': 1.0,
            'std_error': 0,
            'confidence_interval': (0, 0)
        }

def analizar_estrategia_capm_argentina(alpha_beta_metrics, cycle_phase):
    """
    Analiza la estrategia de inversión basada en métricas CAPM para contexto argentino.
    """
    beta = alpha_beta_metrics.get('beta', 1.0)
    alpha_annual = alpha_beta_metrics.get('alpha_annual', 0)
    r_squared = alpha_beta_metrics.get('r_squared', 0)
    information_ratio = alpha_beta_metrics.get('information_ratio', 0)
    sharpe_ratio = alpha_beta_metrics.get('sharpe_ratio', 0)
    
    # Análisis de riesgo sistemático (Beta)
    if beta > 1.5:
        riesgo_sistematico = "MUY ALTO - Portafolio muy volátil respecto al MERVAL"
        recomendacion_beta = "Considerar reducción de exposición a acciones o uso de derivados para cobertura"
    elif beta > 1.2:
        riesgo_sistematico = "ALTO - Portafolio más volátil que el mercado"
        recomendacion_beta = "Evaluar diversificación hacia activos defensivos"
    elif beta > 0.8:
        riesgo_sistematico = "MODERADO - Portafolio con volatilidad similar al mercado"
        recomendacion_beta = "Mantener estrategia actual"
    elif beta > 0.3:
        riesgo_sistematico = "BAJO - Portafolio menos volátil que el mercado"
        recomendacion_beta = "Favorable para contexto defensivo"
    elif beta > -0.3:
        riesgo_sistematico = "MUY BAJO - Portafolio defensivo"
        recomendacion_beta = "Excelente para contextos de alta volatilidad"
    else:
        riesgo_sistematico = "NEGATIVO - Portafolio se mueve en dirección opuesta al mercado"
        recomendacion_beta = "Considerar si la correlación negativa es deseada"
    
    # Análisis de rendimiento ajustado por riesgo (Alpha)
    if alpha_annual > 0.10:  # 10% de alpha anual
        rendimiento_ajustado = "EXCELENTE - Genera valor significativo"
        recomendacion_alpha = "Mantener estrategia, posiblemente aumentar exposición"
    elif alpha_annual > 0.05:  # 5% de alpha anual
        rendimiento_ajustado = "BUENO - Genera valor por encima del mercado"
        recomendacion_alpha = "Estrategia sólida, monitorear continuamente"
    elif alpha_annual > 0.02:  # 2% de alpha anual
        rendimiento_ajustado = "POSITIVO - Ligeramente mejor que el mercado"
        recomendacion_alpha = "Aceptable, buscar oportunidades de mejora"
    elif alpha_annual > -0.02:  # Entre -2% y 2%
        rendimiento_ajustado = "NEUTRO - Rendimiento similar al mercado"
        recomendacion_alpha = "Considerar optimización o cambio de estrategia"
    elif alpha_annual > -0.05:  # Entre -5% y -2%
        rendimiento_ajustado = "DEFICIENTE - Por debajo del mercado"
        recomendacion_alpha = "Revisar estrategia, posible cambio de enfoque"
    else:
        rendimiento_ajustado = "MUY DEFICIENTE - Significativamente por debajo del mercado"
        recomendacion_alpha = "Revisión completa de estrategia requerida"
    
    # Análisis de calidad de la gestión (Information Ratio)
    if information_ratio > 0.5:
        calidad_gestion = "EXCELENTE - Gestión activa muy efectiva"
        recomendacion_ir = "Mantener equipo de gestión actual"
    elif information_ratio > 0.3:
        calidad_gestion = "BUENA - Gestión activa efectiva"
        recomendacion_ir = "Gestión sólida, monitorear continuamente"
    elif information_ratio > 0.1:
        calidad_gestion = "ACEPTABLE - Gestión activa moderadamente efectiva"
        recomendacion_ir = "Buscar mejoras en proceso de inversión"
    elif information_ratio > -0.1:
        calidad_gestion = "NEUTRA - Gestión pasiva podría ser más eficiente"
        recomendacion_ir = "Considerar estrategia pasiva o cambio de gestión"
    else:
        calidad_gestion = "DEFICIENTE - Gestión activa destruye valor"
        recomendacion_ir = "Cambio de estrategia o gestión requerido"
    
    # Análisis de Sharpe Ratio
    if sharpe_ratio > 1.0:
        ratio_sharpe = "EXCELENTE - Excelente retorno ajustado por riesgo"
        recomendacion_sharpe = "Estrategia muy atractiva"
    elif sharpe_ratio > 0.5:
        ratio_sharpe = "BUENO - Buen retorno ajustado por riesgo"
        recomendacion_sharpe = "Estrategia atractiva"
    elif sharpe_ratio > 0.0:
        ratio_sharpe = "POSITIVO - Retorno positivo ajustado por riesgo"
        recomendacion_sharpe = "Estrategia aceptable"
    else:
        ratio_sharpe = "DEFICIENTE - Retorno negativo ajustado por riesgo"
        recomendacion_sharpe = "Revisar estrategia de riesgo"
    
    # Recomendaciones específicas por ciclo económico
    recomendaciones_ciclo = {
        "Expansión": {
            "beta_ideal": "0.8-1.2",
            "estrategia": "Exposición moderada al mercado, aprovechar crecimiento",
            "activos": "Acciones cíclicas, CEDEARs, bonos corporativos"
        },
        "Auge": {
            "beta_ideal": "0.5-0.8",
            "estrategia": "Reducir exposición, preparar para corrección",
            "activos": "Activos defensivos, dólar, bonos soberanos"
        },
        "Contracción": {
            "beta_ideal": "0.3-0.6",
            "estrategia": "Máxima defensa, preservar capital",
            "activos": "Dólar MEP/CCL, bonos CER, letras del tesoro"
        },
        "Recesión": {
            "beta_ideal": "0.0-0.4",
            "estrategia": "Refugio total, activos hard",
            "activos": "Dólar físico, oro, inmuebles, bonos soberanos"
        }
    }
    
    ciclo_recomendacion = recomendaciones_ciclo.get(cycle_phase, {
        "beta_ideal": "0.5-1.0",
        "estrategia": "Diversificación balanceada",
        "activos": "Portafolio mixto"
    })
    
    return {
        'riesgo_sistematico': riesgo_sistematico,
        'recomendacion_beta': recomendacion_beta,
        'rendimiento_ajustado': rendimiento_ajustado,
        'recomendacion_alpha': recomendacion_alpha,
        'calidad_gestion': calidad_gestion,
        'recomendacion_ir': recomendacion_ir,
        'ratio_sharpe': ratio_sharpe,
        'recomendacion_sharpe': recomendacion_sharpe,
        'ciclo_recomendacion': ciclo_recomendacion
    }

def clasificar_estrategias_inversion(alpha_beta_metrics, cycle_phase, argentina_metrics):
    """
    Clasifica estrategias de inversión según la teoría de alpha y beta.
    """
    beta = alpha_beta_metrics.get('beta', 1.0)
    alpha_annual = alpha_beta_metrics.get('alpha_annual', 0)
    information_ratio = alpha_beta_metrics.get('information_ratio', 0)
    sharpe_ratio = alpha_beta_metrics.get('sharpe_ratio', 0)
    
    # Clasificación principal según teoría
    estrategia_principal = ""
    descripcion_principal = ""
    
    # 1. Index Tracker (β = 1, α = 0)
    if abs(beta - 1.0) < 0.1 and abs(alpha_annual) < 0.02:
        estrategia_principal = "Index Tracker"
        descripcion_principal = "Replica el rendimiento del benchmark (MERVAL)"
    # 2. Traditional Long-Only Asset Manager (β = 1, α > 0)
    elif abs(beta - 1.0) < 0.1 and alpha_annual > 0.02:
        estrategia_principal = "Traditional Long-Only Asset Manager"
        descripcion_principal = "Supera el mercado con retorno extra no correlacionado"
    # 3. Smart Beta (β dinámico, α = 0)
    elif abs(alpha_annual) < 0.02 and (beta > 1.1 or beta < 0.9):
        estrategia_principal = "Smart Beta"
        descripcion_principal = "Supera el mercado ajustando dinámicamente ponderaciones"
    # 4. Hedge Fund (β = 0, α > 0)
    elif abs(beta) < 0.3 and alpha_annual > 0.02:
        estrategia_principal = "Hedge Fund"
        descripcion_principal = "Entrega retornos absolutos no correlacionados con el mercado"
    # 5. Estrategia híbrida o no clasificada
    else:
        estrategia_principal = "Estrategia Híbrida"
        descripcion_principal = "Combinación de características de múltiples estrategias"
    
    return {
        'estrategia_principal': estrategia_principal,
        'descripcion_principal': descripcion_principal,
        'beta_actual': beta,
        'alpha_actual': alpha_annual
    }

def recomendar_hedge_funds_smart_beta(alpha_beta_metrics, cycle_phase, argentina_metrics):
    """
    Recomienda estrategias de hedge funds y smart beta basadas en métricas CAPM.
    """
    beta = alpha_beta_metrics.get('beta', 1.0)
    alpha_annual = alpha_beta_metrics.get('alpha_annual', 0)
    information_ratio = alpha_beta_metrics.get('information_ratio', 0)
    sharpe_ratio = alpha_beta_metrics.get('sharpe_ratio', 0)
    
    # Clasificar estrategia principal
    clasificacion = clasificar_estrategias_inversion(alpha_beta_metrics, cycle_phase, argentina_metrics)
    
    # Estrategias de Hedge Funds según métricas
    hedge_fund_strategies = []
    
    # Estrategias basadas en clasificación principal
    if clasificacion['estrategia_principal'] == "Hedge Fund":
        hedge_fund_strategies.append({
            "estrategia": "Market Neutral",
            "descripcion": "Eliminar exposición al mercado manteniendo alpha",
            "exposicion": "50% Long / 50% Short",
            "riesgo": "Bajo",
            "retorno_esperado": "6-10% anual",
            "categoria": "Hedge Fund Puro"
        })
        hedge_fund_strategies.append({
            "estrategia": "Long/Short Equity",
            "descripcion": "Aprovechar el alpha positivo con posiciones largas y cortas",
            "exposicion": "60% Long / 40% Short",
            "riesgo": "Moderado",
            "retorno_esperado": "8-12% anual",
            "categoria": "Hedge Fund Puro"
        })
    elif clasificacion['estrategia_principal'] == "Traditional Long-Only Asset Manager":
        hedge_fund_strategies.append({
            "estrategia": "Enhanced Indexing",
            "descripcion": "Mejorar rendimiento del índice con selección activa",
            "exposicion": "90% Index / 10% Alpha",
            "riesgo": "Bajo",
            "retorno_esperado": "4-8% anual",
            "categoria": "Asset Management"
        })
    elif clasificacion['estrategia_principal'] == "Smart Beta":
        hedge_fund_strategies.append({
            "estrategia": "Dynamic Beta",
            "descripcion": "Ajustar beta dinámicamente según condiciones de mercado",
            "exposicion": "β > 1 en mercados alcistas, β < 1 en mercados bajistas",
            "riesgo": "Moderado",
            "retorno_esperado": "5-9% anual",
            "categoria": "Smart Beta"
        })
    else:  # Index Tracker o Híbrida
        hedge_fund_strategies.append({
            "estrategia": "Risk Parity",
            "descripcion": "Distribuir riesgo equitativamente entre activos",
            "exposicion": "Diversificada por volatilidad",
            "riesgo": "Bajo",
            "retorno_esperado": "3-6% anual",
            "categoria": "Index/Passive"
        })
    
    # Estrategias basadas en Alpha
    if alpha_annual > 0.08:
        hedge_fund_strategies.append({
            "estrategia": "Alpha Capture",
            "descripcion": "Capturar alpha mediante estrategias activas",
            "exposicion": "Posiciones largas en activos con alpha positivo",
            "riesgo": "Moderado",
            "retorno_esperado": "8-12% anual",
            "categoria": "Alpha Strategy"
        })
    elif alpha_annual > 0.03:
        hedge_fund_strategies.append({
            "estrategia": "Enhanced Indexing",
            "descripcion": "Mejorar rendimiento del índice con selección activa",
            "exposicion": "90% Index / 10% Alpha",
            "riesgo": "Bajo",
            "retorno_esperado": "4-8% anual",
            "categoria": "Enhanced Index"
        })
    
    # Estrategias basadas en Beta
    if beta > 1.3:
        hedge_fund_strategies.append({
            "estrategia": "Beta Hedging",
            "descripcion": "Reducir exposición sistemática con derivados",
            "exposicion": "Posiciones largas + cobertura con futuros",
            "riesgo": "Moderado",
            "retorno_esperado": "5-9% anual",
            "categoria": "Risk Management"
        })
    elif beta < 0.5:
        hedge_fund_strategies.append({
            "estrategia": "Leveraged Beta",
            "descripcion": "Aumentar exposición controlada al mercado",
            "exposicion": "Uso moderado de apalancamiento",
            "riesgo": "Moderado",
            "retorno_esperado": "7-11% anual",
            "categoria": "Leverage Strategy"
        })
    
    # Estrategias Smart Beta
    smart_beta_strategies = []
    
    # Estrategias según clasificación
    if clasificacion['estrategia_principal'] == "Smart Beta":
        smart_beta_strategies.append({
            "estrategia": "Dynamic Smart Beta",
            "descripcion": "Ajustar ponderaciones dinámicamente según condiciones",
            "implementacion": "β > 1 en mercados alcistas, β < 1 en mercados bajistas",
            "riesgo": "Moderado",
            "retorno_esperado": "6-10% anual",
            "categoria": "Smart Beta Dinámico"
        })
    
    # Estrategias según Information Ratio
    if information_ratio > 0.4:
        smart_beta_strategies.append({
            "estrategia": "Momentum Factor",
            "descripcion": "Aprovechar tendencias de mercado",
            "implementacion": "Selección por momentum de 6-12 meses",
            "riesgo": "Moderado",
            "retorno_esperado": "6-10% anual",
            "categoria": "Factor Investing"
        })
        smart_beta_strategies.append({
            "estrategia": "Quality Factor",
            "descripcion": "Invertir en empresas de alta calidad",
            "implementacion": "Filtros por ROE, deuda, estabilidad",
            "riesgo": "Bajo",
            "retorno_esperado": "4-8% anual",
            "categoria": "Factor Investing"
        })
    elif information_ratio > 0.2:
        smart_beta_strategies.append({
            "estrategia": "Value Factor",
            "descripcion": "Enfoque en empresas subvaloradas",
            "implementacion": "P/B, P/E bajos, dividendos altos",
            "riesgo": "Moderado",
            "retorno_esperado": "5-9% anual",
            "categoria": "Factor Investing"
        })
    else:
        smart_beta_strategies.append({
            "estrategia": "Low Volatility",
            "descripcion": "Minimizar volatilidad del portafolio",
            "implementacion": "Selección por volatilidad histórica",
            "riesgo": "Bajo",
            "retorno_esperado": "3-6% anual",
            "categoria": "Risk Factor"
        })
    
    # Estrategias específicas para Argentina
    argentina_specific_strategies = []
    
    # Basadas en ciclo económico
    if cycle_phase in ["Contracción", "Recesión"]:
        argentina_specific_strategies.append({
            "estrategia": "Dollar Hedging",
            "descripcion": "Protección contra depreciación del peso",
            "implementacion": "Posiciones en dólar MEP/CCL",
            "riesgo": "Bajo",
            "retorno_esperado": "2-5% anual",
            "categoria": "Argentina Defensiva"
        })
        argentina_specific_strategies.append({
            "estrategia": "Inflation Protection",
            "descripcion": "Protección contra inflación",
            "implementacion": "Bonos CER, UVA, activos hard",
            "riesgo": "Bajo",
            "retorno_esperado": "3-7% anual",
            "categoria": "Argentina Defensiva"
        })
    elif cycle_phase == "Auge":
        argentina_specific_strategies.append({
            "estrategia": "Defensive Rotation",
            "descripcion": "Rotación hacia activos defensivos",
            "implementacion": "Sectores defensivos, liquidez alta",
            "riesgo": "Bajo",
            "retorno_esperado": "4-7% anual",
            "categoria": "Argentina Defensiva"
        })
    else:  # Expansión
        argentina_specific_strategies.append({
            "estrategia": "Growth Momentum",
            "descripcion": "Aprovechar crecimiento económico",
            "implementacion": "Sectores cíclicos, CEDEARs",
            "riesgo": "Moderado",
            "retorno_esperado": "8-15% anual",
            "categoria": "Argentina Cíclica"
        })
    
    # Basadas en variables macro argentinas
    if 'IPC' in argentina_metrics:
        ipc_valor = float(argentina_metrics['IPC'].replace('%', ''))
        if ipc_valor > 50:
            argentina_specific_strategies.append({
                "estrategia": "Real Assets",
                "descripcion": "Protección contra inflación alta",
                "implementacion": "Inmuebles, commodities, oro",
                "riesgo": "Moderado",
                "retorno_esperado": "5-10% anual",
                "categoria": "Argentina Inflacionaria"
            })
    
    if 'LELIQ' in argentina_metrics:
        leliq_valor = float(argentina_metrics['LELIQ'].replace('%', ''))
        if leliq_valor > 100:
            argentina_specific_strategies.append({
                "estrategia": "Fixed Income Arbitrage",
                "descripcion": "Aprovechar diferenciales de tasas",
                "implementacion": "Bonos soberanos, letras del tesoro",
                "riesgo": "Bajo",
                "retorno_esperado": "3-6% anual",
                "categoria": "Argentina Monetaria"
            })
    
    return {
        'clasificacion_principal': clasificacion,
        'hedge_fund_strategies': hedge_fund_strategies,
        'smart_beta_strategies': smart_beta_strategies,
        'argentina_specific_strategies': argentina_specific_strategies
    }

def analizar_correlacion_bcra_variables(portfolio_returns, bcra_data, argentina_metrics):
    """
    Analiza la correlación del portafolio con variables específicas del BCRA.
    """
    correlaciones = {}
    
    try:
        # Convertir datos del BCRA a series temporales si es posible
        if not bcra_data.empty:
            # Simular correlación con variables clave
            variables_clave = ['LELIQ', 'IPC', 'Tipo de cambio', 'Reservas']
            
            for variable in variables_clave:
                if variable in argentina_metrics:
                    # Simular correlación basada en el contexto
                    if variable == 'LELIQ':
                        # Alta LELIQ suele ser negativa para acciones
                        correlacion = -0.3 if float(argentina_metrics[variable].replace('%', '')) > 100 else -0.1
                    elif variable == 'IPC':
                        # Alta inflación puede ser positiva para activos hard
                        ipc_valor = float(argentina_metrics[variable].replace('%', ''))
                        correlacion = 0.2 if ipc_valor > 50 else 0.0
                    elif variable == 'Tipo de cambio':
                        # Depreciación del peso puede ser positiva para exportadores
                        correlacion = 0.1
                    else:
                        correlacion = 0.0
                    
                    correlaciones[variable] = {
                        'correlacion': correlacion,
                        'interpretacion': interpretar_correlacion(variable, correlacion),
                        'recomendacion': generar_recomendacion_correlacion(variable, correlacion)
                    }
    
    except Exception as e:
        st.error(f"Error en análisis de correlación: {str(e)}")
    
    return correlaciones

def interpretar_correlacion(variable, correlacion):
    """
    Interpreta la correlación con variables del BCRA.
    """
    if abs(correlacion) < 0.1:
        return "Correlación débil - Poca influencia directa"
    elif abs(correlacion) < 0.3:
        return "Correlación moderada - Influencia significativa"
    elif abs(correlacion) < 0.5:
        return "Correlación fuerte - Alta influencia"
    else:
        return "Correlación muy fuerte - Influencia dominante"

def generar_recomendacion_correlacion(variable, correlacion):
    """
    Genera recomendaciones basadas en la correlación con variables del BCRA.
    """
    if variable == 'LELIQ':
        if correlacion < -0.2:
            return "Considerar reducción de exposición a activos sensibles a tasas"
        else:
            return "Mantener exposición actual a activos de renta fija"
    elif variable == 'IPC':
        if correlacion > 0.2:
            return "Aumentar exposición a activos que protejan contra inflación"
        else:
            return "Mantener diversificación con activos ajustables"
    elif variable == 'Tipo de cambio':
        if correlacion > 0.1:
            return "Considerar exposición a empresas exportadoras"
        else:
            return "Evaluar cobertura cambiaria si es necesario"
    else:
        return "Monitorear evolución de la variable"

def generar_informe_capm_completo(alpha_beta_metrics, estrategia_analisis, cycle_phase, argentina_metrics, hedge_smart_recommendations=None, correlaciones_bcra=None):
    """
    Genera un informe CAPM completo y detallado para contexto argentino.
    """
    informe = f"""
    # 📊 INFORME CAPM COMPLETO - CONTEXTO ARGENTINO
    
    ## 🎯 RESUMEN EJECUTIVO
    
    ### Métricas CAPM Principales
    - **Alpha Anualizado**: {alpha_beta_metrics.get('alpha_annual', 0):.2%}
    - **Beta**: {alpha_beta_metrics.get('beta', 0):.2f}
    - **R²**: {alpha_beta_metrics.get('r_squared', 0):.2f}
    - **Information Ratio**: {alpha_beta_metrics.get('information_ratio', 0):.2f}
    - **Sharpe Ratio**: {alpha_beta_metrics.get('sharpe_ratio', 0):.2f}
    
    ### Diagnóstico del Ciclo Económico
    - **Fase Actual**: {cycle_phase}
    - **Contexto Macroeconómico**: {argentina_metrics.get('Diagnóstico', 'No disponible')}
    
    ### Clasificación de Estrategia de Inversión
    """
    
    if hedge_smart_recommendations and 'clasificacion_principal' in hedge_smart_recommendations:
        clasificacion = hedge_smart_recommendations['clasificacion_principal']
        informe += f"""
    - **Estrategia Principal**: {clasificacion['estrategia_principal']}
    - **Descripción**: {clasificacion['descripcion_principal']}
    - **Beta Actual**: {clasificacion['beta_actual']:.2f}
    - **Alpha Actual**: {clasificacion['alpha_actual']:.2%}
    """
    
    informe += f"""
    
    ---
    
    ## 📈 ANÁLISIS DETALLADO DE RIESGO Y RENDIMIENTO
    
    ### 1. Riesgo Sistemático (Beta)
    **Valor**: {alpha_beta_metrics.get('beta', 0):.2f}
    **Interpretación**: {estrategia_analisis['riesgo_sistematico']}
    **Recomendación**: {estrategia_analisis['recomendacion_beta']}
    
    ### 2. Rendimiento Ajustado por Riesgo (Alpha)
    **Valor**: {alpha_beta_metrics.get('alpha_annual', 0):.2%}
    **Interpretación**: {estrategia_analisis['rendimiento_ajustado']}
    **Recomendación**: {estrategia_analisis['recomendacion_alpha']}
    
    ### 3. Calidad de la Gestión (Information Ratio)
    **Valor**: {alpha_beta_metrics.get('information_ratio', 0):.2f}
    **Interpretación**: {estrategia_analisis['calidad_gestion']}
    **Recomendación**: {estrategia_analisis['recomendacion_ir']}
    
    ### 4. Ratio de Sharpe
    **Valor**: {alpha_beta_metrics.get('sharpe_ratio', 0):.2f}
    **Interpretación**: {estrategia_analisis['ratio_sharpe']}
    **Recomendación**: {estrategia_analisis['recomendacion_sharpe']}
    
    ---
    
    ## 🇦🇷 CONTEXTO ARGENTINO ESPECÍFICO
    
    ### Variables Macroeconómicas Clave
    """
    
    # Agregar métricas específicas de Argentina
    for key, value in argentina_metrics.items():
        if key != 'Diagnóstico':
            informe += f"- **{key}**: {value}\n"
    
    informe += f"""
    
    ### Recomendaciones por Ciclo Económico
    **Beta Ideal para {cycle_phase}**: {estrategia_analisis['ciclo_recomendacion']['beta_ideal']}
    **Estrategia Recomendada**: {estrategia_analisis['ciclo_recomendacion']['estrategia']}
    **Activos Sugeridos**: {estrategia_analisis['ciclo_recomendacion']['activos']}
    
    ---
    
    ## 🎯 ESTRATEGIAS ESPECÍFICAS POR CONTEXTO
    
    """
    
    # Estrategias específicas según el contexto
    if cycle_phase in ["Contracción", "Recesión"]:
        informe += """
    ### 🛡️ Estrategias Defensivas para Contexto Contractivo
    
    **Activos Refugio Recomendados:**
    - **Dólar MEP/CCL**: Protección cambiaria con monitoreo de volatilidad
    - **Bonos CER**: Protección inflacionaria
    - **Letras del Tesoro**: Liquidez y seguridad
    - **FCI de renta fija**: Diversificación profesional
    
    **Análisis Granular Requerido:**
    - Identificar empresas individuales en MERVAL con resiliencia macroeconómica
    - Buscar oportunidades de inversión a largo plazo en sectores defensivos
    - Evitar alta exposición a acciones del MERVAL en contexto bajista
    
    **Métricas de Seguimiento:**
    - Volatilidad del dólar MEP/CCL
    - Correlación con variables BCRA
    - Tracking error respecto al MERVAL
    """
    elif cycle_phase == "Auge":
        informe += """
    ### ⚠️ Estrategias de Protección para Contexto de Auge
    
    **Activos de Protección:**
    - **Activos hard**: Inmuebles, oro físico
    - **Diversificación**: Balance entre pesos y dólares
    - **FCI mixtos**: Profesionalización del portafolio
    
    **Preparación para Corrección:**
    - Reducir exposición a activos de riesgo
    - Aumentar liquidez
    - Considerar coberturas con derivados
    """
    else:  # Expansión
        informe += """
    ### 📈 Estrategias de Crecimiento para Contexto Expansivo
    
    **Activos de Crecimiento:**
    - **Acciones locales**: Aprovechar crecimiento económico
    - **CEDEARs**: Exposición internacional
    - **Bonos ajustables**: Protección inflacionaria
    
    **Oportunidades de Mercado:**
    - Sectores cíclicos
    - Empresas con apalancamiento operativo
    - Activos con correlación positiva al crecimiento
    """
    
    # Agregar sección de Hedge Funds y Smart Beta si están disponibles
    if hedge_smart_recommendations:
        informe += """
    
    ---
    
    ## 🏦 RECOMENDACIONES DE HEDGE FUNDS Y SMART BETA
    
    ### 🎯 Estrategias de Hedge Funds Basadas en Alpha/Beta
    """
        
        for strategy in hedge_smart_recommendations.get('hedge_fund_strategies', []):
            informe += f"""
    **{strategy['estrategia']}** ({strategy.get('categoria', 'Sin categoría')})
    - **Descripción**: {strategy['descripcion']}
    - **Exposición**: {strategy['exposicion']}
    - **Riesgo**: {strategy['riesgo']}
    - **Retorno Esperado**: {strategy['retorno_esperado']}
    """
        
        informe += """
    
    ### 📊 Estrategias Smart Beta
    """
        
        for strategy in hedge_smart_recommendations.get('smart_beta_strategies', []):
            informe += f"""
    **{strategy['estrategia']}** ({strategy.get('categoria', 'Sin categoría')})
    - **Descripción**: {strategy['descripcion']}
    - **Implementación**: {strategy['implementacion']}
    - **Riesgo**: {strategy['riesgo']}
    - **Retorno Esperado**: {strategy['retorno_esperado']}
    """
        
        informe += """
    
    ### 🇦🇷 Estrategias Específicas para Argentina
    """
        
        for strategy in hedge_smart_recommendations.get('argentina_specific_strategies', []):
            informe += f"""
    **{strategy['estrategia']}** ({strategy.get('categoria', 'Sin categoría')})
    - **Descripción**: {strategy['descripcion']}
    - **Implementación**: {strategy['implementacion']}
    - **Riesgo**: {strategy['riesgo']}
    - **Retorno Esperado**: {strategy['retorno_esperado']}
    """
    
    # Agregar análisis de correlación con variables del BCRA
    if correlaciones_bcra:
        informe += """
    
    ### 📊 Análisis de Correlación con Variables BCRA
    """
        
        for variable, datos in correlaciones_bcra.items():
            informe += f"""
    **{variable}**
    - **Correlación**: {datos['correlacion']:.3f}
    - **Interpretación**: {datos['interpretacion']}
    - **Recomendación**: {datos['recomendacion']}
    """
    
    informe += f"""
    
    ---
    
    ## 📊 MÉTRICAS TÉCNICAS ADICIONALES
    
    ### Estadísticas de Regresión
    - **Observaciones**: {alpha_beta_metrics.get('observations', 0)}
    - **P-Value**: {alpha_beta_metrics.get('p_value', 0):.4f}
    - **Error Estándar**: {alpha_beta_metrics.get('std_error', 0):.4f}
    - **Intervalo de Confianza Beta**: ({alpha_beta_metrics.get('confidence_interval', (0,0))[0]:.3f}, {alpha_beta_metrics.get('confidence_interval', (0,0))[1]:.3f})
    
    ### Ratios de Rendimiento
    - **Treynor Ratio**: {alpha_beta_metrics.get('treynor_ratio', 0):.2f}
    - **Jensen's Alpha**: {alpha_beta_metrics.get('jensen_alpha', 0):.2%}
    - **Tracking Error**: {alpha_beta_metrics.get('tracking_error', 0):.2%}
    
    ---
    
    ## 🎯 RECOMENDACIONES FINALES
    
    ### Acciones Inmediatas
    1. **Evaluar exposición actual** según beta calculado
    2. **Ajustar ponderaciones** según recomendaciones del ciclo
    3. **Monitorear métricas** de forma continua
    4. **Revisar estrategia** si alpha es negativo
    
    ### Seguimiento Continuo
    - Recalcular métricas CAPM mensualmente
    - Monitorear cambios en variables BCRA
    - Ajustar estrategia según evolución del ciclo económico
    - Evaluar nuevas oportunidades según contexto macro
    
    ---
    
    *Informe generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}*
    """
    
    return informe

def mostrar_optimizacion_portafolio(periodo_dias, api_key_input):
    """Muestra el análisis de optimización de portafolio adaptado al contexto argentino con análisis CAPM completo"""
    st.header("🧱 Optimización de Portafolio - Contexto Argentino")
    
    # Obtener datos del BCRA
    with st.spinner('Obteniendo datos del BCRA...'):
        bcra_data = get_bcra_variables()
    
    if not bcra_data.empty:
        # Analizar indicadores del ciclo
        indicators = analyze_economic_cycle(bcra_data)
        
        if indicators:
            # Determinar fase del ciclo
            cycle_phase, cycle_class, cycle_analysis, argentina_metrics = determine_economic_cycle(indicators)
            
            # Mostrar indicador del ciclo
            st.markdown(f"""
            <div class="cycle-indicator {cycle_class}">
                <h3>Fase del Ciclo Económico: {cycle_phase}</h3>
                <p>{argentina_metrics.get('Diagnóstico', '')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Métricas específicas de Argentina
            st.subheader("🇦🇷 Métricas Clave del Contexto Argentino")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                for key, value in list(argentina_metrics.items())[:3]:
                    if key != 'Diagnóstico':
                        st.metric(label=key, value=value)
            
            with col2:
                for key, value in list(argentina_metrics.items())[3:6]:
                    if key != 'Diagnóstico':
                        st.metric(label=key, value=value)
            
            with col3:
                for key, value in list(argentina_metrics.items())[6:]:
                    if key != 'Diagnóstico':
                        st.metric(label=key, value=value)
            
            # Análisis detallado
            st.subheader("📊 Análisis de Indicadores")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Variables BCRA")
                for category, data in indicators.items():
                    if isinstance(data, dict) and 'Valor' in data:
                        st.metric(label=category, value=data['Valor'])
            
            with col2:
                st.subheader("🔍 Interpretación")
                for indicator, value in cycle_analysis.items():
                    st.info(f"**{indicator}**: {value}")
            
            # Recomendaciones de portafolio
            st.subheader("💼 Estrategia de Portafolio Recomendada")
            recommendations = get_portfolio_recommendations(cycle_phase)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🎯 Activos Recomendados")
                for activo in recommendations["activos_recomendados"]:
                    st.write(f"• {activo}")
                
                st.subheader("📝 Contexto")
                st.write(recommendations["comentario"])
            
            with col2:
                st.subheader("⚖️ Ponderación Sugerida")
                for asset, weight in recommendations["ponderacion"].items():
                    st.metric(label=asset, value=f"{weight*100:.0f}%")
                
                st.subheader("📊 Estrategia")
                st.success(f"**{recommendations['estrategia']}**")
                st.metric(label="Nivel de Riesgo", value=recommendations["riesgo"])
            
            # ===== ANÁLISIS CAPM COMPLETO =====
            st.markdown("---")
            st.subheader("📊 ANÁLISIS CAPM COMPLETO - RESPECTO AL MERVAL")
            
            # Configuración del análisis CAPM
            st.sidebar.subheader("⚙️ Configuración CAPM")
            
            # Selección de activos para el portafolio
            st.sidebar.markdown("**Seleccionar Activos para Análisis CAPM:**")
            
            # Activos locales argentinos
            activos_locales = st.sidebar.multiselect(
                "Activos Locales (MERVAL)",
                ["GGAL.BA", "YPF.BA", "PAMP.BA", "ALUA.BA", "TECO2.BA", "CRES.BA", "BMA.BA", "TGS.BA", 
                 "TEN.BA", "SUPV.BA", "LOMA.BA", "AGRO.BA", "MIRG.BA", "EDN.BA", "TGSU2.BA"],
                default=["GGAL.BA", "YPF.BA", "PAMP.BA"]
            )
            
            # CEDEARs para diversificación
            cedears_capm = st.sidebar.multiselect(
                "CEDEARs (Diversificación)",
                ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN", "META", "NFLX"],
                default=["SPY", "AAPL", "MSFT"]
            )
            
            # Activos defensivos
            activos_defensivos = st.sidebar.multiselect(
                "Activos Defensivos",
                ["Dólar MEP", "Dólar CCL", "Bonos CER", "Letras del Tesoro", "Oro (GLD)"],
                default=["Dólar MEP", "Bonos CER"]
            )
            
            # Configuración de ponderaciones
            st.sidebar.markdown("**Ponderaciones del Portafolio:**")
            peso_locales = st.sidebar.slider("Activos Locales (%)", 0, 100, 40)
            peso_cedears = st.sidebar.slider("CEDEARs (%)", 0, 100, 30)
            peso_defensivos = st.sidebar.slider("Activos Defensivos (%)", 0, 100, 30)
            
            # Validar que las ponderaciones sumen 100%
            total_ponderacion = peso_locales + peso_cedears + peso_defensivos
            if total_ponderacion != 100:
                st.sidebar.warning(f"⚠️ Las ponderaciones deben sumar 100%. Actual: {total_ponderacion}%")
            
            # Tasa libre de riesgo
            leliq_valor = float(argentina_metrics.get('LELIQ', '100').replace('%', '')) if 'LELIQ' in argentina_metrics else 100.0
            tasa_libre_riesgo = st.sidebar.number_input(
                "Tasa Libre de Riesgo Anual (%)", 
                min_value=0.0, 
                max_value=50.0, 
                value=leliq_valor,
                step=0.1
            ) / 100
            
            # Botón para ejecutar análisis CAPM
            if st.sidebar.button("🚀 Ejecutar Análisis CAPM Completo"):
                with st.spinner('Calculando métricas CAPM...'):
                    try:
                        # Obtener datos del MERVAL como benchmark
                        merval_data = get_yfinance_data(["^MERV"], period="1y")
                        
                        if not merval_data.empty and '^MERV' in merval_data:
                            merval_returns = merval_data['^MERV']['Adj Close'].pct_change().dropna()
                            
                            # Construir portafolio simulado
                            portfolio_returns = pd.Series(0.0, index=merval_returns.index)
                            
                            # Simular retornos de activos locales
                            if activos_locales:
                                local_returns = get_yfinance_data(activos_locales, period="1y")
                                if not local_returns.empty:
                                    local_portfolio = pd.Series(0.0, index=merval_returns.index)
                                    for asset in activos_locales:
                                        if asset in local_returns:
                                            asset_returns = local_returns[asset]['Adj Close'].pct_change().dropna()
                                            # Alinear con el índice del MERVAL
                                            aligned_returns = asset_returns.reindex(merval_returns.index).fillna(0)
                                            local_portfolio += aligned_returns * (peso_locales / 100 / len(activos_locales))
                                    portfolio_returns += local_portfolio
                            
                            # Simular retornos de CEDEARs
                            if cedears_capm:
                                cedear_returns = get_yfinance_data(cedears_capm, period="1y")
                                if not cedear_returns.empty:
                                    cedear_portfolio = pd.Series(0.0, index=merval_returns.index)
                                    for asset in cedears_capm:
                                        if asset in cedear_returns:
                                            asset_returns = cedear_returns[asset]['Adj Close'].pct_change().dropna()
                                            aligned_returns = asset_returns.reindex(merval_returns.index).fillna(0)
                                            cedear_portfolio += aligned_returns * (peso_cedears / 100 / len(cedears_capm))
                                    portfolio_returns += cedear_portfolio
                            
                            # Simular retornos de activos defensivos (simplificado)
                            if activos_defensivos:
                                # Para activos defensivos, usar una volatilidad menor
                                defensive_volatility = 0.05  # 5% anual
                                defensive_returns = np.random.normal(0.02/252, defensive_volatility/np.sqrt(252), len(merval_returns))
                                defensive_series = pd.Series(defensive_returns, index=merval_returns.index)
                                portfolio_returns += defensive_series * (peso_defensivos / 100)
                            
                            # Calcular métricas CAPM
                            capm_metrics = calcular_alpha_beta_capm(
                                portfolio_returns, 
                                merval_returns, 
                                risk_free_rate=tasa_libre_riesgo
                            )
                            
                            # Analizar estrategia
                            estrategia_analisis = analizar_estrategia_capm_argentina(capm_metrics, cycle_phase)
                            
                            # Obtener recomendaciones de hedge funds y smart beta
                            hedge_smart_recommendations = recomendar_hedge_funds_smart_beta(capm_metrics, cycle_phase, argentina_metrics)
                            
                            # Analizar correlación con variables del BCRA
                            correlaciones_bcra = analizar_correlacion_bcra_variables(portfolio_returns, bcra_data, argentina_metrics)
                            
                            # Mostrar resultados CAPM
                            st.subheader("📈 Métricas CAPM Principales")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric(
                                    "Alpha Anualizado", 
                                    f"{capm_metrics.get('alpha_annual', 0):.2%}",
                                    delta=f"{'Positivo' if capm_metrics.get('alpha_annual', 0) > 0 else 'Negativo'}"
                                )
                            
                            with col2:
                                st.metric(
                                    "Beta", 
                                    f"{capm_metrics.get('beta', 0):.2f}",
                                    delta=f"{'Alto' if capm_metrics.get('beta', 0) > 1.2 else 'Moderado' if capm_metrics.get('beta', 0) > 0.8 else 'Bajo'}"
                                )
                            
                            with col3:
                                st.metric(
                                    "Information Ratio", 
                                    f"{capm_metrics.get('information_ratio', 0):.2f}",
                                    delta=f"{'Excelente' if capm_metrics.get('information_ratio', 0) > 0.5 else 'Bueno' if capm_metrics.get('information_ratio', 0) > 0.3 else 'Aceptable'}"
                                )
                            
                            with col4:
                                st.metric(
                                    "Sharpe Ratio", 
                                    f"{capm_metrics.get('sharpe_ratio', 0):.2f}",
                                    delta=f"{'Excelente' if capm_metrics.get('sharpe_ratio', 0) > 1.0 else 'Bueno' if capm_metrics.get('sharpe_ratio', 0) > 0.5 else 'Aceptable'}"
                                )
                            
                            # Análisis detallado
                            st.subheader("🔍 Análisis Detallado de Riesgo y Rendimiento")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.info(f"**Riesgo Sistemático (Beta)**: {estrategia_analisis['riesgo_sistematico']}")
                                st.info(f"**Rendimiento Ajustado (Alpha)**: {estrategia_analisis['rendimiento_ajustado']}")
                            
                            with col2:
                                st.info(f"**Calidad de Gestión**: {estrategia_analisis['calidad_gestion']}")
                                st.info(f"**Ratio de Sharpe**: {estrategia_analisis['ratio_sharpe']}")
                            
                            # Recomendaciones específicas
                            st.subheader("🎯 Recomendaciones por Ciclo Económico")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.success(f"**Beta Ideal para {cycle_phase}**: {estrategia_analisis['ciclo_recomendacion']['beta_ideal']}")
                                st.success(f"**Estrategia**: {estrategia_analisis['ciclo_recomendacion']['estrategia']}")
                            
                            with col2:
                                st.success(f"**Activos Sugeridos**: {estrategia_analisis['ciclo_recomendacion']['activos']}")
                                st.success(f"**Observaciones**: {capm_metrics.get('observations', 0)} días")
                            
                            # Métricas técnicas adicionales
                            st.subheader("📊 Métricas Técnicas Adicionales")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("R²", f"{capm_metrics.get('r_squared', 0):.3f}")
                                st.metric("Tracking Error", f"{capm_metrics.get('tracking_error', 0):.2%}")
                            
                            with col2:
                                st.metric("Treynor Ratio", f"{capm_metrics.get('treynor_ratio', 0):.2f}")
                                st.metric("Jensen's Alpha", f"{capm_metrics.get('jensen_alpha', 0):.2%}")
                            
                            with col3:
                                st.metric("P-Value", f"{capm_metrics.get('p_value', 0):.4f}")
                                st.metric("Error Estándar", f"{capm_metrics.get('std_error', 0):.4f}")
                            
                            # Gráfico de regresión CAPM
                            st.subheader("📈 Gráfico de Regresión CAPM")
                            
                            try:
                                # Crear gráfico de dispersión
                                fig_capm = go.Figure()
                                
                                # Datos para el gráfico
                                excess_portfolio = portfolio_returns - tasa_libre_riesgo/252
                                excess_merval = merval_returns - tasa_libre_riesgo/252
                                
                                # Puntos de datos
                                fig_capm.add_trace(go.Scatter(
                                    x=excess_merval,
                                    y=excess_portfolio,
                                    mode='markers',
                                    name='Datos',
                                    marker=dict(color='blue', size=6, opacity=0.6)
                                ))
                                
                                # Línea de regresión
                                x_range = np.linspace(excess_merval.min(), excess_merval.max(), 100)
                                y_pred = capm_metrics.get('alpha', 0) + capm_metrics.get('beta', 0) * x_range
                                
                                fig_capm.add_trace(go.Scatter(
                                    x=x_range,
                                    y=y_pred,
                                    mode='lines',
                                    name='Regresión CAPM',
                                    line=dict(color='red', width=3)
                                ))
                                
                                # Línea de mercado (beta = 1)
                                y_market = x_range
                                fig_capm.add_trace(go.Scatter(
                                    x=x_range,
                                    y=y_market,
                                    mode='lines',
                                    name='Línea de Mercado (β=1)',
                                    line=dict(color='green', width=2, dash='dash')
                                ))
                                
                                fig_capm.update_layout(
                                    title="Regresión CAPM: Portafolio vs MERVAL",
                                    xaxis_title="Retorno Excedente MERVAL",
                                    yaxis_title="Retorno Excedente Portafolio",
                                    showlegend=True,
                                    height=500
                                )
                                
                                st.plotly_chart(fig_capm, use_container_width=True)
                                
                            except Exception as e:
                                st.error(f"Error al crear gráfico CAPM: {str(e)}")
                            
                            # Mostrar clasificación principal de la estrategia
                            st.subheader("🎯 CLASIFICACIÓN PRINCIPAL DE LA ESTRATEGIA")
                            
                            clasificacion_principal = hedge_smart_recommendations['clasificacion_principal']
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.success(f"**Estrategia Principal**: {clasificacion_principal['estrategia_principal']}")
                                st.info(f"**Descripción**: {clasificacion_principal['descripcion_principal']}")
                            
                            with col2:
                                st.metric("Beta Actual", f"{clasificacion_principal['beta_actual']:.2f}")
                                st.metric("Alpha Actual", f"{clasificacion_principal['alpha_actual']:.2%}")
                            
                            # Mostrar recomendaciones de Hedge Funds y Smart Beta
                            st.subheader("🏦 RECOMENDACIONES DE HEDGE FUNDS Y SMART BETA")
                            
                            # Hedge Funds
                            if hedge_smart_recommendations['hedge_fund_strategies']:
                                st.markdown("### 🎯 Estrategias de Hedge Funds")
                                for strategy in hedge_smart_recommendations['hedge_fund_strategies']:
                                    with st.expander(f"📊 {strategy['estrategia']}", expanded=False):
                                        st.write(f"**Descripción**: {strategy['descripcion']}")
                                        st.write(f"**Exposición**: {strategy['exposicion']}")
                                        st.write(f"**Riesgo**: {strategy['riesgo']}")
                                        st.write(f"**Retorno Esperado**: {strategy['retorno_esperado']}")
                                        st.write(f"**Categoría**: {strategy['categoria']}")
                                        
                                        # Mostrar indicador visual según categoría
                                        if strategy['categoria'] == "Hedge Fund Puro":
                                            st.success("✅ Estrategia de Hedge Fund puro")
                                        elif strategy['categoria'] == "Asset Management":
                                            st.info("ℹ️ Estrategia de gestión activa")
                                        elif strategy['categoria'] == "Smart Beta":
                                            st.warning("⚠️ Estrategia Smart Beta")
                                        else:
                                            st.info("ℹ️ Estrategia diversificada")
                            
                            # Smart Beta
                            if hedge_smart_recommendations['smart_beta_strategies']:
                                st.markdown("### 📊 Estrategias Smart Beta")
                                for strategy in hedge_smart_recommendations['smart_beta_strategies']:
                                    with st.expander(f"📈 {strategy['estrategia']}", expanded=False):
                                        st.write(f"**Descripción**: {strategy['descripcion']}")
                                        st.write(f"**Implementación**: {strategy['implementacion']}")
                                        st.write(f"**Riesgo**: {strategy['riesgo']}")
                                        st.write(f"**Retorno Esperado**: {strategy['retorno_esperado']}")
                                        st.write(f"**Categoría**: {strategy['categoria']}")
                                        
                                        # Mostrar indicador visual según categoría
                                        if strategy['categoria'] == "Smart Beta Dinámico":
                                            st.warning("⚠️ Smart Beta dinámico")
                                        elif strategy['categoria'] == "Factor Investing":
                                            st.info("ℹ️ Inversión por factores")
                                        elif strategy['categoria'] == "Risk Factor":
                                            st.success("✅ Factor de riesgo")
                                        else:
                                            st.info("ℹ️ Estrategia Smart Beta")
                            
                            # Estrategias específicas para Argentina
                            if hedge_smart_recommendations['argentina_specific_strategies']:
                                st.markdown("### 🇦🇷 Estrategias Específicas para Argentina")
                                for strategy in hedge_smart_recommendations['argentina_specific_strategies']:
                                    with st.expander(f"🇦🇷 {strategy['estrategia']}", expanded=False):
                                        st.write(f"**Descripción**: {strategy['descripcion']}")
                                        st.write(f"**Implementación**: {strategy['implementacion']}")
                                        st.write(f"**Riesgo**: {strategy['riesgo']}")
                                        st.write(f"**Retorno Esperado**: {strategy['retorno_esperado']}")
                                        st.write(f"**Categoría**: {strategy['categoria']}")
                                        
                                        # Mostrar indicador visual según categoría
                                        if strategy['categoria'] == "Argentina Defensiva":
                                            st.success("✅ Estrategia defensiva argentina")
                                        elif strategy['categoria'] == "Argentina Cíclica":
                                            st.warning("⚠️ Estrategia cíclica argentina")
                                        elif strategy['categoria'] == "Argentina Inflacionaria":
                                            st.error("🔥 Estrategia anti-inflacionaria")
                                        elif strategy['categoria'] == "Argentina Monetaria":
                                            st.info("💱 Estrategia monetaria argentina")
                                        else:
                                            st.info("ℹ️ Estrategia argentina")
                            
                            # Análisis de correlación con variables del BCRA
                            if correlaciones_bcra:
                                st.markdown("### 📊 Análisis de Correlación con Variables BCRA")
                                for variable, datos in correlaciones_bcra.items():
                                    with st.expander(f"📈 {variable}", expanded=False):
                                        st.write(f"**Correlación**: {datos['correlacion']:.3f}")
                                        st.write(f"**Interpretación**: {datos['interpretacion']}")
                                        st.write(f"**Recomendación**: {datos['recomendacion']}")
                                        
                                        # Mostrar indicador visual de correlación
                                        if abs(datos['correlacion']) > 0.3:
                                            st.warning("⚠️ Correlación significativa detectada")
                                        elif abs(datos['correlacion']) > 0.1:
                                            st.info("ℹ️ Correlación moderada")
                                        else:
                                            st.success("✅ Correlación débil")
                            
                            # Informe completo
                            st.subheader("📋 INFORME CAPM COMPLETO")
                            
                            # Generar informe completo
                            informe_completo = generar_informe_capm_completo(
                                capm_metrics, 
                                estrategia_analisis, 
                                cycle_phase, 
                                argentina_metrics,
                                hedge_smart_recommendations,
                                correlaciones_bcra
                            )
                            
                            # Mostrar informe en formato expandible
                            with st.expander("📄 Ver Informe CAPM Completo", expanded=False):
                                st.markdown(informe_completo)
                            
                            # Descargar informe
                            st.download_button(
                                label="💾 Descargar Informe CAPM",
                                data=informe_completo,
                                file_name=f"informe_capm_argentina_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                                mime="text/markdown"
                            )
                            
                        else:
                            st.error("❌ No se pudieron obtener datos del MERVAL para el análisis CAPM")
                            
                    except Exception as e:
                        st.error(f"❌ Error en análisis CAPM: {str(e)}")
                        st.info("💡 Asegúrate de tener conexión a internet y que los símbolos sean válidos")
            
            # Análisis adicional específico para Argentina
            st.markdown("---")
            st.subheader("🔬 Análisis Adicional para el Contexto Argentino")
            
            # Análisis de brecha cambiaria
            if 'Tipo de cambio' in argentina_metrics and 'Dólar Oficial' in argentina_metrics:
                st.info("💡 **Brecha Cambiaria**: La diferencia entre dólar oficial y paralelo puede indicar presión sobre el tipo de cambio")
            
            # Análisis de inflación
            if 'IPC' in argentina_metrics:
                ipc_valor = float(argentina_metrics['IPC'].replace('%', ''))
                if ipc_valor > 50:
                    st.warning("⚠️ **Inflación Elevada**: Considerar activos que protejan contra la inflación (CER, UVA, dólar)")
                elif ipc_valor > 25:
                    st.info("ℹ️ **Inflación Moderada**: Mantener diversificación con activos ajustables")
                else:
                    st.success("✅ **Inflación Controlada**: Favorable para activos en pesos")
            
            # Análisis de LELIQ
            if 'LELIQ' in argentina_metrics:
                leliq_valor = float(argentina_metrics['LELIQ'].replace('%', ''))
                if leliq_valor > 100:
                    st.warning("⚠️ **LELIQ Alta**: Contexto contractivo, preferir activos defensivos")
                elif leliq_valor < 50:
                    st.success("✅ **LELIQ Baja**: Contexto expansivo, favorable para activos de riesgo")
                else:
                    st.info("ℹ️ **LELIQ Moderada**: Contexto neutral, mantener diversificación")
            
            # Recomendaciones específicas por contexto
            st.subheader("🎯 Recomendaciones Específicas")
            
            if cycle_phase in ["Contracción", "Recesión"]:
                st.markdown("""
                **Estrategias Defensivas Recomendadas:**
                - **Dólar MEP/CCL**: Protección cambiaria con monitoreo de volatilidad
                - **Bonos CER**: Protección inflacionaria
                - **Letras del Tesoro**: Liquidez y seguridad
                - **FCI de renta fija**: Diversificación profesional
                
                **Análisis Granular Requerido:**
                - Identificar empresas individuales en MERVAL con resiliencia macroeconómica
                - Buscar oportunidades de inversión a largo plazo en sectores defensivos
                - Evitar alta exposición a acciones del MERVAL en contexto bajista
                """)
            elif cycle_phase == "Auge":
                st.markdown("""
                **Estrategias de Protección:**
                - **Activos hard**: Inmuebles, oro físico
                - **Diversificación**: Balance entre pesos y dólares
                - **FCI mixtos**: Profesionalización del portafolio
                """)
            else:  # Expansión
                st.markdown("""
                **Estrategias de Crecimiento:**
                - **Acciones locales**: Aprovechar crecimiento económico
                - **CEDEARs**: Exposición internacional
                - **Bonos ajustables**: Protección inflacionaria
                """)
            
            # Análisis de sectores recomendados por ciclo económico
            st.subheader("🏭 Sectores Recomendados por Ciclo Económico")
            
            sector_recommendations_by_cycle = {
                "Expansión": {
                    "Sectores Favorables": ["Sector Financiero", "Sector Tecnología", "Sector Consumo"],
                    "Sectores Evitar": ["Sector Commodities/Metales Preciosos", "Sector Renta Fija"],
                    "Razón": "Crecimiento económico favorece sectores cíclicos"
                },
                "Auge": {
                    "Sectores Favorables": ["Sector Energético", "Sector Industrial", "Sector Telecomunicaciones"],
                    "Sectores Evitar": ["Sector Tecnología", "Sector Financiero"],
                    "Razón": "Protección ante sobrevaloración, preferir sectores defensivos"
                },
                "Contracción": {
                    "Sectores Favorables": ["Sector Renta Fija", "Sector Commodities/Metales Preciosos", "Sector Inmobiliario"],
                    "Sectores Evitar": ["Sector Tecnología", "Sector Consumo"],
                    "Razón": "Fuga al refugio, sectores defensivos y de valor"
                },
                "Recesión": {
                    "Sectores Favorables": ["Sector Commodities/Metales Preciosos", "Sector Renta Fija", "Sector Inmobiliario"],
                    "Sectores Evitar": ["Sector Tecnología", "Sector Financiero", "Sector Consumo"],
                    "Razón": "Máxima defensa, activos hard y refugio"
                }
            }
            
            cycle_sectors = sector_recommendations_by_cycle.get(cycle_phase, {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.success("**Sectores Favorables:**")
                for sector in cycle_sectors.get("Sectores Favorables", []):
                    st.write(f"• {sector}")
            
            with col2:
                st.warning("**Sectores a Evitar:**")
                for sector in cycle_sectors.get("Sectores Evitar", []):
                    st.write(f"• {sector}")
            
            st.info(f"**Razón**: {cycle_sectors.get('Razón', '')}")
            
            # Análisis de diversificación sectorial recomendada
            st.subheader("📊 Diversificación Sectorial Recomendada")
            
            diversification_recommendations = {
                "Expansión": "4-6 sectores diferentes, énfasis en crecimiento",
                "Auge": "5-7 sectores, balance entre crecimiento y defensa",
                "Contracción": "3-5 sectores defensivos, alta concentración en refugio",
                "Recesión": "2-4 sectores, máxima concentración en activos hard"
            }
            
            st.info(f"**Diversificación recomendada**: {diversification_recommendations.get(cycle_phase, 'Mantener diversificación')}")
            
            # Alertas sectoriales específicas para Argentina
            st.subheader("⚠️ Alertas Sectoriales - Contexto Argentino")
            
            argentina_sector_alerts = {
                "Sector Financiero": "Sensible a cambios en LELIQ y política monetaria",
                "Sector Energético": "Afectado por precios internacionales y regulación local",
                "Sector Agropecuario": "Sensible a clima, precios internacionales y retenciones",
                "Sector Industrial": "Indicador de actividad económica local",
                "Sector Telecomunicaciones": "Regulado, dividendos estables pero limitado crecimiento",
                "Sector Tecnología": "Alta volatilidad, dependiente de acceso a divisas"
            }
            
            for sector, alert in argentina_sector_alerts.items():
                if sector in cycle_sectors.get("Sectores Favorables", []):
                    st.success(f"✅ **{sector}**: {alert}")
                elif sector in cycle_sectors.get("Sectores Evitar", []):
                    st.error(f"❌ **{sector}**: {alert}")
                else:
                    st.info(f"ℹ️ **{sector}**: {alert}")

def mostrar_analisis_intermarket(periodo_dias, api_key_input):
    """Muestra el análisis intermarket adaptado al contexto argentino"""
    st.header("🌐 Análisis Intermarket - Contexto Argentino")
    
    # Configuración de activos específicos para Argentina
    st.sidebar.subheader("📊 Activos para Análisis")
    
    # Activos locales argentinos
    local_assets = st.sidebar.multiselect(
        "Activos Locales (Argentina)",
        ["GGAL.BA", "YPF.BA", "PAMP.BA", "ALUA.BA", "TECO2.BA", "CRES.BA", "BMA.BA", "TGS.BA"],
        default=["GGAL.BA", "YPF.BA", "PAMP.BA"]
    )
    
    # CEDEARs (exposición internacional)
    cedears = st.sidebar.multiselect(
        "CEDEARs (Exposición Internacional)",
        ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN"],
        default=["SPY", "QQQ", "AAPL"]
    )
    
    # Activos defensivos
    defensive_assets = st.sidebar.multiselect(
        "Activos Defensivos",
        ["GLD", "SLV", "TLT", "IEF", "VNQ"],
        default=["GLD", "TLT"]
    )
    
    # Commodities relevantes para Argentina
    commodities = st.sidebar.multiselect(
        "Commodities (Relevantes para Argentina)",
        ["GC=F", "SI=F", "CL=F", "ZC=F", "ZS=F", "CC=F"],
        default=["GC=F", "ZS=F"]
    )
    
    all_assets = local_assets + cedears + defensive_assets + commodities
    
    if all_assets:
        with st.spinner('Obteniendo datos de yfinance...'):
            yf_data = get_yfinance_data(all_assets)
        
        if yf_data:
            # Realizar análisis intermarket
            analysis = analyze_intermarket_data(yf_data, api_key_input)
            
            # Crear gráficos
            fig_prices, fig_corr = create_intermarket_charts(yf_data, analysis)
            
            # Mostrar gráficos
            if fig_prices:
                st.plotly_chart(fig_prices, use_container_width=True)
            
            if fig_corr:
                st.plotly_chart(fig_corr, use_container_width=True)
            
            # Mostrar análisis de momentum
            if 'momentum' in analysis:
                st.subheader("📈 Análisis de Momentum (20 días)")
                
                # Calcular estadísticas de momentum
                momentum_stats = analysis['momentum'].describe()
                st.dataframe(momentum_stats)
                
                # Gráfico de momentum
                fig_momentum = px.line(
                    analysis['momentum'],
                    title="Evolución del Momentum",
                    labels={'value': 'Retorno 20 días', 'variable': 'Activo'}
                )
                st.plotly_chart(fig_momentum, use_container_width=True)
            
            # Análisis de volatilidad
            if yf_data:
                st.subheader("📊 Análisis de Volatilidad")
                
                volatility_data = {}
                for symbol, data in yf_data.items():
                    returns = data['Close'].pct_change().dropna()
                    volatility_data[symbol] = returns.std() * np.sqrt(252) * 100  # Anualizada
                
                vol_df = pd.DataFrame(list(volatility_data.items()), columns=['Activo', 'Volatilidad (%)'])
                st.dataframe(vol_df.sort_values('Volatilidad (%)', ascending=False))
                
                # Gráfico de volatilidad
                fig_vol = px.bar(
                    vol_df,
                    x='Activo',
                    y='Volatilidad (%)',
                    title="Volatilidad Anualizada por Activo"
                )
                st.plotly_chart(fig_vol, use_container_width=True)
                
                # Análisis específico para contexto argentino
                st.subheader("🇦🇷 Análisis de Contexto Argentino")
                
                # Identificar activos más y menos volátiles
                vol_df_sorted = vol_df.sort_values('Volatilidad (%)', ascending=False)
                mas_volatil = vol_df_sorted.iloc[0]
                menos_volatil = vol_df_sorted.iloc[-1]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.warning(f"**Más Volátil**: {mas_volatil['Activo']} ({mas_volatil['Volatilidad (%)']:.1f}%)")
                    if 'BA' in mas_volatil['Activo']:
                        st.info("Activo local - Considerar timing de entrada")
                    elif 'GLD' in mas_volatil['Activo']:
                        st.info("Oro - Activo refugio, volatilidad normal")
                
                with col2:
                    st.success(f"**Menos Volátil**: {menos_volatil['Activo']} ({menos_volatil['Volatilidad (%)']:.1f}%)")
                    if 'TLT' in menos_volatil['Activo']:
                        st.info("Bonos del Tesoro - Activo defensivo")
                    elif 'BA' in menos_volatil['Activo']:
                        st.info("Activo local estable - Buena diversificación")
                
                # Recomendaciones basadas en volatilidad
                st.subheader("💡 Recomendaciones por Volatilidad")
                
                alta_vol = vol_df[vol_df['Volatilidad (%)'] > 30]
                baja_vol = vol_df[vol_df['Volatilidad (%)'] < 15]
                
                if not alta_vol.empty:
                    st.warning("**Activos de Alta Volatilidad** (>30%):")
                    for _, row in alta_vol.iterrows():
                        st.write(f"• {row['Activo']}: {row['Volatilidad (%)']:.1f}%")
                    st.info("Considerar posiciones más pequeñas o timing de entrada")
                
                if not baja_vol.empty:
                    st.success("**Activos de Baja Volatilidad** (<15%):")
                    for _, row in baja_vol.iterrows():
                        st.write(f"• {row['Activo']}: {row['Volatilidad (%)']:.1f}%")
                    st.info("Activos defensivos para estabilizar el portafolio")
                
                # Análisis de correlación con contexto argentino
                if 'correlations' in analysis:
                    st.subheader("🔗 Análisis de Correlaciones - Contexto Argentino")
                    
                    # Identificar correlaciones altas y bajas
                    corr_matrix = analysis['correlations']
                    high_corr = []
                    low_corr = []
                    
                    for i in range(len(corr_matrix.columns)):
                        for j in range(i+1, len(corr_matrix.columns)):
                            corr_val = corr_matrix.iloc[i, j]
                            if abs(corr_val) > 0.7:
                                high_corr.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_val))
                            elif abs(corr_val) < 0.2:
                                low_corr.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_val))
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if high_corr:
                            st.warning("**Correlaciones Altas** (>0.7):")
                            for asset1, asset2, corr in high_corr[:3]:
                                st.write(f"• {asset1} ↔ {asset2}: {corr:.2f}")
                            st.info("Considerar diversificación entre estos activos")
                    
                    with col2:
                        if low_corr:
                            st.success("**Correlaciones Bajas** (<0.2):")
                            for asset1, asset2, corr in low_corr[:3]:
                                st.write(f"• {asset1} ↔ {asset2}: {corr:.2f}")
                            st.info("Buena diversificación entre estos activos")
                
                # Análisis de sectores usando IA
                if 'sectors' in analysis and analysis['sectors']:
                    st.subheader("🏭 Análisis de Sectores por IA")
                    
                    # Crear DataFrame de sectores
                    sectors_df = pd.DataFrame(list(analysis['sectors'].items()), 
                                           columns=['Activo', 'Sector'])
                    
                    # Mostrar distribución de sectores
                    st.subheader("📊 Distribución por Sectores")
                    sector_counts = sectors_df['Sector'].value_counts()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Distribución de Sectores:**")
                        for sector, count in sector_counts.items():
                            st.write(f"• {sector}: {count} activos")
                    
                    with col2:
                        # Gráfico de distribución de sectores
                        fig_sectors = px.pie(
                            values=sector_counts.values,
                            names=sector_counts.index,
                            title="Distribución de Activos por Sector"
                        )
                        st.plotly_chart(fig_sectors, use_container_width=True)
                    
                    # Análisis de diversificación sectorial
                    st.subheader("🎯 Análisis de Diversificación Sectorial")
                    
                    if len(sector_counts) >= 4:
                        st.success("✅ **Buena diversificación sectorial**: Portafolio bien distribuido entre diferentes sectores")
                    elif len(sector_counts) >= 2:
                        st.warning("⚠️ **Diversificación moderada**: Considerar agregar más sectores")
                    else:
                        st.error("❌ **Baja diversificación**: Alto riesgo de concentración sectorial")
                    
                    # Recomendaciones por sector
                    st.subheader("💡 Recomendaciones por Sector")
                    
                    sector_recommendations = {
                        "Sector Financiero": "Sensible a tasas de interés y política monetaria",
                        "Sector Energético": "Correlacionado con precios de commodities energéticos",
                        "Sector Tecnología": "Alta volatilidad, alto potencial de crecimiento",
                        "Sector Agropecuario": "Sensible a clima y precios internacionales",
                        "Sector Industrial": "Indicador de actividad económica",
                        "Sector Telecomunicaciones": "Defensivo, dividendos estables",
                        "Sector Commodities/Metales Preciosos": "Refugio en contextos de incertidumbre",
                        "Sector Renta Fija": "Estabilidad y generación de ingresos",
                        "Sector Inmobiliario": "Protección inflacionaria a largo plazo",
                        "Sector Consumo/Comercio Electrónico": "Sensible al ciclo económico",
                        "Sector Automotriz/Tecnología": "Alto potencial de innovación"
                    }
                    
                    for sector in sector_counts.index:
                        if sector in sector_recommendations:
                            st.info(f"**{sector}**: {sector_recommendations[sector]}")
                    
                    # Análisis de correlación entre sectores
                    if len(sector_counts) > 1:
                        st.subheader("🔗 Correlación entre Sectores")
                        
                        # Agrupar activos por sector
                        sector_returns = {}
                        for symbol, data in yf_data.items():
                            if symbol in analysis['sectors']:
                                sector = analysis['sectors'][symbol]
                                if sector not in sector_returns:
                                    sector_returns[sector] = []
                                returns = data['Close'].pct_change().dropna()
                                sector_returns[sector].append(returns)
                        
                        # Calcular retornos promedio por sector
                        sector_avg_returns = {}
                        for sector, returns_list in sector_returns.items():
                            if returns_list:
                                # Promedio de retornos diarios por sector
                                avg_returns = pd.concat(returns_list, axis=1).mean(axis=1)
                                sector_avg_returns[sector] = avg_returns
                        
                        if len(sector_avg_returns) > 1:
                            # Crear DataFrame de retornos por sector
                            sector_df = pd.DataFrame(sector_avg_returns)
                            sector_corr = sector_df.corr()
                            
                            # Gráfico de correlación entre sectores
                            fig_sector_corr = px.imshow(
                                sector_corr,
                                title="Correlación entre Sectores",
                                color_continuous_scale='RdBu',
                                aspect="auto"
                            )
                            st.plotly_chart(fig_sector_corr, use_container_width=True)
                            
                            # Identificar sectores complementarios
                            complementary_sectors = []
                            for i in range(len(sector_corr.columns)):
                                for j in range(i+1, len(sector_corr.columns)):
                                    corr_val = sector_corr.iloc[i, j]
                                    if abs(corr_val) < 0.3:
                                        complementary_sectors.append((sector_corr.columns[i], sector_corr.columns[j], corr_val))
                            
                            if complementary_sectors:
                                st.success("**Sectores Complementarios** (baja correlación):")
                                for sector1, sector2, corr in complementary_sectors[:3]:
                                    st.write(f"• {sector1} ↔ {sector2}: {corr:.2f}")
                                st.info("Estos sectores proporcionan buena diversificación")

def main():
    # Verificar dependencias
    check_and_install_dependencies()
    
    # Header principal ÚNICO (sin duplicación)
    st.markdown("""
        <div class="main-header fade-in">
            <h1>📊 BCRA Analytics</h1>
            <div class="subtitle">Centro de Análisis Económico • Banco Central de la República Argentina</div>
        </div>
    """, unsafe_allow_html=True)

    # Configuración principal en el sidebar
    st.sidebar.title("⚙️ Configuración")
    
    # Configuración de la API de Gemini
    api_key_input = st.sidebar.text_input(
        "🔑 API Key de Gemini (opcional):",
        type="password",
        value=DEFAULT_GEMINI_API_KEY,
        help="Para análisis avanzado con IA"
    )
    
    if api_key_input:
        st.session_state.GEMINI_API_KEY = api_key_input
        try:
            genai.configure(api_key=api_key_input)
        except:
            pass
    
    # Menú principal de análisis
    st.sidebar.subheader("📊 Tipos de Análisis")
    
    tipo_analisis = st.sidebar.selectbox(
        "Seleccionar tipo de análisis:",
        ["Análisis BCRA", "Optimización de Portafolio", "Análisis Intermarket"],
        help="Elige el tipo de análisis que deseas realizar"
    )
    
    # Configuración del análisis
    with st.sidebar.expander("📊 Configuración del Análisis", expanded=True):
        periodo_dias = st.selectbox(
            "📅 Período de análisis:",
            [30, 60, 90, 180, 365],
            index=1,
            help="Días hacia atrás desde hoy"
        )
        
        mostrar_analisis_tecnico = st.checkbox(
            "🔬 Análisis técnico-estadístico",
            value=True,
            help="Incluye métricas técnicas como VaR, Sharpe, etc."
        )
        
        mostrar_contexto_global = st.checkbox(
            "🌍 Contexto global (intermarket)",
            value=False,
            help="Análisis del contexto macroeconómico global"
        )
    
    # Ejecutar análisis según selección
    if tipo_analisis == "Análisis BCRA":
        mostrar_analisis_principal(periodo_dias, mostrar_analisis_tecnico, mostrar_contexto_global, api_key_input)
    elif tipo_analisis == "Optimización de Portafolio":
        mostrar_optimizacion_portafolio(periodo_dias, api_key_input)
    elif tipo_analisis == "Análisis Intermarket":
        mostrar_analisis_intermarket(periodo_dias, api_key_input)

def mostrar_analisis_principal(periodo_dias, mostrar_analisis_tecnico, mostrar_contexto_global, api_key_input):
    """Muestra el análisis principal integrado"""
    
    # Obtener y mostrar variables BCRA
    with st.spinner('🔄 Cargando variables del BCRA...'):
        df_variables = get_bcra_variables()
    
    if df_variables.empty:
        st.error("❌ No se pudieron cargar las variables del BCRA")
        return
    
    # Mostrar datos disponibles
    st.success(f"✅ {len(df_variables)} variables cargadas del BCRA")
    
    # Selector de variable
    st.subheader("🎯 Seleccionar Variable para Análisis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        variable_seleccionada = st.selectbox(
            "Variable económica a analizar:",
            df_variables['Nombre'].tolist(),
            help="Selecciona la variable económica que quieres analizar"
        )
    
    with col2:
        if st.button("🔄 Actualizar Datos", type="primary"):
            st.cache_data.clear()
            st.rerun()
    
    if variable_seleccionada:
        # Obtener información de la variable seleccionada
        variable_info = df_variables[df_variables['Nombre'] == variable_seleccionada].iloc[0]
        serie_id = variable_info['Serie ID']
        
        if not serie_id:
            st.error("❌ No se pudo obtener el ID de serie para esta variable")
            return
        
        # Calcular fechas
        fecha_hasta = datetime.now().strftime('%Y-%m-%d')
        fecha_desde = (datetime.now() - timedelta(days=periodo_dias)).strftime('%Y-%m-%d')
        
        # Obtener datos históricos
        with st.spinner(f'📈 Obteniendo datos históricos de {variable_seleccionada}...'):
            datos_historicos = get_historical_data(serie_id, fecha_desde, fecha_hasta)
        
        if datos_historicos.empty:
            st.error("❌ No se pudieron obtener datos históricos para esta variable")
            return
        
        # Guardar datos en session state
        st.session_state.bcra_data = datos_historicos
        
        # Mostrar información básica
        st.subheader("📊 Métricas Principales")
        
        col1, col2, col3, col4 = st.columns(4)
        
        current_value, change, change_pct, max_val, min_val = calculate_metrics(datos_historicos)
        
        with col1:
            st.markdown(metric_card(
                "Valor Actual",
                f"{current_value:,.2f}",
                change_pct,
                "chart-line",
                "blue"
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(metric_card(
                "Variación",
                f"{change:+.2f}",
                None,
                "trending-up" if change >= 0 else "trending-down",
                "green" if change >= 0 else "red"
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(metric_card(
                "Máximo",
                f"{max_val:,.2f}",
                None,
                "arrow-up",
                "green"
            ), unsafe_allow_html=True)
        
        with col4:
            st.markdown(metric_card(
                "Mínimo",
                f"{min_val:,.2f}",
                None,
                "arrow-down",
                "red"
            ), unsafe_allow_html=True)
        
        # Gráfico principal
        st.markdown('<div class="section-header"><h2>📈 Evolución Temporal</h2><p>Análisis gráfico de la variable seleccionada</p></div>', unsafe_allow_html=True)
        
        fig, current_value, change, change_pct, max_val, min_val = create_professional_chart(
            datos_historicos, 
            f"Evolución de {variable_seleccionada}", 
            variable_seleccionada
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Análisis técnico-estadístico
        if mostrar_analisis_tecnico:
            st.markdown('<div class="section-header"><h2>🔬 Análisis Técnico-Estadístico</h2><p>Métricas avanzadas de comportamiento económico</p></div>', unsafe_allow_html=True)
            
            analyzer = TechnicalStatisticsAnalyzer(datos_historicos, variable_seleccionada)
            
            # Tabs para organizar el análisis técnico
            tab1, tab2 = st.tabs(["📊 Reporte Estadístico", "🤖 Análisis con IA"])
            
            with tab1:
                with st.spinner("🧮 Calculando métricas técnicas..."):
                    reporte_tecnico = analyzer.generate_technical_report()
                
                st.markdown(reporte_tecnico)
            
            with tab2:
                if api_key_input:
                    if st.button("🧠 Generar Análisis Económico con IA", type="primary"):
                        with st.spinner("🤖 Generando análisis económico con IA..."):
                            reporte_ia = generate_ai_technical_report(analyzer, variable_seleccionada)
                        
                        st.markdown(reporte_ia)
                else:
                    st.info("💡 Configura tu API Key de Gemini en el sidebar para usar análisis con IA")
        
        # Contexto global si está habilitado
        if mostrar_contexto_global:
            crear_analisis_intermarket_integrado()
        
        # Datos tabulares
        with st.expander("📋 Datos Históricos", expanded=False):
            datos_mostrar = datos_historicos.tail(50).sort_values('Fecha', ascending=False)
            st.dataframe(datos_mostrar, use_container_width=True)
            
            # Opción de descarga
            csv = datos_historicos.to_csv(index=False)
            st.download_button(
                label="📥 Descargar datos CSV",
                data=csv,
                file_name=f"{variable_seleccionada}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
    
    # Análisis principal
    mostrar_analisis_principal(periodo_dias, mostrar_analisis_tecnico, mostrar_contexto_global, api_key_input)
