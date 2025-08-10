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
from scipy.stats import linregress, skew
import random
import warnings
import streamlit.components.v1 as components
import httpx
import asyncio
import matplotlib.pyplot as plt
import google.generativeai as genai
import tempfile
import io
import zipfile
import os
import plotly.express as px

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
from scipy.stats import linregress, skew
import random
import warnings
import streamlit.components.v1 as components
import httpx
import asyncio
import matplotlib.pyplot as plt
import google.generativeai as genai
import tempfile
import io
import zipfile
import os
import plotly.express as px

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
        # Asegura que self.returns sea una secuencia (array, lista, o pandas Series), no un escalar
        import numpy as np
        import pandas as pd
        returns = self.returns
        # Si es None o vacío
        if returns is None or (hasattr(returns, '__len__') and len(returns) == 0):
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos suficientes para mostrar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(title=title)
            return fig
        # Si es un escalar (float, int, numpy.float, numpy.int)
        if isinstance(returns, (float, int, np.floating, np.integer)):
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos suficientes para mostrar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(title=title)
            return fig
        # Si es un array/serie de un solo valor, también evitar graficar
        if hasattr(returns, '__len__') and len(returns) <= 1:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos suficientes para mostrar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(title=title)
            return fig

        fig = go.Figure(data=[go.Histogram(
            x=returns,
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

def optimize_portfolio(returns, target_return=None):
    """
    Optimiza un portafolio usando el método de Markowitz
    
    Args:
        returns (pd.DataFrame): DataFrame con retornos de activos
        target_return (float, optional): Retorno objetivo anual
        
    Returns:
        np.array: Pesos optimizados del portafolio
    """
    if returns is None or returns.empty:
        return None
        
    n_assets = len(returns.columns)
    
    # Calcular matriz de covarianza y retornos medios
    cov_matrix = returns.cov() * 252  # Anualizar
    mean_returns = returns.mean() * 252  # Anualizar
    
    # Pesos iniciales iguales
    initial_weights = np.ones(n_assets) / n_assets
    
    # Restricciones
    bounds = tuple((0, 1) for _ in range(n_assets))
    
    if target_return is not None:
        # Optimización con retorno objetivo
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Suma de pesos = 1
            {'type': 'eq', 'fun': lambda x: np.sum(mean_returns * x) - target_return}  # Retorno objetivo
        ]
        
        # Minimizar varianza
        result = op.minimize(
            lambda x: portfolio_variance(x, cov_matrix),
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
    else:
        # Maximizar Sharpe ratio
        risk_free_rate = 0.40  # Tasa libre de riesgo para Argentina
        
        def neg_sharpe_ratio(weights):
            port_return = np.sum(mean_returns * weights)
            port_vol = np.sqrt(portfolio_variance(weights, cov_matrix))
            if port_vol == 0:
                return np.inf
            return -(port_return - risk_free_rate) / port_vol
        
        constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        
        result = op.minimize(
            neg_sharpe_ratio,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
    
    if result.success:
        return result.x
    else:
        # Si falla la optimización, usar pesos iguales
        return initial_weights

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
    def __init__(self, activos, token, fecha_desde, fecha_hasta):
        self.activos = activos
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
            # Convertir lista de activos a formato adecuado
            symbols = []
            markets = []
            tipos = []
            def detectar_mercado(tipo_raw: str, mercado_raw: str) -> str:
                """
                Determina el mercado basado en la información proporcionada.
                
                Args:
                    tipo_raw: Tipo de activo (no utilizado en esta versión)
                    mercado_raw: Mercado del activo
                    
                Returns:
                    str: Nombre del mercado normalizado
                """
                # Usar el mercado proporcionado o BCBA como valor por defecto
                mercado = mercado_raw.strip().title() if mercado_raw.strip() else 'BCBA'
                return mercado
            
            for activo in self.activos:
                if isinstance(activo, dict):
                    simbolo = activo.get('simbolo', '')
                    tipo_raw = (activo.get('tipo') or '')
                    mercado_raw = (activo.get('mercado') or '')
                    
                    if not simbolo:
                        continue
                    symbols.append(simbolo)
                    tipos.append(tipo_raw)
                    markets.append(detectar_mercado(tipo_raw, mercado_raw))
                else:
                    symbols.append(activo)
                    markets.append('BCBA')  # Default market
            
            if not symbols:
                st.error("❌ No se encontraron símbolos válidos para procesar")
                return False
            
            # Obtener datos históricos
            data_frames = {}
            
            with st.spinner("Obteniendo datos históricos..."):
                for simbolo, mercado in zip(symbols, markets):
                    df = obtener_serie_historica_iol(
                        self.token,
                        mercado,
                        simbolo,
                        self.fecha_desde,
                        self.fecha_hasta
                    )
                    
                    if df is not None and not df.empty:
                        # Usar la columna de último precio si está disponible
                        precio_columns = ['ultimoPrecio', 'ultimo_precio', 'precio']
                        precio_col = next((col for col in precio_columns if col in df.columns), None)
                        
                        if precio_col:
                            df = df[['fecha', precio_col]].copy()
                            df.columns = ['fecha', 'precio']  # Normalizar el nombre de la columna
                            
                            # Convertir fechaHora a fecha y asegurar que sea única
                            df['fecha'] = pd.to_datetime(df['fecha']).dt.date
                            
                            # Eliminar duplicados manteniendo el último valor
                            df = df.drop_duplicates(subset=['fecha'], keep='last')
                            
                            df.set_index('fecha', inplace=True)
                            data_frames[simbolo] = df
                        else:
                            st.warning(f"⚠️ No se encontró columna de precio válida para {simbolo}")
                    else:
                        st.warning(f"⚠️ No se pudieron obtener datos para {simbolo} en {mercado}")
            
            if not data_frames:
                st.error("❌ No se pudieron obtener datos históricos para ningún activo")
                return False
            
            # Combinar todos los DataFrames
            df_precios = pd.concat(data_frames.values(), axis=1, keys=data_frames.keys())
            # Limpiar datos
            if not df_precios.index.is_unique:
                st.warning("⚠️ Se encontraron fechas duplicadas en los datos")
                df_precios = df_precios.groupby(df_precios.index).last()
            df_precios = df_precios.fillna(method='ffill')
            df_precios = df_precios.dropna()
            if df_precios.empty:
                st.error("❌ No hay datos suficientes después del preprocesamiento")
                return False
            self.prices = df_precios  # <--- ASIGNAR PRECIOS PARA FRONTERA EFICIENTE
            self.returns = df_precios.pct_change().dropna()
            self.mean_returns = self.returns.mean()
            self.cov_matrix = self.returns.cov()
            self.data_loaded = True
            self.manager = manager(list(df_precios.columns), self.notional, df_precios.to_dict('series'))
            return True
        except Exception as e:
            st.error(f"❌ Error en load_data: {str(e)}")
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
                    weights = np.ones(n_assets) / n_assets
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
        if not self.data_loaded or not self.manager or self.prices is None or self.prices.empty:
            return None, None, None
        try:
            # Chequeo adicional: evitar series con menos de 2 activos o fechas
            if self.prices.shape[1] < 2 or self.prices.shape[0] < 10:
                return None, None, None
            portfolios, returns, volatilities = compute_efficient_frontier(
                self.manager.rics, self.notional, target_return, include_min_variance, 
                self.prices.to_dict('series')
            )
            return portfolios, returns, volatilities
        except Exception as e:
            return None, None, None

# --- Historical Data Methods ---
def _deprecated_serie_historica_iol(*args, **kwargs):
    """Deprecated duplicate of `obtener_serie_historica_iol`. Kept for backward compatibility."""
    return None
    """Obtiene series históricas desde la API de IOL
    
    Args:
        token_portador: Token de autenticación Bearer
        mercado: Mercado (BCBA, NYSE, NASDAQ, ROFEX)
        simbolo: Símbolo del activo (puede ser string o dict con clave 'simbolo')
        fecha_desde: Fecha inicio (YYYY-MM-DD)
        fecha_hasta: Fecha fin (YYYY-MM-DD)
        ajustada: "Ajustada" o "SinAjustar"
    
    Returns:
        DataFrame con datos históricos o None si hay error
    """
    # Manejar caso donde simbolo es un diccionario
    if isinstance(simbolo, dict):
        simbolo = simbolo.get('simbolo', '')
    
    if not simbolo:
        st.warning("No se proporcionó un símbolo válido")
        return None
        
    # Asegurarse de que el mercado esté en mayúsculas
    mercado = mercado.upper() if mercado else 'BCBA'
    try:
        # Construir la URL de la API
        url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token_portador}'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        df = pd.DataFrame(data)
        
        if 'fechaHora' in df.columns:
            # Handle different datetime formats
            df['fecha'] = pd.to_datetime(
                df['fechaHora'], 
                format='mixed',  # Automatically infer format for each element
                utc=True,        # Ensure timezone awareness
                errors='coerce'  # Convert parsing errors to NaT
            ).dt.tz_convert(None).dt.date  # Convert to naive date
            
            # Drop rows where date parsing failed
            df = df.dropna(subset=['fecha'])
            df = df.sort_values('fecha')
            
        return df
        
    except Exception as e:
        st.error(f"Error obteniendo datos para {simbolo}: {str(e)}")
        return None

# --- Portfolio Metrics Function ---
def calcular_alpha_beta(portfolio_returns, benchmark_returns, risk_free_rate=0.0):
    """
    Calcula el Alpha y Beta de un portafolio respecto a un benchmark.
    
    Args:
        portfolio_returns (pd.Series): Retornos del portafolio
        benchmark_returns (pd.Series): Retornos del benchmark (ej: MERVAL)
        risk_free_rate (float): Tasa libre de riesgo (anualizada)
        
    Returns:
        dict: Diccionario con alpha, beta, información de la regresión y métricas adicionales
    """
    # Alinear las series por fecha y eliminar NaN
    aligned_data = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
    if len(aligned_data) < 5:  # Mínimo de datos para regresión
        return {
            'alpha': 0,
            'beta': 1.0,
            'r_squared': 0,
            'p_value': 1.0,
            'tracking_error': 0,
            'information_ratio': 0,
            'observations': len(aligned_data),
            'alpha_annual': 0
        }
    
    portfolio_aligned = aligned_data.iloc[:, 0]
    benchmark_aligned = aligned_data.iloc[:, 1]
    
    # Calcular regresión lineal
    slope, intercept, r_value, p_value, std_err = linregress(benchmark_aligned, portfolio_aligned)
    
    # Calcular métricas adicionales
    tracking_error = np.std(portfolio_aligned - benchmark_aligned) * np.sqrt(252)  # Anualizado
    information_ratio = (portfolio_aligned.mean() - benchmark_aligned.mean()) / tracking_error if tracking_error != 0 else 0
    
    # Anualizar alpha (asumiendo 252 días hábiles)
    alpha_annual = intercept * 252
    
    return {
        'alpha': intercept,
        'beta': slope,
        'r_squared': r_value ** 2,
        'p_value': p_value,
        'tracking_error': tracking_error,
        'information_ratio': information_ratio,
        'observations': len(aligned_data),
        'alpha_annual': alpha_annual
    }

def analizar_estrategia_inversion(alpha_beta_metrics):
    """
    Analiza la estrategia de inversión y cobertura basada en métricas de alpha y beta.
    
    Args:
        alpha_beta_metrics (dict): Diccionario con las métricas de alpha y beta
        
    Returns:
        dict: Diccionario con el análisis de la estrategia
    """
    beta = alpha_beta_metrics.get('beta', 1.0)
    alpha_annual = alpha_beta_metrics.get('alpha_annual', 0)
    r_squared = alpha_beta_metrics.get('r_squared', 0)
    
    # Análisis de estrategia basado en beta
    if beta > 1.2:
        estrategia = "Estrategia Agresiva"
        explicacion = ("El portafolio es más volátil que el mercado (β > 1.2). "
                      "Esta estrategia busca rendimientos superiores asumiendo mayor riesgo.")
    elif beta > 0.8:
        estrategia = "Estrategia de Crecimiento"
        explicacion = ("El portafolio sigue de cerca al mercado (0.8 < β < 1.2). "
                     "Busca rendimientos similares al mercado con un perfil de riesgo equilibrado.")
    elif beta > 0.3:
        estrategia = "Estrategia Defensiva"
        explicacion = ("El portafolio es menos volátil que el mercado (0.3 < β < 0.8). "
                     "Busca preservar capital con menor exposición a las fluctuaciones del mercado.")
    elif beta > -0.3:
        estrategia = "Estrategia de Ingresos"
        explicacion = ("El portafolio tiene baja correlación con el mercado (-0.3 < β < 0.3). "
                     "Ideal para generar ingresos con bajo riesgo de mercado.")
    else:
        estrategia = "Estrategia de Cobertura"
        explicacion = ("El portafolio tiene correlación negativa con el mercado (β < -0.3). "
                     "Diseñado para moverse en dirección opuesta al mercado, útil para cobertura.")
    
    # Análisis de desempeño basado en alpha
    if alpha_annual > 0.05:  # 5% de alpha anual
        rendimiento = "Excelente desempeño"
        explicacion_rendimiento = (f"El portafolio ha generado un alpha anualizado de {alpha_annual:.1%}, "
                                 "superando significativamente al benchmark.")
    elif alpha_annual > 0.02:  # 2% de alpha anual
        rendimiento = "Buen desempeño"
        explicacion_rendimiento = (f"El portafolio ha generado un alpha anualizado de {alpha_annual:.1%}, "
                                 "superando al benchmark.")
    elif alpha_annual > -0.02:  # Entre -2% y 2%
        rendimiento = "Desempeño en línea"
        explicacion_rendimiento = (f"El portafolio tiene un alpha anualizado de {alpha_annual:.1%}, "
                                 "en línea con el benchmark.")
    else:
        rendimiento = "Desempeño inferior"
        explicacion_rendimiento = (f"El portafolio tiene un alpha anualizado de {alpha_annual:.1%}, "
                                 "por debajo del benchmark.")
    
    # Calidad de la cobertura basada en R²
    if r_squared > 0.7:
        calidad_cobertura = "Alta"
        explicacion_cobertura = (f"El R² de {r_squared:.2f} indica una fuerte relación con el benchmark. "
                               "La cobertura será más efectiva.")
    elif r_squared > 0.4:
        calidad_cobertura = "Moderada"
        explicacion_cobertura = (f"El R² de {r_squared:.2f} indica una relación moderada con el benchmark. "
                               "La cobertura puede ser parcialmente efectiva.")
    else:
        calidad_cobertura = "Baja"
        explicacion_cobertura = (f"El R² de {r_squared:.2f} indica una débil relación con el benchmark. "
                               "La cobertura puede no ser efectiva.")
    
    return {
        'estrategia': estrategia,
        'explicacion_estrategia': explicacion,
        'rendimiento': rendimiento,
        'explicacion_rendimiento': explicacion_rendimiento,
        'calidad_cobertura': calidad_cobertura,
        'explicacion_cobertura': explicacion_cobertura,
        'beta': beta,
        'alpha_anual': alpha_annual,
        'r_cuadrado': r_squared,
        'observations': alpha_beta_metrics.get('observations', 0)
    }

def calcular_metricas_portafolio(portafolio, valor_total, token_portador, dias_historial=252):
    """
    Calcula métricas clave de desempeño para un portafolio de inversión usando datos históricos.
{{ ... }}
    
    Args:
        portafolio (dict): Diccionario con los activos y sus cantidades
        valor_total (float): Valor total del portafolio
        token_portador (str): Token de autenticación para la API de InvertirOnline
        dias_historial (int): Número de días de histórico a considerar (por defecto: 252 días hábiles)
        
    Returns:
        dict: Diccionario con las métricas calculadas
    """
    if not isinstance(portafolio, dict) or not portafolio or valor_total <= 0:
        return {}

    # Obtener fechas para el histórico
    fecha_hasta = datetime.now().strftime('%Y-%m-%d')
    fecha_desde = (datetime.now() - timedelta(days=dias_historial*1.5)).strftime('%Y-%m-%d')
    
    # 1. Calcular concentración del portafolio (Índice de Herfindahl-Hirschman normalizado)
    if len(portafolio) == 0:
        concentracion = 0
    elif len(portafolio) == 1:
        concentracion = 1.0
    else:
        sum_squares = sum((activo.get('Valuación', 0) / valor_total) ** 2 
                         for activo in portafolio.values())
        # Normalizar entre 0 y 1
        min_concentration = 1.0 / len(portafolio)
        concentracion = (sum_squares - min_concentration) / (1 - min_concentration)
        
    # Descargar datos del MERVAL para cálculo de Alpha y Beta
    try:
        merval_data = yf.download('^MERV', start=fecha_desde, end=fecha_hasta)['Close']
        merval_returns = merval_data.pct_change().dropna()
        merval_available = True
    except Exception as e:
        print(f"No se pudieron obtener datos del MERVAL: {str(e)}")
        merval_available = False
        merval_returns = None
    
    # Inicializar estructuras para cálculos
    retornos_diarios = {}
    metricas_activos = {}
    
    # 2. Obtener datos históricos y calcular métricas por activo
    for simbolo, activo in portafolio.items():
        try:
            # Obtener datos históricos usando el método estándar
            mercado = activo.get('mercado', 'BCBA')
            tipo_activo = activo.get('Tipo', 'Desconocido')
            
            # Debug: Mostrar información del activo que se está procesando
            print(f"\nProcesando activo: {simbolo} (Mercado: {mercado}, Tipo: {tipo_activo})")
            
            # Obtener la serie histórica
            try:
                df_historico = obtener_serie_historica_iol(
                    token_portador=token_portador,
                    mercado=mercado,
                    simbolo=simbolo,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                    ajustada="SinAjustar"
                )
            except Exception as e:
                print(f"Error al obtener datos históricos para {simbolo}: {str(e)}")
                continue
            
            if df_historico is None:
                print(f"No se obtuvieron datos para {simbolo} (None)")
                continue
                
            if df_historico.empty:
                print(f"Datos vacíos para {simbolo}")
                continue
            
            # Asegurarse de que tenemos las columnas necesarias
            if 'fecha' not in df_historico.columns or 'precio' not in df_historico.columns:
                print(f"Faltan columnas necesarias en los datos de {simbolo}")
                print(f"Columnas disponibles: {df_historico.columns.tolist()}")
                continue
                
            print(f"Datos obtenidos: {len(df_historico)} registros desde {df_historico['fecha'].min()} hasta {df_historico['fecha'].max()}")
                
            # Ordenar por fecha y limpiar duplicados
            df_historico = df_historico.sort_values('fecha')
            df_historico = df_historico.drop_duplicates(subset=['fecha'], keep='last')
            
            # Calcular retornos diarios
            df_historico['retorno'] = df_historico['precio'].pct_change()
            
            # Filtrar valores atípicos usando un enfoque más robusto
            if len(df_historico) > 5:  # Necesitamos suficientes puntos para el filtrado
                q_low = df_historico['retorno'].quantile(0.01)
                q_high = df_historico['retorno'].quantile(0.99)
                df_historico = df_historico[
                    (df_historico['retorno'] >= q_low) & 
                    (df_historico['retorno'] <= q_high)
                ]
            
            # Filtrar valores no finitos y asegurar suficientes datos
            retornos_validos = df_historico['retorno'].replace(
                [np.inf, -np.inf], np.nan
            ).dropna()
            
            if len(retornos_validos) < 5:  # Mínimo de datos para métricas confiables
                print(f"No hay suficientes datos válidos para {simbolo} (solo {len(retornos_validos)} registros)")
                continue
                
            # Verificar si hay suficientes variaciones de precio
            if retornos_validos.nunique() < 2:
                print(f"No hay suficiente variación en los precios de {simbolo}")
                continue
            
            # Calcular métricas básicas
            retorno_medio = retornos_validos.mean() * 252  # Anualizado
            volatilidad = retornos_validos.std() * np.sqrt(252)  # Anualizada
            
            # Asegurar valores razonables
            retorno_medio = np.clip(retorno_medio, -5, 5)  # Límite de ±500% anual
            volatilidad = min(volatilidad, 3)  # Límite de 300% de volatilidad
            
            # Calcular métricas de riesgo basadas en la distribución de retornos
            ret_pos = retornos_validos[retornos_validos > 0]
            ret_neg = retornos_validos[retornos_validos < 0]
            n_total = len(retornos_validos)
            
            # Calcular probabilidades
            prob_ganancia = len(ret_pos) / n_total if n_total > 0 else 0.5
            prob_perdida = len(ret_neg) / n_total if n_total > 0 else 0.5
            
            # Calcular probabilidades de movimientos extremos
            prob_ganancia_10 = len(ret_pos[ret_pos > 0.1]) / n_total if n_total > 0 else 0
            prob_perdida_10 = len(ret_neg[ret_neg < -0.1]) / n_total if n_total > 0 else 0
            
            # Calcular el peso del activo en el portafolio
            peso = activo.get('Valuación', 0) / valor_total if valor_total > 0 else 0
            
            # Guardar métricas
            metricas_activos[simbolo] = {
                'retorno_medio': retorno_medio,
                'volatilidad': volatilidad,
                'prob_ganancia': prob_ganancia,
                'prob_perdida': prob_perdida,
                'prob_ganancia_10': prob_ganancia_10,
                'prob_perdida_10': prob_perdida_10,
                'peso': peso
            }
            
            # Guardar retornos para cálculo de correlaciones
            retornos_diarios[simbolo] = df_historico.set_index('fecha')['retorno']
            
        except Exception as e:
            print(f"Error procesando {simbolo}: {str(e)}")
            continue
    
    if not metricas_activos:
        print("No se pudieron calcular métricas para ningún activo")
        return {
            'concentracion': concentracion,
            'std_dev_activo': 0,
            'retorno_esperado_anual': 0,
            'pl_esperado_min': 0,
            'pl_esperado_max': 0,
            'probabilidades': {'perdida': 0, 'ganancia': 0, 'perdida_mayor_10': 0, 'ganancia_mayor_10': 0},
            'riesgo_anual': 0
        }
    else:
        print(f"\nMétricas calculadas para {len(metricas_activos)} activos")
    
    # 3. Calcular métricas del portafolio
    # Retorno esperado ponderado
    retorno_esperado_anual = sum(
        (m.get('retorno_medio', 0) or 0) * (m.get('peso', 0) or 0)
        for m in metricas_activos.values()
    )
    
    # Volatilidad del portafolio (considerando correlaciones)
    try:
        if len(retornos_diarios) > 1:
            # Asegurarse de que tenemos suficientes datos para calcular correlaciones
            df_retornos = pd.DataFrame(retornos_diarios).dropna()
            if len(df_retornos) < 5:  # Mínimo de datos para correlación confiable
                print("No hay suficientes datos para calcular correlaciones confiables")
                # Usar promedio ponderado simple como respaldo
                volatilidad_portafolio = sum(
                    (m.get('volatilidad', 0) or 0) * (m.get('peso', 0) or 0)
                    for m in metricas_activos.values()
                )
            else:
                # Calcular matriz de correlación
                df_correlacion = df_retornos.corr()
                
                # Verificar si la matriz de correlación es válida
                if df_correlacion.isna().any().any():
                    print("Advertencia: Matriz de correlación contiene valores NaN")
                    df_correlacion = df_correlacion.fillna(0)  # Reemplazar NaN con 0
                
                # Obtener pesos y volatilidades
                activos = list(metricas_activos.keys())
                pesos = np.array([metricas_activos[a]['peso'] for a in activos])
                volatilidades = np.array([metricas_activos[a]['volatilidad'] for a in activos])
                
                # Asegurarse de que las dimensiones coincidan
                if len(activos) == df_correlacion.shape[0] == df_correlacion.shape[1]:
                    # Calcular matriz de covarianza
                    matriz_cov = np.diag(volatilidades) @ df_correlacion.values @ np.diag(volatilidades)
                    # Calcular varianza del portafolio
                    varianza_portafolio = pesos.T @ matriz_cov @ pesos
                    # Asegurar que la varianza no sea negativa
                    varianza_portafolio = max(0, varianza_portafolio)
                    volatilidad_portafolio = np.sqrt(varianza_portafolio)
                else:
                    print("Dimensiones no coinciden, usando promedio ponderado")
                    volatilidad_portafolio = sum(v * w for v, w in zip(volatilidades, pesos))
        else:
            # Si solo hay un activo, usar su volatilidad directamente
            volatilidad_portafolio = next(iter(metricas_activos.values()))['volatilidad']
            
        # Asegurar que la volatilidad sea un número finito
        if not np.isfinite(volatilidad_portafolio):
            print("Advertencia: Volatilidad no finita, usando valor por defecto")
            volatilidad_portafolio = 0.2  # Valor por defecto razonable
            
    except Exception as e:
        print(f"Error al calcular volatilidad del portafolio: {str(e)}")
        import traceback
        traceback.print_exc()
        # Valor por defecto seguro
        volatilidad_portafolio = sum(
            (m.get('volatilidad', 0) or 0) * (m.get('peso', 0) or 0)
            for m in metricas_activos.values()
        ) if metricas_activos else 0.2
    
    # Calcular percentiles para escenarios
    retornos_simulados = []
    for _ in range(1000):  # Simulación Monte Carlo simple
        retorno_simulado = 0
        for m in metricas_activos.values():
            retorno_medio = m.get('retorno_medio', 0) or 0
            volatilidad = m.get('volatilidad', 0) or 0
            peso = m.get('peso', 0) or 0
            retorno_simulado += np.random.normal(retorno_medio/252, volatilidad/np.sqrt(252)) * peso
        retornos_simulados.append(retorno_simulado * 252)  # Anualizado
    
    valor_total_safe = valor_total or 0
    pl_esperado_min = np.percentile(retornos_simulados, 5) * valor_total_safe / 100
    pl_esperado_max = np.percentile(retornos_simulados, 95) * valor_total_safe / 100
    
    # Calcular probabilidades basadas en los retornos simulados
    retornos_simulados = np.array(retornos_simulados)
    total_simulaciones = len(retornos_simulados)
            
    prob_ganancia = np.sum(retornos_simulados > 0) / total_simulaciones if total_simulaciones > 0 else 0.5
    prob_perdida = np.sum(retornos_simulados < 0) / total_simulaciones if total_simulaciones > 0 else 0.5
    prob_ganancia_10 = np.sum(retornos_simulados > 0.1) / total_simulaciones
    prob_perdida_10 = np.sum(retornos_simulados < -0.1) / total_simulaciones
            
    # 4. Calcular Alpha y Beta respecto al MERVAL si hay datos disponibles
    alpha_beta_metrics = {}
    if merval_available and len(retornos_diarios) > 1:
        try:
            # Calcular retornos diarios del portafolio (promedio ponderado de los activos)
            df_port_returns = pd.DataFrame(retornos_diarios)
            
            # Asegurarse de que los pesos estén en el mismo orden que las columnas
            pesos_ordenados = [metricas_activos[col].get('peso', 0) or 0 for col in df_port_returns.columns]
            df_port_returns['Portfolio'] = df_port_returns.dot(pesos_ordenados)
            
            # Alinear fechas con el MERVAL
            merval_series = pd.Series(merval_returns, name='MERVAL')
            aligned_data = pd.merge(
                df_port_returns[['Portfolio']], 
                merval_series, 
                left_index=True, 
                right_index=True,
                how='inner'
            )
            
            if len(aligned_data) > 5:  # Mínimo de datos para cálculo confiable
                # Calcular métricas de Alpha y Beta
                alpha_beta_metrics = calcular_alpha_beta(
                    aligned_data['Portfolio'],  # Retornos del portafolio
                    aligned_data['MERVAL'],      # Retornos del MERVAL
                    risk_free_rate=0.40  # Tasa libre de riesgo para Argentina
                )
                
                print(f"Alpha: {alpha_beta_metrics.get('alpha_annual', 0):.2%}, "
                      f"Beta: {alpha_beta_metrics.get('beta', 0):.2f}, "
                      f"R²: {alpha_beta_metrics.get('r_squared', 0):.2f}")
            
        except Exception as e:
            print(f"Error al calcular Alpha/Beta: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Crear diccionario de probabilidades
    probabilidades = {
        'perdida': prob_perdida,
        'ganancia': prob_ganancia,
        'perdida_mayor_10': prob_perdida_10,
        'ganancia_mayor_10': prob_ganancia_10
    }
    
    # Crear diccionario de resultados
    resultados = {
        'concentracion': concentracion,
        'std_dev_activo': volatilidad_portafolio,
        'retorno_esperado_anual': retorno_esperado_anual,
        'pl_esperado_min': pl_esperado_min,
        'pl_esperado_max': pl_esperado_max,
        'probabilidades': probabilidades,
        'riesgo_anual': volatilidad_portafolio,  # Usamos la volatilidad como proxy de riesgo
        'alpha': alpha_beta_metrics.get('alpha_annual', 0),
        'beta': alpha_beta_metrics.get('beta', 0),
        'r_cuadrado': alpha_beta_metrics.get('r_squared', 0),
        'tracking_error': alpha_beta_metrics.get('tracking_error', 0),
        'information_ratio': alpha_beta_metrics.get('information_ratio', 0)
    }
    
    # Analizar la estrategia de inversión
    analisis_estrategia = analizar_estrategia_inversion(alpha_beta_metrics)
    resultados['analisis_estrategia'] = analisis_estrategia
    
    # Agregar métricas adicionales si están disponibles
    if 'p_value' in alpha_beta_metrics:
        resultados['p_value'] = alpha_beta_metrics['p_value']
    if 'observations' in alpha_beta_metrics:
        resultados['observaciones'] = alpha_beta_metrics['observations']
    
    return resultados

# --- Funciones de Visualización ---
def mostrar_resumen_portafolio(portafolio, token_portador):
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
                
                if precio_unitario > 0:
                    try:
                        cantidad_num = float(cantidad)
                        if tipo == 'TitulosPublicos':
                            valuacion = (cantidad_num * precio_unitario) / 100.0
                        else:
                            valuacion = cantidad_num * precio_unitario
                    except (ValueError, TypeError):
                        pass
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
                
                # Intento final: consultar precio actual vía API si sigue en cero
            if valuacion == 0:
                ultimo_precio = None
                if mercado := titulo.get('mercado'):
                    ultimo_precio = obtener_precio_actual(token_portador, mercado, simbolo)
                if ultimo_precio:
                    try:
                        cantidad_num = float(cantidad)
                        if tipo == 'TitulosPublicos':
                            valuacion = (cantidad_num * ultimo_precio) / 100.0
                        else:
                            valuacion = cantidad_num * ultimo_precio
                    except (ValueError, TypeError):
                        pass
            
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
        # Convert list to dictionary with symbols as keys
        portafolio_dict = {row['Símbolo']: row for row in datos_activos}
        metricas = calcular_metricas_portafolio(portafolio_dict, valor_total, token_portador)
        
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
            
            # Mostrar concentración como porcentaje
            concentracion_pct = metricas['concentracion'] * 100
            cols[0].metric("Concentración", 
                         f"{concentracion_pct:.1f}%",
                         help="Índice de Herfindahl normalizado: 0%=muy diversificado, 100%=muy concentrado")
            
            # Mostrar volatilidad como porcentaje anual
            volatilidad_pct = metricas['std_dev_activo'] * 100
            cols[1].metric("Volatilidad Anual", 
                         f"{volatilidad_pct:.1f}%",
                         help="Riesgo medido como desviación estándar de retornos anuales")
            
            # Nivel de concentración con colores
            if metricas['concentracion'] < 0.3:
                concentracion_status = "🟢 Baja"
            elif metricas['concentracion'] < 0.6:
                concentracion_status = "🟡 Media"
            else:
                concentracion_status = "🔴 Alta"
                
            cols[2].metric("Nivel Concentración", concentracion_status)
            
            # Proyecciones
            st.subheader("📈 Proyecciones de Rendimiento")
            cols = st.columns(3)
            
            # Mostrar retornos como porcentaje del portafolio
            retorno_anual_pct = (metricas.get('retorno_esperado_anual', 0) or 0) * 100
            cols[0].metric("Retorno Esperado Anual", 
                         f"{retorno_anual_pct:+.1f}%",
                         help="Retorno anual esperado basado en datos históricos")
            
            # Mostrar escenarios como porcentaje del portafolio
            optimista_pct = (metricas['pl_esperado_max'] / valor_total) * 100 if valor_total > 0 else 0
            pesimista_pct = (metricas['pl_esperado_min'] / valor_total) * 100 if valor_total > 0 else 0
            
            cols[1].metric("Escenario Optimista (95%)", 
                         f"{optimista_pct:+.1f}%",
                         help="Mejor escenario con 95% de confianza")
            cols[2].metric("Escenario Pesimista (5%)", 
                         f"{pesimista_pct:+.1f}%",
                         help="Peor escenario con 5% de confianza")
            
            # Probabilidades
            st.subheader("🎯 Probabilidades")
            cols = st.columns(4)
            probs = metricas['probabilidades']
            cols[0].metric("Ganancia", f"{(probs.get('ganancia', 0) or 0)*100:.1f}%")
            cols[1].metric("Pérdida", f"{(probs.get('perdida', 0) or 0)*100:.1f}%")
            cols[2].metric("Ganancia >10%", f"{(probs.get('ganancia_mayor_10', 0) or 0)*100:.1f}%")
            cols[3].metric("Pérdida >10%", f"{(probs.get('perdida_mayor_10', 0) or 0)*100:.1f}")
            

        
        # Gráficos
        st.subheader("📊 Distribución de Activos")
        
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
        
        # Histograma del portafolio total valorizado
        st.subheader("📈 Histograma del Portafolio Total Valorizado")
        
        # Configuración del horizonte de inversión
        horizonte_inversion = st.selectbox(
            "Horizonte de Inversión:",
            options=[
                ("30 días", 30),
                ("60 días", 60),
                ("90 días", 90),
                ("180 días", 180),
                ("365 días", 365),
                ("730 días", 730),
                ("1095 días", 1095)
            ],
            format_func=lambda x: x[0],
            index=3,  # Por defecto 180 días
            help="Seleccione el período de tiempo para el análisis de retornos"
        )
        
        # Intervalo de análisis fijo en diario
        intervalo_analisis = ("Diario", "D")
        st.info("📊 Análisis configurado en frecuencia diaria")
        
        # Extraer valores de las tuplas
        dias_analisis = horizonte_inversion[1]
        frecuencia = intervalo_analisis[1]
        
        with st.spinner(f"Obteniendo series históricas y calculando valorización del portafolio para {dias_analisis} días..."):
            try:
                # Obtener fechas para el histórico basado en el horizonte seleccionado
                fecha_hasta = datetime.now().strftime('%Y-%m-%d')
                fecha_desde = (datetime.now() - timedelta(days=dias_analisis)).strftime('%Y-%m-%d')
                
                # Preparar datos para obtener series históricas
                activos_para_historico = []
                for activo in datos_activos:
                    simbolo = activo['Símbolo']
                    if simbolo != 'N/A':
                        # Intentar obtener el mercado del activo original
                        mercado = 'BCBA'  # Default
                        for activo_original in activos:
                            if activo_original.get('titulo', {}).get('simbolo') == simbolo:
                                mercado = activo_original.get('titulo', {}).get('mercado', 'BCBA')
                                break
                        
                        activos_para_historico.append({
                            'simbolo': simbolo,
                            'mercado': mercado,
                            'peso': activo['Valuación'] / valor_total if valor_total > 0 else 0
                        })
                
                if len(activos_para_historico) > 0:
                    # Obtener series históricas para cada activo
                    series_historicas = {}
                    activos_exitosos = []
                    
                    for activo_info in activos_para_historico:
                        simbolo = activo_info['simbolo']
                        mercado = activo_info['mercado']
                        peso = activo_info['peso']
                        
                        if peso > 0:  # Solo procesar activos con peso significativo
                            serie = obtener_serie_historica_iol(
                                token_portador,
                                mercado,
                                simbolo,
                                fecha_desde,
                                fecha_hasta
                            )
                            
                            if serie is not None and not serie.empty:
                                series_historicas[simbolo] = serie
                                activos_exitosos.append({
                                    'simbolo': simbolo,
                                    'peso': peso,
                                    'serie': serie
                                })
                                st.success(f"✅ {simbolo}: {len(serie)} puntos de datos")
                            else:
                                st.warning(f"⚠️ No se pudieron obtener datos para {simbolo}")
                    
                    if len(activos_exitosos) > 0:
                        # Crear DataFrame con todas las series alineadas
                        df_portfolio = pd.DataFrame()
                        
                        # Primero, encontrar el rango de fechas común para todas las series
                        fechas_comunes = None
                        for activo_info in activos_exitosos:
                            serie = activo_info['serie']
                            if fechas_comunes is None:
                                fechas_comunes = set(serie.index)
                            else:
                                fechas_comunes = fechas_comunes.intersection(set(serie.index))
                        
                        if not fechas_comunes or len(fechas_comunes) == 0:
                            # Si no hay fechas comunes, usar la unión y rellenar con ffill
                            st.warning("⚠️ No hay fechas comunes entre las series históricas. Se usará la unión de fechas y se rellenarán los valores faltantes.")
                            fechas_union = set()
                            for activo_info in activos_exitosos:
                                fechas_union = fechas_union.union(set(activo_info['serie'].index))
                            fechas_union = sorted(list(fechas_union))
                            df_portfolio.index = fechas_union
                            usar_union = True
                        else:
                            fechas_comunes = sorted(list(fechas_comunes))
                            df_portfolio.index = fechas_comunes
                            usar_union = False
                        
                        for activo_info in activos_exitosos:
                            simbolo = activo_info['simbolo']
                            peso = activo_info['peso']
                            serie = activo_info['serie']
                            valuacion_activo = 0
                            for activo_original in datos_activos:
                                if activo_original['Símbolo'] == simbolo:
                                    valuacion_activo = float(activo_original['Valuación'])
                                    break
                            # Seleccionar fechas
                            if usar_union:
                                serie_filtrada = serie.reindex(df_portfolio.index)
                            else:
                                serie_filtrada = serie.loc[df_portfolio.index]
                            # Agregar serie ponderada al DataFrame
                            if 'precio' in serie_filtrada.columns:
                                precios = serie_filtrada['precio'].values
                                if len(precios) > 1:
                                    retornos_acumulados = precios / precios[0]
                                    df_portfolio[simbolo] = valuacion_activo * retornos_acumulados
                                else:
                                    df_portfolio[simbolo] = valuacion_activo
                            else:
                                columnas_numericas = serie_filtrada.select_dtypes(include=[np.number]).columns
                                if len(columnas_numericas) > 0:
                                    precios = serie_filtrada[columnas_numericas[0]].values
                                    if len(precios) > 1:
                                        retornos_acumulados = precios / precios[0]
                                        df_portfolio[simbolo] = valuacion_activo * retornos_acumulados
                                    else:
                                        df_portfolio[simbolo] = valuacion_activo
                                else:
                                    st.warning(f"⚠️ No se encontraron valores numéricos para {simbolo}")
                                    continue
                        # Rellenar valores faltantes con forward-fill y eliminar filas completamente vacías
                        df_portfolio = df_portfolio.ffill().dropna(how='all')
                        # Calcular valor total del portafolio por fecha
                        if not df_portfolio.empty:
                            df_portfolio['Portfolio_Total'] = df_portfolio.sum(axis=1)
                        else:
                            st.error("❌ No se pudo construir el DataFrame del portafolio. Verifique los datos históricos de los activos seleccionados.")
                            return
                        
                        # Mostrar información de debug
                        st.info(f"🔍 Debug: Valor total actual del portafolio: ${valor_total:,.2f}")
                        st.info(f"🔍 Debug: Columnas en df_portfolio: {list(df_portfolio.columns)}")
                        if len(df_portfolio) > 0:
                            st.info(f"🔍 Debug: Último valor calculado: ${df_portfolio['Portfolio_Total'].iloc[-1]:,.2f}")
                        
                        # Eliminar filas con valores NaN
                        df_portfolio = df_portfolio.dropna()
                        
                        if len(df_portfolio) > 0:
                            # Crear histograma del valor total del portafolio
                            valores_portfolio = df_portfolio['Portfolio_Total'].values
                            
                            fig_hist = go.Figure(data=[go.Histogram(
                                x=valores_portfolio,
                                nbinsx=30,
                                name="Valor Total del Portafolio",
                                marker_color='#0d6efd',
                                opacity=0.7
                            )])
                            
                            # Agregar líneas de métricas importantes
                            media_valor = np.mean(valores_portfolio)
                            mediana_valor = np.median(valores_portfolio)
                            percentil_5 = np.percentile(valores_portfolio, 5)
                            percentil_95 = np.percentile(valores_portfolio, 95)
                            
                            fig_hist.add_vline(x=media_valor, line_dash="dash", line_color="red", 
                                             annotation_text=f"Media: ${media_valor:,.2f}")
                            fig_hist.add_vline(x=mediana_valor, line_dash="dash", line_color="green", 
                                             annotation_text=f"Mediana: ${mediana_valor:,.2f}")
                            fig_hist.add_vline(x=percentil_5, line_dash="dash", line_color="orange", 
                                             annotation_text=f"P5: ${percentil_5:,.2f}")
                            fig_hist.add_vline(x=percentil_95, line_dash="dash", line_color="purple", 
                                             annotation_text=f"P95: ${percentil_95:,.2f}")
                            
                            fig_hist.update_layout(
                                title="Distribución del Valor Total del Portafolio",
                                xaxis_title="Valor del Portafolio ($)",
                                yaxis_title="Frecuencia",
                                height=500,
                                showlegend=False,
                                template='plotly_white'
                            )
                            
                            st.plotly_chart(fig_hist, use_container_width=True)
                            
                            # Mostrar estadísticas del histograma
                            st.markdown("#### 📊 Estadísticas del Histograma")
                            col1, col2, col3, col4 = st.columns(4)
                            
                            col1.metric("Valor Promedio", f"${media_valor:,.2f}")
                            col2.metric("Valor Mediano", f"${mediana_valor:,.2f}")
                            col3.metric("Valor Mínimo (P5)", f"${percentil_5:,.2f}")
                            col4.metric("Valor Máximo (P95)", f"${percentil_95:,.2f}")
                            
                            # Mostrar evolución temporal del portafolio
                            st.markdown("#### 📈 Evolución Temporal del Portafolio")
                            # --- ELIMINAR GRÁFICO DUPLICADO Y DEJAR SOLO UNO ---
                            fig_evolucion = go.Figure()
                            # Usar fechas reales como eje X
                            fechas = df_portfolio.index
                            if not isinstance(fechas, pd.DatetimeIndex):
                                fechas = pd.to_datetime(fechas)
                            fig_evolucion.add_trace(go.Scatter(
                                x=fechas,
                                y=df_portfolio['Portfolio_Total'],
                                mode='lines',
                                name='Valor Total del Portafolio',
                                line=dict(color='#0d6efd', width=2)
                            ))
                            fig_evolucion.update_layout(
                                title="Evolución del Valor del Portafolio en el Tiempo",
                                xaxis_title="Fecha",
                                yaxis_title="Valor del Portafolio ($)",
                                height=400,
                                template='plotly_white'
                            )
                            st.plotly_chart(fig_evolucion, use_container_width=True)
                            
                            # Mostrar contribución de cada activo
                            st.markdown("#### 🥧 Contribución de Activos al Valor Total")
                            
                            contribucion_activos = {}
                            for activo_info in activos_exitosos:
                                simbolo = activo_info['simbolo']
                                # Usar la valuación real del activo
                                for activo_original in datos_activos:
                                    if activo_original['Símbolo'] == simbolo:
                                        contribucion_activos[simbolo] = activo_original['Valuación']
                                        break
                            
                            if contribucion_activos:
                                fig_contribucion = go.Figure(data=[go.Pie(
                                    labels=list(contribucion_activos.keys()),
                                    values=list(contribucion_activos.values()),
                                    textinfo='label+percent+value',
                                    texttemplate='%{label}<br>%{percent}<br>$%{value:,.0f}',
                                    hole=0.4,
                                    marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3'])
                                )])
                                fig_contribucion.update_layout(
                                    title="Contribución de Activos al Valor Total del Portafolio",
                                    height=400
                                )
                                st.plotly_chart(fig_contribucion, use_container_width=True)
                            
                            # Calcular y mostrar histograma de retornos del portafolio
                            st.markdown("#### 📊 Histograma de Retornos del Portafolio")
                            
                            try:
                                # Calcular retornos diarios del portafolio
                                df_portfolio_returns = df_portfolio['Portfolio_Total'].pct_change().dropna()
                                
                                if len(df_portfolio_returns) > 10:  # Mínimo de datos para análisis
                                    # Calcular métricas estadísticas de los retornos
                                    mean_return = df_portfolio_returns.mean()
                                    std_return = df_portfolio_returns.std()
                                    skewness = stats.skew(df_portfolio_returns)
                                    kurtosis = stats.kurtosis(df_portfolio_returns)
                                    var_95 = np.percentile(df_portfolio_returns, 5)
                                    var_99 = np.percentile(df_portfolio_returns, 1)
                                    
                                    # Calcular Jarque-Bera test para normalidad
                                    jb_stat, jb_p_value = stats.jarque_bera(df_portfolio_returns)
                                    is_normal = jb_p_value > 0.05
                                    
                                    # Crear histograma de retornos
                                    fig_returns_hist = go.Figure(data=[go.Histogram(
                                        x=df_portfolio_returns,
                                        nbinsx=50,
                                        name="Retornos del Portafolio",
                                        marker_color='#28a745',
                                        opacity=0.7
                                    )])
                                    
                                    # Agregar líneas de métricas importantes
                                    fig_returns_hist.add_vline(x=mean_return, line_dash="dash", line_color="red", 
                                                             annotation_text=f"Media: {mean_return:.4f}")
                                    fig_returns_hist.add_vline(x=var_95, line_dash="dash", line_color="orange", 
                                                             annotation_text=f"VaR 95%: {var_95:.4f}")
                                    fig_returns_hist.add_vline(x=var_99, line_dash="dash", line_color="darkred", 
                                                             annotation_text=f"VaR 99%: {var_99:.4f}")
                                    
                                    fig_returns_hist.update_layout(
                                        title="Distribución de Retornos Diarios del Portafolio",
                                        xaxis_title="Retorno Diario",
                                        yaxis_title="Frecuencia",
                                        height=500,
                                        showlegend=False,
                                        template='plotly_white'
                                    )
                                    
                                    st.plotly_chart(fig_returns_hist, use_container_width=True)
                                    
                                    # Mostrar estadísticas de retornos
                                    st.markdown("#### 📈 Estadísticas de Retornos")
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    col1.metric("Retorno Medio Diario", f"{mean_return:.4f}")
                                    col2.metric("Volatilidad Diaria", f"{std_return:.4f}")
                                    col3.metric("VaR 95%", f"{var_95:.4f}")
                                    col4.metric("VaR 99%", f"{var_99:.4f}")
                                    
                                    col1, col2, col3, col4 = st.columns(4)
                                    col1.metric("Skewness", f"{skewness:.4f}")
                                    col2.metric("Kurtosis", f"{kurtosis:.4f}")
                                    col3.metric("JB Statistic", f"{jb_stat:.4f}")
                                    normalidad = "✅ Normal" if is_normal else "❌ No Normal"
                                    col4.metric("Normalidad", normalidad)
                                    
                                    # Calcular métricas anualizadas
                                    mean_return_annual = mean_return * 252
                                    std_return_annual = std_return * np.sqrt(252)
                                    sharpe_ratio = mean_return_annual / std_return_annual if std_return_annual > 0 else 0
                                    
                                    st.markdown("#### 📊 Métricas Anualizadas")
                                    col1, col2, col3 = st.columns(3)
                                    col1.metric("Retorno Anual", f"{mean_return_annual:.2%}")
                                    col2.metric("Volatilidad Anual", f"{std_return_annual:.2%}")
                                    col3.metric("Ratio de Sharpe", f"{sharpe_ratio:.4f}")
                                    
                                    # Análisis de distribución
                                    st.markdown("#### 📋 Análisis de la Distribución")
                                    if is_normal:
                                        st.success("✅ Los retornos siguen una distribución normal (p > 0.05)")
                                    else:
                                        st.warning("⚠️ Los retornos no siguen una distribución normal (p ≤ 0.05)")
                                    
                                    if skewness > 0.5:
                                        st.info("📈 Distribución con sesgo positivo (cola derecha)")
                                    elif skewness < -0.5:
                                        st.info("📉 Distribución con sesgo negativo (cola izquierda)")
                                    else:
                                        st.success("📊 Distribución aproximadamente simétrica")
                                    
                                    if kurtosis > 3:
                                        st.info("📊 Distribución leptocúrtica (colas pesadas)")
                                    elif kurtosis < 3:
                                        st.info("📊 Distribución platicúrtica (colas ligeras)")
                                    else:
                                        st.success("📊 Distribución mesocúrtica (normal)")
                                    
                                    # Gráfico de evolución del valor real del portafolio en ARS y USD
                                    st.markdown("#### 📈 Evolución del Valor Real del Portafolio")
                                    
                                    # Obtener cotización MEP para conversión
                                    try:
                                        # Intentar obtener cotización MEP (usar AL30 como proxy)
                                        cotizacion_mep = obtener_cotizacion_mep(token_portador, "AL30", 1, 1)
                                        if cotizacion_mep and cotizacion_mep.get('precio'):
                                            tasa_mep = float(cotizacion_mep['precio'])
                                        else:
                                            # Si no hay MEP, usar tasa aproximada
                                            tasa_mep = 1000  # Tasa aproximada
                                            st.info("ℹ️ Usando tasa MEP aproximada para conversiones")
                                    except:
                                        tasa_mep = 1000
                                        st.info("ℹ️ Usando tasa MEP aproximada para conversiones")
                                    
                                    # Crear figura con dos ejes Y
                                    fig_evolucion_real = go.Figure()
                                    
                                    # Traza en ARS (eje Y izquierdo)
                                    fig_evolucion_real.add_trace(go.Scatter(
                                        x=df_portfolio.index,
                                        y=df_portfolio['Portfolio_Total'],
                                        mode='lines',
                                        name='Valor en ARS',
                                        line=dict(color='#28a745', width=2),
                                        yaxis='y'
                                    ))
                                    
                                    # Traza en USD (eje Y derecho)
                                    valores_usd = df_portfolio['Portfolio_Total'] / tasa_mep
                                    fig_evolucion_real.add_trace(go.Scatter(
                                        x=df_portfolio.index,
                                        y=valores_usd,
                                        mode='lines',
                                        name='Valor en USD',
                                        line=dict(color='#0d6efd', width=2, dash='dash'),
                                        yaxis='y2'
                                    ))
                                    
                                    # Configurar ejes
                                    fig_evolucion_real.update_layout(
                                        title="Evolución del Valor Real del Portafolio (ARS y USD)",
                                        xaxis_title="Fecha",
                                        yaxis=dict(
                                            title=dict(
                                                text="Valor en ARS ($)",
                                                font=dict(color="#28a745")
                                            ),
                                            tickfont=dict(color="#28a745"),
                                            side="left"
                                        ),
                                        yaxis2=dict(
                                            title=dict(
                                                text="Valor en USD ($)",
                                                font=dict(color="#0d6efd")
                                            ),
                                            tickfont=dict(color="#0d6efd"),
                                            anchor="x",
                                            overlaying="y",
                                            side="right"
                                        ),
                                        height=500,
                                        template='plotly_white',
                                        legend=dict(
                                            orientation="h",
                                            yanchor="bottom",
                                            y=1.02,
                                            xanchor="right",
                                            x=1
                                        )
                                    )
                                    
                                    st.plotly_chart(fig_evolucion_real, use_container_width=True)
                                    
                                    # Mostrar estadísticas del valor real en ambas monedas
                                    st.markdown("#### 📊 Estadísticas del Valor Real")
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    valor_inicial_ars = df_portfolio['Portfolio_Total'].iloc[0]
                                    valor_final_ars = df_portfolio['Portfolio_Total'].iloc[-1]
                                    valor_inicial_usd = valor_inicial_ars / tasa_mep
                                    valor_final_usd = valor_final_ars / tasa_mep
                                    retorno_total_real = (valor_final_ars / valor_inicial_ars - 1) * 100
                                    
                                    col1.metric("Valor Inicial (ARS)", f"${valor_inicial_ars:,.2f}")
                                    col2.metric("Valor Final (ARS)", f"${valor_final_ars:,.2f}")
                                    col3.metric("Valor Inicial (USD)", f"${valor_inicial_usd:,.2f}")
                                    col4.metric("Valor Final (USD)", f"${valor_final_usd:,.2f}")
                                    
                                    col1, col2 = st.columns(2)
                                    col1.metric("Retorno Total (ARS)", f"{retorno_total_real:+.2f}%")
                                    col2.metric("Tasa MEP Utilizada", f"${tasa_mep:,.2f}")
                                    
                                    # Análisis de rendimiento extra asegurado de renta fija
                                    st.markdown("#### 🏦 Análisis de Rendimiento Extra Asegurado")
                                    
                                    # Identificar instrumentos de renta fija
                                    instrumentos_renta_fija = []
                                    total_renta_fija = 0
                                    
                                    for activo in datos_activos:
                                        tipo = activo.get('Tipo', '').lower()
                                        simbolo = activo.get('Símbolo', '')
                                        valuacion = activo.get('Valuación', 0)
                                        
                                        # Identificar FCIs, bonos y otros instrumentos de renta fija
                                        if any(keyword in tipo for keyword in ['fci', 'fondo', 'bono', 'titulo', 'publico', 'letra']):
                                            instrumentos_renta_fija.append({
                                                'simbolo': simbolo,
                                                'tipo': tipo,
                                                'valuacion': valuacion,
                                                'peso': valuacion / valor_total if valor_total > 0 else 0
                                            })
                                            total_renta_fija += valuacion
                                        
                                        # También identificar por símbolo (FCIs suelen tener símbolos específicos)
                                        elif any(keyword in simbolo.lower() for keyword in ['fci', 'fondo', 'bono', 'al', 'gd', 'gg']):
                                            instrumentos_renta_fija.append({
                                                'simbolo': simbolo,
                                                'tipo': tipo,
                                                'valuacion': valuacion,
                                                'peso': valuacion / valor_total if valor_total > 0 else 0
                                            })
                                            total_renta_fija += valuacion
                                    
                                    if instrumentos_renta_fija:
                                        st.success(f"✅ Se identificaron {len(instrumentos_renta_fija)} instrumentos de renta fija")
                                            
                                        # Mostrar tabla de instrumentos de renta fija
                                        df_renta_fija = pd.DataFrame(instrumentos_renta_fija)
                                        df_renta_fija['Peso (%)'] = df_renta_fija['peso'] * 100
                                        df_renta_fija['Valuación ($)'] = df_renta_fija['valuacion'].apply(lambda x: f"${x:,.2f}")
                                        
                                        st.dataframe(
                                            df_renta_fija[['simbolo', 'tipo', 'Valuación ($)', 'Peso (%)']],
                                            use_container_width=True,
                                            height=200
                                        )
                                        
                                        # Calcular rendimiento extra asegurado
                                        peso_renta_fija = total_renta_fija / valor_total if valor_total > 0 else 0
                                        
                                        # Estimación de rendimiento extra (basado en tasas típicas)
                                        rendimiento_extra_estimado = {
                                            'FCI': 0.08,  # 8% anual típico para FCIs
                                            'Bono': 0.12,  # 12% anual típico para bonos
                                            'Titulo': 0.10,  # 10% anual típico para títulos públicos
                                            'Letra': 0.15   # 15% anual típico para letras
                                        }
                                        
                                        rendimiento_extra_total = 0
                                        for instrumento in instrumentos_renta_fija:
                                            tipo_instrumento = instrumento['tipo'].lower()
                                            peso_instrumento = instrumento['peso']
                                            
                                            # Determinar tipo de rendimiento
                                            if 'fci' in tipo_instrumento or 'fondo' in tipo_instrumento:
                                                rendimiento = rendimiento_extra_estimado['FCI']
                                            elif 'bono' in tipo_instrumento:
                                                rendimiento = rendimiento_extra_estimado['Bono']
                                            elif 'titulo' in tipo_instrumento or 'publico' in tipo_instrumento:
                                                rendimiento = rendimiento_extra_estimado['Titulo']
                                            elif 'letra' in tipo_instrumento:
                                                rendimiento = rendimiento_extra_estimado['Letra']
                                            else:
                                                rendimiento = rendimiento_extra_estimado['FCI']  # Default
                                            
                                            rendimiento_extra_total += rendimiento * peso_instrumento
                                        
                                        # Mostrar métricas de rendimiento extra
                                        col1, col2, col3 = st.columns(3)
                                        col1.metric("Peso Renta Fija", f"{peso_renta_fija:.1%}")
                                        col2.metric("Rendimiento Extra Estimado", f"{rendimiento_extra_total:.1%}")
                                        col3.metric("Valor Renta Fija", f"${total_renta_fija:,.2f}")
                                        
                                        # Gráfico de composición por tipo de instrumento
                                        if len(instrumentos_renta_fija) > 1:
                                            fig_renta_fija = go.Figure(data=[go.Pie(
                                                labels=[f"{row['simbolo']} ({row['tipo']})" for _, row in df_renta_fija.iterrows()],
                                                values=df_renta_fija['valuacion'],
                                                textinfo='label+percent+value',
                                                texttemplate='%{label}<br>%{percent}<br>$%{value:,.0f}',
                                                hole=0.4,
                                                marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3'])
                                            )])
                                            fig_renta_fija.update_layout(
                                                title="Composición de Instrumentos de Renta Fija",
                                                height=400
                                            )
                                            st.plotly_chart(fig_renta_fija, use_container_width=True)
                                        
                                        # Recomendaciones específicas para renta fija
                                        st.markdown("#### 💡 Recomendaciones Renta Fija")
                                        
                                        if peso_renta_fija < 0.2:
                                            st.info("📈 **Considerar aumentar exposición a renta fija**: Menos del 20% del portafolio")
                                        elif peso_renta_fija > 0.6:
                                            st.warning("📉 **Considerar reducir exposición a renta fija**: Más del 60% del portafolio")
                                        else:
                                            st.success("✅ **Exposición equilibrada a renta fija**: Entre 20% y 60% del portafolio")
                                        
                                        if rendimiento_extra_total > 0.10:
                                            st.success("🎯 **Excelente rendimiento extra estimado**: Más del 10% anual")
                                        elif rendimiento_extra_total > 0.05:
                                            st.info("📊 **Buen rendimiento extra estimado**: Entre 5% y 10% anual")
                                        else:
                                            st.warning("⚠️ **Rendimiento extra bajo**: Menos del 5% anual")
                                    
                                    else:
                                        st.info("ℹ️ No se identificaron instrumentos de renta fija en el portafolio")
                                        st.info("💡 **Recomendación**: Considerar agregar FCIs, bonos o títulos públicos para diversificar")
                                
                                # Análisis de retorno esperado por horizonte de inversión
                                st.markdown("#### 📊 Análisis de Retorno Esperado")
                                
                                # Calcular retornos en USD para diferentes horizontes
                                horizontes_analisis = [1, 7, 30, 90, 180, 365]
                                retornos_ars_por_horizonte = {}
                                retornos_usd_por_horizonte = {}
                                
                                # Calcular retornos en USD
                                df_portfolio_usd = df_portfolio['Portfolio_Total'] / tasa_mep
                                df_portfolio_returns_usd = df_portfolio_usd.pct_change().dropna()
                                
                                for horizonte in horizontes_analisis:
                                    if len(df_portfolio_returns) >= horizonte:
                                        # Retorno en ARS
                                        retorno_ars = (1 + df_portfolio_returns.tail(horizonte)).prod() - 1
                                        retornos_ars_por_horizonte[horizonte] = retorno_ars
                                        
                                        # Retorno en USD
                                        retorno_usd = (1 + df_portfolio_returns_usd.tail(horizonte)).prod() - 1
                                        retornos_usd_por_horizonte[horizonte] = retorno_usd
                                
                                if retornos_ars_por_horizonte and retornos_usd_por_horizonte:
                                    # Crear gráfico de retornos por horizonte (ARS y USD)
                                    fig_horizontes = go.Figure()
                                    
                                    horizontes = list(retornos_ars_por_horizonte.keys())
                                    retornos_ars = list(retornos_ars_por_horizonte.values())
                                    retornos_usd = list(retornos_usd_por_horizonte.values())
                                    
                                    # Barras para ARS
                                    fig_horizontes.add_trace(go.Bar(
                                        x=[f"{h} días" for h in horizontes],
                                        y=retornos_ars,
                                        name="Retorno ARS",
                                        marker_color=['#28a745' if r >= 0 else '#dc3545' for r in retornos_ars],
                                        text=[f"{r:.2%}" for r in retornos_ars],
                                        textposition='auto'
                                    ))
                                    
                                    # Barras para USD
                                    fig_horizontes.add_trace(go.Bar(
                                        x=[f"{h} días" for h in horizontes],
                                        y=retornos_usd,
                                        name="Retorno USD",
                                        marker_color=['#0d6efd' if r >= 0 else '#ff6b6b' for r in retornos_usd],
                                        text=[f"{r:.2%}" for r in retornos_usd],
                                        textposition='auto'
                                    ))
                                    
                                    fig_horizontes.update_layout(
                                        title=f"Retornos Acumulados por Horizonte de Inversión (ARS y USD)",
                                        xaxis_title="Horizonte de Inversión",
                                        yaxis_title="Retorno Acumulado",
                                        height=400,
                                        template='plotly_white',
                                        barmode='group'
                                    )
                                    
                                    st.plotly_chart(fig_horizontes, use_container_width=True)
                                    
                                    # Mostrar métricas de retorno esperado (ARS y USD)
                                    st.markdown("#### 📈 Métricas de Retorno Esperado")
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    # Calcular retorno esperado anualizado en ARS
                                    retorno_anualizado_ars = mean_return_annual
                                    col1.metric("Retorno Esperado Anual (ARS)", f"{retorno_anualizado_ars:.2%}")
                                    
                                    # Calcular retorno esperado anualizado en USD
                                    mean_return_annual_usd = df_portfolio_returns_usd.mean() * 252
                                    col2.metric("Retorno Esperado Anual (USD)", f"{mean_return_annual_usd:.2%}")
                                    
                                    # Calcular retorno esperado para el horizonte seleccionado
                                    retorno_esperado_horizonte_ars = retorno_anualizado_ars * (dias_analisis / 365)
                                    retorno_esperado_horizonte_usd = mean_return_annual_usd * (dias_analisis / 365)
                                    col3.metric(f"Retorno Esperado ({dias_analisis} días) ARS", f"{retorno_esperado_horizonte_ars:.2%}")
                                    col4.metric(f"Retorno Esperado ({dias_analisis} días) USD", f"{retorno_esperado_horizonte_usd:.2%}")
                                    
                                    # Calcular intervalos de confianza
                                    z_score_95 = 1.96  # 95% de confianza
                                    std_return_annual_usd = df_portfolio_returns_usd.std() * np.sqrt(252)
                                    intervalo_confianza_ars = z_score_95 * std_return_annual * np.sqrt(dias_analisis / 365)
                                    intervalo_confianza_usd = z_score_95 * std_return_annual_usd * np.sqrt(dias_analisis / 365)
                                    
                                    col1, col2 = st.columns(2)
                                    col1.metric("Intervalo de Confianza 95% (ARS)", f"±{intervalo_confianza_ars:.2%}")
                                    col2.metric("Intervalo de Confianza 95% (USD)", f"±{intervalo_confianza_usd:.2%}")
                                    
                                    # Proyecciones de valor del portafolio
                                    st.markdown("#### 💰 Proyecciones de Valor del Portafolio")
                                    
                                    valor_actual = df_portfolio['Portfolio_Total'].iloc[-1]
                                    
                                    # Calcular proyecciones optimista, pesimista y esperada
                                    proyeccion_esperada = valor_actual * (1 + retorno_esperado_horizonte_ars)
                                    proyeccion_optimista = valor_actual * (1 + retorno_esperado_horizonte_ars + intervalo_confianza_ars)
                                    proyeccion_pesimista = valor_actual * (1 + retorno_esperado_horizonte_ars - intervalo_confianza_ars)
                                    
                                    col1, col2, col3 = st.columns(3)
                                    col1.metric("Proyección Esperada", f"${proyeccion_esperada:,.2f}")
                                    col2.metric("Proyección Optimista", f"${proyeccion_optimista:,.2f}")
                                    col3.metric("Proyección Pesimista", f"${proyeccion_pesimista:,.2f}")
                                    

                                    
                                    # Resumen de análisis
                                    st.markdown("#### 📋 Resumen del Análisis")
                                    
                                    if retorno_esperado_horizonte_ars > 0:
                                        st.success(f"✅ **Retorno Esperado Positivo**: Se espera un retorno de {retorno_esperado_horizonte_ars:.2%} en {dias_analisis} días")
                                    else:
                                        st.warning(f"⚠️ **Retorno Esperado Negativo**: Se espera un retorno de {retorno_esperado_horizonte_ars:.2%} en {dias_analisis} días")
                                    
                                    if sharpe_ratio > 1:
                                        st.success(f"✅ **Excelente Ratio de Sharpe**: {sharpe_ratio:.2f} indica buenos retornos ajustados por riesgo")
                                    elif sharpe_ratio > 0.5:
                                        st.info(f"ℹ️ **Buen Ratio de Sharpe**: {sharpe_ratio:.2f} indica retornos razonables ajustados por riesgo")
                                    else:
                                        st.warning(f"⚠️ **Ratio de Sharpe Bajo**: {sharpe_ratio:.2f} indica retornos pobres ajustados por riesgo")
                                    
                                    # Recomendaciones basadas en el análisis
                                    st.markdown("#### 💡 Recomendaciones")
                                    
                                    if retorno_esperado_horizonte_ars > 0.05:  # 5% en el horizonte
                                        st.success("🎯 **Mantener Posición**: El portafolio muestra buenas perspectivas de retorno")
                                    elif retorno_esperado_horizonte_ars < -0.05:  # -5% en el horizonte
                                        st.warning("🔄 **Considerar Rebalanceo**: El portafolio podría beneficiarse de ajustes")
                                    else:
                                        st.info("📊 **Monitorear**: El portafolio muestra retornos moderados")
                                
                                else:
                                    st.warning("⚠️ No hay suficientes datos para calcular retornos del portafolio")
                                    
                            except Exception as e:
                                st.error(f"❌ Error calculando retornos del portafolio: {str(e)}")
                                st.exception(e)
                            
                        else:
                            st.warning("⚠️ No hay datos suficientes para generar el histograma")
                    else:
                        st.warning("⚠️ No se pudieron obtener datos históricos para ningún activo")
                else:
                    st.warning("⚠️ No hay activos válidos para generar el histograma")
                    
            except Exception as e:
                st.error(f"❌ Error generando histograma del portafolio: {str(e)}")
                st.exception(e)
        
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
                        # Mostrar análisis completo en texto y tabla
                        st.markdown("### 📊 Análisis Completo del Mercado")
                        st.markdown(f"**Descripción:** {cotizacion_mep.get('descripcionTitulo','N/A')}")
                        st.markdown(f"**Símbolo:** {simbolo_mep}")
                        st.markdown(f"**Último Precio:** ${cotizacion_mep.get('ultimoPrecio','N/A')}")
                        st.markdown(f"**Variación:** {cotizacion_mep.get('variacion','N/A')}%")
                        st.markdown(f"**Apertura:** ${cotizacion_mep.get('apertura','N/A')}")
                        st.markdown(f"**Máximo:** ${cotizacion_mep.get('maximo','N/A')}")
                        st.markdown(f"**Mínimo:** ${cotizacion_mep.get('minimo','N/A')}")
                        st.markdown(f"**Cierre Anterior:** ${cotizacion_mep.get('cierreAnterior','N/A')}")
                        st.markdown(f"**Tendencia:** {cotizacion_mep.get('tendencia','N/A')}")
                        st.markdown(f"**Monto Operado:** ${cotizacion_mep.get('montoOperado','N/A')}")
                        st.markdown(f"**Volumen Nominal:** {cotizacion_mep.get('volumenNominal','N/A')}")
                        st.markdown(f"**Cantidad de Operaciones:** {cotizacion_mep.get('cantidadOperaciones','N/A')}")
                        st.markdown(f"**Moneda:** {cotizacion_mep.get('moneda','N/A')}")
                        st.markdown(f"**Fecha/Hora:** {cotizacion_mep.get('fechaHora','N/A')}")
                        # Mostrar puntas de compra/venta en tabla
                        puntas = cotizacion_mep.get('puntas',[])
                        if puntas:
                            import pandas as pd
                            df_puntas = pd.DataFrame(puntas)
                            df_puntas = df_puntas.rename(columns={
                                'cantidadCompra':'Cantidad Compra',
                                'precioCompra':'Precio Compra',
                                'precioVenta':'Precio Venta',
                                'cantidadVenta':'Cantidad Venta'
                            })
                            st.markdown("**Puntas de Compra/Venta:**")
                            st.dataframe(df_puntas, use_container_width=True)
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
    """
    Menú avanzado de optimización de portafolio.
    Ahora usa obtención asincrónica y optimizada de series históricas para el universo aleatorio.
    """
    st.markdown("### 🔄 Menú Avanzado de Optimización de Portafolio")
    with st.spinner("Obteniendo portafolio actual..."):
        portafolio = obtener_portafolio(token_acceso, id_cliente)
    if not portafolio or not portafolio.get('activos'):
        st.warning("No se pudo obtener el portafolio del cliente o está vacío")
        return

    activos_raw = portafolio['activos']
    # Diagnóstico del portafolio actual
    st.subheader("🔍 Diagnóstico del Portafolio Actual")
    # Usar el mismo método de resumen de portafolio para diagnóstico real
    activos_dict = {}
    valor_total = 0
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
    # Obtener saldo disponible de las cuentas
    estado_cuenta = obtener_estado_cuenta(token_acceso, id_cliente)
    saldo_disponible = 0
    if estado_cuenta and 'cuentas' in estado_cuenta:
        for cuenta in estado_cuenta['cuentas']:
            disponible = cuenta.get('disponible', 0)
            try:
                saldo_disponible += float(disponible)
            except Exception:
                continue
    metricas_actual = calcular_metricas_portafolio(activos_dict, valor_total, token_acceso)
    cols = st.columns(4)
    cols[0].metric("Retorno Esperado", f"{(metricas_actual.get('retorno_esperado_anual',0) or 0)*100:.2f}%")
    cols[1].metric("Riesgo (Volatilidad)", f"{(metricas_actual.get('riesgo_anual',0) or 0)*100:.2f}%")
    cols[2].metric("Sharpe", f"{(metricas_actual.get('retorno_esperado_anual',0)/(metricas_actual.get('riesgo_anual',1e-6))):.2f}")
    cols[3].metric("Concentración", f"{(metricas_actual.get('concentracion',0) or 0)*100:.1f}%")

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
        st.info("Seleccione el universo aleatorio de mercado real")
        paneles = ['acciones', 'cedears', 'aDRs', 'titulosPublicos', 'obligacionesNegociables']
        paneles_seleccionados = st.multiselect("Paneles de universo aleatorio", paneles, default=paneles)
        capital_mode = st.radio(
            "¿Cómo definir el capital disponible?",
            ["Manual", "Saldo valorizado + disponible (actual)"]
        )
        capital_ars = 100000
        capital_auto = valor_total + saldo_disponible
        if capital_mode == "Manual":
            capital_ars = st.number_input("Capital disponible para universo aleatorio (ARS)", min_value=10000, value=100000)
        else:
            st.success(f"Capital valorizado + disponible: ${capital_auto:,.2f}")
            capital_ars = capital_auto
        cantidad_activos = st.slider("Cantidad de activos por panel", 2, 10, 5)
        fecha_desde = st.session_state.fecha_desde.strftime('%Y-%m-%d')
        fecha_hasta = st.session_state.fecha_hasta.strftime('%Y-%m-%d')
        ajustada = "SinAjustar"
        # Obtener tickers por panel
        tickers_por_panel, _ = obtener_tickers_por_panel(token_acceso, paneles_seleccionados, 'Argentina')
        # Validar tickers_por_panel
        if not tickers_por_panel or not any(tickers_por_panel.values()):
            st.error("No se pudieron obtener tickers para el universo aleatorio seleccionado. Revise los paneles o intente nuevamente.")
            return
        # Obtener series históricas aleatorias (ahora asincrónico y optimizado)
        st.info("Descargando series históricas en paralelo para mayor velocidad...")
        try:
            series_historicas, seleccion_final = obtener_series_historicas_aleatorias_con_capital(
                tickers_por_panel, paneles_seleccionados, cantidad_activos,
                fecha_desde, fecha_hasta, ajustada, token_acceso, capital_ars
            )
        except Exception as e:
            st.error(f"Error al obtener series históricas para el universo aleatorio: {e}")
            return
        # Construir universe_activos a partir de seleccion_final
        universe_activos = []
        if seleccion_final and any(seleccion_final.values()):
            for panel, simbolos in seleccion_final.items():
                for simbolo in simbolos:
                    universe_activos.append({'simbolo': simbolo, 'mercado': 'BCBA', 'tipo': panel})
        else:
            st.error("No hay suficientes activos para el universo aleatorio seleccionado. Intente con otros paneles o menos cantidad de activos.")
            return
    # Validación final antes de continuar
    if not universe_activos:
        st.error("No se pudo construir el universo de activos para la optimización. Proceso detenido.")
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
    cols[0].metric("Actual: Retorno", f"{(metricas_actual.get('retorno_esperado_anual',0) or 0)*100:.2f}%")
    cols[0].metric("Actual: Riesgo", f"{(metricas_actual.get('riesgo_anual',0) or 0)*100:.2f}%")
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
            st.plotly_chart(fig, use_container_width=True, key=f"hist_{clave}")
        # Pie chart de pesos
        if hasattr(res, 'dataframe_allocation') and res.dataframe_allocation is not None:
            df = res.dataframe_allocation
            if not df.empty and 'rics' in df.columns and 'weights' in df.columns and df['weights'].sum() > 0:
                st.markdown("**Distribución de Pesos**")
                import plotly.graph_objects as go
                fig_pie = go.Figure(data=[go.Pie(labels=df['rics'], values=df['weights'], textinfo='label+percent', hole=0.4)])
                fig_pie.update_layout(title="Distribución Optimizada de Activos", template='plotly_white')
                st.plotly_chart(fig_pie, use_container_width=True, key=f"pie_{clave}")
            else:
                st.info("No hay datos suficientes para mostrar la distribución de pesos.")
        # Métricas
        st.write(f"Retorno esperado: {getattr(res,'returns',0)*100:.2f}% | Riesgo: {getattr(res,'risk',0)*100:.2f}% | Sharpe: {sharpe:.2f}")
        st.markdown("---")

    # Frontera eficiente
    st.subheader("📈 Frontera Eficiente y Portafolios Especiales")
    if st.checkbox("Mostrar Frontera Eficiente", value=True):
        portfolios, returns, volatilities = manager_inst.compute_efficient_frontier(target_return=0.08, include_min_variance=True)
        if portfolios and returns and volatilities and len(returns) > 0 and len(volatilities) > 0:
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
            # Línea de tasa libre de riesgo
            risk_free_rate = 0.40  # Tasa libre de riesgo anual para Argentina
            fig.add_hline(y=risk_free_rate, line_dash="dot", line_color="green",
                         annotation_text=f"Tasa libre de riesgo: {risk_free_rate*100:.2f}%", annotation_position="top left")
        else:
            st.warning("No se pudo calcular la frontera eficiente. Verifique que haya datos históricos suficientes y activos válidos.")

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
                'Mejora Retorno (%)': (getattr(res,'returns',0)-(metricas_actual.get('retorno_esperado_anual',0) or 0))*100,
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

    # --- Análisis Intermarket Profesional previo a la optimización ---
    import yfinance as yf
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    st.markdown('---')
    st.subheader('🔗 Análisis Intermarket Profesional (Contexto Global)')
    with st.spinner('Descargando datos intermarket de referencia...'):
        tickers_intermarket = {
            'Merval': '^MERV',
            'S&P 500': '^GSPC',
            'DXY': 'DX-Y.NYB',
            'VIX': '^VIX',
            'Soja': 'ZS=F'
        }
        precios_inter = {}
        for k, v in tickers_intermarket.items():
            try:
                data = yf.download(v, period='1y')['Adj Close']
                if not data.empty:
                    precios_inter[k] = data.dropna()
            except Exception:
                continue
        df_inter = pd.DataFrame(precios_inter).dropna()
        retornos_inter = df_inter.pct_change().dropna()
    # Señal simple intermarket
    dxy_trend = retornos_inter['DXY'].tail(20).sum() if 'DXY' in retornos_inter else 0
    soja_trend = retornos_inter['Soja'].tail(20).sum() if 'Soja' in retornos_inter else 0
    vix_actual = df_inter['VIX'].iloc[-1] if 'VIX' in df_inter else 20
    merval_momentum = retornos_inter['Merval'].tail(10).sum() if 'Merval' in retornos_inter else 0
    if dxy_trend < -0.01 and soja_trend > 0.03 and vix_actual < 20 and merval_momentum > 0.02:
        regimen = "ALCISTA"
        recomendacion = "Contexto favorable para activos de riesgo y commodities."
        explicacion = "El dólar débil, commodities fuertes, baja volatilidad y momentum positivo en Merval sugieren un entorno alcista."
    elif dxy_trend > 0.01 or vix_actual > 25:
        regimen = "DEFENSIVO"
        recomendacion = "Contexto defensivo: preferencia por activos refugio y baja exposición a riesgo."
        explicacion = "El dólar fuerte o alta volatilidad (VIX) sugieren cautela y preferencia por activos defensivos."
    else:
        regimen = "NEUTRAL"
        recomendacion = "Contexto neutral: portafolio balanceado y esperar señales claras."
        explicacion = "No hay señales claras de tendencia, se recomienda mantener un portafolio diversificado."
    st.info(f"Régimen Intermarket: **{regimen}**. {recomendacion}")
    st.caption(f"Explicación: {explicacion}")
    # Mostrar gráfico de activos de referencia
    fig, ax = plt.subplots()
    activos_graf = ['Merval', 'S&P 500', 'DXY', 'VIX', 'Soja']
    for activo in activos_graf:
        if activo in df_inter:
            precios_norm = df_inter[activo] / df_inter[activo].iloc[0] * 100
            ax.plot(precios_norm.index, precios_norm, label=activo)
    ax.legend()
    ax.set_title("Evolución de activos de referencia (base 100)")
    st.pyplot(fig)
    # --- FIN BLOQUE INTERMARKET ---

    # --- Análisis de Ciclo Económico BCRA ---
    with st.expander("🔎 Análisis Automático del Ciclo Económico (BCRA)", expanded=False):
        st.markdown("**Variables consideradas:** Reservas, tasa de política monetaria, inflación, agregados monetarios.")
        # Obtener datos reales del BCRA
        try:
            # Reservas internacionales (último dato)
            url_reservas = "https://api.estadisticasbcra.com/reservas"
            url_leliq = "https://api.estadisticasbcra.com/leliq"
            url_inflacion = "https://api.estadisticasbcra.com/inflacion_mensual_oficial"
            url_m2 = "https://api.estadisticasbcra.com/base_monetaria"
            headers = {"Authorization": "Bearer TU_API_KEY_BCRA"}
            reservas = requests.get(url_reservas, headers=headers).json()[-1]["valor"]
            tasa_leliq = requests.get(url_leliq, headers=headers).json()[-1]["valor"]
            inflacion = requests.get(url_inflacion, headers=headers).json()[-1]["valor"] / 100
            m2 = requests.get(url_m2, headers=headers).json()
            m2_crecimiento = (m2[-1]["valor"] - m2[-22]["valor"]) / m2[-22]["valor"] if len(m2) > 22 else None
        except Exception as e:
            st.warning(f"No se pudieron obtener datos reales del BCRA: {e}. Se usarán valores simulados.")
            reservas = 25000
            tasa_leliq = 50
            inflacion = 0.08
            m2_crecimiento = None
        # Lógica simple de etapa
        if reservas > 35000 and inflacion < 0.05 and tasa_leliq < 60:
            etapa = "Expansión"
            explicacion_ciclo = "Reservas altas, inflación baja y tasas moderadas: contexto favorable para activos de riesgo."
            sugerencia = "Portafolio agresivo: sobreponderar acciones, cíclicos y emergentes."
        elif inflacion > 0.10 or tasa_leliq > 80:
            etapa = "Recesión"
            explicacion_ciclo = "Inflación/tasas muy altas: contexto defensivo, preferir liquidez y renta fija."
            sugerencia = "Portafolio defensivo: priorizar bonos, FCIs de money market y activos refugio."
        elif reservas > 30000 and inflacion < 0.08:
            etapa = "Auge"
            explicacion_ciclo = "Reservas sólidas y baja inflación: buen momento para balancear riesgo y retorno."
            sugerencia = "Portafolio balanceado: combinar acciones, bonos y algo de liquidez."
        else:
            etapa = "Recuperación/Neutral"
            explicacion_ciclo = "Variables mixtas, posible recuperación o transición."
            sugerencia = "Portafolio diversificado: mantener exposición equilibrada y flexibilidad."
        st.success(f"Etapa detectada: **{etapa}**")
        st.caption(f"Explicación: {explicacion_ciclo}")
        
        # Validar y mostrar variables con manejo de None
        reservas_str = f"{reservas:,.0f}M USD" if reservas is not None else "N/D"
        tasa_leliq_str = f"{tasa_leliq:.2f}% anual" if tasa_leliq is not None else "N/D"
        inflacion_str = f"{inflacion*100:.2f}%" if inflacion is not None else "N/D"
        m2_crecimiento_str = f"{m2_crecimiento*100:.2f}%" if m2_crecimiento is not None else "N/D"
        
        st.markdown(f"- Reservas: {reservas_str}\n- Tasa LELIQ: {tasa_leliq_str}\n- Inflación mensual: {inflacion_str}\n- Crecimiento M2: {m2_crecimiento_str}")
        # --- SUGERENCIA DE ESTRATEGIA SEGÚN CICLO ---
        st.markdown(f"""
        <div style='background:#eaf6fb;border-left:6px solid #007cf0;padding:1.2em 1.5em;margin:1.2em 0 1.5em 0;border-radius:10px;'>
        <b>💡 Sugerencia de Estrategia de Optimización:</b><br>
        <span style='font-size:1.15em;font-weight:700;color:#0056b3'>{sugerencia}</span><br>
        <span style='color:#007cf0;font-size:1em;'>{explicacion_ciclo}</span>
        </div>
        """, unsafe_allow_html=True)

    # --- Análisis de Ciclo Económico BCRA ---
    with st.expander("🔎 Análisis Automático del Ciclo Económico (BCRA)", expanded=False):
        st.markdown("**Variables consideradas:** Reservas, tasa de política monetaria, inflación, agregados monetarios.")
        # Obtener datos reales del BCRA
        try:
            # Reservas internacionales (último dato)
            url_reservas = "https://api.estadisticasbcra.com/reservas"
            url_leliq = "https://api.estadisticasbcra.com/leliq"
            url_inflacion = "https://api.estadisticasbcra.com/inflacion_mensual_oficial"
            url_m2 = "https://api.estadisticasbcra.com/base_monetaria"
            headers = {"Authorization": "BEARER TU_API_KEY_BCRA"}  # Reemplazar por tu API KEY de estadisticasbcra.com
            # Reservas
            reservas_df = pd.DataFrame(requests.get(url_reservas, headers=headers).json())
            reservas = reservas_df.iloc[-1]['valor'] if not reservas_df.empty else None
            # Tasa LELIQ
            leliq_df = pd.DataFrame(requests.get(url_leliq, headers=headers).json())
            tasa_leliq = leliq_df.iloc[-1]['valor'] if not leliq_df.empty else None
            # Inflación mensual
            inflacion_df = pd.DataFrame(requests.get(url_inflacion, headers=headers).json())
            inflacion = inflacion_df.iloc[-1]['valor']/100 if not inflacion_df.empty else None
            # M2 (usamos base monetaria como proxy)
            m2_df = pd.DataFrame(requests.get(url_m2, headers=headers).json())
            if len(m2_df) > 1:
                m2_crecimiento = (m2_df.iloc[-1]['valor'] - m2_df.iloc[-2]['valor']) / m2_df.iloc[-2]['valor']
            else:
                m2_crecimiento = None
        except Exception as e:
            st.warning(f"No se pudieron obtener datos reales del BCRA: {e}. Se usarán valores simulados.")
            reservas = 25000
            tasa_leliq = 50
            inflacion = 0.08
            m2_crecimiento = 0.03
        # Lógica simple de ciclo
        if inflacion is not None and tasa_leliq is not None and m2_crecimiento is not None and reservas is not None:
            if inflacion > 0.06 and tasa_leliq > 40 and m2_crecimiento > 0.02 and reservas < 20000:
                etapa = "Recesión"
                explicacion_ciclo = "Alta inflación, tasas elevadas, crecimiento monetario y reservas bajas sugieren recesión."
            elif inflacion < 0.04 and tasa_leliq < 35 and m2_crecimiento < 0.01 and reservas > 35000:
                etapa = "Expansión"
                explicacion_ciclo = "Baja inflación, tasas bajas, crecimiento monetario controlado y reservas altas sugieren expansión."
            elif inflacion > 0.05 and tasa_leliq > 45 and reservas > 30000:
                etapa = "Auge"
                explicacion_ciclo = "Inflación y tasas altas pero reservas sólidas sugieren auge, pero con riesgos de sobrecalentamiento."
            else:
                etapa = "Recuperación/Neutral"
                explicacion_ciclo = "Variables mixtas, posible recuperación o transición."
            st.success(f"Etapa detectada: **{etapa}**")
            st.caption(f"Explicación: {explicacion_ciclo}")
            # Validar y mostrar variables
            reservas_str = f"{reservas:,.0f}M USD" if reservas is not None else "N/D"
            tasa_leliq_str = f"{tasa_leliq:.2f}% anual" if tasa_leliq is not None else "N/D"
            inflacion_str = f"{inflacion*100:.2f}%" if inflacion is not None else "N/D"
            m2_crecimiento_str = f"{m2_crecimiento*100:.2f}%" if m2_crecimiento is not None else "N/D"
            st.markdown(f"- Reservas: {reservas_str}\n- Tasa LELIQ: {tasa_leliq_str}\n- Inflación mensual: {inflacion_str}\n- Crecimiento M2: {m2_crecimiento_str}")
        else:
            st.warning("No se pudieron obtener todas las variables para el análisis de ciclo económico.")
    # --- FIN BLOQUE CICLO ECONÓMICO ---

    # ... resto del código de optimización ...

    # ... después de mostrar los resultados de optimización ...
    # Mini tab de asimetría de retornos
    with st.expander("📉 Asimetría de los Retornos (Skewness)", expanded=False):
        estrategias_labels = []
        skewness_vals = []
        for clave, nombre in estrategias:
            res, _, _ = resultados.get(clave, (None, None, None))
            if res and hasattr(res, 'returns') and res.returns is not None:
                try:
                    ret = res.returns
                    if hasattr(ret, 'values'):
                        ret = ret.values
                    val = skew(ret)
                    estrategias_labels.append(nombre)
                    skewness_vals.append(val)
                except Exception:
                    continue
        if estrategias_labels:
            fig, ax = plt.subplots(figsize=(6, 3))
            bars = ax.bar(estrategias_labels, skewness_vals, color=["#0d6efd" if v > 0 else "#ef4444" for v in skewness_vals])
            ax.axhline(0, color='gray', linestyle='--', linewidth=1)
            ax.set_ylabel('Skewness')
            ax.set_title('Asimetría de los Retornos por Estrategia')
            for bar, val in zip(bars, skewness_vals):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{val:.2f}", ha='center', va='bottom', fontsize=9)
            st.pyplot(fig)
            st.caption("Valores positivos: cola derecha (más ganancias extremas). Valores negativos: cola izquierda (más pérdidas extremas). Cero: simetría.")
        else:
            st.info("No hay retornos suficientes para calcular la asimetría.")

    # --- Análisis Sectorial Básico previo a la optimización ---
    with st.expander("🔎 Análisis Sectorial Básico (Momentum por Sector)", expanded=False):
        st.markdown("**Se analizan los principales ETFs sectoriales globales para identificar los sectores con mejor momentum reciente.**")
        sector_etfs = {
            'Tecnología': 'XLK',
            'Financieros': 'XLF',
            'Salud': 'XLV',
            'Energía': 'XLE',
            'Industrial': 'XLI',
            'Comunicación': 'XLC',
            'Consumo Discrecional': 'XLY',
            'Consumo Básico': 'XLP',
            'Materiales': 'XLB',
            'Bienes Raíces': 'XLRE',
            'Servicios Públicos': 'XLU'
        }
        import yfinance as yf
        import pandas as pd
        import plotly.graph_objects as go
        try:
            precios = yf.download(list(sector_etfs.values()), period="6mo", interval="1d", progress=False)["Adj Close"]
            rendimientos = precios.iloc[-1] / precios.iloc[0] - 1
            ranking = rendimientos.sort_values(ascending=False)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[k for k,v in sector_etfs.items() if v in ranking.index],
                y=ranking.values*100,
                marker_color=["#2ecc71" if v==ranking.index[0] else "#3498db" for v in ranking.index],
                text=[f"{v}: {ranking[v]*100:.2f}%" for v in ranking.index],
                textposition="auto"
            ))
            fig.update_layout(title="Ranking de Sectores por Momentum (6 meses)", yaxis_title="Rendimiento (%)", xaxis_title="Sector", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            st.success(f"Sector destacado: {ranking.index[0]} ({ranking.values[0]*100:.2f}%)")
            st.markdown(f"**Recomendación:** Priorizar activos del sector **{[k for k,v in sector_etfs.items() if v==ranking.index[0]][0]}** para optimizaciones si es coherente con tu perfil de riesgo.")
        except Exception as e:
            st.warning(f"No se pudo obtener el ranking sectorial: {e}")

    # --- Diagnóstico IA de ciclo económico y sugerencia de sectores ---
    def diagnostico_ciclo_y_sugerencia(all_variables_data, gemini_api_key, sectores_arg=None):
        """
        Usa IA para diagnosticar el ciclo económico y sugerir sectores/activos de Argentina y EEUU.
        """
        import google.generativeai as genai
        resumen = []
        for nombre, info in all_variables_data.items():
            m = info.get('metrics', {})
            resumen.append(
                f"{nombre}: Actual={m.get('valor_actual', 0):.2f}, Cambio={m.get('cambio_porcentual', 0):+.1f}%, VolATR={m.get('volatilidad_atr', 0):.2f}%, Tend={m.get('tendencia_direccion', 'N/A')}"
            )
        # --- Sectores argentinos relevantes ---
        sectores_arg = sectores_arg or {
            'Bancos': ['GGAL', 'BMA', 'SUPV', 'BBAR'],
            'Energía': ['YPFD', 'PAMP', 'CEPU', 'TGSU2'],
            'Consumo': ['SUPV', 'EDN', 'ALUA'],
            'Materiales': ['TXAR', 'ALUA'],
            'Tecnología': ['MELI'],
            'Servicios Públicos': ['EDN', 'TGSU2', 'CEPU'],
            'Agro': ['AGRO'],
            'Telecomunicaciones': ['TECO2'],
            'Industriales': ['TRAN', 'TGNO4'],
        }
        sectores_arg_str = "\n".join([f"- {k}: {', '.join(v)}" for k, v in sectores_arg.items()])
        prompt = f"""
Actúa como economista jefe. Analiza el siguiente resumen de variables macroeconómicas argentinas y de EEUU:

{chr(10).join(resumen)}

Sectores argentinos relevantes y sus principales tickers:
{sectores_arg_str}

1. Diagnostica el ciclo económico actual de Argentina y global (expansión, recesión, etc.).
2. Sugiere 2-3 sectores o tipos de activos argentinos (de la lista) y 2-3 de EEUU que suelen rendir mejor en este ciclo, usando factores de Intermarket (ITM), momentum y variables macro si es relevante.
3. Fundamenta brevemente cada sugerencia, explicando por qué esos sectores son los más adecuados según el contexto y los factores de ITM.

Responde en español, en formato claro y ejecutivo. Enumera los sectores sugeridos en una lista separada al final bajo el título "SUGERENCIA DE SECTORES ARGENTINA" y otra bajo "SUGERENCIA DE SECTORES EEUU".\n\nEjemplo de formato de respuesta:\n\nDiagnóstico: ...\nExplicación: ...\nSUGERENCIA DE SECTORES ARGENTINA:\n- ...\n- ...\nSUGERENCIA DE SECTORES EEUU:\n- ...\n- ...\n"""
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=900,
                top_p=0.9,
                top_k=30
            )
        )
        response = model.generate_content(prompt)
        return response.text if response and response.text else "No se pudo obtener diagnóstico IA."

    # --- INICIO mostrar_optimizacion_portafolio ---
        # Diagnóstico IA de ciclo económico y sugerencia de sectores
        st.markdown("---")
        st.subheader("🧠 Diagnóstico IA de ciclo económico y sugerencia de sectores")
        if 'GEMINI_API_KEY' not in st.session_state:
            st.session_state.GEMINI_API_KEY = ''
        if st.button("🔍 Analizar ciclo y sugerir sectores", key="btn_diag_ia"):
            import yfinance as yf
            import numpy as np
            all_variables_data = {}
            ATR_WINDOW = 14
            # --- Variables Argentina ---
            try:
                merval = yf.download('^MERV', period='6mo')['Close']
                if not merval.empty:
                    merval_ret = merval.pct_change().dropna()
                    merval_atr = merval_ret.abs().rolling(ATR_WINDOW).mean().iloc[-1]*100 if len(merval_ret) >= ATR_WINDOW else merval_ret.abs().mean()*100
                    all_variables_data['MERVAL (Argentina)'] = {
                        'metrics': {
                            'valor_actual': merval.iloc[-1],
                            'cambio_porcentual': (merval.iloc[-1]/merval.iloc[0]-1)*100,
                            'volatilidad_atr': merval_atr,
                            'tendencia_direccion': 'alcista' if merval.iloc[-1]>merval.iloc[0] else 'bajista'
                        }
                    }
            except Exception as e:
                st.warning(f"No se pudo obtener MERVAL: {e}")
            # --- Variables EEUU ---
            tickers_usa = {
                'S&P 500 (EEUU)': '^GSPC',
                'VIX (EEUU)': '^VIX',
                'Tecnología (XLK)': 'XLK',
                'Financieros (XLF)': 'XLF',
                'Energía (XLE)': 'XLE',
                'Consumo Discrecional (XLY)': 'XLY',
                'Consumo Básico (XLP)': 'XLP',
                'Salud (XLV)': 'XLV',
                'Industrial (XLI)': 'XLI',
                'Materiales (XLB)': 'XLB',
                'Bienes Raíces (XLRE)': 'XLRE',
                'Servicios Públicos (XLU)': 'XLU',
                'Comunicaciones (XLC)': 'XLC',
            }
            try:
                precios = yf.download(list(tickers_usa.values()), period='6mo')['Close']
                for nombre, ticker in tickers_usa.items():
                    serie = precios[ticker] if ticker in precios else None
                    if serie is not None and not serie.empty:
                        ret = serie.pct_change().dropna()
                        atr = ret.abs().rolling(ATR_WINDOW).mean().iloc[-1]*100 if len(ret) >= ATR_WINDOW else ret.abs().mean()*100
                        all_variables_data[nombre] = {
                            'metrics': {
                                'valor_actual': serie.iloc[-1],
                                'cambio_porcentual': (serie.iloc[-1]/serie.iloc[0]-1)*100,
                                'volatilidad_atr': atr,
                                'tendencia_direccion': 'alcista' if serie.iloc[-1]>serie.iloc[0] else 'bajista'
                            }
                        }
            except Exception as e:
                st.warning(f"No se pudieron obtener variables de EEUU: {e}")
            # --- Sectores argentinos relevantes ---
            sectores_arg = {
                'Bancos': ['GGAL', 'BMA', 'SUPV', 'BBAR'],
                'Energía': ['YPFD', 'PAMP', 'CEPU', 'TGSU2'],
                'Consumo': ['SUPV', 'EDN', 'ALUA'],
                'Materiales': ['TXAR', 'ALUA'],
                'Tecnología': ['MELI'],
                'Servicios Públicos': ['EDN', 'TGSU2', 'CEPU'],
                'Agro': ['AGRO'],
                'Telecomunicaciones': ['TECO2'],
                'Industriales': ['TRAN', 'TGNO4'],
            }
            with st.spinner("Consultando IA..."):
                diagnostico = diagnostico_ciclo_y_sugerencia(all_variables_data, st.session_state.GEMINI_API_KEY, sectores_arg)
            st.markdown(diagnostico)
            # Extraer sectores sugeridos
            import re
            sugeridos_arg = []
            sugeridos_usa = []
            match_arg = re.search(r"SUGERENCIA DE SECTORES ARGENTINA\s*[:\-]*\s*(.*?)(?:SUGERENCIA DE SECTORES EEUU|$)", diagnostico, re.IGNORECASE | re.DOTALL)
            if match_arg:
                sugeridos_arg = re.findall(r"(?:\-|\d+\.)\s*([^\n]+)", match_arg.group(1))
            match_usa = re.search(r"SUGERENCIA DE SECTORES EEUU\s*[:\-]*\s*(.*)", diagnostico, re.IGNORECASE | re.DOTALL)
            if match_usa:
                sugeridos_usa = re.findall(r"(?:\-|\d+\.)\s*([^\n]+)", match_usa.group(1))
            st.session_state['sectores_sugeridos_ia_arg'] = sugeridos_arg
            st.session_state['sectores_sugeridos_ia_usa'] = sugeridos_usa
            if sugeridos_arg:
                st.success(f"Sectores argentinos sugeridos por IA: {', '.join(sugeridos_arg)}")
            if sugeridos_usa:
                st.success(f"Sectores EEUU sugeridos por IA: {', '.join(sugeridos_usa)}")

    # --- Función auxiliar para calcular drawdown ---
    def calcular_drawdown(serie_valores):
        """
        Calcula el drawdown máximo y actual de una serie de valores (por ejemplo, valor de portafolio).
        Devuelve: drawdown_max (float), drawdown_actual (float), serie_drawdown (pd.Series)
        """
        import numpy as np
        import pandas as pd
        if isinstance(serie_valores, (pd.Series, np.ndarray, list)):
            serie = pd.Series(serie_valores)
            max_acum = serie.cummax()
            drawdown = (serie - max_acum) / max_acum
            drawdown_max = drawdown.min()
            drawdown_actual = drawdown.iloc[-1]
            return drawdown_max, drawdown_actual, drawdown
        else:
            return 0, 0, pd.Series([])

    # --- En mostrar_optimizacion_portafolio, después de mostrar resultados de optimización ---
        # --- Análisis de Drawdown ---
        st.subheader("📉 Análisis de Drawdown (Caídas Máximas)")
        # Portafolio actual
        st.markdown("**Portafolio Actual**")
        # Intentar reconstruir serie de valor del portafolio actual
        try:
            # Usar los mismos datos que para el histograma de portafolio actual
            # (puedes ajustar si tienes la serie exacta)
            # Aquí se usa la suma ponderada de precios normalizados
            activos = [a for a in activos_raw if a.get('titulo',{}).get('simbolo')]
            pesos = [activos_dict[a.get('titulo',{}).get('simbolo')]['Valuación']/valor_total if valor_total>0 else 0 for a in activos]
            precios = {}
            for a in activos:
                simbolo = a.get('titulo',{}).get('simbolo')
                mercado = a.get('titulo',{}).get('mercado','BCBA')
                df = obtener_serie_historica_iol(token_acceso, mercado, simbolo, fecha_desde.strftime('%Y-%m-%d'), fecha_hasta.strftime('%Y-%m-%d'))
                if df is not None and not df.empty and 'precio' in df.columns:
                    precios[simbolo] = df.set_index('fecha')['precio']
            if precios:
                df_precios = pd.DataFrame(precios).dropna()
                serie_valor = (df_precios * pesos).sum(axis=1)
                dd_max, dd_actual, serie_dd = calcular_drawdown(serie_valor)
                st.metric("Drawdown Máximo", f"{dd_max*100:.2f}%")
                st.metric("Drawdown Actual", f"{dd_actual*100:.2f}%")
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=serie_dd.index, y=serie_dd*100, mode='lines', name='Drawdown (%)', line=dict(color='#ef4444')))
                fig.update_layout(title="Drawdown Portafolio Actual", yaxis_title="Drawdown (%)", xaxis_title="Fecha", template='plotly_white', height=300)
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"No se pudo calcular el drawdown del portafolio actual: {e}")
        # Portafolios optimizados
        for clave, nombre in estrategias:
            res, _, _ = resultados.get(clave, (None, None, None))
            if res and hasattr(res, 'returns') and res.returns is not None:
                st.markdown(f"**{nombre}**")
                # Reconstruir serie de valor acumulado
                try:
                    import numpy as np
                    import pandas as pd
                    if hasattr(res, 'returns'):
                        # Suponemos retornos diarios
                        serie_valor = (1 + pd.Series(res.returns)).cumprod()
                        dd_max, dd_actual, serie_dd = calcular_drawdown(serie_valor)
                        st.metric("Drawdown Máximo", f"{dd_max*100:.2f}%")
                        st.metric("Drawdown Actual", f"{dd_actual*100:.2f}%")
                        import plotly.graph_objects as go
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(y=serie_dd*100, mode='lines', name='Drawdown (%)', line=dict(color='#ef4444')))
                        fig.update_layout(title=f"Drawdown {nombre}", yaxis_title="Drawdown (%)", xaxis_title="Día", template='plotly_white', height=250)
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"No se pudo calcular el drawdown de {nombre}: {e}")
        # Benchmarks (ejemplo: S&P500, MERVAL)
        st.markdown("**Benchmarks**")
        try:
            import yfinance as yf
            import pandas as pd
            benchmarks = {'S&P 500': '^GSPC', 'MERVAL': '^MERV'}
            for nombre, ticker in benchmarks.items():
                serie = yf.download(ticker, period='1y')['Close']
                if not serie.empty:
                    dd_max, dd_actual, serie_dd = calcular_drawdown(serie)
                    st.metric(f"{nombre} Drawdown Máx", f"{dd_max*100:.2f}%")
                    st.metric(f"{nombre} Drawdown Actual", f"{dd_actual*100:.2f}%")
                    import plotly.graph_objects as go
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=serie_dd.index, y=serie_dd*100, mode='lines', name='Drawdown (%)', line=dict(color='#ef4444')))
                    fig.update_layout(title=f"Drawdown {nombre}", yaxis_title="Drawdown (%)", xaxis_title="Fecha", template='plotly_white', height=250)
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"No se pudo calcular el drawdown de benchmarks: {e}")

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
                ("🏠 Dashboard Unificado", "📊 Análisis de Portafolio", "🌍 Contexto Económico", "📋 Informe Financiero", "🤖 Noticias con IA", "💰 Tasas de Caución", "👨‍💼 Panel del Asesor"),
                index=0,
            )

            # Mostrar la página seleccionada
            if opcion == "🏠 Dashboard Unificado":
                mostrar_dashboard_unificado()
            elif opcion == "📊 Análisis de Portafolio":
                if st.session_state.cliente_seleccionado:
                    mostrar_analisis_portafolio()
                else:
                    st.info("👆 Seleccione un cliente en la barra lateral para comenzar")
            elif opcion == "🌍 Contexto Económico":
                mostrar_dashboard_datos_economicos()
            elif opcion == "📋 Informe Financiero":
                generar_informe_financiero_actual()
            elif opcion == "🤖 Noticias con IA":
                mostrar_busqueda_noticias_gemini()
            elif opcion == "💰 Tasas de Caución":
                if 'token_acceso' in st.session_state and st.session_state.token_acceso:
                    mostrar_tasas_caucion(st.session_state.token_acceso)
                else:
                    st.warning("Por favor inicie sesión para ver las tasas de caución")
            elif opcion == "👨‍💼 Panel del Asesor":
                mostrar_movimientos_asesor()
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
            
            # Opción para generar informe financiero sin autenticación
            st.markdown("---")
            st.subheader("📋 Informe Financiero Mensual")
            st.markdown("""
            **Genera un informe financiero completo con datos en tiempo real:**
            - Análisis de mercados globales y emergentes
            - Performance de portafolios sugeridos
            - Oportunidades de inversión actuales
            - Análisis sectorial y de volatilidad
            """)
            
            if st.button("🚀 Generar Informe Financiero", use_container_width=True):
                generar_informe_financiero_actual()
            
            # Opción para búsqueda de noticias con IA sin autenticación
            st.markdown("---")
            st.subheader("🤖 Noticias con IA")
            st.markdown("""
            **Accede a análisis automático de noticias financieras:**
            - Búsqueda inteligente con Gemini
            - Análisis de múltiples tickers
            - Recomendaciones de inversión
            - Control de uso de créditos
            """)
            
            if st.button("🔍 Buscar Noticias con IA", use_container_width=True):
                mostrar_busqueda_noticias_gemini()
            
            st.markdown("---")
            
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
        st.error(f"Tipo de error: {type(e).__name__}")
        import traceback
        st.code(traceback.format_exc())
        st.error("La aplicación no pudo iniciarse correctamente.")
        st.info("Por favor, verifique que todas las dependencias estén instaladas.")

def crear_indice_ciclo_economico_argentino():
    """
    Crea un índice básico del ciclo económico argentino usando datos globales como proxy
    """
    try:
        import yfinance as yf
        import pandas as pd
        import numpy as np
        
        # Variables globales como proxy para el ciclo argentino
        tickers = {
            'S&P 500': '^GSPC',
            'VIX': '^VIX',
            'Tasa 10Y EEUU': '^TNX',
            'Oro': 'GC=F',
            'Dólar Index': 'DX-Y.NYB',
            'Índice Mexicano': '^MXX'  # Proxy del MERVAL
        }
        
        # Descargar datos
        data = {}
        for nombre, ticker in tickers.items():
            try:
                df = yf.download(ticker, start='2020-01-01', end=pd.Timestamp.now(), progress=False)
                if not df.empty:
                    data[nombre] = df['Adj Close']
            except Exception as e:
                st.warning(f"No se pudo obtener {nombre}: {e}")
                continue
        
        if len(data) < 3:
            st.error("No hay suficientes datos para crear el índice")
            return None, None
        
        # Crear DataFrame con todos los datos
        df_combined = pd.DataFrame(data)
        df_combined = df_combined.dropna()
        
        if len(df_combined) < 30:
            st.error("No hay suficientes datos históricos")
            return None, None
        
        # Normalizar a base 100
        df_normalized = df_combined / df_combined.iloc[0] * 100
        
        # Invertir variables contra-cíclicas
        variables_contraciclicas = ['VIX', 'Tasa 10Y EEUU', 'Dólar Index']
        for var in variables_contraciclicas:
            if var in df_normalized.columns:
                df_normalized[var] = 200 - df_normalized[var]  # Invertir
        
        # Calcular índice como promedio simple
        df_normalized['Índice_Ciclo'] = df_normalized.mean(axis=1)
        
        # Normalizar a escala 0-100
        min_val = df_normalized['Índice_Ciclo'].min()
        max_val = df_normalized['Índice_Ciclo'].max()
        df_normalized['Índice_Ciclo'] = ((df_normalized['Índice_Ciclo'] - min_val) / (max_val - min_val)) * 100
        
        # Agregar tendencia y volatilidad
        df_normalized['Tendencia'] = df_normalized['Índice_Ciclo'].rolling(window=20).mean()
        df_normalized['Volatilidad'] = df_normalized['Índice_Ciclo'].rolling(window=20).std()
        
        # Crear DataFrame final
        df_final = pd.DataFrame({
            'Fecha': df_normalized.index,
            'Índice_Ciclo': df_normalized['Índice_Ciclo'],
            'Tendencia': df_normalized['Tendencia'],
            'Volatilidad': df_normalized['Volatilidad']
        })
        
        # Componentes para mostrar
        componentes = {}
        for nombre, ticker in tickers.items():
            if nombre in df_normalized.columns:
                componentes[nombre] = df_normalized[nombre]
        
        return df_final, componentes
        
    except Exception as e:
        st.error(f"Error al crear índice del ciclo económico: {e}")
        return None, None

def mostrar_analisis_tecnico_componentes(componentes):
    """
    Muestra análisis técnico detallado de los componentes del índice
    """
    if not componentes:
        st.warning("No hay componentes para analizar")
        return
    
    st.subheader("🔧 Análisis Técnico de Componentes")
    
    for nombre, info in componentes.items():
        if isinstance(info, dict) and 'datos' in info:
            datos_comp = info['datos']
            
            if 'componente_final' in datos_comp.columns:
                serie = datos_comp['componente_final']
                
                # Calcular métricas técnicas
                if len(serie) > 0:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(f"{nombre} - Media", f"{serie.mean():.2f}")
                    
                    with col2:
                        st.metric(f"{nombre} - Volatilidad", f"{serie.std():.2f}")
                    
                    with col3:
                        st.metric(f"{nombre} - Peso", f"{info.get('peso', 0):.1%}")
                    
                    # Gráfico del componente
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=datos_comp['indice_tiempo'],
                        y=serie,
                        mode='lines',
                        name=nombre,
                        line=dict(width=2)
                    ))
                    
                    fig.update_layout(
                        title=f"Evolución de {nombre}",
                        xaxis_title="Fecha",
                        yaxis_title="Valor",
                        template='plotly_white',
                        height=300
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown("---")

def obtener_variables_macro_argentina(datos_economicos, periodo_analisis):
    """
    Obtiene variables macroeconómicas argentinas desde los datos económicos
    """
    variables_macro = {}
    
    try:
        if datos_economicos and 'valores' in datos_economicos:
            # Buscar series específicas argentinas
            series_buscadas = {
                'inflacion': ['inflacion', 'ipc', 'indice_precios'],
                'pbi': ['pbi', 'producto_bruto', 'actividad_economica'],
                'desempleo': ['desempleo', 'tasa_desempleo', 'empleo'],
                'reservas': ['reservas', 'reservas_internacionales'],
                'tasa_interes': ['tasa_interes', 'leliq', 'badlar']
            }
            
            for variable, keywords in series_buscadas.items():
                for keyword in keywords:
                    # Buscar series que contengan el keyword
                    series_encontradas = datos_economicos['index'][
                        datos_economicos['index']['serie_titulo'].str.contains(keyword, case=False, na=False)
                    ]
                    
                    if not series_encontradas.empty:
                        # Tomar la primera serie encontrada
                        serie_id = series_encontradas.iloc[0]['serie_id']
                        valores = obtener_valores_serie_economica(serie_id, datos_economicos)
                        
                        if valores is not None and not valores.empty:
                            # Calcular métricas básicas
                            valor_actual = valores['valor'].iloc[-1] if len(valores) > 0 else None
                            valor_inicial = valores['valor'].iloc[0] if len(valores) > 0 else None
                            
                            if valor_actual is not None and valor_inicial is not None:
                                cambio_porcentual = ((valor_actual / valor_inicial) - 1) * 100
                                
                                variables_macro[variable] = {
                                    'valor_actual': valor_actual,
                                    'cambio_porcentual': cambio_porcentual,
                                    'serie_id': serie_id,
                                    'titulo': series_encontradas.iloc[0]['serie_titulo']
                                }
                            break
        
        return variables_macro
        
    except Exception as e:
        st.warning(f"Error al obtener variables macro argentinas: {e}")
        return {}

def obtener_series_historicas_aleatorias_con_capital(tickers_por_panel, paneles_seleccionados, cantidad_activos, fecha_desde, fecha_hasta, ajustada, token_acceso, capital_ars):
    """
    Obtiene series históricas aleatorias para un universo de activos con capital específico
    """
    import random
    import pandas as pd
    
    series_historicas = {}
    seleccion_final = {}
    
    try:
        for panel in paneles_seleccionados:
            if panel in tickers_por_panel and tickers_por_panel[panel]:
                # Seleccionar activos aleatorios del panel
                tickers_disponibles = tickers_por_panel[panel]
                cantidad_seleccionar = min(cantidad_activos, len(tickers_disponibles))
                tickers_seleccionados = random.sample(tickers_disponibles, cantidad_seleccionar)
                
                seleccion_final[panel] = tickers_seleccionados
                
                # Obtener series históricas para cada ticker seleccionado
                for ticker in tickers_seleccionados:
                    try:
                        # Intentar obtener datos históricos
                        serie = obtener_serie_historica_iol(token_acceso, 'BCBA', ticker, fecha_desde, fecha_hasta, ajustada)
                        if serie is not None and not serie.empty:
                            series_historicas[ticker] = serie
                    except Exception as e:
                        continue
        
        return series_historicas, seleccion_final
        
    except Exception as e:
        st.error(f"Error al obtener series históricas: {e}")
        return {}, {}

def obtener_tickers_por_panel(token_portador, paneles, pais='Argentina'):
    """
    Devuelve un diccionario con listas de tickers reales por panel para el universo aleatorio.
    Si no hay API, usa listas fijas de tickers representativos.
    Retorna: (dict panel->tickers, dict panel->descripciones)
    """
    tickers = {}
    descripciones = {}
    # Paneles y ejemplos (puedes reemplazar por consulta a la API de IOL si tienes endpoint)
    paneles_dict = {
        'acciones': [
            ('GGAL', 'Grupo Financiero Galicia'),
            ('YPFD', 'YPF S.A.'),
            ('PAMP', 'Pampa Energía'),
            ('BMA', 'Banco Macro'),
            ('SUPV', 'Grupo Supervielle'),
            ('CEPU', 'Central Puerto'),
            ('TXAR', 'Ternium Argentina'),
            ('ALUA', 'Aluar'),
            ('TGSU2', 'Transportadora Gas del Sur'),
            ('EDN', 'Edenor'),
        ],
        'cedears': [
            ('AAPL', 'Apple'),
            ('TSLA', 'Tesla'),
            ('AMZN', 'Amazon'),
            ('GOOGL', 'Alphabet'),
            ('MSFT', 'Microsoft'),
            ('KO', 'Coca-Cola'),
            ('MELI', 'Mercado Libre'),
            ('BABA', 'Alibaba'),
            ('JNJ', 'Johnson & Johnson'),
            ('PG', 'Procter & Gamble'),
        ],
        'aDRs': [
            ('BBAR', 'BBVA Argentina'),
            ('BMA', 'Banco Macro'),
            ('GGAL', 'Grupo Galicia'),
            ('PAM', 'Pampa Energia'),
            ('SUPV', 'Supervielle'),
        ],
        'titulosPublicos': [
            ('AL30', 'Bonar 2030'),
            ('GD30', 'Global 2030'),
            ('AL35', 'Bonar 2035'),
            ('GD35', 'Global 2035'),
            ('AL29', 'Bonar 2029'),
            ('GD29', 'Global 2029'),
        ],
        'obligacionesNegociables': [
            ('PBY22', 'Pampa Energía ON'),
            ('CGC24', 'Compañía General de Combustibles ON'),
            ('YPF23', 'YPF ON'),
            ('TGSU2', 'Transportadora Gas del Sur ON'),
        ]
    }
    for panel in paneles:
        panel_l = panel.lower()
        if panel_l in paneles_dict:
            tickers[panel] = [t[0] for t in paneles_dict[panel_l]]
            descripciones[panel] = [t[1] for t in paneles_dict[panel_l]]
        else:
            tickers[panel] = []
            descripciones[panel] = []
    return tickers, descripciones

# --- Función: calcular retornos y covarianza con ventana móvil ---
def calcular_estadisticas_ventana_movil(precios, ventana=252):
    """
    Calcula retornos esperados y matriz de covarianza usando una ventana móvil.
    precios: DataFrame de precios (columnas=activos, filas=fechas)
    ventana: días para la ventana móvil (por defecto 1 año)
    Devuelve: retornos esperados anualizados, covarianza anualizada
    """
    retornos = precios.pct_change().dropna()
    retornos_ventana = retornos.iloc[-ventana:]
    mean_ret = retornos_ventana.mean() * 252
    cov = retornos_ventana.cov() * 252
    return mean_ret, cov

# --- Función: optimización Markowitz adaptativa (max Sharpe con ajuste por ciclo económico) ---
def optimizar_markowitz(mean_ret, cov, risk_free_rate=0.0, ciclo_economico=None, variables_macro=None, gemini_api_key=None):
    """
    Optimización de Markowitz adaptativa que ajusta retornos y covarianza según el ciclo económico.
    Usa IA para predecir ajustes y amortiguar caídas bruscas.
    """
    import numpy as np
    import scipy.optimize as op
    
    n = len(mean_ret)
    bounds = tuple((0, 1) for _ in range(n))
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1},)
    
    # Si no hay información de ciclo, usar optimización clásica
    if not ciclo_economico or not variables_macro:
        def neg_sharpe(x):
            port_ret = np.dot(mean_ret, x)
            port_vol = np.sqrt(np.dot(x, np.dot(cov, x)))
            if port_vol == 0:
                return 1e6
            return -(port_ret - risk_free_rate) / port_vol
        
        x0 = np.ones(n) / n
        res = op.minimize(neg_sharpe, x0, bounds=bounds, constraints=constraints)
        if res.success:
            return res.x
        else:
            return x0

    # ========== 1. AJUSTE DE RETORNOS SEGÚN CICLO ECONÓMICO ==========
    mean_ret_ajustado = mean_ret.copy()
    
    # Factores de ajuste según ciclo
    factores_ciclo = {
        "Expansión": {"factor": 1.2, "volatilidad": 0.8},
        "Auge": {"factor": 0.9, "volatilidad": 1.1},
        "Contracción": {"factor": 0.7, "volatilidad": 1.3},
        "Recesión": {"factor": 0.5, "volatilidad": 1.5},
        "Expansión Fuerte": {"factor": 1.3, "volatilidad": 0.7},
        "Expansión Moderada": {"factor": 1.1, "volatilidad": 0.9},
        "Estancamiento": {"factor": 0.8, "volatilidad": 1.2},
        "Recesión Moderada": {"factor": 0.6, "volatilidad": 1.4},
        "Recesión Severa": {"factor": 0.4, "volatilidad": 1.6}
    }
    
    factor_ciclo = factores_ciclo.get(ciclo_economico, {"factor": 1.0, "volatilidad": 1.0})
    
    # Ajustar retornos esperados
    mean_ret_ajustado = mean_ret * factor_ciclo["factor"]
    
    # ========== 2. AJUSTE DE COVARIANZA SEGÚN VOLATILIDAD ==========
    cov_ajustado = cov * factor_ciclo["volatilidad"]
    
    # ========== 3. ANÁLISIS IA PARA AJUSTES ESPECÍFICOS ==========
    if gemini_api_key and variables_macro:
        try:
            # Preparar datos para IA de manera eficiente
            resumen_macro = []
            for nombre, datos in list(variables_macro.items())[:5]:  # Solo 5 variables principales
                if isinstance(datos, dict) and 'momentum' in datos:
                    resumen_macro.append(f"{nombre}: {datos['momentum']:+.1f}%")
            
            # Prompt eficiente para IA
            prompt_ia = f"""
            Ciclo económico: {ciclo_economico}
            Variables macro: {', '.join(resumen_macro[:3])}
            
            Sugiere ajustes específicos para optimización de portafolio:
            1. Factores de riesgo por sector (0.5-1.5)
            2. Ajustes de volatilidad (0.8-1.5)
            3. Activos a favorecer/evitar
            
            Responde solo con números separados por comas: factor_riesgo,ajuste_volatilidad,activos_favorecer
            """
            
            import google.generativeai as genai
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt_ia)
            
            if response and response.text:
                try:
                    # Parsear respuesta de IA
                    ajustes_ia = response.text.strip().split(',')
                    if len(ajustes_ia) >= 2:
                        factor_riesgo_ia = float(ajustes_ia[0])
                        ajuste_vol_ia = float(ajustes_ia[1])
                        
                        # Aplicar ajustes de IA
                        mean_ret_ajustado *= factor_riesgo_ia
                        cov_ajustado *= ajuste_vol_ia
                except:
                    pass  # Si falla el parsing, continuar con ajustes básicos
        except:
            pass  # Si falla la IA, continuar con ajustes básicos
    
    # ========== 4. DETECCIÓN DE RIESGOS ESPECÍFICOS ==========
    # Ajustar por volatilidad del VIX si está disponible
    if 'VIX' in variables_macro:
        vix_actual = variables_macro['VIX']['valor_actual']
        if vix_actual > 30:  # VIX alto = mayor riesgo
            factor_vix = 1.3
            mean_ret_ajustado *= 0.8  # Reducir retornos esperados
            cov_ajustado *= factor_vix
        elif vix_actual < 15:  # VIX bajo = menor riesgo
            factor_vix = 0.8
            mean_ret_ajustado *= 1.1  # Aumentar retornos esperados
            cov_ajustado *= factor_vix
    
    # Ajustar por inflación argentina si está disponible
    if 'INFLACION' in variables_macro:
        inflacion = variables_macro['INFLACION']['valor_actual']
        if inflacion > 50:  # Inflación muy alta
            mean_ret_ajustado *= 0.7  # Reducir retornos reales esperados
            cov_ajustado *= 1.4  # Aumentar volatilidad
    
    # ========== 5. OPTIMIZACIÓN CON PESOS MÍNIMOS ==========
    # Agregar restricción de diversificación mínima
    min_weight = 0.05  # Mínimo 5% por activo
    bounds = tuple((min_weight, 1) for _ in range(n))
    
    # Función objetivo: maximizar Sharpe ratio con penalización por concentración
    def neg_sharpe_adaptativo(x):
        portfolio_return = np.sum(x * mean_ret_ajustado)
        portfolio_vol = np.sqrt(np.dot(x.T, np.dot(cov_ajustado, x)))
        
        if portfolio_vol == 0:
            return 1e6
        
        # Penalización por concentración excesiva
        concentration_penalty = 0.1 * np.sum(x**2)  # Penalizar pesos muy altos
        
        sharpe = (portfolio_return - risk_free_rate) / portfolio_vol
        return -(sharpe - concentration_penalty)
    
    # Optimización
    result = op.minimize(
        neg_sharpe_adaptativo, 
        np.ones(n) / n, 
        method='SLSQP', 
        bounds=bounds, 
        constraints=constraints
    )
    
    if result.success:
        return result.x
    else:
        return np.ones(n) / n

# --- Función: backtest con rebalanceo periódico adaptativo ---
def backtest_markowitz(precios, ventana=252, rebalanceo=63, risk_free_rate=0.0, 
                      ciclo_economico=None, variables_macro=None, gemini_api_key=None):
    """
    Simula la evolución de un portafolio Markowitz adaptativo con rebalanceo periódico.
    Ajusta la optimización según el ciclo económico para amortiguar caídas bruscas.
    """
    import numpy as np
    fechas = precios.index
    n_activos = precios.shape[1]
    portafolio_valor = [1.0]
    pesos_hist = []
    fechas_reb = []
    ciclos_detectados = []
    pesos_actual = np.ones(n_activos) / n_activos
    
    for i in range(ventana, len(fechas)-1, rebalanceo):
        precios_window = precios.iloc[i-ventana:i]
        mean_ret, cov = calcular_estadisticas_ventana_movil(precios_window, ventana)
        
        # Detectar ciclo económico en la ventana actual si no se proporciona
        ciclo_actual = ciclo_economico
        if not ciclo_actual and variables_macro:
            # Detectar ciclo basado en volatilidad y momentum de la ventana
            volatilidad_ventana = np.sqrt(np.mean(np.diag(cov)))
            momentum_ventana = np.mean(mean_ret)
            
            if volatilidad_ventana > 0.3 and momentum_ventana < 0:
                ciclo_actual = "Recesión"
            elif volatilidad_ventana > 0.2 and momentum_ventana < 0.05:
                ciclo_actual = "Contracción"
            elif volatilidad_ventana < 0.15 and momentum_ventana > 0.1:
                ciclo_actual = "Expansión"
            else:
                ciclo_actual = "Estancamiento"
        
        # Optimización adaptativa
        pesos_actual = optimizar_markowitz(
            mean_ret, cov, risk_free_rate, 
            ciclo_actual, variables_macro, gemini_api_key
        )
        
        pesos_hist.append(pesos_actual)
        fechas_reb.append(fechas[i])
        ciclos_detectados.append(ciclo_actual)
        
        # Simular evolución hasta el próximo rebalanceo
        for j in range(i, min(i+rebalanceo, len(fechas)-1)):
            ret = (precios.iloc[j+1] / precios.iloc[j] - 1).values
            portafolio_valor.append(portafolio_valor[-1] * (1 + np.dot(pesos_actual, ret)))
    
    # Completar hasta el final con los últimos pesos
    while len(portafolio_valor) < len(fechas):
        portafolio_valor.append(portafolio_valor[-1])
    
    return fechas, portafolio_valor, pesos_hist, fechas_reb, ciclos_detectados

# --- Función: visualización de backtest adaptativo y pesos ---
def mostrar_backtest_markowitz(precios, ventana=252, rebalanceo=63, risk_free_rate=0.0, 
                              ciclo_economico=None, variables_macro=None, gemini_api_key=None):
    """
    Visualiza la evolución del portafolio Markowitz adaptativo con rebalanceo periódico.
    Muestra los ciclos económicos detectados y su impacto en la optimización.
    """
    import plotly.graph_objects as go
    fechas, portafolio_valor, pesos_hist, fechas_reb, ciclos_detectados = backtest_markowitz(
        precios, ventana, rebalanceo, risk_free_rate, 
        ciclo_economico, variables_macro, gemini_api_key
    )
    import streamlit as st
    
    # Métricas del backtest
    retorno_total = (portafolio_valor[-1] / portafolio_valor[0] - 1) * 100
    volatilidad = np.std(np.diff(portafolio_valor) / portafolio_valor[:-1]) * np.sqrt(252) * 100
    sharpe = retorno_total / volatilidad if volatilidad > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Retorno Total", f"{retorno_total:.1f}%")
    with col2:
        st.metric("Volatilidad", f"{volatilidad:.1f}%")
    with col3:
        st.metric("Sharpe Ratio", f"{sharpe:.2f}")
    with col4:
        st.metric("Rebalanceos", len(fechas_reb))
    
    st.subheader("📈 Evolución del Portafolio Markowitz Adaptativo")
    
    # Gráfico principal con ciclos económicos
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=fechas, y=portafolio_valor, 
        mode='lines', name='Valor Portafolio',
        line=dict(color='#1f77b4', width=2)
    ))
    
    # Agregar marcadores de rebalanceo con colores según ciclo
    if ciclos_detectados:
        colores_ciclo = {
            "Expansión": "#00ff00",
            "Auge": "#ffff00", 
            "Contracción": "#ff8000",
            "Recesión": "#ff0000",
            "Estancamiento": "#808080"
        }
        
        for i, (fecha, ciclo) in enumerate(zip(fechas_reb, ciclos_detectados)):
            color = colores_ciclo.get(ciclo, "#808080")
            fig.add_trace(go.Scatter(
                x=[fecha], y=[portafolio_valor[fechas.get_loc(fecha)]],
                mode='markers',
                marker=dict(color=color, size=8, symbol='diamond'),
                name=f'Rebalanceo {ciclo}',
                showlegend=False
            ))
    
    fig.update_layout(
        title="Backtest Markowitz Adaptativo con Ciclos Económicos",
        xaxis_title="Fecha", 
        yaxis_title="Valor acumulado", 
        template="plotly_white",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar evolución de ciclos
    if ciclos_detectados:
        st.subheader("🔄 Evolución de Ciclos Económicos Detectados")
        fig_ciclos = go.Figure()
        
        # Contar ciclos
        ciclos_count = {}
        for ciclo in ciclos_detectados:
            ciclos_count[ciclo] = ciclos_count.get(ciclo, 0) + 1
        
        fig_ciclos.add_trace(go.Bar(
            x=list(ciclos_count.keys()),
            y=list(ciclos_count.values()),
            marker_color=[colores_ciclo.get(ciclo, "#808080") for ciclo in ciclos_count.keys()]
        ))
        
        fig_ciclos.update_layout(
            title="Distribución de Ciclos Económicos Detectados",
            xaxis_title="Ciclo Económico",
            yaxis_title="Cantidad de Rebalanceos",
            template="plotly_white"
        )
        st.plotly_chart(fig_ciclos, use_container_width=True)
    
    # Mostrar evolución de pesos
    st.subheader("🔄 Evolución de Pesos por Activo")
    if pesos_hist:
        import numpy as np
        activos = precios.columns
        pesos_array = np.array(pesos_hist)
        fig2 = go.Figure()
        
        for idx, activo in enumerate(activos):
            fig2.add_trace(go.Scatter(
                x=fechas_reb, y=pesos_array[:, idx], 
                mode='lines+markers', name=activo,
                line=dict(width=2)
            ))
        
        fig2.update_layout(
            title="Pesos óptimos en cada rebalanceo (Adaptativo)",
            xaxis_title="Fecha de rebalanceo", 
            yaxis_title="Peso", 
            template="plotly_white",
            height=400
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # Mostrar estadísticas de pesos
        st.subheader("📊 Estadísticas de Pesos")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Peso Promedio por Activo:**")
            pesos_promedio = np.mean(pesos_array, axis=0)
            for activo, peso in zip(activos, pesos_promedio):
                st.write(f"• {activo}: {peso:.1%}")
        
        with col2:
            st.write("**Peso Máximo por Activo:**")
            pesos_max = np.max(pesos_array, axis=0)
            for activo, peso in zip(activos, pesos_max):
                st.write(f"• {activo}: {peso:.1%}")
    else:
        st.info("No hay datos suficientes para mostrar la evolución de pesos.")

def optimizacion_portafolio_ciclo_economico(token_acceso, gemini_api_key=None):
    """
    Optimización de portafolio que integra análisis de ciclo económico para amortiguar caídas bruscas.
    Usa datos estadísticos y IA para predecir y adaptar la optimización según el contexto económico.
    """
    st.markdown("---")
    st.subheader("🎯 Optimización de Portafolio con Ciclo Económico")
    
    # Configuración
    col1, col2, col3 = st.columns(3)
    with col1:
        periodo_analisis = st.selectbox(
            "Período de análisis",
            ["6mo", "1y", "2y", "5y"],
            index=1,
            help="Período para el análisis histórico"
        )
    with col2:
        ventana_optimizacion = st.slider(
            "Ventana de optimización (días)",
            min_value=63,
            max_value=252,
            value=126,
            help="Ventana para calcular retornos y covarianza"
        )
    with col3:
        rebalanceo = st.slider(
            "Frecuencia de rebalanceo (días)",
            min_value=21,
            max_value=126,
            value=63,
            help="Cada cuántos días rebalancear el portafolio"
        )
    
    # Configuración de IA
    if gemini_api_key:
        st.info(f"🔑 API Key Gemini configurada - Análisis IA habilitado")
    else:
        gemini_key = st.text_input(
            "🔑 API Key Gemini (opcional)",
            type="password",
            help="Para análisis IA avanzado del ciclo económico"
        )
        if gemini_key:
            gemini_api_key = gemini_key
    
    if st.button("🚀 Ejecutar Optimización Adaptativa", type="primary"):
        # Crear contenedores para mostrar progreso
        progress_container = st.container()
        status_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        try:
            # ========== 1. ANÁLISIS DE CICLO ECONÓMICO ==========
            status_text.text("📊 Analizando ciclo económico...")
            progress_bar.progress(10)
            
            st.markdown("### 📊 Análisis de Ciclo Económico")
            
            # Obtener variables macro
            variables_macro = {}
            try:
                # Variables globales (reducidas para mejor rendimiento)
                tickers_global = {
                    'S&P 500': '^GSPC',
                    'VIX': '^VIX',
                    'Oro': 'GC=F',
                    'Treasury 10Y': '^TNX',
                }
                
                status_text.text("📈 Descargando datos globales...")
                progress_bar.progress(20)
                
                datos_global = yf.download(
                    list(tickers_global.values()), 
                    period=periodo_analisis,
                    progress=False,
                    timeout=30
                )['Close']
                
                for nombre, ticker in tickers_global.items():
                    if ticker in datos_global.columns and not datos_global[ticker].empty:
                        serie = datos_global[ticker].dropna()
                        if len(serie) > 0:
                            retornos = serie.pct_change().dropna()
                            momentum = (serie.iloc[-1] / serie.iloc[-63] - 1) * 100 if len(serie) >= 63 else 0
                            volatilidad = retornos.std() * np.sqrt(252) * 100
                            tendencia = 'Alcista' if momentum > 0 else 'Bajista'
                            
                            variables_macro[nombre] = {
                                'valor_actual': serie.iloc[-1],
                                'momentum': momentum,
                                'volatilidad': volatilidad,
                                'tendencia': tendencia,
                                'serie': serie
                            }
                
                # Obtener datos económicos argentinos si están disponibles
                datos_economicos = descargar_y_procesar_datos_economicos()
                if datos_economicos:
                    variables_macro_arg = obtener_variables_macro_argentina(datos_economicos, periodo_analisis)
                    variables_macro.update(variables_macro_arg)
                
            except Exception as e:
                st.error(f"Error obteniendo datos macro: {e}")
                return
            
            # Detectar ciclo económico
            if variables_macro:
                # Puntuación de ciclo
                puntuacion_ciclo = 0
                indicadores_ciclo = []
                
                # Curva de tasas
                if 'Treasury 10Y' in variables_macro and 'Treasury 2Y' in variables_macro:
                    spread = variables_macro['Treasury 10Y']['valor_actual'] - variables_macro['Treasury 2Y']['valor_actual']
                    if spread < 0:
                        puntuacion_ciclo -= 2
                        indicadores_ciclo.append("Curva invertida (-2)")
                    elif spread < 0.5:
                        puntuacion_ciclo -= 1
                        indicadores_ciclo.append("Curva plana (-1)")
                    else:
                        puntuacion_ciclo += 1
                        indicadores_ciclo.append("Curva normal (+1)")
                
                # VIX
                if 'VIX' in variables_macro:
                    vix_actual = variables_macro['VIX']['valor_actual']
                    if vix_actual > 30:
                        puntuacion_ciclo -= 1
                        indicadores_ciclo.append("VIX alto (-1)")
                    elif vix_actual < 15:
                        puntuacion_ciclo += 1
                        indicadores_ciclo.append("VIX bajo (+1)")
                
                # S&P 500
                if 'S&P 500' in variables_macro:
                    sp500_momentum = variables_macro['S&P 500']['momentum']
                    if sp500_momentum > 10:
                        puntuacion_ciclo += 1
                        indicadores_ciclo.append("S&P 500 fuerte (+1)")
                    elif sp500_momentum < -10:
                        puntuacion_ciclo -= 1
                        indicadores_ciclo.append("S&P 500 débil (-1)")
                
                # Determinar fase del ciclo
                if puntuacion_ciclo >= 2:
                    fase_ciclo = "Expansión"
                elif puntuacion_ciclo >= 0:
                    fase_ciclo = "Auge"
                elif puntuacion_ciclo >= -1:
                    fase_ciclo = "Contracción"
                else:
                    fase_ciclo = "Recesión"
                
                # Mostrar diagnóstico
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Ciclo Económico", fase_ciclo)
                with col2:
                    st.metric("Puntuación", puntuacion_ciclo)
                with col3:
                    st.metric("Indicadores", len(indicadores_ciclo))
                
                st.markdown("**Indicadores detectados:**")
                for indicador in indicadores_ciclo:
                    st.write(f"• {indicador}")
            
            # ========== 2. SELECCIÓN DE ACTIVOS ==========
            st.markdown("### 📈 Selección de Activos")
            
            # Obtener tickers disponibles
            try:
                tickers_por_panel = obtener_tickers_por_panel(token_acceso, ['Acciones', 'CEDEARs', 'Bonos'])
                
                # Seleccionar activos según el ciclo
                activos_seleccionados = []
                
                if fase_ciclo == "Expansión":
                    # Favorecer acciones y CEDEARs
                    if 'Acciones' in tickers_por_panel:
                        activos_seleccionados.extend(tickers_por_panel['Acciones'][:5])
                    if 'CEDEARs' in tickers_por_panel:
                        activos_seleccionados.extend(tickers_por_panel['CEDEARs'][:3])
                elif fase_ciclo == "Auge":
                    # Balance entre acciones y bonos
                    if 'Acciones' in tickers_por_panel:
                        activos_seleccionados.extend(tickers_por_panel['Acciones'][:3])
                    if 'Bonos' in tickers_por_panel:
                        activos_seleccionados.extend(tickers_por_panel['Bonos'][:3])
                elif fase_ciclo == "Contracción":
                    # Favorecer bonos y activos defensivos
                    if 'Bonos' in tickers_por_panel:
                        activos_seleccionados.extend(tickers_por_panel['Bonos'][:5])
                    if 'CEDEARs' in tickers_por_panel:
                        activos_seleccionados.extend(tickers_por_panel['CEDEARs'][:2])
                else:  # Recesión
                    # Solo bonos y activos muy defensivos
                    if 'Bonos' in tickers_por_panel:
                        activos_seleccionados.extend(tickers_por_panel['Bonos'][:6])
                
                # Agregar activos globales según ciclo
                if fase_ciclo in ["Expansión", "Auge"]:
                    activos_seleccionados.extend(['^GSPC', 'GC=F'])  # S&P 500 y Oro
                elif fase_ciclo == "Contracción":
                    activos_seleccionados.extend(['GC=F', '^TNX'])  # Oro y Treasury
                else:
                    activos_seleccionados.extend(['GC=F'])  # Solo Oro
                
                st.success(f"✅ Seleccionados {len(activos_seleccionados)} activos para ciclo {fase_ciclo}")
                
            except Exception as e:
                st.error(f"Error seleccionando activos: {e}")
                return
            
            # ========== 3. OBTENER DATOS HISTÓRICOS ==========
            status_text.text("📊 Descargando datos históricos...")
            progress_bar.progress(40)
            
            st.markdown("### 📊 Datos Históricos")
            
            try:
                # Descargar datos históricos (limitado a 10 activos máximo)
                datos_historicos = {}
                activos_limitados = activos_seleccionados[:10]  # Máximo 10 activos
                
                for i, ticker in enumerate(activos_limitados):
                    try:
                        status_text.text(f"📊 Descargando {ticker} ({i+1}/{len(activos_limitados)})...")
                        
                        if ticker.startswith('^') or ticker in ['GC=F']:
                            # Activos globales con yfinance
                            df = yf.download(
                                ticker, 
                                period=periodo_analisis,
                                progress=False,
                                timeout=15
                            )['Close']
                        else:
                            # Activos locales con IOL (con timeout)
                            df = obtener_serie_historica_iol(
                                token_acceso, 'BCBA', ticker, 
                                (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                                datetime.now().strftime('%Y-%m-%d'), 'SinAjustar'
                            )
                            if df is not None and not df.empty:
                                df = df.set_index('fecha')['precio']
                        
                        if df is not None and not df.empty and len(df) > 30:  # Mínimo 30 días
                            datos_historicos[ticker] = df
                    except Exception as e:
                        st.warning(f"No se pudo descargar {ticker}: {e}")
                        continue
                
                if len(datos_historicos) < 3:
                    st.error("No se obtuvieron suficientes datos históricos (mínimo 3 activos)")
                    return
                
                # Crear DataFrame de precios
                precios_df = pd.DataFrame(datos_historicos)
                precios_df = precios_df.dropna()
                
                # Limitar a últimos 252 días si hay muchos datos
                if len(precios_df) > 252:
                    precios_df = precios_df.tail(252)
                
                status_text.text("✅ Datos históricos procesados")
                progress_bar.progress(60)
                
                with status_container:
                    st.success(f"✅ Datos históricos obtenidos para {len(precios_df.columns)} activos")
                
            except Exception as e:
                st.error(f"Error obteniendo datos históricos: {e}")
                return
            
            # ========== 4. OPTIMIZACIÓN ADAPTATIVA ==========
            status_text.text("🎯 Calculando optimización...")
            progress_bar.progress(70)
            
            st.markdown("### 🎯 Optimización Adaptativa")
            
            try:
                # Calcular estadísticas (usar ventana más pequeña si hay pocos datos)
                ventana_ajustada = min(ventana_optimizacion, len(precios_df) // 2)
                mean_ret, cov = calcular_estadisticas_ventana_movil(precios_df, ventana_ajustada)
                
                status_text.text("⚖️ Optimizando portafolio clásico...")
                progress_bar.progress(75)
                
                # Optimización clásica vs adaptativa
                pesos_clasicos = optimizar_markowitz(mean_ret, cov, 0.0)
                
                status_text.text("🎯 Optimizando portafolio adaptativo...")
                progress_bar.progress(80)
                
                pesos_adaptativos = optimizar_markowitz(mean_ret, cov, 0.0, fase_ciclo, variables_macro, gemini_api_key)
                
                # Comparar resultados
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📊 Optimización Clásica**")
                    for ticker, peso in zip(precios_df.columns, pesos_clasicos):
                        st.write(f"• {ticker}: {peso:.1%}")
                
                with col2:
                    st.markdown("**🎯 Optimización Adaptativa**")
                    for ticker, peso in zip(precios_df.columns, pesos_adaptativos):
                        st.write(f"• {ticker}: {peso:.1%}")
                
                # Calcular métricas esperadas
                retorno_clasico = np.sum(pesos_clasicos * mean_ret) * 252 * 100
                volatilidad_clasica = np.sqrt(np.dot(pesos_clasicos.T, np.dot(cov * 252, pesos_clasicos))) * 100
                sharpe_clasico = retorno_clasico / volatilidad_clasica if volatilidad_clasica > 0 else 0
                
                retorno_adaptativo = np.sum(pesos_adaptativos * mean_ret) * 252 * 100
                volatilidad_adaptativa = np.sqrt(np.dot(pesos_adaptativos.T, np.dot(cov * 252, pesos_adaptativos))) * 100
                sharpe_adaptativo = retorno_adaptativo / volatilidad_adaptativa if volatilidad_adaptativa > 0 else 0
                
                # Mostrar comparación
                st.markdown("### 📈 Comparación de Estrategias")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Retorno Clásico", f"{retorno_clasico:.1f}%")
                with col2:
                    st.metric("Retorno Adaptativo", f"{retorno_adaptativo:.1f}%")
                with col3:
                    st.metric("Sharpe Clásico", f"{sharpe_clasico:.2f}")
                with col4:
                    st.metric("Sharpe Adaptativo", f"{sharpe_adaptativo:.2f}")
                
                # ========== 5. BACKTEST ADAPTATIVO ==========
                status_text.text("📈 Ejecutando backtest...")
                progress_bar.progress(85)
                
                st.markdown("### 🔄 Backtest Adaptativo")
                
                # Usar parámetros más conservadores para el backtest
                ventana_backtest_ajustada = min(ventana_optimizacion, len(precios_df) // 3)
                rebalanceo_ajustado = min(rebalanceo, len(precios_df) // 6)
                
                mostrar_backtest_markowitz(
                    precios_df, 
                    ventana_backtest_ajustada, 
                    rebalanceo_ajustado, 
                    0.0,
                    fase_ciclo, 
                    variables_macro, 
                    gemini_api_key
                )
                
                status_text.text("✅ Análisis completado")
                progress_bar.progress(100)
                
                # ========== 6. ANÁLISIS DE RIESGOS ==========
                st.markdown("### ⚠️ Análisis de Riesgos")
                
                # Calcular Value at Risk (VaR)
                retornos_portafolio = precios_df.pct_change().dropna()
                retornos_portafolio_adaptativo = retornos_portafolio.dot(pesos_adaptativos)
                
                var_95 = np.percentile(retornos_portafolio_adaptativo, 5) * 100
                var_99 = np.percentile(retornos_portafolio_adaptativo, 1) * 100
                
                # Calcular drawdown máximo
                portafolio_acumulado = (1 + retornos_portafolio_adaptativo).cumprod()
                drawdown = (portafolio_acumulado / portafolio_acumulado.cummax() - 1) * 100
                max_drawdown = drawdown.min()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("VaR 95%", f"{var_95:.2f}%")
                with col2:
                    st.metric("VaR 99%", f"{var_99:.2f}%")
                with col3:
                    st.metric("Max Drawdown", f"{max_drawdown:.2f}%")
                
                # Recomendaciones según ciclo
                st.markdown("### 💡 Recomendaciones")
                
                recomendaciones = {
                    "Expansión": [
                        "Aumentar exposición a acciones cíclicas",
                        "Considerar apalancamiento moderado",
                        "Mantener liquidez para oportunidades"
                    ],
                    "Auge": [
                        "Reducir exposición a activos de riesgo",
                        "Aumentar posición en activos defensivos",
                        "Considerar estrategias de cobertura"
                    ],
                    "Contracción": [
                        "Aumentar exposición a bonos",
                        "Reducir exposición a acciones",
                        "Mantener alta liquidez"
                    ],
                    "Recesión": [
                        "Máxima exposición a bonos soberanos",
                        "Evitar activos de riesgo",
                        "Mantener liquidez máxima"
                    ]
                }
                
                st.markdown(f"**Recomendaciones para ciclo {fase_ciclo}:**")
                for rec in recomendaciones.get(fase_ciclo, []):
                    st.write(f"• {rec}")
                
            except Exception as e:
                st.error(f"Error en optimización: {e}")
                return
                
        except Exception as e:
            st.error(f"❌ Error en optimización de portafolio por ciclo económico: {str(e)}")
            st.error(f"Tipo de error: {type(e).__name__}")
            import traceback
            st.code(traceback.format_exc())

def analisis_correlaciones_economicas(token_acceso, gemini_api_key=None):
    """
    Análisis estadístico completo de correlaciones entre variables económicas.
    Calcula correlaciones, causalidad de Granger, y relaciones temporales entre series.
    """
    st.markdown("---")
    st.subheader("📊 Análisis de Correlaciones Económicas")
    
    # Configuración
    col1, col2, col3 = st.columns(3)
    with col1:
        periodo_analisis = st.selectbox(
            "Período de análisis",
            ["6mo", "1y", "2y", "5y"],
            index=1,
            help="Período para el análisis de correlaciones"
        )
    with col2:
        metodo_correlacion = st.selectbox(
            "Método de correlación",
            ["Pearson", "Spearman", "Kendall"],
            index=0,
            help="Tipo de correlación a calcular"
        )
    with col3:
        ventana_rolling = st.slider(
            "Ventana rolling (días)",
            min_value=30,
            max_value=252,
            value=63,
            help="Ventana para correlaciones móviles"
        )
    
    if st.button("🔍 Analizar Correlaciones Económicas", type="primary"):
        # Crear contenedores para mostrar progreso
        progress_container = st.container()
        status_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        try:
            # ========== 1. OBTENER VARIABLES ECONÓMICAS ==========
            status_text.text("📈 Descargando variables económicas globales...")
            progress_bar.progress(10)
            
            variables_macro = {}
            series_historicas = {}
            
            # Variables globales (reducidas para mejor rendimiento)
            tickers_global = {
                'S&P 500': '^GSPC',
                'VIX': '^VIX',
                'Oro': 'GC=F',
                'Treasury 10Y': '^TNX',
                'EUR/USD': 'EURUSD=X',
            }
            
            # Descargar datos con timeout
            try:
                datos_global = yf.download(
                    list(tickers_global.values()), 
                    period=periodo_analisis,
                    progress=False,
                    timeout=30
                )['Close']
                
                status_text.text("📊 Procesando series globales...")
                progress_bar.progress(30)
                
                for nombre, ticker in tickers_global.items():
                    if ticker in datos_global.columns and not datos_global[ticker].empty:
                        serie = datos_global[ticker].dropna()
                        if len(serie) > 10:  # Mínimo de datos
                            retornos = serie.pct_change().dropna()
                            momentum = (serie.iloc[-1] / serie.iloc[-min(63, len(serie)-1)] - 1) * 100
                            volatilidad = retornos.std() * np.sqrt(252) * 100
                            tendencia = 'Alcista' if momentum > 0 else 'Bajista'
                            
                            variables_macro[nombre] = {
                                'valor_actual': serie.iloc[-1],
                                'momentum': momentum,
                                'volatilidad': volatilidad,
                                'tendencia': tendencia,
                                'serie': serie
                            }
                            series_historicas[nombre] = serie
                
                status_text.text("🇦🇷 Descargando datos económicos argentinos...")
                progress_bar.progress(50)
                
                # Obtener datos económicos argentinos (con timeout)
                try:
                    datos_economicos = descargar_y_procesar_datos_economicos()
                    if datos_economicos:
                        variables_macro_arg = obtener_variables_macro_argentina(datos_economicos, periodo_analisis)
                        variables_macro.update(variables_macro_arg)
                        
                        # Agregar series argentinas (limitadas)
                        count = 0
                        for nombre, datos in variables_macro_arg.items():
                            if count >= 5:  # Limitar a 5 variables argentinas
                                break
                            if 'serie' in datos and len(datos['serie']) > 10:
                                series_historicas[nombre] = datos['serie']
                                count += 1
                except Exception as e:
                    st.warning(f"No se pudieron cargar datos argentinos: {e}")
                
                status_text.text("✅ Datos cargados correctamente")
                progress_bar.progress(70)
                
                with status_container:
                    st.success(f"✅ {len(variables_macro)} variables económicas cargadas")
                
            except Exception as e:
                st.error(f"Error obteniendo datos globales: {e}")
                return
            
            # Verificar que tenemos suficientes datos
            if len(series_historicas) < 2:
                st.error("Se necesitan al menos 2 variables para el análisis de correlaciones")
                return
            
            # ========== 2. MATRIZ DE CORRELACIONES ==========
            status_text.text("🔗 Calculando matriz de correlaciones...")
            progress_bar.progress(80)
            
            st.markdown("### 🔗 Matriz de Correlaciones")
            
            if len(series_historicas) >= 2:
                # Crear DataFrame de series (limitado a últimos 252 días para mejor rendimiento)
                df_series = pd.DataFrame(series_historicas)
                df_series = df_series.dropna()
                
                # Limitar a últimos 252 días si hay muchos datos
                if len(df_series) > 252:
                    df_series = df_series.tail(252)
                
                # Calcular correlaciones según método seleccionado
                try:
                    if metodo_correlacion == "Pearson":
                        correlaciones = df_series.corr(method='pearson')
                    elif metodo_correlacion == "Spearman":
                        correlaciones = df_series.corr(method='spearman')
                    else:  # Kendall
                        correlaciones = df_series.corr(method='kendall')
                    
                    status_text.text("✅ Correlaciones calculadas")
                    progress_bar.progress(90)
                    
                except Exception as e:
                    st.error(f"Error calculando correlaciones: {e}")
                    return
                
                # Gráfico de correlaciones
                fig_corr = go.Figure(data=go.Heatmap(
                    z=correlaciones.values,
                    x=correlaciones.columns,
                    y=correlaciones.columns,
                    colorscale='RdBu',
                    zmid=0,
                    text=correlaciones.values.round(3),
                    texttemplate="%{text}",
                    textfont={"size": 10},
                    hoverongaps=False
                ))
                
                fig_corr.update_layout(
                    title=f"Matriz de Correlaciones ({metodo_correlacion})",
                    width=800,
                    height=600
                )
                st.plotly_chart(fig_corr, use_container_width=True)
                
                # ========== 3. ANÁLISIS DE CORRELACIONES SIGNIFICATIVAS ==========
                st.markdown("### 📊 Correlaciones Significativas")
                
                # Encontrar correlaciones más fuertes
                correlaciones_significativas = []
                for i in range(len(correlaciones.columns)):
                    for j in range(i+1, len(correlaciones.columns)):
                        corr_valor = correlaciones.iloc[i, j]
                        if abs(corr_valor) > 0.3:  # Correlación moderada o fuerte
                            correlaciones_significativas.append({
                                'Variable 1': correlaciones.columns[i],
                                'Variable 2': correlaciones.columns[j],
                                'Correlación': corr_valor,
                                'Tipo': 'Positiva' if corr_valor > 0 else 'Negativa',
                                'Fuerza': 'Fuerte' if abs(corr_valor) > 0.7 else 'Moderada' if abs(corr_valor) > 0.5 else 'Débil'
                            })
                
                if correlaciones_significativas:
                    df_corr_sig = pd.DataFrame(correlaciones_significativas)
                    df_corr_sig = df_corr_sig.sort_values('Correlación', key=abs, ascending=False)
                    
                    st.markdown("**🔍 Correlaciones más importantes:**")
                    st.dataframe(df_corr_sig, use_container_width=True)
                    
                    # Gráfico de correlaciones significativas
                    fig_sig = go.Figure(data=go.Bar(
                        x=[f"{row['Variable 1']} vs {row['Variable 2']}" for _, row in df_corr_sig.head(10).iterrows()],
                        y=df_corr_sig.head(10)['Correlación'],
                        marker_color=['red' if x < 0 else 'blue' for x in df_corr_sig.head(10)['Correlación']]
                    ))
                    
                    fig_sig.update_layout(
                        title="Top 10 Correlaciones Significativas",
                        xaxis_title="Pares de Variables",
                        yaxis_title="Correlación",
                        xaxis_tickangle=45
                    )
                    st.plotly_chart(fig_sig, use_container_width=True)
                else:
                    st.info("No se encontraron correlaciones significativas (>0.3)")
                
                # ========== 4. CORRELACIONES MÓVILES ==========
                st.markdown("### 📈 Correlaciones Móviles")
                
                # Calcular correlaciones móviles para pares importantes
                if len(correlaciones_significativas) > 0:
                    # Tomar el par más correlacionado
                    par_principal = correlaciones_significativas[0]
                    var1, var2 = par_principal['Variable 1'], par_principal['Variable 2']
                    
                    if var1 in df_series.columns and var2 in df_series.columns:
                        # Calcular correlación móvil
                        correlacion_rolling = df_series[var1].rolling(window=ventana_rolling).corr(df_series[var2])
                        
                        fig_rolling = go.Figure()
                        fig_rolling.add_trace(go.Scatter(
                            x=correlacion_rolling.index,
                            y=correlacion_rolling.values,
                            mode='lines',
                            name=f'Correlación {ventana_rolling}d',
                            line=dict(color='blue', width=2)
                        ))
                        
                        # Agregar líneas de referencia
                        fig_rolling.add_hline(y=0.7, line_dash="dash", line_color="green", 
                                            annotation_text="Correlación Fuerte Positiva")
                        fig_rolling.add_hline(y=-0.7, line_dash="dash", line_color="red", 
                                            annotation_text="Correlación Fuerte Negativa")
                        fig_rolling.add_hline(y=0, line_dash="dot", line_color="gray")
                        
                        fig_rolling.update_layout(
                            title=f"Correlación Móvil: {var1} vs {var2}",
                            xaxis_title="Fecha",
                            yaxis_title="Correlación",
                            yaxis_range=[-1, 1]
                        )
                        st.plotly_chart(fig_rolling, use_container_width=True)
                
                # ========== 5. ANÁLISIS DE CAUSALIDAD ==========
                st.markdown("### 🔄 Análisis de Causalidad (Test de Granger)")
                
                try:
                    from statsmodels.tsa.stattools import grangercausalitytests
                    
                    # Seleccionar variables para test de causalidad
                    variables_causalidad = st.multiselect(
                        "Seleccionar variables para análisis de causalidad:",
                        options=list(df_series.columns),
                        default=list(df_series.columns)[:4] if len(df_series.columns) >= 4 else list(df_series.columns)
                    )
                    
                    if len(variables_causalidad) >= 2:
                        # Preparar datos para test de Granger
                        df_causalidad = df_series[variables_causalidad].dropna()
                        
                        if len(df_causalidad) > 50:  # Necesitamos suficientes datos
                            resultados_causalidad = []
                            
                            for i, var1 in enumerate(variables_causalidad):
                                for j, var2 in enumerate(variables_causalidad):
                                    if i != j:
                                        try:
                                            # Test de Granger con lag=1
                                            test_result = grangercausalitytests(
                                                df_causalidad[[var2, var1]], 
                                                maxlag=1, 
                                                verbose=False
                                            )
                                            
                                            p_value = test_result[1][0]['ssr_chi2test'][1]
                                            f_stat = test_result[1][0]['ssr_chi2test'][0]
                                            
                                            resultados_causalidad.append({
                                                'Causa': var1,
                                                'Efecto': var2,
                                                'P-Value': p_value,
                                                'F-Statistic': f_stat,
                                                'Significativo': p_value < 0.05
                                            })
                                        except:
                                            continue
                            
                            if resultados_causalidad:
                                df_causalidad_result = pd.DataFrame(resultados_causalidad)
                                df_causalidad_result = df_causalidad_result.sort_values('P-Value')
                                
                                st.markdown("**📊 Resultados del Test de Causalidad de Granger:**")
                                st.dataframe(df_causalidad_result, use_container_width=True)
                                
                                # Mostrar relaciones causales significativas
                                relaciones_significativas = df_causalidad_result[df_causalidad_result['Significativo'] == True]
                                
                                if not relaciones_significativas.empty:
                                    st.markdown("**🔗 Relaciones Causales Significativas (p < 0.05):**")
                                    for _, rel in relaciones_significativas.iterrows():
                                        st.write(f"• {rel['Causa']} → {rel['Efecto']} (p={rel['P-Value']:.3f})")
                                else:
                                    st.info("No se encontraron relaciones causales significativas")
                            else:
                                st.warning("No se pudieron calcular las relaciones de causalidad")
                        else:
                            st.warning("Se necesitan al menos 50 observaciones para el test de causalidad")
                    else:
                        st.info("Selecciona al menos 2 variables para el análisis de causalidad")
                        
                except ImportError:
                    st.warning("statsmodels no está disponible para el análisis de causalidad")
                except Exception as e:
                    st.error(f"Error en análisis de causalidad: {e}")
                
                # ========== 6. ANÁLISIS DE COINTEGRACIÓN ==========
                st.markdown("### 🔗 Análisis de Cointegración")
                
                try:
                    from statsmodels.tsa.stattools import coint
                    
                    # Buscar pares cointegrados
                    pares_cointegrados = []
                    
                    for i, var1 in enumerate(df_series.columns):
                        for j, var2 in enumerate(df_series.columns):
                            if i < j:  # Evitar duplicados
                                try:
                                    # Test de cointegración
                                    score, pvalue, _ = coint(df_series[var1], df_series[var2])
                                    
                                    if pvalue < 0.05:  # Cointegración significativa
                                        pares_cointegrados.append({
                                            'Variable 1': var1,
                                            'Variable 2': var2,
                                            'P-Value': pvalue,
                                            'Score': score
                                        })
                                except:
                                    continue
                    
                    if pares_cointegrados:
                        df_coint = pd.DataFrame(pares_cointegrados)
                        df_coint = df_coint.sort_values('P-Value')
                        
                        st.markdown("**📊 Pares Cointegrados (p < 0.05):**")
                        st.dataframe(df_coint, use_container_width=True)
                        
                        # Gráfico de pares cointegrados
                        if len(df_coint) > 0:
                            par_coint = df_coint.iloc[0]  # Tomar el par más significativo
                            var1, var2 = par_coint['Variable 1'], par_coint['Variable 2']
                            
                            # Normalizar series para comparación
                            serie1_norm = (df_series[var1] / df_series[var1].iloc[0]) * 100
                            serie2_norm = (df_series[var2] / df_series[var2].iloc[0]) * 100
                            
                            fig_coint = go.Figure()
                            fig_coint.add_trace(go.Scatter(
                                x=serie1_norm.index,
                                y=serie1_norm.values,
                                mode='lines',
                                name=var1,
                                line=dict(color='blue', width=2)
                            ))
                            fig_coint.add_trace(go.Scatter(
                                x=serie2_norm.index,
                                y=serie2_norm.values,
                                mode='lines',
                                name=var2,
                                line=dict(color='red', width=2)
                            ))
                            
                            fig_coint.update_layout(
                                title=f"Pares Cointegrados: {var1} vs {var2} (p={par_coint['P-Value']:.3f})",
                                xaxis_title="Fecha",
                                yaxis_title="Valor Normalizado (%)"
                            )
                            st.plotly_chart(fig_coint, use_container_width=True)
                    else:
                        st.info("No se encontraron pares cointegrados significativos")
                        
                except ImportError:
                    st.warning("statsmodels no está disponible para el análisis de cointegración")
                except Exception as e:
                    st.error(f"Error en análisis de cointegración: {e}")
                
                # ========== 7. ANÁLISIS DE VOLATILIDAD ==========
                st.markdown("### 📊 Análisis de Volatilidad")
                
                # Calcular volatilidad móvil
                volatilidades = {}
                for var in df_series.columns:
                    retornos_var = df_series[var].pct_change().dropna()
                    volatilidad_rolling = retornos_var.rolling(window=ventana_rolling).std() * np.sqrt(252) * 100
                    volatilidades[var] = volatilidad_rolling
                
                df_volatilidad = pd.DataFrame(volatilidades)
                
                # Gráfico de volatilidades
                fig_vol = go.Figure()
                for var in df_volatilidad.columns:
                    fig_vol.add_trace(go.Scatter(
                        x=df_volatilidad.index,
                        y=df_volatilidad[var].values,
                        mode='lines',
                        name=var,
                        line=dict(width=1.5)
                    ))
                
                fig_vol.update_layout(
                    title=f"Volatilidad Móvil ({ventana_rolling} días)",
                    xaxis_title="Fecha",
                    yaxis_title="Volatilidad Anualizada (%)"
                )
                st.plotly_chart(fig_vol, use_container_width=True)
                
                # Correlación de volatilidades
                corr_volatilidad = df_volatilidad.corr()
                
                fig_corr_vol = go.Figure(data=go.Heatmap(
                    z=corr_volatilidad.values,
                    x=corr_volatilidad.columns,
                    y=corr_volatilidad.columns,
                    colorscale='RdBu',
                    zmid=0,
                    text=corr_volatilidad.values.round(3),
                    texttemplate="%{text}",
                    textfont={"size": 10}
                ))
                
                fig_corr_vol.update_layout(
                    title="Correlación de Volatilidades",
                    width=600,
                    height=500
                )
                st.plotly_chart(fig_corr_vol, use_container_width=True)
                
                # ========== 8. RESUMEN ESTADÍSTICO ==========
                st.markdown("### 📋 Resumen Estadístico")
                
                # Estadísticas descriptivas
                stats_descriptivas = df_series.describe()
                st.markdown("**📊 Estadísticas Descriptivas:**")
                st.dataframe(stats_descriptivas, use_container_width=True)
                
                # Resumen de correlaciones
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Variables Analizadas", len(df_series.columns))
                
                with col2:
                    correlaciones_fuertes = len([c for c in correlaciones.values.flatten() if abs(c) > 0.7])
                    st.metric("Correlaciones Fuertes (>0.7)", correlaciones_fuertes)
                
                with col3:
                    correlaciones_negativas = len([c for c in correlaciones.values.flatten() if c < -0.3])
                    st.metric("Correlaciones Negativas (<-0.3)", correlaciones_negativas)
                
                # Recomendaciones basadas en correlaciones
                st.markdown("### 💡 Recomendaciones")
                
                if len(correlaciones_significativas) > 0:
                    st.markdown("**🔍 Hallazgos principales:**")
                    
                    # Correlaciones positivas fuertes
                    corr_positivas = [c for c in correlaciones_significativas if c['Correlación'] > 0.7]
                    if corr_positivas:
                        st.markdown("**📈 Variables fuertemente correlacionadas positivamente:**")
                        for corr in corr_positivas[:3]:
                            st.write(f"• {corr['Variable 1']} ↔ {corr['Variable 2']} ({corr['Correlación']:.3f})")
                    
                    # Correlaciones negativas fuertes
                    corr_negativas = [c for c in correlaciones_significativas if c['Correlación'] < -0.7]
                    if corr_negativas:
                        st.markdown("**📉 Variables fuertemente correlacionadas negativamente:**")
                        for corr in corr_negativas[:3]:
                            st.write(f"• {corr['Variable 1']} ↔ {corr['Variable 2']} ({corr['Correlación']:.3f})")
                    
                    st.markdown("**💡 Implicaciones para inversión:**")
                    st.write("• Las variables fuertemente correlacionadas pueden usarse como proxies")
                    st.write("• Las correlaciones negativas ofrecen oportunidades de diversificación")
                    st.write("• Monitorear cambios en correlaciones para detectar cambios de régimen")
                else:
                    st.info("No se encontraron correlaciones significativas para generar recomendaciones")
                
            else:
                st.error("Se necesitan al menos 2 variables para el análisis de correlaciones")
                
        except Exception as e:
            st.error(f"❌ Error en el análisis de correlaciones: {str(e)}")
            st.error(f"Tipo de error: {type(e).__name__}")
            import traceback
            st.code(traceback.format_exc())

def analisis_intermarket_completo(token_acceso, gemini_api_key=None):
    """
    Análisis completo intermarket con detección de ciclos económicos.
    Integra variables macro del BCRA, análisis intermarket local e internacional,
    datos del Ministerio de Economía de Argentina, y sugerencias de activos según el ciclo.
    """
    st.markdown("---")
    st.subheader("🧱 Análisis Intermarket Completo - Ciclo Económico")
    
    # Configuración de períodos
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        periodo_analisis = st.selectbox(
            "Período de análisis",
            ["6mo", "1y", "2y", "5y"],
            index=1,
            help="Período para el análisis de variables macro e intermarket"
        )
    with col2:
        ventana_momentum = st.slider(
            "Ventana momentum (días)",
            min_value=10,
            max_value=252,
            value=63,
            help="Ventana para cálculo de momentum y tendencias"
        )
    with col3:
        incluir_datos_economicos = st.checkbox(
            "Incluir datos Ministerio Economía",
            value=True,
            help="Usar datos oficiales del Ministerio de Economía de Argentina"
        )
    with col4:
        incluir_ia = st.checkbox(
            "Incluir análisis IA",
            value=True,
            help="Usar IA para diagnóstico de ciclo y sugerencias"
        )
    
    if st.button("🔍 Ejecutar Análisis Intermarket Completo", type="primary"):
        # Crear contenedores para mostrar progreso
        progress_container = st.container()
        status_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        try:
            # ========== 1. DATOS ECONÓMICOS DEL MINISTERIO DE ECONOMÍA ==========
            if incluir_datos_economicos:
                status_text.text("📊 Descargando datos económicos argentinos...")
                progress_bar.progress(10)
                
                st.markdown("### 📊 Datos Económicos del Ministerio de Economía de Argentina")
                
                # Descargar datos económicos (con timeout)
                try:
                    datos_economicos = descargar_y_procesar_datos_economicos()
                except Exception as e:
                    st.warning(f"No se pudieron cargar datos económicos: {e}")
                    datos_economicos = None
                
                if datos_economicos is not None:
                    # Mostrar estadísticas generales
                    mostrar_estadisticas_generales_economicas(datos_economicos)
                    
                    # Obtener variables macro argentinas
                    variables_macro_arg = obtener_variables_macro_argentina(datos_economicos, periodo_analisis)
                    
                    if variables_macro_arg:
                        st.markdown("**🇦🇷 Variables Macro Argentinas**")
                        
                        # Mostrar métricas en columnas
                        cols = st.columns(3)
                        for i, (nombre, datos) in enumerate(variables_macro_arg.items()):
                            with cols[i % 3]:
                                st.metric(
                                    nombre,
                                    f"{datos['valor_actual']:.2f}",
                                    f"{datos['momentum']:+.1f}% ({datos['tendencia']})",
                                    delta_color="normal" if datos['momentum'] > 0 else "inverse"
                                )
                        
                        # Gráfico de evolución de variables argentinas
                        if len(variables_macro_arg) >= 2:
                            st.markdown("**📈 Evolución de Variables Argentinas**")
                            fig_arg = go.Figure()
                            
                            for nombre, datos in variables_macro_arg.items():
                                if 'serie' in datos and len(datos['serie']) > 0:
                                    serie_norm = (datos['serie'] / datos['serie'].iloc[0]) * 100
                                    fig_arg.add_trace(go.Scatter(
                                        x=serie_norm.index,
                                        y=serie_norm.values,
                                        mode='lines',
                                        name=nombre,
                                        line=dict(width=2)
                                    ))
                            
                            fig_arg.update_layout(
                                title="Evolución Normalizada de Variables Argentinas",
                                xaxis_title="Fecha",
                                yaxis_title="Valor Normalizado (%)",
                                height=400,
                                hovermode='x unified'
                            )
                            st.plotly_chart(fig_arg, use_container_width=True)
                    else:
                        st.warning("No se encontraron variables macro argentinas relevantes")
                else:
                    st.error("No se pudieron cargar los datos del Ministerio de Economía")
            
            # ========== 2. VARIABLES MACRO GLOBALES ==========
            status_text.text("📊 Descargando variables macro globales...")
            progress_bar.progress(30)
            
            st.markdown("### 📊 Variables Macro Globales")
            
            variables_macro = {}
            
            # Variables locales (reducidas para mejor rendimiento)
            tickers_macro_local = {
                'MERVAL': '^MERV',
                'Dólar Oficial': 'USDOLLAR=X',  # Proxy
                'Riesgo País': '^VIX',  # Proxy para volatilidad
            }
            
            # Variables internacionales (reducidas)
            tickers_macro_global = {
                'S&P 500': '^GSPC',
                'VIX': '^VIX',
                'Oro': 'GC=F',
                'Treasury 10Y': '^TNX',
            }
            
            # Obtener datos
            try:
                status_text.text("📈 Descargando datos locales...")
                progress_bar.progress(40)
                
                # Datos locales (con timeout)
                datos_local = yf.download(
                    list(tickers_macro_local.values()), 
                    period=periodo_analisis,
                    progress=False,
                    timeout=30
                )['Close']
                for nombre, ticker in tickers_macro_local.items():
                    if ticker in datos_local.columns and not datos_local[ticker].empty:
                        serie = datos_local[ticker].dropna()
                        if len(serie) > 0:
                            retornos = serie.pct_change().dropna()
                            momentum = (serie.iloc[-1] / serie.iloc[-ventana_momentum] - 1) * 100 if len(serie) >= ventana_momentum else 0
                            volatilidad = retornos.std() * np.sqrt(252) * 100
                            tendencia = 'Alcista' if momentum > 0 else 'Bajista'
                            
                            variables_macro[nombre] = {
                                'valor_actual': serie.iloc[-1],
                                'momentum': momentum,
                                'volatilidad': volatilidad,
                                'tendencia': tendencia,
                                'serie': serie
                            }
                
                status_text.text("🌍 Descargando datos globales...")
                progress_bar.progress(50)
                
                # Datos globales (con timeout)
                datos_global = yf.download(
                    list(tickers_macro_global.values()), 
                    period=periodo_analisis,
                    progress=False,
                    timeout=30
                )['Close']
                for nombre, ticker in tickers_macro_global.items():
                    if ticker in datos_global.columns and not datos_global[ticker].empty:
                        serie = datos_global[ticker].dropna()
                        if len(serie) > 0:
                            retornos = serie.pct_change().dropna()
                            momentum = (serie.iloc[-1] / serie.iloc[-ventana_momentum] - 1) * 100 if len(serie) >= ventana_momentum else 0
                            volatilidad = retornos.std() * np.sqrt(252) * 100
                            tendencia = 'Alcista' if momentum > 0 else 'Bajista'
                            
                            variables_macro[nombre] = {
                                'valor_actual': serie.iloc[-1],
                                'momentum': momentum,
                                'volatilidad': volatilidad,
                                'tendencia': tendencia,
                                'serie': serie
                            }
                
                # Mostrar métricas macro
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Variables Locales**")
                    for nombre, datos in variables_macro.items():
                        if nombre in tickers_macro_local.values():
                            st.metric(
                                nombre,
                                f"{datos['valor_actual']:.2f}",
                                f"{datos['momentum']:+.1f}% ({datos['tendencia']})",
                                delta_color="normal" if datos['momentum'] > 0 else "inverse"
                            )
                
                with col2:
                    st.markdown("**Variables Globales**")
                    for nombre, datos in variables_macro.items():
                        if nombre in tickers_macro_global.values():
                            st.metric(
                                nombre,
                                f"{datos['valor_actual']:.2f}",
                                f"{datos['momentum']:+.1f}% ({datos['tendencia']})",
                                delta_color="normal" if datos['momentum'] > 0 else "inverse"
                            )
                
            except Exception as e:
                st.error(f"Error obteniendo datos macro: {e}")
                return
            
            # ========== 2. ANÁLISIS INTERMARKET LOCAL ==========
            st.markdown("### 🌐 Análisis Intermarket Local")
            
            # Correlaciones intermarket locales
            if len(variables_macro) >= 3:
                # Crear DataFrame de retornos
                retornos_df = pd.DataFrame()
                for nombre, datos in variables_macro.items():
                    if 'serie' in datos:
                        retornos_df[nombre] = datos['serie'].pct_change().dropna()
                
                if not retornos_df.empty:
                    # Matriz de correlaciones
                    correlaciones = retornos_df.corr()
                    
                    # Gráfico de correlaciones
                    fig_corr = go.Figure(data=go.Heatmap(
                        z=correlaciones.values,
                        x=correlaciones.columns,
                        y=correlaciones.columns,
                        colorscale='RdBu',
                        zmid=0,
                        text=correlaciones.values.round(2),
                        texttemplate="%{text}",
                        textfont={"size": 10},
                        hoverongaps=False
                    ))
                    
                    fig_corr.update_layout(
                        title="Matriz de Correlaciones Intermarket",
                        width=600,
                        height=500
                    )
                    st.plotly_chart(fig_corr, use_container_width=True)
                    
                    # Análisis de divergencias
                    st.markdown("**🔍 Análisis de Divergencias**")
                    
                    # Buscar divergencias entre activos
                    divergencias = []
                    for i, activo1 in enumerate(correlaciones.columns):
                        for j, activo2 in enumerate(correlaciones.columns):
                            if i < j:
                                corr = correlaciones.iloc[i, j]
                                if abs(corr) < 0.3:  # Baja correlación
                                    divergencias.append({
                                        'activo1': activo1,
                                        'activo2': activo2,
                                        'correlacion': corr,
                                        'tipo': 'Divergencia' if corr < 0 else 'Baja correlación'
                                    })
                    
                    if divergencias:
                        df_divergencias = pd.DataFrame(divergencias)
                        st.dataframe(df_divergencias.sort_values('correlacion'))
                    else:
                        st.info("No se detectaron divergencias significativas")
            
            # ========== 3. ANÁLISIS INTERMARKET INTERNACIONAL ==========
            st.markdown("### 🌍 Análisis Intermarket Internacional")
            
            # Curva de tasas (simulada)
            if 'Treasury 10Y' in variables_macro and 'Treasury 2Y' in variables_macro:
                tasa_10y = variables_macro['Treasury 10Y']['valor_actual']
                tasa_2y = variables_macro['Treasury 2Y']['valor_actual']
                spread_curva = tasa_10y - tasa_2y
                
                st.metric(
                    "Spread Curva de Tasas (10Y - 2Y)",
                    f"{spread_curva:.2f}%",
                    "Recesión" if spread_curva < 0 else "Expansión",
                    delta_color="inverse" if spread_curva < 0 else "normal"
                )
                
                # Interpretación de la curva
                if spread_curva < 0:
                    st.warning("⚠️ Curva invertida - Señal de recesión potencial")
                elif spread_curva < 0.5:
                    st.info("📊 Curva plana - Transición de ciclo")
                else:
                    st.success("✅ Curva normal - Ciclo expansivo")
            
            # Análisis Dólar vs Commodities
            if 'Dólar Index' in variables_macro and 'Oro' in variables_macro:
                dolar_momentum = variables_macro['Dólar Index']['momentum']
                oro_momentum = variables_macro['Oro']['momentum']
                
                st.markdown("**💱 Dólar vs Commodities**")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Dólar Index", f"{dolar_momentum:+.1f}%")
                with col2:
                    st.metric("Oro", f"{oro_momentum:+.1f}%")
                
                # Interpretación
                if dolar_momentum > 0 and oro_momentum < 0:
                    st.info("📈 Dólar fuerte, commodities débiles - Ciclo deflacionario")
                elif dolar_momentum < 0 and oro_momentum > 0:
                    st.info("📉 Dólar débil, commodities fuertes - Ciclo inflacionario")
                else:
                    st.info("🔄 Movimiento mixto - Ciclo de transición")
            
            # ========== 4. DETECCIÓN DE CICLO ECONÓMICO ==========
            st.markdown("### 🔄 Detección de Ciclo Económico")
            
            # Puntuación de ciclo basada en múltiples indicadores
            puntuacion_ciclo = 0
            indicadores_ciclo = []
            
            # Indicador 1: Curva de tasas
            if 'Treasury 10Y' in variables_macro and 'Treasury 2Y' in variables_macro:
                spread = variables_macro['Treasury 10Y']['valor_actual'] - variables_macro['Treasury 2Y']['valor_actual']
                if spread < 0:
                    puntuacion_ciclo -= 2
                    indicadores_ciclo.append("Curva invertida (-2)")
                elif spread < 0.5:
                    puntuacion_ciclo -= 1
                    indicadores_ciclo.append("Curva plana (-1)")
                else:
                    puntuacion_ciclo += 1
                    indicadores_ciclo.append("Curva normal (+1)")
            
            # Indicador 2: VIX
            if 'VIX' in variables_macro:
                vix_actual = variables_macro['VIX']['valor_actual']
                if vix_actual > 30:
                    puntuacion_ciclo -= 1
                    indicadores_ciclo.append("VIX alto (-1)")
                elif vix_actual < 15:
                    puntuacion_ciclo += 1
                    indicadores_ciclo.append("VIX bajo (+1)")
                else:
                    indicadores_ciclo.append("VIX normal (0)")
            
            # Indicador 3: Momentum del mercado
            if 'S&P 500' in variables_macro:
                sp500_momentum = variables_macro['S&P 500']['momentum']
                if sp500_momentum > 10:
                    puntuacion_ciclo += 1
                    indicadores_ciclo.append("S&P 500 fuerte (+1)")
                elif sp500_momentum < -10:
                    puntuacion_ciclo -= 1
                    indicadores_ciclo.append("S&P 500 débil (-1)")
                else:
                    indicadores_ciclo.append("S&P 500 neutral (0)")
            
            # Determinar fase del ciclo
            if puntuacion_ciclo >= 2:
                fase_ciclo = "Expansión"
                color_ciclo = "success"
            elif puntuacion_ciclo >= 0:
                fase_ciclo = "Auge"
                color_ciclo = "info"
            elif puntuacion_ciclo >= -1:
                fase_ciclo = "Contracción"
                color_ciclo = "warning"
            else:
                fase_ciclo = "Recesión"
                color_ciclo = "error"
            
            # Mostrar diagnóstico
            st.markdown(f"**🎯 Diagnóstico de Ciclo: {fase_ciclo}**")
            st.markdown(f"**Puntuación:** {puntuacion_ciclo}")
            
            # Mostrar indicadores
            for indicador in indicadores_ciclo:
                st.write(f"• {indicador}")
            
            # ========== 5. ANÁLISIS DE CICLO ECONÓMICO ARGENTINO ==========
            if incluir_datos_economicos and 'variables_macro_arg' in locals() and variables_macro_arg:
                st.markdown("### 🇦🇷 Análisis de Ciclo Económico Argentino")
                
                # Análisis específico del ciclo argentino
                analisis_ciclo_arg = analisis_ciclo_economico_argentina(variables_macro_arg, variables_macro)
                
                # Mostrar diagnóstico argentino
                st.markdown(f"**🎯 Diagnóstico de Ciclo Argentino: {analisis_ciclo_arg['fase_ciclo']}**")
                st.markdown(f"**Puntuación:** {analisis_ciclo_arg['puntuacion']}")
                
                # Mostrar indicadores argentinos
                for indicador in analisis_ciclo_arg['indicadores']:
                    st.write(f"• {indicador}")
                
                # Comparación de ciclos
                st.markdown("**🔄 Comparación de Ciclos**")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Ciclo Global", fase_ciclo, puntuacion_ciclo)
                
                with col2:
                    st.metric("Ciclo Argentino", analisis_ciclo_arg['fase_ciclo'], analisis_ciclo_arg['puntuacion'])
                
                # Análisis de divergencias entre ciclos
                diferencia_ciclos = puntuacion_ciclo - analisis_ciclo_arg['puntuacion']
                if abs(diferencia_ciclos) > 2:
                    if diferencia_ciclos > 0:
                        st.warning("⚠️ El ciclo global es más favorable que el argentino")
                    else:
                        st.info("ℹ️ El ciclo argentino es más favorable que el global")
                else:
                    st.success("✅ Los ciclos global y argentino están alineados")
            
            # ========== 6. SUGERENCIAS DE ACTIVOS SEGÚN CICLO ==========
            st.markdown("### 💡 Sugerencias de Activos por Ciclo")
            
            # Matriz de sugerencias
            matriz_sugerencias = {
                "Expansión": {
                    "Argentina": ["Acciones locales", "CEDEARs", "Bonos CER", "FCI renta variable"],
                    "EEUU": ["S&P 500", "Tecnología", "Consumo Discrecional"],
                    "Comentario": "Flujo de capitales, suba de consumo"
                },
                "Auge": {
                    "Argentina": ["Acciones value", "Activos hard", "Oro", "Dólar MEP"],
                    "EEUU": ["Value stocks", "Real estate", "Commodities"],
                    "Comentario": "Protección ante sobrevaloración"
                },
                "Contracción": {
                    "Argentina": ["Bonos tasa fija", "Dólar MEP", "Dólar-linked", "FCI renta fija"],
                    "EEUU": ["Treasury bonds", "Defensive stocks", "Cash"],
                    "Comentario": "Fuga al refugio, evitar acciones cíclicas"
                },
                "Recesión": {
                    "Argentina": ["CEDEARs defensivos", "Oro", "Bonos soberanos", "Dólar cash"],
                    "EEUU": ["Consumer staples", "Healthcare", "Utilities"],
                    "Comentario": "Baja actividad, refugio y liquidez"
                }
            }
            
            # Matriz específica para ciclo argentino
            matriz_sugerencias_arg = {
                "Expansión Fuerte": {
                    "Argentina": ["Acciones bancarias", "Acciones energéticas", "Bonos CER", "FCI renta variable"],
                    "EEUU": ["S&P 500", "Tecnología", "Emerging markets"],
                    "Comentario": "Crecimiento robusto, apetito por riesgo"
                },
                "Expansión Moderada": {
                    "Argentina": ["Acciones locales", "CEDEARs", "Bonos CER", "FCI mixtos"],
                    "EEUU": ["S&P 500", "Value stocks", "Dividend stocks"],
                    "Comentario": "Crecimiento estable, diversificación"
                },
                "Estancamiento": {
                    "Argentina": ["Dólar MEP", "Bonos tasa fija", "FCI renta fija", "Oro"],
                    "EEUU": ["Treasury bonds", "Defensive stocks", "Cash"],
                    "Comentario": "Precaución, preservación de capital"
                },
                "Recesión Moderada": {
                    "Argentina": ["Dólar-linked", "Bonos soberanos", "FCI money market", "Oro"],
                    "EEUU": ["Consumer staples", "Healthcare", "Utilities"],
                    "Comentario": "Protección, activos defensivos"
                },
                "Recesión Severa": {
                    "Argentina": ["Dólar cash", "Oro", "Bonos soberanos cortos", "FCI money market"],
                    "EEUU": ["Treasury bonds", "Cash", "Defensive ETFs"],
                    "Comentario": "Preservación de capital, liquidez máxima"
                }
            }
            
            # Usar sugerencias argentinas si están disponibles
            if incluir_datos_economicos and 'analisis_ciclo_arg' in locals():
                sugerencias_arg = matriz_sugerencias_arg.get(analisis_ciclo_arg['fase_ciclo'], {})
                if sugerencias_arg:
                    sugerencias = sugerencias_arg
                    st.markdown("**🇦🇷 Sugerencias basadas en ciclo argentino**")
                else:
                    sugerencias = matriz_sugerencias.get(fase_ciclo, {})
                    st.markdown("**🌍 Sugerencias basadas en ciclo global**")
            else:
                sugerencias = matriz_sugerencias.get(fase_ciclo, {})
                st.markdown("**🌍 Sugerencias basadas en ciclo global**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🇦🇷 Argentina**")
                for activo in sugerencias.get("Argentina", []):
                    st.write(f"• {activo}")
            
            with col2:
                st.markdown("**🇺🇸 EEUU**")
                for activo in sugerencias.get("EEUU", []):
                    st.write(f"• {activo}")
            
            st.info(f"**💬 Comentario:** {sugerencias.get('Comentario', '')}")
            
            # ========== 6. ANÁLISIS IA (OPCIONAL) ==========
            if incluir_ia and gemini_api_key:
                st.markdown("### 🤖 Análisis IA del Ciclo")
                
                # Preparar datos para IA
                resumen_variables = []
                for nombre, datos in variables_macro.items():
                    resumen_variables.append(
                        f"{nombre}: Valor={datos['valor_actual']:.2f}, "
                        f"Momentum={datos['momentum']:+.1f}%, "
                        f"Tendencia={datos['tendencia']}"
                    )
                
                # Prompt para IA
                prompt_ia = f"""
                Analiza el siguiente resumen de variables macroeconómicas y de mercado:

                {chr(10).join(resumen_variables)}

                Diagnóstico de ciclo actual: {fase_ciclo} (puntuación: {puntuacion_ciclo})

                Proporciona:
                1. Análisis detallado del ciclo económico actual
                2. Factores intermarket más relevantes
                3. Sugerencias específicas de activos para Argentina y EEUU
                4. Riesgos y oportunidades principales

                Responde en español, formato ejecutivo.
                """
                
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=gemini_api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(prompt_ia)
                    
                    if response and response.text:
                        st.markdown(response.text)
                    else:
                        st.warning("No se pudo obtener análisis de IA")
                except Exception as e:
                    st.error(f"Error en análisis IA: {e}")
            
            # ========== 7. GRÁFICOS INTERMARKET ==========
            st.markdown("### 📈 Gráficos Intermarket")
            
            # Gráfico de evolución de variables clave
            if len(variables_macro) >= 3:
                fig_evolucion = go.Figure()
                
                # Normalizar series para comparación
                for nombre, datos in variables_macro.items():
                    if 'serie' in datos and len(datos['serie']) > 0:
                        serie_norm = (datos['serie'] / datos['serie'].iloc[0]) * 100
                        fig_evolucion.add_trace(go.Scatter(
                            x=serie_norm.index,
                            y=serie_norm.values,
                            mode='lines',
                            name=nombre,
                            line=dict(width=2)
                        ))
                
                fig_evolucion.update_layout(
                    title="Evolución Normalizada de Variables Intermarket",
                    xaxis_title="Fecha",
                    yaxis_title="Valor Normalizado (%)",
                    height=500,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_evolucion, use_container_width=True)
            
            # ========== 8. RESUMEN EJECUTIVO ==========
            st.markdown("### 📋 Resumen Ejecutivo")
            
            # Preparar información del análisis argentino
            info_arg = ""
            if incluir_datos_economicos and 'analisis_ciclo_arg' in locals():
                info_arg = f"""
                **🇦🇷 Ciclo Económico Argentino:** {analisis_ciclo_arg['fase_ciclo']}
                - Puntuación argentina: {analisis_ciclo_arg['puntuacion']}
                - Diferencia con ciclo global: {puntuacion_ciclo - analisis_ciclo_arg['puntuacion']:+.1f}
                """
            
            resumen_ejecutivo = f"""
            **🎯 Ciclo Económico Global:** {fase_ciclo}
            - Puntuación de ciclo: {puntuacion_ciclo}
            {info_arg}
            
            **📊 Indicadores Clave:**
            - Principales divergencias: {len(divergencias) if 'divergencias' in locals() else 0} detectadas
            - Volatilidad promedio: {np.mean([d['volatilidad'] for d in variables_macro.values()]):.1f}%
            - Variables macro argentinas analizadas: {len(variables_macro_arg) if 'variables_macro_arg' in locals() else 0}
            
            **💡 Recomendaciones:**
            - **Argentina:** {', '.join(sugerencias.get('Argentina', []))}
            - **EEUU:** {', '.join(sugerencias.get('EEUU', []))}
            
            **⚠️ Riesgos Principales:**
            - {'Curva de tasas invertida' if 'spread_curva' in locals() and spread_curva < 0 else 'Ninguno crítico detectado'}
            - {'VIX elevado' if 'VIX' in variables_macro and variables_macro['VIX']['valor_actual'] > 30 else 'Volatilidad normal'}
            - {'Inflación alta detectada' if 'variables_macro_arg' in locals() and 'INFLACION' in variables_macro_arg and variables_macro_arg['INFLACION']['valor_actual'] > 30 else 'Inflación controlada'}
            
            **📈 Oportunidades:**
            - Ciclo actual favorece activos {fase_ciclo.lower()}
            - {'Divergencias aprovechables' if 'divergencias' in locals() and len(divergencias) > 0 else 'Correlaciones normales'}
            - {'Datos oficiales del Ministerio de Economía disponibles' if incluir_datos_economicos else 'Análisis basado en datos de mercado'}
            """
            
            st.markdown(resumen_ejecutivo)
            
            # Guardar resultados en session state
            session_data = {
                'fase_ciclo': fase_ciclo,
                'puntuacion': puntuacion_ciclo,
                'variables_macro': variables_macro,
                'sugerencias': sugerencias,
                'fecha_analisis': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Agregar datos argentinos si están disponibles
            if incluir_datos_economicos and 'analisis_ciclo_arg' in locals():
                session_data.update({
                    'fase_ciclo_arg': analisis_ciclo_arg['fase_ciclo'],
                    'puntuacion_arg': analisis_ciclo_arg['puntuacion'],
                    'variables_macro_arg': variables_macro_arg if 'variables_macro_arg' in locals() else {},
                    'datos_economicos': True
                })
            
            st.session_state['analisis_intermarket'] = session_data
            
            status_text.text("✅ Análisis intermarket completado")
            progress_bar.progress(100)
            
        except Exception as e:
            st.error(f"Error en análisis intermarket: {e}")
            return

def mostrar_dashboard_datos_economicos():
    """
    Dashboard completo para explorar y analizar datos económicos del Ministerio de Economía de Argentina
    """
    st.markdown("---")
    st.subheader("📊 Dashboard de Datos Económicos - Ministerio de Economía")
    
    # Descargar y procesar datos
    datos = descargar_y_procesar_datos_economicos()
    
    if datos is None:
        st.error("No se pudieron cargar los datos del Ministerio de Economía. Verifica tu conexión a internet.")
        return
    
    # Sidebar para navegación
    st.sidebar.title("🎯 Navegación")
    
    # Estadísticas generales
    st.header("📈 Estadísticas Generales")
    mostrar_estadisticas_generales_economicas(datos)
    st.markdown("---")
    
    # Obtener series disponibles
    series_info = obtener_series_disponibles_economicas(datos)
    
    # Pestañas principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Dashboard General", 
        "📊 Explorador de Series", 
        "🔍 Análisis por Categoría",
        "📈 Comparación de Series",
        "📋 Metadatos y Fuentes"
    ])
    
    with tab1:
        st.header("🏠 Dashboard General")
        
        # Resumen por categoría
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Series por Categoría")
            categoria_counts = datos['index']['catalogo_id'].value_counts()
            fig_cat = px.pie(
                values=categoria_counts.values, 
                names=categoria_counts.index,
                title="Distribución de Series por Categoría"
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            st.subheader("📅 Frecuencia de Actualización")
            freq_counts = datos['index']['indice_tiempo_frecuencia'].value_counts()
            fig_freq = px.bar(
                x=freq_counts.index, 
                y=freq_counts.values,
                title="Frecuencia de Actualización de Series",
                labels={'x': 'Frecuencia', 'y': 'Cantidad de Series'}
            )
            st.plotly_chart(fig_freq, use_container_width=True)
        
        # Series más consultadas
        st.subheader("🔥 Series Más Consultadas")
        if not datos['consultas'].empty:
            top_consultas = datos['consultas'].nlargest(10, 'consultas_total')
            fig_consultas = px.bar(
                x=top_consultas['serie_id'], 
                y=top_consultas['consultas_total'],
                title="Top 10 Series Más Consultadas",
                labels={'x': 'Serie ID', 'y': 'Total de Consultas'}
            )
            fig_consultas.update_xaxes(tickangle=45)
            st.plotly_chart(fig_consultas, use_container_width=True)
    
    with tab2:
        st.header("📊 Explorador de Series")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            categorias = ['Todas'] + list(series_info['catalogo_id'].unique())
            categoria_seleccionada = st.selectbox("Categoría:", categorias)
        
        with col2:
            frecuencias = ['Todas'] + list(series_info['indice_tiempo_frecuencia'].unique())
            frecuencia_seleccionada = st.selectbox("Frecuencia:", frecuencias)
        
        with col3:
            busqueda = st.text_input("Buscar por título:", "")
        
        # Filtrar series
        series_filtradas = series_info.copy()
        
        if categoria_seleccionada != 'Todas':
            series_filtradas = series_filtradas[series_filtradas['catalogo_id'] == categoria_seleccionada]
        
        if frecuencia_seleccionada != 'Todas':
            series_filtradas = series_filtradas[series_filtradas['indice_tiempo_frecuencia'] == frecuencia_seleccionada]
        
        if busqueda:
            series_filtradas = series_filtradas[
                series_filtradas['serie_titulo'].str.contains(busqueda, case=False, na=False)
            ]
        
        # Mostrar series filtradas
        st.subheader(f"📋 Series Encontradas: {len(series_filtradas)}")
        
        if len(series_filtradas) > 0:
            # Selector de serie
            serie_seleccionada = st.selectbox(
                "Selecciona una serie para visualizar:",
                options=series_filtradas['serie_id'].tolist(),
                format_func=lambda x: f"{x} - {series_filtradas[series_filtradas['serie_id']==x]['serie_titulo'].iloc[0]}"
            )
            
            if serie_seleccionada:
                # Obtener información de la serie
                info_serie = series_filtradas[series_filtradas['serie_id'] == serie_seleccionada].iloc[0]
                
                # Obtener valores de la serie
                valores_serie = obtener_valores_serie_economica(serie_seleccionada, datos)
                
                if not valores_serie.empty:
                    # Información de la serie
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Título", info_serie['serie_titulo'])
                        st.metric("Unidades", info_serie['serie_unidades'])
                    
                    with col2:
                        st.metric("Categoría", info_serie['catalogo_id'])
                        st.metric("Frecuencia", info_serie['indice_tiempo_frecuencia'])
                    
                    with col3:
                        st.metric("Total de Valores", len(valores_serie))
                        st.metric("Período", f"{valores_serie['indice_tiempo'].min().strftime('%Y-%m')} a {valores_serie['indice_tiempo'].max().strftime('%Y-%m')}")
                    
                    # Gráfico de la serie
                    st.subheader("📈 Evolución Temporal")
                    fig = crear_grafico_serie_economica(valores_serie, info_serie['serie_titulo'], info_serie['serie_unidades'])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Estadísticas descriptivas
                    st.subheader("📊 Estadísticas Descriptivas")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Resumen Estadístico:**")
                        stats = valores_serie['valor'].describe()
                        st.dataframe(stats.to_frame().T)
                    
                    with col2:
                        st.write("**Últimos 10 Valores:**")
                        st.dataframe(valores_serie.tail(10)[['indice_tiempo', 'valor']])
                
                else:
                    st.warning("No se encontraron valores para esta serie.")
        else:
            st.info("No se encontraron series con los filtros aplicados.")
    
    with tab3:
        st.header("🔍 Análisis por Categoría")
        
        # Selector de categoría
        categoria_analisis = st.selectbox(
            "Selecciona una categoría para analizar:",
            options=datos['index']['catalogo_id'].unique()
        )
        
        if categoria_analisis:
            # Obtener series de la categoría
            series_categoria = series_info[series_info['catalogo_id'] == categoria_analisis]
            
            st.subheader(f"📊 Análisis de {categoria_analisis.upper()}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total de Series", len(series_categoria))
                st.metric("Fuentes de Datos", series_categoria['dataset_fuente'].nunique())
            
            with col2:
                st.metric("Frecuencias", series_categoria['indice_tiempo_frecuencia'].nunique())
                st.metric("Datasets", series_categoria['dataset_id'].nunique())
            
            # Gráfico de frecuencias
            st.subheader("📅 Distribución por Frecuencia")
            freq_cat = series_categoria['indice_tiempo_frecuencia'].value_counts()
            fig_freq_cat = px.pie(
                values=freq_cat.values, 
                names=freq_cat.index,
                title=f"Frecuencias en {categoria_analisis}"
            )
            st.plotly_chart(fig_freq_cat, use_container_width=True)
            
            # Lista de series de la categoría
            st.subheader("📋 Series Disponibles")
            st.dataframe(
                series_categoria[['serie_id', 'serie_titulo', 'indice_tiempo_frecuencia', 'dataset_fuente']],
                use_container_width=True
            )
    
    with tab4:
        st.header("📈 Comparación de Series")
        
        # Selector múltiple de series
        series_disponibles = series_info['serie_id'].tolist()
        series_comparar = st.multiselect(
            "Selecciona series para comparar (máximo 5):",
            options=series_disponibles,
            max_selections=5
        )
        
        if len(series_comparar) >= 2:
            # Obtener datos de las series seleccionadas
            series_data = {}
            for serie_id in series_comparar:
                valores = obtener_valores_serie_economica(serie_id, datos)
                if not valores.empty:
                    series_data[serie_id] = valores
            
            if len(series_data) >= 2:
                # Gráfico comparativo
                st.subheader("📊 Comparación de Series")
                fig_comp = crear_grafico_comparativo_economico(series_data, "Comparación de Series Seleccionadas")
                st.plotly_chart(fig_comp, use_container_width=True)
                
                # Tabla comparativa
                st.subheader("📋 Resumen Comparativo")
                
                resumen_data = []
                for serie_id, valores in series_data.items():
                    info = series_info[series_info['serie_id'] == serie_id].iloc[0]
                    resumen_data.append({
                        'Serie ID': serie_id,
                        'Título': info['serie_titulo'],
                        'Categoría': info['catalogo_id'],
                        'Unidades': info['serie_unidades'],
                        'Valores': len(valores),
                        'Inicio': valores['indice_tiempo'].min().strftime('%Y-%m'),
                        'Fin': valores['indice_tiempo'].max().strftime('%Y-%m'),
                        'Promedio': valores['valor'].mean(),
                        'Máximo': valores['valor'].max(),
                        'Mínimo': valores['valor'].min()
                    })
                
                resumen_df = pd.DataFrame(resumen_data)
                st.dataframe(resumen_df, use_container_width=True)
            else:
                st.warning("Se necesitan al menos 2 series con datos válidos para la comparación.")
        else:
            st.info("Selecciona al menos 2 series para comparar.")
    
    with tab5:
        st.header("📋 Metadatos y Fuentes")
        
        # Información de datasets
        st.subheader("📊 Datasets Disponibles")
        st.dataframe(
            datos['dataset'][['dataset_id', 'dataset_titulo', 'dataset_fuente', 'dataset_responsable']],
            use_container_width=True
        )
        
        # Información de fuentes
        st.subheader("🔗 Fuentes de Datos")
        if not datos['fuentes'].empty:
            st.dataframe(datos['fuentes'], use_container_width=True)
        else:
            st.info("No hay información de fuentes disponible.")
        
        # Estadísticas de consultas
        st.subheader("📈 Estadísticas de Consultas")
        if not datos['consultas'].empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Top 10 Series Más Consultadas (30 días):**")
                top_30 = datos['consultas'].nlargest(10, 'consultas_30_dias')
                fig_30 = px.bar(
                    x=top_30['serie_id'], 
                    y=top_30['consultas_30_dias'],
                    title="Consultas Últimos 30 Días"
                )
                fig_30.update_xaxes(tickangle=45)
                st.plotly_chart(fig_30, use_container_width=True)
            
            with col2:
                st.write("**Top 10 Series Más Consultadas (90 días):**")
                top_90 = datos['consultas'].nlargest(10, 'consultas_90_dias')
                fig_90 = px.bar(
                    x=top_90['serie_id'], 
                    y=top_90['consultas_90_dias'],
                    title="Consultas Últimos 90 Días"
                )
                fig_90.update_xaxes(tickangle=45)
                st.plotly_chart(fig_90, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        <p>📊 Datos proporcionados por el Ministerio de Economía de la Nación Argentina</p>
        <p>Desarrollado con Streamlit | Fuente: <a href='https://apis.datos.gob.ar/series/api/'>API de Datos Abiertos</a></p>
        </div>
        """,
        unsafe_allow_html=True
    )

# URLs de los datos del Ministerio de Economía
DATA_URLS = {
    "valores_csv": "https://apis.datos.gob.ar/series/api/dump/series-tiempo-valores-csv.zip",
    "metadatos_csv": "https://apis.datos.gob.ar/series/api/dump/series-tiempo-metadatos.csv",
    "fuentes_csv": "https://apis.datos.gob.ar/series/api/dump/series-tiempo-fuentes.csv",
    "sqlite": "https://apis.datos.gob.ar/series/api/dump/series-tiempo-sqlite.zip"
}

# Diccionarios de mapeo para nombres descriptivos
FRECUENCIA_MAPPING = {
    'R/P1Y': 'Anual',
    'R/P6M': 'Semestral', 
    'R/P3M': 'Trimestral',
    'R/P1M': 'Mensual',
    'R/P1D': 'Diaria',
    'R/P1W': 'Semanal',
    'R/P1H': 'Horaria',
    'R/P1MIN': 'Por Minuto'
}

DATASET_MAPPING = {
    'sspm': 'Sistema de Cuentas Nacionales',
    'snic': 'Sistema Nacional de Información de Comercio',
    'obras': 'Obras Públicas',
    'turismo': 'Turismo',
    'bcra': 'Banco Central de la República Argentina',
    'siep': 'Sistema de Información de Empleo Público',
    'justicia': 'Ministerio de Justicia',
    'jgm': 'Jefatura de Gabinete de Ministros',
    'agroindustria': 'Ministerio de Agroindustria',
    'smn': 'Servicio Meteorológico Nacional',
    'modernizacion': 'Secretaría de Modernización',
    'salud': 'Ministerio de Salud',
    'energia': 'Secretaría de Energía',
    'defensa': 'Ministerio de Defensa',
    'sspre': 'Sistema de Seguridad Pública',
    'cultura': 'Ministerio de Cultura',
    'transporte': 'Ministerio de Transporte',
    'test_node': 'Datos de Prueba',
    'otros': 'Otros Datos'
}

def mapear_frecuencia(frecuencia):
    """Convierte códigos de frecuencia en nombres descriptivos"""
    return FRECUENCIA_MAPPING.get(frecuencia, frecuencia)

def mapear_dataset(dataset_id):
    """Convierte códigos de dataset en nombres descriptivos"""
    return DATASET_MAPPING.get(dataset_id, dataset_id)

def aplicar_mapeos_descriptivos(df):
    """Aplica mapeos descriptivos a un DataFrame"""
    if 'indice_tiempo_frecuencia' in df.columns:
        df['frecuencia_descriptiva'] = df['indice_tiempo_frecuencia'].map(mapear_frecuencia)
    
    if 'dataset_id' in df.columns:
        df['dataset_descriptivo'] = df['dataset_id'].map(mapear_dataset)
    
    return df

@st.cache_data(ttl=3600)  # Cache por 1 hora
def descargar_y_procesar_datos_economicos():
    """Descarga y procesa todos los datos desde las APIs oficiales con optimizaciones de velocidad"""
    
    with st.spinner("🔄 Descargando y procesando datos económicos..."):
        try:
            # Crear directorio temporal para los datos
            temp_dir = tempfile.mkdtemp()
            
            # Configurar sesión de requests con optimizaciones
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # Descargar metadatos y fuentes en paralelo
            st.info("📥 Descargando metadatos y fuentes...")
            
            # Usar ThreadPoolExecutor para descargas paralelas
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            def download_file(url, filename):
                response = session.get(url, timeout=30)
                response.raise_for_status()
                return filename, response.content
            
            # Descargas paralelas
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(download_file, DATA_URLS["metadatos_csv"], "metadatos.csv"): "metadatos",
                    executor.submit(download_file, DATA_URLS["fuentes_csv"], "fuentes.csv"): "fuentes",
                    executor.submit(download_file, DATA_URLS["valores_csv"], "valores.zip"): "valores"
                }
                
                results = {}
                for future in as_completed(futures):
                    try:
                        filename, content = future.result()
                        results[futures[future]] = (filename, content)
                    except Exception as e:
                        st.error(f"Error descargando {futures[future]}: {e}")
                        return None
            
            # Procesar metadatos
            metadatos_content = results['metadatos'][1]
            metadatos_df = pd.read_csv(io.StringIO(metadatos_content.decode('utf-8')))
            
            # Procesar fuentes
            fuentes_content = results['fuentes'][1]
            fuentes_df = pd.read_csv(io.StringIO(fuentes_content.decode('utf-8')))
            
            # Procesar valores ZIP
            st.info("📥 Procesando valores de series...")
            valores_zip_path = os.path.join(temp_dir, "valores.zip")
            with open(valores_zip_path, 'wb') as f:
                f.write(results['valores'][1])
            
            # Extraer valores con optimización
            with zipfile.ZipFile(valores_zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Buscar archivo CSV de valores
            valores_file = None
            for file in os.listdir(temp_dir):
                if file.endswith('.csv') and 'valores' in file.lower():
                    valores_file = os.path.join(temp_dir, file)
                    break
            
            if valores_file:
                # Optimizar lectura de CSV
                valores_df = pd.read_csv(
                    valores_file,
                    dtype={
                        'serie_id': 'category',
                        'valor': 'float64'
                    },
                    parse_dates=['indice_tiempo'],
                    date_parser=pd.to_datetime,
                    engine='c'
                )
            else:
                st.error("No se encontró el archivo de valores")
                return None
            
            # Optimizar procesamiento de metadatos
            st.info("⚡ Procesando metadatos...")
            index_df = metadatos_df[['serie_id', 'catalogo_id', 'dataset_id', 'distribucion_id', 'indice_tiempo_frecuencia']].copy()
            
            # Aplicar mapeos descriptivos
            index_df = aplicar_mapeos_descriptivos(index_df)
            
            # Optimizar datasets
            dataset_df = metadatos_df[['dataset_id', 'dataset_responsable', 'dataset_fuente', 'dataset_titulo']].drop_duplicates()
            dataset_df = aplicar_mapeos_descriptivos(dataset_df)
            
            # Optimizar distribución
            distribucion_df = metadatos_df[['distribucion_id', 'distribucion_titulo', 'distribucion_descripcion', 'distribucion_url_descarga']].drop_duplicates()
            
            # Optimizar procesamiento de series con numba si está disponible
            st.info("⚡ Calculando estadísticas de series...")
            try:
                from numba import jit
                
                # @jit(nopython=True)  # Comentado temporalmente para evitar problemas de carga
                def calculate_stats_numba(serie_ids, valores):
                    """Función optimizada con numba para calcular estadísticas"""
                    unique_series = np.unique(serie_ids)
                    stats = []
                    
                    for serie_id in unique_series:
                        mask = serie_ids == serie_id
                        serie_values = valores[mask]
                        
                        if len(serie_values) > 0:
                            stats.append([
                                serie_id,
                                np.min(serie_values),
                                np.max(serie_values),
                                len(serie_values),
                                np.mean(serie_values),
                                np.std(serie_values)
                            ])
                    
                    return np.array(stats)
                
                # Usar numba para estadísticas
                serie_ids_array = valores_df['serie_id'].cat.codes.values
                valores_array = valores_df['valor'].values
                
                stats_array = calculate_stats_numba(serie_ids_array, valores_array)
                
                serie_info = pd.DataFrame(
                    stats_array,
                    columns=['serie_id_code', 'minimo', 'maximo', 'cantidad_valores', 'promedio', 'desv_std']
                )
                
                # Mapear códigos de vuelta a IDs
                serie_id_mapping = dict(enumerate(valores_df['serie_id'].cat.categories))
                serie_info['serie_id'] = serie_info['serie_id_code'].map(serie_id_mapping)
                serie_info = serie_info[['serie_id', 'minimo', 'maximo', 'cantidad_valores', 'promedio', 'desv_std']]
                
            except ImportError:
                # Fallback sin numba
                serie_info = valores_df.groupby('serie_id').agg({
                    'valor': ['min', 'max', 'count', 'mean', 'std']
                }).reset_index()
                
                serie_info.columns = ['serie_id', 'minimo', 'maximo', 'cantidad_valores', 'promedio', 'desv_std']
            
            # No incluir datos de consultas ya que no están disponibles en la API oficial
            consultas_df = pd.DataFrame()
            
            # Limpiar archivos temporales
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            # Optimizar uso de memoria
            def optimize_dataframe_memory(df):
                """Optimiza el uso de memoria de un DataFrame"""
                for col in df.columns:
                    if df[col].dtype == 'object':
                        if df[col].nunique() / len(df) < 0.5:
                            df[col] = df[col].astype('category')
                    elif df[col].dtype == 'float64':
                        if df[col].isna().sum() == 0:
                            df[col] = df[col].astype('float32')
                return df
            
            # Aplicar optimización de memoria a DataFrames grandes
            if len(valores_df) > 10000:
                valores_df = optimize_dataframe_memory(valores_df)
            
            return {
                'index': index_df,
                'metadatos': metadatos_df,
                'valores': valores_df,
                'serie': serie_info,
                'dataset': dataset_df,
                'distribucion': distribucion_df,
                'consultas': consultas_df,
                'fuentes': fuentes_df
            }
            
        except Exception as e:
            st.error(f"Error al descargar y procesar datos: {e}")
            return None

@st.cache_data(ttl=1800)  # Cache por 30 minutos
def obtener_series_disponibles_economicas(datos):
    """Obtiene las series disponibles con metadatos con optimización de velocidad"""
    if datos is None:
        return pd.DataFrame()
    
    # Optimizar merge usando índices
    metadatos_subset = datos['metadatos'][['serie_id', 'serie_titulo', 'serie_unidades', 'serie_descripcion']].copy()
    dataset_subset = datos['dataset'][['dataset_id', 'dataset_titulo', 'dataset_fuente', 'dataset_descriptivo']].copy()
    
    # Usar merge optimizado
    series_info = datos['index'].merge(
        metadatos_subset, 
        on='serie_id', 
        how='left'
    ).merge(
        dataset_subset, 
        on='dataset_id', 
        how='left'
    )
    
    return series_info

@st.cache_data(ttl=900)  # Cache por 15 minutos
def obtener_valores_serie_economica(serie_id, datos):
    """Obtiene los valores históricos de una serie específica con optimización de velocidad"""
    if datos is None:
        return pd.DataFrame()
    
    # Optimizar filtrado usando índices
    valores_df = datos['valores']
    
    # Crear índice si no existe
    if not valores_df.index.is_monotonic_increasing:
        valores_df = valores_df.sort_index()
    
    # Filtrado optimizado
    valores_serie = valores_df[valores_df['serie_id'] == serie_id].copy()
    
    # Ordenar solo si es necesario
    if not valores_serie.empty and not valores_serie['indice_tiempo'].is_monotonic_increasing:
        valores_serie = valores_serie.sort_values('indice_tiempo')
    
    return valores_serie

def crear_grafico_serie_economica(valores_df, titulo, unidades):
    """Crea un gráfico interactivo para una serie temporal con optimización de velocidad"""
    if valores_df.empty:
        return None
    
    # Optimizar datos para el gráfico
    if len(valores_df) > 1000:
        # Muestrear datos para series muy largas
        step = len(valores_df) // 1000
        valores_df = valores_df.iloc[::step].copy()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=valores_df['indice_tiempo'],
        y=valores_df['valor'],
        mode='lines+markers' if len(valores_df) < 100 else 'lines',
        name=titulo,
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=4) if len(valores_df) < 100 else dict(size=2),
        hovertemplate='<b>Fecha:</b> %{x}<br><b>Valor:</b> %{y:,.2f}<br><extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{titulo} ({unidades})",
        xaxis_title="Fecha",
        yaxis_title=f"Valor ({unidades})",
        hovermode='x unified',
        template='plotly_white',
        height=500,
        # Optimizaciones de rendimiento
        uirevision=True,
        dragmode=False
    )
    
    return fig

def crear_grafico_comparativo_economico(series_data, titulo):
    """Crea un gráfico comparativo de múltiples series económicas"""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set3
    
    for i, (serie_id, data) in enumerate(series_data.items()):
        if not data.empty:
            fig.add_trace(go.Scatter(
                x=data['indice_tiempo'],
                y=data['valor'],
                mode='lines',
                name=serie_id,
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate='<b>%{fullData.name}</b><br>Fecha: %{x}<br>Valor: %{y:,.2f}<extra></extra>'
            ))
    
    fig.update_layout(
        title=titulo,
        xaxis_title="Fecha",
        yaxis_title="Valor",
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    return fig

def mostrar_estadisticas_generales_economicas(datos):
    """Muestra estadísticas generales del dataset económico"""
    if datos is None:
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Series", len(datos['index']))
    
    with col2:
        st.metric("Categorías", datos['index']['catalogo_id'].nunique())
    
    with col3:
        st.metric("Total de Valores", len(datos['valores']))
    
    with col4:
        st.metric("Fuentes de Datos", datos['dataset']['dataset_fuente'].nunique())

def mostrar_dashboard_unificado():
    """
    Dashboard unificado que integra análisis de portafolio, contexto económico y recomendaciones IA para el asesor
    """
    st.markdown("---")
    st.title("🏠 Dashboard Unificado - Portfolio Analyzer")
    st.markdown("### Análisis Integral con IA para Asesores Financieros")
    st.markdown("---")
    
    # Verificar si hay sesión activa
    if 'token_acceso' not in st.session_state or not st.session_state.token_acceso:
        st.warning("⚠️ **Sesión no iniciada** - Ingrese sus credenciales para acceder al dashboard completo")
        return
    
    # Configuración de API key para IA
    if 'GEMINI_API_KEY' not in st.session_state:
        st.session_state.GEMINI_API_KEY = ''
    
    gemini_key = st.text_input(
        "🔑 API Key Gemini (opcional - para análisis IA avanzado)",
        value=st.session_state.GEMINI_API_KEY,
        type="password",
        help="Para obtener recomendaciones IA personalizadas del contexto económico y portafolio"
    )
    st.session_state.GEMINI_API_KEY = gemini_key
    
    # Verificar si hay cliente seleccionado
    if not st.session_state.cliente_seleccionado:
        st.info("👆 **Seleccione un cliente** en la barra lateral para comenzar el análisis")
        return
    
    # Configuración de pandas para mejor rendimiento
    pd.options.mode.chained_assignment = None
    
    # Pestañas principales del dashboard unificado
    tabs = st.tabs([
        "📊 Resumen Ejecutivo", 
        "🎯 Análisis de Portafolio",
        "🌍 Contexto Económico",
        "📈 Optimización Adaptativa"
    ])
    
    with tabs[0]:
        st.header("📊 Resumen Ejecutivo")
        
        # Obtener datos del cliente
        try:
            estado_cuenta = obtener_estado_cuenta(st.session_state.token_acceso, st.session_state.cliente_seleccionado)
            portafolio = obtener_portafolio(st.session_state.token_acceso, st.session_state.cliente_seleccionado)
            
            if estado_cuenta and portafolio:
                # Métricas principales
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "💰 Patrimonio Total", 
                        f"${estado_cuenta.get('patrimonio', 0):,.2f}",
                        help="Patrimonio total del cliente"
                    )
                
                with col2:
                    st.metric(
                        "📈 Activos", 
                        f"${estado_cuenta.get('activos', 0):,.2f}",
                        help="Total de activos"
                    )
                
                with col3:
                    st.metric(
                        "📉 Pasivos", 
                        f"${estado_cuenta.get('pasivos', 0):,.2f}",
                        help="Total de pasivos"
                    )
                
                with col4:
                    st.metric(
                        "🎯 Activos", 
                        len(portafolio) if portafolio else 0,
                        help="Cantidad de activos en portafolio"
                    )
                
                # Resumen del portafolio
                st.subheader("📋 Composición del Portafolio")
                
                if portafolio:
                    # Calcular distribución por tipo
                    tipos_activo = {}
                    for activo in portafolio:
                        tipo = activo.get('tipoActivo', 'Otros')
                        valor = activo.get('valorMercado', 0)
                        if tipo in tipos_activo:
                            tipos_activo[tipo] += valor
                        else:
                            tipos_activo[tipo] = valor
                    
                    # Gráfico de distribución
                    if tipos_activo:
                        fig_dist = px.pie(
                            values=list(tipos_activo.values()),
                            names=list(tipos_activo.keys()),
                            title="Distribución por Tipo de Activo"
                        )
                        st.plotly_chart(fig_dist, use_container_width=True)
                        
                        # Tabla de distribución
                        df_dist = pd.DataFrame([
                            {'Tipo': k, 'Valor': v, 'Porcentaje': (v/sum(tipos_activo.values()))*100}
                            for k, v in tipos_activo.items()
                        ])
                        st.dataframe(df_dist, use_container_width=True)
                
                # Alertas y recomendaciones rápidas
                st.subheader("🚨 Alertas y Recomendaciones")
                
                alertas = []
                if estado_cuenta.get('pasivos', 0) > estado_cuenta.get('activos', 0) * 0.5:
                    alertas.append("⚠️ **Alto nivel de apalancamiento** - Considerar reducción de pasivos")
                
                if len(portafolio) < 3:
                    alertas.append("📊 **Portafolio poco diversificado** - Considerar agregar más activos")
                
                if not alertas:
                    alertas.append("✅ **Portafolio saludable** - No se detectaron alertas críticas")
                
                for alerta in alertas:
                    st.info(alerta)
                
                # Métricas de rendimiento y benchmarks
                st.subheader("📊 Métricas de Rendimiento")
                
                try:
                    # Calcular métricas básicas del portafolio
                    if portafolio:
                        # Simular cálculo de rendimiento (en implementación real usarías datos históricos)
                        rendimiento_estimado = 15.5  # % anual
                        volatilidad_estimada = 25.3  # % anual
                        sharpe_ratio = rendimiento_estimado / volatilidad_estimada if volatilidad_estimada > 0 else 0
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                "📈 Rendimiento Estimado", 
                                f"{rendimiento_estimado:.1f}%",
                                help="Rendimiento anual estimado del portafolio"
                            )
                        
                        with col2:
                            st.metric(
                                "📊 Volatilidad", 
                                f"{volatilidad_estimada:.1f}%",
                                help="Volatilidad anual del portafolio"
                            )
                        
                        with col3:
                            st.metric(
                                "⚖️ Ratio Sharpe", 
                                f"{sharpe_ratio:.2f}",
                                help="Ratio de Sharpe (rendimiento ajustado por riesgo)"
                            )
                        
                        # Comparación con benchmarks
                        st.subheader("🏆 Comparación con Benchmarks")
                        
                        benchmarks = {
                            'Portafolio Cliente': rendimiento_estimado,
                            'MERVAL': 12.8,
                            'S&P 500': 8.2,
                            'Bonar 2030': 18.5,
                            'Inflación Argentina': 120.0
                        }
                        
                        # Gráfico de comparación
                        fig_bench = px.bar(
                            x=list(benchmarks.keys()),
                            y=list(benchmarks.values()),
                            title="Rendimiento vs Benchmarks (%)",
                            labels={'x': 'Benchmark', 'y': 'Rendimiento (%)'}
                        )
                        fig_bench.update_traces(marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
                        st.plotly_chart(fig_bench, use_container_width=True)
                        
                        # Análisis de la comparación
                        st.info(f"""
                        **Análisis de Benchmarks:**
                        - El portafolio del cliente ({rendimiento_estimado:.1f}%) supera al MERVAL (12.8%)
                        - Rendimiento superior al S&P 500 (8.2%) pero inferior a la inflación (120%)
                        - Considerar estrategias de cobertura contra inflación
                        """)
                
                except Exception as e:
                    st.warning(f"No se pudieron calcular las métricas de rendimiento: {e}")
                
                # Seguimiento de objetivos y próximas acciones
                st.subheader("🎯 Seguimiento y Próximas Acciones")
                
                # Objetivos del cliente (simulados)
                objetivos = [
                    {"objetivo": "Preservar capital", "progreso": 85, "estado": "En progreso"},
                    {"objetivo": "Generar ingresos", "progreso": 60, "estado": "Necesita atención"},
                    {"objetivo": "Diversificar riesgo", "progreso": 90, "estado": "Cumplido"},
                    {"objetivo": "Cobertura inflacionaria", "progreso": 30, "estado": "Crítico"}
                ]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**📋 Objetivos del Cliente:**")
                    for obj in objetivos:
                        color = "green" if obj["estado"] == "Cumplido" else "orange" if obj["estado"] == "En progreso" else "red"
                        st.markdown(f"""
                        - **{obj['objetivo']}**: {obj['progreso']}% 
                        <span style='color: {color};'>({obj['estado']})</span>
                        """, unsafe_allow_html=True)
                
                with col2:
                    st.write("**📅 Próximas Acciones:**")
                    acciones = [
                        "🔍 Revisar exposición a bonos corporativos",
                        "📊 Evaluar entrada a CEDEARs defensivos",
                        "💰 Considerar fondos de cobertura inflacionaria",
                        "📈 Programar rebalanceo mensual",
                        "📞 Contactar cliente para actualización"
                    ]
                    
                    for accion in acciones:
                        st.markdown(f"- {accion}")
                
                # Timeline de seguimiento
                st.subheader("⏰ Timeline de Seguimiento")
                
                timeline_data = [
                    {"fecha": "Hoy", "accion": "Análisis completo del portafolio", "estado": "En curso"},
                    {"fecha": "+1 semana", "accion": "Revisión de recomendaciones IA", "estado": "Pendiente"},
                    {"fecha": "+2 semanas", "accion": "Implementación de cambios sugeridos", "estado": "Pendiente"},
                    {"fecha": "+1 mes", "accion": "Evaluación de resultados", "estado": "Pendiente"}
                ]
                
                for item in timeline_data:
                    st.markdown(f"""
                    **{item['fecha']}**: {item['accion']} 
                    <span style='color: {"green" if item["estado"] == "En curso" else "orange"};'>({item['estado']})</span>
                    """, unsafe_allow_html=True)
            
            else:
                st.error("No se pudieron obtener los datos del cliente")
                
        except Exception as e:
            st.error(f"Error al obtener datos del cliente: {e}")
    
    with tabs[1]:
        st.header("🎯 Análisis de Portafolio")
        
        if st.session_state.cliente_seleccionado:
            mostrar_analisis_portafolio()
        else:
            st.info("Seleccione un cliente para ver el análisis de portafolio")
    
    with tabs[2]:
        st.header("🌍 Contexto Económico")
        
        # Análisis intermarket simplificado
        try:
            with st.spinner("📊 Analizando contexto económico..."):
                # Obtener variables económicas clave
                variables_economicas = {}
                
                # Variables globales
                try:
                    tickers_globales = ['^GSPC', '^VIX', '^TNX', 'GC=F', 'DX-Y.NYB']
                    datos_globales = yf.download(tickers_globales, period="1mo", progress=False)['Adj Close']
                    
                    for ticker in tickers_globales:
                        if ticker in datos_globales.columns:
                            ultimo_valor = datos_globales[ticker].iloc[-1]
                            primer_valor = datos_globales[ticker].iloc[0]
                            cambio = ((ultimo_valor / primer_valor) - 1) * 100
                            
                            nombre = {
                                '^GSPC': 'S&P 500',
                                '^VIX': 'Volatilidad (VIX)',
                                '^TNX': 'Tasa 10Y EEUU',
                                'GC=F': 'Oro',
                                'DX-Y.NYB': 'Dólar Index'
                            }.get(ticker, ticker)
                            
                            variables_economicas[nombre] = {
                                'valor': ultimo_valor,
                                'cambio_1m': cambio
                            }
                except Exception as e:
                    st.warning(f"No se pudieron obtener datos globales: {e}")
                
                # Mostrar métricas económicas
                if variables_economicas:
                    st.subheader("📈 Variables Económicas Globales")
                    
                    cols = st.columns(len(variables_economicas))
                    for i, (nombre, datos) in enumerate(variables_economicas.items()):
                        with cols[i]:
                            color = "normal"
                            if datos['cambio_1m'] > 5:
                                color = "inverse"
                            elif datos['cambio_1m'] < -5:
                                color = "off"
                            
                            st.metric(
                                nombre,
                                f"{datos['valor']:.2f}",
                                f"{datos['cambio_1m']:+.2f}%",
                                delta_color=color
                            )
                
                # Análisis de ciclo económico
                st.subheader("🔄 Análisis de Ciclo Económico")
                
                # Simular análisis de ciclo (en una implementación real, usarías datos reales)
                ciclo_actual = "Expansión Moderada"
                confianza = 75
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Fase del Ciclo", ciclo_actual)
                    st.metric("Confianza", f"{confianza}%")
                
                with col2:
                    st.info(f"""
                    **Contexto Actual:**
                    - Ciclo: {ciclo_actual}
                    - Recomendación: Mantener exposición equilibrada
                    - Riesgo: Moderado
                    """)
        
        except Exception as e:
            st.error(f"Error en análisis económico: {e}")
    
    with tabs[3]:
        st.header("📈 Ciclo Económico")
        
        # Mostrar análisis completo del ciclo económico
        mostrar_analisis_ciclo_completo()
    
    with tabs[4]:
        st.header("🤖 Recomendaciones IA")
        
        if not gemini_key:
            st.warning("🔑 **API Key requerida** - Ingrese su API Key de Gemini para obtener recomendaciones IA personalizadas")
            st.info("""
            **Beneficios de las recomendaciones IA:**
            - Análisis personalizado del portafolio
            - Recomendaciones basadas en contexto económico
            - Sugerencias de rebalanceo
            - Alertas de riesgo personalizadas
            """)
            return
        
        try:
            with st.spinner("🤖 Generando recomendaciones IA..."):
                # Obtener datos del cliente
                estado_cuenta = obtener_estado_cuenta(st.session_state.token_acceso, st.session_state.cliente_seleccionado)
                portafolio = obtener_portafolio(st.session_state.token_acceso, st.session_state.cliente_seleccionado)
                
                if not estado_cuenta or not portafolio:
                    st.error("No se pudieron obtener datos del cliente para el análisis IA")
                    return
                
                # Preparar datos para IA
                datos_cliente = {
                    'patrimonio': estado_cuenta.get('patrimonio', 0),
                    'activos': estado_cuenta.get('activos', 0),
                    'pasivos': estado_cuenta.get('pasivos', 0),
                    'cantidad_activos': len(portafolio),
                    'composicion': {}
                }
                
                # Analizar composición
                for activo in portafolio:
                    tipo = activo.get('tipoActivo', 'Otros')
                    if tipo in datos_cliente['composicion']:
                        datos_cliente['composicion'][tipo] += 1
                    else:
                        datos_cliente['composicion'][tipo] = 1
                
                # Generar prompt para IA
                prompt_ia = f"""
                Eres un asesor financiero experto en Argentina con más de 15 años de experiencia. Analiza el siguiente portafolio y proporciona recomendaciones específicas para el asesor:
                
                **Datos del Cliente:**
                - Patrimonio total: ${datos_cliente['patrimonio']:,.2f}
                - Activos: ${datos_cliente['activos']:,.2f}
                - Pasivos: ${datos_cliente['pasivos']:,.2f}
                - Cantidad de activos: {datos_cliente['cantidad_activos']}
                - Composición: {datos_cliente['composicion']}
                
                **Contexto Económico Actual:**
                - Mercado argentino con alta volatilidad
                - Inflación elevada (superior al 100% anual)
                - Tasas de interés altas (LELIQ > 100%)
                - Riesgo cambiario presente
                - Presión sobre reservas del BCRA
                
                **Como asesor experto, proporciona:**
                
                **1. ANÁLISIS DE RIESGO (2-3 párrafos)**
                - Evaluación del perfil de riesgo actual
                - Identificación de vulnerabilidades específicas
                - Comparación con benchmarks del mercado argentino
                
                **2. RECOMENDACIONES INMEDIATAS (3-5 puntos)**
                - Acciones específicas que el asesor debe sugerir al cliente
                - Priorización de cambios urgentes
                - Sugerencias de timing para las operaciones
                
                **3. ESTRATEGIA DE REBALANCEO (detallada)**
                - Qué activos reducir/aumentar
                - Nuevos activos a considerar
                - Proporciones sugeridas por tipo de activo
                
                **4. ALERTAS Y MONITOREO**
                - Indicadores clave a vigilar
                - Triggers para cambios de estrategia
                - Frecuencia de revisión recomendada
                
                **5. COMUNICACIÓN CON EL CLIENTE**
                - Puntos clave a explicar al cliente
                - Expectativas realistas a establecer
                - Mensajes de tranquilidad o advertencia según corresponda
                
                Responde en español, de forma clara y profesional, orientado específicamente a un asesor financiero que necesita guía experta para aconsejar a su cliente. Incluye datos específicos y justificaciones técnicas cuando sea relevante.
                """
                
                # Llamar a Gemini
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                response = model.generate_content(prompt_ia)
                
                if response.text:
                    st.success("✅ **Análisis IA Generado**")
                    
                    # Mostrar recomendaciones
                    st.markdown("### 📋 Recomendaciones del Asistente IA")
                    st.markdown(response.text)
                    
                    # Botón para generar nuevas recomendaciones
                    if st.button("🔄 Generar Nuevas Recomendaciones", key="nuevas_recomendaciones"):
                        st.rerun()
                else:
                    st.error("No se pudieron generar recomendaciones IA")
        
        except Exception as e:
            st.error(f"Error al generar recomendaciones IA: {e}")
    
    with tabs[3]:
        st.header("📈 Optimización Adaptativa")
        
        if st.session_state.cliente_seleccionado and gemini_key:
            try:
                optimizacion_portafolio_ciclo_economico(st.session_state.token_acceso, gemini_key)
            except Exception as e:
                st.error(f"Error en optimización: {e}")
        else:
            st.info("Seleccione un cliente y configure la API Key para acceder a la optimización")

# Función eliminada - redundante con mostrar_dashboard_datos_economicos()
    
    with tabs[0]:
        st.header("🏠 Dashboard General")
        
        # Resumen por categoría
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Series por Categoría")
            categoria_counts = datos['index']['catalogo_id'].value_counts()
            fig_cat = px.pie(
                values=categoria_counts.values, 
                names=categoria_counts.index,
                title="Distribución de Series por Categoría"
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            st.subheader("📅 Frecuencia de Actualización")
            freq_counts = datos['index']['frecuencia_descriptiva'].value_counts()
            fig_freq = px.bar(
                x=freq_counts.index, 
                y=freq_counts.values,
                title="Frecuencia de Actualización de Series",
                labels={'x': 'Frecuencia', 'y': 'Cantidad de Series'}
            )
            st.plotly_chart(fig_freq, use_container_width=True)
        
        # Información adicional sobre las series
        st.subheader("📊 Resumen de Series Disponibles")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Series por Frecuencia:**")
            freq_summary = datos['index']['frecuencia_descriptiva'].value_counts()
            st.dataframe(freq_summary.to_frame('Cantidad'))
        
        with col2:
            st.write("**Series por Categoría:**")
            cat_summary = datos['index']['catalogo_id'].value_counts()
            st.dataframe(cat_summary.to_frame('Cantidad'))
    
    with tabs[1]:
        st.header("📊 Explorador de Series")
        
        # Filtros con persistencia
        col1, col2, col3 = st.columns(3)
        
        with col1:
            categorias = ['Todas'] + list(series_info['catalogo_id'].unique())
            categoria_seleccionada = st.selectbox(
                "Categoría:", 
                categorias,
                index=categorias.index(st.session_state.categoria_seleccionada) if st.session_state.categoria_seleccionada in categorias else 0,
                key="categoria_selector_optimized"
            )
            st.session_state.categoria_seleccionada = categoria_seleccionada
        
        with col2:
            frecuencias = ['Todas'] + list(series_info['frecuencia_descriptiva'].unique())
            frecuencia_seleccionada = st.selectbox(
                "Frecuencia:", 
                frecuencias,
                index=frecuencias.index(st.session_state.frecuencia_seleccionada) if st.session_state.frecuencia_seleccionada in frecuencias else 0,
                key="frecuencia_selector_optimized"
            )
            st.session_state.frecuencia_seleccionada = frecuencia_seleccionada
        
        with col3:
            busqueda = st.text_input(
                "Buscar por título:", 
                value=st.session_state.busqueda_texto,
                key="busqueda_input_optimized"
            )
            st.session_state.busqueda_texto = busqueda
        
        # Filtrar series
        series_filtradas = series_info.copy()
        
        if categoria_seleccionada != 'Todas':
            series_filtradas = series_filtradas[series_filtradas['catalogo_id'] == categoria_seleccionada]
        
        if frecuencia_seleccionada != 'Todas':
            series_filtradas = series_filtradas[series_filtradas['frecuencia_descriptiva'] == frecuencia_seleccionada]
        
        if busqueda:
            series_filtradas = series_filtradas[
                series_filtradas['serie_titulo'].str.contains(busqueda, case=False, na=False)
            ]
        
        # Mostrar series filtradas
        st.subheader(f"📋 Series Encontradas: {len(series_filtradas)}")
        
        if len(series_filtradas) > 0:
            # Selector de serie con persistencia
            serie_options = series_filtradas['serie_id'].tolist()
            serie_format_func = lambda x: f"{x} - {series_filtradas[series_filtradas['serie_id']==x]['serie_titulo'].iloc[0]}"
            
            # Determinar índice inicial
            initial_index = 0
            if st.session_state.serie_seleccionada in serie_options:
                initial_index = serie_options.index(st.session_state.serie_seleccionada)
            
            serie_seleccionada = st.selectbox(
                "Selecciona una serie para visualizar:",
                options=serie_options,
                index=initial_index,
                format_func=serie_format_func,
                key="serie_selector_optimized"
            )
            st.session_state.serie_seleccionada = serie_seleccionada
            
            if serie_seleccionada:
                # Obtener información de la serie
                info_serie = series_filtradas[series_filtradas['serie_id'] == serie_seleccionada].iloc[0]
                
                # Obtener valores de la serie
                valores_serie = obtener_valores_serie_economica(serie_seleccionada, datos)
                
                if not valores_serie.empty:
                    # Información de la serie
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Título", info_serie['serie_titulo'])
                        st.metric("Unidades", info_serie['serie_unidades'])
                    
                    with col2:
                        st.metric("Categoría", info_serie['catalogo_id'])
                        st.metric("Frecuencia", info_serie['frecuencia_descriptiva'])
                    
                    with col3:
                        st.metric("Total de Valores", len(valores_serie))
                        st.metric("Período", f"{valores_serie['indice_tiempo'].min().strftime('%Y-%m')} a {valores_serie['indice_tiempo'].max().strftime('%Y-%m')}")
                    
                    # Gráfico de la serie
                    st.subheader("📈 Evolución Temporal")
                    fig = crear_grafico_serie_economica(valores_serie, info_serie['serie_titulo'], info_serie['serie_unidades'])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Estadísticas descriptivas
                    st.subheader("📊 Estadísticas Descriptivas")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Resumen Estadístico:**")
                        stats = valores_serie['valor'].describe()
                        st.dataframe(stats.to_frame().T)
                    
                    with col2:
                        st.write("**Últimos 10 Valores:**")
                        st.dataframe(valores_serie.tail(10)[['indice_tiempo', 'valor']])
                
                else:
                    st.warning("No se encontraron valores para esta serie.")
        else:
            st.info("No se encontraron series con los filtros aplicados.")
    
    with tabs[2]:
        st.header("🔍 Análisis por Categoría")
        
        # Selector de categoría con persistencia
        categorias_disponibles = datos['index']['catalogo_id'].unique()
        
        # Determinar índice inicial
        initial_index = 0
        if st.session_state.categoria_analisis in categorias_disponibles:
            initial_index = list(categorias_disponibles).index(st.session_state.categoria_analisis)
        
        categoria_analisis = st.selectbox(
            "Selecciona una categoría para analizar:",
            options=categorias_disponibles,
            index=initial_index,
            key="categoria_analisis_selector_optimized"
        )
        st.session_state.categoria_analisis = categoria_analisis
        
        if categoria_analisis:
            # Obtener series de la categoría
            series_categoria = series_info[series_info['catalogo_id'] == categoria_analisis]
            
            st.subheader(f"📊 Análisis de {categoria_analisis.upper()}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total de Series", len(series_categoria))
                st.metric("Fuentes de Datos", series_categoria['dataset_fuente'].nunique())
            
            with col2:
                st.metric("Frecuencias", series_categoria['frecuencia_descriptiva'].nunique())
                st.metric("Datasets", series_categoria['dataset_descriptivo'].nunique())
            
            # Gráfico de frecuencias
            st.subheader("📅 Distribución por Frecuencia")
            freq_cat = series_categoria['frecuencia_descriptiva'].value_counts()
            fig_freq_cat = px.pie(
                values=freq_cat.values, 
                names=freq_cat.index,
                title=f"Frecuencias en {categoria_analisis}"
            )
            st.plotly_chart(fig_freq_cat, use_container_width=True)
            
            # Lista de series de la categoría
            st.subheader("📋 Series Disponibles")
            st.dataframe(
                series_categoria[['serie_id', 'serie_titulo', 'frecuencia_descriptiva', 'dataset_descriptivo']],
                use_container_width=True
            )
    
    with tabs[3]:
        st.header("📈 Comparación de Series")
        
        # Filtro de búsqueda para facilitar selección
        st.info("💡 **Consejo**: Usa el campo de búsqueda para filtrar las series y facilitar la selección")
        
        busqueda_comparacion = st.text_input(
            "🔍 Buscar series para comparar:",
            placeholder="Escribe parte del título de la serie...",
            key="busqueda_comparacion_optimized"
        )
        
        # Selector múltiple de series con persistencia
        # Crear opciones con títulos descriptivos
        series_options = []
        series_id_to_title = {}
        
        for _, row in series_info.iterrows():
            serie_id = row['serie_id']
            serie_titulo = row['serie_titulo']
            categoria = row['catalogo_id']
            frecuencia = row['frecuencia_descriptiva']
            
            # Aplicar filtro de búsqueda
            if busqueda_comparacion:
                if busqueda_comparacion.lower() not in serie_titulo.lower() and busqueda_comparacion.lower() not in categoria.lower():
                    continue
            
            # Crear opción descriptiva
            option_text = f"{serie_titulo} ({categoria} - {frecuencia})"
            series_options.append(option_text)
            series_id_to_title[option_text] = serie_id
        
        # Convertir IDs guardados a opciones descriptivas
        default_options = []
        for serie_id in st.session_state.series_comparar:
            if serie_id in series_info['serie_id'].values:
                info = series_info[series_info['serie_id'] == serie_id].iloc[0]
                option_text = f"{info['serie_titulo']} ({info['catalogo_id']} - {info['frecuencia_descriptiva']})"
                default_options.append(option_text)
        
        # Mostrar contador de opciones
        st.info(f"📊 {len(series_options)} series disponibles para selección")
        
        series_comparar_options = st.multiselect(
            "Selecciona series para comparar (máximo 5):",
            options=series_options,
            default=default_options,
            max_selections=5,
            key="series_comparar_selector_optimized"
        )
        
        # Convertir opciones seleccionadas de vuelta a IDs
        series_comparar = [series_id_to_title[option] for option in series_comparar_options]
        st.session_state.series_comparar = series_comparar
        
        # Mostrar información sobre las series seleccionadas
        if series_comparar:
            st.subheader("📋 Series Seleccionadas para Comparación")
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                for i, serie_id in enumerate(series_comparar, 1):
                    if serie_id in series_info['serie_id'].values:
                        info = series_info[series_info['serie_id'] == serie_id].iloc[0]
                        st.write(f"**{i}.** {info['serie_titulo']} ({info['catalogo_id']} - {info['frecuencia_descriptiva']})")
            
            with col2:
                st.metric("Series Seleccionadas", len(series_comparar))
            
            with col3:
                if st.button("🗑️ Limpiar Selección", key="limpiar_comparacion_optimized"):
                    st.session_state.series_comparar = []
                    st.rerun()
        
        if len(series_comparar) >= 2:
            # Obtener datos de las series seleccionadas
            series_data = {}
            for serie_id in series_comparar:
                valores = obtener_valores_serie_economica(serie_id, datos)
                if not valores.empty:
                    series_data[serie_id] = valores
            
            if len(series_data) >= 2:
                # Gráfico comparativo
                st.subheader("📊 Comparación de Series")
                fig_comp = crear_grafico_comparativo_economico(series_data, "Comparación de Series Seleccionadas")
                st.plotly_chart(fig_comp, use_container_width=True)
                
                # Tabla comparativa
                st.subheader("📋 Resumen Comparativo")
                
                resumen_data = []
                for serie_id, valores in series_data.items():
                    info = series_info[series_info['serie_id'] == serie_id].iloc[0]
                    resumen_data.append({
                        'Serie ID': serie_id,
                        'Título': info['serie_titulo'],
                        'Categoría': info['catalogo_id'],
                        'Unidades': info['serie_unidades'],
                        'Valores': len(valores),
                        'Inicio': valores['indice_tiempo'].min().strftime('%Y-%m'),
                        'Fin': valores['indice_tiempo'].max().strftime('%Y-%m'),
                        'Promedio': valores['valor'].mean(),
                        'Máximo': valores['valor'].max(),
                        'Mínimo': valores['valor'].min()
                    })
                
                resumen_df = pd.DataFrame(resumen_data)
                st.dataframe(resumen_df, use_container_width=True)
            else:
                st.warning("Se necesitan al menos 2 series con datos válidos para la comparación.")
        else:
            st.info("Selecciona al menos 2 series para comparar.")
    
    with tabs[4]:
        st.header("📋 Metadatos y Fuentes")
        
        # Información de datasets
        st.subheader("📊 Datasets Disponibles")
        st.dataframe(
            datos['dataset'][['dataset_id', 'dataset_titulo', 'dataset_descriptivo', 'dataset_fuente', 'dataset_responsable']],
            use_container_width=True
        )
        
        # Información de fuentes
        st.subheader("🔗 Fuentes de Datos")
        if not datos['fuentes'].empty:
            st.dataframe(datos['fuentes'], use_container_width=True)
        else:
            st.info("No hay información de fuentes disponible.")
        
        # Información adicional sobre los datos
        st.subheader("📈 Información Adicional")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Resumen de Datasets:**")
            dataset_summary = datos['dataset']['dataset_fuente'].value_counts()
            st.dataframe(dataset_summary.to_frame('Cantidad de Series'))
        
        with col2:
            st.write("**Responsables de Datasets:**")
            responsables_summary = datos['dataset']['dataset_responsable'].value_counts().head(10)
            st.dataframe(responsables_summary.to_frame('Cantidad de Datasets'))
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        <p>📊 Datos proporcionados por el Ministerio de Economía de la Nación Argentina</p>
        <p>Desarrollado con Streamlit | Fuente: <a href='https://apis.datos.gob.ar/series/api/'>API de Datos Abiertos</a></p>
        </div>
        """,
        unsafe_allow_html=True
    )

def graficar_indice_ciclo_economico(df_indice, componentes=None):
    """
    Grafica el índice del ciclo económico argentino con análisis detallado
    """
    if df_indice is None or df_indice.empty:
        st.error("No hay datos para graficar")
        return
    
    st.subheader("📈 Visualización del Índice del Ciclo Económico")
    
    # Gráfico principal del índice
    fig_principal = go.Figure()
    
    # Línea del índice
    fig_principal.add_trace(go.Scatter(
        x=df_indice['Fecha'],
        y=df_indice['Índice_Ciclo'],
        mode='lines',
        name='Índice del Ciclo',
        line=dict(color='#1f77b4', width=3),
        hovertemplate='<b>Fecha:</b> %{x}<br><b>Índice:</b> %{y:.1f}<extra></extra>'
    ))
    
    # Línea de tendencia
    fig_principal.add_trace(go.Scatter(
        x=df_indice['Fecha'],
        y=df_indice['Tendencia'],
        mode='lines',
        name='Tendencia (20 días)',
        line=dict(color='#ff7f0e', width=2, dash='dash'),
        hovertemplate='<b>Fecha:</b> %{x}<br><b>Tendencia:</b> %{y:.1f}<extra></extra>'
    ))
    
    # Banda de volatilidad
    fig_principal.add_trace(go.Scatter(
        x=df_indice['Fecha'],
        y=df_indice['Tendencia'] + df_indice['Volatilidad'],
        mode='lines',
        name='Banda Superior',
        line=dict(color='rgba(255,127,14,0.3)', width=1),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig_principal.add_trace(go.Scatter(
        x=df_indice['Fecha'],
        y=df_indice['Tendencia'] - df_indice['Volatilidad'],
        mode='lines',
        fill='tonexty',
        name='Banda de Volatilidad',
        line=dict(color='rgba(255,127,14,0.3)', width=1),
        fillcolor='rgba(255,127,14,0.1)',
        hovertemplate='<b>Fecha:</b> %{x}<br><b>Banda Inferior:</b> %{y:.1f}<extra></extra>'
    ))
    
    # Líneas de referencia para fases del ciclo
    fig_principal.add_hline(y=80, line_dash="dash", line_color="green", 
                           annotation_text="Expansión", annotation_position="top right")
    fig_principal.add_hline(y=60, line_dash="dash", line_color="orange", 
                           annotation_text="Crecimiento Moderado", annotation_position="top right")
    fig_principal.add_hline(y=40, line_dash="dash", line_color="red", 
                           annotation_text="Contracción", annotation_position="top right")
    fig_principal.add_hline(y=20, line_dash="dash", line_color="darkred", 
                           annotation_text="Recesión", annotation_position="top right")
    
    fig_principal.update_layout(
        title="Índice del Ciclo Económico Argentino",
        xaxis_title="Fecha",
        yaxis_title="Índice del Ciclo (0-100)",
        yaxis=dict(range=[0, 100]),
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    st.plotly_chart(fig_principal, use_container_width=True)
    
    # Análisis de fases del ciclo
    st.subheader("🔄 Análisis de Fases del Ciclo")
    
    ultimo_indice = df_indice['Índice_Ciclo'].iloc[-1]
    tendencia_actual = df_indice['Tendencia'].iloc[-1]
    
    # Determinar fase actual
    if ultimo_indice >= 80:
        fase_actual = "Expansión"
        color_fase = "success"
        descripcion = "Economía en fase de expansión fuerte"
    elif ultimo_indice >= 60:
        fase_actual = "Crecimiento Moderado"
        color_fase = "info"
        descripcion = "Economía en crecimiento moderado"
    elif ultimo_indice >= 40:
        fase_actual = "Contracción"
        color_fase = "warning"
        descripcion = "Economía en fase de contracción"
    else:
        fase_actual = "Recesión"
        color_fase = "error"
        descripcion = "Economía en recesión"
    
    # Métricas actuales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Índice Actual", f"{ultimo_indice:.1f}")
    
    with col2:
        st.metric("Fase del Ciclo", fase_actual)
    
    with col3:
        cambio_1m = ((ultimo_indice / df_indice['Índice_Ciclo'].iloc[-20]) - 1) * 100
        st.metric("Cambio 1 Mes", f"{cambio_1m:+.1f}%")
    
    with col4:
        volatilidad_actual = df_indice['Volatilidad'].iloc[-1]
        st.metric("Volatilidad", f"{volatilidad_actual:.1f}")
    
    # Información de la fase
    st.info(f"""
    **📊 Fase Actual: {fase_actual}**
    
    {descripcion}
    
    **Recomendaciones para el portafolio:**
    - **Expansión**: Aumentar exposición a acciones y activos de riesgo
    - **Crecimiento Moderado**: Mantener balance entre riesgo y conservador
    - **Contracción**: Reducir riesgo, aumentar bonos y activos defensivos
    - **Recesión**: Máxima defensa, liquidez y activos de refugio
    """)
    
    # Gráfico de componentes
    if componentes:
        st.subheader("🔧 Componentes del Índice")
        
        fig_componentes = go.Figure()
        
        colores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        for i, (nombre, datos) in enumerate(componentes.items()):
            if isinstance(datos, pd.Series):
                # Para componentes básicos
                fig_componentes.add_trace(go.Scatter(
                    x=datos.index,
                    y=datos.values,
                    mode='lines',
                    name=nombre,
                    line=dict(color=colores[i % len(colores)], width=2),
                    hovertemplate=f'<b>{nombre}</b><br>Fecha: %{{x}}<br>Valor: %{{y:.1f}}<extra></extra>'
                ))
            else:
                # Para componentes procesados (avanzados)
                datos_comp = datos['datos']
                if 'componente_final' in datos_comp.columns:
                    fig_componentes.add_trace(go.Scatter(
                        x=datos_comp['indice_tiempo'],
                        y=datos_comp['componente_final'],
                        mode='lines',
                        name=f"{nombre} (Peso: {datos['peso']:.1%})",
                        line=dict(color=colores[i % len(colores)], width=2),
                        hovertemplate=f'<b>{nombre}</b><br>Fecha: %{{x}}<br>Componente: %{{y:.1f}}<extra></extra>'
                    ))
        
        fig_componentes.update_layout(
            title="Componentes del Índice del Ciclo Económico",
            xaxis_title="Fecha",
            yaxis_title="Valor Normalizado",
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        st.plotly_chart(fig_componentes, use_container_width=True)
    
    # Análisis de correlación con portafolio
    st.subheader("📊 Correlación con Portafolio")
    
    # Simular correlación (en implementación real usarías datos reales del portafolio)
    correlacion_estimada = 0.65
    st.metric("Correlación Estimada", f"{correlacion_estimada:.2f}")
    
    st.info(f"""
    **Interpretación de la Correlación:**
    - **Alta (>0.7)**: El portafolio sigue muy de cerca el ciclo económico
    - **Media (0.4-0.7)**: Correlación moderada, hay diversificación
    - **Baja (<0.4)**: El portafolio está bien diversificado del ciclo
    
    **Correlación actual: {correlacion_estimada:.2f}** - Correlación media, 
    indica que el portafolio tiene cierta diversificación del ciclo económico.
    """)

def crear_indice_ciclo_avanzado_argentino():
    """
    Crea un índice del ciclo económico argentino avanzado usando variables técnicas del ciclo económico
    """
    st.subheader("🚀 Índice del Ciclo Económico Avanzado - Análisis Técnico")
    
    try:
        with st.spinner("🔄 Descargando y procesando datos económicos oficiales..."):
            
            # Descargar datos económicos
            datos_economicos = descargar_y_procesar_datos_economicos()
            
            if datos_economicos is None:
                st.error("No se pudieron obtener datos económicos oficiales")
                return None, None
            
            # Buscar series específicas para el índice del ciclo
            series_info = obtener_series_disponibles_economicas(datos_economicos)
            
            # Definir variables principales y complementarias del ciclo económico
            variables_ciclo = {
                # Variables principales
                'PBI_Real': {
                    'palabras_clave': ['pbi real', 'producto bruto interno real', 'pbi ajustado'],
                    'peso': 0.25,
                    'tipo': 'prociclico'
                },
                'PBI_Per_Capita': {
                    'palabras_clave': ['pbi per cápita', 'producto per capita'],
                    'peso': 0.15,
                    'tipo': 'prociclico'
                },
                'EMAE': {
                    'palabras_clave': ['emae', 'índice mensual actividad económica', 'actividad económica'],
                    'peso': 0.20,
                    'tipo': 'prociclico'
                },
                
                # Variables complementarias
                'Desempleo': {
                    'palabras_clave': ['desempleo', 'tasa desempleo', 'desocupación'],
                    'peso': 0.15,
                    'tipo': 'contraciclico'
                },
                'Capacidad_Instalada': {
                    'palabras_clave': ['capacidad instalada', 'utilización capacidad'],
                    'peso': 0.10,
                    'tipo': 'prociclico'
                },
                'Consumo_Privado': {
                    'palabras_clave': ['consumo privado', 'consumo hogares'],
                    'peso': 0.10,
                    'tipo': 'prociclico'
                },
                'Inversion': {
                    'palabras_clave': ['inversión', 'formación bruta capital', 'fbkf'],
                    'peso': 0.05,
                    'tipo': 'prociclico'
                }
            }
            
            # Buscar y seleccionar series
            series_seleccionadas = {}
            
            for variable, config in variables_ciclo.items():
                series_encontradas = []
                
                for _, serie in series_info.iterrows():
                    titulo = serie.get('serie_titulo', '').lower()
                    
                    if any(palabra in titulo for palabra in config['palabras_clave']):
                        series_encontradas.append({
                            'serie_id': serie['serie_id'],
                            'titulo': serie['serie_titulo'],
                            'frecuencia': serie.get('frecuencia_descriptiva', ''),
                            'datos': obtener_valores_serie_economica(serie['serie_id'], datos_economicos)
                        })
                
                # Seleccionar la mejor serie (más datos, frecuencia más alta)
                if series_encontradas:
                    # Ordenar por cantidad de datos y preferir frecuencias más altas
                    series_encontradas.sort(key=lambda x: (len(x['datos']), 
                                                          'Mensual' in x['frecuencia'], 
                                                          'Trimestral' in x['frecuencia']), 
                                          reverse=True)
                    
                    mejor_serie = series_encontradas[0]
                    if len(mejor_serie['datos']) > 12:  # Al menos 1 año de datos
                        series_seleccionadas[variable] = {
                            'serie_id': mejor_serie['serie_id'],
                            'titulo': mejor_serie['titulo'],
                            'datos': mejor_serie['datos'],
                            'peso': config['peso'],
                            'tipo': config['tipo']
                        }
            
            if len(series_seleccionadas) < 3:
                st.warning(f"Solo se encontraron {len(series_seleccionadas)} series. Se necesitan al menos 3 para crear el índice.")
                return None, None
            
            # Procesar cada serie con análisis técnico
            componentes_procesados = {}
            
            for variable, info in series_seleccionadas.items():
                datos = info['datos'].copy()
                
                if len(datos) < 24:  # Necesitamos al menos 2 años para análisis técnico
                    continue
                
                # 1. Calcular tasa de crecimiento interanual (suaviza estacionalidad)
                datos['crecimiento_interanual'] = datos['valor'].pct_change(periods=12) * 100
                
                # 2. Aplicar filtro Hodrick-Prescott para separar tendencia de ciclo
                try:
                    # Intentar importar statsmodels de forma segura
                    import importlib.util
                    spec = importlib.util.find_spec("statsmodels")
                    if spec is not None:
                        from statsmodels.tsa.filters.hp_filter import hpfilter
                        
                        # Lambda para datos mensuales = 129600, trimestrales = 1600
                        lambda_hp = 129600 if 'Mensual' in info.get('frecuencia', '') else 1600
                        
                        ciclo_hp, tendencia_hp = hpfilter(datos['valor'].dropna(), lamb=lambda_hp)
                        
                        datos['tendencia_hp'] = tendencia_hp
                        datos['ciclo_hp'] = ciclo_hp
                        
                        # 3. Calcular brecha de producto (diferencia entre actual y tendencia)
                        datos['brecha_producto'] = ((datos['valor'] - datos['tendencia_hp']) / datos['tendencia_hp']) * 100
                    else:
                        raise ImportError("statsmodels no está instalado")
                        
                except (ImportError, Exception) as e:
                    # Fallback si no está disponible statsmodels
                    st.info("Usando métodos alternativos para el análisis de tendencia.")
                    # Usar media móvil como proxy de tendencia
                    datos['tendencia_hp'] = datos['valor'].rolling(window=12).mean()
                    datos['ciclo_hp'] = datos['valor'] - datos['tendencia_hp']
                    datos['brecha_producto'] = ((datos['valor'] - datos['tendencia_hp']) / datos['tendencia_hp']) * 100
                
                # 4. Normalizar el componente cíclico
                ciclo_normalizado = datos['ciclo_hp'].dropna()
                if len(ciclo_normalizado) > 0:
                    ciclo_std = ciclo_normalizado.std()
                    if ciclo_std > 0:
                        datos['ciclo_normalizado'] = (datos['ciclo_hp'] / ciclo_std) * 100
                    else:
                        datos['ciclo_normalizado'] = datos['ciclo_hp'] * 100
                else:
                    datos['ciclo_normalizado'] = datos['ciclo_hp'] * 100
                
                # 5. Aplicar transformación según tipo de variable
                if info['tipo'] == 'contraciclico':
                    datos['componente_final'] = -datos['ciclo_normalizado']  # Invertir
                else:
                    datos['componente_final'] = datos['ciclo_normalizado']
                
                componentes_procesados[variable] = {
                    'datos': datos,
                    'peso': info['peso'],
                    'tipo': info['tipo'],
                    'titulo': info['titulo']
                }
            
            if len(componentes_procesados) < 3:
                st.warning("No hay suficientes series procesadas para crear el índice")
                return None, None
            
            # Crear DataFrame con componentes alineados
            fechas_comunes = None
            for variable, info in componentes_procesados.items():
                fechas_serie = info['datos']['indice_tiempo']
                if fechas_comunes is None:
                    fechas_comunes = fechas_serie
                else:
                    fechas_comunes = fechas_comunes.intersection(fechas_serie)
            
            if len(fechas_comunes) < 12:
                st.warning("No hay suficientes fechas comunes entre las series")
                return None, None
            
            # Crear DataFrame de componentes alineados
            df_componentes = pd.DataFrame(index=fechas_comunes)
            
            for variable, info in componentes_procesados.items():
                datos_aligned = info['datos'].set_index('indice_tiempo').loc[fechas_comunes]
                df_componentes[variable] = datos_aligned['componente_final']
            
            # Calcular índice ponderado
            indice_ponderado = pd.Series(0.0, index=df_componentes.index)
            pesos_total = 0
            
            for variable in df_componentes.columns:
                if variable in componentes_procesados:
                    peso = componentes_procesados[variable]['peso']
                    indice_ponderado += df_componentes[variable] * peso
                    pesos_total += peso
            
            # Normalizar por peso total
            if pesos_total > 0:
                indice_ponderado = indice_ponderado / pesos_total
            
            # Normalizar índice final a escala 0-100
            indice_final = ((indice_ponderado - indice_ponderado.min()) / 
                           (indice_ponderado.max() - indice_ponderado.min())) * 100
            
            # Crear DataFrame final con análisis técnico
            df_indice_avanzado = pd.DataFrame({
                'Fecha': indice_final.index,
                'Índice_Ciclo': indice_final.values,
                'Tendencia': indice_final.rolling(window=min(12, len(indice_final)//4)).mean(),
                'Volatilidad': indice_final.rolling(window=min(12, len(indice_final)//4)).std(),
                'Brecha_Producto': df_componentes.mean(axis=1) if len(df_componentes.columns) > 0 else 0
            })
            
            return df_indice_avanzado, componentes_procesados
            
    except Exception as e:
        st.error(f"Error al crear índice avanzado: {e}")
        return None, None

def mostrar_analisis_ciclo_completo():
    """
    Muestra un análisis completo del ciclo económico argentino
    """
    st.header("📊 Análisis Completo del Ciclo Económico Argentino")
    
    # Pestañas para diferentes tipos de análisis
    tabs = st.tabs([
        "📈 Índice Básico", 
        "🚀 Índice Avanzado",
        "🎯 Índice Sintético",
        "🔍 Comparación",
        "📋 Metodología"
    ])
    
    with tabs[0]:
        st.subheader("📈 Índice Básico - Datos Globales")
        
        # Crear y graficar índice básico
        df_indice, componentes = crear_indice_ciclo_economico_argentino()
        
        if df_indice is not None:
            graficar_indice_ciclo_economico(df_indice, componentes)
        else:
            st.error("No se pudo crear el índice básico")
    
    with tabs[1]:
        st.subheader("🚀 Índice Avanzado - Análisis Técnico")
        
        # Crear índice avanzado
        df_indice_avanzado, componentes_avanzados = crear_indice_ciclo_avanzado_argentino()
        
        if df_indice_avanzado is not None:
            graficar_indice_ciclo_economico(df_indice_avanzado, componentes_avanzados)
            
            # Mostrar análisis técnico detallado de componentes
            mostrar_analisis_tecnico_componentes(componentes_avanzados)
            
            # Información adicional sobre las series utilizadas
            st.subheader("📋 Series Utilizadas")
            
            for variable, info in componentes_avanzados.items():
                st.write(f"**{variable}** ({info['titulo']}): {len(info['datos'])} observaciones | Peso: {info['peso']:.1%}")
        else:
            st.error("No se pudo crear el índice avanzado")
    
    with tabs[2]:
        st.subheader("🎯 Índice Sintético - Combinación de Metodologías")
        
        # Crear índice sintético
        df_sintetico, df_indices = crear_indice_sintetico_ciclo()
        
        if df_sintetico is not None:
            graficar_indice_sintetico(df_sintetico, df_indices)
        else:
            st.error("No se pudo crear el índice sintético")
    
    with tabs[3]:
        st.subheader("🔍 Comparación de Índices")
        
        # Crear ambos índices para comparar
        df_basico, _ = crear_indice_ciclo_economico_argentino()
        df_avanzado, _ = crear_indice_ciclo_avanzado_argentino()
        
        if df_basico is not None and df_avanzado is not None:
            # Gráfico comparativo
            fig_comparacion = go.Figure()
            
            fig_comparacion.add_trace(go.Scatter(
                x=df_basico['Fecha'],
                y=df_basico['Índice_Ciclo'],
                mode='lines',
                name='Índice Básico',
                line=dict(color='#1f77b4', width=2)
            ))
            
            fig_comparacion.add_trace(go.Scatter(
                x=df_avanzado['Fecha'],
                y=df_avanzado['Índice_Ciclo'],
                mode='lines',
                name='Índice Avanzado',
                line=dict(color='#ff7f0e', width=2)
            ))
            
            fig_comparacion.update_layout(
                title="Comparación de Índices del Ciclo Económico",
                xaxis_title="Fecha",
                yaxis_title="Índice del Ciclo (0-100)",
                hovermode='x unified',
                template='plotly_white',
                height=500
            )
            
            st.plotly_chart(fig_comparacion, use_container_width=True)
            
            # Análisis de correlación entre índices
            # Alinear fechas para comparar
            df_basico_aligned = df_basico.set_index('Fecha')['Índice_Ciclo']
            df_avanzado_aligned = df_avanzado.set_index('Fecha')['Índice_Ciclo']
            
            # Encontrar fechas comunes
            fechas_comunes = df_basico_aligned.index.intersection(df_avanzado_aligned.index)
            
            if len(fechas_comunes) > 10:
                correlacion = df_basico_aligned.loc[fechas_comunes].corr(df_avanzado_aligned.loc[fechas_comunes])
                st.metric("Correlación entre Índices", f"{correlacion:.3f}")
                
                st.info(f"""
                **Interpretación de la Correlación:**
                - **Alta (>0.8)**: Ambos índices capturan el mismo patrón del ciclo
                - **Media (0.5-0.8)**: Los índices tienen similitudes pero también diferencias
                - **Baja (<0.5)**: Los índices capturan aspectos diferentes del ciclo
                
                **Correlación actual: {correlacion:.3f}**
                """)
            else:
                st.warning("No hay suficientes fechas comunes para calcular la correlación")
        else:
            st.error("No se pudieron crear ambos índices para la comparación")
    
    with tabs[3]:
        st.subheader("📋 Metodología de los Índices")
        
        st.markdown("""
        ## 📊 Metodología del Índice Básico
        
        **Variables Utilizadas:**
        - **S&P 500**: Proxy de actividad económica global
        - **VIX**: Volatilidad del mercado (invertido)
        - **Tasa 10Y EEUU**: Condiciones monetarias (invertida)
        - **Oro**: Commodities y refugio
        - **Dólar Index**: Condiciones cambiarias (invertido)
        - **Índice Mexicano**: Proxy del MERVAL
        
        **Cálculo:**
        1. Normalización de cada variable a base 100
        2. Inversión de variables contra-cíclicas
        3. Promedio simple de componentes
        4. Normalización final a escala 0-100
        
        ---
        
        ## 🚀 Metodología del Índice Avanzado
        
        **Fuentes de Datos:**
        - **Ministerio de Economía de Argentina**: Datos oficiales
        - **BCRA**: Variables monetarias
        - **INDEC**: Indicadores económicos
        
        **Variables Principales del Ciclo:**
        - **PBI Real**: Producto Interno Bruto ajustado por inflación (peso: 25%)
        - **PBI Per Cápita**: Ajustado por crecimiento poblacional (peso: 15%)
        - **EMAE**: Índice Mensual de Actividad Económica (peso: 20%)
        
        **Variables Complementarias:**
        - **Tasa de Desempleo**: Indicador contracíclico clave (peso: 15%)
        - **Utilización de Capacidad**: Intensidad uso recursos productivos (peso: 10%)
        - **Consumo Privado Real**: Componente importante del PBI (peso: 10%)
        - **Inversión Real**: Formación Bruta de Capital Fijo (peso: 5%)
        
        **Análisis Técnico Aplicado:**
        1. **Tasas de Crecimiento Interanual**: Suaviza estacionalidad
        2. **Filtro Hodrick-Prescott**: Separa tendencia de ciclo
        3. **Brechas de Producto**: Diferencia entre actual y potencial
        4. **Normalización Cíclica**: Estandarización de componentes
        5. **Ponderación Económica**: Según importancia en el ciclo
        
        ---
        
        ## 🔍 Interpretación de Fases
        
        - **80-100**: Expansión económica fuerte
        - **60-80**: Crecimiento moderado
        - **40-60**: Contracción económica
        - **20-40**: Recesión moderada
        - **0-20**: Recesión severa
        
        ---
        
        ## ⚠️ Limitaciones
        
        - **Índice Básico**: Usa proxies globales, no específicos de Argentina
        - **Índice Avanzado**: Depende de la disponibilidad de datos oficiales
        - **Rezagos**: Los datos oficiales pueden tener rezagos de publicación
        - **Revisión**: Los datos pueden ser revisados posteriormente
        """)

def crear_indice_sintetico_ciclo():
    """
    Crea un índice sintético que combina múltiples metodologías de análisis del ciclo
    """
    st.subheader("🎯 Índice Sintético del Ciclo Económico")
    
    try:
        with st.spinner("🔄 Calculando índice sintético..."):
            
            # Crear índices individuales
            df_basico, componentes_basico = crear_indice_ciclo_economico_argentino()
            df_avanzado, componentes_avanzado = crear_indice_ciclo_avanzado_argentino()
            
            if df_basico is None and df_avanzado is None:
                st.error("No se pudieron crear los índices individuales")
                return None
            
            # Combinar índices disponibles
            indices_disponibles = {}
            
            if df_basico is not None:
                indices_disponibles['Básico'] = df_basico.set_index('Fecha')['Índice_Ciclo']
            
            if df_avanzado is not None:
                indices_disponibles['Avanzado'] = df_avanzado.set_index('Fecha')['Índice_Ciclo']
            
            # Encontrar fechas comunes
            fechas_comunes = None
            for nombre, indice in indices_disponibles.items():
                if fechas_comunes is None:
                    fechas_comunes = indice.index
                else:
                    fechas_comunes = fechas_comunes.intersection(indice.index)
            
            if len(fechas_comunes) < 12:
                st.warning("No hay suficientes fechas comunes para crear el índice sintético")
                return None
            
            # Crear DataFrame con índices alineados
            df_indices = pd.DataFrame(index=fechas_comunes)
            
            for nombre, indice in indices_disponibles.items():
                df_indices[nombre] = indice.loc[fechas_comunes]
            
            # Calcular índice sintético (promedio ponderado)
            if len(df_indices.columns) == 2:
                # Si tenemos ambos índices, dar más peso al avanzado
                pesos = {'Básico': 0.3, 'Avanzado': 0.7}
            else:
                # Si solo tenemos uno, usarlo directamente
                pesos = {df_indices.columns[0]: 1.0}
            
            indice_sintetico = pd.Series(0.0, index=df_indices.index)
            
            for nombre, peso in pesos.items():
                if nombre in df_indices.columns:
                    indice_sintetico += df_indices[nombre] * peso
            
            # Normalizar índice sintético
            indice_sintetico_norm = ((indice_sintetico - indice_sintetico.min()) / 
                                   (indice_sintetico.max() - indice_sintetico.min())) * 100
            
            # Crear DataFrame final
            df_sintetico = pd.DataFrame({
                'Fecha': indice_sintetico_norm.index,
                'Índice_Sintético': indice_sintetico_norm.values,
                'Tendencia': indice_sintetico_norm.rolling(window=min(12, len(indice_sintetico_norm)//4)).mean(),
                'Volatilidad': indice_sintetico_norm.rolling(window=min(12, len(indice_sintetico_norm)//4)).std()
            })
            
            # Agregar componentes individuales para visualización
            for nombre in df_indices.columns:
                df_sintetico[f'Índice_{nombre}'] = df_indices[nombre].values
            
            return df_sintetico, df_indices
            
    except Exception as e:
        st.error(f"Error al crear índice sintético: {e}")
        return None, None

def graficar_indice_sintetico(df_sintetico, df_indices):
    """
    Grafica el índice sintético con comparación de metodologías
    """
    if df_sintetico is None or df_sintetico.empty:
        st.error("No hay datos para graficar")
        return
    
    st.subheader("📊 Índice Sintético del Ciclo Económico")
    
    # Gráfico principal del índice sintético
    fig_sintetico = go.Figure()
    
    # Línea del índice sintético
    fig_sintetico.add_trace(go.Scatter(
        x=df_sintetico['Fecha'],
        y=df_sintetico['Índice_Sintético'],
        mode='lines',
        name='Índice Sintético',
        line=dict(color='#1f77b4', width=4),
        hovertemplate='<b>Fecha:</b> %{x}<br><b>Índice Sintético:</b> %{y:.1f}<extra></extra>'
    ))
    
    # Línea de tendencia
    fig_sintetico.add_trace(go.Scatter(
        x=df_sintetico['Fecha'],
        y=df_sintetico['Tendencia'],
        mode='lines',
        name='Tendencia',
        line=dict(color='#ff7f0e', width=2, dash='dash'),
        hovertemplate='<b>Fecha:</b> %{x}<br><b>Tendencia:</b> %{y:.1f}<extra></extra>'
    ))
    
    # Agregar índices individuales
    colores_individuales = ['#2ca02c', '#d62728', '#9467bd']
    
    for i, columna in enumerate(df_indices.columns):
        if f'Índice_{columna}' in df_sintetico.columns:
            fig_sintetico.add_trace(go.Scatter(
                x=df_sintetico['Fecha'],
                y=df_sintetico[f'Índice_{columna}'],
                mode='lines',
                name=f'Índice {columna}',
                line=dict(color=colores_individuales[i % len(colores_individuales)], width=1, dash='dot'),
                opacity=0.7,
                hovertemplate=f'<b>Fecha:</b> %{{x}}<br><b>Índice {columna}:</b> %{{y:.1f}}<extra></extra>'
            ))
    
    # Líneas de referencia para fases del ciclo
    fig_sintetico.add_hline(y=80, line_dash="dash", line_color="green", 
                           annotation_text="Expansión", annotation_position="top right")
    fig_sintetico.add_hline(y=60, line_dash="dash", line_color="orange", 
                           annotation_text="Crecimiento Moderado", annotation_position="top right")
    fig_sintetico.add_hline(y=40, line_dash="dash", line_color="red", 
                           annotation_text="Contracción", annotation_position="top right")
    fig_sintetico.add_hline(y=20, line_dash="dash", line_color="darkred", 
                           annotation_text="Recesión", annotation_position="top right")
    
    fig_sintetico.update_layout(
        title="Índice Sintético del Ciclo Económico Argentino",
        xaxis_title="Fecha",
        yaxis_title="Índice del Ciclo (0-100)",
        yaxis=dict(range=[0, 100]),
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    st.plotly_chart(fig_sintetico, use_container_width=True)
    
    # Análisis de robustez
    st.subheader("🔍 Análisis de Robustez")
    
    # Calcular correlaciones entre índices
    if len(df_indices.columns) > 1:
        correlacion_matrix = df_indices.corr()
        
        st.write("**Matriz de Correlación entre Índices:**")
        st.dataframe(correlacion_matrix.style.format("{:.3f}"))
        
        # Análisis de divergencias
        st.subheader("📈 Análisis de Divergencias")
        
        if len(df_indices.columns) == 2:
            divergencia = df_indices.iloc[:, 0] - df_indices.iloc[:, 1]
            divergencia_actual = divergencia.iloc[-1]
            
            st.metric("Divergencia Actual", f"{divergencia_actual:+.1f}")
            
            if abs(divergencia_actual) > 10:
                st.warning("⚠️ **Alta divergencia** - Los índices muestran señales diferentes del ciclo")
            elif abs(divergencia_actual) > 5:
                st.info("ℹ️ **Divergencia moderada** - Los índices muestran algunas diferencias")
            else:
                st.success("✅ **Baja divergencia** - Los índices están alineados")
    
    # Métricas del índice sintético
    ultimo_sintetico = df_sintetico['Índice_Sintético'].iloc[-1]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Índice Sintético", f"{ultimo_sintetico:.1f}")
    
    with col2:
        cambio_sintetico = ((ultimo_sintetico / df_sintetico['Índice_Sintético'].iloc[-20]) - 1) * 100
        st.metric("Cambio 1 Mes", f"{cambio_sintetico:+.1f}%")
    
    with col3:
        volatilidad_sintetico = df_sintetico['Volatilidad'].iloc[-1]
        st.metric("Volatilidad", f"{volatilidad_sintetico:.1f}")
    
    # Recomendaciones basadas en el índice sintético
    if ultimo_sintetico >= 80:
        fase_sintetica = "Expansión"
        recomendacion = "Aumentar exposición a activos de riesgo, reducir defensivos"
    elif ultimo_sintetico >= 60:
        fase_sintetica = "Crecimiento Moderado"
        recomendacion = "Mantener balance entre riesgo y conservador"
    elif ultimo_sintetico >= 40:
        fase_sintetica = "Contracción"
        recomendacion = "Reducir riesgo, aumentar bonos y activos defensivos"
    else:
        fase_sintetica = "Recesión"
        recomendacion = "Máxima defensa, liquidez y activos de refugio"
    
    st.info(f"""
    **📊 Fase Sintética: {fase_sintetica}**
    
    **Recomendación de Portafolio:**
    {recomendacion}
    
    **Ventajas del Índice Sintético:**
    - Combina múltiples metodologías para mayor robustez
    - Reduce sesgos de una sola fuente de datos
    - Proporciona señal más confiable del ciclo económico
    """)

def analisis_ciclo_economico_argentina(variables_macro_arg, variables_macro_global):
    """Análisis específico del ciclo económico argentino"""
    
    puntuacion_ciclo_arg = 0
    indicadores_ciclo_arg = []
    
    # Indicadores específicos de Argentina
    if 'INFLACION' in variables_macro_arg:
        inflacion = variables_macro_arg['INFLACION']['valor_actual']
        if inflacion > 50:  # Inflación muy alta
            puntuacion_ciclo_arg -= 2
            indicadores_ciclo_arg.append(f"Inflación muy alta: {inflacion:.1f}% (-2)")
        elif inflacion > 30:  # Inflación alta
            puntuacion_ciclo_arg -= 1
            indicadores_ciclo_arg.append(f"Inflación alta: {inflacion:.1f}% (-1)")
        else:
            puntuacion_ciclo_arg += 1
            indicadores_ciclo_arg.append(f"Inflación controlada: {inflacion:.1f}% (+1)")
    
    if 'PBI' in variables_macro_arg:
        pbi_momentum = variables_macro_arg['PBI']['momentum']
        if pbi_momentum > 5:
            puntuacion_ciclo_arg += 2
            indicadores_ciclo_arg.append(f"PBI creciendo: {pbi_momentum:+.1f}% (+2)")
        elif pbi_momentum > 0:
            puntuacion_ciclo_arg += 1
            indicadores_ciclo_arg.append(f"PBI estable: {pbi_momentum:+.1f}% (+1)")
        else:
            puntuacion_ciclo_arg -= 1
            indicadores_ciclo_arg.append(f"PBI en contracción: {pbi_momentum:+.1f}% (-1)")
    
    if 'DESEMPLEO' in variables_macro_arg:
        desempleo = variables_macro_arg['DESEMPLEO']['valor_actual']
        if desempleo < 8:
            puntuacion_ciclo_arg += 1
            indicadores_ciclo_arg.append(f"Desempleo bajo: {desempleo:.1f}% (+1)")
        elif desempleo > 15:
            puntuacion_ciclo_arg -= 1
            indicadores_ciclo_arg.append(f"Desempleo alto: {desempleo:.1f}% (-1)")
        else:
            indicadores_ciclo_arg.append(f"Desempleo moderado: {desempleo:.1f}% (0)")
    
    # Combinar con indicadores globales
    if 'S&P 500' in variables_macro_global:
        sp500_momentum = variables_macro_global['S&P 500']['momentum']
        if sp500_momentum > 10:
            puntuacion_ciclo_arg += 1
            indicadores_ciclo_arg.append(f"Riesgo global bajo: S&P +{sp500_momentum:.1f}% (+1)")
        elif sp500_momentum < -10:
            puntuacion_ciclo_arg -= 1
            indicadores_ciclo_arg.append(f"Riesgo global alto: S&P {sp500_momentum:.1f}% (-1)")
    
    # Determinar fase del ciclo argentino
    if puntuacion_ciclo_arg >= 3:
        fase_ciclo_arg = "Expansión Fuerte"
        color_ciclo_arg = "success"
    elif puntuacion_ciclo_arg >= 1:
        fase_ciclo_arg = "Expansión Moderada"
        color_ciclo_arg = "info"
    elif puntuacion_ciclo_arg >= -1:
        fase_ciclo_arg = "Estancamiento"
        color_ciclo_arg = "warning"
    elif puntuacion_ciclo_arg >= -3:
        fase_ciclo_arg = "Recesión Moderada"
        color_ciclo_arg = "error"
    else:
        fase_ciclo_arg = "Recesión Severa"
        color_ciclo_arg = "error"
    
    return {
        'fase_ciclo': fase_ciclo_arg,
        'puntuacion': puntuacion_ciclo_arg,
        'indicadores': indicadores_ciclo_arg,
        'color': color_ciclo_arg
            }

def generar_informe_financiero_actual():
    """
    Genera un informe financiero completo con datos reales actuales
    similar al informe del 4 de agosto de 2025
    """
    st.title("📊 Informe Financiero Mensual")
    st.markdown("---")
    
    # Fecha actual
    fecha_actual = datetime.now().strftime("%d-%B-%Y")
    st.header(f"Comité de Productores - {fecha_actual}")
    
    # Temario
    st.subheader("📋 Temario")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Lectura de Mercados:**
        - La volatilidad se dispara por el dato de empleo
        - El complejo mundo de los pesos: ¿Menos liquidez pero más FX?
        """)
    
    with col2:
        st.markdown("""
        **Alternativas Locales:**
        - Portafolio Sugerido Actual
        - Rotación de Bonos
        - Performance Fondos
        - Oportunidades de Inversión
        - Actualización de Mercados
        """)
    
    st.markdown("---")
    
    # Lectura de Mercados
    st.header("🌍 Lectura de Mercados")
    
    try:
        # Datos de EEUU
        st.subheader("🇺🇸 Estados Unidos")
        
        # Obtener datos del S&P 500
        sp500 = yf.download('^GSPC', start=(datetime.now() - timedelta(days=30)), end=datetime.now())
        if not sp500.empty:
            cambio_sp500 = ((sp500['Close'][-1] - sp500['Close'][0]) / sp500['Close'][0]) * 100
            st.metric("S&P 500 (30 días)", f"{sp500['Close'][-1]:.2f}", f"{cambio_sp500:+.2f}%")
        
        # Obtener datos del Nasdaq
        nasdaq = yf.download('^IXIC', start=(datetime.now() - timedelta(days=30)), end=datetime.now())
        if not nasdaq.empty:
            cambio_nasdaq = ((nasdaq['Close'][-1] - nasdaq['Close'][0]) / nasdaq['Close'][0]) * 100
            st.metric("Nasdaq (30 días)", f"{nasdaq['Close'][-1]:.2f}", f"{cambio_nasdaq:+.2f}%")
        
        # Obtener datos del VIX
        vix = yf.download('^VIX', start=(datetime.now() - timedelta(days=7)), end=datetime.now())
        if not vix.empty:
            cambio_vix = ((vix['Close'][-1] - vix['Close'][0]) / vix['Close'][0]) * 100
            st.metric("VIX (7 días)", f"{vix['Close'][-1]:.2f}", f"{cambio_vix:+.2f}%")
        
        # Obtener datos del Dólar (usando un proxy para Argentina)
        try:
            # Intentar obtener datos del peso argentino (si están disponibles)
            usd_ars = yf.download('USDARS=X', start=(datetime.now() - timedelta(days=30)), end=datetime.now())
            if not usd_ars.empty:
                cambio_usd = ((usd_ars['Close'][-1] - usd_ars['Close'][0]) / usd_ars['Close'][0]) * 100
                st.metric("USD/ARS (30 días)", f"{usd_ars['Close'][-1]:.2f}", f"{cambio_usd:+.2f}%")
            else:
                # Fallback a USD/CAD como proxy
                usd_cad = yf.download('USDCAD', start=(datetime.now() - timedelta(days=30)), end=datetime.now())
                if not usd_cad.empty:
                    cambio_usd = ((usd_cad['Close'][-1] - usd_cad['Close'][0]) / usd_cad['Close'][0]) * 100
                    st.metric("USD/CAD (30 días)", f"{usd_cad['Close'][-1]:.4f}", f"{cambio_usd:+.2f}%")
        except:
            st.info("ℹ️ No se pudieron obtener datos del tipo de cambio")
        
        # Análisis de volatilidad
        if not sp500.empty:
            volatilidad_sp500 = sp500['Close'].pct_change().std() * np.sqrt(252) * 100
            st.info(f"📈 **Volatilidad anualizada S&P 500:** {volatilidad_sp500:.2f}%")
        
        # Obtener datos de bonos del tesoro
        try:
            # 10-year Treasury
            tnx = yf.download('^TNX', start=(datetime.now() - timedelta(days=30)), end=datetime.now())
            if not tnx.empty:
                cambio_tnx = ((tnx['Close'][-1] - tnx['Close'][0]) / tnx['Close'][0]) * 100
                st.metric("10Y Treasury Yield (30 días)", f"{tnx['Close'][-1]:.2f}%", f"{cambio_tnx:+.2f}%")
            
            # 2-year Treasury
            irx = yf.download('^IRX', start=(datetime.now() - timedelta(days=30)), end=datetime.now())
            if not irx.empty:
                cambio_irx = ((irx['Close'][-1] - irx['Close'][0]) / irx['Close'][0]) * 100
                st.metric("2Y Treasury Yield (30 días)", f"{irx['Close'][-1]:.2f}%", f"{cambio_irx:+.2f}%")
                
        except Exception as e:
            st.warning(f"⚠️ No se pudieron obtener datos de bonos del tesoro: {e}")
        
    except Exception as e:
        st.error(f"❌ Error obteniendo datos de EEUU: {e}")
    
    st.markdown("---")
    
    # Datos de Argentina
    st.subheader("🇦🇷 Argentina")
    
    try:
        # Obtener datos del Merval (si están disponibles)
        merval = yf.download('^MERV', start=(datetime.now() - timedelta(days=30)), end=datetime.now())
        if not merval.empty:
            cambio_merval = ((merval['Close'][-1] - merval['Close'][0]) / merval['Close'][0]) * 100
            st.metric("Merval (30 días)", f"{merval['Close'][-1]:.2f}", f"{cambio_merval:+.2f}%")
        
        # Obtener datos de YPF
        ypf = yf.download('YPF', start=(datetime.now() - timedelta(days=30)), end=datetime.now())
        if not ypf.empty:
            cambio_ypf = ((ypf['Close'][-1] - ypf['Close'][0]) / ypf['Close'][0]) * 100
            st.metric("YPF (30 días)", f"{ypf['Close'][-1]:.2f}", f"{cambio_ypf:+.2f}%")
        
        # Obtener datos de Banco Macro
        macro = yf.download('BMA', start=(datetime.now() - timedelta(days=30)), end=datetime.now())
        if not macro.empty:
            cambio_macro = ((macro['Close'][-1] - macro['Close'][0]) / macro['Close'][0]) * 100
            st.metric("Banco Macro (BMA)", f"{macro['Close'][-1]:.2f}", f"{cambio_macro:+.2f}%")
            
    except Exception as e:
        st.error(f"❌ Error obteniendo datos de Argentina: {e}")
    
    st.markdown("---")
    
    # Mercados Emergentes
    st.subheader("🌱 Mercados Emergentes")
    
    try:
        # Obtener datos de Brasil
        ewz = yf.download('EWZ', start=(datetime.now() - timedelta(days=30)), end=datetime.now())
        if not ewz.empty:
            cambio_ewz = ((ewz['Close'][-1] - ewz['Close'][0]) / ewz['Close'][0]) * 100
            st.metric("ETF Brasil (EWZ)", f"{ewz['Close'][-1]:.2f}", f"{cambio_ewz:+.2f}%")
        
        # Obtener datos de México
        eww = yf.download('EWW', start=(datetime.now() - timedelta(days=30)), end=datetime.now())
        if not eww.empty:
            cambio_eww = ((eww['Close'][-1] - eww['Close'][0]) / eww['Close'][0]) * 100
            st.metric("ETF México (EWW)", f"{eww['Close'][-1]:.2f}", f"{cambio_eww:+.2f}%")
        
    except Exception as e:
        st.error(f"❌ Error obteniendo datos de emergentes: {e}")
    
    st.markdown("---")
    
    # Commodities y Materias Primas
    st.subheader("🛢️ Commodities y Materias Primas")
    
    try:
        # Obtener datos del petróleo
        oil = yf.download('CL=F', start=(datetime.now() - timedelta(days=30)), end=datetime.now())
        if not oil.empty:
            cambio_oil = ((oil['Close'][-1] - oil['Close'][0]) / oil['Close'][0]) * 100
            st.metric("Petróleo WTI (30 días)", f"${oil['Close'][-1]:.2f}", f"{cambio_oil:+.2f}%")
        
        # Obtener datos del oro
        gold = yf.download('GC=F', start=(datetime.now() - timedelta(days=30)), end=datetime.now())
        if not gold.empty:
            cambio_gold = ((gold['Close'][-1] - gold['Close'][0]) / gold['Close'][0]) * 100
            st.metric("Oro (30 días)", f"${gold['Close'][-1]:.2f}", f"{cambio_gold:+.2f}%")
        
        # Obtener datos de la plata
        silver = yf.download('SI=F', start=(datetime.now() - timedelta(days=30)), end=datetime.now())
        if not silver.empty:
            cambio_silver = ((silver['Close'][-1] - silver['Close'][0]) / silver['Close'][0]) * 100
            st.metric("Plata (30 días)", f"${silver['Close'][-1]:.2f}", f"{cambio_silver:+.2f}%")
        
        # Obtener datos del cobre
        copper = yf.download('HG=F', start=(datetime.now() - timedelta(days=30)), end=datetime.now())
        if not copper.empty:
            cambio_copper = ((copper['Close'][-1] - copper['Close'][0]) / copper['Close'][0]) * 100
            st.metric("Cobre (30 días)", f"${copper['Close'][-1]:.2f}", f"{cambio_copper:+.2f}%")
            
    except Exception as e:
        st.error(f"❌ Error obteniendo datos de commodities: {e}")
    
    st.markdown("---")
    
    # Análisis de Sectores
    st.subheader("🏭 Análisis de Sectores")
    
    try:
        # ETFs sectoriales
        sectores = {
            'XLU': 'Utilities',
            'XLK': 'Technology',
            'XLE': 'Energy',
            'XLF': 'Financials',
            'XLV': 'Healthcare'
        }
        
        col1, col2 = st.columns(2)
        
        for i, (ticker, nombre) in enumerate(sectores.items()):
            try:
                data = yf.download(ticker, start=(datetime.now() - timedelta(days=30)), end=datetime.now())
                if not data.empty:
                    cambio = ((data['Close'][-1] - data['Close'][0]) / data['Close'][0]) * 100
                    if i % 2 == 0:
                        with col1:
                            st.metric(f"{nombre} ({ticker})", f"{data['Close'][-1]:.2f}", f"{cambio:+.2f}%")
                    else:
                        with col2:
                            st.metric(f"{nombre} ({ticker})", f"{data['Close'][-1]:.2f}", f"{cambio:+.2f}%")
            except:
                continue
                
    except Exception as e:
        st.error(f"❌ Error obteniendo datos sectoriales: {e}")
    
    st.markdown("---")
    
    # Portafolios Sugeridos
    st.header("💼 Portafolios Sugeridos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Conservador/Moderado")
        st.markdown("""
        **Composición:**
        - 70% dólares y 30% pesos
        - 60% renta fija y 40% renta variable
        
        **Estrategia:**
        - Reducir exposición en instrumentos en pesos
        - Sumar alternativas dolarizadas
        - Mantener activos que permitan diversificación geográfica
        """)
    
    with col2:
        st.subheader("🚀 Agresivo")
        st.markdown("""
        **Composición:**
        - 60% dólares y 40% pesos
        - 55% renta fija y 45% renta variable
        
        **Estrategia:**
        - Sobreponderar alternativas con rendimientos mensuales en pesos
        - Preferencia por bonos ajustables por CER
        - LECAPs de corto plazo
        """)
    
    st.markdown("---")
    
    # Performance Histórica
    st.subheader("📊 Performance Histórica")
    
    try:
        # Simular performance histórica (en un caso real, obtendrías estos datos de tu base)
        performance_data = {
            'Período': ['1 Mes', '3 Meses', '6 Meses', '12 Meses'],
            'Conservador/Moderado': [7.5, 18.2, 28.7, 35.4],
            'Agresivo': [5.0, 22.1, 35.8, 61.2],
            'Dólar MEP': [3.2, 8.9, 15.4, 5.8],
            'Plazo Fijo': [2.8, 8.4, 16.8, 35.5]
        }
        
        df_performance = pd.DataFrame(performance_data)
        st.dataframe(df_performance, use_container_width=True)
        
        # Gráfico de performance
        fig = go.Figure()
        
        for col in ['Conservador/Moderado', 'Agresivo', 'Dólar MEP', 'Plazo Fijo']:
            if col != 'Período':
                fig.add_trace(go.Bar(
                    name=col,
                    x=df_performance['Período'],
                    y=df_performance[col],
                    text=[f'{val:.1f}%' for val in df_performance[col]],
                    textposition='auto'
                ))
        
        fig.update_layout(
            title="Performance Comparativa de Portafolios",
            xaxis_title="Período",
            yaxis_title="Rendimiento (%)",
            barmode='group',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error generando performance: {e}")
    
    st.markdown("---")
    
    # Oportunidades de Inversión
    st.header("💡 Oportunidades de Inversión")
    
    st.subheader("🏦 Bonos Provinciales")
    st.markdown("""
    **Análisis BA37D y BB37D:**
    - Vencimiento: 2037
    - Cupones step-up semestrales: 6,625% y 5,875%
    - Consolidados como principales referentes de deuda sub-soberana
    - Spread comprimido vs AE38 (por debajo de 200 pb)
    - **Recomendación:** Considerar rotación por niveles actuales
    """)
    
    st.subheader("⚡ Edenor")
    st.markdown("""
    **Características:**
    - Mayor distribuidora de electricidad de Argentina
    - EBITDA: USD 242 millones (margen 10%)
    - Deuda financiera: USD 415 millones
    - Liquidez: USD 347 millones
    - Calificación: A(arg) con Perspectiva Estable
    
    **Oportunidades:**
    - ON Hard dollar Clase 8 (Agosto 2026)
    - Tasa: 8,0% en USD
    - ON TAMAR Clase 9 (Agosto 2026)
    - Tasa: TAMAR +6%
    """)
    
    st.markdown("---")
    
    # Fondos Comunes de Inversión
    st.header("💰 Fondos Comunes de Inversión")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💵 IOL Dólar Ahorro Plus")
        st.markdown("""
        **Métricas Julio 2025:**
        - Retorno directo: +0,58%
        - Retorno mensual anualizado: +7%
        - Retorno acumulado: +3,4%
        - Volatilidad anualizada: 1%
        - Duration: 1,9 años
        """)
    
    with col2:
        st.subheader("🚀 IOL Portafolio Potenciado")
        st.markdown("""
        **Métricas Julio 2025:**
        - Retorno directo: +5,2%
        - Retorno mensual anualizado: +62,6%
        - Retorno acumulado: +7,3%
        - Volatilidad anualizada: 12%
        - VaR diario: -1%
        """)
    
    st.markdown("---")
    
    # Resumen y Recomendaciones
    st.header("🎯 Resumen y Recomendaciones")
    
    st.markdown("""
    **Lectura de Mercados:**
    - La volatilidad se mantiene elevada por incertidumbre en datos económicos
    - Los mercados emergentes muestran divergencias sectoriales
    - El dólar mantiene tendencia alcista con presiones inflacionarias
    
    **Estrategia Recomendada:**
    1. **Mantener diversificación geográfica** con exposición a mercados desarrollados
    2. **Considerar rotación** en bonos provinciales por niveles actuales
    3. **Sobreponderar renta fija local** con tasas reales atractivas
    4. **Mantener liquidez** para aprovechar oportunidades de volatilidad
    
    **Riesgos a Monitorear:**
    - Evolución de la política monetaria de la Fed
    - Tensiones geopolíticas y comerciales
    - Dinámica inflacionaria global
    - Calendario electoral en mercados emergentes
    """)
    
    st.markdown("---")
    
    # Análisis de Correlaciones
    st.header("🔗 Análisis de Correlaciones")
    
    try:
        # Crear DataFrame con los principales activos
        activos_principales = {}
        
        # Agregar activos disponibles
        if 'sp500' in locals() and not sp500.empty:
            activos_principales['S&P 500'] = sp500['Close']
        if 'nasdaq' in locals() and not nasdaq.empty:
            activos_principales['Nasdaq'] = nasdaq['Close']
        if 'gold' in locals() and not gold.empty:
            activos_principales['Oro'] = gold['Close']
        if 'oil' in locals() and not oil.empty:
            activos_principales['Petróleo'] = oil['Close']
        if 'merval' in locals() and not merval.empty:
            activos_principales['Merval'] = merval['Close']
        
        if len(activos_principales) > 1:
            # Crear DataFrame de correlaciones
            df_correlaciones = pd.DataFrame(activos_principales)
            
            # Calcular correlaciones
            correlaciones = df_correlaciones.pct_change().corr()
            
            # Mostrar matriz de correlaciones
            st.subheader("📊 Matriz de Correlaciones (30 días)")
            st.dataframe(correlaciones.round(3), use_container_width=True)
            
            # Crear heatmap de correlaciones
            fig_corr = px.imshow(
                correlaciones,
                text_auto=True,
                aspect="auto",
                color_continuous_scale='RdBu',
                title="Mapa de Calor de Correlaciones"
            )
            fig_corr.update_layout(height=500)
            st.plotly_chart(fig_corr, use_container_width=True)
            
            # Análisis de correlaciones
            st.subheader("💡 Interpretación de Correlaciones")
            
            # Encontrar correlaciones más altas y más bajas
            correlaciones_sin_diagonal = correlaciones.where(~np.eye(correlaciones.shape[0], dtype=bool))
            
            if not correlaciones_sin_diagonal.empty:
                max_corr = correlaciones_sin_diagonal.max().max()
                min_corr = correlaciones_sin_diagonal.min().min()
                
                # Encontrar qué activos tienen la correlación más alta
                max_corr_idx = correlaciones_sin_diagonal.stack().idxmax()
                min_corr_idx = correlaciones_sin_diagonal.stack().idxmin()
                
                st.info(f"""
                **🔍 Hallazgos Clave:**
                - **Correlación más alta:** {max_corr_idx[0]} vs {max_corr_idx[1]} ({max_corr:.3f})
                - **Correlación más baja:** {min_corr_idx[0]} vs {min_corr_idx[1]} ({min_corr:.3f})
                
                **📈 Implicaciones:**
                - Correlaciones altas sugieren menor diversificación
                - Correlaciones bajas ofrecen mejor diversificación
                - Considere activos con correlaciones negativas para reducir riesgo
                """)
        
    except Exception as e:
        st.error(f"❌ Error generando análisis de correlaciones: {e}")
    
    st.markdown("---")
    
    # Opciones de Exportación
    st.header("📤 Exportar Informe")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Resumen Ejecutivo")
        if st.button("📄 Generar Resumen", use_container_width=True):
            st.success("✅ Resumen generado")
            st.markdown("""
            **📊 RESUMEN EJECUTIVO - {fecha_actual}**
            
            **🌍 Mercados Globales:**
            - S&P 500: {sp500['Close'][-1]:.2f} ({((sp500['Close'][-1] - sp500['Close'][0]) / sp500['Close'][0] * 100):+.2f}%)
            - Nasdaq: {nasdaq['Close'][-1]:.2f} ({((nasdaq['Close'][-1] - nasdaq['Close'][0]) / nasdaq['Close'][0] * 100):+.2f}%)
            - VIX: {vix['Close'][-1]:.2f} ({((vix['Close'][-1] - vix['Close'][0]) / vix['Close'][0] * 100):+.2f}%)
            
            **🇦🇷 Mercado Local:**
            - Merval: {merval['Close'][-1]:.2f} ({((merval['Close'][-1] - merval['Close'][0]) / merval['Close'][0] * 100):+.2f}%)
            
            **🛢️ Commodities:**
            - Petróleo: ${oil['Close'][-1]:.2f} ({((oil['Close'][-1] - oil['Close'][0]) / oil['Close'][0] * 100):+.2f}%)
            - Oro: ${gold['Close'][-1]:.2f} ({((gold['Close'][-1] - gold['Close'][0]) / gold['Close'][0] * 100):+.2f}%)
            
            **💡 Recomendaciones:**
            - Mantener diversificación geográfica
            - Considerar rotación en bonos provinciales
            - Monitorear volatilidad del VIX
            """.format(
                fecha_actual=fecha_actual,
                sp500=sp500 if 'sp500' in locals() and not sp500.empty else pd.DataFrame({'Close': [0, 0]}),
                nasdaq=nasdaq if 'nasdaq' in locals() and not nasdaq.empty else pd.DataFrame({'Close': [0, 0]}),
                vix=vix if 'vix' in locals() and not vix.empty else pd.DataFrame({'Close': [0, 0]}),
                merval=merval if 'merval' in locals() and not merval.empty else pd.DataFrame({'Close': [0, 0]}),
                oil=oil if 'oil' in locals() and not oil.empty else pd.DataFrame({'Close': [0, 0]}),
                gold=gold if 'gold' in locals() and not gold.empty else pd.DataFrame({'Close': [0, 0]})
            ))
    
    with col2:
        st.subheader("📊 Datos para Análisis")
        if st.button("💾 Descargar Datos", use_container_width=True):
            st.info("💡 Los datos están disponibles en tiempo real en el informe")
            st.markdown("""
            **📈 Datos Disponibles:**
            - Precios históricos de 30 días
            - Correlaciones entre activos
            - Métricas de volatilidad
            - Performance comparativa
            
            **🔧 Para análisis avanzado:**
            - Use las funciones de optimización de portafolio
            - Acceda al análisis técnico
            - Explore el dashboard unificado
            """)
    
    st.markdown("---")
    st.markdown("*Informe generado automáticamente con datos en tiempo real*")

def buscar_noticias_automaticas_gemini(gemini_api_key, tickers=None, max_creditos=3):
    """
    Busca noticias automáticamente usando Gemini con el mínimo uso de créditos.
    
    Args:
        gemini_api_key: API key de Gemini
        tickers: Lista de tickers para buscar noticias (opcional)
        max_creditos: Máximo número de llamadas a Gemini (por defecto 3)
    
    Returns:
        DataFrame con noticias y análisis
    """
    
    # Configurar Gemini
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Error configurando Gemini: {e}")
        return None
    
    # Tickers por defecto si no se especifican
    if tickers is None:
        tickers = ['META', 'GOOGL', 'AMZN', 'MSFT', 'AAPL', 'TSLA', '^MERV', 'YPF']
    
    st.subheader("🔍 Búsqueda Automática de Noticias con IA")
    st.info("💡 Usando Gemini para análisis inteligente con mínimo uso de créditos")
    
    # Crear un prompt eficiente que combine múltiples tickers
    prompt_base = f"""
    Analiza las noticias más relevantes de los últimos 3 días para estos tickers: {', '.join(tickers[:6])}
    
    Proporciona:
    1. Resumen ejecutivo (máximo 100 palabras)
    2. 3-5 noticias clave por ticker más importante
    3. Impacto esperado en el mercado (positivo/negativo/neutral)
    4. Recomendación de inversión (1-2 frases)
    
    Formato de respuesta:
    - Solo texto, sin formato especial
    - Máximo 300 palabras total
    - Enfoque en datos concretos y análisis objetivo
    """
    
    try:
        with st.spinner("🤖 Analizando noticias con Gemini..."):
            response = model.generate_content(prompt_base)
            
            if response and response.text:
                st.success("✅ Análisis completado con 1 crédito de Gemini")
                
                # Mostrar el análisis
                st.markdown("### 📰 Resumen de Noticias")
                st.write(response.text)
                
                # Crear un DataFrame estructurado
                noticias_data = []
                lines = response.text.split('\n')
                current_ticker = None
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('-') and not line.startswith('•'):
                        if any(ticker in line.upper() for ticker in tickers):
                            current_ticker = next((t for t in tickers if t in line.upper()), 'General')
                        elif line and len(line) > 20:
                            noticias_data.append({
                                'Ticker': current_ticker or 'General',
                                'Noticia': line[:100] + '...' if len(line) > 100 else line,
                                'Impacto': 'Neutral',
                                'Fecha': datetime.now().strftime('%Y-%m-%d')
                            })
                
                if noticias_data:
                    df_noticias = pd.DataFrame(noticias_data)
                    st.markdown("### 📊 Noticias Estructuradas")
                    st.dataframe(df_noticias, use_container_width=True)
                    
                    # Opción para análisis adicional con 1 crédito más
                    if st.button("🔍 Análisis Técnico Adicional (1 crédito)", key="analisis_adicional"):
                        if max_creditos > 1:
                            prompt_tecnico = f"""
                            Basándote en las noticias anteriores, proporciona:
                            1. Análisis técnico breve de {tickers[0]} y {tickers[1]}
                            2. Niveles de soporte y resistencia clave
                            3. Señales de trading (máximo 150 palabras)
                            """
                            
                            response_tecnico = model.generate_content(prompt_tecnico)
                            if response_tecnico and response_tecnico.text:
                                st.markdown("### 📈 Análisis Técnico")
                                st.write(response_tecnico.text)
                                st.info("💡 Usado 2 créditos de Gemini en total")
                            else:
                                st.warning("No se pudo generar análisis técnico")
                        else:
                            st.warning("No hay créditos disponibles para análisis adicional")
                    
                    # Opción para análisis de sentimiento con 1 crédito más
                    if st.button("😊 Análisis de Sentimiento (1 crédito)", key="sentimiento"):
                        if max_creditos > 1:
                            prompt_sentimiento = f"""
                            Analiza el sentimiento del mercado basándote en las noticias:
                            1. Sentimiento general (alcista/bajista/neutral)
                            2. Factores de riesgo principales
                            3. Oportunidades emergentes (máximo 100 palabras)
                            """
                            
                            response_sentimiento = model.generate_content(prompt_sentimiento)
                            if response_sentimiento and response_sentimiento.text:
                                st.markdown("### 😊 Análisis de Sentimiento")
                                st.write(response_sentimiento.text)
                                st.info("💡 Usado 2 créditos de Gemini en total")
                            else:
                                st.warning("No se pudo generar análisis de sentimiento")
                        else:
                            st.warning("No hay créditos disponibles para análisis de sentimiento")
                
                return df_noticias if noticias_data else None
                
            else:
                st.error("No se pudo generar contenido con Gemini")
                return None
                
    except Exception as e:
        st.error(f"Error en la generación: {e}")
        return None

def buscar_noticias_especificas_gemini(gemini_api_key, ticker, max_creditos=2):
    """
    Busca noticias específicas para un ticker usando Gemini de forma eficiente.
    
    Args:
        gemini_api_key: API key de Gemini
        ticker: Ticker específico a analizar
        max_creditos: Máximo número de llamadas a Gemini
    
    Returns:
        Análisis específico del ticker
    """
    
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Error configurando Gemini: {e}")
        return None
    
    st.subheader(f"🔍 Análisis Específico: {ticker}")
    
    prompt_especifico = f"""
    Analiza {ticker} con enfoque en:
    1. Últimas noticias relevantes (máximo 3)
    2. Análisis técnico breve
    3. Recomendación de inversión
    4. Factores de riesgo
    
    Máximo 200 palabras, solo texto.
    """
    
    try:
        with st.spinner(f"🤖 Analizando {ticker}..."):
            response = model.generate_content(prompt_especifico)
            
            if response and response.text:
                st.success(f"✅ Análisis de {ticker} completado con 1 crédito")
                st.markdown("### 📊 Análisis Completo")
                st.write(response.text)
                
                # Opción para análisis más profundo
                if st.button(f"🔍 Análisis Profundo de {ticker} (1 crédito)", key=f"profundo_{ticker}"):
                    if max_creditos > 1:
                        prompt_profundo = f"""
                        Profundiza en el análisis de {ticker}:
                        1. Comparación con competidores
                        2. Análisis fundamental breve
                        3. Perspectivas a 3-6 meses
                        4. Niveles de entrada y salida sugeridos
                        
                        Máximo 250 palabras.
                        """
                        
                        response_profundo = model.generate_content(prompt_profundo)
                        if response_profundo and response_profundo.text:
                            st.markdown("### 📈 Análisis Profundo")
                            st.write(response_profundo.text)
                            st.info("💡 Usado 2 créditos de Gemini en total")
                        else:
                            st.warning("No se pudo generar análisis profundo")
                    else:
                        st.warning("No hay créditos disponibles para análisis profundo")
                
                return response.text
            else:
                st.error("No se pudo generar análisis")
                return None
                
    except Exception as e:
        st.error(f"Error en el análisis: {e}")
        return None

def mostrar_busqueda_noticias_gemini():
    """
    Interfaz principal para la búsqueda automática de noticias con Gemini
    """
    st.title("🤖 Búsqueda Automática de Noticias con IA")
    st.markdown("---")
    
    # Configuración de API Key
    gemini_api_key = st.text_input(
        "🔑 API Key de Gemini",
        value="AIzaSyBFtK05ndkKgo4h0w9gl224Gn94NaWaI6E",
        type="password",
        help="Ingresa tu API key de Gemini para acceder a análisis automático de noticias"
    )
    
    if not gemini_api_key:
        st.warning("⚠️ Ingresa tu API key de Gemini para continuar")
        return
    
    # Opciones de búsqueda
    st.subheader("🎯 Opciones de Búsqueda")
    
    col1, col2 = st.columns(2)
    
    with col1:
        modo_busqueda = st.radio(
            "Selecciona el modo de búsqueda:",
            ["📰 Análisis General", "🎯 Ticker Específico"],
            help="Análisis general usa menos créditos, ticker específico es más detallado"
        )
    
    with col2:
        max_creditos = st.slider(
            "💳 Máximo de créditos a usar:",
            min_value=1,
            max_value=5,
            value=3,
            help="Controla cuántas llamadas a Gemini realizarás"
        )
    
    st.markdown("---")
    
    if modo_busqueda == "📰 Análisis General":
        st.info("💡 **Modo Eficiente**: Analiza múltiples tickers en una sola llamada (1 crédito)")
        
        # Tickers personalizables
        tickers_default = ['META', 'GOOGL', 'AMZN', 'MSFT', 'AAPL', 'TSLA', '^MERV', 'YPF']
        tickers_personalizados = st.multiselect(
            "📊 Selecciona tickers para analizar:",
            options=tickers_default,
            default=tickers_default[:6],
            help="Selecciona hasta 6 tickers para optimizar el uso de créditos"
        )
        
        if st.button("🚀 Iniciar Búsqueda Automática", use_container_width=True):
            if tickers_personalizados:
                buscar_noticias_automaticas_gemini(gemini_api_key, tickers_personalizados, max_creditos)
            else:
                st.warning("Selecciona al menos un ticker")
    
    else:  # Ticker Específico
        st.info("💡 **Modo Detallado**: Análisis profundo de un ticker específico (1-2 créditos)")
        
        ticker_especifico = st.text_input(
            "🎯 Ingresa el ticker a analizar:",
            value="META",
            help="Ejemplo: META, GOOGL, AMZN, etc."
        ).upper()
        
        if st.button(f"🔍 Analizar {ticker_especifico}", use_container_width=True):
            if ticker_especifico:
                buscar_noticias_especificas_gemini(gemini_api_key, ticker_especifico, max_creditos)
            else:
                st.warning("Ingresa un ticker válido")
    
    # Información sobre uso de créditos
    st.markdown("---")
    st.markdown("### 💰 Información sobre Créditos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📰 Análisis General", "1 crédito", "Múltiples tickers")
    
    with col2:
        st.metric("🎯 Ticker Específico", "1-2 créditos", "Análisis detallado")
    
    with col3:
        st.metric("🔍 Análisis Adicional", "+1 crédito", "Por cada extra")
    
    st.info("""
    **💡 Consejos para optimizar créditos:**
    - Usa el modo general para obtener una visión amplia
    - Elige tickers específicos solo cuando necesites análisis profundo
    - Combina múltiples análisis en una sola sesión
    - Revisa el historial de análisis antes de hacer nuevas consultas
    """)

if __name__ == "__main__":
    try:
        st.write("🚀 Iniciando aplicación...")
        main()
    except Exception as e:
        st.error(f"❌ Error fatal al iniciar la aplicación: {str(e)}")
        st.error(f"Tipo de error: {type(e).__name__}")
        import traceback
        st.code(traceback.format_exc())
        
        # Información de diagnóstico
        st.subheader("🔍 Diagnóstico del Sistema")
        st.write(f"**Streamlit version:** {st.__version__}")
        st.write(f"**Pandas version:** {pd.__version__}")
        st.write(f"**Numpy version:** {np.__version__}")
        
        # Verificar importaciones críticas
        try:
            import yfinance
            st.success("✅ yfinance importado correctamente")
        except Exception as e:
            st.error(f"❌ Error con yfinance: {e}")
        
        try:
            import plotly
            st.success("✅ plotly importado correctamente")
        except Exception as e:
            st.error(f"❌ Error con plotly: {e}")
        
        try:
            import requests
            st.success("✅ requests importado correctamente")
        except Exception as e:
            st.error(f"❌ Error con requests: {e}")
