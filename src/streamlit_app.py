import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import base64
import io
import matplotlib.pyplot as plt
from scipy import stats
import seaborn as sns
from scipy.optimize import minimize
import warnings
import random
from typing import Dict, List, Tuple, Optional, Union
warnings.filterwarnings('ignore')

# Configuración de la API
API_BASE_URL = 'https://api.invertironline.com'
TOKEN_URL = f"{API_BASE_URL}/token"

class IOLDataFetcher:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self._authenticate()
    
    def _authenticate(self) -> bool:
        """Autentica y obtiene los tokens de acceso"""
        payload = {
            'username': self.username,
            'password': self.password,
            'grant_type': 'password'
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(TOKEN_URL, data=payload, headers=headers)
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens['access_token']
            self.refresh_token = tokens['refresh_token']
            return True
        else:
            st.error(f"Error de autenticación: {response.status_code} - {response.text}")
            return False
    
    def _refresh_token(self) -> bool:
        """Actualiza el token de acceso usando el refresh token"""
        if not self.refresh_token:
            return self._authenticate()
            
        payload = {
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(TOKEN_URL, data=payload, headers=headers)
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens['access_token']
            self.refresh_token = tokens.get('refresh_token', self.refresh_token)
            return True
        else:
            return self._authenticate()
    
    def _make_request(self, endpoint: str, method: str = 'GET', **kwargs) -> Optional[dict]:
        """Realiza una petición autenticada a la API"""
        if not self.access_token:
            if not self._authenticate():
                return None
        
        url = f"{API_BASE_URL}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, **kwargs)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, **kwargs)
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:  # Token expirado
                if self._refresh_token():
                    return self._make_request(endpoint, method, **kwargs)
            
            st.error(f"Error en la petición {endpoint}: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            st.error(f"Error al realizar la petición a {endpoint}: {str(e)}")
            return None
    
    def get_historical_data(self, symbol: str, market: str, 
                          start_date: str, end_date: str, 
                          adjusted: bool = False) -> Optional[pd.DataFrame]:
        """Obtiene datos históricos para un símbolo en un mercado específico"""
        endpoint = f"/api/v2/{market}/Titulos/{symbol}/Cotizacion/seriehistorica/"
        endpoint += f"{start_date}/{end_date}/{'Ajustada' if adjusted else 'SinAjustar'}"
        
        data = self._make_request(endpoint)
        if data and isinstance(data, list):
            df = pd.DataFrame(data)
            if not df.empty and 'fecha' in df.columns:
                df['fecha'] = pd.to_datetime(df['fecha'])
                df.set_index('fecha', inplace=True)
                df.sort_index(inplace=True)
                return df
        return None
    
    def get_tickers_by_panel(self, panel: str, country: str = 'Argentina') -> List[dict]:
        """Obtiene los tickers disponibles para un panel específico"""
        endpoint = f'/api/v2/cotizaciones-orleans/{panel}/{country}/Operables'
        params = {
            'cotizacionInstrumentoModel.instrumento': panel,
            'cotizacionInstrumentoModel.pais': country.lower()
        }
        
        data = self._make_request(endpoint, params=params)
        if data and 'titulos' in data:
            return data['titulos']
        return []
    
    def get_random_assets(self, panels: List[str], n_assets: int, country: str = 'Argentina') -> Dict[str, List[dict]]:
        """Obtiene activos aleatorios de los paneles especificados"""
        selected_assets = {}
        
        for panel in panels:
            tickers = self.get_tickers_by_panel(panel, country)
            if tickers:
                # Seleccionar aleatoriamente hasta n_assets del panel
                selected = random.sample(tickers, min(n_assets, len(tickers)))
                selected_assets[panel] = selected
        
        return selected_assets
    
    def get_historical_data_for_assets(self, assets: Dict[str, List[dict]], 
                                     start_date: str, end_date: str,
                                     adjusted: bool = False) -> Dict[str, pd.DataFrame]:
        """Obtiene datos históricos para múltiples activos"""
        historical_data = {}
        
        for panel, asset_list in assets.items():
            for asset in asset_list:
                symbol = asset.get('simbolo')
                market = asset.get('mercado', 'BCBA')  # Por defecto BCBA si no se especifica
                
                if symbol and market:
                    df = self.get_historical_data(symbol, market, start_date, end_date, adjusted)
                    if df is not None and not df.empty:
                        asset_key = f"{panel}_{symbol}"
                        historical_data[asset_key] = df
        
        return historical_data

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
                            if fecha_parsed is not None:
                                precios.append(float(precio))
                                fechas.append(fecha_parsed)
                except (ValueError, AttributeError) as e:
                    continue
            
            if precios and fechas:
                serie = pd.Series(precios, index=fechas, name='precio')
                serie = serie[~serie.index.duplicated(keep='last')]
                return serie.sort_index()
        
        # Para respuestas que son un solo valor (ej: MEP)
        elif isinstance(data, (int, float)):
            return pd.Series([float(data)], index=[pd.Timestamp.now()], name='precio')
            
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

def get_historical_data_for_optimization(token_portador, simbolos, fecha_desde, fecha_hasta):
    """
    Obtiene datos históricos para optimización con manejo mejorado de errores,
    reintentos automáticos y soporte para FCIs
    """
    precios = {}
    errores = []
    max_retries = 2
    
    with st.spinner("Obteniendo datos históricos..."):
        progress_bar = st.progress(0)
        total_symbols = len(simbolos)
        
        for idx, (simbolo, mercado) in enumerate(simbolos):
            progress = (idx + 1) / total_symbols
            progress_bar.progress(progress, text=f"Procesando {simbolo} ({idx+1}/{total_symbols})")
            
            # Manejo especial para FCIs
            if mercado.lower() == 'fci':
                data = obtener_serie_historica_fci(token_portador, simbolo, fecha_desde, fecha_hasta)
                if data and 'ultimaCotizacion' in data and 'fecha' in data['ultimaCotizacion']:
                    try:
                        df = pd.DataFrame({
                            'fecha': [pd.to_datetime(data['ultimaCotizacion']['fecha'])],
                            'cierre': [data['ultimaCotizacion']['precio']]
                        })
                        df.set_index('fecha', inplace=True)
                        precios[simbolo] = df['cierre']
                    except Exception as e:
                        st.warning(f"Error al procesar datos del FCI {simbolo}: {str(e)}")
                        errores.append(simbolo)
                else:
                    st.warning(f"No se encontraron datos válidos para el FCI {simbolo}")
                    errores.append(simbolo)
                continue
                
            for attempt in range(max_retries):
                try:
                    # Intentar obtener datos de IOL
                    serie = obtener_serie_historica_iol(
                        token_portador=token_portador,
                        mercado=mercado,
                        simbolo=simbolo,
                        fecha_desde=fecha_desde,
                        fecha_hasta=fecha_hasta
                    )
                    
                    if serie is not None and not serie.empty:
                        precios[simbolo] = serie
                        break  # Salir del bucle de reintentos si tiene éxito
                    
                except Exception as e:
                    if attempt == max_retries - 1:  # Último intento
                        st.warning(f"No se pudo obtener datos para {simbolo} después de {max_retries} intentos: {str(e)}")
                        errores.append(simbolo)
                    continue
            
            # Pequeña pausa entre solicitudes para no saturar el servidor
            time.sleep(0.5)
        
        progress_bar.empty()
        
        if errores:
            st.warning(f"No se pudieron obtener datos para {len(errores)} de {len(simbolos)} activos")
        
        if precios:
            st.success(f"✅ Datos obtenidos para {len(precios)} de {len(simbolos)} activos")
            
            # Asegurarse de que todas las series tengan la misma longitud
            min_length = min(len(s) for s in precios.values()) if precios else 0
            if min_length < 5:  # Mínimo razonable de datos para optimización
                st.error("Los datos históricos son insuficientes para la optimización")
                return None, None, None
                
            # Crear DataFrame con las series alineadas
            df_precios = pd.DataFrame({k: v.iloc[-min_length:] for k, v in precios.items()})
            
            # Calcular retornos y validar
            returns = df_precios.pct_change().dropna()
            
            if returns.empty or len(returns) < 30:
                st.warning("No hay suficientes datos para el análisis")
                return None, None, None
                
            # Eliminar columnas con desviación estándar cero
            if (returns.std() == 0).any():
                columnas_constantes = returns.columns[returns.std() == 0].tolist()
                returns = returns.drop(columns=columnas_constantes)
                df_precios = df_precios.drop(columns=columnas_constantes)
                
                if returns.empty or len(returns.columns) < 2:
                    st.warning("No hay suficientes activos válidos para la optimización")
                    return None, None, None
                    
            mean_returns = returns.mean()
            cov_matrix = returns.cov()
            return mean_returns, cov_matrix, df_precios
        
    st.error("❌ No se pudieron cargar los datos históricos")
    return None, None, None

def calcular_metricas_portafolio(activos_data, valor_total):
    """
    Calcula métricas detalladas del portafolio, incluyendo FCIs si están presentes
    """
    try:
        # Procesar FCIs si existen
        fcis = [activo for activo in activos_data if activo.get('tipo_activo', '').lower() == 'fci']
        total_fci = 0
        porcentaje_fci = 0
        
        if fcis:
            total_fci = sum(activo.get('valor_actual', 0) for activo in fcis)
            porcentaje_fci = (total_fci / valor_total) * 100 if valor_total > 0 else 0
            
            # Agregar métricas específicas de FCIs
            for fci in fcis:
                fci['porcentaje_portafolio'] = (fci.get('valor_actual', 0) / valor_total) * 100 if valor_total > 0 else 0
                fci['rendimiento_anual'] = fci.get('variacion_anual', 0)
                fci['volatilidad_anual'] = fci.get('volatilidad_anual', 0)
                fci['sharpe_ratio'] = fci.get('sharpe_ratio', 0)
        
        # Obtener valores de los activos
        try:
            valores = [activo.get('Valuación', activo.get('valor_actual', 0)) for activo in activos_data 
                     if activo.get('Valuación', activo.get('valor_actual', 0)) > 0]
        except (KeyError, AttributeError):
            valores = []
        
        if not valores:
            return None
            
        valores_array = np.array(valores)
        
        # Cálculo de métricas básicas
        media = np.mean(valores_array)
        mediana = np.median(valores_array)
        std_dev = np.std(valores_array)
        var_95 = np.percentile(valores_array, 5)
        var_99 = np.percentile(valores_array, 1)
        
        # Cálculo de cuantiles
        q25 = np.percentile(valores_array, 25)
        q50 = np.percentile(valores_array, 50)
        q75 = np.percentile(valores_array, 75)
        q90 = np.percentile(valores_array, 90)
        q95 = np.percentile(valores_array, 95)
        
        # Cálculo de concentración
        pesos = valores_array / valor_total if valor_total > 0 else np.zeros_like(valores_array)
        concentracion = np.sum(pesos ** 2)
        
        # Cálculo de retorno y riesgo esperados
        retorno_esperado_anual = 0.08  # Tasa de retorno anual esperada
        volatilidad_anual = 0.20  # Volatilidad anual esperada
        
        retorno_esperado_pesos = valor_total * retorno_esperado_anual
        riesgo_anual_pesos = valor_total * volatilidad_anual
        
        # Simulación de Monte Carlo para calcular métricas de riesgo
        np.random.seed(42)
        num_simulaciones = 1000
        retornos_simulados = np.random.normal(retorno_esperado_anual, volatilidad_anual, num_simulaciones)
        pl_simulado = valor_total * retornos_simulados
        
        # Cálculo de probabilidades
        prob_ganancia = np.sum(pl_simulado > 0) / num_simulaciones
        prob_perdida = np.sum(pl_simulado < 0) / num_simulaciones
        prob_perdida_mayor_10 = np.sum(pl_simulado < -valor_total * 0.10) / num_simulaciones
        prob_ganancia_mayor_10 = np.sum(pl_simulado > valor_total * 0.10) / num_simulaciones
        
        # Retornar métricas en un diccionario
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
            'pl_esperado_min': np.min(pl_simulado) if len(pl_simulado) > 0 else 0,
            'pl_esperado_max': np.max(pl_simulado) if len(pl_simulado) > 0 else 0,
            'pl_esperado_medio': np.mean(pl_simulado) if len(pl_simulado) > 0 else 0,
            'pl_percentil_5': np.percentile(pl_simulado, 5) if len(pl_simulado) > 0 else 0,
            'pl_percentil_95': np.percentile(pl_simulado, 95) if len(pl_simulado) > 0 else 0,
            'probabilidades': {
                'ganancia': prob_ganancia,
                'perdida': prob_perdida,
                'perdida_mayor_10': prob_perdida_mayor_10,
                'ganancia_mayor_10': prob_ganancia_mayor_10
            },
            'fcis': {
                'total_invertido': total_fci,
                'porcentaje_portafolio': porcentaje_fci,
                'cantidad': len(fcis)
            }
        }
        
    except Exception as e:
        st.error(f"Error al calcular métricas del portafolio: {str(e)}")
        return None

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
    def __init__(self, returns, notional, prices=None):
        """
        Inicializa el objeto de salida del portafolio con métricas básicas.
        
        Args:
            returns (pd.Series): Serie de retornos diarios del portafolio
            notional (float): Valor nominal del portafolio
            prices (pd.Series, optional): Serie de precios del portafolio para análisis adicional
        """
        self.returns = returns
        self.prices = prices
        self.notional = notional
        
        # Métricas básicas
        self.mean_daily = np.mean(returns)
        self.median_daily = np.median(returns)
        self.volatility_daily = np.std(returns)
        self.skewness = stats.skew(returns, nan_policy='omit')
        self.kurtosis = stats.kurtosis(returns, nan_policy='omit')
        self.jb_stat, self.p_value = stats.jarque_bera(returns)
        self.is_normal = self.p_value > 0.05
        
        # Métricas de riesgo
        self.var_95 = np.percentile(returns, 5)
        self.cvar_95 = self._calculate_cvar(returns, 0.05)
        self.max_drawdown = self._calculate_max_drawdown()
        
        # Ratios
        self.sharpe_ratio = self._calculate_sharpe_ratio()
        self.sortino_ratio = self._calculate_sortino_ratio()
        self.calmar_ratio = self._calculate_calmar_ratio()
        
        # Anualización (asumiendo 252 días hábiles)
        self.volatility_annual = self.volatility_daily * np.sqrt(252)
        self.return_annual = (1 + self.mean_daily) ** 252 - 1
        
        # Configuración
        self.decimals = 4
        self.str_title = 'Portfolio Returns'
        
        # Placeholders
        self.weights = None
        self.dataframe_allocation = None
        self.monte_carlo_prices = None
        self.monte_carlo_returns = None
        self.simulation_days = 252  # Días hábiles para simulación
        
    def _calculate_cvar(self, returns, alpha=0.05):
        """Calcula el Conditional Value at Risk (CVaR)"""
        if len(returns) == 0:
            return np.nan
        sorted_returns = np.sort(returns)
        index = int(alpha * len(sorted_returns))
        return np.mean(sorted_returns[:index]) if index > 0 else np.min(returns)
    
    def _calculate_max_drawdown(self):
        """Calcula el máximo drawdown basado en precios o retornos"""
        if self.prices is not None and len(self.prices) > 1:
            cumulative_returns = (1 + self.returns).cumprod()
            rolling_max = cumulative_returns.cummax()
            drawdowns = (cumulative_returns - rolling_max) / rolling_max
            return drawdowns.min()
        elif len(self.returns) > 0:
            cumulative_returns = (1 + self.returns).cumprod()
            rolling_max = cumulative_returns.cummax()
            drawdowns = (cumulative_returns - rolling_max) / rolling_max
            return drawdowns.min()
        return np.nan
    
    def _calculate_sharpe_ratio(self, risk_free_rate=0.0):
        """Calcula el ratio de Sharpe anualizado"""
        if self.volatility_daily == 0:
            return 0
        return (self.mean_daily * 252 - risk_free_rate) / (self.volatility_daily * np.sqrt(252))
    
    def _calculate_sortino_ratio(self, risk_free_rate=0.0):
        """Calcula el ratio de Sortino anualizado"""
        if len(self.returns) == 0:
            return 0
        excess_returns = self.returns - risk_free_rate/252
        downside_returns = np.minimum(0, excess_returns)
        downside_deviation = np.std(downside_returns) * np.sqrt(252)
        return (np.mean(excess_returns) * 252 - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
    
    def _calculate_calmar_ratio(self, years=3):
        """Calcula el ratio de Calmar (retorno anualizado / máximo drawdown)"""
        if self.max_drawdown == 0 or np.isnan(self.max_drawdown):
            return 0
        return self.return_annual / abs(self.max_drawdown)

    def get_metrics_dict(self):
        """
        Retorna un diccionario con métricas detalladas del portafolio.
        
        Returns:
            dict: Diccionario con métricas de rendimiento, riesgo y ratios
        """
        metrics = {
            # Rendimiento
            'Retorno Promedio Diario': self.mean_daily,
            'Retorno Mediano Diario': self.median_daily,
            'Retorno Anualizado': self.return_annual,
            
            # Riesgo
            'Volatilidad Diaria': self.volatility_daily,
            'Volatilidad Anualizada': self.volatility_annual,
            'VaR 95% (1 día)': self.var_95,
            'CVaR 95% (1 día)': self.cvar_95,
            'Máximo Drawdown': self.max_drawdown if not np.isnan(self.max_drawdown) else 0,
            
            # Ratios
            'Ratio de Sharpe': self.sharpe_ratio,
            'Ratio de Sortino': self.sortino_ratio,
            'Ratio de Calmar': self.calmar_ratio,
            
            # Estadísticas de distribución
            'Asimetría': self.skewness,
            'Curtosis': self.kurtosis,
            'Estadístico JB': self.jb_stat,
            'P-Valor (Normalidad)': self.p_value,
            'Distribución Normal': 'Sí' if self.is_normal else 'No'
        }
        
        # Agregar métricas de Monte Carlo si están disponibles
        if hasattr(self, 'monte_carlo_returns') and self.monte_carlo_returns is not None and len(self.monte_carlo_returns) > 0:
            try:
                mc_returns = self.monte_carlo_returns.flatten()
                metrics.update({
                    'Retorno Esperado (MC)': np.mean(mc_returns) * 252,
                    'Volatilidad (MC)': np.std(mc_returns) * np.sqrt(252),
                    'Mejor Escenario (MC)': np.percentile(mc_returns, 90) * 252,
                    'Peor Escenario (MC)': np.percentile(mc_returns, 10) * 252,
                    'Prob. Pérdida (MC)': np.mean(mc_returns < 0) * 100
                })
            except Exception as e:
                st.warning(f"Error al calcular métricas de Monte Carlo: {str(e)}")
        
        # Formatear valores para mejor visualización
        formatted_metrics = {}
        for key, value in metrics.items():
            if isinstance(value, float):
                if 'Ratio' in key or 'Retorno' in key or 'VaR' in key or 'CVaR' in key or 'Volatilidad' in key:
                    if 'Prob.' in key:
                        formatted_metrics[key] = f"{value:.2f}%"
                    else:
                        formatted_metrics[key] = f"{value:.6f}"
                elif 'P-Valor' in key:
                    formatted_metrics[key] = f"{value:.6f}"
                elif 'Máximo Drawdown' in key:
                    formatted_metrics[key] = f"{value*100:.2f}%"
                else:
                    formatted_metrics[key] = f"{value:.6f}"
            elif isinstance(value, bool):
                formatted_metrics[key] = 'Sí' if value else 'No'
            else:
                formatted_metrics[key] = value
        
        return formatted_metrics

    def run_monte_carlo_simulation(self, n_simulations=1000, days=252, random_seed=None):
        """
        Ejecuta una simulación Monte Carlo para proyectar precios futuros del portafolio.
        
        Args:
            n_simulations (int): Número de simulaciones a ejecutar
            days (int): Número de días a proyectar
            random_seed (int, optional): Semilla para reproducibilidad
            
        Returns:
            tuple: (precios_simulados, retornos_simulados)
        """
        if random_seed is not None:
            np.random.seed(random_seed)
            
        if self.prices is not None and len(self.prices) > 1:
            # Usar precios históricos si están disponibles
            log_returns = np.log(self.prices / self.prices.shift(1)).dropna()
        else:
            # Usar retornos directos si no hay precios
            log_returns = np.log(1 + self.returns).dropna()
        
        if len(log_returns) < 2:
            raise ValueError("No hay suficientes datos para la simulación")
        
        # Calcular parámetros de la distribución
        mu = log_returns.mean()
        sigma = log_returns.std()
        last_price = self.prices.iloc[-1] if self.prices is not None else 1.0
        
        # Inicializar matriz de precios simulados
        self.simulation_days = days
        simulated_prices = np.zeros((days, n_simulations))
        
        # Generar trayectorias de precios
        for i in range(n_simulations):
            # Generar retornos aleatorios con distribución normal
            random_returns = np.random.normal(mu, sigma, days)
            # Calcular precios simulados
            price_series = [last_price]
            for r in random_returns:
                price_series.append(price_series[-1] * np.exp(r))
            simulated_prices[:, i] = price_series[1:]
        
        self.monte_carlo_prices = simulated_prices
        self.monte_carlo_returns = (simulated_prices[1:] / simulated_prices[:-1] - 1)
        
        # Calcular métricas de la simulación
        if hasattr(self, 'monte_carlo_returns') and self.monte_carlo_returns is not None and len(self.monte_carlo_returns) > 0:
            try:
                mc_returns = self.monte_carlo_returns.flatten()
                self.simulation_metrics = {
                    'retorno_anual': np.mean(mc_returns) * 252 * 100,
                    'volatilidad_anual': np.std(mc_returns) * np.sqrt(252) * 100,
                    'prob_perdida': np.mean(mc_returns < 0) * 100
                }
            except Exception as e:
                gridcolor='LightPink',
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='Gray',
                type='log' if last_price > 1000 else 'linear'  # Usar escala logarítmica para valores altos
            )
        )
        
        return fig
        
    def plot_monte_carlo_simulation(self, n_simulations=100, days=252):
        """Visualiza la simulación Monte Carlo de precios futuros"""
        if self.monte_carlo_prices is None:
            self.run_monte_carlo_simulation(n_simulations, days)
            
        fig = go.Figure()
        
        # Añadir trayectorias simuladas
        for i in range(min(n_simulations, 50)):  # Limitar a 50 trayectorias para mejor rendimiento
            fig.add_trace(go.Scatter(
                x=list(range(days)),
                y=self.monte_carlo_prices[:, i],
                mode='lines',
                line=dict(width=1, color='rgba(31, 119, 180, 0.1)'),
                showlegend=False,
                hoverinfo='skip'
            ))
            
        # Calcular percentiles
        percentiles = np.percentile(self.monte_carlo_prices, [5, 50, 95], axis=1)
        
        # Añadir percentiles
        fig.add_trace(go.Scatter(
            x=list(range(days)),
            y=percentiles[1],  # Mediana
            mode='lines',
            line=dict(color='#2ca02c', width=2),
            name='Mediana',
            hovertemplate='Día %{x}<br>Precio: %{y:.2f}<extra></extra>'
        ))
        
        # Rango de confianza 90%
        fig.add_trace(go.Scatter(
            x=list(range(days)) + list(range(days))[::-1],
            y=np.concatenate([percentiles[0], percentiles[2][::-1]]),  # 5% a 95%
            fill='toself',
            fillcolor='rgba(44, 160, 44, 0.2)',
            line=dict(width=0),
            name='Rango 90%',
            hoverinfo='skip'
        ))
        
        # Actualizar diseño
        fig.update_layout(
            title=dict(
                text=f'Simulación Monte Carlo ({n_simulations} simulaciones)',
                x=0.5,
                xanchor='center'
            ),
            xaxis_title='Días hábiles',
            yaxis_title='Valor del Portafolio',
            showlegend=True,
            template='plotly_white',
            height=600,
            hovermode='x unified',
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
        
    def plot_return_distribution(self, title=None, show_metrics=True):
        """
        Visualiza la distribución de retornos con histograma, KDE y estadísticas.
        
        Args:
            title (str, optional): Título del gráfico
            show_metrics (bool): Si se muestran las métricas en el gráfico
            
        Returns:
            plotly.graph_objs.Figure: Figura con la distribución de retornos
        """
        if self.returns is None or len(self.returns) == 0:
            st.warning("No hay datos de retornos para mostrar")
            return None
            
        # Crear figura con subplots
        fig = make_subplots(rows=2, cols=1, 
                          row_heights=[0.7, 0.3],
                          vertical_spacing=0.02,
                          shared_xaxes=True)
        
        # Histograma
        hist_data = np.clip(self.returns, 
                          np.percentile(self.returns, 0.1), 
                          np.percentile(self.returns, 99.9))
        
        fig.add_trace(
            go.Histogram(
                x=hist_data,
                nbinsx=100,
                name='Frecuencia',
                marker_color='#1f77b4',
                opacity=0.7,
                hovertemplate='Retorno: %{x:.4f}<br>Frecuencia: %{y}' + '<extra></extra>',
                hoverlabel=dict(namelength=0)
            ),
            row=1, col=1
        )
        
        # Línea KDE
        x = np.linspace(min(hist_data), max(hist_data), 500)
        kde = stats.gaussian_kde(hist_data)
        kde_curve = kde(x)
        
        fig.add_trace(
            go.Scatter(
                x=x,
                y=kde_curve * len(hist_data) * (max(hist_data) - min(hist_data)) / 100,
                mode='lines',
                name='KDE',
                line=dict(color='#ff7f0e', width=2),
                hovertemplate='Retorno: %{x:.4f}<br>Densidad: %{y:.4f}' + '<extra>KDE</extra>'
            ),
            row=1, col=1
        )
        
        # Línea distribución normal
        normal_pdf = stats.norm.pdf(x, loc=np.mean(hist_data), scale=np.std(hist_data))
        fig.add_trace(
            go.Scatter(
                x=x,
                y=normal_pdf * len(hist_data) * (max(hist_data) - min(hist_data)) / 100,
                mode='lines',
                name='Normal',
                line=dict(color='#2ca02c', width=2, dash='dash'),
                hovertemplate='Retorno: %{x:.4f}<br>Densidad: %{y:.4f}' + '<extra>Normal</extra>'
            ),
            row=1, col=1
        )
        
        # Box plot
        fig.add_trace(
            go.Box(
                x=hist_data,
                name='',
                boxpoints=False,
                marker_color='#1f77b4',
                line_width=1,
                showlegend=False,
                hoverinfo='x'
            ),
            row=2, col=1
        )
        
        # Líneas de referencia importantes
        mean = np.mean(self.returns)
        median = np.median(self.returns)
        std = np.std(self.returns)
        
        # Añadir líneas verticales
        for value, name, color, dash in [
            (mean, 'Media', 'red', 'solid'),
            (median, 'Mediana', 'green', 'solid'),
            (self.var_95, 'VaR 95%', 'purple', 'dash'),
            (self.cvar_95, 'CVaR 95%', 'orange', 'dot')
        ]:
            fig.add_vline(
                x=value,
                line=dict(color=color, width=1.5, dash=dash),
                opacity=0.8,
                annotation_text=f"{name}: {value:.4f}",
                annotation_position="top right",
                row=1, col=1
            )
        
        # Actualizar diseño
        fig.update_layout(
            title=dict(
                text=title or 'Distribución de Retornos',
                x=0.5,
                xanchor='center',
                font=dict(size=18)
            ),
            showlegend=True,
            template='plotly_white',
            height=700,
            hovermode='x',
            margin=dict(l=50, r=50, t=80, b=50),
            plot_bgcolor='rgba(0,0,0,0.02)',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Actualizar ejes
        fig.update_xaxes(
            title_text="Retornos",
            row=2, col=1,
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(211, 211, 211, 0.5)',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='LightGray',
            showspikes=True,
            spikethickness=1,
            spikedash='dot',
            spikecolor='#999999',
            spikemode='across',
            spikesnap='cursor',
            fixedrange=False
        )
        
        fig.update_yaxes(
            title_text="Frecuencia",
            row=1, col=1,
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(211, 211, 211, 0.5)',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='LightGray',
            fixedrange=False
        )
        
        # Ocultar el eje y del box plot
        fig.update_yaxes(
            showticklabels=False,
            row=2, col=1,
            fixedrange=False
        )
        
        # Añadir anotaciones con métricas si se solicita
        if show_metrics:
            metrics_text = (
                f"<b>Estadísticas Descriptivas:</b><br>"
                f"Media: {mean:.6f}<br>"
                f"Mediana: {median:.6f}<br>"
                f"Desv. Estándar: {std:.6f}<br>"
                f"Asimetría: {self.skewness:.4f}<br>"
                f"Curtosis: {self.kurtosis:.4f}<br>"
                f"VaR 95%: {self.var_95:.6f}<br>"
                f"CVaR 95%: {self.cvar_95:.6f}"
            )
            
            fig.add_annotation(
                x=0.02,
                y=0.98,
                xref='paper',
                yref='paper',
                text=metrics_text,
                showarrow=False,
                align='left',
                bordercolor='#c7c7c7',
                borderwidth=1,
                borderpad=4,
                bgcolor='white',
                opacity=0.8,
                xanchor='left',
                yanchor='top'
            )
        
        return fig
        
    def plot_drawdowns(self):
        """Visualiza los drawdowns del portafolio"""
        if self.prices is None or len(self.prices) < 2:
            return None
            
        # Calcular drawdowns
        cumulative_returns = (1 + self.returns).cumprod()
        rolling_max = cumulative_returns.cummax()
        drawdowns = (cumulative_returns - rolling_max) / rolling_max
        
        fig = go.Figure()
        
        # Área de drawdown
        fig.add_trace(go.Scatter(
            x=drawdowns.index,
            y=drawdowns * 100,  # Convertir a porcentaje
            fill='tozeroy',
            mode='none',
            name='Drawdown',
            fillcolor='rgba(255, 127, 14, 0.3)',
            line=dict(color='#ff7f0e', width=1)
        ))
        
        # Línea de drawdown
        fig.add_trace(go.Scatter(
            x=drawdowns.index,
            y=drawdowns * 100,
            mode='lines',
            name='Drawdown',
            line=dict(color='#ff7f0e', width=1.5),
            hovertemplate='%{y:.2f}%<extra></extra>'
        ))
        
        # Línea en y=0
        fig.add_hline(
            y=0,
            line_dash='dash',
            line_color='gray',
            opacity=0.7
        )
        
        # Calcular métricas
        max_drawdown = drawdowns.min() * 100
        avg_drawdown = drawdowns.mean() * 100
        
        # Añadir anotación con métricas
        metrics_text = (
            f"<b>Métricas de Drawdown:</b><br>"
            f"Máximo Drawdown: {max_drawdown:.2f}%<br>"
            f"Drawdown Promedio: {avg_drawdown:.2f}%"
        )
        
        fig.add_annotation(
            x=0.02,
            y=0.98,
            xref='paper',
            yref='paper',
            text=metrics_text,
            showarrow=False,
            align='left',
            bordercolor='#c7c7c7',
            borderwidth=1,
            borderpad=4,
            bgcolor='white',
            opacity=0.8
        )
        
        # Actualizar diseño
        fig.update_layout(
            title='Evolución de Drawdowns',
            xaxis_title='Fecha',
            yaxis_title='Drawdown (%)',
            showlegend=False,
            template='plotly_white',
            height=400,
            hovermode='x'
        )
        
        return fig

def portfolio_variance(x, mtx_var_covar):
    """Calcula la varianza del portafolio"""
    variance = np.matmul(np.transpose(x), np.matmul(mtx_var_covar, x))
    return variance

def compute_efficient_frontier(rics, notional, target_return, include_min_variance, data):
    """Computa la frontera eficiente y portafolios especiales"""
    # special portfolios    
    label1 = 'min-variance-l1'
    label2 = 'min-variance-l2'
    label3 = 'equi-weight'
    label4 = 'long-only'
    label5 = 'markowitz-none'
    label6 = 'markowitz-target'
    
    # compute covariance matrix
    port_mgr = manager(rics, notional, data)
    port_mgr.compute_covariance()
    
    # compute vectors of returns and volatilities for Markowitz portfolios
    min_returns = np.min(port_mgr.mean_returns)
    max_returns = np.max(port_mgr.mean_returns)
    returns = min_returns + np.linspace(0.05, 0.95, 50) * (max_returns - min_returns)
    volatilities = []
    valid_returns = []
    
    for ret in returns:
        try:
            port = port_mgr.compute_portfolio('markowitz', ret)
            volatilities.append(port.volatility_annual)
            valid_returns.append(ret)
        except:
            continue
    
    # compute special portfolios
    portfolios = {}
    try:
        portfolios[label1] = port_mgr.compute_portfolio(label1)
    except:
        portfolios[label1] = None
        
    try:
        portfolios[label2] = port_mgr.compute_portfolio(label2)
    except:
        portfolios[label2] = None
        
    portfolios[label3] = port_mgr.compute_portfolio(label3)
    portfolios[label4] = port_mgr.compute_portfolio(label4)
    portfolios[label5] = port_mgr.compute_portfolio('markowitz')
    
    try:
        portfolios[label6] = port_mgr.compute_portfolio('markowitz', target_return)
    except:
        portfolios[label6] = None
    
    return portfolios, valid_returns, volatilities

class PortfolioManager:
    def __init__(self, symbols, token, fecha_desde, fecha_hasta):
        self.symbols = symbols
        self.token = token
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.data_loaded = False
        self.returns = None
        self.prices = None
        self.notional = 100000  # Valor nominal por defecto
        self.manager = None
    
    def load_data(self):
        try:
            mean_returns, cov_matrix, df_precios = get_historical_data_for_optimization(
                self.token, self.symbols, self.fecha_desde, self.fecha_hasta
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
            return False
    
    def compute_portfolio(self, strategy='markowitz', target_return=None):
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
            return None

    def compute_efficient_frontier(self, target_return=0.08, include_min_variance=True):
        """Computa la frontera eficiente"""
        if not self.data_loaded or not self.manager:
            return None, None, None
        
        try:
            portfolios, returns, volatilities = compute_efficient_frontier(
                self.symbols, self.notional, target_return, include_min_variance, 
                self.prices.to_dict('series')
            )
            return portfolios, returns, volatilities
        except Exception as e:
            return None, None, None

# --- Funciones de Visualización ---
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
            
            valuacion = 0
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
                campos_precio = [
                    'precioPromedio',
                    'precioCompra',
                    'precioActual',
                    'precio',
                    'precioUnitario',
                    'ultimoPrecio',
                    'cotizacion'
                ]
                
                precio_unitario = 0
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
                        # Ajustar la valuación para bonos (precio por 100 nominal)
                        if tipo == 'TitulosPublicos':
                            valuacion = (cantidad_num * precio_unitario) / 100.0
                        else:
                            valuacion = cantidad_num * precio_unitario
                    except (ValueError, TypeError) as e:
                        st.warning(f"Error calculando valuación para {simbolo}: {str(e)}")
            
            datos_activos.append({
                'Símbolo': simbolo,
                'Descripción': descripcion,
                'Tipo': tipo,
                'Cantidad': cantidad,
                'Valuación': valuacion,
            })
            
            valor_total += valuacion
        except Exception as e:
            continue
    
    if datos_activos:
        df_activos = pd.DataFrame(datos_activos)
        metricas = calcular_metricas_portafolio(datos_activos, valor_total)
        
        # Información General
        cols = st.columns(4)
        cols[0].metric("Total de Activos", len(datos_activos))
        cols[1].metric("Símbolos Únicos", df_activos['Símbolo'].nunique())
        cols[2].metric("Tipos de Activos", df_activos['Tipo'].nunique())
        cols[3].metric("Valor Total", f"${valor_total:,.2f}")
        
        if metricas:
            # Métricas de Riesgo
            st.subheader("⚖️ Análisis de Riesgo")
            cols = st.columns(3)
            
            cols[0].metric("Concentración", 
                          f"{metricas['concentracion']:.3f}",
                          help="Índice de Herfindahl: 0=diversificado, 1=concentrado")
            
            cols[1].metric("Volatilidad", 
                          f"${metricas['std_dev_activo']:,.0f}",
                          help="Desviación estándar de los valores de activos")
            
            concentracion_status = "🟢 Baja" if metricas['concentracion'] < 0.25 else "🟡 Media" if metricas['concentracion'] < 0.5 else "🔴 Alta"
            cols[2].metric("Nivel Concentración", concentracion_status)
            
            # Proyecciones
            st.subheader("📈 Proyecciones de Rendimiento")
            cols = st.columns(3)
            cols[0].metric("Retorno Esperado", f"${metricas['retorno_esperado_anual']:,.0f}")
            cols[1].metric("Escenario Optimista", f"${metricas['pl_percentil_95']:,.0f}")
            cols[2].metric("Escenario Pesimista", f"${metricas['pl_percentil_5']:,.0f}")
            
            # Probabilidades
            st.subheader("🎯 Probabilidades")
            cols = st.columns(4)
            probs = metricas['probabilidades']
            cols[0].metric("Ganancia", f"{probs['ganancia']*100:.1f}%")
            cols[1].metric("Pérdida", f"{probs['perdida']*100:.1f}%")
            cols[2].metric("Ganancia >10%", f"{probs['ganancia_mayor_10']*100:.1f}%")
            cols[3].metric("Pérdida >10%", f"{probs['perdida_mayor_10']*100:.1f}%")
        
        # Gráficos
        st.subheader("📊 Distribución de Activos")
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Tipo' in df_activos.columns and df_activos['Valuación'].sum() > 0:
                tipo_stats = df_activos.groupby('Tipo')['Valuación'].sum().reset_index()
                fig_pie = go.Figure(data=[go.Pie(
                    labels=tipo_stats['Tipo'],
                    values=tipo_stats['Valuación'],
                    textinfo='label+percent',
                    hole=0.4,
                    marker=dict(colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
                )])
                fig_pie.update_layout(
                    title="Distribución por Tipo",
                    height=400
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            if len(datos_activos) > 1:
                valores_activos = [a['Valuación'] for a in datos_activos if a['Valuación'] > 0]
                if valores_activos:
                    fig_hist = go.Figure(data=[go.Histogram(
                        x=valores_activos,
                        nbinsx=min(20, len(valores_activos)),
                        marker_color='#0d6efd'
                    )])
                    fig_hist.update_layout(
                        title="Distribución de Valores",
                        xaxis_title="Valor ($)",
                        yaxis_title="Frecuencia",
                        height=400
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
        
        # Tabla de activos
        st.subheader("📋 Detalle de Activos")
        df_display = df_activos.copy()
        df_display['Valuación'] = df_display['Valuación'].apply(
            lambda x: f"${x:,.2f}" if x > 0 else "N/A"
        )
        df_display['Peso (%)'] = (df_activos['Valuación'] / valor_total * 100).round(2)
        df_display = df_display.sort_values('Peso (%)', ascending=False)
        
        st.dataframe(df_display, use_container_width=True, height=400)
        
        # Recomendaciones
        st.subheader("💡 Recomendaciones")
        if metricas:
            if metricas['concentracion'] > 0.5:
                st.warning("""
                **⚠️ Portafolio Altamente Concentrado**  
                Considere diversificar sus inversiones para reducir el riesgo.
                """)
            elif metricas['concentracion'] > 0.25:
                st.info("""
                **ℹ️ Concentración Moderada**  
                Podría mejorar su diversificación para optimizar el riesgo.
                """)
            else:
                st.success("""
                **✅ Buena Diversificación**  
                Su portafolio está bien diversificado.
                """)
            
            ratio_riesgo_retorno = metricas['retorno_esperado_anual'] / metricas['riesgo_anual'] if metricas['riesgo_anual'] > 0 else 0
            if ratio_riesgo_retorno > 0.5:
                st.success("""
                **✅ Buen Balance Riesgo-Retorno**  
                La relación entre riesgo y retorno es favorable.
                """)
            else:
                st.warning("""
                **⚠️ Revisar Balance Riesgo-Retorno**  
                El riesgo podría ser alto en relación al retorno esperado.
                """)
    else:
        st.warning("No se encontraron activos en el portafolio")

def mostrar_estado_cuenta(estado_cuenta):
    st.markdown("### 💰 Estado de Cuenta")
    
    if not estado_cuenta:
        st.warning("No hay datos de estado de cuenta disponibles")
        return
    
    total_en_pesos = estado_cuenta.get('totalEnPesos', 0)
    cuentas = estado_cuenta.get('cuentas', [])
    
    cols = st.columns(3)
    cols[0].metric("Total en Pesos", f"AR$ {total_en_pesos:,.2f}")
    cols[1].metric("Número de Cuentas", len(cuentas))
    
    if cuentas:
        st.subheader("📊 Detalle de Cuentas")
        
        datos_cuentas = []
        for cuenta in cuentas:
            datos_cuentas.append({
                'Número': cuenta.get('numero', 'N/A'),
                'Tipo': cuenta.get('tipo', 'N/A').replace('_', ' ').title(),
                'Moneda': cuenta.get('moneda', 'N/A').replace('_', ' ').title(),
                'Disponible': f"${cuenta.get('disponible', 0):,.2f}",
                'Saldo': f"${cuenta.get('saldo', 0):,.2f}",
                'Total': f"${cuenta.get('total', 0):,.2f}",
            })
        
        df_cuentas = pd.DataFrame(datos_cuentas)
        st.dataframe(df_cuentas, use_container_width=True, height=300)

def mostrar_cotizaciones_mercado(token_acceso):
    st.markdown("### 💱 Cotizaciones y Mercado")
    
    with st.expander("💰 Cotización MEP", expanded=True):
        with st.form("mep_form"):
            col1, col2, col3 = st.columns(3)
            simbolo_mep = col1.text_input("Símbolo", value="AL30", help="Ej: AL30, GD30, etc.")
            id_plazo_compra = col2.number_input("ID Plazo Compra", value=1, min_value=1)
            id_plazo_venta = col3.number_input("ID Plazo Venta", value=1, min_value=1)
            
            if st.form_submit_button("🔍 Consultar MEP"):
                if simbolo_mep:
                    with st.spinner("Consultando cotización MEP..."):
                        cotizacion_mep = obtener_cotizacion_mep(
                            token_acceso, simbolo_mep, id_plazo_compra, id_plazo_venta
                        )
                    
                    if cotizacion_mep:
                        st.success("✅ Cotización MEP obtenida")
                        precio_mep = cotizacion_mep.get('precio', 'N/A')
                        st.metric("Precio MEP", f"${precio_mep}" if precio_mep != 'N/A' else 'N/A')
                    else:
                        st.error("❌ No se pudo obtener la cotización MEP")
    
    with st.expander("🏦 Tasas de Caución", expanded=True):
        if st.button("🔄 Actualizar Tasas"):
            with st.spinner("Consultando tasas de caución..."):
                tasas_caucion = obtener_tasas_caucion(token_acceso)
            
            if tasas_caucion is not None and not tasas_caucion.empty:
                df_tasas = pd.DataFrame(tasas_caucion)
                columnas_relevantes = ['simbolo', 'tasa', 'bid', 'offer', 'ultimo']
                columnas_disponibles = [col for col in columnas_relevantes if col in df_tasas.columns]
                
                if columnas_disponibles:
                    st.dataframe(df_tasas[columnas_disponibles].head(10))
                else:
                    st.dataframe(df_tasas.head(10))
            else:
                st.error("❌ No se pudieron obtener las tasas de caución")

def mostrar_optimizacion_portafolio(token_acceso, id_cliente):
    st.markdown("### 🔄 Optimización de Portafolio")
    
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
        simbolo = titulo.get('simbolo')
        if simbolo:
            simbolos.append(simbolo)
    
    if not simbolos:
        st.warning("No se encontraron símbolos válidos")
        return
    
    fecha_desde = st.session_state.fecha_desde
    fecha_hasta = st.session_state.fecha_hasta
    
    st.info(f"Analizando {len(simbolos)} activos desde {fecha_desde} hasta {fecha_hasta}")
    
    # Configuración de optimización extendida
    col1, col2, col3 = st.columns(3)
    
    with col1:
        estrategia = st.selectbox(
            "Estrategia de Optimización:",
            options=['markowitz', 'equi-weight', 'min-variance-l1', 'min-variance-l2', 'long-only'],
            format_func=lambda x: {
                'markowitz': 'Optimización de Markowitz',
                'equi-weight': 'Pesos Iguales',
                'min-variance-l1': 'Mínima Varianza L1',
                'min-variance-l2': 'Mínima Varianza L2',
                'long-only': 'Solo Posiciones Largas'
            }[x]
        )
    
    with col2:
        target_return = st.number_input(
            "Retorno Objetivo (anual):",
            min_value=0.0, max_value=1.0, value=0.08, step=0.01,
            help="Solo aplica para estrategia Markowitz"
        )
    
    with col3:
        show_frontier = st.checkbox("Mostrar Frontera Eficiente", value=True)
    
    col1, col2 = st.columns(2)
    with col1:
        ejecutar_optimizacion = st.button("🚀 Ejecutar Optimización", type="primary")
    with col2:
        ejecutar_frontier = st.button("📈 Calcular Frontera Eficiente")
    
    if ejecutar_optimizacion:
        with st.spinner("Ejecutando optimización..."):
            try:
                # Crear manager de portafolio
                manager_inst = PortfolioManager(simbolos, token_acceso, fecha_desde, fecha_hasta)
                
                # Cargar datos
                if manager_inst.load_data():
                    # Computar optimización
                    use_target = target_return if estrategia == 'markowitz' else None
                    portfolio_result = manager_inst.compute_portfolio(strategy=estrategia, target_return=use_target)
                    
                    if portfolio_result:
                        st.success("✅ Optimización completada")
                        
                        # Mostrar resultados extendidos
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 📊 Pesos Optimizados")
                            if portfolio_result.dataframe_allocation is not None:
                                weights_df = portfolio_result.dataframe_allocation.copy()
                                weights_df['Peso (%)'] = weights_df['weights'] * 100
                                weights_df = weights_df.sort_values('Peso (%)', ascending=False)
                                st.dataframe(weights_df[['rics', 'Peso (%)']], use_container_width=True)
                        
                        with col2:
                            st.markdown("#### 📈 Métricas del Portafolio")
                            metricas = portfolio_result.get_metrics_dict()
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("Retorno Anual", f"{metricas['Annual Return']:.2%}")
                                st.metric("Volatilidad Anual", f"{metricas['Annual Volatility']:.2%}")
                                st.metric("Ratio de Sharpe", f"{metricas['Sharpe Ratio']:.4f}")
                                st.metric("VaR 95%", f"{metricas['VaR 95%']:.4f}")
                            with col_b:
                                st.metric("Skewness", f"{metricas['Skewness']:.4f}")
                                st.metric("Kurtosis", f"{metricas['Kurtosis']:.4f}")
                                st.metric("JB Statistic", f"{metricas['JB Statistic']:.4f}")
                                normalidad = "✅ Normal" if metricas['Is Normal'] else "❌ No Normal"
                                st.metric("Normalidad", normalidad)
                        
                        # Gráfico de distribución de retornos
                        if portfolio_result.returns is not None:
                            st.markdown("#### 📊 Distribución de Retornos del Portafolio Optimizado")
                            fig = portfolio_result.plot_histogram_streamlit()
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Gráfico de pesos
                        if portfolio_result.weights is not None:
                            st.markdown("#### 🥧 Distribución de Pesos")
                            fig_pie = go.Figure(data=[go.Pie(
                                labels=portfolio_result.dataframe_allocation['rics'],
                                values=portfolio_result.weights,
                                textinfo='label+percent',
                                marker_color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
                            )])
                            fig_pie.update_layout(
                                title="Distribución Optimizada de Activos",
                                template='plotly_white'
                            )
                            st.plotly_chart(fig_pie, use_container_width=True)
                        
                    else:
                        st.error("❌ Error en la optimización")
                else:
                    st.error("❌ No se pudieron cargar los datos históricos")
                    
            except Exception as e:
                st.error(f"❌ Error durante la optimización: {str(e)}")
    
    if ejecutar_frontier and show_frontier:
        with st.spinner("Calculando frontera eficiente..."):
            try:
                manager_inst = PortfolioManager(simbolos, token_acceso, fecha_desde, fecha_hasta)
                
                if manager_inst.load_data():
                    portfolios, returns, volatilities = manager_inst.compute_efficient_frontier(
                        target_return=target_return, include_min_variance=True
                    )
                    
                    if portfolios and returns and volatilities:
                        st.success("✅ Frontera eficiente calculada")
                        
                        # Crear gráfico de frontera eficiente
                        fig = go.Figure()
                        
                        # Línea de frontera eficiente
                        fig.add_trace(go.Scatter(
                            x=volatilities, y=returns,
                            mode='lines+markers',
                            name='Frontera Eficiente',
                            line=dict(color='#0d6efd', width=3),
                            marker=dict(size=6)
                        ))
                        
                        # Portafolios especiales
                        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
                        labels = ['Min Var L1', 'Min Var L2', 'Pesos Iguales', 'Solo Largos', 'Markowitz', 'Markowitz Target']
                        
                        for i, (label, portfolio) in enumerate(portfolios.items()):
                            if portfolio is not None:
                                fig.add_trace(go.Scatter(
                                    x=[portfolio.volatility_annual], 
                                    y=[portfolio.return_annual],
                                    mode='markers',
                                    name=labels[i] if i < len(labels) else label,
                                    marker=dict(size=12, color=colors[i % len(colors)])
                                ))
                        
                        fig.update_layout(
                            title='Frontera Eficiente del Portafolio',
                            xaxis_title='Volatilidad Anual',
                            yaxis_title='Retorno Anual',
                            showlegend=True,
                            template='plotly_white',
                            height=500
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Tabla comparativa de portafolios
                        st.markdown("#### 📊 Comparación de Estrategias")
                        comparison_data = []
                        for label, portfolio in portfolios.items():
                            if portfolio is not None:
                                comparison_data.append({
                                    'Estrategia': label,
                                    'Retorno Anual': f"{portfolio.return_annual:.2%}",
                                    'Volatilidad Anual': f"{portfolio.volatility_annual:.2%}",
                                    'Sharpe Ratio': f"{portfolio.sharpe_ratio:.4f}",
                                    'VaR 95%': f"{portfolio.var_95:.4f}",
                                    'Skewness': f"{portfolio.skewness:.4f}",
                                    'Kurtosis': f"{portfolio.kurtosis:.4f}"
                                })
                        
                        if comparison_data:
                            df_comparison = pd.DataFrame(comparison_data)
                            st.dataframe(df_comparison, use_container_width=True)
                    
                    else:
                        st.error("❌ No se pudo calcular la frontera eficiente")
                else:
                    st.error("❌ No se pudieron cargar los datos históricos")
                    
            except Exception as e:
                st.error(f"❌ Error calculando frontera eficiente: {str(e)}")
    
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
    cliente = st.session_state.cliente_seleccionado
    token_acceso = st.session_state.token_acceso

    if not cliente:
        st.error("No hay cliente seleccionado")
        return

    id_cliente = cliente.get('numeroCliente', cliente.get('id'))
    nombre_cliente = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))

    st.title(f"📊 Análisis de Portafolio - {nombre_cliente}")
    
    # Crear tabs con iconos
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Resumen Portafolio", 
        "💰 Estado de Cuenta", 
        "📊 Análisis Técnico",
        "💱 Cotizaciones",
        "🔄 Optimización"
    ])

    with tab1:
        portafolio = obtener_portafolio(token_acceso, id_cliente)
        if portafolio:
            mostrar_resumen_portafolio(portafolio)
        else:
            st.warning("No se pudo obtener el portafolio del cliente")
    
    with tab2:
        estado_cuenta = obtener_estado_cuenta(token_acceso, id_cliente)
        if estado_cuenta:
            mostrar_estado_cuenta(estado_cuenta)
        else:
            st.warning("No se pudo obtener el estado de cuenta")
    
    with tab3:
        mostrar_analisis_tecnico(token_acceso, id_cliente)
    
    with tab4:
        mostrar_cotizaciones_mercado(token_acceso)
    
    with tab5:
        mostrar_optimizacion_portafolio(token_acceso, id_cliente)

def main():
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
                
                # Crear lista de opciones con nombre completo desde el perfil si está disponible
                opciones_clientes = []
                for c in clientes:
                    cliente_id = c.get('numeroCliente', c.get('id'))
                    if 'perfil' in c and c['perfil']:
                        nombre = f"{c['perfil'].get('apellido', '')}, {c['perfil'].get('nombre', '')}".strip()
                        if not nombre:
                            nombre = c.get('apellidoYNombre', c.get('nombre', f'Cliente {cliente_id}'))
                    else:
                        nombre = c.get('apellidoYNombre', c.get('nombre', f'Cliente {cliente_id}'))
                    opciones_clientes.append((cliente_id, nombre))
                
                # Ordenar por nombre
                opciones_clientes.sort(key=lambda x: x[1])
                cliente_ids = [x[0] for x in opciones_clientes]
                cliente_nombres = [x[1] for x in opciones_clientes]
                
                cliente_seleccionado = st.selectbox(
                    "Seleccione un cliente:",
                    options=cliente_ids,
                    format_func=lambda x: cliente_nombres[cliente_ids.index(x)] if x in cliente_ids else "Cliente",
                    label_visibility="collapsed"
                )
                
                # Obtener el cliente seleccionado
                cliente_actual = next(
                    (c for c in clientes if str(c.get('numeroCliente', c.get('id'))) == str(cliente_seleccionado)),
                    None
                )
                
                # Mostrar información del perfil si está disponible
                if cliente_actual and 'perfil' in cliente_actual and cliente_actual['perfil']:
                    perfil = cliente_actual['perfil']
                    with st.expander("👤 Información del Perfil", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Nombre", f"{perfil.get('nombre', '')} {perfil.get('apellido', '')}")
                            st.metric("DNI", perfil.get('dni', 'No disponible'))
                            st.metric("CUIL/CUIT", perfil.get('cuitCuil', 'No disponible'))
                            
                        with col2:
                            st.metric("Email", perfil.get('email', 'No disponible'))
                            estado_cuenta = "🟢 Activa" if perfil.get('cuentaAbierta', False) else "🔴 Inactiva"
                            st.metric("Estado de la Cuenta", estado_cuenta)
                            
                            # Mostrar perfil de inversor con color según el riesgo
                            perfil_inversor = perfil.get('perfilInversor', 'No definido')
                            color = "#28a745"  # Verde por defecto
                            if "conservador" in perfil_inversor.lower():
                                color = "#28a745"  # Verde
                            elif "moderado" in perfil_inversor.lower():
                                color = "#ffc107"  # Amarillo
                            elif "agresivo" in perfil_inversor.lower():
                                color = "#dc3545"  # Rojo
                                
                            st.markdown(f"""
                                <div style="margin-top: 10px; margin-bottom: 10px;">
                                    <div style="font-size: 0.8em; color: #666; margin-bottom: 2px;">Perfil de Inversor</div>
                                    <div style="background-color: {color}20; border-left: 4px solid {color}; padding: 8px 12px; border-radius: 4px;">
                                        <strong style="color: {color};">{perfil_inversor}</strong>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        # Mostrar alertas si hay actualizaciones pendientes
                        actualizaciones_pendientes = []
                        if perfil.get('actualizarDDJJ', False):
                            actualizaciones_pendientes.append("Declaración Jurada")
                        if perfil.get('actualizarTestInversor', False):
                            actualizaciones_pendientes.append("Test de Inversor")
                        if perfil.get('actualizarTyC', False):
                            actualizaciones_pendientes.append("Términos y Condiciones")
                        if perfil.get('actualizarTyCApp', False):
                            actualizaciones_pendientes.append("Términos y Condiciones de la App")
                            
                        if actualizaciones_pendientes:
                            st.warning(f"⚠️ **Actualizaciones pendientes:** {', '.join(actualizaciones_pendientes)}")
                        
                        # Mostrar si está en período de arrepentimiento
                        if perfil.get('esBajaArrepentimiento', False):
                            st.error("""
                            ⚠️ **Período de Arrepentimiento Activo**  
                            El cliente se encuentra dentro del período de arrepentimiento.
                            """)
                
                st.session_state.cliente_seleccionado = cliente_actual
                
                if st.button("🔄 Actualizar lista de clientes", use_container_width=True):
                    with st.spinner("Actualizando..."):
                        nuevos_clientes = obtener_lista_clientes(st.session_state.token_acceso)
                        if nuevos_clientes:
                            # Preservar los perfiles existentes si es posible
                            clientes_actuales = {c.get('numeroCliente', c.get('id')): c for c in st.session_state.clientes}
                            
                            for cliente in nuevos_clientes:
                                cliente_id = cliente.get('numeroCliente', cliente.get('id'))
                                if cliente_id in clientes_actuales and 'perfil' in clientes_actuales[cliente_id]:
                                    cliente['perfil'] = clientes_actuales[cliente_id]['perfil']
                            
                            st.session_state.clientes = nuevos_clientes
                            st.success("✅ Lista de clientes actualizada")
                        else:
                            st.warning("No se pudieron cargar los clientes")
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
