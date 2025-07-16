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
import asyncio
import httpx
import yfinance as yf
from typing import List, Dict, Any, Optional
from collections import defaultdict
import nest_asyncio

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

# Configuración de la API de Gemini
GEMINI_API_KEY = "AIzaSyBFtK05ndkKgo4h0w9gl224Gn94NaWaI6E"
genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(
    page_title="BCRA Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        padding: 3rem 2rem;
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
        font-size: clamp(2rem, 4vw, 3rem);
        font-weight: 800;
        margin: 0;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1.5rem;
        position: relative;
        z-index: 1;
        letter-spacing: -0.025em;
    }
    
    .main-header .subtitle {
        font-size: 1.25rem;
        font-weight: 300;
        text-align: center;
        margin-top: 1rem;
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
""", unsafe_allow_html=True)# Header principal mejorado
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
                    bgcolor='rgba(255, 255, 255, 0.9)',
                    bordercolor='#e2e8f0',
                    borderwidth=1,
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
                bgcolor='rgba(255, 255, 255, 0.9)',
                bordercolor='#e2e8f0',
                borderwidth=1
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
            bordercolor="#3b82f6",
            borderwidth=1,
            font=dict(size=11, family='Manrope', color='#3b82f6')        )
        
        return fig, current_value, change, change_pct, max_val, min_val        
    except Exception as e:
        st.error(f"Error al generar el gráfico: {str(e)}")
        return go.Figure(), 0, 0, 0, 0, 0

def generate_basic_analysis_report(data: pd.DataFrame, variable_name: str, variable_description: str = "") -> str:
    """
    Genera un informe básico de análisis sin usar IA como fallback.
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
    
    try:
        import httpx
    except ImportError:
        missing_deps.append("httpx")
    try:
        import yfinance
    except ImportError:
        missing_deps.append("yfinance")
    
    if missing_deps:
        st.error(f"⚠️ **Dependencias faltantes**: {', '.join(missing_deps)}")
        with st.expander("📦 **Instrucciones de instalación**", expanded=True):
            st.markdown("### Para instalar las dependencias necesarias:")
            st.code(f"pip install {' '.join(missing_deps)}", language="bash")
            st.markdown("### O instalar todas las dependencias:")
            st.code("pip install google-generativeai markdown2 streamlit pandas plotly requests beautifulsoup4 scipy matplotlib numpy httpx yfinance", language="bash")
            st.markdown("### Después de la instalación:")
            st.markdown("1. Reinicie la aplicación")
            st.markdown("2. El análisis IA estará disponible")
            st.warning("⚠️ **Nota**: Sin estas dependencias, el análisis IA y el análisis intermarket no funcionarán, pero el análisis estadístico básico seguirá disponible.")
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
        
        # Tendencia (regresión linear simple)
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

def generate_specific_analysis_link(variable_name: str, metrics: dict, data: pd.DataFrame):
    """
    Genera links y análisis específicos para diferentes aspectos de la variable.
    """
    if not metrics:
        return {}
    
    analyses = {}
    
    # Análisis de Volatilidad
    volatility = metrics.get('volatilidad', 0)
    if volatility < 5:
        volatility_level = "🟢 Baja"
        volatility_desc = "Variable muy estable con fluctuaciones mínimas"
        volatility_recom = "Ideal para pronósticos y planificación a largo plazo"
    elif volatility < 15:
        volatility_level = "🟡 Moderada"
        volatility_desc = "Fluctuaciones normales dentro de rangos esperados"
        volatility_recom = "Monitoreo regular recomendado"
    else:
        volatility_level = "🔴 Alta"
        volatility_desc = "Fluctuaciones significativas que requieren atención"
        volatility_recom = "Seguimiento diario y análisis de causas"
    
    analyses["volatilidad"] = {
        "titulo": f"📊 Análisis de Volatilidad - {variable_name}",
        "nivel": volatility_level,
        "valor": f"{volatility:.2f}%",
        "descripcion": volatility_desc,
        "recomendacion": volatility_recom,
        "link_texto": "Ver análisis detallado de volatilidad →"
    }
    
    # Análisis de Tendencia
    tendencia = metrics.get('tendencia_direccion', 'lateral')
    cambio_pct = metrics.get('cambio_porcentual', 0)
    
    if tendencia == "alcista":
        tendencia_emoji = "📈"
        tendencia_desc = f"Tendencia ascendente con crecimiento del {abs(cambio_pct):.2f}%"
        tendencia_recom = "Momento favorable para decisiones estratégicas"
    elif tendencia == "bajista":
        tendencia_emoji = "📉"
        tendencia_desc = f"Tendencia descendente con declive del {abs(cambio_pct):.2f}%"
        tendencia_recom = "Evaluar causas y considerar medidas correctivas"
    else:
        tendencia_emoji = "➡️"
        tendencia_desc = f"Tendencia lateral con variación del {abs(cambio_pct):.2f}%"
        tendencia_recom = "Período de estabilización o consolidación"
    
    analyses["tendencia"] = {
        "titulo": f"{tendencia_emoji} Análisis de Tendencia - {variable_name}",
        "direccion": tendencia.title(),
        "cambio": f"{cambio_pct:+.2f}%",
        "descripcion": tendencia_desc,
        "recomendacion": tendencia_recom,
        "link_texto": "Ver análisis completo de tendencia →"
    }
    
    # Análisis de Extremos (Soporte y Resistencia)
    soporte = metrics.get('soporte', 0)
    resistencia = metrics.get('resistencia', 0)
    valor_actual = metrics.get('valor_actual', 0)
    
    # Determinar posición actual
    if valor_actual >= resistencia * 0.95:
        posicion = "🔴 Cerca de resistencia"
        posicion_desc = "El valor está cerca del nivel de resistencia técnica"
    elif valor_actual <= soporte * 1.05:
        posicion = "🟢 Cerca de soporte"
        posicion_desc = "El valor está cerca del nivel de soporte técnico"
    else:
        posicion = "🟡 En rango medio"
        posicion_desc = "El valor se encuentra en el rango intermedio"
    
    analyses["extremos"] = {
        "titulo": f"🎯 Análisis de Niveles - {variable_name}",
        "soporte": f"{soporte:,.2f}",
        "resistencia": f"{resistencia:,.2f}",
        "posicion_actual": posicion,
        "descripcion": posicion_desc,
        "recomendacion": f"Vigilar quiebres de {soporte:,.2f} (soporte) y {resistencia:,.2f} (resistencia)",
        "link_texto": "Ver análisis técnico completo →"
    }
    
    # Análisis Histórico
    dias_max = metrics.get('dias_desde_maximo', 0)
    dias_min = metrics.get('dias_desde_minimo', 0)
    periodo = metrics.get('periodo_dias', 0)
    
    if dias_max < 30:
        hist_estado = "🔥 Máximo reciente"
        hist_desc = f"Alcanzó su máximo hace {dias_max} días"
    elif dias_min < 30:
        hist_estado = "❄️ Mínimo reciente"
        hist_desc = f"Tocó su mínimo hace {dias_min} días"
    else:
        hist_estado = "⚖️ Rango intermedio"
        hist_desc = f"Sin extremos recientes en los últimos 30 días"
    
    analyses["historico"] = {
        "titulo": f"📅 Análisis Histórico - {variable_name}",
        "estado": hist_estado,
        "descripcion": hist_desc,
        "periodo_analisis": f"{periodo} días",
        "dias_desde_max": dias_max,
        "dias_desde_min": dias_min,
        "link_texto": "Ver análisis histórico detallado →"
    }
    
    return analyses

def generate_global_analysis_prompt(all_variables_data: dict):
    """
    Genera un prompt optimizado para análisis global de múltiples variables económicas,
    minimizando el uso de tokens mientras maximiza el valor del análisis.
    """
    if not all_variables_data:
        return ""
    
    # Preparar resumen compacto de cada variable
    variables_summary = []
    
    for var_name, data_info in all_variables_data.items():
        if 'data' not in data_info or 'metrics' not in data_info:
            continue
            
        data = data_info['data']
        metrics = data_info['metrics']
        
        if data.empty or not metrics:
            continue
        
        # Extraer información clave compacta
        valor_actual = metrics.get('valor_actual', 0)
        cambio_pct = metrics.get('cambio_porcentual', 0)
        volatilidad = metrics.get('volatilidad', 0)
        tendencia = metrics.get('tendencia_direccion', 'lateral')
        periodo = metrics.get('periodo_dias', 0)
        
        # Formato ultra-compacto para ahorrar tokens
        var_summary = f"{var_name}: Actual={valor_actual:.2f}, Cambio={cambio_pct:+.1f}%, Vol={volatilidad:.1f}%, Tend={tendencia}, Días={periodo}"
        variables_summary.append(var_summary)
    
    if not variables_summary:
        return ""
    
    # Prompt ultra-optimizado
    prompt = f"""Actúa como economista jefe del BCRA. Analiza estas {len(variables_summary)} variables económicas argentinas:

{chr(10).join(variables_summary)}

Genera un informe ejecutivo de máximo 400 palabras con:

1. **PANORAMA GENERAL** (2-3 líneas): Estado macro actual
2. **VARIABLES CRÍTICAS** (3-4 puntos): Qué variables requieren atención inmediata y por qué
3. **CORRELACIONES CLAVE** (2-3 puntos): Relaciones importantes entre variables
4. **RECOMENDACIONES** (3-4 acciones): Medidas prioritarias para autoridades
5. **OUTLOOK** (2 líneas): Perspectiva próximos 30-60 días

Enfócate en insights accionables. Usa lenguaje claro para no economistas."""
    
    return prompt

def query_glossary_ai(term: str, context: str = ""):
    """
    Consulta al glosario usando IA para términos no definidos o para explicaciones contextuales.
    """
    try:
        # Verificar dependencias IA
        import google.generativeai as genai
        
        # Configurar la API de Gemini con configuración ultra-eficiente
        if 'GEMINI_API_KEY' not in st.session_state or not st.session_state.GEMINI_API_KEY:
            return "⚠️ API Key de Gemini no configurada. Configure en la barra lateral para usar consultas IA del glosario."
        
        genai.configure(api_key=st.session_state.GEMINI_API_KEY)
        
        # Prompt optimizado para consultas de glosario
        prompt = f"""Eres un experto economista argentino. Explica de manera simple y clara el término económico: "{term}"

{f"Contexto adicional: {context}" if context else ""}

Responde en máximo 150 palabras con:
1. Definición simple (1 línea)
2. Explicación práctica (2-3 líneas)  
3. Ejemplo argentino actual (1-2 líneas)

Usa lenguaje accesible para no economistas."""

        # Configuración ultra-optimizada
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=200,
                top_p=0.8,
                top_k=20
            )
        )
        
        response = model.generate_content(prompt)
        
        if response and response.text:
            return f"🤖 **Explicación IA**: {response.text}"
        else:
            return "❌ No se pudo generar explicación. Intente nuevamente."
            
    except ImportError:
        return "⚠️ Función IA no disponible. Instale google-generativeai para usar consultas IA."
    except Exception as e:
        return f"❌ Error en consulta IA: {str(e)}"

def format_data_for_prompt(data_clean: pd.DataFrame) -> str:
    """
    Formatea los datos para el prompt de manera eficiente, similar al código TypeScript.
    Reduce la cantidad de datos enviados para ahorrar tokens.
    """
    if len(data_clean) <= 10:
        # Si hay pocos datos, enviar todos
        return '\n'.join([f"{row['Fecha'].strftime('%d/%m/%Y')}: {row['Valor']:.2f}" 
                         for _, row in data_clean.iterrows()])
    else:
        # Si hay muchos datos, enviar solo los primeros 5 y últimos 5
        first_five = '\n'.join([f"{row['Fecha'].strftime('%d/%m/%Y')}: {row['Valor']:.2f}" 
                               for _, row in data_clean.head(5).iterrows()])
        last_five = '\n'.join([f"{row['Fecha'].strftime('%d/%m/%Y')}: {row['Valor']:.2f}" 
                              for _, row in data_clean.tail(5).iterrows()])
        return f"{first_five}\n...\n{last_five}"

def generate_analysis_report_optimized(data: pd.DataFrame, variable_name: str, variable_description: str = "") -> str:
    """
    Genera un informe de análisis optimizado usando la API de Gemini con uso mínimo de tokens.
    Basado en el patrón del código TypeScript proporcionado.
    """
    try:
        if data.empty or 'Valor' not in data.columns or 'Fecha' not in data.columns:
            return generate_basic_analysis_report(data, variable_name, variable_description)
            
        # Preparar y limpiar datos
        data_clean = data.dropna(subset=['Valor', 'Fecha']).copy()
        if len(data_clean) == 0:
            return generate_basic_analysis_report(data, variable_name, variable_description)
        
        data_clean['Valor'] = pd.to_numeric(data_clean['Valor'], errors='coerce')
        data_clean = data_clean.dropna(subset=['Valor'])
        
        if len(data_clean) == 0:
            return generate_basic_analysis_report(data, variable_name, variable_description)
        
        # Calcular estadísticas básicas
        first_value = data_clean['Valor'].iloc[0]
        last_value = data_clean['Valor'].iloc[-1]
        total_change = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0
        
        # Formatear datos para el prompt (reducir tokens)
        data_sample = format_data_for_prompt(data_clean)
        start_date = data_clean['Fecha'].min().strftime('%d/%m/%Y')
        end_date = data_clean['Fecha'].max().strftime('%d/%m/%Y')
        
        # Prompt optimizado y conciso (similar al TypeScript)
        prompt = f"""Actúa como un analista financiero experto para el Banco Central de la República Argentina.
Tu tarea es analizar los datos históricos de la siguiente variable económica y generar un informe conciso y claro en español.

**Variable a Analizar:** {variable_name}
**Período de Datos:** Desde {start_date} hasta {end_date}
**Variación Total:** {total_change:+.2f}%

**Muestra de Datos (Fecha: Valor):**
{data_sample}

**Estructura del Informe:**
1. **Título:** Un título claro y descriptivo.
2. **Resumen de la Tendencia:** Describe en 1-2 frases la tendencia general observada en el período (ej: alcista, bajista, estable, volátil).
3. **Observaciones Clave:** En 2-3 puntos (bullet points), destaca los movimientos o hitos más importantes en los datos (ej: picos, valles, cambios abruptos de tendencia).
4. **Conclusión:** Ofrece una breve conclusión sobre la situación actual de la variable basada en los datos proporcionados.

Por favor, genera el informe siguiendo esta estructura. Sé profesional y objetivo en tu análisis. Máximo 300 palabras."""

        # Intentar generar con IA usando configuración ultra-optimizada
        try:
            import google.generativeai as genai
            
            if 'GEMINI_API_KEY' not in st.session_state or not st.session_state.GEMINI_API_KEY:
                return generate_basic_analysis_report(data, variable_name, variable_description)
            
            genai.configure(api_key=st.session_state.GEMINI_API_KEY)
            
            # Configuración de modelo ultra-eficiente para minimizar costos
            model = genai.GenerativeModel(
                'gemini-1.5-flash',  # Modelo más barato y rápido
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=500,  # Limitar output para ahorrar
                    top_p=0.8,
                    top_k=20
                )
            )
            
            response = model.generate_content(prompt)
            
            if response and response.text:
                return f"## 🧠 Análisis Avanzado - {variable_name}\n\n{response.text}\n\n---\n\n*Análisis generado con IA + datos oficiales del BCRA*"
            else:
                return generate_basic_analysis_report(data, variable_name, variable_description)
                
        except ImportError:
            return generate_basic_analysis_report(data, variable_name, variable_description)
        except Exception as e:
            st.warning(f"⚠️ Error en análisis IA: {str(e)}. Usando análisis estadístico básico.")
            return generate_basic_analysis_report(data, variable_name, variable_description)
            
    except Exception as e:
        return f"## ❌ Error en el análisis\n\nNo se pudo generar el análisis: {str(e)}"

def display_specific_analysis_links(variable_name: str, analyses: dict):
    """
    Muestra los links de análisis específicos en la interfaz.
    """
    if not analyses:
        return
    
    st.markdown("### 🔗 Análisis Específicos Disponibles")
    
    # Crear columnas para organizar los links
    cols = st.columns(2)
    
    with cols[0]:
        if "volatilidad" in analyses:
            vol_data = analyses["volatilidad"]
            with st.expander(f"📊 Volatilidad: {vol_data['nivel']}", expanded=False):
                st.metric("Nivel de Volatilidad", vol_data['valor'])
                st.info(vol_data['descripcion'])
                st.success(f"💡 **Recomendación**: {vol_data['recomendacion']}")
                if st.button("📊 Ver Análisis Detallado de Volatilidad", key="vol_btn"):
                    st.session_state['show_volatility_analysis'] = True
        
        if "extremos" in analyses:
            ext_data = analyses["extremos"]
            with st.expander(f"🎯 Niveles Técnicos: {ext_data['posicion_actual']}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Soporte", ext_data['soporte'])
                with col2:
                    st.metric("Resistencia", ext_data['resistencia'])
                st.info(ext_data['descripcion'])
                st.success(f"💡 **Recomendación**: {ext_data['recomendacion']}")
    
    with cols[1]:
        if "tendencia" in analyses:
            trend_data = analyses["tendencia"]
            with st.expander(f"📈 Tendencia: {trend_data['direccion']}", expanded=False):
                st.metric("Cambio Total", trend_data['cambio'])
                st.info(trend_data['descripcion'])
                st.success(f"💡 **Recomendación**: {trend_data['recomendacion']}")
                if st.button("📈 Ver Análisis Completo de Tendencia", key="trend_btn"):
                    st.session_state['show_trend_analysis'] = True
        
        if "historico" in analyses:
            hist_data = analyses["historico"]
            with st.expander(f"📅 Estado Histórico: {hist_data['estado']}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Días desde máximo", hist_data['dias_desde_max'])
                with col2:
                    st.metric("Días desde mínimo", hist_data['dias_desde_min'])
                st.info(hist_data['descripcion'])

def display_glossary_interface(key_prefix=""):  # <-- Añadir key_prefix para unicidad
    """
    Muestra la interfaz del glosario interactivo.
    """
    st.markdown("### 📚 Glosario Económico Interactivo")
    
    # Obtener glosario predefinido
    glossary = create_glossary()
    
    # Selector de término predefinido
    predefined_terms = list(glossary.keys())
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_term = st.selectbox(
            "Seleccionar término:",
            [""] + predefined_terms,
            help="Seleccione un término económico para ver su explicación",
            key=f"selectbox_glosario_{key_prefix}"
        )
    
    with col2:
        if st.button("🤖 Consulta IA", help="Haga una consulta personalizada al glosario IA", key=f"btn_ia_{key_prefix}"):
            st.session_state[f'show_ai_query_{key_prefix}'] = True
    
    # Mostrar definición del término seleccionado
    if selected_term and selected_term in glossary:
        term_data = glossary[selected_term]
        
        with st.container():
            st.markdown(f"#### �� {selected_term}")
            
            # Definición
            st.markdown("**Definición:**")
            st.info(term_data['definicion'])
            
            # Explicación simple
            st.markdown("**Explicación Simple:**")
            st.success(term_data['explicacion'])
            
            # Ejemplo
            st.markdown("**Ejemplo:**")
            st.warning(term_data['ejemplo'])
    
    # Consulta IA personalizada
    if st.session_state.get(f'show_ai_query_{key_prefix}', False):
        st.markdown("---")
        st.markdown("#### 🤖 Consulta Personalizada al Glosario IA")
        custom_term = st.text_input(
            "¿Qué término económico quiere que le explique?",
            placeholder="Ej: inflación subyacente, carry trade, etc.",
            key=f"custom_term_{key_prefix}"
        )
        context = st.text_area(
            "Contexto adicional (opcional):",
            placeholder="Ej: en el contexto argentino actual, relacionado con...",
            height=100,
            key=f"context_{key_prefix}"
        )
        if st.button("🚀 Consultar IA", type="primary", key=f"consultar_ia_{key_prefix}"):
            if custom_term:
                with st.spinner("🧠 Consultando IA..."):
                    ai_response = query_glossary_ai(custom_term, context)
                    st.markdown(ai_response)
            else:
                st.warning("⚠️ Por favor ingrese un término para consultar.")
        if st.button("❌ Cerrar consulta IA", key=f"cerrar_ia_{key_prefix}"):
            st.session_state[f'show_ai_query_{key_prefix}'] = False
            st.rerun()

def display_integral_analysis():
    st.markdown("""
    <div class="section-header fade-in">
        <h2>🌐 Análisis Integral Intermarket & Global (IA Opcional)</h2>
        <p>Visualización, métricas, análisis estadístico global y sectorial, e informe IA integral (opcional) en un solo flujo profesional.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Sectores económicos y tickers representativos ---
    sectores = {
        "Agro": ["AGRO.BA", "CRESY"],
        "Energía": ["YPF.BA", "PAMP.BA", "TS.BA", "CEPU.BA"],
        "Bancos": ["GGAL.BA", "BMA.BA", "SUPV.BA"],
        "Consumo": ["MELI", "LOMA.BA", "IRSA.BA"],
        "Tecnología": ["MELI", "GLOB"],
        "Industria": ["TXAR.BA", "ALUA.BA", "TGSU2.BA"],
        "Bonos": ["AL30.BA", "GD30.BA", "AL35.BA", "GD35.BA"],
        "Internacional": ["SPY", "QQQ", "GLD", "USO", "DXY", "TLT", "MSCI"],
    }

    st.markdown("""
    <div class="controls-section fade-in">
        <b>El análisis integral incluye todas las variables macro, todos los sectores y activos internacionales relevantes.</b>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📊 Analizar Intermarket & Global", type="primary"):
        with st.spinner("🔄 Recolectando y analizando datos globales, sectoriales y macro..."):
            # --- Recolectar datos de ArgentinaDatos ---
            ad = ArgentinaDatos()
            datos_ad = ad.get_all_economic_data()
            # --- Recolectar datos sectoriales y globales ---
            sector_metrics = {}
            for sector, tickers in sectores.items():
                sector_data = {}
                for ticker in tickers:
                    try:
                        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
                        if not df.empty and 'Close' in df.columns:
                            close = df['Close'].dropna()
                            if len(close) > 1:
                                first = close.iloc[0]
                                last = close.iloc[-1]
                                change = (last - first) / first * 100 if first != 0 else 0
                                volatility = close.pct_change().std() * 100 if len(close) > 2 else 0
                                trend = "Alcista" if last > first else "Bajista" if last < first else "Lateral"
                                sector_data[ticker] = {
                                    "actual": last,
                                    "variacion": change,
                                    "volatilidad": volatility,
                                    "tendencia": trend
                                }
                    except Exception:
                        continue
                if sector_data:
                    sector_metrics[sector] = sector_data
            # --- Mostrar resumen sectorial y global ---
            st.markdown("#### 📊 Resumen Estadístico Global y Sectorial")
            for sector, data in sector_metrics.items():
                st.markdown(f"**{sector}:**")
                for ticker, m in data.items():
                    st.markdown(f"- {ticker}: {m['actual']:.2f} ({m['variacion']:+.2f}%), Volatilidad: {m['volatilidad']:.2f}%, Tendencia: {m['tendencia']}")
            st.markdown("#### 🇦🇷 Variables Macroeconómicas (ArgentinaDatos)")
            for k, v in datos_ad.items():
                st.markdown(f"- **{k}**: {v}")
            # --- Botón para análisis IA intermarket ---
            st.markdown("---")
            st.info("🧠 El informe IA integral solo se genera si lo solicitas. Esto consume créditos de Gemini.")
            if st.button("🧠 Generar Informe IA Integral", type="secondary"):
                with st.spinner("🧠 Generando informe IA integral..."):
                    resumen_ia = []
                    for sector, data in sector_metrics.items():
                        for ticker, m in data.items():
                            resumen_ia.append(f"{sector}-{ticker}: {m['actual']:.2f} ({m['variacion']:+.2f}%), Vol: {m['volatilidad']:.2f}%, Tend: {m['tendencia']}")
                    for k, v in datos_ad.items():
                        resumen_ia.append(f"{k}: {v}")
                    prompt = f"""Actúa como economista jefe argentino. Analiza estos datos sectoriales y macroeconómicos locales e internacionales:
{chr(10).join(resumen_ia)}
1. Diagnóstico macro local e internacional
2. Correlaciones y riesgos sectoriales
3. Recomendaciones para inversores argentinos
4. Detección de incoherencias y oportunidades
Responde en español, con viñetas y máximo 400 palabras."""
                    try:
                        import google.generativeai as genai
                        if 'GEMINI_API_KEY' in st.session_state and st.session_state.GEMINI_API_KEY:
                            genai.configure(api_key=st.session_state.GEMINI_API_KEY)
                            model = genai.GenerativeModel(
                                'gemini-1.5-flash',
                                generation_config=genai.types.GenerationConfig(
                                    temperature=0.4,
                                    max_output_tokens=800,
                                    top_p=0.9,
                                    top_k=30
                                )
                            )
                            response = model.generate_content(prompt)
                            informe = response.text if response and response.text else "No se pudo generar el informe IA."
                        else:
                            informe = "API Key de Gemini no configurada."
                    except Exception as e:
                        informe = f"Error IA: {e}"
                    st.markdown("### 🧠 Informe IA Integral Intermarket & Global")
                    st.markdown(informe)
                    st.download_button(
                        label="📥 Descargar Informe IA",
                        data=informe,
                        file_name=f"informe_ia_integral_{datetime.now().strftime('%Y%m%d')}.md",
                        mime="text/markdown"
                    )
    # --- Glosario como expander al final ---
    st.markdown("---")
    with st.expander("📚 Glosario Económico Interactivo"):
        display_glossary_interface("itm")

def display_individual_analysis():
    st.markdown("""
    <div class="section-header fade-in">
        <h2>🔎 Análisis Individual de Variables y Activos</h2>
        <p>Selecciona una variable macroeconómica o un activo/ticker para ver su análisis detallado, gráfico, métricas e informe.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Listado de variables macro y tickers sectoriales ---
    ad = ArgentinaDatos()
    macro_vars = {
        'Dólar Oficial': ('dolares', 'Dólar Oficial'),
        'Inflación': ('inflacion', 'Inflación'),
        'Tasas': ('tasas', 'Tasas de Interés'),
        'UVA': ('uva', 'UVA'),
        'Riesgo País': ('riesgo_pais', 'Riesgo País'),
    }
    sectores = {
        "Agro": ["AGRO.BA", "CRESY"],
        "Energía": ["YPF.BA", "PAMP.BA", "TS.BA", "CEPU.BA"],
        "Bancos": ["GGAL.BA", "BMA.BA", "SUPV.BA"],
        "Consumo": ["MELI", "LOMA.BA", "IRSA.BA"],
        "Tecnología": ["MELI", "GLOB"],
        "Industria": ["TXAR.BA", "ALUA.BA", "TGSU2.BA"],
        "Bonos": ["AL30.BA", "GD30.BA", "AL35.BA", "GD35.BA"],
        "Internacional": ["SPY", "QQQ", "GLD", "USO", "DXY", "TLT", "MSCI"],
    }
    # Unificar variables y tickers
    opciones = [(k, v[0], v[1]) for k, v in macro_vars.items()]
    for sector, tickers in sectores.items():
        for t in tickers:
            opciones.append((f"{sector} - {t}", t, sector))
    seleccion = st.selectbox(
        "Selecciona una variable o activo:",
        [o[0] for o in opciones],
        help="Elige una variable macro o un ticker para analizar"
    )
    # --- Mostrar análisis según selección ---
    if seleccion:
        # Macro
        macro_keys = [k for k in macro_vars.keys()]
        if seleccion in macro_keys:
            key, nombre = macro_vars[seleccion]
            st.info(f"🔎 Analizando variable macroeconómica: **{nombre}**")
            datos = ad.get_all_economic_data().get(key, [])
            if datos:
                df = pd.DataFrame(datos)
                if 'fecha' in df.columns and 'valor' in df.columns:
                    df['Fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
                    df['Valor'] = pd.to_numeric(df['valor'], errors='coerce')
                    df = df.dropna(subset=['Fecha', 'Valor'])
                    fig, *_ = create_professional_chart(df, nombre, nombre)
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown(generate_analysis_report(df, nombre))
                else:
                    st.warning("No hay datos válidos para esta variable.")
            else:
                st.warning("No se pudo obtener datos para esta variable.")
        else:
            # Es un ticker
            ticker = [o[1] for o in opciones if o[0] == seleccion][0]
            st.info(f"🔎 Analizando activo/ticker: **{ticker}**")
            with st.spinner("Descargando datos del activo..."):
                df = yf.download(ticker, period="6mo", interval="1d", progress=False)
            if not df.empty and 'Close' in df.columns:
                df = df.reset_index()
                df = df.rename(columns={'Date': 'Fecha', 'Close': 'Valor'})
                fig, *_ = create_professional_chart(df, ticker, ticker)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown(generate_analysis_report(df, ticker))
            else:
                st.warning("No se pudo obtener datos para este ticker.")
    # --- Glosario como expander al final ---
    st.markdown("---")
    with st.expander("📚 Glosario Económico Interactivo"):
        display_glossary_interface("individual")

def obtener_datos_completos():
    """Obtiene y almacena todos los datos macro, sectoriales e internacionales al inicio."""
    ad = ArgentinaDatos()
    datos_macro = ad.get_all_economic_data()
    sectores = {
        "Agro": ["AGRO.BA", "CRESY"],
        "Energía": ["YPF.BA", "PAMP.BA", "TS.BA", "CEPU.BA"],
        "Bancos": ["GGAL.BA", "BMA.BA", "SUPV.BA"],
        "Consumo": ["MELI", "LOMA.BA", "IRSA.BA"],
        "Tecnología": ["MELI", "GLOB"],
        "Industria": ["TXAR.BA", "ALUA.BA", "TGSU2.BA"],
        "Bonos": ["AL30.BA", "GD30.BA", "AL35.BA", "GD35.BA"],
        "Internacional": ["SPY", "QQQ", "GLD", "USO", "DXY", "TLT", "MSCI"],
    }
    datos_sectoriales = {}
    for sector, tickers in sectores.items():
        for ticker in tickers:
            try:
                df = yf.download(ticker, period="6mo", interval="1d", progress=False)
                if not df.empty and 'Close' in df.columns:
                    datos_sectoriales[ticker] = df.reset_index()
            except Exception:
                continue
    return datos_macro, datos_sectoriales, sectores

def mostrar_datos_seccionados(datos_macro, datos_sectoriales, sectores):
    st.markdown("## 🇦🇷 Variables Macroeconómicas (ArgentinaDatos)")
    glosario = create_glossary()
    for k, v in datos_macro.items():
        st.markdown(f"### {k.title()}")
        if k.title() in glosario:
            st.info(f"**Concepto:** {glosario[k.title()]['definicion']}")
        df = pd.DataFrame(v)
        st.dataframe(df)
    st.markdown("## 📈 Variables Sectoriales e Internacionales")
    for sector, tickers in sectores.items():
        st.markdown(f"### {sector}")
        for ticker in tickers:
            st.markdown(f"**{ticker}**")
            if ticker in glosario:
                st.info(f"**Concepto:** {glosario[ticker]['definicion']}")
            df = datos_sectoriales.get(ticker)
            if df is not None:
                st.dataframe(df)

# --- Tabs principales ---
tabs = st.tabs(["🌐 Análisis Integral", "🔎 Análisis Individual"])

datos_macro, datos_sectoriales, sectores = obtener_datos_completos()

with tabs[0]:
    st.markdown("# 🌐 Análisis Integral Intermarket & Global")
    mostrar_datos_seccionados(datos_macro, datos_sectoriales, sectores)
    st.markdown("---")
    st.markdown("### 📊 Análisis Estadístico y Comparativo Intermarket")
    # Aquí puedes agregar análisis comparativo, correlaciones, riesgos, etc.
    # Botón para análisis IA global
    if st.button("🧠 Generar Informe IA Integral", type="primary"):
        with st.spinner("Generando informe IA integral..."):
            # Resumir métricas para prompt ultra-eficiente
            resumen_ia = []
            for k, v in datos_macro.items():
                resumen_ia.append(f"{k}: {str(v)[:100]}")
            for ticker, df in datos_sectoriales.items():
                resumen_ia.append(f"{ticker}: Último cierre {df['Close'].iloc[-1]:.2f}")
            prompt = f"""Actúa como economista jefe argentino. Analiza estos datos sectoriales y macroeconómicos:
{chr(10).join(resumen_ia)}
1. Diagnóstico macro y sectorial
2. Correlaciones y riesgos
3. Recomendaciones para inversores
Responde en español, máximo 400 palabras."""
            try:
                import google.generativeai as genai
                if 'GEMINI_API_KEY' in st.session_state and st.session_state.GEMINI_API_KEY:
                    genai.configure(api_key=st.session_state.GEMINI_API_KEY)
                    model = genai.GenerativeModel(
                        'gemini-1.5-flash',
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.4,
                            max_output_tokens=800,
                            top_p=0.9,
                            top_k=30
                        )
                    )
                    response = model.generate_content(prompt)
                    informe = response.text if response and response.text else "No se pudo generar el informe IA."
                else:
                    informe = "API Key de Gemini no configurada."
            except Exception as e:
                informe = f"Error IA: {e}"
            st.markdown("### 🧠 Informe IA Integral Intermarket & Global")
            st.markdown(informe)
            st.download_button(
                label="📥 Descargar Informe IA",
                data=informe,
                file_name=f"informe_ia_integral_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
    st.markdown("---")
    with st.expander("📚 Glosario Económico Interactivo"):
        display_glossary_interface("itm")

with tabs[1]:
    st.markdown("# 🔎 Análisis Individual de Variables y Activos")
    mostrar_datos_seccionados(datos_macro, datos_sectoriales, sectores)
    seleccion = st.selectbox(
        "Selecciona una variable o activo para análisis individual:",
        list(datos_macro.keys()) + list(datos_sectoriales.keys()),
        help="Elige una variable macro o un ticker para análisis individual"
    )
    if seleccion:
        if seleccion in datos_macro:
            df = pd.DataFrame(datos_macro[seleccion])
            st.dataframe(df)
            st.markdown(generate_analysis_report(df, seleccion))
            if st.button(f"🧠 Generar Informe IA de {seleccion}", key=f"ia_{seleccion}"):
                with st.spinner(f"Generando informe IA de {seleccion}..."):
                    prompt = f"Analiza la variable {seleccion} con estos datos: {str(df.head(10))}... Responde en español, máximo 200 palabras."
                    try:
                        import google.generativeai as genai
                        if 'GEMINI_API_KEY' in st.session_state and st.session_state.GEMINI_API_KEY:
                            genai.configure(api_key=st.session_state.GEMINI_API_KEY)
                            model = genai.GenerativeModel(
                                'gemini-1.5-flash',
                                generation_config=genai.types.GenerationConfig(
                                    temperature=0.4,
                                    max_output_tokens=400,
                                    top_p=0.9,
                                    top_k=30
                                )
                            )
                            response = model.generate_content(prompt)
                            informe = response.text if response and response.text else "No se pudo generar el informe IA."
                        else:
                            informe = "API Key de Gemini no configurada."
                    except Exception as e:
                        informe = f"Error IA: {e}"
                    st.markdown(f"### 🧠 Informe IA de {seleccion}")
                    st.markdown(informe)
        else:
            df = datos_sectoriales[seleccion]
            st.dataframe(df)
            st.markdown(generate_analysis_report(df, seleccion))
            if st.button(f"🧠 Generar Informe IA de {seleccion}", key=f"ia_{seleccion}"):
                with st.spinner(f"Generando informe IA de {seleccion}..."):
                    prompt = f"Analiza el activo {seleccion} con estos datos: {str(df.head(10))}... Responde en español, máximo 200 palabras."
                    try:
                        import google.generativeai as genai
                        if 'GEMINI_API_KEY' in st.session_state and st.session_state.GEMINI_API_KEY:
                            genai.configure(api_key=st.session_state.GEMINI_API_KEY)
                            model = genai.GenerativeModel(
                                'gemini-1.5-flash',
                                generation_config=genai.types.GenerationConfig(
                                    temperature=0.4,
                                    max_output_tokens=400,
                                    top_p=0.9,
                                    top_k=30
                                )
                            )
                            response = model.generate_content(prompt)
                            informe = response.text if response and response.text else "No se pudo generar el informe IA."
                        else:
                            informe = "API Key de Gemini no configurada."
                    except Exception as e:
                        informe = f"Error IA: {e}"
                    st.markdown(f"### 🧠 Informe IA de {seleccion}")
                    st.markdown(informe)
    st.markdown("---")
    with st.expander("📚 Glosario Económico Interactivo"):
        display_glossary_interface("individual")

class ArgentinaDatos:
    """
    Main class for fetching and analyzing Argentine economic and financial data.
    """
    def __init__(self, base_url: str = 'https://api.argentinadatos.com'):
        self.base_url = base_url
        self.session = requests.Session()

    def fetch_data(self, endpoint: str) -> List[Dict]:
        """
        Fetch data from Argentina Datos API.
        Args:
            endpoint: API endpoint path
        Returns:
            List of data dictionaries
        """
        try:
            response = self.session.get(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching data from {endpoint}: {e}")
            return []

    def get_dolares(self) -> List[Dict]:
        """Get dólar exchange rates data."""
        return self.fetch_data('/v1/cotizaciones/dolares')

    def get_dolares_candlestick(self) -> Dict:
        """Get dólar candlestick data."""
        return self.fetch_data('/v1/cotizaciones/dolares/candlestick')

    def get_inflacion(self) -> List[Dict]:
        """Get inflation data."""
        return self.fetch_data('/v1/indicadores/inflacion')

    def get_tasas(self) -> List[Dict]:
        """Get interest rates data."""
        return self.fetch_data('/v1/indicadores/tasas')

    def get_uva(self) -> List[Dict]:
        """Get UVA data."""
        return self.fetch_data('/v1/indicadores/uva')

    def get_riesgo_pais(self) -> List[Dict]:
        """Get country risk data."""
        return self.fetch_data('/v1/indicadores/riesgo-pais')

    def get_all_economic_data(self) -> Dict[str, Any]:
        """
        Get all economic and financial data in one call.
        Returns:
            Dictionary with all economic data
        """
        return {
            'dolares': self.get_dolares(),
            'dolares_candlestick': self.get_dolares_candlestick(),
            'inflacion': self.get_inflacion(),
            'tasas': self.get_tasas(),
            'uva': self.get_uva(),
            'riesgo_pais': self.get_riesgo_pais(),
        }

def main():
    """
    Función principal del dashboard BCRA Analytics con todas las mejoras implementadas.
    """
    # Inicializar session state
    if 'GEMINI_API_KEY' not in st.session_state:
        st.session_state.GEMINI_API_KEY = GEMINI_API_KEY if 'GEMINI_API_KEY' in globals() else ""
    if 'show_ai_query' not in st.session_state:
        st.session_state.show_ai_query = False
    # Verificar dependencias
    deps_available = check_and_install_dependencies()
    if not deps_available:
        st.info("ℹ️ **Modo Básico**: Funcionando con análisis estadístico estándar.")
    # Sidebar ultra-moderno (sin tabs)
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
            <h2 style="color: #e2e8f0; font-size: 1.5rem; font-weight: 700; margin: 0; font-family: 'Manrope';">
                📊 BCRA Analytics
            </h2>
            <p style="color: #94a3b8; font-size: 0.9rem; margin: 0.5rem 0 0 0; font-family: 'Manrope';">
                Centro de Análisis Económico
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style="margin: 1.5rem 0; padding: 1rem; background: rgba(59, 130, 246, 0.1); border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.2);">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div style="width: 8px; height: 8px; background: #10b981; border-radius: 50%; animation: pulse 2s infinite;"></div>
                <span style="color: #e2e8f0; font-size: 0.9rem; font-weight: 500;">BCRA API Conectado</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("### 🔍 Explorar Variables")
        search_term = st.text_input(
            "Buscar:",
            placeholder="reservas, inflación, tasa...",
            help="Busca variables por nombre o descripción"
        )
        st.markdown("### ⚙️ Configuración")
        col1, col2 = st.columns(2)
        with col1:
            auto_refresh = st.toggle("Auto-actualizar", value=True)
        with col2:
            if st.button("🔄 Actualizar", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        if deps_available:
            st.markdown("### 🤖 Configuración IA")
            api_key = st.text_input(
                "Gemini API Key (opcional):",
                value=st.session_state.get('GEMINI_API_KEY', ''),
                type="password",
                help="Para habilitar análisis avanzado con IA"
            )
            if api_key != st.session_state.get('GEMINI_API_KEY', ''):
                st.session_state.GEMINI_API_KEY = api_key
                st.success("✅ API Key actualizada")
        st.markdown("---")
        try:
            if deps_available and st.session_state.get('GEMINI_API_KEY'):
                analysis_status = "🟢 Disponible"
                analysis_color = "green"
            else:
                analysis_status = "🟡 Básico"
                analysis_color = "orange"
        except:
            analysis_status = "🔴 Error"
            analysis_color = "red"
        st.markdown(f"""
        <div style="background-color: #1e40af; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            <div style="color: white; font-size: 0.9rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span>🏦 BCRA API</span>
                    <span>🟢 Activo</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>🔬 Análisis IA</span>
                    <span style="color: {analysis_color};">{analysis_status}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="text-xs text-gray-400">
            <p class="font-medium">🚀 BCRA Dashboard v3.0</p>
            <p class="mt-1">🤖 IA optimizada + Análisis estadístico</p>
            <p class="mt-1">Última actualización: {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
            <p class="mt-2">© 2025 - Análisis Económico IA</p>
            <p class="mt-1" style="font-size: 0.7rem;">💡 Análisis disponible 24/7 con o sin cuota IA</p>
        </div>
        """, unsafe_allow_html=True)
    # Llamar solo al flujo único de análisis integral
    display_integral_analysis()

# Ejecutar la aplicación
if __name__ == "__main__":
    main()
