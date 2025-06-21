import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
from datetime import date, timedelta, datetime, timezone
import numpy as np
import yfinance as yf
import scipy.optimize as op
from scipy import stats
import random
import warnings
import streamlit.components.v1 as components
import time
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

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
        color: #0d6efd;
    }
    
    /* Mejora de botones */
    .stButton>button {
        background-color: #0d6efd !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
    }
    
    .stButton>button:hover {
        background-color: #0b5ed7 !important;
    }
}  /* Cerrar el bloque CSS */

<style>
    /* Mejora de botones */
    .stButton>button {
        background-color: #0d6efd !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
    }
    
    .stButton>button:hover {
        background-color: #0b5ed7 !important;
    }
}  /* Cerrar el bloque CSS */
}  /* Cerrar el bloque CSS */
    
    /* Mejora de botones */
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
    """
    Obtiene el portafolio del cliente con información detallada de cada activo.
    
    Args:
        token_portador (str): Token de autenticación
        id_cliente (str): ID del cliente
        pais (str): País del portafolio (default: 'Argentina')
        
    Returns:
        dict: Diccionario con la información del portafolio o None en caso de error
    """
    url_portafolio = f'https://api.invertironline.com/api/v2/Asesores/Portafolio/{id_cliente}/{pais}'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    try:
        respuesta = requests.get(url_portafolio, headers=encabezados)
        if respuesta.status_code == 200:
            portafolio = respuesta.json()
            
            # Verificar si la respuesta tiene la estructura esperada
            if 'activos' not in portafolio:
                portafolio['activos'] = []
                
            # Asegurarse de que cada activo tenga la estructura correcta
            for activo in portafolio['activos']:
                if 'titulo' not in activo:
                    activo['titulo'] = {}
                if 'simbolo' not in activo['titulo']:
                    activo['titulo']['simbolo'] = ''
                if 'mercado' not in activo['titulo']:
                    activo['titulo']['mercado'] = 'BCBA'  # Valor por defecto
                if 'tipo' not in activo['titulo']:
                    activo['titulo']['tipo'] = 'ACCIONES'  # Valor por defecto
                    
            return portafolio
        else:
            st.error(f'Error al obtener portafolio: {respuesta.status_code} - {respuesta.text}')
            return None
    except Exception as e:
        st.error(f'Error al obtener portafolio: {str(e)}')
        return None
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
    
    # Convertir fechas a formato ISO (YYYY-MM-DD) para compatibilidad con la API
    try:
        fecha_desde_iso = pd.to_datetime(fecha_desde).strftime('%Y-%m-%d')
        fecha_hasta_iso = pd.to_datetime(fecha_hasta).strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        st.error("Formato de fecha inválido. Por favor, use un formato reconocido.")
        return None

    # Preparar el cuerpo de la solicitud (payload) dinámicamente
    payload = {
        "clientes": clientes,
        "from": fecha_desde_iso,
        "to": fecha_hasta_iso,
        "dateType": tipo_fecha,
    }

    # Añadir parámetros opcionales solo si tienen un valor asignado
    if estado:
        payload['status'] = estado
    if tipo_operacion:
        payload['type'] = tipo_operacion
    if pais:
        payload['country'] = pais
    if moneda:
        payload['currency'] = moneda
    if cuenta_comitente:
        payload['cuentaComitente'] = cuenta_comitente
    
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
    url = "https://api.invertironline.com/api/v2/Cotizaciones/cauciones/argentina/Todos"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_portador}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
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

def refrescar_token(refresh_token):
    """
    Refresca el token de acceso usando el refresh token
    """
    try:
        token_url = 'https://api.invertironline.com/token'
        payload = {
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.post(token_url, data=payload, headers=headers)
        if response.status_code == 200:
            tokens = response.json()
            return tokens['access_token'], tokens['refresh_token']
        else:
            print(f'Error al refrescar token: {response.status_code}')
            print(response.text)
            return None, None
    except Exception as e:
        print(f'Error en refrescar_token: {str(e)}')
        return None, None

def obtener_serie_historica_iol(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="SinAjustar"):
    """
    Obtiene series históricas para diferentes tipos de activos
    
    Args:
        token_portador (str): Token de autenticación
        mercado (str): Mercado del activo (ej: 'BCBA', 'NYSE', 'NASDAQ', 'ROFEX')
        simbolo (str): Símbolo del activo
        fecha_desde (str): Fecha de inicio en formato 'YYYY-MM-DD'
        fecha_hasta (str): Fecha de fin en formato 'YYYY-MM-DD'
        ajustada (str): 'Ajustada' o 'SinAjustar' (default: 'SinAjustar')
        
    Returns:
        DataFrame: Serie histórica del activo o None en caso de error
    """
    try:
        # Construir la URL para la API
        url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
        
        # Configurar headers con el token
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token_portador}'
        }
        
        # Realizar la solicitud
        response = requests.get(url, headers=headers, timeout=30)
        
        # Verificar si el token expiró
        if response.status_code == 401:
            print("Token expirado, intentando refrescar...")
            # Aquí necesitarías implementar la lógica para refrescar el token
            # nuevo_token, nuevo_refresh = refrescar_token(refresh_token)
            # if nuevo_token:
            #     return obtener_serie_historica_iol(nuevo_token, mercado, simbolo, fecha_desde, fecha_hasta, ajustada)
            return None
            
        response.raise_for_status()
        
        # Procesar la respuesta
        data = response.json()
        
        # Convertir a DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
            if not df.empty and 'fecha' in df.columns:
                df['fecha'] = pd.to_datetime(df['fecha'])
                df.set_index('fecha', inplace=True)
                return df
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud para {simbolo} en {mercado}: {str(e)}")
        return None
    except Exception as e:
        print(f"Error inesperado al procesar {simbolo}: {str(e)}")
        return None

def get_historical_data_for_optimization(token_portador, simbolos, fecha_desde, fecha_hasta):
    """
    Obtiene datos históricos para optimización con manejo mejorado de errores,
    reintentos automáticos y soporte para diferentes tipos de activos.
    
    Args:
        token_portador (str): Token de autenticación para la API
        simbolos (list): Lista de tuplas (símbolo, mercado)
        fecha_desde (str): Fecha de inicio en formato 'YYYY-MM-DD'
        fecha_hasta (str): Fecha de fin en formato 'YYYY-MM-DD'
        
    Returns:
        tuple: (mean_returns, cov_matrix, df_precios) o (None, None, None) en caso de error
    """
    precios = {}
    errores = []
    max_retries = 3  # Aumentar el número de reintentos
    min_data_points = 20  # Mínimo de puntos de datos requeridos
    
    with st.spinner("Obteniendo datos históricos..."):
        progress_bar = st.progress(0)
        total_symbols = len(simbolos)
        
        for idx, (simbolo, mercado) in enumerate(simbolos):
            if not simbolo or not isinstance(simbolo, str) or not simbolo.strip():
                st.warning(f"Símbolo inválido en la posición {idx+1}")
                errores.append(f"Símbolo inválido en posición {idx+1}")
                continue
                
            progress = (idx + 1) / total_symbols
            progress_bar.progress(progress, text=f"Procesando {simbolo} ({idx+1}/{total_symbols})")
            
            # Manejar diferentes tipos de activos
            try:
                # 1. Manejar FCIs (Fondos Comunes de Inversión)
                if mercado.upper() == 'FCI':
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
                
                # 2. Manejar otros tipos de activos (acciones, bonos, etc.)
                for attempt in range(max_retries):
                    try:
                        # Intentar obtener datos con el mercado especificado
                        serie = obtener_serie_historica_iol(
                            token_portador=token_portador,
                            mercado=mercado.upper(),
                            simbolo=simbolo,
                            fecha_desde=fecha_desde,
                            fecha_hasta=fecha_hasta
                        )
                        
                        if serie is not None and not serie.empty:
                            if len(serie) >= min_data_points:
                                precios[simbolo] = serie
                                break  # Salir del bucle de reintentos si es exitoso
                            else:
                                st.warning(f"Datos insuficientes para {simbolo} ({len(serie)} puntos)")
                                errores.append(f"{simbolo} (insuficientes datos)")
                                break
                        
                    except Exception as e:
                        if attempt == max_retries - 1:  # Último intento
                            st.warning(f"No se pudo obtener datos para {simbolo} ({mercado}) después de {max_retries} intentos: {str(e)}")
                            errores.append(f"{simbolo} ({mercado})")
                        time.sleep(1)  # Pequeña pausa entre reintentos
                        continue
                
                # Pequeña pausa entre solicitudes para no sobrecargar el servidor
                time.sleep(0.5)
                
            except Exception as e:
                st.error(f"Error inesperado procesando {simbolo} ({mercado}): {str(e)}")
                errores.append(f"{simbolo} (error: {str(e)})")
        
        progress_bar.empty()
        
        # Mostrar resumen de errores
        if errores:
            st.warning(f"⚠️ No se pudieron obtener datos para {len(errores)} de {len(simbolos)} activos")
            with st.expander("Ver detalles de errores"):
                for error in errores:
                    st.write(f"- {error}")
        
        if precios:
            st.success(f"✅ Datos obtenidos para {len(precios)} de {len(simbolos)} activos")
            
            # Asegurar que todas las series tengan la misma longitud
            min_length = min(len(s) for s in precios.values()) if precios else 0
            if min_length < min_data_points:
                st.error(f"❌ Se requieren al menos {min_data_points} puntos de datos para la optimización. Máximo disponible: {min_length}")
                return None, None, None
                
            # Crear DataFrame con las series alineadas
            df_precios = pd.DataFrame({k: v.iloc[-min_length:] for k, v in precios.items()})
            
            # Calcular retornos y validar
            returns = df_precios.pct_change().dropna()
            
            # Validar que haya suficientes datos
            if returns.empty or len(returns) < min_data_points // 2:
                st.error("❌ No hay suficientes datos para el análisis después del cálculo de retornos")
                return None, None, None
                
            # Eliminar activos con volatilidad cero o NaN
            valid_assets = returns.columns[(returns.std() > 0) & (returns.std().notna())]
            
            if len(valid_assets) < 2:
                st.error("❌ No hay suficientes activos válidos (volatilidad > 0) para la optimización")
                return None, None, None
                
            if len(valid_assets) < len(returns.columns):
                removed_assets = set(returns.columns) - set(valid_assets)
                st.warning(f"Se eliminaron {len(removed_assets)} activos con volatilidad cero o NaN: {', '.join(removed_assets)}")
                returns = returns[valid_assets]
                df_precios = df_precios[valid_assets]
            
            # Calcular métricas finales
            mean_returns = returns.mean()
            cov_matrix = returns.cov()
            
            # Validar que la matriz de covarianza sea definida positiva
            try:
                np.linalg.cholesky(cov_matrix)
            except np.linalg.LinAlgError:
                st.warning("La matriz de covarianza no es definida positiva. Aplicando ajuste...")
                # Aplicar un pequeño ajuste a la diagonal para asegurar definición positiva
                min_eig = np.min(np.real(np.linalg.eigvals(cov_matrix)))
                if min_eig < 0:
                    cov_matrix -= 1.1 * min_eig * np.eye(*cov_matrix.shape)
            
            return mean_returns, cov_matrix, df_precios
        
        st.error("❌ No se pudieron cargar los datos históricos para ningún activo")
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

    def compute_portfolio(self, target_return=None, method='max_sharpe'):
        """
        Optimiza el portafolio según el método especificado.
        
        Args:
            target_return (float, optional): Retorno objetivo para optimización con restricción
            method (str): Método de optimización ('max_sharpe', 'min_vol', 'efficient_risk', 'efficient_return')
            
        Returns:
            dict: Resultados de la optimización o None en caso de error
        """
        if self.mean_returns is None or self.cov_matrix is None:
            st.error("❌ Error: Datos no cargados. Ejecute load_data() primero.")
            return None
            
        n_assets = len(self.rics)
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        # Función objetivo: Minimizar la volatilidad (para max_sharpe y min_vol)
        def objective(weights):
            return np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
            
        # Restricción: La suma de los pesos debe ser 1
        constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        
        # Restricción adicional según el método
        if method == 'max_sharpe':
            # Para maximizar el ratio de Sharpe, minimizamos el negativo del ratio
            def neg_sharpe(weights):
                port_return = np.sum(self.mean_returns * weights)
                port_vol = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
                return -(port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0
                
            result = minimize(neg_sharpe, 
                            x0=np.ones(n_assets) / n_assets,
                            method='SLSQP',
                            bounds=bounds,
                            constraints=constraints)
                            
        elif method == 'min_vol':
            # Minimizar la volatilidad
            result = minimize(objective,
                            x0=np.ones(n_assets) / n_assets,
                            method='SLSQP',
                            bounds=bounds,
                            constraints=constraints)
                            
        elif method == 'efficient_return' and target_return is not None:
            # Minimizar volatilidad con retorno objetivo
            constraints.append({
                'type': 'eq',
                'fun': lambda x: np.sum(self.mean_returns * x) - target_return
            })
            
            result = minimize(objective,
                            x0=np.ones(n_assets) / n_assets,
                            method='SLSQP',
                            bounds=bounds,
                            constraints=constraints)
                            
        else:
            st.error(f"Método de optimización no soportado: {method}")
            return None
            
        if result.success:
            weights = result.x
            portfolio_return = np.sum(self.mean_returns * weights)
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
            sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_vol if portfolio_vol > 0 else 0
            
            self.optimal_weights = weights
            self.optimal_metrics = {
                'return': portfolio_return,
                'volatility': portfolio_vol,
                'sharpe_ratio': sharpe_ratio,
                'weights': dict(zip(self.rics, weights))
            }
            self.optimization_successful = True
            
            return self.optimal_metrics
        else:
            st.error(f"Error en la optimización: {result.message}")
            return None
        
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
    def __init__(self, symbols, notional, start_date, end_date, risk_free_rate=0.40):
        """
        Inicializa el gestor de portafolio.
        
        Args:
            symbols (list): Lista de tuplas (símbolo, mercado)
            notional (float): Monto total del portafolio
            start_date (str): Fecha de inicio en formato 'YYYY-MM-DD'
            end_date (str): Fecha de fin en formato 'YYYY-MM-DD'
            risk_free_rate (float): Tasa libre de riesgo anual (default: 40% para Argentina)
        """
        self.symbols = symbols
        self.symbols_list = [s[0] for s in symbols]
        self.notional = notional
        self.start_date = start_date
        self.end_date = end_date
        self.risk_free_rate = risk_free_rate
        
        # Datos del portafolio
        self.prices = None
        self.returns = None
        self.mean_returns = None
        self.cov_matrix = None
        self.correlation_matrix = None
        self.volatilities = None
        
        # Resultados de optimización
        self.optimal_weights = None
        self.optimal_metrics = None
        self.efficient_frontier = None
        self.optimization_successful = False
        self.manager = None
    
{{ ... }}
    def load_data(self, token_portador):
    """
    Carga los datos históricos para los símbolos del portafolio.
    
    Args:
        token_portador (str): Token de autenticación para la API
        
    Returns:
        bool: True si los datos se cargaron correctamente, False en caso contrario
    """
    try:
        st.info("⏳ Cargando datos históricos...")
        
        # Obtener datos históricos
        mean_returns, cov_matrix, df_prices = get_historical_data_for_optimization(
            token_portador, 
            self.symbols, 
            self.start_date, 
            self.end_date
        )
        
        if mean_returns is None or cov_matrix is None or df_prices is None:
            st.error("❌ No se pudieron cargar los datos históricos")
            return False
            
        # Filtrar los símbolos que sí se cargaron correctamente
        valid_symbols = [s for s in self.symbols_list if s in df_prices.columns]
        if len(valid_symbols) < 2:
            st.error("❌ Se requieren al menos 2 activos válidos para la optimización")
            return False
            
        # Actualizar atributos con los datos cargados
        self.symbols_list = valid_symbols
        self.prices = df_prices[valid_symbols]
        self.returns = self.prices.pct_change().dropna()
        self.mean_returns = self.returns.mean() * 252  # Anualizado
        self.cov_matrix = self.returns.cov() * 252     # Anualizado
        self.correlation_matrix = self.returns.corr()
        self.volatilities = self.returns.std() * np.sqrt(252)  # Volatilidad anualizada
        
        # Verificar que la matriz de covarianza sea positiva definida
        if not np.all(np.linalg.eigvals(self.cov_matrix) > 0):
            st.warning("⚠️ La matriz de covarianza no es positiva definida. Se ajustará.")
            self.cov_matrix = self._adjust_covariance_matrix(self.cov_matrix)
        
        st.success("✅ Datos históricos cargados correctamente")
        return True
        
    except Exception as e:
        st.error(f"❌ Error al cargar los datos: {str(e)}")
        return False
        
    def _adjust_covariance_matrix(self, cov_matrix):
        """Ajusta la matriz de covarianza para asegurar que sea positiva definida"""
        try:
            # Método de Higham para encontrar la matriz más cercana positiva definida
            from scipy.linalg import sqrtm
            
            # Calcular la raíz cuadrada de la matriz
            sqrt_cov = sqrtm(cov_matrix)
            # Calcular la matriz más cercana positiva definida
            adjusted_cov = (sqrt_cov + sqrt_cov.T) / 2
            
            # Asegurarse de que la diagonal sea positiva
            np.fill_diagonal(adjusted_cov, np.maximum(np.diag(adjusted_cov), 1e-10))
            
            return adjusted_cov
        except:
            # Si falla, usar un método más simple
            return np.maximum(cov_matrix, 1e-10)
    
    def compute_portfolio(self, strategy='markowitz', target_return=None):
        if not self.data_loaded or self.returns is None:
            return None
        
{{ ... }}
        try:
            if self.manager:
                # Usar el manager avanzado
                portfolio_output = self.manager.compute_portfolio(strategy, target_return)
                return portfolio_output
            else:
                # Fallback a optimización básica
                
            if strategy == 'equi-weight':
                weights = np.array([1/n_assets] * n_assets)
            else:
                weights = optimize_portfolio(self.returns, target_return=target_return)
                
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
        
    
    activos = portafolio.get('activos', [])
    if not activos:
        st.warning("El portafolio está vacío")
        return
    
    simbolos = []
    activos_validos = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo')
        mercado = titulo.get('mercado', 'BCBA').upper()
        tipo = titulo.get('tipo', 'ACCIONES').upper()
        
        if not simbolo:
            continue
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
    
    # Obtener símbolos con su información de mercado
    simbolos = []
    activos_validos = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo')
        mercado = titulo.get('mercado', 'BCBA').upper()
        tipo = titulo.get('tipo', 'ACCIONES').upper()
        
        if not simbolo:
            continue
            
        # Mapear tipos de activo a mercados si es necesario
        if tipo == 'FCI':
            mercado = 'FCI'
        elif mercado not in ['BCBA', 'NYSE', 'NASDAQ', 'AMEX', 'BMA', 'ROFEX', 'MERVAL', 'DOW JONES', 'S&P', 'NASDAQ100', 'DOW JONES COMP', 'ESTADOS UNIDOS', 'MERVAL 25', 'MERVAL ARGENTINA', 'MERVAL ARGENTINA PESOS']:
            # Si el mercado no es uno de los conocidos, intentar determinarlo
            if any(x in tipo for x in ['CEDEAR', 'CEDEARS']):
                mercado = 'BCBA'  # Asumir que los CEDEARs están en BCBA
            elif any(x in tipo for x in ['BONO', 'BONOS', 'OBLIGACIONES']):
                mercado = 'BCBA'  # Asumir que los bonos están en BCBA
            else:
                mercado = 'BCBA'  # Valor por defecto
                
        # Agregar el símbolo y mercado a la lista
        simbolos.append((simbolo, mercado))
        activos_validos.append(activo)
    
    if not simbolos:
        st.warning("No se encontraron símbolos válidos con información de mercado")
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
                ("🏠 Inicio", "📊 Análisis de Portafolio", "📈 Optimización de Portafolio", "💰 Tasas de Caución", "👨\u200d💼 Panel del Asesor"),
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
            elif opcion == "📈 Optimización de Portafolio":
                if 'token_acceso' in st.session_state and st.session_state.token_acceso:
                    mostrar_optimizacion_portafolio_avanzada()
                else:
                    st.warning("Por favor inicie sesión para acceder a la optimización de portafolio")
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

def mostrar_optimizacion_portafolio_avanzada():
    """
    Muestra la interfaz de optimización de portafolio avanzada
    """
    st.title("📈 Optimización de Portafolio")
    
    if 'token_acceso' not in st.session_state or not st.session_state.token_acceso:
        st.warning("Por favor, inicie sesión para acceder a la optimización de portafolio")
        return
    
    # Inicializar el optimizador
    optimizador = PortfolioOptimizer(st.session_state.token_acceso)
    
    # Configuración de la optimización
    st.sidebar.header("Configuración de Optimización")
    
    # Selección de paneles
    paneles_disponibles = optimizador.paneles_disponibles
    paneles_seleccionados = st.sidebar.multiselect(
        "Seleccione los paneles:",
        options=paneles_disponibles,
        default=paneles_disponibles[:2]  # Por defecto selecciona los primeros 2 paneles
    )
    
    # Parámetros de optimización
    col1, col2 = st.sidebar.columns(2)
    with col1:
        cantidad_activos = st.number_input(
            "Activos por panel:",
            min_value=1,
            max_value=20,
            value=5,
            step=1
        )
    
    with col2:
        capital_ars = st.number_input(
            "Capital disponible (ARS):",
            min_value=1000.0,
            max_value=10000000.0,
            value=100000.0,
            step=1000.0
        )
    
    # Fechas para el análisis histórico
    fecha_hoy = datetime.now().date()
    fecha_desde = st.sidebar.date_input(
        "Fecha de inicio:",
        value=fecha_hoy - timedelta(days=365),
        max_value=fecha_hoy
    )
    
    # Botón para ejecutar la optimización
    if st.sidebar.button("🔍 Ejecutar Optimización", use_container_width=True):
        with st.spinner("Optimizando portafolio..."):
            try:
                # Obtener tickers disponibles
                tickers_por_panel, _ = optimizador.obtener_tickers_por_panel(
                    paneles_seleccionados
                )
                
                # Seleccionar activos aleatorios
                df_historicos, seleccion = optimizador.seleccionar_activos_aleatorios(
                    tickers_por_panel=tickers_por_panel,
                    paneles_seleccionados=paneles_seleccionados,
                    cantidad_activos=cantidad_activos,
                    capital_ars=capital_ars
                )
                
                if df_historicos.empty:
                    st.error("No se pudieron obtener datos históricos suficientes.")
                    return
                
                # Calcular métricas
                st.subheader("📊 Métricas de los Activos")
                metricas = optimizador.calcular_metricas_rendimiento(df_historicos)
                
                if not metricas.empty:
                    st.dataframe(metricas.sort_values('retorno_anual', ascending=False))
                
                # Optimizar portafolio
                st.subheader("⚖️ Asignación Óptima")
                resultado_optimizacion = optimizador.optimizar_portafolio(df_historicos)
                
                if resultado_optimizacion:
                    # Mostrar pesos óptimos
                    df_pesos = pd.DataFrame.from_dict(
                        resultado_optimizacion['pesos'], 
                        orient='index', 
                        columns=['Peso']
                    )
                    df_pesos['Peso'] = (df_pesos['Peso'] * 100).round(2)
                    df_pesos = df_pesos.sort_values('Peso', ascending=False)
                    
                    # Mostrar tabla de pesos
                    st.dataframe(df_pesos)
                    
                    # Mostrar métricas del portafolio
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Retorno Esperado Anual", f"{resultado_optimizacion['retorno_esperado']*100:.2f}%")
                    with col2:
                        st.metric("Volatilidad Anual", f"{resultado_optimizacion['volatilidad']*100:.2f}%")
                    with col3:
                        st.metric("Ratio de Sharpe", f"{resultado_optimizacion['sharpe_ratio']:.2f}")
                    
                    # Mostrar gráfico de torta de la asignación
                    fig = go.Figure(data=[go.Pie(
                        labels=df_pesos.index,
                        values=df_pesos['Peso'],
                        hole=.3
                    )])
                    fig.update_layout(title="Distribución del Portafolio")
                    st.plotly_chart(fig, use_container_width=True)
                    
                else:
                    st.warning("No se pudo calcular la optimización con los datos disponibles.")
            
            except Exception as e:
                st.error(f"Error al optimizar el portafolio: {str(e)}")
                st.exception(e)

def obtener_tipo_activo(token_portador, simbolo):
    """
    Obtiene automáticamente el tipo de activo y mercado para un símbolo dado
    
    Args:
        token_portador (str): Token de autenticación
        simbolo (str): Símbolo del activo
        
    Returns:
        dict: Diccionario con información sobre el tipo de activo y mercado
    """
    try:
        # Primero intentamos obtener información del activo
        url = "https://api.invertironline.com/api/v2/activos"
        headers = obtener_encabezado_autorizacion(token_portador)
        
        # Realizamos la solicitud
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Procesamos la respuesta
        activos = response.json()
        
        # Buscamos el activo por símbolo
        for activo in activos:
            if activo.get('simbolo') == simbolo:
                return {
                    'mercado': activo.get('mercado'),
                    'tipo': activo.get('tipo'),
                    'pais': activo.get('pais'),
                    'moneda': activo.get('moneda')
                }
        
        # Si no encontramos el activo, intentamos con la API de cotizaciones
        url_cotizaciones = f"https://api.invertironline.com/api/v2/cotizaciones/{simbolo}"
        response_cotizaciones = requests.get(url_cotizaciones, headers=headers)
        
        if response_cotizaciones.status_code == 200:
            cotizacion = response_cotizaciones.json()
            return {
                'mercado': cotizacion.get('mercado'),
                'tipo': cotizacion.get('tipo'),
                'pais': cotizacion.get('pais'),
                'moneda': cotizacion.get('moneda')
            }
        
        return None
    
    except Exception as e:
        print(f"Error al obtener tipo de activo: {str(e)}")
        return None

@dataclass
class HistoricalDataRequest:
    """Clase para manejar las solicitudes de datos históricos."""
    simbolo: str
    mercado: str = 'BCBA'  # Por defecto mercado local
    fecha_desde: str = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    fecha_hasta: str = datetime.now().strftime('%Y-%m-%d')
    ajustada: bool = False
    frecuencia: str = 'diaria'  # 'diaria', 'semanal', 'mensual'
    max_reintentos: int = 3
    timeout: int = 30


class PortfolioOptimizer:
    def __init__(self, token_portador: str):
        """
        Inicializa el optimizador de portafolio con el token de autenticación.
        
        Args:
            token_portador (str): Token de autenticación para la API de InvertirOnline
        """
        self.token_portador = token_portador
        self.paneles_disponibles = [
            'acciones', 'cedears', 'aDRs', 'titulosPublicos', 'obligacionesNegociables'
        ]
        self._session = self._create_session()
        
    def _create_session(self):
        """Crea una sesión con reintentos automáticos."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def obtener_encabezado_autorizacion(self) -> dict:
        """Retorna los encabezados de autorización."""
        return {
            'Authorization': f'Bearer {self.token_portador}'
        }

    def obtener_tickers_por_panel(self, paneles: list, pais: str = 'Argentina') -> tuple:
        """
        Obtiene los tickers disponibles por panel.
        
        Args:
            paneles: Lista de paneles a consultar
            pais: País de los instrumentos
            
        Returns:
            Tupla con (tickers_por_panel, DataFrame con tickers y paneles)
        """
        tickers_por_panel = {}
        tickers_data = []
        
        for panel in paneles:
            try:
                url = f'https://api.invertironline.com/api/v2/cotizaciones-orleans/{panel}/{pais}/Operables'
                params = {
                    'cotizacionInstrumentoModel.instrumento': panel,
                    'cotizacionInstrumentoModel.pais': pais.lower()
                }
                
                response = requests.get(
                    url, 
                    headers=self.obtener_encabezado_autorizacion(), 
                    params=params
                )
                
                if response.status_code == 200:
                    datos = response.json()
                    tickers = [titulo['simbolo'] for titulo in datos.get('titulos', [])]
                    tickers_por_panel[panel] = tickers
                    tickers_data.extend([{'panel': panel, 'simbolo': t} for t in tickers])
                else:
                    st.warning(f'Error al obtener tickers para {panel}: {response.status_code}')
                    
            except Exception as e:
                st.error(f'Error en obtener_tickers_por_panel para {panel}: {str(e)}')
        
        return tickers_por_panel, pd.DataFrame(tickers_data)

    def calcular_metricas_rendimiento(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula métricas de rendimiento para los activos.
        """
        if df.empty:
            return pd.DataFrame()
            
        # Asegurarse de que tenemos las columnas necesarias
        col_precio = next((c for c in ['ultimoPrecio', 'precio', 'cierre'] 
                          if c in df.columns), None)
        
        if col_precio is None:
            return pd.DataFrame()
        
        # Calcular retornos diarios
        retornos = df.groupby('simbolo')[col_precio].pct_change().dropna()
        
        # Calcular métricas
        metricas = {
            'retorno_anual': retornos.groupby('simbolo').apply(
                lambda x: (1 + x).prod() ** (252/len(x)) - 1 if len(x) > 0 else 0
            ),
            'volatilidad_anual': retornos.groupby('simbolo').std() * np.sqrt(252),
            'sharpe_ratio': retornos.groupby('simbolo').apply(
                lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0
            ),
            'max_drawdown': retornos.groupby('simbolo').apply(
                lambda x: (1 + x).cumprod().div((1 + x).cumprod().cummax()).sub(1).min()
            )
        }
        
        return pd.DataFrame(metricas)

    def obtener_tickers_por_panel(self, paneles: List[str], pais: str = 'Argentina') -> Tuple[Dict[str, List[str]], pd.DataFrame]:
        """
        Obtiene los tickers disponibles para los paneles especificados.
        
        Args:
            paneles: Lista de paneles a consultar (ej: ['acciones', 'cedears'])
            pais: País de los instrumentos
            
        Returns:
            Tuple[Dict[str, List[str]], pd.DataFrame]: 
                - Diccionario con paneles como claves y listas de tickers como valores
                - DataFrame con todos los tickers y sus paneles
        """
        tickers_por_panel = {}
        tickers_df = pd.DataFrame(columns=['panel', 'simbolo'])
        
        for panel in paneles:
            if panel not in self.paneles_disponibles:
                st.warning(f"Panel no disponible: {panel}")
                continue
                
            url = f'https://api.invertironline.com/api/v2/cotizaciones-orleans/{panel}/{pais}/Operables'
            params = {
                'cotizacionInstrumentoModel.instrumento': panel,
                'cotizacionInstrumentoModel.pais': pais.lower()
            }
            
            try:
                respuesta = self._session.get(
                    url,
                    headers=self.obtener_encabezado_autorizacion(),
                    params=params,
                    timeout=30
                )
                respuesta.raise_for_status()
                
                datos = respuesta.json()
                tickers = [titulo['simbolo'] for titulo in datos.get('titulos', [])]
                tickers_por_panel[panel] = tickers
                
                # Crear DataFrame con los tickers del panel
                panel_df = pd.DataFrame({'panel': panel, 'simbolo': tickers})
                tickers_df = pd.concat([tickers_df, panel_df], ignore_index=True)
                
            except Exception as e:
                st.error(f'Error al obtener tickers para el panel {panel}: {str(e)}')
                continue
                
        return tickers_por_panel, tickers_df
        
    def construir_portafolio_aleatorio(
        self,
        paneles_seleccionados: List[str],
        cantidad_activos: int,
        capital_ars: float,
        fecha_desde: str = None,
        fecha_hasta: str = None,
        ajustada: bool = False
    ) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
        """
        Construye un portafolio aleatorio con restricción de capital.
        
        Args:
            paneles_seleccionados: Lista de paneles a incluir
            cantidad_activos: Número de activos por panel a seleccionar
            capital_ars: Capital disponible en ARS
            fecha_desde: Fecha de inicio en formato 'YYYY-MM-DD'
            fecha_hasta: Fecha de fin en formato 'YYYY-MM-DD'
            ajustada: Si es True, usa precios ajustados
            
        Returns:
            Tuple[pd.DataFrame, Dict[str, List[str]]]: 
                - DataFrame con las series históricas
                - Diccionario con los activos seleccionados por panel
        """
        # Establecer fechas por defecto si no se especifican
        if fecha_desde is None:
            fecha_desde = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if fecha_hasta is None:
            fecha_hasta = datetime.now().strftime('%Y-%m-%d')
            
        # Obtener tickers por panel
        tickers_por_panel, _ = self.obtener_tickers_por_panel(paneles_seleccionados)
        
        series_historicas = pd.DataFrame()
        seleccion_final = {}
        
        for panel in paneles_seleccionados:
            if panel not in tickers_por_panel or not tickers_por_panel[panel]:
                continue
                
            tickers = tickers_por_panel[panel]
            random.shuffle(tickers)
            seleccionados = []
            
            # Intentar obtener datos para los tickers hasta completar la cantidad deseada
            for simbolo in tickers:
                if len(seleccionados) >= cantidad_activos:
                    break
                    
                try:
                    # Crear solicitud de datos históricos
                    req = HistoricalDataRequest(
                        simbolo=simbolo,
                        mercado='BCBA',
                        fecha_desde=fecha_desde,
                        fecha_hasta=fecha_hasta,
                        ajustada=ajustada
                    )
                    
                    # Obtener datos históricos
                    resultados = self.obtener_serie_historica_universal(req)
                    if not resultados or simbolo not in resultados:
                        continue
                        
                    df = resultados[simbolo]
                    if df.empty:
                        continue
                        
                    # Buscar columna de precio
                    col_precio = next((c for c in ['ultimoPrecio', 'ultimo_precio', 'precio', 'close', 'cierre'] 
                                    if c in df.columns), None)
                    if not col_precio:
                        continue
                        
                    # Obtener último precio disponible
                    precio = df[col_precio].dropna().iloc[-1]
                    if pd.isna(precio) or precio <= 0:
                        continue
                        
                    # Verificar si el activo es asequible
                    if precio > capital_ars and capital_ars > 0:
                        continue
                        
                    # Agregar a la selección
                    df['simbolo'] = simbolo
                    df['panel'] = panel
                    seleccionados.append((simbolo, df, precio))
                    capital_ars -= precio
                    
                except Exception as e:
                    st.warning(f"Error procesando {simbolo}: {str(e)}")
                    continue
            
            # Guardar selección final
            if seleccionados:
                seleccion_final[panel] = [s[0] for s in seleccionados]
                for _, df, _ in seleccionados:
                    series_historicas = pd.concat([series_historicas, df], ignore_index=True)
        
        return series_historicas, seleccion_final
    
    def calcular_metricas_portafolio_aleatorio(
        self,
        series_historicas: pd.DataFrame,
        seleccion_final: Dict[str, List[str]]
    ) -> Dict[str, pd.Series]:
        """
        Calcula métricas de rendimiento para los portafolios aleatorios.
        
        Args:
            series_historicas: DataFrame con las series históricas
            seleccion_final: Diccionario con los activos seleccionados por panel
            
        Returns:
            Dict[str, pd.Series]: Diccionario con las métricas de cada portafolio
        """
        portafolios_val = {}
        
        for panel, simbolos in seleccion_final.items():
            if not simbolos:
                continue
                
            df_panel = series_historicas[series_historicas['panel'] == panel].copy()
            if df_panel.empty:
                continue
                
            # Buscar columnas de fecha y precio
            fecha_col = next((c for c in ['fecha', 'date', 'fechaHora', 'fechaCotizacion'] 
                           if c in df_panel.columns), None)
            col_precio = next((c for c in ['ultimoPrecio', 'ultimo_precio', 'precio', 'close', 'cierre'] 
                             if c in df_panel.columns), None)
            
            if not fecha_col or not col_precio:
                continue
                
            try:
                # Convertir a datetime si es necesario
                if not pd.api.types.is_datetime64_any_dtype(df_panel[fecha_col]):
                    df_panel[fecha_col] = pd.to_datetime(df_panel[fecha_col])
                
                # Pivotear para tener fechas como índice y columnas por símbolo
                df_pivot = df_panel.pivot_table(
                    index=fecha_col, 
                    columns='simbolo', 
                    values=col_precio,
                    aggfunc='first'
                )
                
                # Filtrar solo los símbolos seleccionados
                df_pivot = df_pivot[df_pivot.columns.intersection(simbolos)]
                
                if df_pivot.empty:
                    continue
                    
                # Normalizar para calcular retornos
                df_normalized = df_pivot / df_pivot.iloc[0]
                
                # Calcular valor del portafolio (suma ponderada)
                portafolio_val = df_normalized.sum(axis=1) / len(df_normalized.columns)
                portafolios_val[panel] = portafolio_val
                
            except Exception as e:
                st.error(f"Error al calcular métricas para {panel}: {str(e)}")
                continue
                
        return portafolios_val
    
    def graficar_portafolio_aleatorio(
        self,
        portafolios_val: Dict[str, pd.Series],
        titulo: str = "Evolución de Portafolios Aleatorios"
    ) -> None:
        """
        Genera gráficos para visualizar los portafolios aleatorios.
        
        Args:
            portafolios_val: Diccionario con las series de valor de los portafolios
            titulo: Título del gráfico principal
        """
        if not portafolios_val:
            st.warning("No hay datos para graficar")
            return
            
        # Crear figura para el gráfico de líneas
        fig_line = go.Figure()
        
        for panel, serie in portafolios_val.items():
            fig_line.add_trace(go.Scatter(
                x=serie.index,
                y=serie.values,
                mode='lines',
                name=f'Portafolio {panel}'
            ))
        
        # Configurar diseño del gráfico
        fig_line.update_layout(
            title=titulo,
            xaxis_title='Fecha',
            yaxis_title='Valor Normalizado',
            legend_title='Paneles',
            hovermode='x',
            template='plotly_white'
        )
        
        # Mostrar gráfico en Streamlit
        st.plotly_chart(fig_line, use_container_width=True)
        
        # Calcular y mostrar métricas para cada portafolio
        for panel, serie in portafolios_val.items():
            if len(serie) < 2:
                continue
                
            with st.expander(f"Métricas - {panel}"):
                col1, col2, col3 = st.columns(3)
                
                # Calcular retornos
                retornos = serie.pct_change().dropna()
                
                # Métricas básicas
                retorno_total = (serie.iloc[-1] / serie.iloc[0] - 1) * 100
                volatilidad = retornos.std() * np.sqrt(252) * 100  # Anualizada
                sharpe = (retornos.mean() / retornos.std()) * np.sqrt(252) if retornos.std() > 0 else 0
                
                col1.metric("Retorno Total", f"{retorno_total:.2f}%")
                col2.metric("Volatilidad Anual", f"{volatilidad:.2f}%")
                col3.metric("Ratio de Sharpe", f"{sharpe:.2f}")
                
                # Gráfico de distribución de retornos
                fig_hist = go.Figure()
                fig_hist.add_trace(go.Histogram(
                    x=retornos * 100,
                    nbinsx=50,
                    name='Frecuencia',
                    marker_color='#1f77b4',
                    opacity=0.75
                ))
                
                fig_hist.update_layout(
                    title=f'Distribución de Retornos - {panel}',
                    xaxis_title='Retorno (%)',
                    yaxis_title='Frecuencia',
                    template='plotly_white',
                    showlegend=False
                )
                
                st.plotly_chart(fig_hist, use_container_width=True)
    
    def obtener_serie_historica_universal(self, request: Union[HistoricalDataRequest, List[HistoricalDataRequest]]) -> Dict[str, pd.DataFrame]:
        """
        Obtiene series históricas de precios para uno o múltiples activos.
        
        Args:
            request: Un solo objeto HistoricalDataRequest o una lista de ellos
            
        Returns:
            Dict[str, pd.DataFrame]: Diccionario con símbolos como claves y DataFrames como valores
        """
        if isinstance(request, HistoricalDataRequest):
            requests_list = [request]
        else:
            requests_list = request
            
        resultados = {}
        
        for req in requests_list:
            try:
                # Construir la URL según el tipo de activo
                if req.mercado.upper() in ['BCBA', 'BCS', 'ROFEX']:
                    # Mercado local
                    url = (
                        f"https://api.invertironline.com/api/v2/{req.mercado}/Titulos/"
                        f"{req.simbolo}/Cotizacion/seriehistorica/"
                        f"{req.fecha_desde}/{req.fecha_hasta}/"
                        f"{'Ajustada' if req.ajustada else 'SinAjustar'}"
                    )
                else:
                    # Mercados internacionales
                    url = (
                        f"https://api.invertironline.com/api/v2/{req.mercado}/Titulos/"
                        f"{req.simbolo}/Cotizacion/"
                        f"{req.fecha_desde}/{req.fecha_hasta}/"
                        f"{'Ajustada' if req.ajustada else 'SinAjustar'}"
                    )
                
                # Configurar headers
                headers = {
                    'Authorization': f'Bearer {self.token_portador}',
                    'Accept': 'application/json'
                }
                
                # Realizar la solicitud con manejo de reintentos
                for intento in range(req.max_reintentos):
                    try:
                        response = self._session.get(
                            url,
                            headers=headers,
                            timeout=req.timeout
                        )
                        response.raise_for_status()
                        
                        # Procesar la respuesta
                        data = response.json()
                        if not data:
                            st.warning(f"No se encontraron datos para {req.simbolo} en {req.mercado}")
                            continue
                            
                        # Convertir a DataFrame y estandarizar
                        df = pd.DataFrame(data)
                        if 'fecha' in df.columns:
                            df['fecha'] = pd.to_datetime(df['fecha'])
                            df.set_index('fecha', inplace=True)
                        
                        # Aplicar frecuencia si es necesario
                        if req.frecuencia != 'diaria':
                            if req.frecuencia == 'semanal':
                                df = df.resample('W').last()
                            elif req.frecuencia == 'mensual':
                                df = df.resample('M').last()
                        
                        resultados[req.simbolo] = df
                        break
                        
                    except requests.exceptions.RequestException as e:
                        if intento == req.max_reintentos - 1:
                            st.error(f"Error al obtener datos para {req.simbolo} en {req.mercado}: {str(e)}")
                        time.sleep(1)  # Esperar antes de reintentar
            
            except Exception as e:
                st.error(f"Error inesperado procesando {req.simbolo}: {str(e)}")
                continue
                
        return resultados
        
    def optimizar_portafolio(self, df: pd.DataFrame) -> dict:
        """
        Optimiza el portafolio usando el método de Markowitz.
        """
        if df.empty:
            return {}
            
        # Calcular matriz de covarianza y retornos esperados
        col_precio = next((c for c in ['ultimoPrecio', 'precio', 'cierre'] 
                          if c in df.columns), None)
        
        if col_precio is None:
            return {}
            
        # Pivotar para tener precios por fecha y activo
        precios = df.pivot_table(
            index=df.index, 
            columns='simbolo', 
            values=col_precio,
            aggfunc='first'
        )
        
        # Calcular retornos logarítmicos
        retornos = np.log(precios / precios.shift(1)).dropna()
        
        if retornos.empty:
            return {}
            
        # Calcular matriz de covarianza y retornos esperados
        cov_matrix = retornos.cov() * 252  # Anualizado
        retornos_esperados = retornos.mean() * 252  # Anualizado
        
        # Optimización (versión simplificada)
        num_portfolios = 10000
        resultados = np.zeros((4 + len(retornos_esperados), num_portfolios))
        
        for i in range(num_portfolios):
            pesos = np.random.random(len(retornos_esperados))
            pesos /= np.sum(pesos)
            
            # Guardar resultados
            resultados[0, i] = np.sum(retornos_esperados * pesos)  # Retorno esperado
            resultados[1, i] = np.sqrt(np.dot(pesos.T, np.dot(cov_matrix, pesos)))  # Volatilidad
            resultados[2, i] = resultados[0, i] / resultados[1, i] if resultados[1, i] > 0 else 0  # Sharpe ratio
            
            # Guardar pesos
            for j, peso in enumerate(pesos):
                resultados[j+3, i] = peso
        
        # Encontrar el portafolio con mejor ratio de Sharpe
        max_sharpe_idx = np.argmax(resultados[2])
        pesos_optimos = resultados[3:, max_sharpe_idx]
        
        return {
            'activos': list(retornos_esperados.index),
            'pesos': dict(zip(retornos_esperados.index, pesos_optimos)),
            'retorno_esperado': resultados[0, max_sharpe_idx],
            'volatilidad': resultados[1, max_sharpe_idx],
            'sharpe_ratio': resultados[2, max_sharpe_idx]
        }

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Se produjo un error en la aplicación: {str(e)}")
        st.exception(e)
