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

def get_historical_data_for_optimization(token_portador, simbolos, fecha_desde, fecha_hasta, activos_portafolio=None):
    """
    Obtiene datos históricos para optimización de portafolio detectando tipo de activo automáticamente.
    """
    try:
        df_precios = pd.DataFrame()
        simbolos_exitosos = []
        simbolos_fallidos = []
        detalles_errores = {}

        fecha_desde_str = fecha_desde.strftime('%Y-%m-%d')
        fecha_hasta_str = fecha_hasta.strftime('%Y-%m-%d')

        st.info(f"🔍 Buscando datos históricos desde {fecha_desde_str} hasta {fecha_hasta_str}")

        progress_bar = st.progress(0)
        total_simbolos = len(simbolos)

        for idx, simbolo in enumerate(simbolos):
            progress_bar.progress((idx + 1) / total_simbolos, text=f"Procesando {simbolo}...")
            
            # Detectar tipo automáticamente
            tipo = None
            if activos_portafolio:
                tipo = detectar_tipo_activo(simbolo, activos_portafolio)
                
            mercado = obtener_mercado_para_tipo(tipo)
            serie_obtenida = False

            try:
                # Buscar clase D si es bono
                simbolo_consulta = simbolo
                if tipo and ('BONO' in tipo.upper() or 'OBLIGACION' in tipo.upper()):
                    clase_d = obtener_clase_d(simbolo, mercado, token_portador)
                    if clase_d:
                        simbolo_consulta = clase_d
                        
                serie = obtener_serie_historica_iol(
                    token_portador, mercado, simbolo_consulta,
                    fecha_desde_str, fecha_hasta_str
                )
                
                if serie is not None and len(serie) > 10 and serie.nunique() > 1:
                    df_precios[simbolo_consulta] = serie
                    simbolos_exitosos.append(simbolo_consulta)
                    serie_obtenida = True
                    st.success(f"✅ {simbolo_consulta} ({mercado}, tipo: {tipo or 'N/A'}): {len(serie)} puntos de datos")
                    
            except Exception as e:
                detalles_errores[f"{simbolo}_{mercado}"] = str(e)

            if not serie_obtenida:
                # Intentar con otros mercados como fallback
                mercados_fallback = ['bCBA', 'nYSE', 'nASDAQ', 'rOFEX']
                for mercado_fb in mercados_fallback:
                    if mercado_fb != mercado:
                        try:
                            serie = obtener_serie_historica_iol(
                                token_portador, mercado_fb, simbolo,
                                fecha_desde_str, fecha_hasta_str
                            )
                            if serie is not None and len(serie) > 10 and serie.nunique() > 1:
                                df_precios[simbolo] = serie
                                simbolos_exitosos.append(simbolo)
                                serie_obtenida = True
                                st.success(f"✅ {simbolo} ({mercado_fb}): {len(serie)} puntos de datos")
                                break
                        except Exception:
                            continue

            if not serie_obtenida:
                try:
                    serie_yf = obtener_datos_alternativos_yfinance(
                        simbolo, fecha_desde, fecha_hasta
                    )
                    if serie_yf is not None and len(serie_yf) > 10 and serie_yf.nunique() > 1:
                        df_precios[simbolo] = serie_yf
                        simbolos_exitosos.append(simbolo)
                        st.info(f"ℹ️ {simbolo} (Yahoo Finance): {len(serie_yf)} puntos de datos")
                        serie_obtenida = True
                except Exception as e:
                    detalles_errores[f"{simbolo}_yfinance"] = str(e)

            if not serie_obtenida:
                simbolos_fallidos.append(simbolo)
                st.warning(f"⚠️ No se pudieron obtener datos para {simbolo}")

        progress_bar.empty()
        
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
        
        # Intentar diferentes estrategias de alineación
        try:
            # Usar forward fill y backward fill
            df_precios_filled = df_precios.fillna(method='ffill').fillna(method='bfill')
            
            if not df_precios_filled.dropna().empty:
                df_precios = df_precios_filled.dropna()
                st.info("✅ Usando estrategia forward/backward fill")
            else:
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
        return None, None, None

def detectar_tipo_activo(simbolo, activos_portafolio):
    """
    Detecta el tipo de activo automáticamente usando la data del portafolio.
    """
    for activo in activos_portafolio:
        titulo = activo.get('titulo', {})
        if titulo.get('simbolo', '') == simbolo:
            return titulo.get('tipo', '').upper()
    return None

def obtener_mercado_para_tipo(tipo):
    """
    Mapea el tipo de activo al mercado/endpoint correcto de IOL.
    """
    if not tipo:
        return 'bCBA'  # Default
    tipo = tipo.upper()
    if 'FCI' in tipo:
        return 'FCI'
    if 'OPCION' in tipo:
        return 'Opciones'
    if 'BONO' in tipo or 'OBLIGACION' in tipo:
        return 'bCBA'
    if 'ACCION' in tipo:
        return 'bCBA'
    if 'CEDEAR' in tipo:
        return 'bCBA'
    return 'bCBA'

# --- Portfolio Optimization Functions ---
def optimize_portfolio(returns, target_return=None):
    """
    Optimización Markowitz: mínima varianza o máxima Sharpe.
    """
    n = returns.shape[1]
    mean_returns = returns.mean()
    cov_matrix = returns.cov()
    bounds = tuple((0, 1) for _ in range(n))
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

    def portfolio_volatility(weights):
        return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

    if target_return is not None:
        def constraint_return(weights):
            return np.dot(weights, mean_returns) - target_return
        constraints = (constraints, {'type': 'eq', 'fun': constraint_return})

    result = op.minimize(portfolio_volatility, n * [1. / n, ], bounds=bounds, constraints=constraints)
    if result.success:
        return result.x
    else:
        # fallback: pesos iguales
        return np.array([1 / n] * n)

# --- Portfolio Manager ---
class PortfolioManager:
    """
    Clase simplificada para manejo de portafolio y optimización
    """
    def __init__(self, symbols, token, fecha_desde, fecha_hasta, activos_portafolio=None):
        self.symbols = symbols
        self.token = token
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.activos_portafolio = activos_portafolio
        self.data_loaded = False
        self.returns = None
        self.prices = None

    def load_data(self):
        """
        Carga datos históricos para los símbolos del portafolio
        """
        try:
            mean_returns, cov_matrix, df_precios = get_historical_data_for_optimization(
                self.token, self.symbols, self.fecha_desde, self.fecha_hasta, self.activos_portafolio
            )
            
            if mean_returns is not None and cov_matrix is not None:
                self.returns = df_precios.pct_change().dropna() if df_precios is not None else None
                self.prices = df_precios
                self.mean_returns = mean_returns
                self.cov_matrix = cov_matrix
                self.data_loaded = True
                return True
            else:
                return False
                
        except Exception as e:
            st.error(f"Error cargando datos: {str(e)}")
            return False
    
    def compute_portfolio(self, strategy='markowitz', target_return=None):
        """
        Computa la optimización del portafolio
        """
        if not self.data_loaded or self.returns is None:
            return None
        
        try:
            # Optimización básica usando pesos iguales como fallback
            n_assets = len(self.returns.columns)
            
            if strategy == 'equi-weight':
                weights = np.array([1/n_assets] * n_assets)
            else:
                # Intentar optimización real
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

class PortfolioOutput:
    """
    Clase para almacenar resultados de optimización de portafolio
    """
    def __init__(self, weights, asset_names, returns):
        self.weights = weights
        self.asset_names = asset_names
        self.returns = returns
        self.portfolio_returns = None
        
        if returns is not None and len(weights) == len(returns.columns):
            self.portfolio_returns = (returns * weights).sum(axis=1)
    
    def get_metrics_dict(self):
        """
        Calcula y retorna métricas del portafolio
        """
        if self.portfolio_returns is None or len(self.portfolio_returns) == 0:
            return {
                'Mean Daily': 0,
                'Volatility Daily': 0,
                'Sharpe Ratio': 0,
                'VaR 95%': 0
            }
        
        mean_daily = self.portfolio_returns.mean()
        vol_daily = self.portfolio_returns.std()
        sharpe = mean_daily / vol_daily if vol_daily > 0 else 0
        var_95 = np.percentile(self.portfolio_returns, 5)
        
        return {
            'Mean Daily': mean_daily,
            'Volatility Daily': vol_daily,
            'Sharpe Ratio': sharpe,
            'VaR 95%': var_95
        }
    
    def plot_histogram_streamlit(self, title="Distribución de Retornos"):
        """
        Crea un histograma de retornos usando Plotly para Streamlit
        """
        if self.portfolio_returns is None or len(self.portfolio_returns) == 0:
            # Crear gráfico vacío
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos suficientes para mostrar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(title=title)
            return fig
        
        fig = go.Figure(data=[go.Histogram(
            x=self.portfolio_returns,
            nbinsx=30,
            name="Retornos del Portafolio"
        )])
        
        fig.update_layout(
            title=f"{title}",
            xaxis_title="Retorno",
            yaxis_title="Frecuencia",
            showlegend=False
        )
        
        return fig

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
    
    # Sidebar para autenticación y configuración
    with st.sidebar:
        st.header("🔐 Autenticación IOL")
        
        if st.session_state.token_acceso is None:
            # Formulario de login
            with st.form("login_form"):
                st.markdown("#### Ingrese sus credenciales de IOL")
                usuario = st.text_input("Usuario", placeholder="su_usuario")
                contraseña = st.text_input("Contraseña", type="password", placeholder="su_contraseña")
                
                if st.form_submit_button("🚀 Conectar"):
                    if usuario and contraseña:
                        with st.spinner("Conectando con IOL..."):
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
            # Usuario conectado
            st.success("✅ Conectado a IOL")
            
            # Configuración de fechas
            st.markdown("#### 📅 Configuración de Fechas")
            col1, col2 = st.columns(2)
            with col1:
                fecha_desde = st.date_input(
                    "Fecha desde:",
                    value=st.session_state.fecha_desde,
                    max_value=date.today()
                )
            with col2:
                fecha_hasta = st.date_input(
                    "Fecha hasta:",
                    value=st.session_state.fecha_hasta,
                    max_value=date.today()
                )
            
            st.session_state.fecha_desde = fecha_desde

            st.session_state.fecha_hasta = fecha_hasta
            
            # Obtener lista de clientes
            if not st.session_state.clientes:
                with st.spinner("Cargando clientes..."):
                    clientes = obtener_lista_clientes(st.session_state.token_acceso)
                    st.session_state.clientes = clientes
            
            clientes = st.session_state.clientes
            
            if clientes:
                st.info(f"👥 {len(clientes)} clientes disponibles")
                
                # Seleccionar cliente
                cliente_ids = [c.get('numeroCliente', c.get('id')) for c in clientes]
                cliente_nombres = [c.get('apellidoYNombre', c.get('nombre', 'Cliente')) for c in clientes]
                
                cliente_seleccionado = st.selectbox(
                    "Seleccione un cliente:",
                    options=cliente_ids,
                    format_func=lambda x: cliente_nombres[cliente_ids.index(x)] if x in cliente_ids else "Cliente Desconocido"
                )
                
                # Guardar cliente seleccionado en session state
                st.session_state.cliente_seleccionado = next(
                    (c for c in clientes if c.get('numeroCliente', c.get('id')) == cliente_seleccionado),
                    None
                )
                
                if st.button("🔄 Actualizar lista de clientes"):
                    with st.spinner("Actualizando clientes..."):
                        nuevos_clientes = obtener_lista_clientes(st.session_state.token_acceso)
                        st.session_state.clientes = nuevos_clientes
                        st.success("✅ Lista de clientes actualizada")
                        st.rerun()
            
            else:
                st.warning("No se encontraron clientes. Verifique su conexión y permisos.")
    
    # Contenido principal con manejo de errores mejorado
    try:
        if st.session_state.token_acceso and st.session_state.cliente_seleccionado:
            mostrar_analisis_portafolio()
        elif st.session_state.token_acceso:
            st.info("👆 Seleccione un cliente en la barra lateral para comenzar el análisis")
        else:
            st.info("👆 Ingrese sus credenciales de IOL en la barra lateral para comenzar")
    except Exception as e:
        st.error(f"❌ Error en la aplicación: {str(e)}")
        st.error("🔄 Por favor, recargue la página e intente nuevamente")

# Agrega la función faltante mostrar_analisis_portafolio (stub mínima para evitar el error)
def mostrar_analisis_portafolio():
    st.info("Funcionalidad de análisis de portafolio en desarrollo. Pronto disponible.")

def mostrar_optimizacion_portafolio(portafolio, token_acceso, fecha_desde, fecha_hasta):
    """
    Muestra la optimización del portafolio usando datos históricos con estrategias extendidas
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
        ejecutar_optimizacion = st.button("🚀 Ejecutar Optimización")
    with col2:
        ejecutar_frontier = st.button("📈 Calcular Frontera Eficiente")
    
    if ejecutar_optimizacion:
        with st.spinner("Ejecutando optimización..."):
            try:
                # Crear manager de portafolio
                manager_inst = PortfolioManager(simbolos, token_acceso, fecha_desde, fecha_hasta, activos)
                
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
                            if hasattr(portfolio_result, 'dataframe_allocation') and portfolio_result.dataframe_allocation is not None:
                                weights_df = portfolio_result.dataframe_allocation.copy()
                                weights_df['Peso (%)'] = weights_df['weights'] * 100
                                weights_df = weights_df.sort_values('Peso (%)', ascending=False)
                                st.dataframe(weights_df[['rics', 'Peso (%)']], use_container_width=True)
                            elif hasattr(portfolio_result, 'weights') and portfolio_result.weights is not None:
                                weights_df = pd.DataFrame({
                                    'Activo': simbolos,
                                    'Peso (%)': portfolio_result.weights * 100
                                })
                                weights_df = weights_df.sort_values('Peso (%)', ascending=False)
                                st.dataframe(weights_df, use_container_width=True)
                        
                        with col2:
                            st.markdown("#### 📈 Métricas del Portafolio")
                            metricas = portfolio_result.get_metrics_dict()
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("Retorno Diario", f"{metricas['Mean Daily']:.4f}")
                                st.metric("Volatilidad Diaria", f"{metricas['Volatility Daily']:.4f}")
                                st.metric("Ratio de Sharpe", f"{metricas['Sharpe Ratio']:.4f}")
                                st.metric("VaR 95%", f"{metricas['VaR 95%']:.4f}")
                        
                        # Gráfico de distribución de retornos
                        if hasattr(portfolio_result, 'returns') and portfolio_result.returns is not None:
                            st.markdown("#### 📊 Distribución de Retornos del Portafolio Optimizado")
                            fig = portfolio_result.plot_histogram_streamlit()
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Gráfico de pesos
                        if hasattr(portfolio_result, 'weights') and portfolio_result.weights is not None:
                            st.markdown("#### 🥧 Distribución de Pesos")
                            fig_pie = go.Figure(data=[go.Pie(
                                labels=simbolos,
                                values=portfolio_result.weights,
                                textinfo='label+percent',
                            )])
                            fig_pie.update_layout(title="Distribución Optimizada de Activos")
                            st.plotly_chart(fig_pie, use_container_width=True)
                        
                    else:
                        st.error("❌ Error en la optimización")
                else:
                    st.error("❌ No se pudieron cargar los datos históricos")
                    
            except Exception as e:
                st.error(f"❌ Error durante la optimización: {str(e)}")
    
    # Información adicional extendida
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
        
        **Mínima Varianza L1:**
        - Minimiza la varianza del portafolio
        - Restricción L1 para regularización
        - Tiende a generar portafolios más concentrados
        
        **Mínima Varianza L2:**
        - Minimiza la varianza del portafolio
        - Restricción L2 para regularización
        - Genera portafolios más diversificados
        
        **Solo Posiciones Largas:**
        - Optimización estándar sin restricciones adicionales
        - Permite solo posiciones compradoras
        - Suma de pesos = 100%
        """)

def get_historical_data_for_optimization(token_portador, simbolos, fecha_desde, fecha_hasta, activos_portafolio=None):
    """
    Obtiene datos históricos para optimización de portafolio detectando tipo de activo automáticamente.
    """
    try:
        df_precios = pd.DataFrame()
        simbolos_exitosos = []
        simbolos_fallidos = []
        detalles_errores = {}

        fecha_desde_str = fecha_desde.strftime('%Y-%m-%d')
        fecha_hasta_str = fecha_hasta.strftime('%Y-%m-%d')

        st.info(f"🔍 Buscando datos históricos desde {fecha_desde_str} hasta {fecha_hasta_str}")

        progress_bar = st.progress(0)
        total_simbolos = len(simbolos)

        for idx, simbolo in enumerate(simbolos):
            progress_bar.progress((idx + 1) / total_simbolos, text=f"Procesando {simbolo}...")
            
            # Detectar tipo automáticamente
            tipo = None
            if activos_portafolio:
                tipo = detectar_tipo_activo(simbolo, activos_portafolio)
                
            mercado = obtener_mercado_para_tipo(tipo)
            serie_obtenida = False

            try:
                # Buscar clase D si es bono
                simbolo_consulta = simbolo
                if tipo and ('BONO' in tipo.upper() or 'OBLIGACION' in tipo.upper()):
                    clase_d = obtener_clase_d(simbolo, mercado, token_portador)
                    if clase_d:
                        simbolo_consulta = clase_d
                        
                serie = obtener_serie_historica_iol(
                    token_portador, mercado, simbolo_consulta,
                    fecha_desde_str, fecha_hasta_str
                )
                
                if serie is not None and len(serie) > 10 and serie.nunique() > 1:
                    df_precios[simbolo_consulta] = serie
                    simbolos_exitosos.append(simbolo_consulta)
                    serie_obtenida = True
                    st.success(f"✅ {simbolo_consulta} ({mercado}, tipo: {tipo or 'N/A'}): {len(serie)} puntos de datos")
                    
            except Exception as e:
                detalles_errores[f"{simbolo}_{mercado}"] = str(e)

            if not serie_obtenida:
                # Intentar con otros mercados como fallback
                mercados_fallback = ['bCBA', 'nYSE', 'nASDAQ', 'rOFEX']
                for mercado_fb in mercados_fallback:
                    if mercado_fb != mercado:
                        try:
                            serie = obtener_serie_historica_iol(
                                token_portador, mercado_fb, simbolo,
                                fecha_desde_str, fecha_hasta_str
                            )
                            if serie is not None and len(serie) > 10 and serie.nunique() > 1:
                                df_precios[simbolo] = serie
                                simbolos_exitosos.append(simbolo)
                                serie_obtenida = True
                                st.success(f"✅ {simbolo} ({mercado_fb}): {len(serie)} puntos de datos")
                                break
                        except Exception:
                            continue

            if not serie_obtenida:
                try:
                    serie_yf = obtener_datos_alternativos_yfinance(
                        simbolo, fecha_desde, fecha_hasta
                    )
                    if serie_yf is not None and len(serie_yf) > 10 and serie_yf.nunique() > 1:
                        df_precios[simbolo] = serie_yf
                        simbolos_exitosos.append(simbolo)
                        st.info(f"ℹ️ {simbolo} (Yahoo Finance): {len(serie_yf)} puntos de datos")
                        serie_obtenida = True
                except Exception as e:
                    detalles_errores[f"{simbolo}_yfinance"] = str(e)

            if not serie_obtenida:
                simbolos_fallidos.append(simbolo)
                st.warning(f"⚠️ No se pudieron obtener datos para {simbolo}")

        progress_bar.empty()
        
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
        
        # Intentar diferentes estrategias de alineación
        try:
            # Usar forward fill y backward fill
            df_precios_filled = df_precios.fillna(method='ffill').fillna(method='bfill')
            
            if not df_precios_filled.dropna().empty:
                df_precios = df_precios_filled.dropna()
                st.info("✅ Usando estrategia forward/backward fill")
            else:
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
        return None, None, None

class PortfolioManager:
    """
    Clase para manejo de portafolio y optimización con funcionalidades extendidas
    """
    def __init__(self, symbols, token, fecha_desde, fecha_hasta, activos_portafolio=None):
        self.symbols = symbols
        self.token = token
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.activos_portafolio = activos_portafolio
        self.data_loaded = False
        self.returns = None
        self.prices = None
        self.notional = 100000  # Valor nominal por defecto
        self.manager = None
    
    def load_data(self):
        """
        Carga datos históricos para los símbolos del portafolio
        """
        try:
            mean_returns, cov_matrix, df_precios = get_historical_data_for_optimization(
                self.token, self.symbols, self.fecha_desde, self.fecha_hasta, self.activos_portafolio
            )
            
            if mean_returns is not None and cov_matrix is not None and df_precios is not None:
                self.returns = df_precios.pct_change().dropna()
                self.prices = df_precios
                self.mean_returns = mean_returns
                self.cov_matrix = cov_matrix
                self.data_loaded = True
                
                # Crear manager para optimización avanzada
                self.manager = manager(list(df_precios.columns), self.notional, df_precios.to_dict('series'))
                
                return True
            else:
                return False
                
        except Exception as e:
            st.error(f"Error cargando datos: {str(e)}")
            return False
    
    def compute_portfolio(self, strategy='markowitz', target_return=None):
        """
        Computa la optimización del portafolio con estrategias extendidas
        """
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
                    weights = np.array([1/n_assets] * n_assets)
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
            st.error(f"Error en optimización: {str(e)}")
            return None
