
import requests
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
from datetime import date, timedelta
import numpy as np
from scipy import optimize
import os
import datetime
import scipy.stats as st
import yfinance as yf
import plotly.express as px

try:
    from IPython.display import display, HTML
except ImportError:
    def display(_): pass
    def HTML(_): return ""
    print("IPython no disponible. Algunas salidas (tablas HTML) pueden no mostrarse correctamente.")

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
    respuesta = requests.post(url_login, data=datos)
    if respuesta.status_code == 200:
        respuesta_json = respuesta.json()
        return respuesta_json['access_token'], respuesta_json['refresh_token']
    else:
        print(f'Error al obtener tokens: {respuesta.status_code}')
        print(respuesta.text)
        return None, None

def obtener_lista_clientes(token_portador):
    url_clientes = 'https://api.invertironline.com/api/v2/Asesores/Clientes'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    respuesta = requests.get(url_clientes, headers=encabezados)
    if respuesta.status_code == 200:
        return respuesta.json()
    else:
        print(f'Error al obtener la lista de clientes: {respuesta.status_code}')
        print(respuesta.text)
        return []

def seleccionar_cliente(lista_clientes):
    if not lista_clientes:
        print("No hay clientes disponibles.")
        return None
    print("Lista de clientes:")
    for i, cliente in enumerate(lista_clientes):
        primer_nombre = cliente['nombre'].split()[0]
        print(f"{i + 1}. {primer_nombre}")
    while True:
        try:
            seleccion = int(input("Seleccione un cliente por número: "))
            if 1 <= seleccion <= len(lista_clientes):
                return lista_clientes[seleccion - 1]
            else:
                print("Selección inválida. Intente nuevamente.")
        except ValueError:
            print("Entrada inválida. Por favor, ingrese un número.")

def obtener_estado_cuenta(token_portador, id_cliente):
    url_estado_cuenta = f'https://api.invertironline.com/api/v2/Asesores/EstadoDeCuenta/{id_cliente}'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    respuesta = requests.get(url_estado_cuenta, headers=encabezados)
    if respuesta.status_code == 200:
        return respuesta.json()
    else:
        return None

def obtener_portafolio(token_portador, id_cliente, pais='Argentina'):
    url_portafolio = f'https://api.invertironline.com/api/v2/Asesores/Portafolio/{id_cliente}/{pais}'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    respuesta = requests.get(url_portafolio, headers=encabezados)
    if respuesta.status_code == 200:
        return respuesta.json()
    else:
        return None

def obtener_cotizacion_mep(token_portador, simbolo, id_plazo_compra, id_plazo_venta):
    url_cotizacion_mep = 'https://api.invertironline.com/api/v2/Cotizaciones/MEP'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    datos = {
        "simbolo": simbolo,
        "idPlazoOperatoriaCompra": id_plazo_compra,
        "idPlazoOperatoriaVenta": id_plazo_venta
    }

    respuesta = requests.post(url_cotizacion_mep, headers=encabezados, json=datos)

    if respuesta.status_code == 200:
        try:
            return respuesta.json().get('valor', None)
        except (AttributeError, KeyError):
            print("Respuesta MEP inesperada:", respuesta.text)
            return None
    elif respuesta.status_code == 401:
        print("Error: Autorización denegada. Verifica el token de autorización.")
        return None
    else:
        print(f'Error al obtener la cotización MEP: {respuesta.status_code}')
        print(respuesta.text)
        return None

def obtener_tasas_caucion(token_portador, instrumento="Cauciones", panel="Todas", pais="Argentina"):
    url = f"https://api.invertironline.com/api/v2/Cotizaciones/{instrumento}/{panel}/{pais}"
    headers = {
        "Authorization": f"Bearer {token_portador}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al obtener las tasas de caución: {response.status_code}, {response.text}")
        return None

def obtener_datos_historicos(token_portador, simbolo, mercado, fecha_desde, fecha_hasta, ajustada="ajustada"):
    url_historicos = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    encabezados = obtener_encabezado_autorizacion(token_portador)
    respuesta = requests.get(url_historicos, headers=encabezados)
    if respuesta.status_code == 200:
        return respuesta.json()
    else:
        print(f"Error al obtener datos históricos para {simbolo}: {respuesta.status_code}")
        print(respuesta.text)
        return None

def obtener_cotizacion_actual(token_portador, mercado, simbolo):
    url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion"
    headers = obtener_encabezado_autorizacion(token_portador)

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al obtener la cotización actual para {simbolo}: {response.status_code}")
        print(response.text)
        return None

def obtener_serie_historica_iol(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="ajustada"):
    url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    headers = obtener_encabezado_autorizacion(token_portador)

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        precios = [item['ultimoPrecio'] for item in data]
        fechas = [item['fechaHora'] for item in data]
        try:
            return pd.Series(precios, index=pd.to_datetime(fechas, format='mixed'))
        except ValueError as e:
            print(f"Error al procesar las fechas para {simbolo}: {e}")
            return None
    else:
        print(f"Error al obtener la serie histórica para {simbolo}: {response.status_code}")
        print(response.text)
        return None

def obtener_sector_activo(simbolo):
    try:
        ticker = yf.Ticker(simbolo)
        info = ticker.info
        sector = info.get('sector')
        industry = info.get('industry')

        if sector and sector != 'N/A' and sector != 'Unknown':
            if 'bond' in info.get('quoteType', '').lower() or 'index' in info.get('quoteType', '').lower():
                return 'Renta Fija/Índice'
            return sector
        elif industry and industry != 'N/A' and industry != 'Unknown':
            return industry
        else:
            if simbolo.startswith(('AL', 'GD')): return 'Bonos Soberanos'
            if simbolo.endswith('O'): return 'Obligaciones Negociables'
            if 'ETF' in simbolo: return 'ETF'
            return 'No disponible'

    except Exception:
        if simbolo.startswith(('AL', 'GD')): return 'Bonos Soberanos'
        if simbolo.endswith('O'): return 'Obligaciones Negociables'
        if 'ETF' in simbolo: return 'ETF'
        return 'No disponible'

def calcular_estadisticas_portafolio(precios_df, pesos, tasa_libre_riesgo=0.0, dias_por_año=252):
    pesos = np.array(pesos)
    retornos_arit_df = precios_df.pct_change().dropna()
    retornos_log_df = np.log(precios_df / precios_df.shift(1)).dropna()

    if len(pesos) != len(retornos_log_df.columns):
        raise ValueError(f"Número de pesos ({len(pesos)}) no coincide con número de activos ({len(retornos_log_df.columns)})")

    retornos_portafolio_log = retornos_log_df.dot(pesos)
    retornos_portafolio_arit = retornos_arit_df.dot(pesos)

    retorno_medio_log = np.mean(retornos_portafolio_log)
    volatilidad = np.std(retornos_portafolio_log)

    retorno_anual = np.exp(retorno_medio_log * dias_por_año) - 1
    volatilidad_anual = volatilidad * np.sqrt(dias_por_año)

    sharpe_ratio = (retorno_anual - tasa_libre_riesgo) / volatilidad_anual if volatilidad_anual > 0 else 0

    var_95 = np.percentile(retornos_portafolio_arit, 5)
    cvar_95 = retornos_portafolio_arit[retornos_portafolio_arit <= var_95].mean()
    skewness = st.skew(retornos_portafolio_arit)
    kurtosis = st.kurtosis(retornos_portafolio_arit)

    return {
        'retornos_log': retornos_portafolio_log,
        'retornos_arit': retornos_portafolio_arit,
        'retorno_anual': retorno_anual,
        'volatilidad_anual': volatilidad_anual,
        'sharpe_ratio': sharpe_ratio,
        'var_95': var_95,
        'cvar_95': cvar_95,
        'skewness': skewness,
        'kurtosis': kurtosis
    }

class PortfolioAnalyzer:
    def __init__(self, tickers, precios_df=None, tasa_libre_riesgo=0.0, periodo='1y', intervalo='1d'):
        self.tickers = tickers
        self.precios_df = precios_df
        self.tasa_libre_riesgo_anual = tasa_libre_riesgo
        self.periodo = periodo
        self.intervalo = intervalo
        self._intervalos_por_año = self._calcular_intervalos_por_año(intervalo)

        if self.precios_df is None:
            self.cargar_datos_historicos(periodo=self.periodo, intervalo=self.intervalo)

    def _calcular_intervalos_por_año(self, intervalo):
        intervalo = intervalo.lower()
        if 'm' in intervalo or 'h' in intervalo:
            minutos_por_dia = 6.5 * 60
            dias_año = 252
            if 'm' in intervalo:
                minutos = int(intervalo.replace('m', ''))
                return (minutos_por_dia / minutos) * dias_año
            elif 'h' in intervalo:
                horas = int(intervalo.replace('h', ''))
                return (minutos_por_dia / (horas * 60)) * dias_año
        elif 'd' in intervalo:
            return 252
        elif 'wk' in intervalo:
            return 52
        elif 'mo' in intervalo:
            return 12
        else:
            print(f"Advertencia: Intervalo '{intervalo}' no reconocido para anualización. Usando 252.")
            return 252

    def cargar_datos_historicos(self, periodo='1y', intervalo='1d'):
        try:
            print(f"Descargando datos para: {self.tickers} (Periodo: {periodo}, Intervalo: {intervalo})")
            valid_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']
            if intervalo not in valid_intervals:
                print(f"Advertencia: Intervalo '{intervalo}' puede no ser válido para yfinance. Intentando de todas formas.")

            if 'm' in intervalo or 'h' in intervalo:
                period_days = self._parse_period_to_days(periodo)
                if periodo == 'max':
                    print("Advertencia: 'max' no es compatible con datos intradía. Usando '60d'.")
                    periodo = '60d'
                elif 'm' in intervalo and period_days > 60:
                    print(f"Advertencia: Periodo '{periodo}' excede los 60 días para intervalo '{intervalo}'. yfinance podría limitarlo.")
                elif ('h' in intervalo or intervalo == '90m') and period_days > 730:
                    print(f"Advertencia: Periodo '{periodo}' excede los 730 días para intervalo '{intervalo}'. yfinance podría limitarlo.")

            data = yf.download(tickers=self.tickers, period=periodo, interval=intervalo, progress=True)

            if data.empty:
                print("No se descargaron datos.")
                self.precios_df = pd.DataFrame()
                return False

            if isinstance(data.columns, pd.MultiIndex):
                if 'Adj Close' in data.columns.levels[0]:
                    self.precios_df = data['Adj Close']
                else:
                    self.precios_df = data['Close']
            else:
                if 'Adj Close' in data.columns:
                    self.precios_df = data[['Adj Close']].rename(columns={'Adj Close': self.tickers[0]})
                else:
                    self.precios_df = data[['Close']].rename(columns={'Close': self.tickers[0]})

            tickers_originales = list(self.tickers)
            self.precios_df = self.precios_df.dropna(axis=1, how='all')
            tickers_con_datos = list(self.precios_df.columns)

            tickers_descartados = [t for t in tickers_originales if t not in tickers_con_datos]
            if tickers_descartados:
                print(f"Tickers descartados por falta de datos: {tickers_descartados}")

            self.tickers = tickers_con_datos
            self.precios_df = self.precios_df.ffill().bfill().dropna(axis=0)

            if self.precios_df.empty or len(self.tickers) < 2:
                print("No hay suficientes datos o tickers válidos después de la limpieza.")
                return False

            print(f"Datos cargados y limpiados para {len(self.tickers)} tickers.")
            self._intervalos_por_año = self._calcular_intervalos_por_año(intervalo)
            return True

        except Exception as e:
            print(f"Error al cargar datos históricos: {str(e)}")
            self.precios_df = pd.DataFrame()
            return False

    def _parse_period_to_days(self, period):
        period = period.lower()
        if 'd' in period: return int(period.replace('d', ''))
        if 'mo' in period: return int(period.replace('mo', '')) * 30
        if 'y' in period: return int(period.replace('y', '')) * 365
        return 9999

    def calcular_retornos(self, log=True):
        if self.precios_df is not None and not self.precios_df.empty:
            if log:
                return np.log(self.precios_df / self.precios_df.shift(1)).dropna()
            else:
                return self.precios_df.pct_change().dropna()
        return pd.DataFrame()

    def calcular_covarianza(self, retornos_df=None, anualizar=True):
        if retornos_df is None:
            retornos_df = self.calcular_retornos(log=True)
        if retornos_df.empty:
            return pd.DataFrame()

        cov_matrix = retornos_df.cov()
        if anualizar:
            cov_matrix *= self._intervalos_por_año
        return cov_matrix

    def calcular_pesos_optimizados(self, metodo='sharpe', target_return_anual=None):
        retornos_log_df = self.calcular_retornos(log=True)
        if retornos_log_df.empty or len(self.tickers) < 2:
            print("No hay suficientes datos o tickers para optimizar.")
            if len(self.tickers) == 1: return np.array([1.0])
            return np.array([1.0 / len(self.tickers)] * len(self.tickers))

        mean_log_returns_intervalo = retornos_log_df.mean()
        mean_returns_anual = np.exp(mean_log_returns_intervalo * self._intervalos_por_año) - 1

        cov_matrix_anual = self.calcular_covarianza(retornos_log_df, anualizar=True)

        num_assets = len(self.tickers)
        initial_weights = np.ones(num_assets) / num_assets
        bounds = tuple((0, 1) for _ in range(num_assets))
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

        if metodo == 'equal':
            return initial_weights

        elif metodo == 'min_var':
            def portfolio_variance_anual(weights):
                return np.dot(weights.T, np.dot(cov_matrix_anual, weights))

            result = optimize.minimize(portfolio_variance_anual,
                                       initial_weights,
                                       method='SLSQP',
                                       bounds=bounds,
                                       constraints=constraints)
            if result.success:
                return result.x
            else:
                print(f"Optimización Min Var falló: {result.message}")
                return initial_weights

        elif metodo == 'sharpe':
            def neg_sharpe_ratio_anual(weights):
                portfolio_return_anual = np.sum(mean_returns_anual * weights)
                portfolio_variance_anual = np.dot(weights.T, np.dot(cov_matrix_anual, weights))
                portfolio_volatility_anual = np.sqrt(portfolio_variance_anual)

                if portfolio_volatility_anual == 0: return np.inf
                sharpe = (portfolio_return_anual - self.tasa_libre_riesgo_anual) / portfolio_volatility_anual
                return -sharpe

            result = optimize.minimize(neg_sharpe_ratio_anual,
                                       initial_weights,
                                       method='SLSQP',
                                       bounds=bounds,
                                       constraints=constraints)
            if result.success:
                return result.x
            else:
                print(f"Optimización Max Sharpe falló: {result.message}")
                return initial_weights

        elif metodo == 'markowitz' and target_return_anual is not None:
            def portfolio_variance_anual(weights):
                return np.dot(weights.T, np.dot(cov_matrix_anual, weights))

            def portfolio_return_anual_constraint(weights):
                return np.sum(mean_returns_anual * weights) - target_return_anual

            markowitz_constraints = (
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': portfolio_return_anual_constraint}
            )

            result = optimize.minimize(portfolio_variance_anual,
                                       initial_weights,
                                       method='SLSQP',
                                       bounds=bounds,
                                       constraints=markowitz_constraints)
            if result.success:
                return result.x
            else:
                print(f"Optimización Markowitz (target return) falló: {result.message}")
                return initial_weights
        else:
            print(f"Método de optimización '{metodo}' no reconocido o falta target_return.")
            return initial_weights

    def simular_portafolios_eficientes(self, num_portafolios=5000):
        retornos_log_df = self.calcular_retornos(log=True)
        if retornos_log_df.empty or len(self.tickers) < 2:
            return pd.DataFrame(), pd.DataFrame()

        mean_log_returns_intervalo = retornos_log_df.mean()
        mean_returns_anual = np.exp(mean_log_returns_intervalo * self._intervalos_por_año) - 1
        cov_matrix_anual = self.calcular_covarianza(retornos_log_df, anualizar=True)

        num_assets = len(self.tickers)
        results = np.zeros((num_portafolios, 3))
        weights_record = np.zeros((num_portafolios, num_assets))

        for i in range(num_portafolios):
            weights = np.random.random(num_assets)
            weights /= np.sum(weights)
            weights_record[i, :] = weights

            portfolio_return_anual = np.sum(mean_returns_anual * weights)
            portfolio_variance_anual = np.dot(weights.T, np.dot(cov_matrix_anual, weights))
            portfolio_volatility_anual = np.sqrt(portfolio_variance_anual)
            sharpe_ratio_anual = (portfolio_return_anual - self.tasa_libre_riesgo_anual) / portfolio_volatility_anual if portfolio_volatility_anual > 0 else 0

            results[i, 0] = portfolio_return_anual
            results[i, 1] = portfolio_volatility_anual
            results[i, 2] = sharpe_ratio_anual

        df_results = pd.DataFrame(results, columns=['Retorno', 'Volatilidad', 'Sharpe'])
        df_weights = pd.DataFrame(weights_record, columns=self.tickers)

        return df_results, df_weights

    def graficar_frontera_eficiente(self, df_simulacion=None, df_pesos_simulacion=None, incluir_markowitz=True):
        retornos_log_df = self.calcular_retornos(log=True)
        if retornos_log_df.empty or len(self.tickers) < 2:
            print("No se pueden calcular retornos/covarianza. Verifique los datos.")
            return None
        mean_returns_anual = np.exp(retornos_log_df.mean() * self._intervalos_por_año) - 1
        cov_matrix_anual = self.calcular_covarianza(retornos_log_df, anualizar=True)

        if df_simulacion is None or df_pesos_simulacion is None:
            print("Simulando portafolios aleatorios para la frontera...")
            df_simulacion, df_pesos_simulacion = self.simular_portafolios_eficientes()

        if df_simulacion.empty:
            print("No se pudieron simular portafolios.")

        pesos_max_sharpe = self.calcular_pesos_optimizados(metodo='sharpe')
        pesos_min_vol = self.calcular_pesos_optimizados(metodo='min_var')
        pesos_equal = self.calcular_pesos_optimizados(metodo='equal')

        def calcular_metricas_anualizadas(weights, mean_returns_anual, cov_matrix_anual, risk_free_rate_anual):
            ret = np.sum(mean_returns_anual * weights)
            vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix_anual, weights)))
            sharpe = (ret - risk_free_rate_anual) / vol if vol > 0 else 0
            return ret, vol, sharpe

        ret_max_sharpe, vol_max_sharpe, sharpe_max_sharpe = calcular_metricas_anualizadas(
            pesos_max_sharpe, mean_returns_anual, cov_matrix_anual, self.tasa_libre_riesgo_anual
        )
        ret_min_vol, vol_min_vol, sharpe_min_vol = calcular_metricas_anualizadas(
            pesos_min_vol, mean_returns_anual, cov_matrix_anual, self.tasa_libre_riesgo_anual
        )
        ret_equal, vol_equal, sharpe_equal = calcular_metricas_anualizadas(
            pesos_equal, mean_returns_anual, cov_matrix_anual, self.tasa_libre_riesgo_anual
        )

        fig = go.Figure()

        if not df_simulacion.empty:
            fig.add_trace(go.Scatter(
                x=df_simulacion['Volatilidad'],
                y=df_simulacion['Retorno'],
                mode='markers',
                marker=dict(
                    size=5,
                    color=df_simulacion['Sharpe'],
                    colorscale='Viridis',
                    colorbar=dict(title="Sharpe Ratio (Sim)"),
                    showscale=True,
                    opacity=0.5
                ),
                name='Portafolios Simulados',
                customdata=df_pesos_simulacion.values,
                hovertemplate=(
                    '<b>Simulado</b><br>' +
                    'Volatilidad: %{x:.2%}<br>' +
                    'Retorno: %{y:.2%}<br>' +
                    'Sharpe: %{marker.color:.2f}<br>' +
                    '<extra></extra>'
                )
            ))

        # Añadir la frontera de Markowitz si es solicitado
        if incluir_markowitz:
            print("Calculando frontera eficiente de Markowitz...")
            retornos_markowitz, volatilidades_markowitz, pesos_markowitz = self.calcular_frontera_markowitz(num_puntos=15)

            if retornos_markowitz and volatilidades_markowitz:
                # Ordenar puntos por volatilidad para dibujar la línea correctamente
                puntos_ordenados = sorted(zip(volatilidades_markowitz, retornos_markowitz, pesos_markowitz))
                volatilidades_ordenadas = [p[0] for p in puntos_ordenados]
                retornos_ordenados = [p[1] for p in puntos_ordenados]
                pesos_ordenados = [p[2] for p in puntos_ordenados]

                # Calcular sharpe ratio para cada punto
                sharpes_markowitz = [(ret - self.tasa_libre_riesgo_anual) / vol if vol > 0 else 0
                                    for ret, vol in zip(retornos_ordenados, volatilidades_ordenadas)]

                # Agregar la línea de la frontera eficiente de Markowitz
                fig.add_trace(go.Scatter(
                    x=volatilidades_ordenadas,
                    y=retornos_ordenados,
                    mode='lines+markers',
                    line=dict(color='rgba(128, 0, 128, 0.7)', width=3),
                    marker=dict(
                        size=7,
                        color=sharpes_markowitz,
                        colorscale='Plasma',
                        showscale=False,
                        symbol='circle'
                    ),
                    name='Frontera de Markowitz',
                    hovertemplate=(
                        '<b>Markowitz</b><br>' +
                        'Volatilidad: %{x:.2%}<br>' +
                        'Retorno: %{y:.2%}<br>' +
                        'Sharpe: %{text:.2f}<br>' +
                        '<extra></extra>'
                    ),
                    text=sharpes_markowitz
                ))

                # Destacar algunos portafolios de Markowitz específicos
                indices_destacar = [0, len(retornos_ordenados)//2, len(retornos_ordenados)-1]
                for idx in indices_destacar:
                    if idx < len(retornos_ordenados):
                        vol = volatilidades_ordenadas[idx]
                        ret = retornos_ordenados[idx]
                        pesos = pesos_ordenados[idx]

                        hover_text = f'<b>Markowitz {idx+1}</b><br>Vol: {vol:.2%}<br>Ret: {ret:.2%}<br>' + '<br>'.join([f"{t}: {w:.1%}" for t, w in zip(self.tickers, pesos) if w > 0.01])

                        fig.add_trace(go.Scatter(
                            x=[vol], y=[ret], mode='markers',
                            marker=dict(size=10, color='purple', symbol='diamond', line=dict(width=1, color='black')),
                            name=f'Markowitz {idx+1}',
                            hovertemplate=hover_text + '<extra></extra>'
                        ))

        hover_text_sharpe = f'<b>Máx. Sharpe</b><br>Vol: {vol_max_sharpe:.2%}<br>Ret: {ret_max_sharpe:.2%}<br>Sharpe: {sharpe_max_sharpe:.2f}<br>' + '<br>'.join([f"{t}: {w:.1%}" for t, w in zip(self.tickers, pesos_max_sharpe) if w > 0.01])
        fig.add_trace(go.Scatter(
            x=[vol_max_sharpe], y=[ret_max_sharpe], mode='markers',
            marker=dict(size=15, color='#FF4500', symbol='star', line=dict(width=1, color='black')),
            name='Portafolio Máx. Sharpe',
            hovertemplate=hover_text_sharpe + '<extra></extra>'
        ))

        hover_text_minvol = f'<b>Mín. Varianza</b><br>Vol: {vol_min_vol:.2%}<br>Ret: {ret_min_vol:.2%}<br>Sharpe: {sharpe_min_vol:.2f}<br>' + '<br>'.join([f"{t}: {w:.1%}" for t, w in zip(self.tickers, pesos_min_vol) if w > 0.01])
        fig.add_trace(go.Scatter(
            x=[vol_min_vol], y=[ret_min_vol], mode='markers',
            marker=dict(size=15, color='#32CD32', symbol='star', line=dict(width=1, color='black')),
            name='Portafolio Mín. Varianza',
            hovertemplate=hover_text_minvol + '<extra></extra>'
        ))

        hover_text_equal = f'<b>Pesos Iguales</b><br>Vol: {vol_equal:.2%}<br>Ret: {ret_equal:.2%}<br>Sharpe: {sharpe_equal:.2f}<br>' + '<br>'.join([f"{t}: {w:.1%}" for t, w in zip(self.tickers, pesos_equal) if w > 0.01])
        fig.add_trace(go.Scatter(
            x=[vol_equal], y=[ret_equal], mode='markers',
            marker=dict(size=12, color='#1E90FF', symbol='diamond', line=dict(width=1, color='black')),
            name='Portafolio Pesos Iguales',
            hovertemplate=hover_text_equal + '<extra></extra>'
        ))

        if vol_max_sharpe > 0:
            max_vol_display = max(vol_max_sharpe, vol_min_vol, vol_equal, df_simulacion['Volatilidad'].max() if not df_simulacion.empty else 0)
            x_max_cal = max_vol_display * 1.1
            y_max_cal = self.tasa_libre_riesgo_anual + sharpe_max_sharpe * x_max_cal

            fig.add_trace(go.Scatter(
                x=[0, x_max_cal], y=[self.tasa_libre_riesgo_anual, y_max_cal],
                mode='lines', line=dict(color='red', dash='dash', width=1.5),
                name='CAL'
            ))

        fig.update_layout(
            title="Frontera Eficiente y Portafolios Clave",
            xaxis_title="Volatilidad Anualizada",
            yaxis_title="Retorno Esperado Anualizado",
            legend_title="Portafolios",
            hovermode="closest",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            xaxis=dict(tickformat=".1%"),
            yaxis=dict(tickformat=".1%")
        )

        fig.add_annotation(
            x=0, y=self.tasa_libre_riesgo_anual,
            text=f"Rf: {self.tasa_libre_riesgo_anual:.2%}",
            showarrow=True, arrowhead=1, ax=30, ay=-30,
            font=dict(size=10, color="black"),
            bgcolor="rgba(255, 255, 255, 0.7)", bordercolor="black", borderwidth=1
        )

        return fig

    def visualizar_composicion_portafolios(self, resultados_simulacion=None, incluir_markowitz=True):
        pesos_max_sharpe = self.calcular_pesos_optimizados(metodo='sharpe')
        pesos_min_vol = self.calcular_pesos_optimizados(metodo='min_var')
        pesos_equal = self.calcular_pesos_optimizados(metodo='equal')

        # Calcular un punto representativo de la frontera de Markowitz
        pesos_markowitz = None
        if incluir_markowitz:
            retornos_log_df = self.calcular_retornos(log=True)
            if not retornos_log_df.empty and len(self.tickers) >= 2:
                mean_returns_anual = np.exp(retornos_log_df.mean() * self._intervalos_por_año) - 1

                # Calculamos un punto de Markowitz intermedio entre min_vol y max_sharpe
                ret_min_vol = np.sum(mean_returns_anual * pesos_min_vol)
                ret_max_sharpe = np.sum(mean_returns_anual * pesos_max_sharpe)

                # Punto intermedio de retorno para Markowitz
                target_return = (ret_min_vol + ret_max_sharpe) / 2

                pesos_markowitz = self.calcular_pesos_optimizados(metodo='markowitz', target_return_anual=target_return)

        retornos_log_df = self.calcular_retornos(log=True)
        if retornos_log_df.empty:
            print("No se pueden calcular métricas para los títulos.")
            return None
        mean_returns_anual = np.exp(retornos_log_df.mean() * self._intervalos_por_año) - 1
        cov_matrix_anual = self.calcular_covarianza(retornos_log_df, anualizar=True)

        def calcular_metricas_anualizadas(weights, mean_returns_anual, cov_matrix_anual, risk_free_rate_anual):
            ret = np.sum(mean_returns_anual * weights)
            vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix_anual, weights)))
            sharpe = (ret - risk_free_rate_anual) / vol if vol > 0 else 0
            return ret, vol, sharpe

        ret_ms, vol_ms, sharpe_ms = calcular_metricas_anualizadas(pesos_max_sharpe, mean_returns_anual, cov_matrix_anual, self.tasa_libre_riesgo_anual)
        ret_mv, vol_mv, sharpe_mv = calcular_metricas_anualizadas(pesos_min_vol, mean_returns_anual, cov_matrix_anual, self.tasa_libre_riesgo_anual)
        ret_eq, vol_eq, sharpe_eq = calcular_metricas_anualizadas(pesos_equal, mean_returns_anual, cov_matrix_anual, self.tasa_libre_riesgo_anual)

        title_ms = f"Max Sharpe<br>Ret:{ret_ms:.1%} Vol:{vol_ms:.1%} Sh:{sharpe_ms:.2f}"
        title_mv = f"Min Vol<br>Ret:{ret_mv:.1%} Vol:{vol_mv:.1%} Sh:{sharpe_mv:.2f}"
        title_eq = f"Equal Weight<br>Ret:{ret_eq:.1%} Vol:{vol_eq:.1%} Sh:{sharpe_eq:.2f}"

        # Definir número de columnas y subtítulos según si incluimos Markowitz
        if incluir_markowitz and pesos_markowitz is not None:
            ret_mw, vol_mw, sharpe_mw = calcular_metricas_anualizadas(pesos_markowitz, mean_returns_anual, cov_matrix_anual, self.tasa_libre_riesgo_anual)
            title_mw = f"Markowitz<br>Ret:{ret_mw:.1%} Vol:{vol_mw:.1%} Sh:{sharpe_mw:.2f}"

            fig = make_subplots(
                rows=1, cols=4,
                specs=[[{'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}]],
                subplot_titles=[title_ms, title_mv, title_eq, title_mw]
            )
        else:
            fig = make_subplots(
                rows=1, cols=3,
                specs=[[{'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}]],
                subplot_titles=[title_ms, title_mv, title_eq]
            )

        def preparar_datos_torta(pesos, tickers):
            df_pesos = pd.DataFrame({'ticker': tickers, 'peso': pesos})
            df_pesos_filtrado = df_pesos[df_pesos['peso'] > 0.005].copy()
            peso_otros = 1 - df_pesos_filtrado['peso'].sum()
            if peso_otros > 0.001:
                df_otros = pd.DataFrame({'ticker': ['Otros'], 'peso': [peso_otros]})
                df_final = pd.concat([df_pesos_filtrado, df_otros], ignore_index=True)
            else:
                df_final = df_pesos_filtrado
                df_final['peso'] = df_final['peso'] / df_final['peso'].sum()
            return df_final

        df_max_sharpe = preparar_datos_torta(pesos_max_sharpe, self.tickers)
        df_min_vol = preparar_datos_torta(pesos_min_vol, self.tickers)
        df_equal = preparar_datos_torta(pesos_equal, self.tickers)

        if incluir_markowitz and pesos_markowitz is not None:
            df_markowitz = preparar_datos_torta(pesos_markowitz, self.tickers)

        fig.add_trace(
            go.Pie(
                labels=df_max_sharpe['ticker'], values=df_max_sharpe['peso'],
                textinfo='label+percent', hole=0.4,
                marker=dict(colors=px.colors.qualitative.Set1), sort=False, name='Max Sharpe',
                hoverinfo='label+percent+value', textposition='outside'
            ), row=1, col=1
        )
        fig.add_trace(
            go.Pie(
                labels=df_min_vol['ticker'], values=df_min_vol['peso'],
                textinfo='label+percent', hole=0.4,
                marker=dict(colors=px.colors.qualitative.Set2), sort=False, name='Min Vol',
                hoverinfo='label+percent+value', textposition='outside'
            ), row=1, col=2
        )
        fig.add_trace(
            go.Pie(
                labels=df_equal['ticker'], values=df_equal['peso'],
                textinfo='label+percent', hole=0.4,
                marker=dict(colors=px.colors.qualitative.Pastel), sort=False, name='Equal Weight',
                hoverinfo='label+percent+value', textposition='outside'
            ), row=1, col=3
        )

        # Agregar la gráfica de Markowitz si está habilitado
        if incluir_markowitz and pesos_markowitz is not None:
            fig.add_trace(
                go.Pie(
                    labels=df_markowitz['ticker'], values=df_markowitz['peso'],
                    textinfo='label+percent', hole=0.4,
                    marker=dict(colors=px.colors.qualitative.Vivid), sort=False, name='Markowitz',
                    hoverinfo='label+percent+value', textposition='outside'
                ), row=1, col=4
            )

        fig.update_traces(textfont_size=10)
        fig.update_layout(
            title_text="Composición y Métricas de Portafolios Clave",
            height=450,
            margin=dict(t=100, b=20, l=20, r=20),
            legend_title_text='Portafolios',
            showlegend=False
        )

        return fig

    def graficar_rendimiento_intradia(self):
        if self.precios_df is None or self.precios_df.empty:
            print("No hay datos de precios disponibles para graficar rendimiento.")
            return None
        if 'm' not in self.intervalo and 'h' not in self.intervalo:
            print(f"El intervalo actual ('{self.intervalo}') no es intradía. Gráfico de rendimiento no generado.")
            return None

        print("Calculando rendimiento intradía de portafolios clave...")

        pesos_max_sharpe = self.calcular_pesos_optimizados(metodo='sharpe')
        pesos_min_vol = self.calcular_pesos_optimizados(metodo='min_var')
        pesos_equal = self.calcular_pesos_optimizados(metodo='equal')

        retornos_intervalo_df = self.calcular_retornos(log=False)
        if retornos_intervalo_df.empty:
            print("No se pudieron calcular los retornos del intervalo.")
            return None

        retornos_ms = retornos_intervalo_df.dot(pesos_max_sharpe)
        retornos_mv = retornos_intervalo_df.dot(pesos_min_vol)
        retornos_eq = retornos_intervalo_df.dot(pesos_equal)

        rendimiento_acum_ms = (1 + retornos_ms).cumprod()
        rendimiento_acum_mv = (1 + retornos_mv).cumprod()
        rendimiento_acum_eq = (1 + retornos_eq).cumprod()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=rendimiento_acum_ms.index, y=rendimiento_acum_ms, mode='lines', name='Max Sharpe', line=dict(color='#FF4500')))
        fig.add_trace(go.Scatter(x=rendimiento_acum_mv.index, y=rendimiento_acum_mv, mode='lines', name='Min Varianza', line=dict(color='#32CD32')))
        fig.add_trace(go.Scatter(x=rendimiento_acum_eq.index, y=rendimiento_acum_eq, mode='lines', name='Pesos Iguales', line=dict(color='#1E90FF')))

        fig.update_layout(
            title=f"Rendimiento Acumulado Intradía ({self.periodo}, {self.intervalo})",
            xaxis_title="Fecha y Hora",
            yaxis_title="Rendimiento Acumulado (Base 1)",
            hovermode="x unified",
            template="plotly_white",
            legend_title="Portafolios",
            yaxis_tickformat=".4f"
        )

        return fig

    def calcular_frontera_markowitz(self, num_puntos=10):
        """
        Calcula múltiples portafolios de Markowitz para formar la frontera eficiente.

        Args:
            num_puntos (int): Número de portafolios a calcular a lo largo de la frontera.

        Returns:
            tuple: (retornos, volatilidades, pesos) correspondientes a cada portafolio.
        """
        retornos_log_df = self.calcular_retornos(log=True)
        if retornos_log_df.empty or len(self.tickers) < 2:
            print("No hay suficientes datos o tickers para calcular la frontera de Markowitz.")
            return [], [], []

        mean_log_returns_intervalo = retornos_log_df.mean()
        mean_returns_anual = np.exp(mean_log_returns_intervalo * self._intervalos_por_año) - 1
        cov_matrix_anual = self.calcular_covarianza(retornos_log_df, anualizar=True)

        # Calcular límites de retorno para la frontera
        pesos_min_vol = self.calcular_pesos_optimizados(metodo='min_var')
        pesos_max_sharpe = self.calcular_pesos_optimizados(metodo='sharpe')

        ret_min_vol = np.sum(mean_returns_anual * pesos_min_vol)
        ret_max_sharpe = np.sum(mean_returns_anual * pesos_max_sharpe)

        # Usar un rango ligeramente más amplio para la frontera
        min_ret = max(ret_min_vol * 0.8, np.min(mean_returns_anual))
        max_ret = min(ret_max_sharpe * 1.2, np.max(mean_returns_anual))

        target_returns = np.linspace(min_ret, max_ret, num_puntos)
        volatilidades = []
        pesos_portafolios = []
        retornos_validos = []

        for target_return in target_returns:
            try:
                pesos = self.calcular_pesos_optimizados(metodo='markowitz', target_return_anual=target_return)
                vol = np.sqrt(np.dot(pesos.T, np.dot(cov_matrix_anual, pesos)))

                if not np.isnan(vol) and vol > 0:
                    volatilidades.append(vol)
                    pesos_portafolios.append(pesos)
                    retornos_validos.append(target_return)
            except Exception as e:
                print(f"Error al calcular portafolio con retorno {target_return:.4f}: {str(e)}")
                continue

        return retornos_validos, volatilidades, pesos_portafolios

usuario = 'boosandr97@gmail.com'
contraseña ='Yacanto1997_'

token_portador, token_refresco = obtener_tokens(usuario, contraseña)
if token_portador and token_refresco:
    cotizacion_mep = obtener_cotizacion_mep(token_portador, simbolo="AL30", id_plazo_compra=1, id_plazo_venta=2)

    tasas_caucion = obtener_tasas_caucion(token_portador)
    tasa_caucion_promedio = None
    if tasas_caucion and 'titulos' in tasas_caucion:
        df_tasas_caucion = pd.DataFrame(tasas_caucion['titulos'])
        if not df_tasas_caucion.empty and 'tasaPromedio' in df_tasas_caucion.columns:
            tasa_caucion_promedio = df_tasas_caucion['tasaPromedio'].mean()

    tasa_caucion_texto = f"{tasa_caucion_promedio:.2f}%" if tasa_caucion_promedio is not None else "No disponible"

    lista_clientes = obtener_lista_clientes(token_portador)
    cliente_seleccionado = seleccionar_cliente(lista_clientes)
    if cliente_seleccionado:
        print(f"Cliente seleccionado: {cliente_seleccionado['nombre']} (ID: {cliente_seleccionado['id']})")

        estado_cuenta = obtener_estado_cuenta(token_portador, cliente_seleccionado['id'])

        portafolio = obtener_portafolio(token_portador, cliente_seleccionado['id'])

        if portafolio:
            activos = portafolio['activos']
            for activo in activos:
                activo['tipo'] = activo['titulo']['tipo']
                activo['sector'] = obtener_sector_activo(activo['titulo']['simbolo'])

            df_portafolio = pd.DataFrame(activos)
            df_portafolio['position'] = df_portafolio['valorizado']

            saldo_disponible_ars = sum(cuenta['disponible'] for cuenta in estado_cuenta['cuentas'] if cuenta['moneda'] == 'peso_Argentino')
            saldo_disponible_usd = sum(cuenta['disponible'] for cuenta in estado_cuenta['cuentas'] if cuenta['moneda'] == 'dolar_Estadounidense')

            df_portafolio = pd.concat([
                df_portafolio,
                pd.DataFrame([
                    {'tipo': 'Saldo Disponible (ARS)', 'position': saldo_disponible_ars},
                    {'tipo': 'Saldo Disponible (USD)', 'position': saldo_disponible_usd}
                ])
            ], ignore_index=True)

            distribucion = df_portafolio.groupby('tipo')['position'].sum().reset_index()
            distribucion['position'] = (distribucion['position'] / distribucion['position'].sum()) * 100
            distribucion.columns = ['tipo', 'porcentaje']

            df_portafolio_sin_saldos = df_portafolio[~df_portafolio['tipo'].str.contains('Saldo Disponible', na=False)]
            distribucion_sector = df_portafolio_sin_saldos.groupby('sector')['position'].sum().reset_index()
            distribucion_sector['position'] = (distribucion_sector['position'] / distribucion_sector['position'].sum()) * 100
            distribucion_sector.columns = ['sector', 'porcentaje']

            tickers_por_sector = df_portafolio_sin_saldos.groupby('sector')['titulo'].apply(
                lambda x: ', '.join(set([t['simbolo'] for t in x if isinstance(t, dict)]))
            ).reset_index()
            distribucion_sector = distribucion_sector.merge(tickers_por_sector, on='sector', how='left')

            traduccion_sectores = {
                'Technology': 'Tecnología',
                'Finance': 'Finanzas',
                'Healthcare': 'Salud',
                'Energy': 'Energía',
                'Consumer Goods': 'Bienes de Consumo',
                'Cripto': 'Cripto',
                'No disponible': 'No disponible'
            }
            distribucion_sector['sector_es'] = distribucion_sector['sector'].map(traduccion_sectores).fillna(distribucion_sector['sector'])

            subtitulo = f"Cliente: {cliente_seleccionado['nombre']} | ID: {cliente_seleccionado['id']}<br>MEP: {cotizacion_mep} | Tasa Caución: {tasa_caucion_texto}"

            fig_actual = make_subplots(
                rows=1, cols=3,
                specs=[[{'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}]],
                subplot_titles=("Tipo", "Activo", " Sector")
            )

            fig_actual.add_trace(go.Pie(
                labels=distribucion['tipo'],
                values=df_portafolio.groupby('tipo')['position'].sum().values,
                textinfo='label+percent',
                textposition='inside',
                hovertemplate='%{label}<br>Valorizado: $%{value:.2f}<extra></extra>',
                marker=dict(colors=['#636EFA', '#00CC96', '#FF6F61', '#F7B7A3', '#FF9900', '#AB63FA', '#FFA15A']),
                insidetextfont=dict(color='white'),
                name="Tipo"
            ), row=1, col=1)

            fig_actual.add_trace(go.Pie(
                labels=df_portafolio.apply(
                    lambda x: f"{x['titulo']['simbolo']}: {int(x['cantidad'])}" if isinstance(x['titulo'], dict) else None,
                    axis=1
                ).dropna(),
                values=df_portafolio.loc[df_portafolio['titulo'].apply(lambda x: isinstance(x, dict)), 'position'],
                textinfo='label+percent',
                textposition='inside',
                hovertemplate='%{label}<br>Valorizado: $%{value:.2f}<extra></extra>',
                marker=dict(colors=['#636EFA', '#00CC96', '#FF6F61', '#F7B7A3', '#FF9900', '#AB63FA', '#FFA15A']),
                insidetextfont=dict(color='white'),
                name="Activo"
            ), row=1, col=2)

            fig_actual.add_trace(go.Pie(
                labels=distribucion_sector['sector_es'],
                values=distribucion_sector['porcentaje'],
                textinfo='label+percent',
                textposition='inside',
                hovertemplate='%{label}<br>Tickers: %{customdata}<extra></extra>',
                customdata=distribucion_sector['titulo'],
                marker=dict(colors=['#636EFA', '#00CC96', '#FF6F61', '#F7B7A3', '#FF9900', '#AB63FA', '#FFA15A']),
                insidetextfont=dict(color='white'),
                name="Sector"
            ), row=1, col=3)

            fig_actual.update_layout(
                title={
                    'text': subtitulo,
                    'x': 0.5
                },
                showlegend=True
            )

            fig_actual.show()

            print("\n--- Analizando portafolio óptimo ---")

            tickers_portafolio = []
            for activo in activos:
                if isinstance(activo.get('titulo'), dict) and 'simbolo' in activo['titulo']:
                    ticker = activo['titulo']['simbolo']
                    tipo = activo['tipo'].lower()

                    if 'accion' in tipo or 'cedear' in tipo:
                        if 'accion' in tipo and not ticker.endswith('.BA') and 'cedear' not in tipo and 'usa' not in tipo:
                            ticker = f"{ticker}.BA"

                        if ticker not in tickers_portafolio:
                            tickers_portafolio.append(ticker)

            print(f"Tickers seleccionados para análisis: {tickers_portafolio}")

            print(f"Total de tickers para análisis: {len(tickers_portafolio)}")

            tasa_libre_riesgo = tasa_caucion_promedio / 36500 if tasa_caucion_promedio else 0.0

            if len(tickers_portafolio) >= 2:
                print(f"Creando analizador con tickers: {tickers_portafolio}, periodo='30d', intervalo='5m'")
                analyzer = PortfolioAnalyzer(
                    tickers=list(tickers_portafolio),
                    tasa_libre_riesgo=tasa_libre_riesgo,
                    periodo='30d',
                    intervalo='5m'
                )

                if analyzer.precios_df is not None and not analyzer.precios_df.empty and len(analyzer.tickers) >= 2:
                    print(f"Datos intradía ('5m') cargados exitosamente para {len(analyzer.tickers)} tickers válidos: {analyzer.tickers}")

                    print("Generando gráfico de Frontera Eficiente...")
                    fig_frontera = analyzer.graficar_frontera_eficiente()
                    if fig_frontera:
                        fig_frontera.show()
                    else:
                        print("No se pudo generar el gráfico de la frontera eficiente.")

                    print("Generando gráfico de Composición de Portafolios Clave...")
                    fig_composicion = analyzer.visualizar_composicion_portafolios()
                    if fig_composicion:
                        fig_composicion.show()
                    else:
                        print("No se pudo generar el gráfico de composición.")

                    print("Generando gráfico de Rendimiento Intradía...")
                    fig_rendimiento_intradia = analyzer.graficar_rendimiento_intradia()
                    if fig_rendimiento_intradia:
                        fig_rendimiento_intradia.show()
                    else:
                        print("No se pudo generar el gráfico de rendimiento intradía.")
                else:
                    print(f"No se pudieron cargar suficientes datos históricos válidos para el análisis con intervalo '5m' y periodo '30d'.")
                    print(f"Tickers intentados: {tickers_portafolio}")
                    if analyzer.precios_df is not None:
                         print(f"Tickers con datos finalmente obtenidos por el analizador: {analyzer.tickers}")
                    print("Recomendación: Verifique la disponibilidad de datos intradía para estos tickers en yfinance o ajuste el periodo/intervalo.")
            else:
                print("Se requieren al menos 2 acciones o CEDEARs para realizar análisis de optimización de portafolio.")
                print("Su portafolio actual no tiene suficientes activos elegibles para este análisis.")

# Definir funciones para visualización con Plotly

def graficar_frontera_eficiente_plotly(dict_portfolios, risk_free_rate=0.0, mostrar_nombres=True):
    """
    Grafica la frontera eficiente usando Plotly, proporcionando una visualización
    interactiva y detallada de los portafolios.

    Args:
        dict_portfolios (dict): Diccionario de portafolios calculados
        risk_free_rate (float): Tasa libre de riesgo diaria
        mostrar_nombres (bool): Si se muestran los nombres de los portafolios

    Returns:
        fig: Figura de Plotly que puede ser mostrada o guardada
    """
    # Extraer datos de los portafolios
    datos = []
    for nombre, portafolio in dict_portfolios.items():
        datos.append({
            'nombre': nombre,
            'riesgo': portafolio.volatility_daily,
            'retorno': portafolio.mean_daily,
            'sharpe': (portafolio.mean_daily - risk_free_rate) / portafolio.volatility_daily if portafolio.volatility_daily > 0 else 0
        })

    # Convertir a DataFrame para facilitar el manejo
    df = pd.DataFrame(datos)

    # Crear gráfico base
    fig = go.Figure()

    # Agregar dispersión principal
    fig.add_trace(go.Scatter(
        x=df['riesgo'],
        y=df['retorno'],
        mode='markers+text' if mostrar_nombres else 'markers',
        text=df['nombre'] if mostrar_nombres else None,
        textposition="top center",
        marker=dict(
            size=10,
            color=df['sharpe'],
            colorscale='Viridis',
            colorbar=dict(title="Ratio de Sharpe"),
            showscale=True
        ),
        hovertemplate='<b>%{text}</b><br>Riesgo: %{x:.4f}<br>Retorno: %{y:.4f}<br>Sharpe: %{marker.color:.4f}<extra></extra>'
    ))

    # Personalizar el diseño
    fig.update_layout(
        title="Frontera Eficiente de Portafolios",
        xaxis_title="Riesgo (Volatilidad)",
        yaxis_title="Retorno Esperado",
        legend_title="Portafolios",
        hovermode="closest",
        template="plotly_white"
    )

    return fig

def obtener_sector_activo(ticker):
    """
    Obtiene el sector de un activo utilizando yfinance.

    Args:
        ticker (str): Símbolo del activo.

    Returns:
        str: Nombre del sector o 'No disponible' si no se encuentra.
    """
    try:
        # Ya debe tener sufijo .BA si corresponde
        ticker_info = yf.Ticker(ticker)
        info = ticker_info.info
        sector = info.get('sector', 'No disponible')
        return sector
    except Exception:
        return 'No disponible'

def visualizar_composicion_portafolios(dict_portafolios, tickers):
    """
    Visualiza la composición de los portafolios usando gráficos de torta interactivos.

    Args:
        dict_portafolios (dict): Diccionario de portafolios calculados
        tickers (list): Lista de símbolos utilizados

    Returns:
        fig: Figura de Plotly con la visualización
    """
    # Crear figura con subgráficos para cada portafolio
    n_portafolios = len(dict_portafolios)
    fig = make_subplots(
        rows=1, cols=n_portafolios,
        specs=[[{'type': 'domain'} for _ in range(n_portafolios)]],
        subplot_titles=list(dict_portafolios.keys())
    )

    # Obtener sectores para cada ticker (si es posible)
    sectores = {}
    for ticker in tickers:
        sectores[ticker] = obtener_sector_activo(ticker)

    # Colores para los sectores
    colores_sectores = {
        'Technology': '#636EFA',
        'Tecnología': '#636EFA',
        'Finance': '#00CC96',
        'Finanzas': '#00CC96',
        'Healthcare': '#FF6F61',
        'Salud': '#FF6F61',
        'Energy': '#F7B7A3',
        'Energía': '#F7B7A3',
        'Consumer Goods': '#FF9900',
        'Bienes de Consumo': '#FF9900',
        'No disponible': '#AB63FA'
    }

    # Agregar tortas para cada portafolio
    for i, (nombre_port, portafolio) in enumerate(dict_portafolios.items(), start=1):
        # Simular datos de pesos por ticker (asumimos que compute_portfolio genera datos aleatorios)
        # En una implementación real, estos datos vendrían del cálculo real del portafolio
        n_tickers = len(tickers)
        pesos = np.random.dirichlet(np.ones(n_tickers), size=1)[0]  # Pesos aleatorios que suman 1

        # Crear DataFrame con los pesos
        df_pesos = pd.DataFrame({
            'ticker': tickers,
            'peso': pesos,
            'sector': [sectores.get(ticker, 'No disponible') for ticker in tickers]
        })

        # Agregar gráfico de torta
        fig.add_trace(go.Pie(
            labels=df_pesos['ticker'],
            values=df_pesos['peso'],
            textinfo='label+percent',
            textposition='inside',
            hovertemplate='%{label}<br>Peso: %{value:.2%}<br>Sector: %{customdata}<extra></extra>',
            customdata=df_pesos['sector'],
            marker=dict(
                colors=[colores_sectores.get(sector, '#CCCCCC') for sector in df_pesos['sector']]
            ),
            insidetextfont=dict(color='white'),
            name=nombre_port
        ), row=1, col=i)

    # Actualizar el diseño
    fig.update_layout(
        title_text='Composición de los Portafolios',
        height=600,
        margin=dict(t=100, b=0, l=0, r=0)
    )

    return fig
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as st
import importlib
import random
import scipy.optimize as op
import os
import datetime
import requests
import yfinance as yf
# Agregar importación de Plotly
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# importar nuestros archivos y recargarlos
# import market_data  # Comentado porque el módulo no está disponible
# importlib.reload(market_data)
# import capm  # Comentado porque el módulo no está disponible
# importlib.reload(capm)

# Configuración de la API
URL_BASE = "https://api.invertironline.com/api/v2"
TOKEN = "your_token_here"  # Reemplazar con el token correspondiente

# Función para obtener datos históricos desde la API
def obtener_serie_historica(simbolo, mercado, fecha_desde, fecha_hasta, ajustada="SinAjustar", bearer_token=None):
    """
    Obtiene la serie histórica de un título desde la API de InvertirOnline.

    Args:
        simbolo (str): Símbolo del activo.
        mercado (str): Mercado del activo.
        fecha_desde (str): Fecha de inicio en formato 'YYYY-MM-DD'.
        fecha_hasta (str): Fecha de fin en formato 'YYYY-MM-DD'.
        ajustada (str): Tipo de ajuste ('SinAjustar' por defecto).
        bearer_token (str): Token de autenticación Bearer.

    Returns:
        pd.DataFrame: DataFrame con la serie histórica o vacío en caso de error.
    """
    url = f"{URL_BASE}/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    headers = {"Authorization": f"Bearer {bearer_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        print(f"Error al obtener datos históricos para {simbolo}: {response.status_code}")
        return pd.DataFrame()

# Reemplazar la obtención de datos históricos diarios por datos intradía usando yfinance
def obtener_datos_intradia(simbolo, periodo='7d', intervalo='1m'):
    """
    Obtiene datos intradía de un símbolo usando yfinance.

    Args:
        simbolo (str): Símbolo del activo.
        periodo (str): Periodo de tiempo (por defecto '7d').
        intervalo (str): Intervalo de tiempo (por defecto '1m').

    Returns:
        pd.DataFrame: DataFrame con los datos intradía o vacío en caso de error.
    """
    try:
        data = yf.download(tickers=simbolo, period=periodo, interval=intervalo)
        if not data.empty:
            return data
        else:
            print(f"No se encontraron datos intradía para {simbolo}.")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error al obtener datos intradía para {simbolo}: {str(e)}")
        return pd.DataFrame()

# Definición de la clase portfolio.output
class output:
    def __init__(self, returns, risk_free_rate=0.0):
        self.returns = returns
        self.mean_daily = np.mean(returns)
        self.volatility_daily = np.std(returns)
        self.sharpe_ratio = (self.mean_daily - risk_free_rate) / self.volatility_daily
        self.var_95 = np.percentile(returns, 5)
        self.skewness = st.skew(returns)
        self.kurtosis = st.kurtosis(returns)
        self.jb_stat, self.p_value = st.jarque_bera(returns)
        self.is_normal = self.p_value > 0.05
        self.decimals = 4

    def plot_histogram(self, portfolio_name):
        str_title = f'{portfolio_name} Portfolio Returns\n' + \
                    'mean_daily=' + str(np.round(self.mean_daily, self.decimals)) + ' | ' + \
                    'volatility_daily=' + str(np.round(self.volatility_daily, self.decimals)) + '\n' + \
                    'sharpe_ratio=' + str(np.round(self.sharpe_ratio, self.decimals)) + ' | ' + \
                    'var_95=' + str(np.round(self.var_95, self.decimals)) + '\n' + \
                    'skewness=' + str(np.round(self.skewness, self.decimals)) + ' | ' + \
                    'kurtosis=' + str(np.round(self.kurtosis, self.decimals)) + '\n' + \
                    'JB stat=' + str(np.round(self.jb_stat, self.decimals)) + ' | ' + \
                    'p-value=' + str(np.round(self.p_value, self.decimals)) + '\n' + \
                    'is_normal=' + str(self.is_normal)
        plt.figure()
        plt.hist(self.returns, bins=100)
        plt.title(str_title)
        plt.xlabel('Return')
        plt.ylabel('Frequency')
        plt.show()

# Definición de la clase portfolio.manager
class manager:
    def __init__(self, rics, notional):
        self.rics = rics
        self.notional = notional
        self.data = self.load_data()

    def load_data(self):
        data = {}
        for ric in self.rics:
            # Aquí se puede implementar la lógica para cargar datos desde la API si es necesario
            print(f'Datos cargados para: {ric}')
        return data

    def compute_covariance(self):
        # Implementar la lógica para computar la matriz de varianza-covarianza
        pass

    def compute_portfolio(self, strategy, target_return=None):
        # Implementar la lógica para computar el portafolio
        # Aquí se devuelve un objeto de la clase output con datos de ejemplo
        returns = np.random.normal(0, 1, 100)  # Datos de ejemplo
        return output(returns, risk_free_rate=tasa_libre_riesgo)

# Clase modelo para cálculos de regresión y betas
class modelo:
    def __init__(self, referencia, seguridad, directorio=None, decimales=6):
        self.referencia = referencia
        self.seguridad = seguridad
        self.directorio = directorio
        self.decimales = decimales
        self.series_temporales = None
        self.x = None
        self.y = None
        self.alpha = None
        self.beta = None
        self.valor_p = None
        self.hipotesis_nula = None
        self.correlacion = None
        self.r_cuadrado = None
        self.predictor_regresion = None

    def sincronizar_series_temporales(self):
        # Aquí se debe implementar la lógica para sincronizar series temporales
        pass

    def calcular_regresion_lineal(self):
        self.x = self.series_temporales['return_x'].values
        self.y = self.series_temporales['return_y'].values
        if len(self.x) == 0 or len(self.y) == 0:
            raise ValueError("Los vectores para regresión lineal no deben estar vacíos.")
        slope, intercept, r_value, p_value, std_err = st.linregress(self.x, self.y)
        self.alpha = np.round(intercept, self.decimales)
        self.beta = np.round(slope, self.decimales)
        self.valor_p = np.round(p_value, self.decimales)
        self.hipotesis_nula = p_value > 0.05
        self.correlacion = np.round(r_value, self.decimales)
        self.r_cuadrado = np.round(r_value ** 2, self.decimales)
        self.predictor_regresion = intercept + slope * self.x

# Función de costo para CAPM
def funcion_costo_capm(x, betas, delta_objetivo, beta_objetivo, regularizacion):
    f_delta = (np.sum(x) + delta_objetivo) ** 2
    f_beta = (np.dot(betas, x) + beta_objetivo) ** 2
    f_penalizacion = regularizacion * np.sum(x ** 2)
    return f_delta + f_beta + f_penalizacion

# Definición de funciones relacionadas con la API
def obtener_tokens(usuario, contraseña):
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
        print(f'Error en la solicitud: {respuesta.status_code}')
        print(respuesta.text)
        return None, None

def refrescar_token(token_refresco):
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
        print(f'Error en la solicitud: {respuesta.status_code}')
        print(respuesta.text)
        return None, None

def obtener_encabezado_autorizacion(token_portador):
    return {
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'application/json'
    }

def obtener_tickers_por_panel(token_portador, paneles, pais):
    """
    Obtiene los tickers operables de los paneles especificados para un país determinado.

    Args:
        token_portador (str): Token de autorización para la API.
        paneles (list): Lista de paneles a consultar (acciones, cedears, etc.).
        pais (str): País del mercado (Argentina, Estados_Unidos, etc.).

    Returns:
        dict: Diccionario con los tickers operables por panel.
        pd.DataFrame: DataFrame con todos los tickers operables.
        list: Lista de paneles disponibles que tienen tickers operables.
    """
    tickers_por_panel = {}
    tickers_df = pd.DataFrame(columns=['panel', 'simbolo'])
    paneles_disponibles = []

    for panel in paneles:
        # ADRs solo está disponible para Argentina, no para Estados Unidos
        if panel == 'aDRs' and pais.lower() == 'estados_unidos':
            print(f"Advertencia: El panel '{panel}' no está disponible para el país '{pais}'.")
            continue  # Omitir solicitudes para ADRs en Estados Unidos

        try:
            # Esta URL trae específicamente los tickers OPERABLES del panel y país especificados
            url = f'https://api.invertironline.com/api/v2/cotizaciones-orleans/{panel}/{pais}/Operables'
            params = {
                'cotizacionInstrumentoModel.instrumento': panel,
                'cotizacionInstrumentoModel.pais': pais.lower()
            }
            encabezados = obtener_encabezado_autorizacion(token_portador)
            respuesta = requests.get(url, headers=encabezados, params=params)

            if respuesta.status_code == 200:
                datos = respuesta.json()
                # Extraemos solo los símbolos de los tickers operables
                tickers = [titulo['simbolo'] for titulo in datos.get('titulos', [])]

                print(f"Panel '{panel}': Se encontraron {len(tickers)} tickers operables")

                if tickers:  # Solo agregar el panel si tiene tickers operables
                    tickers_por_panel[panel] = tickers
                    panel_df = pd.DataFrame({'panel': panel, 'simbolo': tickers})
                    tickers_df = pd.concat([tickers_df, panel_df], ignore_index=True)
                    paneles_disponibles.append(panel)
                else:
                    print(f"Advertencia: El panel '{panel}' no contiene tickers operables para {pais}.")
            elif respuesta.status_code == 401:
                print(f"Error 401: No autorizado para acceder al panel '{panel}' en el país '{pais}'.")
            else:
                print(f'Error en la solicitud para {panel}: {respuesta.status_code}')
                print(respuesta.text)

        except Exception as e:
            print(f"Error al procesar el panel '{panel}': {str(e)}")

    return tickers_por_panel, tickers_df, paneles_disponibles

def obtener_series_intradia_aleatorias(tickers, periodo='7d', intervalo='1m'):
    """
    Obtiene datos intradía aleatorios para una lista de tickers usando yfinance.

    Args:
        tickers (list): Lista de símbolos de activos.
        periodo (str): Periodo de tiempo (por defecto '7d').
        intervalo (str): Intervalo de tiempo (por defecto '1m').

    Returns:
        pd.DataFrame: DataFrame con los datos intradía seleccionados.
        list: Lista de tickers con datos válidos.
    """
    series_intradia = pd.DataFrame()
    tickers_validos = []

    for simbolo in tickers:
        try:
            data = obtener_datos_intradia(simbolo, periodo=periodo, intervalo=intervalo)
            if not data.empty:
                data['simbolo'] = simbolo
                series_intradia = pd.concat([series_intradia, data], ignore_index=True)
                tickers_validos.append(simbolo)
            else:
                print(f"No se encontraron datos intradía para {simbolo}.")
        except Exception as e:
            print(f"Error al obtener datos intradía para {simbolo}: {str(e)}")
    return series_intradia, tickers_validos

def obtener_tasas_caucion(token_portador):
    """
    Obtiene las tasas de caución disponibles desde la API de InvertirOnline.

    Args:
        token_portador (str): Token de autenticación Bearer.

    Returns:
        float: Promedio de las tasas de caución o None en caso de error.
    """
    try:
        url = f"{URL_BASE}/Titulos/Caucion/Tasas"
        headers = {"Authorization": f"Bearer {token_portador}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            datos = response.json()
            # Extraer las tasas disponibles
            tasas = [item['tasa'] for item in datos if 'tasa' in item]
            if tasas:
                # Convertir a valores diarios (asumiendo tasas anuales)
                return np.mean(tasas) / 365
            else:
                return 0.0
        else:
            print(f"Error al obtener tasas de caución: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error en obtener_tasas_caucion: {str(e)}")
        return None

# inputs
notional = 15 # in mn USD

# Reemplazar la lógica de selección de tickers
usuario = 'boosandr97@gmail.com'
contraseña = 'Yacanto1997_'

# Obtener los tokens
token_portador, token_refresco = obtener_tokens(usuario, contraseña)
if token_portador and token_refresco:
    # Refrescar el token cuando expire
    token_portador, token_refresco = refrescar_token(token_refresco)

    # Obtener tickers de los paneles seleccionados
    paneles_seleccionados = ['acciones', 'cedears']
    print("\nObteniendo tickers de los paneles:", paneles_seleccionados)
    tickers_por_panel, tickers_df, paneles_disponibles = obtener_tickers_por_panel(token_portador, paneles_seleccionados, 'Argentina')

    rics = []
    if paneles_disponibles:
        # Mostrar información de tickers disponibles por panel
        print("\nInformación de tickers operables por panel:")
        for panel in paneles_disponibles:
            if panel in tickers_por_panel:
                print(f"  - Panel '{panel}': {len(tickers_por_panel[panel])} tickers operables")

        # Solicitar al usuario la cantidad de activos
        cantidad_activos = int(input("\nIngrese la cantidad de activos a seleccionar aleatoriamente por panel: "))

        # Lista de tickers que no requieren sufijo .BA (no cotizan localmente)
        tickers_sin_sufijo = ['BBDC', 'BYMAC', 'ITUB', 'VALE', 'PBR', 'ABEV', 'BSBR', 'BBD']

        # Seleccionar aleatoriamente tickers de los paneles disponibles
        for panel in paneles_disponibles:
            if panel in tickers_por_panel and tickers_por_panel[panel]:
                # Filtrar tickers operables y mostrar información adicional
                tickers_disponibles = tickers_por_panel[panel]
                print(f"\nPanel '{panel}': Seleccionando {min(cantidad_activos, len(tickers_disponibles))} de {len(tickers_disponibles)} tickers operables")

                # Seleccionar aleatoriamente tickers de este panel
                seleccionados = random.sample(tickers_disponibles, min(cantidad_activos, len(tickers_disponibles)))

                # Procesar cada ticker para hacerlo compatible con yfinance
                panel_tickers = []
                for ticker in seleccionados:
                    ticker_limpio = ticker.strip()

                    # Verificar si el ticker está en la lista de tickers sin sufijo
                    if ticker_limpio.upper() in tickers_sin_sufijo:
                        ticker_yf = ticker_limpio
                    # Para el mercado argentino, generalmente necesitamos agregar el sufijo .BA
                    elif panel in ['acciones', 'cedears']:
                        ticker_yf = f"{ticker_limpio}.BA"
                    else:
                        ticker_yf = ticker_limpio

                    panel_tickers.append(ticker_yf)

                rics.extend(panel_tickers)
                print(f"\nPanel '{panel}': Se agregaron {len(panel_tickers)} tickers")

        print(f"\nTotal de tickers seleccionados: {len(rics)}")

        # Descargar y verificar datos
        if rics:
            print("\nVerificando disponibilidad de datos intradía...")
            periodo_intradia = '7d'  # Última semana
            intervalo_intradia = '1h'  # Cambio a 1 hora para mayor disponibilidad de datos

            # Comprobar primero los tickers en lotes para optimizar
            print("Validando tickers en lotes...")
            lote_size = 5  # Procesar en lotes de 5 tickers
            rics_validos = []

            # Desactivar la salida estándar de yfinance
            import sys
            from io import StringIO
            original_stdout = sys.stdout
            sys.stdout = StringIO()  # Redirigir stdout a un buffer

            # Dividir los tickers en lotes para procesamiento más eficiente
            for i in range(0, len(rics), lote_size):
                lote_tickers = rics[i:i+lote_size]

                # Probar obtener datos para el lote completo
                try:
                    data_lote = yf.download(tickers=" ".join(lote_tickers), period=periodo_intradia,
                                           interval=intervalo_intradia, group_by='ticker', progress=False)

                    # Verificar tickers individuales en el lote
                    if isinstance(data_lote, pd.DataFrame) and not data_lote.empty:
                        if len(lote_tickers) > 1:  # Si hay múltiples tickers
                            # yfinance agrupa por ticker cuando hay múltiples
                            for ticker in lote_tickers:
                                if ticker in data_lote.columns.levels[0]:
                                    rics_validos.append(ticker)
                        else:  # Un solo ticker
                            rics_validos.append(lote_tickers[0])
                except Exception as e:
                    pass

            # Restaurar la salida estándar
            sys.stdout = original_stdout

            if rics_validos:
                print(f"Se validaron correctamente {len(rics_validos)} tickers.")
                rics = rics_validos

                # Obtener datos para todos los tickers válidos
                series_intradia, _ = obtener_series_intradia_aleatorias(rics, periodo=periodo_intradia, intervalo=intervalo_intradia)

                if series_intradia.empty:
                    print("Error: No se pudieron obtener datos para los tickers validados.")
                    rics = []
            else:
                print("No se pudieron validar tickers con sufijo. Intentando sin sufijo...")
                # Intentar nuevamente sin el sufijo .BA para aquellos que lo tienen
                rics_sin_sufijo = [ric.replace(".BA", "") if ".BA" in ric else ric for ric in rics]
                series_intradia, rics_validos = obtener_series_intradia_aleatorias(rics_sin_sufijo, periodo=periodo_intradia, intervalo=intervalo_intradia)

                if not series_intradia.empty:
                    print(f"Se obtuvieron datos para {len(rics_validos)} tickers sin sufijo.")
                    rics = rics_validos
                else:
                    print("No se pudieron obtener datos para ningún ticker.")
                    rics = []
    else:
        print("No se encontraron paneles disponibles.")
        rics = []

if rics:
    tasa_libre_riesgo = obtener_tasas_caucion(token_portador) if token_portador else None
    if tasa_libre_riesgo is not None:
        print(f"Tasa libre de riesgo (promedio de caución): {tasa_libre_riesgo}")
    else:
        print("No se pudo obtener la tasa libre de riesgo. Usando valor por defecto.")
        tasa_libre_riesgo = 0.0  # Valor por defecto en caso de error

    # inicializar la instancia de la clase
    port_mgr = manager(rics, notional)

    # computar correlación y matriz de varianza-covarianza
    port_mgr.compute_covariance()

    # computar los portafolios deseados: clase de salida = portfolio.output
    port_min_variance_l1 = port_mgr.compute_portfolio('min-variance-l1')
    port_min_variance_l2 = port_mgr.compute_portfolio('min-variance-l2')
    port_long_only = port_mgr.compute_portfolio('long-only')
    port_equi_weight = port_mgr.compute_portfolio('equi-weight')
    port_markowitz = port_mgr.compute_portfolio('markowitz', target_return=None)

    # graficar los histogramas de retornos para el portafolio deseado
    port_min_variance_l1.plot_histogram('Min Variance L1')
    port_min_variance_l2.plot_histogram('Min Variance L2')
    port_long_only.plot_histogram('Long Only')
    port_equi_weight.plot_histogram('Equi Weight')
    port_markowitz.plot_histogram('Markowitz')

    # Definir la función para graficar la frontera eficiente con Plotly
    def graficar_frontera_eficiente_plotly(dict_portfolios, risk_free_rate=0.0, mostrar_nombres=True):
        """
        Grafica la frontera eficiente usando Plotly, proporcionando una visualización
        interactiva y detallada de los portafolios.

        Args:
            dict_portfolios (dict): Diccionario de portafolios calculados
            risk_free_rate (float): Tasa libre de riesgo diaria
            mostrar_nombres (bool): Si se muestran los nombres de los portafolios

        Returns:
            fig: Figura de Plotly que puede ser mostrada o guardada
        """
        # Extraer datos de los portafolios
        datos = []
        for nombre, portafolio in dict_portfolios.items():
            datos.append({
                'nombre': nombre,
                'riesgo': portafolio.volatility_daily,
                'retorno': portafolio.mean_daily,
                'sharpe': (portafolio.mean_daily - risk_free_rate) / portafolio.volatility_daily if portafolio.volatility_daily > 0 else 0
            })

        # Convertir a DataFrame para facilitar el manejo
        df = pd.DataFrame(datos)

        # Crear gráfico base
        fig = go.Figure()

        # Agregar dispersión principal
        fig.add_trace(go.Scatter(
            x=df['riesgo'],
            y=df['retorno'],
            mode='markers+text' if mostrar_nombres else 'markers',
            text=df['nombre'] if mostrar_nombres else None,
            textposition="top center",
            marker=dict(
                size=10,
                color=df['sharpe'],
                colorscale='Viridis',
                colorbar=dict(title="Ratio de Sharpe"),
                showscale=True
            ),
            hovertemplate='<b>%{text}</b><br>Riesgo: %{x:.4f}<br>Retorno: %{y:.4f}<br>Sharpe: %{marker.color:.4f}<extra></extra>'
        ))

        # Personalizar el diseño
        fig.update_layout(
            title="Frontera Eficiente de Portafolios",
            xaxis_title="Riesgo (Volatilidad)",
            yaxis_title="Retorno Esperado",
            legend_title="Portafolios",
            hovermode="closest",
            template="plotly_white"
        )

        return fig

    # Graficar la frontera eficiente con Plotly (después de los cálculos existentes)
    dict_portafolios = {
        'Min Varianza L1': port_min_variance_l1,
        'Min Varianza L2': port_min_variance_l2,
        'Long Only': port_long_only,
        'Equi Weight': port_equi_weight,
        'Markowitz': port_markowitz
    }

    # Graficar frontera eficiente interactiva
    fig_frontera = graficar_frontera_eficiente_plotly(dict_portafolios, risk_free_rate=tasa_libre_riesgo)
    fig_frontera.show()

    # Asegurarse de que visualizar_composicion_portafolios esté definida
    def visualizar_composicion_portafolios(dict_portafolios, tickers):
        """
        Visualiza la composición de los portafolios usando gráficos de torta interactivos.

        Args:
            dict_portafolios (dict): Diccionario de portafolios calculados
            tickers (list): Lista de símbolos utilizados

        Returns:
            fig: Figura de Plotly con la visualización
        """
        # Crear figura con subgráficos para cada portafolio
        n_portafolios = len(dict_portafolios)
        fig = make_subplots(
            rows=1, cols=n_portafolios,
            specs=[[{'type': 'domain'} for _ in range(n_portafolios)]],
            subplot_titles=list(dict_portafolios.keys())
        )

        # Obtener sectores para cada ticker (si es posible)
        sectores = {}
        for ticker in tickers:
            sectores[ticker] = obtener_sector_activo(ticker)

        # Colores para los sectores
        colores_sectores = {
            'Technology': '#636EFA',
            'Tecnología': '#636EFA',
            'Finance': '#00CC96',
            'Finanzas': '#00CC96',
            'Healthcare': '#FF6F61',
            'Salud': '#FF6F61',
            'Energy': '#F7B7A3',
            'Energía': '#F7B7A3',
            'Consumer Goods': '#FF9900',
            'Bienes de Consumo': '#FF9900',
            'No disponible': '#AB63FA'
        }

        # Agregar tortas para cada portafolio
        for i, (nombre_port, portafolio) in enumerate(dict_portafolios.items(), start=1):
            # Simular datos de pesos por ticker (asumimos que compute_portfolio genera datos aleatorios)
            # En una implementación real, estos datos vendrían del cálculo real del portafolio
            n_tickers = len(tickers)
            pesos = np.random.dirichlet(np.ones(n_tickers), size=1)[0]  # Pesos aleatorios que suman 1

            # Crear DataFrame con los pesos
            df_pesos = pd.DataFrame({
                'ticker': tickers,
                'peso': pesos,
                'sector': [sectores.get(ticker, 'No disponible') for ticker in tickers]
            })

            # Agregar gráfico de torta
            fig.add_trace(go.Pie(
                labels=df_pesos['ticker'],
                values=df_pesos['peso'],
                textinfo='label+percent',
                textposition='inside',
                hovertemplate='%{label}<br>Peso: %{value:.2%}<br>Sector: %{customdata}<extra></extra>',
                customdata=df_pesos['sector'],
                marker=dict(
                    colors=[colores_sectores.get(sector, '#CCCCCC') for sector in df_pesos['sector']]
                ),
                insidetextfont=dict(color='white'),
                name=nombre_port
            ), row=1, col=i)

        # Actualizar el diseño
        fig.update_layout(
            title_text='Composición de los Portafolios',
            height=600,
            margin=dict(t=100, b=0, l=0, r=0)
        )

        return fig

    # Graficar composición de cada portafolio
    fig_composicion = visualizar_composicion_portafolios(dict_portafolios, rics)
    fig_composicion.show()
else:
    print("No se pudieron obtener tickers válidos. Verifique las credenciales o la disponibilidad de los datos.")
    rics = []

# Definición de funciones para visualización con Plotly
def graficar_frontera_eficiente_plotly(dict_portfolios, risk_free_rate=0.0, mostrar_nombres=True):
    """
    Grafica la frontera eficiente usando Plotly, proporcionando una visualización
    interactiva y detallada de los portafolios.

    Args:
        dict_portfolios (dict): Diccionario de portafolios calculados
        risk_free_rate (float): Tasa libre de riesgo diaria
        mostrar_nombres (bool): Si se muestran los nombres de los portafolios

    Returns:
        fig: Figura de Plotly que puede ser mostrada o guardada
    """
    # Extraer datos de los portafolios
    datos = []
    for nombre, portafolio in dict_portfolios.items():
        datos.append({
            'nombre': nombre,
            'riesgo': portafolio.volatility_daily,
            'retorno': portafolio.mean_daily,
            'sharpe': (portafolio.mean_daily - risk_free_rate) / portafolio.volatility_daily if portafolio.volatility_daily > 0 else 0
        })

    # Convertir a DataFrame para facilitar el manejo
    df = pd.DataFrame(datos)

    # Crear gráfico base
    fig = go.Figure()

    # Agregar dispersión principal
    fig.add_trace(go.Scatter(
        x=df['riesgo'],
        y=df['retorno'],
        mode='markers+text' if mostrar_nombres else 'markers',
        text=df['nombre'] if mostrar_nombres else None,
        textposition="top center",
        marker=dict(
            size=10,
            color=df['sharpe'],
            colorscale='Viridis',
            colorbar=dict(title="Ratio de Sharpe"),
            showscale=True
        ),
        hovertemplate='<b>%{text}</b><br>Riesgo: %{x:.4f}<br>Retorno: %{y:.4f}<br>Sharpe: %{marker.color:.4f}<extra></extra>'
    ))

    # Personalizar el diseño
    fig.update_layout(
        title="Frontera Eficiente de Portafolios",
        xaxis_title="Riesgo (Volatilidad)",
        yaxis_title="Retorno Esperado",
        legend_title="Portafolios",
        hovermode="closest",
        template="plotly_white"
    )

    return fig

# Función para graficar las series históricas de los portafolios y benchmarks
def graficar_comparacion_benchmarks(dict_portfolios, benchmarks=None, periodo='1y', intervalo='1d'):
    """
    Grafica la evolución temporal de los portafolios calculados en comparación con benchmarks.

    Args:
        dict_portfolios (dict): Diccionario de portafolios calculados
        benchmarks (dict, optional): Diccionario con tickers de benchmarks y sus nombres
        periodo (str): Periodo de tiempo para los datos (por defecto '1y')
        intervalo (str): Intervalo de tiempo entre datos (por defecto '1d')

    Returns:
        fig: Figura de Plotly con la evolución de portafolios y benchmarks
    """
    if benchmarks is None:
        benchmarks = {
            '^MERV': 'MERVAL',
            '^SPX': 'S&P 500',
            '^IXIC': 'NASDAQ',
            'XLF': 'Sector Financiero',
            'XLK': 'Sector Tecnología'
        }

    # Descargar datos de benchmarks
    print("Descargando datos de benchmarks...")
    datos_benchmarks = pd.DataFrame()
    try:
        benchmarks_validos = {}
        for ticker, nombre in benchmarks.items():
            try:
                data = yf.download(ticker, period=periodo, interval=intervalo)['Close']
                if not data.empty:
                    datos_benchmarks[nombre] = data
                    benchmarks_validos[ticker] = nombre
                    print(f"Datos descargados para {nombre} ({ticker})")
                else:
                    print(f"No se encontraron datos para {nombre} ({ticker})")
            except Exception as e:
                print(f"Error al descargar datos para {nombre} ({ticker}): {str(e)}")

        if datos_benchmarks.empty:
            print("No se pudieron descargar datos para ningún benchmark. Usando sólo portafolios.")
    except Exception as e:
        print(f"Error al descargar benchmarks: {str(e)}")

    # Crear DataFrame para portafolios simulados
    # En una implementación real esto vendría del histórico real de los portafolios
    datos_portafolios = pd.DataFrame(index=datos_benchmarks.index)

    # Obtener rendimientos simulados para cada portafolio
    # Simulamos los datos para el propósito de visualización
    for nombre, portafolio in dict_portfolios.items():
        # Simulamos valores históricos basados en las estadísticas del portafolio
        np.random.seed(42)  # Para reproducibilidad
        rend_diarios = np.random.normal(
            loc=portafolio.mean_daily,
            scale=portafolio.volatility_daily,
            size=len(datos_benchmarks)
        )
        # Convertimos a precios acumulados
        valores = (1 + pd.Series(rend_diarios, index=datos_benchmarks.index)).cumprod() * 100
        datos_portafolios[nombre] = valores

    # Normalizar todas las series (portafolios y benchmarks) a base 100
    datos_normalizados = pd.DataFrame(index=datos_benchmarks.index)

    # Normalizar benchmarks
    for nombre in datos_benchmarks.columns:
        primer_valor = datos_benchmarks[nombre].iloc[0]
        if primer_valor > 0:  # Evitar división por cero
            datos_normalizados[nombre] = datos_benchmarks[nombre] * 100 / primer_valor

    # Agregar portafolios normalizados
    for nombre in datos_portafolios.columns:
        datos_normalizados[nombre] = datos_portafolios[nombre]

    # Calcular métricas de correlación y beta para cada portafolio vs benchmarks
    metricas = []
    for nombre_port, _ in dict_portafolios.items():
        if nombre_port in datos_portafolios.columns:
            # Calcular retornos diarios
            retornos_port = datos_portafolios[nombre_port].pct_change().dropna()

            for nombre_bench in datos_benchmarks.columns:
                retornos_bench = datos_benchmarks[nombre_bench].pct_change().dropna()

                # Alinear las series de tiempo
                ret_port_alineado, ret_bench_alineado = retornos_port.align(retornos_bench, join='inner')

                if len(ret_port_alineado) > 1:
                    # Calcular correlación
                    corr = np.corrcoef(ret_port_alineado, ret_bench_alineado)[0, 1]

                    # Calcular beta
                    cov = np.cov(ret_port_alineado, ret_bench_alineado)[0, 1]
                    var = np.var(ret_bench_alineado)
                    beta = cov / var if var > 0 else np.nan

                    metricas.append({
                        'Portafolio': nombre_port,
                        'Benchmark': nombre_bench,
                        'Correlación': np.round(corr, 4),
                        'Beta': np.round(beta, 4)
                    })

    # Crear el gráfico con Plotly
    fig = go.Figure()

    # Paleta de colores más extensa para distinción clara
    colores_ports = px.colors.qualitative.Vivid
    colores_benchs = px.colors.qualitative.Dark24

    # Agregar líneas para cada portafolio
    for i, nombre in enumerate(datos_portafolios.columns):
        color = colores_ports[i % len(colores_ports)]
        fig.add_trace(go.Scatter(
            x=datos_normalizados.index,
            y=datos_normalizados[nombre],
            mode='lines',
            line=dict(width=3, color=color),
            name=f"{nombre} (Port)",
            hovertemplate='%{y:.2f}<extra>%{fullData.name}</extra>',
        ))

    # Agregar líneas para cada benchmark con líneas punteadas
    for i, nombre in enumerate(datos_benchmarks.columns):
        color = colores_benchs[i % len(colores_benchs)]
        fig.add_trace(go.Scatter(
            x=datos_normalizados.index,
            y=datos_normalizados[nombre],
            mode='lines',
            line=dict(width=2, color=color, dash='dash'),
            name=f"{nombre} (Bench)",
            hovertemplate='%{y:.2f}<extra>%{fullData.name}</extra>',
        ))

    # Personalizar el diseño
    fig.update_layout(
        title="Evolución histórica de Portafolios vs Benchmarks (Base 100)",
        xaxis_title="Fecha",
        yaxis_title="Valor Normalizado (Base 100)",
        legend_title="Series",
        hovermode="x unified",
        template="plotly_white"
    )

    # Crear tabla de métricas
    if metricas:
        df_metricas = pd.DataFrame(metricas)

        # Agregar tabla de métricas al visualizar
        print("\nMetricas de correlación y Beta entre Portafolios y Benchmarks:")
        print(df_metricas)

        # Crear gráfico de tabla con métricas
        fig_tabla = go.Figure(data=[go.Table(
            header=dict(
                values=list(df_metricas.columns),
                fill_color='paleturquoise',
                align='left',
                font=dict(size=12)
            ),
            cells=dict(
                values=[df_metricas[col] for col in df_metricas.columns],
                fill_color='lavender',
                align='left',
                font=dict(size=11)
            )
        )])

        fig_tabla.update_layout(
            title="Métricas de Correlación y Beta entre Portafolios y Benchmarks"
        )

        fig_tabla.show()

    return fig

def obtener_sector_activo(ticker):
    """
    Obtiene el sector de un activo a partir de su ticker.

    Args:
        ticker (str): Símbolo del activo.

    Returns:
        str: Sector del activo o 'No disponible' si no se encuentra.
    """
    # Mapeo simplificado de tickers a sectores
    sectores_conocidos = {
        # Tecnología
        'AAPL': 'Tecnología', 'MSFT': 'Tecnología', 'GOOGL': 'Tecnología',
        'GGAL.BA': 'Finanzas', 'YPF.BA': 'Energía', 'PAMP.BA': 'Energía',
        'BMA.BA': 'Finanzas', 'TXAR.BA': 'Energía', 'CEPU.BA': 'Servicios Públicos',
        # ETFs sectoriales
        'XLK': 'Tecnología', 'XLF': 'Finanzas', 'XLV': 'Salud',
        'XLE': 'Energía', 'XLP': 'Consumo Básico'
    }

    # Si es un ticker con sufijo, intentamos con la parte base
    ticker_base = ticker.split('.')[0] if '.' in ticker else ticker

    # Intentamos obtener información del ticker usando yfinance
    try:
        info = yf.Ticker(ticker).info
        sector = info.get('sector', None)
        if sector:
            return sector
    except:
        pass

    # Si no se encuentra, buscamos en nuestro mapeo conocido
    return sectores_conocidos.get(ticker, 'No disponible')
