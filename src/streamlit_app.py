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
# Nuevas importaciones
import sys
import math
import scipy.stats as st_stats
import matplotlib.pyplot as plt
import seaborn as sns

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

# Función para obtener datos diarios usando yfinance
def obtener_datos_diarios(ticker, periodo="1y", intervalo="1d"):
    datos = yf.download(ticker, period=periodo, interval=intervalo)
    datos.reset_index(inplace=True)  # Aseguramos que la fecha quede en una columna
    return datos

# Función para cargar datos desde el DataFrame
def cargar_serie_temporal(df, columna_fecha, columna_precio):
    """
    Carga los datos de la serie temporal desde el DataFrame.
    """
    t = pd.DataFrame()
    t['fecha'] = pd.to_datetime(df[columna_fecha], utc=True, errors='coerce')
    t['cierre'] = df[columna_precio]
    t = t.sort_values(by='fecha').dropna().reset_index(drop=True)
    t['cierre_anterior'] = t['cierre'].shift(1)
    t['retorno_cierre'] = t['cierre'] / t['cierre_anterior'] - 1
    t = t.dropna().reset_index(drop=True)
    return t

# Clase para análisis de distribuciones
class Distribucion:
    def __init__(self, serie_temporal, decimales=5, factor=252):
        self.serie_temporal = serie_temporal
        self.decimales = decimales
        self.factor = factor  # Factor para anualizar (252 días hábiles)
        self.vector = self.serie_temporal['retorno_cierre'].values
        self.precio_actual = self.serie_temporal['cierre'].iloc[-1]
        self.media_anual = None
        self.volatilidad_anual = None
        self.ratio_sharpe = None
        self.var_95 = None
        self.sesgo = None
        self.curtosis = None
        self.jb_stat = None
        self.p_valor = None
        self.es_normal = None
        self.mejor_ajuste = None
        self.mejores_parametros = None
        self.nombre_mejor_ajuste = None  # Para guardar el nombre completo

    def calcular_estadisticas(self):
        """
        Calcula estadísticas clave:
        - Media anualizada
        - Volatilidad anualizada
        - Ratio de Sharpe
        - Percentil al 5% (VaR)
        - Test de normalidad (Jarque-Bera)
        """
        self.media_anual = np.mean(self.vector) * self.factor
        self.volatilidad_anual = np.std(self.vector) * np.sqrt(self.factor)
        self.ratio_sharpe = self.media_anual / self.volatilidad_anual if self.volatilidad_anual > 0 else 0.0
        self.var_95 = np.percentile(self.vector, 5)
        self.sesgo = st_stats.skew(self.vector)
        self.curtosis = st_stats.kurtosis(self.vector)
        self.jb_stat = len(self.vector) / 6 * (self.sesgo**2 + (1 / 4) * self.curtosis**2)
        self.p_valor = 1 - st_stats.chi2.cdf(self.jb_stat, df=2)
        self.es_normal = self.p_valor > 0.05

        # Ajustar la mejor distribución
        self.mejor_ajuste, self.mejores_parametros, self.nombre_mejor_ajuste = self.analizar_mejor_distribucion()

    def analizar_mejor_distribucion(self):
        """
        Encuentra la mejor distribución ajustada a los datos.
        """
        distribuciones = {
            'norm': 'Normal',
            't': 't de Student',
            'uniform': 'Uniforme',
            'expon': 'Exponencial',
            'chi2': 'Chi-cuadrado'
        }
        resultados = {}
        for codigo_dist, nombre_dist in distribuciones.items():
            try:
                objeto_dist = getattr(st_stats, codigo_dist)
                parametros = objeto_dist.fit(self.vector)
                ks_stat, p_valor = st_stats.kstest(self.vector, codigo_dist, args=parametros)
                resultados[codigo_dist] = {'KS Statistic': ks_stat, 'P-Value': p_valor, 'Params': parametros, 'Name': nombre_dist}
            except Exception:
                continue
        
        if resultados:
            codigo_mejor_ajuste = max(resultados, key=lambda x: resultados[x]['P-Value'])
            return codigo_mejor_ajuste, resultados[codigo_mejor_ajuste]['Params'], resultados[codigo_mejor_ajuste]['Name']
        else:
            return 'norm', st_stats.norm.fit(self.vector), 'Normal'

    def crear_grafico_plotly(self, ticker_name="Activo"):
        """
        Crea un gráfico interactivo con Plotly para Streamlit
        """
        # Crear histograma
        fig = go.Figure()
        
        # Histograma de retornos
        fig.add_trace(go.Histogram(
            x=self.vector,
            nbinsx=50,
            histnorm='probability density',
            name='Retornos Observados',
            marker_color='lightblue',
            opacity=0.7
        ))
        
        # Línea de distribución ajustada
        x_range = np.linspace(min(self.vector), max(self.vector), 1000)
        try:
            y_fitted = getattr(st_stats, self.mejor_ajuste).pdf(x_range, *self.mejores_parametros)
            fig.add_trace(go.Scatter(
                x=x_range,
                y=y_fitted,
                mode='lines',
                name=f'Ajuste {self.nombre_mejor_ajuste}',
                line=dict(color='red', width=2)
            ))
        except Exception:
            pass
        
        # Configurar layout
        titulo = (
            f"Análisis de Distribución - {ticker_name}<br>"
            f"<sub>Media Anual: {self.media_anual:.4f} | Volatilidad Anual: {self.volatilidad_anual:.4f}<br>"
            f"Sharpe: {self.ratio_sharpe:.4f} | VaR 95%: {self.var_95:.4f}<br>"
            f"Sesgo: {self.sesgo:.4f} | Curtosis: {self.curtosis:.4f}<br>"
            f"Jarque-Bera: {self.jb_stat:.4f} | P-valor: {self.p_valor:.4f}<br>"
            f"Normal: {self.es_normal} | Mejor Ajuste: {self.nombre_mejor_ajuste}</sub>"
        )
        
        fig.update_layout(
            title=titulo,
            xaxis_title="Retornos Diarios",
            yaxis_title="Densidad de Probabilidad",
            showlegend=True,
            height=600
        )
        
        return fig

def mostrar_analisis_distribucion(token_portador, simbolo):
    """
    Muestra el análisis de distribución para un símbolo específico
    """
    st.markdown(f"#### 📊 Análisis de Distribución - {simbolo}")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        periodo_seleccionado = st.selectbox(
            "Periodo de análisis:",
            options=["1y", "2y", "5y", "max"],
            index=0,
            help="Periodo de datos históricos para el análisis"
        )
        
    with col2:
        usar_iol = st.checkbox(
            "Usar datos de IOL",
            value=True,
            help="Si está marcado, intenta usar datos de IOL primero, sino usa Yahoo Finance"
        )
    
    if st.button(f"🔄 Analizar Distribución de {simbolo}"):
        with st.spinner(f"Analizando distribución de retornos para {simbolo}..."):
            serie_temporal = None
            
            if usar_iol:
                # Intentar obtener datos de IOL primero
                try:
                    fecha_hasta_dt = datetime.now()
                    if periodo_seleccionado == "1y":
                        fecha_desde_dt = fecha_hasta_dt - timedelta(days=365)
                    elif periodo_seleccionado == "2y":
                        fecha_desde_dt = fecha_hasta_dt - timedelta(days=730)
                    elif periodo_seleccionado == "5y":
                        fecha_desde_dt = fecha_hasta_dt - timedelta(days=1825)
                    else:  # max
                        fecha_desde_dt = fecha_hasta_dt - timedelta(days=3650)
                    
                    # Probar diferentes mercados
                    mercados = ['bCBA', 'nYSE', 'nASDAQ', 'rOFEX']
                    serie_iol = None
                    
                    for mercado in mercados:
                        serie_iol = obtener_serie_historica_iol(
                            token_portador, mercado, simbolo,
                            fecha_desde_dt.strftime('%Y-%m-%d'),
                            fecha_hasta_dt.strftime('%Y-%m-%d')
                        )
                        if serie_iol is not None and len(serie_iol) > 30:
                            break
                    
                    if serie_iol is not None and len(serie_iol) > 30:
                        # Convertir serie de IOL al formato esperado
                        df_iol = pd.DataFrame({
                            'Date': serie_iol.index,
                            'Close': serie_iol.values
                        }).reset_index(drop=True)
                        serie_temporal = cargar_serie_temporal(df_iol, 'Date', 'Close')
                        st.success("✅ Datos obtenidos desde IOL")
                    else:
                        raise Exception("No se pudieron obtener datos suficientes de IOL")
                        
                except Exception as e:
                    st.warning(f"⚠️ No se pudieron obtener datos de IOL: {str(e)}")
                    usar_iol = False
            
            if not usar_iol or serie_temporal is None:
                # Fallback a Yahoo Finance
                try:
                    df_yf = obtener_datos_diarios(simbolo, periodo=periodo_seleccionado, intervalo="1d")
                    
                    if df_yf.empty:
                        # Intentar con sufijos argentinos
                        sufijos = ['.BA', '.AR']
                        for sufijo in sufijos:
                            df_yf = obtener_datos_diarios(simbolo + sufijo, periodo=periodo_seleccionado, intervalo="1d")
                            if not df_yf.empty:
                                break
                    
                    if not df_yf.empty:
                        # Eliminar duplicados
                        if df_yf['Date'].duplicated().any():
                            df_yf = df_yf.drop_duplicates(subset=['Date'])
                        
                        serie_temporal = cargar_serie_temporal(df_yf, 'Date', 'Close')
                        st.success("✅ Datos obtenidos desde Yahoo Finance")
                    else:
                        raise Exception("No se pudieron obtener datos de Yahoo Finance")
                        
                except Exception as e:
                    st.error(f"❌ Error obteniendo datos: {str(e)}")
                    return
            
            if serie_temporal is not None and len(serie_temporal) > 30:
                try:
                    # Realizar análisis de distribución
                    distribucion = Distribucion(serie_temporal)
                    distribucion.calcular_estadisticas()
                    
                    # Mostrar métricas principales
                    st.markdown("#### 📈 Métricas Estadísticas")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    col1.metric(
                        "Retorno Anual",
                        f"{distribucion.media_anual:.2%}",
                        help="Retorno promedio anualizado"
                    )
                    col2.metric(
                        "Volatilidad Anual",
                        f"{distribucion.volatilidad_anual:.2%}",
                        help="Volatilidad anualizada"
                    )
                    col3.metric(
                        "Ratio Sharpe",
                        f"{distribucion.ratio_sharpe:.3f}",
                        help="Ratio riesgo-retorno"
                    )
                    col4.metric(
                        "VaR 95%",
                        f"{distribucion.var_95:.2%}",
                        help="Valor en Riesgo al 95%"
                    )
                    
                    # Segunda fila de métricas
                    col1, col2, col3, col4 = st.columns(4)
                    
                    col1.metric(
                        "Sesgo",
                        f"{distribucion.sesgo:.3f}",
                        help="Asimetría de la distribución"
                    )
                    col2.metric(
                        "Curtosis",
                        f"{distribucion.curtosis:.3f}",
                        help="Forma de las colas de la distribución"
                    )
                    col3.metric(
                        "Jarque-Bera",
                        f"{distribucion.jb_stat:.3f}",
                        help="Estadístico de normalidad"
                    )
                    col4.metric(
                        "¿Es Normal?",
                        "Sí" if distribucion.es_normal else "No",
                        help=f"P-valor: {distribucion.p_valor:.4f}"
                    )
                    
                    # Mostrar información sobre la mejor distribución
                    st.markdown("#### 🎯 Mejor Ajuste de Distribución")
                    st.info(f"**{distribucion.nombre_mejor_ajuste}** es la distribución que mejor se ajusta a los datos")
                    
                    # Gráfico interactivo
                    fig = distribucion.crear_grafico_plotly(simbolo)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Interpretación de resultados
                    st.markdown("#### 💡 Interpretación de Resultados")
                    
                    interpretaciones = []
                    
                    # Análisis de sesgo
                    if abs(distribucion.sesgo) < 0.5:
                        interpretaciones.append("✅ **Sesgo**: Los retornos están relativamente balanceados")
                    elif distribucion.sesgo > 0.5:
                        interpretaciones.append("📈 **Sesgo Positivo**: Mayor frecuencia de retornos positivos extremos")
                    else:
                        interpretaciones.append("📉 **Sesgo Negativo**: Mayor frecuencia de retornos negativos extremos")
                    
                    # Análisis de curtosis
                    if abs(distribucion.curtosis) < 1:
                        interpretaciones.append("✅ **Curtosis**: Distribución similar a la normal en las colas")
                    elif distribucion.curtosis > 1:
                        interpretaciones.append("⚠️ **Leptocúrtica**: Colas más pesadas que la distribución normal (mayor riesgo de eventos extremos)")
                    else:
                        interpretaciones.append("📊 **Platicúrtica**: Colas más ligeras que la distribución normal")
                    
                    # Análisis de normalidad
                    if distribucion.es_normal:
                        interpretaciones.append("✅ **Normalidad**: Los datos siguen una distribución normal (p > 0.05)")
                    else:
                        interpretaciones.append("⚠️ **No Normal**: Los datos NO siguen una distribución normal (p ≤ 0.05)")
                    
                    # Análisis de VaR
                    if distribucion.var_95 < -0.05:
                        interpretaciones.append("🔴 **Alto Riesgo**: VaR indica pérdidas diarias potenciales superiores al 5%")
                    elif distribucion.var_95 < -0.02:
                        interpretaciones.append("🟡 **Riesgo Moderado**: VaR indica pérdidas diarias potenciales entre 2% y 5%")
                    else:
                        interpretaciones.append("🟢 **Bajo Riesgo**: VaR indica pérdidas diarias potenciales menores al 2%")
                    
                    for interpretacion in interpretaciones:
                        st.markdown(interpretacion)
                    
                    # Información adicional en expander
                    with st.expander("📊 Datos Técnicos Detallados"):
                        st.markdown("**Parámetros de la Mejor Distribución:**")
                        params_info = f"Distribución: {distribucion.nombre_mejor_ajuste}\n"
                        params_info += f"Parámetros: {distribucion.mejores_parametros}"
                        st.code(params_info)
                        
                        st.markdown("**Estadísticas de la Serie:**")
                        stats_info = f"Observaciones: {len(distribucion.vector)}\n"
                        stats_info += f"Precio actual: ${distribucion.precio_actual:.2f}\n"
                        stats_info += f"Retorno mínimo: {min(distribucion.vector):.4f}\n"
                        stats_info += f"Retorno máximo: {max(distribucion.vector):.4f}"
                        st.code(stats_info)
                
                except Exception as e:
                    st.error(f"❌ Error en el análisis de distribución: {str(e)}")
            else:
                st.error("❌ No se obtuvieron suficientes datos para el análisis")

def get_historical_data_for_optimization(token_portador, simbolos, fecha_desde, fecha_hasta):
    """
    Enhanced function to get historical data with better error handling and fallbacks
    """
    try:
        df_precios = pd.DataFrame()
        simbolos_exitosos = []
        simbolos_fallidos = []
        
        # Progress bar
        progress_bar = st.progress(0)
        total_symbols = len(simbolos)
        
        for idx, simbolo in enumerate(simbolos):
            progress_bar.progress((idx + 1) / total_symbols, text=f"Processing {simbolo}...")
            
            # Try different markets
            mercados = ['bCBA', 'nYSE', 'nASDAQ', 'rOFEX']
            serie_obtenida = False
            
            for mercado in mercados:
                try:
                    # Try to get class D if available
                    simbolo_consulta = simbolo
                    clase_d = obtener_clase_d(simbolo, mercado, token_portador)
                    if clase_d:
                        simbolo_consulta = clase_d
                    
                    # Get historical data
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
            
            # Fallback to Yahoo Finance if IOL fails
            if not serie_obtenida:
                try:
                    serie_yf = obtener_datos_alternativos_yfinance(
                        simbolo, fecha_desde, fecha_hasta
                    )
                    if serie_yf is not None and len(serie_yf) > 10 and serie_yf.nunique() > 1:
                        df_precios[simbolo] = serie_yf
                        simbolos_exitosos.append(simbolo)
                        serie_obtenida = True
                except Exception:
                    pass
            
            if not serie_obtenida:
                simbolos_fallidos.append(simbolo)
        
        progress_bar.empty()
        
        # Report results
        if simbolos_exitosos:
            st.success(f"✅ Data obtained for {len(simbolos_exitosos)} assets")
        if simbolos_fallidos:
            st.warning(f"⚠️ Failed to get data for {len(simbolos_fallidos)} assets")
        
        # Check if we have enough data
        if len(simbolos_exitosos) < 2:
            st.error("Need at least 2 assets with valid data")
            return None, None, None
        
        # Clean and align data
        df_precios = df_precios.ffill().bfill().dropna()
        
        if df_precios.empty:
            st.error("No common dates after processing")
            return None, None, None
        
        # Calculate returns
        returns = df_precios.pct_change().dropna()
        
        if returns.empty or len(returns) < 30:
            st.error("Not enough data for valid returns calculation")
            return None, None, None
        
        # Remove assets with constant returns
        constant_assets = returns.columns[returns.std() == 0].tolist()
        if constant_assets:
            st.warning(f"Removing assets with constant returns: {constant_assets}")
            returns = returns.drop(columns=constant_assets)
            df_precios = df_precios.drop(columns=constant_assets)
        
        if len(returns.columns) < 2:
            st.error("Not enough assets remaining after filtering")
            return None, None, None
        
        # Calculate metrics
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        
        return mean_returns, cov_matrix, df_precios
        
    except Exception as e:
        st.error(f"Error getting historical data: {str(e)}")
        return None, None, None

# Clase PortfolioManager simplificada para compatibilidad
class PortfolioManager:
    def __init__(self, symbols, token, fecha_desde, fecha_hasta):
        self.symbols = symbols
        self.token = token
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.data_loaded = False
        self.returns = None
        self.prices = None
        self.notional = 1000000  # Default notional value
        self.risk_free_rate = 0.40  # Annual risk-free rate (40% as example for Argentina)
        
    def load_data(self):
        """Load historical data for optimization"""
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
            st.error(f"Error loading data: {str(e)}")
            return False
    
    def compute_portfolio(self, strategy='markowitz', target_return=None):
        """Compute optimized portfolio with different strategies"""
        if not self.data_loaded or self.returns is None:
            return None
            
        n_assets = len(self.returns.columns)
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        if strategy == 'equi-weight':
            # Equal weight portfolio
            weights = np.ones(n_assets) / n_assets
            return self._create_output(weights)
            
        elif strategy == 'min-variance-l1':
            # Minimum variance with L1 regularization
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'ineq', 'fun': lambda x: 1 - np.sum(np.abs(x))}
            ]
            objective = lambda x: portfolio_variance(x, self.cov_matrix)
            
        elif strategy == 'min-variance-l2':
            # Minimum variance with L2 regularization
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'ineq', 'fun': lambda x: 1 - np.sum(x**2)}
            ]
            objective = lambda x: portfolio_variance(x, self.cov_matrix)
            
        elif strategy == 'long-only':
            # Standard long-only optimization
            constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
            objective = lambda x: portfolio_variance(x, self.cov_matrix)
            
        elif strategy == 'markowitz':
            if target_return is not None:
                # Target return optimization
                constraints = [
                    {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                    {'type': 'eq', 'fun': lambda x: np.sum(self.mean_returns * x) - target_return}
                ]
                objective = lambda x: portfolio_variance(x, self.cov_matrix)
            else:
                # Maximize Sharpe ratio
                constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
                def neg_sharpe_ratio(weights):
                    port_return = np.sum(self.mean_returns * weights)
                    port_vol = np.sqrt(portfolio_variance(weights, self.cov_matrix))
                    return -(port_return - self.risk_free_rate) / port_vol if port_vol > 0 else np.inf
                objective = neg_sharpe_ratio
        
        else:
            # Unrecognized strategy
            st.warning("Estrategia no reconocida, usando pesos iguales.")
            weights = np.ones(n_assets) / n_assets
            return self._create_output(weights)
        
        # Optimization
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
        """Create output object with portfolio metrics"""
        port_returns = (self.returns * weights).sum(axis=1)
        port_output = PortfolioOutput(port_returns, self.notional)
        port_output.weights = weights
        port_output.asset_names = list(self.returns.columns)
        port_output.mean_returns = self.mean_returns
        port_output.cov_matrix = self.cov_matrix
        return port_output
    
    def compute_efficient_frontier(self, n_points=50):
        """Compute efficient frontier"""
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

def portfolio_variance(weights, cov_matrix):
    """Calcula la varianza del portafolio dado un vector de pesos y la matriz de covarianza."""
    return np.dot(weights.T, np.dot(cov_matrix, weights))

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
        """Return comprehensive metrics dictionary"""
        return {
            'Daily Return': f"{self.mean_daily:.2%}",
            'Daily Volatility': f"{self.volatility_daily:.2%}",
            'Annual Return': f"{self.return_annual:.2%}",
            'Annual Volatility': f"{self.volatility_annual:.2%}",
            'Sharpe Ratio': f"{self.sharpe_ratio:.2f}",
            'VaR 95% (Daily)': f"{self.var_95:.2%}",
            'Skewness': f"{self.skewness:.2f}",
            'Kurtosis': f"{self.kurtosis:.2f}",
            'JB Statistic': f"{self.jb_stat:.2f}",
            'Normality (p-value)': f"{self.p_value:.4f}",
            'Is Normal': "Yes" if self.is_normal else "No"
        }
    
    def plot_histogram_streamlit(self):
        """Create histogram plot for Streamlit"""
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=self.returns,
            nbinsx=50,
            name="Portfolio Returns",
            marker_color='#1f77b4'
        ))
        
        # Add mean and VaR lines
        fig.add_vline(x=self.mean_daily, line_dash="dash", line_color="red",
                     annotation_text=f"Mean: {self.mean_daily:.2%}")
        fig.add_vline(x=self.var_95, line_dash="dash", line_color="orange",
                     annotation_text=f"VaR 95%: {self.var_95:.2%}")
        
        fig.update_layout(
            title="Portfolio Returns Distribution",
            xaxis_title="Daily Returns",
            yaxis_title="Frequency",
            showlegend=False
        )
        return fig
    
    def plot_weights_streamlit(self):
        """Create weights pie chart for Streamlit"""
        if self.weights is None or self.asset_names is None:
            return None
            
        df_weights = pd.DataFrame({
            'Asset': self.asset_names,
            'Weight': self.weights
        }).sort_values('Weight', ascending=False)
        
        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=df_weights['Asset'],
            values=df_weights['Weight'],
            textinfo='label+percent',
            insidetextorientation='radial'
        ))
        fig.update_layout(
            title="Portfolio Allocation",
            uniformtext_minsize=12,
            uniformtext_mode='hide'
        )
        return fig

def main():
    """
    Función principal de la aplicación Streamlit
    """
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
    
    # Sidebar para autenticación y configuración
    with st.sidebar:
        st.header("🔐 Autenticación IOL")
        
        if st.session_state.token_acceso is None:
            # Formulario de login
            with st.form("login_form"):
                st.markdown("#### Ingrese sus credenciales de IOL")
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
            # Usuario conectado
            st.success("✅ Conectado a IOL")
            
            # Configuración de fechas
            st.markdown("#### 📅 Configuración de Fechas")
            col1, col2 = st.columns(2)
            with col1:
                fecha_desde = st.date_input(
                    "Fecha desde:",
                    value=st.session_state.fecha_desde,
                    max_value=date.today()
                )
            with col2:
                fecha_hasta = st.date_input(
                    "Fecha hasta:",
                    value=st.session_state.fecha_hasta,
                    max_value=date.today()
                )
            
            st.session_state.fecha_desde = fecha_desde
            st.session_state.fecha_hasta = fecha_hasta
            
            # Obtener lista de clientes
            if not st.session_state.clientes:
                with st.spinner("Cargando clientes..."):
                    clientes = obtener_lista_clientes(st.session_state.token_acceso)
                    st.session_state.clientes = clientes
            
            clientes = st.session_state.clientes
            
            if clientes:
                st.info(f"👥 {len(clientes)} clientes disponibles")
                
                # Seleccionar cliente
                cliente_ids = [c.get('numeroCliente', c.get('id')) for c in clientes]
                cliente_nombres = [c.get('apellidoYNombre', c.get('nombre', 'Cliente')) for c in clientes]
                
                cliente_seleccionado = st.selectbox(
                    "Seleccione un cliente:",
                    options=cliente_ids,
                    format_func=lambda x: cliente_nombres[cliente_ids.index(x)] if x in cliente_ids else "Cliente Desconocido"
                )
                
                # Guardar cliente seleccionado en session state
                st.session_state.cliente_seleccionado = next(
                    (c for c in clientes if c.get('numeroCliente', c.get('id')) == cliente_seleccionado),
                    None
                )
                
                if st.button("🔄 Actualizar lista de clientes"):
                    with st.spinner("Actualizando clientes..."):
                        nuevos_clientes = obtener_lista_clientes(st.session_state.token_acceso)
                        st.session_state.clientes = nuevos_clientes
                        st.success("✅ Lista de clientes actualizada")
                        st.rerun()
            
            else:
                st.warning("No se encontraron clientes. Verifique su conexión y permisos.")
    
    # Contenido principal con manejo de errores mejorado
    try:
        if st.session_state.token_acceso and st.session_state.cliente_seleccionado:
            mostrar_analisis_portafolio()
        elif st.session_state.token_acceso:
            st.info("👆 Seleccione un cliente en la barra lateral para comenzar el análisis")
        else:
            st.info("👆 Ingrese sus credenciales de IOL en la barra lateral para comenzar")
    except Exception as e:
        st.error(f"❌ Error en la aplicación: {str(e)}")
        st.error("🔄 Por favor, recargue la página e intente nuevamente")

if __name__ == "__main__":
    main()
