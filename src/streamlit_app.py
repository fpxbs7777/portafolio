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
                
        else:
            return None
            
    except Exception as e:
        return None

def obtener_clase_d(simbolo, mercado, bearer_token):
    """
    Función mejorada para obtener clases D de bonos con mejor manejo de errores
    """
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
    
    url = f"https://api.invertironline.com/api/v2/{mercado_correcto}/Titulos/{simbolo}/Clases"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            clases = response.json()
            if isinstance(clases, list):
                # Buscar clases D (dólares) y otras variantes
                for clase in clases:
                    simbolo_clase = clase.get('simbolo', '')
                    if simbolo_clase.endswith('D') or simbolo_clase.endswith('USD'):
                        return simbolo_clase
                
                # Si no encuentra clase D, devolver el símbolo original
                return simbolo
            return simbolo
        else:
            return simbolo
    except Exception:
        return simbolo

def detectar_tipo_instrumento(simbolo, titulo_info=None):
    """
    Detecta el tipo de instrumento basado en el símbolo y información adicional
    """
    simbolo_upper = simbolo.upper()
    
    # FCIs
    if simbolo_upper.startswith('F') or (titulo_info and 'fondo' in titulo_info.get('descripcion', '').lower()):
        return 'FCI'
    
    # Opciones
    if 'CALL' in simbolo_upper or 'PUT' in simbolo_upper or (titulo_info and titulo_info.get('tipo') == 'OPCION'):
        return 'Opciones'
    
    # CEDEARs (suelen tener formato específico)
    if len(simbolo_upper) >= 4 and (simbolo_upper.endswith('D') or simbolo_upper.endswith('C')):
        if any(x in simbolo_upper for x in ['AAPL', 'GOOGL', 'AMZN', 'TSLA', 'MSFT', 'META']):
            return 'CEDEAR'
    
    # Bonos (suelen empezar con letras específicas)
    if simbolo_upper.startswith(('AL', 'AE', 'GD', 'TX', 'DICA', 'PARP', 'BOPREAL')):
        return 'BONO'
    
    # Por defecto, acciones
    return 'ACCION'

def get_historical_data_for_optimization(token_portador, simbolos, fecha_desde, fecha_hasta):
    """
    Función mejorada para obtener datos históricos con mejor soporte para todos los tipos de activos
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
        
        # Mostrar resultados
        if simbolos_exitosos:
            st.success(f"✅ Datos obtenidos para {len(simbolos_exitosos)} activos: {', '.join(simbolos_exitosos[:5])}{'...' if len(simbolos_exitosos) > 5 else ''}")
        
        if simbolos_fallidos:
            st.warning(f"⚠️ No se pudieron obtener datos para {len(simbolos_fallidos)} activos: {', '.join(simbolos_fallidos[:3])}{'...' if len(simbolos_fallidos) > 3 else ''}")
            
            # Mostrar detalles de errores en expander
            with st.expander("Ver detalles de errores"):
                for error_key, error_msg in list(detalles_errores.items())[:10]:  # Mostrar solo los primeros 10
                    st.text(f"{error_key}: {error_msg}")
        
        if len(simbolos_exitosos) < 2:
            st.error("❌ Se necesitan al menos 2 activos con datos válidos para el análisis")
            return None, None, None
        
        # Procesar y limpiar datos
        try:
            # Usar métodos más modernos para pandas
            df_precios_filled = df_precios.fillna(method='ffill').fillna(method='bfill')
            df_precios_interpolated = df_precios.interpolate(method='time', limit_direction='both')
            
            if not df_precios_filled.dropna().empty:
                df_precios = df_precios_filled.dropna()
            elif not df_precios_interpolated.dropna().empty:
                df_precios = df_precios_interpolated.dropna()
            else:
                df_precios = df_precios.dropna()
                
        except Exception as e:
            # Fallback a métodos básicos
            df_precios = df_precios.fillna(method='ffill').fillna(method='bfill').dropna()
        
        if df_precios.empty:
            st.error("❌ No hay datos suficientes después del procesamiento")
            return None, None, None
        
        # Calcular retornos
        returns = df_precios.pct_change().dropna()
        
        if returns.empty or len(returns) < 30:
            st.error("❌ Datos insuficientes para calcular retornos (mínimo 30 observaciones)")
            return None, None, None
        
        # Eliminar activos con varianza cero
        if (returns.std() == 0).any():
            columnas_constantes = returns.columns[returns.std() == 0].tolist()
            if columnas_constantes:
                st.warning(f"⚠️ Eliminando activos con precio constante: {', '.join(columnas_constantes)}")
                returns = returns.drop(columns=columnas_constantes)
                df_precios = df_precios.drop(columns=columnas_constantes)
        
        if len(returns.columns) < 2:
            st.error("❌ Se necesitan al menos 2 activos con varianza no nula")
            return None, None, None
        
        # Calcular estadísticas
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        
        # Verificar que la matriz de covarianza sea válida
        if cov_matrix.isnull().any().any() or (cov_matrix == 0).all().all():
            st.error("❌ Matriz de covarianza inválida")
            return None, None, None
        
        st.info(f"📊 Datos procesados: {len(df_precios)} observaciones para {len(df_precios.columns)} activos")
        
        return mean_returns, cov_matrix, df_precios
        
    except Exception as e:
        st.error(f"❌ Error inesperado en get_historical_data_for_optimization: {str(e)}")
        return None, None, None

def obtener_datos_alternativos_yfinance(simbolo, fecha_desde, fecha_hasta):
    """
    Función mejorada para obtener datos de yfinance con mejor manejo de sufijos argentinos
    """
    try:
        # Sufijos argentinos más completos
        sufijos_ar = ['.BA', '.AR', '.BS', '.BCBA']
        
        # Primero intentar con sufijos argentinos
        for sufijo in sufijos_ar:
            try:
                ticker = yf.Ticker(simbolo + sufijo)
                data = ticker.history(start=fecha_desde, end=fecha_hasta, auto_adjust=True, back_adjust=True)
                if not data.empty and len(data) > 10:
                    return data['Close']
            except Exception:
                continue
        
        # Luego intentar sin sufijo
        try:
            ticker = yf.Ticker(simbolo)
            data = ticker.history(start=fecha_desde, end=fecha_hasta, auto_adjust=True, back_adjust=True)
            if not data.empty and len(data) > 10:
                return data['Close']
        except Exception:
            pass
        
        # Intentar variaciones del símbolo para CEDEARs
        if len(simbolo) >= 3:
            variaciones = [
                simbolo + 'D',  # Clase dólar
                simbolo + 'C',  # Clase pesos
                simbolo[:-1] if simbolo.endswith('D') else None,  # Quitar D final
                simbolo[:-1] if simbolo.endswith('C') else None   # Quitar C final
            ]
            
            for variacion in variaciones:
                if variacion:
                    for sufijo in sufijos_ar + ['']:
                        try:
                            ticker = yf.Ticker(variacion + sufijo)
                            data = ticker.history(start=fecha_desde, end=fecha_hasta, auto_adjust=True, back_adjust=True)
                            if not data.empty and len(data) > 10:
                                return data['Close']
                        except Exception:
                            continue
            
        return None
        
    except Exception:
        return None

class IndividualAssetAnalyzer:
    def __init__(self, token, symbol, fecha_desde, fecha_hasta):
        self.token = token
        self.symbol = symbol
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.prices = None
        self.returns = None
        self.distribution_analysis = None
        self.tipo_instrumento = None
        
    def load_data(self):
        """Carga datos históricos del activo con mejor detección de tipo"""
        try:
            self.tipo_instrumento = detectar_tipo_instrumento(self.symbol)
            
            # Estrategia específica según tipo de instrumento
            if self.tipo_instrumento == 'FCI':
                serie = obtener_serie_historica_iol(
                    self.token, 'FCI', self.symbol, 
                    self.fecha_desde.strftime('%Y-%m-%d'), 
                    self.fecha_hasta.strftime('%Y-%m-%d')
                )
                
            elif self.tipo_instrumento == 'Opciones':
                serie = obtener_serie_historica_iol(
                    self.token, 'Opciones', self.symbol, 
                    self.fecha_desde.strftime('%Y-%m-%d'), 
                    self.fecha_hasta.strftime('%Y-%m-%d')
                )
                
            else:
                # Para acciones, bonos, CEDEARs
                mercados = ['bCBA', 'nYSE', 'nASDAQ', 'rOFEX']
                serie = None
                
                for mercado in mercados:
                    simbolo_consulta = self.symbol
                    
                    # Para bonos, intentar obtener clase D
                    if self.tipo_instrumento == 'BONO':
                        clase_d = obtener_clase_d(self.symbol, mercado, self.token)
                        if clase_d and clase_d != self.symbol:
                            simbolo_consulta = clase_d
                    
                    serie = obtener_serie_historica_iol(
                        self.token, mercado, simbolo_consulta, 
                        self.fecha_desde.strftime('%Y-%m-%d'), 
                        self.fecha_hasta.strftime('%Y-%m-%d')
                    )
                    
                    if serie is not None and len(serie) > 10:
                        break
            
            # Fallback a yfinance
            if serie is None or len(serie) < 10:
                serie = obtener_datos_alternativos_yfinance(
                    self.symbol, self.fecha_desde, self.fecha_hasta
                )
            
            if serie is not None and len(serie) > 10:
                self.prices = serie
                self.returns = serie.pct_change().dropna()
                return True
            else:
                return False
                
        except Exception as e:
            return False
    
    def analyze(self):
        """Realiza análisis completo del activo"""
        if self.returns is None:
            return None
            
        self.distribution_analysis = Distribution(self.returns, 100000)
        self.distribution_analysis.compute_stats()
        self.distribution_analysis.analyze_best_distribution()
        
        return self.distribution_analysis
    
    def get_complete_analysis(self):
        """Retorna análisis completo en formato diccionario con información del tipo de instrumento"""
        if self.distribution_analysis is None:
            return None
            
        analysis = {
            'symbol': self.symbol,
            'tipo_instrumento': self.tipo_instrumento,
            'data_points': len(self.returns) if self.returns is not None else 0,
            'price_range': {
                'min': float(self.prices.min()) if self.prices is not None else 0,
                'max': float(self.prices.max()) if self.prices is not None else 0,
                'current': float(self.prices.iloc[-1]) if self.prices is not None else 0
            },
            'metrics': self.distribution_analysis.get_metrics_dict(),
            'best_distribution': self.distribution_analysis.best_distribution,
            'distribution_results': self.distribution_analysis.distribution_results
        }
        
        return analysis

# --- Funciones de Optimización de Portafolio ---
def optimize_portfolio(returns, target_return=None):
    n_assets = returns.shape[1]
    
    # Constraints: weights sum to 1
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
    
    # Bounds: each weight between 0 and 1
    bounds = tuple((0, 1) for _ in range(n_assets))
    
    # Initial guess: equal weights
    init_guess = np.array([1/n_assets] * n_assets)
    
    # If target return is provided, add it as a constraint
    if target_return is not None:
        # Define the function for target return
        target_constraint = {
            'type': 'eq',
            'fun': lambda w: target_return - np.dot(w, returns.mean())
        }
        constraints = [constraints, target_constraint]
    
    # Objective function: minimize portfolio variance
    def objective(w):
        return np.dot(w.T, np.dot(returns.cov(), w))
    
    # Optimization
    result = op.minimize(
        objective,
        init_guess,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )
    
    return result.x

def calcular_metricas_portafolio(activos_data, valor_total):
    try:
        valores = [activo['Valuación'] for activo in activos_data if activo['Valuación'] > 0]
        
        if not valores:
            return None
        
        valores_array = np.array(valores)
        
        media = np.mean(valores_array)
        mediana = np.median(valores_array)
        std_dev = np.std(valores_array)
        var_95 = np.percentile(valores_array, 5)
        var_99 = np.percentile(valores_array, 1)
        
        q25 = np.percentile(valores_array, 25)
        q50 = np.percentile(valores_array, 50)
        q75 = np.percentile(valores_array, 75)
        q90 = np.percentile(valores_array, 90)
        q95 = np.percentile(valores_array, 95)
        
        pesos = valores_array / valor_total
        concentracion = np.sum(pesos ** 2)
        
        retorno_esperado_anual = 0.08
        volatilidad_anual = 0.20
        
        retorno_esperado_pesos = valor_total * retorno_esperado_anual
        riesgo_anual_pesos = valor_total * volatilidad_anual
        
        np.random.seed(42)
        num_simulaciones = 1000
        retornos_simulados = np.random.normal(retorno_esperado_anual, volatilidad_anual, num_simulaciones)
        pl_simulado = valor_total * retornos_simulados
        
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

    def compute_portfolio(self, portfolio_type=None, target_return=None):
        if self.cov_matrix is None:
            self.compute_covariance()
            
        n_assets = len(self.rics)
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        if portfolio_type == 'min-variance-l1':
            # Minimizar varianza con restricción L1
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'ineq', 'fun': lambda x: 1 - np.sum(np.abs(x))}
            ]
            
        elif portfolio_type == 'min-variance-l2':
            # Minimizar varianza con restricción L2
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'ineq', 'fun': lambda x: 1 - np.sum(x**2)}
            ]
            
        elif portfolio_type == 'equi-weight':
            # Pesos iguales
            weights = np.ones(n_assets) / n_assets
            return self._create_output(weights)
            
        elif portfolio_type == 'long-only':
            # Optimización long-only estándar
            constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
            
        elif portfolio_type == 'markowitz':
            if target_return is not None:
                # Optimización con retorno objetivo
                constraints = [
                    {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                    {'type': 'eq', 'fun': lambda x: np.sum(self.mean_returns * x) - target_return}
                ]
            else:
                # Maximizar Sharpe Ratio
                constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
                def neg_sharpe_ratio(weights):
                    port_ret = np.sum(self.mean_returns * weights)
                    port_vol = np.sqrt(portfolio_variance(weights, self.cov_matrix))
                    if port_vol == 0:
                        return np.inf
                    return -(port_ret - self.risk_free_rate) / port_vol
                
                result = op.minimize(
                    neg_sharpe_ratio, 
                    x0=np.ones(n_assets)/n_assets,
                    method='SLSQP',
                    bounds=bounds,
                    constraints=constraints
                )
                return self._create_output(result.x)
        
        # Optimización general de varianza mínima
        result = op.minimize(
            lambda x: portfolio_variance(x, self.cov_matrix),
            x0=np.ones(n_assets)/n_assets,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        return self._create_output(result.x)

    def _create_output(self, weights):
        """Crea un objeto output con los pesos optimizados"""
        port_ret = np.sum(self.mean_returns * weights)
        port_vol = np.sqrt(portfolio_variance(weights, self.cov_matrix))
        
        # Calcular retornos del portafolio
        portfolio_returns = self.returns.dot(weights)
        
        # Crear objeto output
        port_output = output(portfolio_returns, self.notional)
        port_output.weights = weights
        port_output.dataframe_allocation = pd.DataFrame({
            'rics': self.rics,
            'weights': weights,
            'volatilities': np.sqrt(np.diag(self.cov_matrix)),
            'returns': self.mean_returns
        })
        
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

# --- Nuevas clases para análisis avanzado ---
class Distribution:
    def __init__(self, timeseries, investment_amount, decimals=5, factor=252):
        self.timeseries = timeseries
        self.investment_amount = investment_amount
        self.decimals = decimals
        self.factor = factor  # Factor para anualizar (252 días hábiles)
        self.vector = timeseries if isinstance(timeseries, np.ndarray) else timeseries.values
        self.current_price = None
        self.mean_annual = None
        self.volatility_annual = None
        self.sharpe_ratio = None
        self.var_95 = None
        self.skewness = None
        self.kurtosis = None
        self.jb_stat = None
        self.p_value = None
        self.is_normal = None
        self.max_loss = None
        self.expected_loss = None
        self.expected_gain = None
        self.max_gain = None
        self.most_probable = None
        self.best_distribution = None
        self.distribution_results = None

    def compute_stats(self):
        """Calcula estadísticas clave del activo"""
        if len(self.vector) == 0:
            return
            
        self.mean_annual = np.mean(self.vector) * self.factor
        self.volatility_annual = np.std(self.vector) * np.sqrt(self.factor)
        self.sharpe_ratio = self.mean_annual / self.volatility_annual if self.volatility_annual > 0 else 0.0
        self.var_95 = np.percentile(self.vector, 5)
        self.var_99 = np.percentile(self.vector, 1)
        self.skewness = stats.skew(self.vector)
        self.kurtosis = stats.kurtosis(self.vector)
        
        # Test de Jarque-Bera para normalidad
        try:
            self.jb_stat, self.p_value = stats.jarque_bera(self.vector)
            self.is_normal = self.p_value > 0.05
        except:
            self.jb_stat = np.nan
            self.p_value = np.nan
            self.is_normal = False

        # Calcular escenarios de inversión
        negative_returns = self.vector[self.vector < 0]
        positive_returns = self.vector[self.vector > 0]
        
        self.expected_loss = np.mean(negative_returns) if len(negative_returns) > 0 else 0
        self.expected_gain = np.mean(positive_returns) if len(positive_returns) > 0 else 0
        self.max_gain = np.max(self.vector) if len(self.vector) > 0 else 0
        self.max_loss = np.min(self.vector) if len(self.vector) > 0 else 0
        self.most_probable = np.median(self.vector) if len(self.vector) > 0 else 0

    def analyze_best_distribution(self):
        """Analiza qué distribución se ajusta mejor a los datos"""
        if len(self.vector) < 10:
            return None, None
            
        distributions = ['norm', 't', 'uniform', 'expon', 'chi2', 'lognorm']
        results = {}
        
        for dist in distributions:
            try:
                dist_obj = getattr(stats, dist)
                params = dist_obj.fit(self.vector)
                ks_stat, p_value = stats.kstest(self.vector, dist, args=params)
                results[dist] = {
                    'KS_Statistic': round(ks_stat, self.decimals), 
                    'P_Value': round(p_value, self.decimals),
                    'params': params
                }
            except Exception:
                continue
        
        if results:
            best_fit = max(results, key=lambda x: results[x]['P_Value'])
            self.distribution_results = results
            self.best_distribution = best_fit
            return results, best_fit
        
        return None, None

    def get_metrics_dict(self):
        """Retorna métricas en formato diccionario"""
        return {
            'Media Anual': self.mean_annual,
            'Volatilidad Anual': self.volatility_annual,
            'Ratio Sharpe': self.sharpe_ratio,
            'VaR 95%': self.var_95,
            'VaR 99%': self.var_99,
            'Skewness': self.skewness,
            'Kurtosis': self.kurtosis,
            'JB Statistic': self.jb_stat,
            'P-Value': self.p_value,
            'Es Normal': self.is_normal,
            'Ganancia Máxima': self.max_gain,
            'Pérdida Máxima': self.max_loss,
            'Ganancia Esperada': self.expected_gain,
            'Pérdida Esperada': self.expected_loss,
            'Retorno Más Probable': self.most_probable
        }

    def plot_distribution_comparison_plotly(self):
        """Crea gráfico comparativo de distribuciones usando Plotly"""
        if self.distribution_results is None:
            self.analyze_best_distribution()
        
        if self.distribution_results is None:
            return None
            
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Histograma de Retornos', 'Comparación de Distribuciones', 
                          'Q-Q Plot vs Normal', 'Estadísticas de Bondad de Ajuste'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Histograma principal
        fig.add_trace(
            go.Histogram(x=self.vector, nbinsx=50, name="Datos Reales", 
                        marker_color='lightblue', opacity=0.7),
            row=1, col=1
        )
        
        # Comparación con la mejor distribución
        if self.best_distribution:
            x_range = np.linspace(self.vector.min(), self.vector.max(), 100)
            try:
                dist_obj = getattr(stats, self.best_distribution)
                params = self.distribution_results[self.best_distribution]['params']
                y_fitted = dist_obj.pdf(x_range, *params)
                
                fig.add_trace(
                    go.Scatter(x=x_range, y=y_fitted, mode='lines', 
                             name=f'Ajuste {self.best_distribution}', 
                             line=dict(color='red', width=2)),
                    row=1, col=2
                )
            except Exception:
                pass
        
        # Q-Q Plot vs Normal
        try:
            theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, len(self.vector)))
            sample_quantiles = np.sort(self.vector)
            
            fig.add_trace(
                go.Scatter(x=theoretical_quantiles, y=sample_quantiles, 
                         mode='markers', name='Q-Q Normal',
                         marker=dict(color='green', size=4)),
                row=2, col=1
            )
            
            # Línea de referencia perfecta
            min_val = min(theoretical_quantiles.min(), sample_quantiles.min())
            max_val = max(theoretical_quantiles.max(), sample_quantiles.max())
            fig.add_trace(
                go.Scatter(x=[min_val, max_val], y=[min_val, max_val], 
                         mode='lines', name='Línea Perfecta',
                         line=dict(color='red', dash='dash')),
                row=2, col=1
            )
        except Exception:
            pass
        
        # Tabla de estadísticas
        if self.distribution_results:
            distributions = list(self.distribution_results.keys())
            ks_stats = [self.distribution_results[d]['KS_Statistic'] for d in distributions]
            p_values = [self.distribution_results[d]['P_Value'] for d in distributions]
            
            fig.add_trace(
                go.Bar(x=distributions, y=p_values, name='P-Values',
                      marker_color='orange', opacity=0.7),
                row=2, col=2
            )
        
        fig.update_layout(
            title=f"Análisis de Distribución - Mejor ajuste: {self.best_distribution or 'N/A'}",
            height=600,
            showlegend=True
        )
        
        return fig

class IndividualAssetAnalyzer:
    def __init__(self, token, symbol, fecha_desde, fecha_hasta):
        self.token = token
        self.symbol = symbol
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.prices = None
        self.returns = None
        self.distribution_analysis = None
        self.tipo_instrumento = None
        
    def load_data(self):
        """Carga datos históricos del activo con mejor detección de tipo"""
        try:
            self.tipo_instrumento = detectar_tipo_instrumento(self.symbol)
            
            # Estrategia específica según tipo de instrumento
            if self.tipo_instrumento == 'FCI':
                serie = obtener_serie_historica_iol(
                    self.token, 'FCI', self.symbol, 
                    self.fecha_desde.strftime('%Y-%m-%d'), 
                    self.fecha_hasta.strftime('%Y-%m-%d')
                )
                
            elif self.tipo_instrumento == 'Opciones':
                serie = obtener_serie_historica_iol(
                    self.token, 'Opciones', self.symbol, 
                    self.fecha_desde.strftime('%Y-%m-%d'), 
                    self.fecha_hasta.strftime('%Y-%m-%d')
                )
                
            else:
                # Para acciones, bonos, CEDEARs
                mercados = ['bCBA', 'nYSE', 'nASDAQ', 'rOFEX']
                serie = None
                
                for mercado in mercados:
                    simbolo_consulta = self.symbol
                    
                    # Para bonos, intentar obtener clase D
                    if self.tipo_instrumento == 'BONO':
                        clase_d = obtener_clase_d(self.symbol, mercado, self.token)
                        if clase_d and clase_d != self.symbol:
                            simbolo_consulta = clase_d
                    
                    serie = obtener_serie_historica_iol(
                        self.token, mercado, simbolo_consulta, 
                        self.fecha_desde.strftime('%Y-%m-%d'), 
                        self.fecha_hasta.strftime('%Y-%m-%d')
                    )
                    
                    if serie is not None and len(serie) > 10:
                        break
            
            # Fallback a yfinance
            if serie is None or len(serie) < 10:
                serie = obtener_datos_alternativos_yfinance(
                    self.symbol, self.fecha_desde, self.fecha_hasta
                )
            
            if serie is not None and len(serie) > 10:
                self.prices = serie
                self.returns = serie.pct_change().dropna()
                return True
            else:
                return False
                
        except Exception as e:
            return False
    
    def analyze(self):
        """Realiza análisis completo del activo"""
        if self.returns is None:
            return None
            
        self.distribution_analysis = Distribution(self.returns, 100000)
        self.distribution_analysis.compute_stats()
        self.distribution_analysis.analyze_best_distribution()
        
        return self.distribution_analysis
    
    def get_complete_analysis(self):
        """Retorna análisis completo en formato diccionario con información del tipo de instrumento"""
        if self.distribution_analysis is None:
            return None
            
        analysis = {
            'symbol': self.symbol,
            'tipo_instrumento': self.tipo_instrumento,
            'data_points': len(self.returns) if self.returns is not None else 0,
            'price_range': {
                'min': float(self.prices.min()) if self.prices is not None else 0,
                'max': float(self.prices.max()) if self.prices is not None else 0,
                'current': float(self.prices.iloc[-1]) if self.prices is not None else 0
            },
            'metrics': self.distribution_analysis.get_metrics_dict(),
            'best_distribution': self.distribution_analysis.best_distribution,
            'distribution_results': self.distribution_analysis.distribution_results
        }
        
        return analysis

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
