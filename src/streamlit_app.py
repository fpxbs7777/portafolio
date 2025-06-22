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
import random
import warnings
import streamlit.components.v1 as components
from functools import lru_cache
import hashlib
from concurrent.futures import ThreadPoolExecutor
from bayes_opt import BayesianOptimization
from scipy import optimize as op

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

def obtener_endpoint_historico(mercado, simbolo, fecha_desde, fecha_hasta, ajustada="ajustada"):
    """
    Devuelve el endpoint correcto según el tipo de activo
    """
    base_url = "https://api.invertironline.com/api/v2"
    
    # Mapeo de mercados a sus respectivos endpoints
    endpoints = {
        'Opciones': f"{base_url}/Opciones/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'FCI': f"{base_url}/FCI/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'MEP': f"{base_url}/Cotizaciones/MEP/{simbolo}",
        'Caucion': f"{base_url}/Cotizaciones/Cauciones/Todas/Argentina",
        'TitulosPublicos': f"{base_url}/TitulosPublicos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'Cedears': f"{base_url}/Cedears/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'ADRs': f"{base_url}/ADRs/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'Bonos': f"{base_url}/Bonos/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
    }
    
    # Intentar determinar automáticamente el tipo de activo si no se especifica
    if mercado not in endpoints:
        if simbolo.endswith(('.BA', '.AR')):
            return endpoints.get('Cedears')
        elif any(ext in simbolo.upper() for ext in ['AL', 'GD', 'AY24', 'GD30', 'AL30']):
            return endpoints.get('Bonos')
        else:
            # Por defecto, asumimos que es un título regular
            return f"{base_url}/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    
    return endpoints.get(mercado)

def parse_datetime_flexible(date_str: str):
    """
    Parses a datetime string that may or may not include microseconds or timezone info.
    Uses pandas.to_datetime for robust parsing.
    """
    if not isinstance(date_str, str):
        return None
    try:
        # pd.to_datetime is very robust and can handle various formats, including ISO 8601
        # with or without microseconds and timezone information.
        # errors='coerce' will return NaT (Not a Time) for strings that cannot be parsed.
        return pd.to_datetime(date_str, errors='coerce', utc=True)
    except Exception:
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
                serie = pd.Series(precios, index=fechas, name='Cierre')
                serie = serie[~serie.index.duplicated(keep='last')]
                return serie.sort_index()
        
        # Para respuestas que son un solo valor (ej: MEP)
        elif isinstance(data, (int, float)):
            return pd.Series([float(data)], index=[pd.Timestamp.now(tz='UTC')], name='precio')
            
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

def obtener_serie_historica_fci(token_portador, simbolo, fecha_desde, fecha_hasta):
    """
    Obtiene la serie histórica de un fondo común de inversión
    """
    url = f'https://api.invertironline.com/api/v2/Titulos/FCI/{simbolo}/cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/ajustada'
    headers = {
        'Authorization': f'Bearer {token_portador}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error al obtener serie histórica del FCI {simbolo}: {str(e)}")
        return None

def obtener_serie_historica_iol(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="ajustada"):
    """
    Obtiene series históricas para diferentes tipos de activos con manejo mejorado de errores
    """
    try:
        # Primero intentamos con el endpoint específico del mercado
        url = obtener_endpoint_historico(mercado, simbolo, fecha_desde, fecha_hasta, ajustada)
        if not url:
            st.warning(f"No se pudo determinar el endpoint para el símbolo {simbolo}")
            return None
        
        headers = obtener_encabezado_autorizacion(token_portador)
        
        # Configurar un timeout más corto para no bloquear la interfaz
        response = requests.get(url, headers=headers, timeout=10)
        
        # Verificar si la respuesta es exitosa
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and data.get('status') == 'error':
                st.warning(f"Error en la respuesta para {simbolo}: {data.get('message', 'Error desconocido')}")
                return None
                
            # Procesar la respuesta según el tipo de activo
            return procesar_respuesta_historico(data, mercado)
        else:
            st.warning(f"Error {response.status_code} al obtener datos para {simbolo}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.warning(f"Error de conexión para {simbolo}: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error inesperado al procesar {simbolo}: {str(e)}")
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
            if ric in self.timeseries:
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
        portfolio_returns = self.returns.dot(weights)
        
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


def obtener_saldo_disponible(token_acceso):
    """
    Obtiene el saldo disponible en la cuenta
    
    Args:
        token_acceso: Token de acceso IOL
        
    Returns:
        Saldo disponible en ARS o None si hay error
    """
    try:
        url = "https://api.invertironline.com/api/v2/estadocuenta"
        headers = {
            'Authorization': f'Bearer {token_acceso}',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if not data or not isinstance(data, dict):
            raise ValueError("Respuesta inválida de la API")
            
        # Buscar todas las cuentas disponibles
        cuentas = data.get('cuentas', [])
        if not cuentas:
            raise ValueError("No se encontraron cuentas en el estado de cuenta")
            
        # Intentar encontrar una cuenta en pesos
        for cuenta in cuentas:
            moneda = cuenta.get('moneda', '').upper()
            if moneda in ['PESO ARGENTINO', 'PESO', 'ARS', 'AR$']:
                disponible = cuenta.get('disponible')
                if disponible is not None:
                    return float(disponible)
                    
        # Si no se encontró cuenta en pesos, usar la primera cuenta disponible
        primera_cuenta = cuentas[0]
        moneda = primera_cuenta.get('moneda', '')
        disponible = primera_cuenta.get('disponible')
        if disponible is not None:
            return float(disponible)
            
        raise ValueError(f"No se encontró saldo disponible en ninguna cuenta")
        
    except Exception as e:
        st.warning(f"⚠️ No se pudo obtener saldo disponible: {str(e)}")
        # Si hay error, usar un valor nominal por defecto
        return 100000  # Valor nominal por defecto en ARS

def compute_efficient_frontier(rics, notional, target_returns, data):
    """
    Grafica la frontera eficiente con múltiples portafolios optimizados
    
    Args:
        rics: Lista de activos
        notional: Capital total a invertir
        target_returns: Lista de retornos objetivos para los portafolios
        data: Datos históricos de precios
    """
    try:
        if not rics or not isinstance(rics, list):
            raise ValueError("Los RICs deben ser una lista no vacía")
            
        if not data or not isinstance(data, dict):
            raise ValueError("Los datos deben ser un diccionario")
        
        # Filtrar RICs con datos válidos
        valid_rics = []
        for ric in rics:
            df = data.get(ric)
            if df is not None and not df.empty:
                price_col = next((col for col in df.columns if col.lower() in ['cierre', 'close', 'precio', 'price', 'ultimoprecio']), None)
                if price_col is not None:
                    df = df.rename(columns={price_col: 'Cierre'})
                    data[ric] = df
                    valid_rics.append(ric)
        
        if not valid_rics:
            raise ValueError("No se encontraron datos de precios válidos")
        
        # Inicializar manager
        port_mgr = manager(valid_rics, notional, data)
        
        if port_mgr.returns is None or port_mgr.returns.empty:
            raise ValueError("No hay datos de retornos válidos")
            
        if port_mgr.cov_matrix is None:
            raise ValueError("No se pudo calcular la matriz de covarianza")
        
        # Crear figura de Plotly
        fig = go.Figure()
        
        # Agregar puntos de los activos individuales
        asset_returns = []
        asset_volatilities = []
        
        for ric in valid_rics:
            df = data[ric]
            if 'Cierre' not in df.columns:
                continue
                
            returns = df['Cierre'].pct_change().dropna()
            if not returns.empty:
                annual_return = returns.mean() * 252
                annual_vol = returns.std() * np.sqrt(252)
                asset_returns.append(annual_return)
                asset_volatilities.append(annual_vol)
        
        # Agregar activos individuales al gráfico
        fig.add_trace(go.Scatter(
            x=asset_volatilities,
            y=asset_returns,
            mode='markers+text',
            text=valid_rics,
            textposition="top center",
            name="Activos",
            marker=dict(size=10, color='blue'),
            opacity=0.7,
            hoverinfo='text+name',
            hovertext=[f"{ric}<br>Retorno: {ret:.2%}<br>Volatilidad: {vol:.2%}" 
                      for ric, ret, vol in zip(valid_rics, asset_returns, asset_volatilities)]
        ))
        
        # Calcular y agregar portafolios optimizados
        portfolio_data = []
        
        for i, target in enumerate(target_returns):
            try:
                port = port_mgr.compute_portfolio('markowitz', target)
                if port and hasattr(port, 'volatility_annual') and hasattr(port, 'return_annual'):
                    portfolio_data.append({
                        'Retorno': port.return_annual,
                        'Volatilidad': port.volatility_annual,
                        'Sharpe': port.sharpe_ratio if hasattr(port, 'sharpe_ratio') else 0,
                        'Pesos': port.weights if hasattr(port, 'weights') else {}
                    })
            except Exception as e:
                st.warning(f"No se pudo calcular el portafolio para retorno objetivo {target}: {str(e)}")
        
        # Ordenar portafolios por volatilidad
        portfolio_data.sort(key=lambda x: x['Volatilidad'])
        
        # Agregar portafolios al gráfico
        if portfolio_data:
            # Línea de la frontera eficiente
            fig.add_trace(go.Scatter(
                x=[p['Volatilidad'] for p in portfolio_data],
                y=[p['Retorno'] for p in portfolio_data],
                mode='lines',
                name='Frontera Eficiente',
                line=dict(color='green', width=2, dash='dash'),
                hoverinfo='none'
            ))
            
            # Puntos de los portafolios
            for i, port in enumerate(portfolio_data):
                fig.add_trace(go.Scatter(
                    x=[port['Volatilidad']],
                    y=[port['Retorno']],
                    mode='markers',
                    name=f'Portafolio {i+1}',
                    marker=dict(size=12, color='red'),
                    text=f"Retorno: {port['Retorno']:.2%}<br>"
                         f"Volatilidad: {port['Volatilidad']:.2%}<br>"
                         f"Sharpe: {port['Sharpe']:.2f}<br>"
                         f"Pesos: {', '.join([f'{k}: {v:.1%}' for k, v in port['Pesos'].items()])}",
                    hoverinfo='text+name',
                    visible='legendonly'  # Inicialmente ocultos, se muestran desde la leyenda
                ))
        
        # Configuración del layout
        fig.update_layout(
            title='Frontera Eficiente del Portafolio',
            xaxis_title='Volatilidad Anual',
            yaxis_title='Retorno Anual',
            showlegend=True,
            template='plotly_white',
            height=600,
            hovermode='closest',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Mostrar el gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar tabla con los portafolios
        if portfolio_data:
            st.subheader("Resumen de Portafolios")
            portfolio_df = pd.DataFrame([{
                'Portafolio': f'Portafolio {i+1}',
                'Retorno Anual': f"{p['Retorno']:.2%}",
                'Volatilidad Anual': f"{p['Volatilidad']:.2%}",
                'Ratio de Sharpe': f"{p['Sharpe']:.2f}",
                'Activos': ', '.join([f'{k} ({v:.1%})' for k, v in p['Pesos'].items()])
            } for i, p in enumerate(portfolio_data)])
            
            st.dataframe(portfolio_df, use_container_width=True, hide_index=True)
        
        return None, None, None
            
    except Exception as e:
        st.error(f"❌ Error calculando la frontera eficiente: {str(e)}")
        import traceback
        st.error(f"Detalles: {traceback.format_exc()}")
        return None, None, None

def optimize_portfolio_advanced(returns, target_return=None, strategy='markowitz', risk_free_rate=0.02):
    """
    Optimización avanzada de portafolio con múltiples estrategias
    
    Args:
        returns: DataFrame con los retornos de los activos
        target_return: Retorno objetivo anualizado (opcional)
        strategy: Estrategia de optimización ('markowitz', 'risk_parity', 'min_var')
        risk_free_rate: Tasa libre de riesgo anual
        
    Returns:
        Array con los pesos óptimos
    """
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    n_assets = len(mean_returns)
    
    def portfolio_volatility(weights):
        return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    
    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    bounds = tuple((0, 1) for _ in range(n_assets))
    
    # Estrategias específicas
    if strategy == 'markowitz':
        if target_return is not None:
            constraints.append({
                'type': 'eq', 
                'fun': lambda x: np.sum(mean_returns * x) - target_return
            })
            objective = portfolio_volatility
        else:
            def neg_sharpe(weights):
                ret = np.sum(mean_returns * weights)
                vol = portfolio_volatility(weights)
                return -(ret - risk_free_rate) / vol if vol > 0 else np.inf
            objective = neg_sharpe
            
    elif strategy == 'risk_parity':
        def risk_parity_objective(weights):
            marginal_risk = np.dot(cov_matrix, weights)
            risk_contributions = weights * marginal_risk
            target_rc = np.ones(n_assets) / n_assets
            return np.sum((risk_contributions - target_rc)**2)
        objective = risk_parity_objective
        
    elif strategy == 'min_var':
        objective = portfolio_volatility
        
    # Optimización
    result = op.minimize(
        objective,
        x0=np.ones(n_assets)/n_assets,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )
    
    return result.x

class EnhancedPortfolioManager:
    def __init__(self, token_acceso, portafolio_data, fecha_desde, fecha_hasta):
        """
        Inicializa el manager de portafolio mejorado
        
        Args:
            token_acceso (str): Token de acceso a la API de IOL
            portafolio_data (dict): Datos del portafolio obtenidos de la API
            fecha_desde (date): Fecha inicio para datos históricos
            fecha_hasta (date): Fecha fin para datos históricos
        """
        self.token = token_acceso
        self.portafolio_data = portafolio_data
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.activos = self._procesar_activos()
        self.data_loaded = False
        self.returns = None
        self.prices = None
        self.mean_returns = None
        self.cov_matrix = None
        self.risk_free_rate = 0.40  # Tasa libre de riesgo para Argentina
        
    def _procesar_activos(self):
        """Procesa los activos del portafolio para optimización"""
        activos = []
        for activo in self.portafolio_data.get('activos', []):
            titulo = activo.get('titulo', {})
            simbolo = titulo.get('simbolo')
            mercado = titulo.get('mercado', 'bCBA')  # Default a BCBA
            
            if simbolo and mercado:
                activos.append({
                    'simbolo': simbolo,
                    'mercado': mercado,
                    'raw_data': activo  # Guardar datos originales
                })
        return activos
    
    def load_data(self):
        """Carga y preprocesa datos históricos para optimización"""
        try:
            simbolos = [a['simbolo'] for a in self.activos]
            mercados = [a['mercado'] for a in self.activos]
            
            # Obtener datos históricos
            data = {}
            with st.spinner('Obteniendo datos históricos...'):
                for simbolo, mercado in zip(simbolos, mercados):
                    serie = obtener_serie_historica_iol(
                        self.token,
                        mercado,
                        simbolo,
                        self.fecha_desde.strftime('%Y-%m-%d'),
                        self.fecha_hasta.strftime('%Y-%m-%d')
                    )
                    if serie is not None:
                        data[simbolo] = serie
            
            if not data:
                st.error("No se pudieron obtener datos históricos")
                return False
                
            # Convertir a DataFrame
            self.prices = pd.DataFrame(data)
            self.prices = self.prices.ffill().bfill().dropna()
            
            if self.prices.empty:
                st.error("No hay suficientes datos después del preprocesamiento")
                return False
                
            # Calcular retornos
            self.returns = self.prices.pct_change().dropna()
            self.mean_returns = self.returns.mean() * 252  # Anualizar
            self.cov_matrix = self.returns.cov() * 252     # Anualizar
            
            self.data_loaded = True
            return True
            
        except Exception as e:
            st.error(f"Error cargando datos: {str(e)}")
            return False
            
    def get_account_balance(self):
        """Obtiene el saldo disponible de la cuenta"""
        url = "https://api.invertironline.com/api/v2/estadocuenta"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                # Buscar saldo disponible en pesos
                for cuenta in data.get('cuentas', []):
                    if cuenta.get('moneda', '').upper() in ['PESO ARGENTINO', 'PESO', 'ARS']:
                        disponible = cuenta.get('disponible')
                        if disponible is not None:
                            return float(disponible)
                
                # Si no encuentra en pesos, devolver primer saldo disponible
                for cuenta in data.get('cuentas', []):
                    disponible = cuenta.get('disponible')
                    if disponible is not None:
                        return float(disponible)
                        
                return 0.0
            else:
                st.warning(f"No se pudo obtener saldo. Código: {response.status_code}")
                return 0.0
        except Exception as e:
            st.warning(f"Error obteniendo saldo: {str(e)}")
            return 0.0
    
    def optimize_portfolio(self, strategy='markowitz', target_return=None):
        """
        Optimiza el portafolio según la estrategia seleccionada
        
        Args:
            strategy (str): Estrategia de optimización
                - 'markowitz': Optimización de Markowitz (max Sharpe ratio)
                - 'min_var': Minimiza varianza
                - 'risk_parity': Paridad de riesgo
                - 'equi_weight': Pesos iguales
            target_return (float): Retorno objetivo anual (solo para Markowitz)
        
        Returns:
            dict: Resultados de la optimización
        """
        if not self.data_loaded:
            if not self.load_data():
                return None
                
        n_assets = len(self.returns.columns)
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        # Función para calcular volatilidad del portafolio
        def portfolio_volatility(weights):
            return np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
        
        # Configurar según estrategia
        if strategy == 'markowitz':
            if target_return is not None:
                # Optimización con retorno objetivo
                constraints = [
                    {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                    {'type': 'eq', 'fun': lambda x: np.sum(self.mean_returns * x) - target_return}
                ]
                objective = portfolio_volatility
            else:
                # Maximizar Sharpe Ratio
                def neg_sharpe(weights):
                    ret = np.sum(self.mean_returns * weights)
                    vol = portfolio_volatility(weights)
                    return -(ret - self.risk_free_rate) / vol if vol > 0 else np.inf
                objective = neg_sharpe
                constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
                
        elif strategy == 'min_var':
            # Minimizar varianza
            objective = portfolio_volatility
            constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
            
        elif strategy == 'risk_parity':
            # Paridad de riesgo
            def risk_parity_objective(weights):
                marginal_risk = np.dot(self.cov_matrix, weights)
                risk_contributions = weights * marginal_risk
                target_rc = np.ones(n_assets) / n_assets
                return np.sum((risk_contributions - target_rc)**2)
            objective = risk_parity_objective
            constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
            
        elif strategy == 'equi_weight':
            # Pesos iguales
            weights = np.ones(n_assets) / n_assets
            return self._create_result(weights)
            
        else:
            st.error("Estrategia no reconocida")
            return None
            
        # Optimización
        initial_weights = np.ones(n_assets) / n_assets
        result = op.minimize(
            objective,
            x0=initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            return self._create_result(result.x)
        else:
            st.warning("La optimización no convergió. Usando pesos iguales.")
            return self._create_result(initial_weights)
    
    def _create_result(self, weights):
        """Crea el diccionario de resultados con métricas"""
        port_return = np.sum(self.mean_returns * weights)
        port_vol = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
        sharpe = (port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0
        
        # DataFrame con asignación
        df_allocation = pd.DataFrame({
            'Activo': self.returns.columns,
            'Peso': weights,
            'Retorno Esperado': self.mean_returns,
            'Volatilidad': np.sqrt(np.diag(self.cov_matrix))
        }).sort_values('Peso', ascending=False)
        
        return {
            'weights': weights,
            'return': port_return,
            'volatility': port_vol,
            'sharpe': sharpe,
            'allocation': df_allocation,
            'returns': self.returns.dot(weights)  # Retornos diarios del portafolio
        }
    
    def compute_efficient_frontier(self, n_points=20):
        """Calcula la frontera eficiente"""
        if not self.data_loaded:
            if not self.load_data():
                return None, None
                
        min_ret = np.min(self.mean_returns)
        max_ret = np.max(self.mean_returns)
        target_returns = np.linspace(min_ret, max_ret, n_points)
        
        frontiers = []
        volatilities = []
        
        for ret in target_returns:
            result = self.optimize_portfolio('markowitz', ret)
            if result:
                frontiers.append(result['return'])
                volatilities.append(result['volatility'])
        
        return frontiers, volatilities


class PortfolioManager:
    def __init__(self, activos, token, fecha_desde, fecha_hasta, saldo_disponible=None, tasa_libre_riesgo=0.02):
        """
        Inicializa el manager de portafolio
        
        Args:
            activos: Lista de activos con sus mercados
            token: Token de acceso IOL
            fecha_desde: Fecha inicio de datos
            fecha_hasta: Fecha fin de datos
            saldo_disponible: Saldo disponible en cuenta (opcional)
            tasa_libre_riesgo: Tasa libre de riesgo anual (default 2%)
        """
        self.activos = activos
        self.token = token
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.data_loaded = False
        self.returns = None
        self.prices = None
        self.notional = saldo_disponible or 100000  # Usar saldo disponible si se proporciona
        self.manager = None
        self.tasa_libre_riesgo = tasa_libre_riesgo
        self.data = None
        
    @lru_cache(maxsize=100)
    def _cached_historical_data(self, symbol, market, start_date, end_date):
        """
        Obtiene datos históricos con caché
        
        Args:
            symbol: Símbolo del activo
            market: Mercado del activo
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            DataFrame con los datos históricos o None si hay error
        """
        try:
            return obtener_serie_historica_iol(
                token_portador=self.token,
                mercado=market,
                simbolo=symbol,
                fecha_desde=start_date,
                fecha_hasta=end_date
            )
        except Exception as e:
            st.warning(f"Error al obtener datos para {symbol}: {str(e)}")
            return None
    
    def _load_data_parallel(self):
        """
        Carga datos de múltiples activos en paralelo
        
        Returns:
            Dict con DataFrames de precios por símbolo
        """
        all_data = {}
        
        if not self.activos:
            st.warning("No hay activos para cargar")
            return all_data
            
        with ThreadPoolExecutor(max_workers=min(5, len(self.activos))) as executor:
            futures = []
            
            # Programar la carga de datos para cada activo
            for asset in self.activos:
                if not isinstance(asset, dict) or 'simbolo' not in asset:
                    st.warning(f"Formato de activo inválido: {asset}")
                    continue
                    
                future = executor.submit(
                    self._cached_historical_data,
                    symbol=asset['simbolo'],
                    market=asset.get('mercado', 'BCBA'),
                    start_date=self.fecha_desde,
                    end_date=self.fecha_hasta
                )
                futures.append((asset['simbolo'], future))
            
            # Procesar los resultados a medida que estén disponibles
            for symbol, future in futures:
                try:
                    data = future.result()
                    if data is not None and not data.empty:
                        # Buscar columna de precios (puede variar según el tipo de activo)
                        price_columns = [
                            col for col in data.columns 
                            if col.lower() in ['cierre', 'ultimoprecio', 'precio', 'close', 'price']
                        ]
                        if price_columns:
                            price_col = price_columns[0]
                            all_data[symbol] = data[price_col]
                        else:
                            st.warning(f"No se encontró columna de precios para {symbol}")
                except Exception as e:
                    st.warning(f"Error procesando datos para {symbol}: {str(e)}")
        
        return all_data
    
    def _preprocess_data(self, data_dict):
        """Preprocesa los datos históricos"""
        if not data_dict:
            return None, None
            
        # Unir todos los datos en un solo DataFrame
        prices = pd.concat(data_dict.values(), axis=1, keys=data_dict.keys())
        prices = prices.ffill().bfill()  # Rellenar valores faltantes
        
        # Calcular retornos logarítmicos
        returns = np.log(prices / prices.shift(1)).dropna()
        
        return prices, returns
        
    def rebalanceo_aleatorio(self, panel='BCBA', cantidad_activos=5, cantidad_simulaciones=1000, target_return=None):
        """
        Realiza un rebalanceo aleatorio del portafolio
        
        Args:
            panel: Panel de cotizaciones (BCBA, NYSE, etc.)
            cantidad_activos: Número de activos a seleccionar
            cantidad_simulaciones: Número de simulaciones a realizar
            target_return: Retorno objetivo (opcional)
        
        Returns:
            DataFrame con los activos seleccionados y sus precios
        """
        try:
            # Obtener todos los tickers del panel
            tickers = self._obtener_tickers_panel(panel)
            
            if not tickers:
                raise ValueError(f"No se encontraron tickers para el panel {panel}")
                
            # Seleccionar activos aleatoriamente
            tickers_seleccionados = random.sample(tickers, min(cantidad_activos, len(tickers)))
            
            # Obtener datos históricos para los activos seleccionados
            data_frames = {}
            
            with st.spinner("Obteniendo datos históricos..."):
                for simbolo in tickers_seleccionados:
                    df = obtener_serie_historica_iol(
                        self.token,
                        panel,
                        simbolo,
                        self.fecha_desde,
                        self.fecha_hasta
                    )
                    
                    if df is not None and not df.empty:
                        # Verificar que el DataFrame tenga la columna 'Cierre'
                        if 'Cierre' not in df.columns:
                            raise ValueError(f"DataFrame para {simbolo} no tiene columna 'Cierre'")
                            
                        # Verificar que no haya valores nulos en la columna 'Cierre'
                        if df['Cierre'].isnull().any():
                            raise ValueError(f"Valores nulos en la columna 'Cierre' para {simbolo}")
                            
                        data_frames[simbolo] = df
                        
            if not data_frames:
                raise ValueError("No se pudieron cargar datos históricos para ningún activo")
                
            # Verificar que todos los DataFrames tengan la misma longitud
            lengths = [len(df) for df in data_frames.values()]
            if len(set(lengths)) > 1:
                raise ValueError("Los DataFrames tienen longitudes diferentes")
                
            # Convertir a DataFrame con múltiples columnas
            self.prices = pd.concat(
                [df['Cierre'].rename(simbolo) for simbolo, df in data_frames.items()],
                axis=1
            )
            
            # Calcular retornos
            self.returns = self.prices.pct_change().dropna()
            
            if self.returns.empty:
                raise ValueError("No se pudieron calcular retornos válidos")
                
            # Calcular estadísticas de retornos
            mean_returns = self.returns.mean() * 252  # Anualizar retornos
            std_returns = self.returns.std() * np.sqrt(252)  # Anualizar volatilidad
            
            # Ajustar cantidad de simulaciones según el retorno objetivo
            if target_return is not None:
                # Calcular el ratio de Sharpe esperado
                sharpe_ratio = (target_return - self.tasa_libre_riesgo) / std_returns.mean()
                
                # Ajustar cantidad de simulaciones según el ratio de Sharpe
                if sharpe_ratio < 0.5:
                    cantidad_simulaciones = int(max(1000, cantidad_simulaciones * 0.5))  # Reducir para retornos bajos
                elif sharpe_ratio < 1.0:
                    cantidad_simulaciones = int(max(2000, cantidad_simulaciones * 0.75))  # Moderado
                else:
                    cantidad_simulaciones = int(max(5000, cantidad_simulaciones * 1.5))  # Aumentar para retornos altos
            
            # Generar portafolios aleatorios
            best_sharpe = -np.inf
            best_weights = None
            
            for _ in range(cantidad_simulaciones):
                # Generar pesos aleatorios
                weights = np.random.random(len(mean_returns))
                weights /= np.sum(weights)
                
                # Calcular retorno y volatilidad del portafolio
                portfolio_return = np.sum(mean_returns * weights)
                portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(self.returns.cov() * 252, weights)))
                
                # Calcular ratio de Sharpe
                sharpe_ratio = (portfolio_return - self.tasa_libre_riesgo) / portfolio_volatility
                
                # Actualizar mejor portafolio encontrado
                if sharpe_ratio > best_sharpe:
                    best_sharpe = sharpe_ratio
                    best_weights = weights
            
            if best_weights is not None:
                # Crear DataFrame de resultados
                df_resultados = pd.DataFrame({
                    'Activo': mean_returns.index,
                    'Peso': best_weights,
                    'Retorno Anual': mean_returns,
                    'Volatilidad Anual': std_returns
                })
                
                # Ordenar por peso
                df_resultados = df_resultados.sort_values('Peso', ascending=False)
                
                return df_resultados
            
            raise ValueError("No se pudo encontrar un portafolio óptimo")
            
        except Exception as e:
            st.error(f"❌ Error en rebalanceo aleatorio: {str(e)}")
            return None
            
    def _obtener_tickers_panel(self, panel):
        """Obtiene la lista de tickers disponibles para un panel"""
        url = f'https://api.invertironline.com/api/v2/cotizaciones-orleans/{panel}/Argentina/Operables'
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            datos = response.json()
            return [titulo['simbolo'] for titulo in datos.get('titulos', [])]
        except Exception as e:
            st.warning(f"⚠️ Error obteniendo tickers para {panel}: {str(e)}")
            return []
    
    def load_data(self):
        """
        Carga los datos históricos de los activos de manera eficiente
        
        Returns:
            bool: True si la carga fue exitosa, False en caso contrario
        """
        try:
            if not self.activos:
                st.error("No se han proporcionado activos para cargar")
                return False
                
            # Inicializar estructura para almacenar los datos
            all_data = {}
            
            # Usar ThreadPoolExecutor para cargar datos en paralelo
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                
                # Programar la carga de datos para cada activo
                for activo in self.activos:
                    if not isinstance(activo, dict) or 'simbolo' not in activo:
                        st.warning(f"Formato de activo inválido: {activo}")
                        continue
                        
                    future = executor.submit(
                        obtener_serie_historica_iol,
                        token_portador=self.token,
                        mercado=activo.get('mercado', 'BCBA'),
                        simbolo=activo['simbolo'],
                        fecha_desde=self.fecha_desde,
                        fecha_hasta=self.fecha_hasta
                    )
                    futures.append((activo['simbolo'], future))
                
                # Procesar los resultados a medida que estén disponibles
                for symbol, future in futures:
                    try:
                        data = future.result()
                        if data is not None and not data.empty:
                            # Buscar columna de precios (puede variar según el tipo de activo)
                            price_columns = [col for col in data.columns if col.lower() in ['cierre', 'ultimoprecio', 'precio', 'close', 'price']]
                            if price_columns:
                                price_col = price_columns[0]
                                all_data[symbol] = data[price_col]
                            else:
                                st.warning(f"No se encontró columna de precios para {symbol}")
                    except Exception as e:
                        st.warning(f"Error procesando datos para {symbol}: {str(e)}")
            
            # Verificar si se cargaron datos
            if not all_data:
                st.error("No se pudieron cargar datos para ningún activo")
                return False
            
            # Crear DataFrame con los precios
            self.prices = pd.DataFrame(all_data)
            
            # Manejar valores faltantes
            self.prices = self.prices.ffill().bfill()
            
            # Calcular retornos logarítmicos diarios
            self.returns = np.log(self.prices / self.prices.shift(1)).dropna()
            
            # Validar que haya suficientes datos
            if self.returns.empty or len(self.returns) < 5:  # Mínimo 5 días de datos
                st.error("No hay suficientes datos para realizar el análisis")
                return False
            
            # Calcular estadísticas básicas
            self.mean_returns = self.returns.mean() * 252  # Anualizado
            self.cov_matrix = self.returns.cov() * 252     # Matriz de covarianza anualizada
            
            self.data_loaded = True
            return True
            
        except Exception as e:
            st.error(f"Error al cargar los datos: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return False
    
    def optimize_portfolio_bayes(self, n_iter=25, init_points=5):
        """
        Optimización bayesiana de portafolio
        
        Args:
            n_iter: Número de iteraciones de optimización
            init_points: Número de puntos iniciales para la optimización
            
        Returns:
            Diccionario con los resultados de la optimización
        """
        if not self.data_loaded:
            if not self.load_data():
                return None
                
        mean_returns = self.returns.mean() * 252
        cov_matrix = self.returns.cov() * 252
        n_assets = len(mean_returns)
        
        def objective(**weights):
            """Función objetivo para la optimización bayesiana"""
            w = np.array([weights[f'w{i}'] for i in range(n_assets)])
            w = w / np.sum(w)  # Normalizar pesos
            
            # Calcular métricas
            port_return = np.sum(mean_returns * w)
            port_vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
            sharpe = (port_return - self.tasa_libre_riesgo) / port_vol if port_vol > 0 else 0
            
            return sharpe
        
        # Espacio de búsqueda para los pesos
        pbounds = {f'w{i}': (0, 1) for i in range(n_assets)}
        
        # Optimización bayesiana
        optimizer = BayesianOptimization(
            f=objective,
            pbounds=pbounds,
            random_state=42,
            allow_duplicate_points=True
        )
        
        optimizer.maximize(
            init_points=init_points,
            n_iter=n_iter
        )
        
        # Obtener mejores pesos
        best_weights = np.array([optimizer.max['params'][f'w{i}'] for i in range(n_assets)])
        best_weights = best_weights / np.sum(best_weights)  # Normalizar
        
        # Calcular métricas finales
        port_return = np.sum(mean_returns * best_weights)
        port_vol = np.sqrt(np.dot(best_weights.T, np.dot(cov_matrix, best_weights)))
        sharpe = (port_return - self.tasa_libre_riesgo) / port_vol if port_vol > 0 else 0
        
        return {
            'weights': best_weights,
            'assets': [a['simbolo'] for a in self.activos],
            'returns': self.returns,
            'performance': {
                'return': port_return,
                'volatility': port_vol,
                'sharpe': sharpe
            },
            'optimizer': optimizer
        }
    
    def compute_portfolio(self, strategy='markowitz', target_return=None, use_bayesian=False):
        """
        Calcula el portafolio óptimo según la estrategia especificada
        
        Args:
            strategy: Estrategia de optimización ('markowitz', 'risk_parity', 'min_var')
            target_return: Retorno objetivo para la estrategia de Markowitz
            use_bayesian: Si es True, usa optimización bayesiana (solo para estrategia 'markowitz')
            
        Returns:
            Diccionario con los resultados de la optimización
        """
        if not self.data_loaded:
            if not self.load_data():
                return None
        
        try:
            if strategy == 'markowitz' and use_bayesian:
                return self.optimize_portfolio_bayes()
                
            # Usar la función de optimización avanzada
            weights = optimize_portfolio_advanced(
                returns=self.returns,
                target_return=target_return,
                strategy=strategy,
                risk_free_rate=self.tasa_libre_riesgo
            )
            
            # Calcular métricas del portafolio
            mean_returns = self.returns.mean() * 252
            cov_matrix = self.returns.cov() * 252
            
            port_return = np.sum(mean_returns * weights)
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe = (port_return - self.tasa_libre_riesgo) / port_vol if port_vol > 0 else 0
            
            # Calcular contribución al riesgo
            marginal_risk = np.dot(cov_matrix, weights)
            risk_contributions = weights * marginal_risk
            risk_contributions_pct = risk_contributions / port_vol**2 if port_vol > 0 else np.zeros_like(weights)
            
            # Crear resultado
            result = {
                'weights': weights,
                'assets': [a['simbolo'] for a in self.activos],
                'returns': self.returns,
                'risk_contributions': risk_contributions_pct,
                'performance': {
                    'return': port_return,
                    'volatility': port_vol,
                    'sharpe': sharpe,
                    'sortino': self._calculate_sortino_ratio(weights),
                    'max_drawdown': self._calculate_max_drawdown(weights)
                }
            }
            
            return result
            
        except Exception as e:
            st.error(f"Error al optimizar el portafolio: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return None
    
    def _calculate_sortino_ratio(self, weights, target_return=0, risk_free_rate=None):
        """Calcula el ratio de Sortino para el portafolio"""
        if risk_free_rate is None:
            risk_free_rate = self.tasa_libre_riesgo
            
        port_returns = (self.returns * weights).sum(axis=1)
        excess_returns = port_returns - (risk_free_rate / 252)  # Retorno diario excedente
        
        # Calcular desviación a la baja
        downside_returns = np.minimum(0, port_returns - (target_return / 252))
        downside_deviation = np.sqrt(np.mean(downside_returns**2)) * np.sqrt(252)
        
        # Calcular retorno anualizado
        annualized_return = np.prod(1 + port_returns)**(252/len(port_returns)) - 1
        
        # Calcular ratio de Sortino
        if downside_deviation > 0:
            sortino_ratio = (annualized_return - risk_free_rate) / downside_deviation
        else:
            sortino_ratio = np.nan
            
        return sortino_ratio
    
    def _calculate_max_drawdown(self, weights):
        """
        Calcula el máximo drawdown del portafolio
        
        Args:
            weights: Vector de pesos del portafolio
            
        Returns:
            float: Máximo drawdown del portafolio
        """
        port_returns = (self.returns * weights).sum(axis=1)
        cumulative_returns = (1 + port_returns).cumprod()
        
        # Calcular máximo acumulado
        rolling_max = cumulative_returns.cummax()
        
        # Calcular drawdowns
        drawdowns = (cumulative_returns - rolling_max) / rolling_max
        
        # Retornar el máximo drawdown
        return drawdowns.min()

# ... (rest of the code remains the same)
# Removed stray error handling code that was causing indentation issues

    try:
        manager_inst = PortfolioManager(activos_para_optimizacion, token_acceso, fecha_desde, fecha_hasta)
        
        if manager_inst.load_data():
            try:
                portfolios, returns, volatilities = manager_inst.compute_efficient_frontier(
                    target_return=target_return, include_min_variance=True
                )
                
                if portfolios and returns and volatilities:
                    st.success("✅ Frontera eficiente calculada")
                    st.markdown("#### 📊 Comparación de Estrategias")
                    
                    st.markdown("#### 📊 Comparación de Estrategias")
                    comparison_data = []
                    for label, portfolio in portfolios.items():
                        comparison_data.append({
                            'Estrategia': label,
                            'Retorno Anual': portfolio.return_annual,
                            'Volatilidad Anual': portfolio.volatility_annual,
                            'Ratio de Sharpe': portfolio.sharpe_ratio,
                            'Pesos': portfolio.weights
                        })
                    
                    df_comparison = pd.DataFrame(comparison_data)
                    st.dataframe(df_comparison, use_container_width=True)
                
                else:
                    st.error("❌ No se pudo calcular la frontera eficiente")
                
            except Exception as e:
                st.error(f"❌ Error en el cálculo de la frontera eficiente: {str(e)}")
                st.error(f"Detalles: {str(e)}")
            
        else:
            st.error("❌ No se pudieron cargar los datos históricos")
            
    except Exception as e:
        st.error(f"❌ Error general en el proceso de optimización: {str(e)}")
        st.error(f"Detalles: {str(e)}")
    
    # Información adicional extendida
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

def mostrar_optimizacion_portafolio(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Muestra la interfaz de optimización de portafolio usando la clase mejorada
    """
    st.markdown("### 🎯 Optimización Avanzada de Portafolio")
    
    # Configuración de la optimización
    col1, col2 = st.columns(2)
    with col1:
        estrategia = st.selectbox(
            "Estrategia de Optimización",
            options=['markowitz', 'min_var', 'risk_parity', 'equi_weight'],
            format_func=lambda x: {
                'markowitz': 'Markowitz (Max Sharpe)',
                'min_var': 'Mínima Varianza',
                'risk_parity': 'Paridad de Riesgo',
                'equi_weight': 'Pesos Iguales'
            }[x]
        )
    
    with col2:
        target_return = None
        if estrategia == 'markowitz':
            target_return = st.slider(
                "Retorno Objetivo Anual",
                min_value=0.0, max_value=1.0, value=0.08, step=0.01
            )
    
    if st.button("🚀 Optimizar Portafolio"):
        with st.spinner("Optimizando portafolio..."):
            try:
                # Crear instancia del manager mejorado
                manager = EnhancedPortfolioManager(
                    token_acceso,
                    portafolio,
                    fecha_desde,
                    fecha_hasta
                )
                
                # Cargar datos y optimizar
                if manager.load_data():
                    result = manager.optimize_portfolio(estrategia, target_return)
                    
                    if result:
                        st.success("✅ Optimización completada")
                        
                        # Mostrar resultados
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 📊 Asignación de Activos")
                            st.dataframe(
                                result['allocation'].style.format({
                                    'Peso': '{:.2%}',
                                    'Retorno Esperado': '{:.2%}',
                                    'Volatilidad': '{:.2%}'
                                }),
                                use_container_width=True
                            )
                        
                        with col2:
                            st.markdown("#### 📈 Métricas del Portafolio")
                            st.metric("Retorno Esperado", f"{result['return']:.2%}")
                            st.metric("Volatilidad", f"{result['volatility']:.2%}")
                            st.metric("Ratio de Sharpe", f"{result['sharpe']:.2f}")
                        
                        # Gráfico de distribución de pesos
                        st.markdown("#### 📊 Distribución de Pesos")
                        fig = go.Figure(go.Pie(
                            labels=result['allocation']['Activo'],
                            values=result['allocation']['Peso'],
                            textinfo='label+percent'
                        ))
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Calcular frontera eficiente si es Markowitz
                        if estrategia == 'markowitz':
                            st.markdown("#### 🌐 Frontera Eficiente")
                            frontiers, volatilities = manager.compute_efficient_frontier()
                            
                            if frontiers and volatilities:
                                fig = go.Figure()
                                fig.add_trace(go.Scatter(
                                    x=volatilities,
                                    y=frontiers,
                                    mode='lines',
                                    name='Frontera Eficiente'
                                ))
                                fig.add_trace(go.Scatter(
                                    x=[result['volatility']],
                                    y=[result['return']],
                                    mode='markers',
                                    marker=dict(size=12, color='red'),
                                    name='Portafolio Óptimo'
                                ))
                                fig.update_layout(
                                    title='Frontera Eficiente',
                                    xaxis_title='Volatilidad',
                                    yaxis_title='Retorno Esperado'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("❌ No se pudieron cargar los datos para optimización")
                    
            except Exception as e:
                st.error(f"❌ Error durante la optimización: {str(e)}")
    
    # Explicación de estrategias
    with st.expander("ℹ️ Explicación de Estrategias"):
        st.markdown("""
        **Markowitz (Max Sharpe Ratio):**
        - Maximiza el ratio de retorno/riesgo
        - Considera correlaciones entre activos
        - Puede especificar retorno objetivo
        
        **Mínima Varianza:**
        - Minimiza la volatilidad del portafolio
        - No considera retornos esperados
        - Bueno para inversores conservadores
        
        **Paridad de Riesgo:**
        - Distribuye el riesgo equitativamente
        - No requiere estimación de retornos
        - Popular en estrategias institucionales
        
        **Pesos Iguales:**
        - Asignación simple e igualitaria
        - No requiere optimización
        - Buen benchmark para comparación
        """)


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
    if 'cliente_seleccionado' not in st.session_state or not st.session_state.cliente_seleccionado:
        st.error("No hay cliente seleccionado")
        return

    cliente = st.session_state.cliente_seleccionado
    id_cliente = cliente.get('numeroCliente', cliente.get('id'))
    nombre_cliente = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))

    st.title(f"Análisis de Portafolio - {nombre_cliente}")
    
    # Obtener datos del cliente una sola vez
    portafolio = obtener_portafolio(st.session_state.token_acceso, id_cliente)
    estado_cuenta = obtener_estado_cuenta(st.session_state.token_acceso, id_cliente)
    
    # Crear tabs con iconos
    tab1, tab2, tab3 = st.tabs([
        "Portafolio", 
        "Optimización",
        "Estado de Cuenta"
    ])
    
    with tab1:
        if portafolio:
            mostrar_resumen_portafolio(portafolio)
        else:
            st.warning("No se pudo obtener el portafolio del cliente")
    
    with tab2:
        if portafolio:
            mostrar_optimizacion_portafolio(
                portafolio,
                st.session_state.token_acceso,
                st.session_state.fecha_desde,
                st.session_state.fecha_hasta
            )
        else:
            st.warning("No se puede optimizar sin datos del portafolio")
    
    with tab3:
        if estado_cuenta:
            # Usar la clase mejorada para mostrar saldos
            manager = EnhancedPortfolioManager(
                st.session_state.token_acceso,
                portafolio or {},
                st.session_state.fecha_desde,
                st.session_state.fecha_hasta
            )
            
            # Mostrar saldo disponible
            with st.container():
                st.subheader("Saldos Disponibles")
                saldo_disponible = manager.get_account_balance()
                st.metric("Saldo Disponible", f"${saldo_disponible:,.2f}")
                
                # Botón para actualizar saldo
                if st.button("Actualizar Saldo", key="actualizar_saldo"):
                    saldo_actualizado = manager.get_account_balance()
                    st.rerun()
            
            # Mostrar estado de cuenta completo
            st.subheader("Estado de Cuenta")
            mostrar_estado_cuenta(estado_cuenta)
        else:
            st.warning("No se pudo obtener el estado de cuenta")

def main():
    st.title("IOL Portfolio Analyzer")
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
                ("🏠 Inicio", "📊 Análisis de Portafolio", "💰 Tasas de Caución", "👨\u200d💼 Panel del Asesor"),
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

if __name__ == "__main__":
    main()
