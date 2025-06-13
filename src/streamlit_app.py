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

warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="IOL Portfolio Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
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
        'Authorization': f'Bearer {bearer_token}',
        'Content-Type': 'application/json'
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
def calculate_portfolio_metrics(returns, weights):
    """
    Calcula métricas básicas de un portafolio
    """
    portfolio_return = np.sum(returns.mean() * weights) * 252
    portfolio_std = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
    sharpe_ratio = portfolio_return / portfolio_std if portfolio_std > 0 else 0
    
    return portfolio_return, portfolio_std, sharpe_ratio

def optimize_portfolio(returns, risk_free_rate=0.0, target_return=None):
    """
    Optimiza un portafolio usando teoría moderna de portafolio
    """
    try:
        from scipy.optimize import minimize
        
        n_assets = len(returns.columns)
        
        # Función objetivo para maximizar el ratio de Sharpe
        def negative_sharpe(weights):
            portfolio_return = np.sum(returns.mean() * weights) * 252
            portfolio_std = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
            if portfolio_std == 0:
                return -np.inf
            sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_std
            return -sharpe_ratio
        
        # Restricciones
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        # Pesos iniciales igualmente distribuidos
        initial_guess = n_assets * [1. / n_assets]
        
        # Optimización
        result = minimize(negative_sharpe, initial_guess, method='SLSQP',
                         bounds=bounds, constraints=constraints)
        
        if result.success:
            return result.x
        else:
            st.warning("La optimización no convergió. Usando pesos iguales.")
            return np.array(initial_guess)
            
    except ImportError:
        st.warning("scipy no disponible. Usando pesos iguales.")
        return np.array([1/n_assets] * n_assets)
    except Exception as e:
        st.warning(f"Error en optimización: {str(e)}. Usando pesos iguales.")
        return np.array([1/n_assets] * n_assets)

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

def mostrar_resumen_portafolio(portafolio):
    """
    Muestra un resumen comprehensivo del portafolio con interfaz mejorada
    """
    st.markdown("### 📈 Resumen del Portafolio")
    
    activos = portafolio.get('activos', [])
    
    # Preparar datos para análisis con mejor extracción de valuación
    datos_activos = []
    valor_total = 0
    
    for activo in activos:
        try:
            titulo = activo.get('titulo', {})
            simbolo = titulo.get('simbolo', 'N/A')
            descripcion = titulo.get('descripcion', 'Sin descripción')
            tipo = titulo.get('tipo', 'N/A')
            cantidad = activo.get('cantidad', 0)
            
            # Mejorar extracción de valuación con más campos posibles
            valuacion = 0
            
            # Campos de valuación en orden de preferencia
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
            
            for campo in campos_valuacion:
                if campo in activo and activo[campo] is not None:
                    try:
                        valuacion = float(activo[campo])
                        if valuacion > 0:
                            break
                    except (ValueError, TypeError):
                        continue
            
            # Si no se encuentra valuación directa, intentar calcular
            if valuacion == 0 and cantidad:
                precio_unitario = titulo.get('precio', titulo.get('cotizacion', 0))
                if precio_unitario:
                    try:
                        valuacion = float(cantidad) * float(precio_unitario)
                    except (ValueError, TypeError):
                        pass
            
            datos_activos.append({
                'Símbolo': simbolo,
                'Descripción': descripcion,
                'Tipo': tipo,
                'Cantidad': cantidad,
                'Valuación': valuacion,
                'Datos_Raw': activo
            })
            
            valor_total += valuacion
            
        except Exception as e:
            st.warning(f"Error procesando activo: {str(e)}")
            continue
    
    if datos_activos:
        df_activos = pd.DataFrame(datos_activos)
        
        # === CARDS DE MÉTRICAS PRINCIPALES ===
        st.markdown("#### 📊 Métricas Principales")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h4 style="margin: 0; color: #1f4e79;">📈 Total de Activos</h4>
                <h2 style="margin: 0.5rem 0; color: #2d5aa0;">{}</h2>
                <p style="margin: 0; color: #666; font-size: 0.9rem;">Posiciones únicas</p>
            </div>
            """.format(len(datos_activos)), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h4 style="margin: 0; color: #1f4e79;">🏷️ Símbolos Únicos</h4>
                <h2 style="margin: 0.5rem 0; color: #2d5aa0;">{}</h2>
                <p style="margin: 0; color: #666; font-size: 0.9rem;">Instrumentos diferentes</p>
            </div>
            """.format(df_activos['Símbolo'].nunique()), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h4 style="margin: 0; color: #1f4e79;">📊 Tipos de Activos</h4>
                <h2 style="margin: 0.5rem 0; color: #2d5aa0;">{}</h2>
                <p style="margin: 0; color: #666; font-size: 0.9rem;">Clases de instrumentos</p>
            </div>
            """.format(df_activos['Tipo'].nunique()), unsafe_allow_html=True)
        
        with col4:
            valor_display = f"${valor_total:,.2f}"
            color_valor = "#28a745" if valor_total > 0 else "#dc3545"
            st.markdown("""
            <div class="metric-card">
                <h4 style="margin: 0; color: #1f4e79;">💰 Valor Total</h4>
                <h2 style="margin: 0.5rem 0; color: {};">{}</h2>
                <p style="margin: 0; color: #666; font-size: 0.9rem;">Valuación actual</p>
            </div>
            """.format(color_valor, valor_display), unsafe_allow_html=True)
        
        # Calcular métricas comprehensivas del portafolio
        metricas = calcular_metricas_portafolio(datos_activos, valor_total)
        
        # === ANÁLISIS DE RIESGO CON CARDS MEJORADAS ===
        if metricas:
            st.markdown("#### ⚠️ Análisis de Riesgo")
            
            col1, col2, col3, col4 = st.columns(4)
            
            # Determinar color de concentración
            concentracion = metricas['concentracion']
            if concentracion < 0.25:
                color_conc = "#28a745"
                status_conc = "🟢 Diversificado"
            elif concentracion < 0.5:
                color_conc = "#ffc107"
                status_conc = "🟡 Moderado"
            else:
                color_conc = "#dc3545"
                status_conc = "🔴 Concentrado"
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h4 style="margin: 0; color: #1f4e79;">🎯 Concentración</h4>
                    <h2 style="margin: 0.5rem 0; color: {color_conc};">{concentracion:.3f}</h2>
                    <p style="margin: 0; color: #666; font-size: 0.9rem;">{status_conc}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <h4 style="margin: 0; color: #1f4e79;">📉 VaR 95%</h4>
                    <h2 style="margin: 0.5rem 0; color: #dc3545;">${metricas['var_95']:,.0f}</h2>
                    <p style="margin: 0; color: #666; font-size: 0.9rem;">Valor en riesgo</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <h4 style="margin: 0; color: #1f4e79;">📊 Volatilidad Anual</h4>
                    <h2 style="margin: 0.5rem 0; color: #ff6b35;">${metricas['riesgo_anual']:,.0f}</h2>
                    <p style="margin: 0; color: #666; font-size: 0.9rem;">Riesgo estimado</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                vol_percent = (metricas['riesgo_anual'] / valor_total * 100) if valor_total > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <h4 style="margin: 0; color: #1f4e79;">📈 Volatilidad %</h4>
                    <h2 style="margin: 0.5rem 0; color: #ff6b35;">{vol_percent:.1f}%</h2>
                    <p style="margin: 0; color: #666; font-size: 0.9rem;">Del valor total</p>
                </div>
                """, unsafe_allow_html=True)
        
        # === PROYECCIONES DE RENDIMIENTO ===
        if metricas:
            st.markdown("#### 📈 Proyecciones de Rendimiento (12 meses)")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                retorno_percent = (metricas['retorno_esperado_anual']/valor_total*100) if valor_total > 0 else 0
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: #28a745;">
                    <h4 style="margin: 0; color: #1f4e79;">💹 Retorno Esperado</h4>
                    <h2 style="margin: 0.5rem 0; color: #28a745;">${metricas['retorno_esperado_anual']:,.0f}</h2>
                    <p style="margin: 0; color: #28a745; font-weight: bold;">+{retorno_percent:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                optimista_percent = (metricas['pl_percentil_95']/valor_total*100) if valor_total > 0 else 0
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: #28a745;">
                    <h4 style="margin: 0; color: #1f4e79;">🚀 Escenario Optimista</h4>
                    <h2 style="margin: 0.5rem 0; color: #28a745;">${metricas['pl_percentil_95']:,.0f}</h2>
                    <p style="margin: 0; color: #28a745; font-weight: bold;">+{optimista_percent:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                pesimista_percent = (metricas['pl_percentil_5']/valor_total*100) if valor_total > 0 else 0
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: #dc3545;">
                    <h4 style="margin: 0; color: #1f4e79;">📉 Escenario Pesimista</h4>
                    <h2 style="margin: 0.5rem 0; color: #dc3545;">${metricas['pl_percentil_5']:,.0f}</h2>
                    <p style="margin: 0; color: #dc3545; font-weight: bold;">{pesimista_percent:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
        
        # === GRÁFICOS INTERACTIVOS ===
        if valor_total > 0:
            st.markdown("#### 📊 Visualizaciones")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de distribución por tipo mejorado
                if 'Tipo' in df_activos.columns and df_activos['Valuación'].sum() > 0:
                    st.markdown("##### 🥧 Distribución por Tipo de Activo")
                    
                    tipo_stats = df_activos.groupby('Tipo').agg({
                        'Valuación': 'sum',
                        'Símbolo': 'count'
                    }).round(2)
                    tipo_stats.columns = ['Valor_Total', 'Cantidad']
                    tipo_stats = tipo_stats.reset_index()
                    
                    # Gráfico de torta con colores personalizados
                    colors = ['#1f4e79', '#2d5aa0', '#4dabf7', '#74c0fc', '#a5d8ff']
                    
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=tipo_stats['Tipo'],
                        values=tipo_stats['Valor_Total'],
                        textinfo='label+percent+value',
                        texttemplate='%{label}<br>%{percent}<br>$%{value:,.0f}',
                        marker=dict(colors=colors[:len(tipo_stats)]),
                        hole=0.3
                    )])
                    
                    fig_pie.update_layout(
                        title="Distribución por Tipo de Activo",
                        height=400,
                        showlegend=True,
                        legend=dict(orientation="v", yanchor="middle", y=0.5)
                    )
                    
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Gráfico de top activos
                st.markdown("##### 📊 Top 10 Activos por Valuación")
                
                top_activos = df_activos.nlargest(10, 'Valuación')
                
                fig_bar = go.Figure(data=[go.Bar(
                    x=top_activos['Valuación'],
                    y=top_activos['Símbolo'],
                    orientation='h',
                    marker=dict(
                        color=top_activos['Valuación'],
                        colorscale='Blues',
                        showscale=True
                    ),
                    text=[f'${v:,.0f}' for v in top_activos['Valuación']],
                    textposition='auto'
                )])
                
                fig_bar.update_layout(
                    title="Top Activos por Valor",
                    xaxis_title="Valuación ($)",
                    yaxis_title="Símbolo",
                    height=400,
                    yaxis=dict(categoryorder='total ascending')
                )
                
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # === TABLA DE ACTIVOS MEJORADA ===
        st.markdown("#### 📋 Detalle de Activos")
        
        # Preparar DataFrame para mostrar
        df_display = df_activos.copy()
        df_display['Peso (%)'] = (df_display['Valuación'] / valor_total * 100).round(2) if valor_total > 0 else 0
        df_display['Valuación_fmt'] = df_display['Valuación'].apply(lambda x: f"${x:,.2f}" if x > 0 else "Sin valor")
        
        # Crear indicadores visuales
        def get_peso_indicator(peso):
            if peso >= 20:
                return "🔴"
            elif peso >= 10:
                return "🟡"
            elif peso >= 5:
                return "🟢"
            else:
                return "⚪"
        
        df_display['Indicador'] = df_display['Peso (%)'].apply(get_peso_indicator)
        
        # Reordenar y formatear columnas
        columns_order = ['Indicador', 'Símbolo', 'Descripción', 'Tipo', 'Cantidad', 'Valuación', 'Peso (%)']
        df_final = df_display[columns_order].copy()
        df_final.columns = ['🎯', 'Símbolo', 'Descripción', 'Tipo', 'Cantidad', 'Valuación', 'Peso (%)']
        
        # Ordenar por peso descendente
        df_final = df_final.sort_values('Peso (%)', ascending=False)
        
        # Configurar el dataframe con colores
        st.dataframe(
            df_final,
            use_container_width=True,
            height=400,
            column_config={
                "🎯": st.column_config.TextColumn("🎯", help="🔴>20% 🟡10-20% 🟢5-10% ⚪<5%"),
                "Peso (%)": st.column_config.ProgressColumn("Peso (%)", min_value=0, max_value=100),
                "Valuación": st.column_config.TextColumn("Valuación")
            }
        )
        
        # === ALERTAS Y RECOMENDACIONES MEJORADAS ===
        st.markdown("#### 💡 Análisis y Recomendaciones")
        
        if metricas:
            alertas = []
            
            # Análisis de concentración
            if metricas['concentracion'] > 0.5:
                alertas.append({
                    'tipo': 'error',
                    'titulo': '⚠️ Portafolio Altamente Concentrado',
                    'mensaje': 'Su portafolio tiene un alto nivel de concentración. Considere diversificar para reducir el riesgo.',
                    'accion': 'Diversificar posiciones'
                })
            elif metricas['concentracion'] > 0.25:
                alertas.append({
                    'tipo': 'warning',
                    'titulo': 'ℹ️ Concentración Moderada',
                    'mensaje': 'Su portafolio está moderadamente concentrado. La diversificación adicional podría reducir el riesgo.',
                    'accion': 'Considerar más diversificación'
                })
            else:
                alertas.append({
                    'tipo': 'success',
                    'titulo': '✅ Buena Diversificación',
                    'mensaje': 'Su portafolio muestra un buen nivel de diversificación.',
                    'accion': 'Mantener estrategia actual'
                })
            
            # Análisis de activos principales
            top_3_pesos = df_display.nlargest(3, 'Peso (%)')['Peso (%)']
            if len(top_3_pesos) > 0 and top_3_pesos.iloc[0] > 30:
                alertas.append({
                    'tipo': 'warning',
                    'titulo': '🎯 Concentración en Activo Principal',
                    'mensaje': f'Su activo principal representa {top_3_pesos.iloc[0]:.1f}% del portafolio.',
                    'accion': 'Considerar reducir posición dominante'
                })
            
            # Análisis de correlación
            if len(df_display) > 1:
                st.markdown("#### 🔗 Matriz de Correlación de Activos")
                
                # Calcular matriz de correlación
                correlacion = df_display.corr()
                
                # Gráfico de calor interactivo
                fig_heatmap = go.Figure(data=go.Heatmap(
                    z=correlacion.values,
                    x=correlacion.index,
                    y=correlacion.columns,
                    colorscale='Viridis',
                    colorbar=dict(title="Correlación")
                ))
                
                fig_heatmap.update_layout(
                    title="Matriz de Correlación - Activos del Portafolio",
                    xaxis_title="Activos",
                    yaxis_title="Activos",
                    height=400
                )
                
                st.plotly_chart(fig_heatmap, use_container_width=True)
        
            # Mostrar alertas con diseño mejorado
            for alerta in alertas:
                if alerta['tipo'] == 'success':
                    color = "#d4edda"
                    border = "#c3e6cb"
                elif alerta['tipo'] == 'warning':
                    color = "#fff3cd"
                    border = "#ffeaa7"
                else:
                    color = "#f8d7da"
                    border = "#f5c6cb"
                
                st.markdown(f"""
                <div style="background: {color}; border: 1px solid {border}; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                    <h4 style="margin: 0 0 0.5rem 0;">{alerta['titulo']}</h4>
                    <p style="margin: 0 0 0.5rem 0;">{alerta['mensaje']}</p>
                    <p style="margin: 0; font-weight: bold; font-size: 0.9rem;"><strong>Recomendación:</strong> {alerta['accion']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # === INFORMACIÓN DE DEBUG EXPANDIBLE ===
        with st.expander("🔍 Información Técnica y Debug"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📊 Estadísticas del Análisis:**")
                debug_info = f"""
                • Total de activos procesados: {len(datos_activos)}
                • Activos con valuación > 0: {len([a for a in datos_activos if a['Valuación'] > 0])}
                • Valor total calculado: ${valor_total:,.2f}
                • Número de tipos únicos: {df_activos['Tipo'].nunique()}
                • Símbolos únicos: {df_activos['Símbolo'].nunique()}
                """
                st.code(debug_info)
            
            with col2:
                st.markdown("**🔧 Datos Técnicos:**")
                if activos:
                    campos_encontrados = set()
                    for activo in activos[:3]:
                        if isinstance(activo, dict):
                            campos_encontrados.update(activo.keys())
                    
                    st.code("Campos disponibles:\n" + "\n".join(sorted(list(campos_encontrados))[:15]))
                    
                    if st.button("Ver estructura completa"):
                        st.json(activos[0] if activos else {})

def mostrar_estado_cuenta(estado_cuenta):
    """
    Muestra el estado de cuenta del cliente con interfaz moderna y mejorada
    """
    st.markdown("### 💰 Estado de Cuenta Detallado")
    
    if not estado_cuenta:
        st.markdown("""
        <div class="warning-box">
            <h3>⚠️ No hay datos disponibles</h3>
            <p>No se pudieron obtener los datos del estado de cuenta.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # === RESUMEN EJECUTIVO ===
    st.markdown("#### 📊 Resumen Ejecutivo")
    
    # Extraer información según la estructura de la API
    total_en_pesos = estado_cuenta.get('totalEnPesos', 0)
    cuentas = estado_cuenta.get('cuentas', [])
    estadisticas = estado_cuenta.get('estadisticas', [])
    
    # Calcular totales agregados
    total_disponible = 0
    total_comprometido = 0
    total_saldo = 0
    total_titulos_valorizados = 0
    total_general = 0
    
    cuentas_por_moneda = {}
    
    for cuenta in cuentas:
        # Extraer valores de cada cuenta
        disponible = float(cuenta.get('disponible', 0))
        comprometido = float(cuenta.get('comprometido', 0))
        saldo = float(cuenta.get('saldo', 0))
        titulos_valorizados = float(cuenta.get('titulosValorizados', 0))
        total_cuenta = float(cuenta.get('total', 0))
        moneda = cuenta.get('moneda', 'peso_Argentino')
        
        # Sumar totales
        total_disponible += disponible
        total_comprometido += comprometido
        total_saldo += saldo
        total_titulos_valorizados += titulos_valorizados
        total_general += total_cuenta
        
        # Agrupar por moneda
        if moneda not in cuentas_por_moneda:
            cuentas_por_moneda[moneda] = {
                'disponible': 0,
                'saldo': 0,
                'total': 0,
                'cuentas': []
            }
        
        cuentas_por_moneda[moneda]['disponible'] += disponible
        cuentas_por_moneda[moneda]['saldo'] += saldo
        cuentas_por_moneda[moneda]['total'] += total_cuenta
        cuentas_por_moneda[moneda]['cuentas'].append(cuenta)
    
    # === MÉTRICAS PRINCIPALES CON CARDS MEJORADAS ===
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        color_total = "#28a745" if total_general > 0 else "#dc3545"
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {color_total};">
            <h4 style="margin: 0; color: #1f4e79;">💰 Total General</h4>
            <h2 style="margin: 0.5rem 0; color: {color_total};">${total_general:,.2f}</h2>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">Suma de todas las cuentas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #2d5aa0;">
            <h4 style="margin: 0; color: #1f4e79;">🇦🇷 Total en Pesos</h4>
            <h2 style="margin: 0.5rem 0; color: #2d5aa0;">AR$ {total_en_pesos:,.2f}</h2>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">Según cotización IOL</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        color_disponible = "#28a745" if total_disponible > 0 else "#6c757d"
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {color_disponible};">
            <h4 style="margin: 0; color: #1f4e79;">✅ Disponible</h4>
            <h2 style="margin: 0.5rem 0; color: {color_disponible};">${total_disponible:,.2f}</h2>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">Para operar</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        color_titulos = "#ff6b35" if total_titulos_valorizados > 0 else "#6c757d"
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {color_titulos};">
            <h4 style="margin: 0; color: #1f4e79;">📈 Títulos</h4>
            <h2 style="margin: 0.5rem 0; color: {color_titulos};">${total_titulos_valorizados:,.2f}</h2>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">Valor de cartera</p>
        </div>
        """, unsafe_allow_html=True)
    
    # === DISTRIBUCIÓN POR MONEDA ===
    if cuentas_por_moneda:
        st.markdown("#### 💱 Distribución por Moneda")
        
        for moneda, datos in cuentas_por_moneda.items():
            # Convertir nombre de moneda a formato legible
            nombre_moneda_map = {
                'peso_Argentino': '🇦🇷 Pesos Argentinos',
                'dolar_Estadounidense': '🇺🇸 Dólares Estadounidenses',
                'euro': '🇪🇺 Euros'
            }
            nombre_moneda = nombre_moneda_map.get(moneda, f"💰 {moneda.replace('_', ' ').title()}")
            
            with st.expander(f"{nombre_moneda} ({len(datos['cuentas'])} cuenta(s))", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                        <h4 style="margin: 0; color: #28a745;">Disponible</h4>
                        <h3 style="margin: 0.5rem 0; color: #28a745;">${datos['disponible']:,.2f}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                        <h4 style="margin: 0; color: #2d5aa0;">Saldo</h4>
                        <h3 style="margin: 0.5rem 0; color: #2d5aa0;">${datos['saldo']:,.2f}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                        <h4 style="margin: 0; color: #1f4e79;">Total</h4>
                        <h3 style="margin: 0.5rem 0; color: #1f4e79;">${datos['total']:,.2f}</h3>
                    </div>
                    """, unsafe_allow_html=True)
    
    # === DETALLE DE CUENTAS ===
    if cuentas:
        st.markdown("#### 📋 Detalle de Cuentas")
        
        # Crear DataFrame mejorado
        datos_cuentas = []
        for cuenta in cuentas:
            # Calcular porcentajes
            disponible_val = cuenta.get('disponible', 0)
            total_val = cuenta.get('total', 0)
            porcentaje_disponible = (disponible_val / total_val * 100) if total_val > 0 else 0
            
            datos_cuentas.append({
                'Número': cuenta.get('numero', 'N/A'),
                'Tipo': cuenta.get('tipo', 'N/A').replace('_', ' ').title(),
                'Moneda': cuenta.get('moneda', 'N/A').replace('_', ' ').title(),
                'Disponible': disponible_val,
                'Comprometido': cuenta.get('comprometido', 0),
                'Saldo': cuenta.get('saldo', 0),
                'Títulos': cuenta.get('titulosValorizados', 0),
                'Total': total_val,
                'Estado': cuenta.get('estado', 'N/A').title(),
                '% Disponible': porcentaje_disponible
            })
        
        if datos_cuentas:
            df_cuentas = pd.DataFrame(datos_cuentas)
            
            # Formatear columnas monetarias
            money_cols = ['Disponible', 'Comprometido', 'Saldo', 'Títulos', 'Total']
            for col in money_cols:
                df_cuentas[f'{col}_fmt'] = df_cuentas[col].apply(lambda x: f"${x:,.2f}")
            
            # Seleccionar columnas para mostrar
            display_cols = ['Número', 'Tipo', 'Moneda', 'Disponible_fmt', 'Títulos_fmt', 'Total_fmt', 'Estado', '% Disponible']
            df_display = df_cuentas[display_cols].copy()
            df_display.columns = ['Número', 'Tipo', 'Moneda', 'Disponible', 'Títulos', 'Total', 'Estado', '% Disponible']
            
            # Configurar el dataframe con progreso
            st.dataframe(
                df_display,
                use_container_width=True,
                height=300,
                column_config={
                    "% Disponible": st.column_config.ProgressColumn(
                        "% Disponible",
                        min_value=0,
                        max_value=100,
                        format="%.1f%%"
                    ),
                }
            )
    
    # === ESTADÍSTICAS ADICIONALES ===
    if estadisticas:
        st.markdown("#### 📈 Estadísticas de Operaciones")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Mostrar estadísticas en cards
            for i, stat in enumerate(estadisticas[:3]):  # Mostrar solo las primeras 3
                descripcion = stat.get('descripcion', 'N/A')
                cantidad = stat.get('cantidad', 0)
                volumen = stat.get('volumen', 0)
                
                st.markdown(f"""
                <div class="metric-card">
                    <h4 style="margin: 0; color: #1f4e79;">{descripcion}</h4>
                    <div style="display: flex; justify-content: space-between; margin: 0.5rem 0;">
                        <div>
                            <h3 style="margin: 0; color: #2d5aa0;">{cantidad}</h3>
                            <p style="margin: 0; color: #666; font-size: 0.9rem;">Operaciones</p>
                        </div>
                        <div style="text-align: right;">
                            <h3 style="margin: 0; color: #ff6b35;">${volumen:,.2f}</h3>
                            <p style="margin: 0; color: #666; font-size: 0.9rem;">Volumen</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            # Gráfico de estadísticas si hay suficientes datos
            if len(estadisticas) > 1:
                st.markdown("##### 📊 Distribución de Volumen")
                
                # Crear gráfico demo
                labels = [s.get('descripcion', f'Operación {i+1}') for i, s in enumerate(estadisticas)]
                values = [s.get('volumen', 0) for s in estadisticas]
                
                fig_stats = go.Figure(data=[go.Bar(
                    x=labels,
                    y=values,
                    marker=dict(color='#1f4e79'),
                    text=[f'${v:,.0f}' for v in values],
                    textposition='auto'
                )])
                
                fig_stats.update_layout(
                    title="Volumen por Tipo de Operación",
                    xaxis_title="Tipo de Operación",
                    yaxis_title="Volumen ($)",
                    height=300,
                    template="plotly_white"
                )
                
                st.plotly_chart(fig_stats, use_container_width=True)
    
    # === ANÁLISIS FINANCIERO ===
    st.markdown("#### 💡 Análisis Financiero")
    
    # Calcular ratios y métricas
    if total_general > 0:
        ratio_liquidez = (total_disponible / total_general * 100)
        ratio_inversion = (total_titulos_valorizados / total_general * 100)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            color_liquidez = "#28a745" if ratio_liquidez > 20 else "#ffc107" if ratio_liquidez > 10 else "#dc3545"
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: {color_liquidez};">
                <h4 style="margin: 0; color: #1f4e79;">💧 Ratio de Liquidez</h4>
                <h2 style="margin: 0.5rem 0; color: {color_liquidez};">{ratio_liquidez:.1f}%</h2>
                <p style="margin: 0; color: #666; font-size: 0.9rem;">
                    {'Alto' if ratio_liquidez > 20 else 'Medio' if ratio_liquidez > 10 else 'Bajo'}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            color_inversion = "#ff6b35" if ratio_inversion > 70 else "#28a745" if ratio_inversion > 50 else "#ffc107"
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: {color_inversion};">
                <h4 style="margin: 0; color: #1f4e79;">📈 Ratio de Inversión</h4>
                <h2 style="margin: 0.5rem 0; color: {color_inversion};">{ratio_inversion:.1f}%</h2>
                <p style="margin: 0; color: #666; font-size: 0.9rem;">
                    {'Alto' if ratio_inversion > 70 else 'Bueno' if ratio_inversion > 50 else 'Conservador'}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            diversificacion_monedas = len(cuentas_por_moneda)
            color_div = "#28a745" if diversificacion_monedas > 2 else "#ffc107" if diversificacion_monedas > 1 else "#dc3545"
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: {color_div};">
                <h4 style="margin: 0; color: #1f4e79;">🌍 Diversificación</h4>
                <h2 style="margin: 0.5rem 0; color: {color_div};">{diversificacion_monedas}</h2>
                <p style="margin: 0; color: #666; font-size: 0.9rem;">Monedas diferentes</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Recomendaciones basadas en ratios
        st.markdown("##### 💡 Recomendaciones")
        
        recomendaciones = []
        
        if ratio_liquidez < 10:
            recomendaciones.append("🔴 **Baja Liquidez**: Considere mantener más efectivo disponible para oportunidades.")
        elif ratio_liquidez > 30:
            recomendaciones.append("🟡 **Alta Liquidez**: Tiene mucho efectivo disponible, considere oportunidades de inversión.")
        else:
            recomendaciones.append("🟢 **Liquidez Adecuada**: Mantiene un buen balance entre efectivo e inversiones.")
        
        if ratio_inversion < 30:
            recomendaciones.append("🟡 **Perfil Conservador**: Considere incrementar inversiones gradualmente.")
        elif ratio_inversion > 90:
            recomendaciones.append("🔴 **Alta Exposición**: Considere mantener algo de efectivo para emergencias.")
        else:
            recomendaciones.append("🟢 **Buena Distribución**: Mantiene un equilibrio saludable.")
        
        for rec in recomendaciones:
            st.markdown(f"- {rec}")
    
    # === INFORMACIÓN TÉCNICA ===
    with st.expander("🔍 Información Técnica"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Resumen de Datos:**")
            resumen_tech = f"""
            • Total de cuentas: {len(cuentas)}
            • Monedas diferentes: {len(cuentas_por_moneda)}
            • Estadísticas disponibles: {len(estadisticas)}
            • Total general: ${total_general:,.2f}
            • Última actualización: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            """
            st.code(resumen_tech)
        
        with col2:
            st.markdown("**🔧 Estructura de Datos:**")
            if isinstance(estado_cuenta, dict):
                campos_principales = list(estado_cuenta.keys())
                st.code("Campos principales:\n" + "\n".join(sorted(campos_principales)))

def mostrar_cotizaciones_mercado(token_acceso):
    """
    Muestra cotizaciones y datos de mercado con interfaz moderna
    """
    st.markdown("### 💱 Centro de Mercado y Cotizaciones")
    
    # === TABS PARA DIFERENTES FUNCIONES ===
    tab1, tab2, tab3 = st.tabs(["💰 Cotización MEP", "🏦 Tasas de Caución", "📊 Mercado General"])
    
    with tab1:
        st.markdown("#### 💰 Calculadora de Dólar MEP")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Formulario mejorado para MEP
            with st.form("mep_form"):
                st.markdown("##### ⚙️ Configuración de Consulta")
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    simbolo_mep = st.text_input(
                        "🎯 Símbolo para MEP", 
                        value="AL30",
                        help="Bonos comunes: AL30, GD30, AE38, etc."
                    )
                    id_plazo_compra = st.number_input(
                        "📅 ID Plazo Compra", 
                        value=1, 
                        min_value=1,
                        help="1=Inmediato, 2=24hs, 3=48hs"
                    )
                
                with col_b:
                    monto_ejemplo = st.number_input(
                        "💵 Monto de Ejemplo (USD)",
                        value=1000,
                        min_value=1,
                        help="Monto para calcular equivalencia"
                    )
                    id_plazo_venta = st.number_input(
                        "📅 ID Plazo Venta", 
                        value=1, 
                        min_value=1,
                        help="1=Inmediato, 2=24hs, 3=48hs"
                    )
                
                consultar_mep = st.form_submit_button(
                    "🔍 Consultar Cotización MEP",
                    use_container_width=True,
                    type="primary"
                )
                
                if consultar_mep and simbolo_mep:
                    with st.spinner("📊 Consultando cotización MEP..."):
                        # Simular llamada a la función (reemplazar con función real)
                        # cotizacion_mep = obtener_cotizacion_mep(token_acceso, simbolo_mep, id_plazo_compra, id_plazo_venta)
                        cotizacion_mep = None  # Placeholder
                    
                    if cotizacion_mep:
                        st.success("✅ Cotización MEP obtenida exitosamente")
                        
                        # Mostrar resultados MEP
                        if isinstance(cotizacion_mep, dict):
                            dolar_mep = cotizacion_mep.get('cotizacion', 0)
                            
                            col_r1, col_r2, col_r3 = st.columns(3)
                            
                            with col_r1:
                                st.markdown(f"""
                                <div class="metric-card">
                                    <h4>💱 Dólar MEP</h4>
                                    <h2 style="color: #28a745;">AR$ {dolar_mep:,.2f}</h2>
                                    <p>Por cada USD</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col_r2:
                                pesos_necesarios = monto_ejemplo * dolar_mep
                                st.markdown(f"""
                                <div class="metric-card">
                                    <h4>🧮 Equivalencia</h4>
                                    <h2 style="color: #2d5aa0;">AR$ {pesos_necesarios:,.2f}</h2>
                                    <p>Por USD {monto_ejemplo:,.2f}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col_r3:
                                # Comparar con dólar oficial (simulado)
                                dolar_oficial = 950  # Placeholder
                                brecha = ((dolar_mep - dolar_oficial) / dolar_oficial * 100)
                                st.markdown(f"""
                                <div class="metric-card">
                                    <h4>📈 Brecha vs Oficial</h4>
                                    <h2 style="color: {'#dc3545' if brecha > 0 else '#28a745'};">
                                        {brecha:+.1f}%
                                    </h2>
                                    <p>Diferencia porcentual</p>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.error("❌ No se pudo obtener la cotización MEP")
                        st.info("💡 Verifique que el símbolo sea correcto y que tenga permisos de acceso.")
        
        with col2:
            st.markdown("##### 💡 Símbolos Populares")
            simbolos_populares = ["AL30", "GD30", "AE38", "AL35", "GD35"]
            
            for simbolo in simbolos_populares:
                if st.button(f"📊 {simbolo}", key=f"mep_{simbolo}", use_container_width=True):
                    st.info(f"🎯 Símbolo seleccionado: **{simbolo}**")
    
    with tab2:
        st.markdown("#### 🏦 Monitoreo de Tasas de Caución")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("🔄 Actualizar Tasas", use_container_width=True, type="primary"):
                with st.spinner("📊 Consultando tasas de caución..."):
                    # Simular llamada a la función
                    # tasas_caucion = obtener_tasas_caucion(token_acceso)
                    tasas_caucion = None  # Placeholder
                
                if tasas_caucion:
                    st.success("✅ Tasas actualizadas")
                    
                    # Procesar y mostrar tasas
                    if isinstance(tasas_caucion, list) and tasas_caucion:
                        # Crear DataFrame simulado para demo
                        import random
                        
                        df_tasas_demo = pd.DataFrame({
                            'Símbolo': ['CAUC1', 'CAUC7', 'CAUC30', 'CAUC60', 'CAUC90'],
                            'Plazo': ['1 día', '7 días', '30 días', '60 días', '90 días'],
                            'Tasa (% anual)': [random.uniform(80, 120) for _ in range(5)],
                            'Bid': [random.uniform(75, 85) for _ in range(5)],
                            'Offer': [random.uniform(85, 95) for _ in range(5)]
                        })
                        
                        # Mostrar métricas principales
                        col_t1, col_t2, col_t3 = st.columns(3)
                        
                        with col_t1:
                            tasa_max = df_tasas_demo['Tasa (% anual)'].max()
                            st.markdown(f"""
                            <div class="metric-card">
                                <h4>📈 Tasa Máxima</h4>
                                <h2 style="color: #28a745;">{tasa_max:.2f}%</h2>
                                <p>Anual</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_t2:
                            tasa_min = df_tasas_demo['Tasa (% anual)'].min()
                            st.markdown(f"""
                            <div class="metric-card">
                                <h4>📉 Tasa Mínima</h4>
                                <h2 style="color: #dc3545;">{tasa_min:.2f}%</h2>
                                <p>Anual</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_t3:
                            tasa_promedio = df_tasas_demo['Tasa (% anual)'].mean()
                            st.markdown(f"""
                            <div class="metric-card">
                                <h4>📊 Tasa Promedio</h4>
                                <h2 style="color: #2d5aa0;">{tasa_promedio:.2f}%</h2>
                                <p>Anual</p>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.error("❌ No se pudieron obtener las tasas de caución")
        
        with col2:
            # Gráfico de evolución de tasas (simulado)
            st.markdown("##### 📈 Evolución de Tasas por Plazo")
            
            # Crear gráfico demo
            plazos = ['1 día', '7 días', '30 días', '60 días', '90 días']
            tasas_demo = [85.5, 88.2, 92.1, 95.8, 99.3]
            
            fig_tasas = go.Figure(data=[go.Scatter(
                x=plazos,
                y=tasas_demo,
                mode='lines+markers',
                name='Tasa Anual %',
                line=dict(color='#1f4e79', width=3),
                marker=dict(size=8, color='#ff6b35')
            )])
            
            fig_tasas.update_layout(
                title="Curva de Tasas de Caución",
                xaxis_title="Plazo",
                yaxis_title="Tasa Anual (%)",
                height=300,
                template="plotly_white",
                showlegend=False
            )
            
            st.plotly_chart(fig_tasas, use_container_width=True)
    
    with tab3:
        st.markdown("#### 📊 Panorama General del Mercado")
        
        # Información general del mercado
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🇦🇷 Mercado Argentino")
            
            # Métricas simuladas del mercado
            merval_puntos = 1850000  # Simulado
            merval_variacion = 2.3   # Simulado
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>📈 Merval</h4>
                <h2 style="color: {'#28a745' if merval_variacion > 0 else '#dc3545'};">
                    {merval_puntos:,.0f}
                </h2>
                <p style="color: {'#28a745' if merval_variacion > 0 else '#dc3545'};">
                    {merval_variacion:+.2f}% hoy
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Otros indicadores
            riesgo_pais = 1850  # Simulado
            st.markdown(f"""
            <div class="metric-card">
                <h4>🌍 Riesgo País</h4>
                <h2 style="color: #dc3545;">{riesgo_pais} pb</h2>
                <p>Puntos básicos</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("##### 🌍 Mercados Internacionales")
            
            # Índices internacionales simulados
            sp500 = 4750  # Simulado
            sp500_var = 0.8
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>🇺🇸 S&P 500</h4>
                <h2 style="color: {'#28a745' if sp500_var > 0 else '#dc3545'};">
                    {sp500:,.0f}
                </h2>
                <p style="color: {'#28a745' if sp500_var > 0 else '#dc3545'};">
                    {sp500_var:+.2f}% hoy
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            nasdaq = 15200  # Simulado
            nasdaq_var = 1.2
            st.markdown(f"""
            <div class="metric-card">
                <h4>🇺🇸 Nasdaq</h4>
                <h2 style="color: {'#28a745' if nasdaq_var > 0 else '#dc3545'};">
                    {nasdaq:,.0f}
                </h2>
                <p style="color: {'#28a745' if nasdaq_var > 0 else '#dc3545'};">
                    {nasdaq_var:+.2f}% hoy
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Noticias o alertas del mercado
        st.markdown("##### 📰 Alertas del Mercado")
        
        alertas_mercado = [
            {"tipo": "info", "mensaje": "📊 Mercado operando en rangos normales"},
            {"tipo": "warning", "mensaje": "⚠️ Alta volatilidad en bonos soberanos"},
            {"tipo": "success", "mensaje": "✅ Buena liquidez en el mercado local"}
        ]
        
        for alerta in alertas_mercado:
            color_map = {
                'info': ('#d1ecf1', '#bee5eb'),
                'warning': ('#fff3cd', '#ffeaa7'),
                'success': ('#d4edda', '#c3e6cb')
            }
            bg_color, border_color = color_map[alerta['tipo']]
            
            st.markdown(f"""
            <div style="background: {bg_color}; border: 1px solid {border_color}; 
                        border-radius: 5px; padding: 0.8rem; margin: 0.5rem 0;">
                {alerta['mensaje']}
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    st.title("📊 IOL Portfolio Analyzer")
    st.markdown("Bienvenido al analizador de portafolio de IOL. Ingrese sus credenciales para comenzar.")

    with st.form("login_form"):
        usuario = st.text_input("Usuario IOL", value="", type="default")
        contraseña = st.text_input("Contraseña IOL", value="", type="password")
        submit = st.form_submit_button("Iniciar sesión")

    if submit:
        with st.spinner("Autenticando..."):
            access_token, refresh_token = obtener_tokens(usuario, contraseña)
        if access_token:
            st.success("✅ Autenticación exitosa")
            # Tabs principales
            tab1, tab2, tab3 = st.tabs(["💰 Estado de Cuenta", "📈 Portafolio", "💱 Mercado"])
            with tab1:
                estado_cuenta = obtener_estado_cuenta(access_token)
                mostrar_estado_cuenta(estado_cuenta)
            with tab2:
                clientes = obtener_lista_clientes(access_token)
                if clientes:
                    cliente_sel = st.selectbox("Seleccione cliente", [c.get("nombre", "Sin nombre") for c in clientes])
                    id_cliente = clientes[[c.get("nombre", "Sin nombre") for c in clientes].index(cliente_sel)].get("id")
                else:
                    id_cliente = None
                portafolio = obtener_portafolio(access_token, id_cliente) if id_cliente else None
                if portafolio:
                    mostrar_resumen_portafolio(portafolio)
                else:
                    st.info("No se pudo obtener el portafolio.")
            with tab3:
                mostrar_cotizaciones_mercado(access_token)
        else:
            st.error("No se pudo autenticar. Verifique sus credenciales.")
    else:
        st.info("Ingrese sus credenciales y presione 'Iniciar sesión'.")
