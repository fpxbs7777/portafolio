"""More actions
Panel de Opciones - Calcula precios de opciones del mercado argentino usando Black-Scholes y el modelo Binomial.
"""

import sys, math, requests
import pandas as pd, numpy as np
from datetime import datetime, date, timedelta
from scipy.stats import norm
import yfinance as yf
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import matplotlib.table as table
from adjustText import adjust_text
import pandas_market_calendars as mcal
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
import json
import streamlit.components.v1 as components

# Clase para simulación de movimiento browniano geométrico
class MonteCarloGBM:
    def __init__(self, S0, mu, sigma, T, n_steps, n_simulations, historical_returns=None):
        """
        Geometric Brownian Motion for Monte Carlo simulation
        
        Parameters:
        S0: Initial stock price
        mu: Expected return (drift)
        sigma: Volatility
        T: Time horizon in years
        n_steps: Number of time steps
        n_simulations: Number of simulations
        historical_returns: Optional array of historical returns (daily). 
                           If provided, will use bootstrapping instead of normal distribution.
        """
        self.S0 = S0
        self.mu = mu
        self.sigma = sigma
        self.T = T
        self.n_steps = n_steps
        self.n_simulations = n_simulations
        self.historical_returns = historical_returns

    def simulate(self):
        """Run Monte Carlo simulation using GBM"""
        dt = self.T/self.n_steps

        # Initialize price matrix
        S = np.zeros((self.n_steps + 1, self.n_simulations))
        S[0] = self.S0

        if self.historical_returns is not None:
            # Use empirical distribution (bootstrapping)
            for t in range(1, self.n_steps + 1):
                # Sample daily returns from historical data
                returns = np.random.choice(
                    self.historical_returns, 
                    size=self.n_simulations,
                    replace=True
                )
                S[t] = S[t-1] * (1 + returns)
        else:
            # Use standard GBM with normal distribution
            # Brownian motion
            dW = np.random.normal(0, np.sqrt(dt), (self.n_steps, self.n_simulations))

            for t in range(1, self.n_steps + 1):
                S[t] = S[t-1] * np.exp((self.mu - 0.5 * self.sigma**2) * dt + 
                                      self.sigma * dW[t-1])

        return S

    def plot_simulations(self, S):
        """Plot simulation paths"""
        plt.figure(figsize=(10,6))
        plt.plot(S[:, :10])  # Plot first 10 paths
        plt.title('Geometric Brownian Motion Simulations')
        plt.xlabel('Time Steps')
        plt.ylabel('Stock Price')
        plt.grid(True)
        plt.show()

# Configuración de Streamlit
st.set_page_config(
    page_title="Panel de Análisis de Opciones - Mercado Argentino",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("📈 Panel de Análisis de Opciones - Mercado Argentino")
st.sidebar.title("Configuración")

# --- ESTILO GLOBAL STREAMLIT ---
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
        background-color: #1a1a1a !important;
        color: #ffffff !important;
    }
    .stApp, .css-18e3th9 {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
    }
    .st-bb, .st-cq, .st-dx {
        color: #ffffff !important;
    }
    .stMetric {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        border: 1px solid #444444;
    }
    .stMetric label, .stMetric span, .stMetric div {
        color: #ffffff !important;
    }
    .stDataFrame {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
    }
    .stDataFrame table, .stDataFrame th, .stDataFrame td {
        color: #ffffff !important;
        background: #2d2d2d !important;
        border: 1px solid #444444;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: #2d2d2d !important;
        border: 1px solid #444444;
    }
    .stTabs [data-baseweb="tab"] {
        color: #ffffff !important;
        background: #2d2d2d !important;
    }
    .stTabs [aria-selected="true"] {
        background: #1a237e !important;
        color: #ffffff !important;
        border: 1px solid #1a237e;
    }
    input, select, textarea {
        color: #ffffff !important;
        background: #2d2d2d !important;
        border: 1px solid #444444;
    }
    ::-webkit-scrollbar {
        width: 8px;
        background: #2d2d2d;
    }
    ::-webkit-scrollbar-thumb {
        background: #1a237e;
        border-radius: 4px;
    }
    .stNumberInput input, .stTextInput input, .stSelectbox div, .stSelectbox span, .stSelectbox label {
        color: #ffffff !important;
        background: #2d2d2d !important;
    }
    .stButton button {
        color: #ffffff !important;
        background: #1a237e !important;
        border: 1px solid #1a237e;
    }
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown strong, .stMarkdown em, .stMarkdown code {
        color: #ffffff !important;
    }
    /* --- Sidebar oscuro y letras blancas --- */
    section[data-testid="stSidebar"] {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .st-bb, 
    section[data-testid="stSidebar"] .st-cq, 
    section[data-testid="stSidebar"] .st-dx {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] input, 
    section[data-testid="stSidebar"] select, 
    section[data-testid="stSidebar"] textarea {
        color: #ffffff !important;
        background: #2d2d2d !important;
    }
    section[data-testid="stSidebar"] .stNumberInput input, 
    section[data-testid="stSidebar"] .stTextInput input, 
    section[data-testid="stSidebar"] .stSelectbox div, 
    section[data-testid="stSidebar"] .stSelectbox span, 
    section[data-testid="stSidebar"] .stSelectbox label {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .stButton button {
        color: #ffffff !important;
        background: #1a237e !important;
    }
    /* Mejorar contraste de texto en gráficos */
    .plotly-graph-div {
        background-color: #2d2d2d !important;
    }
    .plotly-graph-div .modebar {
        background-color: #2d2d2d !important;
        border: 1px solid #444444 !important;
    }
    .plotly-graph-div .modebar-group {
        border: 1px solid #444444 !important;
    }
    .plotly-graph-div .modebar .modebar-btn {
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# Variables globales para manejo de estado
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'token_portador' not in st.session_state:
    st.session_state.token_portador = None

# Funciones de autenticación y obtención de tokens
def obtener_tokens(usuario, contraseña):
    """
    Obtiene los tokens de acceso y refresco desde la API de InvertirOnline.
    """
    url_token = 'https://api.invertironline.com/token'
    datos = {
        'username': usuario,
        'password': contraseña,
        'grant_type': 'password'
    }
    encabezados = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    respuesta = requests.post(url_token, data=datos, headers=encabezados)
    if respuesta.status_code == 200:
        tokens = respuesta.json()
        return tokens['access_token'], tokens['refresh_token']
    else:
        return None, None

def refrescar_token(token_refresco):
    """
    Refresca el token de acceso usando el token de refresco.
    """
    url_token = 'https://api.invertironline.com/token'
    datos = {
        'refresh_token': token_refresco,
        'grant_type': 'refresh_token'
    }
    encabezados = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    respuesta = requests.post(url_token, data=datos, headers=encabezados)
    if respuesta.status_code == 200:
        tokens = respuesta.json()
        return tokens['access_token'], tokens['refresh_token']
    else:
        return None, None

# Credenciales de usuario de INVERTIRONLINE ############################################################################################################
usuario = 'XXXX7@gmail.com'
contraseña = 'xxxxxxxx'

# Obtener los tokens
token_portador, token_refresco = obtener_tokens(usuario, contraseña)
if token_portador and token_refresco:
    # Refrescar el token cuando expire
    token_portador, token_refresco = refrescar_token(token_refresco)

# Exportar el token_portador
productor_token = token_portador

# Configuración adaptada al mercado argentino
CONFIG = {
    'mercado': "BCBA",
    'vol_periodo': '1y',
    'pasos_binomial': 100
}

# Función de autenticación en Streamlit
def streamlit_auth():
    """
    Interfaz de autenticación para Streamlit
    """
    st.sidebar.subheader("🔐 Autenticación InvertirOnline")

    if not st.session_state.authenticated:
        with st.sidebar.form("auth_form"):
            usuario = st.text_input("Usuario", placeholder="usuario@email.com")
            contraseña = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Conectar")

            if submit and usuario and contraseña:
                with st.spinner("Autenticando..."):
                    token_portador, token_refresco = obtener_tokens(usuario, contraseña)
                    if token_portador:
                        st.session_state.authenticated = True
                        st.session_state.token_portador = token_portador
                        st.success("✅ Autenticación exitosa")
                        st.rerun()
                    else:
                        st.error("❌ Error de autenticación")
        return False
    else:
        st.sidebar.success("✅ Conectado")
        if st.sidebar.button("Desconectar"):
            st.session_state.authenticated = False
            st.session_state.token_portador = None
            st.rerun()
        return True

def seleccionar_subyacente():
    """
    Permite al usuario seleccionar un subyacente de una lista predefinida.
    Si se ejecuta en modo interactivo (por ejemplo, Jupyter o consola), usa input().
    Si se ejecuta en modo no interactivo (por ejemplo, Streamlit), usa selectbox.
    Si no hay consola disponible, selecciona el primero por defecto.
    """
    subyacentes_disponibles = ["COME", "GGAL", "YPFD", "PAMP", "BMA", "ALUA", "TGNO4", "TGSU2", "TECO2", "BYMA", "SUPV", "BHIP"]

    # Verificar si estamos en Streamlit
    try:
        if 'st' in globals() and hasattr(st, "sidebar"):
            return st.sidebar.selectbox("Selecciona un subyacente", subyacentes_disponibles, key="subyacente_selectbox_main")
    except Exception:
        pass

    # Verificar si tenemos consola interactiva disponible
    try:
        import sys
        if sys.stdin and sys.stdin.isatty():
            print("Seleccione un subyacente de la lista:")
            for i, subyacente in enumerate(subyacentes_disponibles, start=1):
                print(f"{i}. {subyacente}")
            while True:
                try:
                    seleccion = int(input("Ingrese el número correspondiente al subyacente: "))
                    if 1 <= seleccion <= len(subyacentes_disponibles):
                        return subyacentes_disponibles[seleccion - 1]
                    else:
                        print("Selección inválida. Intente nuevamente.")
                except ValueError:
                    print("Entrada no válida. Por favor, ingrese un número.")
        else:
            # No hay consola interactiva, elegir el primero por defecto
            print(f"No hay consola interactiva. Seleccionando subyacente por defecto: {subyacentes_disponibles[0]}")
            return subyacentes_disponibles[0]
    except (AttributeError, OSError, ValueError):
        # Error al acceder a stdin, usar el primer subyacente por defecto
        print(f"Error al acceder a la consola. Seleccionando subyacente por defecto: {subyacentes_disponibles[0]}")
        return subyacentes_disponibles[0]

def procesar_monto(valor):
    try:
        return float(valor.replace('.', '').replace(',', '.')) if isinstance(valor, str) else float(valor)
    except Exception:
        return 0.0

def ajustar_precio_por_dividendos(S, dividendos, fecha_vencimiento):
    """
    Ajusta el precio del subyacente para reflejar los pagos de dividendos futuros.
    """
    now = pd.Timestamp.now(tz="UTC")  # Estandarizar a UTC
    ajuste = 0
    for fecha_pago, monto_dividendo in dividendos:
        fecha_pago = pd.to_datetime(fecha_pago).tz_localize("UTC")  # Convertir a UTC
        fecha_vencimiento = pd.to_datetime(fecha_vencimiento).tz_localize("UTC")  # Convertir a UTC
        if now < fecha_pago <= fecha_vencimiento:
            tiempo_hasta_pago = (fecha_pago - now).days / 365
            ajuste += monto_dividendo * math.exp(-CONFIG['tasa_riesgo'] * tiempo_hasta_pago)
    return S - ajuste

def black_scholes(tipo, S, K, T, r, sigma, q=0, dividendos_discretos=None):
    """
    Modelo Black-Scholes ajustado para incluir dividendos discretos y continuos.
    """
    if dividendos_discretos:
        S = ajustar_precio_por_dividendos(S, dividendos_discretos, T)

    if None in [S, K, T, r, sigma] or T <= 0 or sigma <= 0:
        return (None,) * 7

    d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))  # Incluir q
    d2 = d1 - sigma * np.sqrt(T)
    nd1 = norm.pdf(d1)

    if tipo == 'Call':
        precio = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        delta, prob = norm.cdf(d1), norm.cdf(d2)
        theta = ((-S * nd1 * sigma) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * norm.cdf(d2)) / 252
    else:
        precio = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta, prob = norm.cdf(d1) - 1, norm.cdf(-d2)
        theta = ((-S * nd1 * sigma) / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 252

    if tipo == 'Put' and prob < 0:
        prob = 0

    gamma = nd1 / (S * sigma * np.sqrt(T))
    vega = S * nd1 * np.sqrt(T)
    rho = K * T * np.exp(-r * T) * (norm.cdf(d2) if tipo == 'Call' else -norm.cdf(-d2))

    return precio, delta, gamma, vega, theta, rho, prob

def binomial_pricing(tipo, S, K, T, r, sigma, N, q=0, americana=False, dividendos_discretos=None):
    """
    Modelo Binomial ajustado para incluir dividendos y opciones americanas.
    """
    if dividendos_discretos:
        S = ajustar_precio_por_dividendos(S, dividendos_discretos, T)

    if None in [S, K, T, r, sigma] or T <= 0 or sigma <= 0:
        return None

    dt = T / N
    u = math.exp(sigma * math.sqrt(dt))
    d = 1 / u
    p = (math.exp((r - q) * dt) - d) / (u - d)
    disc = math.exp(-r * dt)

    # Inicializar precios al vencimiento
    precios = [S * (u ** (N - i)) * (d ** i) for i in range(N + 1)]
    payoff = [max(0, precio - K) if tipo == 'Call' else max(0, K - precio) for precio in precios]

    # Inducción hacia atrás
    for j in range(N - 1, -1, -1):
        for i in range(j + 1):
            payoff[i] = disc * (p * payoff[i] + (1 - p) * payoff[i + 1])
            if americana:
                ejercicio = max(0, precios[i] - K) if tipo == 'Call' else max(0, K - precios[i])
                payoff[i] = max(payoff[i], ejercicio)

    return payoff[0]

def calcular_volatilidad_implicita(tipo, S, K, T, r, precio_mercado, q=0, tol=1e-5, max_iter=100, volatilidad_historica=0.2):
    """
    Calcula la volatilidad implícita con controles mejorados y método de Brent como respaldo.
    """
    if precio_mercado <= 0 or T <= 0 or S <= 0:
        return None

    if tipo == 'Call':
        lower = max(S - K * math.exp(-r * T), 0)
        upper = S
    else:
        lower = max(K * math.exp(-r * T) - S, 0)
        upper = K * math.exp(-r * T)

    if precio_mercado < lower or precio_mercado > upper:
        return None

    # Usar volatilidad histórica como base para los límites
    sigma_min = max(volatilidad_historica * 0.8, 0.20)
    sigma_max = min(volatilidad_historica * 1.5, 2.0)

    def f(sigma):
        return black_scholes(tipo, S, K, T, r, sigma, q)[0] - precio_mercado

    try:
        from scipy.optimize import brentq
        sigma = brentq(f, sigma_min, sigma_max, xtol=tol, maxiter=200)
    except ValueError:
        # Fallback a método de Newton mejorado
        def vega(sigma):
            d1 = (math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
            return S * math.sqrt(T) * norm.pdf(d1)
        try:
            from scipy.optimize import newton
            sigma = newton(f, volatilidad_historica, fprime=vega, tol=tol, maxiter=200)
        except:
            return None
    return sigma

def obtener_datos_api():
    """
    Obtiene datos de opciones del mercado argentino desde la API de InvertirOnline.
    Usa el endpoint correcto según la documentación oficial.
    """
    # Usar el token de la sesión de Streamlit si está disponible
    token_a_usar = st.session_state.get('token_portador', productor_token)

    # Usar el endpoint correcto para cotizaciones de opciones según la documentación
    url = f"https://api.invertironline.com/api/v2/Cotizaciones/Opciones/Panel%20General/Argentina"
    headers = {"Authorization": f"Bearer {token_a_usar}"}

    try:
        st.write(f"🔄 Consultando opciones para {CONFIG['simbolo']}...")
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 401:
            st.error("❌ Error de autenticación. Por favor, verifica tus credenciales.")
            return pd.DataFrame()
        elif response.status_code == 404:
            st.error(f"❌ No se encontraron opciones para el símbolo {CONFIG['simbolo']}")
            return pd.DataFrame()
        elif response.status_code != 200:
            st.error(f"❌ Error en la API: {response.status_code} - {response.text}")
            return pd.DataFrame()

        data = response.json()

        if not data or 'titulos' not in data:
            st.warning(f"⚠️ No hay opciones disponibles")
            return pd.DataFrame()

        # Filtrar solo las opciones del símbolo que nos interesa
        opciones_filtradas = []
        for titulo in data['titulos']:
            if CONFIG['simbolo'].lower() in titulo.get('simbolo', '').lower():
                opciones_filtradas.append(titulo)

        if not opciones_filtradas:
            st.warning(f"⚠️ No hay opciones disponibles para {CONFIG['simbolo']}")
            return pd.DataFrame()

        df = pd.DataFrame(opciones_filtradas)

        # Debug: mostrar información de los datos obtenidos
        st.success(f"✅ Se obtuvieron {len(df)} opciones para {CONFIG['simbolo']}")
        if not df.empty:
            st.write(f"📊 Columnas disponibles: {', '.join(df.columns.tolist())}")

            # Mostrar muestra de datos para debug
            with st.expander("🔍 Ver muestra de datos (debug)"):
                st.dataframe(df.head())

        return df

    except requests.exceptions.Timeout:
        st.error("❌ Timeout al conectar con la API. Intenta nuevamente.")
        return pd.DataFrame()
    except requests.exceptions.ConnectionError:
        st.error("❌ Error de conexión con la API. Verifica tu conexión a internet.")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error al obtener datos de la API: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
        return pd.DataFrame()

def obtener_serie_historica_subyacente(mercado, fecha_desde, fecha_hasta, ajustada, bearer_token):
    """
    Obtiene la serie histórica del subyacente configurado en CONFIG desde la API de InvertirOnline.
    """
    simbolo = CONFIG['simbolo']
    url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        return pd.DataFrame()

def obtener_series_historicas(tickers, mercados, fecha_desde, fecha_hasta, ajustada, bearer_token):
    """
    Obtiene las series históricas para una lista de símbolos y mercados.
    """
    series_historicas = {}
    for simbolo in tickers:
        for mercado in mercados:
            serie_historica = obtener_serie_historica(simbolo, mercado, fecha_desde, fecha_hasta, ajustada, bearer_token)
            if serie_historica:
                df = pd.DataFrame(serie_historica)
                series_historicas[f"{simbolo}_{mercado}"] = df
    return series_historicas

def calcular_volatilidad_historica_serie(hist, ventana=30):
    """
    Calcula una serie histórica de la volatilidad del subyacente usando una ventana móvil.
    """
    log_retornos = np.log(hist['Close'] / hist['Close'].shift(1))
    # Convertir a porcentaje anualizado (multiplicar por sqrt(252) para anualizar)
    volatilidad_serie = log_retornos.rolling(window=ventana).std() * np.sqrt(252)
    hist['VolatilidadHistorica'] = volatilidad_serie
    return hist

def calcular_volatilidad_dinamica(hist, lmbda=0.94, ventana_inicial=30):
    """
    Calcula la volatilidad dinámica usando EWMA (Exponential Weighted Moving Average).
    """
    log_retornos = np.log(hist['Close'] / hist['Close'].shift(1)).dropna()
    vol_squared = np.zeros(len(log_retornos))

    # Calcular la varianza inicial usando una ventana de datos
    initial_variance = log_retornos.iloc[:ventana_inicial].var()
    vol_squared[:ventana_inicial] = initial_variance

    # Aplicar EWMA para calcular la volatilidad dinámica
    for t in range(ventana_inicial, len(log_retornos)):
        vol_squared[t] = lmbda * vol_squared[t-1] + (1 - lmbda) * float(log_retornos.iloc[t-1])**2

    # Convertir a volatilidad anualizada
    volatilidad_dinamica = np.sqrt(vol_squared * 252)
    hist['VolatilidadDinamica'] = pd.Series(volatilidad_dinamica, index=log_retornos.index)
    return hist

# --- OPTIMIZACIONES Y MEJORAS DE PERFORMANCE Y ROBUSTEZ ---

# 1. Cacheo de funciones costosas con st.cache_data (Streamlit >=1.18)
@st.cache_data(show_spinner="Obteniendo datos del subyacente...", max_entries=10)
def obtener_datos_subyacente_cacheado(simbolo, periodo):
    ticker = yf.Ticker(f"{simbolo}.BA")
    hist = ticker.history(period=periodo)
    if hist.empty:
        return None, None, None, None
    hist = calcular_volatilidad_historica_serie(hist)
    hist = calcular_volatilidad_dinamica(hist)
    precio_spot = hist['Close'].iloc[-1]
    volatilidad_historica = hist['VolatilidadHistorica'].iloc[-1]
    volatilidad_dinamica = hist['VolatilidadDinamica'].iloc[-1]
    # Ajuste de valores extremos
    if volatilidad_historica > 1.0:
        volatilidad_historica = min(volatilidad_historica, 0.5)
    if abs(volatilidad_historica - volatilidad_dinamica) / max(volatilidad_historica, volatilidad_dinamica) > 0.5:
        promedio_vol = (volatilidad_historica + volatilidad_dinamica) / 2
        volatilidad_historica = promedio_vol
        volatilidad_dinamica = promedio_vol
    return precio_spot, volatilidad_historica, volatilidad_dinamica, hist

# 2. Cacheo de API de opciones (evita múltiples requests)
@st.cache_data(show_spinner="Obteniendo datos de opciones...", max_entries=10)
def obtener_datos_api_cacheado(token_a_usar, simbolo):
    url = f"https://api.invertironline.com/api/v2/{CONFIG['mercado']}/Titulos/{simbolo}/Opciones"
    headers = {"Authorization": f"Bearer {token_a_usar}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return pd.DataFrame()
        data = response.json()
        if not data or not isinstance(data, list):
            return pd.DataFrame()
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

# 3. Vectorización de Monte Carlo para todo el DataFrame (acelera cálculos masivos)
def calcular_montecarlo_vectorizado(df, precio_spot, volatilidad, tasa_riesgo, n_sim=5000):
    # Solo para filas válidas
    valid = (df['T'] > 0) & (df['strike'] > 0) & (df['precioOpcion'] > 0)
    df_valid = df[valid].copy()
    if df_valid.empty:
        df[['MC_ProbProfit', 'MC_GananciaEsperada', 'MC_ProbITM', 'MC_PrecioSimulado']] = None
        return df
    # Precalcular Z para todos
    np.random.seed(42)
    Z = np.random.standard_normal((len(df_valid), n_sim))
    S0 = precio_spot
    r = tasa_riesgo
    # Usar volatilidad implícita si está, sino la de subyacente
    sigmas = df_valid['volatilidadImplicita'].fillna(volatilidad).values
    Ks = df_valid['strike'].values
    Ts = df_valid['T'].values
    primas = df_valid['precioOpcion'].values
    tipos = df_valid['tipoOpcion'].values
    ST = S0 * np.exp((r - 0.5 * sigmas[:, None]**2) * Ts[:, None] + sigmas[:, None] * np.sqrt(Ts[:, None]) * Z)
    payoff_intrinseco = np.where(
        tipos[:, None] == 'Call',
        np.maximum(ST - Ks[:, None], 0),
        np.maximum(Ks[:, None] - ST, 0)
    )
    payoff_neto = payoff_intrinseco - primas[:, None]
    prob_itm_mc = np.where(
        tipos == 'Call',
        np.mean(ST > Ks[:, None], axis=1),
        np.mean(ST < Ks[:, None], axis=1)
    )
    prob_profit_mc = np.mean(payoff_neto > 0, axis=1)
    ganancia_esperada_mc = np.mean(payoff_neto, axis=1) * prob_profit_mc * prob_itm_mc
    precio_subyacente_simulado = np.mean(ST, axis=1)
    # Asignar resultados
    df.loc[valid, 'MC_ProbProfit'] = prob_profit_mc
    df.loc[valid, 'MC_GananciaEsperada'] = ganancia_esperada_mc
    df.loc[valid, 'MC_ProbITM'] = prob_itm_mc
    df.loc[valid, 'MC_PrecioSimulado'] = precio_subyacente_simulado
    return df

# 4. Mejoras en procesar_dataframe: evitar apply fila a fila para Monte Carlo
def procesar_dataframe(df, precio_spot, volatilidad_historica, volatilidad_dinamica, tasa_dividendos, hist_volatilidad):
    if df.empty:
        print("DataFrame vacío recibido")
        return pd.DataFrame()

    # --- Extraer datos según la estructura correcta de la API de IOL ---
    # Los campos están directamente en el objeto, no en un sub-objeto 'cotizacion'
    
    # Extraer precio de la opción
    if 'ultimoPrecio' in df.columns:
        df['precioOpcion'] = df['ultimoPrecio'].apply(lambda x: procesar_monto(x) if x is not None else 0.0)
    else:
        df['precioOpcion'] = 0.0

    # Extraer volumen directamente
    if 'volumen' in df.columns:
        df['volumen'] = df['volumen'].apply(lambda x: procesar_monto(x) if x is not None else 0.0)
    else:
        df['volumen'] = 0.0

    # Extraer montoOperado directamente
    if 'montoOperado' in df.columns:
        df['montoOperado'] = df['montoOperado'].apply(lambda x: procesar_monto(x) if x is not None else 0.0)
    else:
        df['montoOperado'] = 0.0

    # Extraer bid y ask de las puntas
    if 'puntas' in df.columns:
        df['bid'] = df['puntas'].apply(lambda x: procesar_monto(x.get('precioCompra', 0)) if isinstance(x, dict) else 0.0)
        df['ask'] = df['puntas'].apply(lambda x: procesar_monto(x.get('precioVenta', 0)) if isinstance(x, dict) else 0.0)
    else:
        df['bid'] = 0.0
        df['ask'] = 0.0

    # Corregir bid y ask si son 0
    df.loc[df['bid'] == 0, 'bid'] = df['precioOpcion'] * 0.95
    df.loc[df['ask'] == 0, 'ask'] = df['precioOpcion'] * 1.05

    # Extraer strike (precioEjercicio según la documentación)
    if 'precioEjercicio' in df.columns:
        df['strike'] = df['precioEjercicio'].apply(lambda x: procesar_monto(x) if x is not None else 0.0)
    elif 'strike' in df.columns:
        df['strike'] = df['strike'].apply(lambda x: procesar_monto(x) if x is not None else 0.0)
    elif 'descripcion' in df.columns:
        df['strike'] = df['descripcion'].str.split().str[2].str.replace(',', '').astype(float, errors='ignore')
    else:
        print("No se pudo encontrar información de strike")
        return pd.DataFrame()

    # Corregir strikes mal escalados
    df['strike'] = df['strike'].apply(lambda x: x * 1000 if x < 10 else x)

    # Filtrar filas con strike válido
    df = df[df['strike'].notnull() & (df['strike'] > 0)]

    # Procesar fecha de vencimiento
    if 'fechaVencimiento' in df.columns:
        df['fechaVencimiento'] = pd.to_datetime(df['fechaVencimiento'], errors='coerce').dt.date
    else:
        print("No se pudo encontrar información de fecha de vencimiento")
        return pd.DataFrame()

    # Calcular tiempo hasta vencimiento
    calendario_arg = mcal.get_calendar("XBUE")
    now = pd.Timestamp.now().normalize()

    df['T'] = df['fechaVencimiento'].apply(
        lambda x: len(calendario_arg.valid_days(start_date=now, end_date=pd.Timestamp(x))) / 252
        if pd.notnull(x) and pd.Timestamp(x) > now else None
    )

    # Filtrar opciones válidas
    df = df[(df['precioOpcion'] > 0) & (df['T'] > 0)]
    df = df[df['strike'].notnull() & (df['strike'] > 0) & df['T'].notnull() & (df['T'] > 0)]

    if df.empty:
        print("No quedan opciones válidas después del filtrado")
        return pd.DataFrame()

    df['precioSubyacente'] = precio_spot

    if 'Moneyness' not in df.columns:
        df['Moneyness'] = df.apply(
            lambda r: 'ITM' if
                (r['tipoOpcion'] == 'Call' and r['strike'] < r['precioSubyacente']) or
                (r['tipoOpcion'] == 'Put' and r['strike'] > r['precioSubyacente'])
            else 'OTM',
            axis=1
        )

    # Calcular volatilidad implícita primero
    df['volatilidadImplicita'] = df.apply(
        lambda r: calcular_volatilidad_implicita(
            r['tipoOpcion'], precio_spot, r['strike'], r['T'], CONFIG['tasa_riesgo'],
            r['precioOpcion'], tasa_dividendos, volatilidad_historica=volatilidad_dinamica
        ) if r['precioOpcion'] > 0 else None,
        axis=1
    )

    df['volatilidadImplicita_original'] = df['volatilidadImplicita']
    df['volatilidadSubyacente'] = volatilidad_dinamica

    # Usar volatilidad implícita si está disponible, sino usar volatilidad del subyacente
    volatilidad_para_calculos = df.apply(
        lambda r: r['volatilidadImplicita'] if pd.notnull(r['volatilidadImplicita']) else volatilidad_dinamica,
        axis=1
    )

    # Calcular Black-Scholes
    bs = df.apply(
        lambda r: black_scholes(
            r['tipoOpcion'], precio_spot, r['strike'], r['T'], CONFIG['tasa_riesgo'],
            volatilidad_para_calculos[r.name], tasa_dividendos
        ) if volatilidad_para_calculos[r.name] > 0 else (None,) * 7,
        axis=1
    )
    df[['BlackScholes', 'Delta', 'Gamma', 'Vega', 'Theta', 'Rho', 'Prob_ITM']] = pd.DataFrame(bs.tolist(), index=df.index)

    # Calcular Binomial
    df['Binomial'] = df.apply(
        lambda r: binomial_pricing(
            r['tipoOpcion'], precio_spot, r['strike'], r['T'], CONFIG['tasa_riesgo'],
            volatilidad_para_calculos[r.name], CONFIG['pasos_binomial'], tasa_dividendos, americana=True
        ) if volatilidad_para_calculos[r.name] > 0 else None,
        axis=1
    )

    # NUEVO: Calcular Monte Carlo para cada opción una vez
    print("Calculando Monte Carlo para todas las opciones...")
    def calcular_montecarlo_fila(row):
        """Calcula Monte Carlo para una fila específica"""
        try:
            S0 = precio_spot
            K = row['strike']
            T = row['T']
            sigma = volatilidad_para_calculos[row.name]
            r = CONFIG.get('tasa_riesgo', 0.05)
            prima = row['precioOpcion']
            tipo = row['tipoOpcion']

            # Validar parámetros
            if T <= 0 or sigma <= 0 or S0 <= 0 or K <= 0 or prima <= 0:
                return None, None, None, None

            # Simulación Monte Carlo
            n_sim = 5000  # Reducido para eficiencia
            np.random.seed(42)  # Para reproducibilidad
            Z = np.random.standard_normal(n_sim)
            ST = S0 * np.exp((r - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * Z)

            # Calcular payoffs
            if tipo == 'Call':
                payoff_intrinseco = np.maximum(ST - K, 0)
                payoff_neto = payoff_intrinseco - prima
                prob_itm_mc = np.mean(ST > K)
            else:  # Put
                payoff_intrinseco = np.maximum(K - ST, 0)
                payoff_neto = payoff_intrinseco - prima
                prob_itm_mc = np.mean(ST < K)

            prob_profit_mc = np.mean(payoff_neto > 0)
            # Ajuste: Ganancia esperada ponderada por probabilidad de profit e ITM
            ganancia_esperada_mc = (
                np.mean(payoff_neto) * prob_profit_mc * prob_itm_mc
                if prob_profit_mc is not None and prob_itm_mc is not None else np.mean(payoff_neto)
            )
            precio_subyacente_simulado = np.mean(ST)

            return prob_profit_mc, ganancia_esperada_mc, prob_itm_mc, precio_subyacente_simulado

        except Exception as e:
            print(f"Error en Monte Carlo para fila {row.name}: {e}")
            return None, None, None, None

    # Aplicar Monte Carlo a todas las filas
    mc_results = df.apply(calcular_montecarlo_fila, axis=1)
    df[['MC_ProbProfit', 'MC_GananciaEsperada', 'MC_ProbITM', 'MC_PrecioSimulado']] = pd.DataFrame(mc_results.tolist(), index=df.index)

    # Calcular VaR
    df['VaR'] = df.apply(
        lambda r: calcular_var_opciones(pd.DataFrame([r]))['VaR'].iloc[0] if pd.notnull(r['Delta']) and pd.notnull(r['Gamma']) else None,
        axis=1
    )

    if 'Prob_OTM' not in df.columns:
        df['Prob_OTM'] = 1 - df['Prob_ITM']

    return df

def crear_df_resumen(df_procesado):
    """
    Crea un DataFrame resumido con las columnas más importantes para mostrar.
    Ahora incluye las métricas de Monte Carlo.
    """
    if df_procesado.empty:
        return pd.DataFrame()

    columnas_resumen = [
        'simbolo', 'tipoOpcion', 'strike', 'fechaVencimiento', 'T',
        'precioOpcion', 'bid', 'ask', 'volumen', 'montoOperado',
        'volatilidadImplicita', 'BlackScholes', 'Binomial', 'Delta', 
        'Gamma', 'Vega', 'Theta', 'Rho', 'Prob_ITM', 'Prob_OTM', 
        'Moneyness', 'VaR', 'precioSubyacente',
        'MC_ProbProfit', 'MC_GananciaEsperada', 'MC_ProbITM', 'MC_PrecioSimulado'  # Nuevas columnas MC
    ]

    # Seleccionar solo las columnas que existen
    columnas_existentes = [col for col in columnas_resumen if col in df_procesado.columns]

    if 'simbolo' not in df_procesado.columns:
        df_procesado['simbolo'] = df_procesado.get('descripcion', 'N/A')

    df_resumen = df_procesado[columnas_existentes].copy()

    # Ensure precioSubyacente is in the DataFrame
    if 'precioSubyacente' not in df_resumen.columns and 'precioSubyacente' in df_procesado.columns:
        df_resumen['precioSubyacente'] = df_procesado['precioSubyacente']

    return df_resumen

def mostrar_tabla_opciones(df_resumen):
    """
    Muestra la tabla de opciones procesadas en Streamlit.
    Ahora incluye las columnas de Monte Carlo y filtro por vencimiento.
    """
    st.subheader("📋 Tabla de Opciones Procesadas")

    if df_resumen.empty:
        st.info("No hay opciones procesadas para mostrar.")
        return

    # Filtros interactivos
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        tipos_disponibles = ['Todos'] + list(df_resumen['tipoOpcion'].unique())
        filtro_tipo = st.selectbox("Filtrar por tipo", tipos_disponibles)

    with col2:
        moneyness_disponibles = ['Todos'] + list(df_resumen['Moneyness'].unique())
        filtro_moneyness = st.selectbox("Filtrar por moneyness", moneyness_disponibles)

    with col3:
        # Nuevo: filtro por vencimiento
        vencimientos_disponibles = ['Todos'] + sorted(df_resumen['fechaVencimiento'].dropna().unique().tolist())
        filtro_vencimiento = st.selectbox("Filtrar por vencimiento", vencimientos_disponibles)

    with col4:
        ordenar_por = st.selectbox("Ordenar por", 
                                  ['Prob_ITM', 'MC_ProbProfit', 'volatilidadImplicita', 'Delta', 'VaR', 'strike'])

    # Aplicar filtros
    df_filtrado = df_resumen.copy()

    if filtro_tipo != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['tipoOpcion'] == filtro_tipo]

    if filtro_moneyness != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Moneyness'] == filtro_moneyness]

    if filtro_vencimiento != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['fechaVencimiento'] == filtro_vencimiento]

    # Ordenar
    if ordenar_por in df_filtrado.columns:
        df_filtrado = df_filtrado.sort_values(ordenar_por, ascending=False)

    # Formatear columnas para mostrar
    df_display = df_filtrado.copy()

    # Formatear porcentajes
    for col in ['volatilidadImplicita', 'Prob_ITM', 'Prob_OTM', 'MC_ProbProfit', 'MC_ProbITM']:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else "N/A")

    # Formatear números
    for col in ['precioOpcion', 'BlackScholes', 'Binomial', 'VaR', 'MC_GananciaEsperada', 'MC_PrecioSimulado']:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A")

    # Formatear griegas
    for col in ['Delta', 'Gamma', 'Vega', 'Theta', 'Rho']:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(lambda x: f"{x:.4f}" if pd.notnull(x) else "N/A")

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Estadísticas resumen mejoradas - SEPARADAS POR TIPO DE OPCIÓN
    st.markdown("### 📊 Estadísticas Resumen")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Total Opciones", len(df_filtrado))

    with col2:
        calls_count = len(df_filtrado[df_filtrado['tipoOpcion'] == 'Call']) if 'tipoOpcion' in df_filtrado.columns else 0
        st.metric("Calls", calls_count)

    with col3:
        puts_count = len(df_filtrado[df_filtrado['tipoOpcion'] == 'Put']) if 'tipoOpcion' in df_filtrado.columns else 0
        st.metric("Puts", puts_count)

    with col4:
        vol_promedio = df_filtrado['volatilidadImplicita'].mean() if 'volatilidadImplicita' in df_filtrado.columns else 0
        st.metric("Vol. Impl. Promedio", f"{vol_promedio:.2%}" if pd.notnull(vol_promedio) else "N/A")

    with col5:
        # Probabilidad de profit promedio para CALLS
        calls_df = df_filtrado[df_filtrado['tipoOpcion'] == 'Call'] if 'tipoOpcion' in df_filtrado.columns else pd.DataFrame()
        mc_profit_calls = calls_df['MC_ProbProfit'].mean() if not calls_df.empty and 'MC_ProbProfit' in calls_df.columns else 0
        st.metric("Prob. Profit Calls (MC)", f"{mc_profit_calls:.2%}" if pd.notnull(mc_profit_calls) else "N/A")

    with col6:
        # Probabilidad de profit promedio para PUTS
        puts_df = df_filtrado[df_filtrado['tipoOpcion'] == 'Put'] if 'tipoOpcion' in df_filtrado.columns else pd.DataFrame()
        mc_profit_puts = puts_df['MC_ProbProfit'].mean() if not puts_df.empty and 'MC_ProbProfit' in puts_df.columns else 0
        st.metric("Prob. Profit Puts (MC)", f"{mc_profit_puts:.2%}" if pd.notnull(mc_profit_puts) else "N/A")

def mostrar_perfil_riesgo_y_composicion(token_portador):
    """
    Muestra el perfil de riesgo y composición sugerida de la cartera.
    """
    st.subheader("⚖️ Perfil de Riesgo y Composición Sugerida")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📋 Perfil de Riesgo")
        st.info("""
        **Recomendaciones generales:**
        - Diversificar entre calls y puts
        - Considerar diferentes vencimientos
        - Monitorear volatilidad implícita vs histórica
        - Establecer stop-loss apropiados
        """)

    with col2:
        st.markdown("#### 🎯 Composición Sugerida")
        # Crear gráfico de composición ejemplo
        labels = ['Calls ITM', 'Calls OTM', 'Puts ITM', 'Puts OTM']
        values = [30, 20, 25, 25]

        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
        fig.update_layout(
            title="Distribución Sugerida",
            height=300,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)

def graficar_volumen_historico(simbolo, token_portador, dias=60):
    """
    Grafica el volumen histórico del subyacente.
    """
    st.subheader(f"📊 Volumen Histórico - {simbolo}")
    try:
        ticker = yf.Ticker(f"{simbolo}.BA")
        hist = ticker.history(period=f"{dias}d")
        if not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['Volume'],
                mode='lines',
                name='Volumen',
                line=dict(color='#42a5f5')
            ))
            fig.update_layout(
                title=f"Volumen Histórico - {simbolo} (últimos {dias} días)",
                xaxis_title="Fecha",
                yaxis_title="Volumen",
                height=400,
                template="plotly_dark",
                font=dict(color="#fff"),
                plot_bgcolor="#232323",
                paper_bgcolor="#232323"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Estadísticas del volumen
            vol_promedio = hist['Volume'].mean()
            vol_max = hist['Volume'].max()
            vol_min = hist['Volume'].min()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Volumen Máximo", f"{vol_max:,.0f}")
            with col2:
                st.metric("Volumen Promedio", f"{vol_promedio:,.0f}")
            with col3:
                st.metric("Volumen Mínimo", f"{vol_min:,.0f}")
    except Exception as e:
        st.error(f"Error al obtener volumen histórico: {str(e)}")

def graficar_sonrisa_volatilidad_avanzada(df_procesado):
    """
    Grafica la sonrisa de volatilidad implícita mostrando TODAS las opciones, sin filtrar por vencimiento.
    Eje X: Strike real, Eje Y: Volatilidad real (decimal), color por vencimiento, forma por tipo.
    """
    if df_procesado.empty or 'volatilidadImplicita' not in df_procesado.columns:
        st.warning("No hay datos de volatilidad implícita disponibles")
        return

    df_vol = df_procesado.dropna(subset=['volatilidadImplicita', 'strike', 'tipoOpcion', 'T', 'fechaVencimiento'])
    if df_vol.empty:
        st.warning("No hay datos válidos para graficar la sonrisa de volatilidad")
        return

    # Mapear tipoOpcion a símbolo
    symbol_map = {'Call': 'triangle-up', 'Put': 'triangle-down'}
    color_map = {v: c for v, c in zip(sorted(df_vol['fechaVencimiento'].unique()), px.colors.qualitative.Plotly)}

    fig = go.Figure()
    for tipo in ['Call', 'Put']:
        df_tipo = df_vol[df_vol['tipoOpcion'] == tipo]
        for venc in sorted(df_tipo['fechaVencimiento'].unique()):
            df_v = df_tipo[df_tipo['fechaVencimiento'] == venc]
            fig.add_trace(go.Scatter(
                x=df_v['strike'],
                y=df_v['volatilidadImplicita'],
                mode='markers',
                name=f"{tipo} {venc}",
                marker=dict(
                    symbol=symbol_map.get(tipo, 'circle'),
                    size=10,
                    color=color_map.get(venc, None),
                    line=dict(width=1, color='black')
                ),
                text=[f"Venc: {venc}" for _ in range(len(df_v))],
                hovertemplate=f'{tipo} - Venc: {venc}<br>Strike: %{{x}}<br>Vol. Impl.: %{{y:.4f}}<extra></extra>'
            ))

    # Línea de volatilidad histórica
    if 'volatilidadSubyacente' in df_vol.columns:
        vol_historica = df_vol['volatilidadSubyacente'].iloc[0]
        fig.add_hline(
            y=vol_historica,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"Vol. Histórica: {vol_historica:.4f}",
            annotation_position="top right"
        )
    # Línea del precio spot
    if 'precioSubyacente' in df_vol.columns:
        precio_spot = df_vol['precioSubyacente'].iloc[0]
        fig.add_vline(
            x=precio_spot,
            line_dash="dot",
            line_color="red",
            annotation_text=f"Spot: {precio_spot:.2f}",
            annotation_position="top"
        )

    fig.update_layout(
        title="Sonrisa de Volatilidad Implícita (Todas las Opciones)",
        xaxis_title="Strike",
        yaxis_title="Volatilidad Implícita",
        template="plotly_white",
        height=500,
        hovermode='closest',
        legend_title="Tipo y Vencimiento"
    )
    # Ejes con valores reales
    fig.update_xaxes(tickformat=None)
    fig.update_yaxes(tickformat=None)
    st.plotly_chart(fig, use_container_width=True)

    # Análisis adicional de la sonrisa
    st.markdown("#### 📈 Análisis de la Sonrisa de Volatilidad")
    col1, col2, col3 = st.columns(3)
    with col1:
        if len(df_vol) > 2:
            precio_spot = df_vol['precioSubyacente'].iloc[0] if 'precioSubyacente' in df_vol.columns else df_vol['strike'].median()
            df_vol['distancia_atm'] = abs(df_vol['strike'] - precio_spot)
            atm_vol = df_vol.loc[df_vol['distancia_atm'].idxmin(), 'volatilidadImplicita']
            otm_calls = df_vol[(df_vol['tipoOpcion'] == 'Call') & (df_vol['strike'] > precio_spot)]
            otm_puts = df_vol[(df_vol['tipoOpcion'] == 'Put') & (df_vol['strike'] < precio_spot)]
            if not otm_calls.empty and not otm_puts.empty:
                sesgo_calls = otm_calls['volatilidadImplicita'].mean() - atm_vol
                sesgo_puts = otm_puts['volatilidadImplicita'].mean() - atm_vol
                sesgo_promedio = (sesgo_calls + sesgo_puts) / 2
                st.metric("📊 Sesgo Promedio", f"{sesgo_promedio:.2%}")
            else:
                st.metric("📊 Sesgo Promedio", "N/A")
        else:
            st.metric("📊 Sesgo Promedio", "N/A")
    with col2:
        vol_min = df_vol['volatilidadImplicita'].min()
        vol_max = df_vol['volatilidadImplicita'].max()
        convexidad = vol_max - vol_min
        st.metric("📐 Convexidad", f"{convexidad:.2%}")
    with col3:
        st.metric("📍 Puntos de Datos", len(df_vol))

def graficar_var(df_resumen):
    """
    Grafica el Value at Risk (VaR) de todas las opciones.
    Eje X: Strike real, Eje Y: VaR real, color por vencimiento, forma por tipo.
    """
    st.subheader("📉 Gráfico de Value at Risk (VaR) de Opciones")
    if df_resumen.empty or 'VaR' not in df_resumen.columns:
        st.warning("No hay datos de VaR disponibles")
        return
    df_var = df_resumen.dropna(subset=['VaR', 'strike', 'tipoOpcion', 'fechaVencimiento'])
    if df_var.empty:
        st.warning("No hay datos válidos de VaR")
        return

    symbol_map = {'Call': 'triangle-up', 'Put': 'triangle-down'}
    color_map = {v: c for v, c in zip(sorted(df_var['fechaVencimiento'].unique()), px.colors.qualitative.Plotly)}

    fig = go.Figure()
    for tipo in ['Call', 'Put']:
        df_tipo = df_var[df_var['tipoOpcion'] == tipo]
        for venc in sorted(df_tipo['fechaVencimiento'].unique()):
            df_v = df_tipo[df_tipo['fechaVencimiento'] == venc]
            fig.add_trace(go.Scatter(
                x=df_v['strike'],
                y=df_v['VaR'],
                mode='markers',
                name=f"{tipo} {venc}",
                marker=dict(
                    symbol=symbol_map.get(tipo, 'circle'),
                    size=10,
                    color=color_map.get(venc, None),
                    line=dict(width=1, color='black')
                ),
                text=[f"Venc: {venc}" for _ in range(len(df_v))],
                hovertemplate=f'{tipo} - Venc: {venc}<br>Strike: %{{x}}<br>VaR: %{{y}}<extra></extra>'
            ))
    fig.update_layout(
        title="Value at Risk (VaR) por Strike",
        xaxis_title="Strike",
        yaxis_title="VaR",
        template="plotly_white",
        height=400,
        legend_title="Tipo y Vencimiento"
    )
    fig.update_xaxes(tickformat=None)
    fig.update_yaxes(tickformat=None)
    st.plotly_chart(fig, use_container_width=True)

def graficar_probabilidad_profit(df_resumen):
    """
    Grafica la probabilidad de profit de todas las opciones.
    Eje X: Strike real, Eje Y: Probabilidad real (decimal), color por vencimiento, forma por tipo.
    """
    st.subheader("📈 Gráfico de Probabilidad de Profit de Opciones")
    if df_resumen.empty or 'MC_ProbProfit' not in df_resumen.columns:
        st.warning("No hay datos de probabilidad de profit disponibles")
        return
    df_prob = df_resumen.dropna(subset=['MC_ProbProfit', 'strike', 'tipoOpcion', 'fechaVencimiento'])
    if df_prob.empty:
        st.warning("No hay datos válidos de probabilidad de profit")
        return

    symbol_map = {'Call': 'triangle-up', 'Put': 'triangle-down'}
    color_map = {v: c for v, c in zip(sorted(df_prob['fechaVencimiento'].unique()), px.colors.qualitative.Plotly)}

    fig = go.Figure()
    for tipo in ['Call', 'Put']:
        df_tipo = df_prob[df_prob['tipoOpcion'] == tipo]
        for venc in sorted(df_tipo['fechaVencimiento'].unique()):
            df_v = df_tipo[df_tipo['fechaVencimiento'] == venc]
            fig.add_trace(go.Scatter(
                x=df_v['strike'],
                y=df_v['MC_ProbProfit'],
                mode='markers',
                name=f"{tipo} {venc}",
                marker=dict(
                    symbol=symbol_map.get(tipo, 'circle'),
                    size=10,
                    color=color_map.get(venc, None),
                    line=dict(width=1, color='black')
                ),
                text=[f"Venc: {venc}" for _ in range(len(df_v))],
                hovertemplate=f'{tipo} - Venc: {venc}<br>Strike: %{{x}}<br>Prob. Profit: %{{y:.4f}}<extra></extra>'
            ))
    fig.update_layout(
        title="Probabilidad de Profit por Strike",
        xaxis_title="Strike",
        yaxis_title="Probabilidad de Profit",
        template="plotly_white",
        height=400,
        legend_title="Tipo y Vencimiento"
    )
    fig.update_xaxes(tickformat=None)
    fig.update_yaxes(tickformat=None)
    st.plotly_chart(fig, use_container_width=True)
def main_streamlit():
    """
    Función principal para la aplicación Streamlit
    """
    # Verificar autenticación
    if not streamlit_auth():
        st.info("👆 Por favor, ingresa tus credenciales de InvertirOnline en la barra lateral para continuar.")
        return

    # Configuración del análisis
    CONFIG['simbolo'] = seleccionar_subyacente()

    # Botón para ejecutar análisis
    if st.sidebar.button("🚀 Ejecutar Análisis", type="primary"):
        with st.spinner("Analizando opciones..."):
            try:
                # Obtener tasa de caución
                tasa_caucion = obtener_tasas_caucion(st.session_state.token_portador)
                if tasa_caucion and 'titulos' in tasa_caucion:
                    df_tasas = pd.DataFrame(tasa_caucion['titulos'])
                    if not df_tasas.empty and 'tasaPromedio' in df_tasas.columns:
                        CONFIG['tasa_riesgo'] = df_tasas['tasaPromedio'].max() / 100
                        CONFIG['tasa_riesgo'] = df_tasas['tasaPromedio'].mean() / 100  # Cambiado de max() a mean()
                    else:
                        CONFIG['tasa_riesgo'] = 0.05
                else:
                    CONFIG['tasa_riesgo'] = 0.05

                # Obtener datos del subyacente (cacheado)
                precio_spot, vol_hist, vol_din, hist_vol = obtener_datos_subyacente_cacheado(CONFIG['simbolo'], CONFIG['vol_periodo'])
                if not precio_spot:
                    st.error("No se pudieron obtener datos del subyacente")
                    return

                # Obtener dividendos
                df_div, total_div = obtener_dividendos_splits()
                tasa_div = (total_div / precio_spot) if precio_spot and total_div > 0 else 0

                # Procesar opciones (cacheado)
                df_api = obtener_datos_api_cacheado(st.session_state.token_portador, CONFIG['simbolo'])
                if df_api.empty:
                    st.error("No se pudieron obtener datos de opciones")
                    return

                df_procesado = procesar_dataframe(df_api, precio_spot, vol_hist, vol_din, tasa_div, hist_vol)
                df_procesado = calcular_var_opciones(df_procesado)

                # Crear resumen
                df_resumen = crear_df_resumen(df_procesado)

                # Calcular sesgo
                sesgo = calcular_sesgo(df_procesado, precio_spot)

                # Preparar resultados
                resultados = {
                    'df_procesado': df_procesado,
                    'df_resumen': df_resumen,
                    'precio_spot': precio_spot,
                    'volatilidad_historica': vol_hist,
                    'volatilidad_dinamica': vol_din,
                    'sesgo_mercado': sesgo
                }

                # Guardar en session_state
                st.session_state.resultados = resultados
                st.session_state.hist_volatilidad = hist_vol

                st.success("✅ Análisis completado")

            except Exception as e:
                st.error(f"Error durante el análisis: {str(e)}")
                return

    # Mostrar resultados si están disponibles
    if 'resultados' in st.session_state:
        resultados = st.session_state.resultados
        hist_vol = st.session_state.get('hist_volatilidad')

        # --- NUEVO: Tabs principales ---
        tabs = st.tabs([
            "📊 Métricas Principales",
            "⚖️ Perfil de Riesgo",
            "📉 Análisis Técnico Subyacente",
            "📋 Tabla de Opciones",
            # "📈 Gráficos Interactivos",  # Eliminado
            "😊 Sonrisa de Volatilidad",
            "📉 VaR",
            "📈 Probabilidad Profit",
            "🎯 Monte Carlo"
        ])
        # Tab 0: Métricas principales
        with tabs[0]:
            mostrar_metricas_principales(resultados)
        # Tab 1: Perfil de riesgo y composición sugerida
        with tabs[1]:
            mostrar_perfil_riesgo_y_composicion(st.session_state.token_portador)
        # Tab 2: Análisis técnico subyacente (volumen histórico)
        with tabs[2]:
            mostrar_analisis_tecnico_subyacente(CONFIG['simbolo'], st.session_state.token_portador)
        # Tab 3: Tabla de opciones
        with tabs[3]:
            mostrar_tabla_opciones(resultados['df_resumen'])
        # Tab 4: Sonrisa de volatilidad
        with tabs[4]:
            graficar_sonrisa_volatilidad_avanzada(resultados['df_procesado'])
        # Tab 5: VaR
        with tabs[5]:
            graficar_var(resultados['df_resumen'])
        # Tab 6: Probabilidad de profit
        with tabs[6]:
            graficar_probabilidad_profit(resultados['df_resumen'])
        # Tab 7: Monte Carlo y análisis de profit
        with tabs[7]:
            mostrar_probabilidad_profit_y_montecarlo(resultados['df_resumen'])

def mostrar_tradingview_chart(simbolo):
    """
    Muestra un gráfico interactivo de TradingView para el símbolo dado.
    """
    tv_symbol = f"BCBA:{simbolo}"
    html_code = f"""
    <div style="width:100%;height:500px;">
      <iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_{simbolo}&symbol={tv_symbol}&interval=D&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=dark&style=1&timezone=America%2FArgentina%2FBuenos_Aires&withdateranges=1&hidevolume=0&hideideas=1&studies_overrides=%7B%7D&overrides=%7B%7D&enabled_features=%5B%5D&disabled_features=%5B%5D&locale=es" 
        style="width:100%;height:500px;" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
    </div>
    """
    components.html(html_code, height=520)

def mostrar_analisis_tecnico_subyacente(simbolo, token_portador):
    """
    Muestra una ventana/pestaña de análisis técnico del subyacente, incluyendo el gráfico de volumen histórico y TradingView.
    """
    st.markdown("### 📉 Análisis Técnico del Subyacente")
    # Mostrar TradingView chart
    mostrar_tradingview_chart(simbolo)
    dias_vol = st.slider("Días para volumen histórico", min_value=10, max_value=365, value=60, step=10, key="tecnico_dias_vol")
    graficar_volumen_historico(simbolo, token_portador, dias=dias_vol)

def calcular_probabilidad_profit_montecarlo(row, n_sim=10000):
    """
    Calcula la probabilidad de profit usando simulación de Monte Carlo.
    Simula el precio del subyacente al vencimiento y calcula el payoff de la opción.
    Retorna (probabilidad de profit, array de payoffs simulados).
    """
    required_fields = ['precioSubyacente', 'strike', 'T', 'volatilidadImplicita', 'precioOpcion', 'tipoOpcion']
    # --- Cambio: obtener volatilidad válida ---
    # Usar volatilidad implícita, si no es válida usar volatilidadSubyacente si está disponible
    sigma = row.get('volatilidadImplicita', None)
    if (sigma is None or not np.isfinite(sigma) or sigma <= 0):
        sigma = row.get('volatilidadSubyacente', None)
    if (sigma is None or not np.isfinite(sigma) or sigma <= 0):
        # Último recurso: usar volatilidad histórica si está disponible
        sigma = row.get('volatilidadHistorica', None)
    # Si sigue siendo inválida, abortar
    if (sigma is None or not np.isfinite(sigma) or sigma <= 0):
        return None, None

    # Validar los demás campos requeridos
    for field in required_fields:
        if field not in row.index or pd.isnull(row[field]):
            return None, None

    S0 = row['precioSubyacente']
    K = row['strike']
    T = row['T']
    r = CONFIG.get('tasa_riesgo', 0.05)
    prima = row['precioOpcion']
    tipo = row['tipoOpcion']

    # Validar valores numéricos positivos
    if S0 <= 0 or K <= 0 or T <= 0 or sigma <= 0 or prima < 0:
        return None, None

    # Simulación de precios finales del subyacente al vencimiento
    np.random.seed(42)
    Z = np.random.standard_normal(n_sim)
    ST = S0 * np.exp((r - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * Z)

    # Calcular payoff de la opción
    if tipo == 'Call':
        payoff = np.maximum(ST - K, 0) - prima
    else:
        payoff = np.maximum(K - ST, 0) - prima

    prob_profit = np.mean(payoff > 0)
    return prob_profit, payoff

def graficar_histograma_montecarlo(payoff, tipo_opcion, strike, precio_opcion):
    """
    Genera un histograma de los resultados de la simulación de Monte Carlo.
    """
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=payoff, nbinsx=50, name="Payoff"))
    fig.update_layout(
        title_text="Simulación Monte Carlo - Distribución de Payoff",
        xaxis_title="Payoff al vencimiento",
        yaxis_title="Frecuencia",
        bargap=0.05,
        template="plotly_white"
    )
    # Línea en cero (break-even)
    fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Break-even", annotation_position="top right")
    return fig

def graficar_volatilidad_implícita(df_resumen, hist_vol):
    """
    Grafica la volatilidad implícita de las opciones.
    Por ahora, función dummy.
    """
    print("Gráfico de volatilidad implícita (dummy).")

def graficar_probabilidad_itm(df_resumen):
    """
    Grafica la probabilidad ITM de las opciones.
    Por ahora, función dummy.
    """
    print("Gráfico de probabilidad ITM (dummy).")

def mostrar_metricas_principales(resultados):
    """
    Muestra las métricas principales del análisis.
    """
    st.subheader("📊 Métricas Principales")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Precio Spot", f"${resultados['precio_spot']:.2f}")

    with col2:
        st.metric("Vol. Histórica", f"{resultados['volatilidad_historica']:.2%}")

    with col3:
        st.metric("Vol. Dinámica", f"{resultados['volatilidad_dinamica']:.2%}")

    with col4:
        # Mostrar sesgo y si es alcista/bajista/neutro
        sesgo = resultados['sesgo_mercado']
        if isinstance(sesgo, tuple):
            sesgo_val, sesgo_tipo = sesgo
        else:
            sesgo_val, sesgo_tipo = sesgo, "Neutro"
        st.metric("Sesgo Mercado", f"{sesgo_val:.2%} ({sesgo_tipo})")

def mostrar_probabilidad_profit_y_montecarlo(df_resumen):
    """
    Muestra análisis de probabilidad de profit y simulaciones Monte Carlo.
    Incluye botones de compra/venta y explicaciones.
    """
    st.subheader("🎯 Análisis de Probabilidad de Profit y Simulación Monte Carlo")
    st.markdown("""
    <div style='background: #1565c0; color: #fff; border-radius: 10px; padding: 10px; margin-bottom: 10px;'>
    <b>¿Qué muestra este gráfico?</b><br>
    Cada punto representa una opción. El eje X indica la probabilidad de obtener ganancia (según simulación Monte Carlo), el eje Y la ganancia esperada.<br>
    <b>Haz clic en un punto para ver detalles y operar.</b>
    </div>
    """, unsafe_allow_html=True)

    if df_resumen.empty:
        st.info("No hay datos de opciones para mostrar.")
        return

    df_mc = df_resumen.dropna(subset=['MC_ProbProfit', 'MC_GananciaEsperada'])
    if df_mc.empty:
        st.warning("No hay datos de Monte Carlo disponibles.")
        return

    tab1, tab2 = st.tabs(["🎲 Simulación Individual", "📈 Análisis Comparativo"])

    with tab1:
        st.markdown("#### 🎲 Simulación Monte Carlo Individual")
        # --- Menús dependientes: tipo -> vencimiento -> strike ---
        tipos = df_mc['tipoOpcion'].dropna().unique().tolist()
        tipo_sel = st.selectbox("Tipo de opción", tipos, key="mc_tipo_opcion_sim_indiv")

        # Solo mostrar vencimientos disponibles para el tipo seleccionado
        df_tipo = df_mc[df_mc['tipoOpcion'] == tipo_sel]
        vencimientos = df_tipo['fechaVencimiento'].dropna().unique().tolist()
        vencimientos = sorted(vencimientos)
        venc_sel = st.selectbox("Vencimiento", vencimientos, key=f"mc_venc_sim_indiv_{tipo_sel}")

        # Solo mostrar strikes disponibles para el tipo y vencimiento seleccionados
        df_venc = df_tipo[df_tipo['fechaVencimiento'] == venc_sel].copy()
        
        # Calcular distancia al precio actual para ordenar los strikes por cercanía
        if not df_venc.empty and 'precioSubyacente' in df_venc.columns:
            precio_actual = df_venc['precioSubyacente'].iloc[0]
            df_venc['distancia'] = abs(df_venc['strike'] - precio_actual)
            df_venc = df_venc.sort_values('distancia')
        
        # Mostrar información de precios actuales
        if not df_venc.empty and 'precioSubyacente' in df_venc.columns:
            precio_actual = df_venc['precioSubyacente'].iloc[0]
            st.markdown(f"**Precio actual del subyacente:** :green[${precio_actual:,.2f}]", help="Precio de mercado actual del activo subyacente")
        
        strikes = df_venc['strike'].dropna().unique().tolist()
        
        # Crear lista de opciones con precios para el selectbox
        opciones_strike = []
        for strike in strikes:
            df_strike_temp = df_venc[df_venc['strike'] == strike]
            if not df_strike_temp.empty:
                precio_prima = df_strike_temp['precioOpcion'].iloc[0]
                opciones_strike.append(f"${strike:,.2f} (Prima: ${precio_prima:,.2f})")
        
        # Mostrar selectbox con precios de prima
        if opciones_strike:
            strike_idx = st.selectbox(
                "Seleccionar Strike (con prima actual):",
                range(len(opciones_strike)),
                format_func=lambda x: opciones_strike[x],
                key=f"mc_strike_sim_indiv_{tipo_sel}_{venc_sel}"
            )
            strike_sel = strikes[strike_idx]
        else:
            st.warning("No hay strikes disponibles para la selección actual")
            return
        
        df_strike = df_venc[df_venc['strike'] == strike_sel]

        # Inputs para contratos y simulaciones (usar claves únicas por contexto)
        col_inputs = st.columns(3)
        with col_inputs[0]:
            cantidad_contratos = st.number_input("Cantidad de contratos", min_value=1, max_value=10000, value=1, step=1, key=f"mc_cant_contr_{tipo_sel}_{venc_sel}_{strike_sel}")
        with col_inputs[1]:
            n_sim = st.number_input("Cantidad de simulaciones", min_value=1000, max_value=int(1e12), value=10000, step=1000, key=f"mc_nsim_{tipo_sel}_{venc_sel}_{strike_sel}", format="%i")
        with col_inputs[2]:
            comision = 0.0
            if not df_strike.empty:
                row_tmp = df_strike.iloc[0]
                comision = obtener_comision_operacion(
                    st.session_state.token_portador,
                    CONFIG['mercado'],
                    row_tmp['simbolo'] if 'simbolo' in row_tmp else row_tmp.get('descripcion', ''),
                    int(cantidad_contratos),
                    float(row_tmp['precioOpcion'])
                )
            st.number_input("Comisión total ($)", min_value=0.0, value=comision, step=1.0, key=f"mc_comision_{tipo_sel}_{venc_sel}_{strike_sel}", disabled=True)

        # Seleccionar la fila correspondiente
        if not df_strike.empty:
            row_seleccionada = df_strike.iloc[0]
            # Obtener comisión actualizada para la selección
            comision = obtener_comision_operacion(
                st.session_state.token_portador,
                CONFIG['mercado'],
                row_seleccionada['simbolo'] if 'simbolo' in row_seleccionada else row_seleccionada.get('descripcion', ''),
                int(cantidad_contratos),
                float(row_seleccionada['precioOpcion'])
            )

            # Calcular inversión inicial
            inversion_inicial = row_seleccionada['precioOpcion'] * cantidad_contratos + comision

            prob_profit, payoffs = calcular_probabilidad_profit_montecarlo(row_seleccionada, n_sim=int(n_sim))
            if prob_profit is not None and payoffs is not None:
                # Calcular payoffs totales considerando contratos y comisión
                payoffs_total = payoffs * cantidad_contratos - comision

                # Mostrar precio de la prima de la opción
                st.markdown(f"**Prima de la opción:** :orange[${row_seleccionada['precioOpcion']:.2f}]")
                st.markdown(f"**Inversión inicial (prima x contratos + comisión):** :orange[${inversion_inicial:,.2f}]")
                st.markdown(f"**Comisión considerada:** :orange[${comision:,.2f}]")
                # --- NUEVO: Estado ITM/OTM/ATM ---
                estado_opcion = "N/A"
                if (
                    pd.notnull(row_seleccionada.get('tipoOpcion')) and
                    pd.notnull(row_seleccionada.get('strike')) and
                    pd.notnull(row_seleccionada.get('precioSubyacente'))
                ):
                    if row_seleccionada['tipoOpcion'] == 'Call':
                        if row_seleccionada['precioSubyacente'] > row_seleccionada['strike']:
                            estado_opcion = "ITM"
                        elif row_seleccionada['precioSubyacente'] < row_seleccionada['strike']:
                            estado_opcion = "OTM"
                        else:
                            estado_opcion = "ATM"
                    elif row_seleccionada['tipoOpcion'] == 'Put':
                        if row_seleccionada['precioSubyacente'] < row_seleccionada['strike']:
                            estado_opcion = "ITM"
                        elif row_seleccionada['precioSubyacente'] > row_seleccionada['strike']:
                            estado_opcion = "OTM"
                        else:
                            estado_opcion = "ATM"

                st.markdown(f"**Estado de la opción:** :blue[{estado_opcion}]")

                # Mostrar métricas de la simulación
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Probabilidad de Profit", f"{prob_profit:.2%}")
                with col2:
                    ganancia_esperada = np.mean(payoffs_total)
                    st.metric("Ganancia Esperada", f"${ganancia_esperada:.2f}")
                with col3:
                    max_ganancia = np.max(payoffs_total)
                    st.metric("Máxima Ganancia", f"${max_ganancia:.2f}")
                with col4:
                    max_perdida = np.min(payoffs_total)
                    st.metric("Máxima Pérdida", f"${max_perdida:.2f}")

                # Histograma de payoffs
                fig = graficar_histograma_montecarlo(
                    payoffs_total, 
                    row_seleccionada['tipoOpcion'], 
                    row_seleccionada['strike'], 
                    row_seleccionada['precioOpcion']
                )
                st.plotly_chart(fig, use_container_width=True)

                # Estadísticas adicionales
                st.markdown("##### 📈 Estadísticas Detalladas")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Percentil 5%:** ${np.percentile(payoffs_total, 5):.2f}")
                    st.write(f"**Percentil 25%:** ${np.percentile(payoffs_total, 25):.2f}")
                    st.write(f"**Mediana:** ${np.percentile(payoffs_total, 50):.2f}")
                with col2:
                    st.write(f"**Percentil 75%:** ${np.percentile(payoffs_total, 75):.2f}")
                    st.write(f"**Percentil 95%:** ${np.percentile(payoffs_total, 95):.2f}")
                    st.write(f"**Desviación Estándar:** ${np.std(payoffs_total):.2f}")
            else:
                st.error("No se pudo calcular la simulación Monte Carlo para esta opción.")
        else:
            st.info("No hay opción disponible con la combinación seleccionada.")

    with tab2:
        st.markdown("#### 📈 Análisis Comparativo")
        st.info(
            "En este gráfico, cada punto es una opción. "
            "El eje X es la probabilidad de obtener ganancia (Monte Carlo), el eje Y la ganancia esperada. "
            "El símbolo de la opción aparece en el tooltip. "
            "Puedes operar directamente desde aquí."
        )

        fig = go.Figure()
        hover_texts = []
        for tipo in ['Call', 'Put']:
            df_tipo = df_mc[df_mc['tipoOpcion'] == tipo]
            if not df_tipo.empty:
                hover_text = (
                    df_tipo.apply(
                        lambda r: f"Símbolo: {r['simbolo']}<br>Strike: {r['strike']}<br>Vencimiento: {r['fechaVencimiento']}<br>Tipo: {r['tipoOpcion']}", axis=1
                    )
                )
                hover_texts.append(hover_text)
                fig.add_trace(go.Scatter(
                    x=df_tipo['MC_ProbProfit'],
                    y=df_tipo['MC_GananciaEsperada'],
                    mode='markers',
                    name=f'{tipo}s',
                    marker=dict(
                        size=12,
                        opacity=0.8,
                        symbol='triangle-up' if tipo == 'Call' else 'triangle-down'
                    ),
                    text=hover_text,
                    customdata=df_tipo.index,
                    hovertemplate='%{text}<br>Prob. Profit: %{x:.1%}<br>Ganancia Esperada: $%{y:.2f}<extra></extra>'
                ))

        fig.update_layout(
            title="Probabilidad de Profit vs Ganancia Esperada (Monte Carlo)",
            xaxis_title="Probabilidad de Profit",
            yaxis_title="Ganancia Esperada ($)",
            template="plotly_white",
            height=550
        )
        fig.update_xaxes(tickformat='.1%')
        selected = st.plotly_chart(fig, use_container_width=True, selection_mode="single")

        # Explicación adicional
        st.markdown("""
        <div style='background: #2d2d2d; color: #ffffff; border-radius: 10px; padding: 15px; margin-top: 15px;'>
        <b>Teoría:</b> <br>
        La probabilidad de profit se estima simulando miles de escenarios posibles para el precio del activo subyacente al vencimiento de la opción. 
        La ganancia esperada es el promedio de los resultados de esas simulaciones, considerando el costo de la prima.
        </div>
        """, unsafe_allow_html=True)

def operar_compra(token_portador, mercado, simbolo, cantidad, precio, monto=0, plazo="t0", tipoOrden="precioLimite", idFuente=0):
    """
    Realiza una orden de compra usando la API de InvertirOnline.
    """
    url = "https://api.invertironline.com/api/v2/operar/Comprar"
    headers = {
        "Authorization": f"Bearer {token_portador}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    validez = (datetime.now() + timedelta(minutes=10)).isoformat()
    data = {
        "mercado": mercado,
        "simbolo": simbolo,
        "cantidad": cantidad,
        "precio": precio,
        "plazo": plazo,
        "validez": validez,
        "tipoOrden": tipoOrden,
        "monto": monto,
        "idFuente": idFuente
    }
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(data))
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"ok": False, "messages": [{"title": "Error", "description": resp.text}]}
    except Exception as e:
        return {"ok": False, "messages": [{"title": "Error", "description": str(e)}]}

def operar_venta(token_portador, mercado, simbolo, cantidad, precio, plazo="t0", tipoOrden="precioLimite", idFuente=0):
    """
    Realiza una orden de venta usando la API de InvertirOnline.
    Usa formato x-www-form-urlencoded como requiere la documentación oficial.
    """
    url = "https://api.invertironline.com/api/v2/operar/Vender"
    headers = {
        "Authorization": f"Bearer {token_portador}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    validez = (datetime.now() + timedelta(minutes=10)).isoformat()
    data = {
        "mercado": mercado,
        "simbolo": simbolo,
        "cantidad": cantidad,
        "precio": precio,
        "plazo": plazo,
        "validez": validez,
        "tipoOrden": tipoOrden
    }
    try:
        resp = requests.post(url, headers=headers, data=data)
        if resp.status_code in (200, 201):
            return resp.json()
        else:
            return {"ok": False, "messages": [{"title": "Error", "description": resp.text}]}
    except Exception as e:
        return {"ok": False, "messages": [{"title": "Error", "description": str(e)}]}

def operar_token(token_portador, mercado, simbolo, cantidad, monto):
    """
    Solicita un token de operación usando la API de InvertirOnline.
    """
    url = "https://api.invertironline.com/api/v2/operar/Token"
    headers = {
        "Authorization": f"Bearer {token_portador}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "mercado": mercado,
        "simbolo": simbolo,
        "cantidad": cantidad,
        "monto": monto
    }
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(data))
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"ok": False, "messages": [{"title": "Error", "description": resp.text}]}
    except Exception as e:
        return {"ok": False, "messages": [{"title": "Error", "description": str(e)}]}

def obtener_comision_operacion(token_portador, mercado, simbolo, cantidad, precio):
    """
    Obtiene la comisión estimada para una operación desde la API de InvertirOnline.
    """
    url = "https://api.invertironline.com/api/v2/operar/Comisiones"
    headers = {
        "Authorization": f"Bearer {token_portador}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "mercado": mercado,
        "simbolo": simbolo,
        "cantidad": cantidad,
        "precio": precio
    }
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(data))
        if resp.status_code == 200:
            res = resp.json()
            # Buscar la comisión total (puede variar según el formato de respuesta)
            if isinstance(res, dict):
                # Ejemplo: {'comisionTotal': 123.45, ...}
                if 'comisionTotal' in res:
                    return float(res['comisionTotal'])
                # Ejemplo alternativo: lista de comisiones
                if 'comisiones' in res and isinstance(res['comisiones'], list):
                    return sum(float(c.get('importe', 0)) for c in res['comisiones'])
            return 0.0
        else:
            return 0.0
    except Exception:
        return 0.0

def obtener_tasas_caucion(token_portador):
    """
    Obtiene las tasas de caución (tasas de interés) desde la API de InvertirOnline.
    
    Args:
        token_portador: Token de autenticación para la API.
        
    Returns:
        dict: Diccionario con las tasas de caución, o None si hay un error.
    """
    url = "https://api.invertironline.com/api/v2/Cotizaciones/cauciones/argentina"
    headers = {
        "Authorization": f"Bearer {token_portador}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error al obtener tasas de caución: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al obtener tasas de caución: {str(e)}")
        return None
    except Exception as e:
        print(f"Error inesperado al obtener tasas de caución: {str(e)}")
        return None

def calcular_sesgo(df_procesado, precio_spot):
    """
    Calcula el sesgo del mercado basado en la volatilidad implícita de calls y puts.
    
    Args:
        df_procesado: DataFrame con las opciones procesadas
        precio_spot: Precio actual del subyacente
        
    Returns:
        tuple: (valor del sesgo, tipo de sesgo)
    """
    if df_procesado.empty or 'volatilidadImplicita' not in df_procesado.columns:
        return (0, "Neutro")

    # Filtrar opciones válidas
    df_vol = df_procesado.dropna(subset=['volatilidadImplicita', 'strike', 'tipoOpcion'])
    if df_vol.empty:
        return (0, "Neutro")

    # Identificar opciones cerca del dinero (ATM)
    df_vol['distancia_atm'] = abs(df_vol['strike'] - precio_spot)
    atm_threshold = df_vol['distancia_atm'].quantile(0.2)  # Considerar el 20% más cercano como ATM
    df_atm = df_vol[df_vol['distancia_atm'] <= atm_threshold]

    # Separar calls y puts
    calls_atm = df_atm[df_atm['tipoOpcion'] == 'Call']
    puts_atm = df_atm[df_atm['tipoOpcion'] == 'Put']

    if calls_atm.empty or puts_atm.empty:
        return (0, "Neutro")

    # Calcular volatilidad promedio para cada tipo
    vol_calls = calls_atm['volatilidadImplicita'].mean()
    vol_puts = puts_atm['volatilidadImplicita'].mean()

    # Calcular el sesgo
    sesgo = vol_puts - vol_calls

    # Determinar tipo de sesgo
    if abs(sesgo) < 0.05:  # Umbral de 5%
        tipo_sesgo = "Neutro"
    elif sesgo > 0:
        tipo_sesgo = "Alcista"
    else:
        tipo_sesgo = "Bajista"

    return (sesgo, tipo_sesgo)

def calcular_var_opciones(df):
    """
    Calcula el Value at Risk (VaR) para cada opción en el DataFrame.
    Usa la aproximación delta-gamma.
    
    Args:
        df: DataFrame con las opciones procesadas
        
    Returns:
        DataFrame: El mismo DataFrame con una columna adicional 'VaR'
    """
    if df.empty:
        return df

    # Verificar que las columnas necesarias existan
    required_cols = ['Delta', 'Gamma', 'precioSubyacente', 'volatilidadImplicita']
    if not all(col in df.columns for col in required_cols):
        # Agregar columna VaR con valores nulos si faltan columnas requeridas
        df['VaR'] = None
        return df

    # Parámetros para el cálculo del VaR
    confianza = 0.95  # Nivel de confianza (95%)
    dias = 1  # Horizonte temporal (1 día)

    # Factor Z para el nivel de confianza (distribución normal)
    z = norm.ppf(confianza)

    # Calcular VaR para cada opción
    def calcular_var_opcion(row):
        try:
            # Verificar valores requeridos
            if pd.isnull(row['Delta']) or pd.isnull(row['Gamma']) or pd.isnull(row['precioSubyacente']) or pd.isnull(row['volatilidadImplicita']):
                return None

            # Parámetros
            S = row['precioSubyacente']
            sigma = row['volatilidadImplicita']
            delta = row['Delta']
            gamma = row['Gamma']

            # Cálculo del VaR delta-gamma
            volatilidad_diaria = sigma / np.sqrt(252)
            cambio_precio = S * volatilidad_diaria * z * np.sqrt(dias)

            # Componente delta
            var_delta = abs(delta * cambio_precio)

            # Componente gamma (corrección de segundo orden)
            var_gamma = 0.5 * gamma * cambio_precio**2

            # VaR total (considerando ambos componentes)
            var_total = var_delta + var_gamma

            return var_total

        except Exception as e:
            return None

    # Aplicar la función a cada fila
    df['VaR'] = df.apply(calcular_var_opcion, axis=1)

    return df

def obtener_dividendos_splits():
    """
    Obtiene información de dividendos y splits para el símbolo configurado.
    
    Returns:
        tuple: (DataFrame con dividendos, total de dividendos esperados)
    """
    # Crear DataFrame vacío para dividendos
    df_dividendos = pd.DataFrame(columns=['fecha', 'monto'])
    total_dividendos = 0.0

    # En una implementación real, esto obtendría los datos de una API
    # Para este ejemplo, devolvemos un DataFrame vacío
    return df_dividendos, total_dividendos

# --- INICIO: Código original sin cambios ---

if __name__ == "__main__":
    try:
        # Intentar ejecutar como web
        main_streamlit()
    except Exception as e:
        print("No se pudo ejecutar la web de Streamlit. Ejecutando en modo consola básico.")
        # Configuración manual para consola
        CONFIG['simbolo'] = seleccionar_subyacente()
        
        # Obtener tasa de caución
        tasa_caucion = obtener_tasas_caucion(productor_token)
        if tasa_caucion and 'titulos' in tasa_caucion:
            df_tasas = pd.DataFrame(tasa_caucion['titulos'])
            if not df_tasas.empty and 'tasaPromedio' in df_tasas.columns:
                CONFIG['tasa_riesgo'] = df_tasas['tasaPromedio'].max() / 100
                CONFIG['tasa_riesgo'] = df_tasas['tasaPromedio'].mean() / 100  # Cambiado de max() a mean()
            else:
                CONFIG['tasa_riesgo'] = 0.05
        else:
            CONFIG['tasa_riesgo'] = 0.05

        # Obtener datos del subyacente (usando versión cacheada)
        precio_spot, vol_hist, vol_din, hist_vol = obtener_datos_subyacente_cacheado(CONFIG['simbolo'], CONFIG['vol_periodo'])
        if not precio_spot:
            print("No se pudieron obtener datos del subyacente")
            exit(1)

        # Obtener dividendos
        df_div, total_div = obtener_dividendos_splits()
        tasa_div = (total_div / precio_spot) if precio_spot and total_div > 0 else 0

        df_api = obtener_datos_api()
        if df_api.empty:
            print("No se pudieron obtener datos de opciones")
            exit(1)

        df_procesado = procesar_dataframe(df_api, precio_spot, vol_hist, vol_din, tasa_div, hist_vol)
        df_procesado = calcular_var_opciones(df_procesado)
        df_resumen = crear_df_resumen(df_procesado)
        
        # Mostrar análisis de probabilidad y gráficos
        mostrar_probabilidad_profit_y_montecarlo(df_resumen)
        graficar_volatilidad_implícita(df_resumen, hist_vol)
        graficar_probabilidad_itm(df_resumen)
