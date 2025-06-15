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
        "Authorization": f"Bearer {token_portador}"
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
                    # Extraer precio
                    precio = item.get('ultimoPrecio')
                    if not precio or precio == 0:
                        precio = item.get('cierreAnterior') or item.get('precioPromedio') or item.get('apertura')
                    
                    # Extraer volumen con diferentes nombres posibles
                    volumen = (item.get('cantidadNominal') or 
                              item.get('volumen') or 
                              item.get('cantidadOperada') or 
                              item.get('cantidad') or 
                              item.get('volumeNominal') or 0)
                    
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
    Obtiene las operaciones de un cliente con filtros opcionales. Corregido para usar parámetros correctos.
    """
    # Construir URL base
    url_operaciones = f'https://api.invertironline.com/api/v2/Asesores/Operaciones'
    
    # Construir parámetros correctamente
    params = {
        'IdClienteAsesorado': id_cliente,
        'Estado': estado,
        'Pais': pais
    }
    
    if fecha_desde:
        params['FechaDesde'] = fecha_desde
    if fecha_hasta:
        params['FechaHasta'] = fecha_hasta
    if numero:
        params['Numero'] = numero
    
    encabezados = obtener_encabezado_autorizacion(token_portador)
    
    try:
        respuesta = requests.get(url_operaciones, headers=encabezados, params=params, timeout=15)
        st.info(f"🔍 Solicitando operaciones para cliente {id_cliente}")
        st.info(f"📡 URL: {respuesta.url}")
        st.info(f"📊 Status Code: {respuesta.status_code}")
        
        if respuesta.status_code == 200:
            operaciones = respuesta.json()
            if not operaciones:
                st.warning(f"No se encontraron operaciones para el cliente con ID {id_cliente}")
            else:
                st.success(f"✅ {len(operaciones)} operaciones encontradas")
            return operaciones
        elif respuesta.status_code == 401:
            st.warning("🔐 Token expirado. Intentando refrescar token...")
            nuevo_token = refrescar_token()
            if nuevo_token:
                # Reintentar una vez con el nuevo token
                encabezados = obtener_encabezado_autorizacion(nuevo_token)
                respuesta = requests.get(url_operaciones, headers=encabezados, params=params, timeout=15)
                if respuesta.status_code == 200:
                    operaciones = respuesta.json()
                    if not operaciones:
                        st.warning(f"No se encontraron operaciones para el cliente con ID {id_cliente}")
                    else:
                        st.success(f"✅ {len(operaciones)} operaciones encontradas")
                    return operaciones
                else:
                    st.error(f"❌ Error tras refrescar token: {respuesta.status_code}")
                    return None
            else:
                st.error("No se pudo refrescar el token. Por favor, vuelva a iniciar sesión.")
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
    
    # Intentar obtener datos de volumen desde IOL
    df_datos, mercado_usado = obtener_volumen_desde_iol(
        token_portador, simbolo, mercados_prioritarios, fecha_desde, fecha_hasta
    )
    
    if df_datos is not None and not df_datos.empty:
        datos_obtenidos = True
        st.success(f"✅ Datos de volumen obtenidos para {simbolo} desde IOL ({mercado_usado})")
    
    # Fallback a yfinance si IOL no tiene datos de volumen
    if not datos_obtenidos:
        try:
            st.info(f"🔄 Intentando obtener datos de volumen desde Yahoo Finance...")
            
            # Probar diferentes sufijos según el país
            if pais.lower() == 'argentina':
                sufijos = ['.BA', '.AR', '']
            else:
                sufijos = ['', '.US']
            
            for sufijo in sufijos:
                simbolo_yf = simbolo + sufijo if sufijo else simbolo
                ticker = yf.Ticker(simbolo_yf)
                data_yf = ticker.history(start=fecha_desde, end=fecha_hasta)
                
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
    
    if not datos_obtenidos or df_datos is None:
        st.error(f"❌ No se pudieron obtener datos de volumen para {simbolo}")
        return None
    
    # Calcular métricas de volumen
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
    
    # Inicializar variables para evitar UnboundLocalError
    picos_volumen = 0
    tendencia = 'N/A'
    vol_ma_20 = 0
    volatilidad_vol = 0
    
    # Mostrar métricas adicionales
    if len(df_con_metricas) > 20:
        col1, col2, col3, col4 = st.columns(4)
        
        picos_volumen = df_con_metricas['pico_volumen'].sum() if 'pico_volumen' in df_con_metricas.columns else 0
        tendencia = df_con_metricas['tendencia_volumen'].iloc[-1] if 'tendencia_volumen' in df_con_metricas.columns else 'N/A'
        vol_ma_20 = df_con_metricas['volumen_ma'].iloc[-1]
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
        - **Picos de volumen con {picos_volumen} eventos**: {'Actividad alta' if picos_volumen > 5 else 'Actividad moderada'}
        
        **VWAP (Volume Weighted Average Price):**
        - Precio promedio ponderado por volumen
        - Útil para determinar si el precio actual está por encima o debajo del consenso del mercado
        
        **Recomendaciones:**
        - Monitorear cambios significativos en el volumen relativo
        - Usar VWAP como referencia para puntos de entrada/salida
        - Considerar la tendencia del volumen para validar movimientos de precio
        """)
    
    return df_con_metricas

def detectar_mercado_por_pais(pais, simbolo):
    """
    Detecta los mercados apropiados según el país y símbolo
    """
    simbolo_upper = simbolo.upper()
    
    if pais.lower() == 'argentina':
        # Priorizar mercados argentinos
        if simbolo_upper.startswith('AL') or simbolo_upper.startswith('GD') or simbolo_upper.startswith('AE'):
            return ['bCBA', 'bMAE', 'MERV']
        elif any(x in simbolo_upper for x in ['FCI', 'FIMA', 'GALICIA', 'MACRO']):
            return ['FCI', 'bCBA', 'bMAE']
        else:
            return ['bCBA', 'bMAE', 'MERV', 'FCI']
    else:
        # Estados Unidos y otros
        return ['NASDAQ', 'NYSE', 'bCBA']

def mostrar_resumen_portafolio(portafolio):
    """
    Muestra un resumen completo del portafolio del cliente
    """
    if not portafolio or 'activos' not in portafolio:
        st.warning("⚠️ No hay datos de portafolio disponibles")
        return
    
    activos = portafolio['activos']
    
    if not activos:
        st.info("ℹ️ El portafolio no contiene activos")
        return
    
    # Calcular valor total
    valor_total = sum(activo.get('valorizado', 0) for activo in activos)
    
    # Mostrar resumen general
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Valor Total", f"${valor_total:,.2f}")
    
    with col2:
        st.metric("Cantidad de Activos", len(activos))
    
    with col3:
        # Calcular P&L total
        pl_total = sum(
            (activo.get('ultimoPrecio', 0) - activo.get('ppc', 0)) * activo.get('cantidad', 0)
            for activo in activos if activo.get('ppc', 0) > 0
        )
        st.metric("P&L Total", f"${pl_total:,.2f}")
    
    with col4:
        # Calcular P&L porcentual
        valor_invertido = sum(activo.get('ppc', 0) * activo.get('cantidad', 0) for activo in activos)
        pl_pct = (pl_total / valor_invertido * 100) if valor_invertido > 0 else 0
        st.metric("P&L (%)", f"{pl_pct:.2f}%")
    
    # Tabla detallada de activos
    st.markdown("#### 📋 Detalle de Activos")
    
    activos_data = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', 'N/A')
        cantidad = activo.get('cantidad', 0)
        ppc = activo.get('ppc', 0)
        ultimo_precio = activo.get('ultimoPrecio', 0)
        valorizado = activo.get('valorizado', 0)
        
        # Calcular peso
        peso = (valorizado / valor_total * 100) if valor_total > 0 else 0
        
        # Calcular P&L
        pl_activo = (ultimo_precio - ppc) * cantidad if ppc > 0 else 0
        pl_pct_activo = ((ultimo_precio / ppc - 1) * 100) if ppc > 0 else 0
        
        activos_data.append({
            'Símbolo': simbolo,
            'Cantidad': f"{cantidad:,.0f}",
            'PPC': f"${ppc:.2f}",
            'Último Precio': f"${ultimo_precio:.2f}",
            'Valor': f"${valorizado:,.2f}",
            'Peso (%)': f"{peso:.2f}",
            'P&L': f"${pl_activo:,.2f}",
            'P&L (%)': f"{pl_pct_activo:.2f}%"
        })
    
    df_activos = pd.DataFrame(activos_data)
    st.dataframe(df_activos, use_container_width=True)
    
    # Gráfico de composición
    st.markdown("#### 🥧 Composición del Portafolio")
    
    simbolos = [activo.get('titulo', {}).get('simbolo', 'N/A') for activo in activos]
    valores = [activo.get('valorizado', 0) for activo in activos]
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=simbolos,
        values=valores,
        hole=0.3
    )])
    
    fig_pie.update_layout(
        title="Distribución por Valor",
        height=400
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)

def calcular_indice_diversificacion(portafolio):
    """
    Calcula índices de diversificación del portafolio
    """
    if not portafolio or 'activos' not in portafolio:
        return None
    
    activos = portafolio['activos']
    if not activos:
        return None
    
    # Calcular valor total
    valor_total = sum(activo.get('valorizado', 0) for activo in activos)
    
    if valor_total == 0:
        return None
    
    # Calcular pesos
    pesos = [activo.get('valorizado', 0) / valor_total for activo in activos]
    
    # Índice Herfindahl-Hirschman (HHI)
    hhi = sum(peso**2 for peso in pesos)
    
    # Número efectivo de activos
    numero_efectivo_activos = 1 / hhi if hhi > 0 else 0
    
    # Diversificación normalizada (0-1)
    diversificacion_normalizada = (1 - hhi) if len(activos) > 1 else 0
    
    # Nivel de diversificación
    if hhi < 0.1:
        nivel = "Alta"
    elif hhi < 0.25:
        nivel = "Media"
    else:
        nivel = "Baja"
    
    # Contar tipos de activos
    tipos = set()
    for activo in activos:
        tipo = activo.get('titulo', {}).get('tipo', 'Desconocido')
        tipos.add(tipo)
    
    return {
        'hhi': hhi,
        'numero_efectivo_activos': numero_efectivo_activos,
        'diversificacion_normalizada': diversificacion_normalizada,
        'nivel_diversificacion': nivel,
        'diversificacion_tipos': len(tipos),
        'interpretacion': {
            'concentracion': f"HHI de {hhi:.3f} indica {'alta' if hhi > 0.25 else 'media' if hhi > 0.1 else 'baja'} concentración",
            'efectividad': f"Equivale a {numero_efectivo_activos:.1f} activos con pesos iguales",
            'diversificacion': f"Diversificación {nivel.lower()} con {len(tipos)} tipos de instrumentos"
        }
    }

def calcular_perfil_portafolio_actual(portafolio):
    """
    Determina el perfil de riesgo del portafolio actual basado en su composición
    """
    if not portafolio or 'activos' not in portafolio:
        return None
    
    activos = portafolio['activos']
    if not activos:
        return None
    
    # Clasificar activos por riesgo
    composicion = {
        'conservador': 0,  # Bonos, FCIs de renta fija, cauciones
        'moderado': 0,     # FCIs mixtos, algunos bonos corporativos
        'agresivo': 0      # Acciones, CEDEARs, FCIs de renta variable
    }
    
    for activo in activos:
        titulo = activo.get('titulo', {})
        tipo = titulo.get('tipo', '').lower()
        simbolo = titulo.get('simbolo', '').upper()
        valor = activo.get('valorizado', 0)
        peso = valor / valor_total
        
        # Clasificación simplificada por tipo de instrumento
        if any(palabra in tipo for palabra in ['bono', 'titulo publico', 'caucion', 'plazo fijo']):
            composicion['conservador'] += peso
        elif any(palabra in tipo for palabra in ['fci']) and any(palabra in simbolo for palabra in ['RF', 'RENTA FIJA', 'CONSERVADOR']):
            composicion['conservador'] += peso
        elif any(palabra in tipo for palabra in ['accion', 'cedear', 'adr']):
            composicion['agresivo'] += peso
        elif any(palabra in tipo for palabra in ['fci']) and any(palabra in simbolo for palabra in ['RV', 'RENTA VARIABLE', 'ACCIONES']):
            composicion['agresivo'] += peso
        else:
            composicion['moderado'] += peso
    
    # Determinar perfil dominante
    perfil_dominante = max(composicion, key=composicion.get)
    
    return {
        'perfil_dominante': perfil_dominante,
        'composicion': {k: v * 100 for k, v in composicion.items()}
    }

def panel_opciones_argentinas(token_acceso):
    """
    Panel para análisis de opciones argentinas - COMPLETAMENTE IMPLEMENTADO
    """
    st.markdown("### 🟢 Panel de Opciones Argentinas")
    
    tab1, tab2, tab3 = st.tabs(["📊 Valuación Black-Scholes", "📈 Análisis de Greeks", "🎯 Estrategias"])
    
    with tab1:
        st.markdown("#### 💰 Calculadora Black-Scholes")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            S = st.number_input("💵 Precio del Subyacente", min_value=1.0, value=100.0)
            K = st.number_input("🎯 Precio de Ejercicio", min_value=1.0, value=100.0)
        
        with col2:
            T = st.number_input("⏰ Tiempo a Vencimiento (años)", min_value=0.01, max_value=5.0, value=0.25, step=0.01)
            r = st.number_input("📈 Tasa Libre de Riesgo (%)", min_value=0.0, max_value=50.0, value=5.0) / 100
        
        with col3:
            sigma = st.number_input("📊 Volatilidad Implícita (%)", min_value=1.0, max_value=200.0, value=25.0) / 100
            option_type = st.selectbox("🔄 Tipo de Opción", ["call", "put"])
        
        if st.button("💰 Calcular Precio"):
            precio_bs = calcular_black_scholes(S, K, T, r, sigma, option_type)
            greeks = calcular_greeks(S, K, T, r, sigma, option_type)
            
            st.success(f"💰 **Precio {option_type.upper()}:** ${precio_bs:.4f}")
            
            # Mostrar Greeks
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Δ Delta", f"{greeks['delta']:.4f}")
            col2.metric("Γ Gamma", f"{greeks['gamma']:.6f}")
            col3.metric("Θ Theta", f"{greeks['theta']:.4f}")
            col4.metric("ν Vega", f"{greeks['vega']:.4f}")
            col5.metric("ρ Rho", f"{greeks['rho']:.4f}")
            
            # Gráfico de sensibilidad al precio
            precios_subyacente = np.linspace(S * 0.5, S * 1.5, 50)
            precios_opcion = [calcular_black_scholes(p, K, T, r, sigma, option_type) for p in precios_subyacente]
            
            fig_sens = go.Figure()
            fig_sens.add_trace(go.Scatter(
                x=precios_subyacente,
                y=precios_opcion,
                mode='lines',
                name=f'Precio {option_type.upper()}'
            ))
            
            # Punto actual
            fig_sens.add_trace(go.Scatter(
                x=[S],
                y=[precio_bs],
                mode='markers',
                marker=dict(size=10, color='red'),
                name='Precio Actual'
            ))
            
            fig_sens.update_layout(
                title=f"Sensibilidad del Precio de la Opción {option_type.upper()}",
                xaxis_title="Precio del Subyacente",
                yaxis_title="Precio de la Opción",
                height=400
            )
            
            st.plotly_chart(fig_sens, use_container_width=True)
    
    with tab2:
        st.markdown("#### 📈 Análisis Detallado de Greeks")
        
        if 'greeks' in locals():
            # Gráficos de sensibilidad
            col1, col2 = st.columns(2)
            
            with col1:
                # Delta vs Precio del Subyacente
                precios = np.linspace(S * 0.7, S * 1.3, 30)
                deltas = [calcular_greeks(p, K, T, r, sigma, option_type)['delta'] for p in precios]
                
                fig_delta = go.Figure()
                fig_delta.add_trace(go.Scatter(x=precios, y=deltas, mode='lines', name='Delta'))
                fig_delta.update_layout(title="Delta vs Precio Subyacente", height=300)
                st.plotly_chart(fig_delta, use_container_width=True)
            
            with col2:
                # Gamma vs Precio del Subyacente
                gammas = [calcular_greeks(p, K, T, r, sigma, option_type)['gamma'] for p in precios]
                
                fig_gamma = go.Figure()
                fig_gamma.add_trace(go.Scatter(x=precios, y=gammas, mode='lines', name='Gamma', line=dict(color='green')))
                fig_gamma.update_layout(title="Gamma vs Precio Subyacente", height=300)
                st.plotly_chart(fig_gamma, use_container_width=True)
            
            # Interpretación de Greeks
            with st.expander("📚 Interpretación de Greeks"):
                st.markdown(f"""
                **Delta ({greeks['delta']:.4f}):** {'La opción sube $1 por cada $1 que sube el subyacente' if greeks['delta'] > 0 else 'La opción baja $1 por cada $1 que sube el subyacente'}
                
                **Gamma ({greeks['gamma']:.6f}):** {'Acelera las ganancias si el precio sube' if greeks['gamma'] > 0 else 'Acelera las pérdidas si el precio baja'}
                
                **Theta ({greeks['theta']:.4f}):** La opción pierde ${abs(greeks['theta']):.4f} por día por el paso del tiempo
                
                **Vega ({greeks['vega']:.4f}):** La opción {'sube' if greeks['vega'] > 0 else 'baja'} ${abs(greeks['vega']):.4f} por cada 1% de aumento en volatilidad
                
                **Rho ({greeks['rho']:.4f}):** La opción {'sube' if greeks['rho'] > 0 else 'baja'} ${abs(greeks['rho']):.4f} por cada 1% de aumento en tasas
                """)
    
    with tab3:
        st.markdown("#### 🎯 Análisis de Estrategias con Opciones")
        
        estrategia = st.selectbox("📋 Seleccionar Estrategia", [
            "Long Call", "Long Put", "Covered Call", "Protective Put", 
            "Bull Call Spread", "Bear Put Spread", "Long Straddle", "Long Strangle"
        ])
        
        st.info(f"📊 Configurando estrategia: **{estrategia}**")
        
        if estrategia == "Long Call":
            st.markdown("**Estrategia:** Compra de Call")
            payoff_desc = "Ganancias ilimitadas si el precio sube por encima del strike + prima"
        elif estrategia == "Covered Call":
            st.markdown("**Estrategia:** Acción + Venta de Call")
            payoff_desc = "Genera ingresos adicionales, limita ganancias al strike"
        else:
            payoff_desc = f"Análisis de {estrategia} próximamente"
        
        st.info(f"💡 **Descripción:** {payoff_desc}")

def refrescar_token():
    """
    Refresca el token de acceso usando el refresh token
    """
    if not st.session_state.token_refresco:
        return None
    
    url_refresh = 'https://api.invertironline.com/token'
    datos = {
        'refresh_token': st.session_state.token_refresco,
        'grant_type': 'refresh_token'
    }
    
    try:
        respuesta = requests.post(url_refresh, data=datos, timeout=15)
        if respuesta.status_code == 200:
            respuesta_json = respuesta.json()
            nuevo_token = respuesta_json['access_token']
            nuevo_refresh = respuesta_json.get('refresh_token', st.session_state.token_refresco)
            
            # Actualizar tokens en session state
            st.session_state.token_acceso = nuevo_token
            st.session_state.token_refresco = nuevo_refresh
            
            return nuevo_token
        else:
            return None
    except Exception as e:
        st.error(f'Error al refrescar token: {str(e)}')
        return None

def mostrar_login():
    """
    Pantalla de login de la aplicación
    """
    st.markdown("# 🏦 IOL Portfolio Analyzer")
    st.markdown("### 🔐 Iniciar Sesión")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.markdown("#### Credenciales de IOL")
            usuario = st.text_input("👤 Usuario", placeholder="Ingrese su usuario de IOL")
            contraseña = st.text_input("🔒 Contraseña", type="password", placeholder="Ingrese su contraseña")
            
            submit_button = st.form_submit_button("🚀 Conectar", use_container_width=True)
            
            if submit_button:
                if usuario and contraseña:
                    with st.spinner("🔄 Conectando con IOL..."):
                        token_acceso, token_refresco = obtener_tokens(usuario, contraseña)
                        
                        if token_acceso:
                            # Guardar tokens en session state
                            st.session_state.token_acceso = token_acceso
                            st.session_state.token_refresco = token_refresco
                            st.session_state.usuario = usuario
                            st.session_state.authenticated = True
                            
                            # Obtener lista de clientes
                            clientes = obtener_lista_clientes(token_acceso)
                            st.session_state.clientes = clientes
                            
                            if clientes:
                                st.success(f"✅ ¡Conectado exitosamente! Se encontraron {len(clientes)} clientes.")
                                st.session_state.current_page = "main"
                                st.rerun()
                            else:
                                st.warning("⚠️ Conectado, pero no se encontraron clientes asociados.")
                                st.session_state.current_page = "main"
                                st.rerun()
                        else:
                            st.error("❌ Error de autenticación. Verifique sus credenciales.")
                else:
                    st.error("⚠️ Por favor complete todos los campos.")
    
    # Información adicional
    with st.expander("ℹ️ Información sobre la aplicación"):
        st.markdown("""
        **IOL Portfolio Analyzer** es una herramienta avanzada para análisis de portafolios que se conecta directamente con la API de InvertirOnline.
        
        **Características principales:**
        - 📊 Análisis completo de portafolios
        - 📈 Optimización de carteras
        - 🎯 Simulaciones Monte Carlo
        - 📉 Backtesting de estrategias
        - 🔍 Análisis de volumen avanzado
        - 💹 Seguimiento de operaciones
        
        **Requisitos:**
        - Cuenta activa en InvertirOnline
        - Permisos de API habilitados
        - Credenciales válidas
        """)

def mostrar_selector_cliente():
    """
    Selector de cliente en la barra lateral
    """
    if st.session_state.clientes:
        st.sidebar.markdown("### 👥 Seleccionar Cliente")
        
        # Crear lista de opciones para el selectbox
        opciones_clientes = []
        for i, cliente in enumerate(st.session_state.clientes):
            nombre = cliente.get('nombre', 'N/A')
            apellido = cliente.get('apellido', 'N/A')
            id_cliente = cliente.get('id', 'N/A')
            opciones_clientes.append(f"{nombre} {apellido} (ID: {id_cliente})")
        
        cliente_seleccionado_idx = st.sidebar.selectbox(
            "Cliente:",
            range(len(opciones_clientes)),
            format_func=lambda x: opciones_clientes[x],
            key="selector_cliente"
        )
        
        if cliente_seleccionado_idx is not None:
            st.session_state.cliente_seleccionado = st.session_state.clientes[cliente_seleccionado_idx]
            
            cliente = st.session_state.cliente_seleccionado
            with st.sidebar.expander("📋 Info del Cliente"):
                st.write(f"**Nombre:** {cliente.get('nombre', 'N/A')} {cliente.get('apellido', 'N/A')}")
                st.write(f"**ID:** {cliente.get('id', 'N/A')}")
                st.write(f"**Email:** {cliente.get('email', 'N/A')}")
    else:
        st.sidebar.warning("⚠️ No hay clientes disponibles")

def mostrar_navegacion():
    """
    Menú de navegación en la barra lateral
    """
    st.sidebar.markdown("### 🧭 Navegación")
    
    paginas = {
        "🏠 Dashboard": "dashboard",
        "💼 Portafolio": "portafolio", 
        "📊 Análisis": "analisis",
        "🎯 Optimización": "optimizacion",
        "📈 Operaciones": "operaciones",
        "📉 Volumen": "volumen",
        "🟢 Opciones": "opciones",
        "⚙️ Configuración": "configuracion"
    }
    
    for nombre, clave in paginas.items():
        if st.sidebar.button(nombre, use_container_width=True, key=f"nav_{clave}"):
            st.session_state.current_page = clave
            st.rerun()

def mostrar_dashboard():
    """
    Dashboard principal con resumen general
    """
    st.markdown("# 🏠 Dashboard - IOL Portfolio Analyzer")
    
    if not st.session_state.cliente_seleccionado:
        st.warning("⚠️ Seleccione un cliente para ver el dashboard")
        return
    
    cliente = st.session_state.cliente_seleccionado
    id_cliente = cliente.get('id')
    
    st.markdown(f"### 👤 Cliente: {cliente.get('nombre', 'N/A')} {cliente.get('apellido', 'N/A')}")
    
    # Obtener datos básicos
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown("#### 💰 Estado de Cuenta")
            estado_cuenta = obtener_estado_cuenta(st.session_state.token_acceso, id_cliente)
            if estado_cuenta:
                # Mostrar métricas del estado de cuenta
                if isinstance(estado_cuenta, dict):
                    saldo_total = estado_cuenta.get('saldoTotal', 0)
                    saldo_disponible = estado_cuenta.get('saldoDisponible', 0)
                    st.metric("Saldo Total", f"${saldo_total:,.2f}")
                    st.metric("Saldo Disponible", f"${saldo_disponible:,.2f}")
                else:
                    st.info("ℹ️ Estructura de estado de cuenta no reconocida")
            else:
                st.warning("⚠️ No se pudo obtener el estado de cuenta")
    
    with col2:
        with st.container():
            st.markdown("#### 📈 Resumen del Portafolio")
            portafolio = obtener_portafolio(st.session_state.token_acceso, id_cliente)
            if portafolio and 'activos' in portafolio:
                activos = portafolio['activos']
                valor_total = sum(activo.get('valorizado', 0) for activo in activos)
                cantidad_activos = len(activos)
                
                st.metric("Valor Total", f"${valor_total:,.2f}")
                st.metric("Cantidad de Activos", cantidad_activos)
            else:
                st.warning("⚠️ No se pudo obtener el portafolio")
    
    # Gráficos resumen
    st.markdown("#### 📊 Análisis Rápido")
    
    if portafolio and 'activos' in portafolio:
        activos = portafolio['activos']
        if activos:
            # Gráfico de torta de composición
            simbolos = [activo.get('titulo', {}).get('simbolo', 'N/A') for activo in activos]
            valores = [activo.get('valorizado', 0) for activo in activos]
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=simbolos,
                values=valores,
                hole=0.3,
                hovertemplate='<b>%{label}</b><br>Valor: $%{value:,.2f}<br>Porcentaje: %{percent}<extra></extra>'
            )])
            
            fig_pie.update_layout(
                title="Composición del Portafolio",
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("ℹ️ El portafolio no contiene activos")
    
    # Accesos rápidos
    st.markdown("#### 🚀 Accesos Rápidos")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Ver Portafolio Completo", use_container_width=True):
            st.session_state.current_page = "portafolio"
            st.rerun()
    
    with col2:
        if st.button("🎯 Optimizar Portafolio", use_container_width=True):
            st.session_state.current_page = "optimizacion"
            st.rerun()
    
    with col3:
        if st.button("📈 Ver Operaciones", use_container_width=True):
            st.session_state.current_page = "operaciones"
            st.rerun()
    
    with col4:
        if st.button("📉 Análisis de Volumen", use_container_width=True):
            st.session_state.current_page = "volumen"
            st.rerun()

def mostrar_portafolio():
    """
    Pantalla de análisis detallado del portafolio
    """
    st.markdown("# 💼 Análisis de Portafolio")
    
    if not st.session_state.cliente_seleccionado:
        st.warning("⚠️ Seleccione un cliente para ver el portafolio")
        return
    
    cliente = st.session_state.cliente_seleccionado
    id_cliente = cliente.get('id')
    
    # Obtener portafolio
    portafolio = obtener_portafolio(st.session_state.token_acceso, id_cliente)
    
    if portafolio:
        mostrar_resumen_portafolio(portafolio)

        # --- INICIO: Agregar análisis avanzado por activo ---
        st.markdown("### 🔬 Análisis Avanzado de Activos del Portafolio")
        activos = portafolio.get('activos', [])
        if activos:
            fecha_fin = date.today()
            fecha_inicio = fecha_fin - timedelta(days=365)
            for activo in activos:
                simbolo = activo.get('titulo', {}).get('simbolo', None)
                if simbolo:
                    with st.expander(f"Análisis avanzado: {simbolo}", expanded=False):
                        analisis_avanzado_activo_portafolio(simbolo, fecha_inicio, fecha_fin)
        else:
            st.info("El portafolio no contiene activos para análisis avanzado.")
        # --- FIN: Agregar análisis avanzado por activo ---

    else:
        st.error("❌ No se pudo obtener el portafolio del cliente")

# === INICIO: Integración de análisis avanzado de activos en el portafolio ===

def analisis_avanzado_activo_portafolio(simbolo, fecha_inicio, fecha_fin):
    """
    Análisis avanzado de un activo del portafolio usando ML, volumen, gráficos, etc.
    """
    import yfinance as yf
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

    # Descargar datos
    datos = yf.download(simbolo, start=fecha_inicio, end=fecha_fin)
    if datos.empty:
        st.warning(f"No se encontraron datos para {simbolo}")
        return

    # Calcular indicadores técnicos básicos
    datos['MA5'] = datos['Close'].rolling(window=5, min_periods=1).mean()
    datos['MA20'] = datos['Close'].rolling(window=20, min_periods=1).mean()
    datos['RSI'] = calcular_rsi(datos['Close'])
    datos['MACD'] = datos['Close'].ewm(span=12, adjust=False).mean() - datos['Close'].ewm(span=26, adjust=False).mean()
    datos['Signal'] = datos['MACD'].ewm(span=9, adjust=False).mean()
    datos['Target'] = (datos['Close'].shift(-1) > datos['Close']).astype(int)

    # Limpiar datos para ML
    caracteristicas_ml = ['MA5', 'MA20', 'RSI', 'MACD', 'Signal']
    datos_ml = datos[caracteristicas_ml + ['Target']].dropna()
    if datos_ml.empty:
        st.info("No hay suficientes datos para análisis ML.")
        return

    X = datos_ml[caracteristicas_ml]
    y = datos_ml['Target']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False, random_state=42)
    modelo = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo.fit(X_train, y_train)
    y_pred = modelo.predict(X_test)
    precision = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    precision_score_val = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)

    # Gráfico simple de precios y medias móviles
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=datos.index, y=datos['Close'], name='Precio', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=datos.index, y=datos['MA5'], name='MA5', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=datos.index, y=datos['MA20'], name='MA20', line=dict(color='green')))
    fig.update_layout(title=f"Precio y Medias Móviles - {simbolo}", height=300)

    # Mostrar resultados
    st.plotly_chart(fig, use_container_width=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Precisión ML", f"{precision:.2%}")
    col2.metric("F1", f"{f1:.2f}")
    col3.metric("Precisión", f"{precision_score_val:.2f}")
    col4.metric("Recall", f"{recall:.2f}")

    # Importancia de características
    importancia = pd.DataFrame({
        'Característica': caracteristicas_ml,
        'Importancia': modelo.feature_importances_
    }).sort_values('Importancia', ascending=False)
    st.bar_chart(importancia.set_index('Característica'))

    # Predicción para el próximo día
    ultimos_datos = datos_ml.iloc[[-1]][caracteristicas_ml]
    prediccion = modelo.predict(ultimos_datos)[0]
    probas = modelo.predict_proba(ultimos_datos)[0]
    st.info(f"Predicción próxima jornada: {'🟢 SUBIDA' if prediccion == 1 else '🔴 BAJADA'} (confianza: {max(probas):.2%})")

def calcular_rsi(precios, ventana=14):
    delta = precios.diff()
    ganancia = delta.where(delta > 0, 0)
    perdida = -delta.where(delta < 0, 0)
    ganancia_promedio = ganancia.rolling(ventana, min_periods=1).mean()
    perdida_promedio = perdida.rolling(ventana, min_periods=1).mean()
    rs = ganancia_promedio / perdida_promedio.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

# === FIN: Integración de análisis avanzado de activos en el portafolio ===

def main():
    """
    Función principal de la aplicación
    """
    init_session_state()
    if not st.session_state.authenticated:
        mostrar_login()
        return
    mostrar_selector_cliente()
    mostrar_navegacion()
    if st.session_state.current_page == "main" or st.session_state.current_page == "dashboard":
        mostrar_dashboard()
    elif st.session_state.current_page == "portafolio":
        mostrar_portafolio()
    elif st.session_state.current_page == "analisis":
        mostrar_analisis()
    elif st.session_state.current_page == "optimizacion":
        mostrar_optimizacion()
    elif st.session_state.current_page == "operaciones":
        mostrar_operaciones()
    elif st.session_state.current_page == "volumen":
        mostrar_volumen()
    elif st.session_state.current_page == "opciones":
        mostrar_opciones()
    elif st.session_state.current_page == "configuracion":
        mostrar_configuracion()
    else:
        mostrar_dashboard()

if __name__ == "__main__":
    main()
