# -*- coding: utf-8 -*-

"""
================================================================================
IOL PORTFOLIO ANALYZER - VERSIÓN MEJORADA
================================================================================
Autor: Gemini
Fecha: 27 de Agosto de 2025

Descripción:
Aplicación Streamlit para visualizar y analizar portafolios de inversión
de InvertirOnline (IOL), diseñada para asesores financieros.
Esta versión ha sido completamente refactorizada para mejorar la estructura,
rendimiento, robustez y experiencia de usuario.

Principales mejoras:
- Lógica de API encapsulada en la clase IOLApiClient.
- Manejo de errores centralizado con reintentos y backoff exponencial.
- Uso intensivo de caché (@st.cache_data) para optimizar el rendimiento.
- Interfaz de usuario completa con login, selección de cliente y pestañas.
- Módulo de análisis avanzado con cálculo de Frontera Eficiente.
- Código modular, limpio y bien documentado.
================================================================================
"""

# ------------------------------------------------------------------------------
# 1. IMPORTACIONES Y CONFIGURACIÓN INICIAL
# ------------------------------------------------------------------------------
import streamlit as st
import requests
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import scipy.optimize as sco
from datetime import date, timedelta, datetime
import time
import warnings

# Ignorar advertencias comunes que no afectan la ejecución
warnings.filterwarnings('ignore', category=FutureWarning)

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="IOL Portfolio Analyzer Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ------------------------------------------------------------------------------
# 2. CLIENTE DE API (IOL API CLIENT)
# ------------------------------------------------------------------------------

class IOLApiClient:
    """
    Cliente encapsulado para manejar todas las interacciones con la API de IOL.
    Gestiona la autenticación, sesión de requests, reintentos y formateo de llamadas.
    """
    BASE_URL = 'https://api.invertironline.com'

    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._access_token = None
        self._refresh_token = None
        self._session = self._create_session()

    def _create_session(self):
        """Crea una sesión de requests con una estrategia de reintentos."""
        session = requests.Session()
        retries = requests.adapters.Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=retries))
        return session

    def _authenticate(self):
        """Obtiene los tokens de acceso y refresco."""
        url = f"{self.BASE_URL}/token"
        data = {
            'username': self._username,
            'password': self._password,
            'grant_type': 'password'
        }
        try:
            response = self._session.post(url, data=data, timeout=20)
            response.raise_for_status()  # Lanza un error para códigos 4xx/5xx
            tokens = response.json()
            if 'access_token' in tokens and 'refresh_token' in tokens:
                self._access_token = tokens['access_token']
                self._refresh_token = tokens['refresh_token']
                return True
            else:
                st.error("❌ Respuesta de autenticación incompleta desde IOL.")
                return False
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [400, 401]:
                st.error("❌ Credenciales incorrectas. Por favor, verifique su usuario y contraseña.")
            else:
                st.error(f"❌ Error de autenticación HTTP: {e.response.status_code}")
            return False
        except (requests.exceptions.RequestException, Exception) as e:
            st.error(f"🔌 Error de conexión al autenticar: {e}")
            return False

    def _make_request(self, method, endpoint, **kwargs):
        """Realiza una petición a la API, manejando la autenticación."""
        if not self._access_token and not self._authenticate():
            return None  # Falla si la autenticación inicial no funciona

        url = f"{self.BASE_URL}{endpoint}"
        headers = {'Authorization': f'Bearer {self._access_token}'}
        
        try:
            response = self._session.request(method, url, headers=headers, timeout=20, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ Error en la petición a la API ({e.response.status_code}): {endpoint}")
            return None
        except (requests.exceptions.RequestException, Exception) as e:
            st.error(f"🔌 Error de conexión en la petición: {e}")
            return None

    def get_client_list(self):
        """Obtiene la lista de clientes del asesor."""
        return self._make_request('get', '/api/v2/Asesores/Clientes')

    def get_portfolio(self, client_id, country='Argentina'):
        """Obtiene el portafolio de un cliente específico."""
        return self._make_request('get', f'/api/v2/Asesores/Portafolio/{client_id}/{country}')

    def get_us_portfolio(self, client_id):
        """Obtiene el portafolio de USA de un cliente."""
        # Nota: La API original parecía tener endpoints separados. Unificamos a un solo método.
        return self.get_portfolio(client_id, country='EstadosUnidos')


# ------------------------------------------------------------------------------
# 3. LÓGICA DE ANÁLISIS FINANCIERO
# ------------------------------------------------------------------------------

@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_historical_data(tickers, start_date, end_date):
    """Descarga datos históricos de precios de cierre para una lista de tickers."""
    if not tickers:
        st.warning("⚠️ No se proporcionaron tickers para descargar.")
        return pd.DataFrame()
    
    try:
        # Filtrar tickers vacíos o None
        valid_tickers = [t for t in tickers if t and str(t).strip()]
        if not valid_tickers:
            st.warning("⚠️ No hay tickers válidos para descargar.")
            return pd.DataFrame()
        
        if st.session_state.get('debug_enabled', False):
            st.write(f"Intentando descargar datos para: {valid_tickers}")
        
        data = yf.download(valid_tickers, start=start_date, end=end_date, progress=False)
        
        if data.empty:
            st.warning("⚠️ No se obtuvieron datos de Yahoo Finance.")
            return pd.DataFrame()
        
        # Verificar que tenemos la columna 'Adj Close'
        if 'Adj Close' not in data.columns:
            st.warning("⚠️ Los datos no contienen precios ajustados.")
            if st.session_state.get('debug_enabled', False):
                st.write("Columnas disponibles:", data.columns.tolist())
            return pd.DataFrame()
        
        adj_close_data = data['Adj Close']
        # Eliminar activos sin datos
        clean_data = adj_close_data.dropna(axis=1, how='any')
        
        if clean_data.empty:
            st.warning("⚠️ No hay datos válidos después de limpiar valores faltantes.")
            return pd.DataFrame()
        
        if st.session_state.get('debug_enabled', False):
            st.write(f"Datos descargados exitosamente para {len(clean_data.columns)} activos")
        
        return clean_data
        
    except Exception as e:
        st.error(f"❌ Error al descargar datos históricos: {e}")
        if st.session_state.get('debug_enabled', False):
            st.write("Tickers intentados:", tickers)
            st.write("Fechas:", start_date, "a", end_date)
        return pd.DataFrame()

def calculate_portfolio_stats(weights, returns):
    """Calcula el rendimiento, volatilidad y Sharpe ratio anualizados."""
    try:
        weights = np.array(weights)
        
        # Verificar que tenemos datos válidos
        if returns is None or returns.empty:
            raise ValueError("No hay datos de retornos para calcular estadísticas")
        
        if len(weights) != len(returns.columns):
            raise ValueError(f"El número de pesos ({len(weights)}) no coincide con el número de activos ({len(returns.columns)})")
        
        # Calcular estadísticas
        pret = np.sum(returns.mean() * weights) * 252
        pvol = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
        
        # Evitar división por cero
        if pvol == 0:
            pvol = 1e-6  # Valor muy pequeño para evitar división por cero
        
        sharpe_ratio = pret / pvol
        
        return np.array([pret, pvol, sharpe_ratio])
        
    except Exception as e:
        st.error(f"❌ Error al calcular estadísticas del portafolio: {e}")
        if st.session_state.get('debug_enabled', False):
            st.write("Pesos:", weights)
            st.write("Retornos:", returns)
        raise

def optimize_portfolio(returns):
    """
    Realiza la optimización de la cartera para encontrar la Frontera Eficiente,
    el portafolio de máxima Sharpe y el de mínima volatilidad.
    """
    try:
        # Verificar que tenemos datos válidos
        if returns is None or returns.empty:
            raise ValueError("No hay datos de retornos para optimizar")
        
        if len(returns.columns) < 2:
            raise ValueError("Se requieren al menos 2 activos para la optimización")
        
        num_assets = len(returns.columns)
        args = (returns,)
        
        # Restricciones: la suma de los pesos debe ser 1
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        # Límites: los pesos deben estar entre 0 y 1
        bounds = tuple((0, 1) for _ in range(num_assets))
        # Pesos iniciales iguales
        initial_guess = num_assets * [1. / num_assets,]
    except Exception as e:
        st.error(f"❌ Error en la preparación de la optimización: {e}")
        if st.session_state.get('debug_enabled', False):
            st.write("Datos de retornos:", returns)
        raise

    # 1. Maximizar Sharpe Ratio
    try:
        # Función a minimizar: -Sharpe Ratio
        def neg_sharpe_ratio(weights, returns):
            return -calculate_portfolio_stats(weights, returns)[2]
            
        max_sharpe_result = sco.minimize(neg_sharpe_ratio, initial_guess, args=args,
                                         method='SLSQP', bounds=bounds, constraints=constraints)
        
        if not max_sharpe_result.success:
            st.warning("⚠️ La optimización de máximo Sharpe no convergió correctamente.")
            if st.session_state.get('debug_enabled', False):
                st.write("Resultado de optimización:", max_sharpe_result)
        
        max_sharpe_weights = max_sharpe_result.x
        max_sharpe_stats = calculate_portfolio_stats(max_sharpe_weights, returns)
    except Exception as e:
        st.error(f"❌ Error en la optimización de máximo Sharpe: {e}")
        raise

    # 2. Minimizar Volatilidad
    try:
        # Función a minimizar: volatilidad
        def portfolio_volatility(weights, returns):
            return calculate_portfolio_stats(weights, returns)[1]

        min_vol_result = sco.minimize(portfolio_volatility, initial_guess, args=args,
                                      method='SLSQP', bounds=bounds, constraints=constraints)
        
        if not min_vol_result.success:
            st.warning("⚠️ La optimización de mínima volatilidad no convergió correctamente.")
            if st.session_state.get('debug_enabled', False):
                st.write("Resultado de optimización:", min_vol_result)
        
        min_vol_weights = min_vol_result.x
        min_vol_stats = calculate_portfolio_stats(min_vol_weights, returns)
    except Exception as e:
        st.error(f"❌ Error en la optimización de mínima volatilidad: {e}")
        raise
    
    # 3. Simular portafolios para la Frontera Eficiente
    try:
        port_returns = []
        port_volatility = []
        for _ in range(2500):
            weights = np.random.random(num_assets)
            weights /= np.sum(weights)
            stats = calculate_portfolio_stats(weights, returns)
            port_returns.append(stats[0])
            port_volatility.append(stats[1])
    except Exception as e:
        st.error(f"❌ Error en la simulación de portafolios: {e}")
        # Usar valores por defecto si falla la simulación
        port_returns = [0.1, 0.15, 0.2]
        port_volatility = [0.15, 0.2, 0.25]
        
    return {
        'max_sharpe_stats': max_sharpe_stats,
        'max_sharpe_weights': max_sharpe_weights,
        'min_vol_stats': min_vol_stats,
        'min_vol_weights': min_vol_weights,
        'simulation': (port_returns, port_volatility)
    }


# ------------------------------------------------------------------------------
# 4. FUNCIONES DE INTERFAZ DE USUARIO (UI)
# ------------------------------------------------------------------------------

def load_custom_css():
    """Carga los estilos CSS personalizados para un tema oscuro profesional."""
    st.markdown("""
    <style>
        /* [EL MISMO CSS QUE PROVEÍSTE, PERO UNA SOLA VEZ Y ENCAPSULADO] */
        /* ... (Tu bloque CSS va aquí, lo he omitido por brevedad) ... */
        /* Asegúrate de copiar y pegar tu bloque <style> completo aquí */
        .stApp {
            background-color: #0f172a !important;
            color: #f8f9fa !important;
        }
        h1, h2, h3 {
            color: #4CAF50;
        }
        .stButton>button {
            border-radius: 8px;
            font-weight: 500;
            background-color: #4CAF50;
            color: white;
            border: none;
        }
        [data-testid="stMetric"] {
            background-color: #1e293b;
            border-left: 5px solid #4CAF50;
            border-radius: 8px;
            padding: 15px;
        }
        [data-baseweb="tab"][aria-selected="true"] {
            background-color: #4CAF50 !important;
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)


def display_portfolio(portfolio_data):
    """Muestra el portafolio en un formato de tabla y gráfico."""
    if not portfolio_data:
        st.warning("⚠️ No se recibieron datos del portafolio.")
        return None
    
    # Debug: mostrar estructura de datos si está habilitado
    if st.session_state.get('debug_enabled', False):
        st.write("Estructura del portafolio:", portfolio_data)
    
    # Intentar diferentes estructuras de datos comunes
    assets = []
    
    # Estructura 1: activos directos
    if 'activos' in portfolio_data and portfolio_data['activos']:
        try:
            for a in portfolio_data['activos']:
                asset = {
                    'Símbolo': a.get('simbolo', a.get('symbol', a.get('ticker', 'N/A'))),
                    'Cantidad': a.get('cantidad', a.get('quantity', a.get('amount', 0))),
                    'Valorizado ($)': a.get('monto', a.get('amount', a.get('value', 0))),
                    'Moneda': a.get('moneda', a.get('currency', 'ARS')),
                    'Tipo': a.get('titulo', {}).get('tipo', a.get('type', 'N/A')) if isinstance(a.get('titulo'), dict) else a.get('type', 'N/A')
                }
                assets.append(asset)
        except Exception as e:
            st.warning(f"⚠️ Error procesando estructura 'activos': {e}")
    
    # Estructura 2: activos en diferentes campos
    elif 'assets' in portfolio_data and portfolio_data['assets']:
        try:
            for a in portfolio_data['assets']:
                asset = {
                    'Símbolo': a.get('symbol', a.get('ticker', 'N/A')),
                    'Cantidad': a.get('quantity', a.get('amount', 0)),
                    'Valorizado ($)': a.get('value', a.get('amount', 0)),
                    'Moneda': a.get('currency', 'ARS'),
                    'Tipo': a.get('type', 'N/A')
                }
                assets.append(asset)
        except Exception as e:
            st.warning(f"⚠️ Error procesando estructura 'assets': {e}")
    
    # Estructura 3: datos directos (sin anidación)
    elif isinstance(portfolio_data, list):
        try:
            for a in portfolio_data:
                asset = {
                    'Símbolo': a.get('simbolo', a.get('symbol', a.get('ticker', 'N/A'))),
                    'Cantidad': a.get('cantidad', a.get('quantity', a.get('amount', 0))),
                    'Valorizado ($)': a.get('monto', a.get('amount', a.get('value', 0))),
                    'Moneda': a.get('moneda', a.get('currency', 'ARS')),
                    'Tipo': a.get('tipo', a.get('type', 'N/A'))
                }
                assets.append(asset)
        except Exception as e:
            st.warning(f"⚠️ Error procesando estructura de lista: {e}")
    
    if not assets:
        st.warning("⚠️ No se pudieron procesar los datos del portafolio.")
        st.write("Datos recibidos:", portfolio_data)
        return None
    df = pd.DataFrame(assets)
    
    # Verificar que tenemos datos válidos
    if df.empty:
        st.warning("⚠️ No se pudieron procesar activos del portafolio.")
        return None
    
    # Filtrar activos sin valor, pero manejar casos donde el valor puede ser 0 o None
    try:
        df = df[df['Valorizado ($)'] > 0]
    except Exception as e:
        st.warning(f"⚠️ Error al filtrar activos por valor: {e}")
        # Si hay error en el filtro, mostrar todos los activos
        pass

    if df.empty:
        st.warning("⚠️ No hay activos valorizados en el portafolio.")
        return None

    total_value = df['Valorizado ($)'].sum()

    st.subheader("Composición del Portafolio")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.metric(label="Valor Total del Portafolio", value=f"${total_value:,.2f}")
        df['Ponderación (%)'] = (df['Valorizado ($)'] / total_value) * 100
        
        styled_df = df[['Símbolo', 'Cantidad', 'Valorizado ($)', 'Ponderación (%)', 'Tipo']].style.format({
            'Valorizado ($)': '${:,.2f}',
            'Ponderación (%)': '{:.2f}%',
            'Cantidad': '{:,.2f}'
        }).highlight_max(subset=['Ponderación (%)'], color='#4CAF50', axis=0)
        
        st.dataframe(styled_df, use_container_width=True)

    with col2:
        try:
            fig = go.Figure(data=[go.Pie(
                labels=df['Símbolo'],
                values=df['Valorizado ($)'],
                hole=.4,
                textinfo='percent+label',
                marker_colors=go.layout.Colorscale(colors=['#4CAF50', '#8BC34A', '#CDDC39', '#FFEB3B', '#FFC107'])
            )])
            fig.update_layout(
                title_text='Distribución de Activos',
                template='plotly_dark',
                legend_title_text='Activos'
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"⚠️ Error al crear el gráfico: {e}")
            if st.session_state.get('debug_enabled', False):
                st.write("Datos del DataFrame:", df)
    
    return df


def display_optimization_analysis(portfolio_df):
    """Muestra la sección de análisis y optimización de la cartera."""
    st.subheader("🔬 Análisis y Optimización de la Cartera")

    # Verificar que tenemos datos válidos
    if portfolio_df is None or portfolio_df.empty:
        st.warning("⚠️ No hay datos de portafolio para analizar.")
        return
    
    try:
        # Verificar que tenemos la columna Símbolo
        if 'Símbolo' not in portfolio_df.columns:
            st.error("❌ El DataFrame no contiene la columna 'Símbolo' requerida.")
            if st.session_state.get('debug_enabled', False):
                st.write("Columnas disponibles:", portfolio_df.columns.tolist())
            return
        
        # Mapeo de tickers IOL a Yahoo Finance (esto puede necesitar ajustes)
        ticker_map = {
            'GGAL': 'GGAL.BA', 'YPFD': 'YPFD.BA', 'PAMP': 'PAMP.BA',
            'AAPL': 'AAPL', 'GOOGL': 'GOOGL', 'MSFT': 'MSFT', 'KO': 'KO',
            'GD30': 'GD30.BA' # Ejemplo para bonos, puede que no haya datos en YF
        }
        
        # Añadimos un sufijo '.BA' a los tickers argentinos para yfinance
        tickers_to_fetch = [
            ticker_map.get(s, s + '.BA' if not s.endswith(('.O', '.D')) else s)
            for s in portfolio_df['Símbolo']
        ]
    except Exception as e:
        st.error(f"❌ Error al procesar los símbolos del portafolio: {e}")
        if st.session_state.get('debug_enabled', False):
            st.write("DataFrame recibido:", portfolio_df)
        return

    end_date = date.today()
    start_date = end_date - timedelta(days=365 * 2) # 2 años de datos

    try:
        with st.spinner("Descargando datos históricos..."):
            historical_data = get_historical_data(tickers_to_fetch, start_date, end_date)

        if historical_data.empty or len(historical_data.columns) < 2:
            st.warning("⚠️ Se requieren al menos dos activos con datos históricos para el análisis. No se pudo continuar.")
            if st.session_state.get('debug_enabled', False):
                st.write("Tickers intentados:", tickers_to_fetch)
                st.write("Datos históricos recibidos:", historical_data)
            return

        daily_returns = historical_data.pct_change().dropna()
        
        with st.spinner("Calculando Frontera Eficiente..."):
            try:
                optimization_results = optimize_portfolio(daily_returns)
            except Exception as e:
                st.error(f"❌ Error durante la optimización del portafolio: {e}")
                if st.session_state.get('debug_enabled', False):
                    st.write("Datos de retornos diarios:", daily_returns)
                return
    except Exception as e:
        st.error(f"❌ Error al obtener datos históricos: {e}")
        if st.session_state.get('debug_enabled', False):
            st.write("Tickers intentados:", tickers_to_fetch)
        return

    # Gráfico de la Frontera Eficiente
    try:
        fig = go.Figure()
        
        # 1. Puntos de la simulación
        sim_returns, sim_vols = optimization_results['simulation']
        sharpe_ratios = np.array(sim_returns) / np.array(sim_vols)
        
        fig.add_trace(go.Scatter(
            x=sim_vols,
            y=sim_returns,
            mode='markers',
            marker=dict(
                color=sharpe_ratios,
                showscale=True,
                colorscale='YlGnBu',
                colorbar_title='Sharpe Ratio'
            ),
            name='Portafolios Simulados'
        ))

        # 2. Portafolio de Máximo Sharpe
        max_sharpe_stats = optimization_results['max_sharpe_stats']
        fig.add_trace(go.Scatter(
            x=[max_sharpe_stats[1]], y=[max_sharpe_stats[0]],
            mode='markers',
            marker=dict(color='red', size=15, symbol='star'),
            name='Máximo Sharpe'
        ))

        # 3. Portafolio de Mínima Volatilidad
        min_vol_stats = optimization_results['min_vol_stats']
        fig.add_trace(go.Scatter(
            x=[min_vol_stats[1]], y=[min_vol_stats[0]],
            mode='markers',
            marker=dict(color='orange', size=15, symbol='diamond'),
            name='Mínima Volatilidad'
        ))
        
        fig.update_layout(
            title='Frontera Eficiente y Portafolios Óptimos',
            xaxis_title='Volatilidad Anualizada (Riesgo)',
            yaxis_title='Retorno Anualizado',
            template='plotly_dark',
            legend_title='Portafolios'
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error al crear el gráfico de optimización: {e}")
        if st.session_state.get('debug_enabled', False):
            st.write("Resultados de optimización:", optimization_results)

    # Mostrar composición de los portafolios óptimos
    try:
        col1, col2 = st.columns(2)
        assets = daily_returns.columns
        
        with col1:
            st.markdown("##### ⭐️ Portafolio de Máximo Sharpe")
            st.metric("Ratio de Sharpe", f"{max_sharpe_stats[2]:.2f}")
            weights_df = pd.DataFrame({
                'Activo': assets,
                'Peso (%)': optimization_results['max_sharpe_weights'] * 100
            })
            st.dataframe(weights_df[weights_df['Peso (%)'] > 0.1].style.format({'Peso (%)': '{:.2f}%'}), use_container_width=True)

        with col2:
            st.markdown("##### 🛡️ Portafolio de Mínima Volatilidad")
            st.metric("Volatilidad", f"{min_vol_stats[1]:.2%}")
            weights_df = pd.DataFrame({
                'Activo': assets,
                'Peso (%)': optimization_results['min_vol_weights'] * 100
            })
            st.dataframe(weights_df[weights_df['Peso (%)'] > 0.1].style.format({'Peso (%)': '{:.2f}%'}), use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error al mostrar los portafolios óptimos: {e}")
        if st.session_state.get('debug_enabled', False):
            st.write("Datos disponibles:", {
                'max_sharpe_stats': max_sharpe_stats,
                'min_vol_stats': min_vol_stats,
                'assets': assets,
                'optimization_results': optimization_results
            })


# ------------------------------------------------------------------------------
# 5. APLICACIÓN PRINCIPAL DE STREAMLIT
# ------------------------------------------------------------------------------
def main():
    """Función principal que ejecuta la aplicación Streamlit."""
    load_custom_css()

    st.title("📊 IOL Portfolio Analyzer Pro")
    st.markdown("Herramienta avanzada para asesores financieros de InvertirOnline.")

    # --- BARRA LATERAL: LOGIN Y CONTROLES ---
    with st.sidebar:
        st.header("🔑 Acceso Asesor")
        
        # Debug toggle global
        if 'debug_enabled' not in st.session_state:
            st.session_state.debug_enabled = False
        
        debug_enabled = st.checkbox("🔍 Modo Debug", value=st.session_state.debug_enabled)
        st.session_state.debug_enabled = debug_enabled
        
        if 'api_client' not in st.session_state:
            # Usar st.secrets en producción
            default_user = st.secrets.get("IOL_USER", "")
            default_pass = st.secrets.get("IOL_PASS", "")

            user = st.text_input("Usuario", value=default_user)
            password = st.text_input("Contraseña", type="password", value=default_pass)

            if st.button("Conectar a IOL"):
                if user and password:
                    with st.spinner("Autenticando..."):
                        try:
                            client = IOLApiClient(user, password)
                            if client._authenticate():
                                st.session_state.api_client = client
                                st.success("✅ Conexión exitosa")
                                st.rerun() # Recargar para mostrar la vista de datos
                            else:
                                st.error("❌ Falló la autenticación.")
                        except Exception as e:
                            st.error(f"❌ Error durante la autenticación: {e}")
                            if st.session_state.get('debug_enabled', False):
                                st.write("Detalles del error:", str(e))
                else:
                    st.warning("Por favor, ingrese usuario y contraseña.")
        else:
            st.success(f"Conectado como **{st.session_state.api_client._username}**")
            
            # --- SELECCIÓN DE CLIENTE ---
            client = st.session_state.api_client
            
            @st.cache_data(ttl=600) # Cachear lista de clientes por 10 mins
            def get_clients(_client_instance):
                return _client_instance.get_client_list()

            with st.spinner("Cargando clientes..."):
                try:
                    client_list = get_clients(client)
                    if client_list is None:
                        st.error("❌ Error al obtener la lista de clientes. Verifique su conexión.")
                        client_list = []
                    elif not isinstance(client_list, list):
                        st.warning(f"⚠️ Formato inesperado de datos: {type(client_list)}")
                        st.write("Datos recibidos:", client_list)
                        client_list = []
                except Exception as e:
                    st.error(f"❌ Error inesperado al cargar clientes: {e}")
                    client_list = []
            
            if client_list:
                # Debug: Mostrar la estructura de datos para entender qué campos están disponibles
                if st.checkbox("🔍 Debug: Mostrar estructura de datos"):
                    st.write("Estructura del primer cliente:", client_list[0] if client_list else "No hay clientes")
                
                # Intentar diferentes combinaciones de campos comunes para nombres de clientes
                client_names = {}
                for c in client_list:
                    try:
                        # Intentar diferentes combinaciones de campos
                        if 'nombre' in c and 'numero' in c:
                            name = f"{c['nombre']} ({c['numero']})"
                        elif 'name' in c and 'number' in c:
                            name = f"{c['name']} ({c['number']})"
                        elif 'nombre' in c:
                            name = f"{c['nombre']} ({c.get('numero', c.get('id', 'N/A'))})"
                        elif 'name' in c:
                            name = f"{c['name']} ({c.get('number', c.get('id', 'N/A'))})"
                        elif 'razonSocial' in c:
                            name = f"{c['razonSocial']} ({c.get('id', 'N/A')})"
                        elif 'apellido' in c and 'nombre' in c:
                            name = f"{c['apellido']}, {c['nombre']} ({c.get('id', 'N/A')})"
                        else:
                            # Fallback: usar el ID si no hay campos de nombre
                            name = f"Cliente {c.get('id', 'N/A')}"
                        
                        client_names[name] = c.get('id', c.get('numero', 'N/A'))
                    except Exception as e:
                        st.warning(f"Error procesando cliente: {e}")
                        continue
                
                if client_names:
                    selected_client_name = st.selectbox(
                        "Seleccione un Cliente",
                        options=client_names.keys(),
                        index=0
                    )
                    st.session_state.selected_client_id = client_names[selected_client_name]
                else:
                    st.error("No se pudieron procesar los datos de los clientes.")
                    st.write("Datos recibidos:", client_list)
            else:
                st.error("No se pudo cargar la lista de clientes.")
            
            if st.button("Cerrar Sesión"):
                for key in st.session_state.keys():
                    del st.session_state[key]
                st.rerun()

    # --- ÁREA PRINCIPAL: VISUALIZACIÓN DE DATOS ---
    if 'api_client' in st.session_state and 'selected_client_id' in st.session_state:
        client = st.session_state.api_client
        client_id = st.session_state.selected_client_id

        # Obtener datos del portafolio (cache por 5 minutos)
        @st.cache_data(ttl=300)
        def fetch_portfolio_data(_client, _client_id):
            arg_portfolio = _client.get_portfolio(_client_id, 'Argentina')
            us_portfolio = _client.get_portfolio(_client_id, 'EstadosUnidos')
            return arg_portfolio, us_portfolio
        
        with st.spinner(f"Cargando portafolio para cliente {client_id}..."):
            try:
                portfolio_arg, portfolio_us = fetch_portfolio_data(client, client_id)
                
                # Debug: Mostrar estructura de datos del portafolio
                if st.checkbox("🔍 Debug: Mostrar estructura del portafolio"):
                    st.write("Portafolio Argentina:", portfolio_arg)
                    st.write("Portafolio USA:", portfolio_us)
                    
            except Exception as e:
                st.error(f"❌ Error al cargar el portafolio: {e}")
                portfolio_arg, portfolio_us = None, None

        # Navegación por pestañas
        tab1, tab2, tab3 = st.tabs(["🇦🇷 Portafolio Argentina", "🇺🇸 Portafolio USA", "🚀 Optimización de Cartera"])

        with tab1:
            st.header("Cartera de Inversión - Argentina")
            try:
                df_arg = display_portfolio(portfolio_arg) if portfolio_arg else None
            except Exception as e:
                st.error(f"❌ Error al mostrar portafolio Argentina: {e}")
                df_arg = None

        with tab2:
            st.header("Cartera de Inversión - Estados Unidos")
            try:
                df_us = display_portfolio(portfolio_us) if portfolio_us else None
            except Exception as e:
                st.error(f"❌ Error al mostrar portafolio USA: {e}")
                df_us = None

        with tab3:
            st.header("Análisis Avanzado")
            # Unir ambos portafolios para un análisis completo
            if df_arg is not None and df_us is not None:
                combined_df = pd.concat([df_arg, df_us], ignore_index=True)
            elif df_arg is not None:
                combined_df = df_arg
            elif df_us is not None:
                combined_df = df_us
            else:
                combined_df = None

            if combined_df is not None and not combined_df.empty:
                display_optimization_analysis(combined_df)
            else:
                st.info("Seleccione un portafolio con activos para iniciar el análisis.")

    elif 'api_client' not in st.session_state:
        st.info("👋 ¡Bienvenido! Por favor, inicie sesión en la barra lateral para comenzar.")

if __name__ == "__main__":
    main()
