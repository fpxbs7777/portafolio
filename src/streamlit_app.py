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
                serie = pd.Series(precios, index=fechas, name='precio')
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

# ... (rest of the code remains the same)

def compute_portfolio(self, strategy=None, target_return=None, risk_aversion=1.0, n_simulations=1000, use_monte_carlo=False):
    """
    Calcula los pesos óptimos del portafolio según la estrategia especificada.
    
    Args:
        strategy (str): Tipo de optimización a realizar. Opciones:
            - 'min-variance': Mínima varianza
            - 'min-variance-l1': Mínima varianza con restricción L1
            - 'min-variance-l2': Mínima varianza con restricción L2
            - 'equi-weight': Pesos iguales
            - 'long-only': Optimización con pesos positivos
            - 'markowitz': Optimización de Markowitz (máximo ratio de Sharpe o retorno objetivo)
            - 'risk-parity': Asignación de riesgo equitativa
            - 'mean-variance': Media-varianza con aversión al riesgo ajustable
        target_return (float, optional): Retorno objetivo para la optimización
        risk_aversion (float): Parámetro de aversión al riesgo (solo para mean-variance)
        n_simulations (int): Número de simulaciones para Monte Carlo
        use_monte_carlo (bool): Usar simulación de Monte Carlo para encontrar punto inicial
            
    Returns:
        output: Objeto con los resultados de la optimización o None en caso de error
    """
    try:
        if self.cov_matrix is None or self.mean_returns is None:
            self.compute_covariance()
        
        n_assets = len(self.rics)
        
        # Configuración de la optimización
        bounds = tuple((0.0, 1.0) for _ in range(n_assets))
        constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}]
        
        # Manejar retorno objetivo
        if target_return is not None:
            # Forzar el retorno objetivo como restricción fuerte
            constraints.append({
                'type': 'eq',
                'fun': lambda x: np.sum(self.mean_returns * x) - target_return,
                'jac': lambda x: self.mean_returns
            })
        
        # Función objetivo: varianza del portafolio
        def portfolio_variance_obj(weights):
            return portfolio_variance(weights, self.cov_matrix)
                
        # Función objetivo: media-varianza con aversión al riesgo
        def mean_variance_obj(weights):
            port_ret = np.sum(self.mean_returns * weights)
            port_var = portfolio_variance(weights, self.cov_matrix)
            return -port_ret + risk_aversion * port_var  # Maximizar retorno, minimizar varianza
        
        # Configuración común de la optimización
        opt_options = {
            'maxiter': 1000,
            'ftol': 1e-6,  # Tolerancia más ajustada para mejor precisión
            'disp': False,
            'eps': 1e-10,
            'iprint': 0  # Sin salida de depuración para mayor velocidad
        }
        
        # Encontrar mejor punto inicial usando Monte Carlo si está habilitado
        if use_monte_carlo and n_simulations > 0:
            try:
                # Realizar simulación de Monte Carlo
                returns, vols, weights, sharpes = self.monte_carlo_simulation(
                    min(n_simulations, 10000)  # Límite razonable
                )
                
                # Encontrar el mejor portafolio según el tipo de optimización
                if target_return is not None:
                    # Para optimización con retorno objetivo, buscar el de menor varianza
                    valid_idx = returns >= target_return
                    if np.any(valid_idx):
                        best_idx = np.argmin(vols[valid_idx])
                        x0 = weights[valid_idx][best_idx]
                    else:
                        x0 = np.ones(n_assets) / n_assets
                else:
                    # Para optimización general, usar el mejor ratio de Sharpe
                    best_idx = np.argmax(sharpes)
                    x0 = weights[best_idx]
                    
                # Mezclar con el último punto conocido si existe
                if hasattr(self, 'last_weights') and self.last_weights is not None:
                    x0 = 0.7 * x0 + 0.3 * self.last_weights
                    x0 /= np.sum(x0)  # Normalizar
                    
            except Exception as e:
                st.warning(f"Advertencia en simulación Monte Carlo: {str(e)}")
                x0 = np.ones(n_assets) / n_assets
        else:
            # Usar último punto conocido o inicialización uniforme
            if hasattr(self, 'last_weights') and self.last_weights is not None:
                x0 = self.last_weights
            else:
                x0 = np.ones(n_assets) / n_assets
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
    # Inicializar el gestor de portafolios
    port_mgr = manager(rics, notional, data)
    
    # Calcular matriz de covarianza y retornos medios
    cov_matrix, mean_returns = port_mgr.compute_covariance()
    
    # Si no hay datos suficientes, retornar error
    if cov_matrix is None or mean_returns is None or len(mean_returns) == 0:
        st.error("No hay suficientes datos para calcular la frontera eficiente")
        return None, {}
    
    # Calcular límites de retorno
    min_ret = np.min(mean_returns)
    max_ret = np.max(mean_returns)
    
    # Crear puntos para la frontera eficiente
    target_rets = np.linspace(min_ret, max_ret, 50)
    
    # Calcular la frontera eficiente
    frontier_vol = []
    frontier_ret = []
    
    for ret in target_rets:
        try:
            # Optimizar portafolio para el retorno objetivo
            port = port_mgr.compute_portfolio('markowitz', ret)
            if port is not None and hasattr(port, 'volatility_annual') and hasattr(port, 'return_annual'):
                frontier_vol.append(port.volatility_annual)
                frontier_ret.append(port.return_annual)
        except Exception as e:
            st.warning(f"No se pudo calcular el portafolio para retorno {ret:.2%}: {str(e)}")
            continue
    
    # Calcular portafolios especiales
    portfolios = {}
    
    # 1. Portafolio de mínima varianza
    try:
        min_var_port = port_mgr.compute_portfolio('min-variance-l1')
        if min_var_port is not None:
            portfolios['min-var'] = min_var_port
    except Exception as e:
        st.warning(f"No se pudo calcular el portafolio de mínima varianza: {str(e)}")
    
    # 2. Portafolio de máximo ratio de Sharpe
    try:
        sharpe_port = port_mgr.compute_portfolio('markowitz')
        if sharpe_port is not None:
            portfolios['max-sharpe'] = sharpe_port
    except Exception as e:
        st.warning(f"No se pudo calcular el portafolio de máximo Sharpe: {str(e)}")
    
    # 3. Portafolio con pesos iguales
    try:
        eq_port = port_mgr.compute_portfolio('equi-weight')
        if eq_port is not None:
            portfolios['equal-weight'] = eq_port
    except Exception as e:
        st.warning(f"No se pudo calcular el portafolio de pesos iguales: {str(e)}")
    
    # 4. Portafolio con retorno objetivo
    if target_return is not None and min_ret <= target_return <= max_ret:
        try:
            target_port = port_mgr.compute_portfolio('markowitz', target_return)
            if target_port is not None:
                portfolios['target'] = target_port
        except Exception as e:
            st.warning(f"No se pudo calcular el portafolio con retorno objetivo: {str(e)}")
    
    # Crear gráfico de la frontera eficiente
    fig = go.Figure()
    
    # Agregar frontera eficiente
    if len(frontier_vol) > 0 and len(frontier_ret) > 0:
        # Ordenar por volatilidad para una línea suave
        sorted_idx = np.argsort(frontier_vol)
        frontier_vol = np.array(frontier_vol)[sorted_idx]
        frontier_ret = np.array(frontier_ret)[sorted_idx]
        
        fig.add_trace(go.Scatter(
            x=frontier_vol,
            y=frontier_ret,
            mode='lines',
            name='Frontera Eficiente',
            line=dict(color='blue', width=2)
        ))
    
    # Agregar activos individuales
    for i, ric in enumerate(rics):
        fig.add_trace(go.Scatter(
            x=[np.sqrt(cov_matrix.iloc[i,i])],
            y=[mean_returns[i]],
            mode='markers',
            name=ric,
            marker=dict(size=10)
        ))
    
    # Agregar portafolios especiales
    for label, port in portfolios.items():
        fig.add_trace(go.Scatter(
            x=[port.volatility_annual],
            y=[port.return_annual],
            mode='markers',
            name=label.replace('-', ' ').title(),
            marker=dict(size=12, symbol='star')
        ))
    
    # Configurar diseño del gráfico
    fig.update_layout(
        title='Frontera Eficiente de Portafolios',
        xaxis_title='Volatilidad Anual',
        yaxis_title='Retorno Anual',
        showlegend=True,
        width=900,
        height=600,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig, portfolios

class PortfolioManager:
    def __init__(self, activos, token, fecha_desde=None, fecha_hasta=None):
        self.activos = activos
        self.token = token
        
        # Usar fechas de sesión si no se proporcionan
        if fecha_desde is None and 'fecha_desde' in st.session_state:
            self.fecha_desde = st.session_state.fecha_desde
        else:
            self.fecha_desde = fecha_desde or (date.today() - timedelta(days=365))
            
    class PortfolioManager:
        def __init__(self, activos, token, fecha_desde=None, fecha_hasta=None):
            self.activos = activos
            self.token = token
            self.fecha_desde = fecha_desde or date.today() - timedelta(days=365)
            self.fecha_hasta = fecha_hasta or date.today()
            
            self.data_loaded = False
            self.returns = None
            self.prices = None
            self.notional = 100000  # Valor nominal por defecto
            self.manager = None
            
            # Asegurarse de que las fechas sean objetos date
            if isinstance(self.fecha_desde, str):
                self.fecha_desde = datetime.strptime(self.fecha_desde, '%Y-%m-%d').date()
            if isinstance(self.fecha_hasta, str):
                self.fecha_hasta = datetime.strptime(self.fecha_hasta, '%Y-%m-%d').date()

        def load_data(self):
            try:
                # Validar fechas
                if self.fecha_desde >= self.fecha_hasta:
                    st.error("❌ La fecha de inicio debe ser anterior a la fecha de fin")
                    return False
                    
                # Limitar el rango de fechas a un máximo de 5 años para optimización
                max_days = 365 * 5
                if (self.fecha_hasta - self.fecha_desde).days > max_days:
                    self.fecha_desde = self.fecha_hasta - timedelta(days=max_days)
                    st.warning(f"⚠️ El rango de fechas se ha limitado a los últimos {max_days//365} años para optimización")
                
                # Convertir lista de activos a formato adecuado
                symbols = []
                markets = []
                
                for activo in self.activos:
                    if isinstance(activo, dict):
                        symbols.append(activo.get('simbolo', ''))
                        markets.append(activo.get('mercado', '').upper())
                    else:
                        symbols.append(activo)
                        markets.append('BCBA')  # Default market
                
                if not symbols:
                    st.error("❌ No se encontraron símbolos válidos para procesar")
                    return False
                
                st.info(f"📅 Período de análisis: {self.fecha_desde} a {self.fecha_hasta}")
                
                # Obtener datos históricos
                data_frames = {}
                success_count = 0
                
                with st.spinner("⏳ Obteniendo datos históricos..."):
                    progress_bar = st.progress(0)
                    total_symbols = len(symbols)
                    
                    for i, (simbolo, mercado) in enumerate(zip(symbols, markets)):
                        try:
                            progress = (i + 1) / total_symbols
                            progress_bar.progress(min(int(progress * 100), 100))
                            
                            df = obtener_serie_historica_iol(
                                self.token,
                                mercado,
                                simbolo,
                                self.fecha_desde.strftime('%Y-%m-%d'),
                                self.fecha_hasta.strftime('%Y-%m-%d')
                            )
                            
                            if df is not None and not df.empty:
                                # Usar la columna de último precio si está disponible
                                precio_columns = ['ultimoPrecio', 'ultimo_precio', 'precio', 'close', 'last']
                                precio_col = next((col for col in precio_columns if col in df.columns), None)
                                
                                if precio_col:
                                    df = df[['fecha', precio_col]].copy()
                                    df.columns = ['fecha', 'precio']  # Normalizar el nombre de la columna
                                    
                                    # Convertir fecha a datetime y asegurar que sea única
                                    df['fecha'] = pd.to_datetime(df['fecha']).dt.date
                                    
                                    # Filtrar por rango de fechas exacto
                                    df = df[(df['fecha'] >= self.fecha_desde) & 
                                          (df['fecha'] <= self.fecha_hasta)]
                                    
                                    if not df.empty:
                                        # Eliminar duplicados manteniendo el último valor
                                        df = df.drop_duplicates(subset=['fecha'], keep='last')
                                        
                                        # Ordenar por fecha
                                        df = df.sort_values('fecha')
                                        
                                        # Reindexar para asegurar fechas continuas
                                        date_range = pd.date_range(start=self.fecha_desde, end=self.fecha_hasta, freq='D')
                                        df = df.set_index('fecha').reindex(date_range.date).ffill()
                                        
                                        data_frames[simbolo] = df
                                        success_count += 1
                                    else:
                                        st.warning(f"⚠️ No hay datos en el rango de fechas para {simbolo}")
                                else:
                                    st.warning(f"⚠️ No se encontró columna de precio válida para {simbolo}")
                            else:
                                st.warning(f"⚠️ No se pudieron obtener datos para {simbolo} en {mercado}")
                        except Exception as e:
                            st.error(f"❌ Error procesando {simbolo}: {str(e)}")
                            continue
                    
                progress_bar.empty()
                
                if not data_frames:
                    st.error("❌ No se pudieron obtener datos históricos para ningún activo")
                    return False
                    
                st.success(f"✅ Datos obtenidos para {success_count} de {total_symbols} activos")
                
                # Verificar que tengamos suficientes datos para continuar
                if success_count < 2:  # Necesitamos al menos 2 activos para optimización
                    st.error("❌ Se requieren al menos 2 activos con datos para la optimización")
                    return False
                
                # Combinar todos los DataFrames
                df_precios = pd.concat(data_frames.values(), axis=1, keys=data_frames.keys())
                
                # Limpiar datos
                # Primero verificar si hay fechas duplicadas
                if not df_precios.index.is_unique:
                    st.warning("⚠️ Se encontraron fechas duplicadas en los datos")
                    # Eliminar duplicados manteniendo el último valor de cada fecha
                    df_precios = df_precios.groupby(df_precios.index).last()
                
                # Luego llenar y eliminar valores faltantes
                df_precios = df_precios.fillna(method='ffill')
                df_precios = df_precios.dropna()
                
                if df_precios.empty:
                    st.error("❌ No hay datos suficientes después del preprocesamiento")
                    return False
                
                # Calcular retornos
                self.returns = df_precios.pct_change().dropna()
                
                # Calcular estadísticas
                self.mean_returns = self.returns.mean()
                self.cov_matrix = self.returns.cov()
                self.data_loaded = True
                
                # Crear manager para optimización avanzada
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
                        weights = np.array([1/n_assets] * n_assets)
                    elif strategy == 'markowitz':
                        weights = markowitz_optimization(self.mean_returns, self.cov_matrix, target_return)
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
                    self.manager.rics, self.notional, target_return, include_min_variance, 
                    self.prices.to_dict('series')
                )
                return portfolios, returns, volatilities
            except Exception as e:
                return None, None, None            
        # Limitar el rango de fechas a un máximo de 5 años para optimización
        max_days = 365 * 5
        if (self.fecha_hasta - self.fecha_desde).days > max_days:
            self.fecha_desde = self.fecha_hasta - timedelta(days=max_days)
            st.warning(f"⚠️ El rango de fechas se ha limitado a los últimos {max_days//365} años para optimización")
{{ ... }}
        
    def load_data(self):
        # Convertir lista de activos a formato adecuado
        symbols = []
        markets = []
        
        for activo in self.activos:
            if isinstance(activo, dict):
                symbols.append(activo.get('simbolo', ''))
                markets.append(activo.get('mercado', '').upper())
            else:
                symbols.append(activo)
                markets.append('BCBA')  # Default market
        
        if not symbols:
            st.error("❌ No se encontraron símbolos válidos para procesar")
            return False
        
        st.info(f"📅 Período de análisis: {self.fecha_desde} a {self.fecha_hasta}")
        
        # Obtener datos históricos
        data_frames = {}
        success_count = 0
        
        with st.spinner("⏳ Obteniendo datos históricos..."):
            progress_bar = st.progress(0)
            total_symbols = len(symbols)
            
            for i, (simbolo, mercado) in enumerate(zip(symbols, markets)):
                try:
                    progress = (i + 1) / total_symbols
                    progress_bar.progress(min(int(progress * 100), 100))
                    
                    df = obtener_serie_historica_iol(
                        self.token,
                        mercado,
                        simbolo,
                        self.fecha_desde.strftime('%Y-%m-%d'),
                        self.fecha_hasta.strftime('%Y-%m-%d')
                    )
                    
                    if df is not None and not df.empty:
                        # Usar la columna de último precio si está disponible
                        precio_columns = ['ultimoPrecio', 'ultimo_precio', 'precio', 'close', 'last']
                        precio_col = next((col for col in precio_columns if col in df.columns), None)
                        
                        if precio_col:
                            df = df[['fecha', precio_col]].copy()
                            df.columns = ['fecha', 'precio']  # Normalizar el nombre de la columna
                            
                            # Convertir fecha a datetime y asegurar que sea única
                            df['fecha'] = pd.to_datetime(df['fecha']).dt.date
                            
                            # Filtrar por rango de fechas exacto
                            df = df[(df['fecha'] >= self.fecha_desde) & 
                                  (df['fecha'] <= self.fecha_hasta)]
                            
                            if not df.empty:
                                # Eliminar duplicados manteniendo el último valor
                                df = df.drop_duplicates(subset=['fecha'], keep='last')
                                
                                # Ordenar por fecha
                                df = df.sort_values('fecha')
                                
                                # Reindexar para asegurar fechas continuas
                                date_range = pd.date_range(start=self.fecha_desde, end=self.fecha_hasta, freq='D')
                                df = df.set_index('fecha').reindex(date_range.date).ffill()
                                
                                data_frames[simbolo] = df
                                success_count += 1
                            else:
                                st.warning(f"⚠️ No hay datos en el rango de fechas para {simbolo}")
                        else:
                            st.warning(f"⚠️ No se encontró columna de precio válida para {simbolo}")
                    else:
                        st.warning(f"⚠️ No se pudieron obtener datos para {simbolo} en {mercado}")
                except Exception as e:
                    st.error(f"❌ Error procesando {simbolo}: {str(e)}")
                    continue
                
            progress_bar.empty()
            
            if not data_frames:
                st.error("❌ No se pudieron obtener datos históricos para ningún activo")
                return False
                
            st.success(f"✅ Datos obtenidos para {success_count} de {total_symbols} activos")
            
            # Verificar que tengamos suficientes datos para continuar
            if success_count < 2:  # Necesitamos al menos 2 activos para optimización
                st.error("❌ Se requieren al menos 2 activos con datos para la optimización")
                return False
            
            # Combinar todos los DataFrames
            df_precios = pd.concat(data_frames.values(), axis=1, keys=data_frames.keys())
            
            # Limpiar datos
            # Primero verificar si hay fechas duplicadas
            if not df_precios.index.is_unique:
                st.warning("⚠️ Se encontraron fechas duplicadas en los datos")
                # Eliminar duplicados manteniendo el último valor de cada fecha
                df_precios = df_precios.groupby(df_precios.index).last()
            
            # Luego llenar y eliminar valores faltantes
            df_precios = df_precios.fillna(method='ffill')
            df_precios = df_precios.dropna()
            
            if df_precios.empty:
                st.error("❌ No hay datos suficientes después del preprocesamiento")
                return False
            
            # Calcular retornos
            self.returns = df_precios.pct_change().dropna()
            
            # Calcular estadísticas
            self.mean_returns = self.returns.mean()
            self.cov_matrix = self.returns.cov()
            self.data_loaded = True
            
            # Crear manager para optimización avanzada
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
                    weights = np.array([1/n_assets] * n_assets)
                
                if strategy == 'markowitz':
                    weights = markowitz_optimization(self.mean_returns, self.cov_matrix, target_return)
                
                portfolio_result = PortfolioResult(weights, self.returns, self.mean_returns, self.cov_matrix)
                
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
                        try:
                            metricas = portfolio_result.get_metrics_dict()
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("Retorno Anual", f"{metricas.get('Annual Return', 0):.2%}")
                                st.metric("Volatilidad Anual", f"{metricas.get('Annual Volatility', 0):.2%}")
                                st.metric("Ratio de Sharpe", f"{metricas.get('Sharpe Ratio', 0):.4f}")
                                st.metric("VaR 95% (1 día)", f"{metricas.get('VaR 95%', 0):.4f}")
                            with col_b:
                                st.metric("Skewness", f"{metricas.get('Skewness', 0):.4f}")
                                st.metric("Kurtosis", f"{metricas.get('Kurtosis', 0):.4f}")
                                st.metric("JB Statistic", f"{metricas.get('JB Statistic', 0):.4f}")
                                normalidad = "✅ Normal" if metricas.get('Is Normal', False) else "❌ No Normal"
                                st.metric("Normalidad", normalidad)
                        except Exception as e:
                            st.error(f"❌ Error al obtener métricas: {str(e)}")
                    
                    # Gráfico de distribución de retornos
                    if hasattr(portfolio_result, 'returns') and portfolio_result.returns is not None:
                        st.markdown("#### 📊 Distribución de Retornos del Portafolio Optimizado")
                        try:
                            fig = portfolio_result.plot_histogram_streamlit()
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error al generar el gráfico de distribución: {str(e)}")
                    
                    # Gráfico de pesos
                    if (hasattr(portfolio_result, 'weights') and portfolio_result.weights is not None and 
                        hasattr(portfolio_result, 'dataframe_allocation') and portfolio_result.dataframe_allocation is not None):
                        st.markdown("#### 🥧 Distribución de Pesos")
                        try:
                            fig_pie = go.Figure(data=[go.Pie(
                                labels=portfolio_result.dataframe_allocation['rics'],
                                values=portfolio_result.weights,
                                textinfo='label+percent',
                                hole=0.4,
                                marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3'])
                            )])
                            fig_pie.update_layout(
                                title="Distribución Optimizada de Activos",
                                template='plotly_white'
                            )
                            st.plotly_chart(fig_pie, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error al generar el gráfico de pesos: {str(e)}")
                else:
                    st.error("❌ No se obtuvieron resultados de la optimización")
            except Exception as e:
                st.error(f"❌ Error durante la optimización: {str(e)}")

            # Mostrar frontera eficiente si está habilitado
            if show_frontier and ejecutar_optimizacion:
                with st.spinner("Calculando frontera eficiente..."):
                    try:
                        # Validar fechas nuevamente
                        if fecha_desde >= fecha_hasta:
                            st.error("❌ La fecha de inicio debe ser anterior a la fecha de fin")
                            return
                        
                        # Validar que hay suficientes días de datos
                        dias_analisis = (fecha_hasta - fecha_desde).days
                        if dias_analisis < 30:  # Mínimo 30 días para frontera eficiente
                            st.error("❌ El período de análisis es demasiado corto para calcular la frontera eficiente. Seleccione un rango mayor.")
                            return
                        
                        with st.status("🔍 Calculando frontera eficiente..."):
                            st.write("Inicializando gestor de portafolio...")
                            manager_inst = PortfolioManager(activos_para_optimizacion, token_acceso, fecha_desde, fecha_hasta)
                            
                            st.write(f"Cargando datos históricos desde {fecha_desde} hasta {fecha_hasta}...")
                            if not manager_inst.load_data():
                                st.error("❌ Error al cargar los datos históricos. Verifique la conexión y los parámetros.")
                                return
                            
                            st.write("Calculando la frontera eficiente... (Esto puede tomar unos momentos)")
                            
                            try:
                                portfolios, returns, volatilities, sharpe_ratios = manager_inst.compute_efficient_frontier(
                                    target_return=target_return, 
                                    include_min_variance=True,
                                    n_points=50,  # Número de puntos en la frontera
                                    risk_free_rate=risk_free_rate  # Usar la tasa libre de riesgo
                                )
                            except Exception as e:
                                st.error(f"❌ Error al calcular la frontera eficiente: {str(e)}")
                                st.error("⚠️ Intente ajustar el rango de fechas o los activos seleccionados")
                                return
                            
                        if portfolios and returns and volatilities:
                            st.success("✅ Frontera eficiente calculada")
                            
                            # Crear gráfico de frontera eficiente
                            fig = go.Figure()
                            
                            # Línea de frontera eficiente
                            fig.add_trace(go.Scatter(
                                x=volatilities, 
                                y=returns,
                                mode='lines+markers',
                                name='Frontera Eficiente',
                                line=dict(color='#0d6efd', width=3),
                                marker=dict(size=6, color=sharpe_ratios, colorscale='Viridis', showscale=True, colorbar=dict(title='Ratio de Sharpe'))
                            ))
                            
                            # Agregar línea del activo libre de riesgo
                            max_volatility = max(volatilities) * 1.1
                            max_return = max(returns) * 1.1
                            
                            # Línea del activo libre de riesgo al portafolio de mercado
                            fig.add_trace(go.Scatter(
                                x=[0, max_volatility],
                                y=[risk_free_rate, risk_free_rate + (max_return - risk_free_rate) / max_volatility * max_volatility],
                                mode='lines',
                                name='Línea de Mercado de Capitales',
                                line=dict(color='#FF6B6B', width=2, dash='dash')
                            ))
                            
                            # Portafolios especiales
                            colors = ['#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#A569BD']
                            labels = ['Min Var', 'Max Sharpe', 'Pesos Iguales', 'Solo Largos', 'Markowitz', 'Mercado']
                            
                            for i, (label, portfolio) in enumerate(portfolios.items()):
                                if portfolio is not None and i < len(colors):
                                    fig.add_trace(go.Scatter(
                                        x=[portfolio.volatility_annual], 
                                        y=[portfolio.return_annual],
                                        mode='markers+text',
                                        name=labels[i],
                                        text=[labels[i]],
                                        textposition='top center',
                                        marker=dict(
                                            size=14,
                                            color=colors[i],
                                            line=dict(width=2, color='DarkSlateGrey')
                                        )
                                    ))
                            
                            fig.update_layout(
                                title=dict(
                                    text='Frontera Eficiente y Línea de Mercado de Capitales',
                                    x=0.5,
                                    xanchor='center',
                                    font=dict(size=16)
                                ),
                                xaxis_title='Volatilidad Anual',
                                yaxis_title='Retorno Anual',
                                showlegend=True,
                                template='plotly_white',
                                height=600,
                                margin=dict(l=50, r=50, t=80, b=50),
                                legend=dict(
                                    orientation='h',
                                    yanchor='bottom',
                                    y=1.02,
                                    xanchor='right',
                                    x=1
                                ),
                                hovermode='closest',
                                xaxis=dict(
                                    range=[0, max_volatility * 1.05],
                                    showgrid=True,
                                    gridwidth=1,
                                    gridcolor='#f0f0f0'
                                ),
                                yaxis=dict(
                                    range=[min(min(returns) * 0.9, risk_free_rate * 0.9), max_return * 1.05],
                                    showgrid=True,
                                    gridwidth=1,
                                    gridcolor='#f0f0f0',
                                    tickformat='.0%'
                                )
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"❌ Error durante el cálculo de la frontera eficiente: {str(e)}")
        except Exception as e:
            st.error(f"❌ Error durante la optimización: {str(e)}")

# --- Historical Data Methods ---
def obtener_serie_historica_iol(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="SinAjustar"):
    """
    Obtiene series históricas desde la API de IOL
{{ ... }}
    
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
def calcular_metricas_portafolio(portafolio, valor_total):
    """
    Calcula métricas clave de desempeño para un portafolio de inversión.
    
    Args:
        portafolio (dict): Diccionario con los activos y sus cantidades
        valor_total (float): Valor total del portafolio
        
    Returns:
        dict: Diccionario con las métricas calculadas
    """
    if not isinstance(portafolio, dict):
        return {}

    if valor_total == 0:
        return {
            'concentracion': 0,
            'std_dev_activo': 0,
            'retorno_esperado_anual': 0,
            'pl_esperado_min': 0,
            'pl_esperado_max': 0,
            'probabilidades': {'perdida': 0, 'ganancia': 0, 'perdida_mayor_10': 0, 'ganancia_mayor_10': 0},
            'riesgo_anual': 0
        }

    # 1. Calcular concentración del portafolio
    concentracion = 0
    for activo in portafolio.values():
        concentracion += (activo.get('Valuación', 0) / valor_total) ** 2
    
    # 2. Calcular volatilidad de los activos
    std_dev_activo = 0
    for activo in portafolio.values():
        std_dev_activo += activo.get('Valuación', 0) * activo.get('volatilidad', 0)
    
    # 3. Calcular retorno esperado
    retorno_esperado_anual = 0
    for activo in portafolio.values():
        retorno_esperado_anual += activo.get('Valuación', 0) * activo.get('retorno_esperado', 0)
    
    # 4. Calcular escenarios de pérdida y ganancia
    pl_esperado_min = 0
    pl_esperado_max = 0
    for activo in portafolio.values():
        pl_esperado_min += activo.get('Valuación', 0) * activo.get('pl_min', 0)
        pl_esperado_max += activo.get('Valuación', 0) * activo.get('pl_max', 0)
    
    # 5. Calcular probabilidades de pérdida y ganancia
    probabilidades = {
        'perdida': 0,
        'ganancia': 0,
        'perdida_mayor_10': 0,
        'ganancia_mayor_10': 0
    }
    for activo in portafolio.values():
        probabilidades['perdida'] += activo.get('Valuación', 0) * activo.get('probabilidad_perdida', 0)
        probabilidades['ganancia'] += activo.get('Valuación', 0) * activo.get('probabilidad_ganancia', 0)
        probabilidades['perdida_mayor_10'] += activo.get('Valuación', 0) * activo.get('probabilidad_perdida_mayor_10', 0)
        probabilidades['ganancia_mayor_10'] += activo.get('Valuación', 0) * activo.get('probabilidad_ganancia_mayor_10', 0)
    
    # 6. Calcular riesgo anual
    riesgo_anual = 0
    for activo in portafolio.values():
        riesgo_anual += activo.get('Valuación', 0) * activo.get('riesgo', 0)
    
    return {
        'concentracion': concentracion,
        'std_dev_activo': std_dev_activo,
        'retorno_esperado_anual': retorno_esperado_anual,
        'pl_esperado_min': pl_esperado_min,
        'pl_esperado_max': pl_esperado_max,
        'probabilidades': probabilidades,
        'riesgo_anual': riesgo_anual
    }

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
        # Convert list to dictionary with symbols as keys
        portafolio_dict = {row['Símbolo']: row for row in datos_activos}
        metricas = calcular_metricas_portafolio(portafolio_dict, valor_total)
        
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
            cols[1].metric("Escenario Optimista", f"${metricas['pl_esperado_max']:,.0f}")
            cols[2].metric("Escenario Pesimista", f"${metricas['pl_esperado_min']:,.0f}")
            
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
    
    # Obtener fechas de la sesión o usar valores por defecto
    if 'fecha_desde' not in st.session_state:
        st.session_state.fecha_desde = (date.today() - timedelta(days=365)).strftime('%Y-%m-%d')
    if 'fecha_hasta' not in st.session_state:
        st.session_state.fecha_hasta = date.today().strftime('%Y-%m-%d')
    
    # Mostrar selector de fechas en el sidebar
    with st.sidebar.expander("📅 Configuración de Fechas", expanded=True):
        fecha_desde = st.date_input(
            "Fecha de inicio",
            value=datetime.strptime(st.session_state.fecha_desde, '%Y-%m-%d').date(),
            min_value=date(2000, 1, 1),
            max_value=date.today()
        )
        
        fecha_hasta = st.date_input(
            "Fecha de fin",
            value=datetime.strptime(st.session_state.fecha_hasta, '%Y-%m-%d').date(),
            min_value=date(2000, 1, 1),
            max_value=date.today()
        )
        
        # Validar fechas
        if fecha_desde >= fecha_hasta:
            st.error("❌ La fecha de inicio debe ser anterior a la fecha de fin")
            return
            
        # Actualizar fechas en la sesión
        st.session_state.fecha_desde = fecha_desde.strftime('%Y-%m-%d')
        st.session_state.fecha_hasta = fecha_hasta.strftime('%Y-%m-%d')
    
    with st.spinner("Obteniendo portafolio..."):
        portafolio = obtener_portafolio(token_acceso, id_cliente)
    
    if not portafolio:
        st.warning("No se pudo obtener el portafolio del cliente")
        return
    
    activos_raw = portafolio.get('activos', [])
    if not activos_raw:
        st.warning("El portafolio está vacío")
        return
    
    # Mostrar resumen de activos
    st.markdown("### 📊 Activos en el Portafolio")
    activos_data = []
    for activo in activos_raw:
        titulo = activo.get('titulo', {})
        activos_data.append({
            'Símbolo': titulo.get('simbolo', 'N/A'),
            'Mercado': titulo.get('mercado', 'N/A'),
            'Descripción': titulo.get('descripcion', 'N/A'),
            'Cantidad': activo.get('cantidad', 0),
            'Último Precio': f"${activo.get('ultimoPrecio', 0):,.2f}",
            'Moneda': activo.get('moneda', 'ARS')
        })
    
    if activos_data:
        st.dataframe(pd.DataFrame(activos_data), use_container_width=True)
    
    # Extraer símbolos y mercados para optimización
    activos_para_optimizacion = []
    for activo in activos_raw:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo')
        mercado = titulo.get('mercado')
        if simbolo and mercado:
            activos_para_optimizacion.append({'simbolo': simbolo, 'mercado': mercado})
    
    if not activos_para_optimizacion:
        st.warning("No se encontraron activos con información de mercado válida para optimizar.")
        return
    
    st.info(f"🔍 Analizando {len(activos_para_optimizacion)} activos desde {fecha_desde} hasta {fecha_hasta}")
    
    # Mostrar advertencia si hay pocos datos
    dias_analisis = (fecha_hasta - fecha_desde).days
    if dias_analisis < 30:
        st.warning("⚠️ El período de análisis es muy corto. Se recomienda seleccionar al menos 3 meses para obtener resultados más confiables.")
    elif dias_analisis > 365 * 5:  # Más de 5 años
        st.info("ℹ️ El período de análisis es extenso. La optimización podría llevar más tiempo en completarse.")
    
    # Mostrar opciones de optimización
    st.sidebar.markdown("### 🔧 Opciones de Optimización")
    
    # Fila 1: Estrategia y Tasa Libre de Riesgo
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        estrategia = st.selectbox(
            "Estrategia de Optimización",
            ["min-var", "max-sharpe", "equi-weight", "long-only", "markowitz", "risk-parity"],
            index=1
        )
    
    with col2:
        # Tasa libre de riesgo con valor por defecto para Argentina
        risk_free_rate = st.number_input(
            "Tasa Libre de Riesgo (%)", 
            min_value=0.0, 
            max_value=100.0, 
            value=40.0,
            step=0.1,
            format="%.2f"
        ) / 100  # Convertir a decimal
    
    # Fila 2: Simulaciones y opciones avanzadas
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        # Número de simulaciones Monte Carlo
        n_simulations = st.number_input(
            "Número de Simulaciones", 
            min_value=100, 
            max_value=10000, 
            value=1000,
            step=100,
            help="Número de simulaciones para el análisis de Monte Carlo"
        )
    
    with col2:
        # Opción para usar Monte Carlo
        use_monte_carlo = st.checkbox(
            "Usar Monte Carlo", 
            value=True,
            help="Usar simulación de Monte Carlo para inicialización"
        )
    
    # Fila 2: Opciones específicas de estrategia
    if estrategia == "markowitz":
        target_return = st.sidebar.number_input(
            "Retorno Anual Objetivo (%)", 
            min_value=0.0, 
            max_value=100.0, 
            value=40.0,
            step=0.1,
            format="%.2f"
        ) / 100  # Convertir a decimal
    else:
        target_return = None
    
    # Mostrar opción de aversión al riesgo para mean-variance
    if estrategia == "mean-variance":
        risk_aversion = st.sidebar.slider(
            "Aversión al Riesgo", 
            min_value=0.1, 
            max_value=10.0, 
            value=1.0,
            step=0.1,
            help="Mayor valor = Menor tolerancia al riesgo"
        )
    else:
        risk_aversion = 1.0
    
    # Opciones avanzadas en un expander
    with st.sidebar.expander("⚙️ Otras Opciones"):
        # Mostrar opciones adicionales aquí si es necesario
        st.info("Ajusta el número de simulaciones y la opción de Monte Carlo en la sección principal.")
    
    # Mostrar opción de frontera eficiente
    show_frontier = st.sidebar.checkbox(
        "Mostrar Frontera Eficiente", 
        value=True,
        help="Muestra la frontera eficiente y portafolios especiales"
    )
    
    # Botón para ejecutar optimización
    ejecutar_optimizacion = st.sidebar.button("🚀 Ejecutar Optimización", type="primary")
    
    # Validar fechas al ejecutar la optimización
    if ejecutar_optimizacion:
        if fecha_desde >= fecha_hasta:
            st.error("❌ La fecha de inicio debe ser anterior a la fecha de fin")
            st.stop()
        
        # Validar que hay suficientes días de datos
        dias_analisis = (fecha_hasta - fecha_desde).days
        if dias_analisis < 30:  # Mínimo 30 días para optimización
            st.error("❌ El período de análisis es demasiado corto. Seleccione un rango mayor.")
            st.stop()
        
        # Limitar el rango de fechas a un máximo de 5 años para optimización
        max_dias = 365 * 5
        if dias_analisis > max_dias:
            st.warning(f"⚠️ El rango de fechas se ha limitado a los últimos {max_dias//365} años para optimización")
            fecha_desde = fecha_hasta - timedelta(days=max_dias)
        
        # Inicializar el gestor de portafolio con las fechas seleccionadas
        with st.spinner("Cargando datos y optimizando portafolio..."):
            manager_inst = PortfolioManager(activos_para_optimizacion, token_acceso, fecha_desde, fecha_hasta)
            
            # Cargar datos
            if not manager_inst.load_data():
                st.error("No se pudieron cargar los datos históricos. Verifique la conexión y los parámetros.")
                st.stop()
            
            # Calcular portafolio óptimo
            try:
                portfolio_result = manager_inst.compute_portfolio(
                    strategy=estrategia,
                    target_return=target_return,
                    risk_aversion=risk_aversion,
                    n_simulations=n_simulations,
                    use_monte_carlo=use_monte_carlo
                )
                
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
                        try:
                            metricas = portfolio_result.get_metrics_dict()
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("Retorno Anual", f"{metricas.get('Annual Return', 0):.2%}")
                                st.metric("Volatilidad Anual", f"{metricas.get('Annual Volatility', 0):.2%}")
                                st.metric("Ratio de Sharpe", f"{metricas.get('Sharpe Ratio', 0):.4f}")
                                st.metric("VaR 95% (1 día)", f"{metricas.get('VaR 95%', 0):.4f}")
                            with col_b:
                                st.metric("Skewness", f"{metricas.get('Skewness', 0):.4f}")
                                st.metric("Kurtosis", f"{metricas.get('Kurtosis', 0):.4f}")
                                st.metric("JB Statistic", f"{metricas.get('JB Statistic', 0):.4f}")
                                normalidad = "✅ Normal" if metricas.get('Is Normal', False) else "❌ No Normal"
                                st.metric("Normalidad", normalidad)
                        except Exception as e:
                            st.error(f"Error al obtener métricas: {str(e)}")
                    
                    # Gráfico de distribución de retornos
                    if hasattr(portfolio_result, 'returns') and portfolio_result.returns is not None:
                        st.markdown("#### 📊 Distribución de Retornos del Portafolio Optimizado")
                        try:
                            fig = portfolio_result.plot_histogram_streamlit()
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error al generar el gráfico de distribución: {str(e)}")
                    
                    # Gráfico de pesos
                    if (hasattr(portfolio_result, 'weights') and portfolio_result.weights is not None and 
                        hasattr(portfolio_result, 'dataframe_allocation') and portfolio_result.dataframe_allocation is not None):
                        st.markdown("#### 🥧 Distribución de Pesos")
                        try:
                            fig_pie = go.Figure(data=[go.Pie(
                                labels=portfolio_result.dataframe_allocation['rics'],
                                values=portfolio_result.weights,
                                textinfo='label+percent',
                                hole=0.4,
                                marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3'])
                            )])
                            fig_pie.update_layout(
                                title="Distribución Optimizada de Activos",
                                template='plotly_white'
                            )
                            st.plotly_chart(fig_pie, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error al generar el gráfico de pesos: {str(e)}")
                else:
                    st.error("❌ No se obtuvieron resultados de la optimización")
            except Exception as e:
                st.error(f"❌ Error durante la optimización: {str(e)}")
                return
                            })
                    
                    if comparison_data:
                        df_comparison = pd.DataFrame(comparison_data)
                        # Resaltar la mejor estrategia para cada métrica
                        def highlight_max(s):
                            is_max = s == s.max()
                            return ['background-color: #e6f3ff' if v else '' for v in is_max]
                        
                        try:
                            # Convertir las columnas porcentuales a numéricas para el resaltado
                            df_numeric = df_comparison.copy()
                            for col in ['Retorno Anual', 'Volatilidad Anual']:
                                df_numeric[col] = df_numeric[col].str.rstrip('%').astype('float') / 100.0
                            
                            # Aplicar formato condicional
                            styled_df = df_comparison.style\
                                .apply(highlight_max, subset=['Retorno Anual', f'Sharpe Ratio (Rf={risk_free_rate*100:.1f}%)'])
                            
                            # Mostrar la tabla con formato
                            st.dataframe(styled_df, use_container_width=True)
                        except Exception as e:
                            st.warning(f"No se pudo aplicar formato a la tabla: {str(e)}")
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

if __name__ == "__main__":
    main()
