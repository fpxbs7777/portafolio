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
    """Análisis técnico mejorado"""
    st.markdown("#### 📊 Análisis Técnico Avanzado")
    
    if not portafolio:
        portafolio = obtener_portafolio(token_acceso, id_cliente)
    
    if portafolio:
        activos = portafolio.get('activos', [])
        if activos:
            simbolos = [activo.get('titulo', {}).get('simbolo', '') for activo in activos]
            simbolos = [s for s in simbolos if s]
            
            if simbolos:
                col1, col2 = st.columns(2)
                
                with col1:
                    simbolo_seleccionado = st.selectbox(
                        "Seleccione un activo:",
                        options=simbolos,
                        key="tech_analysis_symbol"
                    )
                
                with col2:
                    indicador = st.selectbox(
                        "Indicador técnico:",
                        ["RSI", "MACD", "Bandas de Bollinger", "Media Móvil"],
                        key="tech_indicator"
                    )
                
                if simbolo_seleccionado:
                    st.info(f"Análisis técnico de {simbolo_seleccionado} con {indicador} estará disponible próximamente")
    else:
        st.warning("No se pudo cargar el portafolio para análisis técnico")

def mostrar_cotizaciones_tiempo_real(token_acceso):
    """Cotizaciones en tiempo real mejoradas"""
    st.markdown("#### 💱 Cotizaciones en Tiempo Real")
    
    col1, col2 = st.columns(2)
    
    with col1:
        simbolo_consulta = st.text_input(
            "Símbolo a consultar:",
            placeholder="Ej: GGAL, YPFD, AL30",
            key="realtime_symbol"
        )
        
        mercado_consulta = st.selectbox(
            "Mercado:",
            ["bCBA", "nYSE", "nASDAQ"],
            key="realtime_market"
        )
    
    with col2:
        if st.button("🔄 Obtener Cotización", key="get_quote"):
            if simbolo_consulta:
                with st.spinner(f"Consultando {simbolo_consulta}..."):
                    cotizacion = obtener_cotizacion_actual(token_acceso, mercado_consulta, simbolo_consulta)
                    
                    if cotizacion:
                        # Mostrar cotización
                        ultimo_precio = cotizacion.get('ultimoPrecio', 'N/A')
                        variacion = cotizacion.get('variacionPorcentual', 'N/A')
                        
                        col_quote1, col_quote2 = st.columns(2)
                        col_quote1.metric("Último Precio", f"${ultimo_precio}")
                        col_quote2.metric("Variación %", f"{variacion}%")
                        
                        with st.expander("Ver detalles completos"):
                            st.json(cotizacion)
                    else:
                        st.error(f"No se pudo obtener cotización para {simbolo_consulta}")

def mostrar_calculadora_mep(token_acceso):
    """Calculadora MEP mejorada"""
    st.markdown("#### 💰 Calculadora MEP")
    
    with st.form("mep_calculator"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            simbolo_mep = st.text_input("Símbolo", value="AL30", help="Ej: AL30, GD30, etc.")
        
        with col2:
            id_plazo_compra = st.number_input("Plazo Compra", value=1, min_value=1)
        
        with col3:
            id_plazo_venta = st.number_input("Plazo Venta", value=1, min_value=1)
        
        monto_pesos = st.number_input("Monto en Pesos ARS", value=100000, min_value=1000)
        
        if st.form_submit_button("💱 Calcular MEP"):
            if simbolo_mep:
                with st.spinner("Calculando MEP..."):
                    cotizacion_mep = obtener_cotizacion_mep(
                        token_acceso, simbolo_mep, id_plazo_compra, id_plazo_venta
                    )
                
                if cotizacion_mep:
                    # Mostrar resultados del cálculo
                    precio_mep = cotizacion_mep.get('precio', cotizacion_mep.get('cotizacion', 0))
                    
                    if precio_mep and precio_mep > 0:
                        dolares_obtenidos = monto_pesos / precio_mep
                        
                        col_result1, col_result2, col_result3 = st.columns(3)
                        col_result1.metric("Cotización MEP", f"${precio_mep:.2f}")
                        col_result2.metric("Dólares Obtenidos", f"USD {dolares_obtenidos:.2f}")
                        col_result3.metric("Costo Efectivo", f"${precio_mep:.2f} por USD")
                    else:
                        st.warning("No se pudo obtener precio válido")
                else:
                    st.error("❌ No se pudo obtener la cotización MEP")

def mostrar_tasas_caucion_detalladas(token_acceso):
    """Tasas de caución con más detalle"""
    st.markdown("#### 🏦 Tasas de Caución Detalladas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Actualizar Tasas", key="update_rates"):
            with st.spinner("Consultando tasas..."):
                tasas_caucion = obtener_tasas_caucion(token_acceso)
            
            if tasas_caucion:
                st.success("✅ Tasas actualizadas")
                
                if isinstance(tasas_caucion, list) and tasas_caucion:
                    df_tasas = pd.DataFrame(tasas_caucion)
                    
                    # Filtrar y ordenar
                    if 'tasa' in df_tasas.columns:
                        df_tasas = df_tasas.sort_values('tasa', ascending=False)
                    
                    st.dataframe(df_tasas.head(20), use_container_width=True)
                else:
                    st.warning("Formato de datos inesperado")
            else:
                st.error("❌ No se pudieron obtener las tasas")
    
    with col2:
        # Calculadora de rendimiento
        st.markdown("##### 📊 Calculadora de Rendimiento")
        
        with st.form("yield_calculator"):
            capital_inicial = st.number_input("Capital Inicial ($)", value=100000)
            tasa_anual = st.number_input("Tasa Anual (%)", value=45.0, step=0.1)
            dias_inversion = st.number_input("Días de Inversión", value=30, min_value=1)
            
            if st.form_submit_button("💰 Calcular Rendimiento"):
                rendimiento_diario = tasa_anual / 365 / 100
                rendimiento_total = capital_inicial * (1 + rendimiento_diario) ** dias_inversion
                ganancia = rendimiento_total - capital_inicial
                
                st.metric("Capital Final", f"${rendimiento_total:,.2f}")
                st.metric("Ganancia", f"${ganancia:,.2f}")
                st.metric("Rendimiento %", f"{(ganancia/capital_inicial*100):.2f}%")

# Funciones placeholder para desarrollo futuro
def mostrar_placeholder_flujos_efectivo():
    st.info("📊 Próximamente: Análisis detallado de flujos de efectivo entrantes y salientes")

def mostrar_placeholder_historico_operaciones():
    st.info("📈 Próximamente: Histórico completo de compras, ventas y dividendos")

def mostrar_placeholder_rebalanceo():
    st.info("⚖️ Próximamente: Herramienta automática de rebalanceo de portafolio")

def mostrar_placeholder_escenarios():
    st.info("🎭 Próximamente: Análisis de diferentes escenarios de mercado")

def mostrar_placeholder_correlaciones():
    st.info("🔗 Próximamente: Matriz de correlaciones entre activos")

def mostrar_placeholder_backtesting():
    st.info("⏮️ Próximamente: Backtesting de estrategias de inversión")

def mostrar_placeholder_montecarlo():
    st.info("🎲 Próximamente: Simulaciones Monte Carlo para proyecciones")

def mostrar_placeholder_alertas():
    st.info("🔔 Próximamente: Sistema de alertas personalizables")

def main():
    """
    Función principal de la aplicación Streamlit
    """
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
    # Add missing date parameters
    if 'fecha_desde' not in st.session_state:
        st.session_state.fecha_desde = date.today() - timedelta(days=365)
    if 'fecha_hasta' not in st.session_state:
        st.session_state.fecha_hasta = date.today()
    
    # Sidebar reorganizada with mejor flujo
    with st.sidebar:
        st.header("🔐 Panel de Control")
        
        # Sección 1: Estado de Conexión
        st.markdown("#### 📡 Estado de Conexión")
        
        if st.session_state.token_acceso is None:
            st.error("🔴 Desconectado")
            
            # Formulario de login mejorado
            with st.form("login_form"):
                st.markdown("##### Credenciales IOL")
                usuario = st.text_input("👤 Usuario", placeholder="su_usuario")
                contraseña = st.text_input("🔒 Contraseña", type="password", placeholder="su_contraseña")
                
                # Opciones avanzadas
                with st.expander("⚙️ Configuración Avanzada"):
                    recordar_sesion = st.checkbox("Recordar por más tiempo", value=False)
                    endpoint_alternativo = st.checkbox("Usar endpoint alternativo", value=False)
                
                if st.form_submit_button("🚀 Conectar a IOL", use_container_width=True):
                    if usuario and contraseña:
                        with st.spinner("🔄 Conectando con IOL..."):
                            token_acceso, refresh_token = obtener_tokens(usuario, contraseña)
                            
                            if token_acceso:
                                st.session_state.token_acceso = token_acceso
                                st.session_state.refresh_token = refresh_token
                                st.success("✅ ¡Conexión exitosa!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("❌ Error en la autenticación")
                    else:
                        st.warning("⚠️ Complete todos los campos")
        else:
            # Usuario conectado - panel mejorado
            st.success("🟢 Conectado a IOL")
            
            # Sección 2: Configuración de Análisis
            st.markdown("#### ⚙️ Configuración de Análisis")
            
            with st.expander("📅 Rango de Fechas", expanded=True):
                fecha_desde = st.date_input(
                    "📅 Desde:",
                    value=st.session_state.fecha_desde,
                    max_value=date.today(),
                    key="fecha_desde_input"
                )
                fecha_hasta = st.date_input(
                    "📅 Hasta:",
                    value=st.session_state.fecha_hasta,
                    max_value=date.today(),
                    key="fecha_hasta_input"
                )
                
                # Botones de rango rápido
                col1, col2, col3 = st.columns(3)
                if col1.button("1M", help="Último mes"):
                    st.session_state.fecha_desde = date.today() - timedelta(days=30)
                    st.rerun()
                if col2.button("6M", help="Últimos 6 meses"):
                    st.session_state.fecha_desde = date.today() - timedelta(days=180)
                    st.rerun()
                if col3.button("1A", help="Último año"):
                    st.session_state.fecha_desde = date.today() - timedelta(days=365)
                    st.rerun()
            
            st.session_state.fecha_desde = fecha_desde
            st.session_state.fecha_hasta = fecha_hasta
            
            # Sección 3: Selección de Cliente
            st.markdown("#### 👥 Selección de Cliente")
            
            # Obtener lista de clientes
            if not st.session_state.clientes:
                with st.spinner("🔄 Cargando clientes..."):
                    clientes = obtener_lista_clientes(st.session_state.token_acceso)
                    st.session_state.clientes = clientes
            
            clientes = st.session_state.clientes
            
            if clientes:
                st.success(f"✅ {len(clientes)} clientes disponibles")
                
                # Seleccionar cliente con mejor UX
                cliente_ids = [c.get('numeroCliente', c.get('id')) for c in clientes]
                cliente_nombres = [c.get('apellidoYNombre', c.get('nombre', 'Cliente')) for c in clientes]
                
                cliente_seleccionado = st.selectbox(
                    "🎯 Cliente:",
                    options=cliente_ids,
                    format_func=lambda x: cliente_nombres[cliente_ids.index(x)] if x in cliente_ids else "Cliente Desconocido",
                    key="cliente_selector"
                )
                
                # Guardar cliente seleccionado en session state
                st.session_state.cliente_seleccionado = next(
                    (c for c in clientes if c.get('numeroCliente', c.get('id')) == cliente_seleccionado),
                    None
                )
                
                # Mostrar info del cliente seleccionado
                if st.session_state.cliente_seleccionado:
                    cliente_info = st.session_state.cliente_seleccionado
                    with st.expander("ℹ️ Info del Cliente"):
                        st.text(f"ID: {cliente_info.get('numeroCliente', 'N/A')}")
                        st.text(f"Nombre: {cliente_info.get('apellidoYNombre', 'N/A')}")
                
                if st.button("🔄 Actualizar Clientes", use_container_width=True):
                    with st.spinner("🔄 Actualizando..."):
                        nuevos_clientes = obtener_lista_clientes(st.session_state.token_acceso)
                        st.session_state.clientes = nuevos_clientes
                        st.success("✅ Lista actualizada")
                        st.rerun()
            
            else:
                st.warning("⚠️ No se encontraron clientes")
                st.markdown("**Posibles causas:**")
                st.markdown("- Permisos insuficientes")
                st.markdown("- Problema de conectividad")
                st.markdown("- Token expirado")
            
            # Sección 4: Acciones Rápidas
            st.markdown("#### ⚡ Acciones Rápidas")
            
            if st.button("🔄 Reconectar", use_container_width=True):
                st.session_state.token_acceso = None
                st.session_state.refresh_token = None
                st.rerun()
            
            if st.button("🗑️ Limpiar Cache", use_container_width=True):
                st.session_state.clientes = []
                st.session_state.cliente_seleccionado = None
                st.success("✅ Cache limpiado")
                st.rerun()
    
    # Contenido principal con mejor manejo de estados
    try:
        if st.session_state.token_acceso and st.session_state.cliente_seleccionado:
            # Mostrar breadcrumb
            cliente_nombre = st.session_state.cliente_seleccionado.get('apellidoYNombre', 'Cliente')
            st.markdown(f"📍 **Navegación:** Inicio > {cliente_nombre} > Análisis de Portafolio")
            
            mostrar_analisis_portafolio()
        elif st.session_state.token_acceso:
            # Conectado pero sin cliente
            st.info("🎯 **Paso 2:** Seleccione un cliente en la barra lateral para comenzar el análisis")
            
            # Mostrar resumen de conexión
            col1, col2, col3 = st.columns(3)
            col1.success("✅ Conectado a IOL")
            col2.info(f"📅 Rango: {st.session_state.fecha_desde} - {st.session_state.fecha_hasta}")
            col3.warning("⏳ Esperando selección de cliente")
            
        else:
            # No conectado
            st.info("🔐 **Paso 1:** Ingrese sus credenciales de IOL en la barra lateral para comenzar")
            
            # Mostrar información de ayuda
            st.markdown("### 🚀 Bienvenido al IOL Portfolio Analyzer")
            

            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                #### ✨ Características Principales:
                - 📊 **Dashboard Ejecutivo** - Vista general del portafolio
                - 💰 **Estado Financiero** - Análisis de cuentas y flujos
                - 🎯 **Optimización** - Estrategias de Markowitz y rebalanceo
                - 📈 **Análisis Avanzado** - Técnico, correlaciones, backtesting
                - 🛠️ **Herramientas** - MEP, cotizaciones, alertas
                """)
            
            with col2:
                st.markdown("""
                #### 🔧 Pasos para Comenzar:
                1. **Conectar** - Ingrese sus credenciales IOL
                2. **Seleccionar** - Elija el cliente a analizar
                3. **Configurar** - Ajuste fechas y parámetros
                4. **Analizar** - Explore las diferentes herramientas
                """)
                
    except Exception as e:
        st.error(f"❌ Error en la aplicación: {str(e)}")
        
        # Botón de recuperación
        if st.button("🔄 Reiniciar Aplicación"):
            # Limpiar session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        # Información de debug en expander
        with st.expander("🔍 Información de Debug"):
            st.code(str(e))
            st.markdown("**Session State:**")
            st.json(dict(st.session_state))
