import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import yfinance as yf
import scipy.optimize as op
from scipy import stats
from datetime import date, timedelta, datetime
import warnings
import streamlit.components.v1 as components

warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="IOL Portfolio Analyzer Pro",
    page_icon="📊",
    layout="wide"
)

## ----------------------------
## API Functions
## ----------------------------

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
                st.warning(f"Estructura de datos inesperada: {clientes_data}")
                return []
        else:
            st.error(f'Error al obtener la lista de clientes: {respuesta.status_code}')
            return []
    except Exception as e:
        st.error(f'Error de conexión al obtener clientes: {str(e)}')
        return []

def obtener_portafolio(token_portador, id_cliente, pais='Argentina'):
    url_portafolio = f'https://api.invertironline.com/api/v2/Asesores/Portafolio/{id_cliente}/{pais}'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    try:
        respuesta = requests.get(url_portafolio, headers=encabezados)
        if respuesta.status_code == 200:
            return respuesta.json()
        elif respuesta.status_code == 404:
            st.warning(f"⚠️ Cliente {id_cliente} no encontrado o sin portafolio")
            return None
        else:
            st.error(f'❌ Error al obtener portafolio: {respuesta.status_code}')
            return None
    except Exception as e:
        st.error(f'💥 Error de conexión al obtener portafolio: {str(e)}')
        return None

def obtener_serie_historica_iol(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="ajustada"):
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
                    precio = item.get('ultimoPrecio')
                    if not precio or precio == 0:
                        precio = item.get('cierreAnterior') or item.get('precioPromedio') or item.get('apertura')
                    
                    fecha_str = item.get('fechaHora')
                    fecha_parsed = pd.to_datetime(fecha_str) if fecha_str else None
                    
                    if precio is not None and precio > 0 and fecha_parsed is not None:
                        precios.append(precio)
                        fechas.append(fecha_parsed)
                except Exception:
                    continue
            
            if precios and fechas:
                serie = pd.Series(precios, index=fechas)
                serie = serie.sort_index()
                serie = serie[~serie.index.duplicated(keep='last')]
                return serie
            return None
        else:
            return None
    except Exception:
        return None

def obtener_clase_d(simbolo, mercado, bearer_token):
    mercados_mapping = {
        'BCBA': 'bCBA',
        'NYSE': 'nYSE', 
        'NASDAQ': 'nASDAQ',
        'ROFEX': 'rOFEX',
        'Merval': 'bCBA'
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
        return None
    except Exception:
        return None

## ----------------------------
## Portfolio Optimization Classes
## ----------------------------

class PortfolioOutput:
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
        
        # Annualized metrics
        self.return_annual = (1 + self.mean_daily) ** 252 - 1
        self.volatility_annual = self.volatility_daily * np.sqrt(252)
        
        # Placeholders
        self.weights = None
        self.asset_names = None
        self.mean_returns = None
        self.cov_matrix = None
    
    def get_metrics_dict(self):
        return {
            'Retorno Diario': f"{self.mean_daily:.2%}",
            'Volatilidad Diaria': f"{self.volatility_daily:.2%}",
            'Retorno Anual': f"{self.return_annual:.2%}",
            'Volatilidad Anual': f"{self.volatility_annual:.2%}",
            'Ratio de Sharpe': f"{self.sharpe_ratio:.2f}",
            'VaR 95% (Diario)': f"{self.var_95:.2%}",
            'Asimetría': f"{self.skewness:.2f}",
            'Curtosis': f"{self.kurtosis:.2f}",
            'Estadístico JB': f"{self.jb_stat:.2f}",
            'Valor p': f"{self.p_value:.4f}",
            'Distribución Normal': "Sí" if self.is_normal else "No"
        }
    
    def plot_histogram_streamlit(self):
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=self.returns,
            nbinsx=50,
            name="Retornos del Portafolio",
            marker_color='#1f77b4'
        ))
        
        fig.add_vline(x=self.mean_daily, line_dash="dash", line_color="red",
                     annotation_text=f"Media: {self.mean_daily:.2%}")
        fig.add_vline(x=self.var_95, line_dash="dash", line_color="orange",
                     annotation_text=f"VaR 95%: {self.var_95:.2%}")
        
        fig.update_layout(
            title="Distribución de Retornos del Portafolio",
            xaxis_title="Retornos Diarios",
            yaxis_title="Frecuencia",
            showlegend=False
        )
        return fig
    
    def plot_weights_streamlit(self):
        if self.weights is None or self.asset_names is None:
            return None
            
        df_weights = pd.DataFrame({
            'Activo': self.asset_names,
            'Peso': self.weights
        }).sort_values('Peso', ascending=False)
        
        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=df_weights['Activo'],
            values=df_weights['Peso'],
            textinfo='label+percent',
            insidetextorientation='radial'
        ))
        fig.update_layout(
            title="Composición del Portafolio",
            uniformtext_minsize=12,
            uniformtext_mode='hide'
        )
        return fig

class PortfolioManager:
    def __init__(self, symbols, token, fecha_desde, fecha_hasta):
        self.symbols = symbols
        self.token = token
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.data_loaded = False
        self.returns = None
        self.prices = None
        self.notional = 1000000
        self.risk_free_rate = 0.40  # Tasa libre de riesgo anual (ejemplo para Argentina)
        
    def load_data(self):
        try:
            mean_returns, cov_matrix, df_prices = get_historical_data_for_optimization(
                self.token, self.symbols, self.fecha_desde, self.fecha_hasta
            )
            
            if mean_returns is not None and cov_matrix is not None and df_prices is not None:
                self.returns = df_prices.pct_change().dropna()
                self.prices = df_prices
                self.mean_returns = mean_returns
                self.cov_matrix = cov_matrix
                self.data_loaded = True
                return True
            return False
        except Exception as e:
            st.error(f"Error cargando datos: {str(e)}")
            return False
    
    def compute_portfolio(self, strategy='markowitz', target_return=None):
        if not self.data_loaded or self.returns is None:
            return None
            
        n_assets = len(self.returns.columns)
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        if strategy == 'equi-weight':
            weights = np.ones(n_assets) / n_assets
            return self._create_output(weights)
            
        elif strategy == 'min-variance-l1':
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'ineq', 'fun': lambda x: 1 - np.sum(np.abs(x))}
            ]
            objective = lambda x: portfolio_variance(x, self.cov_matrix)
            
        elif strategy == 'min-variance-l2':
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'ineq', 'fun': lambda x: 1 - np.sum(x**2)}
            ]
            objective = lambda x: portfolio_variance(x, self.cov_matrix)
            
        elif strategy == 'long-only':
            constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
            objective = lambda x: portfolio_variance(x, self.cov_matrix)
            
        elif strategy == 'markowitz':
            if target_return is not None:
                constraints = [
                    {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                    {'type': 'eq', 'fun': lambda x: np.sum(self.mean_returns * x) - target_return}
                ]
                objective = lambda x: portfolio_variance(x, self.cov_matrix)
            else:
                constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
                def neg_sharpe_ratio(weights):
                    port_return = np.sum(self.mean_returns * weights)
                    port_vol = np.sqrt(portfolio_variance(weights, self.cov_matrix))
                    return -(port_return - self.risk_free_rate) / port_vol if port_vol > 0 else np.inf
                objective = neg_sharpe_ratio
        
        initial_weights = np.ones(n_assets) / n_assets
        result = op.minimize(
            objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            return self._create_output(result.x)
        return None
    
    def _create_output(self, weights):
        port_returns = (self.returns * weights).sum(axis=1)
        port_output = PortfolioOutput(port_returns, self.notional)
        port_output.weights = weights
        port_output.asset_names = list(self.returns.columns)
        port_output.mean_returns = self.mean_returns
        port_output.cov_matrix = self.cov_matrix
        return port_output
    
    def compute_efficient_frontier(self, n_points=50):
        if not self.data_loaded:
            return None, None
            
        min_return = self.mean_returns.min()
        max_return = self.mean_returns.max()
        target_returns = np.linspace(min_return, max_return, n_points)
        
        frontier_returns = []
        frontier_volatilities = []
        
        for ret in target_returns:
            port = self.compute_portfolio('markowitz', target_return=ret)
            if port:
                frontier_returns.append(port.return_annual)
                frontier_volatilities.append(port.volatility_annual)
        
        return frontier_returns, frontier_volatilities

## ----------------------------
## Utility Functions
## ----------------------------

def portfolio_variance(weights, cov_matrix):
    return np.dot(weights.T, np.dot(cov_matrix, weights))

def get_historical_data_for_optimization(token_portador, simbolos, fecha_desde, fecha_hasta):
    try:
        df_precios = pd.DataFrame()
        simbolos_exitosos = []
        simbolos_fallidos = []
        
        progress_bar = st.progress(0)
        total_symbols = len(simbolos)
        
        for idx, simbolo in enumerate(simbolos):
            progress_bar.progress((idx + 1) / total_symbols, text=f"Procesando {simbolo}...")
            
            mercados = ['bCBA', 'nYSE', 'nASDAQ', 'rOFEX']
            serie_obtenida = False
            
            for mercado in mercados:
                try:
                    simbolo_consulta = simbolo
                    clase_d = obtener_clase_d(simbolo, mercado, token_portador)
                    if clase_d:
                        simbolo_consulta = clase_d
                    
                    serie = obtener_serie_historica_iol(
                        token_portador, mercado, simbolo_consulta,
                        fecha_desde.strftime('%Y-%m-%d'),
                        fecha_hasta.strftime('%Y-%m-%d')
                    )
                    
                    if serie is not None and len(serie) > 10 and serie.nunique() > 1:
                        df_precios[simbolo_consulta] = serie
                        simbolos_exitosos.append(simbolo_consulta)
                        serie_obtenida = True
                        break
                        
                except Exception:
                    continue
            
            if not serie_obtenida:
                try:
                    serie_yf = yf.download(
                        simbolo + '.BA',
                        start=fecha_desde,
                        end=fecha_hasta
                    )['Close']
                    if serie_yf is not None and len(serie_yf) > 10 and serie_yf.nunique() > 1:
                        df_precios[simbolo] = serie_yf
                        simbolos_exitosos.append(simbolo)
                        serie_obtenida = True
                except Exception:
                    pass
            
            if not serie_obtenida:
                simbolos_fallidos.append(simbolo)
        
        progress_bar.empty()
        
        if simbolos_exitosos:
            st.success(f"✅ Datos obtenidos para {len(simbolos_exitosos)} activos")
        if simbolos_fallidos:
            st.warning(f"⚠️ No se pudieron obtener datos para {len(simbolos_fallidos)} activos")
        
        if len(simbolos_exitosos) < 2:
            st.error("Se necesitan al menos 2 activos con datos válidos")
            return None, None, None
        
        df_precios = df_precios.ffill().bfill().dropna()
        
        if df_precios.empty:
            st.error("No hay fechas comunes después del procesamiento")
            return None, None, None
        
        returns = df_precios.pct_change().dropna()
        
        if returns.empty or len(returns) < 30:
            st.error("No hay suficientes datos para calcular retornos válidos")
            return None, None, None
        
        constant_assets = returns.columns[returns.std() == 0].tolist()
        if constant_assets:
            st.warning(f"Removiendo activos con retornos constantes: {constant_assets}")
            returns = returns.drop(columns=constant_assets)
            df_precios = df_precios.drop(columns=constant_assets)
        
        if len(returns.columns) < 2:
            st.error("No quedan suficientes activos después del filtrado")
            return None, None, None
        
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        
        return mean_returns, cov_matrix, df_precios
        
    except Exception as e:
        st.error(f"Error crítico obteniendo datos históricos: {str(e)}")
        return None, None, None

## ----------------------------
## Display Functions
## ----------------------------

def mostrar_resumen_portafolio(portafolio):
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
            
            valuacion = 0
            campos_valuacion = [
                'valuacionEnMonedaOriginal', 'valuacionActual', 'valorNominalEnMonedaOriginal',
                'valorNominal', 'valuacionDolar', 'valuacion', 'valorActual', 'montoInvertido',
                'valorMercado', 'valorTotal', 'importe'
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
            
            if valuacion == 0 and cantidad:
                precio_unitario = 0
                campos_precio = [
                    'precioPromedio', 'precioCompra', 'precioActual', 'precio',
                    'precioUnitario', 'ultimoPrecio', 'cotizacion'
                ]
                
                for campo in campos_precio:
                    if campo in activo and activo[campo] is not None:
                        try:
                            precio = float(activo[campo])
                            if precio > 0:
                                precio_unitario = precio
                                break
                        except (ValueError, TypeError):
                            continue
                
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
                'Valuación': valuacion
            })
            
            valor_total += valuacion
            
        except Exception as e:
            st.warning(f"Error procesando activo: {str(e)}")
            continue
    
    if datos_activos:
        df_activos = pd.DataFrame(datos_activos)
        
        st.markdown("#### 📊 Información General")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Activos", len(datos_activos))
        col2.metric("Símbolos Únicos", df_activos['Símbolo'].nunique())
        col3.metric("Tipos de Activos", df_activos['Tipo'].nunique())
        col4.metric("Valor Total", f"${valor_total:,.2f}")
        
        st.markdown("#### 📋 Detalle de Activos")
        df_display = df_activos.copy()
        df_display['Valuación'] = df_display['Valuación'].apply(lambda x: f"${x:,.2f}" if x > 0 else "N/A")
        df_display['Peso (%)'] = (df_activos['Valuación'] / valor_total * 100).round(2)
        st.dataframe(df_display[['Símbolo', 'Descripción', 'Tipo', 'Cantidad', 'Valuación', 'Peso (%)']], 
                    use_container_width=True)
        
        st.markdown("#### 📊 Distribución por Tipo")
        tipo_stats = df_activos.groupby('Tipo').agg({
            'Valuación': ['sum', 'count', 'mean']
        }).round(2)
        tipo_stats.columns = ['Valor Total', 'Cantidad', 'Valor Promedio']
        tipo_stats = tipo_stats.reset_index()
        
        col1, col2 = st.columns(2)
        with col1:
            fig_pie = go.Figure(data=[go.Pie(
                labels=tipo_stats['Tipo'],
                values=tipo_stats['Valor Total'],
                textinfo='label+percent'
            )])
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            fig_bar = go.Figure(data=[go.Bar(
                x=tipo_stats['Tipo'],
                y=tipo_stats['Valor Total'],
                text=[f"${val:,.0f}" for val in tipo_stats['Valor Total']]
            )])
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("No se pudieron procesar los datos de los activos")

def mostrar_optimizacion_portafolio(portafolio, token_acceso, fecha_desde, fecha_hasta):
    st.markdown("## 🎯 Optimización Avanzada de Portafolio")
    
    activos = portafolio.get('activos', [])
    simbolos = [activo.get('titulo', {}).get('simbolo', '') for activo in activos if activo.get('titulo', {}).get('simbolo', '')]
    
    if len(simbolos) < 2:
        st.warning("Se necesitan al menos 2 activos para optimización")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        estrategia = st.selectbox(
            "Estrategia de Optimización",
            options=['markowitz', 'min-variance-l1', 'min-variance-l2', 'equi-weight', 'long-only'],
            format_func=lambda x: {
                'markowitz': 'Markowitz (Máx Sharpe)',
                'min-variance-l1': 'Mínima Varianza (L1)',
                'min-variance-l2': 'Mínima Varianza (L2)',
                'equi-weight': 'Pesos Iguales',
                'long-only': 'Solo Posiciones Largas'
            }[x]
        )
    
    with col2:
        target_return = None
        if estrategia == 'markowitz':
            target_return = st.number_input(
                "Retorno Anual Objetivo (opcional)",
                min_value=0.0, max_value=5.0, value=0.40, step=0.05,
                format="%.2f"
            )
    
    if st.button("🚀 Ejecutar Optimización"):
        with st.spinner("Optimizando portafolio..."):
            try:
                pm = PortfolioManager(simbolos, token_acceso, fecha_desde, fecha_hasta)
                if not pm.load_data():
                    st.error("Error al cargar datos")
                    return
                
                portfolio = pm.compute_portfolio(estrategia, target_return)
                
                if portfolio:
                    st.success("¡Optimización completada con éxito!")
                    
                    st.markdown("### 📊 Métricas del Portafolio")
                    metrics = portfolio.get_metrics_dict()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Retorno Anual", metrics['Retorno Anual'])
                        st.metric("Volatilidad Anual", metrics['Volatilidad Anual'])
                        st.metric("Ratio de Sharpe", metrics['Ratio de Sharpe'])
                    
                    with col2:
                        st.metric("VaR 95% (Diario)", metrics['VaR 95% (Diario)'])
                        st.metric("Asimetría", metrics['Asimetría'])
                        st.metric("Curtosis", metrics['Curtosis'])
                    
                    st.markdown("### 🥧 Composición del Portafolio")
                    fig_weights = portfolio.plot_weights_streamlit()
                    st.plotly_chart(fig_weights, use_container_width=True)
                    
                    st.markdown("### 📈 Distribución de Retornos")
                    fig_hist = portfolio.plot_histogram_streamlit()
                    st.plotly_chart(fig_hist, use_container_width=True)
                    
                    if estrategia == 'markowitz' and not target_return:
                        st.markdown("### 🌐 Frontera Eficiente")
                        returns, volatilities = pm.compute_efficient_frontier()
                        
                        if returns and volatilities:
                            fig_frontier = go.Figure()
                            fig_frontier.add_trace(go.Scatter(
                                x=volatilities, y=returns,
                                mode='lines',
                                name='Frontera Eficiente',
                                line=dict(color='blue')
                            ))
                            
                            fig_frontier.add_trace(go.Scatter(
                                x=[portfolio.volatility_annual],
                                y=[portfolio.return_annual],
                                mode='markers',
                                name='Portafolio Optimizado',
                                marker=dict(size=12, color='red')
                            ))
                            
                            fig_frontier.update_layout(
                                title="Frontera Eficiente",
                                xaxis_title="Volatilidad Anual",
                                yaxis_title="Retorno Anual",
                                showlegend=True
                            )
                            st.plotly_chart(fig_frontier, use_container_width=True)
                else:
                    st.error("Error en la optimización")
                    
            except Exception as e:
                st.error(f"Error durante la optimización: {str(e)}")
    
    with st.expander("💡 Explicación de las Estrategias"):
        st.markdown("""
        **Markowitz (Máx Sharpe)**:
        - Maximiza el ratio de Sharpe (retorno por unidad de riesgo)
        - Considera correlaciones entre activos
        - Encuentra el óptimo riesgo-retorno
        
        **Mínima Varianza (L1)**:
        - Minimiza la varianza del portafolio
        - Usa regularización L1 (suma de valores absolutos)
        - Tiende a producir portafolios más concentrados
        
        **Mínima Varianza (L2)**:
        - Minimiza la varianza del portafolio
        - Usa regularización L2 (suma de cuadrados)
        - Produce portafolios más diversificados
        
        **Pesos Iguales**:
        - Asignación equitativa a todos los activos
        - No considera optimización
        - Punto de referencia útil
        
        **Solo Posiciones Largas**:
        - Optimización estándar sin ventas en corto
        - Pesos entre 0% y 100%
        """)

def mostrar_analisis_tecnico(portafolio):
    st.markdown("## 📊 Análisis Técnico")
    
    activos = portafolio.get('activos', [])
    simbolos = [activo.get('titulo', {}).get('simbolo', '') for activo in activos if activo.get('titulo', {}).get('simbolo', '')]
    
    if not simbolos:
        st.warning("No hay símbolos disponibles para análisis técnico")
        return
    
    simbolo_seleccionado = st.selectbox("Seleccione un activo para análisis técnico:", simbolos)
    
    if simbolo_seleccionado:
        st.markdown(f"### Gráfico interactivo para {simbolo_seleccionado}")
        
        # Widget de TradingView
        tv_widget = f"""
        <div class="tradingview-widget-container">
          <div id="tradingview_{simbolo_seleccionado}"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget(
            {{
              "autosize": true,
              "symbol": "BCBA:{simbolo_seleccionado}",
              "interval": "D",
              "timezone": "America/Argentina/Buenos_Aires",
              "theme": "light",
              "style": "1",
              "locale": "es",
              "toolbar_bg": "#f1f3f6",
              "enable_publishing": false,
              "allow_symbol_change": true,
              "container_id": "tradingview_{simbolo_seleccionado}"
            }}
          );
          </script>
        </div>
        """
        components.html(tv_widget, height=600)

## ----------------------------
## Main App
## ----------------------------

def main():
    st.title("📊 IOL Portfolio Analyzer Pro")
    st.markdown("Analizador avanzado de portafolios para Invertir Online")
    
    # Initialize session state
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
    
    # Sidebar
    with st.sidebar:
        st.header("🔐 Autenticación IOL")
        
        if st.session_state.token_acceso is None:
            with st.form("login_form"):
                usuario = st.text_input("Usuario", placeholder="su_usuario")
                contraseña = st.text_input("Contraseña", type="password", placeholder="su_contraseña")
                
                if st.form_submit_button("🚀 Conectar"):
                    if usuario and contraseña:
                        with st.spinner("Conectando con IOL..."):
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
            
            st.markdown("#### 📅 Rango de Fechas")
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
            
            if not st.session_state.clientes:
                with st.spinner("Cargando clientes..."):
                    clientes = obtener_lista_clientes(st.session_state.token_acceso)
                    st.session_state.clientes = clientes
            
            clientes = st.session_state.clientes
            
            if clientes:
                st.info(f"👥 {len(clientes)} clientes disponibles")
                
                cliente_ids = [c.get('numeroCliente', c.get('id')) for c in clientes]
                cliente_nombres = [c.get('apellidoYNombre', c.get('nombre', 'Cliente')) for c in clientes]
                
                cliente_seleccionado = st.selectbox(
                    "Seleccione un cliente:",
                    options=cliente_ids,
                    format_func=lambda x: cliente_nombres[cliente_ids.index(x)] if x in cliente_ids else "Cliente Desconocido"
                )
                
                st.session_state.cliente_seleccionado = next(
                    (c for c in clientes if c.get('numeroCliente', c.get('id')) == cliente_seleccionado),
                    None
                )
                
                if st.button("🔄 Actualizar lista de clientes"):
                    with st.spinner("Actualizando clientes..."):
                        nuevos_clientes = obtener_lista_clientes(st.session_state.token_acceso)
                        st.session_state.clientes = nuevos_clientes
                        st.success("✅ Lista actualizada")
                        st.rerun()
            else:
                st.warning("No se encontraron clientes")
    
    # Main content
    if st.session_state.token_acceso and st.session_state.cliente_seleccionado:
        cliente = st.session_state.cliente_seleccionado
        id_cliente = cliente.get('numeroCliente', cliente.get('id'))
        nombre_cliente = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))
        
        st.title(f"📊 Análisis de Portafolio - {nombre_cliente}")
        
        tab1, tab2, tab3 = st.tabs(["📈 Resumen", "🎯 Optimización", "📊 Análisis Técnico"])
        
        with tab1:
            with st.spinner("Cargando portafolio..."):
                portafolio = obtener_portafolio(st.session_state.token_acceso, id_cliente)
            
            if portafolio:
                mostrar_resumen_portafolio(portafolio)
            else:
                st.warning("No se pudo obtener el portafolio")
        
        with tab2:
            if 'portafolio' not in locals():
                with st.spinner("Cargando portafolio para optimización..."):
                    portafolio = obtener_portafolio(st.session_state.token_acceso, id_cliente)
            
            if portafolio:
                mostrar_optimizacion_portafolio(
                    portafolio,
                    st.session_state.token_acceso,
                    st.session_state.fecha_desde,
                    st.session_state.fecha_hasta
                )
            else:
                st.warning("No se pudo obtener el portafolio para optimización")
        
        with tab3:
            if 'portafolio' not in locals():
                with st.spinner("Cargando portafolio para análisis técnico..."):
                    portafolio = obtener_portafolio(st.session_state.token_acceso, id_cliente)
            
            if portafolio:
                mostrar_analisis_tecnico(portafolio)
            else:
                st.warning("No se pudo obtener el portafolio para análisis técnico")
    
    elif st.session_state.token_acceso:
        st.info("👆 Seleccione un cliente en la barra lateral para comenzar")
    else:
        st.info("👆 Ingrese sus credenciales de IOL para comenzar")

if __name__ == "__main__":
    main()
