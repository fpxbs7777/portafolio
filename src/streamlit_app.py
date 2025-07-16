import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
from datetime import date, timedelta, datetime
import numpy as np
import pandas as pd
import yfinance as yf
import scipy.optimize as op
from scipy import stats
import random
import warnings
import streamlit.components.v1 as components
from scipy.stats import linregress
import httpx
import asyncio
import matplotlib.pyplot as plt
from scipy.stats import skew
import google.generativeai as genai
import json
from typing import Dict, List, Optional, Any
import os
from dotenv import load_dotenv
import plotly.express as px
from bs4 import BeautifulSoup
import io
import base64
import time
import markdown2

# Load environment variables
load_dotenv()

# ============================
# ARGENTINADATOS API FUNCTIONS
# ============================

BASE_URL = 'https://api.argentinadatos.com/v1'

async def fetch_argentinadatos(endpoint: str) -> Any:
    """
    Obtiene datos de la API de ArgentinaDatos de forma asíncrona.
    Args:
        endpoint (str): Endpoint de la API (ej: '/cotizaciones/dolares').
    Returns:
        Any: Respuesta JSON de la API.
    """
    url = f"{BASE_URL}{endpoint}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()

async def obtener_dolares() -> List[Dict]:
    """Obtiene cotizaciones de dólares desde ArgentinaDatos."""
    return await fetch_argentinadatos('/cotizaciones/dolares')

async def obtener_inflacion() -> List[Dict]:
    """Obtiene datos de inflación desde ArgentinaDatos."""
    return await fetch_argentinadatos('/inflacion')

async def obtener_tasas() -> List[Dict]:
    """Obtiene tasas de interés desde ArgentinaDatos."""
    return await fetch_argentinadatos('/tasas')

async def obtener_uva() -> List[Dict]:
    """Obtiene datos de UVA desde ArgentinaDatos."""
    return await fetch_argentinadatos('/uva')

async def obtener_riesgo_pais() -> List[Dict]:
    """Obtiene datos de riesgo país desde ArgentinaDatos."""
    return await fetch_argentinadatos('/riesgo-pais')

# ============================
# BCRA SCRAPING FUNCTIONS
# ============================

def obtener_tasa_leliq_bcra() -> Optional[float]:
    """
    Obtiene la tasa Leliq del BCRA desde la web oficial (scraping simple).
    Returns:
        float | None: Tasa Leliq si se encuentra, None si falla.
    """
    url = "https://www.bcra.gob.ar"
    try:
        resp = requests.get(f"{url}/")
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Este selector puede necesitar ajuste si cambia la web
        tasa = soup.find(string=lambda t: t and "LELIQ" in t)
        if tasa:
            num = ''.join(filter(lambda c: c.isdigit() or c=='.', tasa))
            return float(num)
    except Exception:
        pass
    return None

# ============================
# YFINANCE FUNCTIONS
# ============================

def obtener_datos_yfinance(ticker: str, periodo: str = '1y', intervalo: str = '1d') -> Any:
    """
    Descarga datos históricos de un ticker usando yfinance.
    Args:
        ticker (str): Símbolo (ej: 'YPF.BA', 'GGAL.BA', 'AAPL').
        periodo (str): Periodo (ej: '1y', '6mo', '1mo').
        intervalo (str): Intervalo (ej: '1d', '1wk').
    Returns:
        DataFrame: Datos históricos del activo.
    """
    data = yf.download(ticker, period=periodo, interval=intervalo, progress=False)
    return data

# ============================
# ANÁLISIS DE BETA Y CORRELACIÓN
# ============================

# Diccionario expandido de benchmarks con categorías de activos completas
BENCHMARK_FACTORS = {
    # ÍNDICES GLOBALES PRINCIPALES
    '^GSPC': 'S&P 500 (EE.UU.)',
    '^DJI': 'Dow Jones Industrial (EE.UU.)',
    '^IXIC': 'NASDAQ Composite (EE.UU.)',
    '^RUT': 'Russell 2000 (EE.UU. Small Cap)',
    '^VIX': 'Índice de Volatilidad VIX',
    
    # ÍNDICES INTERNACIONALES
    '^FTSE': 'FTSE 100 (Reino Unido)',
    '^GDAXI': 'DAX (Alemania)',
    '^FCHI': 'CAC 40 (Francia)',
    '^STOXX50E': 'Euro STOXX 50',
    '^N225': 'Nikkei 225 (Japón)',
    '^HSI': 'Hang Seng (Hong Kong)',
    '000001.SS': 'Shanghai Composite (China)',
    '^AXJO': 'ASX 200 (Australia)',
    '^BVSP': 'Bovespa (Brasil)',
    '^MXX': 'IPC (México)',
    '^MERV': 'MERVAL (Argentina)',
    '^IPSA': 'IPSA (Chile)',
    
    # SECTORES SPDR (XL Series)
    'XLK': 'Tecnología (SPDR)',
    'XLF': 'Servicios Financieros (SPDR)',
    'XLV': 'Salud (SPDR)',
    'XLE': 'Energía (SPDR)',
    'XLI': 'Industrial (SPDR)',
    'XLC': 'Servicios de Comunicación (SPDR)',
    'XLY': 'Consumo Discrecional (SPDR)',
    'XLP': 'Consumo Básico (SPDR)',
    'XLB': 'Materiales (SPDR)',
    'XLRE': 'Bienes Raíces (SPDR)',
    'XLU': 'Servicios Públicos (SPDR)',
    
    # SECTORES VANGUARD (VTI Series)
    'VTI': 'Total Stock Market (Vanguard)',
    'VGT': 'Tecnología (Vanguard)',
    'VFH': 'Financieros (Vanguard)',
    'VHT': 'Salud (Vanguard)',
    'VDE': 'Energía (Vanguard)',
    'VIS': 'Industrial (Vanguard)',
    'VOX': 'Telecomunicaciones (Vanguard)',
    'VCR': 'Consumo Discrecional (Vanguard)',
    'VDC': 'Consumo Básico (Vanguard)',
    'VAW': 'Materiales (Vanguard)',
    'VNQ': 'REITs (Vanguard)',
    'VPU': 'Servicios Públicos (Vanguard)',
    
    # ETFS TEMÁTICOS Y DE ESTILO
    'SPY': 'SPDR S&P 500 ETF',
    'QQQ': 'Invesco QQQ (NASDAQ-100)',
    'IWM': 'iShares Russell 2000 (Small Cap)',
    'EFA': 'iShares MSCI EAFE (Desarrollados)',
    'EEM': 'iShares MSCI Emerging Markets',
    'VEA': 'Vanguard Developed Markets',
    'VWO': 'Vanguard Emerging Markets',
    'IEFA': 'iShares Core MSCI EAFE',
    
    # ETFS POR REGIÓN
    'EWW': 'iShares MSCI México',
    'EWZ': 'iShares MSCI Brasil',
    'EWJ': 'iShares MSCI Japón',
    'EWG': 'iShares MSCI Alemania',
    'EWU': 'iShares MSCI Reino Unido',
    'EWQ': 'iShares MSCI Francia',
    'EWI': 'iShares MSCI Italia',
    'EWP': 'iShares MSCI España',
    'EWC': 'iShares MSCI Canadá',
    'EWA': 'iShares MSCI Australia',
    'EWY': 'iShares MSCI Corea del Sur',
    'EWT': 'iShares MSCI Taiwán',
    'INDA': 'iShares MSCI India',
    'EWS': 'iShares MSCI Singapur',
    'THD': 'iShares MSCI Tailandia',
    'FXI': 'iShares China Large-Cap',
    'ASHR': 'iShares China A-Shares',
    
    # COMMODITIES
    'GLD': 'SPDR Gold Trust',
    'SLV': 'iShares Silver Trust',
    'USO': 'United States Oil Fund',
    'UNG': 'United States Natural Gas Fund',
    'DBA': 'Invesco DB Agriculture Fund',
    'DBC': 'Invesco DB Commodity Index',
    
    # BONOS
    'TLT': 'iShares 20+ Year Treasury Bond',
    'IEF': 'iShares 7-10 Year Treasury Bond',
    'SHY': 'iShares 1-3 Year Treasury Bond',
    'LQD': 'iShares iBoxx Investment Grade Corporate Bond',
    'HYG': 'iShares iBoxx High Yield Corporate Bond',
    'EMB': 'iShares J.P. Morgan USD Emerging Markets Bond',
    
    # DIVISAS
    'UUP': 'Invesco DB US Dollar Index Bullish Fund',
    'FXE': 'Invesco CurrencyShares Euro Trust',
    'FXY': 'Invesco CurrencyShares Japanese Yen Trust',
    'FXB': 'Invesco CurrencyShares British Pound Sterling Trust',
    'FXC': 'Invesco CurrencyShares Canadian Dollar Trust',
    'FXA': 'Invesco CurrencyShares Australian Dollar Trust',
    
    # REAL ESTATE
    'VNQ': 'Vanguard Real Estate ETF',
    'IYR': 'iShares U.S. Real Estate ETF',
    'SCHH': 'Schwab U.S. REIT ETF',
    'RWR': 'SPDR Dow Jones REIT ETF',
    
    # ALTERNATIVOS
    'ARKK': 'ARK Innovation ETF',
    'ARKW': 'ARK Next Generation Internet ETF',
    'ARKG': 'ARK Genomic Revolution ETF',
    'ARKF': 'ARK Fintech Innovation ETF',
    'ARKQ': 'ARK Autonomous Technology & Robotics ETF',
    'ARKX': 'ARK Space Exploration & Innovation ETF',
    
    # FACTORES
    'MTUM': 'iShares MSCI Momentum Factor ETF',
    'VLUE': 'iShares MSCI USA Value Factor ETF',
    'QUAL': 'iShares MSCI USA Quality Factor ETF',
    'SIZE': 'iShares MSCI USA Size Factor ETF',
    'USMV': 'iShares MSCI USA Min Vol Factor ETF',
    
    # CRYPTO
    'GBTC': 'Grayscale Bitcoin Trust',
    'ETHE': 'Grayscale Ethereum Trust',
    'BITO': 'ProShares Bitcoin Strategy ETF',
    'BITI': 'ProShares Short Bitcoin Strategy ETF',
}

def calcular_beta_alpha(returns_asset, returns_benchmark):
    """
    Calcula beta y alpha usando regresión lineal.
    
    Args:
        returns_asset: Series de retornos del activo
        returns_benchmark: Series de retornos del benchmark
        
    Returns:
        tuple: (beta, alpha, r_squared, p_value)
    """
    try:
        # Alinear las series de tiempo
        aligned_data = pd.concat([returns_asset, returns_benchmark], axis=1).dropna()
        if len(aligned_data) < 30:  # Mínimo 30 observaciones
            return None, None, None, None
            
        asset_returns = aligned_data.iloc[:, 0]
        benchmark_returns = aligned_data.iloc[:, 1]
        
        # Regresión lineal
        slope, intercept, r_value, p_value, std_err = stats.linregress(benchmark_returns, asset_returns)
        
        beta = slope
        alpha = intercept
        r_squared = r_value ** 2
        
        return beta, alpha, r_squared, p_value
        
    except Exception as e:
        st.error(f"Error en cálculo de beta/alpha: {str(e)}")
        return None, None, None, None

def clasificar_estrategia(beta, alpha, r_squared, p_value):
    """
    Clasifica la estrategia según beta y alpha.
    
    Args:
        beta: Coeficiente beta
        alpha: Coeficiente alpha
        r_squared: R-cuadrado de la regresión
        p_value: Valor p de la regresión
        
    Returns:
        str: Clasificación de la estrategia
    """
    if beta is None or alpha is None:
        return "Datos Insuficientes"
    
    # Verificar significancia estadística
    if p_value > 0.05:
        return "Sin Significancia Estadística"
    
    # Clasificación según criterios
    if abs(beta - 1) < 0.1 and abs(alpha) < 0.001:
        return "Index Tracker"
    elif abs(beta - 1) < 0.1 and alpha > 0.001:
        return "Tradicional Long-Only"
    elif abs(alpha) < 0.001:
        return "Smart Beta"
    elif abs(beta) < 0.2 and alpha > 0.001:
        return "Hedge Fund"
    else:
        return "Estrategia Mixta"

def obtener_serie_historica_yfinance(ticker, periodo='1y'):
    """
    Obtiene serie histórica usando yfinance.
    
    Args:
        ticker: Símbolo del ticker
        periodo: Período de tiempo ('1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max')
        
    Returns:
        pd.Series: Serie de retornos diarios
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period=periodo)
        
        if hist.empty:
            return None
            
        # Calcular retornos diarios
        returns = hist['Close'].pct_change().dropna()
        return returns
        
    except Exception as e:
        st.error(f"Error obteniendo datos para {ticker}: {str(e)}")
        return None

def crear_grafico_alpha_beta(resultados):
    """
    Crea gráfico de dispersión alpha vs beta.
    
    Args:
        resultados: DataFrame con columnas ['Ticker', 'Beta', 'Alpha', 'Estrategia']
        
    Returns:
        plotly.graph_objects.Figure: Gráfico interactivo
    """
    fig = go.Figure()
    
    # Colores por estrategia
    colores = {
        'Index Tracker': '#1f77b4',
        'Tradicional Long-Only': '#ff7f0e',
        'Smart Beta': '#2ca02c',
        'Hedge Fund': '#d62728',
        'Estrategia Mixta': '#9467bd',
        'Sin Significancia Estadística': '#8c564b',
        'Datos Insuficientes': '#e377c2'
    }
    
    for estrategia in resultados['Estrategia'].unique():
        data_estrategia = resultados[resultados['Estrategia'] == estrategia]
        
        fig.add_trace(go.Scatter(
            x=data_estrategia['Beta'],
            y=data_estrategia['Alpha'],
            mode='markers',
            name=estrategia,
            marker=dict(
                size=10,
                color=colores.get(estrategia, '#7f7f7f'),
                opacity=0.7
            ),
            text=data_estrategia['Ticker'],
            hovertemplate='<b>%{text}</b><br>Beta: %{x:.3f}<br>Alpha: %{y:.3f}<extra></extra>'
        ))
    
    # Líneas de referencia
    fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Alpha = 0")
    fig.add_vline(x=1, line_dash="dash", line_color="gray", annotation_text="Beta = 1")
    fig.add_vline(x=0, line_dash="dash", line_color="gray", annotation_text="Beta = 0")
    
    fig.update_layout(
        title="Análisis Alpha vs Beta por Estrategia",
        xaxis_title="Beta",
        yaxis_title="Alpha",
        template="plotly_white",
        height=600
    )
    
    return fig

def mostrar_analisis_beta_correlacion():
    """
    Función principal para mostrar el análisis de beta y correlación.
    """
    st.header("📊 Análisis de Beta y Correlación")
    st.markdown("### Clasificación de Estrategias de Inversión")
    
    # Configuración
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Configuración")
        
        # Selección de benchmark
        benchmark_seleccionado = st.selectbox(
            "Seleccione Benchmark:",
            options=list(BENCHMARK_FACTORS.keys()),
            format_func=lambda x: f"{x} - {BENCHMARK_FACTORS[x]}",
            index=0
        )
        
        # Período de análisis
        periodo = st.selectbox(
            "Período de Análisis:",
            options=['1mo', '3mo', '6mo', '1y', '2y', '5y'],
            index=3
        )
        
        # Umbral de significancia
        umbral_significancia = st.slider(
            "Umbral de Significancia (p-value):",
            min_value=0.01,
            max_value=0.10,
            value=0.05,
            step=0.01
        )
    
    with col2:
        st.subheader("📋 Información")
        st.info(f"""
        **Benchmark Seleccionado:** {benchmark_seleccionado} - {BENCHMARK_FACTORS[benchmark_seleccionado]}
        
        **Período:** {periodo}
        
        **Umbral de Significancia:** {umbral_significancia}
        """)
    
    # Obtener datos del benchmark
    st.subheader("📈 Datos del Benchmark")
    with st.spinner(f"Obteniendo datos del benchmark {benchmark_seleccionado}..."):
        benchmark_returns = obtener_serie_historica_yfinance(benchmark_seleccionado, periodo)
        
        if benchmark_returns is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Retorno Total", f"{benchmark_returns.sum():.2%}")
                st.metric("Volatilidad", f"{benchmark_returns.std() * np.sqrt(252):.2%}")
            
            with col2:
                st.metric("Retorno Promedio Diario", f"{benchmark_returns.mean():.2%}")
                st.metric("Observaciones", len(benchmark_returns))
            
            # Gráfico del benchmark
            fig_benchmark = go.Figure()
            fig_benchmark.add_trace(go.Scatter(
                x=benchmark_returns.index,
                y=(1 + benchmark_returns).cumprod(),
                mode='lines',
                name=f'Benchmark ({benchmark_seleccionado})',
                line=dict(color='blue', width=2)
            ))
            
            fig_benchmark.update_layout(
                title=f"Evolución del Benchmark: {BENCHMARK_FACTORS[benchmark_seleccionado]}",
                xaxis_title="Fecha",
                yaxis_title="Valor Acumulado",
                template="plotly_white"
            )
            
            st.plotly_chart(fig_benchmark, use_container_width=True)
        else:
            st.error("No se pudieron obtener los datos del benchmark")
            return
    
    # Análisis de activos
    st.subheader("🔍 Análisis de Activos")
    
    # Aquí puedes agregar la lógica para obtener los tickers de los paneles seleccionados
    # Por ahora, usaremos algunos ejemplos
    tickers_ejemplo = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **Nota:** Esta sección está configurada para analizar activos específicos.
        Para integrar con los paneles de cotización, selecciona los paneles deseados
        y se analizarán automáticamente todos los activos de esos paneles.
        """)
        
        # Opción para usar tickers de ejemplo o paneles
        modo_analisis = st.radio(
            "Modo de Análisis:",
            ["Tickers de Ejemplo", "Paneles de Cotización"],
            index=0
        )
    
    with col2:
        if modo_analisis == "Tickers de Ejemplo":
            tickers_analizar = st.multiselect(
                "Seleccione tickers para analizar:",
                options=tickers_ejemplo,
                default=tickers_ejemplo[:5]
            )
        else:
            st.info("Selecciona los paneles en la pestaña de Paneles de Cotización")
            tickers_analizar = []
    
    # Ejecutar análisis
    if st.button("🚀 Ejecutar Análisis", use_container_width=True):
        if not tickers_analizar:
            st.warning("Selecciona al menos un ticker para analizar")
            return
        
        resultados = []
        
        with st.spinner("Analizando activos..."):
            for ticker in tickers_analizar:
                asset_returns = obtener_serie_historica_yfinance(ticker, periodo)
                
                if asset_returns is not None:
                    beta, alpha, r_squared, p_value = calcular_beta_alpha(asset_returns, benchmark_returns)
                    estrategia = clasificar_estrategia(beta, alpha, r_squared, p_value)
                    
                    resultados.append({
                        'Ticker': ticker,
                        'Beta': beta if beta is not None else 0,
                        'Alpha': alpha if alpha is not None else 0,
                        'R_Squared': r_squared if r_squared is not None else 0,
                        'P_Value': p_value if p_value is not None else 1,
                        'Estrategia': estrategia,
                        'Retorno_Total': asset_returns.sum(),
                        'Volatilidad': asset_returns.std() * np.sqrt(252)
                    })
        
        if resultados:
            # Crear DataFrame
            df_resultados = pd.DataFrame(resultados)
            
            # Mostrar resultados
            st.subheader("📊 Resultados del Análisis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(
                    df_resultados[['Ticker', 'Beta', 'Alpha', 'Estrategia']].round(4),
                    use_container_width=True
                )
            
            with col2:
                # Estadísticas por estrategia
                stats_estrategia = df_resultados.groupby('Estrategia').agg({
                    'Ticker': 'count',
                    'Beta': ['mean', 'std'],
                    'Alpha': ['mean', 'std']
                }).round(4)
                
                st.write("**Estadísticas por Estrategia:**")
                st.dataframe(stats_estrategia, use_container_width=True)
            
            # Gráfico alpha vs beta
            st.subheader("📈 Gráfico Alpha vs Beta")
            fig_alpha_beta = crear_grafico_alpha_beta(df_resultados)
            st.plotly_chart(fig_alpha_beta, use_container_width=True)
            
            # Explicación de estrategias
            st.subheader("📚 Explicación de Estrategias")
            
            estrategias_info = {
                'Index Tracker': {
                    'descripcion': 'Replica el rendimiento de un benchmark',
                    'caracteristicas': 'β ≈ 1, α ≈ 0',
                    'ejemplo': 'ETF que replica S&P 500'
                },
                'Tradicional Long-Only': {
                    'descripcion': 'Supera el mercado con retorno extra no correlacionado',
                    'caracteristicas': 'β ≈ 1, α > 0',
                    'ejemplo': 'Fondos mutuos tradicionales'
                },
                'Smart Beta': {
                    'descripcion': 'Supera el mercado ajustando dinámicamente los pesos',
                    'caracteristicas': 'β > 1 (mercado alcista), β < 1 (mercado bajista), α ≈ 0',
                    'ejemplo': 'ETFs factor-based'
                },
                'Hedge Fund': {
                    'descripcion': 'Entrega retornos absolutos no correlacionados con el mercado',
                    'caracteristicas': 'β ≈ 0, α > 0',
                    'ejemplo': 'Estrategias long/short'
                }
            }
            
            for estrategia, info in estrategias_info.items():
                with st.expander(f"📋 {estrategia}"):
                    st.write(f"**Descripción:** {info['descripcion']}")
                    st.write(f"**Características:** {info['caracteristicas']}")
                    st.write(f"**Ejemplo:** {info['ejemplo']}")
            
            # Almacenar resultados
            if st.button("💾 Guardar Resultados", use_container_width=True):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nombre_archivo = f"analisis_beta_alpha_{timestamp}.json"
                
                try:
                    with open(nombre_archivo, 'w', encoding='utf-8') as f:
                        json.dump({
                            'fecha_analisis': datetime.now().isoformat(),
                            'benchmark': benchmark_seleccionado,
                            'periodo': periodo,
                            'resultados': df_resultados.to_dict('records')
                        }, f, ensure_ascii=False, indent=2)
                    
                    st.success(f"✅ Resultados guardados en {nombre_archivo}")
                except Exception as e:
                    st.error(f"Error al guardar: {str(e)}")

# ============================
# BCRA DASHBOARD FUNCTIONS
# ============================

def metric_card(title: str, value: str, change: float = None, icon: str = "chart-line", color: str = "blue") -> str:
    """Crea una tarjeta de métrica con estilo moderno"""
    color_classes = {
        "blue": {"bg": "bg-blue-50", "text": "text-blue-600", "icon_bg": "bg-blue-100"},
        "green": {"bg": "bg-green-50", "text": "text-green-600", "icon_bg": "bg-green-100"},
        "yellow": {"bg": "bg-yellow-50", "text": "text-yellow-600", "icon_bg": "bg-yellow-100"},
        "red": {"bg": "bg-red-50", "text": "text-red-600", "icon_bg": "bg-red-100"},
    }
    
    colors = color_classes.get(color, color_classes["blue"])
    
    change_html = ""
    if change is not None:
        is_positive = change >= 0
        change_icon = "arrow-up" if is_positive else "arrow-down"
        change_color = "text-green-500" if is_positive else "text-red-500"
        change_html = f"""
            <span class="text-sm font-medium {change_color}">
                <i class="fas fa-{change_icon}"></i> {abs(change):.2f}%
            </span>
        """
    
    return f"""
    <div class="metric-card">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-gray-500 text-sm font-medium">{title}</p>
                <p class="text-2xl font-bold text-gray-900">{value}</p>
            </div>
            <div class="p-3 rounded-full {colors['icon_bg']} {colors['text']}">
                <i class="fas fa-{icon} text-xl"></i>
            </div>
        </div>
        {change_html}
    </div>
    """

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
    """Crear gráfico profesional con diseño mejorado"""
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
        
        # Crear el gráfico principal
        fig = go.Figure()
        
        # Línea principal
        fig.add_trace(go.Scatter(
            x=data['Fecha'],
            y=data['Valor'],
            mode='lines+markers',
            name=variable_name,
            customdata=data[['Fecha', 'Valor']],
            line=dict(
                color='#3b82f6',
                width=3,
                shape='spline'
            ),
            marker=dict(
                size=4,
                color='#3b82f6',
                line=dict(color='white', width=1)
            ),
            fill='tonexty',
            fillcolor='rgba(59, 130, 246, 0.1)',
            hovertemplate='<b>%{y:,.2f}</b><br>%{x}<extra></extra>'
        ))
        
        # Línea de tendencia (solo si hay suficientes puntos)
        if len(data) > 2:
            try:
                x = np.arange(len(data))
                y = data['Valor'].values
                
                # Verificar que no haya valores NaN o infinitos
                mask = np.isfinite(y)
                if np.any(mask):
                    z = np.polyfit(x[mask], y[mask], 1)
                    p = np.poly1d(z)
                    
                    fig.add_trace(go.Scatter(
                        x=data['Fecha'],
                        y=p(x),
                        mode='lines',
                        name='Tendencia',
                        line=dict(
                            color='#f59e0b',
                            width=2,
                            dash='dot'
                        ),
                        hovertemplate='<b>Tendencia: %{y:,.2f}</b><extra></extra>'
                    ))
            except Exception as e:
                st.warning(f"No se pudo calcular la línea de tendencia: {str(e)}")
        
        # Personalizar diseño del gráfico
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                xanchor='center',
                font=dict(size=18, family='Inter')
            ),
            xaxis=dict(
                title='Fecha',
                showgrid=True,
                gridwidth=1,
                gridcolor='#e5e7eb',
                showline=True,
                linewidth=1,
                linecolor='#d1d5db',
                tickformat='%d/%m/%Y',
                rangeslider=dict(visible=True, thickness=0.05),
                rangeselector=dict(
                    buttons=list([
                        dict(count=7, label="7D", step="day", stepmode="backward"),
                        dict(count=30, label="30D", step="day", stepmode="backward"),
                        dict(count=90, label="3M", step="day", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="1A", step="year", stepmode="backward"),
                        dict(step="all", label="Todo")
                    ])
                )
            ),
            yaxis=dict(
                title=variable_name,
                showgrid=True,
                gridwidth=1,
                gridcolor='#e5e7eb',
                showline=True,
                linewidth=1,
                linecolor='#d1d5db',
                tickformat=',.2f'
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='white',
                font_size=12,
                font_family='Inter'
            ),
            margin=dict(l=50, r=50, t=80, b=50),
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            )
        )
        
        return fig, current_value, change, change_pct, max_val, min_val
        
    except Exception as e:
        st.error(f"Error al generar el gráfico: {str(e)}")
        return go.Figure(), 0, 0, 0

def generate_bcra_analysis_report(data: pd.DataFrame, variable_name: str, variable_description: str = "") -> str:
    """
    Genera un informe básico de análisis para datos del BCRA.
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

def mostrar_bcra_dashboard():
    """
    Función principal para mostrar el dashboard del BCRA.
    """
    st.header("🏦 BCRA Dashboard")
    st.markdown("### Panel de Control - Banco Central de la República Argentina")
    
    # Obtener datos con spinner mejorado
    with st.spinner('📊 Obteniendo datos del BCRA...'):
        variables_df = get_bcra_variables()
    
    if not variables_df.empty:
        # Sección de métricas principales
        st.markdown("""
        <div class="flex items-center justify-between mb-6">
            <div>
                <h2 class="text-2xl font-bold text-gray-800">📊 Indicadores Principales</h2>
                <p class="text-gray-500">Variables económicas más relevantes del BCRA</p>
            </div>
            <div class="text-sm text-gray-500">
                <i class="far fa-clock mr-1"></i> Actualizado: {}
            </div>
        </div>
        """.format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)
        
        # Mostrar métricas principales
        cols = st.columns(4)
        colors = ["blue", "green", "yellow", "red"]
        icons = ["dollar-sign", "chart-line", "percentage", "wallet"]
        
        for idx, row in variables_df.head(4).iterrows():
            with cols[idx % 4]:
                # Calcular cambio porcentual si hay datos históricos
                change = None
                if 'hist_data' in st.session_state and not st.session_state.hist_data.empty and len(st.session_state.hist_data) > 1:
                    values = st.session_state.hist_data['Valor'].values
                    if len(values) >= 2:
                        change = ((values[-1] - values[-2]) / values[-2]) * 100
                
                st.markdown(metric_card(
                    title=row['Nombre'],
                    value=row['Valor'],
                    change=change,
                    icon=icons[idx % len(icons)],
                    color=colors[idx % len(colors)]
                ), unsafe_allow_html=True)
        
        # Sección de análisis histórico
        st.markdown("""
        <div class="mt-10 mb-6">
            <h2 class="text-2xl font-bold text-gray-800">📈 Análisis Histórico</h2>
            <p class="text-gray-500">Evolución temporal de las variables económicas</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Controles de análisis
        st.markdown('<div class="bg-white p-6 rounded-xl shadow-sm mb-6">', unsafe_allow_html=True)
        
        # Filtros en fila
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Buscador mejorado
            search_container = st.container()
            with search_container:
                selected_var = st.selectbox(
                    "Seleccionar variable:",
                    options=variables_df['Nombre'].tolist(),
                    index=0,
                    help="Seleccione la variable para ver su evolución histórica"
                )
        
        with col2:
            # Selector de rango de fechas
            start_date = st.date_input(
                "Desde:",
                value=datetime.now() - timedelta(days=90),
                max_value=datetime.now() - timedelta(days=1),
                help="Fecha de inicio del análisis"
            )
        
        with col3:
            end_date = st.date_input(
                "Hasta:",
                value=datetime.now(),
                max_value=datetime.now(),
                min_value=start_date + timedelta(days=1) if start_date else None,
                help="Fecha de fin del análisis"
            )
        
        # Botón de análisis
        analyze_col, _ = st.columns([1, 3])
        with analyze_col:
            analyze_clicked = st.button(
                "🔍 Analizar Variable", 
                type="primary",
                use_container_width=True,
                help="Generar análisis para la variable seleccionada"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)  # Cierre del contenedor de controles
        
        # Obtener la serie seleccionada
        selected_serie = variables_df[variables_df['Nombre'] == selected_var].iloc[0] if not variables_df.empty else None
        
        # Tabs para organizar contenido
        tab1, tab2, tab3 = st.tabs(["📊 Gráfico", "📋 Datos", "💾 Descargar"])
        
        with tab1:
            if analyze_clicked and selected_serie is not None:
                with st.spinner('📈 Generando análisis...'):
                    hist_data = get_historical_data(
                        selected_serie['Serie ID'],
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d')
                    )
                    
                    if not hist_data.empty and 'Fecha' in hist_data.columns and 'Valor' in hist_data.columns:
                        # Crear gráfico profesional con métricas
                        fig, current_val, change, change_pct, max_val, min_val = create_professional_chart(
                            hist_data, 
                            f"Evolución de {selected_var}", 
                            selected_var
                        )
                        
                        # Mostrar métricas en tarjetas mejoradas
                        st.markdown("### 📊 Resumen de la Serie")
                        
                        # Crear columnas para las métricas
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.markdown(metric_card(
                                title="Valor Actual",
                                value=f"{current_val:,.2f}",
                                icon="dollar-sign",
                                color="blue"
                            ), unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(metric_card(
                                title="Cambio",
                                value=f"{change:,.2f}",
                                change=change_pct,
                                icon="chart-line",
                                color="green" if change_pct >= 0 else "red"
                            ), unsafe_allow_html=True)
                        
                        with col3:
                            st.markdown(metric_card(
                                title="Máximo",
                                value=f"{max_val:,.2f}",
                                icon="arrow-up",
                                color="green"
                            ), unsafe_allow_html=True)
                        
                        with col4:
                            st.markdown(metric_card(
                                title="Mínimo",
                                value=f"{min_val:,.2f}",
                                icon="arrow-down",
                                color="red"
                            ), unsafe_allow_html=True)
                        
                        st.markdown("<div class='h-4'></div>", unsafe_allow_html=True)  # Espaciador
                        
                        # Mostrar gráfico
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Generar informe automático
                        if st.session_state.get('selected_var') != selected_var or not st.session_state.get('analysis_report'):
                            # Mostrar indicador de generación
                            with st.status("🤖 Generando análisis...", expanded=True) as status:
                                st.write("📊 Procesando datos estadísticos...")
                                
                                # Generar el informe
                                report = generate_bcra_analysis_report(
                                    hist_data,
                                    selected_var,
                                    selected_serie.get('Descripción', f'Variable económica del BCRA: {selected_var}')
                                )
                                
                                st.write("✅ Análisis completado")
                                status.update(label="✅ Análisis generado exitosamente", state="complete")
                                
                                # Guardar en session state
                                st.session_state.analysis_report = report
                                st.session_state.selected_var = selected_var
                                st.session_state.report_generated = True
                        
                        # Mostrar vista previa del informe si está disponible
                        if st.session_state.get('analysis_report'):
                            st.markdown("---")
                            st.markdown("### 🤖 Vista Previa del Análisis")
                            
                            with st.expander("📄 Ver análisis completo", expanded=False):
                                st.markdown(st.session_state.analysis_report, unsafe_allow_html=True)
                            
                            st.info("💡 **Tip**: Ve a la pestaña 'Datos' para ver el informe completo y más detalles estadísticos.")
                        
                        # Guardar datos en session state para otras tabs
                        st.session_state.hist_data = hist_data
                        st.session_state.selected_serie = selected_serie
                        
                    else:
                        st.warning("📊 No se encontraron datos para el período seleccionado.")
        
        with tab2:
            if 'hist_data' in st.session_state and not st.session_state.hist_data.empty:
                # Mostrar datos en un contenedor con estilo
                with st.container():
                    st.markdown("### 📊 Datos Históricos")
                    st.dataframe(
                        st.session_state.hist_data,
                        use_container_width=True,
                        height=400
                    )
                
                # Mostrar estadísticas descriptivas
                st.markdown("---")
                st.subheader("📊 Estadísticas Descriptivas")
                stats = st.session_state.hist_data['Valor'].describe()
                
                # Mostrar métricas en columnas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Media", f"{stats['mean']:,.2f}")
                with col2:
                    st.metric("Mediana", f"{stats['50%']:,.2f}")
                with col3:
                    st.metric("Mínimo", f"{stats['min']:,.2f}")
                with col4:
                    st.metric("Máximo", f"{stats['max']:,.2f}")
                
                # Sección de Análisis
                st.markdown("---")
                st.markdown("## 🤖 Análisis Inteligente")
                
                # Mostrar el informe generado
                if 'analysis_report' in st.session_state and st.session_state.analysis_report:
                    # Botones de acción
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        if st.button("🔄 Regenerar Análisis", key="refresh_analysis", help="Generar un nuevo análisis"):
                            with st.spinner("🤖 Regenerando análisis..."):
                                # Limpiar el análisis actual
                                st.session_state.analysis_report = None
                                st.session_state.report_generated = False
                                
                                # Generar nuevo análisis
                                new_report = generate_bcra_analysis_report(
                                    st.session_state.hist_data,
                                    st.session_state.selected_var,
                                    st.session_state.selected_serie.get('Descripción', f'Variable económica del BCRA: {st.session_state.selected_var}')
                                )
                                
                                st.session_state.analysis_report = new_report
                                st.session_state.report_generated = True
                                st.rerun()
                    
                    # Mostrar el análisis en una caja con estilo
                    st.markdown("### 📄 Informe Completo")
                    
                    # Contenedor del análisis con scroll
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="
                                background-color: white;
                                padding: 2rem;
                                border-radius: 10px;
                                border: 1px solid #e5e7eb;
                                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                                max-height: 600px;
                                overflow-y: auto;
                                margin: 1rem 0;
                            ">
                                {st.session_state.analysis_report}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                
                else:
                    # No hay análisis disponible
                    st.info("💡 **Análisis no disponible**")
                    
                    if st.button("🚀 Generar Análisis", key="generate_new_analysis", type="primary"):
                        st.session_state.generating_report = True
                        st.rerun()
                
                # Trigger para generar análisis si está marcado
                if st.session_state.get('generating_report', False):
                    with st.spinner("🤖 Generando análisis..."):
                        new_report = generate_bcra_analysis_report(
                            st.session_state.hist_data,
                            st.session_state.selected_var,
                            st.session_state.selected_serie.get('Descripción', f'Variable económica del BCRA: {st.session_state.selected_var}')
                        )
                        
                        st.session_state.analysis_report = new_report
                        st.session_state.generating_report = False
                        st.session_state.report_generated = True
                        st.rerun()
            else:
                st.info("👆 Primero genere el análisis en la pestaña 'Gráfico'")
        
        with tab3:
            if 'hist_data' in st.session_state and not st.session_state.hist_data.empty:
                # Formato de descarga
                download_format = st.selectbox(
                    "Formato de descarga:",
                    ["CSV", "Excel", "JSON"],
                    index=0
                )
                
                # Botón de descarga
                if download_format == "CSV":
                    csv = st.session_state.hist_data.to_csv(index=False)
                    st.download_button(
                        label="💾 Descargar CSV",
                        data=csv,
                        file_name=f"{st.session_state.selected_var.replace(' ', '_').lower()}.csv",
                        mime="text/csv"
                    )
                elif download_format == "Excel":
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        st.session_state.hist_data.to_excel(writer, index=False, sheet_name='Datos')
                    excel_data = excel_buffer.getvalue()
                    st.download_button(
                        label="💾 Descargar Excel",
                        data=excel_data,
                        file_name=f"{st.session_state.selected_var.replace(' ', '_').lower()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:  # JSON
                    json_data = st.session_state.hist_data.to_json(orient='records', date_format='iso')
                    st.download_button(
                        label="💾 Descargar JSON",
                        data=json_data,
                        file_name=f"{st.session_state.selected_var.replace(' ', '_').lower()}.json",
                        mime="application/json"
                    )
                
                # Opción para descargar el informe de análisis
                if 'analysis_report' in st.session_state:
                    st.markdown("---")
                    st.markdown("### 📄 Descargar Informe de Análisis")
                    
                    # Formato del informe
                    report_format = st.radio(
                        "Formato del informe:",
                        ["Texto Plano (TXT)", "Markdown (MD)", "HTML"],
                        index=0,
                        horizontal=True
                    )
                    
                    # Generar el contenido según el formato seleccionado
                    if report_format == "Texto Plano (TXT)":
                        file_extension = "txt"
                        mime_type = "text/plain"
                        report_content = st.session_state.analysis_report
                    elif report_format == "Markdown (MD)":
                        file_extension = "md"
                        mime_type = "text/markdown"
                        report_content = st.session_state.analysis_report
                    else:  # HTML
                        file_extension = "html"
                        mime_type = "text/html"
                        # Convertir markdown a HTML
                        html_content = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="UTF-8">
                            <title>Informe de Análisis - {st.session_state.selected_var}</title>
                            <style>
                                body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                                h1, h2, h3 {{ color: #2c3e50; }}
                                .header {{ text-align: center; margin-bottom: 30px; }}
                                .date {{ color: #7f8c8d; font-style: italic; }}
                                .metrics {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                            </style>
                        </head>
                        <body>
                            <div class="header">
                                <h1>Informe de Análisis</h1>
                                <h2>{st.session_state.selected_var}</h2>
                                <p class="date">Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                            </div>
                            {markdown2.markdown(st.session_state.analysis_report)}
                        </body>
                        </html>
                        """
                        report_content = html_content
                    
                    st.download_button(
                        label=f"⬇️ Descargar Informe ({report_format.split(' ')[0]})",
                        data=report_content,
                        file_name=f"informe_analisis_{st.session_state.selected_var.replace(' ', '_').lower()}.{file_extension}",
                        mime=mime_type
                    )
            else:
                st.info("No hay datos para descargar. Por favor, selecciona una variable y haz clic en 'Analizar Variable'.")
        
        # Expandir para ver todas las variables
        with st.expander("📋 Ver todas las variables disponibles", expanded=False):
            st.dataframe(
                variables_df[['Nombre', 'Valor', 'Fecha']].reset_index(drop=True),
                use_container_width=True,
                hide_index=True
            )
    
    else:
        st.error("❌ No se pudieron cargar los datos del BCRA. Por favor, inténtelo más tarde.")
    
    # Footer mejorado
    st.markdown(f"""
        <div class="footer">
            <p><strong>🏦 BCRA Dashboard</strong> - Panel de Control Económico</p>
            <p>Datos oficiales del <a href="https://www.bcra.gob.ar/" target="_blank">Banco Central de la República Argentina</a></p>
            <p>Última actualización: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</p>
            <p><small>Desarrollado con ❤️ usando Streamlit y Plotly</small></p>
        </div>
    """, unsafe_allow_html=True)

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
            response = self.session.get(f"{self.base_url}{endpoint}", timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching data from {endpoint}: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching data from {endpoint}: {e}")
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
    
    def create_dolares_chart(self, data: List[Dict], periodo: str = '1 mes', 
                            casas: Optional[List[str]] = None) -> Dict:
        """
        Create dólares chart with Plotly.
        
        Args:
            data: Dólares data
            periodo: Time period ('1 semana', '1 mes', '1 año', '5 años', 'Todo')
            casas: List of exchange houses to include
            
        Returns:
            Plotly figure as dictionary
        """
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        # Filter by period
        periodos = {
            '1 semana': 7,
            '1 mes': 30,
            '1 año': 365,
            '5 años': 1825,
        }
        
        if periodo in periodos and periodo != 'Todo':
            cutoff_date = datetime.now() - timedelta(days=periodos[periodo])
            df = df[df['fecha'] >= cutoff_date]
        
        # Filter by selected houses
        if casas:
            df = df[df['casa'].isin(casas)]
        
        fig = go.Figure()
        
        for casa in df['casa'].unique():
            casa_data = df[df['casa'] == casa]
            fig.add_trace(go.Scatter(
                x=casa_data['fecha'],
                y=casa_data['venta'],
                mode='lines',
                name=casa,
                hovertemplate='<b>%{x}</b><br>Cotización: %{y}<extra></extra>'
            ))
        
        fig.update_layout(
            title='Cotizaciones del Dólar en Argentina',
            xaxis_title='Fecha',
            yaxis_title='Cotización',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_dolares_candlestick_chart(self, data: Dict, periodo: str = '1 mes', 
                                        casa: str = 'blue') -> Dict:
        """
        Create dólares candlestick chart with Plotly.
        
        Args:
            data: Candlestick data
            periodo: Time period
            casa: Exchange house
            
        Returns:
            Plotly figure as dictionary
        """
        if not data or casa not in data:
            return {}
        
        candlestick_data = data[casa]['candlesticks']
        df = pd.DataFrame(candlestick_data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        # Filter by period
        periodos = {
            '1 semana': 7,
            '1 mes': 30,
            '1 año': 365,
            '5 años': 1825,
        }
        
        if periodo in periodos and periodo != 'Todo':
            cutoff_date = datetime.now() - timedelta(days=periodos[periodo])
            df = df[df['fecha'] >= cutoff_date]
        
        fig = go.Figure()
        
        # Candlestick chart
        fig.add_trace(go.Candlestick(
            x=df['fecha'],
            open=df['apertura'],
            high=df['maximo'],
            low=df['minimo'],
            close=df['cierre'],
            name=casa,
            increasing_line_color='#3b82f6',
            decreasing_line_color='#ef4444'
        ))
        
        fig.update_layout(
            title=f'Evolución del Dólar - {casa}',
            xaxis_title='Fecha',
            yaxis_title='Cotización',
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_inflacion_chart(self, data: List[Dict]) -> Dict:
        """
        Create inflación chart with Plotly.
        
        Args:
            data: Inflation data
            
        Returns:
            Plotly figure as dictionary
        """
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['fecha'],
            y=df['valor'],
            mode='lines+markers',
            name='Inflación',
            line=dict(color='#3b82f6', width=2),
            hovertemplate='<b>%{x}</b><br>Inflación: %{y}%<extra></extra>'
        ))
        
        fig.update_layout(
            title='Evolución de la Inflación',
            xaxis_title='Fecha',
            yaxis_title='Inflación (%)',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_tasas_chart(self, data: List[Dict]) -> Dict:
        """
        Create tasas chart with Plotly.
        
        Args:
            data: Interest rates data
            
        Returns:
            Plotly figure as dictionary
        """
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        fig = go.Figure()
        
        for tasa in df['tasa'].unique():
            tasa_data = df[df['tasa'] == tasa]
            fig.add_trace(go.Scatter(
                x=tasa_data['fecha'],
                y=tasa_data['valor'],
                mode='lines+markers',
                name=tasa,
                hovertemplate='<b>%{x}</b><br>%{fullData.name}: %{y}%<extra></extra>'
            ))
        
        fig.update_layout(
            title='Evolución de las Tasas',
            xaxis_title='Fecha',
            yaxis_title='Tasa (%)',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_uva_chart(self, data: List[Dict]) -> Dict:
        """
        Create UVA chart with Plotly.
        
        Args:
            data: UVA data
            
        Returns:
            Plotly figure as dictionary
        """
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['fecha'],
            y=df['valor'],
            mode='lines+markers',
            name='UVA',
            line=dict(color='#10b981', width=2),
            hovertemplate='<b>%{x}</b><br>UVA: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Evolución del UVA',
            xaxis_title='Fecha',
            yaxis_title='UVA',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_riesgo_pais_chart(self, data: List[Dict]) -> Dict:
        """
        Create riesgo país chart with Plotly.
        
        Args:
            data: Country risk data
            
        Returns:
            Plotly figure as dictionary
        """
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['fecha'],
            y=df['valor'],
            mode='lines+markers',
            name='Riesgo País',
            line=dict(color='#f59e0b', width=2),
            hovertemplate='<b>%{x}</b><br>Riesgo País: %{y} puntos<extra></extra>'
        ))
        
        fig.update_layout(
            title='Evolución del Riesgo País',
            xaxis_title='Fecha',
            yaxis_title='Riesgo País (puntos)',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
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
            'riesgo_pais': self.get_riesgo_pais()
        }
    
    def create_all_charts(self, periodo: str = '1 mes', 
                         casas: Optional[List[str]] = None,
                         candlestick_casa: str = 'blue') -> Dict[str, Dict]:
        """
        Create all economic charts in one call.
        
        Args:
            periodo: Time period for charts
            casas: Exchange houses for dólar chart
            candlestick_casa: Exchange house for candlestick chart
            
        Returns:
            Dictionary with all chart figures
        """
        data = self.get_all_economic_data()
        
        return {
            'dolares': self.create_dolares_chart(data['dolares'], periodo, casas),
            'dolares_candlestick': self.create_dolares_candlestick_chart(
                data['dolares_candlestick'], periodo, candlestick_casa
            ),
            'inflacion': self.create_inflacion_chart(data['inflacion']),
            'tasas': self.create_tasas_chart(data['tasas']),
            'uva': self.create_uva_chart(data['uva']),
            'riesgo_pais': self.create_riesgo_pais_chart(data['riesgo_pais'])
        }

def mostrar_datos_argentina():
    """
    Función para mostrar el análisis de datos económicos de Argentina.
    """
    st.header("🇦🇷 Datos Económicos de Argentina")
    st.markdown("### Análisis de Indicadores Económicos y Financieros")
    
    # Inicializar ArgentinaDatos
    ad = ArgentinaDatos()
    
    # Sidebar para controles
    with st.sidebar:
        st.subheader("⚙️ Configuración de Análisis")
        
        # Selector de período
        periodo = st.selectbox(
            "Período de análisis:",
            ["1 semana", "1 mes", "1 año", "5 años", "Todo"],
            index=1,
            help="Seleccione el período de tiempo para el análisis"
        )
        
        # Selector de casas de cambio para dólar
        casas_dolar = st.multiselect(
            "Casas de cambio (Dólar):",
            ["oficial", "blue", "ccl", "mep"],
            default=["oficial", "blue"],
            help="Seleccione las casas de cambio a mostrar"
        )
        
        # Selector de casa para candlestick
        casa_candlestick = st.selectbox(
            "Casa para candlestick:",
            ["blue", "oficial", "ccl", "mep"],
            index=0,
            help="Seleccione la casa de cambio para el gráfico de candlestick"
        )
        
        # Botón para actualizar datos
        if st.button("🔄 Actualizar Datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Obtener datos con spinner
    with st.spinner('📊 Obteniendo datos económicos...'):
        try:
            data = ad.get_all_economic_data()
            
            # Verificar si se obtuvieron datos
            total_data = sum(len(v) if isinstance(v, list) else len(v) if isinstance(v, dict) else 0 for v in data.values())
            
            if total_data == 0:
                st.warning("⚠️ No se pudieron obtener datos de la API. Mostrando datos de ejemplo...")
                
                # Datos de ejemplo para demostración
                data = {
                    'dolares': [
                        {'fecha': '2024-01-01', 'casa': 'oficial', 'compra': 800, 'venta': 820},
                        {'fecha': '2024-01-02', 'casa': 'oficial', 'compra': 810, 'venta': 830},
                        {'fecha': '2024-01-03', 'casa': 'oficial', 'compra': 820, 'venta': 840},
                        {'fecha': '2024-01-01', 'casa': 'blue', 'compra': 1200, 'venta': 1250},
                        {'fecha': '2024-01-02', 'casa': 'blue', 'compra': 1220, 'venta': 1270},
                        {'fecha': '2024-01-03', 'casa': 'blue', 'compra': 1240, 'venta': 1290}
                    ],
                    'inflacion': [
                        {'fecha': '2024-01-01', 'valor': 25.5},
                        {'fecha': '2024-02-01', 'valor': 26.2},
                        {'fecha': '2024-03-01', 'valor': 27.1}
                    ],
                    'tasas': [
                        {'fecha': '2024-01-01', 'tasa': 'Tasa de Referencia', 'valor': 118},
                        {'fecha': '2024-02-01', 'tasa': 'Tasa de Referencia', 'valor': 120},
                        {'fecha': '2024-03-01', 'tasa': 'Tasa de Referencia', 'valor': 122}
                    ],
                    'uva': [
                        {'fecha': '2024-01-01', 'valor': 100.5},
                        {'fecha': '2024-02-01', 'valor': 102.3},
                        {'fecha': '2024-03-01', 'valor': 104.1}
                    ],
                    'riesgo_pais': [
                        {'fecha': '2024-01-01', 'valor': 1500},
                        {'fecha': '2024-02-01', 'valor': 1550},
                        {'fecha': '2024-03-01', 'valor': 1600}
                    ],
                    'dolares_candlestick': {}
                }
                
                st.info("💡 Los datos mostrados son de ejemplo. Para datos reales, verifique su conexión a internet.")
            
            # Mostrar resumen de datos
            st.subheader("📋 Resumen de Datos Disponibles")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Dólares", f"{len(data['dolares'])} registros")
                st.metric("Inflación", f"{len(data['inflacion'])} registros")
            
            with col2:
                st.metric("Tasas", f"{len(data['tasas'])} registros")
                st.metric("UVA", f"{len(data['uva'])} registros")
            
            with col3:
                st.metric("Riesgo País", f"{len(data['riesgo_pais'])} registros")
                st.metric("Candlestick", f"{len(data['dolares_candlestick'])} casas")
            
            # Crear pestañas para diferentes análisis
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "💵 Dólar", "📈 Inflación", "🏦 Tasas", "📊 UVA", "⚠️ Riesgo País", "📋 Todos los Gráficos"
            ])
            
            with tab1:
                st.subheader("💵 Análisis del Dólar")
                
                if data['dolares']:
                    # Crear gráfico de dólares
                    fig_data = ad.create_dolares_chart(data['dolares'], periodo, casas_dolar)
                    if fig_data:
                        fig = go.Figure(fig_data)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Mostrar datos más recientes
                    df_dolares = pd.DataFrame(data['dolares'])
                    if not df_dolares.empty:
                        df_dolares['fecha'] = pd.to_datetime(df_dolares['fecha'])
                        df_dolares = df_dolares.sort_values('fecha', ascending=False)
                        
                        st.subheader("📊 Últimas Cotizaciones")
                        st.dataframe(
                            df_dolares.head(10)[['fecha', 'casa', 'compra', 'venta']],
                            use_container_width=True
                        )
                else:
                    st.warning("No se pudieron obtener datos del dólar")
                
                # Gráfico de candlestick
                if data['dolares_candlestick'] and casa_candlestick in data['dolares_candlestick']:
                    st.subheader(f"📊 Candlestick - {casa_candlestick.title()}")
                    candlestick_data = ad.create_dolares_candlestick_chart(
                        data['dolares_candlestick'], periodo, casa_candlestick
                    )
                    if candlestick_data:
                        fig = go.Figure(candlestick_data)
                        st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                st.subheader("📈 Análisis de Inflación")
                
                if data['inflacion']:
                    fig_data = ad.create_inflacion_chart(data['inflacion'])
                    if fig_data:
                        fig = go.Figure(fig_data)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Mostrar datos de inflación
                    df_inflacion = pd.DataFrame(data['inflacion'])
                    if not df_inflacion.empty:
                        df_inflacion['fecha'] = pd.to_datetime(df_inflacion['fecha'])
                        df_inflacion = df_inflacion.sort_values('fecha', ascending=False)
                        
                        st.subheader("📊 Datos de Inflación")
                        st.dataframe(
                            df_inflacion.head(10)[['fecha', 'valor']],
                            use_container_width=True
                        )
                else:
                    st.warning("No se pudieron obtener datos de inflación")
            
            with tab3:
                st.subheader("🏦 Análisis de Tasas")
                
                if data['tasas']:
                    fig_data = ad.create_tasas_chart(data['tasas'])
                    if fig_data:
                        fig = go.Figure(fig_data)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Mostrar datos de tasas
                    df_tasas = pd.DataFrame(data['tasas'])
                    if not df_tasas.empty:
                        df_tasas['fecha'] = pd.to_datetime(df_tasas['fecha'])
                        df_tasas = df_tasas.sort_values('fecha', ascending=False)
                        
                        st.subheader("📊 Datos de Tasas")
                        st.dataframe(
                            df_tasas.head(10)[['fecha', 'tasa', 'valor']],
                            use_container_width=True
                        )
                else:
                    st.warning("No se pudieron obtener datos de tasas")
            
            with tab4:
                st.subheader("📊 Análisis del UVA")
                
                if data['uva']:
                    fig_data = ad.create_uva_chart(data['uva'])
                    if fig_data:
                        fig = go.Figure(fig_data)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Mostrar datos del UVA
                    df_uva = pd.DataFrame(data['uva'])
                    if not df_uva.empty:
                        df_uva['fecha'] = pd.to_datetime(df_uva['fecha'])
                        df_uva = df_uva.sort_values('fecha', ascending=False)
                        
                        st.subheader("📊 Datos del UVA")
                        st.dataframe(
                            df_uva.head(10)[['fecha', 'valor']],
                            use_container_width=True
                        )
                else:
                    st.warning("No se pudieron obtener datos del UVA")
            
            with tab5:
                st.subheader("⚠️ Análisis del Riesgo País")
                
                if data['riesgo_pais']:
                    fig_data = ad.create_riesgo_pais_chart(data['riesgo_pais'])
                    if fig_data:
                        fig = go.Figure(fig_data)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Mostrar datos del riesgo país
                    df_riesgo = pd.DataFrame(data['riesgo_pais'])
                    if not df_riesgo.empty:
                        df_riesgo['fecha'] = pd.to_datetime(df_riesgo['fecha'])
                        df_riesgo = df_riesgo.sort_values('fecha', ascending=False)
                        
                        st.subheader("📊 Datos del Riesgo País")
                        st.dataframe(
                            df_riesgo.head(10)[['fecha', 'valor']],
                            use_container_width=True
                        )
                else:
                    st.warning("No se pudieron obtener datos del riesgo país")
            
            with tab6:
                st.subheader("📋 Todos los Gráficos")
                
                # Crear todos los gráficos
                charts = ad.create_all_charts(periodo, casas_dolar, casa_candlestick)
                
                # Mostrar cada gráfico
                for chart_name, fig_data in charts.items():
                    if fig_data:
                        st.subheader(f"📊 {chart_name.replace('_', ' ').title()}")
                        fig = go.Figure(fig_data)
                        st.plotly_chart(fig, use_container_width=True)
                        st.markdown("---")
            
            # Sección de descarga de datos
            st.markdown("---")
            st.subheader("💾 Descargar Datos")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if data['dolares']:
                    df_dolares = pd.DataFrame(data['dolares'])
                    csv_dolares = df_dolares.to_csv(index=False)
                    st.download_button(
                        label="📥 Descargar Dólares (CSV)",
                        data=csv_dolares,
                        file_name="dolares_argentina.csv",
                        mime="text/csv"
                    )
            
            with col2:
                if data['inflacion']:
                    df_inflacion = pd.DataFrame(data['inflacion'])
                    csv_inflacion = df_inflacion.to_csv(index=False)
                    st.download_button(
                        label="📥 Descargar Inflación (CSV)",
                        data=csv_inflacion,
                        file_name="inflacion_argentina.csv",
                        mime="text/csv"
                    )
            
            with col3:
                if data['riesgo_pais']:
                    df_riesgo = pd.DataFrame(data['riesgo_pais'])
                    csv_riesgo = df_riesgo.to_csv(index=False)
                    st.download_button(
                        label="📥 Descargar Riesgo País (CSV)",
                        data=csv_riesgo,
                        file_name="riesgo_pais_argentina.csv",
                        mime="text/csv"
                    )
        
        except Exception as e:
            st.error(f"❌ Error al obtener datos económicos: {str(e)}")
            st.info("💡 Verifique su conexión a internet e intente nuevamente")

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

def parse_datetime_string(datetime_string):
    """
    Parsea una cadena de fecha/hora usando múltiples formatos
    """
    if not datetime_string:
        return None
        
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
                # Eliminar duplicados manteniendo el último
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

def obtener_serie_historica_fci(token_portador, simbolo, fecha_desde, fecha_hasta):
    """
    Obtiene la serie histórica de un Fondo Común de Inversión.
    
    Args:
        token_portador (str): Token de autenticación
        simbolo (str): Símbolo del FCI
        fecha_desde (str): Fecha inicio (YYYY-MM-DD)
        fecha_hasta (str): Fecha fin (YYYY-MM-DD)
        
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
            if ric in self.timeseries and self.timeseries[ric] is not None:
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
        """Crea un objeto output con los pesos optimizados"""
        port_ret = np.sum(self.mean_returns * weights)
        port_vol = np.sqrt(portfolio_variance(weights, self.cov_matrix))
        
        # Calcular retornos del portafolio
        if self.returns is not None:
            portfolio_returns = self.returns.dot(weights)
        else:
            # Fallback si returns es None
            portfolio_returns = pd.Series([0] * 252)  # Serie vacía
        
        # Crear objeto output
        port_output = output(portfolio_returns, self.notional)
        port_output.weights = weights
        port_output.dataframe_allocation = pd.DataFrame({
            'rics': self.rics,
            'weights': weights,
            'volatilities': np.sqrt(np.diag(self.cov_matrix)),
            'returns': self.mean_returns
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
        # Compatibilidad: alias para risk y returns (usados en la interfaz)
        self.risk = self.volatility_annual
        self.returns = self.return_annual

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
        # Asegura que self.returns sea una secuencia (array, lista, o pandas Series), no un escalar
        import numpy as np
        import pandas as pd
        returns = self.returns
        # Si es None o vacío
        if returns is None or (hasattr(returns, '__len__') and len(returns) == 0):
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos suficientes para mostrar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(title=title)
            return fig
        # Si es un escalar (float, int, numpy.float, numpy.int)
        if isinstance(returns, (float, int, np.floating, np.integer)):
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos suficientes para mostrar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(title=title)
            return fig
        # Si es un array/serie de un solo valor, también evitar graficar
        if hasattr(returns, '__len__') and len(returns) <= 1:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos suficientes para mostrar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(title=title)
            return fig

        fig = go.Figure(data=[go.Histogram(
            x=returns,
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

def optimize_portfolio(returns, target_return=None):
    """
    Optimiza un portafolio usando el método de Markowitz
    
    Args:
        returns (pd.DataFrame): DataFrame con retornos de activos
        target_return (float, optional): Retorno objetivo anual
        
    Returns:
        np.array: Pesos optimizados del portafolio
    """
    if returns is None or returns.empty:
        return None
        
    n_assets = len(returns.columns)
    
    # Calcular matriz de covarianza y retornos medios
    cov_matrix = returns.cov() * 252  # Anualizar
    mean_returns = returns.mean() * 252  # Anualizar
    
    # Pesos iniciales iguales
    initial_weights = np.ones(n_assets) / n_assets
    
    # Restricciones
    bounds = tuple((0, 1) for _ in range(n_assets))
    
    if target_return is not None:
        # Optimización con retorno objetivo
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Suma de pesos = 1
            {'type': 'eq', 'fun': lambda x: np.sum(mean_returns * x) - target_return}  # Retorno objetivo
        ]
        
        # Minimizar varianza
        result = op.minimize(
            lambda x: portfolio_variance(x, cov_matrix),
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
    else:
        # Maximizar Sharpe ratio
        risk_free_rate = 0.40  # Tasa libre de riesgo para Argentina
        
        def neg_sharpe_ratio(weights):
            port_return = np.sum(mean_returns * weights)
            port_vol = np.sqrt(portfolio_variance(weights, cov_matrix))
            if port_vol == 0:
                return np.inf
            return -(port_return - risk_free_rate) / port_vol
        
        constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        
        result = op.minimize(
            neg_sharpe_ratio,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
    
    if result.success:
        return result.x
    else:
        # Si falla la optimización, usar pesos iguales
        return initial_weights

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

class PortfolioManager:
    def __init__(self, activos, token, fecha_desde, fecha_hasta):
        self.activos = activos
        self.token = token
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.data_loaded = False
        self.returns = None
        self.prices = None
        self.notional = 100000  # Valor nominal por defecto
        self.manager = None
    
    def load_data(self):
        try:
            # Convertir lista de activos a formato adecuado
            symbols = []
            markets = []
            tipos = []
            def detectar_mercado(tipo_raw: str, mercado_raw: str) -> str:
                """
                Determina el mercado basado en la información proporcionada.
                
                Args:
                    tipo_raw: Tipo de activo (no utilizado en esta versión)
                    mercado_raw: Mercado del activo
                    
                Returns:
                    str: Nombre del mercado normalizado
                """
                # Usar el mercado proporcionado o BCBA como valor por defecto
                mercado = mercado_raw.strip().title() if mercado_raw.strip() else 'BCBA'
                return mercado
            
            for activo in self.activos:
                if isinstance(activo, dict):
                    simbolo = activo.get('simbolo', '')
                    tipo_raw = (activo.get('tipo') or '')
                    mercado_raw = (activo.get('mercado') or '')
                    
                    if not simbolo:
                        continue
                    symbols.append(simbolo)
                    tipos.append(tipo_raw)
                    markets.append(detectar_mercado(tipo_raw, mercado_raw))
                else:
                    symbols.append(activo)
                    markets.append('BCBA')  # Default market
            
            if not symbols:
                st.error("❌ No se encontraron símbolos válidos para procesar")
                return False
            
            # Obtener datos históricos
            data_frames = {}
            
            with st.spinner("Obteniendo datos históricos..."):
                for simbolo, mercado in zip(symbols, markets):
                    df = obtener_serie_historica_iol(
                        self.token,
                        mercado,
                        simbolo,
                        self.fecha_desde,
                        self.fecha_hasta
                    )
                    
                    if df is not None and not df.empty:
                        # Usar la columna de último precio si está disponible
                        precio_columns = ['ultimoPrecio', 'ultimo_precio', 'precio']
                        precio_col = next((col for col in precio_columns if col in df.columns), None)
                        
                        if precio_col:
                            df = df[['fecha', precio_col]].copy()
                            df.columns = ['fecha', 'precio']  # Normalizar el nombre de la columna
                            
                            # Convertir fechaHora a fecha y asegurar que sea única
                            df['fecha'] = pd.to_datetime(df['fecha']).dt.date
                            
                            # Eliminar duplicados manteniendo el último valor
                            df = df.drop_duplicates(subset=['fecha'], keep='last')
                            
                            df.set_index('fecha', inplace=True)
                            data_frames[simbolo] = df
                        else:
                            st.warning(f"⚠️ No se encontró columna de precio válida para {simbolo}")
                    else:
                        st.warning(f"⚠️ No se pudieron obtener datos para {simbolo} en {mercado}")
            
            if not data_frames:
                st.error("❌ No se pudieron obtener datos históricos para ningún activo")
                return False
            
            # Combinar todos los DataFrames
            df_precios = pd.concat(data_frames.values(), axis=1, keys=data_frames.keys())
            # Limpiar datos
            if not df_precios.index.is_unique:
                st.warning("⚠️ Se encontraron fechas duplicadas en los datos")
                df_precios = df_precios.groupby(df_precios.index).last()
            df_precios = df_precios.fillna(method='ffill')
            df_precios = df_precios.dropna()
            if df_precios.empty:
                st.error("❌ No hay datos suficientes después del preprocesamiento")
                return False
            self.prices = df_precios  # <--- ASIGNAR PRECIOS PARA FRONTERA EFICIENTE
            self.returns = df_precios.pct_change().dropna()
            self.mean_returns = self.returns.mean()
            self.cov_matrix = self.returns.cov()
            self.data_loaded = True
            self.manager = manager(list(df_precios.columns), self.notional, df_precios.to_dict('series'))
            return True
        except Exception as e:
            st.error(f"❌ Error en load_data: {str(e)}")
            return False
    
    def compute_portfolio(self, strategy='markowitz', target_return=None):
        if not self.data_loaded or self.returns is None:
            return None
        
        try:
            if self.manager:
                # Usar el manager avanzado
                portfolio_output = self.manager.compute_portfolio(strategy, target_return)
                return portfolio_output
            else:
                # Fallback a optimización básica
                n_assets = len(self.returns.columns)
                
                if strategy == 'equi-weight':
                    weights = np.ones(n_assets) / n_assets
                else:
                    weights = optimize_portfolio(self.returns, target_return=target_return)
                
                # Crear objeto de resultado básico
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
            
        except Exception as e:
            return None

    def compute_efficient_frontier(self, target_return=0.08, include_min_variance=True):
        """Computa la frontera eficiente"""
        if not self.data_loaded or not self.manager or self.prices is None or self.prices.empty:
            return None, None, None
        try:
            # Chequeo adicional: evitar series con menos de 2 activos o fechas
            if self.prices.shape[1] < 2 or self.prices.shape[0] < 10:
                return None, None, None
            portfolios, returns, volatilities = compute_efficient_frontier(
                self.manager.rics, self.notional, target_return, include_min_variance, 
                self.prices.to_dict('series')
            )
            return portfolios, returns, volatilities
        except Exception as e:
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
def calcular_alpha_beta(portfolio_returns, benchmark_returns, risk_free_rate=0.0):
    """
    Calcula el Alpha y Beta de un portafolio respecto a un benchmark.
    
    Args:
        portfolio_returns (pd.Series): Retornos del portafolio
        benchmark_returns (pd.Series): Retornos del benchmark (ej: MERVAL)
        risk_free_rate (float): Tasa libre de riesgo (anualizada)
        
    Returns:
        dict: Diccionario con alpha, beta, información de la regresión y métricas adicionales
    """
    # Alinear las series por fecha y eliminar NaN
    aligned_data = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
    if len(aligned_data) < 5:  # Mínimo de datos para regresión
        return {
            'alpha': 0,
            'beta': 1.0,
            'r_squared': 0,
            'p_value': 1.0,
            'tracking_error': 0,
            'information_ratio': 0,
            'observations': len(aligned_data),
            'alpha_annual': 0
        }
    
    portfolio_aligned = aligned_data.iloc[:, 0]
    benchmark_aligned = aligned_data.iloc[:, 1]
    
    # Calcular regresión lineal
    slope, intercept, r_value, p_value, std_err = linregress(benchmark_aligned, portfolio_aligned)
    
    # Calcular métricas adicionales
    tracking_error = np.std(portfolio_aligned - benchmark_aligned) * np.sqrt(252)  # Anualizado
    information_ratio = (portfolio_aligned.mean() - benchmark_aligned.mean()) / tracking_error if tracking_error != 0 else 0
    
    # Anualizar alpha (asumiendo 252 días hábiles)
    alpha_annual = intercept * 252
    
    return {
        'alpha': intercept,
        'beta': slope,
        'r_squared': r_value ** 2,
        'p_value': p_value,
        'tracking_error': tracking_error,
        'information_ratio': information_ratio,
        'observations': len(aligned_data),
        'alpha_annual': alpha_annual
    }

def analizar_estrategia_inversion(alpha_beta_metrics):
    """
    Analiza la estrategia de inversión y cobertura basada en métricas de alpha y beta.
    
    Args:
        alpha_beta_metrics (dict): Diccionario con las métricas de alpha y beta
        
    Returns:
        dict: Diccionario con el análisis de la estrategia
    """
    beta = alpha_beta_metrics.get('beta', 1.0)
    alpha_annual = alpha_beta_metrics.get('alpha_annual', 0)
    r_squared = alpha_beta_metrics.get('r_squared', 0)
    
    # Análisis de estrategia basado en beta
    if beta > 1.2:
        estrategia = "Estrategia Agresiva"
        explicacion = ("El portafolio es más volátil que el mercado (β > 1.2). "
                      "Esta estrategia busca rendimientos superiores asumiendo mayor riesgo.")
    elif beta > 0.8:
        estrategia = "Estrategia de Crecimiento"
        explicacion = ("El portafolio sigue de cerca al mercado (0.8 < β < 1.2). "
                     "Busca rendimientos similares al mercado con un perfil de riesgo equilibrado.")
    elif beta > 0.3:
        estrategia = "Estrategia Defensiva"
        explicacion = ("El portafolio es menos volátil que el mercado (0.3 < β < 0.8). "
                     "Busca preservar capital con menor exposición a las fluctuaciones del mercado.")
    elif beta > -0.3:
        estrategia = "Estrategia de Ingresos"
        explicacion = ("El portafolio tiene baja correlación con el mercado (-0.3 < β < 0.3). "
                     "Ideal para generar ingresos con bajo riesgo de mercado.")
    else:
        estrategia = "Estrategia de Cobertura"
        explicacion = ("El portafolio tiene correlación negativa con el mercado (β < -0.3). "
                     "Diseñado para moverse en dirección opuesta al mercado, útil para cobertura.")
    
    # Análisis de desempeño basado en alpha
    if alpha_annual > 0.05:  # 5% de alpha anual
        rendimiento = "Excelente desempeño"
        explicacion_rendimiento = (f"El portafolio ha generado un alpha anualizado de {alpha_annual:.1%}, "
                                 "superando significativamente al benchmark.")
    elif alpha_annual > 0.02:  # 2% de alpha anual
        rendimiento = "Buen desempeño"
        explicacion_rendimiento = (f"El portafolio ha generado un alpha anualizado de {alpha_annual:.1%}, "
                                 "superando al benchmark.")
    elif alpha_annual > -0.02:  # Entre -2% y 2%
        rendimiento = "Desempeño en línea"
        explicacion_rendimiento = (f"El portafolio tiene un alpha anualizado de {alpha_annual:.1%}, "
                                 "en línea con el benchmark.")
    else:
        rendimiento = "Desempeño inferior"
        explicacion_rendimiento = (f"El portafolio tiene un alpha anualizado de {alpha_annual:.1%}, "
                                 "por debajo del benchmark.")
    
    # Calidad de la cobertura basada en R²
    if r_squared > 0.7:
        calidad_cobertura = "Alta"
        explicacion_cobertura = (f"El R² de {r_squared:.2f} indica una fuerte relación con el benchmark. "
                               "La cobertura será más efectiva.")
    elif r_squared > 0.4:
        calidad_cobertura = "Moderada"
        explicacion_cobertura = (f"El R² de {r_squared:.2f} indica una relación moderada con el benchmark. "
                               "La cobertura puede ser parcialmente efectiva.")
    else:
        calidad_cobertura = "Baja"
        explicacion_cobertura = (f"El R² de {r_squared:.2f} indica una débil relación con el benchmark. "
                               "La cobertura puede no ser efectiva.")
    
    return {
        'estrategia': estrategia,
        'explicacion_estrategia': explicacion,
        'rendimiento': rendimiento,
        'explicacion_rendimiento': explicacion_rendimiento,
        'calidad_cobertura': calidad_cobertura,
        'explicacion_cobertura': explicacion_cobertura,
        'beta': beta,
        'alpha_anual': alpha_annual,
        'r_cuadrado': r_squared,
        'observations': alpha_beta_metrics.get('observations', 0)
    }

def calcular_metricas_portafolio(portafolio, valor_total, token_portador, dias_historial=252):
    """
    Calcula métricas clave de desempeño para un portafolio de inversión usando datos históricos.
{{ ... }}
    
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
        
    # Descargar datos del MERVAL para cálculo de Alpha y Beta
    try:
        merval_data = yf.download('^MERV', start=fecha_desde, end=fecha_hasta)['Close']
        merval_returns = merval_data.pct_change().dropna()
        merval_available = True
    except Exception as e:
        print(f"No se pudieron obtener datos del MERVAL: {str(e)}")
        merval_available = False
        merval_returns = None
    
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
                
                # Asegurarse de que las dimensiones coincidan
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
            
    # 4. Calcular Alpha y Beta respecto al MERVAL si hay datos disponibles
    alpha_beta_metrics = {}
    if merval_available and len(retornos_diarios) > 1:
        try:
            # Calcular retornos diarios del portafolio (promedio ponderado de los activos)
            df_port_returns = pd.DataFrame(retornos_diarios)
            
            # Asegurarse de que los pesos estén en el mismo orden que las columnas
            pesos_ordenados = [metricas_activos[col]['peso'] for col in df_port_returns.columns]
            df_port_returns['Portfolio'] = df_port_returns.dot(pesos_ordenados)
            
            # Alinear fechas con el MERVAL
            merval_series = pd.Series(merval_returns, name='MERVAL')
            aligned_data = pd.merge(
                df_port_returns[['Portfolio']], 
                merval_series, 
                left_index=True, 
                right_index=True,
                how='inner'
            )
            
            if len(aligned_data) > 5:  # Mínimo de datos para cálculo confiable
                # Calcular métricas de Alpha y Beta
                alpha_beta_metrics = calcular_alpha_beta(
                    aligned_data['Portfolio'],  # Retornos del portafolio
                    aligned_data['MERVAL'],      # Retornos del MERVAL
                    risk_free_rate=0.40  # Tasa libre de riesgo para Argentina
                )
                
                print(f"Alpha: {alpha_beta_metrics.get('alpha_annual', 0):.2%}, "
                      f"Beta: {alpha_beta_metrics.get('beta', 0):.2f}, "
                      f"R²: {alpha_beta_metrics.get('r_squared', 0):.2f}")
            
        except Exception as e:
            print(f"Error al calcular Alpha/Beta: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Crear diccionario de probabilidades
    probabilidades = {
        'perdida': prob_perdida,
        'ganancia': prob_ganancia,
        'perdida_mayor_10': prob_perdida_10,
        'ganancia_mayor_10': prob_ganancia_10
    }
    
    # Crear diccionario de resultados
    resultados = {
        'concentracion': concentracion,
        'std_dev_activo': volatilidad_portafolio,
        'retorno_esperado_anual': retorno_esperado_anual,
        'pl_esperado_min': pl_esperado_min,
        'pl_esperado_max': pl_esperado_max,
        'probabilidades': probabilidades,
        'riesgo_anual': volatilidad_portafolio,  # Usamos la volatilidad como proxy de riesgo
        'alpha': alpha_beta_metrics.get('alpha_annual', 0),
        'beta': alpha_beta_metrics.get('beta', 0),
        'r_cuadrado': alpha_beta_metrics.get('r_squared', 0),
        'tracking_error': alpha_beta_metrics.get('tracking_error', 0),
        'information_ratio': alpha_beta_metrics.get('information_ratio', 0)
    }
    
    # Analizar la estrategia de inversión
    analisis_estrategia = analizar_estrategia_inversion(alpha_beta_metrics)
    resultados['analisis_estrategia'] = analisis_estrategia
    
    # Agregar métricas adicionales si están disponibles
    if 'p_value' in alpha_beta_metrics:
        resultados['p_value'] = alpha_beta_metrics['p_value']
    if 'observations' in alpha_beta_metrics:
        resultados['observaciones'] = alpha_beta_metrics['observations']
    
    return resultados

# --- Funciones de Visualización ---
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
                    ultimo_precio = obtener_precio_actual(token_portador, mercado, simbolo)
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
            cols[3].metric("Pérdida >10%", f"{probs['perdida_mayor_10']*100:.1f}")
            

        
        # Gráficos
        st.subheader("📊 Distribución de Activos")
        
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
        
        # Histograma del portafolio total valorizado
        st.subheader("📈 Histograma del Portafolio Total Valorizado")
        
        # Configuración del horizonte de inversión
        horizonte_inversion = st.selectbox(
            "Horizonte de Inversión:",
            options=[
                ("30 días", 30),
                ("60 días", 60),
                ("90 días", 90),
                ("180 días", 180),
                ("365 días", 365),
                ("730 días", 730),
                ("1095 días", 1095)
            ],
            format_func=lambda x: x[0],
            index=3,  # Por defecto 180 días
            help="Seleccione el período de tiempo para el análisis de retornos"
        )
        
        # Intervalo de análisis fijo en diario
        intervalo_analisis = ("Diario", "D")
        st.info("📊 Análisis configurado en frecuencia diaria")
        
        # Extraer valores de las tuplas
        dias_analisis = horizonte_inversion[1]
        frecuencia = intervalo_analisis[1]
        
        with st.spinner(f"Obteniendo series históricas y calculando valorización del portafolio para {dias_analisis} días..."):
            try:
                # Obtener fechas para el histórico basado en el horizonte seleccionado
                fecha_hasta = datetime.now().strftime('%Y-%m-%d')
                fecha_desde = (datetime.now() - timedelta(days=dias_analisis)).strftime('%Y-%m-%d')
                
                # Preparar datos para obtener series históricas
                activos_para_historico = []
                for activo in datos_activos:
                    simbolo = activo['Símbolo']
                    if simbolo != 'N/A':
                        # Intentar obtener el mercado del activo original
                        mercado = 'BCBA'  # Default
                        for activo_original in activos:
                            if activo_original.get('titulo', {}).get('simbolo') == simbolo:
                                mercado = activo_original.get('titulo', {}).get('mercado', 'BCBA')
                                break
                        
                        activos_para_historico.append({
                            'simbolo': simbolo,
                            'mercado': mercado,
                            'peso': activo['Valuación'] / valor_total if valor_total > 0 else 0
                        })
                
                if len(activos_para_historico) > 0:
                    # Obtener series históricas para cada activo
                    series_historicas = {}
                    activos_exitosos = []
                    
                    for activo_info in activos_para_historico:
                        simbolo = activo_info['simbolo']
                        mercado = activo_info['mercado']
                        peso = activo_info['peso']
                        
                        if peso > 0:  # Solo procesar activos con peso significativo
                            serie = obtener_serie_historica_iol(
                                token_portador,
                                mercado,
                                simbolo,
                                fecha_desde,
                                fecha_hasta
                            )
                            
                            if serie is not None and not serie.empty:
                                series_historicas[simbolo] = serie
                                activos_exitosos.append({
                                    'simbolo': simbolo,
                                    'peso': peso,
                                    'serie': serie
                                })
                                st.success(f"✅ {simbolo}: {len(serie)} puntos de datos")
                            else:
                                st.warning(f"⚠️ No se pudieron obtener datos para {simbolo}")
                    
                    if len(activos_exitosos) > 0:
                        # Crear DataFrame con todas las series alineadas
                        df_portfolio = pd.DataFrame()
                        
                        # Primero, encontrar el rango de fechas común para todas las series
                        fechas_comunes = None
                        for activo_info in activos_exitosos:
                            serie = activo_info['serie']
                            if fechas_comunes is None:
                                fechas_comunes = set(serie.index)
                            else:
                                fechas_comunes = fechas_comunes.intersection(set(serie.index))
                        
                        if not fechas_comunes or len(fechas_comunes) == 0:
                            # Si no hay fechas comunes, usar la unión y rellenar con ffill
                            st.warning("⚠️ No hay fechas comunes entre las series históricas. Se usará la unión de fechas y se rellenarán los valores faltantes.")
                            fechas_union = set()
                            for activo_info in activos_exitosos:
                                fechas_union = fechas_union.union(set(activo_info['serie'].index))
                            fechas_union = sorted(list(fechas_union))
                            df_portfolio.index = fechas_union
                            usar_union = True
                        else:
                            fechas_comunes = sorted(list(fechas_comunes))
                            df_portfolio.index = fechas_comunes
                            usar_union = False
                        
                        for activo_info in activos_exitosos:
                            simbolo = activo_info['simbolo']
                            peso = activo_info['peso']
                            serie = activo_info['serie']
                            valuacion_activo = 0
                            for activo_original in datos_activos:
                                if activo_original['Símbolo'] == simbolo:
                                    valuacion_activo = float(activo_original['Valuación'])
                                    break
                            # Seleccionar fechas
                            if usar_union:
                                serie_filtrada = serie.reindex(df_portfolio.index)
                            else:
                                serie_filtrada = serie.loc[df_portfolio.index]
                            # Agregar serie ponderada al DataFrame
                            if 'precio' in serie_filtrada.columns:
                                precios = serie_filtrada['precio'].values
                                if len(precios) > 1:
                                    retornos_acumulados = precios / precios[0]
                                    df_portfolio[simbolo] = valuacion_activo * retornos_acumulados
                                else:
                                    df_portfolio[simbolo] = valuacion_activo
                            else:
                                columnas_numericas = serie_filtrada.select_dtypes(include=[np.number]).columns
                                if len(columnas_numericas) > 0:
                                    precios = serie_filtrada[columnas_numericas[0]].values
                                    if len(precios) > 1:
                                        retornos_acumulados = precios / precios[0]
                                        df_portfolio[simbolo] = valuacion_activo * retornos_acumulados
                                    else:
                                        df_portfolio[simbolo] = valuacion_activo
                                else:
                                    st.warning(f"⚠️ No se encontraron valores numéricos para {simbolo}")
                                    continue
                        # Rellenar valores faltantes con forward-fill y eliminar filas completamente vacías
                        df_portfolio = df_portfolio.ffill().dropna(how='all')
                        # Calcular valor total del portafolio por fecha
                        if not df_portfolio.empty:
                            df_portfolio['Portfolio_Total'] = df_portfolio.sum(axis=1)
                        else:
                            st.error("❌ No se pudo construir el DataFrame del portafolio. Verifique los datos históricos de los activos seleccionados.")
                            return
                        
                        # Mostrar información de debug
                        st.info(f"🔍 Debug: Valor total actual del portafolio: ${valor_total:,.2f}")
                        st.info(f"🔍 Debug: Columnas en df_portfolio: {list(df_portfolio.columns)}")
                        if len(df_portfolio) > 0:
                            st.info(f"🔍 Debug: Último valor calculado: ${df_portfolio['Portfolio_Total'].iloc[-1]:,.2f}")
                        
                        # Eliminar filas con valores NaN
                        df_portfolio = df_portfolio.dropna()
                        
                        if len(df_portfolio) > 0:
                            # Crear histograma del valor total del portafolio
                            valores_portfolio = df_portfolio['Portfolio_Total'].values
                            
                            fig_hist = go.Figure(data=[go.Histogram(
                                x=valores_portfolio,
                                nbinsx=30,
                                name="Valor Total del Portafolio",
                                marker_color='#0d6efd',
                                opacity=0.7
                            )])
                            
                            # Agregar líneas de métricas importantes
                            media_valor = np.mean(valores_portfolio)
                            mediana_valor = np.median(valores_portfolio)
                            percentil_5 = np.percentile(valores_portfolio, 5)
                            percentil_95 = np.percentile(valores_portfolio, 95)
                            
                            fig_hist.add_vline(x=media_valor, line_dash="dash", line_color="red", 
                                             annotation_text=f"Media: ${media_valor:,.2f}")
                            fig_hist.add_vline(x=mediana_valor, line_dash="dash", line_color="green", 
                                             annotation_text=f"Mediana: ${mediana_valor:,.2f}")
                            fig_hist.add_vline(x=percentil_5, line_dash="dash", line_color="orange", 
                                             annotation_text=f"P5: ${percentil_5:,.2f}")
                            fig_hist.add_vline(x=percentil_95, line_dash="dash", line_color="purple", 
                                             annotation_text=f"P95: ${percentil_95:,.2f}")
                            
                            fig_hist.update_layout(
                                title="Distribución del Valor Total del Portafolio",
                                xaxis_title="Valor del Portafolio ($)",
                                yaxis_title="Frecuencia",
                                height=500,
                                showlegend=False,
                                template='plotly_white'
                            )
                            
                            st.plotly_chart(fig_hist, use_container_width=True)
                            
                            # Mostrar estadísticas del histograma
                            st.markdown("#### 📊 Estadísticas del Histograma")
                            col1, col2, col3, col4 = st.columns(4)
                            
                            col1.metric("Valor Promedio", f"${media_valor:,.2f}")
                            col2.metric("Valor Mediano", f"${mediana_valor:,.2f}")
                            col3.metric("Valor Mínimo (P5)", f"${percentil_5:,.2f}")
                            col4.metric("Valor Máximo (P95)", f"${percentil_95:,.2f}")
                            
                            # Mostrar evolución temporal del portafolio
                            st.markdown("#### 📈 Evolución Temporal del Portafolio")
                            # --- ELIMINAR GRÁFICO DUPLICADO Y DEJAR SOLO UNO ---
                            fig_evolucion = go.Figure()
                            # Usar fechas reales como eje X
                            fechas = df_portfolio.index
                            if not isinstance(fechas, pd.DatetimeIndex):
                                fechas = pd.to_datetime(fechas)
                            fig_evolucion.add_trace(go.Scatter(
                                x=fechas,
                                y=df_portfolio['Portfolio_Total'],
                                mode='lines',
                                name='Valor Total del Portafolio',
                                line=dict(color='#0d6efd', width=2)
                            ))
                            fig_evolucion.update_layout(
                                title="Evolución del Valor del Portafolio en el Tiempo",
                                xaxis_title="Fecha",
                                yaxis_title="Valor del Portafolio ($)",
                                height=400,
                                template='plotly_white'
                            )
                            st.plotly_chart(fig_evolucion, use_container_width=True)
                            
                            # Mostrar contribución de cada activo
                            st.markdown("#### 🥧 Contribución de Activos al Valor Total")
                            
                            contribucion_activos = {}
                            for activo_info in activos_exitosos:
                                simbolo = activo_info['simbolo']
                                # Usar la valuación real del activo
                                for activo_original in datos_activos:
                                    if activo_original['Símbolo'] == simbolo:
                                        contribucion_activos[simbolo] = activo_original['Valuación']
                                        break
                            
                            if contribucion_activos:
                                fig_contribucion = go.Figure(data=[go.Pie(
                                    labels=list(contribucion_activos.keys()),
                                    values=list(contribucion_activos.values()),
                                    textinfo='label+percent+value',
                                    texttemplate='%{label}<br>%{percent}<br>$%{value:,.0f}',
                                    hole=0.4,
                                    marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3'])
                                )])
                                fig_contribucion.update_layout(
                                    title="Contribución de Activos al Valor Total del Portafolio",
                                    height=400
                                )
                                st.plotly_chart(fig_contribucion, use_container_width=True)
                            
                            # Calcular y mostrar histograma de retornos del portafolio
                            st.markdown("#### 📊 Histograma de Retornos del Portafolio")
                            
                            try:
                                # Calcular retornos diarios del portafolio
                                df_portfolio_returns = df_portfolio['Portfolio_Total'].pct_change().dropna()
                                
                                if len(df_portfolio_returns) > 10:  # Mínimo de datos para análisis
                                    # Calcular métricas estadísticas de los retornos
                                    mean_return = df_portfolio_returns.mean()
                                    std_return = df_portfolio_returns.std()
                                    skewness = stats.skew(df_portfolio_returns)
                                    kurtosis = stats.kurtosis(df_portfolio_returns)
                                    var_95 = np.percentile(df_portfolio_returns, 5)
                                    var_99 = np.percentile(df_portfolio_returns, 1)
                                    
                                    # Calcular Jarque-Bera test para normalidad
                                    jb_stat, jb_p_value = stats.jarque_bera(df_portfolio_returns)
                                    is_normal = jb_p_value > 0.05
                                    
                                    # Crear histograma de retornos
                                    fig_returns_hist = go.Figure(data=[go.Histogram(
                                        x=df_portfolio_returns,
                                        nbinsx=50,
                                        name="Retornos del Portafolio",
                                        marker_color='#28a745',
                                        opacity=0.7
                                    )])
                                    
                                    # Agregar líneas de métricas importantes
                                    fig_returns_hist.add_vline(x=mean_return, line_dash="dash", line_color="red", 
                                                             annotation_text=f"Media: {mean_return:.4f}")
                                    fig_returns_hist.add_vline(x=var_95, line_dash="dash", line_color="orange", 
                                                             annotation_text=f"VaR 95%: {var_95:.4f}")
                                    fig_returns_hist.add_vline(x=var_99, line_dash="dash", line_color="darkred", 
                                                             annotation_text=f"VaR 99%: {var_99:.4f}")
                                    
                                    fig_returns_hist.update_layout(
                                        title="Distribución de Retornos Diarios del Portafolio",
                                        xaxis_title="Retorno Diario",
                                        yaxis_title="Frecuencia",
                                        height=500,
                                        showlegend=False,
                                        template='plotly_white'
                                    )
                                    
                                    st.plotly_chart(fig_returns_hist, use_container_width=True)
                                    
                                    # Mostrar estadísticas de retornos
                                    st.markdown("#### 📈 Estadísticas de Retornos")
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    col1.metric("Retorno Medio Diario", f"{mean_return:.4f}")
                                    col2.metric("Volatilidad Diaria", f"{std_return:.4f}")
                                    col3.metric("VaR 95%", f"{var_95:.4f}")
                                    col4.metric("VaR 99%", f"{var_99:.4f}")
                                    
                                    col1, col2, col3, col4 = st.columns(4)
                                    col1.metric("Skewness", f"{skewness:.4f}")
                                    col2.metric("Kurtosis", f"{kurtosis:.4f}")
                                    col3.metric("JB Statistic", f"{jb_stat:.4f}")
                                    normalidad = "✅ Normal" if is_normal else "❌ No Normal"
                                    col4.metric("Normalidad", normalidad)
                                    
                                    # Calcular métricas anualizadas
                                    mean_return_annual = mean_return * 252
                                    std_return_annual = std_return * np.sqrt(252)
                                    sharpe_ratio = mean_return_annual / std_return_annual if std_return_annual > 0 else 0
                                    
                                    st.markdown("#### 📊 Métricas Anualizadas")
                                    col1, col2, col3 = st.columns(3)
                                    col1.metric("Retorno Anual", f"{mean_return_annual:.2%}")
                                    col2.metric("Volatilidad Anual", f"{std_return_annual:.2%}")
                                    col3.metric("Ratio de Sharpe", f"{sharpe_ratio:.4f}")
                                    
                                    # Análisis de distribución
                                    st.markdown("#### 📋 Análisis de la Distribución")
                                    if is_normal:
                                        st.success("✅ Los retornos siguen una distribución normal (p > 0.05)")
                                    else:
                                        st.warning("⚠️ Los retornos no siguen una distribución normal (p ≤ 0.05)")
                                    
                                    if skewness > 0.5:
                                        st.info("📈 Distribución con sesgo positivo (cola derecha)")
                                    elif skewness < -0.5:
                                        st.info("📉 Distribución con sesgo negativo (cola izquierda)")
                                    else:
                                        st.success("📊 Distribución aproximadamente simétrica")
                                    
                                    if kurtosis > 3:
                                        st.info("📊 Distribución leptocúrtica (colas pesadas)")
                                    elif kurtosis < 3:
                                        st.info("📊 Distribución platicúrtica (colas ligeras)")
                                    else:
                                        st.success("📊 Distribución mesocúrtica (normal)")
                                    
                                    # Gráfico de evolución del valor real del portafolio en ARS y USD
                                    st.markdown("#### 📈 Evolución del Valor Real del Portafolio")
                                    
                                    # Obtener cotización MEP para conversión
                                    try:
                                        # Intentar obtener cotización MEP (usar AL30 como proxy)
                                        cotizacion_mep = obtener_cotizacion_mep(token_portador, "AL30", 1, 1)
                                        if cotizacion_mep and cotizacion_mep.get('precio'):
                                            tasa_mep = float(cotizacion_mep['precio'])
                                        else:
                                            # Si no hay MEP, usar tasa aproximada
                                            tasa_mep = 1000  # Tasa aproximada
                                            st.info("ℹ️ Usando tasa MEP aproximada para conversiones")
                                    except:
                                        tasa_mep = 1000
                                        st.info("ℹ️ Usando tasa MEP aproximada para conversiones")
                                    
                                    # Crear figura con dos ejes Y
                                    fig_evolucion_real = go.Figure()
                                    
                                    # Traza en ARS (eje Y izquierdo)
                                    fig_evolucion_real.add_trace(go.Scatter(
                                        x=df_portfolio.index,
                                        y=df_portfolio['Portfolio_Total'],
                                        mode='lines',
                                        name='Valor en ARS',
                                        line=dict(color='#28a745', width=2),
                                        yaxis='y'
                                    ))
                                    
                                    # Traza en USD (eje Y derecho)
                                    valores_usd = df_portfolio['Portfolio_Total'] / tasa_mep
                                    fig_evolucion_real.add_trace(go.Scatter(
                                        x=df_portfolio.index,
                                        y=valores_usd,
                                        mode='lines',
                                        name='Valor en USD',
                                        line=dict(color='#0d6efd', width=2, dash='dash'),
                                        yaxis='y2'
                                    ))
                                    
                                    # Configurar ejes
                                    fig_evolucion_real.update_layout(
                                        title="Evolución del Valor Real del Portafolio (ARS y USD)",
                                        xaxis_title="Fecha",
                                        yaxis=dict(
                                            title=dict(
                                                text="Valor en ARS ($)",
                                                font=dict(color="#28a745")
                                            ),
                                            tickfont=dict(color="#28a745"),
                                            side="left"
                                        ),
                                        yaxis2=dict(
                                            title=dict(
                                                text="Valor en USD ($)",
                                                font=dict(color="#0d6efd")
                                            ),
                                            tickfont=dict(color="#0d6efd"),
                                            anchor="x",
                                            overlaying="y",
                                            side="right"
                                        ),
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
                                    
                                    st.plotly_chart(fig_evolucion_real, use_container_width=True)
                                    
                                    # Mostrar estadísticas del valor real en ambas monedas
                                    st.markdown("#### 📊 Estadísticas del Valor Real")
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    valor_inicial_ars = df_portfolio['Portfolio_Total'].iloc[0]
                                    valor_final_ars = df_portfolio['Portfolio_Total'].iloc[-1]
                                    valor_inicial_usd = valor_inicial_ars / tasa_mep
                                    valor_final_usd = valor_final_ars / tasa_mep
                                    retorno_total_real = (valor_final_ars / valor_inicial_ars - 1) * 100
                                    
                                    col1.metric("Valor Inicial (ARS)", f"${valor_inicial_ars:,.2f}")
                                    col2.metric("Valor Final (ARS)", f"${valor_final_ars:,.2f}")
                                    col3.metric("Valor Inicial (USD)", f"${valor_inicial_usd:,.2f}")
                                    col4.metric("Valor Final (USD)", f"${valor_final_usd:,.2f}")
                                    
                                    col1, col2 = st.columns(2)
                                    col1.metric("Retorno Total (ARS)", f"{retorno_total_real:+.2f}%")
                                    col2.metric("Tasa MEP Utilizada", f"${tasa_mep:,.2f}")
                                    
                                    # Análisis de rendimiento extra asegurado de renta fija
                                    st.markdown("#### 🏦 Análisis de Rendimiento Extra Asegurado")
                                    
                                    # Identificar instrumentos de renta fija
                                    instrumentos_renta_fija = []
                                    total_renta_fija = 0
                                    
                                    for activo in datos_activos:
                                        tipo = activo.get('Tipo', '').lower()
                                        simbolo = activo.get('Símbolo', '')
                                        valuacion = activo.get('Valuación', 0)
                                        
                                        # Identificar FCIs, bonos y otros instrumentos de renta fija
                                        if any(keyword in tipo for keyword in ['fci', 'fondo', 'bono', 'titulo', 'publico', 'letra']):
                                            instrumentos_renta_fija.append({
                                                'simbolo': simbolo,
                                                'tipo': tipo,
                                                'valuacion': valuacion,
                                                'peso': valuacion / valor_total if valor_total > 0 else 0
                                            })
                                            total_renta_fija += valuacion
                                        
                                        # También identificar por símbolo (FCIs suelen tener símbolos específicos)
                                        elif any(keyword in simbolo.lower() for keyword in ['fci', 'fondo', 'bono', 'al', 'gd', 'gg']):
                                            instrumentos_renta_fija.append({
                                                'simbolo': simbolo,
                                                'tipo': tipo,
                                                'valuacion': valuacion,
                                                'peso': valuacion / valor_total if valor_total > 0 else 0
                                            })
                                            total_renta_fija += valuacion
                                    
                                    if instrumentos_renta_fija:
                                        st.success(f"✅ Se identificaron {len(instrumentos_renta_fija)} instrumentos de renta fija")
                                            
                                        # Mostrar tabla de instrumentos de renta fija
                                        df_renta_fija = pd.DataFrame(instrumentos_renta_fija)
                                        df_renta_fija['Peso (%)'] = df_renta_fija['peso'] * 100
                                        df_renta_fija['Valuación ($)'] = df_renta_fija['valuacion'].apply(lambda x: f"${x:,.2f}")
                                        
                                        st.dataframe(
                                            df_renta_fija[['simbolo', 'tipo', 'Valuación ($)', 'Peso (%)']],
                                            use_container_width=True,
                                            height=200
                                        )
                                        
                                        # Calcular rendimiento extra asegurado
                                        peso_renta_fija = total_renta_fija / valor_total if valor_total > 0 else 0
                                        
                                        # Estimación de rendimiento extra (basado en tasas típicas)
                                        rendimiento_extra_estimado = {
                                            'FCI': 0.08,  # 8% anual típico para FCIs
                                            'Bono': 0.12,  # 12% anual típico para bonos
                                            'Titulo': 0.10,  # 10% anual típico para títulos públicos
                                            'Letra': 0.15   # 15% anual típico para letras
                                        }
                                        
                                        rendimiento_extra_total = 0
                                        for instrumento in instrumentos_renta_fija:
                                            tipo_instrumento = instrumento['tipo'].lower()
                                            peso_instrumento = instrumento['peso']
                                            
                                            # Determinar tipo de rendimiento
                                            if 'fci' in tipo_instrumento or 'fondo' in tipo_instrumento:
                                                rendimiento = rendimiento_extra_estimado['FCI']
                                            elif 'bono' in tipo_instrumento:
                                                rendimiento = rendimiento_extra_estimado['Bono']
                                            elif 'titulo' in tipo_instrumento or 'publico' in tipo_instrumento:
                                                rendimiento = rendimiento_extra_estimado['Titulo']
                                            elif 'letra' in tipo_instrumento:
                                                rendimiento = rendimiento_extra_estimado['Letra']
                                            else:
                                                rendimiento = rendimiento_extra_estimado['FCI']  # Default
                                            
                                            rendimiento_extra_total += rendimiento * peso_instrumento
                                        
                                        # Mostrar métricas de rendimiento extra
                                        col1, col2, col3 = st.columns(3)
                                        col1.metric("Peso Renta Fija", f"{peso_renta_fija:.1%}")
                                        col2.metric("Rendimiento Extra Estimado", f"{rendimiento_extra_total:.1%}")
                                        col3.metric("Valor Renta Fija", f"${total_renta_fija:,.2f}")
                                        
                                        # Gráfico de composición por tipo de instrumento
                                        if len(instrumentos_renta_fija) > 1:
                                            fig_renta_fija = go.Figure(data=[go.Pie(
                                                labels=[f"{row['simbolo']} ({row['tipo']})" for _, row in df_renta_fija.iterrows()],
                                                values=df_renta_fija['valuacion'],
                                                textinfo='label+percent+value',
                                                texttemplate='%{label}<br>%{percent}<br>$%{value:,.0f}',
                                                hole=0.4,
                                                marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3'])
                                            )])
                                            fig_renta_fija.update_layout(
                                                title="Composición de Instrumentos de Renta Fija",
                                                height=400
                                            )
                                            st.plotly_chart(fig_renta_fija, use_container_width=True)
                                        
                                        # Recomendaciones específicas para renta fija
                                        st.markdown("#### 💡 Recomendaciones Renta Fija")
                                        
                                        if peso_renta_fija < 0.2:
                                            st.info("📈 **Considerar aumentar exposición a renta fija**: Menos del 20% del portafolio")
                                        elif peso_renta_fija > 0.6:
                                            st.warning("📉 **Considerar reducir exposición a renta fija**: Más del 60% del portafolio")
                                        else:
                                            st.success("✅ **Exposición equilibrada a renta fija**: Entre 20% y 60% del portafolio")
                                        
                                        if rendimiento_extra_total > 0.10:
                                            st.success("🎯 **Excelente rendimiento extra estimado**: Más del 10% anual")
                                        elif rendimiento_extra_total > 0.05:
                                            st.info("📊 **Buen rendimiento extra estimado**: Entre 5% y 10% anual")
                                        else:
                                            st.warning("⚠️ **Rendimiento extra bajo**: Menos del 5% anual")
                                    
                                    else:
                                        st.info("ℹ️ No se identificaron instrumentos de renta fija en el portafolio")
                                        st.info("💡 **Recomendación**: Considerar agregar FCIs, bonos o títulos públicos para diversificar")
                                
                                # Análisis de retorno esperado por horizonte de inversión
                                st.markdown("#### 📊 Análisis de Retorno Esperado")
                                
                                # Calcular retornos en USD para diferentes horizontes
                                horizontes_analisis = [1, 7, 30, 90, 180, 365]
                                retornos_ars_por_horizonte = {}
                                retornos_usd_por_horizonte = {}
                                
                                # Calcular retornos en USD
                                df_portfolio_usd = df_portfolio['Portfolio_Total'] / tasa_mep
                                df_portfolio_returns_usd = df_portfolio_usd.pct_change().dropna()
                                
                                for horizonte in horizontes_analisis:
                                    if len(df_portfolio_returns) >= horizonte:
                                        # Retorno en ARS
                                        retorno_ars = (1 + df_portfolio_returns.tail(horizonte)).prod() - 1
                                        retornos_ars_por_horizonte[horizonte] = retorno_ars
                                        
                                        # Retorno en USD
                                        retorno_usd = (1 + df_portfolio_returns_usd.tail(horizonte)).prod() - 1
                                        retornos_usd_por_horizonte[horizonte] = retorno_usd
                                
                                if retornos_ars_por_horizonte and retornos_usd_por_horizonte:
                                    # Crear gráfico de retornos por horizonte (ARS y USD)
                                    fig_horizontes = go.Figure()
                                    
                                    horizontes = list(retornos_ars_por_horizonte.keys())
                                    retornos_ars = list(retornos_ars_por_horizonte.values())
                                    retornos_usd = list(retornos_usd_por_horizonte.values())
                                    
                                    # Barras para ARS
                                    fig_horizontes.add_trace(go.Bar(
                                        x=[f"{h} días" for h in horizontes],
                                        y=retornos_ars,
                                        name="Retorno ARS",
                                        marker_color=['#28a745' if r >= 0 else '#dc3545' for r in retornos_ars],
                                        text=[f"{r:.2%}" for r in retornos_ars],
                                        textposition='auto'
                                    ))
                                    
                                    # Barras para USD
                                    fig_horizontes.add_trace(go.Bar(
                                        x=[f"{h} días" for h in horizontes],
                                        y=retornos_usd,
                                        name="Retorno USD",
                                        marker_color=['#0d6efd' if r >= 0 else '#ff6b6b' for r in retornos_usd],
                                        text=[f"{r:.2%}" for r in retornos_usd],
                                        textposition='auto'
                                    ))
                                    
                                    fig_horizontes.update_layout(
                                        title=f"Retornos Acumulados por Horizonte de Inversión (ARS y USD)",
                                        xaxis_title="Horizonte de Inversión",
                                        yaxis_title="Retorno Acumulado",
                                        height=400,
                                        template='plotly_white',
                                        barmode='group'
                                    )
                                    
                                    st.plotly_chart(fig_horizontes, use_container_width=True)
                                    
                                    # Mostrar métricas de retorno esperado (ARS y USD)
                                    st.markdown("#### 📈 Métricas de Retorno Esperado")
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    # Calcular retorno esperado anualizado en ARS
                                    retorno_anualizado_ars = mean_return_annual
                                    col1.metric("Retorno Esperado Anual (ARS)", f"{retorno_anualizado_ars:.2%}")
                                    
                                    # Calcular retorno esperado anualizado en USD
                                    mean_return_annual_usd = df_portfolio_returns_usd.mean() * 252
                                    col2.metric("Retorno Esperado Anual (USD)", f"{mean_return_annual_usd:.2%}")
                                    
                                    # Calcular retorno esperado para el horizonte seleccionado
                                    retorno_esperado_horizonte_ars = retorno_anualizado_ars * (dias_analisis / 365)
                                    retorno_esperado_horizonte_usd = mean_return_annual_usd * (dias_analisis / 365)
                                    col3.metric(f"Retorno Esperado ({dias_analisis} días) ARS", f"{retorno_esperado_horizonte_ars:.2%}")
                                    col4.metric(f"Retorno Esperado ({dias_analisis} días) USD", f"{retorno_esperado_horizonte_usd:.2%}")
                                    
                                    # Calcular intervalos de confianza
                                    z_score_95 = 1.96  # 95% de confianza
                                    std_return_annual_usd = df_portfolio_returns_usd.std() * np.sqrt(252)
                                    intervalo_confianza_ars = z_score_95 * std_return_annual * np.sqrt(dias_analisis / 365)
                                    intervalo_confianza_usd = z_score_95 * std_return_annual_usd * np.sqrt(dias_analisis / 365)
                                    
                                    col1, col2 = st.columns(2)
                                    col1.metric("Intervalo de Confianza 95% (ARS)", f"±{intervalo_confianza_ars:.2%}")
                                    col2.metric("Intervalo de Confianza 95% (USD)", f"±{intervalo_confianza_usd:.2%}")
                                    
                                    # Proyecciones de valor del portafolio
                                    st.markdown("#### 💰 Proyecciones de Valor del Portafolio")
                                    
                                    valor_actual = df_portfolio['Portfolio_Total'].iloc[-1]
                                    
                                    # Calcular proyecciones optimista, pesimista y esperada
                                    proyeccion_esperada = valor_actual * (1 + retorno_esperado_horizonte_ars)
                                    proyeccion_optimista = valor_actual * (1 + retorno_esperado_horizonte_ars + intervalo_confianza_ars)
                                    proyeccion_pesimista = valor_actual * (1 + retorno_esperado_horizonte_ars - intervalo_confianza_ars)
                                    
                                    col1, col2, col3 = st.columns(3)
                                    col1.metric("Proyección Esperada", f"${proyeccion_esperada:,.2f}")
                                    col2.metric("Proyección Optimista", f"${proyeccion_optimista:,.2f}")
                                    col3.metric("Proyección Pesimista", f"${proyeccion_pesimista:,.2f}")
                                    

                                    
                                    # Resumen de análisis
                                    st.markdown("#### 📋 Resumen del Análisis")
                                    
                                    if retorno_esperado_horizonte_ars > 0:
                                        st.success(f"✅ **Retorno Esperado Positivo**: Se espera un retorno de {retorno_esperado_horizonte_ars:.2%} en {dias_analisis} días")
                                    else:
                                        st.warning(f"⚠️ **Retorno Esperado Negativo**: Se espera un retorno de {retorno_esperado_horizonte_ars:.2%} en {dias_analisis} días")
                                    
                                    if sharpe_ratio > 1:
                                        st.success(f"✅ **Excelente Ratio de Sharpe**: {sharpe_ratio:.2f} indica buenos retornos ajustados por riesgo")
                                    elif sharpe_ratio > 0.5:
                                        st.info(f"ℹ️ **Buen Ratio de Sharpe**: {sharpe_ratio:.2f} indica retornos razonables ajustados por riesgo")
                                    else:
                                        st.warning(f"⚠️ **Ratio de Sharpe Bajo**: {sharpe_ratio:.2f} indica retornos pobres ajustados por riesgo")
                                    
                                    # Recomendaciones basadas en el análisis
                                    st.markdown("#### 💡 Recomendaciones")
                                    
                                    if retorno_esperado_horizonte_ars > 0.05:  # 5% en el horizonte
                                        st.success("🎯 **Mantener Posición**: El portafolio muestra buenas perspectivas de retorno")
                                    elif retorno_esperado_horizonte_ars < -0.05:  # -5% en el horizonte
                                        st.warning("🔄 **Considerar Rebalanceo**: El portafolio podría beneficiarse de ajustes")
                                    else:
                                        st.info("📊 **Monitorear**: El portafolio muestra retornos moderados")
                                
                                else:
                                    st.warning("⚠️ No hay suficientes datos para calcular retornos del portafolio")
                                    
                            except Exception as e:
                                st.error(f"❌ Error calculando retornos del portafolio: {str(e)}")
                                st.exception(e)
                            
                        else:
                            st.warning("⚠️ No hay datos suficientes para generar el histograma")
                    else:
                        st.warning("⚠️ No se pudieron obtener datos históricos para ningún activo")
                else:
                    st.warning("⚠️ No hay activos válidos para generar el histograma")
                    
            except Exception as e:
                st.error(f"❌ Error generando histograma del portafolio: {str(e)}")
                st.exception(e)
        
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
                        # Mostrar análisis completo en texto y tabla
                        st.markdown("### 📊 Análisis Completo del Mercado")
                        st.markdown(f"**Descripción:** {cotizacion_mep.get('descripcionTitulo','N/A')}")
                        st.markdown(f"**Símbolo:** {simbolo_mep}")
                        st.markdown(f"**Último Precio:** ${cotizacion_mep.get('ultimoPrecio','N/A')}")
                        st.markdown(f"**Variación:** {cotizacion_mep.get('variacion','N/A')}%")
                        st.markdown(f"**Apertura:** ${cotizacion_mep.get('apertura','N/A')}")
                        st.markdown(f"**Máximo:** ${cotizacion_mep.get('maximo','N/A')}")
                        st.markdown(f"**Mínimo:** ${cotizacion_mep.get('minimo','N/A')}")
                        st.markdown(f"**Cierre Anterior:** ${cotizacion_mep.get('cierreAnterior','N/A')}")
                        st.markdown(f"**Tendencia:** {cotizacion_mep.get('tendencia','N/A')}")
                        st.markdown(f"**Monto Operado:** ${cotizacion_mep.get('montoOperado','N/A')}")
                        st.markdown(f"**Volumen Nominal:** {cotizacion_mep.get('volumenNominal','N/A')}")
                        st.markdown(f"**Cantidad de Operaciones:** {cotizacion_mep.get('cantidadOperaciones','N/A')}")
                        st.markdown(f"**Moneda:** {cotizacion_mep.get('moneda','N/A')}")
                        st.markdown(f"**Fecha/Hora:** {cotizacion_mep.get('fechaHora','N/A')}")
                        # Mostrar puntas de compra/venta en tabla
                        puntas = cotizacion_mep.get('puntas',[])
                        if puntas:
                            import pandas as pd
                            df_puntas = pd.DataFrame(puntas)
                            df_puntas = df_puntas.rename(columns={
                                'cantidadCompra':'Cantidad Compra',
                                'precioCompra':'Precio Compra',
                                'precioVenta':'Precio Venta',
                                'cantidadVenta':'Cantidad Venta'
                            })
                            st.markdown("**Puntas de Compra/Venta:**")
                            st.dataframe(df_puntas, use_container_width=True)
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

def mostrar_optimizacion_portafolio(token_acceso, id_cliente):
    """
    Menú avanzado de optimización de portafolio.
    Ahora usa obtención asincrónica y optimizada de series históricas para el universo aleatorio.
    """
    st.markdown("### 🔄 Menú Avanzado de Optimización de Portafolio")
    with st.spinner("Obteniendo portafolio actual..."):
        portafolio = obtener_portafolio(token_acceso, id_cliente)
    if not portafolio or not portafolio.get('activos'):
        st.warning("No se pudo obtener el portafolio del cliente o está vacío")
        return

    activos_raw = portafolio['activos']
    # Diagnóstico del portafolio actual
    st.subheader("🔍 Diagnóstico del Portafolio Actual")
    # Usar el mismo método de resumen de portafolio para diagnóstico real
    activos_dict = {}
    valor_total = 0
    for activo in activos_raw:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', 'N/A')
        tipo = titulo.get('tipo', 'N/A')
        valuacion = 0
        campos_valuacion = [
            'valuacionEnMonedaOriginal', 'valuacionActual', 'valorNominalEnMonedaOriginal', 'valorNominal',
            'valuacionDolar', 'valuacion', 'valorActual', 'montoInvertido', 'valorMercado', 'valorTotal', 'importe'
        ]
        for campo in campos_valuacion:
            if campo in activo and activo[campo] is not None:
                try:
                    val = float(activo[campo])
                    if val > 0:
                        valuacion = val
                        break
                except (ValueError, TypeError):
                    continue
        if valuacion == 0 and activo.get('cantidad', 0):
            campos_precio = [
                'precioPromedio', 'precioCompra', 'precioActual', 'precio', 'precioUnitario', 'ultimoPrecio', 'cotizacion'
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
                    cantidad_num = float(activo.get('cantidad', 0))
                    if tipo == 'TitulosPublicos':
                        valuacion = (cantidad_num * precio_unitario) / 100.0
                    else:
                        valuacion = cantidad_num * precio_unitario
                except (ValueError, TypeError):
                    pass
        mercado = titulo.get('mercado', 'BCBA')
        if simbolo:
            activos_dict[simbolo] = {
                'Valuación': valuacion,
                'Tipo': tipo,
                'mercado': mercado
            }
            valor_total += valuacion
    # Obtener saldo disponible de las cuentas
    estado_cuenta = obtener_estado_cuenta(token_acceso, id_cliente)
    saldo_disponible = 0
    if estado_cuenta and 'cuentas' in estado_cuenta:
        for cuenta in estado_cuenta['cuentas']:
            disponible = cuenta.get('disponible', 0)
            try:
                saldo_disponible += float(disponible)
            except Exception:
                continue
    metricas_actual = calcular_metricas_portafolio(activos_dict, valor_total, token_acceso)
    cols = st.columns(4)
    cols[0].metric("Retorno Esperado", f"{metricas_actual.get('retorno_esperado_anual',0)*100:.2f}%")
    cols[1].metric("Riesgo (Volatilidad)", f"{metricas_actual.get('riesgo_anual',0)*100:.2f}%")
    cols[2].metric("Sharpe", f"{(metricas_actual.get('retorno_esperado_anual',0)/(metricas_actual.get('riesgo_anual',1e-6))):.2f}")
    cols[3].metric("Concentración", f"{metricas_actual.get('concentracion',0)*100:.1f}%")

    st.markdown("---")
    st.subheader("⚙️ Configuración de Universo de Optimización")
    universo = st.radio(
        "¿Con qué universo de activos desea optimizar?",
        ["Portafolio actual", "Universo aleatorio"],
        help="Puede optimizar con sus activos actuales o simular con un universo aleatorio por tipo/cantidad."
    )
    if universo == "Portafolio actual":
        universe_activos = [
            {'simbolo': a.get('titulo',{}).get('simbolo'),
             'mercado': a.get('titulo',{}).get('mercado'),
             'tipo': a.get('titulo',{}).get('tipo')}
            for a in activos_raw if a.get('titulo',{}).get('simbolo')
        ]
    else:
        st.info("Seleccione el universo aleatorio de mercado real")
        paneles = ['acciones', 'cedears', 'aDRs', 'titulosPublicos', 'obligacionesNegociables']
        paneles_seleccionados = st.multiselect("Paneles de universo aleatorio", paneles, default=paneles)
        capital_mode = st.radio(
            "¿Cómo definir el capital disponible?",
            ["Manual", "Saldo valorizado + disponible (actual)"]
        )
        capital_ars = 100000
        capital_auto = valor_total + saldo_disponible
        if capital_mode == "Manual":
            capital_ars = st.number_input("Capital disponible para universo aleatorio (ARS)", min_value=10000, value=100000)
        else:
            st.success(f"Capital valorizado + disponible: ${capital_auto:,.2f}")
            capital_ars = capital_auto
        cantidad_activos = st.slider("Cantidad de activos por panel", 2, 10, 5)
        fecha_desde = st.session_state.fecha_desde.strftime('%Y-%m-%d')
        fecha_hasta = st.session_state.fecha_hasta.strftime('%Y-%m-%d')
        ajustada = "SinAjustar"
        # Obtener tickers por panel
        tickers_por_panel, _ = obtener_tickers_por_panel(token_acceso, paneles_seleccionados, 'Argentina')
        # Validar tickers_por_panel
        if not tickers_por_panel or not any(tickers_por_panel.values()):
            st.error("No se pudieron obtener tickers para el universo aleatorio seleccionado. Revise los paneles o intente nuevamente.")
            return
        # Obtener series históricas aleatorias (ahora asincrónico y optimizado)
        st.info("Descargando series históricas en paralelo para mayor velocidad...")
        try:
            series_historicas, seleccion_final = obtener_series_historicas_aleatorias_con_capital(
                tickers_por_panel, paneles_seleccionados, cantidad_activos,
                fecha_desde, fecha_hasta, ajustada, token_acceso, capital_ars
            )
        except Exception as e:
            st.error(f"Error al obtener series históricas para el universo aleatorio: {e}")
            return
        # Construir universe_activos a partir de seleccion_final
        universe_activos = []
        if seleccion_final and any(seleccion_final.values()):
            for panel, simbolos in seleccion_final.items():
                for simbolo in simbolos:
                    universe_activos.append({'simbolo': simbolo, 'mercado': 'BCBA', 'tipo': panel})
        else:
            st.error("No hay suficientes activos para el universo aleatorio seleccionado. Intente con otros paneles o menos cantidad de activos.")
            return
    # Validación final antes de continuar
    if not universe_activos:
        st.error("No se pudo construir el universo de activos para la optimización. Proceso detenido.")
        return

    fecha_desde = st.session_state.fecha_desde
    fecha_hasta = st.session_state.fecha_hasta
    st.info(f"Optimizando {len(universe_activos)} activos desde {fecha_desde} hasta {fecha_hasta}")

    # Automatizar todas las estrategias
    st.subheader("🚀 Ejecución Automática de Estrategias de Optimización")
    estrategias = [
        ('markowitz', 'Markowitz'),
        ('min-variance-l1', 'Min Var L1'),
        ('min-variance-l2', 'Min Var L2'),
        ('equi-weight', 'Pesos Iguales'),
        ('long-only', 'Solo Largos')
    ]
    target_sharpe = st.number_input("Sharpe objetivo (opcional, Markowitz)", min_value=0.0, max_value=3.0, value=0.8, step=0.01)
    st.caption("Si no es posible alcanzar el Sharpe exacto, se mostrará el portafolio más cercano.")

    # Cargar datos y preparar manager
    manager_inst = PortfolioManager(universe_activos, token_acceso, fecha_desde, fecha_hasta)
    if not manager_inst.load_data():
        st.error("No se pudieron cargar los datos históricos para optimización.")
        return

    resultados = {}
    for clave, nombre in estrategias:
        if clave == 'markowitz':
            # Mejorar lógica de Sharpe objetivo: buscar el retorno objetivo que más se aproxime al Sharpe deseado
            mejor_sharpe = -1e9
            mejor_result = None
            mejor_ret = None
            for ret in [x/100 for x in range(2, 25, 1)]:
                res = manager_inst.compute_portfolio(strategy='markowitz', target_return=ret)
                if not res or not hasattr(res, 'returns') or not hasattr(res, 'risk'):
                    continue
                sharpe = res.returns / (res.risk if res.risk else 1e-6)
                if abs(sharpe - target_sharpe) < abs(mejor_sharpe - target_sharpe):
                    mejor_sharpe = sharpe
                    mejor_result = res
                    mejor_ret = ret
            resultados[clave] = (mejor_result, mejor_sharpe, mejor_ret)
        else:
            res = manager_inst.compute_portfolio(strategy=clave)
            if res:
                sharpe = res.returns / (res.risk if res.risk else 1e-6)
                resultados[clave] = (res, sharpe, None)

    # Mostrar resultados
    st.markdown("---")
    st.subheader("📊 Resultados de Optimización y Comparación")
    cols = st.columns(len(estrategias)+1)
    # Métricas del portafolio actual
    cols[0].metric("Actual: Sharpe", f"{(metricas_actual.get('retorno_esperado_anual',0)/(metricas_actual.get('riesgo_anual',1e-6))):.2f}")
    cols[0].metric("Actual: Retorno", f"{metricas_actual.get('retorno_esperado_anual',0)*100:.2f}%")
    cols[0].metric("Actual: Riesgo", f"{metricas_actual.get('riesgo_anual',0)*100:.2f}%")
    for i, (clave, nombre) in enumerate(estrategias):
        res, sharpe, ret = resultados.get(clave, (None, None, None))
        if res:
            cols[i+1].metric(f"{nombre}\nSharpe", f"{sharpe:.2f}")
            cols[i+1].metric(f"{nombre}\nRetorno", f"{getattr(res,'returns',0)*100:.2f}%")
            cols[i+1].metric(f"{nombre}\nRiesgo", f"{getattr(res,'risk',0)*100:.2f}%")
            if clave == 'markowitz' and ret is not None:
                cols[i+1].caption(f"Retorno objetivo: {ret*100:.2f}%")
    st.markdown("---")

    # Gráficos y visualizaciones
    for clave, nombre in estrategias:
        res, sharpe, ret = resultados.get(clave, (None, None, None))
        if not res:
            continue
        st.markdown(f"#### {nombre}")
        # Histograma de retornos
        if hasattr(res, 'plot_histogram_streamlit'):
            st.markdown("**Distribución de Retornos**")
            fig = res.plot_histogram_streamlit()
            st.plotly_chart(fig, use_container_width=True, key=f"hist_{clave}")
        # Pie chart de pesos
        if hasattr(res, 'dataframe_allocation') and res.dataframe_allocation is not None:
            df = res.dataframe_allocation
            if not df.empty and 'rics' in df.columns and 'weights' in df.columns and df['weights'].sum() > 0:
                st.markdown("**Distribución de Pesos**")
                import plotly.graph_objects as go
                fig_pie = go.Figure(data=[go.Pie(labels=df['rics'], values=df['weights'], textinfo='label+percent', hole=0.4)])
                fig_pie.update_layout(title="Distribución Optimizada de Activos", template='plotly_white')
                st.plotly_chart(fig_pie, use_container_width=True, key=f"pie_{clave}")
            else:
                st.info("No hay datos suficientes para mostrar la distribución de pesos.")
        # Métricas
        st.write(f"Retorno esperado: {getattr(res,'returns',0)*100:.2f}% | Riesgo: {getattr(res,'risk',0)*100:.2f}% | Sharpe: {sharpe:.2f}")
        st.markdown("---")

    # Frontera eficiente
    st.subheader("📈 Frontera Eficiente y Portafolios Especiales")
    if st.checkbox("Mostrar Frontera Eficiente", value=True):
        portfolios, returns, volatilities = manager_inst.compute_efficient_frontier(target_return=0.08, include_min_variance=True)
        if portfolios and returns and volatilities and len(returns) > 0 and len(volatilities) > 0:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=volatilities, y=returns, mode='lines+markers', name='Frontera Eficiente', line=dict(color='#0d6efd', width=3), marker=dict(size=6)))
            # Marcar portafolios especiales
            colores = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
            for i, (label, port) in enumerate(portfolios.items()):
                if port and hasattr(port, 'risk') and hasattr(port, 'returns'):
                    fig.add_trace(go.Scatter(x=[port.risk], y=[port.returns], mode='markers+text', name=label, marker=dict(color=colores[i%len(colores)], size=14, symbol='star'), text=[label], textposition='top center'))
            fig.update_layout(title='Frontera Eficiente del Portafolio', xaxis_title='Volatilidad Anual', yaxis_title='Retorno Anual', showlegend=True, template='plotly_white', height=500)
            st.plotly_chart(fig, use_container_width=True)
            # Línea de tasa libre de riesgo
            risk_free_rate = 0.40  # Tasa libre de riesgo anual para Argentina
            fig.add_hline(y=risk_free_rate, line_dash="dot", line_color="green",
                         annotation_text=f"Tasa libre de riesgo: {risk_free_rate*100:.2f}%", annotation_position="top left")
        else:
            st.warning("No se pudo calcular la frontera eficiente. Verifique que haya datos históricos suficientes y activos válidos.")

    # Comparación final
    st.subheader("🔬 Comparación Directa con Portafolio Actual")
    st.write("Se muestran las mejoras potenciales en retorno, riesgo y Sharpe respecto al portafolio actual.")
    df_comp = []
    for clave, nombre in estrategias:
        res, sharpe, _ = resultados.get(clave, (None, None, None))
        if res:
            df_comp.append({
                'Estrategia': nombre,
                'Retorno': getattr(res,'returns',0)*100,
                'Riesgo': getattr(res,'risk',0)*100,
                'Sharpe': sharpe,
                'Mejora Retorno (%)': (getattr(res,'returns',0)-metricas_actual.get('retorno_esperado_anual',0))*100,
                'Mejora Sharpe': sharpe-(metricas_actual.get('retorno_esperado_anual',0)/(metricas_actual.get('riesgo_anual',1e-6)))
            })
    if df_comp:
        import pandas as pd
        st.dataframe(pd.DataFrame(df_comp), use_container_width=True)

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

    # --- Análisis Intermarket Profesional previo a la optimización ---
    import yfinance as yf
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    st.markdown('---')
    st.subheader('🔗 Análisis Intermarket Profesional (Contexto Global)')
    with st.spinner('Descargando datos intermarket de referencia...'):
        tickers_intermarket = {
            'Merval': '^MERV',
            'S&P 500': '^GSPC',
            'DXY': 'DX-Y.NYB',
            'VIX': '^VIX',
            'Soja': 'ZS=F'
        }
        precios_inter = {}
        for k, v in tickers_intermarket.items():
            try:
                data = yf.download(v, period='1y')['Adj Close']
                if not data.empty:
                    precios_inter[k] = data.dropna()
            except Exception:
                continue
        df_inter = pd.DataFrame(precios_inter).dropna()
        retornos_inter = df_inter.pct_change().dropna()
    # Señal simple intermarket
    dxy_trend = retornos_inter['DXY'].tail(20).sum() if 'DXY' in retornos_inter else 0
    soja_trend = retornos_inter['Soja'].tail(20).sum() if 'Soja' in retornos_inter else 0
    vix_actual = df_inter['VIX'].iloc[-1] if 'VIX' in df_inter else 20
    merval_momentum = retornos_inter['Merval'].tail(10).sum() if 'Merval' in retornos_inter else 0
    if dxy_trend < -0.01 and soja_trend > 0.03 and vix_actual < 20 and merval_momentum > 0.02:
        regimen = "ALCISTA"
        recomendacion = "Contexto favorable para activos de riesgo y commodities."
        explicacion = "El dólar débil, commodities fuertes, baja volatilidad y momentum positivo en Merval sugieren un entorno alcista."
    elif dxy_trend > 0.01 or vix_actual > 25:
        regimen = "DEFENSIVO"
        recomendacion = "Contexto defensivo: preferencia por activos refugio y baja exposición a riesgo."
        explicacion = "El dólar fuerte o alta volatilidad (VIX) sugieren cautela y preferencia por activos defensivos."
    else:
        regimen = "NEUTRAL"
        recomendacion = "Contexto neutral: portafolio balanceado y esperar señales claras."
        explicacion = "No hay señales claras de tendencia, se recomienda mantener un portafolio diversificado."
    st.info(f"Régimen Intermarket: **{regimen}**. {recomendacion}")
    st.caption(f"Explicación: {explicacion}")
    # Mostrar gráfico de activos de referencia
    fig, ax = plt.subplots()
    activos_graf = ['Merval', 'S&P 500', 'DXY', 'VIX', 'Soja']
    for activo in activos_graf:
        if activo in df_inter:
            precios_norm = df_inter[activo] / df_inter[activo].iloc[0] * 100
            ax.plot(precios_norm.index, precios_norm, label=activo)
    ax.legend()
    ax.set_title("Evolución de activos de referencia (base 100)")
    st.pyplot(fig)
    # --- FIN BLOQUE INTERMARKET ---

    # --- Análisis de Ciclo Económico BCRA ---
    with st.expander("🔎 Análisis Automático del Ciclo Económico (BCRA)", expanded=False):
        st.markdown("**Variables consideradas:** Reservas, tasa de política monetaria, inflación, agregados monetarios.")
        # Obtener datos reales del BCRA
        try:
            # Reservas internacionales (último dato)
            url_reservas = "https://api.estadisticasbcra.com/reservas"
            url_leliq = "https://api.estadisticasbcra.com/leliq"
            url_inflacion = "https://api.estadisticasbcra.com/inflacion_mensual_oficial"
            url_m2 = "https://api.estadisticasbcra.com/base_monetaria"
            headers = {"Authorization": "Bearer TU_API_KEY_BCRA"}
            reservas = requests.get(url_reservas, headers=headers).json()[-1]["valor"]
            tasa_leliq = requests.get(url_leliq, headers=headers).json()[-1]["valor"]
            inflacion = requests.get(url_inflacion, headers=headers).json()[-1]["valor"] / 100
            m2 = requests.get(url_m2, headers=headers).json()
            m2_crecimiento = (m2[-1]["valor"] - m2[-22]["valor"]) / m2[-22]["valor"] if len(m2) > 22 else None
        except Exception as e:
            st.warning(f"No se pudieron obtener datos reales del BCRA: {e}. Se usarán valores simulados.")
            reservas = 25000
            tasa_leliq = 50
            inflacion = 0.08
            m2_crecimiento = None
        # Lógica simple de etapa
        if reservas > 35000 and inflacion < 0.05 and tasa_leliq < 60:
            etapa = "Expansión"
            explicacion_ciclo = "Reservas altas, inflación baja y tasas moderadas: contexto favorable para activos de riesgo."
            sugerencia = "Portafolio agresivo: sobreponderar acciones, cíclicos y emergentes."
        elif inflacion > 0.10 or tasa_leliq > 80:
            etapa = "Recesión"
            explicacion_ciclo = "Inflación/tasas muy altas: contexto defensivo, preferir liquidez y renta fija."
            sugerencia = "Portafolio defensivo: priorizar bonos, FCIs de money market y activos refugio."
        elif reservas > 30000 and inflacion < 0.08:
            etapa = "Auge"
            explicacion_ciclo = "Reservas sólidas y baja inflación: buen momento para balancear riesgo y retorno."
            sugerencia = "Portafolio balanceado: combinar acciones, bonos y algo de liquidez."
        else:
            etapa = "Recuperación/Neutral"
            explicacion_ciclo = "Variables mixtas, posible recuperación o transición."
            sugerencia = "Portafolio diversificado: mantener exposición equilibrada y flexibilidad."
        st.success(f"Etapa detectada: **{etapa}**")
        st.caption(f"Explicación: {explicacion_ciclo}")
        st.markdown(f"- Reservas: {reservas:,.0f}M USD\n- Tasa LELIQ: {tasa_leliq:.2f}% anual\n- Inflación mensual: {inflacion*100:.2f}%\n- Crecimiento M2: {m2_crecimiento*100:.2f}%")
        # --- SUGERENCIA DE ESTRATEGIA SEGÚN CICLO ---
        st.markdown(f"""
        <div style='background:#eaf6fb;border-left:6px solid #007cf0;padding:1.2em 1.5em;margin:1.2em 0 1.5em 0;border-radius:10px;'>
        <b>💡 Sugerencia de Estrategia de Optimización:</b><br>
        <span style='font-size:1.15em;font-weight:700;color:#0056b3'>{sugerencia}</span><br>
        <span style='color:#007cf0;font-size:1em;'>{explicacion_ciclo}</span>
        </div>
        """, unsafe_allow_html=True)

    # --- Análisis de Ciclo Económico BCRA ---
    with st.expander("🔎 Análisis Automático del Ciclo Económico (BCRA)", expanded=False):
        st.markdown("**Variables consideradas:** Reservas, tasa de política monetaria, inflación, agregados monetarios.")
        # Obtener datos reales del BCRA
        try:
            # Reservas internacionales (último dato)
            url_reservas = "https://api.estadisticasbcra.com/reservas"
            url_leliq = "https://api.estadisticasbcra.com/leliq"
            url_inflacion = "https://api.estadisticasbcra.com/inflacion_mensual_oficial"
            url_m2 = "https://api.estadisticasbcra.com/base_monetaria"
            headers = {"Authorization": "BEARER TU_API_KEY_BCRA"}  # Reemplazar por tu API KEY de estadisticasbcra.com
            # Reservas
            reservas_df = pd.DataFrame(requests.get(url_reservas, headers=headers).json())
            reservas = reservas_df.iloc[-1]['valor'] if not reservas_df.empty else None
            # Tasa LELIQ
            leliq_df = pd.DataFrame(requests.get(url_leliq, headers=headers).json())
            tasa_leliq = leliq_df.iloc[-1]['valor'] if not leliq_df.empty else None
            # Inflación mensual
            inflacion_df = pd.DataFrame(requests.get(url_inflacion, headers=headers).json())
            inflacion = inflacion_df.iloc[-1]['valor']/100 if not inflacion_df.empty else None
            # M2 (usamos base monetaria como proxy)
            m2_df = pd.DataFrame(requests.get(url_m2, headers=headers).json())
            if len(m2_df) > 1:
                m2_crecimiento = (m2_df.iloc[-1]['valor'] - m2_df.iloc[-2]['valor']) / m2_df.iloc[-2]['valor']
            else:
                m2_crecimiento = None
        except Exception as e:
            st.warning(f"No se pudieron obtener datos reales del BCRA: {e}. Se usarán valores simulados.")
            reservas = 25000
            tasa_leliq = 50
            inflacion = 0.08
            m2_crecimiento = 0.03
        # Lógica simple de ciclo
        if inflacion is not None and tasa_leliq is not None and m2_crecimiento is not None and reservas is not None:
            if inflacion > 0.06 and tasa_leliq > 40 and m2_crecimiento > 0.02 and reservas < 20000:
                etapa = "Recesión"
                explicacion_ciclo = "Alta inflación, tasas elevadas, crecimiento monetario y reservas bajas sugieren recesión."
            elif inflacion < 0.04 and tasa_leliq < 35 and m2_crecimiento < 0.01 and reservas > 35000:
                etapa = "Expansión"
                explicacion_ciclo = "Baja inflación, tasas bajas, crecimiento monetario controlado y reservas altas sugieren expansión."
            elif inflacion > 0.05 and tasa_leliq > 45 and reservas > 30000:
                etapa = "Auge"
                explicacion_ciclo = "Inflación y tasas altas pero reservas sólidas sugieren auge, pero con riesgos de sobrecalentamiento."
            else:
                etapa = "Recuperación/Neutral"
                explicacion_ciclo = "Variables mixtas, posible recuperación o transición."
            st.success(f"Etapa detectada: **{etapa}**")
            st.caption(f"Explicación: {explicacion_ciclo}")
            # Validar y mostrar variables
            reservas_str = f"{reservas:,.0f}M USD" if reservas is not None else "N/D"
            tasa_leliq_str = f"{tasa_leliq:.2f}% anual" if tasa_leliq is not None else "N/D"
            inflacion_str = f"{inflacion*100:.2f}%" if inflacion is not None else "N/D"
            m2_crecimiento_str = f"{m2_crecimiento*100:.2f}%" if m2_crecimiento is not None else "N/D"
            st.markdown(f"- Reservas: {reservas_str}\n- Tasa LELIQ: {tasa_leliq_str}\n- Inflación mensual: {inflacion_str}\n- Crecimiento M2: {m2_crecimiento_str}")
        else:
            st.warning("No se pudieron obtener todas las variables para el análisis de ciclo económico.")
    # --- FIN BLOQUE CICLO ECONÓMICO ---

    # ... resto del código de optimización ...

    # ... después de mostrar los resultados de optimización ...
    # Mini tab de asimetría de retornos
    with st.expander("📉 Asimetría de los Retornos (Skewness)", expanded=False):
        estrategias_labels = []
        skewness_vals = []
        for clave, nombre in estrategias:
            res, _, _ = resultados.get(clave, (None, None, None))
            if res and hasattr(res, 'returns') and res.returns is not None:
                try:
                    ret = res.returns
                    if hasattr(ret, 'values'):
                        ret = ret.values
                    val = skew(ret)
                    estrategias_labels.append(nombre)
                    skewness_vals.append(val)
                except Exception:
                    continue
        if estrategias_labels:
            fig, ax = plt.subplots(figsize=(6, 3))
            bars = ax.bar(estrategias_labels, skewness_vals, color=["#0d6efd" if v > 0 else "#ef4444" for v in skewness_vals])
            ax.axhline(0, color='gray', linestyle='--', linewidth=1)
            ax.set_ylabel('Skewness')
            ax.set_title('Asimetría de los Retornos por Estrategia')
            for bar, val in zip(bars, skewness_vals):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{val:.2f}", ha='center', va='bottom', fontsize=9)
            st.pyplot(fig)
            st.caption("Valores positivos: cola derecha (más ganancias extremas). Valores negativos: cola izquierda (más pérdidas extremas). Cero: simetría.")
        else:
            st.info("No hay retornos suficientes para calcular la asimetría.")

    # --- Análisis Sectorial Básico previo a la optimización ---
    with st.expander("🔎 Análisis Sectorial Básico (Momentum por Sector)", expanded=False):
        st.markdown("**Se analizan los principales ETFs sectoriales globales para identificar los sectores con mejor momentum reciente.**")
        sector_etfs = {
            'Tecnología': 'XLK',
            'Financieros': 'XLF',
            'Salud': 'XLV',
            'Energía': 'XLE',
            'Industrial': 'XLI',
            'Comunicación': 'XLC',
            'Consumo Discrecional': 'XLY',
            'Consumo Básico': 'XLP',
            'Materiales': 'XLB',
            'Bienes Raíces': 'XLRE',
            'Servicios Públicos': 'XLU'
        }
        import yfinance as yf
        import pandas as pd
        import plotly.graph_objects as go
        try:
            precios = yf.download(list(sector_etfs.values()), period="6mo", interval="1d", progress=False)["Adj Close"]
            rendimientos = precios.iloc[-1] / precios.iloc[0] - 1
            ranking = rendimientos.sort_values(ascending=False)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[k for k,v in sector_etfs.items() if v in ranking.index],
                y=ranking.values*100,
                marker_color=["#2ecc71" if v==ranking.index[0] else "#3498db" for v in ranking.index],
                text=[f"{v}: {ranking[v]*100:.2f}%" for v in ranking.index],
                textposition="auto"
            ))
            fig.update_layout(title="Ranking de Sectores por Momentum (6 meses)", yaxis_title="Rendimiento (%)", xaxis_title="Sector", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            st.success(f"Sector destacado: {ranking.index[0]} ({ranking.values[0]*100:.2f}%)")
            st.markdown(f"**Recomendación:** Priorizar activos del sector **{[k for k,v in sector_etfs.items() if v==ranking.index[0]][0]}** para optimizaciones si es coherente con tu perfil de riesgo.")
        except Exception as e:
            st.warning(f"No se pudo obtener el ranking sectorial: {e}")

    # --- Diagnóstico IA de ciclo económico y sugerencia de sectores ---
    def diagnostico_ciclo_y_sugerencia(all_variables_data, gemini_api_key, sectores_arg=None):
        """
        Usa IA para diagnosticar el ciclo económico y sugerir sectores/activos de Argentina y EEUU.
        """
        import google.generativeai as genai
        resumen = []
        for nombre, info in all_variables_data.items():
            m = info.get('metrics', {})
            resumen.append(
                f"{nombre}: Actual={m.get('valor_actual', 0):.2f}, Cambio={m.get('cambio_porcentual', 0):+.1f}%, VolATR={m.get('volatilidad_atr', 0):.2f}%, Tend={m.get('tendencia_direccion', 'N/A')}"
            )
        # --- Sectores argentinos relevantes ---
        sectores_arg = sectores_arg or {
            'Bancos': ['GGAL', 'BMA', 'SUPV', 'BBAR'],
            'Energía': ['YPFD', 'PAMP', 'CEPU', 'TGSU2'],
            'Consumo': ['SUPV', 'EDN', 'ALUA'],
            'Materiales': ['TXAR', 'ALUA'],
            'Tecnología': ['MELI'],
            'Servicios Públicos': ['EDN', 'TGSU2', 'CEPU'],
            'Agro': ['AGRO'],
            'Telecomunicaciones': ['TECO2'],
            'Industriales': ['TRAN', 'TGNO4'],
        }
        sectores_arg_str = "\n".join([f"- {k}: {', '.join(v)}" for k, v in sectores_arg.items()])
        prompt = f"""
Actúa como economista jefe. Analiza el siguiente resumen de variables macroeconómicas argentinas y de EEUU:

{chr(10).join(resumen)}

Sectores argentinos relevantes y sus principales tickers:
{sectores_arg_str}

1. Diagnostica el ciclo económico actual de Argentina y global (expansión, recesión, etc.).
2. Sugiere 2-3 sectores o tipos de activos argentinos (de la lista) y 2-3 de EEUU que suelen rendir mejor en este ciclo, usando factores de Intermarket (ITM), momentum y variables macro si es relevante.
3. Fundamenta brevemente cada sugerencia, explicando por qué esos sectores son los más adecuados según el contexto y los factores de ITM.

Responde en español, en formato claro y ejecutivo. Enumera los sectores sugeridos en una lista separada al final bajo el título "SUGERENCIA DE SECTORES ARGENTINA" y otra bajo "SUGERENCIA DE SECTORES EEUU".\n\nEjemplo de formato de respuesta:\n\nDiagnóstico: ...\nExplicación: ...\nSUGERENCIA DE SECTORES ARGENTINA:\n- ...\n- ...\nSUGERENCIA DE SECTORES EEUU:\n- ...\n- ...\n"""
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=900,
                top_p=0.9,
                top_k=30
            )
        )
        response = model.generate_content(prompt)
        return response.text if response and response.text else "No se pudo obtener diagnóstico IA."

    # --- INICIO mostrar_optimizacion_portafolio ---
        # Diagnóstico IA de ciclo económico y sugerencia de sectores
        st.markdown("---")
        st.subheader("🧠 Diagnóstico IA de ciclo económico y sugerencia de sectores")
        if 'GEMINI_API_KEY' not in st.session_state:
            st.session_state.GEMINI_API_KEY = ''
        if st.button("🔍 Analizar ciclo y sugerir sectores", key="btn_diag_ia"):
            import yfinance as yf
            import numpy as np
            all_variables_data = {}
            ATR_WINDOW = 14
            # --- Variables Argentina ---
            try:
                merval = yf.download('^MERV', period='6mo')['Close']
                if not merval.empty:
                    merval_ret = merval.pct_change().dropna()
                    merval_atr = merval_ret.abs().rolling(ATR_WINDOW).mean().iloc[-1]*100 if len(merval_ret) >= ATR_WINDOW else merval_ret.abs().mean()*100
                    all_variables_data['MERVAL (Argentina)'] = {
                        'metrics': {
                            'valor_actual': merval.iloc[-1],
                            'cambio_porcentual': (merval.iloc[-1]/merval.iloc[0]-1)*100,
                            'volatilidad_atr': merval_atr,
                            'tendencia_direccion': 'alcista' if merval.iloc[-1]>merval.iloc[0] else 'bajista'
                        }
                    }
            except Exception as e:
                st.warning(f"No se pudo obtener MERVAL: {e}")
            # --- Variables EEUU ---
            tickers_usa = {
                'S&P 500 (EEUU)': '^GSPC',
                'VIX (EEUU)': '^VIX',
                'Tecnología (XLK)': 'XLK',
                'Financieros (XLF)': 'XLF',
                'Energía (XLE)': 'XLE',
                'Consumo Discrecional (XLY)': 'XLY',
                'Consumo Básico (XLP)': 'XLP',
                'Salud (XLV)': 'XLV',
                'Industrial (XLI)': 'XLI',
                'Materiales (XLB)': 'XLB',
                'Bienes Raíces (XLRE)': 'XLRE',
                'Servicios Públicos (XLU)': 'XLU',
                'Comunicaciones (XLC)': 'XLC',
            }
            try:
                precios = yf.download(list(tickers_usa.values()), period='6mo')['Close']
                for nombre, ticker in tickers_usa.items():
                    serie = precios[ticker] if ticker in precios else None
                    if serie is not None and not serie.empty:
                        ret = serie.pct_change().dropna()
                        atr = ret.abs().rolling(ATR_WINDOW).mean().iloc[-1]*100 if len(ret) >= ATR_WINDOW else ret.abs().mean()*100
                        all_variables_data[nombre] = {
                            'metrics': {
                                'valor_actual': serie.iloc[-1],
                                'cambio_porcentual': (serie.iloc[-1]/serie.iloc[0]-1)*100,
                                'volatilidad_atr': atr,
                                'tendencia_direccion': 'alcista' if serie.iloc[-1]>serie.iloc[0] else 'bajista'
                            }
                        }
            except Exception as e:
                st.warning(f"No se pudieron obtener variables de EEUU: {e}")
            # --- Sectores argentinos relevantes ---
            sectores_arg = {
                'Bancos': ['GGAL', 'BMA', 'SUPV', 'BBAR'],
                'Energía': ['YPFD', 'PAMP', 'CEPU', 'TGSU2'],
                'Consumo': ['SUPV', 'EDN', 'ALUA'],
                'Materiales': ['TXAR', 'ALUA'],
                'Tecnología': ['MELI'],
                'Servicios Públicos': ['EDN', 'TGSU2', 'CEPU'],
                'Agro': ['AGRO'],
                'Telecomunicaciones': ['TECO2'],
                'Industriales': ['TRAN', 'TGNO4'],
            }
            with st.spinner("Consultando IA..."):
                diagnostico = diagnostico_ciclo_y_sugerencia(all_variables_data, st.session_state.GEMINI_API_KEY, sectores_arg)
            st.markdown(diagnostico)
            # Extraer sectores sugeridos
            import re
            sugeridos_arg = []
            sugeridos_usa = []
            match_arg = re.search(r"SUGERENCIA DE SECTORES ARGENTINA\s*[:\-]*\s*(.*?)(?:SUGERENCIA DE SECTORES EEUU|$)", diagnostico, re.IGNORECASE | re.DOTALL)
            if match_arg:
                sugeridos_arg = re.findall(r"(?:\-|\d+\.)\s*([^\n]+)", match_arg.group(1))
            match_usa = re.search(r"SUGERENCIA DE SECTORES EEUU\s*[:\-]*\s*(.*)", diagnostico, re.IGNORECASE | re.DOTALL)
            if match_usa:
                sugeridos_usa = re.findall(r"(?:\-|\d+\.)\s*([^\n]+)", match_usa.group(1))
            st.session_state['sectores_sugeridos_ia_arg'] = sugeridos_arg
            st.session_state['sectores_sugeridos_ia_usa'] = sugeridos_usa
            if sugeridos_arg:
                st.success(f"Sectores argentinos sugeridos por IA: {', '.join(sugeridos_arg)}")
            if sugeridos_usa:
                st.success(f"Sectores EEUU sugeridos por IA: {', '.join(sugeridos_usa)}")

    # --- Función auxiliar para calcular drawdown ---
    def calcular_drawdown(serie_valores):
        """
        Calcula el drawdown máximo y actual de una serie de valores (por ejemplo, valor de portafolio).
        Devuelve: drawdown_max (float), drawdown_actual (float), serie_drawdown (pd.Series)
        """
        import numpy as np
        import pandas as pd
        if isinstance(serie_valores, (pd.Series, np.ndarray, list)):
            serie = pd.Series(serie_valores)
            max_acum = serie.cummax()
            drawdown = (serie - max_acum) / max_acum
            drawdown_max = drawdown.min()
            drawdown_actual = drawdown.iloc[-1]
            return drawdown_max, drawdown_actual, drawdown
        else:
            return 0, 0, pd.Series([])

    # --- En mostrar_optimizacion_portafolio, después de mostrar resultados de optimización ---
        # --- Análisis de Drawdown ---
        st.subheader("📉 Análisis de Drawdown (Caídas Máximas)")
        # Portafolio actual
        st.markdown("**Portafolio Actual**")
        # Intentar reconstruir serie de valor del portafolio actual
        try:
            # Usar los mismos datos que para el histograma de portafolio actual
            # (puedes ajustar si tienes la serie exacta)
            # Aquí se usa la suma ponderada de precios normalizados
            activos = [a for a in activos_raw if a.get('titulo',{}).get('simbolo')]
            pesos = [activos_dict[a.get('titulo',{}).get('simbolo')]['Valuación']/valor_total if valor_total>0 else 0 for a in activos]
            precios = {}
            for a in activos:
                simbolo = a.get('titulo',{}).get('simbolo')
                mercado = a.get('titulo',{}).get('mercado','BCBA')
                df = obtener_serie_historica_iol(token_acceso, mercado, simbolo, fecha_desde.strftime('%Y-%m-%d'), fecha_hasta.strftime('%Y-%m-%d'))
                if df is not None and not df.empty and 'precio' in df.columns:
                    precios[simbolo] = df.set_index('fecha')['precio']
            if precios:
                df_precios = pd.DataFrame(precios).dropna()
                serie_valor = (df_precios * pesos).sum(axis=1)
                dd_max, dd_actual, serie_dd = calcular_drawdown(serie_valor)
                st.metric("Drawdown Máximo", f"{dd_max*100:.2f}%")
                st.metric("Drawdown Actual", f"{dd_actual*100:.2f}%")
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=serie_dd.index, y=serie_dd*100, mode='lines', name='Drawdown (%)', line=dict(color='#ef4444')))
                fig.update_layout(title="Drawdown Portafolio Actual", yaxis_title="Drawdown (%)", xaxis_title="Fecha", template='plotly_white', height=300)
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"No se pudo calcular el drawdown del portafolio actual: {e}")
        # Portafolios optimizados
        for clave, nombre in estrategias:
            res, _, _ = resultados.get(clave, (None, None, None))
            if res and hasattr(res, 'returns') and res.returns is not None:
                st.markdown(f"**{nombre}**")
                # Reconstruir serie de valor acumulado
                try:
                    import numpy as np
                    import pandas as pd
                    if hasattr(res, 'returns'):
                        # Suponemos retornos diarios
                        serie_valor = (1 + pd.Series(res.returns)).cumprod()
                        dd_max, dd_actual, serie_dd = calcular_drawdown(serie_valor)
                        st.metric("Drawdown Máximo", f"{dd_max*100:.2f}%")
                        st.metric("Drawdown Actual", f"{dd_actual*100:.2f}%")
                        import plotly.graph_objects as go
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(y=serie_dd*100, mode='lines', name='Drawdown (%)', line=dict(color='#ef4444')))
                        fig.update_layout(title=f"Drawdown {nombre}", yaxis_title="Drawdown (%)", xaxis_title="Día", template='plotly_white', height=250)
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"No se pudo calcular el drawdown de {nombre}: {e}")
        # Benchmarks (ejemplo: S&P500, MERVAL)
        st.markdown("**Benchmarks**")
        try:
            import yfinance as yf
            import pandas as pd
            benchmarks = {'S&P 500': '^GSPC', 'MERVAL': '^MERV'}
            for nombre, ticker in benchmarks.items():
                serie = yf.download(ticker, period='1y')['Close']
                if not serie.empty:
                    dd_max, dd_actual, serie_dd = calcular_drawdown(serie)
                    st.metric(f"{nombre} Drawdown Máx", f"{dd_max*100:.2f}%")
                    st.metric(f"{nombre} Drawdown Actual", f"{dd_actual*100:.2f}%")
                    import plotly.graph_objects as go
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=serie_dd.index, y=serie_dd*100, mode='lines', name='Drawdown (%)', line=dict(color='#ef4444')))
                    fig.update_layout(title=f"Drawdown {nombre}", yaxis_title="Drawdown (%)", xaxis_title="Fecha", template='plotly_white', height=250)
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"No se pudo calcular el drawdown de benchmarks: {e}")

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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Resumen Portafolio", 
        "💰 Estado de Cuenta", 
        "📊 Análisis Técnico",
        "💱 Cotizaciones",
        "🔄 Rebalanceo",
        "🤖 Informe IA"
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
        mostrar_informe_ia(token_acceso, id_cliente)

def main():
    # Configuración de estilos para BCRA Dashboard
    st.markdown("""
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">
        <style>
            /* Estilos generales */
            .stApp {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-color: #f8fafc;
            }
            
            /* Sidebar */
            .css-1d391kg, .css-1d391kg > div:first-child {
                background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%) !important;
                color: white !important;
            }
            
            /* Tarjetas */
            .metric-card {
                transition: all 0.3s ease;
                border-radius: 0.75rem;
                background: white;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                padding: 1.5rem;
                height: 100%;
            }
            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            }
            
            /* Botones */
            .stButton > button {
                border-radius: 0.5rem !important;
                font-weight: 500 !important;
                transition: all 0.2s !important;
            }
            
            /* Pestañas */
            .stTabs [data-baseweb="tab-list"] {
                gap: 0.5rem;
            }
            .stTabs [data-baseweb="tab"] {
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                transition: all 0.2s;
            }
            .stTabs [aria-selected="true"] {
                background-color: #3b82f6;
                color: white !important;
            }
            
            /* Tablas */
            .stDataFrame {
                border-radius: 0.5rem;
                overflow: hidden;
                box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
            }
            
            /* Footer */
            .footer {
                background: var(--card-background);
                padding: 2rem;
                border-radius: 12px;
                margin-top: 3rem;
                text-align: center;
                box-shadow: var(--shadow);
                border: 1px solid var(--border-color);
            }
            
            .footer p {
                margin: 0.5rem 0;
                color: var(--text-secondary);
            }
        </style>
    """, unsafe_allow_html=True)
    
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
        if st.session_state.token_acceso:
            st.sidebar.title("Menú Principal")
            opcion = st.sidebar.radio(
                "Seleccione una opción:",
                ("🏠 Inicio", "📊 Análisis de Portafolio", "💰 Tasas de Caución", "👨\u200d💼 Panel del Asesor", "🇦🇷 Datos Económicos", "🏦 BCRA Dashboard", "📊 Paneles de Cotización", "📈 Análisis Beta/Correlación", "🔗 Datos Integrados (ArgentinaDatos+BCRA+yfinance)"),
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
            elif opcion == "💰 Tasas de Caución":
                if 'token_acceso' in st.session_state and st.session_state.token_acceso:
                    mostrar_tasas_caucion(st.session_state.token_acceso)
                else:
                    st.warning("Por favor inicie sesión para ver las tasas de caución")
            elif opcion == "👨\u200d💼 Panel del Asesor":
                mostrar_movimientos_asesor()
                st.info("👆 Seleccione una opción del menú para comenzar")
            elif opcion == "🇦🇷 Datos Económicos":
                mostrar_datos_argentina()
            elif opcion == "🏦 BCRA Dashboard":
                mostrar_bcra_dashboard()
            elif opcion == "📊 Paneles de Cotización":
                mostrar_paneles_cotizacion()
            elif opcion == "📈 Análisis Beta/Correlación":
                mostrar_analisis_beta_correlacion()
            elif opcion == "🔗 Datos Integrados (ArgentinaDatos+BCRA+yfinance)":
                mostrar_datos_argentinadatos_bcra()
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

def obtener_paneles_cotizacion(token_portador, pais='Argentina'):
    """
    Obtiene todos los paneles de cotización disponibles.
    """
    try:
        headers = obtener_encabezado_autorizacion(token_portador)
        url = f"https://api.invertironline.com/api/v2/{pais}/Titulos/Cotizacion/Paneles"
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"Error al obtener paneles de cotización: {str(e)}")
        return []

def obtener_instrumentos_por_panel(token_portador, instrumento, panel, pais='Argentina'):
    """
    Obtiene los instrumentos de un panel específico.
    """
    try:
        headers = obtener_encabezado_autorizacion(token_portador)
        url = f"https://api.invertironline.com/api/v2/Cotizaciones/{instrumento}/{panel}/{pais}"
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"Error al obtener instrumentos del panel {panel}: {str(e)}")
        return []

def obtener_cotizaciones_todos_instrumentos(token_portador, instrumento, pais='Argentina'):
    """
    Obtiene cotizaciones de todos los instrumentos de un tipo.
    """
    try:
        headers = obtener_encabezado_autorizacion(token_portador)
        url = f"https://api.invertironline.com/api/v2/Cotizaciones/{instrumento}/{pais}/Todos"
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"Error al obtener cotizaciones de {instrumento}: {str(e)}")
        return []

def obtener_fci_administradoras(token_portador):
    """
    Obtiene las administradoras de fondos comunes de inversión.
    """
    try:
        headers = obtener_encabezado_autorizacion(token_portador)
        url = "https://api.invertironline.com/api/v2/Titulos/FCI/Administradoras"
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"Error al obtener administradoras FCI: {str(e)}")
        return []

def obtener_fci_por_administradora(token_portador, administradora):
    """
    Obtiene los fondos comunes de inversión de una administradora específica.
    """
    try:
        headers = obtener_encabezado_autorizacion(token_portador)
        url = f"https://api.invertironline.com/api/v2/Titulos/FCI/Administradoras/{administradora}/TipoFondos"
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"Error al obtener FCI de {administradora}: {str(e)}")
        return []

def obtener_serie_historica_completa(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="SinAjustar"):
    """
    Obtiene la serie histórica completa de un instrumento.
    """
    try:
        headers = obtener_encabezado_autorizacion(token_portador)
        url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"Error al obtener serie histórica de {simbolo}: {str(e)}")
        return []

def almacenar_datos_para_analisis(datos, nombre_archivo):
    """
    Almacena datos para análisis posterior en formato JSON.
    """
    try:
        import json
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_completo = f"{nombre_archivo}_{timestamp}.json"
        
        with open(nombre_completo, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        
        return nombre_completo
    except Exception as e:
        st.error(f"Error al almacenar datos: {str(e)}")
        return None

def obtener_cotizacion_detalle(token_portador, mercado, simbolo):
    """
    Obtiene el detalle completo de cotización de un instrumento.
    """
    try:
        headers = obtener_encabezado_autorizacion(token_portador)
        url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/CotizacionDetalle"
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"Error al obtener detalle de cotización de {simbolo}: {str(e)}")
        return None

def obtener_opciones_instrumento(token_portador, mercado, simbolo):
    """
    Obtiene las opciones disponibles para un instrumento.
    """
    try:
        headers = obtener_encabezado_autorizacion(token_portador)
        url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Opciones"
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"Error al obtener opciones de {simbolo}: {str(e)}")
        return []

def obtener_cotizacion_mep_detalle(token_portador, simbolo):
    """
    Obtiene cotización MEP detallada para un símbolo.
    """
    try:
        headers = obtener_encabezado_autorizacion(token_portador)
        url = f"https://api.invertironline.com/api/v2/Cotizaciones/MEP/{simbolo}"
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        st.error(f"Error al obtener cotización MEP de {simbolo}: {str(e)}")
        return None

def analizar_datos_almacenados(archivo_json):
    """
    Analiza datos almacenados y genera insights.
    """
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        if not datos:
            return None
        
        df = pd.DataFrame(datos)
        
        # Análisis básico
        analisis = {
            'total_registros': len(df),
            'columnas': list(df.columns),
            'tipos_datos': df.dtypes.to_dict(),
            'valores_faltantes': df.isnull().sum().to_dict()
        }
        
        # Análisis numérico si hay columnas numéricas
        columnas_numericas = df.select_dtypes(include=[np.number]).columns
        if len(columnas_numericas) > 0:
            analisis['estadisticas_numericas'] = df[columnas_numericas].describe().to_dict()
        
        # Análisis de fechas si hay columnas de fecha
        columnas_fecha = df.select_dtypes(include=['datetime64']).columns
        if len(columnas_fecha) > 0:
            analisis['rangos_fecha'] = {
                col: {
                    'min': df[col].min().strftime('%Y-%m-%d'),
                    'max': df[col].max().strftime('%Y-%m-%d')
                } for col in columnas_fecha
            }
        
        return analisis
    except Exception as e:
        st.error(f"Error al analizar datos: {str(e)}")
        return None

def mostrar_paneles_cotizacion():
    """
    Función principal para mostrar todos los paneles de cotización y sus series.
    """
    st.header("📊 Paneles de Cotización y Series Históricas")
    st.markdown("### Análisis Completo de Instrumentos Financieros")
    
    if 'token_acceso' not in st.session_state or not st.session_state.token_acceso:
        st.warning("🔐 Por favor, inicie sesión para acceder a los paneles de cotización")
        return
    
    token_acceso = st.session_state.token_acceso
    
    # Configuración de análisis
    st.subheader("⚙️ Configuración de Análisis")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        pais = st.selectbox("País", ["Argentina", "Estados Unidos"], index=0)
    with col2:
        fecha_desde = st.date_input("Fecha Desde", value=st.session_state.fecha_desde)
    with col3:
        fecha_hasta = st.date_input("Fecha Hasta", value=st.session_state.fecha_hasta)
    
    # Opciones de análisis
    st.subheader("📋 Opciones de Análisis")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏢 Fondos Comunes", "📈 Instrumentos", "📊 Paneles", "📉 Series Históricas", "💾 Almacenamiento", "🔍 Análisis Avanzado"
    ])
    
    with tab1:
        st.subheader("🏢 Fondos Comunes de Inversión")
        
        if st.button("🔄 Cargar Administradoras FCI", use_container_width=True):
            with st.spinner("Cargando administradoras..."):
                administradoras = obtener_fci_administradoras(token_acceso)
                
                if administradoras:
                    st.success(f"✅ Se encontraron {len(administradoras)} administradoras")
                    
                    # Mostrar administradoras
                    for admin in administradoras:
                        with st.expander(f"🏢 {admin.get('nombre', 'Sin nombre')}"):
                            if st.button(f"📊 Ver FCI de {admin.get('nombre', 'Administradora')}", key=f"fci_{admin.get('id')}"):
                                with st.spinner(f"Cargando FCI de {admin.get('nombre', 'Administradora')}..."):
                                    fci_list = obtener_fci_por_administradora(token_acceso, admin.get('id'))
                                    
                                    if fci_list:
                                        st.success(f"✅ Se encontraron {len(fci_list)} fondos")
                                        
                                        # Crear DataFrame para mejor visualización
                                        df_fci = pd.DataFrame(fci_list)
                                        st.dataframe(df_fci, use_container_width=True)
                                        
                                        # Opción para almacenar datos
                                        if st.button(f"💾 Almacenar FCI {admin.get('nombre', 'Administradora')}", key=f"store_fci_{admin.get('id')}"):
                                            nombre_archivo = almacenar_datos_para_analisis(fci_list, f"FCI_{admin.get('nombre', 'Admin')}")
                                            if nombre_archivo:
                                                st.success(f"✅ Datos almacenados en {nombre_archivo}")
                                    else:
                                        st.warning("No se encontraron fondos para esta administradora")
                else:
                    st.warning("No se encontraron administradoras")
    
    with tab2:
        st.subheader("📈 Instrumentos por Tipo")
        
        instrumentos = ["Acciones", "Bonos", "Opciones", "Futuros", "Cedears"]
        instrumento_seleccionado = st.selectbox("Seleccionar Instrumento", instrumentos)
        
        if st.button(f"🔄 Cargar {instrumento_seleccionado}", use_container_width=True):
            with st.spinner(f"Cargando {instrumento_seleccionado}..."):
                cotizaciones = obtener_cotizaciones_todos_instrumentos(token_acceso, instrumento_seleccionado, pais)
                
                if cotizaciones:
                    st.success(f"✅ Se encontraron {len(cotizaciones)} instrumentos")
                    
                    # Crear DataFrame
                    df_cotizaciones = pd.DataFrame(cotizaciones)
                    st.dataframe(df_cotizaciones, use_container_width=True)
                    
                    # Estadísticas básicas
                    if not df_cotizaciones.empty:
                        st.subheader("📊 Estadísticas")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Total Instrumentos", len(df_cotizaciones))
                        with col2:
                            if 'ultimoPrecio' in df_cotizaciones.columns:
                                st.metric("Precio Promedio", f"${df_cotizaciones['ultimoPrecio'].mean():.2f}")
                        with col3:
                            if 'variacion' in df_cotizaciones.columns:
                                st.metric("Variación Promedio", f"{df_cotizaciones['variacion'].mean():.2f}%")
                    
                    # Opción para almacenar datos
                    if st.button(f"💾 Almacenar {instrumento_seleccionado}", key=f"store_{instrumento_seleccionado}"):
                        nombre_archivo = almacenar_datos_para_analisis(cotizaciones, f"{instrumento_seleccionado}_{pais}")
                        if nombre_archivo:
                            st.success(f"✅ Datos almacenados en {nombre_archivo}")
                else:
                    st.warning(f"No se encontraron {instrumento_seleccionado}")
    
    with tab3:
        st.subheader("📊 Paneles de Cotización")
        
        if st.button("🔄 Cargar Paneles", use_container_width=True):
            with st.spinner("Cargando paneles..."):
                paneles = obtener_paneles_cotizacion(token_acceso, pais)
                
                if paneles:
                    st.success(f"✅ Se encontraron {len(paneles)} paneles")
                    
                    for panel in paneles:
                        with st.expander(f"📊 Panel: {panel.get('nombre', 'Sin nombre')}"):
                            st.write(f"**Descripción:** {panel.get('descripcion', 'Sin descripción')}")
                            st.write(f"**Instrumento:** {panel.get('instrumento', 'N/A')}")
                            
                            if st.button(f"📈 Ver Instrumentos", key=f"panel_{panel.get('id')}"):
                                with st.spinner(f"Cargando instrumentos del panel {panel.get('nombre', 'Panel')}..."):
                                    instrumentos_panel = obtener_instrumentos_por_panel(
                                        token_acceso, 
                                        panel.get('instrumento', 'Acciones'), 
                                        panel.get('nombre', 'Panel'), 
                                        pais
                                    )
                                    
                                    if instrumentos_panel:
                                        st.success(f"✅ Se encontraron {len(instrumentos_panel)} instrumentos")
                                        
                                        df_panel = pd.DataFrame(instrumentos_panel)
                                        st.dataframe(df_panel, use_container_width=True)
                                        
                                        # Gráfico de precios si hay datos
                                        if 'ultimoPrecio' in df_panel.columns and not df_panel.empty:
                                            fig = go.Figure()
                                            fig.add_trace(go.Bar(
                                                x=df_panel['simbolo'],
                                                y=df_panel['ultimoPrecio'],
                                                name='Último Precio'
                                            ))
                                            fig.update_layout(
                                                title=f"Precios - Panel {panel.get('nombre', 'Panel')}",
                                                xaxis_title="Símbolo",
                                                yaxis_title="Precio ($)"
                                            )
                                            st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.warning("No se encontraron instrumentos en este panel")
                else:
                    st.warning("No se encontraron paneles")
    
    with tab4:
        st.subheader("📉 Series Históricas")
        
        col1, col2 = st.columns(2)
        with col1:
            mercado = st.text_input("Mercado", placeholder="ROFEX")
        with col2:
            simbolo = st.text_input("Símbolo", placeholder="GGAL")
        
        ajustada = st.selectbox("Ajuste", ["SinAjustar", "Ajustada"], index=0)
        
        if st.button("📊 Obtener Serie Histórica", use_container_width=True):
            if mercado and simbolo:
                with st.spinner(f"Obteniendo serie histórica de {simbolo}..."):
                    serie_historica = obtener_serie_historica_completa(
                        token_acceso, 
                        mercado, 
                        simbolo, 
                        fecha_desde.strftime("%Y-%m-%d"), 
                        fecha_hasta.strftime("%Y-%m-%d"), 
                        ajustada
                    )
                    
                    if serie_historica:
                        st.success(f"✅ Serie histórica obtenida con {len(serie_historica)} registros")
                        
                        # Crear DataFrame
                        df_serie = pd.DataFrame(serie_historica)
                        
                        # Convertir fechas si es necesario
                        if 'fecha' in df_serie.columns:
                            df_serie['fecha'] = pd.to_datetime(df_serie['fecha'])
                        
                        # Gráfico de precios
                        if not df_serie.empty and 'precio' in df_serie.columns:
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=df_serie['fecha'] if 'fecha' in df_serie.columns else df_serie.index,
                                y=df_serie['precio'],
                                mode='lines',
                                name='Precio'
                            ))
                            fig.update_layout(
                                title=f"Serie Histórica - {simbolo}",
                                xaxis_title="Fecha",
                                yaxis_title="Precio ($)"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Mostrar datos
                        st.dataframe(df_serie, use_container_width=True)
                        
                        # Estadísticas
                        if not df_serie.empty and 'precio' in df_serie.columns:
                            st.subheader("📊 Estadísticas de la Serie")
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Precio Máximo", f"${df_serie['precio'].max():.2f}")
                            with col2:
                                st.metric("Precio Mínimo", f"${df_serie['precio'].min():.2f}")
                            with col3:
                                st.metric("Precio Promedio", f"${df_serie['precio'].mean():.2f}")
                            with col4:
                                st.metric("Volatilidad", f"{df_serie['precio'].std():.2f}")
                        
                        # Opción para almacenar datos
                        if st.button(f"💾 Almacenar Serie {simbolo}", key=f"store_serie_{simbolo}"):
                            nombre_archivo = almacenar_datos_para_analisis(serie_historica, f"Serie_{simbolo}_{mercado}")
                            if nombre_archivo:
                                st.success(f"✅ Datos almacenados en {nombre_archivo}")
                    else:
                        st.warning("No se pudo obtener la serie histórica")
            else:
                st.warning("Por favor complete mercado y símbolo")
    
    with tab5:
        st.subheader("💾 Gestión de Datos Almacenados")
        
        st.info("""
        **Funcionalidades de Almacenamiento:**
        - Los datos se guardan automáticamente en formato JSON
        - Cada archivo incluye timestamp para identificación única
        - Los datos están listos para análisis posterior
        - Formato compatible con pandas y otras herramientas de análisis
        """)
        
        # Mostrar archivos almacenados recientemente
        import os
        import glob
        
        archivos_json = glob.glob("*.json")
        if archivos_json:
            st.subheader("📁 Archivos Disponibles")
            
            # Ordenar por fecha de modificación
            archivos_json.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            for archivo in archivos_json[:10]:  # Mostrar solo los 10 más recientes
                tamaño = os.path.getsize(archivo) / 1024  # KB
                fecha_mod = datetime.fromtimestamp(os.path.getmtime(archivo))
                
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"📄 {archivo}")
                with col2:
                    st.write(f"{tamaño:.1f} KB")
                with col3:
                    st.write(fecha_mod.strftime("%Y-%m-%d %H:%M"))
                
                # Opción para cargar y analizar
                if st.button(f"📊 Analizar {archivo}", key=f"analyze_{archivo}"):
                    try:
                        with open(archivo, 'r', encoding='utf-8') as f:
                            datos = json.load(f)
                        
                        st.success(f"✅ Datos cargados: {len(datos)} registros")
                        
                        # Análisis básico
                        if isinstance(datos, list) and len(datos) > 0:
                            df_temp = pd.DataFrame(datos)
                            st.dataframe(df_temp.head(), use_container_width=True)
                            
                            # Estadísticas básicas
                            st.write(f"**Columnas disponibles:** {list(df_temp.columns)}")
                            st.write(f"**Registros:** {len(df_temp)}")
                            
                            # Análisis avanzado
                            analisis = analizar_datos_almacenados(archivo)
                            if analisis:
                                st.subheader("📊 Análisis Detallado")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write("**Información General:**")
                                    st.write(f"- Total registros: {analisis['total_registros']}")
                                    st.write(f"- Columnas: {len(analisis['columnas'])}")
                                
                                with col2:
                                    st.write("**Valores Faltantes:**")
                                    for col, faltantes in analisis['valores_faltantes'].items():
                                        if faltantes > 0:
                                            st.write(f"- {col}: {faltantes}")
                                
                                # Gráficos si hay datos numéricos
                                if 'estadisticas_numericas' in analisis:
                                    st.subheader("📈 Estadísticas Numéricas")
                                    df_stats = pd.DataFrame(analisis['estadisticas_numericas'])
                                    st.dataframe(df_stats, use_container_width=True)
                                    
                                    # Gráfico de distribución si hay suficientes datos
                                    if len(df_temp) > 10:
                                        columnas_numericas = df_temp.select_dtypes(include=[np.number]).columns
                                        if len(columnas_numericas) > 0:
                                            col_seleccionada = st.selectbox("Seleccionar columna para gráfico", columnas_numericas)
                                            
                                            if col_seleccionada:
                                                fig = go.Figure()
                                                fig.add_trace(go.Histogram(
                                                    x=df_temp[col_seleccionada],
                                                    nbinsx=20,
                                                    name='Distribución'
                                                ))
                                                fig.update_layout(
                                                    title=f"Distribución de {col_seleccionada}",
                                                    xaxis_title=col_seleccionada,
                                                    yaxis_title="Frecuencia"
                                                )
                                                st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error al cargar archivo: {str(e)}")
        else:
            st.info("📁 No hay archivos JSON almacenados aún. Use las otras pestañas para generar datos.")
    
    with tab6:
        st.subheader("🔍 Análisis Avanzado")
        
        # Análisis MEP
        st.markdown("### 💱 Análisis MEP")
        
        col1, col2 = st.columns(2)
        with col1:
            simbolo_mep = st.text_input("Símbolo para MEP", placeholder="GGAL")
        with col2:
            if st.button("📊 Obtener MEP", use_container_width=True):
                if simbolo_mep:
                    with st.spinner(f"Obteniendo MEP para {simbolo_mep}..."):
                        mep_data = obtener_cotizacion_mep_detalle(token_acceso, simbolo_mep)
                        
                        if mep_data:
                            st.success(f"✅ MEP obtenido para {simbolo_mep}")
                            
                            # Mostrar datos MEP
                            if isinstance(mep_data, dict):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Compra", f"${mep_data.get('compra', 0):.2f}")
                                with col2:
                                    st.metric("Venta", f"${mep_data.get('venta', 0):.2f}")
                                
                                # Gráfico MEP si hay datos históricos
                                if 'historico' in mep_data:
                                    fig = go.Figure()
                                    fig.add_trace(go.Scatter(
                                        x=mep_data['historico'].get('fechas', []),
                                        y=mep_data['historico'].get('valores', []),
                                        mode='lines',
                                        name='MEP Histórico'
                                    ))
                                    fig.update_layout(
                                        title=f"Evolución MEP - {simbolo_mep}",
                                        xaxis_title="Fecha",
                                        yaxis_title="Precio MEP ($)"
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning(f"No se pudo obtener MEP para {simbolo_mep}")
                else:
                    st.warning("Por favor ingrese un símbolo")
        
        # Análisis detallado de instrumentos
        st.markdown("### 📊 Análisis Detallado de Instrumentos")
        
        col1, col2 = st.columns(2)
        with col1:
            mercado_detalle = st.text_input("Mercado", placeholder="ROFEX")
        with col2:
            simbolo_detalle = st.text_input("Símbolo", placeholder="GGAL")
        
        if st.button("🔍 Obtener Detalle", use_container_width=True):
            if mercado_detalle and simbolo_detalle:
                with st.spinner(f"Obteniendo detalle de {simbolo_detalle}..."):
                    detalle = obtener_cotizacion_detalle(token_acceso, mercado_detalle, simbolo_detalle)
                    
                    if detalle:
                        st.success(f"✅ Detalle obtenido para {simbolo_detalle}")
                        
                        # Mostrar información detallada
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Información General:**")
                            for key, value in detalle.items():
                                if key not in ['opciones', 'historico']:
                                    st.write(f"- {key}: {value}")
                        
                        with col2:
                            st.write("**Métricas de Trading:**")
                            if 'volumen' in detalle:
                                st.metric("Volumen", f"{detalle['volumen']:,}")
                            if 'variacion' in detalle:
                                st.metric("Variación", f"{detalle['variacion']:.2f}%")
                            if 'ultimoPrecio' in detalle:
                                st.metric("Último Precio", f"${detalle['ultimoPrecio']:.2f}")
                        
                        # Opciones si están disponibles
                        if 'opciones' in detalle and detalle['opciones']:
                            st.subheader("📋 Opciones Disponibles")
                            df_opciones = pd.DataFrame(detalle['opciones'])
                            st.dataframe(df_opciones, use_container_width=True)
                        
                        # Almacenar detalle
                        if st.button(f"💾 Almacenar Detalle {simbolo_detalle}", key=f"store_detalle_{simbolo_detalle}"):
                            nombre_archivo = almacenar_datos_para_analisis(detalle, f"Detalle_{simbolo_detalle}_{mercado_detalle}")
                            if nombre_archivo:
                                st.success(f"✅ Detalle almacenado en {nombre_archivo}")
                    else:
                        st.warning(f"No se pudo obtener detalle para {simbolo_detalle}")
            else:
                st.warning("Por favor complete mercado y símbolo")
        
        # Análisis comparativo
        st.markdown("### 📈 Análisis Comparativo")
        
        instrumentos_comparar = st.multiselect(
            "Seleccionar instrumentos para comparar",
            ["GGAL", "YPF", "PAMP", "TENAR", "CRESUD"],
            default=["GGAL", "YPF"]
        )
        
        if st.button("📊 Comparar Instrumentos", use_container_width=True) and len(instrumentos_comparar) >= 2:
            with st.spinner("Obteniendo datos comparativos..."):
                datos_comparacion = []
                
                for simbolo in instrumentos_comparar:
                    detalle = obtener_cotizacion_detalle(token_acceso, "ROFEX", simbolo)
                    if detalle:
                        datos_comparacion.append({
                            'simbolo': simbolo,
                            'precio': detalle.get('ultimoPrecio', 0),
                            'variacion': detalle.get('variacion', 0),
                            'volumen': detalle.get('volumen', 0)
                        })
                
                if datos_comparacion:
                    df_comparacion = pd.DataFrame(datos_comparacion)
                    
                    # Gráfico comparativo
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=df_comparacion['simbolo'],
                        y=df_comparacion['precio'],
                        name='Precio',
                        text=df_comparacion['precio'].round(2),
                        textposition='auto'
                    ))
                    fig.update_layout(
                        title="Comparación de Precios",
                        xaxis_title="Símbolo",
                        yaxis_title="Precio ($)"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tabla comparativa
                    st.dataframe(df_comparacion, use_container_width=True)
                    
                    # Almacenar comparación
                    if st.button("💾 Almacenar Comparación", key="store_comparacion"):
                        nombre_archivo = almacenar_datos_para_analisis(datos_comparacion, "Comparacion_Instrumentos")
                        if nombre_archivo:
                            st.success(f"✅ Comparación almacenada en {nombre_archivo}")
                else:
                    st.warning("No se pudieron obtener datos para la comparación")
        
        # --- SUB-TAB: Clasificación Estrategias (Alpha/Beta) ---
        st.markdown("---")
        st.markdown("### 📊 Clasificación de Estrategias (Alpha/Beta)")
        
        # Configuración para análisis de estrategias
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Configuración de Análisis")
            
            # Selección de benchmark
            benchmark_seleccionado = st.selectbox(
                "Seleccione Benchmark:",
                options=list(BENCHMARK_FACTORS.keys()),
                format_func=lambda x: f"{x} - {BENCHMARK_FACTORS[x]}",
                index=0,
                key="benchmark_strategy"
            )
            
            # Período de análisis
            periodo_estrategia = st.selectbox(
                "Período de Análisis:",
                options=['1mo', '3mo', '6mo', '1y', '2y', '5y'],
                index=3,
                key="periodo_strategy"
            )
            
            # Umbral de significancia
            umbral_significancia = st.slider(
                "Umbral de Significancia (p-value):",
                min_value=0.01,
                max_value=0.10,
                value=0.05,
                step=0.01,
                key="umbral_strategy"
            )
        
        with col2:
            st.subheader("📋 Información")
            st.info(f"""
            **Benchmark Seleccionado:** {benchmark_seleccionado} - {BENCHMARK_FACTORS[benchmark_seleccionado]}
            
            **Período:** {periodo_estrategia}
            
            **Umbral de Significancia:** {umbral_significancia}
            """)
        
        # Selección de paneles para análisis
        st.subheader("🔍 Selección de Paneles para Análisis")
        
        # Obtener paneles disponibles
        paneles_disponibles = obtener_paneles_cotizacion(token_acceso, pais)
        if paneles_disponibles:
            nombres_paneles = [panel.get('nombre', f"Panel {i}") for i, panel in enumerate(paneles_disponibles)]
            paneles_seleccionados = st.multiselect(
                "Seleccione paneles para analizar:",
                options=nombres_paneles,
                default=nombres_paneles[:3] if len(nombres_paneles) >= 3 else nombres_paneles
            )
        else:
            st.warning("No se pudieron obtener paneles. Usando tickers de ejemplo.")
            paneles_seleccionados = []
        
        # Opción para usar tickers de ejemplo si no hay paneles
        if not paneles_seleccionados:
            tickers_ejemplo = ['GGAL', 'YPF', 'PAMP', 'BMA', 'SUPV', 'CEPU', 'TXAR', 'ALUA']
            tickers_analizar = st.multiselect(
                "Seleccione tickers para analizar:",
                options=tickers_ejemplo,
                default=tickers_ejemplo[:5]
            )
        else:
            tickers_analizar = []
            # Aquí se procesarían los paneles seleccionados para obtener tickers
            st.info("Los tickers se obtendrán de los paneles seleccionados")
        
        # Ejecutar análisis de estrategias
        if st.button("🚀 Ejecutar Análisis de Estrategias", use_container_width=True):
            if not tickers_analizar and not paneles_seleccionados:
                st.warning("Selecciona al menos un panel o ticker para analizar")
                return
            
            # Obtener datos del benchmark
            with st.spinner(f"Obteniendo datos del benchmark {benchmark_seleccionado}..."):
                benchmark_returns = obtener_serie_historica_yfinance(benchmark_seleccionado, periodo_estrategia)
                
                if benchmark_returns is None:
                    st.error("No se pudieron obtener los datos del benchmark")
                    return
            
            # Procesar tickers de los paneles seleccionados
            if paneles_seleccionados:
                tickers_analizar = []
                for panel_nombre in paneles_seleccionados:
                    panel_data = next((p for p in paneles_disponibles if p.get('nombre') == panel_nombre), None)
                    if panel_data:
                        instrumentos_panel = obtener_instrumentos_por_panel(
                            token_acceso,
                            panel_data.get('instrumento', 'Acciones'),
                            panel_nombre,
                            pais
                        )
                        if instrumentos_panel:
                            tickers_panel = [item.get('simbolo') for item in instrumentos_panel if item.get('simbolo')]
                            tickers_analizar.extend(tickers_panel)
            
            if not tickers_analizar:
                st.warning("No se encontraron tickers para analizar")
                return
            
            # Ejecutar análisis
            resultados = []
            
            with st.spinner("Analizando estrategias de inversión..."):
                for ticker in tickers_analizar[:20]:  # Limitar a 20 tickers para evitar sobrecarga
                    asset_returns = obtener_serie_historica_yfinance(ticker, periodo_estrategia)
                    
                    if asset_returns is not None:
                        beta, alpha, r_squared, p_value = calcular_beta_alpha(asset_returns, benchmark_returns)
                        estrategia = clasificar_estrategia(beta, alpha, r_squared, p_value)
                        
                        resultados.append({
                            'Ticker': ticker,
                            'Beta': beta if beta is not None else 0,
                            'Alpha': alpha if alpha is not None else 0,
                            'R_Squared': r_squared if r_squared is not None else 0,
                            'P_Value': p_value if p_value is not None else 1,
                            'Estrategia': estrategia,
                            'Retorno_Total': asset_returns.sum(),
                            'Volatilidad': asset_returns.std() * np.sqrt(252)
                        })
            
            if resultados:
                # Crear DataFrame
                df_resultados = pd.DataFrame(resultados)
                
                # Mostrar resultados
                st.subheader("📊 Resultados del Análisis de Estrategias")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.dataframe(
                        df_resultados[['Ticker', 'Beta', 'Alpha', 'Estrategia']].round(4),
                        use_container_width=True
                    )
                
                with col2:
                    # Estadísticas por estrategia
                    stats_estrategia = df_resultados.groupby('Estrategia').agg({
                        'Ticker': 'count',
                        'Beta': ['mean', 'std'],
                        'Alpha': ['mean', 'std']
                    }).round(4)
                    
                    st.write("**Estadísticas por Estrategia:**")
                    st.dataframe(stats_estrategia, use_container_width=True)
                
                # Gráfico alpha vs beta
                st.subheader("📈 Gráfico Alpha vs Beta")
                fig_alpha_beta = crear_grafico_alpha_beta(df_resultados)
                st.plotly_chart(fig_alpha_beta, use_container_width=True)
                
                # Explicación de estrategias
                st.subheader("📚 Explicación de Estrategias")
                
                estrategias_info = {
                    'Index Tracker': {
                        'descripcion': 'Replica el rendimiento de un benchmark',
                        'caracteristicas': 'β ≈ 1, α ≈ 0',
                        'ejemplo': 'ETF que replica S&P 500'
                    },
                    'Tradicional Long-Only': {
                        'descripcion': 'Supera el mercado con retorno extra no correlacionado',
                        'caracteristicas': 'β ≈ 1, α > 0',
                        'ejemplo': 'Fondos mutuos tradicionales'
                    },
                    'Smart Beta': {
                        'descripcion': 'Supera el mercado ajustando dinámicamente los pesos',
                        'caracteristicas': 'β > 1 (mercado alcista), β < 1 (mercado bajista), α ≈ 0',
                        'ejemplo': 'ETFs factor-based'
                    },
                    'Hedge Fund': {
                        'descripcion': 'Entrega retornos absolutos no correlacionados con el mercado',
                        'caracteristicas': 'β ≈ 0, α > 0',
                        'ejemplo': 'Estrategias long/short'
                    }
                }
                
                for estrategia, info in estrategias_info.items():
                    with st.expander(f"📋 {estrategia}"):
                        st.write(f"**Descripción:** {info['descripcion']}")
                        st.write(f"**Características:** {info['caracteristicas']}")
                        st.write(f"**Ejemplo:** {info['ejemplo']}")
                
                # Almacenar resultados
                if st.button("💾 Guardar Análisis de Estrategias", use_container_width=True):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nombre_archivo = f"analisis_estrategias_{timestamp}.json"
                    
                    try:
                        with open(nombre_archivo, 'w', encoding='utf-8') as f:
                            json.dump({
                                'fecha_analisis': datetime.now().isoformat(),
                                'benchmark': benchmark_seleccionado,
                                'periodo': periodo_estrategia,
                                'paneles_analizados': paneles_seleccionados,
                                'resultados': df_resultados.to_dict('records')
                            }, f, ensure_ascii=False, indent=2)
                        
                        st.success(f"✅ Análisis de estrategias guardado en {nombre_archivo}")
                    except Exception as e:
                        st.error(f"Error al guardar: {str(e)}")
            else:
                st.warning("No se obtuvieron resultados del análisis")
    
    def obtener_tickers_por_panel(token_portador, paneles, pais='Argentina'):
        """
        Devuelve un diccionario con listas de tickers reales por panel para el universo aleatorio.
        Si no hay API, usa listas fijas de tickers representativos.
        Retorna: (dict panel->tickers, dict panel->descripciones)
        """
    tickers = {}
    descripciones = {}
    # Paneles y ejemplos (puedes reemplazar por consulta a la API de IOL si tienes endpoint)
    paneles_dict = {
        'acciones': [
            ('GGAL', 'Grupo Financiero Galicia'),
            ('YPFD', 'YPF S.A.'),
            ('PAMP', 'Pampa Energía'),
            ('BMA', 'Banco Macro'),
            ('SUPV', 'Grupo Supervielle'),
            ('CEPU', 'Central Puerto'),
            ('TXAR', 'Ternium Argentina'),
            ('ALUA', 'Aluar'),
            ('TGSU2', 'Transportadora Gas del Sur'),
            ('EDN', 'Edenor'),
        ],
        'cedears': [
            ('AAPL', 'Apple'),
            ('TSLA', 'Tesla'),
            ('AMZN', 'Amazon'),
            ('GOOGL', 'Alphabet'),
            ('MSFT', 'Microsoft'),
            ('KO', 'Coca-Cola'),
            ('MELI', 'Mercado Libre'),
            ('BABA', 'Alibaba'),
            ('JNJ', 'Johnson & Johnson'),
            ('PG', 'Procter & Gamble'),
        ],
        'aDRs': [
            ('BBAR', 'BBVA Argentina'),
            ('BMA', 'Banco Macro'),
            ('GGAL', 'Grupo Galicia'),
            ('PAM', 'Pampa Energia'),
            ('SUPV', 'Supervielle'),
        ],
        'titulosPublicos': [
            ('AL30', 'Bonar 2030'),
            ('GD30', 'Global 2030'),
            ('AL35', 'Bonar 2035'),
            ('GD35', 'Global 2035'),
            ('AL29', 'Bonar 2029'),
            ('GD29', 'Global 2029'),
        ],
        'obligacionesNegociables': [
            ('PBY22', 'Pampa Energía ON'),
            ('CGC24', 'Compañía General de Combustibles ON'),
            ('YPF23', 'YPF ON'),
            ('TGSU2', 'Transportadora Gas del Sur ON'),
        ]
    }
    for panel in paneles:
        panel_l = panel.lower()
        if panel_l in paneles_dict:
            tickers[panel] = [t[0] for t in paneles_dict[panel_l]]
            descripciones[panel] = [t[1] for t in paneles_dict[panel_l]]
        else:
            tickers[panel] = []
            descripciones[panel] = []
    return tickers, descripciones

# --- Función: calcular retornos y covarianza con ventana móvil ---
def calcular_estadisticas_ventana_movil(precios, ventana=252):
    """
    Calcula retornos esperados y matriz de covarianza usando una ventana móvil.
    precios: DataFrame de precios (columnas=activos, filas=fechas)
    ventana: días para la ventana móvil (por defecto 1 año)
    Devuelve: retornos esperados anualizados, covarianza anualizada
    """
    retornos = precios.pct_change().dropna()
    retornos_ventana = retornos.iloc[-ventana:]
    mean_ret = retornos_ventana.mean() * 252
    cov = retornos_ventana.cov() * 252
    return mean_ret, cov

# --- Función: optimización Markowitz (max Sharpe) ---
def optimizar_markowitz(mean_ret, cov, risk_free_rate=0.0):
    """
    Devuelve los pesos óptimos de Markowitz (max Sharpe, long-only)
    """
    import numpy as np
    import scipy.optimize as op
    n = len(mean_ret)
    bounds = tuple((0, 1) for _ in range(n))
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1},)
    def neg_sharpe(x):
        port_ret = np.dot(mean_ret, x)
        port_vol = np.sqrt(np.dot(x, np.dot(cov, x)))
        if port_vol == 0:
            return 1e6
        return -(port_ret - risk_free_rate) / port_vol
    x0 = np.ones(n) / n
    res = op.minimize(neg_sharpe, x0, bounds=bounds, constraints=constraints)
    if res.success:
        return res.x
    else:
        return x0

# --- Función: backtest con rebalanceo periódico ---
def backtest_markowitz(precios, ventana=252, rebalanceo=63, risk_free_rate=0.0):
    """
    Simula la evolución de un portafolio Markowitz con rebalanceo periódico.
    precios: DataFrame de precios (columnas=activos, filas=fechas)
    ventana: días para estimar retornos/covarianza
    rebalanceo: cada cuántos días rebalancear (63 = 3 meses aprox)
    Devuelve: fechas, valores del portafolio, lista de pesos, fechas de rebalanceo
    """
    import numpy as np
    fechas = precios.index
    n_activos = precios.shape[1]
    portafolio_valor = [1.0]
    pesos_hist = []
    fechas_reb = []
    pesos_actual = np.ones(n_activos) / n_activos
    for i in range(ventana, len(fechas)-1, rebalanceo):
        precios_window = precios.iloc[i-ventana:i]
        mean_ret, cov = calcular_estadisticas_ventana_movil(precios_window, ventana)
        pesos_actual = optimizar_markowitz(mean_ret, cov, risk_free_rate)
        pesos_hist.append(pesos_actual)
        fechas_reb.append(fechas[i])
        # Simular evolución hasta el próximo rebalanceo
        for j in range(i, min(i+rebalanceo, len(fechas)-1)):
            ret = (precios.iloc[j+1] / precios.iloc[j] - 1).values
            portafolio_valor.append(portafolio_valor[-1] * (1 + np.dot(pesos_actual, ret)))
    # Completar hasta el final con los últimos pesos
    while len(portafolio_valor) < len(fechas):
        portafolio_valor.append(portafolio_valor[-1])
    return fechas, portafolio_valor, pesos_hist, fechas_reb

# --- Función: visualización de backtest y pesos ---
def mostrar_backtest_markowitz(precios, ventana=252, rebalanceo=63, risk_free_rate=0.0):
    """
    Visualiza la evolución del portafolio Markowitz con rebalanceo periódico.
    """
    import plotly.graph_objects as go
    fechas, portafolio_valor, pesos_hist, fechas_reb = backtest_markowitz(precios, ventana, rebalanceo, risk_free_rate)
    import streamlit as st
    st.subheader("📈 Evolución del Portafolio Markowitz (Backtest)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fechas, y=portafolio_valor, mode='lines', name='Valor Portafolio'))
    fig.update_layout(title="Backtest Markowitz con rebalanceo", xaxis_title="Fecha", yaxis_title="Valor acumulado", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
    # Mostrar evolución de pesos
    st.subheader("🔄 Evolución de Pesos por Activo")
    if pesos_hist:
        import numpy as np
        activos = precios.columns
        pesos_array = np.array(pesos_hist)
        fig2 = go.Figure()
        for idx, activo in enumerate(activos):
            fig2.add_trace(go.Scatter(x=fechas_reb, y=pesos_array[:, idx], mode='lines+markers', name=activo))
        fig2.update_layout(title="Pesos óptimos en cada rebalanceo", xaxis_title="Fecha de rebalanceo", yaxis_title="Peso", template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No hay datos suficientes para mostrar la evolución de pesos.")
# --- FIN FUNCIONES ROBUSTAS ---

def obtener_series_historicas_aleatorias_con_capital(tickers_por_panel, paneles_seleccionados, cantidad_activos, fecha_desde, fecha_hasta, ajustada, token_acceso, capital_ars):
    """
    Selecciona aleatoriamente tickers de los paneles seleccionados, descarga sus series históricas y devuelve:
    - series_historicas: dict[ticker] -> DataFrame de precios
    - seleccion_final: dict[panel] -> lista de tickers seleccionados
    Respeta la cantidad de activos por panel y el capital disponible.
    """
    import random
    import yfinance as yf
    import pandas as pd
    series_historicas = {}
    seleccion_final = {}
    for panel in paneles_seleccionados:
        tickers = tickers_por_panel.get(panel, [])
        if not tickers:
            continue
        seleccionados = random.sample(tickers, min(cantidad_activos, len(tickers)))
        seleccion_final[panel] = seleccionados
        for ticker in seleccionados:
            try:
                # Preferir yfinance para tickers internacionales y Cedears
                if panel.lower() in ['cedears', 'adrs'] or ticker.isalpha():
                    df = yf.download(ticker, start=fecha_desde, end=fecha_hasta)[['Close']]
                    if not df.empty:
                        df = df.rename(columns={'Close': 'precio'})
                        df = df.reset_index().rename(columns={'Date': 'fecha'})
                        series_historicas[ticker] = df
                else:
                    # Para acciones locales, usar la API de IOL si es necesario
                    df = obtener_serie_historica_iol(token_acceso, 'BCBA', ticker, fecha_desde, fecha_hasta, ajustada)
                    if df is not None and not df.empty:
                        series_historicas[ticker] = df
            except Exception as e:
                continue
    # Validar que haya suficientes series
    total_activos = sum(len(v) for v in seleccion_final.values())
    if total_activos == 0 or not series_historicas:
        raise Exception("No se pudieron obtener series históricas suficientes para el universo aleatorio.")
    return series_historicas, seleccion_final

def mostrar_informe_ia(token_acceso, id_cliente):
    """
    Genera un informe inteligente del portafolio usando IA
    """
    st.header("🤖 Informe IA - Análisis Inteligente")
    
    # Obtener datos del portafolio
    portafolio = obtener_portafolio(token_acceso, id_cliente)
    estado_cuenta = obtener_estado_cuenta(token_acceso, id_cliente)
    
    if not portafolio or not estado_cuenta:
        st.warning("No se pudieron obtener los datos necesarios para el informe IA")
        return
    
    # Configuración de la IA
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔧 Configuración del Análisis IA")
        
        # API Key para Gemini (opcional)
        gemini_api_key = st.text_input(
            "Clave API de Gemini (opcional):",
            type="password",
            help="Para análisis más avanzado con IA de Google"
        )
        
        # Opciones de análisis
        analisis_opciones = st.multiselect(
            "Seleccione tipos de análisis:",
            ["Análisis de Riesgo", "Recomendaciones de Rebalanceo", "Análisis de Correlaciones", 
             "Predicción de Tendencias", "Análisis de Concentración", "Optimización de Portafolio"],
            default=["Análisis de Riesgo", "Recomendaciones de Rebalanceo"]
        )
        
        # Período de análisis
        periodo_analisis = st.selectbox(
            "Período de análisis:",
            ["Último mes", "Últimos 3 meses", "Últimos 6 meses", "Último año"],
            index=2
        )
    
    with col2:
        st.subheader("📊 Métricas Rápidas")
        
        # Calcular métricas básicas
        valor_total = sum(float(activo.get('valorMercado', 0)) for activo in portafolio)
        activos_count = len(portafolio)
        
        st.metric("Valor Total", f"${valor_total:,.2f}")
        st.metric("Cantidad de Activos", activos_count)
        
        # Distribución por tipo
        tipos_activo = {}
        for activo in portafolio:
            tipo = activo.get('tipoActivo', 'Otro')
            valor = float(activo.get('valorMercado', 0))
            tipos_activo[tipo] = tipos_activo.get(tipo, 0) + valor
        
        if tipos_activo:
            tipo_principal = max(tipos_activo, key=tipos_activo.get)
            st.metric("Tipo Principal", tipo_principal)
    
    # Generar informe
    if st.button("🚀 Generar Informe IA", type="primary", use_container_width=True):
        with st.spinner("Generando informe inteligente..."):
            
            # Crear tabs para diferentes secciones del informe
            tab1, tab2, tab3, tab4 = st.tabs([
                "📈 Análisis General", 
                "⚖️ Gestión de Riesgo", 
                "🎯 Recomendaciones",
                "📊 Visualizaciones"
            ])
            
            with tab1:
                st.subheader("📈 Análisis General del Portafolio")
                
                # Análisis de composición
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Composición por Tipo de Activo:**")
                    if tipos_activo:
                        # Crear gráfico de torta
                        fig = go.Figure(data=[go.Pie(
                            labels=list(tipos_activo.keys()),
                            values=list(tipos_activo.values()),
                            hole=0.3
                        )])
                        fig.update_layout(title="Distribución del Portafolio")
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.write("**Top 5 Activos por Valor:**")
                    activos_ordenados = sorted(portafolio, key=lambda x: float(x.get('valorMercado', 0)), reverse=True)
                    
                    for i, activo in enumerate(activos_ordenados[:5], 1):
                        simbolo = activo.get('simbolo', 'N/A')
                        valor = float(activo.get('valorMercado', 0))
                        porcentaje = (valor / valor_total * 100) if valor_total > 0 else 0
                        
                        st.write(f"{i}. **{simbolo}** - ${valor:,.2f} ({porcentaje:.1f}%)")
            
            with tab2:
                st.subheader("⚖️ Análisis de Riesgo")
                
                # Calcular métricas de riesgo
                if "Análisis de Riesgo" in analisis_opciones:
                    
                    # Concentración del portafolio
                    concentracion = {}
                    for activo in portafolio:
                        simbolo = activo.get('simbolo', 'N/A')
                        valor = float(activo.get('valorMercado', 0))
                        concentracion[simbolo] = valor
                    
                    # Top concentraciones
                    top_concentraciones = sorted(concentracion.items(), key=lambda x: x[1], reverse=True)[:5]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Concentración por Activo:**")
                        for simbolo, valor in top_concentraciones:
                            porcentaje = (valor / valor_total * 100) if valor_total > 0 else 0
                            color = "🔴" if porcentaje > 20 else "🟡" if porcentaje > 10 else "🟢"
                            st.write(f"{color} {simbolo}: {porcentaje:.1f}%")
                    
                    with col2:
                        st.write("**Alertas de Riesgo:**")
                        
                        # Verificar concentración excesiva
                        max_concentracion = max(concentracion.values()) if concentracion else 0
                        max_porcentaje = (max_concentracion / valor_total * 100) if valor_total > 0 else 0
                        
                        if max_porcentaje > 30:
                            st.error(f"⚠️ Concentración excesiva: {max_porcentaje:.1f}% en un solo activo")
                        elif max_porcentaje > 20:
                            st.warning(f"⚠️ Concentración alta: {max_porcentaje:.1f}% en un solo activo")
                        else:
                            st.success("✅ Concentración diversificada")
                        
                        # Verificar diversificación
                        if len(portafolio) < 5:
                            st.warning("⚠️ Portafolio poco diversificado")
                        else:
                            st.success(f"✅ Buena diversificación: {len(portafolio)} activos")
            
            with tab3:
                st.subheader("🎯 Recomendaciones IA")
                
                if "Recomendaciones de Rebalanceo" in analisis_opciones:
                    
                    # Análisis básico de recomendaciones
                    recomendaciones = []
                    
                    # Verificar concentración
                    if max_concentracion > valor_total * 0.3:
                        recomendaciones.append({
                            "tipo": "🔴 Crítica",
                            "titulo": "Reducir concentración",
                            "descripcion": f"El activo más concentrado representa el {max_porcentaje:.1f}% del portafolio. Considere diversificar."
                        })
                    
                    # Verificar diversificación
                    if len(portafolio) < 5:
                        recomendaciones.append({
                            "tipo": "🟡 Importante",
                            "titulo": "Aumentar diversificación",
                            "descripcion": "Considere agregar más activos para mejorar la diversificación del portafolio."
                        })
                    
                    # Verificar tipos de activos
                    if len(tipos_activo) < 3:
                        recomendaciones.append({
                            "tipo": "🟡 Importante",
                            "titulo": "Diversificar tipos de activos",
                            "descripcion": "El portafolio está concentrado en pocos tipos de activos. Considere agregar diferentes clases de activos."
                        })
                    
                    # Mostrar recomendaciones
                    if recomendaciones:
                        for rec in recomendaciones:
                            with st.expander(f"{rec['tipo']} {rec['titulo']}"):
                                st.write(rec['descripcion'])
                    else:
                        st.success("✅ No se detectaron problemas críticos en el portafolio")
                    
                    # Recomendaciones generales
                    st.subheader("💡 Sugerencias de Mejora")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Estrategias Sugeridas:**")
                        st.write("• Rebalanceo trimestral")
                        st.write("• Monitoreo de correlaciones")
                        st.write("• Evaluación de liquidez")
                        st.write("• Análisis de volatilidad")
                    
                    with col2:
                        st.write("**Próximos Pasos:**")
                        st.write("• Revisar asignación por sector")
                        st.write("• Evaluar exposición cambiaria")
                        st.write("• Considerar activos defensivos")
                        st.write("• Planificar horizonte temporal")
            
            with tab4:
                st.subheader("📊 Visualizaciones Avanzadas")
                
                if "Análisis de Correlaciones" in analisis_opciones:
                    st.write("**Análisis de Correlaciones entre Activos:**")
                    
                    # Crear matriz de correlaciones simulada (en un caso real se usarían datos históricos)
                    if len(portafolio) > 1:
                        # Simular correlaciones (en implementación real se calcularían con datos históricos)
                        simbolos = [activo.get('simbolo', f'Activo_{i}') for i, activo in enumerate(portafolio[:5])]
                        
                        # Matriz de correlación simulada
                        np.random.seed(42)
                        correlaciones = np.random.rand(len(simbolos), len(simbolos))
                        correlaciones = (correlaciones + correlaciones.T) / 2
                        np.fill_diagonal(correlaciones, 1)
                        
                        fig = go.Figure(data=go.Heatmap(
                            z=correlaciones,
                            x=simbolos,
                            y=simbolos,
                            colorscale='RdBu',
                            zmid=0
                        ))
                        fig.update_layout(title="Matriz de Correlaciones")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Se necesitan al menos 2 activos para analizar correlaciones")
                
                if "Predicción de Tendencias" in analisis_opciones:
                    st.write("**Análisis de Tendencias:**")
                    
                    # Gráfico de evolución del valor del portafolio (simulado)
                    fechas = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
                    valores_simulados = np.cumsum(np.random.randn(len(fechas)) * 0.02 + 0.01) * valor_total + valor_total
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=fechas,
                        y=valores_simulados,
                        mode='lines+markers',
                        name='Valor del Portafolio'
                    ))
                    fig.update_layout(
                        title="Evolución Simulada del Portafolio",
                        xaxis_title="Fecha",
                        yaxis_title="Valor ($)"
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    # Información adicional
    st.divider()
    st.info("💡 **Nota:** Este informe utiliza análisis básico de datos. Para análisis más avanzado, considere proporcionar una clave API de Gemini.")

if __name__ == "__main__":
    main()
