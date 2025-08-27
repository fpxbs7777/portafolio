import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configuración de la página con tema oscuro
st.set_page_config(
    page_title="📊 IOL Portfolio Analyzer Pro",
    page_icon="��",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para tema oscuro
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stApp {
        background-color: #0e1117;
    }
    .stSidebar {
        background-color: #262730;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    .metric-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #4CAF50;
        margin: 10px 0;
    }
    .section-header {
        color: #4CAF50;
        font-size: 24px;
        font-weight: bold;
        margin: 20px 0 10px 0;
        border-bottom: 2px solid #4CAF50;
        padding-bottom: 5px;
    }
    .error-message {
        background-color: #ff4444;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .success-message {
        background-color: #4CAF50;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

class PortfolioAnalyzer:
    """Clase mejorada para análisis de portafolios con manejo de errores"""
    
    def __init__(self, symbols, start_date, end_date):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.returns = None
        self.cov_matrix = None
        self.correlation_matrix = None
        
    def fetch_data(self):
        """Obtiene datos de Yahoo Finance con manejo de errores"""
        try:
            data = {}
            for symbol in self.symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(start=self.start_date, end=self.end_date)
                    if not hist.empty:
                        data[symbol] = hist['Close']
                    else:
                        st.warning(f"No se pudieron obtener datos para {symbol}")
                except Exception as e:
                    st.error(f"Error al obtener datos de {symbol}: {str(e)}")
                    continue
            
            if data:
                self.data = pd.DataFrame(data)
                self.data = self.data.dropna()
                if len(self.data) > 0:
                    self.calculate_returns()
                    return True
                else:
                    st.error("No hay datos suficientes después de limpiar valores nulos")
                    return False
            else:
                st.error("No se pudieron obtener datos para ningún símbolo")
                return False
                
        except Exception as e:
            st.error(f"Error general al obtener datos: {str(e)}")
            return False
    
    def calculate_returns(self):
        """Calcula retornos logarítmicos con validación"""
        try:
            if self.data is not None and len(self.data) > 1:
                self.returns = np.log(self.data / self.data.shift(1)).dropna()
                
                # Validar que los retornos sean finitos
                if not np.all(np.isfinite(self.returns)):
                    st.warning("Se encontraron valores infinitos en los retornos. Limpiando...")
                    self.returns = self.returns.replace([np.inf, -np.inf], np.nan).dropna()
                
                if len(self.returns) > 0:
                    self.calculate_covariance()
                    return True
                else:
                    st.error("No hay retornos válidos después de la limpieza")
                    return False
            else:
                st.error("Datos insuficientes para calcular retornos")
                return False
                
        except Exception as e:
            st.error(f"Error al calcular retornos: {str(e)}")
            return False
    
    def calculate_covariance(self):
        """Calcula matriz de covarianza y correlación"""
        try:
            if self.returns is not None and len(self.returns) > 0:
                # Usar método robusto para covarianza
                self.cov_matrix = self.returns.cov() * 252  # Anualización
                self.correlation_matrix = self.returns.corr()
                
                # Validar matrices
                if self.cov_matrix.isnull().any().any():
                    st.warning("Se encontraron valores nulos en la matriz de covarianza")
                    self.cov_matrix = self.cov_matrix.fillna(0)
                
                return True
            else:
                st.error("No hay retornos para calcular covarianza")
                return False
                
        except Exception as e:
            st.error(f"Error al calcular covarianza: {str(e)}")
            return False
    
    def calculate_portfolio_metrics(self, weights):
        """Calcula métricas del portafolio con validación robusta"""
        try:
            if self.returns is None or self.cov_matrix is None:
                st.error("Datos no disponibles para cálculo de métricas")
                return None
            
            if len(weights) != len(self.symbols):
                st.error("Número de pesos no coincide con símbolos")
                return None
            
            # Validar pesos
            weights = np.array(weights)
            if not np.all(np.isfinite(weights)):
                st.error("Pesos contienen valores no válidos")
                return None
            
            # Normalizar pesos
            weights = weights / np.sum(weights)
            
            # Calcular retorno esperado anualizado
            expected_return = np.sum(self.returns.mean() * weights) * 252
            
            # Calcular volatilidad
            portfolio_variance = np.dot(weights.T, np.dot(self.cov_matrix, weights))
            portfolio_std = np.sqrt(portfolio_variance)
            
            # Calcular Sharpe ratio (asumiendo tasa libre de riesgo del 2%)
            risk_free_rate = 0.02
            sharpe_ratio = (expected_return - risk_free_rate) / portfolio_std if portfolio_std > 0 else 0
            
            # Calcular VaR (Value at Risk) al 95%
            portfolio_returns = np.dot(self.returns, weights)
            var_95 = np.percentile(portfolio_returns, 5)
            
            # Calcular máximo drawdown
            cumulative_returns = (1 + portfolio_returns).cumprod()
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdown)
            
            return {
                'expected_return': expected_return,
                'volatility': portfolio_std,
                'sharpe_ratio': sharpe_ratio,
                'var_95': var_95,
                'max_drawdown': max_drawdown,
                'weights': weights
            }
            
        except Exception as e:
            st.error(f"Error al calcular métricas del portafolio: {str(e)}")
            return None
    
    def optimize_portfolio(self, optimization_type='sharpe', target_return=None):
        """Optimización de portafolio con diferentes estrategias"""
        try:
            if self.returns is None or self.cov_matrix is None:
                st.error("Datos no disponibles para optimización")
                return None
            
            n_assets = len(self.symbols)
            
            if optimization_type == 'equal_weight':
                weights = np.ones(n_assets) / n_assets
                
            elif optimization_type == 'min_variance':
                # Optimización de mínima varianza
                from scipy.optimize import minimize
                
                def objective(weights):
                    return np.dot(weights.T, np.dot(self.cov_matrix, weights))
                
                constraints = [
                    {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Suma de pesos = 1
                ]
                bounds = [(0, 1) for _ in range(n_assets)]  # Pesos entre 0 y 1
                
                result = minimize(objective, np.ones(n_assets) / n_assets, 
                                method='SLSQP', bounds=bounds, constraints=constraints)
                
                if result.success:
                    weights = result.x
                else:
                    st.warning("Optimización falló, usando pesos iguales")
                    weights = np.ones(n_assets) / n_assets
                    
            elif optimization_type == 'max_sharpe':
                # Optimización de máximo Sharpe ratio
                from scipy.optimize import minimize
                
                def objective(weights):
                    portfolio_return = np.sum(self.returns.mean() * weights) * 252
                    portfolio_std = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
                    if portfolio_std > 0:
                        return -(portfolio_return - 0.02) / portfolio_std
                    return 0
                
                constraints = [
                    {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                ]
                bounds = [(0, 1) for _ in range(n_assets)]
                
                result = minimize(objective, np.ones(n_assets) / n_assets,
                                method='SLSQP', bounds=bounds, constraints=constraints)
                
                if result.success:
                    weights = result.x
                else:
                    st.warning("Optimización falló, usando pesos iguales")
                    weights = np.ones(n_assets) / n_assets
            
            else:
                st.error("Tipo de optimización no válido")
                return None
            
            # Normalizar pesos
            weights = weights / np.sum(weights)
            
            return self.calculate_portfolio_metrics(weights)
            
        except Exception as e:
            st.error(f"Error en optimización del portafolio: {str(e)}")
            return None
    
    def plot_portfolio_analysis(self, portfolio_metrics):
        """Genera gráficos de análisis del portafolio"""
        try:
            if portfolio_metrics is None:
                st.error("No hay métricas para graficar")
                return
            
            # Crear subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Distribución de Pesos', 'Retorno vs Riesgo', 
                              'Correlación de Activos', 'Métricas del Portafolio'),
                specs=[[{"type": "bar"}, {"type": "scatter"}],
                       [{"type": "heatmap"}, {"type": "indicator"}]]
            )
            
            # Gráfico 1: Distribución de pesos
            fig.add_trace(
                go.Bar(x=self.symbols, y=portfolio_metrics['weights'], 
                      name='Pesos', marker_color='#4CAF50'),
                row=1, col=1
            )
            
            # Gráfico 2: Retorno vs Riesgo
            fig.add_trace(
                go.Scatter(x=[portfolio_metrics['volatility']], 
                          y=[portfolio_metrics['expected_return']],
                          mode='markers', name='Portafolio',
                          marker=dict(size=15, color='#4CAF50')),
                row=1, col=2
            )
            
            # Gráfico 3: Matriz de correlación
            if self.correlation_matrix is not None:
                fig.add_trace(
                    go.Heatmap(z=self.correlation_matrix.values,
                              x=self.correlation_matrix.index,
                              y=self.correlation_matrix.columns,
                              colorscale='RdBu', zmid=0),
                    row=2, col=1
                )
            
            # Gráfico 4: Métricas principales
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=portfolio_metrics['sharpe_ratio'],
                    title={'text': "Sharpe Ratio"},
                    delta={'reference': 1.0},
                    gauge={'axis': {'range': [-1, 3]},
                           'bar': {'color': "#4CAF50"},
                           'steps': [{'range': [-1, 0], 'color': "lightgray"},
                                    {'range': [0, 1], 'color': "yellow"},
                                    {'range': [1, 3], 'color': "green"}]}
                ),
                row=2, col=2
            )
            
            fig.update_layout(
                height=800,
                showlegend=False,
                title_text="Análisis Completo del Portafolio",
                title_x=0.5,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#fafafa')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error al generar gráficos: {str(e)}")

def main():
    """Función principal de la aplicación"""
    
    # Título principal
    st.markdown('<h1 class="section-header">📊 IOL Portfolio Analyzer Pro</h1>', unsafe_allow_html=True)
    st.markdown("### Análisis Avanzado de Portafolios de Inversión")
    
    # Sidebar para configuración
    with st.sidebar:
        st.markdown('<h3 class="section-header">⚙️ Configuración</h3>', unsafe_allow_html=True)
        
        # Selección de símbolos
        symbols_input = st.text_area(
            "Símbolos de Acciones (uno por línea):",
            value="AAPL\nMSFT\nGOOGL\nAMZN\nTSLA",
            height=100
        )
        
        symbols = [s.strip().upper() for s in symbols_input.split('\n') if s.strip()]
        
        # Fechas
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Fecha de Inicio:",
                value=datetime.now() - timedelta(days=365)
            )
        with col2:
            end_date = st.date_input(
                "Fecha de Fin:",
                value=datetime.now()
            )
        
        # Tipo de optimización
        optimization_type = st.selectbox(
            "Tipo de Optimización:",
            ["equal_weight", "min_variance", "max_sharpe"]
        )
        
        # Botón de análisis
        analyze_button = st.button("🚀 Analizar Portafolio", type="primary")
    
    # Contenido principal
    if analyze_button and symbols:
        try:
            # Crear instancia del analizador
            analyzer = PortfolioAnalyzer(symbols, start_date, end_date)
            
            # Mostrar progreso
            with st.spinner("Obteniendo datos de mercado..."):
                if analyzer.fetch_data():
                    st.success("✅ Datos obtenidos exitosamente")
                    
                    # Mostrar información básica
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Activos", len(symbols))
                    with col2:
                        st.metric("Período de Análisis", f"{(end_date - start_date).days} días")
                    with col3:
                        st.metric("Observaciones", len(analyzer.data))
                    
                    # Análisis del portafolio
                    st.markdown('<h2 class="section-header">📈 Análisis del Portafolio</h2>', unsafe_allow_html=True)
                    
                    with st.spinner("Optimizando portafolio..."):
                        portfolio_metrics = analyzer.optimize_portfolio(optimization_type)
                    
                    if portfolio_metrics:
                        # Mostrar métricas principales
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            st.metric("Retorno Esperado", f"{portfolio_metrics['expected_return']:.2%}")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            st.metric("Volatilidad", f"{portfolio_metrics['volatility']:.2%}")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col3:
                            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            st.metric("Sharpe Ratio", f"{portfolio_metrics['sharpe_ratio']:.2f}")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col4:
                            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            st.metric("VaR 95%", f"{portfolio_metrics['var_95']:.2%}")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Gráficos de análisis
                        st.markdown('<h2 class="section-header">�� Visualizaciones</h2>', unsafe_allow_html=True)
                        analyzer.plot_portfolio_analysis(portfolio_metrics)
                        
                        # Tabla de pesos
                        st.markdown('<h2 class="section-header">⚖️ Distribución de Pesos</h2>', unsafe_allow_html=True)
                        weights_df = pd.DataFrame({
                            'Activo': symbols,
                            'Peso (%)': [f"{w*100:.2f}%" for w in portfolio_metrics['weights']]
                        })
                        st.dataframe(weights_df, use_container_width=True)
                        
                    else:
                        st.error("❌ No se pudieron calcular las métricas del portafolio")
                        
                else:
                    st.error("❌ Error al obtener datos del mercado")
                    
        except Exception as e:
            st.error(f"❌ Error general en el análisis: {str(e)}")
            st.info("💡 Verifique que los símbolos sean válidos y las fechas sean correctas")
    
    elif not symbols:
        st.warning("⚠️ Por favor, ingrese al menos un símbolo de acción")
    
    # Información adicional
    with st.expander("ℹ️ Información del Análisis"):
        st.markdown("""
        **Métricas Calculadas:**
        - **Retorno Esperado**: Retorno anualizado esperado del portafolio
        - **Volatilidad**: Desviación estándar anualizada de los retornos
        - **Sharpe Ratio**: Relación retorno-riesgo (mayor es mejor)
        - **VaR 95%**: Pérdida máxima esperada con 95% de confianza
        - **Máximo Drawdown**: Mayor caída desde un pico
        
        **Tipos de Optimización:**
        - **Pesos Iguales**: Distribución uniforme entre todos los activos
        - **Mínima Varianza**: Minimiza la volatilidad del portafolio
        - **Máximo Sharpe**: Maximiza la relación retorno-riesgo
        """)

if __name__ == "__main__":
    main()
