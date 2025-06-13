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
        # Eliminar mensajes de interfaz innecesarios
        # st.info(f"💰 Solicitando estado de cuenta - URL: {url_estado_cuenta}")
        # st.info(f"📊 Status Code: {respuesta.status_code}")
        
        if respuesta.status_code == 200:
            estado_data = respuesta.json()
            # st.success(f"✅ Estado de cuenta obtenido exitosamente")
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
        # Eliminar mensajes de interfaz innecesarios
        # st.info(f"🔍 Solicitando portafolio para cliente {id_cliente}")
        # st.info(f"📡 URL: {url_portafolio}")
        # st.info(f"📊 Status Code: {respuesta.status_code}")
        
        if respuesta.status_code == 200:
            portafolio_data = respuesta.json()
            # st.success(f"✅ Portafolio obtenido exitosamente")
            # st.info(f"📋 Estructura de portafolio: {type(portafolio_data)}")
            # if isinstance(portafolio_data, dict):
            #     st.info(f"🔑 Claves disponibles: {list(portafolio_data.keys())}")
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
    Obtiene datos históricos para optimización de portafolio usando SOLO la función obtener_serie_historica_iol
    (con fallback a yfinance solo si falla), para todos los instrumentos: acciones, bonos, FCI, opciones, etc.
    Alinea las fechas solo si hay al menos 2 activos con fechas comunes, si no, intenta devolver los datos disponibles.
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

            serie_obtenida = False
            simbolo_upper = simbolo.upper()

            # Determinar mercados según el tipo de instrumento
            if simbolo_upper == "ADCGLOA":
                mercados = ['FCI']
            elif simbolo_upper.startswith("AE") or simbolo_upper.endswith("D") or simbolo_upper.endswith("C") or simbolo_upper.endswith("O"):
                mercados = ['bCBA']
            elif simbolo_upper.endswith("48") or simbolo_upper.endswith("30") or simbolo_upper.endswith("29"):
                mercados = ['bCBA']
            elif simbolo_upper.startswith("MERV") or simbolo_upper.startswith("OPC"):
                mercados = ['Opciones']
            else:
                mercados = ['bCBA', 'nYSE', 'nASDAQ', 'rOFEX']

            # Intentar obtener datos de cada mercado usando SIEMPRE obtener_serie_historica_iol
            for mercado in mercados:
                try:
                    simbolo_consulta = simbolo
                    # Buscar clase D solo para bonos en bCBA
                    if mercado == 'bCBA' and (simbolo_upper.endswith("D") or simbolo_upper.endswith("C") or simbolo_upper.endswith("O") or simbolo_upper.startswith("AE")):
                        clase_d = obtener_clase_d(simbolo, mercado, token_portador)
                        if clase_d:
                            simbolo_consulta = clase_d

                    serie = obtener_serie_historica_iol(
                        token_portador, mercado, simbolo_consulta,
                        fecha_desde_str, fecha_hasta_str
                    )

                    if serie is not None and len(serie) > 10:
                        # Verificar que la serie tenga valores válidos y variación
                        serie_clean = serie.dropna()
                        if len(serie_clean) > 10 and serie_clean.nunique() > 1 and serie_clean.std() > 0:
                            df_precios[simbolo] = serie_clean
                            simbolos_exitosos.append(simbolo)
                            serie_obtenida = True
                            st.success(f"✅ {simbolo} ({mercado}): {len(serie_clean)} puntos de datos")
                            break
                except Exception as e:
                    detalles_errores[f"{simbolo}_{mercado}"] = str(e)
                    continue

            # Fallback a yfinance solo si no se pudo obtener de IOL
            if not serie_obtenida:
                try:
                    serie_yf = obtener_datos_alternativos_yfinance(
                        simbolo, fecha_desde, fecha_hasta
                    )
                    if serie_yf is not None and len(serie_yf) > 10:
                        serie_yf_clean = serie_yf.dropna()
                        if len(serie_yf_clean) > 10 and serie_yf_clean.nunique() > 1 and serie_yf_clean.std() > 0:
                            df_precios[simbolo] = serie_yf_clean
                            simbolos_exitosos.append(simbolo)
                            serie_obtenida = True
                            st.info(f"ℹ️ {simbolo} (Yahoo Finance): {len(serie_yf_clean)} puntos de datos")
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
                        serie = df_precios[simbolo].dropna()
                        if len(serie) > 0:
                            datos_info = f"{simbolo}: {len(serie)} puntos, rango: {serie.min():.2f} - {serie.max():.2f}"
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

        if len(simbolos_exitosos) < 2:
            if len(simbolos_exitosos) == 1:
                st.error("❌ Se necesitan al menos 2 activos con datos históricos válidos para el análisis.")
            else:
                st.error("❌ No se pudieron obtener datos históricos para ningún activo.")
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

        st.info(f"📊 Alineando datos de {len(df_precios.columns)} activos...")

        if df_precios.empty:
            st.error("❌ DataFrame de precios está vacío")
            return None, None, None

        # Limpiar datos y alinear fechas
        try:
            # Paso 1: Asegurar que todas las series tengan al menos 30 puntos
            series_validas = {}
            for col in df_precios.columns:
                serie = df_precios[col].dropna()
                if len(serie) >= 30 and serie.std() > 0:
                    series_validas[col] = serie
                else:
                    st.warning(f"⚠️ Descartando {col}: insuficientes datos válidos ({len(serie)} puntos)")
            
            if len(series_validas) < 2:
                st.error("❌ No hay suficientes activos con datos válidos después del filtrado")
                return None, None, None
            
            # Paso 2: Crear DataFrame con series válidas
            df_precios_limpio = pd.DataFrame(series_validas)
            
            # Paso 3: Buscar fechas comunes
            fechas_comunes = None
            for col in df_precios_limpio.columns:
                fechas_serie = set(df_precios_limpio[col].dropna().index)
                if fechas_comunes is None:
                    fechas_comunes = fechas_serie
                else:
                    fechas_comunes = fechas_comunes.intersection(fechas_serie)
            
            # Paso 4: Decidir estrategia de alineación
            if len(fechas_comunes) >= 30:
                # Usar solo fechas comunes
                fechas_comunes_sorted = sorted(list(fechas_comunes))
                df_aligned = df_precios_limpio.loc[fechas_comunes_sorted].dropna()
                st.info(f"✅ Usando {len(fechas_comunes)} fechas comunes")
            else:
                # Estrategia de interpolación y rellenado
                st.warning(f"⚠️ Solo {len(fechas_comunes)} fechas comunes. Aplicando interpolación...")
                
                # Reindexar a fechas completas del rango
                fecha_completa = pd.date_range(start=fecha_desde, end=fecha_hasta, freq='D')
                df_reindexed = df_precios_limpio.reindex(fecha_completa)
                
                # Aplicar forward fill y backward fill
                df_filled = df_reindexed.fillna(method='ffill').fillna(method='bfill')
                
                # Quitar fines de semana y días sin datos en ninguna serie
                df_aligned = df_filled.dropna()
                
                if len(df_aligned) < 30:
                    st.error("❌ No hay suficientes datos después de la alineación")
                    return None, None, None
                
                st.info(f"✅ Datos interpolados: {len(df_aligned)} observaciones")
            
            # Paso 5: Calcular retornos
            returns = df_aligned.pct_change().dropna()
            
            # Verificar que los retornos sean válidos
            if returns.empty or len(returns) < 20:
                st.error("❌ No hay suficientes retornos válidos para el análisis")
                return None, None, None
            
            # Verificar que no haya retornos constantes
            returns_std = returns.std()
            columnas_constantes = returns_std[returns_std == 0].index.tolist()
            
            if len(columnas_constantes) > 0:
                st.warning(f"⚠️ Removiendo activos con retornos constantes: {columnas_constantes}")
                returns = returns.drop(columns=columnas_constantes)
                df_aligned = df_aligned.drop(columns=columnas_constantes)
            
            if len(returns.columns) < 2:
                st.error("❌ Después de filtrar, no quedan suficientes activos para análisis")
                return None, None, None
            
            # Paso 6: Calcular estadísticas finales
            mean_returns = returns.mean() * 252  # Anualizar
            cov_matrix = returns.cov() * 252     # Anualizar
            
            # Verificar que la matriz de covarianza sea válida
            if np.any(np.isnan(cov_matrix.values)) or np.any(np.isinf(cov_matrix.values)):
                st.error("❌ Matriz de covarianza contiene valores inválidos")
                return None, None, None
            
            # Mostrar estadísticas finales
            st.info(f"📊 Datos finales: {len(returns.columns)} activos, {len(returns)} observaciones de retornos")
            
            with st.expander("🔍 Debug - Estadísticas de retornos"):
                st.write("**Retornos medios anualizados:**")
                for col in mean_returns.index:
                    st.text(f"{col}: {mean_returns[col]:.2%}")
                
                st.write("**Volatilidades anualizadas:**")
                vol_annual = returns.std() * np.sqrt(252)
                for col in vol_annual.index:
                    st.text(f"{col}: {vol_annual[col]:.2%}")
            
            return mean_returns, cov_matrix, df_aligned
            
        except Exception as e:
            st.error(f"❌ Error en procesamiento de datos: {str(e)}")
            return None, None, None
        
    except Exception as e:
        st.error(f"❌ Error crítico obteniendo datos históricos: {str(e)}")
        return None, None, None

def obtener_serie_historica(simbolo, mercado, fecha_desde, fecha_hasta, ajustada, bearer_token):
    """
    Obtiene la serie histórica de precios para un símbolo y mercado específico.
    Usa el mapeo de mercados de IOL y busca automáticamente la clase 'D' si existe.
    """
    # Mapear nombres de mercados a los correctos de IOL
    mercados_mapping = {
        'BCBA': 'bCBA',
        'NYSE': 'nYSE',
        'NASDAQ': 'nASDAQ',
        'ROFEX': 'rOFEX',
        'Merval': 'bCBA'
    }
    mercado_correcto = mercados_mapping.get(mercado, mercado)
    # Buscar clase D si es bono
    clase_d = obtener_clase_d(simbolo, mercado_correcto, bearer_token)
    simbolo_final = clase_d if clase_d else simbolo
    url = f"https://api.invertironline.com/api/v2/{mercado_correcto}/Titulos/{simbolo_final}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error en la solicitud de serie histórica para {simbolo_final} en {mercado_correcto}: {response.status_code}")
        print(response.text)
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
        'Merval': 'bCBA'
    }
    mercado_correcto = mercados_mapping.get(mercado, mercado)
    url = f"https://api.invertironline.com/api/v2/{mercado_correcto}/Titulos/{simbolo}/Clases"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        clases = response.json()
        for clase in clases:
            if clase.get('simbolo', '').endswith('D'):
                return clase['simbolo']
        return None
    else:
        print(f"Error al buscar clases para {simbolo} en {mercado_correcto}: {response.status_code}")
        print(response.text)
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
    
    # Crear tabs para diferentes análisis
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Resumen", 
        "💰 Estado de Cuenta", 
        "🎯 Optimización", 
        "📊 Análisis Técnico",
        "💱 Cotizaciones"
    ])
    
    with tab1:
        # Obtener portafolio
        with st.spinner("Cargando portafolio..."):
            portafolio = obtener_portafolio(token_acceso, id_cliente)
        
        if portafolio:
            mostrar_resumen_portafolio(portafolio)
        else:
            st.warning("No se pudo obtener el portafolio del cliente")
    
    with tab2:
        # Mostrar estado de cuenta - intentar primero con ID cliente, luego sin ID
        with st.spinner("Cargando estado de cuenta..."):
            estado_cuenta = obtener_estado_cuenta(token_acceso, id_cliente)
        
        if estado_cuenta:
            mostrar_estado_cuenta(estado_cuenta)
        else:
            st.warning("No se pudo obtener el estado de cuenta")
            
            # Ofrecer alternativa
            st.markdown("#### 🔄 Intentar con endpoint alternativo")
            if st.button("🚀 Probar endpoint directo"):
                with st.spinner("Probando endpoint directo..."):
                    estado_cuenta_directo = obtener_estado_cuenta(token_acceso, None)
                    if estado_cuenta_directo:
                        mostrar_estado_cuenta(estado_cuenta_directo)
                    else:
                        st.error("❌ No se pudo obtener el estado de cuenta con ningún método")

    with tab3:
        # Optimización de portafolio
        if 'portafolio' not in locals():
            with st.spinner("Cargando portafolio para optimización..."):
                portafolio = obtener_portafolio(token_acceso, id_cliente)
        
        if portafolio:
            mostrar_optimizacion_portafolio(portafolio, token_acceso, fecha_desde, fecha_hasta)
        else:
            st.warning("No se pudo obtener el portafolio para optimización")
    
    with tab4:
        # Análisis técnico
        st.markdown("### 📊 Análisis Técnico")
        st.info("🚧 Funcionalidad en desarrollo")
        
        # Placeholder para análisis técnico futuro
        if 'portafolio' not in locals():
            portafolio = obtener_portafolio(token_acceso, id_cliente)
        
        if portafolio:
            activos = portafolio.get('activos', [])
            if activos:
                simbolos = [activo.get('titulo', {}).get('simbolo', '') for activo in activos]
                simbolos = [s for s in simbolos if s]
                
                if simbolos:
                    simbolo_seleccionado = st.selectbox(
                        "Seleccione un activo para análisis técnico:",
                        options=simbolos
                    )
                    
                    if simbolo_seleccionado:
                        st.info(f"Análisis técnico para {simbolo_seleccionado} estará disponible próximamente")
    
    with tab5:
        # Cotizaciones y mercado
        mostrar_cotizaciones_mercado(token_acceso)

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
    
    # Alertas y recomendaciones
    if total_general == 0 and total_en_pesos == 0:
        st.warning("⚠️ No se encontraron saldos en las cuentas")
        st.markdown("#### 💡 Posibles causas:")
        st.markdown("""
        1. **Cuentas vacías**: Las cuentas pueden no tener saldos actualmente
        2. **Permisos**: Verificar que tenga permisos para ver estados de cuenta
        3. **Sincronización**: Los datos pueden estar siendo actualizados por IOL
        """)
    
    elif total_disponible == 0 and total_titulos_valorizados > 0:
        st.info("ℹ️ **Cartera invertida**: Todo el capital está invertido en títulos")
    
    elif total_disponible > 0:
        porcentaje_invertido = (total_titulos_valorizados / total_general * 100) if total_general > 0 else 0
        if porcentaje_invertido < 50:
            st.info(f"💡 **Oportunidad de inversión**: Tiene {porcentaje_invertido:.1f}% invertido. Considere revisar oportunidades de inversión.")
        else:
            st.success(f"✅ **Buena distribución**: Tiene {porcentaje_invertido:.1f}% de su capital invertido.")

def mostrar_cotizaciones_mercado(token_acceso):
    """
    Muestra cotizaciones y datos de mercado
    """
    st.markdown("### 💱 Cotizaciones y Mercado")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💰 Cotización MEP")
        
        # Formulario para consultar MEP
        with st.form("mep_form"):
            simbolo_mep = st.text_input("Símbolo para MEP", value="AL30", help="Ej: AL30, GD30, etc.")
            id_plazo_compra = st.number_input("ID Plazo Compra", value=1, min_value=1)
            id_plazo_venta = st.number_input("ID Plazo Venta", value=1, min_value=1)
            
            if st.form_submit_button("Consultar MEP"):
                if simbolo_mep:
                    with st.spinner("Consultando cotización MEP..."):
                        cotizacion_mep = obtener_cotizacion_mep(
                            token_acceso, simbolo_mep, id_plazo_compra, id_plazo_venta
                        )
                    
                    if cotizacion_mep:
                        st.success("✅ Cotización MEP obtenida")
                        
                        # Mostrar datos de MEP
                        if isinstance(cotizacion_mep, dict):
                            # Extraer precio si está disponible
                            precio_mep = cotizacion_mep.get('precio', cotizacion_mep.get('cotizacion', 'N/A'))
                            
                            col_mep1, col_mep2 = st.columns(2)
                            col_mep1.metric("Símbolo", simbolo_mep)
                            col_mep2.metric("Precio MEP", f"${precio_mep}" if precio_mep != 'N/A' else 'N/A')
                        
                        with st.expander("Ver detalles MEP"):
                            st.json(cotizacion_mep)
                    else:
                        st.error("❌ No se pudo obtener la cotización MEP")
    
    with col2:
        st.markdown("#### 🏦 Tasas de Caución")
        
        if st.button("🔄 Actualizar Tasas de Caución"):
            with st.spinner("Consultando tasas de caución..."):
                tasas_caucion = obtener_tasas_caucion(token_acceso)
            
            if tasas_caucion:
                st.success("✅ Tasas de caución obtenidas")
                
                # Mostrar tasas si es una lista
                if isinstance(tasas_caucion, list) and tasas_caucion:
                    df_tasas = pd.DataFrame(tasas_caucion)
                    
                    # Mostrar solo columnas relevantes si están disponibles
                    columnas_relevantes = ['simbolo', 'tasa', 'bid', 'offer', 'ultimo']
                    columnas_disponibles = [col for col in columnas_relevantes if col in df_tasas.columns]
                    
                    if columnas_disponibles:
                        st.dataframe(df_tasas[columnas_disponibles].head(10))
                    else:
                        st.dataframe(df_tasas.head(10))
                
                with st.expander("Ver datos completos de caución"):
                    st.json(tasas_caucion)
            else:
                st.error("❌ No se pudieron obtener las tasas de caución")

# Clase PortfolioManager simplificada para compatibilidad
class PortfolioManager:
    """
    Clase simplificada para manejo de portafolio y optimización
    """
    def __init__(self, symbols, token, fecha_desde, fecha_hasta):
        self.symbols = symbols
        self.token = token
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.data_loaded = False
        self.returns = None
        self.prices = None
    
    def load_data(self):
        """
        Carga datos históricos para los símbolos del portafolio
        """
        try:
            mean_returns, cov_matrix, df_precios = get_historical_data_for_optimization(
                self.token, self.symbols, self.fecha_desde, self.fecha_hasta
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
            st.error(f"Error en optimización: {str(e)}. Usando pesos iguales.")
            return np.array([1/n_assets] * n_assets)

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
        
        # Agregar líneas de métricas importantes
        fig.add_vline(x=self.mean_daily, line_dash="dash", line_color="red", 
                     annotation_text=f"Media: {self.mean_daily:.4f}")
        fig.add_vline(x=self.var_95, line_dash="dash", line_color="orange", 
                     annotation_text=f"VaR 95%: {self.var_95:.4f}")
        
        fig.update_layout(
            title=f"{title}",
            xaxis_title="Retorno",
            yaxis_title="Frecuencia",
            showlegend=False
        )
        
        return fig

# Enhanced Portfolio Management Classes
class manager:
    def __init__(self, rics, notional, token_portador=None, fecha_desde=None, fecha_hasta=None):
        self.rics = rics
        self.notional = notional
        self.token_portador = token_portador
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.timeseries = None
        self.returns = None
        self.cov_matrix = None
        self.mean_returns = None
        self.risk_free_rate = 0.40  # Tasa libre de riesgo anual
        self.data_loaded = False

    def load_intraday_timeseries(self, ticker):
        """
        Carga series históricas usando las mismas funciones que para estadísticas del portafolio
        """
        if self.token_portador and self.fecha_desde and self.fecha_hasta:
            # Usar la función principal de obtención de datos históricos
            fecha_desde_str = self.fecha_desde.strftime('%Y-%m-%d') if hasattr(self.fecha_desde, 'strftime') else str(self.fecha_desde)
            fecha_hasta_str = self.fecha_hasta.strftime('%Y-%m-%d') if hasattr(self.fecha_hasta, 'strftime') else str(self.fecha_hasta)
            
            # Determinar tipo de instrumento usando la misma lógica
            if ticker.upper() == "ADCGLOA":
                mercados = ['FCI']
            elif ticker.upper().startswith("AE") or ticker.upper().endswith("D") or ticker.upper().endswith("C") or ticker.upper().endswith("O"):
                # Bonos (puedes ajustar la lógica según nomenclatura)
                mercados = ['bCBA']
            else:
                mercados = ['bCBA', 'nYSE', 'nASDAQ', 'rOFEX', 'Opciones', 'FCI']
            
            # Intentar obtener datos de cada mercado
            for mercado in mercados:
                try:
                    simbolo_consulta = ticker
                    if mercado not in ['Opciones', 'FCI']:
                        clase_d = obtener_clase_d(ticker, mercado, self.token_portador)
                        if clase_d:
                            simbolo_consulta = clase_d

                    serie = obtener_serie_historica_iol(
                        self.token_portador, mercado, simbolo_consulta,
                        fecha_desde_str, fecha_hasta_str
                    )

                    if serie is not None and len(serie) > 10:
                        # Verificar que la serie tenga valores válidos y variación
                        serie_clean = serie.dropna()
                        if len(serie_clean) > 10 and serie_clean.nunique() > 1 and serie_clean.std() > 0:
                            return serie
                except Exception:
                    continue
            
            # Fallback a yfinance si IOL no funciona
            try:
                serie_yf = obtener_datos_alternativos_yfinance(
                    ticker, self.fecha_desde, self.fecha_hasta
                )
                if serie_yf is not None and len(serie_yf) > 10:
                    serie_yf_clean = serie_yf.dropna()
                    if len(serie_yf_clean) > 10 and serie_yf_clean.nunique() > 1 and serie_yf_clean.std() > 0:
                        return serie_yf
            except Exception:
                pass        
        return None

    def synchronise_timeseries(self):
        """
        Sincroniza las series temporales usando SIEMPRE get_historical_data_for_optimization,
        igual que las estadísticas del portafolio.
        """
        if self.token_portador and self.fecha_desde and self.fecha_hasta:
            mean_returns, cov_matrix, df_precios = get_historical_data_for_optimization(
                self.token_portador, self.rics, self.fecha_desde, self.fecha_hasta
            )
            if mean_returns is not None and cov_matrix is not None and df_precios is not None:
                self.timeseries = df_precios
                self.returns = df_precios.pct_change().dropna()
                self.cov_matrix = cov_matrix
                self.mean_returns = mean_returns
                self.data_loaded = True
                return True
            else:
                st.error("❌ No se pudieron sincronizar las series temporales")
                return False

        # Fallback al método original si no hay token
        dic_timeseries = {}
        for ric in self.rics:
            serie = self.load_intraday_timeseries(ric)
            if serie is not None:
                dic_timeseries[ric] = serie

        if dic_timeseries:
            self.timeseries = pd.DataFrame(dic_timeseries)
            return True
        return False

    def compute_covariance(self):
        """
        Computa la matriz de covarianza usando datos sincronizados
        """
        if not self.data_loaded:
            success = self.synchronise_timeseries()
            if not success:
                return None, None
        
        if self.cov_matrix is not None and self.mean_returns is not None:
            return self.cov_matrix, self.mean_returns
        
        # Método de respaldo si no se cargaron datos con la función principal
        if self.timeseries is not None and len(self.timeseries) > 0:
            # Calcular retornos logarítmicos
            returns_matrix = {}
            for ric in self.rics:
                if ric in self.timeseries.columns:
                    prices = self.timeseries[ric].dropna()
                    if len(prices) > 1:
                        returns = np.log(prices / prices.shift(1)).dropna()
                        if len(returns) > 10 and returns.std() > 0:
                            returns_matrix[ric] = returns
            
            if len(returns_matrix) >= 2:
                # Convertir a DataFrame para alinear fechas
                self.returns = pd.DataFrame(returns_matrix)
                
                # Calcular matriz de covarianza y retornos medios
                self.cov_matrix = self.returns.cov() * 252  # Anualizar
                self.mean_returns = self.returns.mean() * 252  # Anualizar
                
                return self.cov_matrix, self.mean_returns
        
        return None, None

    def compute_portfolio(self, portfolio_type=None, target_return=None):
        cov_matrix, mean_returns = self.compute_covariance()
        
        if cov_matrix is None or mean_returns is None:
            st.error("❌ No se pudo calcular la matriz de covarianza")
            return None
            
        n_assets = len(mean_returns)
        if n_assets < 2:
            st.error("❌ Se necesitan al menos 2 activos para optimización")
            return None
            
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        if portfolio_type == 'equi-weight':
            # Pesos iguales
            weights = np.ones(n_assets) / n_assets
            return self._create_output(weights, mean_returns.index)
        
        # Configurar restricciones según el tipo de portafolio
        constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        
        if portfolio_type == 'min-variance-l1':
            # Minimizar varianza con restricción L1
            constraints.append({'type': 'ineq', 'fun': lambda x: 1 - np.sum(np.abs(x))})
        elif portfolio_type == 'min-variance-l2':
            # Minimizar varianza con restricción L2
            constraints.append({'type': 'ineq', 'fun': lambda x: 1 - np.sum(x**2)})
        elif portfolio_type == 'markowitz' and target_return is not None:
            # Optimización con retorno objetivo
            constraints.append({
                'type': 'eq', 
                'fun': lambda x: np.sum(mean_returns.values * x) - target_return
            })
        
        try:
            if portfolio_type == 'markowitz' and target_return is None:
                # Maximizar Sharpe Ratio
                def neg_sharpe_ratio(weights):
                    port_ret = np.sum(mean_returns.values * weights)
                    port_vol = np.sqrt(portfolio_variance(weights, cov_matrix.values))
                    if port_vol == 0:
                        return np.inf
                    return -(port_ret - self.risk_free_rate) / port_vol
                
                objective = neg_sharpe_ratio
            else:
                # Minimizar varianza
                objective = lambda x: portfolio_variance(x, cov_matrix.values)
            
            # Optimización
            initial_guess = np.ones(n_assets) / n_assets
            
            result = op.minimize(
                objective, 
                x0=initial_guess,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000, 'ftol': 1e-9}
            )
            
            if result.success:
                return self._create_output(result.x, mean_returns.index)
            else:
                st.warning(f"⚠️ Optimización no convergió: {result.message}. Usando pesos iguales.")
                weights = np.ones(n_assets) / n_assets
                return self._create_output(weights, mean_returns.index)
                
        except Exception as e:
            st.error(f"❌ Error en optimización: {str(e)}. Usando pesos iguales.")
            weights = np.ones(n_assets) / n_assets
            return self._create_output(weights, mean_returns.index)

    def _create_output(self, weights, asset_names):
        """Crea un objeto output con los pesos optimizados"""
        if self.returns is None or len(self.returns) == 0:
            st.error("❌ No hay datos de retornos disponibles")
            return None
            
        try:
            # Asegurar que los nombres de activos coincidan
            common_assets = [asset for asset in asset_names if asset in self.returns.columns]
            if len(common_assets) != len(weights):
                st.warning(f"⚠️ Ajustando pesos para {len(common_assets)} activos comunes")
                # Reajustar pesos para activos comunes
                weights = weights[:len(common_assets)]
                weights = weights / weights.sum()  # Renormalizar
                asset_names = common_assets
            
            # Calcular retornos del portafolio
            portfolio_returns = self.returns[common_assets].dot(weights)
            
            if len(portfolio_returns) == 0:
                st.error("❌ No se pudieron calcular retornos del portafolio")
                return None
            
            # Crear objeto output
            port_output = output(portfolio_returns.values, self.notional)
            port_output.weights = weights
            port_output.asset_names = list(asset_names)
            
            # Calcular métricas del portafolio
            port_ret = np.sum(self.mean_returns[common_assets].values * weights)
            port_vol = np.sqrt(portfolio_variance(weights, self.cov_matrix.loc[common_assets, common_assets].values))
            
            # Actualizar métricas anualizadas
            port_output.return_annual = port_ret
            port_output.volatility_annual = port_vol
            
            # Crear DataFrame de asignación
            volatilities = []
            returns_list = []
            for asset in common_assets:
                if asset in self.returns.columns:
                    vol = self.returns[asset].std() * np.sqrt(252)
                    ret = self.mean_returns[asset] if asset in self.mean_returns.index else 0
                else:
                    vol = 0
                    ret = 0
                volatilities.append(vol)
                returns_list.append(ret)
            
            port_output.dataframe_allocation = pd.DataFrame({
                'rics': common_assets,
                'weights': weights,
                'volatilities': volatilities,
                'returns': returns_list
            })
            
            return port_output
            
        except Exception as e:
            st.error(f"❌ Error creando output del portafolio: {str(e)}")
            return None
