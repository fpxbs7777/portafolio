import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
from datetime import date, timedelta, datetime
import numpy as np
import yfinance as yf
import scipy.optimize as op
from scipy import stats # Added for skewness, kurtosis, jarque_bera
import random
import warnings
import streamlit.components.v1 as components

warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="IOL Portfolio Analyzer",
    page_icon="📊",
    layout="wide"
)

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
        respuesta = requests.post(url_login, data=datos, timeout=15) # Added timeout
        respuesta.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
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
    except requests.exceptions.ConnectionError as conn_err:
        st.error(f'Error de conexión al intentar obtener tokens: {conn_err}')
        st.warning("No se pudo conectar al servidor de IOL. Verifique su conexión a internet y que el servicio de IOL esté disponible.")
        return None, None
    except requests.exceptions.Timeout as timeout_err:
        st.error(f'Timeout al intentar obtener tokens: {timeout_err}')
        st.warning("La solicitud a IOL tardó demasiado en responder. Intente más tarde.")
        return None, None
    except requests.exceptions.RequestException as req_err: # Catch any other requests error
        st.error(f'Error en la solicitud al obtener tokens: {req_err}')
        return None, None
    except Exception as e: # General fallback
        st.error(f'Error inesperado al obtener tokens: {str(e)}')
        return None, None

def obtener_lista_clientes(token_portador):
    url_clientes = 'https://api.invertironline.com/api/v2/Asesores/Clientes'
    encabezados = obtener_encabezado_autorizacion(token_portador)
    try:
        respuesta = requests.get(url_clientes, headers=encabezados)
        if respuesta.status_code == 200:
            clientes_data = respuesta.json()
            # Debug: mostrar estructura de respuesta
            st.info(f"📋 Estructura de respuesta de clientes: {type(clientes_data)}")
            if isinstance(clientes_data, list):
                return clientes_data
            elif isinstance(clientes_data, dict) and 'clientes' in clientes_data:
                return clientes_data['clientes']
            else:
                st.warning(f"Estructura de datos inesperada: {clientes_data}")
                return []
        else:
            st.error(f'Error al obtener la lista de clientes: {respuesta.status_code}')
            st.error(f'Respuesta: {respuesta.text}')
            return []
    except Exception as e:
        st.error(f'Error de conexión al obtener clientes: {str(e)}')
        return []

def obtener_estado_cuenta(token_portador, id_cliente=None):
    """
    Obtiene el estado de cuenta del usuario autenticado o cliente específico
    """
    # Usar endpoint directo para usuario autenticado o endpoint de asesor para cliente específico
    if id_cliente:
        url_estado_cuenta = f'https://api.invertironline.com/api/v2/Asesores/EstadoDeCuenta/{id_cliente}'
    else:
        url_estado_cuenta = 'https://api.invertironline.com/api/v2/estadocuenta'
    
    encabezados = obtener_encabezado_autorizacion(token_portador)
    try:
        respuesta = requests.get(url_estado_cuenta, headers=encabezados)
        st.info(f"💰 Solicitando estado de cuenta - URL: {url_estado_cuenta}")
        st.info(f"📊 Status Code: {respuesta.status_code}")
        
        if respuesta.status_code == 200:
            estado_data = respuesta.json()
            st.success(f"✅ Estado de cuenta obtenido exitosamente")
            return estado_data
        elif respuesta.status_code == 401:
            st.warning(f"🔐 No autorizado - Token inválido o permisos insuficientes")
            if id_cliente:
                st.info("💡 Intentando con endpoint directo sin ID de cliente...")
                # Intentar con endpoint directo
                return obtener_estado_cuenta(token_portador, None)
            return None
        elif respuesta.status_code == 404:
            st.warning(f"⚠️ Estado de cuenta no encontrado")
            return None
        else:
            st.error(f'❌ Error al obtener estado de cuenta: {respuesta.status_code}')
            st.error(f'📄 Respuesta: {respuesta.text}')
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

def obtener_datos_alternativos_yfinance(simbolo, fecha_desde, fecha_hasta):
    """
    Fallback usando yfinance para símbolos que no estén disponibles en IOL
    """
    try:
        # Mapear símbolos argentinos a Yahoo Finance si es posible
        simbolo_yf = simbolo
        
        # Agregar sufijos comunes para acciones argentinas
        sufijos_ar = ['.BA', '.AR']
        
        for sufijo in sufijos_ar:
            try:
                ticker = yf.Ticker(simbolo + sufijo)
                data = ticker.history(start=fecha_desde, end=fecha_hasta)
                if not data.empty and len(data) > 10:
                    # Usar precio de cierre
                    return data['Close']
            except:
                continue
        
        # Intentar sin sufijo
        try:
            ticker = yf.Ticker(simbolo)
            data = ticker.history(start=fecha_desde, end=fecha_hasta)
            if not data.empty and len(data) > 10:
                return data['Close']
        except:
            pass
            
        return None
    except Exception:
        return None

def get_historical_data_for_optimization(token_portador, simbolos, fecha_desde, fecha_hasta):
    """
    Obtiene datos históricos para optimización de portafolio con manejo mejorado de errores.
    Actualizada para mejor compatibilidad con la API de IOL.
    """
    try:
        df_precios = pd.DataFrame()
        simbolos_exitosos = []
        simbolos_fallidos = []
        detalles_errores = {}
        
        # Convertir fechas a string en formato correcto
        fecha_desde_str = fecha_desde.strftime('%Y-%m-%d')
        fecha_hasta_str = fecha_hasta.strftime('%Y-%m-%d')
        
        st.info(f"🔍 Buscando datos históricos desde {fecha_desde_str} hasta {fecha_hasta_str}")
        
        # Crear barra de progreso
        progress_bar = st.progress(0)
        total_simbolos = len(simbolos)
        
        for idx, simbolo in enumerate(simbolos):
            # Actualizar barra de progreso
            progress_bar.progress((idx + 1) / total_simbolos, text=f"Procesando {simbolo}...")
            
            # Usar mercados correctos según la API de IOL (sin 'Merval')
            mercados = ['bCBA', 'nYSE', 'nASDAQ', 'rOFEX', 'Opciones', 'FCI']
            serie_obtenida = False
            
            for mercado in mercados:
                try:
                    # Buscar clase D si es posible (solo para mercados tradicionales)
                    simbolo_consulta = simbolo
                    if mercado not in ['Opciones', 'FCI']:
                        clase_d = obtener_clase_d(simbolo, mercado, token_portador)
                        if clase_d:
                            simbolo_consulta = clase_d
                    
                    serie = obtener_serie_historica_iol(
                        token_portador, mercado, simbolo_consulta, 
                        fecha_desde_str, fecha_hasta_str
                    )
                    
                    if serie is not None and len(serie) > 10:
                        # Verificar que los datos no sean todos iguales
                        if serie.nunique() > 1:
                            df_precios[simbolo_consulta] = serie
                            simbolos_exitosos.append(simbolo_consulta)
                            serie_obtenida = True
                            
                            # Mostrar información del símbolo exitoso
                            st.success(f"✅ {simbolo_consulta} ({mercado}): {len(serie)} puntos de datos")
                            break
                        
                except Exception as e:
                    detalles_errores[f"{simbolo}_{mercado}"] = str(e)
                    continue
            
            # Si IOL falló completamente, intentar con yfinance como fallback
            if not serie_obtenida:
                try:
                    serie_yf = obtener_datos_alternativos_yfinance(
                        simbolo, fecha_desde, fecha_hasta
                    )
                    if serie_yf is not None and len(serie_yf) > 10:
                        if serie_yf.nunique() > 1:
                            df_precios[simbolo] = serie_yf
                            simbolos_exitosos.append(simbolo)
                            serie_obtenida = True
                            st.info(f"ℹ️ {simbolo} (Yahoo Finance): {len(serie_yf)} puntos de datos")
                except Exception as e:
                    detalles_errores[f"{simbolo}_yfinance"] = str(e)
            
            if not serie_obtenida:
                simbolos_fallidos.append(simbolo)
                st.warning(f"⚠️ No se pudieron obtener datos para {simbolo}")
        
        # Limpiar barra de progreso
        progress_bar.empty()
        
        # Informar resultados detallados
        if simbolos_exitosos:
            st.success(f"✅ Datos obtenidos para {len(simbolos_exitosos)} activos")
            with st.expander("📋 Ver activos exitosos"):
                for simbolo in simbolos_exitosos:
                    if simbolo in df_precios.columns:
                        datos_info = f"{simbolo}: {len(df_precios[simbolo])} puntos, rango: {df_precios[simbolo].min():.2f} - {df_precios[simbolo].max():.2f}"
                        st.text(datos_info)
        
        if simbolos_fallidos:
            st.warning(f"⚠️ No se pudieron obtener datos para {len(simbolos_fallidos)} activos")
            with st.expander("❌ Ver activos fallidos y errores"):
                for simbolo in simbolos_fallidos:
                    st.text(f"• {simbolo}")
                
                if detalles_errores:
                    st.markdown("**Detalles de errores:**")
                    for key, error in detalles_errores.items():
                        st.text(f"{key}: {error}")
        
        # Continuar si tenemos al menos 2 activos
        if len(simbolos_exitosos) < 2:
            if len(simbolos_exitosos) == 1:
                st.error("❌ Se necesitan al menos 2 activos con datos históricos válidos para el análisis.")
            else:
                st.error("❌ No se pudieron obtener datos históricos para ningún activo.")
            
            # Mostrar sugerencias
            st.markdown("#### 💡 Sugerencias para resolver el problema:")
            st.markdown("""
            1. **Verificar conectividad**: Asegúrese de que su conexión a IOL esté activa
            2. **Revisar símbolos**: Algunos símbolos pueden haber cambiado o no estar disponibles
            3. **Ajustar fechas**: Pruebe con un rango de fechas más amplio o diferente
            4. **Verificar permisos**: Asegúrese de tener permisos para acceder a datos históricos
            """)
            
            return None, None, None
        
        if len(simbolos_exitosos) < len(simbolos):
            st.info(f"ℹ️ Continuando análisis con {len(simbolos_exitosos)} de {len(simbolos)} activos disponibles.")
        
        # Alinear datos por fechas comunes con mejor manejo
        st.info(f"📊 Alineando datos de {len(df_precios.columns)} activos...")
        
        # Verificar que tenemos datos válidos antes de alinear
        if df_precios.empty:
            st.error("❌ DataFrame de precios está vacío")
            return None, None, None
        
        # Mostrar información de debug sobre las fechas
        with st.expander("🔍 Debug - Información de fechas"):
            for col in df_precios.columns:
                serie = df_precios[col]
                st.text(f"{col}: {len(serie)} puntos, desde {serie.index.min()} hasta {serie.index.max()}")
        
        # Intentar diferentes estrategias de alineación
        try:
            # Estrategia 1: Forward fill y luego backward fill
            df_precios_filled = df_precios.fillna(method='ffill').fillna(method='bfill')
            
            # Estrategia 2: Interpolar valores faltantes
            df_precios_interpolated = df_precios.interpolate(method='time')
            
            # Usar la estrategia que conserve más datos
            if not df_precios_filled.dropna().empty:
                df_precios = df_precios_filled.dropna()
                st.info("✅ Usando estrategia forward/backward fill")
            elif not df_precios_interpolated.dropna().empty:
                df_precios = df_precios_interpolated.dropna()
                st.info("✅ Usando estrategia de interpolación")
            else:
                # Estrategia 3: Usar solo fechas con datos completos
                df_precios = df_precios.dropna()
                st.info("✅ Usando solo fechas con datos completos")
                
        except Exception as e:
            st.warning(f"⚠️ Error en alineación de datos: {str(e)}. Usando datos sin procesar.")
            df_precios = df_precios.dropna()
        
        if df_precios.empty:
            st.error("❌ No hay fechas comunes entre los activos después del procesamiento")
            return None, None, None
        
        st.success(f"✅ Datos alineados: {len(df_precios)} observaciones para {len(df_precios.columns)} activos")
        
        # Calcular retornos
        returns = df_precios.pct_change().dropna()
        
        if returns.empty or len(returns) < 30:
            st.error("❌ No hay suficientes datos para calcular retornos válidos (mínimo 30 observaciones)")
            return None, None, None
        
        # Verificar que los retornos no sean constantes
        if (returns.std() == 0).any():
            columnas_constantes = returns.columns[returns.std() == 0].tolist()
            st.warning(f"⚠️ Removiendo activos con retornos constantes: {columnas_constantes}")
            returns = returns.drop(columns=columnas_constantes)
            df_precios = df_precios.drop(columns=columnas_constantes)
        
        if len(returns.columns) < 2:
            st.error("❌ Después de filtrar, no quedan suficientes activos para análisis")
            return None, None, None
        
        # Calcular métricas finales
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        
        # Mostrar estadísticas finales
        st.info(f"📊 Datos finales: {len(returns.columns)} activos, {len(returns)} observaciones de retornos")
        
        return mean_returns, cov_matrix, df_precios
        
    except Exception as e:
        st.error(f"❌ Error crítico obteniendo datos históricos: {str(e)}")
        with st.expander("🔍 Información de debug"):
            st.code(f"Error: {str(e)}")
            st.code(f"Símbolos: {simbolos}")
            st.code(f"Rango de fechas: {fecha_desde} a {fecha_hasta}")
        return None, None, None

def obtener_serie_historica(simbolo, mercado, fecha_desde, fecha_hasta, ajustada, bearer_token):
    """
    Obtiene la serie histórica de precios para un símbolo y mercado específico.
    Actualizada para usar nombres correctos de mercados IOL.
    """
    # Mapear nombres de mercados a los correctos de IOL
    mercados_mapping = {
        'BCBA': 'bCBA',
        'NYSE': 'nYSE', 
        'NASDAQ': 'nASDAQ',
        'ROFEX': 'rOFEX',
        'Merval': 'bCBA'  # Merval no existe, usar bCBA
    }
    
    mercado_correcto = mercados_mapping.get(mercado, mercado)
    
    url = f"https://api.invertironline.com/api/v2/{mercado_correcto}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None

def obtener_clase_d(simbolo, mercado, bearer_token):
    """
    Busca automáticamente la clase 'D' de un bono dado su símbolo y mercado.
    Devuelve el símbolo de la clase 'D' si existe, si no, devuelve None.
    """
    # Mapear nombres de mercados a los correctos de IOL
    mercados_mapping = {
        'BCBA': 'bCBA',
        'NYSE': 'nYSE', 
        'NASDAQ': 'nASDAQ',
        'ROFEX': 'rOFEX',
        'Merval': 'bCBA'  # Merval no existe, usar bCBA
    }
    
    mercado_correcto = mercados_mapping.get(mercado, mercado)
    
    url = f"https://api.invertironline.com/api/v2/{mercado_correcto}/Titulos/{simbolo}/Clases"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            clases = response.json()
            for clase in clases:
                if clase.get('simbolo', '').endswith('D'):
                    return clase['simbolo']
            return None
        else:
            return None
    except Exception:
        return None

# --- Portfolio Optimization Functions ---
# Eliminar funciones relacionadas con optimización:
# - calculate_portfolio_metrics
# - optimize_portfolio
# - calcular_metricas_portafolio (mantener, ya que se usa en resumen)
# - PortfolioManager
# - PortfolioOutput
# - mostrar_optimizacion_portafolio

def calcular_metricas_portafolio(activos_data, valor_total):
    """
    Calcula métricas comprehensivas del portafolio incluyendo P&L, quantiles y probabilidades
    """
    try:
        # Calcular estadísticas básicas
        valores = [activo['Valuación'] for activo in activos_data if activo['Valuación'] > 0]
        
        if not valores:
            return None
        
        # Convertir a numpy array para cálculos
        valores_array = np.array(valores)
        
        # Estadísticas básicas
        media = np.mean(valores_array)
        mediana = np.median(valores_array)
        std_dev = np.std(valores_array)
        var_95 = np.percentile(valores_array, 5)  # VaR al 5%
        var_99 = np.percentile(valores_array, 1)  # VaR al 1%
        
        # Quantiles
        q25 = np.percentile(valores_array, 25)
        q50 = np.percentile(valores_array, 50)  # Mediana
        q75 = np.percentile(valores_array, 75)
        q90 = np.percentile(valores_array, 90)
        q95 = np.percentile(valores_array, 95)
        
        # Calcular concentración del portafolio
        pesos = valores_array / valor_total
        concentracion = np.sum(pesos ** 2)  # Índice de Herfindahl
        
        # Simular retornos esperados (usando distribución normal)
        # Asumiendo retorno anual promedio del 8% con volatilidad del 20%
        retorno_esperado_anual = 0.08
        volatilidad_anual = 0.20
        
        # Calcular métricas en términos monetarios
        retorno_esperado_pesos = valor_total * retorno_esperado_anual
        riesgo_anual_pesos = valor_total * volatilidad_anual
        
        # Simulación Monte Carlo simple para P&L esperado
        np.random.seed(42)
        num_simulaciones = 1000
        retornos_simulados = np.random.normal(retorno_esperado_anual, volatilidad_anual, num_simulaciones)
        pl_simulado = valor_total * retornos_simulados
        
        # Probabilidades
        prob_ganancia = np.sum(pl_simulado > 0) / num_simulaciones
        prob_perdida = np.sum(pl_simulado < 0) / num_simulaciones
        prob_perdida_mayor_10 = np.sum(pl_simulado < -valor_total * 0.10) / num_simulaciones
        prob_ganancia_mayor_10 = np.sum(pl_simulado > valor_total * 0.10) / num_simulaciones
        
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
            'pl_esperado_min': np.min(pl_simulado),
            'pl_esperado_max': np.max(pl_simulado),
            'pl_esperado_medio': np.mean(pl_simulado),
            'pl_percentil_5': np.percentile(pl_simulado, 5),
            'pl_percentil_95': np.percentile(pl_simulado, 95),
            'probabilidades': {
                'ganancia': prob_ganancia,
                'perdida': prob_perdida,
                'perdida_mayor_10': prob_perdida_mayor_10,
                'ganancia_mayor_10': prob_ganancia_mayor_10
            }
        }
    except Exception as e:
        st.error(f"Error calculando métricas del portafolio: {str(e)}")
        return None

# Clase para análisis de distribuciones estadísticas
class DistribucionPortafolio:
    def __init__(self, retornos, decimales=5, factor=252):
        self.retornos = retornos
        self.decimales = decimales
        self.factor = factor  # Factor para anualizar (252 días hábiles)
        self.vector = retornos.values if hasattr(retornos, 'values') else np.array(retornos)
        self.media_anual = None
        self.volatilidad_anual = None
        self.ratio_sharpe = None
        self.var_95 = None
        self.var_99 = None
        self.cvar_95 = None
        self.sesgo = None
        self.curtosis = None
        self.jb_stat = None
        self.p_valor = None
        self.es_normal = None
        self.mejor_ajuste = None
        self.mejores_parametros = None
        self.nombre_mejor_ajuste = None
        self.max_drawdown = None
        self.calmar_ratio = None
        self.sortino_ratio = None

    def calcular_estadisticas_completas(self):
        """
        Calcula estadísticas comprehensivas del portafolio
        """
        if len(self.vector) == 0:
            return False
            
        # Estadísticas básicas
        self.media_anual = np.mean(self.vector) * self.factor
        self.volatilidad_anual = np.std(self.vector) * np.sqrt(self.factor)
        self.ratio_sharpe = self.media_anual / self.volatilidad_anual if self.volatilidad_anual > 0 else 0.0
        
        # Métricas de riesgo
        self.var_95 = np.percentile(self.vector, 5)
        self.var_99 = np.percentile(self.vector, 1)
        self.cvar_95 = np.mean(self.vector[self.vector <= self.var_95])
        
        # Momentos estadísticos
        self.sesgo = stats.skew(self.vector)
        self.curtosis = stats.kurtosis(self.vector)
        
        # Test de normalidad Jarque-Bera
        self.jb_stat, self.p_valor = stats.jarque_bera(self.vector)
        self.es_normal = self.p_valor > 0.05
        
        # Métricas adicionales de riesgo
        self.max_drawdown = self.calcular_max_drawdown()
        self.calmar_ratio = self.media_anual / abs(self.max_drawdown) if self.max_drawdown != 0 else 0
        
        # Sortino Ratio (usando volatilidad de retornos negativos)
        retornos_negativos = self.vector[self.vector < 0]
        downside_deviation = np.std(retornos_negativos) * np.sqrt(self.factor) if len(retornos_negativos) > 0 else 0
        self.sortino_ratio = self.media_anual / downside_deviation if downside_deviation > 0 else 0
        
        # Mejor ajuste de distribución
        self.mejor_ajuste, self.mejores_parametros, self.nombre_mejor_ajuste = self.analizar_mejor_distribucion()
        
        return True

    def calcular_max_drawdown(self):
        """
        Calcula el máximo drawdown de la serie de retornos
        """
        try:
            precios_acumulados = (1 + self.vector).cumprod()
            rolling_max = np.maximum.accumulate(precios_acumulados)
            drawdown = (precios_acumulados - rolling_max) / rolling_max
            return np.min(drawdown)
        except:
            return 0

    def analizar_mejor_distribucion(self):
        """
        Encuentra la mejor distribución ajustada a los datos
        """
        distribuciones = {
            'norm': 'Normal',
            't': 't de Student',
            'skewnorm': 'Normal Sesgada',
            'uniform': 'Uniforme',
            'expon': 'Exponencial',
            'chi2': 'Chi-cuadrado'
        }
        
        resultados = {}
        for codigo_dist, nombre_dist in distribuciones.items():
            try:
                objeto_dist = getattr(stats, codigo_dist)
                parametros = objeto_dist.fit(self.vector)
                ks_stat, p_valor = stats.kstest(self.vector, codigo_dist, args=parametros)
                resultados[codigo_dist] = {
                    'KS Statistic': ks_stat, 
                    'P-Value': p_valor, 
                    'Params': parametros, 
                    'Name': nombre_dist
                }
            except:
                continue
        
        if not resultados:
            return 'norm', (0, 1), 'Normal'
            
        codigo_mejor_ajuste = max(resultados, key=lambda x: resultados[x]['P-Value'])
        return (codigo_mejor_ajuste, 
                resultados[codigo_mejor_ajuste]['Params'], 
                resultados[codigo_mejor_ajuste]['Name'])

    def crear_graficos_streamlit(self):
        """
        Crea gráficos para mostrar en Streamlit
        """
        # Histograma de retornos con distribución ajustada
        fig_hist = go.Figure()
        
        # Histograma
        fig_hist.add_trace(go.Histogram(
            x=self.vector,
            nbinsx=50,
            name="Retornos Observados",
            opacity=0.7,
            histnorm='probability density'
        ))
        
        # Distribución ajustada
        try:
            x = np.linspace(np.min(self.vector), np.max(self.vector), 1000)
            objeto_dist = getattr(stats, self.mejor_ajuste)
            y = objeto_dist.pdf(x, *self.mejores_parametros)
            
            fig_hist.add_trace(go.Scatter(
                x=x, y=y,
                mode='lines',
                name=f'Ajuste {self.nombre_mejor_ajuste}',
                line=dict(color='red', width=2)
            ))
        except:
            pass
        
        fig_hist.update_layout(
            title="Distribución de Retornos del Portafolio",
            xaxis_title="Retornos",
            yaxis_title="Densidad",
            height=400
        )
        
        # Q-Q Plot
        fig_qq = go.Figure()
        
        try:
            from scipy import stats as scipy_stats
            theoretical_quantiles = scipy_stats.probplot(self.vector, dist="norm")[0][0]
            sample_quantiles = scipy_stats.probplot(self.vector, dist="norm")[0][1]
            
            fig_qq.add_trace(go.Scatter(
                x=theoretical_quantiles,
                y=sample_quantiles,
                mode='markers',
                name='Datos observados'
            ))
            
            # Línea de referencia
            min_val = min(min(theoretical_quantiles), min(sample_quantiles))
            max_val = max(max(theoretical_quantiles), max(sample_quantiles))
            fig_qq.add_trace(go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode='lines',
                name='Distribución normal teórica',
                line=dict(color='red', dash='dash')
            ))
            
            fig_qq.update_layout(
                title="Q-Q Plot vs Distribución Normal",
                xaxis_title="Cuantiles Teóricos",
                yaxis_title="Cuantiles de la Muestra",
                height=400
            )
        except:
            fig_qq = None
        
        return fig_hist, fig_qq

def mostrar_estadisticas_detalladas_portafolio(activos_data, df_precios):
    """
    Muestra análisis estadístico detallado del portafolio
    """
    st.markdown("### 📊 Análisis Estadístico Detallado del Portafolio")
    
    if df_precios is None or df_precios.empty:
        st.warning("No hay datos históricos suficientes para análisis estadístico")
        return
    
    # Calcular retornos del portafolio
    try:
        # Calcular pesos basados en valuación actual
        valuaciones = [activo['Valuación'] for activo in activos_data if activo['Valuación'] > 0]
        valor_total = sum(valuaciones)
        
        if valor_total == 0:
            st.warning("No se pueden calcular pesos del portafolio - valuaciones no disponibles")
            return
        
        # Encontrar símbolos comunes entre activos y precios históricos
        simbolos_activos = [activo['Símbolo'] for activo in activos_data if activo['Valuación'] > 0]
        simbolos_precios = df_precios.columns.tolist()
        simbolos_comunes = list(set(simbolos_activos) & set(simbolos_precios))
        
        if len(simbolos_comunes) < 2:
            st.warning("Necesitamos al menos 2 activos con datos históricos para análisis estadístico")
            return
        
        # Crear pesos para los símbolos con datos
        pesos = {}
        valor_comun = 0
        for activo in activos_data:
            if activo['Símbolo'] in simbolos_comunes and activo['Valuación'] > 0:
                pesos[activo['Símbolo']] = activo['Valuación']
                valor_comun += activo['Valuación']
        
        # Normalizar pesos
        for simbolo in pesos:
            pesos[simbolo] = pesos[simbolo] / valor_comun
        
        # Calcular retornos del portafolio
        retornos_df = df_precios[simbolos_comunes].pct_change().dropna()
        pesos_array = np.array([pesos[simbolo] for simbolo in simbolos_comunes])
        retornos_portafolio = (retornos_df * pesos_array).sum(axis=1)
        
        if len(retornos_portafolio) < 30:
            st.warning("Datos históricos insuficientes (menos de 30 observaciones)")
            return
        
        # Crear objeto de análisis estadístico
        distribucion = DistribucionPortafolio(retornos_portafolio)
        
        if not distribucion.calcular_estadisticas_completas():
            st.error("Error calculando estadísticas")
            return
        
        # === MÉTRICAS PRINCIPALES ===
        st.markdown("#### 📈 Métricas de Rendimiento y Riesgo")
        
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric(
            "Retorno Anualizado",
            f"{distribucion.media_anual:.2%}",
            help="Retorno promedio anualizado del portafolio"
        )
        
        col2.metric(
            "Volatilidad Anualizada",
            f"{distribucion.volatilidad_anual:.2%}",
            help="Riesgo anualizado (desviación estándar)"
        )
        
        col3.metric(
            "Ratio de Sharpe",
            f"{distribucion.ratio_sharpe:.3f}",
            help="Retorno por unidad de riesgo"
        )
        
        col4.metric(
            "Ratio de Sortino",
            f"{distribucion.sortino_ratio:.3f}",
            help="Retorno por unidad de riesgo de cola"
        )
        
        # === MÉTRICAS DE RIESGO ===
        st.markdown("#### ⚠️ Métricas de Riesgo")
        
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric(
            "VaR 95% (diario)",
            f"{distribucion.var_95:.2%}",
            help="Pérdida máxima esperada en el 95% de los casos"
        )
        
        col2.metric(
            "VaR 99% (diario)",
            f"{distribucion.var_99:.2%}",
            help="Pérdida máxima esperada en el 99% de los casos"
        )
        
        col3.metric(
            "CVaR 95%",
            f"{distribucion.cvar_95:.2%}",
            help="Pérdida esperada condicionada (tail risk)"
        )
        
        col4.metric(
            "Max Drawdown",
            f"{distribucion.max_drawdown:.2%}",
            help="Máxima pérdida acumulada desde un pico"
        )
        
        # === ANÁLISIS DE DISTRIBUCIÓN ===
        st.markdown("#### 📊 Análisis de Distribución")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        col1.metric(
            "Sesgo (Skewness)",
            f"{distribucion.sesgo:.3f}",
            help="Asimetría de la distribución (0=simétrica)"
        )
        
        col2.metric(
            "Curtosis",
            f"{distribucion.curtosis:.3f}",
            help="Exceso de curtosis (0=normal)"
        )
        
        col3.metric(
            "Jarque-Bera",
            f"{distribucion.jb_stat:.3f}",
            help="Estadístico de normalidad"
        )
        
        col4.metric(
            "P-valor JB",
            f"{distribucion.p_valor:.4f}",
            help="Significancia del test de normalidad"
        )
        
        normalidad_status = "✅ Normal" if distribucion.es_normal else "❌ No Normal"
        col5.metric(
            "Distribución",
            normalidad_status,
            help="Test de normalidad Jarque-Bera (α=0.05)"
        )
        
        # === MEJOR AJUSTE DE DISTRIBUCIÓN ===
        st.markdown("#### 🎯 Mejor Ajuste de Distribución")
        
        col1, col2 = st.columns(2)
        
        col1.metric(
            "Mejor Distribución",
            distribucion.nombre_mejor_ajuste,
            help="Distribución que mejor ajusta a los datos"
        )
        
        col2.metric(
            "Ratio de Calmar",
            f"{distribucion.calmar_ratio:.3f}",
            help="Retorno anualizado / |Max Drawdown|"
        )
        
        # === GRÁFICOS ESTADÍSTICOS ===
        st.markdown("#### 📈 Visualizaciones Estadísticas")
        
        fig_hist, fig_qq = distribucion.crear_graficos_streamlit()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            if fig_qq:
                st.plotly_chart(fig_qq, use_container_width=True)
            else:
                st.info("Q-Q Plot no disponible")
        
        # === INTERPRETACIÓN Y RECOMENDACIONES ===
        st.markdown("#### 💡 Interpretación y Recomendaciones")
        
        # Análisis de Sharpe Ratio
        if distribucion.ratio_sharpe > 1.0:
            st.success("✅ **Excelente Ratio de Sharpe**: El portafolio muestra un retorno ajustado por riesgo muy bueno.")
        elif distribucion.ratio_sharpe > 0.5:
            st.info("ℹ️ **Buen Ratio de Sharpe**: El retorno ajustado por riesgo es aceptable.")
        else:
            st.warning("⚠️ **Bajo Ratio de Sharpe**: Considere revisar la estrategia de inversión.")
        
        # Análisis de normalidad
        if not distribucion.es_normal:
            st.warning("⚠️ **Distribución No Normal**: Los retornos no siguen distribución normal. Considere:")
            st.markdown("""
            - Usar métricas de riesgo no paramétricas
            - Considerar modelos de colas pesadas
            - Evaluar estrategias de cobertura adicionales
            """)
        
        # Análisis de sesgo
        if abs(distribucion.sesgo) > 0.5:
            if distribucion.sesgo > 0:
                st.info("📈 **Sesgo Positivo**: Tendencia a retornos extremos positivos ocasionales.")
            else:
                st.warning("📉 **Sesgo Negativo**: Mayor probabilidad de pérdidas extremas.")
        
        # Análisis de drawdown
        if abs(distribucion.max_drawdown) > 0.2:
            st.warning("⚠️ **Alto Drawdown**: El portafolio ha experimentado pérdidas significativas. Considere diversificación adicional.")
        
        # === TABLA RESUMEN DE ESTADÍSTICAS ===
        with st.expander("📊 Tabla Resumen de Todas las Estadísticas"):
            estadisticas_resumen = {
                "Métrica": [
                    "Retorno Anualizado", "Volatilidad Anualizada", "Ratio de Sharpe", 
                    "Ratio de Sortino", "VaR 95%", "VaR 99%", "CVaR 95%", 
                    "Max Drawdown", "Ratio de Calmar", "Sesgo", "Curtosis", 
                    "Jarque-Bera", "P-valor JB", "Es Normal", "Mejor Distribución"
                ],
                "Valor": [
                    f"{distribucion.media_anual:.4f}",
                    f"{distribucion.volatilidad_anual:.4f}",
                    f"{distribucion.ratio_sharpe:.4f}",
                    f"{distribucion.sortino_ratio:.4f}",
                    f"{distribucion.var_95:.4f}",
                    f"{distribucion.var_99:.4f}",
                    f"{distribucion.cvar_95:.4f}",
                    f"{distribucion.max_drawdown:.4f}",
                    f"{distribucion.calmar_ratio:.4f}",
                    f"{distribucion.sesgo:.4f}",
                    f"{distribucion.curtosis:.4f}",
                    f"{distribucion.jb_stat:.4f}",
                    f"{distribucion.p_valor:.6f}",
                    "Sí" if distribucion.es_normal else "No",
                    distribucion.nombre_mejor_ajuste
                ]
            }
            
            df_estadisticas = pd.DataFrame(estadisticas_resumen)
            st.dataframe(df_estadisticas, use_container_width=True)
        
        # === INFORMACIÓN TÉCNICA ===
        with st.expander("🔍 Información Técnica del Análisis"):
            st.markdown(f"""
            **Parámetros del Análisis:**
            - Observaciones utilizadas: {len(retornos_portafolio)}
            - Factor de anualización: {distribucion.factor}
            - Activos en el análisis: {len(simbolos_comunes)}
            - Período analizado: {retornos_df.index.min().strftime('%Y-%m-%d')} a {retornos_df.index.max().strftime('%Y-%m-%d')}
            
            **Pesos del Portafolio:**
            """)
            
            # Mostrar pesos como tabla
            pesos_df = pd.DataFrame({
                'Activo': list(pesos.keys()),
                'Peso': [f"{p:.2%}" for p in pesos.values()]
            })
            st.dataframe(pesos_df)
            
    except Exception as e:
        st.error(f"Error en análisis estadístico: {str(e)}")
        st.exception(e)

# Función para crear la interfaz principal
def crear_interfaz_principal():
    """
    Crea la interfaz principal de la aplicación
    """
    # Título y descripción
    st.title("📊 IOL Portfolio Analyzer")
    st.markdown("""
    Esta aplicación te permite analizar tu portafolio de inversiones de InvertirOnline (IOL).
    Podrás visualizar estadísticas, distribución de activos y métricas de riesgo.
    """)
    
    # Separador visual
    st.markdown("---")
    
    # Sección de login
    st.header("🔐 Acceso a InvertirOnline")
    
    # Usar columnas para organizar la interfaz
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("login_form"):
            st.markdown("#### Ingresa tus credenciales de IOL")
            usuario = st.text_input("Usuario", key="usuario")
            contraseña = st.text_input("Contraseña", type="password", key="password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                submit_button = st.form_submit_button("Iniciar Sesión")
            with col_btn2:
                demo_button = st.form_submit_button("Modo Demo")
    
    with col2:
        st.info("""
        ℹ️ **Información**
        
        Esta aplicación es segura y no almacena tus credenciales.
        Las credenciales se utilizan únicamente para acceder a la API de IOL.
        
        Si prefieres no usar tus credenciales, puedes usar el modo demo.
        """)
    
    # Acciones cuando se presiona el botón de inicio de sesión
    if submit_button and usuario and contraseña:
        with st.spinner("Conectando con InvertirOnline..."):
            token_acceso, token_refresh = obtener_tokens(usuario, contraseña)
            
            if token_acceso:
                st.session_state['token_acceso'] = token_acceso
                st.session_state['token_refresh'] = token_refresh
                st.session_state['logged_in'] = True
                
                # Mostrar mensaje de éxito y recargar
                st.success("✅ Sesión iniciada correctamente")
                st.experimental_rerun()
            else:
                st.error("❌ Error al iniciar sesión. Verifica tus credenciales.")
    
    # Modo demo
    if demo_button:
        st.session_state['demo_mode'] = True
        st.success("✅ Modo demo activado")
        st.experimental_rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("Desarrollado con ❤️ para la comunidad de inversores")

# Función para cargar datos reales en modo demo
def cargar_datos_demo():
    """
    Carga datos reales de ejemplo utilizando la API pública de Yahoo Finance
    """
    st.markdown("### 🎮 Modo Demo Activado")
    st.info("Estás usando el modo demo con datos reales obtenidos de Yahoo Finance.")
    
    # Definir símbolos de demostración (empresas importantes del mercado)
    simbolos_demo = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"]
    
    with st.spinner("Obteniendo datos reales de mercado..."):
        # Obtener datos históricos recientes
        end_date = pd.Timestamp.today()
        start_date = end_date - pd.Timedelta(days=365)
        
        # Obtener datos de precios usando yfinance
        try:
            datos_yf = yf.download(
                simbolos_demo,
                start=start_date,
                end=end_date,
                progress=False
            )
            
            # Usar precios de cierre
            df_precios_reales = datos_yf['Close']
            
            # Calcular la valuación actual basada en el último precio disponible
            precios_actuales = df_precios_reales.iloc[-1]
            
            # Definir cantidades para crear un portafolio diversificado
            cantidades = {
                "AAPL": 10,
                "MSFT": 8,
                "GOOGL": 2,
                "AMZN": 5,
                "META": 7,
                "TSLA": 6,
                "NVDA": 4
            }
            
            # Crear el portafolio de activos con datos reales
            activos_reales = []
            for simbolo in simbolos_demo:
                if simbolo in precios_actuales and not pd.isna(precios_actuales[simbolo]):
                    precio = precios_actuales[simbolo]
                    cantidad = cantidades.get(simbolo, 1)  # Usar 1 si no está definido
                    valuacion = precio * cantidad
                    
                    activo = {
                        "Símbolo": simbolo,
                        "Tipo": "Acción",
                        "Cantidad": cantidad,
                        "Precio": precio,
                        "Valuación": valuacion
                    }
                    
                    activos_reales.append(activo)
        
        except Exception as e:
            st.error(f"Error obteniendo datos reales: {str(e)}")
            # Crear datos mínimos en caso de error
            activos_reales = []
            df_precios_reales = pd.DataFrame()
            
            # Notificar al usuario
            st.warning("No se pudieron obtener datos reales. Verifica tu conexión a internet.")
            return
    
    # Verificar que tenemos datos
    if not activos_reales or df_precios_reales.empty:
        st.error("No se pudieron obtener datos reales para el demo.")
        return
    
    # Tabs para diferentes visualizaciones
    tab1, tab2, tab3 = st.tabs(["📝 Resumen", "📈 Gráficos", "🧮 Estadísticas"])
    
    with tab1:
        # Resumen del portafolio
        st.markdown("#### Resumen del Portafolio")
        df_activos = pd.DataFrame(activos_reales)
        st.dataframe(df_activos, use_container_width=True)
        
        # Valor total y distribución
        valor_total = sum(activo["Valuación"] for activo in activos_reales)
        st.metric("Valor Total del Portafolio", f"${valor_total:,.2f}")
        
        # Métricas básicas
        col1, col2, col3 = st.columns(3)
        col1.metric("Cantidad de Activos", len(activos_reales))
        col2.metric("Promedio por Activo", f"${valor_total/len(activos_reales):,.2f}")
        
        # Encontrar el activo con mayor valuación
        max_activo = max(activos_reales, key=lambda x: x["Valuación"])
        col3.metric("Mayor Exposición", f"{max_activo['Símbolo']}")
    
    with tab2:
        # Gráficos
        st.markdown("#### Distribución del Portafolio")
        
        # Gráfico de torta
        fig = go.Figure(data=[go.Pie(
            labels=[activo["Símbolo"] for activo in activos_reales],
            values=[activo["Valuación"] for activo in activos_reales],
            hole=.3
        )])
        fig.update_layout(title_text="Distribución por Activo")
        st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de rendimiento histórico
        st.markdown("#### Rendimiento Histórico")
        # Normalizar precios (base 100)
        df_norm = df_precios_reales.div(df_precios_reales.iloc[0]) * 100
        
        fig_hist = go.Figure()
        for col in df_norm.columns:
            fig_hist.add_trace(go.Scatter(
                x=df_norm.index,
                y=df_norm[col],
                name=col
            ))
        
        fig_hist.update_layout(
            title="Rendimiento Histórico (Base 100)",
            xaxis_title="Fecha",
            yaxis_title="Valor (Base 100)"
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with tab3:
        # Estadísticas reales
        st.markdown("#### Estadísticas del Portafolio")
        
        # Mostrar estadísticas detalladas con datos reales
        mostrar_estadisticas_detalladas_portafolio(activos_reales, df_precios_reales)

def main():
    # Inicializar variables de sesión si no existen
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'demo_mode' not in st.session_state:
        st.session_state['demo_mode'] = False
    if 'token_acceso' not in st.session_state:
        st.session_state['token_acceso'] = None

    # Lógica principal de la aplicación
    if st.session_state['logged_in'] and st.session_state['token_acceso']:
        st.success("Autenticado con IOL")
        # Aquí puedes agregar el dashboard real con datos de IOL
    elif st.session_state['demo_mode']:
        cargar_datos_demo()
        if st.sidebar.button("Salir del Modo Demo"):
            st.session_state['demo_mode'] = False
            st.experimental_rerun()
    else:
        crear_interfaz_principal()

# Ejecutar la aplicación automáticamente
if __name__ == "__main__":
    main()
