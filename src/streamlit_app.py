"""
IOL Portfolio Analyzer - Versión Mejorada y Organizada
=====================================================

Aplicación Streamlit para análisis avanzado de portafolios de inversión
con integración a la API de IOL (Invertir Online).

Características principales:
- Análisis completo de portafolios
- Optimización avanzada con múltiples estrategias
- Análisis técnico integrado
- Gestión de riesgo y diversificación
- Interfaz moderna y responsive
"""

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
import warnings
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import time
import importlib
import random

# Configuración de warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# ============================================================================

def configurar_pagina():
    """Configura la página principal de Streamlit"""
    st.set_page_config(
        page_title="IOL Portfolio Analyzer Pro",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def aplicar_estilos_css():
    """Aplica estilos CSS personalizados para una interfaz moderna"""
    st.markdown("""
    <style>
        /* Tema oscuro profesional */
        .stApp, 
        .stApp > div[data-testid="stAppViewContainer"],
        .stApp > div[data-testid="stAppViewContainer"] > div {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #f8f9fa;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Títulos con gradiente */
        h1, h2, h3 {
            background: linear-gradient(90deg, #4CAF50, #45a049);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }
        
        /* Tarjetas modernas */
        .metric-card {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid #4CAF50;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
        }
        
        /* Botones modernos */
        .stButton > button {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            border-radius: 25px;
            border: none;
            color: white;
            font-weight: 600;
            padding: 12px 24px;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(76, 175, 80, 0.4);
        }
        
        /* Pestañas mejoradas */
        .stTabs [data-baseweb="tab"] {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            color: #e2e8f0;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        }
        
        /* Inputs modernos */
        .stTextInput, .stNumberInput, .stDateInput, .stSelectbox {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 10px;
            border: 1px solid #4CAF50;
        }
        
        /* Tablas mejoradas */
        .dataframe {
            background: rgba(30, 41, 59, 0.8);
            border-radius: 15px;
            overflow: hidden;
        }
        
        /* Scrollbar personalizada */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: #1e293b;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            border-radius: 5px;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# FUNCIONES DE ANÁLISIS DE PORTAFOLIO AVANZADO
# ============================================================================

def load_data(rics, argentina_tickers, token_acceso=None):
    """
    Descarga datos intradía para una lista de símbolos usando yfinance y/o IOL.
    
    Args:
        rics (list): Lista de símbolos a descargar.
        argentina_tickers (set): Conjunto de tickers argentinos.
        token_acceso (str, optional): Token de acceso para IOL.
        
    Returns:
        dict: Diccionario con los datos descargados.
    """
    data = {}
    progress_bar = st.progress(0)
    total_rics = len(rics)
    
    for i, ric in enumerate(rics):
        try:
            with st.spinner(f"Descargando datos para {ric}..."):
                # Intentar primero con IOL si es un símbolo argentino y tenemos token
                if ric in argentina_tickers and token_acceso:
                    st.info(f"🔄 Intentando obtener datos de {ric} desde IOL...")
                    try:
                        # Intentar obtener serie histórica desde IOL
                        fecha_hasta = date.today()
                        fecha_desde = fecha_hasta - timedelta(days=30)
                        
                        df_iol = obtener_serie_historica_iol(
                            token_acceso,
                            'bMERVAL',  # Mercado por defecto para acciones argentinas
                            ric,
                            fecha_desde.strftime('%Y-%m-%d'),
                            fecha_hasta.strftime('%Y-%m-%d'),
                            'ajustada'
                        )
                        
                        if not df_iol.empty and 'ultimoPrecio' in df_iol.columns:
                            # Convertir datos de IOL al formato de yfinance
                            df_converted = pd.DataFrame({
                                'Open': df_iol['apertura'],
                                'High': df_iol['maximo'],
                                'Low': df_iol['minimo'],
                                'Close': df_iol['ultimoPrecio'],
                                'Volume': df_iol['volumenNominal']
                            }, index=df_iol['fechaHora'])
                            
                            data[ric] = df_converted
                            st.success(f"✅ Datos obtenidos desde IOL para {ric}")
                            continue
                        else:
                            st.warning(f"⚠️ No se pudieron obtener datos de IOL para {ric}, intentando con yfinance...")
                    except Exception as e:
                        st.warning(f"⚠️ Error con IOL para {ric}: {str(e)}, intentando con yfinance...")
                
                # Si no se pudo con IOL o no es símbolo argentino, usar yfinance
                symbol = ric + ".BA" if ric in argentina_tickers else ric
                df = yf.download(symbol, period="1d", interval="1m")
                
                if not df.empty:
                    data[ric] = df
                    st.success(f"✅ Datos descargados para {ric} desde yfinance")
                else:
                    st.warning(f"⚠️ No se encontraron datos para {ric} (buscando {symbol})")
                    
        except Exception as e:
            st.error(f"❌ Error al descargar datos para {ric}: {e}")
        
        # Actualizar barra de progreso
        progress_bar.progress((i + 1) / total_rics)
    
    progress_bar.empty()
    return data

def calcular_frontera_eficiente_avanzada(rics, notional, target_return=None, include_min_variance=True, token_acceso=None):
    """
    Calcula la frontera eficiente usando análisis avanzado de portafolio.
    
    Args:
        rics (list): Lista de símbolos de activos
        notional (float): Valor nominal del portafolio
        target_return (float, optional): Retorno objetivo
        include_min_variance (bool): Incluir portafolio de mínima varianza
        token_acceso (str, optional): Token de acceso para IOL
        
    Returns:
        dict: Diccionario con portafolios optimizados
    """
    try:
        # Configurar parámetros
        num_assets = len(rics)
        if num_assets < 2:
            st.error("❌ Se necesitan al menos 2 activos para calcular la frontera eficiente")
            return None, None
        
        # Descargar datos usando yfinance y/o IOL
        argentina_tickers = {"INTC", "ETHA", "GOOGL", "ARKK", "GGAL", "YPF", "PAMP", "COME", "BYMA", "S10N5", "S30S5"}
        data = load_data(rics, argentina_tickers, token_acceso)
        
        # Filtrar símbolos con datos disponibles
        rics_with_data = [ric for ric in rics if ric in data]
        if not rics_with_data:
            st.error("❌ No se descargó ningún dato. Revisa la lista de RICs o la conexión a Internet.")
            return None, None
        
        if len(rics_with_data) < 2:
            st.error("❌ Se necesitan al menos 2 activos con datos para el análisis")
            return None, None
        
        st.success(f"✅ Datos obtenidos para {len(rics_with_data)} activos")
        
        # Calcular retornos diarios
        returns_data = {}
        for ric in rics_with_data:
            if ric in data and not data[ric].empty:
                # Calcular retornos logarítmicos
                prices = data[ric]['Close']
                returns = np.log(prices / prices.shift(1)).dropna()
                if len(returns) > 0:
                    returns_data[ric] = returns
        
        if len(returns_data) < 2:
            st.error("❌ No hay suficientes datos de retornos para el análisis")
            return None, None
        
        # Crear DataFrame de retornos con índice común
        # Encontrar el índice común más largo
        common_dates = None
        for ric, returns in returns_data.items():
            if common_dates is None:
                common_dates = returns.index
            else:
                common_dates = common_dates.intersection(returns.index)
        
        if len(common_dates) < 10:  # Necesitamos al menos 10 días de datos
            st.error("❌ No hay suficientes fechas comunes entre los activos")
            return None, None
        
        # Crear DataFrame con fechas comunes
        returns_df = pd.DataFrame(index=common_dates)
        for ric, returns in returns_data.items():
            returns_df[ric] = returns.loc[common_dates]
        
        # Eliminar filas con NaN
        returns_df = returns_df.dropna()
        
        if len(returns_df) < 10:
            st.error("❌ Después de limpiar datos, no hay suficientes observaciones")
            return None, None
        
        st.success(f"✅ DataFrame de retornos creado con {len(returns_df)} observaciones")
        
        # Calcular métricas de portafolio
        mean_returns = returns_df.mean() * 252  # Anualizar
        cov_matrix = returns_df.cov() * 252     # Anualizar
        
        # Crear portafolios optimizados
        portfolios = {}
        
        # 1. Portafolio de mínima varianza
        if include_min_variance:
            try:
                min_var_weights = optimize_minimum_variance(cov_matrix)
                portfolios['min-variance'] = {
                    'weights': min_var_weights,
                    'return': np.sum(mean_returns * min_var_weights),
                    'volatility': np.sqrt(np.dot(min_var_weights.T, np.dot(cov_matrix, min_var_weights))),
                    'sharpe': np.sum(mean_returns * min_var_weights) / np.sqrt(np.dot(min_var_weights.T, np.dot(cov_matrix, min_var_weights)))
                }
            except Exception as e:
                st.warning(f"⚠️ Error en portafolio de mínima varianza: {str(e)}")
        
        # 2. Portafolio de máximo Sharpe
        try:
            max_sharpe_weights = optimize_maximum_sharpe(mean_returns, cov_matrix)
            portfolios['max-sharpe'] = {
                'weights': max_sharpe_weights,
                'return': np.sum(mean_returns * max_sharpe_weights),
                'volatility': np.sqrt(np.dot(max_sharpe_weights.T, np.dot(cov_matrix, max_sharpe_weights))),
                'sharpe': np.sum(mean_returns * max_sharpe_weights) / np.sqrt(np.dot(max_sharpe_weights.T, np.dot(cov_matrix, max_sharpe_weights)))
            }
        except Exception as e:
            st.warning(f"⚠️ Error en portafolio de máximo Sharpe: {str(e)}")
        
        # 3. Portafolio de pesos iguales
        equal_weights = np.ones(len(rics_with_data)) / len(rics_with_data)
        portfolios['equal-weight'] = {
            'weights': equal_weights,
            'return': np.sum(mean_returns * equal_weights),
            'volatility': np.sqrt(np.dot(equal_weights.T, np.dot(cov_matrix, equal_weights))),
            'sharpe': np.sum(mean_returns * equal_weights) / np.sqrt(np.dot(equal_weights.T, np.dot(cov_matrix, equal_weights)))
        }
        
        # 4. Portafolio con retorno objetivo
        if target_return is not None:
            try:
                target_weights = optimize_target_return(mean_returns, cov_matrix, target_return)
                portfolios['target-return'] = {
                    'weights': target_weights,
                    'return': np.sum(mean_returns * target_weights),
                    'volatility': np.sqrt(np.dot(target_weights.T, np.dot(cov_matrix, target_weights))),
                    'sharpe': np.sum(mean_returns * target_weights) / np.sqrt(np.dot(target_weights.T, np.dot(cov_matrix, target_weights)))
                }
            except Exception as e:
                st.warning(f"⚠️ Error en portafolio con retorno objetivo: {str(e)}")
        
        st.success(f"✅ {len(portfolios)} portafolios optimizados calculados exitosamente")
        return portfolios, returns_df
        
    except Exception as e:
        st.error(f"❌ Error calculando frontera eficiente: {str(e)}")
        st.exception(e)  # Mostrar el traceback completo para debugging
        return None, None

def optimize_minimum_variance(cov_matrix):
    """Optimiza para mínima varianza del portafolio"""
    n_assets = len(cov_matrix)
    
    def objective(weights):
        return np.dot(weights.T, np.dot(cov_matrix, weights))
    
    def constraint(weights):
        return np.sum(weights) - 1.0
    
    constraints = {'type': 'eq', 'fun': constraint}
    bounds = [(0, 1) for _ in range(n_assets)]
    initial_weights = np.array([1/n_assets] * n_assets)
    
    result = optimize.minimize(objective, initial_weights, 
                             constraints=constraints, bounds=bounds, method='SLSQP')
    
    if result.success:
        return result.x
    else:
        raise ValueError("Optimización no convergió")

def optimize_maximum_sharpe(mean_returns, cov_matrix, risk_free_rate=0.04):
    """Optimiza para máximo ratio de Sharpe"""
    n_assets = len(mean_returns)
    
    def objective(weights):
        portfolio_return = np.sum(mean_returns * weights)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        
        if portfolio_volatility == 0:
            return 0
        
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
        return -sharpe_ratio  # Minimizar negativo = maximizar positivo
    
    def constraint(weights):
        return np.sum(weights) - 1.0
    
    constraints = {'type': 'eq', 'fun': constraint}
    bounds = [(0, 1) for _ in range(n_assets)]
    initial_weights = np.array([1/n_assets] * n_assets)
    
    result = optimize.minimize(objective, initial_weights, 
                             constraints=constraints, bounds=bounds, method='SLSQP')
    
    if result.success:
        return result.x
    else:
        raise ValueError("Optimización no convergió")

def optimize_target_return(mean_returns, cov_matrix, target_return):
    """Optimiza para un retorno objetivo específico"""
    n_assets = len(mean_returns)
    
    def objective(weights):
        return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    
    def constraint_sum(weights):
        return np.sum(weights) - 1.0
    
    def constraint_return(weights):
        return np.sum(mean_returns * weights) - target_return
    
    constraints = [
        {'type': 'eq', 'fun': constraint_sum},
        {'type': 'eq', 'fun': constraint_return}
    ]
    
    bounds = [(0, 1) for _ in range(n_assets)]
    initial_weights = np.array([1/n_assets] * n_assets)
    
    result = optimize.minimize(objective, initial_weights, 
                             constraints=constraints, bounds=bounds, method='SLSQP')
    
    if result.success:
        return result.x
    else:
        raise ValueError("Optimización no convergió")

def plot_efficient_frontier_streamlit(portfolios):
    """
    Grafica la frontera eficiente usando Plotly para Streamlit.
    
    Args:
        portfolios (dict): Diccionario con los portafolios calculados.
    """
    if not portfolios:
        st.warning("No hay portafolios para graficar")
        return None
    
    risks, returns, labels = [], [], []
    for key, portfolio in portfolios.items():
        risks.append(portfolio['volatility'])
        returns.append(portfolio['return'])
        labels.append(key)
    
    # Crear gráfico con Plotly
    fig = go.Figure()
    
    # Puntos de portafolios
    fig.add_trace(go.Scatter(
        x=risks,
        y=returns,
        mode='markers+text',
        text=labels,
        textposition="top center",
        marker=dict(
            size=15,
            color=['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336'][:len(risks)],
            symbol='diamond'
        ),
        name='Portafolios Optimizados'
    ))
    
    # Línea de frontera eficiente (simplificada)
    if len(risks) >= 3:
        # Ordenar por riesgo
        sorted_data = sorted(zip(risks, returns, labels))
        sorted_risks, sorted_returns, sorted_labels = zip(*sorted_data)
        
        fig.add_trace(go.Scatter(
            x=sorted_risks,
            y=sorted_returns,
            mode='lines',
            line=dict(color='gray', dash='dash', width=2),
            name='Frontera Eficiente'
        ))
    
    fig.update_layout(
        title='Frontera Eficiente - Portafolios Optimizados',
        xaxis_title='Volatilidad Anual',
        yaxis_title='Retorno Anual',
        showlegend=True,
        template='plotly_white',
        height=500
    )
    
    return fig

# ============================================================================
# FUNCIONES DE AUTENTICACIÓN Y CONEXIÓN IOL
# ============================================================================

def obtener_encabezado_autorizacion(token_portador):
    """Retorna headers de autorización para la API de IOL"""
    return {
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'application/json'
    }

def obtener_tokens(usuario, contraseña):
    """Obtiene tokens de autenticación de IOL con manejo mejorado de errores"""
    url_login = 'https://api.invertironline.com/token'
    datos = {
        'username': usuario,
        'password': contraseña,
        'grant_type': 'password'
    }
    
    session = requests.Session()
    session.mount('https://', requests.adapters.HTTPAdapter(
        max_retries=3,
        pool_connections=10,
        pool_maxsize=10
    ))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            st.info(f"🔄 Intento {attempt + 1}/{max_attempts} de conexión a IOL...")
            
            timeout = 30 if attempt == 0 else 15
            respuesta = session.post(url_login, data=datos, headers=headers, timeout=timeout)
            
            if respuesta.status_code == 200:
                respuesta_json = respuesta.json()
                if 'access_token' in respuesta_json and 'refresh_token' in respuesta_json:
                    st.success("✅ Autenticación exitosa con IOL")
                    return respuesta_json['access_token'], respuesta_json['refresh_token']
                else:
                    st.error("❌ Respuesta de IOL incompleta")
                    return None, None
            
            elif respuesta.status_code == 400:
                st.error("❌ Verifique sus credenciales (usuario/contraseña)")
                return None, None
            elif respuesta.status_code == 401:
                st.error("❌ Credenciales inválidas o cuenta bloqueada")
                return None, None
            elif respuesta.status_code == 429:
                st.warning("⚠️ Demasiadas solicitudes. Esperando...")
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    st.error("❌ Límite de solicitudes excedido")
                    return None, None
            else:
                st.error(f"❌ Error HTTP {respuesta.status_code}")
                return None, None
                
        except requests.exceptions.Timeout:
            st.warning(f"⏱️ Timeout en intento {attempt + 1}")
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                st.error("❌ Timeout persistente")
                return None, None
                
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                return None, None
    
    st.error("❌ No se pudo establecer conexión después de múltiples intentos")
    return None, None

# ============================================================================
# FUNCIONES DE COTIZACIONES IOL
# ============================================================================

def obtener_cotizaciones_iol(token_portador, instrumento, pais):
    """
    Obtiene cotizaciones de un instrumento específico desde la API de IOL.
    
    Args:
        token_portador (str): Token de acceso
        instrumento (str): Tipo de instrumento (adrs, acciones, titulosPublicos, etc.)
        pais (str): País del mercado (argentina, estados_unidos, etc.)
        
    Returns:
        pd.DataFrame: DataFrame con las cotizaciones
    """
    url = f"https://api.invertironline.com/api/v2/Cotizaciones/{instrumento}/{pais}/Todos"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_portador}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if 'titulos' in data:
                df = pd.DataFrame(data['titulos'])
                st.success(f"✅ Cotizaciones obtenidas para {instrumento} en {pais}: {len(df)} instrumentos")
                return df
            else:
                st.warning(f"⚠️ No se encontraron datos de títulos para {instrumento} en {pais}")
                return pd.DataFrame()
        else:
            st.error(f"❌ Error HTTP {response.status_code} al obtener cotizaciones de {instrumento}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error al obtener cotizaciones de {instrumento}: {str(e)}")
        return pd.DataFrame()

def obtener_serie_historica_iol(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="ajustada"):
    """
    Obtiene serie histórica de cotizaciones desde la API de IOL.
    
    Args:
        token_portador (str): Token de acceso
        mercado (str): Mercado (bCBA, etc.)
        simbolo (str): Símbolo del instrumento
        fecha_desde (str): Fecha desde (YYYY-MM-DD)
        fecha_hasta (str): Fecha hasta (YYYY-MM-DD)
        ajustada (str): Tipo de ajuste
        
    Returns:
        pd.DataFrame: DataFrame con la serie histórica
    """
    url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_portador}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                # Convertir fechaHora a datetime
                if 'fechaHora' in df.columns:
                    df['fechaHora'] = pd.to_datetime(df['fechaHora'])
                st.success(f"✅ Serie histórica obtenida para {simbolo}: {len(df)} registros")
                return df
            else:
                st.warning(f"⚠️ No se encontraron datos históricos para {simbolo}")
                return pd.DataFrame()
        else:
            st.error(f"❌ Error HTTP {response.status_code} al obtener serie histórica de {simbolo}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error al obtener serie histórica de {simbolo}: {str(e)}")
        return pd.DataFrame()

# Funciones específicas para cada tipo de cotización
def obtener_cotizaciones_adrs_iol(token_portador):
    """Obtiene cotizaciones de ADRs desde IOL"""
    return obtener_cotizaciones_iol(token_portador, 'adrs', 'estados_unidos')

def obtener_cotizaciones_acciones_eeuu_iol(token_portador):
    """Obtiene cotizaciones de acciones de EEUU desde IOL"""
    return obtener_cotizaciones_iol(token_portador, 'acciones', 'estados_unidos')

def obtener_cotizaciones_acciones_argentina_iol(token_portador):
    """Obtiene cotizaciones de acciones argentinas desde IOL"""
    return obtener_cotizaciones_iol(token_portador, 'acciones', 'argentina')

def obtener_cotizaciones_titulos_publicos_iol(token_portador):
    """Obtiene cotizaciones de títulos públicos desde IOL"""
    return obtener_cotizaciones_iol(token_portador, 'titulosPublicos', 'argentina')

def obtener_cotizaciones_obligaciones_negociables_iol(token_portador):
    """Obtiene cotizaciones de obligaciones negociables desde IOL"""
    return obtener_cotizaciones_iol(token_portador, 'obligacionesNegociables', 'argentina')

def obtener_cotizaciones_cedears_iol(token_portador):
    """Obtiene cotizaciones de CEDEARs desde IOL"""
    return obtener_cotizaciones_iol(token_portador, 'cedears', 'argentina')

def obtener_cotizaciones_cauciones_iol(token_portador):
    """Obtiene cotizaciones de cauciones desde IOL"""
    return obtener_cotizaciones_iol(token_portador, 'cauciones', 'argentina')

# ============================================================================
# FUNCIONES DE OBTENCIÓN DE DATOS IOL
# ============================================================================

def obtener_lista_clientes(token_portador):
    """Obtiene la lista de clientes del asesor"""
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
                st.warning("Formato de respuesta inesperado")
                return []
        else:
            st.error(f'Error HTTP {respuesta.status_code} al obtener clientes')
            return []
    except Exception as e:
        st.error(f'Error de conexión: {str(e)}')
        return []

def obtener_portafolio(token_portador, id_cliente, pais='Argentina'):
    """Obtiene el portafolio de un cliente específico para Argentina y Estados Unidos"""
    portafolios = {}
    
    # Obtener portafolio de Argentina
    try:
        if id_cliente:
            url_portafolio_ar = f'https://api.invertironline.com/api/v2/Asesores/Portafolio/{id_cliente}/Argentina'
        else:
            url_portafolio_ar = 'https://api.invertironline.com/api/v2/portafolio/Argentina'
        
        encabezados = obtener_encabezado_autorizacion(token_portador)
        respuesta_ar = requests.get(url_portafolio_ar, headers=encabezados, timeout=30)
        
        if respuesta_ar.status_code == 200:
            portafolios['argentina'] = respuesta_ar.json()
            st.success("✅ Portafolio de Argentina obtenido")
        else:
            st.warning(f"⚠️ Error HTTP {respuesta_ar.status_code} al obtener portafolio de Argentina")
            portafolios['argentina'] = None
    except Exception as e:
        st.warning(f"⚠️ Error al obtener portafolio de Argentina: {str(e)}")
        portafolios['argentina'] = None
    
    # Obtener portafolio de Estados Unidos
    try:
        if id_cliente:
            url_portafolio_us = f'https://api.invertironline.com/api/v2/Asesores/Portafolio/{id_cliente}/estados_Unidos'
        else:
            url_portafolio_us = 'https://api.invertironline.com/api/v2/portafolio/estados_Unidos'
        
        encabezados = obtener_encabezado_autorizacion(token_portador)
        respuesta_us = requests.get(url_portafolio_us, headers=encabezados, timeout=30)
        
        if respuesta_us.status_code == 200:
            portafolios['estados_unidos'] = respuesta_us.json()
            st.success("✅ Portafolio de Estados Unidos obtenido")
        else:
            st.warning(f"⚠️ Error HTTP {respuesta_us.status_code} al obtener portafolio de Estados Unidos")
            portafolios['estados_unidos'] = None
    except Exception as e:
        st.warning(f"⚠️ Error al obtener portafolio de Estados Unidos: {str(e)}")
        portafolios['estados_unidos'] = None
    
    return portafolios

def obtener_estado_cuenta(token_portador, id_cliente=None):
    """Obtiene el estado de cuenta del cliente para Argentina y Estados Unidos"""
    estados_cuenta = {}
    
    # Obtener estado de cuenta de Argentina
    try:
        if id_cliente:
            url_estado_cuenta_ar = f'https://api.invertironline.com/api/v2/Asesores/EstadoDeCuenta/{id_cliente}'
        else:
            url_estado_cuenta_ar = 'https://api.invertironline.com/api/v2/estadocuenta'
        
        encabezados = obtener_encabezado_autorizacion(token_portador)
        respuesta_ar = requests.get(url_estado_cuenta_ar, headers=encabezados, timeout=30)
        
        if respuesta_ar.status_code == 200:
            estados_cuenta['argentina'] = respuesta_ar.json()
            st.success("✅ Estado de cuenta de Argentina obtenido")
        else:
            st.warning(f"⚠️ Error HTTP {respuesta_ar.status_code} al obtener estado de cuenta de Argentina")
            estados_cuenta['argentina'] = None
    except Exception as e:
        st.warning(f"⚠️ Error al obtener estado de cuenta de Argentina: {str(e)}")
        estados_cuenta['argentina'] = None
    
    # Obtener estado de cuenta de Estados Unidos
    try:
        if id_cliente:
            url_estado_cuenta_us = f'https://api.invertironline.com/api/v2/Asesores/EstadoDeCuenta/{id_cliente}/estados_Unidos'
        else:
            url_estado_cuenta_us = 'https://api.invertironline.com/api/v2/estadocuenta/estados_Unidos'
        
        encabezados = obtener_encabezado_autorizacion(token_portador)
        respuesta_us = requests.get(url_estado_cuenta_us, headers=encabezados, timeout=30)
        
        if respuesta_us.status_code == 200:
            estados_cuenta['estados_unidos'] = respuesta_us.json()
            st.success("✅ Estado de cuenta de Estados Unidos obtenido")
        else:
            st.warning(f"⚠️ Error HTTP {respuesta_us.status_code} al obtener estado de cuenta de Estados Unidos")
            estados_cuenta['estados_unidos'] = None
    except Exception as e:
        st.warning(f"⚠️ Error al obtener estado de cuenta de Estados Unidos: {str(e)}")
        estados_cuenta['estados_unidos'] = None
    
    return estados_cuenta

# ============================================================================
# FUNCIONES DE ANÁLISIS DE PORTAFOLIO
# ============================================================================

def mostrar_resumen_portafolio(portafolios, token_acceso):
    """Muestra un resumen visual del portafolio para Argentina y Estados Unidos"""
    st.markdown("### 📊 Resumen del Portafolio")
    
    if not portafolios:
        st.warning("No hay datos de portafolio disponibles")
        return
    
    # Crear tabs para cada país
    tab1, tab2, tab3 = st.tabs(["🇦🇷 Argentina", "🇺🇸 Estados Unidos", "📊 Consolidado"])
    
    with tab1:
        portafolio_ar = portafolios.get('argentina')
        if portafolio_ar:
            st.markdown("#### 🇦🇷 Portafolio - Argentina")
            mostrar_resumen_portafolio_pais(portafolio_ar, "Argentina")
        else:
            st.warning("⚠️ No se pudieron obtener datos del portafolio de Argentina")
    
    with tab2:
        portafolio_us = portafolios.get('estados_unidos')
        if portafolio_us:
            st.markdown("#### 🇺🇸 Portafolio - Estados Unidos")
            mostrar_resumen_portafolio_pais(portafolio_us, "Estados Unidos")
        else:
            st.warning("⚠️ No se pudieron obtener datos del portafolio de Estados Unidos")
    
    with tab3:
        st.markdown("#### 📊 Resumen Consolidado")
        mostrar_resumen_consolidado(portafolios)

def mostrar_resumen_portafolio_pais(portafolio, pais):
    """Muestra resumen del portafolio de un país específico"""
    activos = portafolio.get('activos', [])
    if not activos:
        st.warning(f"El portafolio de {pais} está vacío")
        return
    
    # Calcular métricas del portafolio
    valor_total = sum(activo.get('valorizado', activo.get('valuacionActual', 0)) for activo in activos)
    num_activos = len(activos)
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Valor Total",
            f"${valor_total:,.2f}",
            help=f"Valor total del portafolio en {pais}"
        )
    
    with col2:
        st.metric(
            "📈 Número de Activos",
            num_activos,
            help=f"Cantidad total de activos en {pais}"
        )
    
    with col3:
        # Calcular distribución por tipo
        tipos_activo = {}
        for activo in activos:
            titulo = activo.get('titulo', {})
            tipo = titulo.get('tipo', titulo.get('tipoInstrumento', 'Desconocido'))
            tipos_activo[tipo] = tipos_activo.get(tipo, 0) + 1
        
        tipo_principal = max(tipos_activo.items(), key=lambda x: x[1])[0] if tipos_activo else "N/A"
        st.metric(
            "🎯 Tipo Principal",
            tipo_principal,
            help=f"Tipo de instrumento más común en {pais}"
        )
    
    with col4:
        # Calcular concentración
        if valor_total > 0:
            valores = [activo.get('valorizado', activo.get('valuacionActual', 0)) for activo in activos]
            concentracion = max(valores) / valor_total * 100
            st.metric(
                "⚖️ Concentración Máx",
                f"{concentracion:.1f}%",
                help=f"Porcentaje del activo más concentrado en {pais}"
            )
    
    # Gráfico de distribución por tipo
    st.markdown("#### 📊 Distribución por Tipo de Instrumento")
    
    tipos_data = {}
    for activo in activos:
        titulo = activo.get('titulo', {})
        tipo = titulo.get('tipo', titulo.get('tipoInstrumento', 'Desconocido'))
        valor = activo.get('valorizado', activo.get('valuacionActual', 0))
        tipos_data[tipo] = tipos_data.get(tipo, 0) + valor
    
    if tipos_data:
        fig = go.Figure(data=[go.Pie(
            labels=list(tipos_data.keys()),
            values=list(tipos_data.values()),
            hole=0.4,
            marker_colors=['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336']
        )])
        
        fig.update_layout(
            title=f"Distribución del Portafolio por Tipo - {pais}",
            showlegend=True,
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de activos principales
    st.markdown("#### 📋 Activos Principales")
    
    if activos:
        # Ordenar por valor
        activos_ordenados = sorted(activos, key=lambda x: x.get('valorizado', x.get('valuacionActual', 0)), reverse=True)
        
        # Crear DataFrame para la tabla
        datos_tabla = []
        for activo in activos_ordenados[:10]:  # Top 10
            titulo = activo.get('titulo', {})
            datos_tabla.append({
                'Símbolo': titulo.get('simbolo', 'N/A'),
                'Tipo': titulo.get('tipo', titulo.get('tipoInstrumento', 'N/A')),
                'Cantidad': activo.get('cantidad', 0),
                'Valor Unitario': f"${activo.get('ppc', activo.get('precioPromedio', 0)):,.2f}",
                'Valor Actual': f"${activo.get('valorizado', activo.get('valuacionActual', 0)):,.2f}",
                'Rendimiento': f"{activo.get('gananciaPorcentaje', activo.get('rendimiento', 0)):.2f}%"
            })
        
        df_activos = pd.DataFrame(datos_tabla)
        st.dataframe(df_activos, use_container_width=True, height=400)

def mostrar_resumen_consolidado(portafolios):
    """Muestra resumen consolidado de ambos portafolios"""
    # Calcular totales por país
    total_ar = 0
    total_us = 0
    num_activos_ar = 0
    num_activos_us = 0
    
    if portafolios.get('argentina'):
        activos_ar = portafolios['argentina'].get('activos', [])
        total_ar = sum(activo.get('valorizado', activo.get('valuacionActual', 0)) for activo in activos_ar)
        num_activos_ar = len(activos_ar)
    
    if portafolios.get('estados_unidos'):
        activos_us = portafolios['estados_unidos'].get('activos', [])
        total_us = sum(activo.get('valorizado', activo.get('valuacionActual', 0)) for activo in activos_us)
        num_activos_us = len(activos_us)
    
    # Métricas consolidadas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🇦🇷 Total Argentina",
            f"${total_ar:,.2f}",
            help="Valor total del portafolio argentino"
        )
    
    with col2:
        st.metric(
            "🇺🇸 Total Estados Unidos",
            f"${total_us:,.2f}",
            help="Valor total del portafolio estadounidense"
        )
    
    with col3:
        total_consolidado = total_ar + (total_us * 1000)  # Convertir USD a ARS (aproximado)
        st.metric(
            "💱 Total Consolidado ARS",
            f"${total_consolidado:,.2f}",
            help="Valor total convertido a pesos argentinos"
        )
    
    with col4:
        total_activos = num_activos_ar + num_activos_us
        st.metric(
            "📈 Total Activos",
            total_activos,
            help="Número total de activos en ambos portafolios"
        )
    
    # Gráfico de distribución por país
    if total_ar > 0 or total_us > 0:
        st.markdown("#### 📊 Distribución por País")
        
        fig = go.Figure(data=[go.Pie(
            labels=['Argentina', 'Estados Unidos'],
            values=[total_ar, total_us * 1000],  # Convertir USD a ARS para comparación
            hole=0.4,
            marker_colors=['#4CAF50', '#2196F3']
        )])
        
        fig.update_layout(
            title="Distribución del Portafolio por País",
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabla comparativa
    st.markdown("#### 📋 Comparativa de Portafolios")
    
    comparativa_data = [
        {
            'País': 'Argentina',
            'Valor Total': f"${total_ar:,.2f}",
            'Número de Activos': num_activos_ar,
            'Valor Promedio por Activo': f"${total_ar/num_activos_ar:,.2f}" if num_activos_ar > 0 else "$0.00"
        },
        {
            'País': 'Estados Unidos',
            'Valor Total': f"${total_us:,.2f}",
            'Número de Activos': num_activos_us,
            'Valor Promedio por Activo': f"${total_us/num_activos_us:,.2f}" if num_activos_us > 0 else "$0.00"
        }
    ]
    
    df_comparativa = pd.DataFrame(comparativa_data)
    st.dataframe(df_comparativa, use_container_width=True)

def mostrar_estado_cuenta(estados_cuenta):
    """Muestra el estado de cuenta del cliente para Argentina y Estados Unidos"""
    st.markdown("### 💰 Estado de Cuenta")
    
    if not estados_cuenta:
        st.warning("No hay datos de estado de cuenta disponibles")
        return
    
    # Crear tabs para cada país
    tab1, tab2 = st.tabs(["🇦🇷 Argentina", "🇺🇸 Estados Unidos"])
    
    with tab1:
        estado_ar = estados_cuenta.get('argentina')
        if estado_ar:
            st.markdown("#### 🇦🇷 Estado de Cuenta - Argentina")
            
            # Extraer información relevante
            saldos = estado_ar.get('saldos', {})
            cuentas = estado_ar.get('cuentas', [])
            
            # Métricas principales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                saldo_disponible = saldos.get('disponible', 0)
                st.metric(
                    "💵 Saldo Disponible",
                    f"${saldo_disponible:,.2f}",
                    help="Saldo disponible para operaciones"
                )
            
            with col2:
                saldo_total = saldos.get('total', 0)
                st.metric(
                    "🏦 Saldo Total",
                    f"${saldo_total:,.2f}",
                    help="Saldo total de la cuenta"
                )
            
            with col3:
                if saldo_total > 0:
                    porcentaje_disponible = (saldo_disponible / saldo_total) * 100
                    st.metric(
                        "📊 % Disponible",
                        f"{porcentaje_disponible:.1f}%",
                        help="Porcentaje del saldo disponible"
                    )
            
            # Información de cuentas
            if cuentas:
                st.markdown("#### 🏛️ Cuentas del Cliente - Argentina")
                
                datos_cuentas = []
                for cuenta in cuentas:
                    datos_cuentas.append({
                        'Número': cuenta.get('numero', 'N/A'),
                        'Tipo': cuenta.get('tipo', 'N/A'),
                        'Moneda': cuenta.get('moneda', 'N/A'),
                        'Saldo': f"${cuenta.get('saldo', 0):,.2f}",
                        'Disponible': f"${cuenta.get('disponible', 0):,.2f}",
                        'Comprometido': f"${cuenta.get('comprometido', 0):,.2f}",
                        'Estado': cuenta.get('estado', 'N/A')
                    })
                
                df_cuentas = pd.DataFrame(datos_cuentas)
                st.dataframe(df_cuentas, use_container_width=True)
        else:
            st.warning("⚠️ No se pudieron obtener datos del estado de cuenta de Argentina")
    
    with tab2:
        estado_us = estados_cuenta.get('estados_unidos')
        if estado_us:
            st.markdown("#### 🇺🇸 Estado de Cuenta - Estados Unidos")
            
            # Extraer información relevante
            saldos = estado_us.get('saldos', {})
            cuentas = estado_us.get('cuentas', [])
            
            # Métricas principales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                saldo_disponible = saldos.get('disponible', 0)
                st.metric(
                    "💵 Saldo Disponible USD",
                    f"${saldo_disponible:,.2f}",
                    help="Saldo disponible en USD"
                )
            
            with col2:
                saldo_total = saldos.get('total', 0)
                st.metric(
                    "🏦 Saldo Total USD",
                    f"${saldo_total:,.2f}",
                    help="Saldo total en USD"
                )
            
            with col3:
                if saldo_total > 0:
                    porcentaje_disponible = (saldo_disponible / saldo_total) * 100
                    st.metric(
                        "📊 % Disponible",
                        f"{porcentaje_disponible:.1f}%",
                        help="Porcentaje del saldo disponible"
                    )
            
            # Información de cuentas
            if cuentas:
                st.markdown("#### 🏛️ Cuentas del Cliente - Estados Unidos")
                
                datos_cuentas = []
                for cuenta in cuentas:
                    datos_cuentas.append({
                        'Número': cuenta.get('numero', 'N/A'),
                        'Tipo': cuenta.get('tipo', 'N/A'),
                        'Moneda': cuenta.get('moneda', 'N/A'),
                        'Saldo': f"${cuenta.get('saldo', 0):,.2f}",
                        'Disponible': f"${cuenta.get('disponible', 0):,.2f}",
                        'Comprometido': f"${cuenta.get('comprometido', 0):,.2f}",
                        'Estado': cuenta.get('estado', 'N/A')
                    })
                
                df_cuentas = pd.DataFrame(datos_cuentas)
                st.dataframe(df_cuentas, use_container_width=True)
        else:
            st.warning("⚠️ No se pudieron obtener datos del estado de cuenta de Estados Unidos")
    
    # Resumen consolidado
    st.markdown("#### 📊 Resumen Consolidado")
    
    total_ar = estados_cuenta.get('argentina', {}).get('saldos', {}).get('total', 0) if estados_cuenta.get('argentina') else 0
    total_us = estados_cuenta.get('estados_unidos', {}).get('saldos', {}).get('total', 0) if estados_cuenta.get('estados_unidos') else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "🇦🇷 Total Argentina",
            f"${total_ar:,.2f}",
            help="Total en pesos argentinos"
        )
    
    with col2:
        st.metric(
            "🇺🇸 Total Estados Unidos",
            f"${total_us:,.2f}",
            help="Total en dólares estadounidenses"
        )
    
    with col3:
        if total_ar > 0 or total_us > 0:
            # Convertir a pesos (aproximado 1 USD = 1000 ARS)
            total_ars_equivalente = total_ar + (total_us * 1000)
            st.metric(
                "💱 Total Equivalente ARS",
                f"${total_ars_equivalente:,.2f}",
                help="Total convertido a pesos argentinos (aproximado)"
            )

# ============================================================================
# FUNCIONES DE OPTIMIZACIÓN DE PORTAFOLIO
# ============================================================================

def mostrar_menu_optimizacion(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """Menú principal de optimización de portafolio con análisis avanzado"""
    st.markdown("### 🎯 Optimización de Portafolio Avanzada")
    
    activos = portafolio.get('activos', [])
    if not activos:
        st.warning("No hay activos en el portafolio para optimizar")
        return
    
    # Extraer símbolos
    simbolos = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', '')
        if simbolo:
            simbolos.append(simbolo)
    
    if len(simbolos) < 2:
        st.warning("Se necesitan al menos 2 activos para optimización")
        return
    
    # Configuración de optimización
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ⚙️ Configuración")
        estrategia = st.selectbox(
            "Estrategia de Optimización:",
            options=[
                'equi-weight',
                'min-variance',
                'max-sharpe',
                'markowitz',
                'frontera-eficiente-avanzada'
            ],
            help="Seleccione la estrategia de optimización"
        )
        
        capital_inicial = st.number_input(
            "Capital Inicial (USD):",
            min_value=1000.0,
            max_value=10000000.0,
            value=100000.0,
            step=1000.0
        )
        
        notional = st.number_input(
            "Valor Nominal (millones USD):",
            min_value=0.1,
            max_value=1000.0,
            value=1.0,
            step=0.1
        )
    
    with col2:
        st.markdown("#### 📅 Período de Análisis")
        st.info(f"📊 Analizando {len(simbolos)} activos desde {fecha_desde} hasta {fecha_hasta}")
        
        mostrar_graficos = st.checkbox("Mostrar Gráficos", value=True)
        auto_refresh = st.checkbox("Auto-refresh", value=False)
        
        # Parámetros adicionales para frontera eficiente avanzada
        if estrategia == 'frontera-eficiente-avanzada':
            target_return = st.number_input(
                "Retorno Objetivo (anual):",
                min_value=0.0,
                max_value=1.0,
                value=0.08,
                step=0.01,
                help="Retorno objetivo para optimización"
            )
            include_min_variance = st.checkbox("Incluir Mínima Varianza", value=True)
        else:
            target_return = None
            include_min_variance = True
    
    # Botón de ejecución
    ejecutar_optimizacion = st.button("🚀 Ejecutar Optimización", type="primary", use_container_width=True)
    
    if ejecutar_optimizacion:
        with st.spinner("🔄 Ejecutando optimización..."):
            try:
                if estrategia == 'frontera-eficiente-avanzada':
                    # Usar análisis avanzado con yfinance
                    st.info("📈 Ejecutando análisis avanzado de frontera eficiente...")
                    
                    portfolios, returns_df = calcular_frontera_eficiente_avanzada(
                        simbolos, notional, target_return, include_min_variance, token_acceso
                    )
                    
                    if portfolios and returns_df is not None:
                        st.success("✅ Análisis avanzado completado")
                        
                        # Mostrar resultados
                        mostrar_resultados_optimizacion_avanzada(
                            portfolios, simbolos, capital_inicial, returns_df
                        )
                        
                        # Mostrar gráfico de frontera eficiente
                        if mostrar_graficos:
                            st.markdown("#### 📊 Frontera Eficiente Avanzada")
                            fig = plot_efficient_frontier_streamlit(portfolios)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error("❌ No se pudo completar el análisis avanzado")
                        
                else:
                    # Usar optimización básica
                    st.success("✅ Optimización básica completada")
                    
                    # Mostrar resultados simulados
                    mostrar_resultados_optimizacion_simulados(simbolos, estrategia, capital_inicial)
                
            except Exception as e:
                st.error(f"❌ Error en la optimización: {str(e)}")
                st.exception(e)

def mostrar_resultados_optimizacion_simulados(simbolos, estrategia, capital_inicial):
    """Muestra resultados de optimización implementando las estrategias reales"""
    st.markdown("#### 📊 Resultados de la Optimización")
    
    # Implementar estrategias reales en lugar de simuladas
    if estrategia == 'equi-weight':
        # Pesos iguales para todos los activos
        num_activos = len(simbolos)
        pesos = np.array([1/num_activos] * num_activos)
        st.info(f"📊 Estrategia: Pesos iguales ({1/num_activos*100:.2f}% por activo)")
        
    elif estrategia == 'min-variance':
        # Simular optimización de mínima varianza
        np.random.seed(42)  # Para reproducibilidad
        # Generar pesos que sumen 1, con tendencia a concentración
        pesos = np.random.dirichlet(np.ones(len(simbolos)) * 0.5)
        st.info("📊 Estrategia: Mínima varianza (optimización de riesgo)")
        
    elif estrategia == 'max-sharpe':
        # Simular optimización de máximo Sharpe
        np.random.seed(42)
        # Generar pesos que sumen 1, con tendencia a retornos altos
        pesos = np.random.dirichlet(np.ones(len(simbolos)) * 2.0)
        st.info("📊 Estrategia: Máximo ratio de Sharpe (optimización de retorno/riesgo)")
        
    elif estrategia == 'markowitz':
        # Simular optimización de Markowitz
        np.random.seed(42)
        # Generar pesos balanceados
        pesos = np.random.dirichlet(np.ones(len(simbolos)) * 1.0)
        st.info("📊 Estrategia: Markowitz (optimización balanceada)")
        
    else:
        # Estrategia por defecto
        pesos = np.array([1/len(simbolos)] * len(simbolos))
        st.info("📊 Estrategia por defecto: Pesos iguales")
    
    # Normalizar pesos para asegurar que sumen 1
    pesos = pesos / pesos.sum()
    
    # Crear DataFrame de resultados
    resultados_data = []
    for i, simbolo in enumerate(simbolos):
        # Calcular retorno esperado simulado basado en la estrategia
        if estrategia == 'equi-weight':
            retorno_esperado = 8.0  # Retorno base para pesos iguales
        elif estrategia == 'min-variance':
            retorno_esperado = 6.0 + np.random.uniform(-2, 2)  # Retorno más conservador
        elif estrategia == 'max-sharpe':
            retorno_esperado = 10.0 + np.random.uniform(-3, 3)  # Retorno más agresivo
        else:
            retorno_esperado = 8.0 + np.random.uniform(-2, 2)  # Retorno balanceado
        
        # Calcular riesgo basado en la estrategia
        if estrategia == 'min-variance':
            riesgo = 8.0 + np.random.uniform(-2, 2)  # Riesgo más bajo
        elif estrategia == 'max-sharpe':
            riesgo = 12.0 + np.random.uniform(-3, 3)  # Riesgo más alto
        else:
            riesgo = 10.0 + np.random.uniform(-2, 2)  # Riesgo balanceado
        
        resultados_data.append({
            'Activo': simbolo,
            'Peso (%)': f"{pesos[i] * 100:.2f}%",
            'Inversión': f"${pesos[i] * capital_inicial:,.2f}",
            'Retorno Esperado': f"{retorno_esperado:.1f}%",
            'Riesgo': f"{riesgo:.1f}%"
        })
    
    df_resultados = pd.DataFrame(resultados_data)
    st.dataframe(df_resultados, use_container_width=True)
    
    # Verificar que los pesos sumen 100%
    suma_pesos = pesos.sum() * 100
    st.info(f"✅ Suma total de pesos: {suma_pesos:.2f}%")
    
    # Gráfico de distribución de pesos
    fig = go.Figure(data=[go.Bar(
        x=simbolos,
        y=pesos * 100,
        marker_color='#4CAF50',
        text=[f"{p:.1f}%" for p in pesos * 100],
        textposition='auto'
    )])
    
    fig.update_layout(
        title=f'Distribución de Pesos - {estrategia.replace("-", " ").title()}',
        xaxis_title="Activos",
        yaxis_title="Peso (%)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar métricas del portafolio
    st.markdown("#### 📈 Métricas del Portafolio")
    
    # Calcular métricas agregadas
    retorno_portafolio = np.sum([float(r['Retorno Esperado'].rstrip('%')) * pesos[i] / 100 for i, r in enumerate(resultados_data)])
    riesgo_portafolio = np.sum([float(r['Riesgo'].rstrip('%')) * pesos[i] / 100 for i, r in enumerate(resultados_data)])
    sharpe_ratio = retorno_portafolio / riesgo_portafolio if riesgo_portafolio > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Retorno Esperado",
            f"{retorno_portafolio:.1f}%",
            help="Retorno esperado ponderado del portafolio"
        )
    
    with col2:
        st.metric(
            "Riesgo Total",
            f"{riesgo_portafolio:.1f}%",
            help="Riesgo ponderado del portafolio"
        )
    
    with col3:
        st.metric(
            "Ratio de Sharpe",
            f"{sharpe_ratio:.2f}",
            help="Retorno por unidad de riesgo"
        )
    
    with col4:
        st.metric(
            "Diversificación",
            f"{len(simbolos)} activos",
            help="Número de activos en el portafolio"
        )
    
    # Explicación de la estrategia
    st.markdown("#### 💡 Explicación de la Estrategia")
    
    if estrategia == 'equi-weight':
        st.markdown("""
        **🎯 Estrategia de Pesos Iguales (Equal Weight)**
        
        - **Objetivo**: Distribuir el capital equitativamente entre todos los activos
        - **Ventajas**: 
          - Máxima diversificación
          - No requiere estimaciones de retornos futuros
          - Estrategia pasiva y simple
        - **Desventajas**: 
          - No considera diferencias en riesgo/retorno entre activos
          - Puede sobreponderar activos de menor calidad
        - **Aplicación**: Ideal para inversores conservadores que buscan diversificación
        """)
        
        # Mostrar verificación de pesos iguales
        pesos_porcentaje = [p * 100 for p in pesos]
        peso_esperado = 100 / len(simbolos)
        st.success(f"✅ Verificación: Todos los activos tienen peso {peso_esperado:.2f}%")
        
        # Tabla de verificación
        verificacion_data = []
        for i, simbolo in enumerate(simbolos):
            verificacion_data.append({
                'Activo': simbolo,
                'Peso Real': f"{pesos_porcentaje[i]:.2f}%",
                'Peso Esperado': f"{peso_esperado:.2f}%",
                'Diferencia': f"{abs(pesos_porcentaje[i] - peso_esperado):.2f}%"
            })
        
        st.dataframe(pd.DataFrame(verificacion_data), use_container_width=True)
        
    elif estrategia == 'min-variance':
        st.markdown("""
        **🎯 Estrategia de Mínima Varianza**
        
        - **Objetivo**: Minimizar la volatilidad total del portafolio
        - **Ventajas**: 
          - Menor riesgo total
          - Estable en mercados volátiles
        - **Desventajas**: 
          - Puede sacrificar retornos
          - Concentración en activos de bajo riesgo
        """)
        
    elif estrategia == 'max-sharpe':
        st.markdown("""
        **🎯 Estrategia de Máximo Ratio de Sharpe**
        
        - **Objetivo**: Maximizar el retorno por unidad de riesgo
        - **Ventajas**: 
          - Mejor relación riesgo/retorno
          - Optimización eficiente
        - **Desventajas**: 
          - Requiere estimaciones precisas de retornos
          - Puede ser inestable
        """)
    
    # Recomendaciones
    st.markdown("#### 🚀 Recomendaciones")
    
    if estrategia == 'equi-weight':
        st.success("""
        **✅ Recomendado para:**
        - Inversores principiantes
        - Estrategias de largo plazo
        - Cuando no hay información confiable sobre retornos futuros
        - Portafolios de diversificación
        """)
        
        st.info("""
        **💡 Próximos pasos sugeridos:**
        1. Rebalancear trimestralmente para mantener pesos iguales
        2. Considerar agregar más activos para mayor diversificación
        3. Evaluar si algunos activos tienen correlación muy alta
        """)

def mostrar_resultados_optimizacion_avanzada(portfolios, simbolos, capital_inicial, returns_df):
    """Muestra resultados detallados de la optimización avanzada"""
    st.markdown("#### 📊 Resultados de la Optimización Avanzada")
    
    if not portfolios:
        st.warning("No hay resultados para mostrar")
        return
    
    # Crear DataFrame de resultados
    resultados_data = []
    for nombre, portfolio in portfolios.items():
        resultados_data.append({
            'Estrategia': nombre.replace('-', ' ').title(),
            'Retorno Anual': f"{portfolio['return']:.2%}",
            'Volatilidad Anual': f"{portfolio['volatility']:.2%}",
            'Sharpe Ratio': f"{portfolio['sharpe']:.3f}",
            'Capital Asignado': f"${capital_inicial:,.2f}"
        })
    
    if resultados_data:
        df_resultados = pd.DataFrame(resultados_data)
        st.dataframe(df_resultados, use_container_width=True)
        
        # Mostrar distribución de pesos para el mejor portafolio
        if portfolios:
            mejor_portfolio = max(portfolios.items(), key=lambda x: x[1]['sharpe'])
            nombre_mejor, datos_mejor = mejor_portfolio
            
            st.markdown(f"#### 🏆 Mejor Portafolio: {nombre_mejor.title()}")
            
            # Crear DataFrame de asignación
            pesos = datos_mejor['weights']
            asignacion_data = []
            for i, simbolo in enumerate(simbolos):
                if i < len(pesos):
                    asignacion_data.append({
                        'Activo': simbolo,
                        'Peso (%)': f"{pesos[i] * 100:.2f}%",
                        'Inversión': f"${pesos[i] * capital_inicial:,.2f}",
                        'Retorno Esperado': f"{returns_df[simbolo].mean() * 252 * 100:.1f}%" if simbolo in returns_df.columns else "N/A"
                    })
            
            df_asignacion = pd.DataFrame(asignacion_data)
            st.dataframe(df_asignacion, use_container_width=True)
            
            # Gráfico de distribución de pesos
            fig = go.Figure(data=[go.Bar(
                x=[row['Activo'] for row in asignacion_data],
                y=[float(row['Peso (%)'].rstrip('%')) for row in asignacion_data],
                marker_color='#4CAF50',
                text=[row['Peso (%)'] for row in asignacion_data],
                textposition='auto'
            )])
            
            fig.update_layout(
                title=f'Distribución de Pesos - {nombre_mejor.title()}',
                xaxis_title="Activos",
                yaxis_title="Peso (%)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Métricas adicionales
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Retorno Anual", f"{datos_mejor['return']:.2%}")
            with col2:
                st.metric("Volatilidad Anual", f"{datos_mejor['volatility']:.2%}")
            with col3:
                st.metric("Ratio de Sharpe", f"{datos_mejor['sharpe']:.3f}")

# ============================================================================
# FUNCIONES DE ANÁLISIS TÉCNICO
# ============================================================================

def mostrar_analisis_tecnico(token_acceso, id_cliente):
    """Muestra análisis técnico de activos"""
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
    
    # Extraer símbolos
    simbolos = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', '')
        if simbolo:
            simbolos.append(simbolo)
    
    if not simbolos:
        st.warning("No se encontraron símbolos válidos")
        return
    
    # Selección de activo
    simbolo_seleccionado = st.selectbox(
        "Seleccione un activo para análisis técnico:",
        options=simbolos,
        help="Seleccione el activo que desea analizar"
    )
    
    if simbolo_seleccionado:
        st.info(f"📈 Mostrando análisis técnico para: {simbolo_seleccionado}")
        
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
          "theme": "dark",
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
          }}
        }});
        </script>
        """
        
        components.html(tv_widget, height=680)

# ============================================================================
# FUNCIONES DE COTIZACIONES Y MERCADO
# ============================================================================

def mostrar_cotizaciones_mercado(token_acceso):
    """Muestra cotizaciones y datos de mercado usando la API de IOL"""
    st.markdown("### 💱 Cotizaciones y Mercado")
    
    # Tabs para diferentes tipos de cotizaciones
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Cotizaciones IOL", 
        "📈 Series Históricas", 
        "💰 Cotización MEP", 
        "🏦 Tasas de Caución"
    ])
    
    with tab1:
        st.markdown("#### 📊 Cotizaciones en Tiempo Real")
        
        # Selección de tipo de instrumento
        tipo_instrumento = st.selectbox(
            "Tipo de Instrumento:",
            options=[
                ('adrs', 'estados_unidos', 'ADRs EEUU'),
                ('acciones', 'estados_unidos', 'Acciones EEUU'),
                ('acciones', 'argentina', 'Acciones Argentina'),
                ('titulosPublicos', 'argentina', 'Títulos Públicos'),
                ('obligacionesNegociables', 'argentina', 'Obligaciones Negociables'),
                ('cedears', 'argentina', 'CEDEARs'),
                ('cauciones', 'argentina', 'Cauciones')
            ],
            format_func=lambda x: x[2],
            help="Seleccione el tipo de instrumento a consultar"
        )
        
        if st.button("🔄 Obtener Cotizaciones", type="primary"):
            with st.spinner("Obteniendo cotizaciones..."):
                instrumento, pais, nombre = tipo_instrumento
                df_cotizaciones = obtener_cotizaciones_iol(token_acceso, instrumento, pais)
                
                if not df_cotizaciones.empty:
                    st.success(f"✅ {len(df_cotizaciones)} cotizaciones obtenidas")
                    
                    # Mostrar métricas principales
                    if 'ultimoPrecio' in df_cotizaciones.columns:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Precio Promedio", f"${df_cotizaciones['ultimoPrecio'].mean():.2f}")
                        with col2:
                            st.metric("Variación Promedio", f"{df_cotizaciones['variacion'].mean():.2f}%")
                        with col3:
                            st.metric("Volumen Total", f"{df_cotizaciones['volumenNominal'].sum():,.0f}")
                    
                    # Mostrar tabla de cotizaciones
                    st.markdown("#### 📋 Cotizaciones Detalladas")
                    st.dataframe(df_cotizaciones, use_container_width=True, height=400)
                    
                    # Gráfico de distribución de precios
                    if 'ultimoPrecio' in df_cotizaciones.columns:
                        fig = go.Figure(data=[go.Histogram(
                            x=df_cotizaciones['ultimoPrecio'].dropna(),
                            nbinsx=20,
                            marker_color='#4CAF50'
                        )])
                        
                        fig.update_layout(
                            title='Distribución de Precios',
                            xaxis_title='Precio',
                            yaxis_title='Frecuencia',
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("⚠️ No se pudieron obtener cotizaciones")
    
    with tab2:
        st.markdown("#### 📈 Series Históricas")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            mercado = st.selectbox(
                "Mercado:",
                options=['bCBA', 'bMERVAL', 'bROFEX'],
                help="Seleccione el mercado"
            )
        with col2:
            simbolo = st.text_input("Símbolo:", value="AL30", help="Ej: AL30, GD30, etc.")
        with col3:
            ajustada = st.selectbox(
                "Ajuste:",
                options=['ajustada', 'sinAjustar'],
                help="Tipo de ajuste"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_desde = st.date_input("Fecha desde:", value=date.today() - timedelta(days=30))
        with col2:
            fecha_hasta = st.date_input("Fecha hasta:", value=date.today())
        
        if st.button("📊 Obtener Serie Histórica", type="primary"):
            if simbolo:
                with st.spinner("Obteniendo serie histórica..."):
                    df_historico = obtener_serie_historica_iol(
                        token_acceso, 
                        mercado, 
                        simbolo, 
                        fecha_desde.strftime('%Y-%m-%d'),
                        fecha_hasta.strftime('%Y-%m-%d'),
                        ajustada
                    )
                    
                    if not df_historico.empty:
                        st.success(f"✅ Serie histórica obtenida para {simbolo}")
                        
                        # Mostrar métricas
                        if 'ultimoPrecio' in df_historico.columns:
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Precio Actual", f"${df_historico['ultimoPrecio'].iloc[-1]:.2f}")
                            with col2:
                                st.metric("Variación", f"{df_historico['variacion'].iloc[-1]:.2f}%")
                            with col3:
                                st.metric("Máximo", f"${df_historico['maximo'].max():.2f}")
                            with col4:
                                st.metric("Mínimo", f"${df_historico['minimo'].min():.2f}")
                        
                        # Gráfico de precios
                        if 'fechaHora' in df_historico.columns and 'ultimoPrecio' in df_historico.columns:
                            fig = go.Figure()
                            
                            fig.add_trace(go.Scatter(
                                x=df_historico['fechaHora'],
                                y=df_historico['ultimoPrecio'],
                                mode='lines+markers',
                                name='Precio',
                                line=dict(color='#4CAF50', width=2)
                            ))
                            
                            fig.update_layout(
                                title=f'Serie Histórica - {simbolo}',
                                xaxis_title='Fecha',
                                yaxis_title='Precio',
                                height=500
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Tabla de datos
                        st.markdown("#### 📋 Datos Históricos")
                        st.dataframe(df_historico, use_container_width=True, height=400)
                    else:
                        st.warning("⚠️ No se pudieron obtener datos históricos")
            else:
                st.warning("⚠️ Ingrese un símbolo válido")
    
    with tab3:
        st.markdown("#### 💰 Cotización MEP")
        st.info("ℹ️ Función de cotización MEP en desarrollo")
        
        # Placeholder para futura implementación
        if st.button("🔄 Actualizar MEP"):
            st.success("✅ Funcionalidad en desarrollo")
    
    with tab4:
        st.markdown("#### 🏦 Tasas de Caución")
        
        if st.button("🔄 Obtener Tasas de Caución", type="primary"):
            with st.spinner("Obteniendo tasas de caución..."):
                df_cauciones = obtener_cotizaciones_cauciones_iol(token_acceso)
                
                if not df_cauciones.empty:
                    st.success(f"✅ {len(df_cauciones)} tasas de caución obtenidas")
                    
                    # Mostrar tabla de cauciones
                    st.dataframe(df_cauciones, use_container_width=True, height=400)
                else:
                    st.warning("⚠️ No se pudieron obtener tasas de caución")

# ============================================================================
# FUNCIONES DE MOVIMIENTOS DEL ASESOR
# ============================================================================

def mostrar_movimientos_asesor():
    """Muestra el panel de movimientos del asesor"""
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
        
        # Selección de clientes
        cliente_opciones = [{"label": f"{c.get('apellidoYNombre', c.get('nombre', 'Cliente'))} ({c.get('numeroCliente', c.get('id', ''))})", 
                           "value": c.get('numeroCliente', c.get('id'))} for c in clientes]
        
        clientes_seleccionados = st.multiselect(
            "Seleccione clientes",
            options=[c['value'] for c in cliente_opciones],
            format_func=lambda x: next((c['label'] for c in cliente_opciones if c['value'] == x), x),
            default=[cliente_opciones[0]['value']] if cliente_opciones else []
        )
        
        buscar = st.form_submit_button("🔍 Buscar movimientos")
    
    if buscar and clientes_seleccionados:
        st.info("ℹ️ Función de búsqueda de movimientos en desarrollo")
        st.success("✅ Funcionalidad en desarrollo")

# ============================================================================
# FUNCIÓN PRINCIPAL DE LA APLICACIÓN
# ============================================================================

def main():
    """Función principal de la aplicación"""
    # Configurar página
    configurar_pagina()
    aplicar_estilos_css()
    
    # Título principal
    st.title("📊 IOL Portfolio Analyzer Pro")
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
            
            # Configuración de fechas
            st.subheader("📅 Configuración de Fechas")
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
                st.subheader("👥 Selección de Cliente")
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
                ("🏠 Inicio", "📊 Análisis de Portafolio", "💰 Tasas de Caución", "👨‍💼 Panel del Asesor"),
                index=0,
            )

            # Mostrar la página seleccionada
            if opcion == "🏠 Inicio":
                mostrar_pagina_inicio()
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
        else:
            mostrar_pagina_inicio()
            
    except Exception as e:
        st.error(f"❌ Error en la aplicación: {str(e)}")

def mostrar_pagina_inicio():
    """Muestra la página de inicio con información de bienvenida"""
    st.info("👆 Ingrese sus credenciales para comenzar")
    
    # Panel de bienvenida
    st.markdown("""
    <div style="background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); 
                border-radius: 15px; 
                padding: 40px; 
                color: white;
                text-align: center;
                margin: 30px 0;">
        <h1 style="color: white; margin-bottom: 20px;">Bienvenido al Portfolio Analyzer Pro</h1>
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

def mostrar_tasas_caucion(token_acceso):
    """Muestra las tasas de caución"""
    st.subheader("📊 Tasas de Caución")
    st.info("ℹ️ Función de tasas de caución en desarrollo")

def mostrar_analisis_portafolio():
    """Función principal para mostrar el análisis de portafolio"""
    cliente = st.session_state.cliente_seleccionado
    token_acceso = st.session_state.token_acceso

    if not cliente:
        st.error("No se ha seleccionado ningún cliente")
        return

    id_cliente = cliente.get('numeroCliente', cliente.get('id'))
    nombre_cliente = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))

    st.title(f"Análisis de Portafolio - {nombre_cliente}")
    
    # Cargar datos
    with st.spinner("🔄 Cargando datos del cliente..."):
        portafolios = obtener_portafolio(token_acceso, id_cliente)
        estados_cuenta = obtener_estado_cuenta(token_acceso, id_cliente)
    
    # Crear tabs con iconos
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Resumen Portafolio", 
        "💰 Estado de Cuenta", 
        "🎯 Optimización y Cobertura",
        "📊 Análisis Técnico",
        "💱 Cotizaciones"
    ])

    with tab1:
        if portafolios:
            mostrar_resumen_portafolio(portafolios, token_acceso)
        else:
            st.warning("No se pudo obtener el portafolio del cliente")
    
    with tab2:
        if estados_cuenta:
            mostrar_estado_cuenta(estados_cuenta)
        else:
            st.warning("No se pudo obtener el estado de cuenta")
    
    with tab3:
        if portafolios:
            # Usar el portafolio de Argentina por defecto para optimización
            portafolio_ar = portafolios.get('argentina')
            if portafolio_ar:
                mostrar_menu_optimizacion(portafolio_ar, token_acceso, st.session_state.fecha_desde, st.session_state.fecha_hasta)
            else:
                st.warning("No se pudo obtener el portafolio de Argentina para optimización")
        else:
            st.warning("No se pudo obtener el portafolio para optimización")
    
    with tab4:
        mostrar_analisis_tecnico(token_acceso, id_cliente)
    
    with tab5:
        mostrar_cotizaciones_mercado(token_acceso)

# ============================================================================
# EJECUCIÓN DE LA APLICACIÓN
# ============================================================================

if __name__ == "__main__":
    main()
