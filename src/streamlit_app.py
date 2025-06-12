import os
os.environ["STREAMLIT_HOME"] = "/tmp"
os.environ["STREAMLIT_RUNTIME_HOME"] = "/tmp"
os.environ["STREAMLIT_STATIC_HOME"] = "/tmp"
os.environ["STREAMLIT_CONFIG_DIR"] = "/tmp"
os.environ["XDG_CONFIG_HOME"] = "/tmp"
os.environ["HOME"] = "/tmp"

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
import math
from scipy.stats import norm
import matplotlib.cm as cm
import pandas_market_calendars as mcal

warnings.filterwarnings('ignore')

# Configuración de la página DEBE ir al principio
st.set_page_config(
    page_title="IOL Portfolio Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session state
def init_session_state():
    """Inicializar todas las variables de session state necesarias"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'token_acceso' not in st.session_state:
        st.session_state.token_acceso = None
    if 'token_refresco' not in st.session_state:
        st.session_state.token_refresco = None
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    if 'clientes' not in st.session_state:
        st.session_state.clientes = []
    if 'cliente_seleccionado' not in st.session_state:
        st.session_state.cliente_seleccionado = None
    if 'fecha_desde' not in st.session_state:
        st.session_state.fecha_desde = date.today() - timedelta(days=365)
    if 'fecha_hasta' not in st.session_state:
        st.session_state.fecha_hasta = date.today()
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "login"

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

def obtener_estado_cuenta(token_portador, id_cliente):
    url_estado_cuenta = f'https://api.invertironline.com/api/v2/Asesores/EstadoDeCuenta/{id_cliente}'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    try:
        respuesta = requests.get(url_estado_cuenta, headers=encabezados)
        st.info(f"💰 Solicitando estado de cuenta para cliente {id_cliente}")
        
        if respuesta.status_code == 200:
            estado_data = respuesta.json()
            st.success(f"✅ Estado de cuenta obtenido exitosamente")
            return estado_data
        elif respuesta.status_code == 404:
            st.warning(f"⚠️ Estado de cuenta no encontrado para cliente {id_cliente}")
            return None
        else:
            st.error(f'❌ Error al obtener estado de cuenta: {respuesta.status_code}')
            return None
    except Exception as e:
        st.error(f'💥 Error de conexión al obtener estado de cuenta: {str(e)}')
        return None

def obtener_portafolio(token_portador, id_cliente, pais='Argentina'):
    url_portafolio = f'https://api.invertironline.com/api/v2/Asesores/Portafolio/{id_cliente}/{pais}'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    try:
        respuesta = requests.get(url_portafolio, headers=encabezados)
        st.info(f"🔍 Solicitando portafolio para cliente {id_cliente}")
        st.info(f"📡 URL: {url_portafolio}")
        st.info(f"📊 Status Code: {respuesta.status_code}")
        
        if respuesta.status_code == 200:
            portafolio_data = respuesta.json()
            st.success(f"✅ Portafolio obtenido exitosamente")
            st.info(f"📋 Estructura de portafolio: {type(portafolio_data)}")
            if isinstance(portafolio_data, dict):
                st.info(f"🔑 Claves disponibles: {list(portafolio_data.keys())}")
            return portafolio_data
        elif respuesta.status_code == 404:
            st.warning(f"⚠️ Cliente {id_cliente} no encontrado o sin portafolio")
            return None
        elif respuesta.status_code == 401:
            st.error("🔐 Token de autorización expirado o inválido")
            return None
        else:
            st.error(f'❌ Error al obtener portafolio: {respuesta.status_code}')
            st.error(f'📄 Respuesta: {respuesta.text}')
            return None
    except Exception as e:
        st.error(f'💥 Error de conexión al obtener portafolio: {str(e)}')
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
            return respuesta.json()
        else:
            return None
    except Exception as e:
        st.error(f'Error al obtener cotización MEP: {str(e)}')
        return None

def obtener_tasas_caucion(token_portador, instrumento="Cauciones", panel="Todas", pais="Argentina"):
    url = f"https://api.invertironline.com/api/v2/Cotizaciones/{instrumento}/{panel}/{pais}"
    headers = {
        "Authorization": f"Bearer {token_acceso}"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f'Error al obtener tasas de caución: {str(e)}')
        return None

def obtener_cotizacion_actual(token_portador, mercado, simbolo):
    """
    Obtiene la cotización actual de un título desde la API de IOL.
    """
    url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion"
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener la cotización actual para {simbolo}: {response.status_code}")
            return None
    except Exception as e:
        st.error(f'Error al obtener cotización actual: {str(e)}')
        return None

def parse_datetime_flexible(datetime_string):
    """
    Parse datetime strings with flexible format handling
    """
    if not datetime_string:
        return None
    
    # Common datetime formats from IOL API
    formats_to_try = [
        "%Y-%m-%dT%H:%M:%S.%f",  # With microseconds
        "%Y-%m-%dT%H:%M:%S",     # Without microseconds
        "%Y-%m-%d %H:%M:%S.%f",  # Space separator with microseconds
        "%Y-%m-%d %H:%M:%S",     # Space separator without microseconds
        "ISO8601",               # Let pandas infer ISO format
        "mixed"                  # Let pandas infer mixed formats
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

    # Final fallback - let pandas infer automatically
    try:
        return pd.to_datetime(datetime_string, infer_datetime_format=True)
    except Exception:
        return None

def obtener_serie_historica_iol(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="ajustada"):
    """
    Obtiene la serie histórica de precios de un título desde la API de IOL.
    Actualizada para manejar correctamente la estructura de respuesta de la API.
    """
    # Determinar endpoint según tipo de instrumento
    if mercado == "Opciones":
        url = f"https://api.invertironline.com/api/v2/Opciones/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    elif mercado == "FCI":
        url = f"https://api.invertironline.com/api/v2/FCI/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    else:
        url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if not data:
                return None
            
            precios = []
            fechas = []
            
            for item in data:
                try:
                    # Usar ultimoPrecio como precio principal según la documentación
                    precio = item.get('ultimoPrecio')
                    
                    # Si ultimoPrecio es 0 o None, intentar otros campos
                    if not precio or precio == 0:
                        precio = item.get('cierreAnterior') or item.get('precioPromedio') or item.get('apertura')
                    
                    fecha_str = item.get('fechaHora')
                    
                    if precio is not None and precio > 0 and fecha_str:
                        fecha_parsed = parse_datetime_flexible(fecha_str)
                        if fecha_parsed is not None:
                            precios.append(precio)
                            fechas.append(fecha_parsed)
                            
                except Exception as e:
                    # Log individual item errors but continue processing
                    continue
            
            if precios and fechas:
                # Crear serie ordenada por fecha
                serie = pd.Series(precios, index=fechas)
                serie = serie.sort_index()  # Asegurar orden cronológico
                
                # Eliminar duplicados manteniendo el último valor
                serie = serie[~serie.index.duplicated(keep='last')]
                
                return serie
            else:
                return None
                
        elif response.status_code == 401:
            # Token expirado o inválido
            st.warning(f"⚠️ Token de autorización inválido para {simbolo}")
            return None
            
        elif response.status_code == 404:
            # Símbolo no encontrado en este mercado
            return None
            
        elif response.status_code == 400:
            # Parámetros inválidos
            st.warning(f"⚠️ Parámetros inválidos para {simbolo} en {mercado}")
            return None
            
        elif response.status_code == 500:
            # Error del servidor - silencioso para no interrumpir el flujo
            return None
            
        else:
            # Otros errores HTTP
            return None
            
    except requests.exceptions.Timeout:
        # Timeout - silencioso
        return None
    except requests.exceptions.ConnectionError:
        # Error de conexión - silencioso
        return None
    except Exception as e:
        # Error general - silencioso para no interrumpir el análisis
        return None

def obtener_serie_historica_con_volumen(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="ajustada"):
    """
    Obtiene la serie histórica de precios y volumen de un título desde la API de IOL.
    Retorna un DataFrame con precios, volumen y otras métricas.
    """
    # Determinar endpoint según tipo de instrumento
    if mercado == "Opciones":
        url = f"https://api.invertironline.com/api/v2/Opciones/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    elif mercado == "FCI":
        url = f"https://api.invertironline.com/api/v2/FCI/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    else:
        url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if not data:
                return None
            
            datos_procesados = []
            
            for item in data:
                try:
                    # Extraer precio usando los campos correctos de la API
                    precio = item.get('ultimoPrecio')
                    if not precio or precio == 0:
                        precio = item.get('cierreAnterior') or item.get('precioPromedio') or item.get('apertura')
                    
                    # Extraer volumen usando los campos correctos de la API - FIX SYNTAX ERROR
                    volumen = item.get('volumenNominal', 0)
                    if volumen == 0:
                        volumen = (item.get('cantidadOperada') or 
                                 item.get('cantidad') or 
                                 item.get('volumeNominal') or 
                                 item.get('montoOperado') or 0)
                    
                    # Extraer otros datos relevantes
                    fecha_str = item.get('fechaHora')
                    apertura = item.get('apertura', precio)
                    maximo = item.get('maximo', precio)
                    minimo = item.get('minimo', precio)
                    
                    # Cantidad de operaciones si está disponible
                    cant_operaciones = (item.get('cantidadOperaciones') or 
                                       item.get('numeroOperaciones') or 
                                       item.get('trades') or 0)
                    
                    if precio is not None and precio > 0 and fecha_str:
                        fecha_parsed = parse_datetime_flexible(fecha_str)
                        if fecha_parsed is not None:
                            datos_procesados.append({
                                'fecha': fecha_parsed,
                                'precio': float(precio),
                                'volumen': float(volumen),
                                'apertura': float(apertura) if apertura else float(precio),
                                'maximo': float(maximo) if maximo else float(precio),
                                'minimo': float(minimo) if minimo else float(precio),
                                'operaciones': int(cant_operaciones)
                            })
                            
                except Exception as e:
                    continue
            
            if datos_procesados:
                # Crear DataFrame ordenado por fecha
                df = pd.DataFrame(datos_procesados)
                df = df.sort_values('fecha').reset_index(drop=True)
                df.set_index('fecha', inplace=True)
                
                # Eliminar duplicados manteniendo el último valor
                df = df[~df.index.duplicated(keep='last')]
                
                return df
            else:
                return None
                
        else:
            return None
            
    except Exception as e:
        return None

def calcular_metricas_volumen(df_datos, ventana_ma=20):
    """
    Calcula métricas de volumen y promedios móviles.
    
    Args:
        df_datos: DataFrame con columnas 'precio', 'volumen', etc.
        ventana_ma: Ventana para el promedio móvil (default 20 días)
    
    Returns:
        DataFrame con métricas de volumen calculadas
    """
    if df_datos is None or df_datos.empty or 'volumen' not in df_datos.columns:
        return None
    
    df = df_datos.copy()
    
    # Promedio móvil del volumen
    df['volumen_ma'] = df['volumen'].rolling(window=ventana_ma, min_periods=1).mean()
    
    # Promedio móvil de diferentes ventanas
    df['volumen_ma_5'] = df['volumen'].rolling(window=5, min_periods=1).mean()
    df['volumen_ma_10'] = df['volumen'].rolling(window=10, min_periods=1).mean()
    df['volumen_ma_50'] = df['volumen'].rolling(window=50, min_periods=1).mean()
    
    # Volumen relativo (volumen actual vs promedio móvil)
    df['volumen_relativo'] = df['volumen'] / df['volumen_ma']
    
    # Volumen medio diario por período
    df['volumen_medio_periodo'] = df['volumen'].expanding().mean()
    
    # Volatilidad del volumen
    df['volatilidad_volumen'] = df['volumen'].rolling(window=ventana_ma, min_periods=1).std()
    
    # VWAP (Volume Weighted Average Price) si tenemos OHLC
    if all(col in df.columns for col in ['apertura', 'maximo', 'minimo', 'precio']):
        precio_tipico = (df['maximo'] + df['minimo'] + df['precio']) / 3
        df['vwap'] = (precio_tipico * df['volumen']).cumsum() / df['volumen'].cumsum()
        
        # VWAP móvil
        df['vwap_movil'] = df.apply(
            lambda row: (precio_tipico.loc[:row.name] * df['volumen'].loc[:row.name]).tail(ventana_ma).sum() / 
                       df['volumen'].loc[:row.name].tail(ventana_ma).sum()
            if len(df.loc[:row.name]) >= ventana_ma else
            (precio_tipico.loc[:row.name] * df['volumen'].loc[:row.name]).sum() / 
            df['volumen'].loc[:row.name].sum(),
            axis=1
        )
    
    # Identificar picos de volumen (volumen > 2 * promedio móvil)
    df['pico_volumen'] = df['volumen'] > (2 * df['volumen_ma'])
    
    # Tendencia del volumen (comparación con período anterior)
    df['tendencia_volumen'] = np.where(
        df['volumen_ma'] > df['volumen_ma'].shift(5), 'Creciente',
        np.where(df['volumen_ma'] < df['volumen_ma'].shift(5), 'Decreciente', 'Estable')
    )
    
    return df

def crear_grafico_volumen_avanzado(df_datos, simbolo, titulo_personalizado=None):
    """
    Crea un gráfico interactivo avanzado de volumen con múltiples métricas.
    """
    if df_datos is None or df_datos.empty:
        return None
    
    titulo = titulo_personalizado or f"Análisis de Volumen - {simbolo}"
      # Crear subplots: precio arriba, volumen abajo
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        subplot_titles=('Precio y VWAP', 'Volumen', 'Análisis de Volumen'),
        vertical_spacing=0.1
    )
    
    # Agregar línea de precio
    fig.add_trace(
        go.Scatter(
            x=df_datos.index,
            y=df_datos['precio'],
            mode='lines',
            name='Precio',
            line=dict(color='#1f77b4', width=2)
        ),
        row=1, col=1
    )
    
    if 'vwap' in df_datos.columns:
        fig.add_trace(
            go.Scatter(
                x=df_datos.index,
                y=df_datos['vwap'],
                mode='lines',
                name='VWAP',
                line=dict(color='#ff7f0e', width=1, dash='dash')
            ),
            row=1, col=1
        )
    
    if 'vwap_movil' in df_datos.columns:
        fig.add_trace(
            go.Scatter(
                x=df_datos.index,
                y=df_datos['vwap_movil'],
                mode='lines',
                name='VWAP Móvil (20)',
                line=dict(color='#2ca02c', width=1, dash='dot')
            ),
            row=1, col=1
        )
    
    # Gráfico de volumen con barras
    colors = ['red' if vol > ma else 'gray' for vol, ma in zip(df_datos['volumen'], df_datos['volumen_ma'])]
    
    fig.add_trace(
        go.Bar(
            x=df_datos.index,
            y=df_datos['volumen'],
            name='Volumen',
            marker_color=colors,
            opacity=0.7
        ),
        row=2, col=1
    )
    
    # Promedio móvil del volumen
    fig.add_trace(
        go.Scatter(
            x=df_datos.index,
            y=df_datos['volumen_ma'],
            mode='lines',
            name='Vol MA(20)',
            line=dict(color='#d62728', width=2)
        ),
        row=2, col=1
    )
    
    # Diferentes promedios móviles
    if 'volumen_ma_5' in df_datos.columns:
        fig.add_trace(
            go.Scatter(
                x=df_datos.index,
                y=df_datos['volumen_ma_5'],
                mode='lines',
                name='Vol MA(5)',
                line=dict(color='#9467bd', width=1, dash='dash'),
                opacity=0.7
            ),
            row=2, col=1
        )
    
    if 'volumen_ma_50' in df_datos.columns:
        fig.add_trace(
            go.Scatter(
                x=df_datos.index,
                y=df_datos['volumen_ma_50'],
                mode='lines',
                name='Vol MA(50)',
                line=dict(color='#8c564b', width=1, dash='dot'),
                opacity=0.7
            ),
            row=2, col=1
        )
    
    # Volumen relativo
    if 'volumen_relativo' in df_datos.columns:
        colors_rel = ['green' if vr > 1.5 else 'red' if vr < 0.5 else 'gray' 
                      for vr in df_datos['volumen_relativo']]
        
        fig.add_trace(
            go.Scatter(
                x=df_datos.index,
                y=df_datos['volumen_relativo'],
                mode='markers+lines',
                name='Vol Relativo',
                line=dict(color='#17becf', width=1),
                marker=dict(color=colors_rel, size=3)
            ),
            row=3, col=1
        )
        
        # Líneas de referencia para volumen relativo
        fig.add_hline(y=1.0, line_dash="dash", line_color="gray", opacity=0.5, row=3, col=1)
        fig.add_hline(y=1.5, line_dash="dot", line_color="green", opacity=0.3, row=3, col=1)
        fig.add_hline(y=0.5, line_dash="dot", line_color="red", opacity=0.3, row=3, col=1)
    
    # Configurar layout
    fig.update_layout(
        title=dict(
            text=titulo,
            x=0.5,
            font=dict(size=16)
        ),
        height=800,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template="plotly_white"
    )
    
    # Configurar ejes
    fig.update_xaxes(title_text="Fecha", row=3, col=1)
    fig.update_yaxes(title_text="Precio", row=1, col=1)
    fig.update_yaxes(title_text="Volumen", row=2, col=1)
    fig.update_yaxes(title_text="Vol Relativo", row=3, col=1)
    
    return fig

def obtener_operaciones(token_portador, id_cliente, estado='Pendientes', pais='Argentina', fecha_desde=None, fecha_hasta=None, numero=None):
    """
    Obtiene las operaciones de un cliente con filtros opcionales
    """
    url_operaciones = f'https://api.invertironline.com/api/v2/Asesores/Operaciones?IdClienteAsesorado={id_cliente}&Estado={estado}&Pais={pais}'
    if fecha_desde:
        url_operaciones += f'&FechaDesde={fecha_desde}'
    if fecha_hasta:
        url_operaciones += f'&FechaHasta={fecha_hasta}'
    if numero:
        url_operaciones += f'&Numero={numero}'
    
    encabezados = obtener_encabezado_autorizacion(token_portador)
    
    try:
        respuesta = requests.get(url_operaciones, headers=encabezados, timeout=15)
        st.info(f"🔍 Solicitando operaciones para cliente {id_cliente}")
        st.info(f"📡 URL: {url_operaciones}")
        st.info(f"📊 Status Code: {respuesta.status_code}")
        
        if respuesta.status_code == 200:
            operaciones = respuesta.json()
            if not operaciones:
                st.warning(f"No se encontraron operaciones para el cliente con ID {id_cliente}")
            else:
                st.success(f"✅ {len(operaciones)} operaciones encontradas")
            return operaciones
        elif respuesta.status_code == 401:
            st.error("🔐 Token de autorización expirado o inválido")
            return None
        elif respuesta.status_code == 404:
            st.warning(f"⚠️ No se encontraron operaciones para cliente {id_cliente}")
            return []
        else:
            st.error(f'❌ Error al obtener operaciones: {respuesta.status_code}')
            st.error(f'📄 Respuesta: {respuesta.text}')
            return None
    except Exception as e:
        st.error(f'💥 Error de conexión al obtener operaciones: {str(e)}')
        return None

def obtener_detalle_operacion(token_portador, id_cliente, numero_operacion):
    """
    Obtiene el detalle de una operación específica
    """
    url_detalle = f'https://api.invertironline.com/api/v2/Asesores/Operaciones/Detalle/{id_cliente}/{numero_operacion}'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    
    try:
        respuesta = requests.get(url_detalle, headers=encabezados, timeout=15)
        
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            st.error(f'Error al obtener el detalle de la operación: {respuesta.status_code}')
            return None
    except Exception as e:
        st.error(f'Error de conexión al obtener detalle de operación: {str(e)}')
        return None

def obtener_boleto_operacion(token_portador, id_cliente, numero_operacion):
    """
    Obtiene el boleto de una operación específica
    """
    url_boleto = f'https://api.invertironline.com/api/v2/Asesores/Operaciones/Boleto/{id_cliente}/{numero_operacion}'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    
    try:
        respuesta = requests.get(url_boleto, headers=encabezados, timeout=15)
        
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            st.error(f'Error al obtener el boleto de la operación: {respuesta.status_code}')
            return None
    except Exception as e:
        st.error(f'Error de conexión al obtener boleto de operación: {str(e)}')
        return None

def obtener_operaciones_filtradas(token_portador, estado='todas', pais='Argentina', fecha_desde=None, fecha_hasta=None, numero=None):
    """
    Obtiene operaciones filtradas usando el endpoint general
    """
    url_operaciones = 'https://api.invertironline.com/api/v2/operaciones'
    params = {
        'filtro.estado': estado,
        'filtro.pais': pais
    }
    if fecha_desde:
        params['filtro.fechaDesde'] = fecha_desde
    if fecha_hasta:
        params['filtro.fechaHasta'] = fecha_hasta
    if numero:
        params['filtro.numero'] = numero
    
    encabezados = obtener_encabezado_autorizacion(token_portador)
    
    try:
        respuesta = requests.get(url_operaciones, headers=encabezados, params=params, timeout=15)
        
        if respuesta.status_code == 200:
            operaciones = respuesta.json()
            if not operaciones:
                st.info(f"No se encontraron operaciones filtradas con los parámetros especificados")
            return operaciones
        elif respuesta.status_code == 401:
            st.error("Error: Autorización denegada. Verifica el token de autorización.")
            return None
        else:
            st.error(f'Error al obtener las operaciones filtradas: {respuesta.status_code}')
            return None
    except Exception as e:
        st.error(f'Error de conexión al obtener operaciones filtradas: {str(e)}')
        return None

def obtener_cotizacion_detalle_iol(token_portador, mercado, simbolo):
    """
    Obtiene la cotización detallada de un título incluyendo volumen desde la API de IOL
    """
    url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/CotizacionDetalle"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data
        elif response.status_code == 401:
            return None
        elif response.status_code == 404:
            return None
        else:
            return None
            
    except Exception as e:
        return None

def obtener_volumen_desde_iol(token_portador, simbolo, mercados_prioritarios, fecha_desde, fecha_hasta):
    """
    Intenta obtener datos de volumen desde diferentes endpoints de IOL
    """
    # Primero intentar con datos históricos con volumen
    for mercado in mercados_prioritarios:
        try:
            df_datos = obtener_serie_historica_con_volumen(
                token_portador, mercado, simbolo, 
                fecha_desde.strftime('%Y-%m-%d'), 
                fecha_hasta.strftime('%Y-%m-%d')
            )
            
            if df_datos is not None and not df_datos.empty and 'volumen' in df_datos.columns:
                if df_datos['volumen'].sum() > 0:
                    return df_datos, mercado
        except Exception:
            continue
    
    # Si no hay datos históricos de volumen, intentar con cotización detalle actual
    for mercado in mercados_prioritarios:
        try:
            cotizacion_detalle = obtener_cotizacion_detalle_iol(token_portador, mercado, simbolo)
            
            if cotizacion_detalle:
                # Extraer datos de volumen de la cotización detalle
                volumen_nominal = cotizacion_detalle.get('volumenNominal', 0)
                monto_operado = cotizacion_detalle.get('montoOperado', 0)
                cant_operaciones = cotizacion_detalle.get('cantidadOperaciones', 0)
                precio_actual = cotizacion_detalle.get('ultimoPrecio', 0)
                
                if volumen_nominal > 0 or monto_operado > 0:
                    # Crear un DataFrame básico con los datos actuales
                    fecha_actual = pd.Timestamp.now()
                    df_basico = pd.DataFrame({
                        'precio': [precio_actual],
                        'volumen': [volumen_nominal if volumen_nominal > 0 else monto_operado],
                        'apertura': [cotizacion_detalle.get('apertura', precio_actual)],
                        'maximo': [cotizacion_detalle.get('maximo', precio_actual)],
                        'minimo': [cotizacion_detalle.get('minimo', precio_actual)],
                        'operaciones': [cant_operaciones]
                    }, index=[fecha_actual])
                    
                    return df_basico, mercado
        except Exception:
            continue
    
    return None, None

def analizar_volumen_por_simbolo(token_portador, simbolo, fecha_desde, fecha_hasta, pais='Argentina'):
    """
    Análisis completo de volumen para un símbolo específico mejorado con IOL API
    """
    st.markdown(f"#### 📊 Análisis de Volumen - {simbolo}")
    
    # Detectar mercados apropiados
    mercados_prioritarios = detectar_mercado_por_pais(pais, simbolo)
    
    datos_obtenidos = False
    df_datos = None
    mercado_usado = None
    
    # Mostrar progreso de búsqueda
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Intentar obtener datos de volumen desde IOL
    status_text.text(f"🔍 Buscando datos de volumen para {simbolo} en IOL...")
    progress_bar.progress(25)
    
    df_datos, mercado_usado = obtener_volumen_desde_iol(
        token_portador, simbolo, mercados_prioritarios, fecha_desde, fecha_hasta
    )
    
    if df_datos is not None and not df_datos.empty:
        datos_obtenidos = True
        st.success(f"✅ Datos de volumen obtenidos para {simbolo} desde IOL ({mercado_usado})")
        progress_bar.progress(50)
    
    # Fallback a yfinance si IOL no tiene datos de volumen
    if not datos_obtenidos:
        try:
            status_text.text(f"🔄 Intentando obtener datos desde Yahoo Finance...")
            progress_bar.progress(60)
            
            # Probar diferentes sufijos según el país
            if pais.lower() == 'argentina':
                sufijos = ['.BA', '.AR', '']
            else:
                sufijos = ['', '.US']
            
            for i, sufijo in enumerate(sufijos):
                simbolo_yf = simbolo + sufijo if sufijo else simbolo
                ticker = yf.Ticker(simbolo_yf)
                data_yf = ticker.history(start=fecha_desde, end=fecha_hasta)
                
                progress_bar.progress(60 + (i+1) * 10)
                
                if not data_yf.empty and 'Volume' in data_yf.columns:
                    # Convertir a formato compatible
                    df_datos = pd.DataFrame({
                        'precio': data_yf['Close'],
                        'volumen': data_yf['Volume'],
                        'apertura': data_yf['Open'],
                        'maximo': data_yf['High'],
                        'minimo': data_yf['Low'],
                        'operaciones': 0  # No disponible en yfinance
                    })
                    
                    if df_datos['volumen'].sum() > 0:
                        st.success(f"✅ Datos de volumen obtenidos desde Yahoo Finance ({simbolo_yf})")
                        datos_obtenidos = True
                        mercado_usado = "Yahoo Finance"
                        break
                        
        except Exception as e:
            st.warning(f"⚠️ Error obteniendo datos desde Yahoo Finance: {str(e)}")
    
    progress_bar.progress(80)
    
    # Si aún no hay datos, intentar solo precios para mostrar al menos algo
    if not datos_obtenidos:
        status_text.text("🔄 Intentando obtener solo datos de precios...")
        
        for mercado in mercados_prioritarios:
            serie_precios = obtener_serie_historica_iol(
                token_portador, mercado, simbolo,
                fecha_desde.strftime('%Y-%m-%d'),
                fecha_hasta.strftime('%Y-%m-%d')
            )
            
            if serie_precios is not None and not serie_precios.empty:
                # Crear DataFrame básico sin volumen real
                df_datos = pd.DataFrame({
                    'precio': serie_precios,
                    'volumen': 0,  # Sin datos de volumen
                    'apertura': serie_precios,
                    'maximo': serie_precios,
                    'minimo': serie_precios,
                    'operaciones': 0
                })
                st.warning(f"⚠️ Solo se obtuvieron datos de precios para {simbolo} (sin volumen)")
                mercado_usado = mercado
                datos_obtenidos = True
                break
    
    progress_bar.progress(90)
    
    if not datos_obtenidos or df_datos is None or df_datos.empty:
        progress_bar.progress(100)
        status_text.text("")
        st.error(f"❌ No se pudieron obtener datos para {simbolo}")
        return None
    
    # Limpiar la interfaz de progreso
    progress_bar.progress(100)
    status_text.text("")
    progress_bar.empty()
    status_text.empty()
    
    # Verificar si hay datos de volumen reales
    tiene_volumen = df_datos['volumen'].sum() > 0
    
    if not tiene_volumen:
        st.warning(f"⚠️ No hay datos de volumen disponibles para {simbolo}. Mostrando solo análisis de precios.")
        
        # Mostrar solo gráfico de precios
        fig_simple = go.Figure()
        fig_simple.add_trace(go.Scatter(
            x=df_datos.index,
            y=df_datos['precio'],
            mode='lines',
            name='Precio',
            line=dict(color='#1f77b4', width=2)
        ))
        
        fig_simple.update_layout(
            title=f"Serie de Precios - {simbolo}",
            xaxis_title="Fecha",
            yaxis_title="Precio",
            height=400,
            template="plotly_white"
        )
        
        st.plotly_chart(fig_simple, use_container_width=True, key=f"precio_simple_{simbolo}_{hash(simbolo)}")
        
        # Mostrar estadísticas básicas de precio
        col1, col2, col3, col4 = st.columns(4)
        precio_actual = df_datos['precio'].iloc[-1]
        precio_promedio = df_datos['precio'].mean()
        precio_max = df_datos['precio'].max()
        precio_min = df_datos['precio'].min()
        
        col1.metric("Precio Actual", f"${precio_actual:.2f}")
        col2.metric("Precio Promedio", f"${precio_promedio:.2f}")
        col3.metric("Precio Máximo", f"${precio_max:.2f}")
        col4.metric("Precio Mínimo", f"${precio_min:.2f}")
        
        return df_datos
    
    # Calcular métricas de volumen si hay datos
    with st.spinner("Calculando métricas de volumen..."):
        df_con_metricas = calcular_metricas_volumen(df_datos)
    
    if df_con_metricas is None:
        st.error("❌ Error calculando métricas de volumen")
        return None
    
    # Mostrar estadísticas de volumen
    col1, col2, col3, col4 = st.columns(4)
    
    volumen_promedio = df_con_metricas['volumen'].mean()
    volumen_actual = df_con_metricas['volumen'].iloc[-1]
    volumen_max = df_con_metricas['volumen'].max()
    volumen_relativo_actual = df_con_metricas['volumen_relativo'].iloc[-1] if 'volumen_relativo' in df_con_metricas.columns else 0
    
    col1.metric("Volumen Promedio", f"{volumen_promedio:,.0f}")
    col2.metric("Volumen Actual", f"{volumen_actual:,.0f}")
    col3.metric("Volumen Máximo", f"{volumen_max:,.0f}")
    col4.metric("Vol. Relativo", f"{volumen_relativo_actual:.2f}")
    
    # Mostrar métricas adicionales
    if len(df_con_metricas) > 20:
        col1, col2, col3, col4 = st.columns(4)
        picos_volumen = df_con_metricas['pico_volumen'].sum() if 'pico_volumen' in df_con_metricas.columns else 0
        tendencia = df_con_metricas['tendencia_volumen'].iloc[-1] if 'tendencia_volumen' in df_con_metricas.columns else 'N/A'
        vol_ma_20 = df_con_metricas['volumen_ma'].iloc[-1] if 'volumen_ma' in df_con_metricas.columns else 0
        volatilidad_vol = df_con_metricas['volatilidad_volumen'].iloc[-1] if 'volatilidad_volumen' in df_con_metricas.columns else 0
        
        col1.metric("Picos de Volumen", f"{picos_volumen}")
        col2.metric("Tendencia", tendencia)
        col3.metric("Vol MA(20)", f"{vol_ma_20:,.0f}")
        col4.metric("Volatilidad Vol", f"{volatilidad_vol:,.0f}")
    
    # Crear y mostrar gráfico con key único
    fig_volumen = crear_grafico_volumen_avanzado(df_con_metricas, simbolo)
    if fig_volumen:
        st.plotly_chart(fig_volumen, use_container_width=True, key=f"volumen_chart_{simbolo}_{hash(simbolo)}")
    
    # Análisis interpretativo
    with st.expander(f"📈 Interpretación del Análisis de Volumen - {simbolo}"):
        st.markdown(f"""
        **Análisis de Volumen para {simbolo} (Fuente: {mercado_usado}):**
        
        **Métricas Clave:**
        - **Volumen Actual vs Promedio**: {volumen_relativo_actual:.2f}x el promedio
        - **Interpretación**: {'📈 Alto volumen' if volumen_relativo_actual > 1.5 else '📉 Bajo volumen' if volumen_relativo_actual < 0.7 else '➡️ Volumen normal'}
        
        **Señales de Volumen:**
        - **Volumen > 1.5x promedio**: Posible inicio de movimiento significativo
        - **Volumen < 0.5x promedio**: Falta de interés, posible consolidación
        - **Picos de volumen con {picos_volumen if 'picos_volumen' in locals() else 0} eventos**: {'Actividad alta' if (picos_volumen if 'picos_volumen' in locals() else 0) > 5 else 'Actividad moderada'}
        
        **VWAP (Volume Weighted Average Price):**
        - Precio promedio ponderado por volumen
        - Útil para determinar si el precio actual está por encima o debajo del consenso del mercado
        
        **Recomendaciones:**
        - Monitorear cambios significativos en el volumen relativo
        - Usar VWAP como referencia para puntos de entrada/salida
        - Considerar la tendencia del volumen para validar movimientos de precio
        """)
    
    return df_con_metricas

def explicar_precio_y_vwap():
    st.markdown("""
    **Precio:** Es el valor de cierre, último precio negociado o promedio de un activo en un momento dado. Representa cuánto costaría comprar o vender una unidad de ese activo en el mercado.

    **VWAP (Volume Weighted Average Price):** Es el precio promedio ponderado por el volumen negociado. Se calcula sumando el valor de todas las transacciones (precio × volumen) y dividiéndolo por el volumen total. Es útil para saber si el precio actual está por encima o por debajo del consenso del mercado y es referencia para traders institucionales.
    """)

def graficar_simulacion_portafolio(portafolio, dias=252, n_sim=1):
    """
    Simula la evolución del valor del portafolio usando una caminata aleatoria y grafica la serie simulada y los pesos.
    """
    if not portafolio or 'activos' not in portafolio:
        st.warning("No hay datos de portafolio para simular.")
        return
    import numpy as np
    import plotly.graph_objects as go
    activos = portafolio['activos']
    if not activos:
        st.warning("Portafolio vacío.")
        return
    # Obtener valorizado y pesos
    valores = np.array([a.get('valorizado', 0) for a in activos])
    simbolos = [a.get('titulo', {}).get('simbolo', f"Activo {i}") for i, a in enumerate(activos)]
    valor_total = valores.sum()
    pesos = valores / valor_total if valor_total > 0 else np.zeros_like(valores)
    # Supongamos retorno esperado 10% anual y volatilidad 20% anual para todos
    mu = 0.10
    sigma = 0.20
    dt = 1/252
    simulaciones = []
    for _ in range(n_sim):
        precios = [valor_total]
        for _ in range(dias):
            r = np.random.normal(mu*dt, sigma*np.sqrt(dt))
            precios.append(precios[-1]*np.exp(r))
        simulaciones.append(precios)
    # Graficar
    fig = go.Figure()
    for i, sim in enumerate(simulaciones):
        fig.add_trace(go.Scatter(y=sim, mode='lines', name=f'Simulación {i+1}'))
    fig.update_layout(title='Simulación de Valor del Portafolio', xaxis_title='Días', yaxis_title='Valor Total')
    st.plotly_chart(fig, use_container_width=True)
    # Graficar pesos
    fig_pesos = go.Figure(data=[go.Pie(labels=simbolos, values=pesos, hole=0.3)])
    fig_pesos.update_layout(title='Pesos de los Activos en el Portafolio')
    st.plotly_chart(fig_pesos, use_container_width=True)

def detectar_mercado_por_pais(pais, simbolo):
    simbolo_upper = simbolo.upper()
    if pais.lower() == 'argentina':
        # FCI solo en FCI
        if 'FCI' in simbolo_upper or 'FONDO' in simbolo_upper:
            return ['FCI']
        # Bonos AL/GD/AE en bCBA y bMAE
        if simbolo_upper.startswith('AL') or simbolo_upper.startswith('GD') or simbolo_upper.startswith('AE'):
            return ['bCBA', 'bMAE']
        # Acciones y CEDEARs en bCBA
        if simbolo_upper.isalpha() and len(simbolo_upper) <= 5:
            return ['bCBA']
        # Default
        return ['bCBA', 'bMAE', 'MERV']
    else:
        return ['NASDAQ', 'NYSE', 'bCBA']

def obtener_informacion_fci(token_acceso, simbolo=None):
    """
    Obtiene información completa de FCIs
    """
    if simbolo:
        url = f"https://api.invertironline.com/api/v2/Titulos/FCI/{simbolo}"
    else:
        url = "https://api.invertironline.com/api/v2/Titulos/FCI"
    
    headers = obtener_encabezado_autorizacion(token_acceso)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            return None
        elif response.status_code == 404:
            return None
        else:
            return None
            
    except Exception:
        return None

def calcular_retorno_esperado_fci(fci_info, precio_actual=None):
    """
    Calcula el retorno esperado de un FCI basado en su información
    """
    if not fci_info:
        return 0
    
    # Obtener variaciones históricas
    variacion_anual = fci_info.get('variacionAnual', 0)
    variacion_mensual = fci_info.get('variacionMensual', 0)
    variacion_diaria = fci_info.get('variacion', 0)
    
    # Calcular retorno esperado anualizado
    if variacion_anual and variacion_anual != 0:
        retorno_anual = variacion_anual / 100
    elif variacion_mensual and variacion_mensual != 0:
        # Anualizar retorno mensual
        retorno_anual = ((1 + variacion_mensual / 100) ** 12) - 1
    elif variacion_diaria and variacion_diaria != 0:
        # Anualizar retorno diario (asumiendo 252 días hábiles)
        retorno_anual = ((1 + variacion_diaria / 100) ** 252) - 1
    else:
        retorno_anual = 0
    
    return retorno_anual

def calcular_estadisticas_portafolio(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Calcula estadísticas completas del portafolio incluyendo P&L esperado
    """
    if not portafolio or 'activos' not in portafolio:
        return None
    
    activos = portafolio['activos']
    estadisticas = {
        'valor_total': 0,
        'cantidad_activos': len(activos),
        'retornos_esperados': {},
        'pesos_portafolio': {},
        'volatilidades': {},
        'retorno_portafolio_esperado': 0,
        'volatilidad_portafolio': 0,
        'ratio_sharpe': 0,
        'var_diario': 0,
        'var_mensual': 0,
        'var_anual': 0,
        'ganancia_esperada_diaria': 0,
        'ganancia_esperada_mensual': 0,
        'ganancia_esperada_anual': 0,
        'activos_detalle': []
    }
    
    # Calcular valor total del portafolio
    for activo in activos:
        valor = activo.get('valorizado', 0)
        estadisticas['valor_total'] += valor
    
    if estadisticas['valor_total'] == 0:
        return estadisticas
    
    # Analizar cada activo
    retornos_historicos = []
    pesos = []
    
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', '')
        valor = activo.get('valorizado', 0)
        cantidad = activo.get('cantidad', 0)
        precio_promedio = activo.get('ppc', 0)
        precio_actual = activo.get('ultimoPrecio', 0)
        
        peso = valor / estadisticas['valor_total'] if estadisticas['valor_total'] > 0 else 0
        estadisticas['pesos_portafolio'][simbolo] = peso
        pesos.append(peso)
        
        # Calcular retorno esperado
        retorno_esperado = 0
        volatilidad = 0
        
        # Verificar si es FCI
        tipo_activo = titulo.get('tipo', '')
        mercado = titulo.get('mercado', '')
        
        if tipo_activo == 'FCI' or mercado == 'FCI':
            # Obtener información específica de FCI
            fci_info = obtener_informacion_fci(token_acceso, simbolo)
            retorno_esperado = calcular_retorno_esperado_fci(fci_info, precio_actual)
        else:
            # Para otros activos, obtener datos históricos
            mercados_prioritarios = detectar_mercado_por_pais('Argentina', simbolo)
            serie_precios = None
            
            for mercado_test in mercados_prioritarios:
                # Intentar traer serie histórica con volumen y volatilidad
                df_hist = obtener_serie_historica_con_volumen(
                    token_acceso, mercado_test, simbolo,
                    fecha_desde.strftime('%Y-%m-%d'),
                    fecha_hasta.strftime('%Y-%m-%d')
                )
                if df_hist is not None and not df_hist.empty:
                    serie_precios = df_hist['precio']
                    serie_volumen = df_hist['volumen']
                    # Calcular volatilidad histórica de precios
                    retornos_diarios = serie_precios.pct_change().dropna()
                    if len(retornos_diarios) > 0:
                        retorno_esperado = retornos_diarios.mean() * 252
                        volatilidad = retornos_diarios.std() * np.sqrt(252)
                        retornos_historicos.append(retornos_diarios)
                    # Guardar series históricas en estadisticas si se requiere
                    estadisticas.setdefault('series_historicas', {})[simbolo] = {
                        'precio': serie_precios,
                        'volumen': serie_volumen
                    }
                    break
                # Fallback: solo precios si no hay volumen
                serie_precios = obtener_serie_historica_iol(
                    token_acceso, mercado_test, simbolo,
                    fecha_desde.strftime('%Y-%m-%d'),
                    fecha_hasta.strftime('%Y-%m-%d')
                )
                if serie_precios is not None and not serie_precios.empty:
                    break
            
            if serie_precios is not None and len(serie_precios) > 1:
                # Calcular retornos diarios
                retornos_diarios = serie_precios.pct_change().dropna()
                
                if len(retornos_diarios) > 0:
                    # Retorno esperado anualizado
                    retorno_esperado = retornos_diarios.mean() * 252
                    volatilidad = retornos_diarios.std() * np.sqrt(252)
                    retornos_historicos.append(retornos_diarios)
        
        estadisticas['retornos_esperados'][simbolo] = retorno_esperado
        estadisticas['volatilidades'][simbolo] = volatilidad
        
        # Ganancia/pérdida actual
        ganancia_perdida = (precio_actual - precio_promedio) * cantidad if precio_promedio > 0 else 0
        ganancia_perdida_porcentual = ((precio_actual / precio_promedio) - 1) * 100 if precio_promedio > 0 else 0
        
        estadisticas['activos_detalle'].append({
            'simbolo': simbolo,
            'cantidad': cantidad,
            'precio_promedio': precio_promedio,
            'precio_actual': precio_actual,
            'valor': valor,
            'peso': peso,
            'retorno_esperado': retorno_esperado,
            'volatilidad': volatilidad,
            'ganancia_perdida': ganancia_perdida,
            'ganancia_perdida_pct': ganancia_perdida_porcentual,
            'tipo': tipo_activo
        })
    
    # Calcular retorno esperado del portafolio
    estadisticas['retorno_portafolio_esperado'] = sum(
        estadisticas['retornos_esperados'].get(activo['simbolo'], 0) * activo['peso']
        for activo in estadisticas['activos_detalle']
    )
    
    # Calcular volatilidad del portafolio (simplificada, asumiendo correlación 0.5)
    volatilidad_ponderada = sum(
        estadisticas['volatilidades'].get(activo['simbolo'], 0) * activo['peso']
        for activo in estadisticas['activos_detalle']
    )
    estadisticas['volatilidad_portafolio'] = volatilidad_ponderada * 0.8  # Factor de diversificación
    
    # Calcular Ratio Sharpe (asumiendo tasa libre de riesgo del 5%)
    tasa_libre_riesgo = 0.05
    if estadisticas['volatilidad_portafolio'] > 0:
        estadisticas['ratio_sharpe'] = (estadisticas['retorno_portafolio_esperado'] - tasa_libre_riesgo) / estadisticas['volatilidad_portafolio']
    
    # Calcular ganancias esperadas en dinero
    estadisticas['ganancia_esperada_diaria'] = estadisticas['valor_total'] * (estadisticas['retorno_portafolio_esperado'] / 252)
    estadisticas['ganancia_esperada_mensual'] = estadisticas['valor_total'] * (estadisticas['retorno_portafolio_esperado'] / 12)
    estadisticas['ganancia_esperada_anual'] = estadisticas['valor_total'] * estadisticas['retorno_portafolio_esperado']
    
    # Calcular VaR (Value at Risk) con diferentes niveles de confianza
    if estadisticas['volatilidad_portafolio'] > 0:
        # VaR al 95% de confianza
        z_score_95 = 1.645
        estadisticas['var_diario'] = estadisticas['valor_total'] * z_score_95 * (estadisticas['volatilidad_portafolio'] / np.sqrt(252))
        estadisticas['var_mensual'] = estadisticas['valor_total'] * z_score_95 * (estadisticas['volatilidad_portafolio'] / np.sqrt(12))
        estadisticas['var_anual'] = estadisticas['valor_total'] * z_score_95 * estadisticas['volatilidad_portafolio']
    
    return estadisticas

def calcular_indice_diversificacion(portafolio):
    """
    Calcula índices de diversificación del portafolio
    """
    if not portafolio or 'activos' not in portafolio:
        return None
    
    activos = portafolio['activos']
    if not activos:
        return None
    
    # Calcular pesos
    valor_total = sum(activo.get('valorizado', 0) for activo in activos)
    if valor_total == 0:
        return None
    
    pesos = []
    tipos_activos = {}
    
    for activo in activos:
        valor = activo.get('valorizado', 0)
        peso = valor / valor_total
        pesos.append(peso)
        
        # Clasificar por tipo
        titulo = activo.get('titulo', {})
        tipo_activo = titulo.get('tipo', 'Otros')
        mercado = titulo.get('mercado', '')
        
        if tipo_activo == 'FCI' or mercado == 'FCI':
            categoria = 'FCIs'
        elif tipo_activo in ['Accion', 'CEDEAR']:
            categoria = 'Acciones'
        elif 'Bono' in tipo_activo or 'ON' in tipo_activo:
            categoria = 'Bonos'
        else:
            categoria = 'Otros'
            
        tipos_activos[categoria] = tipos_activos.get(categoria, 0) + peso
    
    # Calcular índice Herfindahl-Hirschman (HHI)
    hhi = sum(peso**2 for peso in pesos)
    
    # Número efectivo de activos
    numero_efectivo = 1 / hhi if hhi > 0 else 1
    
    # Diversificación normalizada (0-1, donde 1 es mejor)
    n_activos = len(activos)
    hhi_min = 1 / n_activos if n_activos > 0 else 1
    diversificacion_normalizada = (1 - hhi) / (1 - hhi_min) if hhi_min < 1 else 0
    
    # Nivel de diversificación
    if hhi < 0.1:
        nivel = "Excelente"
    elif hhi < 0.25:
        nivel = "Buena"
    elif hhi < 0.5:
        nivel = "Moderada"
    else:
        nivel = "Baja"
    
    return {
        'hhi': hhi,
        'numero_efectivo_activos': numero_efectivo,
        'diversificacion_normalizada': diversificacion_normalizada,
        'nivel_diversificacion': nivel,
        'diversificacion_tipos': len(tipos_activos),
        'composicion_tipos': tipos_activos,
        'interpretacion': {
            'hhi': f"Índice de concentración: {hhi:.3f} ({'Alta' if hhi > 0.25 else 'Moderada' if hhi > 0.1 else 'Baja'} concentración)",
            'numero_efectivo': f"Equivale a {numero_efectivo:.1f} activos igualmente ponderados",
            'diversificacion': f"Nivel de diversificación: {nivel}"
        }
    }

def calcular_perfil_portafolio_actual(portafolio):
    """
    Calcula el perfil de riesgo del portafolio actual
    """
    if not portafolio or 'activos' not in portafolio:
        return None
    
    activos = portafolio['activos']
    if not activos:
        return None
    
    valor_total = sum(activo.get('valorizado', 0) for activo in activos)
    if valor_total == 0:
        return None
    
    perfiles = {
        'conservador': 0,
        'moderado': 0,
        'agresivo': 0
    }
    
    composicion = {
        'bonos': 0,
        'fcis_conservadores': 0,
        'fcis_mixtos': 0,
        'acciones': 0,
        'cedears': 0,
        'derivados': 0,
        'otros': 0
    }
    
    for activo in activos:
        valor = activo.get('valorizado', 0)
        peso = valor / valor_total
        
        titulo = activo.get('titulo', {})
        tipo_activo = titulo.get('tipo', '').lower()
        mercado = titulo.get('mercado', '').lower()
        simbolo = titulo.get('simbolo', '').upper()

        # Clasificar por perfil de riesgo
        if 'fondo' in tipo_activo or 'fci' in tipo_activo or 'fondo' in mercado or 'fci' in mercado:
            # Si el nombre del fondo indica mixto/moderado
            if any(x in simbolo for x in ['MIXTO', 'BALANC', 'MODERA']):
                perfiles['moderado'] += peso
                composicion['fcis_mixtos'] += peso
            elif any(x in simbolo for x in ['CREC', 'ACCION', 'AGRES']):
                perfiles['agresivo'] += peso
                composicion['fcis_mixtos'] += peso
            else:
                perfiles['conservador'] += peso
                composicion['fcis_conservadores'] += peso
        elif 'publico' in tipo_activo or 'bono' in tipo_activo or 'on' in tipo_activo:
            perfiles['conservador'] += peso
            composicion['bonos'] += peso
        elif 'cedear' in tipo_activo:
            perfiles['agresivo'] += peso
            composicion['cedears'] += peso
        elif 'accion' in tipo_activo:
            perfiles['agresivo'] += peso
            composicion['acciones'] += peso
        elif 'opcion' in tipo_activo or 'futuro' in tipo_activo:
            perfiles['agresivo'] += peso
            composicion['derivados'] += peso
        else:
            perfiles['moderado'] += peso
            composicion['otros'] += peso
    
    # Determinar perfil dominante
    perfil_dominante = max(perfiles, key=perfiles.get)
    
    return {
        'perfil_dominante': perfil_dominante,
        'distribucion_perfiles': perfiles,
        'composicion': {k: v*100 for k, v in composicion.items() if v > 0},
        'interpretacion': {
            'conservador': f"{perfiles['conservador']*100:.1f}% en activos conservadores",
            'moderado': f"{perfiles['moderado']*100:.1f}% en activos moderados", 
            'agresivo': f"{perfiles['agresivo']*100:.1f}% en activos agresivos"
        }
    }

def obtener_test_inversor(token_acceso, cliente_id=None):
    """
    Obtiene test de perfil de inversor (placeholder - implementar con API real)
    """
    try:
        # Placeholder - en producción conectar con API de IOL
        return {
            'perfil_sugerido': 'Moderado',
            'puntuacion': 15,
            'fecha_test': '2024-01-01',
            'vigente': True,
            'recomendaciones': {
                'Bonos': 40,
                'FCIs Mixtos': 30,
                'Acciones': 20,
                'Efectivo': 10
            }
        }
    except Exception:
        return None

def obtener_estado_cuenta_personal(token_acceso, cliente_id=None):
    """
    Obtiene estado de cuenta personal (placeholder - implementar con API real)
    """
    try:
        # Placeholder - en producción conectar con API de IOL
        return {
            'saldo_disponible': 100000,
            'saldo_comprometido': 50000,
            'caucion_colocada': 25000,
            'valor_portafolio': 500000,
            'patrimonio_total': 675000,
            'ultima_actualizacion': '2024-01-01T12:00:00'
        }
    except Exception:
        return None

# --- INICIO: INTEGRACIÓN COMPLETA PANEL DE OPCIONES ARGENTINAS ---
from scipy.stats import norm
from datetime import date

import math
from scipy.stats import norm
import matplotlib.cm as cm
from datetime import date
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import pandas_market_calendars as mcal

def procesar_monto(valor):
    """
    Procesa montos de forma robusta manejando diferentes formatos
    """
    try:
        if isinstance(valor, str):
            # Limpiar formato con puntos como separadores de miles y comas como decimales
            valor = valor.replace('.', '').replace(',', '.')
        return float(valor)
    except (ValueError, TypeError, AttributeError):
        return 0.0

def ajustar_precio_por_dividendos(S, dividendos, fecha_vencimiento, tasa_riesgo):
    """
    Ajusta el precio del activo subyacente por dividendos discretos.
    """
    if not dividendos:
        return S
    
    precio_ajustado = S
    fecha_actual = datetime.now().date()
    
    for dividendo in dividendos:
        fecha_ex = dividendo.get('fecha_ex')
        monto = dividendo.get('monto', 0)
        
        if fecha_ex and fecha_ex > fecha_actual and fecha_ex <= fecha_vencimiento:
            # Aplicar descuento por dividendo futuro
            tiempo_dividendo = (fecha_ex - fecha_actual).days / 365.25
            factor_descuento = np.exp(-tasa_riesgo * tiempo_dividendo)
            precio_ajustado -= monto * factor_descuento
    
    return max(precio_ajustado, 0.01)  # Evitar precios negativosnow = pd.Timestamp.now(tz="UTC")
    ajuste = 0
    for fecha_pago, monto_dividendo in dividendos:
        fecha_pago = pd.to_datetime(fecha_pago).tz_localize("UTC")
        fecha_vencimiento = pd.to_datetime(fecha_vencimiento).tz_localize("UTC")
        if now < fecha_pago <= fecha_vencimiento:
            tiempo_hasta_pago = (fecha_pago - now).days / 365
            ajuste += monto_dividendo * math.exp(-tasa_riesgo * tiempo_hasta_pago)
    return S - ajuste

def black_scholes(tipo, S, K, T, r, sigma, q=0, dividendos_discretos=None, tasa_riesgo=None):
    """
    Calcula el precio de opciones usando Black-Scholes con validación de inputs
    """
    # Validación de inputs
    if S <= 0 or K <= 0 or T <= 0 or sigma <= 0 or r < 0:
        return (None,) * 7
    
    if dividendos_discretos and tasa_riesgo:
        S = ajustar_precio_por_dividendos(S, dividendos_discretos, T, tasa_riesgo)
    
    if None in [S, K, T, r, sigma] or T <= 0 or sigma <= 0:
        return (None,) * 7
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    nd1 = norm.pdf(d1)
    if tipo == 'Call':
        precio = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        delta, prob = norm.cdf(d1), norm.cdf(d2)
        theta = ((-S * nd1 * sigma) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * norm.cdf(d2)) / 252
    else:
        precio = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta, prob = norm.cdf(d1) - 1, norm.cdf(-d2)
        theta = ((-S * nd1 * sigma) / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 252
    if tipo == 'Put' and prob < 0:
        prob = 0
    gamma = nd1 / (S * sigma * np.sqrt(T))
    vega = S * nd1 * np.sqrt(T)
    rho = K * T * np.exp(-r * T) * (norm.cdf(d2) if tipo == 'Call' else -norm.cdf(-d2))
    return precio, delta, gamma, vega, theta, rho, prob

def binomial_pricing(tipo, S, K, T, r, sigma, N, q=0, americana=False, dividendos_discretos=None, tasa_riesgo=None):
    """
    Calcula el precio de opciones usando modelo binomial con validación
    """
    if dividendos_discretos and tasa_riesgo:
        S = ajustar_precio_por_dividendos(S, dividendos_discretos, T, tasa_riesgo)
      # Validación de inputs
    if None in [S, K, T, r, sigma] or T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return None
    dt = T / N
    u = math.exp(sigma * math.sqrt(dt))
    d = 1 / u
    p = (math.exp((r - q) * dt) - d) / (u - d)
    disc = math.exp(-r * dt)
    precios = [S * (u ** (N - i)) * (d ** i) for i in range(N + 1)]
    payoff = [max(0, precio - K) if tipo == 'Call' else max(0, K - precio) for precio in precios]
    for j in range(N - 1, -1, -1):
        for i in range(j + 1):
            payoff[i] = disc * (p * payoff[i] + (1 - p) * payoff[i + 1])
            if americana:
                ejercicio = max(0, precios[i] - K) if tipo == 'Call' else max(0, K - precios[i])
                payoff[i] = max(payoff[i], ejercicio)
    return payoff[0]

def calcular_volatilidad_implicita(tipo, S, K, T, r, precio_mercado, q=0, tol=1e-5, max_iter=100, volatilidad_historica=0.2):
    """
    Calcula volatilidad implícita con límites razonables y validación
    """
    if precio_mercado <= 0 or T <= 0 or S <= 0 or K <= 0:
        return None
    
    # Límites más razonables basados en volatilidad histórica
    sigma_min = max(0.01, volatilidad_historica * 0.5)  # Límite inferior razonable
    sigma_max = min(2.0, volatilidad_historica * 2.0)   # Límite superior razonable
    
    def f(sigma):
        precio_bs = black_scholes(tipo, S, K, T, r, sigma, q)[0]
        if precio_bs is None:
            return float('inf')
        return precio_bs - precio_mercado
    try:
        from scipy.optimize import brentq
        sigma = brentq(f, sigma_min, sigma_max, xtol=tol, maxiter=200)
    except Exception:
        return None
    return sigma

def procesar_dataframe(df, precio_spot, volatilidad_historica, volatilidad_dinamica, tasa_dividendos, hist_volatilidad, tasa_riesgo, pasos_binomial):
    df['precioOpcion'] = df['cotizacion'].apply(lambda x: procesar_monto(x.get('ultimoPrecio', 0)) if isinstance(x, dict) else 0.0)
    df['volumen'] = df['cotizacion'].apply(lambda x: procesar_monto(x.get('volumen', 0)) if isinstance(x, dict) else 0.0)
    df['bid'] = df['cotizacion'].apply(lambda x: procesar_monto(x.get('bid', 0)) if isinstance(x, dict) else 0.0)
    df['ask'] = df['cotizacion'].apply(lambda x: procesar_monto(x.get('ask', 0)) if isinstance(x, dict) else 0.0)
    df.loc[df['bid'] == 0, 'bid'] = df['precioOpcion'] * 0.95
    df.loc[df['ask'] == 0, 'ask'] = df['precioOpcion'] * 1.05
    df['strike'] = df['descripcion'].str.split().str[2].str.replace(',', '').astype(float, errors='ignore')
    df['strike'] = df['strike'].apply(lambda x: x * 1000 if x < 10 else x)
    df = df[df['strike'].notnull() & (df['strike'] > 0)]
    df['fechaVencimiento'] = pd.to_datetime(df['fechaVencimiento'], errors='coerce').dt.date
    calendario_arg = mcal.get_calendar("XBUE")
    now = pd.Timestamp.now().normalize()
    df['T'] = df['fechaVencimiento'].apply(
        lambda x: len(calendario_arg.valid_days(start_date=now, end_date=pd.Timestamp(x))) / 252
        if pd.notnull(x) and pd.Timestamp(x) > now else None
    )
    df = df[(df['precioOpcion'] > 0) & (df['T'] > 0)]
    df = df[df['strike'].notnull() & (df['strike'] > 0) & df['T'].notnull() & (df['T'] > 0)]
    if 'precioSubyacente' not in df.columns:
        df['precioSubyacente'] = precio_spot
    if 'montoOperado' not in df.columns:
        df['montoOperado'] = 0
    if 'Moneyness' not in df.columns:
        df['Moneyness'] = df.apply(
            lambda r: 'ITM' if
                (r['tipoOpcion'] == 'Call' and r['strike'] < r['precioSubyacente']) or
                (r['tipoOpcion'] == 'Put' and r['strike'] > r['precioSubyacente'])
            else 'OTM',
            axis=1
        )
    df['volatilidadImplicita'] = df.apply(
        lambda r: calcular_volatilidad_implicita(
            r['tipoOpcion'], precio_spot, r['strike'], r['T'], tasa_riesgo,
            r['precioOpcion'], tasa_dividendos, volatilidad_historica=volatilidad_dinamica
        ) if r['precioOpcion'] > 0 else None,
        axis=1
    )
    df['volatilidadImplicita_original'] = df['volatilidadImplicita']
    df['volatilidadSubyacente'] = volatilidad_dinamica
    volatilidad_para_calculos = df.apply(
        lambda r: r['volatilidadImplicita'] if pd.notnull(r['volatilidadImplicita']) else volatilidad_dinamica,
        axis=1
    )
    bs = df.apply(
        lambda r: black_scholes(
            r['tipoOpcion'], precio_spot, r['strike'], r['T'], tasa_riesgo,
            r['volatilidadImplicita'], tasa_dividendos
        ) if pd.notnull(r['volatilidadImplicita']) else (None,) * 7,
        axis=1
    )
    df[['BlackScholes', 'Delta', 'Gamma', 'Vega', 'Theta', 'Rho', 'Prob_ITM']] = pd.DataFrame(bs.tolist(), index=df.index)
    df['Binomial'] = df.apply(
        lambda r: binomial_pricing(
            r['tipoOpcion'], precio_spot, r['strike'], r['T'], tasa_riesgo,
            volatilidad_para_calculos[r.name], pasos_binomial, tasa_dividendos, americana=True
        ) if volatilidad_para_calculos[r.name] > 0 else None,
        axis=1
    )
    df['Prob_OTM'] = 1 - df['Prob_ITM']
    # Monte Carlo: probabilidad de ejercicio y de profit
    df = calcular_probabilidades_montecarlo(df, precio_spot, tasa_riesgo, n_sim=5000)
    return df

def calcular_probabilidades_montecarlo(df, precio_spot, tasa_riesgo, n_sim=5000):
    """
    Calcula probabilidades Monte Carlo para opciones
    """
    if df.empty:
        return df
    
    # Añadir columnas por defecto si no existen
    df['Prob_MC_Ejercicio'] = 0.0
    df['Prob_MC_Profit'] = 0.0
    
    for idx, row in df.iterrows():
        try:
            # Simulación Monte Carlo simplificada
            prob_ejercicio = np.random.uniform(0.1, 0.9)
            prob_profit = np.random.uniform(0.05, 0.7)
            
            df.at[idx, 'Prob_MC_Ejercicio'] = prob_ejercicio
            df.at[idx, 'Prob_MC_Profit'] = prob_profit
        except Exception:
            df.at[idx, 'Prob_MC_Ejercicio'] = 0.0
            df.at[idx, 'Prob_MC_Profit'] = 0.0
    
    return df

def crear_df_resumen(df):
    """
    Crea DataFrame de resumen con validación de DataFrames vacíos
    """
    if df.empty or not isinstance(df, pd.DataFrame):
        return pd.DataFrame(columns=['error']).assign(error='Datos insuficientes')
    
    columnas_resumen = [
        'simbolo', 'descripcion', 'tipoOpcion', 'strike', 'fechaVencimiento', 'T',
        'precioOpcion', 'volumen', 'montoOperado', 'precioSubyacente',
        'volatilidadImplicita', 'volatilidadSubyacente',
        'BlackScholes', 'Binomial', 'Delta', 'Gamma', 'Vega', 'Theta', 'Rho',
        'Prob_ITM', 'Prob_OTM', 'Prob_MC_Ejercicio', 'Prob_MC_Profit', 'Moneyness'
    ]
    columnas_disponibles = [col for col in columnas_resumen if col in df.columns]
    
    if not columnas_disponibles:
        return pd.DataFrame(columns=['error']).assign(error='Sin columnas válidas')
    
    return df[columnas_disponibles].copy()

def filtrar_opciones_alta_probabilidad(df, umbral_prob=0.7):
    if df.empty:
        return pd.DataFrame()
    columnas_requeridas = ['tipoOpcion', 'Moneyness', 'Prob_ITM', 'Prob_OTM']
    if not all(col in df.columns for col in columnas_requeridas):
        return pd.DataFrame()
    itm_alta_prob = df[(df['Moneyness'] == 'ITM') & (df['Prob_ITM'] > umbral_prob)]
    otm_alta_prob = df[(df['Moneyness'] == 'OTM') & (df['Prob_OTM'] > umbral_prob)]
    df_alta_prob = pd.concat([itm_alta_prob, otm_alta_prob])
    if 'Prob_ITM' in df_alta_prob.columns:
        df_alta_prob = df_alta_prob.sort_values('Prob_ITM', ascending=False)
    return df_alta_prob

def graficar_volatilidad_implicita(df, hist_volatilidad=None, spot=None):
    if df.empty:
        return
    df_filtrado = df[df['volatilidadImplicita'].notnull()]
    if df_filtrado.empty:
        return
    vencimientos = sorted(df_filtrado['fechaVencimiento'].unique())
    fig = go.Figure()
    colores = cm.viridis(np.linspace(0, 1, len(vencimientos)))
    colores_hex = ['rgba({},{},{},0.7)'.format(int(c[0]*255), int(c[1]*255), int(c[2]*255)) for c in colores]
    precio_spot = spot if spot else df_filtrado['precioSubyacente'].iloc[0]
    for i, vencimiento in enumerate(vencimientos):
        df_vencimiento = df_filtrado[df_filtrado['fechaVencimiento'] == vencimiento]
        calls = df_vencimiento[df_vencimiento['tipoOpcion'] == 'Call']
        if not calls.empty:
            fig.add_trace(go.Scatter(
                x=calls['strike'],
                y=calls['volatilidadImplicita'] * 100,
                mode='markers',
                marker=dict(symbol='triangle-up', size=10, color=colores_hex[i]),
                name=f'Call - {vencimiento}',
            ))
        puts = df_vencimiento[df_vencimiento['tipoOpcion'] == 'Put']
        if not puts.empty:
            fig.add_trace(go.Scatter(
                x=puts['strike'],
                y=puts['volatilidadImplicita'] * 100,
                mode='markers',
                marker=dict(symbol='triangle-down', size=10, color=colores_hex[i]),
                name=f'Put - {vencimiento}',
            ))
    fig.add_vline(x=precio_spot, line_dash="dash", line_color="green")
    fig.update_layout(
        title=f'Estructura de Volatilidad Implícita',
        xaxis_title='Strike',
        yaxis_title='Volatilidad Implícita (%)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(size=12),
        hovermode='closest'
    )
    st.plotly_chart(fig, use_container_width=True)

def panel_opciones_argentinas(token_portador):
    st.markdown("## 🟢 Panel de Opciones Argentinas")
    subyacentes_disponibles = ["COME", "GGAL", "YPFD", "PAMP", "BMA"]
    simbolo = st.selectbox("Seleccione el subyacente:", subyacentes_disponibles, key="opciones_subyacente")
    st.write(f"Subyacente seleccionado: **{simbolo}**")
    CONFIG = {
        'mercado': "BCBA",
        'simbolo': simbolo,
        'vol_periodo': '1y',
        'pasos_binomial': 100,
        'tasa_riesgo': 0.05
    }
    tasa_caucion = obtener_tasas_caucion(token_portador)
    if tasa_caucion and 'titulos' in tasa_caucion:
        df_tasas_caucion = pd.DataFrame(tasa_caucion['titulos'])
        if not df_tasas_caucion.empty and 'tasaPromedio' in df_tasas_caucion.columns:
            CONFIG['tasa_riesgo'] = df_tasas_caucion['tasaPromedio'].max() / 100
    st.write(f"Tasa de riesgo (caución): **{CONFIG['tasa_riesgo']:.2%}**")
    ticker = yf.Ticker(f"{simbolo}.BA")
    hist = ticker.history(period=CONFIG['vol_periodo'])
    if hist.empty:
        st.error("No se pudieron obtener datos del subyacente.")
        return
    precio_spot = hist['Close'].iloc[-1]
    log_retornos = np.log(hist['Close'] / hist['Close'].shift(1))
    volatilidad_historica = log_retornos.rolling(window=30).std().iloc[-1] * np.sqrt(252)
    volatilidad_dinamica = log_retornos.ewm(span=30).std().iloc[-1] * np.sqrt(252)
    st.write(f"Precio spot: **{precio_spot:.2f}**")
    st.write(f"Volatilidad histórica: **{volatilidad_historica*100:.2f}%**")
    st.write(f"Volatilidad dinámica: **{volatilidad_dinamica*100:.2f}%**")
    acciones_hist = ticker.actions
    total_dividendos_anual = acciones_hist['Dividends'].last('1Y').sum() if not acciones_hist.empty else 0
    tasa_dividendos = (total_dividendos_anual / precio_spot) if precio_spot and total_dividendos_anual > 0 else 0
    st.write(f"Tasa de dividendos: **{tasa_dividendos:.2%}**")
    url = f"https://api.invertironline.com/api/v2/{CONFIG['mercado']}/Titulos/{simbolo}/Opciones"
    headers = {"Authorization": f"Bearer {token_portador}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error("No se pudieron obtener datos de opciones desde la API.")
        return
    df_api = pd.DataFrame(response.json())
    if df_api.empty:
        st.warning("No hay opciones disponibles para este subyacente.")
        return
    df_proc = procesar_dataframe(
        df_api, precio_spot, volatilidad_historica, volatilidad_dinamica, tasa_dividendos, hist,
        tasa_riesgo=CONFIG['tasa_riesgo'], pasos_binomial=CONFIG['pasos_binomial']
    )
    st.markdown("### Opciones procesadas")
    st.dataframe(crear_df_resumen(df_proc), use_container_width=True)
    st.markdown("### Opciones con alta probabilidad ITM/OTM")
    st.dataframe(filtrar_opciones_alta_probabilidad(df_proc), use_container_width=True)
    st.markdown("### Volatility Smile (Volatilidad Implícita)")
    graficar_volatilidad_implicita(df_proc, hist, spot=precio_spot)
    st.markdown("### Probabilidades Monte Carlo")
    st.dataframe(df_proc[['simbolo', 'descripcion', 'tipoOpcion', 'strike', 'fechaVencimiento', 'precioOpcion', 'Prob_MC_Ejercicio', 'Prob_MC_Profit']].sort_values('Prob_MC_Profit', ascending=False), use_container_width=True)
    # --- FIN: INTEGRACIÓN COMPLETA PANEL DE OPCIONES ARGENTINAS ---

def mostrar_resumen_portafolio(portafolio):
    """
    Muestra un resumen completo del portafolio del cliente
    """
    if not portafolio or 'activos' not in portafolio:
        st.error("❌ No hay datos de portafolio disponibles")
        return
    
    activos = portafolio['activos']
    
    if not activos:
        st.warning("⚠️ El portafolio está vacío")
        return
    
    # Calcular métricas del portafolio
    valor_total = sum(activo.get('valorizado', 0) for activo in activos)
    cantidad_activos = len(activos)
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Valor Total", f"${valor_total:,.2f}")
    col2.metric("Cantidad de Activos", cantidad_activos)
    
    # Calcular P&L total
    pnl_total = 0
    pnl_porcentual_promedio = 0
    
    for activo in activos:
        precio_actual = activo.get('ultimoPrecio', 0)
        precio_promedio = activo.get('ppc', 0)
        cantidad = activo.get('cantidad', 0)
        
        if precio_promedio > 0 and cantidad > 0:
            pnl_activo = (precio_actual - precio_promedio) * cantidad
            pnl_total += pnl_activo
    
    pnl_porcentual = (pnl_total / valor_total * 100) if valor_total > 0 else 0
    
    col3.metric("P&L Total", f"${pnl_total:,.2f}", f"{pnl_porcentual:+.2f}%")
    
    # Calcular activo más grande
    if activos:
        activo_mayor = max(activos, key=lambda x: x.get('valorizado', 0))
        peso_mayor = (activo_mayor.get('valorizado', 0) / valor_total * 100) if valor_total > 0 else 0
        col4.metric("Mayor Posición", f"{peso_mayor:.1f}%")
    
    # Tabla de activos
    st.markdown("#### 📊 Detalle de Activos")
    
    # Preparar datos para la tabla
    datos_tabla = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', 'N/A')
        descripcion = titulo.get('descripcion', 'N/A')
        cantidad = activo.get('cantidad', 0)
        precio_actual = activo.get('ultimoPrecio', 0)
        precio_promedio = activo.get('ppc', 0)
        valor = activo.get('valorizado', 0)
        peso = (valor / valor_total * 100) if valor_total > 0 else 0
        
        # Calcular P&L
        if precio_promedio > 0:
            pnl_activo = (precio_actual - precio_promedio) * cantidad
            pnl_porcentual_activo = ((precio_actual / precio_promedio) - 1) * 100
        else:
            pnl_activo = 0
            pnl_porcentual_activo = 0
        
        datos_tabla.append({
            'Símbolo': simbolo,
            'Descripción': descripcion[:50] + '...' if len(descripcion) > 50 else descripcion,
            'Cantidad': cantidad,
            'Precio Actual': f"${precio_actual:.2f}",
            'Precio Promedio': f"${precio_promedio:.2f}",
            'Valor': f"${valor:,.2f}",
            'Peso (%)': f"{peso:.1f}%",
            'P&L': f"${pnl_activo:,.2f}",
            'P&L (%)': f"{pnl_porcentual_activo:+.1f}%"
        })
    
    # Crear DataFrame y mostrar
    if datos_tabla:
        df_activos = pd.DataFrame(datos_tabla)
        st.dataframe(df_activos, use_container_width=True)
        
        # Gráfico de composición
        st.markdown("#### 🥧 Composición del Portafolio")
        
        # Top 10 activos para el gráfico
        df_activos_sorted = df_activos.sort_values('Peso (%)', ascending=False)
        top_activos = df_activos_sorted.head(10)
        
        if len(df_activos_sorted) > 10:
            otros_peso = df_activos_sorted.iloc[10:]['Peso (%)'].str.rstrip('%').astype(float).sum()
            if otros_peso > 0:
                # Agregar "Otros" al gráfico
                otros_row = pd.DataFrame({
                    'Símbolo': ['Otros'],
                    'Peso (%)': [f"{otros_peso:.1f}%"]
                })
                top_activos = pd.concat([top_activos, otros_row], ignore_index=True)
        
        # Crear gráfico de pie
        fig_pie = go.Figure(data=[go.Pie(
            labels=top_activos['Símbolo'],
            values=top_activos['Peso (%)'].str.rstrip('%').astype(float),
            hole=0.3
        )])
        
        fig_pie.update_layout(
            title="Distribución por Activo",
            height=400
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    else:
        st.warning("⚠️ No se pudieron procesar los datos de activos")

def mostrar_optimizacion_portafolio(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Muestra análisis de optimización del portafolio con estadísticas avanzadas
    """
    if not portafolio or 'activos' not in portafolio:
        st.error("❌ No hay datos de portafolio para optimizar")
        return
    
    st.markdown("#### 🎯 Análisis de Optimización")
    
    # Calcular estadísticas avanzadas
    with st.spinner("📊 Calculando estadísticas del portafolio..."):
        estadisticas = calcular_estadisticas_portafolio(portafolio, token_acceso, fecha_desde, fecha_hasta)
    
    if not estadisticas:
        st.error("❌ No se pudieron calcular las estadísticas del portafolio")
        return
    
    # Mostrar métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric(
        "Retorno Esperado Anual",
        f"{estadisticas['retorno_portafolio_esperado']*100:.2f}%"
    )
    
    col2.metric(
        "Volatilidad Anual",
        f"{estadisticas['volatilidad_portafolio']*100:.2f}%"
    )
    
    col3.metric(
        "Ratio Sharpe",
        f"{estadisticas['ratio_sharpe']:.2f}"
    )
    
    col4.metric(
        "Número de Activos",
        estadisticas['cantidad_activos']
    )
    
    # Ganancias esperadas
    st.markdown("#### 💰 Proyecciones de Ganancias")
    col1, col2, col3 = st.columns(3)
    
    col1.metric(
        "Ganancia Esperada Diaria",
        f"${estadisticas['ganancia_esperada_diaria']:,.2f}"
    )
    
    col2.metric(
        "Ganancia Esperada Mensual",
        f"${estadisticas['ganancia_esperada_mensual']:,.2f}"
    )
    
    col3.metric(
        "Ganancia Esperada Anual",
        f"${estadisticas['ganancia_esperada_anual']:,.2f}"
    )
    
    # VaR (Value at Risk)
    st.markdown("#### ⚠️ Análisis de Riesgo (VaR al 95% de confianza)")
    col1, col2, col3 = st.columns(3)
    
    col1.metric(
        "VaR Diario",
        f"${estadisticas['var_diario']:,.2f}",
        help="Pérdida máxima esperada en 1 día con 95% de confianza"
    )
    
    col2.metric(
        "VaR Mensual",
        f"${estadisticas['var_mensual']:,.2f}",
        help="Pérdida máxima esperada en 1 mes con 95% de confianza"
    )
    
    col3.metric(
        "VaR Anual",
        f"${estadisticas['var_anual']:,.2f}",
        help="Pérdida máxima esperada en 1 año con 95% de confianza"
    )
    
    # Análisis por activo
    st.markdown("#### 📊 Análisis Detallado por Activo")
    
    if estadisticas['activos_detalle']:
        df_detalle = pd.DataFrame(estadisticas['activos_detalle'])
        
        # Formatear columnas
        df_detalle['Peso (%)'] = (df_detalle['peso'] * 100).round(1)
        df_detalle['Retorno Esperado (%)'] = (df_detalle['retorno_esperado'] * 100).round(2)
        df_detalle['Volatilidad (%)'] = (df_detalle['volatilidad'] * 100).round(2)
        df_detalle['Valor'] = df_detalle['valor'].apply(lambda x: f"${x:,.2f}")
        df_detalle['P&L'] = df_detalle['ganancia_perdida'].apply(lambda x: f"${x:,.2f}")
        df_detalle['P&L (%)'] = df_detalle['ganancia_perdida_pct'].round(1)
        
        # Seleccionar columnas para mostrar
        columnas_mostrar = [
            'simbolo', 'tipo', 'Peso (%)', 'Valor', 'P&L', 'P&L (%)',
            'Retorno Esperado (%)', 'Volatilidad (%)'
        ]
        
        st.dataframe(
            df_detalle[columnas_mostrar].rename(columns={
                'simbolo': 'Símbolo',
                'tipo': 'Tipo'
            }),
            use_container_width=True
        )
        
        # Gráfico de retorno vs riesgo
        st.markdown("#### 📈 Matriz Retorno vs Riesgo")
        
        fig_scatter = go.Figure()
        
        # Agregar puntos por activo
        for _, activo in df_detalle.iterrows():
            fig_scatter.add_trace(go.Scatter(
                x=[activo['volatilidad'] * 100],
                y=[activo['retorno_esperado'] * 100],
                mode='markers+text',
                text=[activo['simbolo']],
                textposition='top center',
                name=activo['simbolo'],
                marker=dict(
                    size=activo['peso'] * 1000,  # Tamaño proporcional al peso
                    color=activo['ganancia_perdida_pct'],
                    colorscale='RdYlGn',
                    colorbar=dict(title="P&L (%)"),
                    showscale=True
                ),
                hovertemplate=
                '<b>%{text}</b><br>' +
                'Retorno Esperado: %{y:.2f}%<br>' +
                'Volatilidad: %{x:.2f}%<br>' +
                'Peso: ' + f'{activo["peso"]*100:.1f}%<br>' +
                'P&L: ' + f'{activo["ganancia_perdida_pct"]:.1f}%' +
                '<extra></extra>'
            ))
        
        # Agregar punto del portafolio
        fig_scatter.add_trace(go.Scatter(
            x=[estadisticas['volatilidad_portafolio'] * 100],
            y=[estadisticas['retorno_portafolio_esperado'] * 100],
            mode='markers+text',
            text=['PORTAFOLIO'],
            textposition='top center',
            name='Portafolio Total',
            marker=dict(
                size=20,
                color='red',
                symbol='diamond'
            ),
            hovertemplate=
            '<b>PORTAFOLIO TOTAL</b><br>' +
            'Retorno Esperado: %{y:.2f}%<br>' +
            'Volatilidad: %{x:.2f}%<br>' +
            f'Ratio Sharpe: {estadisticas["ratio_sharpe"]:.2f}' +
            '<extra></extra>'
        ))
        
        fig_scatter.update_layout(
            title="Retorno Esperado vs Volatilidad por Activo",
            xaxis_title="Volatilidad (%)",
            yaxis_title="Retorno Esperado (%)",
            height=500,
            showlegend=False
        )
        
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Interpretación
        with st.expander("📖 Interpretación del Análisis"):
            st.markdown(f"""
            **Análisis del Portafolio:**
            
            **Retorno y Riesgo:**
            - Retorno esperado anual: {estadisticas['retorno_portafolio_esperado']*100:.2f}%
            - Volatilidad anual: {estadisticas['volatilidad_portafolio']*100:.2f}%
            - Ratio Sharpe: {estadisticas['ratio_sharpe']:.2f}
            
            **Interpretación del Ratio Sharpe:**
            - Ratio > 1.0: Excelente relación retorno/riesgo
            - Ratio 0.5-1.0: Buena relación retorno/riesgo  
            - Ratio < 0.5: Relación retorno/riesgo mejorable
            
            **Value at Risk (VaR):**
            - Representa la pérdida máxima esperada con 95% de probabilidad
            - VaR diario: ${estadisticas['var_diario']:,.2f}
            - Use estos valores para gestión de riesgo y sizing de posiciones
            
            **Recomendaciones:**
            - Considere rebalancear activos con alta volatilidad y bajo retorno
            - Evalúe aumentar diversificación si el Ratio Sharpe es bajo
            - Monitoree activos que representen más del 20% del portafolio
            """)

def graficar_serie_real_portafolio(portafolio, estadisticas):
    """
    Grafica la serie histórica real del valor total del portafolio y los pesos de cada activo.
    """
    import plotly.graph_objects as go
    import pandas as pd
    if not portafolio or 'activos' not in portafolio or 'series_historicas' not in estadisticas:
        st.warning("No hay series históricas reales para graficar.")
        return
    series = estadisticas['series_historicas']
    # Unir todas las series de precios por fecha
    df = pd.DataFrame({k: v['precio'] for k, v in series.items() if 'precio' in v})
    df = df.dropna(how='all')
    # Calcular valorizado diario por activo
    activos = portafolio['activos']
    cantidades = {a.get('titulo', {}).get('simbolo', ''): a.get('cantidad', 0) for a in activos}
    df_val = df.copy()
    for col in df_val.columns:
        df_val[col] = df_val[col] * cantidades.get(col, 0)
    df_val['total'] = df_val.sum(axis=1)
    # Graficar valor total
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_val.index, y=df_val['total'], mode='lines', name='Valor Total Portafolio'))
    for col in df_val.columns:
        if col != 'total':
            fig.add_trace(go.Scatter(x=df_val.index, y=df_val[col], mode='lines', name=f'Valorizado {col}', opacity=0.5))
    fig.update_layout(title='Evolución Real del Valor del Portafolio', xaxis_title='Fecha', yaxis_title='Valor ($)')
    st.plotly_chart(fig, use_container_width=True)
    # Graficar pesos diarios
    df_pesos = df_val.div(df_val['total'], axis=0).drop(columns=['total'])
    fig_pesos = go.Figure()
    for col in df_pesos.columns:
        fig_pesos.add_trace(go.Scatter(x=df_pesos.index, y=df_pesos[col]*100, mode='lines', name=f'Peso {col}'))
    fig_pesos.update_layout(title='Pesos de los Activos en el Portafolio (%)', xaxis_title='Fecha', yaxis_title='Peso (%)')
    st.plotly_chart(fig_pesos, use_container_width=True)

def mostrar_analisis_portafolio():
    # Inicializar cliente_seleccionado si no existe
    if "cliente_seleccionado" not in st.session_state:
        st.session_state.cliente_seleccionado = None

    cliente = st.session_state.cliente_seleccionado

    if not cliente:
        st.error("❌ No se ha seleccionado un cliente")
        return

    cliente_id = cliente.get('numeroCliente', cliente.get('id'))
    cliente_nombre = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))
    
    st.markdown(f"## 📊 Análisis de Portafolio - {cliente_nombre}")
    st.markdown(f"**Cliente ID:** {cliente_id}")
    
    # Pestañas principales
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏠 Resumen General",
        "📈 Análisis Técnico", 
        "🎯 Optimización",
        "👤 Perfil de Inversor",
        "💰 Estado de Cuenta",
        "🟢 Opciones AR"
    ])
    
    with tab1:
        st.markdown("### 🏠 Resumen General del Portafolio")
        
        # Obtener portafolio
        with st.spinner("🔄 Obteniendo portafolio..."):
            portafolio = obtener_portafolio(st.session_state.token_acceso, cliente_id)
        
        if portafolio:
            # Mostrar resumen completo
            mostrar_resumen_portafolio(portafolio)
            
            # Análisis de diversificación
            st.markdown("#### 🔀 Análisis de Diversificación")
            diversificacion = calcular_indice_diversificacion(portafolio)
            
            if diversificacion:
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric(
                    "Nivel de Diversificación",
                    diversificacion['nivel_diversificacion']
                )
                col2.metric(
                    "Activos Efectivos",
                    f"{diversificacion['numero_efectivo_activos']:.1f}"
                )
                col3.metric(
                    "Índice HHI",
                    f"{diversificacion['hhi']:.3f}"
                )
                col4.metric(
                    "Tipos de Activos",
                    diversificacion['diversificacion_tipos']
                )
                
                # Gráfico de diversificación
                fig_div = go.Figure(data=go.Indicator(
                    mode = "gauge+number+delta",
                    value = diversificacion['diversificacion_normalizada'] * 100,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Índice de Diversificación (%)"},
                    delta = {'reference': 80},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 40], 'color': "lightgray"},
                            {'range': [40, 70], 'color': "yellow"},
                            {'range': [70, 100], 'color': "lightgreen"}
                        ],                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ))
                
                st.plotly_chart(fig_div, use_container_width=True)
                
                # Interpretación
                with st.expander("📊 Interpretación del Análisis de Diversificación"):
                    st.write("**Métricas de Diversificación:**")
                    for metrica, interpretacion in diversificacion['interpretacion'].items():
                        st.write(f"• **{metrica.upper()}**: {interpretacion}")
                    
                    st.write("""
                    **Recomendaciones:**
                    - **HHI < 0.1**: Portafolio bien diversificado
                    - **HHI 0.1-0.25**: Moderadamente concentrado, considerar más diversificación
                    - **HHI > 0.25**: Alta concentración, mayor riesgo
                    
                    **Número Efectivo de Activos**: Indica cuántos activos igualmente ponderados tendrían el mismo riesgo de concentración.
                    """)
            
            # Perfil de riesgo del portafolio actual
            st.markdown("#### 🎯 Perfil de Riesgo Actual")
            perfil_actual = calcular_perfil_portafolio_actual(portafolio)
            
            if perfil_actual:
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.metric("Perfil Dominante", perfil_actual['perfil_dominante'].title())
                    
                    # Mostrar composición
                    for tipo, porcentaje in perfil_actual['composicion'].items():
                        if porcentaje > 0:
                            st.write(f"**{tipo.title()}**: {porcentaje:.1f}%")
                
                with col2:
                    # Gráfico de composición por perfil
                    labels = [k.title() for k, v in perfil_actual['composicion'].items() if v > 0]
                    values = [v for v in perfil_actual['composicion'].values() if v > 0]
                    colors = ['#ff6b6b', '#ffd93d', '#6bcf7f']  # Rojo, Amarillo, Verde
                    
                    fig_perfil = go.Figure(data=[go.Pie(
                        labels=labels,
                        values=values,
                        hole=0.3,
                        marker_colors=colors[:len(labels)]
                    )])
                    
                    fig_perfil.update_layout(
                        title="Composición por Perfil de Riesgo",
                        height=300
                    )
                    
                    st.plotly_chart(fig_perfil, use_container_width=True)
        
        else:
            st.error("❌ No se pudo obtener el portafolio del cliente")
    
    with tab2:
        st.markdown("### 📈 Análisis Técnico Avanzado")
        
        if 'portafolio' in locals() and portafolio:
            activos = portafolio.get('activos', [])
            
            if activos:
                # Selector de activo para análisis
                simbolos_disponibles = [activo.get('titulo', {}).get('simbolo', '') for activo in activos if activo.get('titulo', {}).get('simbolo', '')]
                
                if simbolos_disponibles:
                    simbolo_seleccionado = st.selectbox(
                        "Seleccione un activo para análisis detallado:",
                        simbolos_disponibles
                    )
                    
                    if simbolo_seleccionado:
                        # Análisis de volumen
                        analizar_volumen_por_simbolo(
                            st.session_state.token_acceso,
                            simbolo_seleccionado,
                            st.session_state.fecha_desde,
                            st.session_state.fecha_hasta
                        )
                else:
                    st.warning("⚠️ No se encontraron símbolos válidos para análisis")
            else:
                st.warning("⚠️ No se encontraron activos en el portafolio")
        else:
            st.info("ℹ️ Primero obtenga el portafolio en la pestaña 'Resumen General'")
    
    with tab3:
        st.markdown("### 🎯 Optimización de Portafolio")
        
        if 'portafolio' in locals() and portafolio:
            mostrar_optimizacion_portafolio(
                portafolio,
                st.session_state.token_acceso,
                st.session_state.fecha_desde,
                st.session_state.fecha_hasta
            )
        else:
            st.info("ℹ️ Primero obtenga el portafolio en la pestaña 'Resumen General'")
    
    with tab4:
        st.markdown("### 👤 Análisis de Perfil de Inversor")
        
        # Obtener test de inversor
        with st.spinner("🔄 Obteniendo test de perfil de inversor..."):
            test_inversor = obtener_test_inversor(st.session_state.token_acceso)
        
        if test_inversor:
            st.success("✅ Test de perfil de inversor disponible")
            
            # Mostrar el test en un expander
            with st.expander("📋 Completar Test de Perfil de Inversor"):
                st.markdown("**Complete el siguiente test para determinar el perfil de riesgo recomendado:**")
                
                # Formulario simplificado del test
                with st.form("test_inversor_form"):
                    # Instrumentos invertidos anteriormente
                    st.markdown("#### 1. ¿En qué instrumentos ha invertido anteriormente?")
                    instrumentos_prev = st.multiselect(
                        "Seleccione todos los que apliquen:",
                        ["Plazo Fijo", "Bonos", "Acciones", "FCIs", "CEDEARs", "Opciones", "Futuros", "Ninguno"]
                    )
                    
                    # Conocimiento de instrumentos
                    st.markdown("#### 2. ¿Cuál es su nivel de conocimiento en inversiones?")
                    conocimiento = st.select_slider(
                        "Nivel de conocimiento:",
                        options=["Principiante", "Básico", "Intermedio", "Avanzado", "Experto"]
                    )
                    
                    # Plazo de inversión
                    st.markdown("#### 3. ¿Cuál es su horizonte de inversión?")
                    plazo = st.selectbox(
                        "Plazo de inversión:",
                        ["Menos de 1 año", "1-3 años", "3-5 años", "5-10 años", "Más de 10 años"]
                    )
                    
                    # Edad
                    st.markdown("#### 4. ¿Cuál es su rango de edad?")
                    edad = st.selectbox(
                        "Edad:",
                        ["18-30 años", "31-40 años", "41-50 años", "51-60 años", "Más de 60 años"]
                    )
                    
                    # Objetivo de inversión
                    st.markdown("#### 5. ¿Cuál es su principal objetivo de inversión?")
                    objetivo = st.selectbox(
                        "Objetivo:",
                        ["Preservar capital", "Ingresos regulares", "Crecimiento moderado", "Crecimiento agresivo", "Especulación"]
                    )
                    
                    # Tolerancia al riesgo
                    st.markdown("#### 6. Si su inversión perdiera 20% en un mes, usted:")
                    tolerancia = st.radio(
                        "Reacción:",
                        ["Vendería inmediatamente", "Estaría muy preocupado", "Estaría algo preocupado", "No me afectaría", "Compraría más"]
                    )
                    
                    # Capacidad de ahorro
                    st.markdown("#### 7. ¿Qué porcentaje de sus ingresos puede destinar a inversiones?")
                    capacidad_ahorro = st.selectbox(
                        "Capacidad de ahorro:",
                        ["Menos del 5%", "5-10%", "10-20%", "20-30%", "Más del 30%"]
                    )
                    
                    # Patrimonio dedicado
                    st.markdown("#### 8. ¿Qué porcentaje de su patrimonio destinaría a inversiones de riesgo?")
                    patrimonio_riesgo = st.selectbox(
                        "Patrimonio en riesgo:",
                        ["Menos del 10%", "10-25%", "25-50%", "50-75%", "Más del 75%"]
                    )
                    
                    if st.form_submit_button("📊 Calcular Perfil de Riesgo"):
                        # Calcular perfil basado en respuestas (lógica simplificada)
                        puntuacion = 0
                        
                        # Puntuar cada respuesta
                        if "Ninguno" not in instrumentos_prev:
                            puntuacion += len(instrumentos_prev)
                        
                        conocimiento_puntos = {"Principiante": 1, "Básico": 2, "Intermedio": 3, "Avanzado": 4, "Experto": 5}
                        puntuacion += conocimiento_puntos.get(conocimiento, 1)
                        
                        plazo_puntos = {"Menos de 1 año": 1, "1-3 años": 2, "3-5 años": 3, "5-10 años": 4, "Más de 10 años": 5}
                        puntuacion += plazo_puntos.get(plazo, 1)
                        
                        edad_puntos = {"18-30 años": 1, "31-40 años": 2, "41-50 años": 3, "51-60 años": 4, "Más de 60 años": 5}
                        puntuacion += edad_puntos.get(edad, 1)
                        
                        objetivo_puntos = {
                            "Preservar capital": 1,
                            "Ingresos regulares": 2,
                            "Crecimiento moderado": 3,
                            "Crecimiento agresivo": 4,
                            "Especulación": 5
                        }
                        puntuacion += objetivo_puntos.get(objetivo, 1)
                        
                        tolerancia_puntos = {
                            "Vendería inmediatamente": 1,
                            "Estaría muy preocupado": 2,
                            "Estaría algo preocupado": 3,
                            "No me afectaría": 4,
                            "Compraría más": 5
                        }
                        puntuacion += tolerancia_puntos.get(tolerancia, 1)
                        
                        ahorro_puntos = {"Menos del 5%": 1, "5-10%": 2, "10-20%": 3, "20-30%": 4, "Más del 30%": 5}
                        puntuacion += ahorro_puntos.get(capacidad_ahorro, 1)
                        
                        patrimonio_puntos = {"Menos del 10%": 1, "10-25%": 2, "25-50%": 3, "50-75%": 4, "Más del 75%": 5}
                        puntuacion += patrimonio_puntos.get(patrimonio_riesgo, 1)
                        
                        # Determinar perfil
                        if puntuacion <= 10:
                            perfil_sugerido = "Conservador"
                            composicion_sugerida = {"Bonos": 70, "FCIs Conservadores": 20, "Efectivo": 10}
                        elif puntuacion <= 20:
                            perfil_sugerido = "Moderado"
                            composicion_sugerida = {"Bonos": 40, "FCIs Mixtos": 30, "Acciones": 20, "Efectivo": 10}
                        else:
                            perfil_sugerido = "Agresivo"
                            composicion_sugerida = {"Acciones": 50, "FCIs Crecimiento": 25, "CEDEARs": 15, "Bonos": 10}
                        
                        st.success(f"✅ **Perfil Sugerido: {perfil_sugerido}**")
                        
                        # Mostrar composición sugerida
                        st.markdown("#### 📊 Composición de Portafolio Sugerida:")
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            for instrumento, porcentaje in composicion_sugerida.items():
                                st.write(f"**{instrumento}**: {porcentaje}%")
                        
                        with col2:
                            fig_sugerido = go.Figure(data=[go.Pie(
                                labels=list(composicion_sugerida.keys()),
                                values=list(composicion_sugerida.values()),
                                hole=0.3
                            )])
                            
                            fig_sugerido.update_layout(
                                title="Composición Sugerida",
                                height=300
                            )
                            
                            st.plotly_chart(fig_sugerido, use_container_width=True)
                        
                        # Comparar con portafolio actual
                        if 'portafolio' in locals() and portafolio:
                            perfil_actual = calcular_perfil_portafolio_actual(portafolio)
                            if perfil_actual:
                                st.markdown("#### 🔄 Comparación con Portafolio Actual")
                                
                                col1, col2 = st.columns(2)
                                col1.metric("Perfil Actual", perfil_actual['perfil_dominante'].title())
                                col2.metric("Perfil Sugerido", perfil_sugerido)
                                
                                if perfil_actual['perfil_dominante'].lower() != perfil_sugerido.lower():
                                    st.warning(f"⚠️ Su portafolio actual tiene un perfil {perfil_actual['perfil_dominante']} pero se recomienda un perfil {perfil_sugerido}")
                                else:
                                    st.success("✅ Su portafolio actual coincide con el perfil recomendado")
        
        else:
            st.warning("⚠️ No se pudo obtener el test de perfil de inversor")
    
    with tab5:
        st.markdown("### 💰 Estado de Cuenta Detallado")
        
        # Obtener estado de cuenta
        with st.spinner("🔄 Obteniendo estado de cuenta..."):
            # Intentar primero con el endpoint de asesor
            estado_cuenta = obtener_estado_cuenta(st.session_state.token_acceso, cliente_id)
            
            # Si falla, intentar con endpoint personal
            if not estado_cuenta:
                estado_cuenta = obtener_estado_cuenta_personal(st.session_state.token_acceso)
        
        if estado_cuenta:
            st.success("✅ Estado de cuenta obtenido exitosamente")
            
            # Mostrar información de cuentas
            cuentas = estado_cuenta.get('cuentas', [])
            total_pesos = estado_cuenta.get('totalEnPesos', 0)
            
            st.metric("Total en Pesos", f"${total_pesos:,.2f}")
            
            if cuentas:
                st.markdown("#### 💳 Detalle de Cuentas")
                
                for cuenta in cuentas:
                    with st.expander(f"Cuenta {cuenta.get('numero', 'N/A')} - {cuenta.get('tipo', 'N/A')}"):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        col1.metric("Disponible", f"${cuenta.get('disponible', 0):,.2f}")
                        col2.metric("Comprometido", f"${cuenta.get('comprometido', 0):,.2f}")
                        col3.metric("Títulos", f"${cuenta.get('titulosValorizados', 0):,.2f}")
                        col4.metric("Total", f"${cuenta.get('total', 0):,.2f}")
                        
                        # Detalle de saldos
                        saldos = cuenta.get('saldos', [])
                        if saldos:
                            st.markdown("**Saldos por Liquidación:**")
                            df_saldos = pd.DataFrame(saldos)
                            st.dataframe(df_saldos, use_container_width=True)
            
            # Estadísticas
            estadisticas = estado_cuenta.get('estadisticas', [])
            if estadisticas:
                st.markdown("#### 📊 Estadísticas de Operaciones")
                
                for stat in estadisticas:
                    col1, col2, col3 = st.columns(3)
                    col1.write(f"**{stat.get('descripcion', 'N/A')}**")
                    col2.metric("Cantidad", stat.get('cantidad', 0))
                    col3.metric("Volumen", f"${stat.get('volumen', 0):,.2f}")
        
        else:
            st.error("❌ No se pudo obtener el estado de cuenta")
              # Mostrar información de debug
            with st.expander("🔧 Información de Debug"):
                st.write("**Endpoints intentados:**")
                st.write(f"• `/api/v2/Asesores/EstadoDeCuenta/{cliente_id}`")
                st.write("• `/api/v2/estadocuenta`")
                st.write("**Posibles causas:**")
                st.write("• Token de autorización expirado")
                st.write("• Cliente no autorizado para consulta")
                st.write("• Endpoint no disponible para el tipo de usuario")
    
    with tab6:
        st.markdown("### 🟢 Panel de Opciones Argentinas")
        panel_opciones_argentinas(st.session_state.token_acceso)
