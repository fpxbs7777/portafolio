import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
from arch import arch_model
from scipy.stats import norm
import matplotlib.pyplot as plt
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta, date
import scipy.optimize as op
from scipy import stats
import random
import warnings
import streamlit.components.v1 as components

warnings.filterwarnings('ignore')

# Configuración de la página con tema oscuro profesional
st.set_page_config(
    page_title="IOL Portfolio Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para tema oscuro
st.markdown("""
<style>
    /* Estilos generales dark theme */
    .stApp, 
    .stApp > div[data-testid="stAppViewContainer"],
    .stApp > div[data-testid="stAppViewContainer"] > div {
        background-color: #0f172a !important;
        color: #f8f9fa !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Asegurar que todo el texto sea claro */
    body, p, div, span, h1, h2, h3, h4, h5, h6, label, input, select, textarea, button,
    .stSelectbox div[data-baseweb="select"] div,
    .stDateInput div[data-baseweb="input"] input,
    .stTextInput div[data-baseweb="input"] input,
    .stNumberInput div[data-baseweb="input"] input,
    .stTextArea div[data-baseweb="textarea"] textarea,
    .stAlert,
    .stAlert p,
    .stAlert div,
    .stAlert span,
    .stTooltip,
    .stTooltip p,
    .stTooltip div,
    .stTooltip span,
    .stMarkdown,
    .stMarkdown p,
    .stMarkdown div,
    .stMarkdown span,
    a,
    a:visited,
    a:hover,
    .st-bb,
    .st-bj,
    .st-bk,
    .st-bn,
    .st-bo,
    .st-bp,
    .st-bq,
    .st-br,
    .st-bs,
    .st-bt {
        color: #f8f9fa !important;
    }
    
    /* Asegurar que los enlaces sean visibles */
    a {
        color: #4CAF50 !important;
        text-decoration: none;
    }
    
    a:hover {
        color: #45a049 !important;
        text-decoration: underline;
    }
    
    /* Mejorar la visibilidad de los placeholders */
    ::placeholder {
        color: #94a3b8 !important;
        opacity: 1;
    }
    
    /* Mejorar la visibilidad de los tooltips */
    .stTooltip {
        background-color: #1e293b !important;
        border: 1px solid #4CAF50 !important;
        color: #f8f9fa !important;
    }
    
    /* Estilos para menús desplegables y listas */
    /* Select principal */
    div[data-baseweb="select"],
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] input,
    div[data-baseweb="select"] div[role="button"],
    div[data-baseweb="select"] div[role="listbox"],
    div[data-baseweb="select"] div[role="combobox"],
    div[data-baseweb="select"] div[data-baseweb="select"] {
        background-color: #1e293b !important;
        color: #f8f9fa !important;
        border-color: #4CAF50 !important;
    }
    
    /* Opciones del menú desplegable */
    div[role="listbox"],
    div[role="listbox"] ul,
    div[role="listbox"] li,
    div[role="option"],
    div[role="option"] > div,
    div[role="option"] > span,
    div[role="listbox"] > div,
    div[role="listbox"] > div > div,
    div[data-baseweb*="popover"] *,
    div[data-baseweb*="popover"] div,
    div[data-baseweb*="popover"] span,
    div[data-baseweb*="popover"] li,
    div[data-baseweb*="popover"] ul,
    div[data-baseweb*="popover"] p,
    div[data-baseweb*="popover"] a,
    div[data-baseweb*="popover"] button,
    div[data-baseweb*="popover"] input,
    div[data-baseweb*="popover"] select,
    div[data-baseweb*="popover"] option {
        background-color: #1e293b !important;
        color: #f8f9fa !important;
    }
    
    /* Asegurar que el texto dentro de los popovers sea visible */
    div[data-baseweb*="popover"] {
        background-color: #1e293b !important;
        border: 1px solid #4CAF50 !important;
    }
    
    /* Asegurar que el texto de las opciones sea visible */
    div[role="option"] *,
    div[role="option"] span,
    div[role="option"] div {
        color: #f8f9fa !important;
    }
    
    /* Efecto hover en opciones */
    div[role="option"]:hover,
    div[role="option"]:hover > div,
    div[role="option"]:hover > span,
    div[role="listbox"] > div:hover,
    div[role="listbox"] > div > div:hover {
        background-color: #2d3748 !important;
        color: #ffffff !important;
    }
    
    /* Opción seleccionada */
    div[aria-selected="true"],
    div[aria-selected="true"] > div,
    div[aria-selected="true"] > span {
        background-color: #4CAF50 !important;
        color: #ffffff !important;
    }
    
    /* Estilos para los elementos de entrada */
    input[type="text"],
    input[type="number"],
    input[type="date"],
    input[type="time"],
    input[type="password"],
    input[type="email"],
    input[type="search"],
    select,
    textarea {
        background-color: #1e293b !important;
        color: #f8f9fa !important;
        border-color: #4CAF50 !important;
    }
    
    /* Placeholder */
    input::placeholder,
    textarea::placeholder {
        color: #94a3b8 !important;
        opacity: 1;
    }
    
    /* Estilos para las listas de selección múltiple */
    .stMultiSelect [role="button"],
    .stMultiSelect [role="button"]:hover,
    .stMultiSelect [role="button"]:focus {
        background-color: #1e293b !important;
        color: #f8f9fa !important;
        border-color: #4CAF50 !important;
    }
    
    .stMultiSelect [role="option"] {
        background-color: #1e293b !important;
        color: #f8f9fa !important;
    }
    
    .stMultiSelect [role="option"]:hover {
        background-color: #2d3748 !important;
    }
    
    /* Mejorar la visibilidad de los mensajes */
    .stAlert {
        background-color: rgba(30, 41, 59, 0.9) !important;
        border-left: 4px solid #4CAF50 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    /* Ajustes para gráficos */
    .stPlotlyChart {
        background-color: #1e293b !important;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Asegurar que los checkboxes y radio buttons sean visibles */
    .stCheckbox > label,
    .stRadio > label,
    .stCheckbox > div,
    .stRadio > div {
        color: #f8f9fa !important;
    }
    
    /* Estilos para las pestañas activas */
    [data-baseweb="tab"] {
        color: #f8f9fa !important;
    }
    
    [data-baseweb="tab"]:hover {
        background-color: #2d3748 !important;
    }
    
    /* Estilos para los mensajes de error */
    .stAlert.stAlert-warning {
        border-left: 4px solid #ff9800 !important;
    }
    
    .stAlert.stAlert-error {
        border-left: 4px solid #f44336 !important;
    }
    
    .stAlert.stAlert-success {
        border-left: 4px solid #4CAF50 !important;
    }
    
    .stAlert.stAlert-info {
        border-left: 4px solid #2196F3 !important;
    }
    
    /* Mejora de tarjetas y métricas */
    .stMetric, 
    .stMetric > div > div,
    .stMetric > div > div > div {
        background-color: #1e293b !important;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        border-left: 4px solid #4CAF50;
        color: #f8f9fa !important;
    }
    
    .stMetric > div > div {
        color: #94a3b8 !important;
    }
    
    /* Mejora de pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
        background-color: #0f172a;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        padding: 0 20px;
        background-color: #1e293b;
        border-radius: 8px !important;
        font-weight: 500;
        color: #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50 !important;
        color: white !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #334155 !important;
    }
    
    /* Mejora de inputs */
    .stTextInput, .stNumberInput, .stDateInput, .stSelectbox, .stTextArea {
        background-color: #1e293b;
        border-radius: 8px;
        color: #e2e8f0;
        border: 1px solid #334155;
    }
    
    /* Estilos para las etiquetas de los inputs */
    .stTextInput > label, .stNumberInput > label, 
    .stDateInput > label, .stSelectbox > label,
    .stTextArea > label {
        color: #94a3b8 !important;
    }
    
    /* Botones */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        background-color: #4CAF50;
        color: white;
        border: none;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background-color: #45a049;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    /* Barra lateral */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a, #0c1424);
        color: white;
    }
    
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stNumberInput label {
        color: #94a3b8 !important;
    }
    
    /* Títulos */
    h1, h2, h3, h4, h5, h6 {
        color: #4CAF50;
        font-weight: 600;
    }
    
    /* Tablas */
    .dataframe {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    .dataframe th {
        background-color: #334155 !important;
        color: #e2e8f0 !important;
    }
    
    .dataframe tr:nth-child(even) {
        background-color: #1a2233 !important;
    }
    
    .dataframe tr:hover {
        background-color: #2c3a58 !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #4CAF50;
    }
    
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0f172a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #4CAF50;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #45a049;
    }
    
    /* Efectos hover para tarjetas */
    div[data-testid="stExpander"] {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stExpander"]:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transform: translateY(-2px);
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

def obtener_serie_historica_fci(token_portador, simbolo, fecha_desde, fecha_hasta):
    """
    Obtiene la serie histórica de un fondo común de inversión
    """
    url = f'https://api.invertironline.com/api/v2/Titulos/FCI/{simbolo}/cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/ajustada'
    headers = {
        'Authorization': f'Bearer {token_portador}',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        # Procesar la respuesta para convertirla al formato esperado
        if isinstance(data, list):
            fechas = []
            precios = []
            for item in data:
                if 'fecha' in item and 'valorCuota' in item:
                    fechas.append(pd.to_datetime(item['fecha']))
                    precios.append(float(item['valorCuota']))
            if fechas and precios:
                return pd.DataFrame({'fecha': fechas, 'precio': precios}).sort_values('fecha')
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error al obtener serie histórica del FCI {simbolo}: {str(e)}")
        return None

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
            marker_color='#1f77b4'
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
    port_mgr = manager(
        rics,
        notional,
        data
    )
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
        self.volumes = None
        self.notional = 100000  # Valor nominal por defecto
        self.manager = None
        self.garch_models = {}
        self.monte_carlo_results = {}
        self.volatility_forecasts = {}
    
    def analyze_volatility(self, symbol, returns, volumes=None, n_simulations=1000, n_days=30):
        """
        Analiza la volatilidad usando GARCH y simulación de Monte Carlo
        
        Args:
            symbol (str): Símbolo del activo
            returns (pd.Series): Serie de retornos
            volumes (pd.Series, optional): Serie de volúmenes
            n_simulations (int): Número de simulaciones Monte Carlo (default: 1000)
            n_days (int): Número de días a pronosticar (default: 30)
            
        Returns:
            dict: Resultados del análisis de volatilidad
        """
        try:
            # Asegurarse de que no haya valores NaN
            returns = returns.dropna()
            if len(returns) < 30:  # Mínimo de datos para un análisis significativo
                st.warning(f"No hay suficientes datos para analizar la volatilidad de {symbol}")
                return None
                
            # 1. Ajustar modelo GARCH(1,1)
            garch_model = arch_model(
                returns * 100,  # Multiplicar por 100 para mejorar la convergencia
                vol='Garch',
                p=1,
                q=1,
                dist='normal'
            )
            
            # Ajustar el modelo con supresión de salida
            with st.spinner(f"Ajustando modelo GARCH para {symbol}..."):
                garch_fit = garch_model.fit(disp='off')
                
            self.garch_models[symbol] = garch_fit
            
            # 2. Pronóstico de volatilidad
            forecast = garch_fit.forecast(horizon=5)
            forecast_volatility = np.sqrt(forecast.variance.iloc[-1] / 100)  # Deshacer el escalado
            
            # 3. Simulación de Monte Carlo
            last_price = returns.iloc[-1] if hasattr(returns, 'iloc') else 1.0
            last_vol = np.sqrt(garch_fit.conditional_volatility.iloc[-1] / 100)
            
            # Inicializar matrices para almacenar resultados
            price_paths = np.zeros((n_simulations, n_days))
            returns_paths = np.zeros((n_simulations, n_days))
            
            # Mostrar barra de progreso para simulaciones
            progress_bar = st.progress(0)
            progress_text = st.empty()
            
            # Simular trayectorias de precios
            for i in range(n_simulations):
                # Actualizar barra de progreso
                if i % 100 == 0:
                    progress = (i + 1) / n_simulations
                    progress_bar.progress(progress)
                    progress_text.text(f"Simulando trayectorias: {i+1}/{n_simulations}")
                
                # Generar retornos aleatorios con la volatilidad estimada
                daily_returns = np.random.normal(
                    loc=returns.mean(),
                    scale=last_vol,
                    size=n_days
                )
                
                # Asegurar que los retornos sean razonables
                daily_returns = np.clip(daily_returns, -0.3, 0.3)
                
                # Calcular trayectoria de precios
                price_path = last_price * (1 + daily_returns).cumprod()
                
                # Almacenar resultados
                price_paths[i] = price_path
                returns_paths[i] = daily_returns
            
            # Limpiar barra de progreso
            progress_bar.empty()
            progress_text.empty()
            
            # Calcular métricas de la simulación
            final_prices = price_paths[:, -1]
            expected_return = final_prices.mean() / last_price - 1
            expected_volatility = returns_paths.std(axis=1).mean()
            
            # Calcular métricas de riesgo
            var_95 = np.percentile(returns_paths, 5)
            cvar_95 = returns_paths[returns_paths <= var_95].mean()
            
            # Calcular drawdowns simulados
            max_drawdowns = []
            for path in price_paths:
                peak = path[0]
                max_dd = 0
                for price in path:
                    if price > peak:
                        peak = price
                    dd = (peak - price) / peak
                    if dd > max_dd:
                        max_dd = dd
                max_drawdowns.append(max_dd)
            
            avg_max_drawdown = np.mean(max_drawdowns)
            
            # Almacenar resultados
            self.monte_carlo_results[symbol] = {
                'price_paths': price_paths,
                'returns_paths': returns_paths,
                'expected_return': expected_return,
                'expected_volatility': expected_volatility,
                'var_95': var_95,
                'cvar_95': cvar_95,
                'max_drawdown': avg_max_drawdown,
                'last_price': last_price,
                'forecast_dates': [pd.Timestamp.now() + pd.Timedelta(days=i+1) for i in range(n_days)],
                'simulation_date': pd.Timestamp.now()
            }
            
            # Mostrar resumen de métricas
            st.success(f"Análisis de volatilidad completado para {symbol}")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Retorno Esperado", f"{expected_return*100:.2f}%")
            with col2:
                st.metric("Volatilidad Esperada", f"{expected_volatility*100:.2f}%")
            with col3:
                st.metric("VaR 95% (1 día)", f"{var_95*100:.2f}%")
            with col4:
                st.metric("Drawdown Máx. Promedio", f"{avg_max_drawdown*100:.2f}%")
            
            return {
                'garch_model': garch_fit,
                'forecast_volatility': forecast_volatility,
                'monte_carlo': self.monte_carlo_results[symbol]
            }
            
        except Exception as e:
            st.error(f"Error en el análisis de volatilidad para {symbol}: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return None

    def plot_volatility_analysis(self, symbol):
        """
        Genera gráficos para el análisis de volatilidad
        """
        if symbol not in self.monte_carlo_results:
            st.warning(f"No hay datos de análisis de volatilidad para {symbol}")
            return
            
        mc_result = self.monte_carlo_results[symbol]
        
        # Crear figura con subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Trayectorias de Precio Simuladas',
                'Distribución de Retornos Esperados',
                'Volatilidad Pronosticada',
                'Riesgo (VaR)'
            ),
            specs=[[{"secondary_y": True}, {}],
                 [{"secondary_y": True}, {}]]
        )
        
        # 1. Trayectorias de precios simuladas
        for i in range(min(100, len(mc_result['price_paths']))):
            fig.add_trace(
                go.Scatter(
                    x=mc_result['forecast_dates'],
                    y=mc_result['price_paths'][i],
                    line=dict(color='rgba(0, 100, 255, 0.1)'),
                    showlegend=False
                ),
                row=1, col=1
            )
        
        # Añadir media y percentiles
        mean_prices = np.mean(mc_result['price_paths'], axis=0)
        p5 = np.percentile(mc_result['price_paths'], 5, axis=0)
        p95 = np.percentile(mc_result['price_paths'], 95, axis=0)
        
        fig.add_trace(
            go.Scatter(
                x=mc_result['forecast_dates'],
                y=mean_prices,
                line=dict(color='red', width=2),
                name='Media'
            ),
            row=1, col=1, secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=mc_result['forecast_dates'],
                y=p5,
                line=dict(color='green', width=1, dash='dash'),
                name='Percentil 5%'
            ),
            row=1, col=1, secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=mc_result['forecast_dates'],
                y=p95,
                line=dict(color='blue', width=1, dash='dash'),
                name='Percentil 95%'
            ),
            row=1, col=1, secondary_y=False
        )
        
        # 2. Histograma de retornos
        final_returns = (mc_result['price_paths'][:, -1] / mc_result['last_price'] - 1) * 100
        fig.add_trace(
            go.Histogram(
                x=final_returns,
                nbinsx=50,
                name='Distribución de Retornos',
                marker_color='#1f77b4',
                opacity=0.7
            ),
            row=1, col=2
        )
        
        # Añadir línea para el VaR
        var_95 = np.percentile(final_returns, 5)
        fig.add_vline(
            x=var_95,
            line=dict(color='red', width=2, dash='dash'),
            row=1, col=2,
            annotation_text=f'VaR 95%: {var_95:.2f}%',
            annotation_position='top right'
        )
        
        # 3. Volatilidad pronosticada
        if symbol in self.garch_models:
            garch_fit = self.garch_models[symbol]
            volatilities = np.sqrt(garch_fit.conditional_volatility / 100)  # Deshacer escalado
            
            fig.add_trace(
                go.Scatter(
                    x=self.prices.index[-len(volatilities):],
                    y=volatilities * 100,  # Convertir a porcentaje
                    line=dict(color='purple', width=2),
                    name='Volatilidad Condicional',
                    yaxis='y2'
                ),
                row=2, col=1, secondary_y=False
            )
        
        # 4. Riesgo (VaR)
        var_levels = np.arange(1, 11) * 10  # 10% a 100%
        var_values = [np.percentile(returns_paths, level) for level in var_levels]
        
        fig.add_trace(
            go.Bar(
                x=var_levels,
                y=var_values,
                name='Value at Risk',
                marker_color='#ff7f0e'
            ),
            row=2, col=2
        )
        
        # Actualizar diseño
        fig.update_layout(
            title=f'Análisis de Volatilidad - {symbol}',
            showlegend=True,
            height=800,
            template='plotly_dark'
        )
        
        # Actualizar ejes
        fig.update_xaxes(title_text='Fecha', row=1, col=1)
        fig.update_yaxes(title_text='Precio', row=1, col=1)
        fig.update_xaxes(title_text='Retorno (%)', row=1, col=2)
        fig.update_yaxes(title_text='Frecuencia', row=1, col=2)
        fig.update_xaxes(title_text='Fecha', row=2, col=1)
        fig.update_yaxes(title_text='Volatilidad Anualizada (%)', row=2, col=1)
        fig.update_xaxes(title_text='Nivel de Confianza (%)', row=2, col=2)
        fig.update_yaxes(title_text='Pérdida Máxima Esperada (%)', row=2, col=2)
        
        return fig
        
    def load_data(self):
        # Convertir lista de activos a formato adecuado
        symbols = []
        markets = []
        tipos = []
        
        # Función auxiliar para detectar mercado
        def detectar_mercado(tipo_raw: str, mercado_raw: str) -> str:
            """
            Determina el mercado basado en la información proporcionada.
            
            Args:
                tipo_raw: Tipo de activo (ej: 'Acciones', 'Bonos', 'Cedears')
                mercado_raw: Mercado del activo (ej: 'BCBA', 'NYSE', 'NASDAQ')
                
            Returns:
                str: Mercado normalizado para la API
            """
            # Mapeo de mercados comunes
            mercado = str(mercado_raw).upper()
            
            # Si el mercado está vacío, intentar deducirlo del tipo
            if not mercado or mercado == 'NONE':
                tipo = str(tipo_raw).lower()
                if 'cedear' in tipo:
                    return 'BCBA'  # Asumir que los CEDEARs son de BCBA
                elif 'bono' in tipo or 'letra' in tipo or 'obligacion' in tipo:
                    return 'BCBA'  # Asumir bonos en BCBA
                elif 'accion' in tipo:
                    return 'BCBA'  # Asumir acciones en BCBA por defecto
                else:
                    return 'BCBA'  # Valor por defecto
                    
            # Normalizar mercados conocidos
            mercado_map = {
                'BCBA': 'BCBA',
                'BYMA': 'BCBA',
                'ROFEX': 'ROFEX',
                'NYSE': 'NYSE',
                'NASDAQ': 'NASDAQ',
                'AMEX': 'AMEX',
                'BME': 'BME',
                'BVC': 'BVC',
                'BVL': 'BVL',
                'B3': 'B3',
                'BVMF': 'BVMF',
                'EURONEXT': 'EURONEXT',
                'LSE': 'LSE',
                'FWB': 'FWB',
                'SWX': 'SWX',
                'TSX': 'TSX',
                'TSXV': 'TSXV',
                'ASX': 'ASX',
                'NSE': 'NSE',
                'BSE': 'BSE',
                'TSE': 'TSE',
                'HKEX': 'HKEX',
                'SSE': 'SSE',
                'SZSE': 'SZSE',
                'KRX': 'KRX',
                'TASE': 'TASE',
                'MOEX': 'MOEX',
                'JSE': 'JSE'
            }
            
            return mercado_map.get(mercado, 'BCBA')  # Default a BCBA si no se reconoce
            
        # Procesar cada activo
        for activo in self.activos:
            if 'simbolo' not in activo:
                continue
                
            simbolo = activo['simbolo']
            tipo = activo.get('tipo', '')
            mercado = activo.get('mercado', '')
            
            # Determinar mercado
            mercado_normalizado = detectar_mercado(tipo, mercado)
            
            # Agregar a las listas
            symbols.append(simbolo)
            markets.append(mercado_normalizado)
            tipos.append(tipo)
        
        # Obtener datos históricos
        try:
            historical_data = get_historical_data_for_optimization(
                self.token,
                [{'simbolo': s, 'mercado': m} for s, m in zip(symbols, markets)],
                self.fecha_desde,
                self.fecha_hasta
            )
            
            if not historical_data:
                st.error("No se pudieron cargar los datos históricos")
                return False
                
            # Procesar datos en un DataFrame
            prices = pd.DataFrame()
            volumes = pd.DataFrame()
            
            for symbol, data in historical_data.items():
                if data is not None and not data.empty:
                    prices[symbol] = data['precio']
                    if 'volumen' in data.columns:
                        volumes[symbol] = data['volumen']
            
            # Calcular retornos
            returns = prices.pct_change().dropna()
            
            # Guardar datos
            self.prices = prices
            self.returns = returns
            if not volumes.empty:
                self.volumes = volumes
                
            self.data_loaded = True
            return True
            
        except Exception as e:
            st.error(f"Error al cargar datos: {str(e)}")
            st.exception(e)
            return False

    def compute_portfolio(self, strategy='max_sharpe', target_return=None):
        """
        Calcula la cartera óptima según la estrategia especificada.
        
        Args:
            strategy (str): Estrategia de optimización ('max_sharpe', 'min_vol', 'equi-weight')
            target_return (float, optional): Retorno objetivo para estrategias que lo requieran
            
        Returns:
            output: Objeto output con la cartera optimizada o None en caso de error
        """
        if not self.data_loaded or self.returns is None or self.returns.empty:
            st.error("No hay datos de retornos disponibles")
            return None
            
        try:
            # Inicializar el manager si no existe
            if not hasattr(self, 'manager') or not self.manager:
                self.manager = manager(
                    self.returns.columns.tolist(),
                    self.notional,
                    self.prices.to_dict('series')
                )
                
                # Cargar datos y calcular covarianzas
                self.manager.returns = self.returns
                self.manager.compute_covariance()
                
            # Calcular cartera según estrategia
            if strategy in ['max_sharpe', 'min_vol']:
                portfolio_output = self.manager.compute_portfolio(
                    portfolio_type=strategy,
                    target_return=target_return
                )
                
                if portfolio_output is None:
                    st.warning("No se pudo calcular la cartera óptima. Usando estrategia equi-weight.")
                    n_assets = len(self.returns.columns)
                    weights = np.ones(n_assets) / n_assets
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
                
            elif strategy == 'equi-weight':
                n_assets = len(self.returns.columns)
                weights = np.ones(n_assets) / n_assets
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
                
            else:
                st.error(f"Estrategia no soportada: {strategy}")
                return None
                
        except Exception as e:
            st.error(f"Error al calcular la cartera: {str(e)}")
            st.exception(e)
            return None
    
    def compute_efficient_frontier(self, target_return=0.08, include_min_variance=True):
        """Computa la frontera eficiente"""
        if not self.data_loaded or not hasattr(self, 'prices') or self.prices is None:
            st.error("No hay datos de precios disponibles")
            return None, None, None
        
        try:
            portfolios, returns, volatilities = compute_efficient_frontier(
                self.prices.columns.tolist(), 
                self.notional, 
                target_return, 
                include_min_variance,
                self.prices.to_dict('series')
            )
            return portfolios, returns, volatilities
        except Exception as e:
            st.error(f"Error al calcular la frontera eficiente: {str(e)}")
            return None, None, None

    def run_twap_schedule(self, symbol, total_shares, duration_hours, interval_minutes=30):
        """
        Implement Time-Weighted Average Price scheduling
        
        Args:
            symbol: Asset symbol
            total_shares: Total shares to execute
            duration_hours: Total execution duration in hours
            interval_minutes: Interval between executions in minutes
        """
        intervals = (duration_hours * 60) // interval_minutes
        shares_per_interval = total_shares // intervals
        
        # Implement TWAP execution logic
        for i in range(intervals):
            # Execute shares_per_interval at current market price
            # This would connect to your broker API in a real implementation
            print(f"Executing {shares_per_interval} shares of {symbol} at interval {i+1}/{intervals}")
        
        return {
            'strategy': 'TWAP',
            'total_shares': total_shares,
            'executed_shares': shares_per_interval * intervals,
            'intervals': intervals,
            'shares_per_interval': shares_per_interval
        }
    
    def run_vwap_schedule(self, symbol, total_shares, volume_profile):
        """
        Implement Volume-Weighted Average Price scheduling
        
        Args:
            symbol: Asset symbol
            total_shares: Total shares to execute
            volume_profile: Dict with time buckets and volume percentages
                          Example: {'09:00-10:00': 0.047, '10:00-11:00': 0.052, ...}
        """
        execution_plan = {}
        for bucket, pct in volume_profile.items():
            shares = int(total_shares * pct)
            execution_plan[bucket] = shares
            
            # Execute shares in this bucket based on actual volume
            print(f"Executing {shares} shares of {symbol} in time bucket {bucket}")
        
        return {
            'strategy': 'VWAP',
            'total_shares': total_shares,
            'execution_plan': execution_plan,
            'volume_profile': volume_profile
        }
    
    def smart_order_routing(self, symbol, quantity, side, venues):
        """
        Implement Smart Order Routing algorithm
        
        Args:
            symbol: Asset symbol
            quantity: Total quantity to execute
            side: 'buy' or 'sell'
            venues: List of trading venues with rankings
                   Example: [{'name': 'NYSE', 'ranking': 1, 'cost': 0.01}, ...]
        """
        # Sort venues by ranking
        sorted_venues = sorted(venues, key=lambda x: x['ranking'])
        
        # Distribute quantity based on venue ranking
        distributed_qty = {}
        remaining = quantity
        
        for venue in sorted_venues:
            if remaining <= 0:
                break
                
            # Allocate portion to this venue
            qty = min(remaining, int(quantity * (1/venue['ranking'])))
            distributed_qty[venue['name']] = qty
            remaining -= qty
            
            # Execute order at venue
            print(f"Routing {qty} {side} order of {symbol} to {venue['name']}")
        
        return {
            'strategy': 'SOR',
            'symbol': symbol,
            'side': side,
            'total_quantity': quantity,
            'distributed_quantity': distributed_qty,
            'venues': sorted_venues
        }
    
    def execute_market_order(self, symbol, quantity, side, order_type='IoC'):
        """
        Execute market order with different order types
        
        Args:
            symbol: Asset symbol
            quantity: Quantity to execute
            side: 'buy' or 'sell'
            order_type: 'IoC' (Immediate or Cancel), 'FoK' (Fill or Kill)
        """
        if order_type == 'IoC':
            print(f"Executing {quantity} {side} IoC order for {symbol}")
            # In real implementation, this would connect to broker API
            return {'status': 'partial', 'executed': quantity * 0.8}  # Example partial fill
        elif order_type == 'FoK':
            print(f"Executing {quantity} {side} FoK order for {symbol}")
            # In real implementation, this would connect to broker API
            return {'status': 'filled', 'executed': quantity}  # Example full fill
        
    def execute_limit_order(self, symbol, quantity, side, price, order_type='Peg'):
        """
        Execute limit order with different order types
        
        Args:
            symbol: Asset symbol
            quantity: Quantity to execute
            side: 'buy' or 'sell'
            price: Limit price
            order_type: 'Peg' (pegged to best), 'FloatPeg' (pegged with offset)
        """
        if order_type == 'Peg':
            print(f"Placing {quantity} {side} Peg order for {symbol} at best {side} price")
            # In real implementation, this would connect to broker API
            return {'status': 'pending', 'order_id': '12345'}
        elif order_type == 'FloatPeg':
            print(f"Placing {quantity} {side} FloatPeg order for {symbol} with offset")
            # In real implementation, this would connect to broker API
            return {'status': 'pending', 'order_id': '12346'}
    
    def show_analysis_interface(self):
        """Muestra la interfaz de análisis técnico"""
        st.header("📈 Análisis Técnico")
        
        if hasattr(self, 'returns') and self.returns is not None:
            st.subheader("Retornos Diarios")
            st.line_chart(self.returns)
            
            st.subheader("Estadísticas")
            st.dataframe(self.returns.describe())
            
            st.subheader("Correlaciones")
            st.dataframe(self.returns.corr())
        else:
            st.warning("Primero cargue los datos para realizar el análisis")
    
    def optimize_random_universe(self, capital_ars, num_assets=10, panels=['acciones', 'cedears'], 
                               start_date='2021-01-01', end_date=None):
        """
        Optimize portfolio using random ticker selection with capital constraints
        
        Args:
            capital_ars: Available capital in ARS
            num_assets: Number of assets to select per panel
            panels: List of panels to select from (e.g. ['acciones', 'cedears'])
            start_date: Start date for historical data
            end_date: End date for historical data (default: today)
        
        Returns:
            dict: {'selected_assets': list, 'portfolio_value': pd.Series, 
                  'weights': dict, 'metrics': dict}
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        # Get tokens
        token_portador, token_refresco = self._get_tokens()
        if not token_portador:
            return {'error': 'Failed to get API tokens'}
            
        # Get tickers by panel
        tickers_by_panel, _ = self._get_tickers_by_panel(token_portador, panels, 'Argentina')
        
        # Select random assets within capital constraints
        selected_assets = []
        remaining_capital = capital_ars
        
        for panel in panels:
            if panel not in tickers_by_panel:
                continue
                
            # Shuffle and select assets
            tickers = tickers_by_panel[panel]
            random.shuffle(tickers)
            
            for symbol in tickers:
                if len(selected_assets) >= num_assets:
                    break
                    
                # Get historical data
                data = self._get_historical_data(symbol, 'BCBA', start_date, end_date, token_portador)
                if not data or len(data) == 0:
                    continue
                    
                # Get last price
                last_price = self._get_last_price(data)
                if not last_price or last_price <= 0:
                    continue
                    
                # Check if we can afford at least 1 share
                if last_price <= remaining_capital:
                    selected_assets.append({
                        'symbol': symbol,
                        'panel': panel,
                        'price': last_price,
                        'data': data
                    })
                    remaining_capital -= last_price
        
        if len(selected_assets) < 2:
            return {'error': 'Not enough affordable assets found for given capital'}
            
        # Calculate portfolio metrics
        portfolio_value = self._calculate_portfolio_value(selected_assets)
        weights = {a['symbol']: a['price']/capital_ars for a in selected_assets}
        
        # Calculate risk metrics
        returns = portfolio_value.pct_change().dropna()
        metrics = {
            'sharpe': self._calculate_sharpe(returns),
            'volatility': returns.std(),
            'max_drawdown': self._calculate_max_drawdown(portfolio_value)
        }
        
        return {
            'selected_assets': selected_assets,
            'portfolio_value': portfolio_value,
            'weights': weights,
            'metrics': metrics
        }
        
    def _get_tokens(self):
        """Helper to get API tokens"""
        token_url = 'https://api.invertironline.com/token'
        payload = {
            'username': self.username,
            'password': self.password,
            'grant_type': 'password'
        }
        response = requests.post(token_url, data=payload)
        if response.status_code == 200:
            tokens = response.json()
            return tokens['access_token'], tokens['refresh_token']
        return None, None
        
    def _get_tickers_by_panel(self, token, panels, country):
        """Helper to get tickers by panel"""
        tickers = {}
        for panel in panels:
            url = f'https://api.invertironline.com/api/v2/cotizaciones-orleans/{panel}/{country}/Operables'
            response = requests.get(url, headers={'Authorization': f'Bearer {token}'})
            if response.status_code == 200:
                tickers[panel] = [t['simbolo'] for t in response.json().get('titulos', [])]
        return tickers, None
        
    def _get_historical_data(self, symbol, market, start_date, end_date, token):
        """Helper to get historical data"""
        url = f"https://api.invertironline.com/api/v2/{market}/Titulos/{symbol}/Cotizacion/seriehistorica/{start_date}/{end_date}/SinAjustar"
        response = requests.get(url, headers={'Authorization': f'Bearer {token}'})
        return response.json() if response.status_code == 200 else None
        
    def _get_last_price(self, data):
        """Helper to extract last price from historical data"""
        if not data or not isinstance(data, list):
            return None
            
        df = pd.DataFrame(data)
        for col in ['ultimoPrecio', 'ultimo_precio', 'precio', 'close', 'cierre']:
            if col in df.columns:
                return df[col].iloc[-1]
        return None
        
    def _calculate_portfolio_value(self, assets):
        """Helper to calculate portfolio value over time"""
        portfolio = pd.DataFrame()
        
        for asset in assets:
            df = pd.DataFrame(asset['data'])
            for col in ['fecha', 'date', 'fechaHora']:
                if col in df.columns:
                    df['date'] = pd.to_datetime(df[col])
                    break
            
            for col in ['ultimoPrecio', 'ultimo_precio', 'precio', 'close', 'cierre']:
                if col in df.columns:
                    df = df[['date', col]].rename(columns={col: 'price'})
                    df['symbol'] = asset['symbol']
                    portfolio = pd.concat([portfolio, df])
                    break
        
        if portfolio.empty:
            return None
            
        # Pivot and sum
        portfolio = portfolio.pivot(index='date', columns='symbol', values='price')
        return portfolio.sum(axis=1)
        
    def _calculate_sharpe(self, returns, risk_free_rate=0):
        """Helper to calculate Sharpe ratio"""
        if len(returns) == 0:
            return 0
        return (returns.mean() - risk_free_rate) / returns.std()
        
    def _calculate_max_drawdown(self, portfolio_value):
        """Helper to calculate max drawdown"""
        if portfolio_value is None or len(portfolio_value) == 0:
            return 0
            
        cumulative = portfolio_value.cummax()
        drawdown = (portfolio_value - cumulative) / cumulative
        return drawdown.min()

class PortfolioManager:
    def show_trading_interface(self):
        """Display the trading algorithm interface in Streamlit"""
        st.header("Algoritmos de Trading")
        
        # Create tabs for different algorithms
        tab1, tab2, tab3, tab4 = st.tabs(["TWAP", "VWAP", "SOR", "Órdenes"])
        
        with tab1:
            st.subheader("Time-Weighted Average Price (TWAP)")
            col1, col2, col3 = st.columns(3)
            with col1:
                symbol = st.text_input("Símbolo", key="twap_symbol")
            with col2:
                shares = st.number_input("Acciones totales", min_value=1, value=1000, key="twap_shares")
            with col3:
                duration = st.number_input("Duración (horas)", min_value=1, value=4, key="twap_duration")
            interval = st.slider("Intervalo (minutos)", 1, 60, 30, key="twap_interval")
            
            if st.button("Ejecutar TWAP", key="run_twap"):
                if symbol:
                    result = self.run_twap_schedule(symbol, shares, duration, interval)
                    st.success(f"Programado: {result['intervals']} intervalos de {result['shares_per_interval']} acciones")
                    st.json(result)
                else:
                    st.error("Ingrese un símbolo válido")
        
        with tab2:
            st.subheader("Volume-Weighted Average Price (VWAP)")
            col1, col2 = st.columns(2)
            with col1:
                symbol = st.text_input("Símbolo", key="vwap_symbol")
                shares = st.number_input("Acciones totales", min_value=1, value=1000, key="vwap_shares")
            
            st.write("Perfil de volumen (porcentajes por horario)")
            time_buckets = {
                '09:00-10:00': 0.15,
                '10:00-11:00': 0.20,
                '11:00-12:00': 0.25,
                '12:00-13:00': 0.15,
                '13:00-14:00': 0.10,
                '14:00-15:00': 0.10,
                '15:00-16:00': 0.05
            }
            
            # Let user adjust volume percentages
            volume_profile = {}
            for bucket, default in time_buckets.items():
                volume_profile[bucket] = st.slider(
                    f"% volumen {bucket}", 
                    min_value=0.0, 
                    max_value=1.0, 
                    value=default
                )
            
            if st.button("Ejecutar VWAP", key="run_vwap"):
                if symbol and sum(volume_profile.values()) > 0:
                    result = self.run_vwap_schedule(symbol, shares, volume_profile)
                    st.success("Plan de ejecución VWAP creado")
                    st.json(result)
                else:
                    st.error("Ingrese un símbolo y porcentajes válidos")
        
        with tab3:
            st.subheader("Smart Order Routing")
            col1, col2 = st.columns(2)
            with col1:
                symbol = st.text_input("Símbolo", key="sor_symbol")
                quantity = st.number_input("Cantidad", min_value=1, value=1000, key="sor_quantity")
                side = st.selectbox("Lado", ["buy", "sell"], key="sor_side")
            
            st.write("Configurar mercados")
            venues = ["BYMA", "NYSE", "NASDAQ", "ROFEX"]
            venue_config = {}
            
            for venue in venues:
                with st.expander(venue):
                    venue_config[venue] = {
                        "ranking": st.number_input(f"Ranking {venue}", min_value=1, value=1, key=f"sor_rank_{venue}"),
                        "cost": st.number_input(f"Costo {venue}", min_value=0.0, value=0.01, step=0.001, key=f"sor_cost_{venue}")
                    }
            
            if st.button("Ejecutar SOR", key="run_sor"):
                if symbol:
                    result = self.smart_order_routing(
                        symbol, 
                        quantity, 
                        "buy" if side == "Compra" else "sell",
                        [{"name": k, **v} for k, v in venue_config.items()]
                    )
                    st.success("Órdenes distribuidas")
                    st.json(result)
                else:
                    st.error("Ingrese un símbolo válido")
        
        with tab4:
            st.subheader("Ejecución de Órdenes")
            order_type = st.radio("Tipo de orden", ["Mercado", "Límite"], key="order_type")
            
            col1, col2 = st.columns(2)
            with col1:
                symbol = st.text_input("Símbolo", key="order_symbol")
                quantity = st.number_input("Cantidad", min_value=1, value=100, key="order_quantity")
                side = st.selectbox("Lado", ["buy", "sell"], key="order_side")
            
            if order_type == "Mercado":
                market_type = st.selectbox("Tipo de mercado", ["IoC", "FoK"], key="market_type")
                if st.button("Enviar Orden", key="send_market"):
                    if symbol:
                        result = self.execute_market_order(symbol, quantity, side, market_type)
                        st.success(f"Orden ejecutada: {result['status']}")
                        st.json(result)
                    else:
                        st.error("Ingrese un símbolo válido")
            else:
                with col2:
                    price = st.number_input("Precio", min_value=0.01, value=100.0, key="limit_price")
                limit_type = st.selectbox("Tipo", ["Peg", "FloatPeg"], key="limit_type")
                if st.button("Enviar Orden", key="send_limit"):
                    if symbol and price > 0:
                        result = self.execute_limit_order(symbol, quantity, side, price, limit_type)
                        st.success(f"Orden colocada: {result['status']}")
                        st.json(result)
                    else:
                        st.error("Ingrese un símbolo y precio válidos")

def main():
    # Configuración existente
    st.set_page_config(
        page_title="IOL Portfolio Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inicialización con manejo de errores
    try:
        pm = PortfolioManager()
    except Exception as e:
        st.error(f"Error inicializando PortfolioManager: {str(e)}")
        st.stop()
    
    # Navegación principal
    st.sidebar.title("Menú Principal")
    menu = st.sidebar.radio(
        "Secciones",
        ["Dashboard", "Análisis", "Optimización", "Trading", "Reportes"]
    )
    
    # Manejo de cada sección con try-except
    try:
        if menu == "Dashboard":
            if hasattr(pm, 'show_dashboard'):
                pm.show_dashboard()
            else:
                st.warning("Módulo Dashboard no implementado aún")
        elif menu == "Análisis":
            pm.show_analysis_interface()
        elif menu == "Optimización":
            if hasattr(pm, 'show_optimization'):
                pm.show_optimization()
            else:
                st.warning("Módulo Optimización no implementado aún")
        elif menu == "Trading":
            if hasattr(pm, 'show_trading_interface'):
                pm.show_trading_interface()
            else:
                st.warning("Módulo Trading no implementado aún")
        elif menu == "Reportes":
            if hasattr(pm, 'show_reports'):
                pm.show_reports()
            else:
                st.warning("Módulo Reportes no implementado aún")
    except Exception as e:
        st.error(f"Error en el módulo {menu}: {str(e)}")
        
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption("Portfolio Manager v2.0 | 2023")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Error crítico: {str(e)}")
        st.stop()
