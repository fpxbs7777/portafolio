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
import streamlit.components.v1 as components
import seaborn as sns
import matplotlib.pyplot as plt

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

def parse_datetime_flexible(datetime_string):
    if not datetime_string:
        return None
    
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

def obtener_serie_historica_iol(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="ajustada"):
    """
    Función mejorada para obtener series históricas de todos los tipos de activos en IOL
    Maneja: Acciones, Bonos, CEDEARs, ADRs, FCIs, Opciones, etc.
    Con manejo robusto de errores del servidor
    """
    
    # Mapeo de mercados y tipos de instrumentos
    mercados_mapping = {
        'BCBA': 'bCBA',
        'NYSE': 'nYSE', 
        'NASDAQ': 'nASDAQ',
        'ROFEX': 'rOFEX',
        'Merval': 'bCBA',
        'bCBA': 'bCBA',
        'nYSE': 'nYSE',
        'nASDAQ': 'nASDAQ',
        'rOFEX': 'rOFEX'
    }
    
    mercado_correcto = mercados_mapping.get(mercado, mercado)
    
    # Configurar URL según el tipo de instrumento
    if mercado == "Opciones" or "opcion" in simbolo.lower():
        url = f"https://api.invertironline.com/api/v2/Opciones/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    elif mercado == "FCI" or simbolo.startswith('F') or 'fondo' in simbolo.lower():
        url = f"https://api.invertironline.com/api/v2/FCI/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    else:
        # Para acciones, bonos, CEDEARs, ADRs, etc.
        url = f"https://api.invertironline.com/api/v2/{mercado_correcto}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'application/json'
    }
    
    # Implementar reintentos con backoff
    max_retries = 3
    for attempt in range(max_retries):
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
                        # Buscar precio en múltiples campos según el tipo de instrumento
                        precio = None
                        campos_precio = [
                            'ultimoPrecio', 'ultimo', 'price', 'close',
                            'cierreAnterior', 'precioAnterior',
                            'precioPromedio', 'promedioVolumen',
                            'apertura', 'opening',
                            'maximo', 'max', 'high',
                            'minimo', 'min', 'low',
                            'valorCuotaparte'  # Para FCIs
                        ]
                        
                        for campo in campos_precio:
                            if campo in item and item[campo] is not None:
                                try:
                                    precio_temp = float(item[campo])
                                    if precio_temp > 0:
                                        precio = precio_temp
                                        break
                                except (ValueError, TypeError):
                                    continue
                        
                        # Buscar fecha en múltiples campos
                        fecha_str = None
                        campos_fecha = [
                            'fechaHora', 'fecha', 'date', 'datetime',
                            'fechaCotizacion', 'fechaOperacion'
                        ]
                        
                        for campo in campos_fecha:
                            if campo in item and item[campo] is not None:
                                fecha_str = item[campo]
                                break
                        
                        if precio is not None and precio > 0 and fecha_str:
                            fecha_parsed = parse_datetime_flexible(fecha_str)
                            if fecha_parsed is not None:
                                precios.append(precio)
                                fechas.append(fecha_parsed)
                                
                    except Exception as e:
                        continue
                
                if precios and fechas:
                    serie = pd.Series(precios, index=fechas)
                    serie = serie.sort_index()
                    serie = serie[~serie.index.duplicated(keep='last')]
                    return serie
                else:
                    return None
                    
            elif response.status_code == 400:
                # Bad Request - símbolo o parámetros inválidos
                return None
            elif response.status_code == 401:
                # Unauthorized - token expirado
                return None
            elif response.status_code == 500:
                # Server Error - reintentar
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # Backoff exponencial
                    continue
                else:
                    return None
            else:
                return None
                
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                import time
                time.sleep(1)
                continue
            else:
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                import time
                time.sleep(1)
                continue
            else:
                return None
    
    return None

def get_historical_data_for_optimization(token_portador, simbolos, fecha_desde, fecha_hasta):
    """
    Función mejorada para obtener datos históricos con mejor manejo de errores y recuperación
    """
    try:
        df_precios = pd.DataFrame()
        simbolos_exitosos = []
        simbolos_fallidos = []
        detalles_errores = {}
        
        fecha_desde_str = fecha_desde.strftime('%Y-%m-%d')
        fecha_hasta_str = fecha_hasta.strftime('%Y-%m-%d')
        
        progress_bar = st.progress(0)
        total_simbolos = len(simbolos)
        
        for idx, simbolo in enumerate(simbolos):
            progress_bar.progress((idx + 1) / total_simbolos, text=f"Procesando {simbolo}...")
            
            # Detectar tipo de instrumento
            tipo_instrumento = detectar_tipo_instrumento(simbolo)
            
            # Estrategia específica por tipo de instrumento
            serie_obtenida = False
            
            if tipo_instrumento == 'FCI':
                # Estrategia específica para FCIs
                try:
                    serie = obtener_serie_historica_iol(
                        token_portador, 'FCI', simbolo, 
                        fecha_desde_str, fecha_hasta_str
                    )
                    
                    if serie is not None and len(serie) > 10 and serie.nunique() > 1:
                        df_precios[simbolo] = serie
                        simbolos_exitosos.append(simbolo)
                        serie_obtenida = True
                        
                except Exception as e:
                    detalles_errores[f"{simbolo}_FCI"] = str(e)
            
            elif tipo_instrumento == 'Opciones':
                # Estrategia específica para Opciones
                try:
                    serie = obtener_serie_historica_iol(
                        token_portador, 'Opciones', simbolo, 
                        fecha_desde_str, fecha_hasta_str
                    )
                    
                    if serie is not None and len(serie) > 10 and serie.nunique() > 1:
                        df_precios[simbolo] = serie
                        simbolos_exitosos.append(simbolo)
                        serie_obtenida = True
                        
                except Exception as e:
                    detalles_errores[f"{simbolo}_Opciones"] = str(e)
            
            else:
                # Estrategia para acciones, bonos, CEDEARs, etc.
                mercados_prioritarios = ['bCBA', 'nYSE', 'nASDAQ', 'rOFEX']
                
                # Si es un bono, priorizar BCBA
                if tipo_instrumento == 'BONO':
                    mercados_prioritarios = ['bCBA', 'rOFEX', 'nYSE', 'nASDAQ']
                # Si es CEDEAR, priorizar NYSE/NASDAQ
                elif tipo_instrumento == 'CEDEAR':
                    mercados_prioritarios = ['nYSE', 'nASDAQ', 'bCBA', 'rOFEX']
                
                for mercado in mercados_prioritarios:
                    try:
                        simbolo_consulta = simbolo
                        
                        # Para bonos, intentar obtener clase D
                        if tipo_instrumento == 'BONO' and mercado in ['bCBA', 'rOFEX']:
                            clase_d = obtener_clase_d(simbolo, mercado, token_portador)
                            if clase_d and clase_d != simbolo:
                                simbolo_consulta = clase_d
                        
                        serie = obtener_serie_historica_iol(
                            token_portador, mercado, simbolo_consulta, 
                            fecha_desde_str, fecha_hasta_str
                        )
                        
                        if serie is not None and len(serie) > 10 and serie.nunique() > 1:
                            df_precios[simbolo_consulta] = serie
                            simbolos_exitosos.append(simbolo_consulta)
                            serie_obtenida = True
                            break
                            
                    except Exception as e:
                        detalles_errores[f"{simbolo}_{mercado}"] = str(e)
                        continue
            
            # Fallback a yfinance si no se obtuvo la serie
            if not serie_obtenida:
                try:
                    serie_yf = obtener_datos_alternativos_yfinance(
                        simbolo, fecha_desde, fecha_hasta
                    )
                    if serie_yf is not None and len(serie_yf) > 10 and serie_yf.nunique() > 1:
                        df_precios[simbolo] = serie_yf
                        simbolos_exitosos.append(simbolo)
                        serie_obtenida = True
                except Exception as e:
                    detalles_errores[f"{simbolo}_yfinance"] = str(e)
            
            if not serie_obtenida:
                simbolos_fallidos.append(simbolo)
        
        progress_bar.empty()
        
        # Mostrar resultados mejorados
        if simbolos_exitosos:
            st.success(f"✅ Datos obtenidos para {len(simbolos_exitosos)} activos: {', '.join(simbolos_exitosos[:5])}{'...' if len(simbolos_exitosos) > 5 else ''}")
        
        if simbolos_fallidos:
            st.warning(f"⚠️ No se pudieron obtener datos para {len(simbolos_fallidos)} activos: {', '.join(simbolos_fallidos[:3])}{'...' if len(simbolos_fallidos) > 3 else ''}")
            
            # Mostrar detalles de errores en expander
            with st.expander("🔍 Ver detalles de errores"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Errores de servidor (400/500):**")
                    server_errors = [k for k in detalles_errores.keys() if '400' in str(detalles_errores[k]) or '500' in str(detalles_errores[k]) or 'Server Error' in str(detalles_errores[k])]
                    if server_errors:
                        for error_key in server_errors[:5]:
                            st.text(f"• {error_key}")
                    else:
                        st.text("Ninguno")
                
                with col2:
                    st.markdown("**Otros errores:**")
                    other_errors = [k for k in list(detalles_errores.keys())[:5] if k not in server_errors]
                    if other_errors:
                        for error_key in other_errors:
                            st.text(f"• {error_key}: {str(detalles_errores[error_key])[:50]}...")
                    else:
                        st.text("Ninguno")
        
        # Verificar si tenemos datos suficientes
        if len(simbolos_exitosos) == 0:
            st.error("❌ No se pudieron obtener datos para ningún activo. Revise la conectividad o pruebe con fechas diferentes.")
            return None, None, None
        
        if len(simbolos_exitosos) == 1:
            st.warning("⚠️ Solo se obtuvo datos para 1 activo. Se necesitan al menos 2 para análisis de portafolio.")
            # Intentar análisis de activo individual
            return None, None, df_precios
        
        # Procesar y limpiar datos
        try:
            # Usar métodos compatibles con diferentes versiones de pandas
            try:
                df_precios_filled = df_precios.fillna(method='ffill').fillna(method='bfill')
            except:
                df_precios_filled = df_precios.ffill().bfill()
            
            try:
                df_precios_interpolated = df_precios.interpolate(method='time', limit_direction='both')
            except:
                df_precios_interpolated = df_precios.interpolate(method='time')
            
            if not df_precios_filled.dropna().empty:
                df_precios = df_precios_filled.dropna()
            elif not df_precios_interpolated.dropna().empty:
                df_precios = df_precios_interpolated.dropna()
            else:
                df_precios = df_precios.dropna()
                
        except Exception as e:
            # Fallback a métodos básicos
            try:
                df_precios = df_precios.fillna(method='ffill').fillna(method='bfill').dropna()
            except:
                df_precios = df_precios.ffill().bfill().dropna()
        
        if df_precios.empty:
            st.error("❌ No hay datos suficientes después del procesamiento")
            return None, None, None
        
        # Calcular retornos
        returns = df_precios.pct_change().dropna()
        
        if returns.empty or len(returns) < 10:  # Reducir umbral mínimo
            st.error(f"❌ Datos insuficientes para calcular retornos ({len(returns)} observaciones, mínimo 10)")
            return None, None, df_precios
        
        # Eliminar activos con varianza cero
        if (returns.std() == 0).any():
            columnas_constantes = returns.columns[returns.std() == 0].tolist()
            if columnas_constantes:
                st.warning(f"⚠️ Eliminando activos con precio constante: {', '.join(columnas_constantes)}")
                returns = returns.drop(columns=columnas_constantes)
                df_precios = df_precios.drop(columns=columnas_constantes)
        
        if len(returns.columns) < 2:
            st.error("❌ Se necesitan al menos 2 activos con varianza no nula para análisis de portafolio")
            return None, None, df_precios
        
        # Calcular estadísticas
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        
        # Verificar que la matriz de covarianza sea válida
        if cov_matrix.isnull().any().any():
            st.error("❌ Matriz de covarianza contiene valores nulos")
            return None, None, df_precios
        
        if (cov_matrix == 0).all().all():
            st.error("❌ Matriz de covarianza es cero")
            return None, None, df_precios
        
        # Verificar que la matriz sea positiva definida
        try:
            eigenvals = np.linalg.eigvals(cov_matrix.values)
            if np.any(eigenvals <= 0):
                st.warning("⚠️ Matriz de covarianza no es positiva definida. Aplicando regularización.")
                # Aplicar regularización
                regularization = 1e-6
                cov_matrix += regularization * np.eye(len(cov_matrix))
        except Exception as e:
            st.warning(f"⚠️ Error verificando matriz de covarianza: {str(e)}")
        
        st.info(f"📊 Datos procesados: {len(df_precios)} observaciones para {len(df_precios.columns)} activos")
        
        return mean_returns, cov_matrix, df_precios
        
    except Exception as e:
        st.error(f"❌ Error inesperado en get_historical_data_for_optimization: {str(e)}")
        return None, None, None

# Agregar clases faltantes
class PortfolioAdvancedAnalyzer:
    def __init__(self, symbols, weights, token, fecha_desde, fecha_hasta):
        self.symbols = symbols
        self.weights = np.array(weights)
        self.token = token
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.individual_analyses = {}
        self.portfolio_returns = None
        self.portfolio_distribution = None
        
    def analyze_individual_assets(self):
        """Analiza cada activo individualmente"""
        analyses = {}
        
        progress_bar = st.progress(0)
        total_assets = len(self.symbols)
        
        for idx, symbol in enumerate(self.symbols):
            progress_bar.progress((idx + 1) / total_assets, 
                                text=f"Analizando {symbol}...")
            
            analyzer = IndividualAssetAnalyzer(
                self.token, symbol, self.fecha_desde, self.fecha_hasta
            )
            
            if analyzer.load_data():
                analysis = analyzer.analyze()
                if analysis:
                    analyses[symbol] = analyzer.get_complete_analysis()
        
        progress_bar.empty()
        self.individual_analyses = analyses
        return analyses
    
    def compute_portfolio_distribution(self):
        """Calcula la distribución del portafolio ponderado"""
        if not self.individual_analyses:
            return None
            
        # Obtener retornos de todos los activos
        returns_matrix = []
        valid_symbols = []
        
        for symbol in self.symbols:
            if symbol in self.individual_analyses:
                analyzer = IndividualAssetAnalyzer(
                    self.token, symbol, self.fecha_desde, self.fecha_hasta
                )
                if analyzer.load_data():
                    returns_matrix.append(analyzer.returns)
                    valid_symbols.append(symbol)
        
        if len(returns_matrix) > 0:
            # Alinear fechas y calcular retornos del portafolio
            df_returns = pd.concat(returns_matrix, axis=1, keys=valid_symbols)
            df_returns = df_returns.dropna()
            
            # Ajustar pesos para activos válidos
            valid_weights = self.weights[:len(valid_symbols)]
            valid_weights = valid_weights / valid_weights.sum()  # Normalizar
            
            # Calcular retornos del portafolio
            self.portfolio_returns = (df_returns * valid_weights).sum(axis=1)
            
            # Análisis de distribución del portafolio
            self.portfolio_distribution = Distribution(self.portfolio_returns, 100000)
            self.portfolio_distribution.compute_stats()
            self.portfolio_distribution.analyze_best_distribution()
            
            return self.portfolio_distribution
        
        return None
    
    def generate_comparison_report(self):
        """Genera reporte comparativo de activos"""
        if not self.individual_analyses:
            return None
            
        comparison_data = []
        
        for symbol, analysis in self.individual_analyses.items():
            metrics = analysis['metrics']
            comparison_data.append({
                'Símbolo': symbol,
                'Retorno Anual': f"{metrics['Media Anual']:.2%}" if metrics['Media Anual'] else 'N/A',
                'Volatilidad': f"{metrics['Volatilidad Anual']:.2%}" if metrics['Volatilidad Anual'] else 'N/A',
                'Sharpe': f"{metrics['Ratio Sharpe']:.3f}" if metrics['Ratio Sharpe'] else 'N/A',
                'VaR 95%': f"{metrics['VaR 95%']:.3f}" if metrics['VaR 95%'] else 'N/A',
                'Skewness': f"{metrics['Skewness']:.3f}" if metrics['Skewness'] else 'N/A',
                'Kurtosis': f"{metrics['Kurtosis']:.3f}" if metrics['Kurtosis'] else 'N/A',
                'Distribución': analysis['best_distribution'] or 'N/A',
                'Es Normal': '✅' if metrics['Es Normal'] else '❌'
            })
        
        return pd.DataFrame(comparison_data)

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
    def __init__(self, symbols, token, fecha_desde, fecha_hasta):
        self.symbols = symbols
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
            mean_returns, cov_matrix, df_precios = get_historical_data_for_optimization(
                self.token, self.symbols, self.fecha_desde, self.fecha_hasta
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
            elif df_precios is not None:
                # Solo datos de precios, sin matriz de covarianza
                self.prices = df_precios
                self.data_loaded = False
                st.warning("⚠️ Datos insuficientes para optimización completa, pero disponibles para análisis individual")
                return False
            else:
                return False
                
        except Exception as e:
            st.error(f"❌ Error cargando datos: {str(e)}")
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
            st.error(f"❌ Error en compute_portfolio: {str(e)}")
            return None

    def compute_efficient_frontier(self, target_return=0.08, include_min_variance=True):
        """Computa la frontera eficiente"""
        if not self.data_loaded or not self.manager:
            return None, None, None
        
        try:
            portfolios, returns, volatilities = compute_efficient_frontier(
                self.symbols, self.notional, target_return, include_min_variance, 
                self.prices.to_dict('series')
            )
            return portfolios, returns, volatilities
        except Exception as e:
            st.error(f"❌ Error calculando frontera eficiente: {str(e)}")
            return None, None, None

def mostrar_analisis_individual_activos(token_acceso, id_cliente):
    """Muestra análisis detallado de activos individuales con mejor información de tipos"""
    st.markdown("### 🔍 Análisis Individual de Activos")
    
    with st.spinner("Obteniendo portafolio..."):
        portafolio = obtener_portafolio(token_acceso, id_cliente)
    
    if not portafolio:
        st.warning("No se pudo obtener el portafolio del cliente")
        return
    
    activos = portafolio.get('activos', [])
    if not activos:
        st.warning("El portafolio está vacío")
        return
    
    # Crear lista de símbolos con información adicional
    simbolos_info = []
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo')
        if simbolo:
            tipo_detectado = detectar_tipo_instrumento(simbolo, titulo)
            descripcion = titulo.get('descripcion', 'Sin descripción')
            simbolos_info.append({
                'simbolo': simbolo,
                'tipo': tipo_detectado,
                'descripcion': descripcion
            })
    
    if not simbolos_info:
        st.warning("No se encontraron símbolos válidos")
        return
    
    # Mostrar información de tipos detectados
    st.subheader("📋 Activos Detectados")
    tipos_count = {}
    for info in simbolos_info:
        tipos_count[info['tipo']] = tipos_count.get(info['tipo'], 0) + 1
    
    cols = st.columns(len(tipos_count))
    for i, (tipo, count) in enumerate(tipos_count.items()):
        cols[i].metric(tipo, count)
    
    # Selector de activo con información adicional
    simbolos = [info['simbolo'] for info in simbolos_info]
    
    def format_option(simbolo):
        info = next((s for s in simbolos_info if s['simbolo'] == simbolo), {})
        return f"{simbolo} ({info.get('tipo', 'N/A')}) - {info.get('descripcion', '')[:30]}..."
    
    simbolo_seleccionado = st.selectbox(
        "Seleccione un activo para análisis detallado:",
        options=simbolos,
        format_func=format_option
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_desde = st.date_input(
            "Fecha desde:",
            value=st.session_state.fecha_desde,
            key="individual_fecha_desde"
        )
    
    with col2:
        fecha_hasta = st.date_input(
            "Fecha hasta:",
            value=st.session_state.fecha_hasta,
            key="individual_fecha_hasta"
        )
    
    if st.button("📊 Analizar Activo Individual", type="primary"):
        with st.spinner(f"Analizando {simbolo_seleccionado}..."):
            analyzer = IndividualAssetAnalyzer(
                token_acceso, simbolo_seleccionado, fecha_desde, fecha_hasta
            )
            
            if analyzer.load_data():
                distribution_analysis = analyzer.analyze()
                complete_analysis = analyzer.get_complete_analysis()
                
                if distribution_analysis and complete_analysis:
                    st.success("✅ Análisis completado")
                    
                    # Información del instrumento
                    st.subheader(f"📋 Información del Instrumento")
                    col1, col2, col3 = st.columns(3)
                    
                    col1.metric("Símbolo", simbolo_seleccionado)
                    col2.metric("Tipo Instrumento", complete_analysis['tipo_instrumento'])
                    col3.metric("Observaciones", complete_analysis['data_points'])
                    
                    # Métricas principales
                    st.subheader(f"📈 Métricas de {simbolo_seleccionado}")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    metrics = complete_analysis['metrics']
                    
                    col1.metric("Retorno Anual", f"{metrics['Media Anual']:.2%}")
                    col2.metric("Volatilidad Anual", f"{metrics['Volatilidad Anual']:.2%}")
                    col3.metric("Ratio Sharpe", f"{metrics['Ratio Sharpe']:.3f}")
                    col4.metric("VaR 95%", f"{metrics['VaR 95%']:.3f}")
                    
                    # Información de precios
                    st.subheader("💰 Información de Precios")
                    col1, col2, col3 = st.columns(3)
                    
                    price_info = complete_analysis['price_range']
                    col1.metric("Precio Mínimo", f"${price_info['min']:.2f}")
                    col2.metric("Precio Máximo", f"${price_info['max']:.2f}")
                    col3.metric("Precio Actual", f"${price_info['current']:.2f}")
                    
                    # Análisis de distribución
                    st.subheader("📊 Análisis de Distribución")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Mejor Distribución", 
                                complete_analysis['best_distribution'] or 'No determinada')
                        st.metric("Normalidad", 
                                "✅ Normal" if metrics['Es Normal'] else "❌ No Normal")
                        st.metric("Skewness", f"{metrics['Skewness']:.3f}")
                        st.metric("Kurtosis", f"{metrics['Kurtosis']:.3f}")
                    
                    with col2:
                        st.metric("Ganancia Máxima", f"{metrics['Ganancia Máxima']:.3f}")
                        st.metric("Pérdida Máxima", f"{metrics['Pérdida Máxima']:.3f}")
                        st.metric("Ganancia Esperada", f"{metrics['Ganancia Esperada']:.3f}")
                        st.metric("Pérdida Esperada", f"{metrics['Pérdida Esperada']:.3f}")
                    
                    # Gráficos
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Gráfico de precios
                        fig_prices = go.Figure()
                        fig_prices.add_trace(go.Scatter(
                            x=analyzer.prices.index,
                            y=analyzer.prices.values,
                            mode='lines',
                            name='Precio',
                            line=dict(color='#0d6efd')
                        ))
                        fig_prices.update_layout(
                            title=f"Evolución de Precios - {simbolo_seleccionado}",
                            xaxis_title="Fecha",
                            yaxis_title="Precio",
                            template='plotly_white'
                        )
                        st.plotly_chart(fig_prices, use_container_width=True)
                    
                    with col2:
                        # Histograma de retornos
                        fig_hist = go.Figure()
                        fig_hist.add_trace(go.Histogram(
                            x=analyzer.returns.values,
                            nbinsx=50,
                            name="Retornos",
                            marker_color='#28a745'
                        ))
                        fig_hist.update_layout(
                            title=f"Distribución de Retornos - {simbolo_seleccionado}",
                            xaxis_title="Retorno",
                            yaxis_title="Frecuencia",
                            template='plotly_white'
                        )
                        st.plotly_chart(fig_hist, use_container_width=True)
                    
                    # Análisis de distribución comparativo
                    if distribution_analysis.distribution_results:
                        st.subheader("🔬 Análisis de Distribución Comparativo")
                        fig_dist = distribution_analysis.plot_distribution_comparison_plotly()
                        if fig_dist:
                            st.plotly_chart(fig_dist, use_container_width=True)
                        
                        # Tabla de resultados de distribuciones
                        st.subheader("📋 Resultados de Bondad de Ajuste")
                        dist_df = pd.DataFrame(distribution_analysis.distribution_results).T
                        dist_df = dist_df.sort_values('P_Value', ascending=False)
                        st.dataframe(dist_df[['KS_Statistic', 'P_Value']], use_container_width=True)
                    
                else:
                    st.error("❌ No se pudo completar el análisis")
            else:
                st.error("❌ No se pudieron cargar los datos del activo")
                st.info(f"💡 Tip: El instrumento {simbolo_seleccionado} fue detectado como {detectar_tipo_instrumento(simbolo_seleccionado)}. Verifique que el símbolo sea correcto.")

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

def mostrar_analisis_comparativo_portafolio(token_acceso, id_cliente):
    """Muestra análisis comparativo de todos los activos del portafolio"""
    st.markdown("### 📊 Análisis Comparativo del Portafolio")
    
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
    pesos = []
    
    valor_total = sum(activo.get('valuacion', 0) for activo in activos)
    
    for activo in activos:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo')
        valuacion = activo.get('valuacion', 0)
        
        if simbolo and valor_total > 0:
            simbolos.append(simbolo)
            pesos.append(valuacion / valor_total)
    
    if not simbolos:
        st.warning("No se encontraron símbolos válidos")
        return
    
    fecha_desde = st.session_state.fecha_desde
    fecha_hasta = st.session_state.fecha_hasta
    
    if st.button("🚀 Realizar Análisis Comparativo Completo", type="primary"):
        with st.spinner("Realizando análisis comparativo..."):
            analyzer = PortfolioAdvancedAnalyzer(
                simbolos, pesos, token_acceso, fecha_desde, fecha_hasta
            )
            
            # Análisis individual de activos
            individual_analyses = analyzer.analyze_individual_assets()
            
            if individual_analyses:
                st.success(f"✅ Análisis completado para {len(individual_analyses)} activos")
                
                # Reporte comparativo
                comparison_df = analyzer.generate_comparison_report()
                
                if comparison_df is not None:
                    st.subheader("📋 Comparación de Activos")
                    st.dataframe(comparison_df, use_container_width=True)
                    
                    # Gráficos comparativos
                    st.subheader("📊 Visualizaciones Comparativas")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Gráfico de Retorno vs Volatilidad
                        fig_scatter = go.Figure()
                        
                        returns = []
                        volatilities = []
                        symbols_clean = []
                        
                        for symbol, analysis in individual_analyses.items():
                            metrics = analysis['metrics']
                            if metrics['Media Anual'] is not None and metrics['Volatilidad Anual'] is not None:
                                returns.append(metrics['Media Anual'])
                                volatilities.append(metrics['Volatilidad Anual'])
                                symbols_clean.append(symbol)
                        
                        if returns and volatilities:
                            fig_scatter.add_trace(go.Scatter(
                                x=volatilities,
                                y=returns,
                                mode='markers+text',
                                text=symbols_clean,
                                textposition="top center",
                                marker=dict(size=12, color='#ff6b6b'),
                                name='Activos'
                            ))
                            
                            fig_scatter.update_layout(
                                title="Retorno vs Volatilidad por Activo",
                                xaxis_title="Volatilidad Anual",
                                yaxis_title="Retorno Anual",
                                template='plotly_white'
                            )
                            st.plotly_chart(fig_scatter, use_container_width=True)
                    
                    with col2:
                        # Gráfico de Ratios Sharpe
                        sharpe_ratios = []
                        symbols_sharpe = []
                        
                        for symbol, analysis in individual_analyses.items():
                            metrics = analysis['metrics']
                            if metrics['Ratio Sharpe'] is not None:
                                sharpe_ratios.append(metrics['Ratio Sharpe'])
                                symbols_sharpe.append(symbol)
                        
                        if sharpe_ratios:
                            fig_sharpe = go.Figure()
                            fig_sharpe.add_trace(go.Bar(
                                x=symbols_sharpe,
                                y=sharpe_ratios,
                                marker_color='#4ecdc4',
                                name='Ratio Sharpe'
                            ))
                            
                            fig_sharpe.update_layout(
                                title="Ratio de Sharpe por Activo",
                                xaxis_title="Activo",
                                yaxis_title="Ratio Sharpe",
                                template='plotly_white'
                            )
                            st.plotly_chart(fig_sharpe, use_container_width=True)
                
                # Análisis del portafolio conjunto
                portfolio_dist = analyzer.compute_portfolio_distribution()
                
                if portfolio_dist:
                    st.subheader("🎯 Análisis del Portafolio Conjunto")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    port_metrics = portfolio_dist.get_metrics_dict()
                    col1.metric("Retorno Portafolio", f"{port_metrics['Media Anual']:.2%}")
                    col2.metric("Volatilidad Portafolio", f"{port_metrics['Volatilidad Anual']:.2%}")
                    col3.metric("Sharpe Portafolio", f"{port_metrics['Ratio Sharpe']:.3f}")
                    col4.metric("VaR 95% Portafolio", f"{port_metrics['VaR 95%']:.3f}")
                    
                    # Gráfico de distribución del portafolio
                    fig_port_dist = portfolio_dist.plot_distribution_comparison_plotly()
                    if fig_port_dist:
                        st.plotly_chart(fig_port_dist, use_container_width=True)
            else:
                st.error("❌ No se pudieron analizar los activos")
