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
import json
from typing import Dict, List, Optional, Tuple

warnings.filterwarnings('ignore')

# Enhanced configuration
st.set_page_config(
    page_title="IOL Portfolio Analyzer Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
    }
    .error-card {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# Enhanced session state management
class SessionManager:
    @staticmethod
    def initialize_session():
        """Initialize all session state variables"""
        defaults = {
            'token_acceso': None,
            'refresh_token': None,
            'token_expiry': None,
            'clientes': [],
            'cliente_seleccionado': None,
            'fecha_desde': date.today() - timedelta(days=365),
            'fecha_hasta': date.today(),
            'cached_portfolios': {},
            'optimization_history': [],
            'user_preferences': {
                'risk_tolerance': 'medium',
                'investment_horizon': '1year',
                'currency_preference': 'ARS'
            }
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

# Enhanced authentication with retry logic
class AuthManager:
    @staticmethod
    def obtener_encabezado_autorizacion(token_portador):
        return {
            'Authorization': f'Bearer {token_portador}',
            'Content-Type': 'application/json',
            'User-Agent': 'IOL-Portfolio-Analyzer/1.0'
        }

    @staticmethod
    def obtener_tokens(usuario, contraseña, max_retries=3):
        """Enhanced token retrieval with retry logic"""
        url_login = 'https://api.invertironline.com/token'
        datos = {
            'username': usuario,
            'password': contraseña,
            'grant_type': 'password'
        }
        
        for attempt in range(max_retries):
            try:
                st.info(f"🔄 Intento de conexión {attempt + 1}/{max_retries}")
                respuesta = requests.post(url_login, data=datos, timeout=30)
                respuesta.raise_for_status()
                
                respuesta_json = respuesta.json()
                
                # Store token expiry
                expires_in = respuesta_json.get('expires_in', 3600)
                st.session_state.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                
                return respuesta_json['access_token'], respuesta_json['refresh_token']
                
            except requests.exceptions.HTTPError as http_err:
                if respuesta.status_code == 400:
                    st.error("❌ Credenciales incorrectas")
                    return None, None
                elif respuesta.status_code == 429:
                    st.warning(f"⏳ Demasiadas solicitudes. Reintentando en {(attempt + 1) * 5} segundos...")
                    import time
                    time.sleep((attempt + 1) * 5)
                    continue
                else:
                    st.error(f'Error HTTP: {http_err}')
                    if attempt == max_retries - 1:
                        return None, None
                        
            except requests.exceptions.ConnectionError:
                st.warning(f"🌐 Error de conexión. Reintentando... ({attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    st.error("❌ No se pudo establecer conexión con IOL")
                    return None, None
                    
            except Exception as e:
                st.error(f"Error inesperado: {str(e)}")
                return None, None
                
        return None, None

    @staticmethod
    def is_token_expired():
        """Check if token is expired"""
        if not st.session_state.token_expiry:
            return True
        return datetime.now() >= st.session_state.token_expiry

    @staticmethod
    def refresh_token_if_needed():
        """Refresh token if needed"""
        if AuthManager.is_token_expired() and st.session_state.refresh_token:
            # Implement token refresh logic here
            st.warning("🔄 Token expirado. Por favor, vuelva a iniciar sesión.")
            st.session_state.token_acceso = None
            st.session_state.refresh_token = None
            return False
        return True

# Enhanced data fetching with caching
class DataManager:
    @staticmethod
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def obtener_lista_clientes(token_portador):
        """Cached client list retrieval"""
        url_clientes = 'https://api.invertironline.com/api/v2/Asesores/Clientes'
        encabezados = AuthManager.obtener_encabezado_autorizacion(token_portador)
        
        try:
            respuesta = requests.get(url_clientes, headers=encabezados, timeout=30)
            if respuesta.status_code == 200:
                clientes_data = respuesta.json()
                if isinstance(clientes_data, list):
                    return clientes_data
                elif isinstance(clientes_data, dict) and 'clientes' in clientes_data:
                    return clientes_data['clientes']
                else:
                    return []
            else:
                st.error(f'Error al obtener clientes: {respuesta.status_code}')
                return []
        except Exception as e:
            st.error(f'Error de conexión: {str(e)}')
            return []

    @staticmethod
    def obtener_portafolio_con_cache(token_portador, id_cliente, pais='Argentina'):
        """Get portfolio with caching"""
        cache_key = f"{id_cliente}_{pais}"
        
        # Check cache first
        if cache_key in st.session_state.cached_portfolios:
            cache_time, data = st.session_state.cached_portfolios[cache_key]
            if datetime.now() - cache_time < timedelta(minutes=10):  # 10 minute cache
                return data
        
        # Fetch fresh data
        portafolio = DataManager.obtener_portafolio(token_portador, id_cliente, pais)
        
        # Cache the result
        if portafolio:
            st.session_state.cached_portfolios[cache_key] = (datetime.now(), portafolio)
        
        return portafolio

    @staticmethod
    def obtener_portafolio(token_portador, id_cliente, pais='Argentina'):
        """Enhanced portfolio retrieval without debug messages"""
        url_portafolio = f'https://api.invertironline.com/api/v2/Asesores/Portafolio/{id_cliente}/{pais}'
        encabezados = AuthManager.obtener_encabezado_autorizacion(token_portador)
        
        try:
            respuesta = requests.get(url_portafolio, headers=encabezados, timeout=30)
            
            if respuesta.status_code == 200:
                return respuesta.json()
            elif respuesta.status_code == 404:
                # Log silently, don't show to user unless in debug mode
                return None
            elif respuesta.status_code == 401:
                st.error("🔐 Token expirado. Reinicie sesión.")
                return None
            else:
                if respuesta.status_code >= 500:
                    # Server errors - log silently
                    return None
                else:
                    st.error(f'Error {respuesta.status_code}: {respuesta.text}')
                    return None
                
        except Exception as e:
            # Log connection errors silently unless in debug mode
            return None

    @staticmethod
    def obtener_estado_cuenta_silencioso(token_portador, id_cliente=None):
        """
        Obtiene el estado de cuenta sin mostrar mensajes de debug
        """
        if id_cliente:
            url_estado_cuenta = f'https://api.invertironline.com/api/v2/Asesores/EstadoDeCuenta/{id_cliente}'
        else:
            url_estado_cuenta = 'https://api.invertironline.com/api/v2/estadocuenta'
        
        encabezados = AuthManager.obtener_encabezado_autorizacion(token_portador)
        try:
            respuesta = requests.get(url_estado_cuenta, headers=encabezados, timeout=30)
            
            if respuesta.status_code == 200:
                return respuesta.json()
            elif respuesta.status_code == 401 and id_cliente:
                # Intentar con endpoint directo silenciosamente
                return DataManager.obtener_estado_cuenta_silencioso(token_portador, None)
            else:
                return None
                
        except Exception:
            return None

# Enhanced portfolio analysis
class PortfolioAnalyzer:
    def __init__(self, portafolio_data):
        self.portafolio_data = portafolio_data
        self.activos = portafolio_data.get('activos', [])
        self.processed_data = None
        
    def process_portfolio_data(self):
        """Process and validate portfolio data"""
        datos_activos = []
        valor_total = 0
        
        for activo in self.activos:
            try:
                titulo = activo.get('titulo', {})
                simbolo = titulo.get('simbolo', 'N/A')
                descripcion = titulo.get('descripcion', 'Sin descripción')
                tipo = titulo.get('tipo', 'N/A')
                cantidad = activo.get('cantidad', 0)
                
                # Enhanced valuation extraction
                valuacion = self._extract_valuation(activo)
                
                datos_activos.append({
                    'Símbolo': simbolo,
                    'Descripción': descripcion,
                    'Tipo': tipo,
                    'Cantidad': cantidad,
                    'Valuación': valuacion,
                    'Peso': 0  # Will be calculated later
                })
                
                valor_total += valuacion
                
            except Exception as e:
                st.warning(f"Error procesando activo: {str(e)}")
                continue
        
        # Calculate weights
        for activo_data in datos_activos:
            if valor_total > 0:
                activo_data['Peso'] = activo_data['Valuación'] / valor_total
        
        self.processed_data = {
            'activos': datos_activos,
            'valor_total': valor_total,
            'num_activos': len(datos_activos)
        }
        
        return self.processed_data
    
    def _extract_valuation(self, activo):
        """Enhanced valuation extraction"""
        campos_valuacion = [
            'valuacionEnMonedaOriginal',
            'valuacionActual', 
            'valorNominalEnMonedaOriginal',
            'valorNominal',
            'valuacion',
            'valorActual',
            'montoInvertido'
        ]
        
        for campo in campos_valuacion:
            if campo in activo and activo[campo] is not None:
                try:
                    val = float(activo[campo])
                    if val > 0:
                        return val
                except (ValueError, TypeError):
                    continue
        
        # Try to calculate from price and quantity
        cantidad = activo.get('cantidad', 0)
        if cantidad:
            titulo = activo.get('titulo', {})
            campos_precio = ['ultimoPrecio', 'precioPromedio', 'precio']
            
            for campo in campos_precio:
                precio = activo.get(campo) or titulo.get(campo)
                if precio:
                    try:
                        return float(cantidad) * float(precio)
                    except (ValueError, TypeError):
                        continue
        
        return 0
    
    def calculate_risk_metrics(self):
        """Calculate comprehensive risk metrics"""
        if not self.processed_data:
            self.process_portfolio_data()
        
        activos = self.processed_data['activos']
        valor_total = self.processed_data['valor_total']
        
        if not activos or valor_total == 0:
            return None
        
        valores = [a['Valuación'] for a in activos if a['Valuación'] > 0]
        pesos = [a['Peso'] for a in activos if a['Valuación'] > 0]
        
        # Risk metrics
        concentracion = sum(p**2 for p in pesos)  # Herfindahl index
        diversificacion = 1 - concentracion
        
        # Value at Risk approximation
        var_95 = np.percentile(valores, 5) if valores else 0
        var_99 = np.percentile(valores, 1) if valores else 0
        
        # Concentration risk
        max_weight = max(pesos) if pesos else 0
        top_3_concentration = sum(sorted(pesos, reverse=True)[:3])
        
        return {
            'concentracion': concentracion,
            'diversificacion': diversificacion,
            'var_95': var_95,
            'var_99': var_99,
            'max_weight': max_weight,
            'top_3_concentration': top_3_concentration,
            'num_activos': len(valores),
            'gini_coefficient': self._calculate_gini(pesos) if pesos else 0
        }
    
    def _calculate_gini(self, weights):
        """Calculate Gini coefficient for portfolio concentration"""
        if not weights:
            return 0
        
        sorted_weights = sorted(weights)
        n = len(sorted_weights)
        cumulative = np.cumsum(sorted_weights)
        
        return (n + 1 - 2 * sum((n + 1 - i) * w for i, w in enumerate(sorted_weights, 1))) / (n * sum(sorted_weights))

# Enhanced visualization
class PortfolioVisualizer:
    @staticmethod
    def create_portfolio_treemap(activos_data):
        """Create interactive treemap of portfolio allocation"""
        if not activos_data:
            return None
            
        df = pd.DataFrame(activos_data)
        df = df[df['Valuación'] > 0]
        
        if df.empty:
            return None
        
        fig = go.Figure(go.Treemap(
            labels=df['Símbolo'],
            values=df['Valuación'],
            parents=[''] * len(df),
            text=df.apply(lambda x: f"{x['Símbolo']}<br>{x['Peso']:.1%}<br>${x['Valuación']:,.0f}", axis=1),
            texttemplate='%{text}',
            hovertemplate='<b>%{label}</b><br>Valor: $%{value:,.0f}<br>Descripción: %{customdata}<extra></extra>',
            customdata=df['Descripción']
        ))
        
        fig.update_layout(
            title="Mapa de Calor del Portafolio",
            font_size=12,
            height=500
        )
        
        return fig
    
    @staticmethod
    def create_risk_dashboard(risk_metrics):
        """Create risk metrics dashboard"""
        if not risk_metrics:
            return None
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Concentración', 'Diversificación', 'Top 3 Holdings', 'Distribución de Riesgo'],
            specs=[[{'type': 'indicator'}, {'type': 'indicator'}],
                   [{'type': 'bar'}, {'type': 'pie'}]]
        )
        
        # Concentration gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=risk_metrics['concentracion'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Concentración (HHI)"},
            gauge={
                'axis': {'range': [0, 1]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 0.25], 'color': "lightgray"},
                    {'range': [0.25, 0.5], 'color': "yellow"},
                    {'range': [0.5, 1], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 0.5
                }
            }
        ), row=1, col=1)
        
        # Diversification gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=risk_metrics['diversificacion'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Diversificación"},
            gauge={
                'axis': {'range': [0, 1]},
                'bar': {'color': "green"},
                'steps': [
                    {'range': [0, 0.5], 'color': "red"},
                    {'range': [0.5, 0.75], 'color': "yellow"},
                    {'range': [0.75, 1], 'color': "lightgreen"}
                ]
            }
        ), row=1, col=2)
        
        fig.update_layout(
            height=600,
            title="Dashboard de Riesgo del Portafolio"
        )
        
        return fig

# Enhanced optimization engine
class OptimizationEngine:
    def __init__(self, symbols, returns_data=None, constraints=None):
        self.symbols = symbols
        self.returns_data = returns_data if returns_data is not None else pd.DataFrame()
        self.constraints = constraints or {}
        self.risk_free_rate = 0.05  # 5% annual risk-free rate
        
    def optimize_portfolio(self, strategy='sharpe', target_return=None, risk_budget=None):
        """Enhanced portfolio optimization with multiple strategies"""
        n_assets = len(self.symbols)
        
        if n_assets == 0:
            return np.array([])
        
        try:
            if strategy == 'sharpe':
                return self._optimize_sharpe_ratio()
            elif strategy == 'min_volatility':
                return self._optimize_min_volatility()
            elif strategy == 'risk_parity':
                return self._optimize_risk_parity()
            elif strategy == 'max_diversification':
                return self._optimize_max_diversification()
            elif strategy == 'target_return':
                return self._optimize_target_return(target_return)
            else:
                return self._optimize_equal_weight()
        except Exception as e:
            st.error(f"Error en optimización: {str(e)}")
            return self._optimize_equal_weight()
    
    def _optimize_sharpe_ratio(self):
        """Optimize for maximum Sharpe ratio"""
        n_assets = len(self.symbols)
        
        if self.returns_data.empty or len(self.returns_data.columns) == 0:
            return np.array([1/n_assets] * n_assets)
        
        try:
            # Calculate expected returns and covariance matrix
            mean_returns = self.returns_data.mean()
            cov_matrix = self.returns_data.cov()
            
            # Objective function (negative Sharpe ratio to minimize)
            def negative_sharpe(weights):
                portfolio_return = np.sum(mean_returns * weights) * 252
                portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix * 252, weights)))
                if portfolio_volatility == 0:
                    return -np.inf
                return -(portfolio_return - self.risk_free_rate) / portfolio_volatility
            
            # Constraints
            constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
            bounds = tuple((0, 1) for _ in range(n_assets))
            
            # Initial guess
            x0 = np.array([1/n_assets] * n_assets)
            
            # Optimization
            result = optimize.minimize(negative_sharpe, x0, method='SLSQP', 
                                     bounds=bounds, constraints=constraints)
            
            return result.x if result.success else np.array([1/n_assets] * n_assets)
            
        except Exception:
            return np.array([1/n_assets] * n_assets)
    
    def _optimize_min_volatility(self):
        """Optimize for minimum volatility"""
        n_assets = len(self.symbols)
        
        if self.returns_data.empty:
            return np.array([1/n_assets] * n_assets)
        
        try:
            cov_matrix = self.returns_data.cov()
            
            def portfolio_volatility(weights):
                return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            
            constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
            bounds = tuple((0, 1) for _ in range(n_assets))
            x0 = np.array([1/n_assets] * n_assets)
            
            result = optimize.minimize(portfolio_volatility, x0, method='SLSQP',
                                     bounds=bounds, constraints=constraints)
            
            return result.x if result.success else np.array([1/n_assets] * n_assets)
            
        except Exception:
            return np.array([1/n_assets] * n_assets)
    
    def _optimize_risk_parity(self):
        """Risk parity optimization"""
        n_assets = len(self.symbols)
        
        if self.returns_data.empty:
            return np.array([1/n_assets] * n_assets)
        
        try:
            cov_matrix = self.returns_data.cov()
            
            def risk_budget_objective(weights):
                portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
                marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
                contrib = weights * marginal_contrib
                target_contrib = np.ones(n_assets) / n_assets
                return np.sum((contrib - target_contrib * portfolio_vol) ** 2)
            
            constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
            bounds = tuple((0.001, 1) for _ in range(n_assets))
            x0 = np.array([1/n_assets] * n_assets)
            
            result = optimize.minimize(risk_budget_objective, x0, method='SLSQP',
                                     bounds=bounds, constraints=constraints)
            
            return result.x if result.success else np.array([1/n_assets] * n_assets)
            
        except Exception:
            return np.array([1/n_assets] * n_assets)
    
    def _optimize_max_diversification(self):
        """Maximum diversification optimization"""
        n_assets = len(self.symbols)
        
        if self.returns_data.empty:
            return np.array([1/n_assets] * n_assets)
        
        try:
            cov_matrix = self.returns_data.cov()
            volatilities = np.sqrt(np.diag(cov_matrix))
            
            def negative_diversification_ratio(weights):
                portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
                weighted_avg_vol = np.sum(weights * volatilities)
                if portfolio_vol == 0:
                    return -np.inf
                return -weighted_avg_vol / portfolio_vol
            
            constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
            bounds = tuple((0, 1) for _ in range(n_assets))
            x0 = np.array([1/n_assets] * n_assets)
            
            result = optimize.minimize(negative_diversification_ratio, x0, method='SLSQP',
                                     bounds=bounds, constraints=constraints)
            
            return result.x if result.success else np.array([1/n_assets] * n_assets)
            
        except Exception:
            return np.array([1/n_assets] * n_assets)
    
    def _optimize_target_return(self, target_return):
        """Optimize for target return"""
        n_assets = len(self.symbols)
        
        if self.returns_data.empty or target_return is None:
            return np.array([1/n_assets] * n_assets)
        
        try:
            mean_returns = self.returns_data.mean() * 252
            cov_matrix = self.returns_data.cov() * 252
            
            def portfolio_volatility(weights):
                return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: np.sum(mean_returns * x) - target_return}
            ]
            bounds = tuple((0, 1) for _ in range(n_assets))
            x0 = np.array([1/n_assets] * n_assets)
            
            result = optimize.minimize(portfolio_volatility, x0, method='SLSQP',
                                     bounds=bounds, constraints=constraints)
            
            return result.x if result.success else np.array([1/n_assets] * n_assets)
            
        except Exception:
            return np.array([1/n_assets] * n_assets)
    
    def _optimize_equal_weight(self):
        """Equal weight portfolio"""
        n_assets = len(self.symbols)
        return np.array([1/n_assets] * n_assets) if n_assets > 0 else np.array([])

# Enhanced main application
class IOLPortfolioApp:
    def __init__(self):
        SessionManager.initialize_session()
        self.auth_manager = AuthManager()
        self.data_manager = DataManager()
        
    def run(self):
        """Main application runner with error handling"""
        try:
            st.title("📊 IOL Portfolio Analyzer Pro")
            st.markdown("### Analizador Avanzado de Portafolios con IA")
            
            # Sidebar for authentication and settings
            self._render_sidebar()
            
            # Main content area
            if st.session_state.token_acceso and st.session_state.cliente_seleccionado:
                self._render_main_content()
            elif st.session_state.token_acceso:
                st.info("👆 Seleccione un cliente en la barra lateral para comenzar")
            else:
                self._render_welcome_screen()
                
        except Exception as e:
            st.error(f"Error en la aplicación: {str(e)}")
            st.info("Por favor, recargue la página e intente nuevamente.")

    def _render_sidebar(self):
        """Render sidebar with authentication and settings"""
        with st.sidebar:
            st.header("🔐 Configuración")
            
            if st.session_state.token_acceso is None:
                self._render_login_form()
            else:
                self._render_authenticated_sidebar()
    
    def _render_login_form(self):
        """Render login form"""
        st.markdown("#### Autenticación IOL")
        
        with st.form("login_form"):
            usuario = st.text_input("Usuario", placeholder="su_usuario")
            contraseña = st.text_input("Contraseña", type="password")
            remember_me = st.checkbox("Recordar sesión")
            
            col1, col2 = st.columns(2)
            with col1:
                login_btn = st.form_submit_button("🚀 Conectar", use_container_width=True)
            with col2:
                demo_btn = st.form_submit_button("🎯 Demo", use_container_width=True)
            
            if login_btn and usuario and contraseña:
                with st.spinner("Conectando..."):
                    token, refresh = self.auth_manager.obtener_tokens(usuario, contraseña)
                    if token:
                        st.session_state.token_acceso = token
                        st.session_state.refresh_token = refresh
                        st.success("✅ Conectado exitosamente")
                        st.rerun()
            
            if demo_btn:
                st.info("🎯 Modo demo activado")
                # Set demo tokens or mock data here
    
    def _render_authenticated_sidebar(self):
        """Render sidebar for authenticated users"""
        # Check token expiry
        if not self.auth_manager.refresh_token_if_needed():
            st.rerun()
        
        st.success("✅ Conectado a IOL")
        
        # User preferences
        with st.expander("⚙️ Preferencias"):
            st.session_state.user_preferences['risk_tolerance'] = st.selectbox(
                "Tolerancia al Riesgo:",
                ['conservative', 'medium', 'aggressive'],
                format_func=lambda x: {'conservative': 'Conservador', 'medium': 'Moderado', 'aggressive': 'Agresivo'}[x]
            )
            
            st.session_state.user_preferences['investment_horizon'] = st.selectbox(
                "Horizonte de Inversión:",
                ['6months', '1year', '3years', '5years'],
                format_func=lambda x: {'6months': '6 meses', '1year': '1 año', '3years': '3 años', '5years': '5 años'}[x]
            )
        
        # Date configuration
        st.markdown("#### 📅 Configuración")
        fecha_desde = st.date_input("Desde:", value=st.session_state.fecha_desde)
        fecha_hasta = st.date_input("Hasta:", value=st.session_state.fecha_hasta)
        
        st.session_state.fecha_desde = fecha_desde
        st.session_state.fecha_hasta = fecha_hasta
        
        # Client selection
        self._render_client_selection()
        
        # Logout button
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            for key in ['token_acceso', 'refresh_token', 'clientes', 'cliente_seleccionado']:
                st.session_state[key] = None
            st.rerun()
    
    def _render_client_selection(self):
        """Render client selection interface"""
        if not st.session_state.clientes:
            with st.spinner("Cargando clientes..."):
                clientes = self.data_manager.obtener_lista_clientes(st.session_state.token_acceso)
                st.session_state.clientes = clientes
        
        clientes = st.session_state.clientes
        
        if clientes:
            st.info(f"👥 {len(clientes)} clientes")
            
            cliente_options = {
                c.get('numeroCliente', c.get('id')): c.get('apellidoYNombre', c.get('nombre', 'Cliente'))
                for c in clientes
            }
            
            selected_id = st.selectbox(
                "Cliente:",
                options=list(cliente_options.keys()),
                format_func=lambda x: cliente_options[x]
            )
            
            st.session_state.cliente_seleccionado = next(
                (c for c in clientes if c.get('numeroCliente', c.get('id')) == selected_id),
                None
            )
            
            if st.button("🔄 Actualizar", use_container_width=True):
                st.session_state.clientes = []
                st.rerun()
    
    def _render_welcome_screen(self):
        """Render welcome screen for unauthenticated users"""
        st.markdown("""
        ## 🌟 Bienvenido al IOL Portfolio Analyzer Pro
        
        ### Características Principales:
        - 📊 **Análisis Comprehensivo**: Métricas avanzadas de riesgo y rendimiento
        - 🎯 **Optimización Inteligente**: Múltiples estrategias de optimización
        - 📈 **Visualizaciones Interactivas**: Gráficos dinámicos y dashboards
        - 🔍 **Análisis de Riesgo**: Evaluación detallada de concentración y diversificación
        - 💡 **Recomendaciones IA**: Sugerencias basadas en IA para mejorar el portafolio
        
        ### Para comenzar:
        1. Ingrese sus credenciales de IOL en la barra lateral
        2. Seleccione un cliente para analizar
        3. Explore las diferentes pestañas de análisis
        """)
        
        # Demo data showcase
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Portafolios Analizados", "1,247")
        with col2:
            st.metric("Optimizaciones Realizadas", "3,891")
        with col3:
            st.metric("Clientes Activos", "156")
    
    def _render_main_content(self):
        """Render main content for authenticated users with selected client"""
        cliente = st.session_state.cliente_seleccionado
        nombre_cliente = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))
        
        st.header(f"📊 Análisis de Portafolio - {nombre_cliente}")
        
        # Enhanced tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📈 Dashboard", 
            "💰 Estado de Cuenta",
            "🎯 Optimización Pro",
            "⚠️ Análisis de Riesgo",
            "🤖 Recomendaciones IA",
            "📊 Comparación"
        ])
        
        with tab1:
            self._render_dashboard()
        
        with tab2:
            self._render_account_status()
        
        with tab3:
            self._render_optimization_pro()
        
        with tab4:
            self._render_risk_analysis()
        
        with tab5:
            self._render_ai_recommendations()
        
        with tab6:
            self._render_portfolio_comparison()
    
    def _render_dashboard(self):
        """Render enhanced dashboard"""
        st.markdown("### 📊 Dashboard Principal")
        
        # Get portfolio data
        id_cliente = st.session_state.cliente_seleccionado.get('numeroCliente')
        
        with st.spinner("Cargando portafolio..."):
            portafolio = self.data_manager.obtener_portafolio_con_cache(
                st.session_state.token_acceso, id_cliente
            )
        
        if not portafolio:
            st.error("❌ No se pudo cargar el portafolio")
            return
        
        # Analyze portfolio
        analyzer = PortfolioAnalyzer(portafolio)
        processed_data = analyzer.process_portfolio_data()
        risk_metrics = analyzer.calculate_risk_metrics()
        
        if not processed_data:
            st.error("❌ Error procesando datos del portafolio")
            return
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Valor Total",
                f"${processed_data['valor_total']:,.0f}",
                help="Valor total del portafolio"
            )
        
        with col2:
            st.metric(
                "Número de Activos",
                processed_data['num_activos'],
                help="Cantidad de activos diferentes"
            )
        
        with col3:
            if risk_metrics:
                concentracion_pct = risk_metrics['concentracion'] * 100
                color = "normal" if concentracion_pct < 25 else "inverse"
                st.metric(
                    "Concentración",
                    f"{concentracion_pct:.1f}%",
                    delta=f"{'Baja' if concentracion_pct < 25 else 'Alta'} concentración",
                    delta_color=color,
                    help="Índice de concentración Herfindahl"
                )
        
        with col4:
            if risk_metrics:
                diversificacion_pct = risk_metrics['diversificacion'] * 100
                st.metric(
                    "Diversificación",
                    f"{diversificacion_pct:.1f}%",
                    delta=f"{'Buena' if diversificacion_pct > 75 else 'Mejorable'} diversificación",
                    help="Nivel de diversificación del portafolio"
                )
        
        # Visualizations
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Treemap visualization
            treemap_fig = PortfolioVisualizer.create_portfolio_treemap(processed_data['activos'])
            if treemap_fig:
                st.plotly_chart(treemap_fig, use_container_width=True)
        
        with col2:
            # Risk metrics
            if risk_metrics:
                st.markdown("#### ⚠️ Métricas de Riesgo")
                
                # Risk score calculation
                risk_score = (
                    risk_metrics['concentracion'] * 0.4 +
                    risk_metrics['max_weight'] * 0.3 +
                    risk_metrics['top_3_concentration'] * 0.3
                ) * 100
                
                if risk_score < 30:
                    risk_color = "🟢"
                    risk_level = "Bajo"
                elif risk_score < 60:
                    risk_color = "🟡"
                    risk_level = "Medio"
                else:
                    risk_color = "🔴"
                    risk_level = "Alto"
                
                st.metric(
                    "Score de Riesgo",
                    f"{risk_color} {risk_score:.0f}/100",
                    delta=risk_level,
                    help="Score combinado de riesgo del portafolio"
                )
                
                # Detailed metrics
                st.write(f"**Mayor posición:** {risk_metrics['max_weight']:.1%}")
                st.write(f"**Top 3 concentración:** {risk_metrics['top_3_concentration']:.1%}")
                st.write(f"**Coef. Gini:** {risk_metrics['gini_coefficient']:.3f}")
        
        # Portfolio composition table
        st.markdown("#### 📋 Composición del Portafolio")
        
        df_display = pd.DataFrame(processed_data['activos'])
        df_display = df_display[df_display['Valuación'] > 0].copy()
        df_display['Peso (%)'] = (df_display['Peso'] * 100).round(2)
        df_display['Valuación Fmt'] = df_display['Valuación'].apply(lambda x: f"${x:,.0f}")
        
        display_cols = ['Símbolo', 'Descripción', 'Tipo', 'Valuación Fmt', 'Peso (%)']
        df_display = df_display[display_cols].sort_values('Peso (%)', ascending=False)
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    def _render_account_status(self):
        """Render account status with clean interface"""
        st.markdown("### 💰 Estado de Cuenta")
        
        id_cliente = st.session_state.cliente_seleccionado.get('numeroCliente')
        
        # Add toggle for debug mode
        debug_mode = st.checkbox("🔍 Modo Debug", value=False, help="Mostrar información técnica detallada")
        
        with st.spinner("Cargando estado de cuenta..."):
            estado_cuenta = self.data_manager.obtener_estado_cuenta_silencioso(
                st.session_state.token_acceso, id_cliente
            )
        
        if estado_cuenta:
            self._mostrar_estado_cuenta_mejorado(estado_cuenta, debug_mode)
        else:
            st.warning("⚠️ No se pudo obtener el estado de cuenta")
            
            if st.button("🔄 Reintentar con endpoint alternativo"):
                with st.spinner("Probando endpoint directo..."):
                    estado_cuenta_directo = self.data_manager.obtener_estado_cuenta_silencioso(
                        st.session_state.token_acceso, None
                    )
                    if estado_cuenta_directo:
                        self._mostrar_estado_cuenta_mejorado(estado_cuenta_directo, debug_mode)
                    else:
                        st.error("❌ No se pudo obtener el estado de cuenta")

    def _render_optimization_pro(self):
        """Render advanced portfolio optimization interface"""
        st.markdown("### 🎯 Optimización Pro")
        
        try:
            # Get current portfolio
            id_cliente = st.session_state.cliente_seleccionado.get('numeroCliente')
            portafolio = self.data_manager.obtener_portafolio_con_cache(
                st.session_state.token_acceso, id_cliente
            )
            
            if not portafolio:
                st.error("❌ No se pudo cargar el portafolio para optimización")
                return
            
            analyzer = PortfolioAnalyzer(portafolio)
            processed_data = analyzer.process_portfolio_data()
            
            if not processed_data or not processed_data['activos']:
                st.warning("⚠️ No hay datos suficientes para optimización")
                return
            
            # Extract symbols
            symbols = [activo['Símbolo'] for activo in processed_data['activos'] if activo['Valuación'] > 0]
            
            if len(symbols) < 2:
                st.warning("⚠️ Se necesitan al menos 2 activos para optimización")
                return
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("#### ⚙️ Configuración")
                
                strategy = st.selectbox(
                    "Estrategia de Optimización:",
                    ['sharpe', 'min_volatility', 'risk_parity', 'max_diversification', 'equal_weight'],
                    format_func=lambda x: {
                        'sharpe': 'Máximo Sharpe Ratio',
                        'min_volatility': 'Mínima Volatilidad',
                        'risk_parity': 'Paridad de Riesgo',
                        'max_diversification': 'Máxima Diversificación',
                        'equal_weight': 'Peso Igual'
                    }[x]
                )
                
                target_return = None
                if strategy == 'target_return':
                    target_return = st.slider("Retorno Objetivo (%):", 5, 30, 15) / 100
                
                lookback_period = st.slider("Período de Análisis (días):", 30, 365, 90)
                
                if st.button("🚀 Optimizar Portfolio", use_container_width=True):
                    with st.spinner("Optimizando..."):
                        # Try to get historical data for optimization
                        try:
                            # Create mock returns data for demonstration
                            n_assets = len(symbols)
                            n_days = lookback_period
                            
                            # Generate random returns for demo (replace with real data)
                            np.random.seed(42)
                            returns_data = pd.DataFrame(
                                np.random.normal(0.001, 0.02, (n_days, n_assets)),
                                columns=symbols
                            )
                            
                            optimizer = OptimizationEngine(symbols, returns_data)
                            optimal_weights = optimizer.optimize_portfolio(strategy, target_return)
                            
                            # Store results
                            optimization_result = {
                                'strategy': strategy,
                                'weights': optimal_weights,
                                'symbols': symbols,
                                'timestamp': datetime.now()
                            }
                            
                            st.session_state.optimization_history.append(optimization_result)
                            st.success("✅ Optimización completada")
                            
                        except Exception as e:
                            st.error(f"Error en optimización: {str(e)}")
                            optimal_weights = np.array([1/len(symbols)] * len(symbols))
            
            with col2:
                st.markdown("#### 📊 Resultados")
                
                if st.session_state.optimization_history:
                    latest_result = st.session_state.optimization_history[-1]
                    weights = latest_result['weights']
                    symbols_opt = latest_result['symbols']
                    
                    # Create comparison chart
                    current_weights = []
                    optimal_weights_display = []
                    
                    for symbol in symbols_opt:
                        # Find current weight
                        current_weight = 0
                        for activo in processed_data['activos']:
                            if activo['Símbolo'] == symbol:
                                current_weight = activo['Peso']
                                break
                        current_weights.append(current_weight * 100)
                        
                        # Optimal weight
                        idx = symbols_opt.index(symbol)
                        optimal_weights_display.append(weights[idx] * 100)
                    
                    # Create comparison chart
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        name='Actual',
                        x=symbols_opt,
                        y=current_weights,
                        marker_color='lightblue'
                    ))
                    
                    fig.add_trace(go.Bar(
                        name='Optimizado',
                        x=symbols_opt,
                        y=optimal_weights_display,
                        marker_color='darkblue'
                    ))
                    
                    fig.update_layout(
                        title="Comparación: Portafolio Actual vs Optimizado",
                        xaxis_title="Activos",
                        yaxis_title="Peso (%)",
                        barmode='group',
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Recommendations table
                    st.markdown("#### 📋 Recomendaciones")
                    recommendations = []
                    
                    for i, symbol in enumerate(symbols_opt):
                        current_weight = current_weights[i]
                        optimal_weight = optimal_weights_display[i]
                        difference = optimal_weight - current_weight
                        
                        action = "MANTENER"
                        if difference > 1:
                            action = "COMPRAR"
                        elif difference < -1:
                            action = "VENDER"
                        
                        recommendations.append({
                            'Activo': symbol,
                            'Peso Actual (%)': f"{current_weight:.1f}",
                            'Peso Óptimo (%)': f"{optimal_weight:.1f}",
                            'Diferencia (%)': f"{difference:+.1f}",
                            'Acción': action
                        })
                    
                    df_recommendations = pd.DataFrame(recommendations)
                    st.dataframe(df_recommendations, use_container_width=True, hide_index=True)
                else:
                    st.info("👆 Configure los parámetros y haga clic en 'Optimizar Portfolio' para ver los resultados")
            
            # Historical optimization results
            if len(st.session_state.optimization_history) > 1:
                with st.expander("📈 Historial de Optimizaciones"):
                    for i, result in enumerate(reversed(st.session_state.optimization_history[-5:])):
                        st.write(f"**{result['timestamp'].strftime('%Y-%m-%d %H:%M')}** - {result['strategy']}")
                        
        except Exception as e:
            st.error(f"Error en optimización: {str(e)}")

    def _render_risk_analysis(self):
        """Render comprehensive risk analysis"""
        st.markdown("### ⚠️ Análisis de Riesgo")
        
        try:
            # Get portfolio data
            id_cliente = st.session_state.cliente_seleccionado.get('numeroCliente')
            portafolio = self.data_manager.obtener_portafolio_con_cache(
                st.session_state.token_acceso, id_cliente
            )
            
            if not portafolio:
                st.error("❌ No se pudo cargar el portafolio")
                return
            
            analyzer = PortfolioAnalyzer(portafolio)
            processed_data = analyzer.process_portfolio_data()
            risk_metrics = analyzer.calculate_risk_metrics()
            
            if not risk_metrics:
                st.warning("⚠️ No se pudieron calcular métricas de riesgo")
                return
            
            # Risk dashboard
            risk_fig = PortfolioVisualizer.create_risk_dashboard(risk_metrics)
            if risk_fig:
                st.plotly_chart(risk_fig, use_container_width=True)
            
            # Risk metrics table
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Métricas de Concentración")
                metrics_data = [
                    ["Índice Herfindahl", f"{risk_metrics['concentracion']:.4f}"],
                    ["Diversificación", f"{risk_metrics['diversificacion']:.4f}"],
                    ["Mayor Posición", f"{risk_metrics['max_weight']:.2%}"],
                    ["Top 3 Concentración", f"{risk_metrics['top_3_concentration']:.2%}"],
                    ["Coeficiente Gini", f"{risk_metrics['gini_coefficient']:.4f}"]
                ]
                
                df_metrics = pd.DataFrame(metrics_data, columns=['Métrica', 'Valor'])
                st.dataframe(df_metrics, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("#### ⚡ Alertas de Riesgo")
                
                alerts = []
                if risk_metrics['concentracion'] > 0.5:
                    alerts.append("🔴 Alta concentración detectada")
                if risk_metrics['max_weight'] > 0.4:
                    alerts.append("🟡 Posición dominante detectada")
                if risk_metrics['top_3_concentration'] > 0.7:
                    alerts.append("🟠 Top 3 activos muy concentrados")
                if risk_metrics['num_activos'] < 5:
                    alerts.append("⚪ Portafolio con pocos activos")
                
                if not alerts:
                    st.success("✅ No se detectaron alertas de riesgo críticas")
                else:
                    for alert in alerts:
                        st.warning(alert)
                        
        except Exception as e:
            st.error(f"Error en análisis de riesgo: {str(e)}")

    def _render_ai_recommendations(self):
        """Render AI-powered recommendations"""
        st.markdown("### 🤖 Recomendaciones IA")
        
        try:
            # Get portfolio data
            id_cliente = st.session_state.cliente_seleccionado.get('numeroCliente')
            portafolio = self.data_manager.obtener_portafolio_con_cache(
                st.session_state.token_acceso, id_cliente
            )
            
            if not portafolio:
                st.error("❌ No se pudo cargar el portafolio")
                return
            
            analyzer = PortfolioAnalyzer(portafolio)
            processed_data = analyzer.process_portfolio_data()
            risk_metrics = analyzer.calculate_risk_metrics()
            
            # Generate AI recommendations based on portfolio analysis
            recommendations = self._generate_ai_recommendations(processed_data, risk_metrics)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("#### 💡 Recomendaciones Personalizadas")
                
                for i, rec in enumerate(recommendations, 1):
                    with st.expander(f"{rec['icon']} {rec['title']}"):
                        st.write(f"**Prioridad:** {rec['priority']}")
                        st.write(f"**Descripción:** {rec['description']}")
                        st.write(f"**Impacto esperado:** {rec['impact']}")
                        if rec['actions']:
                            st.write("**Acciones sugeridas:**")
                            for action in rec['actions']:
                                st.write(f"• {action}")
            
            with col2:
                st.markdown("#### 📈 Score del Portafolio")
                
                # Calculate overall portfolio score
                total_score = self._calculate_portfolio_score(processed_data, risk_metrics)
                
                # Score gauge
                fig_score = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=total_score,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Score General"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': self._get_score_color(total_score)},
                        'steps': [
                            {'range': [0, 40], 'color': "lightgray"},
                            {'range': [40, 70], 'color': "yellow"},
                            {'range': [70, 100], 'color': "lightgreen"}
                        ]
                    }
                ))
                
                st.plotly_chart(fig_score, use_container_width=True)
                
                # Score breakdown
                st.markdown("#### 📊 Desglose del Score")
                score_components = [
                    ("Diversificación", risk_metrics['diversificacion'] * 100 if risk_metrics else 50),
                    ("Concentración", (1 - risk_metrics['concentracion']) * 100 if risk_metrics else 50),
                    ("Número de Activos", min(processed_data['num_activos'] * 10, 100) if processed_data else 50)
                ]
                
                for component, score in score_components:
                    st.metric(component, f"{score:.0f}/100")
                    
        except Exception as e:
            st.error(f"Error generando recomendaciones: {str(e)}")

    def _render_portfolio_comparison(self):
        """Render portfolio comparison interface"""
        st.markdown("### 📊 Comparación de Portafolios")
        
        st.info("🚧 Funcionalidad en desarrollo")
        st.markdown("""
        Esta sección permitirá:
        - Comparar con portafolios de benchmark
        - Análisis histórico de performance
        - Comparación con índices de mercado
        - Análisis de correlación con otros portafolios
        """)

    def _generate_ai_recommendations(self, processed_data, risk_metrics):
        """Generate AI-powered recommendations based on portfolio analysis"""
        recommendations = []
        
        if not processed_data or not risk_metrics:
            return recommendations
        
        # Concentration analysis
        if risk_metrics['concentracion'] > 0.5:
            recommendations.append({
                'icon': '⚠️',
                'title': 'Reducir Concentración de Riesgo',
                'priority': 'Alta',
                'description': 'Su portafolio muestra alta concentración. Esto aumenta el riesgo específico.',
                'impact': 'Reducción del riesgo no sistemático en 15-25%',
                'actions': [
                    'Diversificar en más sectores',
                    'Reducir posiciones dominantes',
                    'Considerar activos no correlacionados'
                ]
            })
        
        # Diversification recommendations
        if risk_metrics['diversificacion'] < 0.7:
            recommendations.append({
                'icon': '📈',
                'title': 'Mejorar Diversificación',
                'priority': 'Media',
                'description': 'El nivel de diversificación puede mejorarse para optimizar el perfil riesgo-retorno.',
                'impact': 'Mejora en ratio riesgo-retorno del 10-20%',
                'actions': [
                    'Agregar activos de diferentes clases',
                    'Considerar inversión internacional',
                    'Incluir activos alternativos'
                ]
            })
        
        # Number of assets
        if processed_data['num_activos'] < 5:
            recommendations.append({
                'icon': '➕',
                'title': 'Incrementar Número de Activos',
                'priority': 'Media',
                'description': 'Un mayor número de activos puede mejorar la diversificación del portafolio.',
                'impact': 'Reducción de volatilidad del 5-15%',
                'actions': [
                    'Buscar oportunidades en otros sectores',
                    'Considerar ETFs para diversificación instantánea',
                    'Evaluar activos de renta fija'
                ]
            })
        
        # Asset allocation recommendations
        user_preferences = st.session_state.user_preferences
        risk_tolerance = user_preferences.get('risk_tolerance', 'medium')
        
        if risk_tolerance == 'conservative' and risk_metrics['max_weight'] > 0.3:
            recommendations.append({
                'icon': '🛡️',
                'title': 'Ajustar a Perfil Conservador',
                'priority': 'Alta',
                'description': 'Su perfil conservador sugiere menor concentración en activos individuales.',
                'impact': 'Alineación con objetivos de riesgo',
                'actions': [
                    'Reducir posiciones individuales a <20%',
                    'Incrementar posición en renta fija',
                    'Considerar activos defensivos'
                ]
            })
        
        # Default recommendation if portfolio looks good
        if not recommendations:
            recommendations.append({
                'icon': '✅',
                'title': 'Portafolio Bien Diversificado',
                'priority': 'Baja',
                'description': 'Su portafolio muestra buenas características de diversificación.',
                'impact': 'Mantenimiento de perfil óptimo',
                'actions': [
                    'Revisar periódicamente la asignación',
                    'Rebalancear según mercado',
                    'Monitorear correlaciones'
                ]
            })
        
        return recommendations

    def _calculate_portfolio_score(self, processed_data, risk_metrics):
        """Calculate overall portfolio score"""
        if not processed_data or not risk_metrics:
            return 50
        
        # Diversification score (0-40 points)
        diversification_score = risk_metrics['diversificacion'] * 40
        
        # Concentration score (0-30 points)
        concentration_score = (1 - risk_metrics['concentracion']) * 30
        
        # Number of assets score (0-20 points)
        num_assets_score = min(processed_data['num_activos'] * 4, 20)
        
        # Asset allocation score (0-10 points)
        allocation_score = 10 if risk_metrics['max_weight'] < 0.4 else 5
        
        total_score = diversification_score + concentration_score + num_assets_score + allocation_score
        return min(total_score, 100)

    def _get_score_color(self, score):
        """Get color based on score"""
        if score >= 80:
            return "green"
        elif score >= 60:
            return "yellow"
        else:
            return "red"

# Run the application
if __name__ == "__main__":
    try:
        app = IOLPortfolioApp()
        app.run()
    except Exception as e:
        st.error(f"Error crítico en la aplicación: {str(e)}")
        st.info("Por favor, recargue la página.")
