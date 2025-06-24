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
            # Obtener tasas de caución
            url = "https://api.invertironline.com/api/v2/Cotizaciones/cauciones/argentina/todos"
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {token_portador}'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                st.error(f"Error al obtener tasas de caución: {response.status_code}")
                return
                
            data = response.json()
            
            if not data or 'titulos' not in data or not data['titulos']:
                st.warning("No se encontraron datos de tasas de caución.")
                return
            
            # Procesar los datos
            cauciones = []
            for caucion in data['titulos']:
                try:
                    # Extraer el número de días del plazo
                    plazo_str = caucion.get('plazo', '').lower()
                    plazo_dias = 0
                    
                    if 'día' in plazo_str or 'dia' in plazo_str:
                        plazo_dias = int(''.join(filter(str.isdigit, plazo_str)) or '0')
                    elif 'semana' in plazo_str:
                        semanas = int(''.join(filter(str.isdigit, plazo_str)) or '0')
                        plazo_dias = semanas * 7
                    
                    # Calcular tasa anualizada si es necesario
                    tasa = caucion.get('ultimoPrecio', 0)
                    if 'tasa' in caucion and caucion['tasa']:
                        tasa = caucion['tasa']
                    
                    cauciones.append({
                        'simbolo': caucion.get('simbolo', ''),
                        'descripcion': caucion.get('descripcion', ''),
                        'plazo': caucion.get('plazo', ''),
                        'plazo_dias': plazo_dias,
                        'moneda': caucion.get('moneda', 'ARS'),
                        'ultimoPrecio': tasa,
                        'tasa_anual': float(tasa) * (365/max(1, plazo_dias)) if plazo_dias > 0 else float(tasa),
                        'monto': caucion.get('montoOperado', 0)
                    })
                except Exception as e:
                    print(f"Error procesando caución {caucion.get('simbolo', '')}: {str(e)}")
            
            df_cauciones = pd.DataFrame(cauciones)
            
            if df_cauciones.empty:
                st.warning("No se encontraron datos válidos de tasas de caución.")
                return
            
            # Ordenar por plazo
            df_cauciones = df_cauciones.sort_values('plazo_dias')
            
            # Mostrar tabla con todas las cauciones
            st.markdown("### 📋 Listado de Cauciones")
            st.dataframe(
                df_cauciones[['simbolo', 'plazo', 'moneda', 'ultimoPrecio', 'tasa_anual', 'monto']]
                .rename(columns={
                    'simbolo': 'Símbolo',
                    'plazo': 'Plazo',
                    'moneda': 'Moneda',
                    'ultimoPrecio': 'Tasa Nominal',
                    'tasa_anual': 'Tasa Anual (%)',
                    'monto': 'Monto Operado (M)'
                }),
                use_container_width=True,
                height=min(400, 50 + len(df_cauciones) * 35)
            )
            
            # Mostrar resumen estadístico
            st.markdown("### 📊 Resumen Estadístico")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Tasa Mínima", f"{df_cauciones['tasa_anual'].min():.2f}%")
                st.metric("Plazo Mínimo", f"{df_cauciones['plazo_dias'].min()} días")
                
            with col2:
                st.metric("Tasa Máxima", f"{df_cauciones['tasa_anual'].max():.2f}%")
                st.metric("Plazo Máximo", f"{df_cauciones['plazo_dias'].max()} días")
                
            with col3:
                st.metric("Tasa Promedio", f"{df_cauciones['tasa_anual'].mean():.2f}%")
                st.metric("Plazo Promedio", f"{df_cauciones['plazo_dias'].mean():.1f} días")
            
            # Crear gráfico de curva de tasas
            st.markdown("### 📈 Curva de Tasas")
            if len(df_cauciones) > 1:
                fig = go.Figure()
                
                # Agrupar por moneda si hay múltiples monedas
                monedas = df_cauciones['moneda'].unique()
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
                
                for i, moneda in enumerate(monedas):
                    df_moneda = df_cauciones[df_cauciones['moneda'] == moneda]
                    
                    fig.add_trace(go.Scatter(
                        x=df_moneda['plazo_dias'],
                        y=df_moneda['tasa_anual'],
                        mode='lines+markers',
                        name=f'Tasa {moneda}',
                        line=dict(color=colors[i % len(colors)], width=2),
                        marker=dict(size=10, color=colors[i % len(colors)]),
                        hovertemplate=
                            '<b>Plazo</b>: %{x} días<br>' +
                            '<b>Tasa Anual</b>: %{y:.2f}%<br>' +
                            '<b>Moneda</b>: ' + moneda + '<extra></extra>'
                    ))
                
                fig.update_layout(
                    title='Curva de Tasas de Caución',
                    xaxis_title='Plazo (días)',
                    yaxis_title='Tasa Anual (%)',
                    template='plotly_white',
                    height=500,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    hovermode='x unified'
                )
                
                # Agregar anotaciones para los puntos
                for i, row in df_cauciones.iterrows():
                    fig.add_annotation(
                        x=row['plazo_dias'],
                        y=row['tasa_anual'],
                        text=f"{row['tasa_anual']:.1f}%",
                        showarrow=True,
                        yshift=10
                    )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Mostrar tabla de tasas para diferentes plazos
                st.markdown("### 📋 Tasas por Plazo")
                
                # Agrupar por plazo estándar
                plazos_estandar = [1, 7, 14, 21, 30, 60, 90, 180, 365]
                tasas_por_plazo = {}
                
                for plazo in plazos_estandar:
                    # Encontrar la caución más cercana a este plazo
                    df_cercano = df_cauciones.iloc[(df_cauciones['plazo_dias']-plazo).abs().argsort()[:1]]
                    if not df_cercano.empty:
                        tasas_por_plazo[plazo] = {
                            'tasa': df_cercano['tasa_anual'].values[0],
                            'moneda': df_cercano['moneda'].values[0]
                        }
                
                # Crear tabla de tasas por plazo
                df_tasas_plazo = pd.DataFrame([
                    {
                        'Plazo': f"{plazo} días",
                        'Tasa Anual (%)': f"{data['tasa']:.2f}",
                        'Moneda': data['moneda']
                    }
                    for plazo, data in tasas_por_plazo.items()
                ])
                
                if not df_tasas_plazo.empty:
                    st.dataframe(
                        df_tasas_plazo,
                        use_container_width=True,
                        hide_index=True
                    )
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión al obtener tasas de caución: {str(e)}")
    except Exception as e:
        st.error(f"Error inesperado al procesar tasas de caución: {str(e)}")
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
def obtener_tasa_libre_riesgo(token_portador):
    """
    Obtiene la tasa libre de riesgo promedio de las cauciones.
    
    Args:
        token_portador (str): Token de autenticación para la API de IOL
        
    Returns:
        float: Tasa libre de riesgo anualizada promedio
    """
    try:
        # Obtener tasas de caución
        df_cauciones = obtener_tasas_caucion(token_portador)
        
        if df_cauciones is None or df_cauciones.empty:
            st.warning("No se pudieron obtener las tasas de caución. Usando tasa predeterminada del 40%.")
            return 0.40  # Tasa predeterminada como respaldo
            
        # Calcular el promedio ponderado por monto de las tasas
        if 'tasa_limpia' in df_cauciones.columns and 'monto' in df_cauciones.columns:
            # Convertir a numérico y limpiar valores no numéricos
            df_cauciones['tasa_limpia'] = pd.to_numeric(df_cauciones['tasa_limpia'], errors='coerce')
            df_cauciones['monto'] = pd.to_numeric(df_cauciones['monto'], errors='coerce')
            df_cauciones = df_cauciones.dropna(subset=['tasa_limpia', 'monto'])
            
            if len(df_cauciones) > 0:
                # Calcular tasa promedio ponderada por monto
                tasa_promedio = np.average(
                    df_cauciones['tasa_limpia'], 
                    weights=df_cauciones['monto']
                )
                return tasa_promedio / 100  # Convertir de porcentaje a decimal
                
    except Exception as e:
        st.warning(f"Error al obtener tasa libre de riesgo: {str(e)}. Usando tasa predeterminada del 40%.")
    
    return 0.40  # Tasa predeterminada como último recurso

def calcular_alpha_beta(portfolio_returns, benchmark_returns, token_portador=None, risk_free_rate=None):
    """
    Calcula el Alpha y Beta de un portafolio respecto a un benchmark.
    
    Args:
        portfolio_returns (pd.Series): Retornos del portafolio
        benchmark_returns (pd.Series): Retornos del benchmark (ej: MERVAL)
        token_portador (str, optional): Token de autenticación para obtener la tasa libre de riesgo
        risk_free_rate (float, optional): Tasa libre de riesgo (anualizada). Si no se proporciona, se obtendrá automáticamente.
        
    Returns:
        dict: Diccionario con alpha, beta, información de la regresión y métricas adicionales
    """
    # Obtener tasa libre de riesgo si no se proporciona
    if risk_free_rate is None and token_portador is not None:
        risk_free_rate = obtener_tasa_libre_riesgo(token_portador)
    elif risk_free_rate is None:
        risk_free_rate = 0.40  # Tasa predeterminada si no hay token
    
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
            'alpha_annual': 0,
            'risk_free_rate': risk_free_rate
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

def calcular_alpha_beta_activos(activos_returns, benchmark_returns, risk_free_rate=0.0):
    """
    Calcula alpha y beta para múltiples activos respecto a un benchmark.
    
    Args:
        activos_returns (dict): Diccionario con los retornos de cada activo
        benchmark_returns (pd.Series): Retornos del benchmark (ej: MERVAL)
        risk_free_rate (float): Tasa libre de riesgo (anualizada)
        
    Returns:
        dict: Diccionario con métricas de alpha y beta por activo
    """
    resultados = {}
    
    for simbolo, returns in activos_returns.items():
        try:
            # Alinear las series por fecha
            aligned_data = pd.concat([returns, benchmark_returns], axis=1).dropna()
            
            if len(aligned_data) < 5:  # Mínimo de datos para regresión
                continue
                
            portfolio_aligned = aligned_data.iloc[:, 0]
            benchmark_aligned = aligned_data.iloc[:, 1]
            
            # Calcular regresión lineal
            slope, intercept, r_value, p_value, std_err = linregress(
                benchmark_aligned, 
                portfolio_aligned
            )
            
            # Calcular métricas adicionales
            tracking_error = np.std(portfolio_aligned - benchmark_aligned) * np.sqrt(252)
            information_ratio = (portfolio_aligned.mean() - benchmark_aligned.mean()) / tracking_error if tracking_error != 0 else 0
            
            # Anualizar alpha
            alpha_annual = intercept * 252
            
            resultados[simbolo] = {
                'alpha': intercept,
                'alpha_annual': alpha_annual,
                'beta': slope,
                'r_squared': r_value ** 2,
                'p_value': p_value,
                'tracking_error': tracking_error,
                'information_ratio': information_ratio,
                'observations': len(aligned_data)
            }
            
        except Exception as e:
            print(f"Error calculando alpha/beta para {simbolo}: {str(e)}")
            continue
            
    return resultados

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

def obtener_datos_bonos(token_portador, fecha_desde, fecha_hasta):
    """
    Obtiene datos históricos de AL30 y AL30D de InvertirOnline API.
    
    Args:
        token_portador (str): Token de autenticación
        fecha_desde (str): Fecha de inicio en formato 'YYYY-MM-DD'
        fecha_hasta (str): Fecha de fin en formato 'YYYY-MM-DD'
        
    Returns:
        tuple: (df_al30, df_al30d) DataFrames con datos de los bonos
    """
    def obtener_serie_historica_bono(simbolo):
        url = f"https://api.invertironline.com/api/v2/BCBA/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/Ajustada"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token_portador}'
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame(data)
                    # Estandarizar nombres de columnas
                    df = df.rename(columns={
                        'fecha': 'fecha',
                        'fechaHora': 'fecha',
                        'fechaOperacion': 'fecha',
                        'ultimoPrecio': 'cierre',
                        'precioCierre': 'cierre',
                        'cierre': 'cierre'
                    })
                    df['fecha'] = pd.to_datetime(df['fecha'])
                    df = df[['fecha', 'cierre']].dropna()
                    df = df.set_index('fecha')
                    return df
        except Exception as e:
            print(f"Error obteniendo datos para {simbolo}: {str(e)}")
        return None

    # Obtener datos de ambos bonos
    al30 = obtener_serie_historica_bono('AL30')
    al30d = obtener_serie_historica_bono('AL30D')
    
    return al30, al30d

def calcular_mep(al30, al30d):
    """
    Calcula el tipo de cambio MEP a partir de los precios de AL30 y AL30D.
    
    Args:
        al30 (pd.DataFrame): Datos de AL30 con columna 'cierre'
        al30d (pd.DataFrame): Datos de AL30D con columna 'cierre'
        
    Returns:
        pd.Series: Serie de tiempo con el tipo de cambio MEP
    """
    if al30 is None or al30d is None:
        return None
    
    # Unir las series por fecha
    df = pd.concat([al30['cierre'], al30d['cierre']], axis=1)
    df.columns = ['al30', 'al30d']
    df = df.dropna()
    
    # Calcular MEP (precio AL30 / precio AL30D)
    df['mep'] = df['al30'] / df['al30d']
    
    return df['mep']

def analizar_benchmarks(portafolio_returns, token_portador, fecha_desde, fecha_hasta):
    """
    Analiza el portafolio contra múltiples benchmarks, incluyendo AL30/AL30D para MEP.
    
    Args:
        portafolio_returns (pd.Series): Retornos diarios del portafolio
        token_portador (str): Token de autenticación para IOL
        fecha_desde (str): Fecha de inicio en formato 'YYYY-MM-DD'
        fecha_hasta (str): Fecha de fin en formato 'YYYY-MM-DD'
        
    Returns:
        dict: Diccionario con métricas por benchmark
    """
    # Obtener datos de bonos para calcular MEP
    al30, al30d = obtener_datos_bonos(token_portador, fecha_desde, fecha_hasta)
    mep_series = calcular_mep(al30, al30d)
    
    # Calcular retornos del MEP
    mep_returns = mep_series.pct_change().dropna() if mep_series is not None else None

    # Definir benchmarks de yfinance
    benchmarks = {
        '^MERV': 'MERVAL',
        '^GSPC': 'S&P 500',
        '^IXIC': 'NASDAQ',
        '^DJI': 'Dow Jones',
        'GC=F': 'Oro',
        'BTC-USD': 'Bitcoin'
    }
    
    # Agregar MEP si está disponible
    if mep_returns is not None:
        benchmarks['MEP'] = 'Dólar MEP'
    
    # Obtener datos de yfinance
    benchmark_data = {}
    if benchmarks:
        try:
            # Descargar datos de yfinance
            yf_data = yf.download(
                [b for b in benchmarks.keys() if b != 'MEP'], 
                start=fecha_desde, 
                end=fecha_hasta
            )['Adj Close']
            
            # Procesar cada benchmark
            for ticker, name in benchmarks.items():
                if ticker == 'MEP':
                    benchmark_data[name] = mep_returns
                elif ticker in yf_data.columns:
                    benchmark_data[name] = yf_data[ticker].pct_change().dropna()
        except Exception as e:
            print(f"Error descargando datos de yfinance: {str(e)}")
    
    # Calcular métricas para cada benchmark
    resultados = {}
    for name, bench_returns in benchmark_data.items():
        try:
            # Alinear fechas
            aligned_port, aligned_bench = portafolio_returns.align(bench_returns, join='inner')
            
            if len(aligned_port) < 5:  # Mínimo de datos para cálculo
                continue
                
            # Calcular métricas
            corr = np.corrcoef(aligned_port, aligned_bench)[0, 1]
            cov = np.cov(aligned_port, aligned_bench)[0, 1]
            beta = cov / np.var(aligned_bench)
            
            # Calcular alpha anualizado (asumiendo tasa libre de riesgo diaria)
            rf_diario = 0.40 / 252  # Tasa libre de riesgo diaria (40% anual)
            alpha = (aligned_port.mean() - rf_diario) - beta * (aligned_bench.mean() - rf_diario)
            alpha_annual = alpha * 252
            
            # Calcular volatilidad anualizada
            volatilidad_bench = aligned_bench.std() * np.sqrt(252)
            
            # Calcular Sharpe Ratio
            exceso_retorno = aligned_bench.mean() * 252 - 0.40
            volatilidad_anual = aligned_bench.std() * np.sqrt(252)
            sharpe = exceso_retorno / volatilidad_anual if volatilidad_anual > 0 else 0
            
            resultados[name] = {
                'correlacion': corr,
                'beta': beta,
                'alpha_anual': alpha_annual,
                'volatilidad_bench': volatilidad_bench,
                'sharpe_bench': sharpe
            }
        except Exception as e:
            print(f"Error calculando métricas para {name}: {str(e)}")
    
    return resultados

def mostrar_analisis_benchmarks(metricas):
    """Muestra el análisis de benchmarks en la interfaz de Streamlit"""
    if 'benchmark_analysis' not in metricas or not metricas['benchmark_analysis']:
        return
    
    st.subheader("📊 Análisis de Benchmarks")
    
    # Crear DataFrame con los resultados
    data = []
    for benchmark, metrics in metricas['benchmark_analysis'].items():
        data.append({
            'Benchmark': benchmark,
            'Beta': metrics['beta'],
            'Alpha Anual': metrics['alpha_anual'],
            'Correlación': metrics['correlacion'],
            'Volatilidad Anual': metrics['volatilidad_bench'],
            'Sharpe Ratio': metrics['sharpe_bench']
        })
    
    if not data:
        st.warning("No hay datos de benchmarks disponibles")
        return
    
    df = pd.DataFrame(data)
    
    # Formatear columnas
    format_dict = {
        'Beta': '{:.2f}',
        'Alpha Anual': '{:,.2%}',
        'Correlación': '{:.2f}',
        'Volatilidad Anual': '{:,.2%}',
        'Sharpe Ratio': '{:.2f}'
    }
    
    # Aplicar formato
    for col, fmt in format_dict.items():
        df[col] = df[col].apply(lambda x: fmt.format(x) if pd.notnull(x) else '-')
    
    # Mostrar tabla con formato condicional
    st.dataframe(
        df.style
        .bar(subset=['Beta'], color='#5fba7d')
        .bar(subset=['Alpha Anual'], color='#5fba7d')
        .bar(subset=['Correlación'], color='#5fba7d')
        .bar(subset=['Volatilidad Anual'], color='#5fba7d')
        .bar(subset=['Sharpe Ratio'], color='#5fba7d'),
        use_container_width=True,
        height=(len(df) + 1) * 35 + 3,
        hide_index=True
    )
    
    # Explicación de las métricas
    with st.expander("ℹ️ Explicación de las métricas"):
        st.markdown("""
        - **Beta**: Mide la sensibilidad del portafolio a los movimientos del benchmark.
        - **Alpha Anual**: Retorno excedente anualizado respecto al esperado dado el riesgo.
        - **Correlación**: Grado de relación lineal con el benchmark (de -1 a 1).
        - **Volatilidad Anual**: Desviación estándar anualizada de los retornos.
        - **Sharpe Ratio**: Retorno ajustado por riesgo (mayor es mejor).
        """)

def calcular_metricas_portafolio(portafolio, valor_total, token_portador, dias_historial=252):
    """
    Calcula métricas clave de desempeño para un portafolio de inversión usando datos históricos.
    
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
    
    # Inicializar diccionario de resultados
    resultados = {}
    
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
        m['retorno_medio'] * m['peso'] 
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
                    m['volatilidad'] * m['peso'] 
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
            m['volatilidad'] * m['peso'] 
            for m in metricas_activos.values()
        ) if metricas_activos else 0.2
    
    # Calcular alpha y beta para cada activo individual
    if merval_available and retornos_diarios:
        alpha_beta_activos = calcular_alpha_beta_activos(
            retornos_diarios,
            merval_returns,
            risk_free_rate=0.40  # Tasa libre de riesgo para Argentina
        )
        
        # Actualizar métricas de los activos con alpha y beta
        for simbolo, metrics in alpha_beta_activos.items():
            if simbolo in metricas_activos:
                metricas_activos[simbolo].update(metrics)
    
    # Simulación Monte Carlo mejorada
    num_simulaciones = 10000
    dias_proyeccion = 252  # 1 año
    retornos_simulados = []
    valores_finales = []
    
    # Extraer métricas necesarias para la simulación
    activos = list(metricas_activos.keys())
    if not activos:
        print("No hay activos válidos para la simulación")
        return {}
        
    pesos = np.array([metricas_activos[a]['peso'] for a in activos])
    retornos_medios = np.array([m['retorno_medio']/252 for m in metricas_activos.values()])  # Diario
    volatilidades = np.array([m['volatilidad']/np.sqrt(252) for m in metricas_activos.values()])  # Diario
    
    # Matriz de correlación (asumimos correlación cero para simplificar)
    n_activos = len(activos)
    correlaciones = np.eye(n_activos)  # Matriz identidad (correlación cero)
    
    # Generar retornos correlacionados
    medias = np.zeros(n_activos)
    cov = np.diag(volatilidades) @ correlaciones @ np.diag(volatilidades)
    
    # Semilla para reproducibilidad
    np.random.seed(42)
    
    # Simulación de Monte Carlo
    for _ in range(num_simulaciones):
        # Generar retornos diarios correlacionados
        retornos_diarios_sim = np.random.multivariate_normal(medias, cov, size=dias_proyeccion)
        retorno_portfolio_diario = retornos_diarios_sim @ pesos  # Retorno diario del portafolio
        
        # Calcular valor final
        valor_final = valor_total * np.prod(1 + retorno_portfolio_diario)
        retorno_anual = (valor_final / valor_total) ** (252/dias_proyeccion) - 1
        
        retornos_simulados.append(retorno_anual)
        valores_finales.append(valor_final)
    
    # Convertir a arrays de numpy
    retornos_simulados = np.array(retornos_simulados)
    valores_finales = np.array(valores_finales)
    
    # Calcular métricas estadísticas
    retorno_esperado = np.mean(retornos_simulados)
    volatilidad_anual = np.std(retornos_simulados)
    sharpe_ratio = (retorno_esperado - 0.40) / volatilidad_anual if volatilidad_anual > 0 else 0
    var_95 = np.percentile(retornos_simulados, 5)
    cvar_95 = retornos_simulados[retornos_simulados <= var_95].mean()
    
    # Calcular percentiles para escenarios
    pl_esperado_min = np.percentile(valores_finales, 5)
    pl_esperado_max = np.percentile(valores_finales, 95)
    
    # Calcular probabilidades basadas en los retornos simulados
    total_simulaciones = len(retornos_simulados)
    prob_ganancia = np.sum(retornos_simulados > 0) / total_simulaciones if total_simulaciones > 0 else 0.5
    prob_perdida = np.sum(retornos_simulados < 0) / total_simulaciones if total_simulaciones > 0 else 0.5
    prob_ganancia_10 = np.sum(retornos_simulados > 0.1) / total_simulaciones
    prob_perdida_10 = np.sum(retornos_simulados < -0.1) / total_simulaciones
            
    # 4. Calcular Alpha y Beta para el portafolio y cada activo individual
    alpha_beta_metrics = {}
    alpha_beta_activos = {}
    
    if merval_available and len(retornos_diarios) > 1:
        try:
            # Preparar DataFrame con retornos diarios de todos los activos
            df_returns = pd.DataFrame(retornos_diarios)
            
            # Asegurarse de que los pesos estén en el mismo orden que las columnas
            pesos_ordenados = [metricas_activos[col]['peso'] for col in df_returns.columns]
            
            # Calcular retorno ponderado del portafolio
            df_returns['Portfolio'] = df_returns.dot(pesos_ordenados)
            
            # Alinear fechas con el MERVAL
            merval_series = pd.Series(merval_returns, name='MERVAL')
            aligned_data = pd.merge(
                df_returns, 
                merval_series, 
                left_index=True, 
                right_index=True,
                how='inner'
            )
            
            if len(aligned_data) > 5:  # Mínimo de datos para cálculo confiable
                # Obtener tasa libre de riesgo actualizada
                try:
                    tasa_libre_riesgo = obtener_tasa_libre_riesgo(token_portador)
                    print(f"Tasa libre de riesgo obtenida: {tasa_libre_riesgo:.2%} anual")
                except Exception as e:
                    print(f"Error al obtener tasa libre de riesgo: {str(e)}")
                    tasa_libre_riesgo = 0.40  # Valor por defecto si falla
                    print(f"Usando tasa libre de riesgo por defecto: {tasa_libre_riesgo:.0%}")
                
                # Calcular métricas de Alpha y Beta para el portafolio completo
                alpha_beta_metrics = calcular_alpha_beta(
                    aligned_data['Portfolio'],
                    aligned_data['MERVAL'],
                    risk_free_rate=tasa_libre_riesgo,
                    token_portador=token_portador  # Pasar el token para cálculo automático
                )
                
                # Calcular alpha y beta para cada activo individual
                activos_returns = {}
                for activo in df_returns.columns:
                    if activo != 'Portfolio':
                        activos_returns[activo] = aligned_data[activo]
                
                alpha_beta_activos = {}
                for activo, retornos in activos_returns.items():
                    try:
                        # Calcular métricas para cada activo individualmente
                        metrics = calcular_alpha_beta(
                            retornos,
                            aligned_data['MERVAL'],
                            risk_free_rate=tasa_libre_riesgo,
                            token_portador=token_portador
                        )
                        alpha_beta_activos[activo] = metrics
                    except Exception as e:
                        print(f"Error calculando alpha/beta para {activo}: {str(e)}")
                        alpha_beta_activos[activo] = {
                            'alpha': 0,
                            'alpha_annual': 0,
                            'beta': 0,
                            'r_squared': 0,
                            'volatilidad': 0,
                            'sharpe_ratio': 0
                        }
                
                # Agregar información adicional a las métricas de cada activo
                for activo, datos in alpha_beta_activos.items():
                    if activo in metricas_activos:
                        datos.update({
                            'peso': metricas_activos[activo]['peso'],
                            'volatilidad_anual': metricas_activos[activo].get('volatilidad_anual', 0)
                        })
                
                print(f"Portfolio - Alpha: {alpha_beta_metrics.get('alpha_annual', 0):.2%}, "
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
    
    # 5. Realizar análisis de benchmarks
    benchmark_analysis = {}
    try:
        # Obtener retornos diarios del portafolio
        if 'Portfolio' in df_returns.columns:
            benchmark_analysis = analizar_benchmarks(
                df_returns['Portfolio'],
                token_portador,
                fecha_desde,
                fecha_hasta
            )
    except Exception as e:
        print(f"Error en análisis de benchmarks: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Preparar resultados finales
    resultados = {
        'concentracion': concentracion,
        'std_dev_activo': std_dev_activo,
        'retorno_esperado_anual': retorno_esperado_anual,
        'pl_esperado_min': pl_esperado_min,
        'pl_esperado_max': pl_esperado_max,
        'probabilidades': {
            'perdida': prob_perdida,
            'ganancia': prob_ganancia,
            'perdida_mayor_10': prob_perdida_10,
            'ganancia_mayor_10': prob_ganancia_10
        },
        'riesgo_anual': volatilidad_portafolio,
        'metricas_activos': metricas_activos,
        'alpha_beta': alpha_beta_metrics if merval_available else None,
        'benchmark_analysis': benchmark_analysis,
        'alpha_beta_activos': alpha_beta_activos if merval_available else {},
        'estrategia': analisis_estrategia if merval_available else None,
        'simulacion_montecarlo': {
            'retorno_esperado': retorno_esperado,
            'volatilidad_anual': volatilidad_anual,
            'sharpe_ratio': sharpe_ratio,
            'var_95': var_95,
            'cvar_95': cvar_95,
            'percentil_5': np.percentile(retornos_simulados, 5) if len(retornos_simulados) > 0 else 0,
            'percentil_25': np.percentile(retornos_simulados, 25) if len(retornos_simulados) > 0 else 0,
            'mediana': np.median(retornos_simulados) if len(retornos_simulados) > 0 else 0,
            'percentil_75': np.percentile(retornos_simulados, 75) if len(retornos_simulados) > 0 else 0,
            'percentil_95': np.percentile(retornos_simulados, 95) if len(retornos_simulados) > 0 else 0,
            'prob_negativo': prob_perdida * 100,
            'prob_positivo': prob_ganancia * 100,
            'retornos_anuales': retornos_simulados,
            'valores_finales': valores_finales
        }
    }
    
    # Agregar métricas adicionales al diccionario de resultados
    if merval_available and alpha_beta_metrics:
        resultados.update({
            'tracking_error': alpha_beta_metrics.get('tracking_error', 0),
            'information_ratio': alpha_beta_metrics.get('information_ratio', 0)
        })
    
    # Analizar la estrategia de inversión
    analisis_estrategia = analizar_estrategia_inversion(alpha_beta_metrics)
    
    return resultados

def plot_histograma_montecarlo(simulacion, valor_inicial):
    """
    Crea un histograma de los resultados de la simulación de Monte Carlo.
    
    Args:
        simulacion (dict): Resultados de la simulación
        valor_inicial (float): Valor inicial del portafolio
        
    Returns:
        plotly.graph_objects.Figure: Figura con el histograma
    """
    if not simulacion or 'retornos_anuales' not in simulacion:
        return None
    
    stats = {
        'retorno_esperado': simulacion['retorno_esperado'],
        'volatilidad_anual': simulacion['volatilidad_anual'],
        'sharpe_ratio': simulacion['sharpe_ratio'],
        'var_95': simulacion['var_95'],
        'cvar_95': simulacion['cvar_95'],
        'prob_negativo': simulacion['prob_negativo'],
        'prob_positivo': simulacion['prob_positivo']
    }
    
    # Crear histograma
    fig = go.Figure()
    
    # Añadir histograma
    fig.add_trace(go.Histogram(
        x=simulacion['retornos_anuales'] * 100,  # Convertir a porcentaje
        nbinsx=50,
        name='Frecuencia',
        marker_color='#1f77b4',
        opacity=0.7,
        hovertemplate='Retorno: %{x:.2f}%<br>Frecuencia: %{y}'
    ))
    
    # Añadir líneas de referencia
    fig.add_vline(x=0, line_dash='dash', line_color='red', 
                 annotation_text='Cero', annotation_position='top right')
    
    # Añadir estadísticas
    fig.add_vline(x=stats['retorno_esperado'] * 100, line_dash='dash', 
                 line_color='green', annotation_text=f"Media: {stats['retorno_esperado']*100:.2f}%",
                 annotation_position='top right')
    
    fig.add_vline(x=stats['var_95'] * 100, line_dash='dash', 
                 line_color='orange', annotation_text=f"VaR 95%: {stats['var_95']*100:.2f}%",
                 annotation_position='top right')
    
    # Actualizar diseño
    fig.update_layout(
        title='Distribución de Retornos Anuales Proyectados',
        xaxis_title='Retorno Anual (%)',
        yaxis_title='Frecuencia',
        showlegend=False,
        hovermode='x unified',
        height=500,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Añadir anotaciones con estadísticas
    annotations = [
        dict(
            x=0.02, y=0.98,
            xref='paper', yref='paper',
            text=f"<b>Estadísticas de la Simulación</b><br><br>" +
                 f"Retorno Esperado: {stats['retorno_esperado']*100:.2f}%<br>" +
                 f"Volatilidad Anual: {stats['volatilidad_anual']*100:.2f}%<br>" +
                 f"Sharpe Ratio: {stats['sharpe_ratio']:.2f}<br>" +
                 f"VaR 95%: {stats['var_95']*100:.2f}%<br>" +
                 f"Prob. Retorno Negativo: {stats['prob_negativo']:.1f}%",
            showarrow=False,
            align='left',
            bordercolor='black',
            borderwidth=1,
            borderpad=4,
            bgcolor='white',
            opacity=0.8
        )
    ]
    
    fig.update_layout(annotations=annotations)
    
    return fig

def mostrar_resumen_portafolio(portafolio, token_portador):
    """Muestra un resumen detallado del portafolio con métricas de desempeño"""
    if not portafolio or not isinstance(portafolio, dict):
        st.warning("No hay datos del portafolio para mostrar.")
        return
        
    # Calcular valor total del portafolio
    valor_total = sum(activo.get('Valuación', 0) for activo in portafolio.values())
    
    if valor_total <= 0:
        st.warning("El valor total del portafolio debe ser mayor a cero.")
        return
    
    # Calcular métricas del portafolio
    with st.spinner('Calculando métricas del portafolio...'):
        metricas = calcular_metricas_portafolio(portafolio, valor_total, token_portador)
    
    if not metricas:
        st.error("No se pudieron calcular las métricas del portafolio.")
        return
        
    # Mostrar métricas de alpha/beta por activo si están disponibles
    if 'alpha_beta_activos' in metricas and metricas['alpha_beta_activos']:
        st.subheader("📊 Análisis de Riesgo por Activo")
        
        # Crear DataFrame con las métricas
        datos_activos = []
        for simbolo, activo in portafolio.items():
            if simbolo not in metricas['alpha_beta_activos']:
                continue
                
            ab = metricas['alpha_beta_activos'][simbolo]
            peso_activo = activo.get('Valuación', 0) / valor_total
            
            # Calcular contribución al riesgo sistemático del portafolio
            beta_activo = ab.get('beta', 0)
            contrib_riesgo_sistematico = beta_activo * peso_activo
            
            datos_activos.append({
                'Activo': simbolo,
                'Descripción': activo.get('Descripción', ''),
                'Beta': beta_activo,
                'Alpha Anual': ab.get('alpha_annual', 0),
                'R²': ab.get('r_squared', 0),
                'Volatilidad Anual': ab.get('volatilidad_anual', 0) * 100 if 'volatilidad_anual' in ab else 0,
                'Peso': peso_activo * 100,
                'Contrib. Riesgo Sist.': contrib_riesgo_sistematico * 100,
                'Tracking Error': ab.get('tracking_error', 0) * 100,
                'Information Ratio': ab.get('information_ratio', 0)
            })
        
        if datos_activos:
            df_activos = pd.DataFrame(datos_activos)
            
            # Ordenar por contribución al riesgo sistemático (mayor a menor)
            df_activos = df_activos.sort_values('Contrib. Riesgo Sist.', ascending=False)
            
            # Formatear números
            format_dict = {
                'Beta': '{:.2f}',
                'Alpha Anual': '{:,.2f}%',
                'R²': '{:.2f}',
                'Volatilidad Anual': '{:,.2f}%',
                'Peso': '{:,.2f}%',
                'Contrib. Riesgo Sist.': '{:,.2f}%',
                'Tracking Error': '{:,.2f}%',
                'Information Ratio': '{:,.2f}'
            }
            
            # Resaltar filas basado en valores clave
            def highlight_rows(row):
                styles = [''] * len(row)
                
                # Resaltar betas altos (mayor riesgo sistemático)
                if abs(row['Beta']) > 1.5:
                    styles[2] = 'background-color: #ffcccc'  # Rojo claro para alto riesgo
                
                # Resaltar alfas positivos significativos
                if row['Alpha Anual'] > 5:  # Más del 5% de alpha anual
                    styles[3] = 'background-color: #d4edda'  # Verde claro para buen alpha
                
                # Resaltar R² bajos (poca explicación por el mercado)
                if row['R²'] < 0.3:
                    styles[4] = 'background-color: #fff3cd'  # Amarillo claro para advertencia
                
                return styles
            
            # Aplicar formato condicional
            styled_df = df_activos.style.format(format_dict).apply(highlight_rows, axis=1)
            
            # Mostrar tabla con métricas
            st.dataframe(
                styled_df,
                use_container_width=True,
                height=min(500, 50 + len(df_activos) * 35),
                column_config={
                    'Activo': 'Activo',
                    'Descripción': 'Descripción',
                    'Beta': st.column_config.NumberColumn('Beta', help="Sensibilidad al mercado"),
                    'Alpha Anual': st.column_config.NumberColumn('Alpha Anual (%)', help="Rendimiento ajustado por riesgo"),
                    'R²': st.column_config.NumberColumn('R²', help="% de variación explicada por el mercado"),
                    'Volatilidad Anual': st.column_config.NumberColumn('Volatilidad Anual (%)', help="Riesgo total del activo"),
                    'Peso': st.column_config.NumberColumn('Peso (%)', help="Peso en el portafolio"),
                    'Contrib. Riesgo Sist.': st.column_config.NumberColumn('Contrib. Riesgo Sist. (%)', help="Contribución al riesgo sistemático"),
                    'Tracking Error': st.column_config.NumberColumn('Tracking Error (%)', help="Riesgo activo vs. benchmark"),
                    'Information Ratio': st.column_config.NumberColumn('Information Ratio', help="Retorno por unidad de riesgo activo")
                }
            )
            
            # Mostrar interpretación de las métricas
            with st.expander("ℹ️ Guía de Interpretación de Métricas de Riesgo"):
                st.markdown("""
                ### Explicación de las Métricas Clave:
                
                #### 1. Beta (β)
                - **> 1.5**: Alta sensibilidad al mercado (más volátil que el mercado)
                - **1.0**: Misma volatilidad que el mercado
                - **0 a 1**: Menos volátil que el mercado
                - **< 0**: Se mueve en dirección opuesta al mercado
                
                #### 2. Alpha Anual (%)
                - **> 0%**: Sobrerendimiento respecto al esperado por el riesgo asumido
                - **< 0%**: Subrendimiento respecto al esperado
                - Valores superiores al 5% anual se consideran muy buenos
                
                #### 3. R² (R-cuadrado)
                - **0.7-1.0**: Alta correlación con el mercado
                - **0.3-0.7**: Correlación moderada
                - **< 0.3**: Baja correlación con el mercado
                
                #### 4. Contribución al Riesgo Sistemático
                - Mide cuánto contribuye cada activo al riesgo total del portafolio
                - Se calcula como: Beta del activo × Peso en el portafolio
                
                #### 5. Information Ratio
                - **> 1.0**: Buen desempeño ajustado por riesgo
                - **> 0.5**: Desempeño aceptable
                - **< 0.0**: Mal desempeño ajustado por riesgo
                
                #### Código de Colores:
                - 🟢 Verde: Alpha positivo significativo (>5%)
                - 🟡 Amarillo: Bajo R² (<0.3) - poca explicación por el mercado
                - 🔴 Rojo: Beta alto (>1.5) - alto riesgo sistemático
                """)
    
    # Mostrar simulación de Monte Carlo si está disponible
    if 'simulacion_montecarlo' in metricas and metricas['simulacion_montecarlo']:
        st.subheader("📈 Simulación de Monte Carlo")
        
        # Mostrar métricas clave en columnas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Retorno Esperado Anual", 
                     f"{metricas['simulacion_montecarlo']['retorno_esperado']*100:.2f}%",
                     help="Retorno anual promedio esperado según la simulación")
            
        with col2:
            st.metric("Volatilidad Anual",
                    f"{metricas['simulacion_montecarlo']['volatilidad_anual']*100:.2f}%",
                    help="Riesgo medido como desviación estándar de los retornos")
            
        with col3:
            st.metric("Escenario Optimista (95%)", 
                     f"{metricas['simulacion_montecarlo']['percentil_95']*100:.2f}%",
                     help="Mejor escenario dentro del 5% superior de resultados")
            
        with col4:
            st.metric("Escenario Pesimista (5%)",
                    f"{metricas['simulacion_montecarlo']['percentil_5']*100:.2f}%",
                    help="Peor escenario dentro del 5% inferior de resultados")
        
        # Mostrar el histograma de la simulación
        fig = plot_histograma_montecarlo(
            metricas['simulacion_montecarlo'],
            valor_total
        )
        
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar métricas adicionales
            st.markdown("### Otras Métricas de Riesgo")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("VaR 95% (1 día)", 
                         f"{metricas['simulacion_montecarlo']['var_95']*100:.2f}%",
                         help="Pérdida máxima esperada en un día con 95% de confianza")
                
            with col2:
                st.metric("CVaR 95% (1 día)",
                        f"{metricas['simulacion_montecarlo']['cvar_95']*100:.2f}%",
                        help="Pérdida promedio en el peor 5% de los escenarios")
                
            with col3:
                st.metric("Ratio de Sharpe",
                        f"{metricas['simulacion_montecarlo']['sharpe_ratio']:.2f}",
                        help="Retorno por unidad de riesgo asumido")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Retorno Esperado Anual", 
                     f"{metricas['simulacion_montecarlo']['retorno_esperado']*100:.2f}%",
                     help="Retorno anual promedio esperado según la simulación")
            
        with col2:
            st.metric("Volatilidad Anual",
                    f"{metricas['simulacion_montecarlo']['volatilidad_anual']*100:.2f}%",
                    help="Riesgo medido como desviación estándar de los retornos")
            
        with col3:
            st.metric("Escenario Optimista (95%)", 
                     f"{metricas['simulacion_montecarlo']['percentil_95']*100:.2f}%",
                     help="Mejor escenario dentro del 5% superior de resultados")
            
        with col4:
            st.metric("Escenario Pesimista (5%)",
                    f"{metricas['simulacion_montecarlo']['percentil_5']*100:.2f}%",
                    help="Peor escenario dentro del 5% inferior de resultados")
            st.metric("Escenario Pesimista (5%)", 
                     f"{metricas['simulacion_montecarlo']['percentil_5']*100:.2f}%")
        
        # Mostrar histograma de la simulación
        fig_hist = plot_histograma_montecarlo(metricas['simulacion_montecarlo'], valor_total)
        if fig_hist:
            st.plotly_chart(fig_hist, use_container_width=True)
            
        # Mostrar más detalles en un expander
        with st.expander("📊 Ver más detalles de la simulación"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Volatilidad Anual", 
                         f"{metricas['simulacion_montecarlo']['volatilidad_anual']*100:.2f}%")
                st.metric("Ratio de Sharpe", 
                         f"{metricas['simulacion_montecarlo']['sharpe_ratio']:.2f}")
                st.metric("VaR 95%", 
                         f"{metricas['simulacion_montecarlo']['var_95']*100:.2f}%")
                st.metric("CVaR 95%", 
                         f"{metricas['simulacion_montecarlo']['cvar_95']*100:.2f}%")
                
            with col2:
                st.metric("Prob. Retorno Negativo", 
                         f"{metricas['simulacion_montecarlo']['prob_negativo']:.1f}%")
                st.metric("Prob. Retorno > 10%", 
                         f"{np.mean(np.array(metricas['simulacion_montecarlo']['retornos_anuales']) > 0.1)*100:.1f}%")
                st.metric("Retorno Mediano", 
                         f"{np.median(metricas['simulacion_montecarlo']['retornos_anuales'])*100:.2f}%")
                st.metric("Rango Intercuartílico", 
                         f"{metricas['simulacion_montecarlo']['percentil_25']*100:.1f}% a {metricas['simulacion_montecarlo']['percentil_75']*100:.1f}%")
            
            # Mostrar distribución de valores finales
            st.subheader("Distribución de Valores Finales")
            fig_valores = px.histogram(
                x=metricas['simulacion_montecarlo']['valores_finales'],
                nbins=50,
                labels={'x': 'Valor Final del Portafolio', 'y': 'Frecuencia'},
                title='Distribución de Valores Finales Proyectados'
            )
            
            # Añadir líneas de referencia
            fig_valores.add_vline(
                x=valor_total, 
                line_dash='dash', 
                line_color='green', 
                annotation_text=f"Valor Actual: ${valor_total:,.2f}"
            )
            
            fig_valores.add_vline(
                x=metricas['simulacion_montecarlo']['percentil_5'] * valor_total + valor_total, 
                line_dash='dash', 
                line_color='red',
                annotation_text=f"Pesimista (5%): ${(metricas['simulacion_montecarlo']['percentil_5'] * valor_total + valor_total):,.2f}"
            )
            
            fig_valores.add_vline(
                x=metricas['simulacion_montecarlo']['percentil_95'] * valor_total + valor_total, 
                line_dash='dash', 
                line_color='blue',
                annotation_text=f"Optimista (95%): ${(metricas['simulacion_montecarlo']['percentil_95'] * valor_total + valor_total):,.2f}"
            )
            
            st.plotly_chart(fig_valores, use_container_width=True)
    
    # Mostrar análisis de benchmarks si está disponible
    if 'benchmark_analysis' in metricas and metricas['benchmark_analysis']:
        st.markdown("---")
        st.subheader("📊 Análisis Comparativo con Benchmarks")
        
        # Mostrar métricas de benchmarks
        mostrar_analisis_benchmarks(metricas['benchmark_analysis'])
        
        # Explicación de las métricas
        with st.expander("ℹ️ Explicación de las Métricas de Benchmarks"):
            st.markdown("""
            ### Interpretación de las Métricas de Benchmarks
            
            - **Alpha Anualizado**: Mide el rendimiento excedente del portafolio respecto al benchmark. 
              - **Positivo**: El portafolio superó al benchmark.
              - **Negativo**: El portafolio tuvo peor desempeño que el benchmark.
            
            - **Beta**: Mide la sensibilidad del portafolio a los movimientos del mercado.
              - **> 1**: Más volátil que el mercado.
              - **1**: Misma volatilidad que el mercado.
              - **< 1**: Menos volátil que el mercado.
            
            - **Correlación**: Grado de relación entre los retornos del portafolio y el benchmark.
              - **1**: Movimientos perfectamente alineados.
              - **0**: Sin relación.
              - **-1**: Movimientos opuestos.
            
            - **Volatilidad Anual**: Medida del riesgo del portafolio o benchmark.
            
            - **Ratio de Sharpe**: Retorno ajustado por riesgo (mayor es mejor).
            
            - **MEP**: Dólar MEP calculado a partir de los bonos AL30/AL30D, usado como referencia para activos en pesos argentinos.
            """)
    
    simbolo_seleccionado = st.selectbox(
        "Seleccione un activo para análisis técnico:",
        options=simbolos
    )
{{ ... }}
    
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
