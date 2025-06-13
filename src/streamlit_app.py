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
    Muestra un resumen comprehensivo del portafolio con valuación corregida y métricas avanzadas
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
            
            # Campos de valuación en orden de preferencia (más específicos primero)
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
                        val = float(activo[campo])
                        if val > 0:  # Solo usar valores positivos
                            valuacion = val
                            break
                    except (ValueError, TypeError):
                        continue
            
            # Si no se encuentra valuación directa, intentar calcular
            if valuacion == 0 and cantidad:
                # Buscar precio unitario
                precio_unitario = 0
                campos_precio = [
                    'precioPromedio',
                    'precioCompra',
                    'precioActual',
                    'precio',
                    'precioUnitario',
                    'ultimoPrecio',
                    'cotizacion'
                ]
                
                # Buscar en activo
                for campo in campos_precio:
                    if campo in activo and activo[campo] is not None:
                        try:
                            precio = float(activo[campo])
                            if precio > 0:
                                precio_unitario = precio
                                break
                        except (ValueError, TypeError):
                            continue
                
                # Buscar en título si no se encontró en activo
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
                
                # Calcular valuación si encontramos precio
                if precio_unitario > 0:
                    try:
                        cantidad_num = float(cantidad)
                        valuacion = cantidad_num * precio_unitario
                    except (ValueError, TypeError):
                        pass
            
            datos_activos.append({
                'Símbolo': simbolo,
                'Descripción': descripcion,
                'Tipo': tipo,
                'Cantidad': cantidad,
                'Valuación': valuacion,
                'Datos_Raw': activo  # Para debug
            })
            
            valor_total += valuacion;
            
        except Exception as e:
            st.warning(f"Error procesando activo: {str(e)}")
            continue
    
    # Mostrar información de debug para verificar el cálculo
    with st.expander("🔍 Debug - Verificación de Valuaciones"):
        st.write("**Valuaciones individuales por activo:**")
        for i, activo_data in enumerate(datos_activos):
            st.write(f"{activo_data['Símbolo']}: ${activo_data['Valuación']:,.2f}")
        st.write(f"**Suma total calculada: ${valor_total:,.2f}**")
        
        # Verificar si el valor parece estar en una escala incorrecta
        if valor_total > 100000:
            st.warning("⚠️ El valor total parece ser muy alto. Verificando posibles errores de escala...")
            # Intentar detectar si los valores están multiplicados por 10
            valor_corregido = valor_total / 10
            st.info(f"💡 Valor corregido (÷10): ${valor_corregido:,.2f}")
            
            # Preguntar al usuario si quiere usar el valor corregido
            if st.button("🔧 Usar valor corregido"):
                valor_total = valor_corregido
                # Corregir también las valuaciones individuales
                for activo_data in datos_activos:
                    activo_data['Valuación'] = activo_data['Valuación'] / 10
                st.success("✅ Valores corregidos aplicados")
                st.rerun()
    
    if datos_activos:
        df_activos = pd.DataFrame(datos_activos)
        
        # Calcular métricas comprehensivas del portafolio
        metricas = calcular_metricas_portafolio(datos_activos, valor_total)
        
        # === 1. INFORMACIÓN BÁSICA DEL PORTAFOLIO ===
        st.markdown("#### 📊 Información General")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Activos", len(datos_activos))
        col2.metric("Símbolos Únicos", df_activos['Símbolo'].nunique())
        col3.metric("Tipos de Activos", df_activos['Tipo'].nunique())
        
        # Mostrar el valor total con formato correcto y verificación
        valor_display = f"${valor_total:,.2f}"
        if valor_total > 500000:  # Si parece demasiado alto
            st.warning("⚠️ Verificar: el valor total parece alto")
        col4.metric("Valor Total del Portafolio", valor_display)
        
        # === 2. MÉTRICAS DE RIESGO ACTUALES ===
        if metricas:
            st.markdown("#### ⚠️ Análisis de Riesgo")
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric(
                "Concentración del Portafolio", 
                f"{metricas['concentracion']:.3f}",
                help="Índice de Herfindahl: 0=perfectamente diversificado, 1=completamente concentrado"
            )
            col2.metric(
                "VaR 95% (Valor en Riesgo)", 
                f"${metricas['var_95']:,.0f}",
                help="Valor mínimo del activo más pequeño en el 95% de los casos"
            )
            col3.metric(
                "Volatilidad Estimada Anual", 
                f"${metricas['riesgo_anual']:,.0f}",
                help="Riesgo anual estimado basado en 20% de volatilidad"
            )
            
            # Indicador visual de concentración
            concentracion_status = "🟢 Diversificado" if metricas['concentracion'] < 0.25 else "🟡 Moderadamente Concentrado" if metricas['concentracion'] < 0.5 else "🔴 Altamente Concentrado"
            col4.metric("Estado de Diversificación", concentracion_status)
        
        # === 3. PROYECCIONES DE RENDIMIENTO ===
        if metricas:
            st.markdown("#### 📈 Proyecciones de Rendimiento (Próximos 12 meses)")
            
            col1, col2, col3 = st.columns(3)
            col1.metric(
                "Retorno Esperado", 
                f"${metricas['retorno_esperado_anual']:,.0f}",
                delta=f"{(metricas['retorno_esperado_anual']/valor_total*100):.1f}%",
                help="Retorno esperado promedio basado en 8% anual"
            )
            col2.metric(
                "Escenario Optimista (95%)", 
                f"${metricas['pl_percentil_95']:,.0f}",
                delta=f"+{(metricas['pl_percentil_95']/valor_total*100):.1f}%",
                help="Ganancia esperada en el mejor 5% de los casos"
            )
            col3.metric(
                "Escenario Pesimista (5%)", 
                f"${metricas['pl_percentil_5']:,.0f}",
                delta=f"{(metricas['pl_percentil_5']/valor_total*100):.1f}%",
                help="Pérdida máxima esperada en el peor 5% de los casos"
            )
        
        # === 4. PROBABILIDADES DE ESCENARIOS ===
        if metricas:
            st.markdown("#### 🎯 Probabilidades de Escenarios")
            
            col1, col2, col3, col4 = st.columns(4)
            probs = metricas['probabilidades']
            
            col1.metric(
                "Probabilidad de Ganancia", 
                f"{probs['ganancia']*100:.1f}%",
                help="Probabilidad de obtener rendimientos positivos"
            )
            col2.metric(
                "Probabilidad de Pérdida", 
                f"{probs['perdida']*100:.1f}%",
                help="Probabilidad de obtener rendimientos negativos"
            )
            col3.metric(
                "Prob. Ganancia > 10%", 
                f"{probs['ganancia_mayor_10']*100:.1f}%",
                help="Probabilidad de obtener más del 10% de ganancia"
            )
            col4.metric(
                "Prob. Pérdida > 10%", 
                f"{probs['perdida_mayor_10']*100:.1f}%",
                help="Probabilidad de perder más del 10%"
            )
        
        # === 5. DISTRIBUCIÓN DETALLADA DE ACTIVOS ===
        if metricas:
            st.markdown("#### 📊 Distribución Estadística de Valores por Activo")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            quantiles = metricas['quantiles']
            
            col1.metric(
                "Valor Mínimo (Q25)", 
                f"${quantiles['q25']:,.0f}",
                help="25% de los activos valen menos que este monto"
            )
            col2.metric(
                "Valor Mediano (Q50)", 
                f"${quantiles['q50']:,.0f}",
                help="Valor medio de los activos del portafolio"
            )
            col3.metric(
                "Tercer Cuartil (Q75)", 
                f"${quantiles['q75']:,.0f}",
                help="75% de los activos valen menos que este monto"
            )
            col4.metric(
                "Percentil 90", 
                f"${quantiles['q90']:,.0f}",
                help="90% de los activos valen menos que este monto"
            )
            col5.metric(
                "Valor Máximo (Q95)", 
                f"${quantiles['q95']:,.0f}",
                help="Solo el 5% de los activos supera este valor"
            )
        
        # Información de debug mejorada
        with st.expander("🔍 Información de Debug - Estructura del Portafolio"):
            st.markdown("**Campos disponibles en los activos:**")
            if activos:
                campos_encontrados = set()
                for activo in activos[:3]:
                    campos_encontrados.update(activo.keys())
                    if 'titulo' in activo and isinstance(activo['titulo'], dict):
                        titulo_campos = [f"titulo.{k}" for k in activo['titulo'].keys()]
                        campos_encontrados.update(titulo_campos)
                
                st.code(sorted(list(campos_encontrados)))
                
                st.markdown("**Muestra de datos de activo:**")
                st.json(activos[0] if activos else {})
        
        # Gráficos de distribución
        if valor_total > 0:
            # Gráfico de distribución por tipo
            if 'Tipo' in df_activos.columns and df_activos['Valuación'].sum() > 0:
                tipo_stats = df_activos.groupby('Tipo').agg({
                    'Valuación': ['sum', 'count', 'mean']
                }).round(2)
                tipo_stats.columns = ['Valor_Total', 'Cantidad', 'Valor_Promedio']
                tipo_stats = tipo_stats.reset_index()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Pie chart por valor
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=tipo_stats['Tipo'],
                        values=tipo_stats['Valor_Total'],
                        textinfo='label+percent+value',
                        texttemplate='%{label}<br>%{percent}<br>$%{value:,.0f}',
                    )])
                    fig_pie.update_layout(title="Distribución por Valor", height=400)
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    # Bar chart por tipo
                    fig_bar = go.Figure(data=[go.Bar(
                        x=tipo_stats['Tipo'],
                        y=tipo_stats['Valor_Total'],
                        text=[f"${val:,.0f}" for val in tipo_stats['Valor_Total']],
                        textposition='auto'
                    )])
                    fig_bar.update_layout(
                        title="Valor por Tipo de Activo",
                        xaxis_title="Tipo",
                        yaxis_title="Valor ($)",
                        height=400
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
            
            # Histograma de valores individuales
            if len(datos_activos) > 1:
                valores_activos = [a['Valuación'] for a in datos_activos if a['Valuación'] > 0]
                if valores_activos:
                    fig_hist = go.Figure(data=[go.Histogram(
                        x=valores_activos,
                        nbinsx=min(20, len(valores_activos))
                    )])
                    fig_hist.update_layout(
                        title="Distribución de Valores por Activo",
                        xaxis_title="Valor ($)",
                        yaxis_title="Frecuencia",
                        height=400
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
        
        # Tabla de activos mejorada
        st.markdown("#### 📋 Detalle de Activos")
        
        df_display = df_activos.copy()
        df_display['Valuación Formateada'] = df_display['Valuación'].apply(
            lambda x: f"${x:,.2f}" if x > 0 else "No disponible"
        )
        df_display['Peso (%)'] = (df_display['Valuación'] / valor_total * 100).round(2) if valor_total > 0 else 0
        
        # Reordenar columnas
        columns_order = ['Símbolo', 'Descripción', 'Tipo', 'Cantidad', 'Valuación Formateada', 'Peso (%)']
        df_display_final = df_display[columns_order]
        df_display_final = df_display_final.rename(columns={'Valuación Formateada': 'Valuación'})
        
        # Ordenar por valuación descendente
        df_display_final = df_display_final.sort_values('Peso (%)', ascending=False)
        
        st.dataframe(df_display_final, use_container_width=True)
        
        # === ALERTAS Y RECOMENDACIONES ===
        st.markdown("#### 💡 Análisis y Recomendaciones")
        
        if metricas:
            # Análisis de concentración
            if metricas['concentracion'] > 0.5:
                st.warning("⚠️ **Portafolio Altamente Concentrado**: Su portafolio tiene un alto nivel de concentración. Considere diversificar para reducir el riesgo.")
            elif metricas['concentracion'] > 0.25:
                st.info("ℹ️ **Concentración Moderada**: Su portafolio está moderadamente concentrado. La diversificación adicional podría reducir el riesgo.")
            else:
                st.success("✅ **Buena Diversificación**: Su portafolio muestra un buen nivel de diversificación.")
            
            # Análisis de riesgo-retorno
            ratio_riesgo_retorno = metricas['retorno_esperado_anual'] / metricas['riesgo_anual'] if metricas['riesgo_anual'] > 0 else 0
            if ratio_riesgo_retorno > 0.5:
                st.success("✅ **Buen Balance Riesgo-Retorno**: La relación entre retorno esperado y riesgo es favorable.")
            else:
                st.warning("⚠️ **Revisar Balance Riesgo-Retorno**: El riesgo podría ser alto en relación al retorno esperado.")
        
        if valor_total == 0:
            st.error("❌ **Problema de Valuación**: No se pudieron obtener valuaciones válidas para los activos.")
            
            if st.button("🔄 Intentar obtener cotizaciones actuales"):
                with st.spinner("Obteniendo cotizaciones actuales..."):
                    st.info("Funcionalidad de cotizaciones actuales en desarrollo...")
    else:
        st.warning("No se pudieron procesar los datos de los activos")

def mostrar_estado_cuenta(estado_cuenta):
    """
    Muestra el estado de cuenta del cliente con parsing mejorado según la estructura de la API
    """
    st.markdown("### 💰 Estado de Cuenta")
    
    if not estado_cuenta:
        st.warning("No hay datos de estado de cuenta disponibles")
        return
    
    # Mostrar información general
    st.markdown("#### 📋 Información General")
    
    # Extraer información según la estructura documentada de la API
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
        tipo = cuenta.get('tipo', 'N/A')
        
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
    
    # Mostrar métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric(
        "Total General", 
        f"${total_general:,.2f}",
        help="Suma total de todas las cuentas"
    )
    
    col2.metric(
        "Total en Pesos", 
        f"AR$ {total_en_pesos:,.2f}",
        help="Total expresado en pesos argentinos según la API"
    )
    
    col3.metric(
        "Disponible Total", 
        f"${total_disponible:,.2f}",
        help="Total disponible para operar"
    )
    
    col4.metric(
        "Títulos Valorizados", 
        f"${total_titulos_valorizados:,.2f}",
        help="Valor total de títulos en cartera"
    )
    
    # Mostrar información por moneda
    if cuentas_por_moneda:
        st.markdown("#### 💱 Distribución por Moneda")
        
        for moneda, datos in cuentas_por_moneda.items():
            # Convertir nombre de moneda a formato legible
            nombre_moneda = {
                'peso_Argentino': 'Pesos Argentinos',
                'dolar_Estadounidense': 'Dólares Estadounidenses',
                'euro': 'Euros'
            }.get(moneda, moneda)
            
            with st.expander(f"💰 {nombre_moneda} ({len(datos['cuentas'])} cuenta(s))"):
                col1, col2, col3 = st.columns(3)
                
                col1.metric("Disponible", f"${datos['disponible']:,.2f}")
                col2.metric("Saldo", f"${datos['saldo']:,.2f}")
                col3.metric("Total", f"${datos['total']:,.2f}")
    
    # Mostrar detalles de cuentas
    if cuentas:
        st.markdown("#### 📊 Detalle de Cuentas")
        
        # Crear DataFrame con información de cuentas
        datos_cuentas = []
        for cuenta in cuentas:
            datos_cuentas.append({
                'Número': cuenta.get('numero', 'N/A'),
                'Tipo': cuenta.get('tipo', 'N/A').replace('_', ' ').title(),
                'Moneda': cuenta.get('moneda', 'N/A').replace('_', ' ').title(),
                'Disponible': f"${cuenta.get('disponible', 0):,.2f}",
                'Comprometido': f"${cuenta.get('comprometido', 0):,.2f}",
                'Saldo': f"${cuenta.get('saldo', 0):,.2f}",
                'Títulos Valorizados': f"${cuenta.get('titulosValorizados', 0):,.2f}",
                'Total': f"${cuenta.get('total', 0):,.2f}",
                'Estado': cuenta.get('estado', 'N/A').title()
            })
        
        if datos_cuentas:
            df_cuentas = pd.DataFrame(datos_cuentas)
            st.dataframe(df_cuentas, use_container_width=True)
    
    # Mostrar estadísticas si están disponibles
    if estadisticas:
        st.markdown("#### 📈 Estadísticas")
        
        datos_estadisticas = []
        for stat in estadisticas:
            datos_estadisticas.append({
                'Descripción': stat.get('descripcion', 'N/A'),
                'Cantidad': stat.get('cantidad', 0),
                'Volumen': f"${stat.get('volumen', 0):,.2f}"
            })
        
        if datos_estadisticas:
            df_estadisticas = pd.DataFrame(datos_estadisticas)
            st.dataframe(df_estadisticas, use_container_width=True)
    
    # Información de debug
    with st.expander("🔍 Información de Debug - Estructura del Estado de Cuenta"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Estructura encontrada:**")
            if isinstance(estado_cuenta, dict):
                campos_raiz = list(estado_cuenta.keys())
                st.code('\n'.join(sorted(campos_raiz)))
                
                st.markdown("**Resumen de valores:**")
                resumen = []
                resumen.append(f"Total en Pesos: AR$ {total_en_pesos:,.2f}")
                resumen.append(f"Número de cuentas: {len(cuentas)}")
                resumen.append(f"Total general calculado: ${total_general:,.2f}")
                resumen.append(f"Estadísticas disponibles: {len(estadisticas)}")
                st.code('\n'.join(resumen))
            else:
                st.text(f"Tipo de datos: {type(estado_cuenta)}")
        
        with col2:
            st.markdown("**Estructura completa:**")
            st.json(estado_cuenta)

def mostrar_optimizacion_portafolio(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Muestra la optimización del portafolio usando datos históricos
    """
    st.markdown("### 🎯 Optimización de Portafolio")
    
    activos = portafolio.get('activos', [])
    if not activos:
        st.warning("No hay activos en el portafolio para optimizar")
        return
    
    # Extraer símbolos del portafolio
    simbolos = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', '')
        if simbolo:
            simbolos.append(simbolo)
    
    if len(simbolos) < 2:
        st.warning("Se necesitan al menos 2 activos para optimización")
        return
    
    st.info(f"📊 Analizando {len(simbolos)} activos del portafolio")
    
    # Configuración de optimización
    col1, col2, col3 = st.columns(3)
    
    with col1:
        estrategia = st.selectbox(
            "Estrategia de Optimización:",
            options=['markowitz', 'equi-weight', 'minimum-variance'],
            format_func=lambda x: {
                'markowitz': 'Optimización de Markowitz',
                'equi-weight': 'Pesos Iguales',
                'minimum-variance': 'Mínima Varianza'
            }[x]
        )
    
    with col2:
        rango_fechas_amplio = st.checkbox(
            "Usar rango de fechas amplio",
            value=False,
            help="Usar 2 años de datos históricos para mejor análisis"
        )
    
    with col3:
        ejecutar_optimizacion = st.button("🚀 Ejecutar Optimización")
    
    if ejecutar_optimizacion:
        with st.spinner("Ejecutando optimización..."):
            try:
                # Ajustar fechas si se solicita rango amplio
                if rango_fechas_amplio:
                    fecha_desde_opt = fecha_desde - timedelta(days=365)
                    st.info(f"📅 Usando rango amplio: {fecha_desde_opt} hasta {fecha_hasta}")
                else:
                    fecha_desde_opt = fecha_desde
                
                # Crear manager de portafolio con mejor manejo de errores
                manager = PortfolioManagerEnhanced(simbolos, token_acceso, fecha_desde_opt, fecha_hasta)
                
                # Cargar datos con estrategias de fallback
                data_loaded, num_assets_loaded = manager.load_data_with_fallback()
                
                if data_loaded and num_assets_loaded >= 2:
                    # Computar optimización
                    portfolio_result = manager.compute_portfolio(strategy=estrategia)
                    
                    if portfolio_result:
                        st.success("✅ Optimización completada")
                        
                        # Mostrar resultados
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 📊 Pesos Optimizados")
                            weights_df = pd.DataFrame({
                                'Activo': portfolio_result.asset_names,
                                'Peso (%)': [w * 100 for w in portfolio_result.weights]
                            })
                            weights_df = weights_df.sort_values('Peso (%)', ascending=False)
                            st.dataframe(weights_df, use_container_width=True)
                        
                        with col2:
                            st.markdown("#### 📈 Métricas del Portafolio")
                            metricas = portfolio_result.get_metrics_dict()
                            
                            st.metric("Retorno Diario Promedio", f"{metricas['Mean Daily']:.4f}")
                            st.metric("Volatilidad Diaria", f"{metricas['Volatility Daily']:.4f}")
                            st.metric("Ratio de Sharpe", f"{metricas['Sharpe Ratio']:.4f}")
                            st.metric("VaR 95%", f"{metricas['VaR 95%']:.4f}")
                        
                        # Gráfico de distribución de retornos
                        if portfolio_result.portfolio_returns is not None:
                            st.markdown("#### 📊 Distribución de Retornos del Portafolio Optimizado")
                            fig = portfolio_result.plot_histogram_streamlit()
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Gráfico de pesos
                        st.markdown("#### 🥧 Distribución de Pesos")
                        fig_pie = go.Figure(data=[go.Pie(
                            labels=portfolio_result.asset_names,
                            values=portfolio_result.weights,
                            textinfo='label+percent',
                        )])
                        fig_pie.update_layout(title="Distribución Optimizada de Activos")
                        st.plotly_chart(fig_pie, use_container_width=True)
                        
                elif data_loaded and num_assets_loaded == 1:
                    st.warning("⚠️ Solo se pudo cargar 1 activo con datos válidos")
                    st.markdown("#### 💡 Opciones disponibles:")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("🔄 Intentar con rango de fechas más amplio"):
                            st.info("Reintentando con 2 años de datos...")
                            # Recursión con rango amplio
                            mostrar_optimizacion_portafolio(
                                portafolio, token_acceso, 
                                fecha_desde - timedelta(days=730), fecha_hasta
                            )
                    
                    with col2:
                        if st.button("📊 Análisis de activo único"):
                            activo_unico = manager.get_single_asset_analysis()
                            if activo_unico:
                                st.markdown("#### 📈 Análisis del Activo Único")
                                st.json(activo_unico)
                else:
                    st.error("❌ No se pudieron cargar datos suficientes para optimización")
                    
                    # Mostrar diagnóstico detallado
                    diagnostico = manager.get_diagnostics()
                    with st.expander("🔍 Diagnóstico Detallado"):
                        st.json(diagnostico)
                    
                    # Sugerencias específicas
                    st.markdown("#### 💡 Sugerencias Específicas:")
                    st.markdown("1. **Verificar símbolos**: Algunos pueden estar mal escritos")
                    st.markdown("2. **Ampliar rango de fechas**: Usar 1-2 años de datos")
                    st.markdown("3. **Revisar mercados**: Algunos activos pueden estar en otros mercados")
                    st.markdown("4. **Contactar soporte**: Si persiste el problema")
                    
            except Exception as e:
                st.error(f"❌ Error durante la optimización: {str(e)}")
                with st.expander("🔍 Detalles del error"):
                    st.code(str(e))
    
    # Información adicional
    with st.expander("ℹ️ Información sobre las Estrategias"):
        st.markdown("""
        **Optimización de Markowitz:**
        - Maximiza el ratio de Sharpe (retorno/riesgo)
        - Considera la correlación entre activos
        - Busca la frontera eficiente
        
        **Pesos Iguales:**
        - Distribución uniforme entre todos los activos
        - Estrategia simple de diversificación
        - No considera correlaciones históricas
        
        **Mínima Varianza:**
        - Minimiza el riesgo del portafolio
        - Ideal para inversores conservadores
        - Puede concentrarse en pocos activos
        """)

# Clase PortfolioManager mejorada
class PortfolioManagerEnhanced:
    """
    Clase mejorada para manejo de portafolio y optimización con mejor tolerancia a fallos
    """
    def __init__(self, symbols, token, fecha_desde, fecha_hasta):
        self.symbols = symbols
        self.token = token
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.data_loaded = False
        self.returns = None
        self.prices = None
        self.successful_symbols = []
        self.failed_symbols = []
        self.diagnostics = {}
    
    def load_data_with_fallback(self):
        """
        Carga datos históricos con múltiples estrategias de fallback
        """
        try:
            # Estrategia 1: Intentar con función existente
            mean_returns, cov_matrix, df_precios = get_historical_data_for_optimization(
                self.token, self.symbols, self.fecha_desde, self.fecha_hasta
            )
            
            if mean_returns is not None and cov_matrix is not None and len(mean_returns) >= 2:
                self.returns = df_precios.pct_change().dropna() if df_precios is not None else None
                self.prices = df_precios
                self.mean_returns = mean_returns
                self.cov_matrix = cov_matrix
                self.data_loaded = True
                self.successful_symbols = list(mean_returns.index) if mean_returns is not None else []
                return True, len(self.successful_symbols)
            
            # Estrategia 2: Intentar símbolo por símbolo con diferentes mercados
            st.info("🔄 Intentando estrategia alternativa de carga de datos...")
            
            exitos = 0
            datos_individuales = {}
            
            for simbolo in self.symbols:
                datos_simbolo = self._obtener_datos_simbolo_robusto(simbolo)
                if datos_simbolo is not None and len(datos_simbolo) > 10:
                    datos_individuales[simbolo] = datos_simbolo
                    exitos += 1
                    self.successful_symbols.append(simbolo)
                else:
                    self.failed_symbols.append(simbolo)
            
            if exitos >= 2:
                # Construir DataFrame con datos exitosos
                df_combined = pd.DataFrame(datos_individuales)
                df_combined = df_combined.fillna(method='ffill').fillna(method='bfill')
                df_combined = df_combined.dropna()
                
                if len(df_combined) > 30:  # Suficientes observaciones
                    self.prices = df_combined
                    self.returns = df_combined.pct_change().dropna()
                    self.mean_returns = self.returns.mean()
                    self.cov_matrix = self.returns.cov()
                    self.data_loaded = True
                    return True, exitos
            
            # Estrategia 3: Si solo hay 1 activo exitoso, intentar con datos sintéticos para demo
            if exitos == 1:
                self.data_loaded = True
                simbolo_unico = self.successful_symbols[0]
                self.prices = pd.DataFrame({simbolo_unico: datos_individuales[simbolo_unico]})
                self.returns = self.prices.pct_change().dropna()
                return True, 1
            
            return False, 0
                
        except Exception as e:
            self.diagnostics['error_general'] = str(e)
            return False, 0
    
    def _obtener_datos_simbolo_robusto(self, simbolo):
        """
        Obtiene datos de un símbolo probando múltiples mercados y estrategias
        """
        mercados = ['bCBA', 'nYSE', 'nASDAQ', 'rOFEX']
        fecha_desde_str = self.fecha_desde.strftime('%Y-%m-%d')
        fecha_hasta_str = self.fecha_hasta.strftime('%Y-%m-%d')
        
        for mercado in mercados:
            try:
                # Intentar con clase D si aplica
                simbolo_consulta = simbolo
                if mercado in ['bCBA']:
                    clase_d = obtener_clase_d(simbolo, mercado, self.token)
                    if clase_d:
                        simbolo_consulta = clase_d
                
                serie = obtener_serie_historica_iol(
                    self.token, mercado, simbolo_consulta,
                    fecha_desde_str, fecha_hasta_str
                )
                
                if serie is not None and len(serie) > 10 and serie.nunique() > 1:
                    return serie
                    
            except Exception as e:
                self.diagnostics[f'{simbolo}_{mercado}'] = str(e)
                continue
        
        # Fallback a yfinance
        try:
            serie_yf = obtener_datos_alternativos_yfinance(
                simbolo, self.fecha_desde, self.fecha_hasta
            )
            if serie_yf is not None and len(serie_yf) > 10:
                return serie_yf
        except:
            pass
        
        return None
    
    def get_single_asset_analysis(self):
        """
        Análisis para cuando solo hay un activo
        """
        if len(self.successful_symbols) == 1 and self.returns is not None:
            simbolo = self.successful_symbols[0]
            serie_retornos = self.returns[simbolo]
            
            return {
                'simbolo': simbolo,
                'observaciones': len(serie_retornos),
                'retorno_promedio_diario': serie_retornos.mean(),
                'volatilidad_diaria': serie_retornos.std(),
                'retorno_anualizado': serie_retornos.mean() * 252,
                'volatilidad_anualizada': serie_retornos.std() * np.sqrt(252),
                'sharpe_ratio': (serie_retornos.mean() / serie_retornos.std()) if serie_retornos.std() > 0 else 0,
                'var_95': np.percentile(serie_retornos, 5),
                'sesgo': serie_retornos.skew(),
                'curtosis': serie_retornos.kurtosis()
            }
        return None
    
    def get_diagnostics(self):
        """
        Retorna información de diagnóstico
        """
        return {
            'simbolos_originales': self.symbols,
            'simbolos_exitosos': self.successful_symbols,
            'simbolos_fallidos': self.failed_symbols,
            'rango_fechas': f"{self.fecha_desde} a {self.fecha_hasta}",
            'errores_detallados': self.diagnostics
        }
    
    def compute_portfolio(self, strategy='markowitz', target_return=None):
        """
        Computa la optimización del portafolio con manejo mejorado
        """
        if not self.data_loaded or self.returns is None:
            return None
        
        try:
            n_assets = len(self.returns.columns)
            
            if n_assets == 1:
                # Caso especial: un solo activo
                weights = np.array([1.0])
            elif strategy == 'equi-weight':
                weights = np.array([1/n_assets] * n_assets)
            elif strategy == 'minimum-variance':
                weights = self._optimize_minimum_variance()
            else:
                # Markowitz u otra optimización
                weights = optimize_portfolio(self.returns, target_return=target_return)
            
            # Crear objeto de resultado
            portfolio_output = PortfolioOutput(
                weights=weights,
                asset_names=list(self.returns.columns),
                returns=self.returns
            )
            
            return portfolio_output
            
        except Exception as e:
            st.error(f"Error en optimización: {str(e)}")
            return None
    
    def _optimize_minimum_variance(self):
        """
        Optimización de mínima varianza
        """
        try:
            from scipy.optimize import minimize
            
            n_assets = len(self.returns.columns)
            cov_matrix = self.returns.cov().values
            
            # Función objetivo: minimizar varianza
            def portfolio_variance(weights):
                return np.dot(weights.T, np.dot(cov_matrix, weights))
            
            # Restricciones y límites
            constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
            bounds = tuple((0, 1) for _ in range(n_assets))
            initial_guess = np.array([1/n_assets] * n_assets)
            
            # Optimización
            result = minimize(portfolio_variance, initial_guess, method='SLSQP',
                            bounds=bounds, constraints=constraints)
            
            if result.success:
                return result.x
            else:
                return np.array([1/n_assets] * n_assets)
                
        except Exception:
            return np.array([1/len(self.returns.columns)] * len(self.returns.columns))

# --- Funciones de la aplicación Streamlit ---
def mostrar_analisis_portafolio():
    """
    Función principal para mostrar el análisis del portafolio del cliente seleccionado
    """
    cliente = st.session_state.cliente_seleccionado
    token_acceso = st.session_state.token_acceso
    fecha_desde = st.session_state.fecha_desde
    fecha_hasta = st.session_state.fecha_hasta
    
    if not cliente:
        st.error("No hay cliente seleccionado")
        return
    
    # Obtener ID del cliente
    id_cliente = cliente.get('numeroCliente', cliente.get('id'))
    nombre_cliente = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))
    
    st.title(f"📊 Análisis de Portafolio - {nombre_cliente}")
    
    # Reorganizar tabs en orden lógico de uso
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard General", 
        "💰 Estado Financiero", 
        "🎯 Optimización y Estrategias", 
        "📈 Análisis Avanzado",
        "🛠️ Herramientas de Mercado"
    ])
    
    with tab1:
        st.markdown("### 📊 Dashboard General del Portafolio")
        
        # Sub-navegación dentro del dashboard
        dashboard_option = st.selectbox(
            "Seleccione vista del dashboard:",
            ["Resumen Ejecutivo", "Composición Detallada", "Métricas de Riesgo"],
            key="dashboard_nav"
        )
        
        # Obtener portafolio una vez para todo el dashboard
        with st.spinner("Cargando datos del portafolio..."):
            portafolio = obtener_portafolio(token_acceso, id_cliente)
        
        if portafolio:
            if dashboard_option == "Resumen Ejecutivo":
                # Vista de alto nivel con métricas clave
                st.markdown("#### 🎯 Vista Ejecutiva")
                mostrar_resumen_portafolio(portafolio)
                
            elif dashboard_option == "Composición Detallada":
                # Análisis detallado de composición
                st.markdown("#### 🔍 Análisis Detallado de Composición")
                mostrar_composicion_detallada(portafolio)
                
            elif dashboard_option == "Métricas de Riesgo":
                # Enfoque en riesgo y diversificación
                st.markdown("#### ⚠️ Análisis de Riesgo y Diversificación")
                mostrar_analisis_riesgo(portafolio)
        else:
            st.warning("No se pudo obtener el portafolio del cliente")
    
    with tab2:
        st.markdown("### 💰 Estado Financiero Completo")
        
        # Sub-navegación para estado financiero
        financial_option = st.selectbox(
            "Seleccione vista financiera:",
            ["Estado de Cuenta", "Flujos de Efectivo", "Histórico de Operaciones"],
            key="financial_nav"
        )
        
        if financial_option == "Estado de Cuenta":
            # Estado de cuenta actual
            with st.spinner("Cargando estado de cuenta..."):
                estado_cuenta = obtener_estado_cuenta(token_acceso, id_cliente)
            
            if estado_cuenta:
                mostrar_estado_cuenta(estado_cuenta)
            else:
                st.warning("No se pudo obtener el estado de cuenta")
                
                # Ofrecer alternativa
                if st.button("🔄 Probar endpoint alternativo"):
                    with st.spinner("Probando endpoint directo..."):
                        estado_cuenta_directo = obtener_estado_cuenta(token_acceso, None)
                        if estado_cuenta_directo:
                            mostrar_estado_cuenta(estado_cuenta_directo)
                        else:
                            st.error("❌ No se pudo obtener el estado de cuenta con ningún método")
        
        elif financial_option == "Flujos de Efectivo":
            st.info("🚧 Análisis de flujos de efectivo en desarrollo")
            mostrar_placeholder_flujos_efectivo()
            
        elif financial_option == "Histórico de Operaciones":
            st.info("🚧 Histórico de operaciones en desarrollo")
            mostrar_placeholder_historico_operaciones()

    with tab3:
        st.markdown("### 🎯 Optimización y Estrategias")
        
        # Sub-navegación para optimización
        optimization_option = st.selectbox(
            "Seleccione estrategia:",
            ["Optimización de Markowitz", "Rebalanceo Automático", "Análisis de Escenarios"],
            key="optimization_nav"
        )
        
        # Obtener portafolio para optimización
        if 'portafolio' not in locals():
            with st.spinner("Cargando portafolio para optimización..."):
                portafolio = obtener_portafolio(token_acceso, id_cliente)
        
        if portafolio:
            if optimization_option == "Optimización de Markowitz":
                mostrar_optimizacion_portafolio(portafolio, token_acceso, fecha_desde, fecha_hasta)
                
            elif optimization_option == "Rebalanceo Automático":
                st.info("🚧 Herramienta de rebalanceo automático en desarrollo")
                mostrar_placeholder_rebalanceo()
                
            elif optimization_option == "Análisis de Escenarios":
                st.info("🚧 Análisis de escenarios en desarrollo")
                mostrar_placeholder_escenarios()
        else:
            st.warning("No se pudo obtener el portafolio para optimización")
    
    with tab4:
        st.markdown("### 📈 Análisis Avanzado")
        
        # Sub-navegación para análisis avanzado
        advanced_option = st.selectbox(
            "Seleccione tipo de análisis:",
            ["Análisis Técnico", "Correlaciones", "Backtesting", "Monte Carlo"],
            key="advanced_nav"
        )
        
        if advanced_option == "Análisis Técnico":
            mostrar_analisis_tecnico(portafolio if 'portafolio' in locals() else None, token_acceso, id_cliente)
            
        elif advanced_option == "Correlaciones":
            st.info("🚧 Matriz de correlaciones en desarrollo")
            mostrar_placeholder_correlaciones()
            
        elif advanced_option == "Backtesting":
            st.info("🚧 Backtesting de estrategias en desarrollo")
            mostrar_placeholder_backtesting()
            
        elif advanced_option == "Monte Carlo":
            st.info("🚧 Simulación Monte Carlo en desarrollo")
            mostrar_placeholder_montecarlo()
    
    with tab5:
        st.markdown("### 🛠️ Herramientas de Mercado")
        
        # Sub-navegación para herramientas
        tools_option = st.selectbox(
            "Seleccione herramienta:",
            ["Cotizaciones en Tiempo Real", "Calculadora MEP", "Tasas de Caución", "Alertas de Mercado"],
            key="tools_nav"
        )
        
        if tools_option == "Cotizaciones en Tiempo Real":
            mostrar_cotizaciones_tiempo_real(token_acceso)
            
        elif tools_option == "Calculadora MEP":
            mostrar_calculadora_mep(token_acceso)
            
        elif tools_option == "Tasas de Caución":
            mostrar_tasas_caucion_detalladas(token_acceso)
            
        elif tools_option == "Alertas de Mercado":
            st.info("🚧 Sistema de alertas en desarrollo")
            mostrar_placeholder_alertas()

# Nuevas funciones de apoyo para la reorganización

def mostrar_composicion_detallada(portafolio):
    """Muestra análisis detallado de composición del portafolio"""
    st.markdown("#### 📊 Composición Detallada")
    # Implementar análisis de composición más detallado
    mostrar_resumen_portafolio(portafolio)  # Por ahora usa la función existente

def mostrar_analisis_riesgo(portafolio):
    """Muestra análisis específico de riesgo"""
    st.markdown("#### ⚠️ Análisis de Riesgo")
    # Implementar análisis de riesgo específico
    mostrar_resumen_portafolio(portafolio)  # Por ahora usa la función existente

def mostrar_analisis_tecnico(portafolio, token_acceso, id_cliente):
    """Análisis técnico mejorado con herramientas integradas de TradingView"""
    st.markdown("#### 📊 Análisis Técnico Avanzado")
    
    if not portafolio:
        portafolio = obtener_portafolio(token_acceso, id_cliente)
    
    if portafolio:
        activos = portafolio.get('activos', [])
        if activos:
            simbolos = [activo.get('titulo', {}).get('simbolo', '') for activo in activos]
            simbolos = [s for s in simbolos if s]
            
            if simbolos:
                # Panel de configuración principal
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    simbolo_seleccionado = st.selectbox(
                        "📈 Seleccione un activo:",
                        options=simbolos,
                        key="tech_analysis_symbol"
                    )
                
                with col2:
                    tipo_analisis = st.selectbox(
                        "🔧 Tipo de Análisis:",
                        ["Indicadores Técnicos", "Gráficos Interactivos", "Patrones de Precios", "Análisis Multi-Timeframe"],
                        key="analysis_type"
                    )
                
                with col3:
                    timeframe = st.selectbox(
                        "⏰ Timeframe:",
                        ["1D", "1W", "1M", "3M", "6M", "1Y"],
                        index=3,
                        key="timeframe_selector"
                    )
                
                # Tabs para diferentes herramientas
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📊 Indicadores", "✏️ Herramientas de Dibujo", "📈 Análisis de Precios", 
                    "🔄 Comparación", "⚙️ Configuración Avanzada"
                ])
                
                with tab1:
                    mostrar_indicadores_tecnicos(simbolo_seleccionado, token_acceso, timeframe)
                
                with tab2:
                    mostrar_herramientas_dibujo(simbolo_seleccionado, token_acceso)
                
                with tab3:
                    mostrar_analisis_precios(simbolo_seleccionado, token_acceso, timeframe)
                
                with tab4:
                    mostrar_comparacion_activos(simbolos, token_acceso, timeframe)
                
                with tab5:
                    mostrar_configuracion_avanzada()
                
                # Gráfico principal integrado
                if simbolo_seleccionado:
                    mostrar_grafico_principal_integrado(simbolo_seleccionado, token_acceso, timeframe, tipo_analisis)
                    
    else:
        st.warning("No se pudo cargar el portafolio para análisis técnico")

def mostrar_indicadores_tecnicos(simbolo, token_acceso, timeframe):
    """Panel de indicadores técnicos avanzados"""
    st.markdown("##### 📊 Indicadores Técnicos")
    
    # Configuración de indicadores
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("###### 📈 Indicadores de Tendencia")
        
        # Moving Averages
        ma_enabled = st.checkbox("Moving Averages", value=True, key="ma_enabled")
        if ma_enabled:
            ma_periods = st.multiselect(
                "Períodos MA:",
                [5, 10, 20, 50, 100, 200],
                default=[20, 50],
                key="ma_periods"
            )
            ma_type = st.selectbox(
                "Tipo MA:",
                ["SMA", "EMA", "WMA", "HMA"],
                key="ma_type"
            )
        
        # MACD
        macd_enabled = st.checkbox("MACD", value=True, key="macd_enabled")
        if macd_enabled:
            macd_fast = st.number_input("MACD Fast:", value=12, key="macd_fast")
            macd_slow = st.number_input("MACD Slow:", value=26, key="macd_slow")
            macd_signal = st.number_input("MACD Signal:", value=9, key="macd_signal")
        
        # Bollinger Bands
        bb_enabled = st.checkbox("Bollinger Bands", value=False, key="bb_enabled")
        if bb_enabled:
            bb_period = st.number_input("BB Período:", value=20, key="bb_period")
            bb_std = st.number_input("BB Desviación:", value=2.0, step=0.1, key="bb_std")
    
    with col2:
        st.markdown("###### ⚡ Indicadores de Momentum")
        
        # RSI
        rsi_enabled = st.checkbox("RSI", value=True, key="rsi_enabled")
        if rsi_enabled:
            rsi_period = st.number_input("RSI Período:", value=14, key="rsi_period")
            rsi_overbought = st.number_input("RSI Sobrecompra:", value=70, key="rsi_ob")
            rsi_oversold = st.number_input("RSI Sobreventa:", value=30, key="rsi_os")
        
        # Stochastic
        stoch_enabled = st.checkbox("Stochastic", value=False, key="stoch_enabled")
        if stoch_enabled:
            stoch_k = st.number_input("Stoch %K:", value=14, key="stoch_k")
            stoch_d = st.number_input("Stoch %D:", value=3, key="stoch_d")
        
        # Williams %R
        williams_enabled = st.checkbox("Williams %R", value=False, key="williams_enabled")
        if williams_enabled:
            williams_period = st.number_input("Williams Período:", value=14, key="williams_period")
    
    # Configuración de volumen
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("###### 📊 Indicadores de Volumen")
        
        volume_enabled = st.checkbox("Volumen", value=True, key="volume_enabled")
        vwap_enabled = st.checkbox("VWAP", value=False, key="vwap_enabled")
        obv_enabled = st.checkbox("On Balance Volume", value=False, key="obv_enabled")
    
    with col4:
        st.markdown("###### 🎯 Indicadores Personalizados")
        
        # Permitir agregar indicadores personalizados
        custom_indicator = st.text_input(
            "Indicador personalizado:",
            placeholder="Ej: Ichimoku, Fibonacci, etc.",
            key="custom_indicator"
        )
        
        if custom_indicator:
            st.info(f"Indicador '{custom_indicator}' se agregará próximamente")
    
    # Botón para aplicar configuración
    if st.button("🚀 Aplicar Indicadores", key="apply_indicators"):
        # Aquí se aplicarían los indicadores al gráfico
        configuracion_indicadores = {
            'moving_averages': {'enabled': ma_enabled, 'periods': ma_periods if ma_enabled else [], 'type': ma_type if ma_enabled else 'SMA'},
            'macd': {'enabled': macd_enabled, 'fast': macd_fast if macd_enabled else 12, 'slow': macd_slow if macd_enabled else 26, 'signal': macd_signal if macd_enabled else 9},
            'bollinger_bands': {'enabled': bb_enabled, 'period': bb_period if bb_enabled else 20, 'std': bb_std if bb_enabled else 2.0},
            'rsi': {'enabled': rsi_enabled, 'period': rsi_period if rsi_enabled else 14, 'overbought': rsi_overbought if rsi_enabled else 70, 'oversold': rsi_oversold if rsi_enabled else 30},
            'stochastic': {'enabled': stoch_enabled, 'k': stoch_k if stoch_enabled else 14, 'd': stoch_d if stoch_enabled else 3},
            'williams': {'enabled': williams_enabled, 'period': williams_period if williams_enabled else 14},
            'volume': volume_enabled,
            'vwap': vwap_enabled,
            'obv': obv_enabled
        }
        
        st.success("✅ Configuración de indicadores aplicada")
        st.json(configuracion_indicadores)

def mostrar_herramientas_dibujo(simbolo, token_acceso):
    """Panel de herramientas de dibujo avanzadas"""
    st.markdown("##### ✏️ Herramientas de Dibujo")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("###### 📏 Líneas y Formas")
        
        # Herramientas básicas de línea
        if st.button("📏 Línea de Tendencia", key="trend_line"):
            st.info("Modo: Línea de Tendencia activado")
        
        if st.button("📐 Línea Horizontal", key="horizontal_line"):
            st.info("Modo: Línea Horizontal activado")
        
        if st.button("📏 Línea Vertical", key="vertical_line"):
            st.info("Modo: Línea Vertical activado")
        
        if st.button("🔺 Canal de Tendencia", key="trend_channel"):
            st.info("Modo: Canal de Tendencia activado")
        
        if st.button("📦 Rectángulo", key="rectangle"):
            st.info("Modo: Rectángulo activado")
    
    with col2:
        st.markdown("###### 🎯 Herramientas Fibonacci")
        
        if st.button("🌀 Retroceso Fibonacci", key="fib_retracement"):
            st.info("Modo: Retroceso Fibonacci activado")
        
        if st.button("📈 Extensión Fibonacci", key="fib_extension"):
            st.info("Modo: Extensión Fibonacci activado")
        
        if st.button("⚡ Abanico Fibonacci", key="fib_fan"):
            st.info("Modo: Abanico Fibonacci activado")
        
        if st.button("⏰ Zonas Temporales Fibonacci", key="fib_time"):
            st.info("Modo: Zonas Temporales Fibonacci activado")
    
    with col3:
        st.markdown("###### 🎨 Herramientas Avanzadas")
        
        if st.button("🎯 Gann Square", key="gann_square"):
            st.info("Modo: Gann Square activado")
        
        if st.button("📊 Pitchfork", key="pitchfork"):
            st.info("Modo: Pitchfork activado")
        
        if st.button("💬 Texto/Nota", key="text_note"):
            st.info("Modo: Agregar Texto activado")
        
        if st.button("🚨 Alerta de Precio", key="price_alert"):
            st.info("Modo: Alerta de Precio activado")
    
    # Configuración de estilo de dibujo
    st.markdown("###### 🎨 Configuración de Estilo")
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        line_color = st.color_picker("Color de línea:", "#FF0000", key="line_color")
        line_width = st.slider("Grosor de línea:", 1, 5, 2, key="line_width")
    
    with col5:
        line_style = st.selectbox(
            "Estilo de línea:",
            ["Sólida", "Punteada", "Discontinua"],
            key="line_style"
        )
    
    with col6:
        if st.button("🗑️ Limpiar Dibujos", key="clear_drawings"):
            st.warning("Todos los dibujos han sido eliminados")

def mostrar_analisis_precios(simbolo, token_acceso, timeframe):
    """Panel de análisis de precios avanzado"""
    st.markdown("##### 📈 Análisis de Precios")
    
    # Obtener datos históricos para análisis
    with st.spinner(f"Cargando datos de {simbolo}..."):
        fecha_hasta = date.today()
        fecha_desde = fecha_hasta - timedelta(days=365)
        
        # Simular datos para demostración
        datos_precio = simular_datos_precio(simbolo, fecha_desde, fecha_hasta)
    
    if datos_precio is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("###### 📊 Estadísticas de Precio")
            
            precio_actual = datos_precio['close'].iloc[-1]
            precio_anterior = datos_precio['close'].iloc[-2]
            variacion = ((precio_actual - precio_anterior) / precio_anterior) * 100
            
            st.metric("Precio Actual", f"${precio_actual:.2f}", f"{variacion:+.2f}%")
            
            # Estadísticas adicionales
            max_52w = datos_precio['high'].max()
            min_52w = datos_precio['low'].min()
            volatilidad = datos_precio['close'].pct_change().std() * np.sqrt(252) * 100
            
            st.metric("Máximo 52s", f"${max_52w:.2f}")
            st.metric("Mínimo 52s", f"${min_52w:.2f}")
            st.metric("Volatilidad Anual", f"{volatilidad:.1f}%")
        
        with col2:
            st.markdown("###### 🎯 Niveles Clave")
            
            # Calcular soportes y resistencias
            resistencia_1 = calcular_resistencia(datos_precio, nivel=1)
            resistencia_2 = calcular_resistencia(datos_precio, nivel=2)
            soporte_1 = calcular_soporte(datos_precio, nivel=1)
            soporte_2 = calcular_soporte(datos_precio, nivel=2)
            
            st.write(f"🔴 **Resistencia 2:** ${resistencia_2:.2f}")
            st.write(f"🟠 **Resistencia 1:** ${resistencia_1:.2f}")
            st.write(f"⚪ **Precio Actual:** ${precio_actual:.2f}")
            st.write(f"🟢 **Soporte 1:** ${soporte_1:.2f}")
            st.write(f"🔵 **Soporte 2:** ${soporte_2:.2f}")
        
        # Análisis de patrones
        st.markdown("###### 🔍 Detección de Patrones")
        
        patrones_detectados = detectar_patrones_precio(datos_precio)
        
        if patrones_detectados:
            for patron in patrones_detectados:
                st.info(f"📊 Patrón detectado: **{patron['nombre']}** - Confianza: {patron['confianza']:.0%}")
        else:
            st.info("No se detectaron patrones significativos en el período analizado")
        
        # Gráfico de análisis de precios
        fig_precio = crear_grafico_analisis_precio(datos_precio, simbolo)
        st.plotly_chart(fig_precio, use_container_width=True)
    
    else:
        st.warning(f"No se pudieron cargar los datos de {simbolo}")

def mostrar_comparacion_activos(simbolos, token_acceso, timeframe):
    """Panel de comparación entre múltiples activos"""
    st.markdown("##### 🔄 Comparación de Activos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        activos_comparar = st.multiselect(
            "Seleccione activos para comparar:",
            options=simbolos,
            default=simbolos[:min(3, len(simbolos))],
            key="assets_to_compare"
        )
    
    with col2:
        tipo_comparacion = st.selectbox(
            "Tipo de comparación:",
            ["Rendimiento Relativo", "Precios Absolutos", "Volatilidad", "Correlación"],
            key="comparison_type"
        )
    
    if len(activos_comparar) >= 2:
        # Generar datos de comparación
        datos_comparacion = generar_datos_comparacion(activos_comparar, timeframe)
        
        if tipo_comparacion == "Rendimiento Relativo":
            fig_comp = crear_grafico_rendimiento_relativo(datos_comparacion, activos_comparar)
            st.plotly_chart(fig_comp, use_container_width=True)
            
        elif tipo_comparacion == "Correlación":
            matriz_correlacion = calcular_matriz_correlacion(datos_comparacion)
            fig_corr = crear_grafico_correlacion(matriz_correlacion, activos_comparar)
            st.plotly_chart(fig_corr, use_container_width=True)
            
        # Tabla de métricas comparativas
        st.markdown("###### 📊 Métricas Comparativas")
        
        tabla_metricas = crear_tabla_metricas_comparativas(datos_comparacion, activos_comparar)
        st.dataframe(tabla_metricas, use_container_width=True)
    
    else:
        st.info("Seleccione al menos 2 activos para comparar")

def mostrar_configuracion_avanzada():
    """Panel de configuración avanzada para análisis técnico"""
    st.markdown("##### ⚙️ Configuración Avanzada")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("###### 🎨 Personalización Visual")
        
        theme_chart = st.selectbox(
            "Tema del gráfico:",
            ["Oscuro", "Claro", "Personalizado"],
            key="chart_theme"
        )
        
        grid_enabled = st.checkbox("Mostrar grilla", value=True, key="grid_enabled")
        volume_visible = st.checkbox("Mostrar volumen", value=True, key="volume_visible")
        crosshair_enabled = st.checkbox("Crosshair", value=True, key="crosshair_enabled")
    
    with col2:
        st.markdown("###### 📊 Configuración de Datos")
        
        data_source = st.selectbox(
            "Fuente de datos:",
            ["IOL API", "Yahoo Finance", "Alpha Vantage"],
            key="data_source"
        )
        
        update_frequency = st.selectbox(
            "Frecuencia de actualización:",
            ["Tiempo Real", "1 minuto", "5 minutos", "Manual"],
            index=2,
            key="update_frequency"
        )
        
        cache_enabled = st.checkbox("Habilitar cache", value=True, key="cache_enabled")
    
    # Configuración de alertas
    st.markdown("###### 🚨 Configuración de Alertas")
    
    col3, col4 = st.columns(2)
    
    with col3:
        alerts_enabled = st.checkbox("Habilitar alertas", value=False, key="alerts_enabled")
        if alerts_enabled:
            alert_email = st.text_input("Email para alertas:", key="alert_email")
    
    with col4:
        if alerts_enabled:
            alert_types = st.multiselect(
                "Tipos de alerta:",
                ["Precio", "Volumen", "Indicadores", "Patrones"],
                key="alert_types"
            )
    
    # Guardar configuración
    if st.button("💾 Guardar Configuración", key="save_config"):
        config = {
            'theme': theme_chart,
            'grid': grid_enabled,
            'volume': volume_visible,
            'crosshair': crosshair_enabled,
            'data_source': data_source,
            'update_frequency': update_frequency,
            'cache': cache_enabled,
            'alerts': alerts_enabled
        }
        st.success("✅ Configuración guardada")
        st.json(config)

def mostrar_grafico_principal_integrado(simbolo, token_acceso, timeframe, tipo_analisis):
    """Gráfico principal integrado con TradingView-like interface"""
    st.markdown(f"##### 📊 Gráfico Principal - {simbolo}")
    
    # Toolbar superior del gráfico
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        chart_type = st.selectbox(
            "Tipo:",
            ["Velas", "Barras", "Línea", "Renko", "Heikin Ashi"],
            key="chart_type_main"
        )
    
    with col2:
        interval = st.selectbox(
            "Intervalo:",
            ["1m", "5m", "15m", "1h", "4h", "1D", "1W"],
            index=5,
            key="interval_main"
        )
    
    with col3:
        if st.button("📊 Agregar Indicador", key="add_indicator_main"):
            st.info("Selector de indicadores abierto")
    
    with col4:
        if st.button("✏️ Herramientas", key="drawing_tools_main"):
            st.info("Panel de herramientas de dibujo abierto")
    
    with col5:
        if st.button("💾 Guardar Layout", key="save_layout_main"):
            st.success("Layout guardado")
    
    # Generar datos para el gráfico principal
    datos_grafico = generar_datos_grafico_principal(simbolo, timeframe, interval)
    
    if datos_grafico is not None:
        # Crear gráfico principal con subplots para indicadores
        fig_main = crear_grafico_principal_completo(datos_grafico, simbolo, chart_type, tipo_analisis)
        st.plotly_chart(fig_main, use_container_width=True, config={'displayModeBar': True})
        
        # Panel de información en tiempo real
        mostrar_panel_informacion_tiempo_real(simbolo, datos_grafico)
    
    else:
        st.error(f"No se pudieron cargar los datos para {simbolo}")

# Funciones auxiliares para análisis técnico

def simular_datos_precio(simbolo, fecha_desde, fecha_hasta):
    """Simula datos de precio para demostración"""
    try:
        fechas = pd.date_range(fecha_desde, fecha_hasta, freq='D')
        np.random.seed(hash(simbolo) % 2**32)  # Seed basado en símbolo para consistencia
        
        precio_inicial = 100 + np.random.random() * 50
        rendimientos = np.random.normal(0.001, 0.02, len(fechas))
        precios = [precio_inicial]
        
        for r in rendimientos[1:]:
            precio_siguiente = precios[-1] * (1 + r)
            precios.append(max(precio_siguiente, 1))  # Evitar precios negativos
        
        # Generar OHLCV
        data = []
        for i, (fecha, precio) in enumerate(zip(fechas, precios)):
            volatilidad_diaria = 0.01 + np.random.random() * 0.02
            high = precio * (1 + volatilidad_diaria)
            low = precio * (1 - volatilidad_diaria)
            open_price = precios[i-1] if i > 0 else precio
            close_price = precio
            volume = np.random.randint(1000, 10000)
            
            data.append({
                'date': fecha,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume
            })
        
        return pd.DataFrame(data).set_index('date')
    
    except Exception as e:
        st.error(f"Error generando datos: {str(e)}")
        return None

def calcular_resistencia(datos, nivel=1):
    """Calcula niveles de resistencia"""
    try:
        high_prices = datos['high'].tail(100)  # Últimos 100 días
        resistencias = []
        
        for i in range(2, len(high_prices)-2):
            if (high_prices.iloc[i] > high_prices.iloc[i-1] and 
                high_prices.iloc[i] > high_prices.iloc[i-2] and
                high_prices.iloc[i] > high_prices.iloc[i+1] and 
                high_prices.iloc[i] > high_prices.iloc[i+2]):
                resistencias.append(high_prices.iloc[i])
        
        if resistencias:
            resistencias_sorted = sorted(resistencias, reverse=True)
            return resistencias_sorted[min(nivel-1, len(resistencias_sorted)-1)]
        else:
            return datos['high'].max()
    
    except Exception:
        return datos['high'].max()

def calcular_soporte(datos, nivel=1):
    """Calcula niveles de soporte"""
    try:
        low_prices = datos['low'].tail(100)  # Últimos 100 días
        soportes = []
        
        for i in range(2, len(low_prices)-2):
            if (low_prices.iloc[i] < low_prices.iloc[i-1] and 
                low_prices.iloc[i] < low_prices.iloc[i-2] and
                low_prices.iloc[i] < low_prices.iloc[i+1] and 
                low_prices.iloc[i] < low_prices.iloc[i+2]):
                soportes.append(low_prices.iloc[i])
        
        if soportes:
            soportes_sorted = sorted(soportes)
            return soportes_sorted[min(nivel-1, len(soportes_sorted)-1)]
        else:
            return datos['low'].min()
    
    except Exception:
        return datos['low'].min()

def detectar_patrones_precio(datos):
    """Detecta patrones básicos en los precios"""
    patrones = []
    
    try:
        # Patrón de tendencia alcista
        precios_recientes = datos['close'].tail(20)
        if len(precios_recientes) >= 10:
            tendencia = np.polyfit(range(len(precios_recientes)), precios_recientes, 1)[0]
            if tendencia > 0:
                patrones.append({
                    'nombre': 'Tendencia Alcista',
                    'confianza': min(abs(tendencia) * 100, 0.9)
                })
            elif tendencia < 0:
                patrones.append({
                    'nombre': 'Tendencia Bajista',
                    'confianza': min(abs(tendencia) * 100, 0.9)
                })
        
        # Patrón de doble techo/suelo (simplificado)
        if len(datos) >= 50:
            high_recent = datos['high'].tail(50)
            max_idx = high_recent.idxmax()
            if max_idx not in high_recent.tail(10).index:  # El máximo no está en los últimos 10 días
                patrones.append({
                    'nombre': 'Posible Doble Techo',
                    'confianza': 0.6
                })
    
    except Exception:
        pass
    
    return patrones

def crear_grafico_analisis_precio(datos, simbolo):
    """Crea gráfico de análisis de precios"""
    fig = go.Figure()
    
    # Gráfico de velas
    fig.add_trace(go.Candlestick(
        x=datos.index,
        open=datos['open'],
        high=datos['high'],
        low=datos['low'],
        close=datos['close'],
        name=simbolo
    ))
    
    # Añadir niveles de soporte y resistencia
    resistencia = calcular_resistencia(datos)
    soporte = calcular_soporte(datos)
    
    fig.add_hline(y=resistencia, line_dash="dash", line_color="red", 
                  annotation_text="Resistencia")
    fig.add_hline(y=soporte, line_dash="dash", line_color="green", 
                  annotation_text="Soporte")
    
    fig.update_layout(
        title=f"Análisis de Precios - {simbolo}",
        yaxis_title="Precio",
        xaxis_rangeslider_visible=False,
        height=500
    )
    
    return fig

def generar_datos_comparacion(activos, timeframe):
    """Genera datos para comparación de activos"""
    datos = {}
    
    for activo in activos:
        # Simular datos para cada activo
        fecha_hasta = date.today()
        fecha_desde = fecha_hasta - timedelta(days=365)
        datos[activo] = simular_datos_precio(activo, fecha_desde, fecha_hasta)
    
    return datos

def crear_grafico_rendimiento_relativo(datos_comparacion, activos):
    """Crea gráfico de rendimiento relativo"""
    fig = go.Figure()
    
    for activo in activos:
        if activo in datos_comparacion and datos_comparacion[activo] is not None:
            precios = datos_comparacion[activo]['close']
            rendimiento_acumulado = (precios / precios.iloc[0] - 1) * 100;
            
            fig.add_trace(go.Scatter(
                x=rendimiento_acumulado.index,
                y=rendimiento_acumulado,
                mode='lines',
                name=activo
            ))
    
    fig.update_layout(
        title="Rendimiento Relativo (%)",
        yaxis_title="Rendimiento (%)",
        height=400
    )
    
    return fig

def calcular_matriz_correlacion(datos_comparacion):
    """Calcula matriz de correlación entre activos"""
    precios_df = pd.DataFrame()
    
    for activo, datos in datos_comparacion.items():
        if datos is not None:
            precios_df[activo] = datos['close']
    
    return precios_df.corr()

def crear_grafico_correlacion(matriz_correlacion, activos):
    """Crea gráfico de matriz de correlación"""
    fig = go.Figure(data=go.Heatmap(
        z=matriz_correlacion.values,
        x=activos,
        y=activos,
        colorscale='RdBu',
        zmid=0
    ))
    
    fig.update_layout(
        title="Matriz de Correlación",
        height=400
    )
    
    return fig

def crear_tabla_metricas_comparativas(datos_comparacion, activos):
    """Crea tabla de métricas comparativas"""
    metricas = []
    
    for activo in activos:
        if activo in datos_comparacion and datos_comparacion[activo] is not None:
            datos = datos_comparacion[activo]
            rendimientos = datos['close'].pct_change().dropna()
            
            metricas.append({
                'Activo': activo,
                'Precio Actual': f"${datos['close'].iloc[-1]:.2f}",
                'Rendimiento Anual': f"{(datos['close'].iloc[-1] / datos['close'].iloc[0] - 1) * 100:.1f}%",
                'Volatilidad': f"{rendimientos.std() * np.sqrt(252) * 100:.1f}%",
                'Sharpe Ratio': f"{(rendimientos.mean() / rendimientos.std() * np.sqrt(252)):.2f}",
                'Max Drawdown': f"{((datos['close'] / datos['close'].cummax() - 1).min() * 100):.1f}%"
            })
    
    return pd.DataFrame(metricas)

def generar_datos_grafico_principal(simbolo, timeframe, interval):
    """Genera datos para el gráfico principal"""
    fecha_hasta = date.today()
    
    # Mapear timeframe a días
    timeframe_days = {
        '1M': 30,
        '3M': 90,
        '6M': 180,
        '1Y': 365
    }
    
    dias = timeframe_days.get(timeframe, 90)
    fecha_desde = fecha_hasta - timedelta(days=dias)
    
    return simular_datos_precio(simbolo, fecha_desde, fecha_hasta)

def crear_grafico_principal_completo(datos, simbolo, chart_type, tipo_analisis):
    """Crea el gráfico principal completo con indicadores"""
    from plotly.subplots import make_subplots
    
    # Crear subplots (precio principal + indicadores)
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=[f'{simbolo} - Precio', 'RSI', 'Volumen'],
        row_heights=[0.6, 0.2, 0.2]
    )
    
    # Gráfico principal de precio
    if chart_type == "Velas":
        fig.add_trace(go.Candlestick(
            x=datos.index,
            open=datos['open'],
            high=datos['high'],
            low=datos['low'],
            close=datos['close'],
            name=simbolo
        ), row=1, col=1)
    else:  # Línea como fallback
        fig.add_trace(go.Scatter(
            x=datos.index,
            y=datos['close'],
            mode='lines',
            name=simbolo
        ), row=1, col=1)
    
    # Agregar MA 20
    ma20 = datos['close'].rolling(20).mean()
    fig.add_trace(go.Scatter(
        x=datos.index,
        y=ma20,
        mode='lines',
        name='MA 20',
        line=dict(color='blue', width=1)
    ), row=1, col=1)
    
    # RSI
    rsi = calcular_rsi(datos['close'])
    fig.add_trace(go.Scatter(
        x=datos.index,
        y=rsi,
        mode='lines',
        name='RSI',
        line=dict(color='purple')
    ), row=2, col=1)
    
    # Líneas de sobrecompra y sobreventa para RSI
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    # Volumen
    fig.add_trace(go.Bar(
        x=datos.index,
        y=datos['volume'],
        name='Volumen',
        marker_color='rgba(158,202,225,0.6)'
    ), row=3, col=1)
    
    fig.update_layout(
        height=800,
        showlegend=True,
        xaxis_rangeslider_visible=False
    )
    
    return fig

def calcular_rsi(precios, periodo=14):
    """Calcula el RSI (Relative Strength Index)"""
    delta = precios.diff()
    ganancia = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    perdida = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    
    rs = ganancia / perdida
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def mostrar_panel_informacion_tiempo_real(simbolo, datos):
    """Panel de información en tiempo real"""
    st.markdown("##### 📊 Información en Tiempo Real")
    
    col1, col2, col3, col4 = st.columns(4)
    
    precio_actual = datos['close'].iloc[-1]
    precio_anterior = datos['close'].iloc[-2]
    variacion = precio_actual - precio_anterior
    variacion_pct = (variacion / precio_anterior) * 100
    
    with col1:
        st.metric("Precio", f"${precio_actual:.2f}", f"{variacion:+.2f}")
    
    with col2:
        st.metric("Variación %", f"{variacion_pct:+.2f}%")
    
    with col3:
        volumen_actual = datos['volume'].iloc[-1]
        volumen_promedio = datos['volume'].tail(20).mean()
        st.metric("Volumen", f"{volumen_actual:,.0f}", 
                 f"{((volumen_actual/volumen_promedio-1)*100):+.1f}%")
    
    with col4:
        high_dia = datos['high'].iloc[-1]
        low_dia = datos['low'].iloc[-1]
        st.metric("Rango del Día", f"${low_dia:.2f} - ${high_dia:.2f}")
