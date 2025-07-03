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
    Obtiene todas las tasas de caución para todos los plazos desde la API de IOL usando el endpoint correcto.
    Args:
        token_portador (str): Token de autenticación Bearer
    Returns:
        DataFrame: DataFrame con la información de todas las cauciones/plazos o None en caso de error
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
                # Incluir TODOS los instrumentos y plazos reportados por la API
                # Extraer el plazo en días (puede venir como '7 días', '14 días', etc)
                if 'plazo' in df.columns:
                    df['plazo_dias'] = df['plazo'].astype(str).str.extract(r'(\d+)').astype(float)
                else:
                    df['plazo_dias'] = np.nan
                # Limpiar la tasa (convertir a float si es necesario)
                if 'ultimoPrecio' in df.columns:
                    df['tasa_limpia'] = pd.to_numeric(df['ultimoPrecio'], errors='coerce')
                else:
                    df['tasa_limpia'] = np.nan
                # Si hay columna 'volumen', usarla como monto
                if 'monto' not in df.columns and 'volumen' in df.columns:
                    df['monto'] = df['volumen']
                # Ordenar por plazo si está disponible
                if 'plazo_dias' in df.columns:
                    df = df.sort_values('plazo_dias')
                # Seleccionar columnas útiles, pero mostrar todo lo que venga de la API
                columnas_utiles = ['simbolo', 'descripcion', 'plazo', 'plazo_dias', 'ultimoPrecio', 'tasa_limpia', 'monto', 'moneda', 'volumen']
                columnas_disponibles = [col for col in columnas_utiles if col in df.columns]
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
        if isinstance(data, list) and len(data) > 0 and 'fecha' in data[0] and 'ultimoPrecio' in data[0]:
            df = pd.DataFrame(data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df = df.set_index('fecha')
            df = df[['ultimoPrecio']].rename(columns={'ultimoPrecio': 'precio'})
            return df
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error al obtener la serie histórica del FCI {simbolo}: {str(e)}")
        return None


def obtener_tickers_aleatorios_por_clase(token_portador, clases_activo, n_por_clase=5):
    """
    Obtiene una cantidad específica de tickers aleatorios por cada clase de activo.
    
    Args:
        token_portador (str): Token de autenticación
        clases_activo (list): Lista de clases de activo (ej: ['acciones', 'bonos'])
        n_por_clase (int): Cantidad de tickers a seleccionar por clase
        
    Returns:
        list: Lista de diccionarios con la información de los activos seleccionados
    """
    activos_seleccionados = []
    
    # Mapeo de clases de activo a paneles de IOL
    mapeo_paneles = {
        'acciones': 'acciones',
        'bonos': 'titulosPublicos',
        'cedears': 'cedears',
        'obligaciones': 'obligacionesNegociables',
        'adrs': 'aDRs'
    }
    
    for clase in clases_activo:
        panel = mapeo_paneles.get(clase.lower())
        if not panel:
            continue
            
        # Obtener todos los tickers del panel
        tickers_por_panel, _ = obtener_tickers_por_panel(token_portador, [panel], 'Argentina')
        tickers = tickers_por_panel.get(panel, [])
        
        # Seleccionar aleatoriamente n_por_clase tickers
        if tickers:
            seleccion = random.sample(tickers, min(n_por_clase, len(tickers)))
            for simbolo in seleccion:
                activos_seleccionados.append({
                    'simbolo': simbolo,
                    'mercado': 'BCBA',  # Asumimos BCBA por defecto
                    'tipo': clase,
                    'cantidad': 0,  
                    'precio_actual': 0  
                })
    
    return activos_seleccionados

    # Resto de la configuración común
    fecha_desde = st.session_state.fecha_desde
    fecha_hasta = st.session_state.fecha_hasta
    
    st.info(f"Analizando {len(activos_filtrados)} activos desde {fecha_desde} hasta {fecha_hasta}")
    
    # Configuración de optimización
    metodos_optimizacion = {
        'Maximizar Sharpe (Markowitz)': 'max_sharpe',
        'Mínima Varianza L1': 'min-variance-l1',
        'Mínima Varianza L2': 'min-variance-l2',
        'Pesos Iguales': 'equi-weight',
        'Solo Posiciones Largas': 'long-only',
        'Markowitz con Retorno Objetivo': 'markowitz-target'
    }
    metodo_ui = st.selectbox(
        "Método de Optimización de Portafolio:",
        options=list(metodos_optimizacion.keys()),
        key="opt_metodo_optimizacion"
    )
    metodo = metodos_optimizacion[metodo_ui]

    # Pedir retorno objetivo solo si corresponde
    target_return = None
    if metodo == 'markowitz-target':
        target_return = st.number_input(
            "Retorno Objetivo (anual, decimal, ej: 0.15 para 15%):",
            min_value=0.01, value=0.10, step=0.01, format="%.4f",
            help="No hay máximo. Si el retorno es muy alto, la simulación puede no converger."
        )

    show_frontier = st.checkbox("Mostrar Frontera Eficiente", value=True)

    # Configuración de ejecución
    scheduling_methods = {
        'TWAP (Time-Weighted)': 'twap',
        'VWAP (Volume-Weighted)': 'vwap'
    }
    scheduling_ui = st.selectbox(
        "Algoritmo de Scheduling:",
        options=list(scheduling_methods.keys()),
        key="opt_scheduling_algo"
    )
    scheduling = scheduling_methods[scheduling_ui]

    order_types = {
        'Market Order': 'mo',
        'Limit Order': 'lo',
        'Peg Order': 'peg',
        'Float Peg': 'float_peg',
        'Fill or Kill': 'fok',
        'Immediate or Cancel': 'ioc'
    }
    order_type_ui = st.selectbox(
        "Tipo de Orden:",
        options=list(order_types.keys()),
        key="opt_tipo_orden"
    )
    order_type = order_types[order_type_ui]

    # Widget TradingView
    try:
        from streamlit_tradingview_ta import TradingViewWidget
        st.subheader("Gráfico interactivo TradingView")
        TradingViewWidget(
            symbol="NASDAQ:AAPL",  # Cambia por símbolo seleccionado
            interval="D",
            theme="dark",
            studies=["MACD@tv-basicstudies", "RSI@tv-basicstudies"],
            height=600,
            width="100%",
        )
    except ImportError:
        st.info("Instala 'streamlit-tradingview-widget' para habilitar el gráfico TradingView.")

    # Botones de acción
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ejecutar_optimizacion = st.button("🚀 Ejecutar Optimización", type="primary")
    with col2:
        ejecutar_frontier = st.button("📈 Calcular Frontera Eficiente")
    with col3:
        mostrar_cauciones = st.button("💸 Ver Cauciones Todos los Plazos")
    with col4:
        comparar_opt = st.checkbox("Comparar Actual vs Aleatoria", value=False, help="Compara la optimización sobre tu portafolio y sobre un universo aleatorio de activos.")

    # Ejecución de optimización
    if ejecutar_optimizacion:
        with st.spinner("Ejecutando optimización..."):
            try:
                # Configuración común para ambos modos
                if modo_optimizacion == 'Rebalanceo':
                    # Usar datos diarios de IOL y el capital actual del portafolio
                    activos_para_opt = activos_filtrados
                    manager = PortfolioManager(
                        activos_para_opt,
                        token_acceso,
                        fecha_desde,
                        fecha_hasta,
                        capital=capital_inicial
                    )
                    if manager.load_data():
                        portfolio_result = manager.compute_portfolio(strategy=metodo, target_return=target_return)
                        if portfolio_result:
                            st.success("✅ Optimización de Rebalanceo completada")
                            mostrar_resultados_optimizacion(portfolio_result, capital_inicial, manager)
                else:  # Optimización desde Cero
                    if frecuencia_datos == 'Intradía':
                        # Usar yfinance para acciones y cedears
                        import yfinance as yf
                        activos_yf = []
                        for activo in activos_filtrados:
                            tipo = activo.get('tipo')
                            if tipo in ['Acciones', 'Cedears']:
                                simbolo = activo.get('simbolo')
                                if simbolo:
                                    # Agregar sufijo .BA para acciones y cedears
                                    activos_yf.append({
                                        'simbolo': f"{simbolo}.BA",
                                        'tipo': tipo
                                    })
                        if activos_yf:
                            # Obtener datos intradía
                            data_yf = yf.download(
                                [a['simbolo'] for a in activos_yf],
                                start=fecha_desde,
                                end=fecha_hasta,
                                interval="1h"  # Intervalo intradía
                            )
                            if not data_yf.empty:
                                # Convertir datos yfinance a formato compatible
                                activos_formato = []
                                for activo in activos_yf:
                                    simbolo = activo['simbolo']
                                    precios = data_yf['Close'][simbolo]
                                    if not precios.empty:
                                        activos_formato.append({
                                            'simbolo': simbolo,
                                            'precios': precios
                                        })
                                if activos_formato:
                                    manager = PortfolioManager(
                                        activos_formato,
                                        token_acceso,
                                        fecha_desde,
                                        fecha_hasta,
                                        capital=capital_inicial
                                    )
                                    if manager.load_data():
                                        portfolio_result = manager.compute_portfolio(strategy=metodo, target_return=target_return)
                                        if portfolio_result:
                                            st.success("✅ Optimización Intradía completada")
                                            mostrar_resultados_optimizacion(portfolio_result, capital_inicial, manager)
                    else:  # Diario
                        # Usar datos diarios de IOL
                        manager = PortfolioManager(
                            activos_filtrados,
                            token_acceso,
                            fecha_desde,
                            fecha_hasta,
                            capital=capital_inicial
                        )
                        if manager.load_data():
                            portfolio_result = manager.compute_portfolio(strategy=metodo, target_return=target_return)
                            if portfolio_result:
                                st.success("✅ Optimización Diaria completada")
                                mostrar_resultados_optimizacion(portfolio_result, capital_inicial, manager)

            except Exception as e:
                st.error(f"Error en la optimización: {str(e)}")
    
    # Configuración inicial
    col1, col2 = st.columns(2)
    
    with col1:
        modo_optimizacion = st.selectbox(
            "Modo de Optimización:",
            options=['Rebalanceo', 'Optimización desde Cero'],
            format_func=lambda x: {
                'Rebalanceo': 'Rebalanceo (Datos Diarios IOL)',
                'Optimización desde Cero': 'Optimización desde Cero (Intradía y Diario)'
            }[x]
        )
    
    with col2:
        capital_inicial = st.number_input(
            "Capital Inicial (ARS):",
            min_value=1000.0, max_value=1e9, value=100000.0, step=1000.0,
            help="Monto inicial para la optimización. En modo Rebalanceo, se usa el capital actual del portafolio."
        )
    
    # Configuración específica por modo
    if modo_optimizacion == 'Optimización desde Cero':
        col3, col4 = st.columns(2)
        with col3:
            frecuencia_datos = st.selectbox(
                "Frecuencia de Datos:",
                options=['Diario', 'Intradía'],
                format_func=lambda x: {
                    'Diario': 'Datos Diarios (IOL)',
                    'Intradía': 'Datos Intradía (yfinance)'
                }[x]
            )
        
        with col4:
            if frecuencia_datos == 'Intradía':
                st.info("Para acciones y cedears, se agregará automáticamente el sufijo .BA")
                tipos_disponibles = ['Acciones', 'Cedears']
            else:
                tipos_disponibles = sorted(set([a['tipo'] for a in activos_para_optimizacion if a.get('tipo')]))
            
            tipo_seleccionado = st.selectbox(
                "Filtrar por tipo de activo:",
                options=['Todos'] + tipos_disponibles,
                key="opt_tipo_activo",
                format_func=lambda x: "Todos" if x == 'Todos' else x
            )
            
            if tipo_seleccionado != 'Todos':
                activos_filtrados = [a for a in activos_para_optimizacion if a.get('tipo') == tipo_seleccionado]
            else:
                activos_filtrados = activos_para_optimizacion
    else:  # Rebalanceo
        activos_filtrados = activos_para_optimizacion
        frecuencia_datos = 'Diario'

    # Resto de la configuración común
    fecha_desde = st.session_state.fecha_desde
    fecha_hasta = st.session_state.fecha_hasta
    
    st.info(f"Analizando {len(activos_filtrados)} activos desde {fecha_desde} hasta {fecha_hasta}")
    
    # Configuración de optimización
    metodos_optimizacion = {
        'Maximizar Sharpe (Markowitz)': 'max_sharpe',
        'Mínima Varianza L1': 'min-variance-l1',
        'Mínima Varianza L2': 'min-variance-l2',
        'Pesos Iguales': 'equi-weight',
        'Solo Posiciones Largas': 'long-only',
        'Markowitz con Retorno Objetivo': 'markowitz-target'
    }
    metodo_ui = st.selectbox(
        "Método de Optimización de Portafolio:",
        options=list(metodos_optimizacion.keys()),
        key="opt_metodo_optimizacion"
    )
    metodo = metodos_optimizacion[metodo_ui]

    # Pedir retorno objetivo solo si corresponde
    target_return = None
    if metodo == 'markowitz-target':
        target_return = st.number_input(
            "Retorno Objetivo (anual, decimal, ej: 0.15 para 15%):",
            min_value=0.01, value=0.10, step=0.01, format="%.4f",
            help="No hay máximo. Si el retorno es muy alto, la simulación puede no converger."
        )

    show_frontier = st.checkbox("Mostrar Frontera Eficiente", value=True)

    # Configuración de ejecución
    scheduling_methods = {
        'TWAP (Time-Weighted)': 'twap',
        'VWAP (Volume-Weighted)': 'vwap'
    }
    scheduling_ui = st.selectbox(
        "Algoritmo de Scheduling:",
        options=list(scheduling_methods.keys()),
        key="opt_scheduling_algo"
    )
    scheduling = scheduling_methods[scheduling_ui]

    order_types = {
        'Market Order': 'mo',
        'Limit Order': 'lo',
        'Peg Order': 'peg',
        'Float Peg': 'float_peg',
        'Fill or Kill': 'fok',
        'Immediate or Cancel': 'ioc'
    }
    order_type_ui = st.selectbox(
        "Tipo de Orden:",
        options=list(order_types.keys()),
        key="opt_tipo_orden"
    )
    order_type = order_types[order_type_ui]

    # Widget TradingView
    try:
        from streamlit_tradingview_ta import TradingViewWidget
        st.subheader("Gráfico interactivo TradingView")
        TradingViewWidget(
            symbol="NASDAQ:AAPL",  # Cambia por símbolo seleccionado
            interval="D",
            theme="dark",
            studies=["MACD@tv-basicstudies", "RSI@tv-basicstudies"],
            height=600,
            width="100%",
        )
    except ImportError:
        st.info("Instala 'streamlit-tradingview-widget' para habilitar el gráfico TradingView.")

    # Botones de acción
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ejecutar_optimizacion = st.button("🚀 Ejecutar Optimización", type="primary")
    with col2:
        ejecutar_frontier = st.button("📈 Calcular Frontera Eficiente")
    with col3:
        mostrar_cauciones = st.button("💸 Ver Cauciones Todos los Plazos")
    with col4:
        comparar_opt = st.checkbox("Comparar Actual vs Aleatoria", value=False, help="Compara la optimización sobre tu portafolio y sobre un universo aleatorio de activos.")

    # Ejecución de optimización
    if ejecutar_optimizacion:
        with st.spinner("Ejecutando optimización..."):
            try:
                # Configuración común para ambos modos
                if modo_optimizacion == 'Rebalanceo':
                    # Usar datos diarios de IOL y el capital actual del portafolio
                    activos_para_opt = activos_filtrados
                    manager = PortfolioManager(
                        activos_para_opt,
                        token_acceso,
                        fecha_desde,
                        fecha_hasta,
                        capital=capital_inicial
                    )
                    if manager.load_data():
                        portfolio_result = manager.compute_portfolio(strategy=metodo, target_return=target_return)
                        if portfolio_result:
                            st.success("✅ Optimización de Rebalanceo completada")
                            mostrar_resultados_optimizacion(portfolio_result, capital_inicial, manager)
                else:  # Optimización desde Cero
                    if frecuencia_datos == 'Intradía':
                        # Usar yfinance para acciones y cedears
                        import yfinance as yf
                        activos_yf = []
                        for activo in activos_filtrados:
                            tipo = activo.get('tipo')
                            if tipo in ['Acciones', 'Cedears']:
                                simbolo = activo.get('simbolo')
                                if simbolo:
                                    # Agregar sufijo .BA para acciones y cedears
                                    activos_yf.append({
                                        'simbolo': f"{simbolo}.BA",
                                        'tipo': tipo
                                    })
                        if activos_yf:
                            # Obtener datos intradía
                            data_yf = yf.download(
                                [a['simbolo'] for a in activos_yf],
                                start=fecha_desde,
                                end=fecha_hasta,
                                interval="1h"  # Intervalo intradía
                            )
                            if not data_yf.empty:
                                # Convertir datos yfinance a formato compatible
                                activos_formato = []
                                for activo in activos_yf:
                                    simbolo = activo['simbolo']
                                    precios = data_yf['Close'][simbolo]
                                    if not precios.empty:
                                        activos_formato.append({
                                            'simbolo': simbolo,
                                            'precios': precios
                                        })
                                if activos_formato:
                                    manager = PortfolioManager(
                                        activos_formato,
                                        token_acceso,
                                        fecha_desde,
                                        fecha_hasta,
                                        capital=capital_inicial
                                    )
                                    if manager.load_data():
                                        portfolio_result = manager.compute_portfolio(strategy=metodo, target_return=target_return)
                                        if portfolio_result:
                                            st.success("✅ Optimización Intradía completada")
                                            mostrar_resultados_optimizacion(portfolio_result, capital_inicial, manager)
                    else:  # Diario
                        # Usar datos diarios de IOL
                        manager = PortfolioManager(
                            activos_filtrados,
                            token_acceso,
                            fecha_desde,
                            fecha_hasta,
                            capital=capital_inicial
                        )
                        if manager.load_data():
                            portfolio_result = manager.compute_portfolio(strategy=metodo, target_return=target_return)
                            if portfolio_result:
                                st.success("✅ Optimización Diaria completada")
                                mostrar_resultados_optimizacion(portfolio_result, capital_inicial, manager)

            except Exception as e:
                st.error(f"Error en la optimización: {str(e)}")
    
    # Configuración inicial
    col1, col2 = st.columns(2)
    
    with col1:
        modo_optimizacion = st.selectbox(
            "Modo de Optimización:",
            options=['Rebalanceo', 'Optimización desde Cero'],
            format_func=lambda x: {
                'Rebalanceo': 'Rebalanceo (Datos Diarios IOL)',
                'Optimización desde Cero': 'Optimización desde Cero (Intradía y Diario)'
            }[x]
        )
    
    with col2:
        capital_inicial = st.number_input(
            "Capital Inicial (ARS):",
            min_value=1000.0, max_value=1e9, value=100000.0, step=1000.0,
            help="Monto inicial para la optimización. En modo Rebalanceo, se usa el capital actual del portafolio."
        )
    
    # Configuración específica por modo
    if modo_optimizacion == 'Optimización desde Cero':
        col3, col4 = st.columns(2)
        with col3:
            frecuencia_datos = st.selectbox(
                "Frecuencia de Datos:",
                options=['Diario', 'Intradía'],
                format_func=lambda x: {
                    'Diario': 'Datos Diarios (IOL)',
                    'Intradía': 'Datos Intradía (yfinance)'
                }[x]
            )
        
        with col4:
            if frecuencia_datos == 'Intradía':
                st.info("Para acciones y cedears, se agregará automáticamente el sufijo .BA")
                tipos_disponibles = ['Acciones', 'Cedears']
            else:
                tipos_disponibles = sorted(set([a['tipo'] for a in activos_para_optimizacion if a.get('tipo')]))
            
            tipo_seleccionado = st.selectbox(
                "Filtrar por tipo de activo:",
                options=['Todos'] + tipos_disponibles,
                key="opt_tipo_activo",
                format_func=lambda x: "Todos" if x == 'Todos' else x
            )
            
            if tipo_seleccionado != 'Todos':
                activos_filtrados = [a for a in activos_para_optimizacion if a.get('tipo') == tipo_seleccionado]
            else:
                activos_filtrados = activos_para_optimizacion
    else:  # Rebalanceo
        activos_filtrados = activos_para_optimizacion
        frecuencia_datos = 'Diario'

    # Resto de la configuración común
    fecha_desde = st.session_state.fecha_desde
    fecha_hasta = st.session_state.fecha_hasta
    
    st.info(f"Analizando {len(activos_filtrados)} activos desde {fecha_desde} hasta {fecha_hasta}")
    
    # Configuración de optimización
    metodos_optimizacion = {
        'Maximizar Sharpe (Markowitz)': 'max_sharpe',
        'Mínima Varianza L1': 'min-variance-l1',
        'Mínima Varianza L2': 'min-variance-l2',
        'Pesos Iguales': 'equi-weight',
        'Solo Posiciones Largas': 'long-only',
        'Markowitz con Retorno Objetivo': 'markowitz-target'
    }
    metodo_ui = st.selectbox(
        "Método de Optimización de Portafolio:",
        options=list(metodos_optimizacion.keys()),
        key="opt_metodo_optimizacion"
    )
    metodo = metodos_optimizacion[metodo_ui]

    # Pedir retorno objetivo solo si corresponde
    target_return = None
    if metodo == 'markowitz-target':
        target_return = st.number_input(
            "Retorno Objetivo (anual, decimal, ej: 0.15 para 15%):",
            min_value=0.01, value=0.10, step=0.01, format="%.4f",
            help="No hay máximo. Si el retorno es muy alto, la simulación puede no converger."
        )

    show_frontier = st.checkbox("Mostrar Frontera Eficiente", value=True)

    # Configuración de ejecución
    scheduling_methods = {
        'TWAP (Time-Weighted)': 'twap',
        'VWAP (Volume-Weighted)': 'vwap'
    }
    scheduling_ui = st.selectbox(
        "Algoritmo de Scheduling:",
        options=list(scheduling_methods.keys()),
        key="opt_scheduling_algo"
    )
    scheduling = scheduling_methods[scheduling_ui]

    order_types = {
        'Market Order': 'mo',
        'Limit Order': 'lo',
        'Peg Order': 'peg',
        'Float Peg': 'float_peg',
        'Fill or Kill': 'fok',
        'Immediate or Cancel': 'ioc'
    }
    order_type_ui = st.selectbox(
        "Tipo de Orden:",
        options=list(order_types.keys()),
        key="opt_tipo_orden"
    )
    order_type = order_types[order_type_ui]

    # Widget TradingView
    try:
        from streamlit_tradingview_ta import TradingViewWidget
        st.subheader("Gráfico interactivo TradingView")
        TradingViewWidget(
            symbol="NASDAQ:AAPL",  # Cambia por símbolo seleccionado
            interval="D",
            theme="dark",
            studies=["MACD@tv-basicstudies", "RSI@tv-basicstudies"],
            height=600,
            width="100%",
        )
    except ImportError:
        st.info("Instala 'streamlit-tradingview-widget' para habilitar el gráfico TradingView.")

    # Botones de acción
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ejecutar_optimizacion = st.button("🚀 Ejecutar Optimización", type="primary")
    with col2:
        ejecutar_frontier = st.button("📈 Calcular Frontera Eficiente")
    with col3:
        mostrar_cauciones = st.button("💸 Ver Cauciones Todos los Plazos")
    with col4:
        comparar_opt = st.checkbox("Comparar Actual vs Aleatoria", value=False, help="Compara la optimización sobre tu portafolio y sobre un universo aleatorio de activos.")

    # Ejecución de optimización
    if ejecutar_optimizacion:
        with st.spinner("Ejecutando optimización..."):
            try:
                # Configuración común para ambos modos
                if modo_optimizacion == 'Rebalanceo':
                    # Usar datos diarios de IOL y el capital actual del portafolio
                    activos_para_opt = activos_filtrados
                    manager = PortfolioManager(
                        activos_para_opt,
                        token_acceso,
                        fecha_desde,
                        fecha_hasta,
                        capital=capital_inicial
                    )
                    if manager.load_data():
                        portfolio_result = manager.compute_portfolio(strategy=metodo, target_return=target_return)
                        if portfolio_result:
                            st.success("✅ Optimización de Rebalanceo completada")
                            mostrar_resultados_optimizacion(portfolio_result, capital_inicial, manager)
                else:  # Optimización desde Cero
                    if frecuencia_datos == 'Intradía':
                        # Usar yfinance para acciones y cedears
                        import yfinance as yf
                        activos_yf = []
                        for activo in activos_filtrados:
                            tipo = activo.get('tipo')
                            if tipo in ['Acciones', 'Cedears']:
                                simbolo = activo.get('simbolo')
                                if simbolo:
                                    # Agregar sufijo .BA para acciones y cedears
                                    activos_yf.append({
                                        'simbolo': f"{simbolo}.BA",
                                        'tipo': tipo
                                    })
                        if activos_yf:
                            # Obtener datos intradía
                            data_yf = yf.download(
                                [a['simbolo'] for a in activos_yf],
                                start=fecha_desde,
                                end=fecha_hasta,
                                interval="1h"  # Intervalo intradía
                            )
                            if not data_yf.empty:
                                # Convertir datos yfinance a formato compatible
                                activos_formato = []
                                for activo in activos_yf:
                                    simbolo = activo['simbolo']
                                    precios = data_yf['Close'][simbolo]
                                    if not precios.empty:
                                        activos_formato.append({
                                            'simbolo': simbolo,
                                            'precios': precios
                                        })
                                if activos_formato:
                                    manager = PortfolioManager(
                                        activos_formato,
                                        token_acceso,
                                        fecha_desde,
                                        fecha_hasta,
                                        capital=capital_inicial
                                    )
                                    if manager.load_data():
                                        portfolio_result = manager.compute_portfolio(strategy=metodo, target_return=target_return)
                                        if portfolio_result:
                                            st.success("✅ Optimización Intradía completada")
                                            mostrar_resultados_optimizacion(portfolio_result, capital_inicial, manager)
                    else:  # Diario
                        # Usar datos diarios de IOL
                        manager = PortfolioManager(
                            activos_filtrados,
                            token_acceso,
                            fecha_desde,
                            fecha_hasta,
                            capital=capital_inicial
                        )
                        if manager.load_data():
                            portfolio_result = manager.compute_portfolio(strategy=metodo, target_return=target_return)
                            if portfolio_result:
                                st.success("✅ Optimización Diaria completada")
                                mostrar_resultados_optimizacion(portfolio_result, capital_inicial, manager)

            except Exception as e:
                st.error(f"Error en la optimización: {str(e)}")
    
    # Configuración inicial
    col1, col2 = st.columns(2)
    
    with col1:
        modo_optimizacion = st.selectbox(
            "Modo de Optimización:",
            options=['Rebalanceo', 'Optimización desde Cero'],
            format_func=lambda x: {
                'Rebalanceo': 'Rebalanceo (Datos Diarios IOL)',
                'Optimización desde Cero': 'Optimización desde Cero (Intradía y Diario)'
            }[x]
        )
    
    with col2:
        capital_inicial = st.number_input(
            "Capital Inicial (ARS):",
            min_value=1000.0, max_value=1e9, value=100000.0, step=1000.0,
            help="Monto inicial para la optimización. En modo Rebalanceo, se usa el capital actual del portafolio."
        )
    
    # Configuración específica por modo
    if modo_optimizacion == 'Optimización desde Cero':
        col3, col4 = st.columns(2)
        with col3:
            frecuencia_datos = st.selectbox(
                "Frecuencia de Datos:",
                options=['Diario', 'Intradía'],
                format_func=lambda x: {
                    'Diario': 'Datos Diarios (IOL)',
                    'Intradía': 'Datos Intradía (yfinance)'
                }[x]
            )
        
        with col4:
            if frecuencia_datos == 'Intradía':
                st.info("Para acciones y cedears, se agregará automáticamente el sufijo .BA")
                tipos_disponibles = ['Acciones', 'Cedears']
            else:
                tipos_disponibles = sorted(set([a['tipo'] for a in activos_para_optimizacion if a.get('tipo')]))
            
            tipo_seleccionado = st.selectbox(
                "Filtrar por tipo de activo:",
                options=['Todos'] + tipos_disponibles,
                key="opt_tipo_activo",
                format_func=lambda x: "Todos" if x == 'Todos' else x
            )
            
            if tipo_seleccionado != 'Todos':
                activos_filtrados = [a for a in activos_para_optimizacion if a.get('tipo') == tipo_seleccionado]
            else:
                activos_filtrados = activos_para_optimizacion
    else:  # Rebalanceo
        activos_filtrados = activos_para_optimizacion
        frecuencia_datos = 'Diario'

    # Resto de la configuración común
    fecha_desde = st.session_state.fecha_desde
    fecha_hasta = st.session_state.fecha_hasta
    
    st.info(f"Analizando {len(activos_filtrados)} activos desde {fecha_desde} hasta {fecha_hasta}")
    
    if not activos_filtrados:
        st.warning("No se encontraron activos con información de mercado válida para optimizar.")
        return
    
    # --- Métodos avanzados de optimización ---
    metodos_optimizacion = {
        'Maximizar Sharpe (Markowitz)': 'max_sharpe',
        'Mínima Varianza L1': 'min-variance-l1',
        'Mínima Varianza L2': 'min-variance-l2',
        'Pesos Iguales': 'equi-weight',
        'Solo Posiciones Largas': 'long-only',
        'Markowitz con Retorno Objetivo': 'markowitz-target'
    }
    metodo_ui = st.selectbox(
        "Método de Optimización de Portafolio:",
        options=list(metodos_optimizacion.keys()),
        key="opt_metodo_optimizacion"
    )
    metodo = metodos_optimizacion[metodo_ui]

    # Pedir retorno objetivo solo si corresponde
    target_return = None
    if metodo == 'markowitz-target':
        target_return = st.number_input(
            "Retorno Objetivo (anual, decimal, ej: 0.15 para 15%):",
            min_value=0.01, value=0.10, step=0.01, format="%.4f",
            help="No hay máximo. Si el retorno es muy alto, la simulación puede no converger."
        )

    show_frontier = st.checkbox("Mostrar Frontera Eficiente", value=True)

    # --- Scheduling y tipo de orden ---
    scheduling_methods = {
        'TWAP (Time-Weighted)': 'twap',
        'VWAP (Volume-Weighted)': 'vwap'
    }
    scheduling_ui = st.selectbox(
        "Algoritmo de Scheduling:",
        options=list(scheduling_methods.keys()),
        key="opt_scheduling_algo"
    )
    scheduling = scheduling_methods[scheduling_ui]

    order_types = {
        'Market Order': 'mo',
        'Limit Order': 'lo',
        'Peg Order': 'peg',
        'Float Peg': 'float_peg',
        'Fill or Kill': 'fok',
        'Immediate or Cancel': 'ioc'
    }
    order_type_ui = st.selectbox(
        "Tipo de Orden:",
        options=list(order_types.keys()),
        key="opt_tipo_orden"
    )
    order_type = order_types[order_type_ui]

    # Widget TradingView (requiere streamlit-tradingview-widget instalado)
    try:
        from streamlit_tradingview_ta import TradingViewWidget
        st.subheader("Gráfico interactivo TradingView")
        TradingViewWidget(
            symbol="NASDAQ:AAPL",  # Cambia por símbolo seleccionado
            interval="D",
            theme="dark",
            studies=["MACD@tv-basicstudies", "RSI@tv-basicstudies"],
            height=600,
            width="100%",
        )
    except ImportError:
        st.info("Instala 'streamlit-tradingview-widget' para habilitar el gráfico TradingView.")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ejecutar_optimizacion = st.button("🚀 Ejecutar Optimización", type="primary")
    with col2:
        ejecutar_frontier = st.button("📈 Calcular Frontera Eficiente")
    with col3:
        mostrar_cauciones = st.button("💸 Ver Cauciones Todos los Plazos")
    with col4:
        comparar_opt = st.checkbox("Comparar Actual vs Aleatoria", value=False, help="Compara la optimización sobre tu portafolio y sobre un universo aleatorio de activos.")

    def obtener_cotizaciones_cauciones(bearer_token):
        import requests
        import pandas as pd
        url = "https://api.invertironline.com/api/v2/Cotizaciones/cauciones/argentina/Todos"
        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'Accept': 'application/json'
        }
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                cotizaciones = data.get('cotizaciones', [])
                df = pd.DataFrame(cotizaciones)
                
                # Crear gráfico de precios y volumen
                fig = go.Figure()
                
                # Agregar precios
                for plazo in range(1, 11):
                    columna = f'precio{plazo}'
                    if columna in df.columns:
                        fig.add_trace(go.Scatter(
                            x=df['fecha'],
                            y=df[columna],
                            name=f'Plazo {plazo} días',
                            mode='lines'
                        ))
                
                # Agregar volumen en segundo eje y
                fig.add_trace(go.Bar(
                    x=df['fecha'],
                    y=df['volumen'],
                    name='Volumen',
                    yaxis='y2',
                    opacity=0.3
                ))
                
                total_ejecutado = df['volumen'].sum()
                precio_promedio = df['precio1'].mean()
                
                return fig, total_ejecutado, precio_promedio
            else:
                st.error(f"Error en la API: {response.status_code}")
                return None, 0, 0
        except Exception as e:
            st.error(f"Error: {str(e)}")
            return None, 0, 0

    if ejecutar_optimizacion:
        with st.spinner("Ejecutando optimización..."):
            try:
                # Configuración común para ambos modos
                if modo_optimizacion == 'Rebalanceo':
                    # Usar datos diarios de IOL y el capital actual del portafolio
                    activos_para_opt = activos_filtrados
                    manager = PortfolioManager(
                        activos_para_opt,
                        token_acceso,
                        fecha_desde,
                        fecha_hasta,
                        capital=capital_inicial
                    )
                    if manager.load_data():
                        portfolio_result = manager.compute_portfolio(strategy=metodo, target_return=target_return)
                        if portfolio_result:
                            st.success("✅ Optimización de Rebalanceo completada")
                            mostrar_resultados_optimizacion(portfolio_result, capital_inicial, manager)
                else:  # Optimización desde Cero
                    if frecuencia_datos == 'Intradía':
                        # Usar yfinance para acciones y cedears
                        import yfinance as yf
                        activos_yf = []
                        for activo in activos_filtrados:
                            tipo = activo.get('tipo')
                            if tipo in ['Acciones', 'Cedears']:
                                simbolo = activo.get('simbolo')
                                if simbolo:
                                    # Agregar sufijo .BA para acciones y cedears
                                    activos_yf.append({
                                        'simbolo': f"{simbolo}.BA",
                                        'tipo': tipo
                                    })
                        if activos_yf:
                            # Obtener datos intradía
                            data_yf = yf.download(
                                [a['simbolo'] for a in activos_yf],
                                start=fecha_desde,
                                end=fecha_hasta,
                                interval="1h"  # Intervalo intradía
                            )
                            if not data_yf.empty:
                                # Convertir datos yfinance a formato compatible
                                activos_formato = []
                                for activo in activos_yf:
                                    simbolo = activo['simbolo']
                                    precios = data_yf['Close'][simbolo]
                                    if not precios.empty:
                                        activos_formato.append({
                                            'simbolo': simbolo,
                                            'precios': precios
                                        })
                                if activos_formato:
                                    manager = PortfolioManager(
                                        activos_formato,
                                        token_acceso,
                                        fecha_desde,
                                        fecha_hasta,
                                        capital=capital_inicial
                                    )
                                    if manager.load_data():
                                        portfolio_result = manager.compute_portfolio(strategy=metodo, target_return=target_return)
                                        if portfolio_result:
                                            st.success("✅ Optimización Intradía completada")
                                            mostrar_resultados_optimizacion(portfolio_result, capital_inicial, manager)
                    else:  # Diario
                        # Usar datos diarios de IOL
                        manager = PortfolioManager(
                            activos_filtrados,
                            token_acceso,
                            fecha_desde,
                            fecha_hasta,
                            capital=capital_inicial
                        )
                        if manager.load_data():
                            portfolio_result = manager.compute_portfolio(strategy=metodo, target_return=target_return)
                            if portfolio_result:
                                st.success("✅ Optimización Diaria completada")
                                mostrar_resultados_optimizacion(portfolio_result, capital_inicial, manager)

            except Exception as e:
                st.error(f"Error en la optimización: {str(e)}")
    
    # Configuración inicial
    col1, col2 = st.columns(2)
    
    with col1:
        modo_optimizacion = st.selectbox(
            "Modo de Optimización:",
            options=['Rebalanceo', 'Optimización desde Cero'],
            format_func=lambda x: {
                'Rebalanceo': 'Rebalanceo (Datos Diarios IOL)',
                'Optimización desde Cero': 'Optimización desde Cero (Intradía y Diario)'
            }[x]
        )
    
    with col2:
        capital_inicial = st.number_input(
            "Capital Inicial (ARS):",
            min_value=1000.0, max_value=1e9, value=100000.0, step=1000.0,
            help="Monto inicial para la optimización. En modo Rebalanceo, se usa el capital actual del portafolio."
        )
    
    # Configuración específica por modo
    if modo_optimizacion == 'Optimización desde Cero':
        col3, col4 = st.columns(2)
        with col3:
            frecuencia_datos = st.selectbox(
                "Frecuencia de Datos:",
                options=['Diario', 'Intradía'],
                format_func=lambda x: {
                    'Diario': 'Datos Diarios (IOL)',
                    'Intradía': 'Datos Intradía (yfinance)'
                }[x]
            )
        
        with col4:
            if frecuencia_datos == 'Intradía':
                st.info("Para acciones y cedears, se agregará automáticamente el sufijo .BA")
                tipos_disponibles = ['Acciones', 'Cedears']
            else:
                tipos_disponibles = sorted(set([a['tipo'] for a in activos_para_optimizacion if a.get('tipo')]))
            
            tipo_seleccionado = st.selectbox(
                "Filtrar por tipo de activo:",
                options=['Todos'] + tipos_disponibles,
                key="opt_tipo_activo",
                format_func=lambda x: "Todos" if x == 'Todos' else x
            )
            
            if tipo_seleccionado != 'Todos':
                activos_filtrados = [a for a in activos_para_optimizacion if a.get('tipo') == tipo_seleccionado]
            else:
                activos_filtrados = activos_para_optimizacion
    else:  # Rebalanceo
        activos_filtrados = activos_para_optimizacion
        frecuencia_datos = 'Diario'

    # Resto de la configuración común
    fecha_desde = st.session_state.fecha_desde
    fecha_hasta = st.session_state.fecha_hasta
    
    st.info(f"Analizando {len(activos_filtrados)} activos desde {fecha_desde} hasta {fecha_hasta}")
    
    if not activos_para_optimizacion:
        st.warning("No se encontraron activos con información de mercado válida para optimizar.")
        return
    
    fecha_desde = st.session_state.fecha_desde
    fecha_hasta = st.session_state.fecha_hasta
    
    st.info(f"Analizando {len(activos_para_optimizacion)} activos desde {fecha_desde} hasta {fecha_hasta}")

    # --- Función de selección aleatoria de activos respetando el capital ---
    def seleccion_aleatoria_activos_con_capital(activos, token, capital):
        '''
        Selecciona activos aleatorios de la lista sin superar el capital, usando el precio actual de cada activo.
        Retorna lista de activos seleccionados y el total invertido.
        '''
        import random
        random.shuffle(activos)
        seleccionados = []
        capital_restante = capital
        total_invertido = 0
        for activo in activos:
            simbolo = activo.get('simbolo')
            mercado = activo.get('mercado')
            if not simbolo or not mercado:
                continue
            precio = obtener_precio_actual(token, mercado, simbolo)
            if precio is not None and precio > 0 and precio <= capital_restante:
                seleccionados.append({'simbolo': simbolo, 'mercado': mercado, 'precio': precio})
                capital_restante -= precio
                total_invertido += precio
            if capital_restante < 1:
                break
        return seleccionados, total_invertido
    
    # Configuración de selección de universo y optimización
    col_sel, col1, col2, col3 = st.columns(4)

    with col_sel:
        metodo_seleccion = st.selectbox(
            "Método de Selección de Activos:",
            options=['actual', 'aleatoria'],
            format_func=lambda x: {
                'actual': 'Portafolio actual',
                'aleatoria': 'Selección aleatoria'
            }[x]
        )

    # Mostrar input de capital y filtro de tipo de activo solo si corresponde
    if metodo_seleccion == 'aleatoria':
        # Filtro de tipo de activo solo en aleatoria
        tipos_disponibles = sorted(set([a['tipo'] for a in activos_para_optimizacion if a.get('tipo')]))
        tipo_seleccionado = st.selectbox(
            "Filtrar por tipo de activo:",
            options=['Todos'] + tipos_disponibles,
            key="opt_tipo_activo_2",
            format_func=lambda x: "Todos" if x == 'Todos' else x
        )
        if tipo_seleccionado != 'Todos':
            activos_filtrados = [a for a in activos_para_optimizacion if a.get('tipo') == tipo_seleccionado]
        else:
            activos_filtrados = activos_para_optimizacion
            
        capital_inicial = st.number_input(
            "Capital Inicial para Optimización (ARS):",
            min_value=1000.0, max_value=1e9, value=100000.0, step=1000.0,
            help="El monto máximo a invertir en la selección aleatoria de activos",
            key="opt_capital_aleatoria"
        )
    else:
        activos_filtrados = activos_para_optimizacion
        capital_inicial = None

    # --- Métodos avanzados de optimización ---
    metodos_optimizacion = {
        'Maximizar Sharpe (Markowitz)': 'max_sharpe',
        'Mínima Varianza L1': 'min-variance-l1',
        'Mínima Varianza L2': 'min-variance-l2',
        'Pesos Iguales': 'equi-weight',
        'Solo Posiciones Largas': 'long-only',
        'Markowitz con Retorno Objetivo': 'markowitz-target'
    }
    metodo_ui = st.selectbox(
        "Método de Optimización de Portafolio:",
        options=list(metodos_optimizacion.keys()),
        key="opt_metodo_optimizacion"
    )
    metodo = metodos_optimizacion[metodo_ui]

    # Pedir retorno objetivo solo si corresponde
    target_return = None
    if metodo == 'markowitz-target':
        target_return = st.number_input(
            "Retorno Objetivo (anual, decimal, ej: 0.15 para 15%):",
            min_value=0.01, value=0.10, step=0.01, format="%.4f",
            help="No hay máximo. Si el retorno es muy alto, la simulación puede no converger."
        )

    show_frontier = st.checkbox("Mostrar Frontera Eficiente", value=True)

    # --- Scheduling y tipo de orden ---
    scheduling_methods = {
        'TWAP (Time-Weighted)': 'twap',
        'VWAP (Volume-Weighted)': 'vwap'
    }
    scheduling_ui = st.selectbox(
        "Algoritmo de Scheduling:",
        options=list(scheduling_methods.keys()),
        key="opt_scheduling_algo"
    )
    scheduling = scheduling_methods[scheduling_ui]

    order_types = {
        'Market Order': 'mo',
        'Limit Order': 'lo',
        'Peg Order': 'peg',
        'Float Peg': 'float_peg',
        'Fill or Kill': 'fok',
        'Immediate or Cancel': 'ioc'
    }
    order_type_ui = st.selectbox(
        "Tipo de Orden:",
        options=list(order_types.keys()),
        key="opt_tipo_orden"
    )
    order_type = order_types[order_type_ui]

    # Input de capital inicial
    capital_inicial = st.number_input(
        "Capital Inicial para Optimización (ARS):",
        min_value=1000.0, max_value=1e9, value=100000.0, step=1000.0,
        help="El monto máximo a invertir en la selección y optimización de activos"
    )

    # Widget TradingView (requiere streamlit-tradingview-widget instalado)
    try:
        from streamlit_tradingview_ta import TradingViewWidget
        st.subheader("Gráfico interactivo TradingView")
        TradingViewWidget(
            symbol="NASDAQ:AAPL",  # Cambia por símbolo seleccionado
            interval="D",
            theme="dark",
            studies=["MACD@tv-basicstudies", "RSI@tv-basicstudies"],
            height=600,
            width="100%",
        )
    except ImportError:
        st.info("Instala 'streamlit-tradingview-widget' para habilitar el gráfico TradingView.")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ejecutar_optimizacion = st.button("🚀 Ejecutar Optimización", type="primary")
    with col2:
        ejecutar_frontier = st.button("📈 Calcular Frontera Eficiente")
    with col3:
        mostrar_cauciones = st.button("💸 Ver Cauciones Todos los Plazos")
    with col4:
        comparar_opt = st.checkbox("Comparar Actual vs Aleatoria", value=False, help="Compara la optimización sobre tu portafolio y sobre un universo aleatorio de activos.")

    def obtener_cotizaciones_cauciones(bearer_token):
        import requests
        import pandas as pd
        url = "https://api.invertironline.com/api/v2/Cotizaciones/cauciones/argentina/Todos"
        # ... (resto del código de la función)
        fig = go.Figure()
        # ... (resto del código de la función)
        fig.update_layout(
            yaxis=dict(title="Volumen"),
            yaxis2=dict(title="Precio", overlaying="y", side="right"),
            legend=dict(orientation="h")
        )
        return fig, total_ejecutado, precio_promedio

    if ejecutar_optimizacion:
        with st.spinner("Ejecutando optimización..."):
            try:
                # Configuración común para ambos modos
                if modo_optimizacion == 'Rebalanceo':
                    # Usar datos diarios de IOL y el capital actual del portafolio
                    activos_para_opt = activos_filtrados
                    manager = PortfolioManager(
                        activos_para_opt,
                        token_acceso,
                        fecha_desde,
                        fecha_hasta,
                        capital=capital_inicial
                    )
                    if manager.load_data():
                        portfolio_result = manager.compute_portfolio(strategy=metodo, target_return=target_return)
                        if portfolio_result:
                            st.success("✅ Optimización de Rebalanceo completada")
                            mostrar_resultados_optimizacion(portfolio_result, capital_inicial, manager)
                else:  # Optimización desde Cero
                    if frecuencia_datos == 'Intradía':
                        # Usar yfinance para acciones y cedears
                        import yfinance as yf
                        activos_yf = []
                        for activo in activos_filtrados:
                            tipo = activo.get('tipo')
                            if tipo in ['Acciones', 'Cedears']:
                                simbolo = activo.get('simbolo')
                                if simbolo:
                                    # Agregar sufijo .BA para acciones y cedears
                                    activos_yf.append({
                                        'simbolo': f"{simbolo}.BA",
                                        'tipo': tipo
                                    })
                        if activos_yf:
                            # Obtener datos intradía
                            data_yf = yf.download(
                                [a['simbolo'] for a in activos_yf],
                                start=fecha_desde,
                                end=fecha_hasta,
                                interval="1h"  # Intervalo intradía
                            )
                            if not data_yf.empty:
                                # Convertir datos yfinance a formato compatible
                                activos_formato = []
                                for activo in activos_yf:
                                    simbolo = activo['simbolo']
                                    precios = data_yf['Close'][simbolo]
                                    if not precios.empty:
                                        activos_formato.append({
                                            'simbolo': simbolo,
                                            'precios': precios
                                        })
                                if activos_formato:
                                    manager = PortfolioManager(
                                        activos_formato,
                                        token_acceso,
                                        fecha_desde,
                                        fecha_hasta,
                                        capital=capital_inicial
                                    )
                                    if manager.load_data():
                                        portfolio_result = manager.compute_portfolio(strategy=metodo, target_return=target_return)
                                        if portfolio_result:
                                            st.success("✅ Optimización Intradía completada")
                                            mostrar_resultados_optimizacion(portfolio_result, capital_inicial, manager)
                    else:  # Diario
                        # Usar datos diarios de IOL
                        manager = PortfolioManager(
                            activos_filtrados,
                            token_acceso,
                            fecha_desde,
                            fecha_hasta,
                            capital=capital_inicial
                        )
                        if manager.load_data():
                            portfolio_result = manager.compute_portfolio(strategy=metodo, target_return=target_return)
                            if portfolio_result:
                                st.success("✅ Optimización Diaria completada")
                                mostrar_resultados_optimizacion(portfolio_result, capital_inicial, manager)

                                try:
                                    st.plotly_chart(fig_frontier, use_container_width=True)
                                except Exception as e:
                                    st.warning(f"No se pudo calcular la frontera eficiente: {e}")
                                
                                # Simulación de ejecución
                                st.markdown("---")
                                st.subheader("Simulación de Ejecución Algorítmica")
                                volumen_total = int(capital_inicial // portfolio_result.price if hasattr(portfolio_result, 'price') and portfolio_result.price > 0 else capital_inicial // 100)
                                fig_exec, total_exec, avg_price = simular_ejecucion(volumen_total, scheduling, order_type)
                                st.plotly_chart(fig_exec, use_container_width=True)
                                st.info(f"**Volumen Total Ejecutado:** {total_exec}\n\n**Precio Promedio de Ejecución:** {avg_price:.2f}")
                            else:
                                st.error("❌ Error en la optimización: No se pudo calcular el portafolio")
                        else:
                            st.error("❌ No se pudieron cargar los datos históricos")
                    
            except Exception as e:
                st.error(f"❌ Error durante la optimización: {str(e)}")
    
    if ejecutar_frontier and show_frontier:
        with st.spinner("Calculando frontera eficiente..."):
            try:
                manager_inst = PortfolioManager(activos_para_optimizacion, token_acceso, fecha_desde, fecha_hasta)
                
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

class output:
    def __init__(self, returns, notional):
        self.returns = returns
        self.notional = notional
        self.weights = None
        self.dataframe_allocation = None
        
    def get_weights(self):
        return self.weights
        
    def get_allocation(self):
        return self.dataframe_allocation

def portfolio_variance(weights, cov_matrix):
    """Calcula la varianza de un portafolio dado los pesos y la matriz de covarianza."""
    return np.dot(weights.T, np.dot(cov_matrix, weights))

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
                
        elif portfolio_type == 'random-rebalance':
            # Método de optimización y rebalanceo aleatorio
            return self._random_rebalance_portfolio()
            
        # Si constraints no está definido, lanzar error
        if 'constraints' not in locals():
            raise ValueError(f"Tipo de portafolio no soportado o constraints no definidos para: {portfolio_type}")

        # Optimización general de varianza mínima
        result = op.minimize(
            lambda x: portfolio_variance(x, self.cov_matrix),
            x0=np.ones(n_assets)/n_assets,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        return self._create_output(result.x)
        
    def _random_rebalance_portfolio(self):
        """Implementa el método de optimización y rebalanceo aleatorio"""
        # Generar pesos aleatorios que sumen 1
        weights = np.random.dirichlet(np.ones(len(self.rics)), size=1)[0]
        
        # Asegurar que los pesos sean positivos y sumen 1
        weights = np.abs(weights)
        weights /= weights.sum()
        
        # Calcular retornos del portafolio
        portfolio_returns = (self.returns * weights).sum(axis=1)
        
        # Crear objeto de salida
        output_obj = output(portfolio_returns, self.notional)
        output_obj.weights = weights
        output_obj.dataframe_allocation = pd.DataFrame({
            'rics': list(self.returns.columns),
            'weights': weights,
            'volatilities': self.returns.std().values,
            'returns': self.returns.mean().values
        })
        
        return output_obj

    def _create_output(self, weights):
        """Crea un objeto de salida con los pesos y métricas del portafolio"""
        # Calcular retornos del portafolio
        portfolio_returns = (self.returns * weights).sum(axis=1)
        
        # Crear objeto de salida
        output_obj = output(portfolio_returns, self.notional)
        output_obj.weights = weights
        output_obj.dataframe_allocation = pd.DataFrame({
            'rics': list(self.returns.columns),
            'weights': weights,
            'volatilities': self.returns.std().values,
            'returns': self.returns.mean().values
        })
        
        return output_obj


def mostrar_estado_cuenta(token_acceso, id_cliente):
    """Muestra el estado de cuenta del cliente."""
    try:
        st.markdown("### 📝 Estado de Cuenta")
        
        with st.spinner("Obteniendo estado de cuenta..."):
            estado_cuenta = obtener_estado_cuenta(token_acceso, id_cliente)
            
            if not estado_cuenta:
                st.warning("No se pudo obtener el estado de cuenta")
                return
                
            # Mostrar saldos
            st.markdown("### 💰 Saldos")
            
            if 'cuentas' in estado_cuenta and estado_cuenta['cuentas']:
                for cuenta in estado_cuenta['cuentas']:
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.metric("Saldo Disponible", f"${float(cuenta.get('disponible', 0)):,.2f}")
                    with col2:
                        st.metric("Saldo Total", f"${float(cuenta.get('total', 0)):,.2f}")
            
            # Mostrar últimas operaciones
            st.markdown("### 📜 Últimas Operaciones")
            
            if 'ultimasOperaciones' in estado_cuenta and estado_cuenta['ultimasOperaciones']:
                operaciones = []
                for op in estado_cuenta['ultimasOperaciones']:
                    operaciones.append({
                        'Fecha': op.get('fecha', ''),
                        'Tipo': op.get('tipo', ''),
                        'Especie': op.get('especie', ''),
                        'Cantidad': op.get('cantidad', 0),
                        'Precio': f"${float(op.get('precio', 0)):,.2f}",
                        'Monto': f"${float(op.get('monto', 0)):,.2f}",
                        'Estado': op.get('estado', '')
                    })
                
                if operaciones:
                    st.dataframe(
                        pd.DataFrame(operaciones),
                        use_container_width=True,
                        height=min(400, 50 + len(operaciones) * 30)
                    )
                else:
                    st.info("No hay operaciones recientes para mostrar")
            else:
                st.info("No hay información de operaciones disponibles")
                
    except Exception as e:
        st.error(f"Error al obtener el estado de cuenta: {str(e)}")


def mostrar_resumen_portafolio(portafolio, capital_total):
    """Muestra un resumen del portafolio actual.
    
    Args:
        portafolio: Diccionario con la información del portafolio
        capital_total: Capital total del portafolio (puede ser string o número)
    """
    try:
        if not portafolio or 'activos' not in portafolio or not portafolio['activos']:
            st.warning("El portafolio está vacío o no se pudo cargar")
            return
        
        st.markdown("### 📊 Resumen del Portafolio")
        
        # Asegurarse de que capital_total sea un número
        try:
            capital_total_num = float(capital_total) if capital_total is not None else 0
        except (ValueError, TypeError):
            capital_total_num = 0
        
        # Calcular métricas básicas
        activos = portafolio['activos']
        
        # Función segura para convertir a float
        def safe_float(value, default=0.0):
            try:
                return float(value) if value is not None else default
            except (ValueError, TypeError):
                return default
        
        total_invertido = sum(safe_float(a.get('valorizado', 0)) for a in activos)
        rendimiento_total = sum(safe_float(a.get('ganancia', 0)) for a in activos)
        rendimiento_porcentual = (rendimiento_total / total_invertido * 100) if total_invertido > 0 else 0
        
        # Mostrar métricas principales
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Capital Total", f"${capital_total_num:,.2f}")
        with col2:
            st.metric("Invertido", f"${total_invertido:,.2f}")
        with col3:
            st.metric("Rendimiento Total", 
                     f"${rendimiento_total:,.2f}", 
                     f"{rendimiento_porcentual:.2f}%")
        
        # Mostrar tabla de activos
        st.markdown("### 📋 Activos en Cartera")
        
        # Preparar datos para la tabla
        datos_activos = []
        for activo in activos:
            titulo = activo.get('titulo', {})
            datos_activos.append({
                'Símbolo': titulo.get('simbolo', 'N/A'),
                'Tipo': titulo.get('tipo', 'N/A'),
                'Mercado': titulo.get('mercado', 'N/A'),
                'Cantidad': activo.get('cantidad', 0),
                'Precio Promedio': activo.get('precioPromedio', 0),
                'Precio Actual': activo.get('precioActual', 0),
                'Inversión Total': activo.get('valorizado', 0),
                'Ganancia $': activo.get('ganancia', 0),
                'Ganancia %': activo.get('gananciaPorcentual', 0)
            })
        
        # Mostrar tabla con formato
        if datos_activos:
            df_activos = pd.DataFrame(datos_activos)
            
            # Aplicar formato a las columnas numéricas
            st.dataframe(
                df_activos.style.format({
                    'Precio Promedio': '${:,.2f}',
                    'Precio Actual': '${:,.2f}',
                    'Inversión Total': '${:,.2f}',
                    'Ganancia $': '${:,.2f}',
                    'Ganancia %': '{:.2f}%'
                }),
                use_container_width=True,
                height=min(400, 50 + len(datos_activos) * 30)  # Altura dinámica
            )
            
            # Mostrar distribución por tipo de activo
            st.markdown("### 📊 Distribución por Tipo de Activo")
            
            # Calcular totales por tipo
            distribucion = df_activos.groupby('Tipo')['Inversión Total'].sum().reset_index()
            
            if not distribucion.empty:
                # Crear gráfico de torta
                import plotly.express as px
                
                fig = px.pie(
                    distribucion,
                    values='Inversión Total',
                    names='Tipo',
                    title='Distribución del Portafolio por Tipo de Activo',
                    hover_data=['Inversión Total'],
                    labels={'Inversión Total': 'Inversión (USD)'}
                )
                
                # Mostrar gráfico
                st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar top 5 activos por rendimiento
            st.markdown("### 🏆 Top 5 Activos por Rentabilidad")
            
            top_rentables = df_activos.nlargest(5, 'Ganancia %')
            st.dataframe(
                top_rentables[['Símbolo', 'Tipo', 'Ganancia %', 'Ganancia $']]
                .style.format({
                    'Ganancia %': '{:.2f}%',
                    'Ganancia $': '${:,.2f}'
                }),
                use_container_width=True
            )
            
        else:
            st.info("No se encontraron activos para mostrar")
            
    except Exception as e:
        st.error(f"Error al mostrar el resumen del portafolio: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


def mostrar_resultados_optimizacion(portfolio_result, capital, portfolio_manager):
    """Muestra los resultados de la optimización del portafolio.
    
    Args:
        portfolio_result: Objeto con los resultados de la optimización
        capital: Capital total del portafolio
        portfolio_manager: Instancia de PortfolioManager con los datos del portafolio
    """
    try:
        # Obtener los pesos óptimos
        weights = portfolio_result.get_weights()
        allocation = portfolio_result.get_allocation()
        
        # Mostrar métricas principales
        st.subheader("📊 Resultados de la Optimización")
        
        # Calcular métricas
        returns = portfolio_result.returns
        annual_return = np.mean(returns) * 252
        annual_volatility = np.std(returns) * np.sqrt(252)
        sharpe_ratio = (annual_return - 0.04) / (annual_volatility + 1e-10)  # Evitar división por cero
        
        # Mostrar métricas en columnas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Retorno Anualizado", f"{annual_return*100:.2f}%")
        with col2:
            st.metric("Volatilidad Anual", f"{annual_volatility*100:.2f}%")
        with col3:
            st.metric("Ratio de Sharpe", f"{sharpe_ratio:.2f}")
        
        # Mostrar asignación de activos
        st.subheader("📊 Asignación de Activos")
        
        # Calcular montos en pesos
        allocation['monto_ars'] = (allocation['weights'] * capital).round(2)
        
        # Mostrar tabla con asignación
        st.dataframe(allocation[['rics', 'weights', 'monto_ars', 'returns', 'volatilities']]
                     .rename(columns={
                         'rics': 'Activo',
                         'weights': 'Peso',
                         'monto_ars': 'Monto (ARS)',
                         'returns': 'Retorno',
                         'volatilities': 'Volatilidad'
                     })
                     .style.format({
                         'Peso': '{:.2%}',
                         'Monto (ARS)': '${:,.2f}',
                         'Retorno': '{:.2%}',
                         'Volatilidad': '{:.2%}'
                     }))
        
        # Mostrar gráfico de torta de asignación
        st.subheader("📊 Distribución del Portafolio")
        
        import plotly.express as px
        
        # Crear gráfico de torta
        fig = px.pie(
            allocation, 
            values='weights', 
            names='rics',
            title='Distribución del Portafolio',
            hover_data=['monto_ars'],
            labels={'rics': 'Activo', 'weights': 'Peso'}
        )
        
        # Mostrar gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar evolución del portafolio
        st.subheader("📈 Evolución del Portafolio")
        
        # Calcular valor del portafolio a lo largo del tiempo
        if hasattr(portfolio_manager, 'returns'):
            portfolio_returns = portfolio_manager.returns.dot(weights)
            cumulative_returns = (1 + portfolio_returns).cumprod()
            
            # Crear DataFrame con la evolución
            portfolio_evolution = pd.DataFrame({
                'Fecha': portfolio_manager.returns.index,
                'Valor': cumulative_returns * capital
            })
            
            # Mostrar gráfico de evolución
            fig = px.line(
                portfolio_evolution, 
                x='Fecha', 
                y='Valor',
                title='Evolución del Valor del Portafolio',
                labels={'Valor': 'Valor (ARS)', 'Fecha': 'Fecha'}
            )
            
            # Agregar línea de referencia en el capital inicial
            fig.add_hline(y=capital, line_dash="dash", line_color="red", 
                         annotation_text=f"Capital Inicial: ${capital:,.2f}")
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar matriz de correlación
        st.subheader("📉 Matriz de Correlación")
        
        if hasattr(portfolio_manager, 'returns'):
            corr_matrix = portfolio_manager.returns.corr()
            
            # Crear mapa de calor
            fig = px.imshow(
                corr_matrix,
                text_auto=True,
                aspect="auto",
                color_continuous_scale='RdBu',
                zmin=-1,
                zmax=1,
                title='Matriz de Correlación entre Activos'
            )
            
            # Mejorar el diseño
            fig.update_layout(
                xaxis_title="Activos",
                yaxis_title="Activos",
                coloraxis_colorbar=dict(title="Correlación")
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar botones de acción
        st.subheader("⚡ Acciones")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Guardar Estrategia", help="Guarda la estrategia actual"):
                st.success("Estrategia guardada exitosamente")
        
        with col2:
            if st.button("📤 Exportar a Excel", help="Exporta los resultados a Excel"):
                # Crear un Excel en memoria
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    # Hoja de asignación
                    allocation.to_excel(writer, sheet_name='Asignación', index=False)
                    
                    # Hoja de evolución si existe
                    if 'portfolio_evolution' in locals():
                        portfolio_evolution.to_excel(writer, sheet_name='Evolución', index=False)
                    
                    # Hoja de correlación si existe
                    if 'corr_matrix' in locals():
                        corr_matrix.to_excel(writer, sheet_name='Correlación')
                
                # Crear botón de descarga
                st.download_button(
                    label="⬇️ Descargar Excel",
                    data=output.getvalue(),
                    file_name="optimizacion_portafolio.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col3:
            if st.button("🔄 Reoptimizar", help="Volver a ejecutar la optimización"):
                st.experimental_rerun()
    
    except Exception as e:
        st.error(f"Error al mostrar resultados: {str(e)}")

def mostrar_optimizacion_portafolio(token_acceso, id_cliente):
    st.markdown("### 🔄 Optimización de Portafolio")
    
    # Obtener portafolio actual
    with st.spinner("Obteniendo portafolio..."):
        portafolio = obtener_portafolio(token_acceso, id_cliente)
    
    # Inicializar variables
    activos_para_optimizacion = []
    activos_filtrados = []
    
    # Configuración de columnas
    col1, col2 = st.columns(2)
    
    with col1:
        # Selección de modo de optimización
        modo_optimizacion = st.radio(
            "Modo de Optimización:",
            options=['Rebalanceo', 'Optimización desde Cero'],
            format_func=lambda x: {
                'Rebalanceo': 'Rebalanceo de Composición Actual',
                'Optimización desde Cero': 'Optimización desde Cero'
            }[x],
            horizontal=True
        )
    
    with col2:
        # Input de capital inicial
        capital = st.number_input(
            "Capital Inicial (ARS):",
            min_value=1000.0, 
            max_value=1e9, 
            value=100000.0, 
            step=1000.0,
            help="Monto inicial para la optimización"
        )
    
    # Configuración específica por modo
    if modo_optimizacion == 'Rebalanceo':
        if not portafolio:
            st.warning("No se pudo obtener el portafolio del cliente")
            return
            
        activos_raw = portafolio.get('activos', [])
        if not activos_raw:
            st.warning("El portafolio está vacío")
            return
            
        # Extraer símbolos, mercados y tipos de activo
        for activo in activos_raw:
            titulo = activo.get('titulo', {})
            simbolo = titulo.get('simbolo')
            mercado = titulo.get('mercado')
            tipo = titulo.get('tipo')
            if simbolo:
                activos_para_optimizacion.append({
                    'simbolo': simbolo,
                    'mercado': mercado,
                    'tipo': tipo,
                    'cantidad': activo.get('cantidad', 0),
                    'precio_actual': activo.get('precioActual', 0)
                })
        
        activos_filtrados = activos_para_optimizacion
        frecuencia_datos = 'Diario'
        
    else:  # Optimización desde Cero
        # Configuración de frecuencia de datos
        frecuencia_datos = st.radio(
            "Fuente de Datos:",
            options=['Diario', 'Intradía'],
            format_func=lambda x: {
                'Diario': 'Datos Diarios (IOL - Todos los activos)',
                'Intradía': 'Datos Intradía (yfinance - Solo Acciones/Cedears)'
            }[x],
            horizontal=True
        )
        
        # Sección de selección de activos
        st.markdown("### 🎲 Selección de Activos")
        
        # Opción para seleccionar entre activos del portafolio o aleatorios
        tipo_seleccion = st.radio(
            "Tipo de selección:",
            options=['manual', 'aleatoria'],
            format_func=lambda x: {
                'manual': 'Selección Manual',
                'aleatoria': 'Selección Aleatoria'
            }[x],
            horizontal=True,
            key='tipo_seleccion_activos'
        )
        
        if tipo_seleccion == 'aleatoria':
            # Configuración de selección aleatoria
            st.markdown("#### Configuración de Selección Aleatoria")
            
            # Selección de clases de activos
            clases_activo = st.multiselect(
                "Seleccione las clases de activos:",
                options=['Acciones', 'Bonos', 'CEDEARs', 'Obligaciones Negociables', 'ADRs'],
                default=['Acciones', 'CEDEARs']
            )
            
            # Cantidad de activos por clase
            n_por_clase = st.slider("Activos por clase:", 1, 10, 3, 
                                  help="Número de activos aleatorios a seleccionar por cada clase")
            
            # Botón para generar selección aleatoria
            if st.button("🎲 Generar Selección Aleatoria"):
                with st.spinner("Generando selección de activos..."):
                    # Mapear nombres de clases al formato esperado
                    mapeo_clases = {
                        'Acciones': 'acciones',
                        'Bonos': 'bonos',
                        'CEDEARs': 'cedears',
                        'Obligaciones Negociables': 'obligaciones',
                        'ADRs': 'adrs'
                    }
                    
                    clases_mapeadas = [mapeo_clases[clase] for clase in clases_activo 
                                     if clase in mapeo_clases]
                    
                    if not clases_mapeadas:
                        st.warning("Seleccione al menos una clase de activo")
                    else:
                        activos_aleatorios = obtener_tickers_aleatorios_por_clase(
                            token_acceso, 
                            clases_mapeadas,
                            n_por_clase
                        )
                        
                        if not activos_aleatorios:
                            st.error("No se pudieron obtener activos aleatorios. Intente nuevamente.")
                        else:
                            # Actualizar precios actuales
                            for activo in activos_aleatorios:
                                try:
                                    precio = obtener_precio_actual(
                                        token_acceso,
                                        activo['mercado'],
                                        activo['simbolo']
                                    )
                                    activo['precio_actual'] = precio if precio else 0
                                except Exception as e:
                                    st.warning(f"Error al obtener precio de {activo['simbolo']}: {e}")
                                    activo['precio_actual'] = 0
                            
                            st.session_state.activos_aleatorios = activos_aleatorios
                            st.success(f"✅ Se generaron {len(activos_aleatorios)} activos aleatorios")
            
            # Mostrar tabla de activos seleccionados
            if 'activos_aleatorios' in st.session_state and st.session_state.activos_aleatorios:
                st.markdown("#### 📋 Activos Seleccionados")
                df_activos = pd.DataFrame(st.session_state.activos_aleatorios)
                
                # Formatear la visualización de precios
                df_display = df_activos[['simbolo', 'tipo', 'precio_actual']].copy()
                df_display['precio_actual'] = df_display['precio_actual'].apply(
                    lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A"
                )
                st.dataframe(df_display, use_container_width=True)
                
                # Opciones para confirmar o regenerar la selección
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Confirmar Selección"):
                        activos_filtrados = st.session_state.activos_aleatorios
                        st.success("Selección confirmada. Proceda con la optimización.")
                with col2:
                    if st.button("🔄 Regenerar Selección"):
                        del st.session_state.activos_aleatorios
                        st.experimental_rerun()
        
        else:  # Selección manual
            # Si hay portafolio, usarlo como base para selección
            if portafolio and 'activos' in portafolio:
                activos_raw = portafolio.get('activos', [])
                for activo in activos_raw:
                    titulo = activo.get('titulo', {})
                    simbolo = titulo.get('simbolo')
                    if simbolo:
                        activos_para_optimizacion.append({
                            'simbolo': simbolo,
                            'mercado': titulo.get('mercado'),
                            'tipo': titulo.get('tipo')
                        })
            
            # Filtrar por tipo de activo según la fuente de datos
            if frecuencia_datos == 'Intradía':
                st.info("ℹ️ Para acciones y cedears, se agregará automáticamente el sufijo .BA")
                tipos_disponibles = ['Acciones', 'Cedears']
                activos_para_optimizacion = [a for a in activos_para_optimizacion 
                                           if a.get('tipo') in tipos_disponibles]
            else:
                tipos_disponibles = sorted(set([a['tipo'] for a in activos_para_optimizacion 
                                              if a.get('tipo')]))
            
            # Selector de tipo de activo
            if tipos_disponibles:
                tipo_seleccionado = st.selectbox(
                    "Filtrar por tipo de activo:",
                    options=['Todos'] + tipos_disponibles,
                    key="opt_tipo_activo",
                    format_func=lambda x: "Todos" if x == 'Todos' else x
                )
                
                if tipo_seleccionado != 'Todos':
                    activos_filtrados = [a for a in activos_para_optimizacion 
                                       if a.get('tipo') == tipo_seleccionado]
                else:
                    activos_filtrados = activos_para_optimizacion
    
    # Mostrar resumen de activos seleccionados
    if activos_filtrados:
        st.success(f"✅ {len(activos_filtrados)} activos seleccionados para optimización")
        
        # Mostrar tabla con los activos seleccionados
        df_activos = pd.DataFrame([{
            'Símbolo': f"{a['simbolo']}{'.BA' if frecuencia_datos == 'Intradía' and a.get('tipo') in ['Acciones', 'Cedears'] else ''}",
            'Tipo': a.get('tipo', 'N/A'),
            'Mercado': a.get('mercado', 'N/A'),
            'Cantidad': a.get('cantidad', 'N/A') if modo_optimizacion == 'Rebalanceo' else 'N/A',
            'Precio Actual': f"${a.get('precio_actual', 0):.2f}" if a.get('precio_actual') else 'N/A'
        } for a in activos_filtrados])
        
        st.dataframe(df_activos, use_container_width=True, height=min(400, 50 + len(activos_filtrados) * 30))
    
    # Resto de la configuración común
    st.session_state.fecha_desde = fecha_desde = st.session_state.get('fecha_desde', date.today() - timedelta(days=365))
    st.session_state.fecha_hasta = fecha_hasta = st.session_state.get('fecha_hasta', date.today())
    
    st.info(f"Analizando {len(activos_filtrados)} activos desde {fecha_desde} hasta {fecha_hasta}")

def mostrar_analisis_portafolio():
    cliente = st.session_state.cliente_seleccionado
    token_acceso = st.session_state.token_acceso

    if not cliente:
        st.error("No se ha seleccionado ningún cliente")
        return
        
    # Inicializar el gestor de portafolio en session_state si no existe
    if 'portfolio_manager' not in st.session_state:
        st.session_state.portfolio_manager = None

    id_cliente = cliente.get('numeroCliente', cliente.get('id'))
    nombre_cliente = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))

    st.title(f"Análisis de Portafolio - {nombre_cliente}")
    
    # Crear tabs con iconos
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Resumen Portafolio", 
        "💰 Estado de Cuenta", 
        "📊 Análisis Técnico",
        "💱 Cotizaciones",
        "🔄 Optimización",
        "📉 Análisis de Volatilidad"
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
        
    with tab6:
        st.header("📊 Análisis de Volatilidad")
        
        # Obtener datos históricos
        portafolio = obtener_portafolio(token_acceso, id_cliente)
        if not portafolio or 'activos' not in portafolio or not portafolio['activos']:
            st.warning("No hay activos en el portafolio para analizar")
        else:
            # Mostrar selector de activos
            activos = portafolio['activos']
            simbolos = [a['titulo']['simbolo'] for a in activos if 'titulo' in a and 'simbolo' in a['titulo']]
            
            if not simbolos:
                st.warning("No se encontraron símbolos válidos para analizar")
            else:
                simbolo_seleccionado = st.selectbox(
                    "Seleccione un activo para analizar:",
                    options=simbolos,
                    key="vol_asset_selector"
                )
                
                # Configuración del análisis
                with st.expander("⚙️ Configuración del análisis", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        n_simulaciones = st.number_input(
                            "Número de simulaciones",
                            min_value=100,
                            max_value=10000,
                            value=1000,
                            step=100,
                            help="Cantidad de trayectorias a simular en el análisis de Monte Carlo"
                        )
                    with col2:
                        dias_proyeccion = st.number_input(
                            "Días de proyección",
                            min_value=5,
                            max_value=365,
                            value=30,
                            step=5,
                            help="Horizonte temporal para las proyecciones"
                        )
                
                # Botón para ejecutar el análisis
                if st.button("🔍 Analizar Volatilidad", use_container_width=True):
                    with st.spinner("Realizando análisis de volatilidad..."):
                        try:
                            # Inicializar el gestor de portafolio si no existe
                            if st.session_state.portfolio_manager is None:
                                st.session_state.portfolio_manager = PortfolioManager(
                                    activos=[{'simbolo': s} for s in simbolos],
                                    token=token_acceso,
                                    fecha_desde=(date.today() - timedelta(days=365)).strftime('%Y-%m-%d'),
                                    fecha_hasta=date.today().strftime('%Y-%m-%d')
                                )
                                
                                # Cargar datos históricos
                                if not st.session_state.portfolio_manager.load_data():
                                    st.error("Error al cargar datos históricos")
                                    return
                            
                            # Obtener retornos del activo seleccionado
                            if simbolo_seleccionado in st.session_state.portfolio_manager.returns:
                                returns = st.session_state.portfolio_manager.returns[simbolo_seleccionado]
                                
                                # Realizar análisis de volatilidad
                                result = st.session_state.portfolio_manager.analyze_volatility(
                                    symbol=simbolo_seleccionado,
                                    returns=returns,
                                    n_simulations=n_simulaciones,
                                    n_days=dias_proyeccion
                                )
                                
                                if result is not None:
                                    # Mostrar gráficos
                                    fig = st.session_state.portfolio_manager.plot_volatility_analysis(simbolo_seleccionado)
                                    if fig is not None:
                                        st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning(f"No se encontraron datos de retornos para {simbolo_seleccionado}")
                                
                        except Exception as e:
                            st.error(f"Error en el análisis de volatilidad: {str(e)}")
                            st.exception(e)

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
                    label_visibility="collapsed",
                    key="sidebar_cliente_selector"
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
                key="main_navigation_radio"
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
