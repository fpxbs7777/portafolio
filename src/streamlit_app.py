import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
from datetime import date, timedelta, datetime
import numpy as np
import pandas as pd
import yfinance as yf
import scipy.optimize as op
from scipy import stats
import random
import warnings
import streamlit.components.v1 as components
from scipy.stats import linregress
import asyncio
import aiohttp

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

def obtener_precio_actual(token_portador, mercado, simbolo):
    """Obtiene el último precio de un título puntual (endpoint estándar de IOL)."""
    url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion"
    headers = obtener_encabezado_autorizacion(token_portador)
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, (int, float)):
                return float(data)
            elif isinstance(data, dict):
                # La API suele devolver 'ultimoPrecio'
                for k in [
                    'ultimoPrecio', 'ultimo_precio', 'ultimoPrecioComprador', 'ultimoPrecioVendedor',
                    'precio', 'precioActual', 'valor'
                ]:
                    if k in data and data[k] is not None:
                        try:
                            return float(data[k])
                        except ValueError:
                            continue
        return None
    except Exception:
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

def parse_datetime_string(datetime_string):
    """
    Parsea una cadena de fecha/hora usando múltiples formatos
    """
    if not datetime_string:
        return None
        
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

def obtener_endpoint_historico(mercado, simbolo, fecha_desde, fecha_hasta, ajustada="SinAjustar"):
    """Devuelve la URL correcta para la serie histórica del símbolo indicado.

    La prioridad es:
    1. Usar el mercado recibido (ya normalizado por la llamada superior)
       si existe en el mapeo de casos especiales.
    2. Caso contrario, construir la ruta estándar
       "{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/...".

    No se aplican heurísticas sobre el símbolo: la función que invoque debe
    pasar el mercado correcto (por ejemplo: 'Bonos', 'Cedears', 'BCBA').
    """
    base_url = "https://api.invertironline.com/api/v2"

    # Cubrir alias frecuentes para que el mapeo sea coherente
    alias = {
        'TITULOSPUBLICOS': 'TitulosPublicos',
        'TITULOS PUBLICOS': 'TitulosPublicos'
    }
    mercado_norm = alias.get(mercado.upper(), mercado)

    especiales = {
        'Opciones': f"{base_url}/Opciones/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'FCI': f"{base_url}/Titulos/FCI/{simbolo}/cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'MEP': f"{base_url}/Cotizaciones/MEP/{simbolo}",
        'Caucion': f"{base_url}/Cotizaciones/Cauciones/Todas/Argentina",
        'TitulosPublicos': f"{base_url}/TitulosPublicos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'Cedears': f"{base_url}/Cedears/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'ADRs': f"{base_url}/ADRs/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'Bonos': f"{base_url}/Bonos/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
    }

    if mercado_norm in especiales:
        return especiales[mercado_norm]

    # Ruta genérica (acciones BCBA, NYSE, NASDAQ, etc.)
    return f"{base_url}/{mercado_norm}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"

def parse_datetime_flexible(date_str: str):
    """
    Parses a datetime string that may or may not include microseconds or timezone info.
    Handles both formats: with and without milliseconds.
    """
    if not isinstance(date_str, str):
        return None
    try:
        # First try parsing with the exact format that matches the error
        try:
            # Handle format without milliseconds: "2024-12-10T17:11:04"
            if len(date_str) == 19 and 'T' in date_str and date_str.count(':') == 2:
                return pd.to_datetime(date_str, format='%Y-%m-%dT%H:%M:%S', utc=True)
            # Handle format with milliseconds: "2024-12-10T17:11:04.123"
            elif '.' in date_str and 'T' in date_str:
                return pd.to_datetime(date_str, format='%Y-%m-%dT%H:%M:%S.%f', utc=True)
        except (ValueError, TypeError):
            pass
            
        # Fall back to pandas' built-in parser if specific formats don't match
        return pd.to_datetime(date_str, errors='coerce', utc=True)
    except Exception as e:
        st.warning(f"Error parsing date '{date_str}': {str(e)}")
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
                df = pd.DataFrame({'fecha': fechas, 'precio': precios})
                # Eliminar duplicados manteniendo el último
                df = df.drop_duplicates(subset=['fecha'], keep='last')
                df = df.sort_values('fecha')
                return df
        
        # Para respuestas que son un solo valor (ej: MEP)
        elif isinstance(data, (int, float)):
            df = pd.DataFrame({'fecha': [pd.Timestamp.now(tz='UTC').date()], 'precio': [float(data)]})
            return df
            
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



def obtener_serie_historica_iol(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="SinAjustar"):
    """
    Obtiene la serie histórica de precios para un activo específico desde la API de InvertirOnline.
    
    Args:
        token_portador (str): Token de autenticación de la API
        mercado (str): Mercado del activo (ej: 'BCBA', 'NYSE', 'NASDAQ')
        simbolo (str): Símbolo del activo
        fecha_desde (str): Fecha de inicio en formato 'YYYY-MM-DD'
        fecha_hasta (str): Fecha de fin en formato 'YYYY-MM-DD'
        ajustada (str): Tipo de ajuste ('Ajustada' o 'SinAjustar')
        
    Returns:
        pd.DataFrame: DataFrame con las columnas 'fecha' y 'precio', o None en caso de error
    """
    try:
        print(f"Obteniendo datos para {simbolo} en {mercado} desde {fecha_desde} hasta {fecha_hasta}")
        
        # Endpoint para FCIs (manejo especial)
        if mercado.upper() == 'FCI':
            print("Es un FCI, usando función específica")
            return obtener_serie_historica_fci(token_portador, simbolo, fecha_desde, fecha_hasta)
        
        # Construir URL según el tipo de activo y mercado
        url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
        print(f"URL de la API: {url.split('?')[0]}")  # Mostrar URL sin parámetros sensibles
        
        headers = {
            'Authorization': 'Bearer [TOKEN]',  # No mostrar el token real
            'Accept': 'application/json'
        }
        
        # Realizar la solicitud
        response = requests.get(url, headers={
            'Authorization': f'Bearer {token_portador}',
            'Accept': 'application/json'
        }, timeout=30)
        
        # Verificar el estado de la respuesta
        print(f"Estado de la respuesta: {response.status_code}")
        response.raise_for_status()
        
        # Procesar la respuesta
        data = response.json()
        print(f"Tipo de datos recibidos: {type(data)}")
        
        # Procesar la respuesta según el formato esperado
        if isinstance(data, list):
            print(f"Se recibió una lista con {len(data)} elementos")
            if data:
                print(f"Primer elemento: {data[0]}")
                
            # Formato estándar para series históricas
            fechas = []
            precios = []
            
            for item in data:
                try:
                    # Manejar diferentes formatos de fecha
                    fecha_str = item.get('fecha') or item.get('fechaHora')
                    if not fecha_str:
                        print(f"  - Item sin fecha: {item}")
                        continue
                        
                    # Manejar diferentes formatos de precio
                    precio = item.get('ultimoPrecio') or item.get('precioCierre') or item.get('precio')
                    if precio is None:
                        print(f"  - Item sin precio: {item}")
                        continue
                        
                    # Convertir fecha
                    try:
                        fecha = parse_datetime_flexible(fecha_str)
                        if pd.isna(fecha):
                            print(f"  - Fecha inválida: {fecha_str}")
                            continue
                            
                        precio_float = float(precio)
                        if precio_float <= 0:
                            print(f"  - Precio inválido: {precio}")
                            continue
                            
                        fechas.append(fecha)
                        precios.append(precio_float)
                        
                    except (ValueError, TypeError) as e:
                        print(f"  - Error al convertir datos: {e}")
                        continue
                        
                except Exception as e:
                    print(f"  - Error inesperado al procesar item: {e}")
                    continue
            
            if fechas and precios:
                df = pd.DataFrame({'fecha': fechas, 'precio': precios})
                # Eliminar duplicados manteniendo el último
                df = df.drop_duplicates(subset=['fecha'], keep='last')
                df = df.sort_values('fecha')
                print(f"Datos procesados: {len(df)} registros válidos")
                return df
            else:
                print("No se encontraron datos válidos en la respuesta")
                return None
                
        elif isinstance(data, dict):
            print(f"Se recibió un diccionario: {data.keys()}")
            # Para respuestas que son un solo valor (ej: MEP)
            precio = data.get('ultimoPrecio') or data.get('precioCierre') or data.get('precio')
            if precio is not None:
                print(f"Datos de un solo punto: precio={precio}")
                return pd.DataFrame({
                    'fecha': [pd.Timestamp.now(tz='UTC')],
                    'precio': [float(precio)]
                })
            else:
                print("No se encontró precio en la respuesta")
        else:
            print(f"Tipo de respuesta no manejado: {type(data)}")
            
        print(f"No se pudieron procesar los datos para {simbolo} en {mercado}")
        return None
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error de conexión para {simbolo} en {mercado}: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" - Status: {e.response.status_code}"
            try:
                error_msg += f" - Respuesta: {e.response.text[:200]}"
            except:
                pass
        print(error_msg)
        st.warning(error_msg)
        return None
    except Exception as e:
        error_msg = f"Error inesperado al procesar {simbolo} en {mercado}: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        st.error(error_msg)
        return None
        return None

def obtener_serie_historica_fci(token_portador, simbolo, fecha_desde, fecha_hasta):
    """
    Obtiene la serie histórica de un Fondo Común de Inversión.
    
    Args:
        token_portador (str): Token de autenticación
        simbolo (str): Símbolo del FCI
        fecha_desde (str): Fecha inicio (YYYY-MM-DD)
        fecha_hasta (str): Fecha fin (YYYY-MM-DD)
        
    Returns:
        pd.DataFrame: DataFrame con columnas 'fecha' y 'precio', o None si hay error
    """
    try:
        # Primero intentar obtener directamente la serie histórica
        url_serie = f"https://api.invertironline.com/api/v2/Titulos/FCI/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/SinAjustar"
        headers = {
            'Authorization': f'Bearer {token_portador}',
            'Accept': 'application/json'
        }
        
        response = requests.get(url_serie, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Procesar la respuesta según el formato esperado
        if isinstance(data, list):
            fechas = []
            precios = []
            
            for item in data:
                try:
                    # Manejar diferentes formatos de fecha
                    fecha_str = item.get('fecha') or item.get('fechaHora')
                    if not fecha_str:
                        continue
                        
                    # Obtener el valor de la cuota (puede venir en diferentes campos)
                    precio = item.get('valorCuota') or item.get('precio') or item.get('ultimoPrecio')
                    if not precio:
                        continue
                        
                    # Convertir fecha
                    fecha = parse_datetime_flexible(fecha_str)
                    if not pd.isna(fecha):
                        fechas.append(fecha)
                        precios.append(float(precio))
                        
                except (ValueError, TypeError, AttributeError) as e:
                    continue
            
            if fechas and precios:
                df = pd.DataFrame({'fecha': fechas, 'precio': precios})
                df = df.drop_duplicates(subset=['fecha'], keep='last')
                df = df.sort_values('fecha')
                return df
        
        # Si no se pudo obtener la serie histórica, intentar obtener el último valor
        try:
            # Obtener información del FCI
            url_fci = "https://api.invertironline.com/api/v2/Titulos/FCI"
            response = requests.get(url_fci, headers=headers, timeout=30)
            response.raise_for_status()
            fc_data = response.json()
            
            # Buscar el FCI por símbolo
            fci = next((f for f in fc_data if f.get('simbolo') == simbolo), None)
            if fci and 'ultimoValorCuotaParte' in fci:
                return pd.DataFrame({
                    'fecha': [pd.Timestamp.now(tz='UTC')],
                    'precio': [float(fci['ultimoValorCuotaParte'])]
                })
        except Exception:
            pass
        
        st.warning(f"No se pudieron obtener datos históricos para el FCI {simbolo}")
        return None
        
    except requests.exceptions.RequestException as e:
        st.warning(f"Error de conexión al obtener datos del FCI {simbolo}: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error inesperado al procesar el FCI {simbolo}: {str(e)}")
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
            if ric in self.timeseries and self.timeseries[ric] is not None:
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
        if self.returns is not None:
            portfolio_returns = self.returns.dot(weights)
        else:
            # Fallback si returns es None
            portfolio_returns = pd.Series([0] * 252)  # Serie vacía
        
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
        # Compatibilidad: alias para risk y returns (usados en la interfaz)
        self.risk = self.volatility_annual
        self.returns = self.return_annual

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
        # Asegura que self.returns sea un array NumPy plano
        import numpy as np
        arr = self.returns
        if hasattr(arr, "values"):
            arr = arr.values
        arr = np.asarray(arr).flatten()
        if arr is None or len(arr) == 0 or not np.issubdtype(arr.dtype, np.number):
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos suficientes para mostrar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(title=title)
            return fig

        fig = go.Figure(data=[go.Histogram(
            x=arr,
            nbinsx=30,
            name="Retornos del Portafolio",
            marker_color='#0d6efd'
        )])
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


# --- Async Historical Data Download ---
async def obtener_serie_historica_iol_async(session, token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="SinAjustar"):
    """
    Versión asíncrona para obtener la serie histórica de precios de un activo.
    """
    url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    headers = {
        'Authorization': f'Bearer {token_portador}',
        'Accept': 'application/json'
    }
    try:
        async with session.get(url, headers=headers, timeout=30) as response:
            if response.status != 200:
                return None
            data = await response.json()
            # Procesamiento igual que en la función sincrónica
            if isinstance(data, list):
                fechas, precios = [], []
                for item in data:
                    fecha_str = item.get('fecha') or item.get('fechaHora')
                    precio = item.get('ultimoPrecio') or item.get('precioCierre') or item.get('precio')
                    if fecha_str and precio is not None:
                        try:
                            fecha = parse_datetime_flexible(fecha_str)
                            precio_float = float(precio)
                            if pd.isna(fecha) or precio_float <= 0:
                                continue
                            fechas.append(fecha)
                            precios.append(precio_float)
                        except Exception:
                            continue
                if fechas and precios:
                    df = pd.DataFrame({'fecha': fechas, 'precio': precios})
                    df = df.drop_duplicates(subset=['fecha'], keep='last')
                    df = df.sort_values('fecha')
                    return df
            elif isinstance(data, dict):
                precio = data.get('ultimoPrecio') or data.get('precioCierre') or data.get('precio')
                if precio is not None:
                    return pd.DataFrame({
                        'fecha': [pd.Timestamp.now(tz='UTC')],
                        'precio': [float(precio)]
                    })
            return None
    except Exception:
        return None

async def obtener_series_historicas_en_paralelo(token_portador, activos, fecha_desde, fecha_hasta):
    """
    Descarga series históricas en paralelo para una lista de activos.
    activos: lista de dicts con 'simbolo' y 'mercado'
    """
    results = {}
    async with aiohttp.ClientSession() as session:
        tasks = []
        for activo in activos:
            simbolo = activo.get('simbolo')
            mercado = activo.get('mercado')
            if simbolo and mercado:
                tasks.append(obtener_serie_historica_iol_async(session, token_portador, mercado, simbolo, fecha_desde, fecha_hasta))
            else:
                tasks.append(None)
        responses = await asyncio.gather(*tasks)
        for i, activo in enumerate(activos):
            simbolo = activo.get('simbolo')
            if simbolo and responses[i] is not None:
                results[simbolo] = responses[i]
    return results

# --- Funciones principales ---
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

# --- Interfaz de usuario y lógica principal ---
def mostrar_optimizacion_portafolio(token_acceso, id_cliente):
    st.markdown("### 🔄 Menú Avanzado de Optimización de Portafolio")
    with st.spinner("Obteniendo portafolio actual..."):
        portafolio = obtener_portafolio(token_acceso, id_cliente)
    if not portafolio or not portafolio.get('activos'):
        st.warning("No se pudo obtener el portafolio del cliente o está vacío")
        return

    activos_raw = portafolio['activos']
    # Diagnóstico del portafolio actual
    st.subheader("🔍 Diagnóstico del Portafolio Actual")
    # --- NUEVO: Descarga asíncrona de series históricas para diagnóstico ---
    activos_dict = {}
    valor_total = 0
    activos_para_historico = []
    for activo in activos_raw:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', 'N/A')
        tipo = titulo.get('tipo', 'N/A')
        valuacion = 0
        campos_valuacion = [
            'valuacionEnMonedaOriginal', 'valuacionActual', 'valorNominalEnMonedaOriginal', 'valorNominal',
            'valuacionDolar', 'valuacion', 'valorActual', 'montoInvertido', 'valorMercado', 'valorTotal', 'importe'
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
        if valuacion == 0 and activo.get('cantidad', 0):
            campos_precio = [
                'precioPromedio', 'precioCompra', 'precioActual', 'precio', 'precioUnitario', 'ultimoPrecio', 'cotizacion'
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
            if precio_unitario > 0:
                try:
                    cantidad_num = float(activo.get('cantidad', 0))
                    if tipo == 'TitulosPublicos':
                        valuacion = (cantidad_num * precio_unitario) / 100.0
                    else:
                        valuacion = cantidad_num * precio_unitario
                except (ValueError, TypeError):
                    pass
        mercado = titulo.get('mercado', 'BCBA')
        if simbolo:
            activos_dict[simbolo] = {
                'Valuación': valuacion,
                'Tipo': tipo,
                'mercado': mercado
            }
            valor_total += valuacion
            activos_para_historico.append({'simbolo': simbolo, 'mercado': mercado})

    # --- FIN NUEVO ---

    # --- NUEVO: Descarga asíncrona de series históricas antes de calcular métricas ---
    # Esto acelera el diagnóstico y la optimización
    try:
        fecha_hasta_diag = datetime.now().strftime('%Y-%m-%d')
        fecha_desde_diag = (datetime.now() - timedelta(days=252*1.5)).strftime('%Y-%m-%d')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        series_historicas_dict = loop.run_until_complete(
            obtener_series_historicas_en_paralelo(token_acceso, activos_para_historico, fecha_desde_diag, fecha_hasta_diag)
        )
        # Puedes usar series_historicas_dict para cálculos adicionales si lo deseas
    except Exception as e:
        st.warning(f"Error en descarga asíncrona de series históricas: {e}")
    # --- FIN NUEVO ---

    metricas_actual = calcular_metricas_portafolio(activos_dict, valor_total, token_acceso)
    cols = st.columns(4)
    cols[0].metric("Retorno Esperado", f"{metricas_actual.get('retorno_esperado_anual',0)*100:.2f}%")
    cols[1].metric("Riesgo (Volatilidad)", f"{metricas_actual.get('riesgo_anual',0)*100:.2f}%")
    cols[2].metric("Sharpe", f"{(metricas_actual.get('retorno_esperado_anual',0)/(metricas_actual.get('riesgo_anual',1e-6))):.2f}")
    cols[3].metric("Concentración", f"{metricas_actual.get('concentracion',0)*100:.1f}%")

    st.markdown("---")
    st.subheader("⚙️ Configuración de Universo de Optimización")
    universo = st.radio(
        "¿Con qué universo de activos desea optimizar?",
        ["Portafolio actual", "Universo aleatorio"],
        help="Puede optimizar con sus activos actuales o simular con un universo aleatorio por tipo/cantidad."
    )
    if universo == "Portafolio actual":
        universe_activos = [
            {'simbolo': a.get('titulo',{}).get('simbolo'),
             'mercado': a.get('titulo',{}).get('mercado'),
             'tipo': a.get('titulo',{}).get('tipo')}
            for a in activos_raw if a.get('titulo',{}).get('simbolo')
        ]
    else:
        st.info("Seleccione el tipo y cantidad de activos para el universo aleatorio")
        tipos = list(set([a.get('titulo',{}).get('tipo','Acción') for a in activos_raw]))
        tipo_sel = st.multiselect("Tipos de activo", tipos, default=tipos)
        cant = st.slider("Cantidad de activos aleatorios", 3, 15, 5)
        # Simulación simple: tomar random de los tipos seleccionados
        import random
        universe_activos = random.sample([
            {'simbolo': a.get('titulo',{}).get('simbolo'),
             'mercado': a.get('titulo',{}).get('mercado'),
             'tipo': a.get('titulo',{}).get('tipo')}
            for a in activos_raw if a.get('titulo',{}).get('tipo') in tipo_sel
        ], min(cant, len(activos_raw)))
        if not universe_activos:
            st.warning("No hay suficientes activos para el universo aleatorio seleccionado.")
            return

    fecha_desde = st.session_state.fecha_desde
    fecha_hasta = st.session_state.fecha_hasta
    st.info(f"Optimizando {len(universe_activos)} activos desde {fecha_desde} hasta {fecha_hasta}")

    # Automatizar todas las estrategias
    st.subheader("🚀 Ejecución Automática de Estrategias de Optimización")
    estrategias = [
        ('markowitz', 'Markowitz'),
        ('min-variance-l1', 'Min Var L1'),
        ('min-variance-l2', 'Min Var L2'),
        ('equi-weight', 'Pesos Iguales'),
        ('long-only', 'Solo Largos')
    ]
    target_sharpe = st.number_input("Sharpe objetivo (opcional, Markowitz)", min_value=0.0, max_value=3.0, value=0.8, step=0.01)
    st.caption("Si no es posible alcanzar el Sharpe exacto, se mostrará el portafolio más cercano.")

    # Cargar datos y preparar manager
    manager_inst = PortfolioManager(universe_activos, token_acceso, fecha_desde, fecha_hasta)
    if not manager_inst.load_data():
        st.error("No se pudieron cargar los datos históricos para optimización.")
        return

    resultados = {}
    for clave, nombre in estrategias:
        if clave == 'markowitz':
            # Mejorar lógica de Sharpe objetivo: buscar el retorno objetivo que más se aproxime al Sharpe deseado
            mejor_sharpe = -1e9
            mejor_result = None
            mejor_ret = None
            for ret in [x/100 for x in range(2, 25, 1)]:
                res = manager_inst.compute_portfolio(strategy='markowitz', target_return=ret)
                if not res or not hasattr(res, 'returns') or not hasattr(res, 'risk'):
                    continue
                sharpe = res.returns / (res.risk if res.risk else 1e-6)
                if abs(sharpe - target_sharpe) < abs(mejor_sharpe - target_sharpe):
                    mejor_sharpe = sharpe
                    mejor_result = res
                    mejor_ret = ret
            resultados[clave] = (mejor_result, mejor_sharpe, mejor_ret)
        else:
            res = manager_inst.compute_portfolio(strategy=clave)
            if res:
                sharpe = res.returns / (res.risk if res.risk else 1e-6)
                resultados[clave] = (res, sharpe, None)

    # Mostrar resultados
    st.markdown("---")
    st.subheader("📊 Resultados de Optimización y Comparación")
    cols = st.columns(len(estrategias)+1)
    # Métricas del portafolio actual
    cols[0].metric("Actual: Sharpe", f"{(metricas_actual.get('retorno_esperado_anual',0)/(metricas_actual.get('riesgo_anual',1e-6))):.2f}")
    cols[0].metric("Actual: Retorno", f"{metricas_actual.get('retorno_esperado_anual',0)*100:.2f}%")
    cols[0].metric("Actual: Riesgo", f"{metricas_actual.get('riesgo_anual',0)*100:.2f}%")
    for i, (clave, nombre) in enumerate(estrategias):
        res, sharpe, ret = resultados.get(clave, (None, None, None))
        if res:
            cols[i+1].metric(f"{nombre}\nSharpe", f"{sharpe:.2f}")
            cols[i+1].metric(f"{nombre}\nRetorno", f"{getattr(res,'returns',0)*100:.2f}%")
            cols[i+1].metric(f"{nombre}\nRiesgo", f"{getattr(res,'risk',0)*100:.2f}%")
            if clave == 'markowitz' and ret is not None:
                cols[i+1].caption(f"Retorno objetivo: {ret*100:.2f}%")
    st.markdown("---")

    # Gráficos y visualizaciones
    for clave, nombre in estrategias:
        res, sharpe, ret = resultados.get(clave, (None, None, None))
        if not res:
            continue
        st.markdown(f"#### {nombre}")
        # Histograma de retornos
        if hasattr(res, 'plot_histogram_streamlit'):
            st.markdown("**Distribución de Retornos**")
            fig = res.plot_histogram_streamlit()
            st.plotly_chart(fig, use_container_width=True)
        # Pie chart de pesos
        if hasattr(res, 'dataframe_allocation') and res.dataframe_allocation is not None:
            st.markdown("**Distribución de Pesos**")
            import plotly.graph_objects as go
            df = res.dataframe_allocation
            fig_pie = go.Figure(data=[go.Pie(labels=df['Activo'], values=df['Peso'], textinfo='label+percent', hole=0.4)])
            fig_pie.update_layout(title="Distribución Optimizada de Activos", template='plotly_white')
            st.plotly_chart(fig_pie, use_container_width=True)
        # Métricas
        st.write(f"Retorno esperado: {getattr(res,'returns',0)*100:.2f}% | Riesgo: {getattr(res,'risk',0)*100:.2f}% | Sharpe: {sharpe:.2f}")
        st.markdown("---")

    # Frontera eficiente
    st.subheader("📈 Frontera Eficiente y Portafolios Especiales")
    if st.checkbox("Mostrar Frontera Eficiente", value=True):
        portfolios, returns, volatilities = manager_inst.compute_efficient_frontier(target_return=0.08, include_min_variance=True)
        if portfolios and returns and volatilities:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=volatilities, y=returns, mode='lines+markers', name='Frontera Eficiente', line=dict(color='#0d6efd', width=3), marker=dict(size=6)))
            # Marcar portafolios especiales
            colores = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
            for i, (label, port) in enumerate(portfolios.items()):
                if port and hasattr(port, 'risk') and hasattr(port, 'returns'):
                    fig.add_trace(go.Scatter(x=[port.risk], y=[port.returns], mode='markers+text', name=label, marker=dict(color=colores[i%len(colores)], size=14, symbol='star'), text=[label], textposition='top center'))
            fig.update_layout(title='Frontera Eficiente del Portafolio', xaxis_title='Volatilidad Anual', yaxis_title='Retorno Anual', showlegend=True, template='plotly_white', height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No se pudo calcular la frontera eficiente.")

    # Comparación final
    st.subheader("🔬 Comparación Directa con Portafolio Actual")
    st.write("Se muestran las mejoras potenciales en retorno, riesgo y Sharpe respecto al portafolio actual.")
    df_comp = []
    for clave, nombre in estrategias:
        res, sharpe, _ = resultados.get(clave, (None, None, None))
        if res:
            df_comp.append({
                'Estrategia': nombre,
                'Retorno': getattr(res,'returns',0)*100,
                'Riesgo': getattr(res,'risk',0)*100,
                'Sharpe': sharpe,
                'Mejora Retorno (%)': (getattr(res,'returns',0)-metricas_actual.get('retorno_esperado_anual',0))*100,
                'Mejora Sharpe': sharpe-(metricas_actual.get('retorno_esperado_anual',0)/(metricas_actual.get('riesgo_anual',1e-6)))
            })
    if df_comp:
        import pandas as pd
        st.dataframe(pd.DataFrame(df_comp), use_container_width=True)

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
        "🔄 Rebalanceo"
    ])

    with tab1:
        portafolio = obtener_portafolio(token_acceso, id_cliente)
        if portafolio:
            mostrar_resumen_portafolio(portafolio, token_acceso)
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

if __name__ == "__main__":
    main()
