import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
from datetime import date, timedelta, datetime
import numpy as np
import yfinance as yf
import scipy.optimize as op
from scipy import stats # Added for skewness, kurtosis, jarque_bera
import random
import warnings
import streamlit.components.v1 as components

warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="IOL Portfolio Analyzer",
    page_icon="📊",
    layout="wide"
)

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
        respuesta = requests.post(url_login, data=datos, timeout=15) # Added timeout
        respuesta.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
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
    except requests.exceptions.ConnectionError as conn_err:
        st.error(f'Error de conexión al intentar obtener tokens: {conn_err}')
        st.warning("No se pudo conectar al servidor de IOL. Verifique su conexión a internet y que el servicio de IOL esté disponible.")
        return None, None
    except requests.exceptions.Timeout as timeout_err:
        st.error(f'Timeout al intentar obtener tokens: {timeout_err}')
        st.warning("La solicitud a IOL tardó demasiado en responder. Intente más tarde.")
        return None, None
    except requests.exceptions.RequestException as req_err: # Catch any other requests error
        st.error(f'Error en la solicitud al obtener tokens: {req_err}')
        return None, None
    except Exception as e: # General fallback
        st.error(f'Error inesperado al obtener tokens: {str(e)}')
        return None, None

def obtener_lista_clientes(token_portador):
    url_clientes = 'https://api.invertironline.com/api/v2/Asesores/Clientes'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    try:
        respuesta = requests.get(url_clientes, headers=encabezados)
        if respuesta.status_code == 200:
            clientes_data = respuesta.json()
            # Debug: mostrar estructura de respuesta
            st.info(f"📋 Estructura de respuesta de clientes: {type(clientes_data)}")
            if isinstance(clientes_data, list):
                return clientes_data
            elif isinstance(clientes_data, dict) and 'clientes' in clientes_data:
                return clientes_data['clientes']
            else:
                st.warning(f"Estructura de datos inesperada: {clientes_data}")
                return []
        else:
            st.error(f'Error al obtener la lista de clientes: {respuesta.status_code}')
            st.error(f'Respuesta: {respuesta.text}')
            return []
    except Exception as e:
        st.error(f'Error de conexión al obtener clientes: {str(e)}')
        return []

def obtener_estado_cuenta(token_portador, id_cliente=None):
    """
    Obtiene el estado de cuenta del usuario autenticado o cliente específico
    """
    # Usar endpoint directo para usuario autenticado o endpoint de asesor para cliente específico
    if id_cliente:
        url_estado_cuenta = f'https://api.invertironline.com/api/v2/Asesores/EstadoDeCuenta/{id_cliente}'
    else:
        url_estado_cuenta = 'https://api.invertironline.com/api/v2/estadocuenta'
    
    encabezados = obtener_encabezado_autorizacion(token_portador)
    try:
        respuesta = requests.get(url_estado_cuenta, headers=encabezados)
        st.info(f"💰 Solicitando estado de cuenta - URL: {url_estado_cuenta}")
        st.info(f"📊 Status Code: {respuesta.status_code}")
        
        if respuesta.status_code == 200:
            estado_data = respuesta.json()
            st.success(f"✅ Estado de cuenta obtenido exitosamente")
            return estado_data
        elif respuesta.status_code == 401:
            st.warning(f"🔐 No autorizado - Token inválido o permisos insuficientes")
            if id_cliente:
                st.info("💡 Intentando con endpoint directo sin ID de cliente...")
                # Intentar con endpoint directo
                return obtener_estado_cuenta(token_portador, None)
            return None
        elif respuesta.status_code == 404:
            st.warning(f"⚠️ Estado de cuenta no encontrado")
            return None
        else:
            st.error(f'❌ Error al obtener estado de cuenta: {respuesta.status_code}')
            st.error(f'📄 Respuesta: {respuesta.text}')
            return None
    except Exception as e:
        st.error(f'💥 Error de conexión al obtener estado de cuenta: {str(e)}')
        return None

def obtener_portafolio(token_portador, id_cliente, pais='Argentina'):
    url_portafolio = f'https://api.invertironline.com/api/v2/Asesores/Portafolio/{id_cliente}/{pais}'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    try:
        respuesta = requests.get(url_portafolio, headers=encabezados)
        st.info(f"🔍 Solicitando portafolio para cliente {id_cliente}")
        st.info(f"📡 URL: {url_portafolio}")
        st.info(f"📊 Status Code: {respuesta.status_code}")
        
        if respuesta.status_code == 200:
            portafolio_data = respuesta.json()
            st.success(f"✅ Portafolio obtenido exitosamente")
            st.info(f"📋 Estructura de portafolio: {type(portafolio_data)}")
            if isinstance(portafolio_data, dict):
                st.info(f"🔑 Claves disponibles: {list(portafolio_data.keys())}")
            return portafolio_data
        elif respuesta.status_code == 404:
            st.warning(f"⚠️ Cliente {id_cliente} no encontrado o sin portafolio")
            return None
        elif respuesta.status_code == 401:
            st.error("🔐 Token de autorización expirado o inválido")
            return None
        else:
            st.error(f'❌ Error al obtener portafolio: {respuesta.status_code}')
            st.error(f'📄 Respuesta: {respuesta.text}')
            return None
    except Exception as e:
        st.error(f'💥 Error de conexión al obtener portafolio: {str(e)}')
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
            return respuesta.json()
        else:
            return None
    except Exception as e:
        st.error(f'Error al obtener cotización MEP: {str(e)}')
        return None

def obtener_tasas_caucion(token_portador, instrumento="Cauciones", panel="Todas", pais="Argentina"):
    url = f"https://api.invertironline.com/api/v2/Cotizaciones/{instrumento}/{panel}/{pais}"
    headers = {
        "Authorization": f"Bearer {token_portador}"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f'Error al obtener tasas de caución: {str(e)}')
        return None

def obtener_cotizacion_actual(token_portador, mercado, simbolo):
    """
    Obtiene la cotización actual de un título desde la API de IOL.
    """
    url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion"
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener la cotización actual para {simbolo}: {response.status_code}")
            return None
    except Exception as e:
        st.error(f'Error al obtener cotización actual: {str(e)}')
        return None

def parse_datetime_flexible(datetime_string):
    """
    Parse datetime strings with flexible format handling
    """
    if not datetime_string:
        return None
    
    # Common datetime formats from IOL API
    formats_to_try = [
        "%Y-%m-%dT%H:%M:%S.%f",  # With microseconds
        "%Y-%m-%dT%H:%M:%S",     # Without microseconds
        "%Y-%m-%d %H:%M:%S.%f",  # Space separator with microseconds
        "%Y-%m-%d %H:%M:%S",     # Space separator without microseconds
        "ISO8601",               # Let pandas infer ISO format
        "mixed"                  # Let pandas infer mixed formats
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

    # Final fallback - let pandas infer automatically
    try:
        return pd.to_datetime(datetime_string, infer_datetime_format=True)
    except Exception:
        return None

def obtener_serie_historica_iol(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="ajustada"):
    """
    Obtiene la serie histórica de precios de un título desde la API de IOL.
    Actualizada para manejar correctamente la estructura de respuesta de la API.
    """
    # Determinar endpoint según tipo de instrumento
    if mercado == "Opciones":
        url = f"https://api.invertironline.com/api/v2/Opciones/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    elif mercado == "FCI":
        url = f"https://api.invertironline.com/api/v2/FCI/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    else:
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
                    
                    fecha_str = item.get('fechaHora')
                    
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
            # Token expirado o inválido
            st.warning(f"⚠️ Token de autorización inválido para {simbolo}")
            return None
            
        elif response.status_code == 404:
            # Símbolo no encontrado en este mercado
            return None
            
        elif response.status_code == 400:
            # Parámetros inválidos
            st.warning(f"⚠️ Parámetros inválidos para {simbolo} en {mercado}")
            return None
            
        elif response.status_code == 500:
            # Error del servidor - silencioso para no interrumpir el flujo
            return None
            
        else:
            # Otros errores HTTP
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
            except:
                continue
        
        # Intentar sin sufijo
        try:
            ticker = yf.Ticker(simbolo)
            data = ticker.history(start=fecha_desde, end=fecha_hasta)
            if not data.empty and len(data) > 10:
                return data['Close']
        except:
            pass
            
        return None
    except Exception:
        return None

# Eliminar la función duplicada get_historical_data_for_optimization y usar solo una versión
# Eliminar la clase PortfolioManager duplicada y usar solo una versión

# Agregar la clase manager que falta
class manager:
    def __init__(self, rics, notional, data):
        self.rics = rics
        self.notional = notional
        self.data = data
        self.timeseries = None
        self.returns = None
        self.cov_matrix = None
        self.mean_returns = None

    def load_intraday_timeseries(self, ticker):
        return self.data[ticker]

    def synchronise_timeseries(self):
        dic_timeseries = {}
        for ric in self.rics:
            dic_timeseries[ric] = self.load_intraday_timeseries(ric)
        self.timeseries = dic_timeseries

    def compute_covariance(self):
        self.synchronise_timeseries()
        returns_matrix = {}
        for ric in self.rics:
            prices = self.timeseries[ric]
            returns_matrix[ric] = np.log(prices / prices.shift(1)).dropna()
        
        self.returns = pd.DataFrame(returns_matrix)
        self.cov_matrix = self.returns.cov() * 252
        self.mean_returns = self.returns.mean() * 252
        
        return self.cov_matrix, self.mean_returns

    def compute_portfolio(self, portfolio_type=None, target_return=None):
        if self.cov_matrix is None:
            self.compute_covariance()
            
        n_assets = len(self.rics)
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        if portfolio_type == 'equi-weight':
            weights = np.ones(n_assets) / n_assets
            return self._create_output(weights)
        else:
            # Optimización básica
            constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
            
            def portfolio_volatility(weights):
                return np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
            
            result = op.minimize(
                portfolio_volatility, 
                x0=np.ones(n_assets)/n_assets,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            return self._create_output(result.x)

    def _create_output(self, weights):
        portfolio_returns = self.returns.dot(weights)
        port_output = output(portfolio_returns, self.notional)
        port_output.weights = weights
        port_output.dataframe_allocation = pd.DataFrame({
            'rics': self.rics,
            'weights': weights,
            'volatilities': np.sqrt(np.diag(self.cov_matrix)),
            'returns': self.mean_returns
        })
        return port_output

# Agregar la clase output que falta
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
        
        self.weights = None
        self.dataframe_allocation = None

    def get_metrics_dict(self):
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
        if self.returns is None or len(self.returns) == 0:
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
            name="Retornos del Portafolio"
        )])
        
        fig.add_vline(x=self.mean_daily, line_dash="dash", line_color="red", 
                     annotation_text=f"Media: {self.mean_daily:.4f}")
        fig.add_vline(x=self.var_95, line_dash="dash", line_color="orange", 
                     annotation_text=f"VaR 95%: {self.var_95:.4f}")
        
        fig.update_layout(
            title=f"{title}",
            xaxis_title="Retorno",
            yaxis_title="Frecuencia",
            showlegend=False
        )
        
        return fig

# --- Portfolio Manager ---
class PortfolioManager:
    """
    Clase para manejo de portafolio y optimización con funcionalidades extendidas
    """
    def __init__(self, symbols, token, fecha_desde, fecha_hasta, activos_portafolio=None):
        self.symbols = symbols
        self.token = token
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.activos_portafolio = activos_portafolio
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
                self.token, self.symbols, self.fecha_desde, self.fecha_hasta, self.activos_portafolio
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
    
    def compute_portfolio(self, strategy='markowitz', target_return=None):
        """
        Computa la optimización del portafolio con estrategias extendidas
        """
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
                    weights = np.array([1/n_assets] * n_assets)
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
            st.error(f"Error en optimización: {str(e)}")
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
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            clases = response.json()
            for clase in clases:
                if clase.get('simbolo', '').endswith('D'):
                    return clase['simbolo']
            return None
        else:
            return None
    except Exception:
        return None

def calcular_metricas_portafolio(activos_data, valor_total):
    """
    Calcula métricas comprehensivas del portafolio incluyendo P&L, quantiles y probabilidades
    """
    try:
        # Calcular estadísticas básicas
        valores = [activo['Valuación'] for activo in activos_data if activo['Valuación'] > 0]
        
        if not valores:
            return None
        
        # Convertir a numpy array para cálculos
        valores_array = np.array(valores)
        
        # Estadísticas básicas
        media = np.mean(valores_array)
        mediana = np.median(valores_array)
        std_dev = np.std(valores_array)
        var_95 = np.percentile(valores_array, 5)  # VaR al 5%
        var_99 = np.percentile(valores_array, 1)  # VaR al 1%
        
        # Quantiles
        q25 = np.percentile(valores_array, 25)
        q50 = np.percentile(valores_array, 50)  # Mediana
        q75 = np.percentile(valores_array, 75)
        q90 = np.percentile(valores_array, 90)
        q95 = np.percentile(valores_array, 95)
        
        # Calcular concentración del portafolio
        pesos = valores_array / valor_total
        concentracion = np.sum(pesos ** 2)  # Índice de Herfindahl
        
        # Simular retornos esperados (usando distribución normal)
        # Asumiendo retorno anual promedio del 8% con volatilidad del 20%
        retorno_esperado_anual = 0.08
        volatilidad_anual = 0.20
        
        # Calcular métricas en términos monetarios
        retorno_esperado_pesos = valor_total * retorno_esperado_anual
        riesgo_anual_pesos = valor_total * volatilidad_anual
        
        # Simulación Monte Carlo simple para P&L esperado
        np.random.seed(42)
        num_simulaciones = 1000
        retornos_simulados = np.random.normal(retorno_esperado_anual, volatilidad_anual, num_simulaciones)
        pl_simulado = valor_total * retornos_simulados
        
        # Probabilidades
        prob_ganancia = np.sum(pl_simulado > 0) / num_simulaciones
        prob_perdida = np.sum(pl_simulado < 0) / num_simulaciones
        prob_perdida_mayor_10 = np.sum(pl_simulado < -valor_total * 0.10) / num_simulaciones
        prob_ganancia_mayor_10 = np.sum(pl_simulado > valor_total * 0.10) / num_simulaciones
        
        return {
            'valor_total': valor_total,
            'media_activo': media,
            'mediana_activo': mediana,
            'std_dev_activo': std_dev,
            'var_95': var_95,
            'var_99': var_99,
            'quantiles': {
                'q25': q25,
                'q50': q50,
                'q75': q75,
                'q90': q90,
                'q95': q95
            },
            'concentracion': concentracion,
            'retorno_esperado_anual': retorno_esperado_pesos,
            'riesgo_anual': riesgo_anual_pesos,
            'pl_esperado_min': np.min(pl_simulado),
            'pl_esperado_max': np.max(pl_simulado),
            'pl_esperado_medio': np.mean(pl_simulado),
            'pl_percentil_5': np.percentile(pl_simulado, 5),
            'pl_percentil_95': np.percentile(pl_simulado, 95),
            'probabilidades': {
                'ganancia': prob_ganancia,
                'perdida': prob_perdida,
                'perdida_mayor_10': prob_perdida_mayor_10,
                'ganancia_mayor_10': prob_ganancia_mayor_10
            }
        }
    except Exception as e:
        st.error(f"Error calculando métricas del portafolio: {str(e)}")
        return None

def mostrar_resumen_portafolio(portafolio):
    """
    Muestra un resumen comprehensivo del portafolio con valuación corregida y métricas avanzadas
    """
    st.markdown("### 📈 Resumen del Portafolio")
    
    activos = portafolio.get('activos', [])
    
    # Preparar datos para análisis con mejor extracción de valuación
    datos_activos = []
    valor_total = 0
    
    for activo in activos:
        try:
            titulo = activo.get('titulo', {})
            simbolo = titulo.get('simbolo', 'N/A')
            descripcion = titulo.get('descripcion', 'Sin descripción')
            tipo = titulo.get('tipo', 'N/A')
            cantidad = activo.get('cantidad', 0)
            
            # Mejorar extracción de valuación con más campos posibles
            valuacion = 0
            
            # Campos de valuación en orden de preferencia (más específicos primero)
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
            
            for campo in campos_valuacion:
                if campo in activo and activo[campo] is not None:
                    try:
                        val = float(activo[campo])
                        if val > 0:  # Solo usar valores positivos
                            valuacion = val
                            break
                    except (ValueError, TypeError):
                        continue
            
            # Si no se encuentra valuación directa, intentar calcular
            if valuacion == 0 and cantidad:
                # Buscar precio unitario
                precio_unitario = 0
                campos_precio = [
                    'precioPromedio',
                    'precioCompra',
                    'precioActual',
                    'precio',
                    'precioUnitario',
                    'ultimoPrecio',
                    'cotizacion'
                ]
                
                # Buscar en activo
                for campo in campos_precio:
                    if campo in activo and activo[campo] is not None:
                        try:
                            precio = float(activo[campo])
                            if precio > 0:
                                precio_unitario = precio
                                break
                        except (ValueError, TypeError):
                            continue
                
                # Buscar en título si no se encontró en activo
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
                
                # Calcular valuación si encontramos precio
                if precio_unitario > 0:
                    try:
                        cantidad_num = float(cantidad)
                        valuacion = cantidad_num * precio_unitario
                    except (ValueError, TypeError):
                        pass
            
            datos_activos.append({
                'Símbolo': simbolo,
                'Descripción': descripcion,
                'Tipo': tipo,
                'Cantidad': cantidad,
                'Valuación': valuacion,
                'Datos_Raw': activo  # Para debug
            })
            
            valor_total += valuacion;
            
        except Exception as e:
            st.warning(f"Error procesando activo: {str(e)}")
            continue
    
    if datos_activos:
        df_activos = pd.DataFrame(datos_activos)
        
        # Calcular métricas comprehensivas del portafolio
        metricas = calcular_metricas_portafolio(datos_activos, valor_total)
        
        # === 1. INFORMACIÓN BÁSICA DEL PORTAFOLIO ===
        st.markdown("#### 📊 Información General")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Activos", len(datos_activos))
        col2.metric("Símbolos Únicos", df_activos['Símbolo'].nunique())
        col3.metric("Tipos de Activos", df_activos['Tipo'].nunique())
        
        # Mostrar el valor total con formato correcto y verificación
        valor_display = f"${valor_total:,.2f}"
        if valor_total > 500000:  # Si parece demasiado alto
            st.warning("⚠️ Verificar: el valor total parece alto")
        col4.metric("Valor Total del Portafolio", valor_display)
        
        # Gráficos de distribución
        if valor_total > 0 and 'Tipo' in df_activos.columns:
            tipo_stats = df_activos.groupby('Tipo').agg({
                'Valuación': ['sum', 'count', 'mean']
            }).round(2)
            tipo_stats.columns = ['Valor_Total', 'Cantidad', 'Valor_Promedio']
            tipo_stats = tipo_stats.reset_index()
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Pie chart por valor
                fig_pie = go.Figure(data=[go.Pie(
                    labels=tipo_stats['Tipo'],
                    values=tipo_stats['Valor_Total'],
                    textinfo='label+percent+value',
                    texttemplate='%{label}<br>%{percent}<br>$%{value:,.0f}',
                )])
                fig_pie.update_layout(title="Distribución por Valor", height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Bar chart por tipo
                fig_bar = go.Figure(data=[go.Bar(
                    x=tipo_stats['Tipo'],
                    y=tipo_stats['Valor_Total'],
                    text=[f"${val:,.0f}" for val in tipo_stats['Valor_Total']],
                    textposition='auto'
                )])
                fig_bar.update_layout(
                    title="Valor por Tipo de Activo",
                    xaxis_title="Tipo",
                    yaxis_title="Valor ($)",
                    height=400
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Tabla de activos
        st.markdown("#### 📋 Detalle de Activos")
        
        df_display = df_activos.copy()
        df_display['Valuación Formateada'] = df_display['Valuación'].apply(
            lambda x: f"${x:,.2f}" if x > 0 else "No disponible"
        )
        df_display['Peso (%)'] = (df_display['Valuación'] / valor_total * 100).round(2) if valor_total > 0 else 0
        
        # Reordenar columnas
        columns_order = ['Símbolo', 'Descripción', 'Tipo', 'Cantidad', 'Valuación Formateada', 'Peso (%)']
        df_display_final = df_display[columns_order]
        df_display_final = df_display_final.rename(columns={'Valuación Formateada': 'Valuación'})
        
        # Ordenar por valuación descendente
        df_display_final = df_display_final.sort_values('Peso (%)', ascending=False)
        
        st.dataframe(df_display_final, use_container_width=True)
    else:
        st.warning("No se pudieron procesar los datos de los activos")

def mostrar_estado_cuenta(estado_cuenta):
    """
    Muestra el estado de cuenta del cliente con parsing mejorado según la estructura de la API
    """
    st.markdown("### 💰 Estado de Cuenta")
    
    if not estado_cuenta:
        st.warning("No hay datos de estado de cuenta disponibles")
        return
    
    # Mostrar información general
    st.markdown("#### 📋 Información General")
    
    # Extraer información según la estructura documentada de la API
    total_en_pesos = estado_cuenta.get('totalEnPesos', 0)
    cuentas = estado_cuenta.get('cuentas', [])
    
    # Calcular totales agregados
    total_disponible = 0
    total_comprometido = 0
    total_saldo = 0
    total_titulos_valorizados = 0
    total_general = 0
    
    for cuenta in cuentas:
        disponible = float(cuenta.get('disponible', 0))
        comprometido = float(cuenta.get('comprometido', 0))
        saldo = float(cuenta.get('saldo', 0))
        titulos_valorizados = float(cuenta.get('titulosValorizados', 0))
        total_cuenta = float(cuenta.get('total', 0))
        
        total_disponible += disponible
        total_comprometido += comprometido
        total_saldo += saldo
        total_titulos_valorizados += titulos_valorizados
        total_general += total_cuenta
    
    # Mostrar métricas principales
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total General", f"${total_general:,.2f}")
    col2.metric("Total en Pesos", f"AR$ {total_en_pesos:,.2f}")
    col3.metric("Disponible Total", f"${total_disponible:,.2f}")
    col4.metric("Títulos Valorizados", f"${total_titulos_valorizados:,.2f}")

def mostrar_cotizaciones_mercado(token_acceso):
    """
    Muestra cotizaciones y datos de mercado
    """
    st.markdown("### 💱 Cotizaciones y Mercado")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💰 Cotización MEP")
        
        # Formulario para consultar MEP
        with st.form("mep_form"):
            simbolo_mep = st.text_input("Símbolo para MEP", value="AL30", help="Ej: AL30, GD30, etc.")
            id_plazo_compra = st.number_input("ID Plazo Compra", value=1, min_value=1)
            id_plazo_venta = st.number_input("ID Plazo Venta", value=1, min_value=1)
            
            if st.form_submit_button("Consultar MEP"):
                if simbolo_mep:
                    with st.spinner("Consultando cotización MEP..."):
                        cotizacion_mep = obtener_cotizacion_mep(
                            token_acceso, simbolo_mep, id_plazo_compra, id_plazo_venta
                        )
                    
                    if cotizacion_mep:
                        st.success("✅ Cotización MEP obtenida")
                        
                        # Mostrar datos de MEP
                        if isinstance(cotizacion_mep, dict):
                            # Extraer precio si está disponible
                            precio_mep = cotizacion_mep.get('precio', cotizacion_mep.get('cotizacion', 'N/A'))
                            
                            col_mep1, col_mep2 = st.columns(2)
                            col_mep1.metric("Símbolo", simbolo_mep)
                            col_mep2.metric("Precio MEP", f"${precio_mep}" if precio_mep != 'N/A' else 'N/A')
                        
                        with st.expander("Ver detalles MEP"):
                            st.json(cotizacion_mep)
                    else:
                        st.error("❌ No se pudo obtener la cotización MEP")
    
    with col2:
        st.markdown("#### 🏦 Tasas de Caución")
        
        if st.button("🔄 Actualizar Tasas de Caución"):
            with st.spinner("Consultando tasas de caución..."):
                tasas_caucion = obtener_tasas_caucion(token_acceso)
            
            if tasas_caucion:
                st.success("✅ Tasas de caución obtenidas")
                
                # Mostrar tasas si es una lista
                if isinstance(tasas_caucion, list) and tasas_caucion:
                    df_tasas = pd.DataFrame(tasas_caucion)
                    
                    # Mostrar solo columnas relevantes si están disponibles
                    columnas_relevantes = ['simbolo', 'tasa', 'bid', 'offer', 'ultimo']
                    columnas_disponibles = [col for col in columnas_relevantes if col in df_tasas.columns]
                    
                    if columnas_disponibles:
                        st.dataframe(df_tasas[columnas_disponibles].head(10))
                    else:
                        st.dataframe(df_tasas.head(10))
                
                with st.expander("Ver datos completos de caución"):
                    st.json(tasas_caucion)
            else:
                st.error("❌ No se pudieron obtener las tasas de caución")

def mostrar_analisis_portafolio():
    """
    Función principal para mostrar el análisis del portafolio del cliente seleccionado
    """
    cliente = st.session_state.cliente_seleccionado
    token_acceso = st.session_state.token_acceso
    fecha_desde = st.session_state.fecha_desde
    fecha_hasta = st.session_state.fecha_hasta

    if not cliente:
        st.error("No hay cliente seleccionado")
        return

    # Obtener ID del cliente
    id_cliente = cliente.get('numeroCliente', cliente.get('id'))
    nombre_cliente = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))

    st.title(f"📊 Análisis de Portafolio - {nombre_cliente}")

    # Crear tabs para diferentes análisis
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Resumen", 
        "💰 Estado de Cuenta", 
        "🎯 Optimización", 
        "📊 Análisis Técnico",
        "💱 Cotizaciones"
    ])

    with tab1:
        # Obtener portafolio
        with st.spinner("Cargando portafolio..."):
            portafolio = obtener_portafolio(token_acceso, id_cliente)
        
        if portafolio:
            mostrar_resumen_portafolio(portafolio)
        else:
            st.warning("No se pudo obtener el portafolio del cliente")

    with tab2:
        # Mostrar estado de cuenta
        with st.spinner("Cargando estado de cuenta..."):
            estado_cuenta = obtener_estado_cuenta(token_acceso, id_cliente)
        
        if estado_cuenta:
            mostrar_estado_cuenta(estado_cuenta)
        else:
            st.warning("No se pudo obtener el estado de cuenta")

    with tab3:
        # Optimización de portafolio
        with st.spinner("Cargando portafolio para optimización..."):
            portafolio = obtener_portafolio(token_acceso, id_cliente)
        
        if portafolio:
            mostrar_optimizacion_portafolio(portafolio, token_acceso, fecha_desde, fecha_hasta)
        else:
            st.warning("No se pudo obtener el portafolio para optimización")

    with tab4:
        st.markdown("### 📊 Análisis Técnico")
        st.info("🚧 Funcionalidad en desarrollo")

    with tab5:
        # Cotizaciones y mercado
        mostrar_cotizaciones_mercado(token_acceso)

# Asegurar que main() esté al final y se ejecute
if __name__ == "__main__":
    main()
