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
import time
import matplotlib.pyplot as plt
import seaborn as sns

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

class SerieHistoricaIOL:
    """
    Clase universal para obtener series históricas de todos los mercados y activos de IOL
    """
    
    def __init__(self, bearer_token, refresh_token=None):
        self.bearer_token = bearer_token
        self.refresh_token = refresh_token
        self.base_url = "https://api.invertironline.com/api/v2"
        self.headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }
        
        # Configuración de mercados y endpoints
        self.mercados_config = {
            'BCBA': {
                'endpoint': 'BCBA/Titulos',
                'tipos_activos': ['Acciones', 'Bonos', 'TitulosPublicos', 'Cedears']
            },
            'NYSE': {
                'endpoint': 'NYSE/Titulos', 
                'tipos_activos': ['Acciones', 'ADRs']
            },
            'NASDAQ': {
                'endpoint': 'NASDAQ/Titulos',
                'tipos_activos': ['Acciones', 'ADRs']
            },
            'ROFEX': {
                'endpoint': 'ROFEX/Titulos',
                'tipos_activos': ['Futuros', 'Opciones']
            },
            'FCI': {
                'endpoint': 'Titulos/FCI',
                'tipos_activos': ['FCI']
            },
            'Bonos': {
                'endpoint': 'Bonos/Titulos',
                'tipos_activos': ['Bonos', 'TitulosPublicos']
            },
            'Cedears': {
                'endpoint': 'Cedears/Titulos',
                'tipos_activos': ['Cedears']
            },
            'ADRs': {
                'endpoint': 'ADRs/Titulos',
                'tipos_activos': ['ADRs']
            },
            'TitulosPublicos': {
                'endpoint': 'TitulosPublicos',
                'tipos_activos': ['TitulosPublicos', 'Bonos']
            },
            'Opciones': {
                'endpoint': 'Opciones',
                'tipos_activos': ['Opciones']
            },
            'Cauciones': {
                'endpoint': 'Cotizaciones/Cauciones',
                'tipos_activos': ['Caucion']
            }
        }
        
        # Endpoints especiales
        self.endpoints_especiales = {
            'MEP': 'Cotizaciones/MEP',
            'Cauciones': 'Cotizaciones/Cauciones/Todas/Argentina',
            'Instrumentos': 'Instrumentos'
        }
    
    def refrescar_token(self):
        """Refresca el token de acceso"""
        if not self.refresh_token:
            return False
            
        try:
            token_url = 'https://api.invertironline.com/token'
            payload = {
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            response = requests.post(token_url, data=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                tokens = response.json()
                self.bearer_token = tokens['access_token']
                self.refresh_token = tokens['refresh_token']
                self.headers['Authorization'] = f'Bearer {self.bearer_token}'
                return True
            else:
                st.error(f'Error refrescando token: {response.status_code}')
                return False
        except Exception as e:
            st.error(f'Error al refrescar token: {str(e)}')
            return False
    
    def _hacer_peticion(self, url, max_reintentos=2):
        """Hace una petición HTTP con manejo de errores y reintentos"""
        for intento in range(max_reintentos + 1):
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401 and intento == 0:
                    # Intentar refrescar token
                    if self.refrescar_token():
                        continue
                    else:
                        return None
                else:
                    if intento == max_reintentos:
                        st.warning(f"Error {response.status_code} en URL: {url}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                if intento == max_reintentos:
                    st.warning(f"Error de conexión: {str(e)}")
                time.sleep(1)  # Pausa entre reintentos
                
        return None
    
    def detectar_mercado_simbolo(self, simbolo):
        """Detecta automáticamente el mercado más probable para un símbolo"""
        simbolo_upper = simbolo.upper()
        
        # Mapeo de prefijos/sufijos a mercados
        prefijos_especiales = {
            'AL': ['TitulosPublicos', 'Bonos', 'BCBA'],
            'GD': ['TitulosPublicos', 'Bonos', 'BCBA'],
            'AY': ['TitulosPublicos', 'Bonos', 'BCBA'],
            'D': ['Cedears', 'BCBA'],  # Cedears normalmente terminan con D
            'C': ['TitulosPublicos', 'Bonos']
        }
        
        # Tickers internacionales conocidos (NASDAQ/NYSE)
        tickers_internacionales = ['NVDA', 'GOOGL', 'TSLA', 'AAPL', 'AMZN', 'META', 'ARKK']
        
        # Primero verificar si es un ticker internacional conocido
        if simbolo_upper in tickers_internacionales:
            return ['NYSE', 'NASDAQ']
        
        # Verificar prefijos especiales
        for prefijo, mercados in prefijos_especiales.items():
            if simbolo_upper.startswith(prefijo) or simbolo_upper.endswith(prefijo):
                return mercados
        
        # Cedears comunes
        cedears_comunes = ['GGAL', 'YPFD', 'PAMP', 'TXAR', 'BMA', 'SUPV', 'COME']
        if simbolo_upper in cedears_comunes:
            return ['BCBA']
        
        # Para tickers de 1-5 letras (probablemente internacionales)
        if len(simbolo_upper) <= 5 and simbolo_upper.isalpha():
            return ['NYSE', 'NASDAQ', 'Cedears', 'BCBA']
        
        # Para tickers con puntos (como NVDA.BA)
        if '.' in simbolo_upper:
            base = simbolo_upper.split('.')[0]
            if base in tickers_internacionales:
                return ['Cedears', 'BCBA']
            return ['BCBA', 'Cedears']
        
        # Default para otros casos
        return ['BCBA', 'TitulosPublicos', 'Bonos', 'Cedears', 'NYSE', 'NASDAQ']
    
    def obtener_serie_historica(self, simbolo, fecha_desde, fecha_hasta, 
                               mercados=None, ajustada='ajustada', max_datos_por_mercado=1):
        """
        Obtiene serie histórica para un símbolo específico
        
        Args:
            simbolo (str): Símbolo del activo
            fecha_desde (str): Fecha de inicio (formato 'YYYY-MM-DD')
            fecha_hasta (str): Fecha de fin (formato 'YYYY-MM-DD')
            mercados (list): Lista de mercados a consultar (None = auto-detectar)
            ajustada (str): 'ajustada' o 'SinAjustar'
            max_datos_por_mercado (int): Máximo número de mercados a consultar
            
        Returns:
            pandas.Series: Serie de precios indexada por fecha
        """
        if mercados is None:
            mercados = self.detectar_mercado_simbolo(simbolo)
        
        mercados_a_probar = mercados[:max_datos_por_mercado] if max_datos_por_mercado else mercados
        
        for mercado in mercados_a_probar:
            try:
                serie = self._obtener_serie_mercado_especifico(
                    simbolo, mercado, fecha_desde, fecha_hasta, ajustada
                )
                if serie is not None and not serie.empty:
                    return serie
            except Exception as e:
                continue
        
        return None
    
    def _obtener_serie_mercado_especifico(self, simbolo, mercado, fecha_desde, fecha_hasta, ajustada):
        """Obtiene serie para un mercado específico"""
        if mercado not in self.mercados_config:
            return None
        
        config = self.mercados_config[mercado]
        endpoint = config['endpoint']
        
        # Construir URL según el tipo de mercado
        if mercado == 'FCI':
            url = f"{self.base_url}/{endpoint}/{simbolo}/cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
        elif mercado in ['Opciones']:
            url = f"{self.base_url}/{endpoint}/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
        elif mercado == 'Cauciones':
            # Para cauciones, usamos endpoint diferente
            url = f"{self.base_url}/Cotizaciones/Cauciones/Todas/Argentina"
        else:
            url = f"{self.base_url}/{endpoint}/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
        
        data = self._hacer_peticion(url)
        return self._procesar_respuesta_serie(data, simbolo)
    
    def _procesar_respuesta_serie(self, data, simbolo):
        """Procesa la respuesta de la API y devuelve una serie de pandas"""
        if not data:
            return None
        
        try:
            # Manejar diferentes formatos de respuesta
            if isinstance(data, list):
                precios = []
                fechas = []
                
                for item in data:
                    try:
                        # Diferentes campos de precio según el endpoint
                        precio = (item.get('ultimoPrecio') or 
                                item.get('precio') or 
                                item.get('valor') or
                                item.get('cierre') or
                                item.get('cierreAnterior') or
                                item.get('precioPromedio') or
                                item.get('apertura'))
                        
                        fecha_str = (item.get('fechaHora') or 
                                   item.get('fecha') or
                                   item.get('fechaOperacion'))
                        
                        if precio is not None and precio > 0 and fecha_str:
                            fecha_parsed = self._parse_fecha(fecha_str)
                            if fecha_parsed:
                                precios.append(float(precio))
                                fechas.append(fecha_parsed)
                    except (ValueError, TypeError):
                        continue
                
                if precios and fechas:
                    serie = pd.Series(precios, index=fechas, name=simbolo)
                    serie = serie[~serie.index.duplicated(keep='last')]
                    return serie.sort_index()
            
            # Para respuestas de FCI o datos únicos
            elif isinstance(data, dict):
                if 'ultimaCotizacion' in data:
                    cotizacion = data['ultimaCotizacion']
                    precio = cotizacion.get('precio')
                    fecha = cotizacion.get('fecha')
                    
                    if precio and fecha:
                        fecha_parsed = self._parse_fecha(fecha)
                        if fecha_parsed:
                            return pd.Series([float(precio)], index=[fecha_parsed], name=simbolo)
                
                # Manejar otros formatos de respuesta
                elif 'precio' in data and ('fecha' in data or 'fechaHora' in data):
                    precio = data.get('precio')
                    fecha = data.get('fecha') or data.get('fechaHora')
                    
                    if precio and fecha:
                        fecha_parsed = self._parse_fecha(fecha)
                        if fecha_parsed:
                            return pd.Series([float(precio)], index=[fecha_parsed], name=simbolo)
            
            # Para respuestas numéricas simples (ej: MEP)
            elif isinstance(data, (int, float)):
                return pd.Series([float(data)], index=[pd.Timestamp.now()], name=simbolo)
            
            return None
            
        except Exception as e:
            st.warning(f"Error procesando serie para {simbolo}: {str(e)}")
            return None
    
    def _parse_fecha(self, fecha_str):
        """Parse flexible de fechas"""
        formatos = [
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y"
        ]
        
        for fmt in formatos:
            try:
                return pd.to_datetime(fecha_str, format=fmt)
            except:
                continue
        
        try:
            return pd.to_datetime(fecha_str, infer_datetime_format=True)
        except:
            return None
    
    def obtener_multiples_series(self, simbolos_mercados, fecha_desde, fecha_hasta, 
                                ajustada='ajustada', mostrar_progreso=True):
        """
        Obtiene múltiples series históricas
        
        Args:
            simbolos_mercados (list): Lista de tuplas (simbolo, mercado) o lista de símbolos
            fecha_desde (str): Fecha inicio
            fecha_hasta (str): Fecha fin
            ajustada (str): Tipo de ajuste
            mostrar_progreso (bool): Mostrar barra de progreso
            
        Returns:
            dict: Diccionario con símbolo como clave y serie como valor
        """
        series_dict = {}
        
        if mostrar_progreso:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        total = len(simbolos_mercados)
        
        for idx, item in enumerate(simbolos_mercados):
            if isinstance(item, tuple):
                simbolo, mercados = item
            else:
                simbolo = item
                mercados = None
            
            if mostrar_progreso:
                progress = (idx + 1) / total
                progress_bar.progress(progress)
                status_text.text(f"Procesando {simbolo} ({idx + 1}/{total})")
            
            try:
                serie = self.obtener_serie_historica(
                    simbolo=simbolo,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                    mercados=mercados,
                    ajustada=ajustada
                )
                
                if serie is not None and not serie.empty:
                    series_dict[simbolo] = serie
                else:
                    st.warning(f"No se obtuvieron datos para {simbolo}")
                    
            except Exception as e:
                st.warning(f"Error obteniendo {simbolo}: {str(e)}")
            
            # Pausa para no saturar la API
            time.sleep(0.3)
        
        if mostrar_progreso:
            progress_bar.empty()
            status_text.empty()
        
        return series_dict
    
    def obtener_cotizacion_mep(self, simbolo, id_plazo_compra=1, id_plazo_venta=1):
        """Obtiene cotización MEP para un símbolo"""
        url = f"{self.base_url}/Cotizaciones/MEP"
        datos = {
            "simbolo": simbolo,
            "idPlazoOperatoriaCompra": id_plazo_compra,
            "idPlazoOperatoriaVenta": id_plazo_venta
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=datos, timeout=15)
            if response.status_code == 200:
                resultado = response.json()
                if isinstance(resultado, (int, float)):
                    return {'precio': resultado, 'simbolo': simbolo}
                elif isinstance(resultado, dict):
                    return resultado
                else:
                    return {'precio': None, 'simbolo': simbolo, 'error': 'Formato inesperado'}
            else:
                return {'precio': None, 'simbolo': simbolo, 'error': f'Error HTTP {response.status_code}'}
        except Exception as e:
            return {'precio': None, 'simbolo': simbolo, 'error': str(e)}
    
    def listar_instrumentos_mercado(self, mercado):
        """Lista todos los instrumentos disponibles en un mercado"""
        if mercado not in self.mercados_config:
            return []
        
        config = self.mercados_config[mercado]
        endpoint = config['endpoint']
        
        # URL para listar instrumentos
        url = f"{self.base_url}/{endpoint}"
        
        data = self._hacer_peticion(url)
        if data and isinstance(data, list):
            return [item.get('simbolo', '') for item in data if 'simbolo' in item]
        elif data and isinstance(data, dict) and 'titulos' in data:
            return [item.get('simbolo', '') for item in data['titulos'] if 'simbolo' in item]
        else:
            return []
    
    def obtener_tickers_por_panel(self, paneles, pais='Argentina'):
        """
        Obtiene tickers operables por panel
        
        Args:
            paneles (list): Lista de paneles a consultar
            pais (str): País de los instrumentos
            
        Returns:
            dict: Diccionario {panel: [tickers]}
            DataFrame: DataFrame con todos los tickers y sus paneles
        """
        tickers_por_panel = {}
        tickers_df = pd.DataFrame(columns=['panel', 'simbolo'])
        
        for panel in paneles:
            url = f'{self.base_url}/cotizaciones-orleans/{panel}/{pais}/Operables'
            data = self._hacer_peticion(url)
            
            if data and 'titulos' in data:
                tickers = [titulo['simbolo'] for titulo in data['titulos']]
                tickers_por_panel[panel] = tickers
                panel_df = pd.DataFrame({'panel': panel, 'simbolo': tickers})
                tickers_df = pd.concat([tickers_df, panel_df], ignore_index=True)
            
        return tickers_por_panel, tickers_df
    
    def obtener_series_historicas_aleatorias(self, tickers_por_panel, paneles_seleccionados,
                                          cantidad_activos, fecha_desde, fecha_hasta, 
                                          ajustada='ajustada'):
        """
        Obtiene series históricas para activos seleccionados aleatoriamente por panel
        
        Args:
            tickers_por_panel (dict): Diccionario de tickers por panel
            paneles_seleccionados (list): Paneles a considerar
            cantidad_activos (int): Número de activos por panel
            fecha_desde (str): Fecha inicio
            fecha_hasta (str): Fecha fin
            ajustada (str): Tipo de ajuste
            
        Returns:
            DataFrame: Series históricas consolidadas
        """
        series_historicas = pd.DataFrame()
        
        for panel in paneles_seleccionados:
            if panel in tickers_por_panel:
                seleccion = random.sample(tickers_por_panel[panel], 
                                      min(cantidad_activos, len(tickers_por_panel[panel])))
                for simbolo in seleccion:
                    mercado = self.detectar_mercado_simbolo(simbolo)[0]
                    serie = self.obtener_serie_historica(simbolo, mercado, fecha_desde, 
                                                        fecha_hasta, ajustada)
                    if serie is not None:
                        df = pd.DataFrame(serie)
                        df['simbolo'] = simbolo
                        df['panel'] = panel
                        series_historicas = pd.concat([series_historicas, df], 
                                                  ignore_index=True)
        
        return series_historicas
    
    def obtener_series_historicas_aleatorias_con_capital(self, tickers_por_panel, paneles_seleccionados, 
                                                       cantidad_activos, fecha_desde, fecha_hasta, 
                                                       ajustada, capital_ars):
        """
        Obtiene series históricas para activos aleatorios considerando capital disponible
        
        Args:
            tickers_por_panel (dict): Diccionario de tickers por panel
            paneles_seleccionados (list): Paneles a considerar
            cantidad_activos (int): Número de activos por panel
            fecha_desde (str): Fecha inicio
            fecha_hasta (str): Fecha fin
            ajustada (str): Tipo de ajuste
            capital_ars (float): Capital disponible en ARS
            
        Returns:
            DataFrame: Series históricas consolidadas
            dict: Diccionario con los activos seleccionados por panel
        """
        series_historicas = pd.DataFrame()
        precios_ultimos = {}
        seleccion_final = {}

        for panel in paneles_seleccionados:
            if panel in tickers_por_panel:
                tickers = tickers_por_panel[panel]
                random.shuffle(tickers)
                seleccionados = []
                
                for simbolo in tickers:
                    mercado = self.detectar_mercado_simbolo(simbolo)[0]
                    serie = self.obtener_serie_historica(simbolo, mercado, fecha_desde, 
                                                        fecha_hasta, ajustada)
                    
                    if serie is not None and len(serie) > 0:
                        precio_final = serie.iloc[-1]
                        precios_ultimos[simbolo] = precio_final
                        seleccionados.append((simbolo, serie, precio_final))
                    
                    if len(seleccionados) >= cantidad_activos:
                        break
                
                # Filtrar por capital disponible
                seleccionados.sort(key=lambda x: x[2])
                seleccionables = []
                capital_restante = capital_ars
                
                for simbolo, serie, precio in seleccionados:
                    if precio <= capital_restante:
                        seleccionables.append((simbolo, serie, precio))
                        capital_restante -= precio
                
                # Consolidar resultados
                if len(seleccionables) > 0:
                    for simbolo, serie, precio in seleccionables:
                        df = pd.DataFrame({'precio': serie, 'fecha': serie.index})
                        df['simbolo'] = simbolo
                        df['panel'] = panel
                        series_historicas = pd.concat([series_historicas, df], ignore_index=True)
                    
                    seleccion_final[panel] = [s[0] for s in seleccionables]
        
        return series_historicas, seleccion_final
    
    def calcular_valorizado_portafolio(self, series_historicas, seleccion_final):
        """
        Calcula la evolución del valor del portafolio por panel
        
        Args:
            series_historicas (DataFrame): Series históricas
            seleccion_final (dict): Activos seleccionados por panel
            
        Returns:
            dict: Diccionario con la evolución del valor por panel
        """
        portafolios_val = {}
        
        for panel, simbolos in seleccion_final.items():
            df_panel = series_historicas[series_historicas['panel'] == panel]
            df_pivot = df_panel.pivot_table(index='fecha', columns='simbolo', values='precio')
            df_pivot = df_pivot[simbolos].sort_index()
            
            # Calcular valorizado (suma simple)
            portafolio_val = df_pivot.sum(axis=1)
            portafolios_val[panel] = portafolio_val
        
        return portafolios_val
    
    @staticmethod
    def calcular_rsi(series, period=14):
        """Calcula el RSI de una serie de precios"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calcular_rvi(series, period=14):
        """
        Calcula el Relative Volatility Index (RVI)
        Similar al RSI pero usando desviación estándar
        """
        delta = series.diff()
        std = delta.rolling(window=period).std()
        up = std.where(delta > 0, 0)
        down = std.where(delta < 0, 0).abs()
        up_mean = up.rolling(window=period).mean()
        down_mean = down.rolling(window=period).mean()
        rvi = 100 * up_mean / (up_mean + down_mean)
        return rvi

# Función de conveniencia para mantener compatibilidad
def crear_serie_historica_manager(token_acceso, refresh_token=None):
    """Crea una instancia del manager de series históricas"""
    return SerieHistoricaIOL(token_acceso, refresh_token)

def get_historical_data_for_optimization(token_portador, simbolos, fecha_desde, fecha_hasta):
    """
    Obtiene datos históricos para optimización usando la nueva clase universal
    """
    try:
        # Crear manager de series históricas
        serie_manager = SerieHistoricaIOL(token_portador)
        
        # Preparar lista de símbolos con mercados auto-detectados
        simbolos_procesados = []
        for item in simbolos:
            if isinstance(item, tuple):
                simbolo, mercado = item
                simbolos_procesados.append((simbolo, [mercado] if mercado else None))
            else:
                simbolos_procesados.append(item)
        
        # Obtener series múltiples
        series_dict = serie_manager.obtener_multiples_series(
            simbolos_mercados=simbolos_procesados,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            ajustada='ajustada',
            mostrar_progreso=True
        )
        
        if not series_dict:
            st.error("❌ No se pudieron cargar los datos históricos")
            return None, None, None
        
        # Crear DataFrame alineado
        df_precios = pd.DataFrame(series_dict)
        
        if df_precios.empty:
            st.error("❌ DataFrame vacío")
            return None, None, None
        
        # Rellenar datos faltantes hacia adelante
        df_precios = df_precios.fillna(method='ffill').dropna()
        
        if len(df_precios) < 30:
            st.warning("⚠️ Datos insuficientes para análisis (menos de 30 observaciones)")
            return None, None, None
        
        # Calcular retornos
        returns = df_precios.pct_change().dropna()
        
        # Eliminar columnas con varianza cero
        valid_columns = returns.columns[returns.std() > 0]
        if len(valid_columns) < 2:
            st.warning("⚠️ No hay suficientes activos con variación para optimización")
            return None, None, None
        
        returns = returns[valid_columns]
        df_precios = df_precios[valid_columns]
        
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        
        st.success(f"✅ Datos cargados: {len(valid_columns)} activos, {len(returns)} observaciones")
        
        return mean_returns, cov_matrix, df_precios
        
    except Exception as e:
        st.error(f"❌ Error en get_historical_data_for_optimization: {str(e)}")
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
    
    # Procesar cada activo para extraer información relevante
    for activo in activos:
        try:
            titulo = activo.get('titulo', {})
            simbolo = titulo.get('simbolo', 'N/A')
            descripcion = titulo.get('descripcion', 'Sin descripción')
            tipo = titulo.get('tipo', 'N/A')
            cantidad = activo.get('cantidad', 0)
            
            # Campos posibles para obtener la valuación
            campos_valuacion = [
                'valuacionEnMonedaOriginal', 'valuacionActual', 'valorNominalEnMonedaOriginal',
                'valorNominal', 'valuacionDolar', 'valuacion', 'valorActual', 'montoInvertido',
                'valorMercado', 'valorTotal', 'importe'
            ]
            
            valuacion = 0
            precio_unitario = 0
            
            # 1. Intentar obtener la valuación directa
            for campo in campos_valuacion:
                if campo in activo and activo[campo] is not None:
                    try:
                        val = float(activo[campo])
                        if val > 0:
                            valuacion = val
                            break
                    except (ValueError, TypeError):
                        continue
            
            # 2. Si no hay valuación, intentar calcularla con cantidad * precio
            if valuacion == 0 and cantidad:
                campos_precio = [
                    'precioPromedio', 'precioCompra', 'precioActual', 'precio',
                    'precioUnitario', 'ultimoPrecio', 'cotizacion'
                ]
                
                # Buscar precio en el activo
                for campo in campos_precio:
                    if campo in activo and activo[campo] is not None:
                        try:
                            precio = float(activo[campo])
                            if precio > 0:
                                precio_unitario = precio
                                break
                        except (ValueError, TypeError):
                            continue
                
                # Si no encontramos precio en el activo, buscamos en el título
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
                
                # Calcular la valuación
                if precio_unitario > 0:
                    try:
                        cantidad_num = float(cantidad)
                        # Ajuste para bonos (precio por 100 nominal)
                        if tipo == 'TitulosPublicos':
                            valuacion = (cantidad_num * precio_unitario) / 100.0
                        else:
                            valuacion = cantidad_num * precio_unitario
                    except (ValueError, TypeError) as e:
                        st.warning(f"Error calculando valuación para {simbolo}: {str(e)}")
            
            # Agregar a los datos del portafolio
            if simbolo != 'N/A' and cantidad > 0:
                datos_activos.append({
                    'simbolo': simbolo,
                    'tipo': tipo,
                    'cantidad': float(cantidad),
                    'precio': precio_unitario if precio_unitario > 0 else valuacion/float(cantidad) if float(cantidad) > 0 else 0,
                    'moneda': 'ARS',  # Asumimos ARS por defecto
                    'descripcion': descripcion,
                    'valor_total': valuacion
                })
                valor_total += valuacion
                
        except Exception as e:
            st.warning(f"Error procesando activo: {str(e)}")
            continue
    
    # Si hay datos, mostramos el análisis
    if datos_activos:
        # Convertir a DataFrame
        df_portafolio = pd.DataFrame(datos_activos)
        
        # Crear y mostrar el análisis con la nueva clase
        try:
            analizador = AnalizadorPortafolio(df_portafolio)
            analizador.mostrar_resumen()
            
            # Mostrar tabla detallada de activos
            st.subheader("📋 Detalle de Activos")
            st.dataframe(df_portafolio[['simbolo', 'descripcion', 'tipo', 'cantidad', 'precio', 'valor_total']]
                        .rename(columns={
                            'simbolo': 'Símbolo',
                            'descripcion': 'Descripción',
                            'tipo': 'Tipo',
                            'cantidad': 'Cantidad',
                            'precio': 'Precio Unitario',
                            'valor_total': 'Valor Total'
                        }), 
                        use_container_width=True)
            
        except Exception as e:
            st.error(f"Error generando análisis del portafolio: {str(e)}")
            st.exception(e)  # Mostrar detalles del error para depuración
    else:
        st.warning("No se encontraron activos para analizar en el portafolio")

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

class AnalizadorPortafolio:
    """
    Sistema completo de análisis de portafolio con:
    - Métricas detalladas
    - Explicaciones claras
    - Visualizaciones interactivas
    - Recomendaciones automáticas
    """
    def __init__(self, portafolio_data):
        """
        Inicializa con datos del portafolio de IOL
        portafolio_data: DataFrame con columnas ['simbolo', 'tipo', 'cantidad', 'precio', 'moneda']
        """
        self.portafolio = portafolio_data
        self.metricas = self._calcular_metricas()
        self.explicaciones = {
            'total_activos': "Número total de posiciones en tu portafolio, incluyendo múltiples posiciones del mismo activo.",
            'simbolos_unicos': "Cantidad de activos diferentes en tu portafolio.",
            'tipos_activos': "Diversificación por clase de activo (acciones, bonos, etc.).",
            'valor_total': "Valor total calculado en pesos al precio de mercado actual.",
            'concentracion': """
                Índice de Herfindahl (0-1) que mide concentración:
                < 0.15 🟢 Baja | 0.15-0.25 🟡 Media | > 0.25 🔴 Alta
                Calculado como suma de (valor_activo/valor_total)^2
            """,
            'volatilidad': "Desviación estándar del valor diario histórico del portafolio.",
            'retorno_esperado': "Media de los retornos históricos proyectados a 1 año.",
            'optimista': "Escenario del mejor 5% de las simulaciones (95% percentil).",
            'pesimista': "Escenario del peor 5% de las simulaciones (5% percentil).",
            'prob_ganancia': "Porcentaje de simulaciones con resultado positivo.",
            'prob_perdida': "Porcentaje de simulaciones con resultado negativo.",
            'prob_ganancia_10': "Probabilidad de ganar más del 10%.",
            'prob_perdida_10': "Probabilidad de perder más del 10%."
        }
    
    def _calcular_metricas(self):
        """Calcula todas las métricas clave del portafolio"""
        # Métricas básicas
        valor_por_activo = self.portafolio['cantidad'] * self.portafolio['precio']
        valor_total = valor_por_activo.sum()
        
        # Cálculo de concentración (Índice Herfindahl)
        participaciones = (valor_por_activo / valor_total) ** 2
        concentracion = participaciones.sum()
        
        # Nivel de concentración (texto)
        if concentracion < 0.15:
            nivel_concentracion = "🟢 Baja"
        elif concentracion < 0.25:
            nivel_concentracion = "🟡 Media"
        else:
            nivel_concentracion = "🔴 Alta"
        
        return {
            'total_activos': len(self.portafolio),
            'simbolos_unicos': self.portafolio['simbolo'].nunique(),
            'tipos_activos': self.portafolio['tipo'].nunique(),
            'valor_total': valor_total,
            'concentracion': concentracion,
            'nivel_concentracion': nivel_concentracion,
            'volatilidad': self._calcular_volatilidad(),
            'retornos': self._calcular_retornos_diarios()
        }
    
    def _calcular_volatilidad(self):
        """Calcula volatilidad histórica del portafolio"""
        # Implementar cálculo real con datos históricos
        return 2946  # Valor de ejemplo
    
    def _calcular_retornos_diarios(self):
        """Obtiene serie histórica de retornos diarios"""
        # Implementar con API de IOL
        return np.random.normal(0.001, 0.02, 252)  # Datos de ejemplo
    
    def generar_recomendaciones(self):
        """Genera recomendaciones basadas en el análisis"""
        recomendaciones = []
        
        if self.metricas['concentracion'] > 0.25:
            recomendaciones.append("🔴 Considera diversificar tu portafolio para reducir riesgo de concentración")
        elif self.metricas['concentracion'] > 0.15:
            recomendaciones.append("🟡 Tu portafolio tiene una concentración moderada")
        else:
            recomendaciones.append("🟢 Buen nivel de diversificación en tu portafolio")
            
        if self.metricas['tipos_activos'] < 3:
            recomendaciones.append("🔴 Aumenta diversificación incluyendo más clases de activos")
            
        if len(recomendaciones) == 0:
            recomendaciones.append("🟢 Tu portafolio está bien diversificado y balanceado")
            
        return recomendaciones
    
    def mostrar_resumen(self):
        """Muestra dashboard completo con todas las métricas"""
        st.title("📊 Análisis Integral de Portafolio")
        
        # Sección 1: Resumen General
        st.header("📈 Resumen del Portafolio")
        cols = st.columns(4)
        cols[0].metric("Total de Activos", self.metricas['total_activos'], 
                      help=self.explicaciones['total_activos'])
        cols[1].metric("Símbolos Únicos", self.metricas['simbolos_unicos'],
                      help=self.explicaciones['simbolos_unicos'])
        cols[2].metric("Tipos de Activos", self.metricas['tipos_activos'],
                      help=self.explicaciones['tipos_activos'])
        cols[3].metric("Valor Total", f"${self.metricas['valor_total']:,.2f}",
                      help=self.explicaciones['valor_total'])
        
        # Sección 2: Análisis de Riesgo
        st.header("⚖️ Análisis de Riesgo")
        cols = st.columns(3)
        cols[0].metric("Concentración", f"{self.metricas['concentracion']:.3f}",
                      help=self.explicaciones['concentracion'])
        cols[1].metric("Volatilidad", f"${self.metricas['volatilidad']:,.2f}",
                      help=self.explicaciones['volatilidad'])
        cols[2].metric("Nivel Concentración", self.metricas['nivel_concentracion'],
                      help="Índice de Herfindahl para medir concentración de riesgo")
        
        # Sección 3: Proyecciones
        st.header("📈 Proyecciones de Rendimiento")
        proyecciones = self._calcular_proyecciones()
        
        cols = st.columns(3)
        cols[0].metric("Retorno Esperado", f"${proyecciones['retorno_esperado']:,.2f}",
                      help=self.explicaciones['retorno_esperado'])
        cols[1].metric("Escenario Optimista", f"${proyecciones['optimista']:,.2f}",
                      help=self.explicaciones['optimista'])
        cols[2].metric("Escenario Pesimista", f"${proyecciones['pesimista']:,.2f}",
                      help=self.explicaciones['pesimista'])
        
        # Sección 4: Probabilidades
        st.header("🎯 Probabilidades")
        cols = st.columns(4)
        cols[0].metric("Ganancia", f"{proyecciones['prob_ganancia']:.1f}%",
                      help=self.explicaciones['prob_ganancia'])
        cols[1].metric("Pérdida", f"{proyecciones['prob_perdida']:.1f}%",
                      help=self.explicaciones['prob_perdida'])
        cols[2].metric("Ganancia >10%", f"{proyecciones['prob_ganancia_10']:.1f}%",
                      help=self.explicaciones['prob_ganancia_10'])
        cols[3].metric("Pérdida >10%", f"{proyecciones['prob_perdida_10']:.1f}%",
                      help=self.explicaciones['prob_perdida_10'])
        
        # Sección 5: Distribución de Activos
        st.header("📊 Distribución de Activos")
        self._graficar_distribucion_activos()
        
        # Sección 6: Detalle de Activos
        st.header("📋 Detalle de Activos")
        st.dataframe(self.portafolio, use_container_width=True)
        
        # Sección 7: Recomendaciones
        st.header("💡 Recomendaciones")
        for rec in self.generar_recomendaciones():
            st.markdown(f"- {rec}")
    
    def _calcular_proyecciones(self, n_simulaciones=10000, horizonte=252):
        """Calcula proyecciones usando simulación Monte Carlo"""
        retornos = self.metricas['retornos']
        media = np.mean(retornos)
        std = np.std(retornos)
        
        # Simulación Monte Carlo
        simulaciones = np.random.normal(media, std, (n_simulaciones, horizonte))
        trayectorias = np.cumprod(1 + simulaciones, axis=1) * self.metricas['valor_total']
        
        # Calcular métricas
        finales = trayectorias[:, -1]
        
        return {
            'retorno_esperado': np.median(finales),
            'optimista': np.percentile(finales, 95),
            'pesimista': np.percentile(finales, 5),
            'prob_ganancia': np.mean(finales > self.metricas['valor_total']) * 100,
            'prob_perdida': np.mean(finales < self.metricas['valor_total']) * 100,
            'prob_ganancia_10': np.mean(finales > self.metricas['valor_total'] * 1.1) * 100,
            'prob_perdida_10': np.mean(finales < self.metricas['valor_total'] * 0.9) * 100
        }
    
    def _graficar_distribucion_activos(self):
        """Muestra gráfico de distribución de activos por tipo"""
        df_activos = self.portafolio.copy()
        df_activos['valor'] = df_activos['cantidad'] * df_activos['precio']
        
        # Agrupar por tipo de activo
        df_tipos = df_activos.groupby('tipo')['valor'].sum().reset_index()
        
        # Crear gráfico de torta
        fig = go.Figure(data=[go.Pie(
            labels=df_tipos['tipo'],
            values=df_tipos['valor'],
            hole=.3,
            textinfo='label+percent',
            insidetextorientation='radial'
        )])
        
        fig.update_layout(
            title_text="Distribución por Tipo de Activo",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
