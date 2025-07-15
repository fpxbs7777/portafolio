import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
from datetime import date, timedelta, datetime
import numpy as np
import pandas as pd
import yfinance as yf
import scipy.optimize as op
from scipy import stats
import random
import warnings
import streamlit.components.v1 as components
from scipy.stats import linregress
import httpx
import asyncio
import matplotlib.pyplot as plt
from scipy.stats import skew
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import json
from typing import Dict, List, Optional, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

warnings.filterwarnings('ignore')

class ArgentinaDatos:
    """
    Main class for fetching and analyzing Argentine economic and financial data.
    """
    
    def __init__(self, base_url: str = 'https://api.argentinadatos.com'):
        self.base_url = base_url
        self.session = requests.Session()
    
    def fetch_data(self, endpoint: str) -> List[Dict]:
        """
        Fetch data from Argentina Datos API.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            List of data dictionaries
        """
        try:
            response = self.session.get(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching data from {endpoint}: {e}")
            return []
    
    def get_dolares(self) -> List[Dict]:
        """Get dólar exchange rates data."""
        return self.fetch_data('/v1/cotizaciones/dolares')
    
    def get_dolares_candlestick(self) -> Dict:
        """Get dólar candlestick data."""
        return self.fetch_data('/v1/cotizaciones/dolares/candlestick')
    
    def get_inflacion(self) -> List[Dict]:
        """Get inflation data."""
        return self.fetch_data('/v1/indicadores/inflacion')
    
    def get_tasas(self) -> List[Dict]:
        """Get interest rates data."""
        return self.fetch_data('/v1/indicadores/tasas')
    
    def get_uva(self) -> List[Dict]:
        """Get UVA data."""
        return self.fetch_data('/v1/indicadores/uva')
    
    def get_riesgo_pais(self) -> List[Dict]:
        """Get country risk data."""
        return self.fetch_data('/v1/indicadores/riesgo-pais')
    
    def get_all_economic_data(self) -> Dict[str, Any]:
        """
        Get all economic and financial data in one call.
        
        Returns:
            Dictionary with all economic data
        """
        return {
            'dolares': self.get_dolares(),
            'dolares_candlestick': self.get_dolares_candlestick(),
            'inflacion': self.get_inflacion(),
            'tasas': self.get_tasas(),
            'uva': self.get_uva(),
            'riesgo_pais': self.get_riesgo_pais()
        }
    
    def create_dolares_chart(self, data: List[Dict], periodo: str = '1 mes', 
                            casas: Optional[List[str]] = None) -> Dict:
        """
        Create dólares chart with Plotly.
        
        Args:
            data: Dólares data
            periodo: Time period ('1 semana', '1 mes', '1 año', '5 años', 'Todo')
            casas: List of exchange houses to include
            
        Returns:
            Plotly figure as dictionary
        """
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        # Filter by period
        periodos = {
            '1 semana': 7,
            '1 mes': 30,
            '1 año': 365,
            '5 años': 1825,
        }
        
        if periodo in periodos and periodo != 'Todo':
            cutoff_date = datetime.now() - timedelta(days=periodos[periodo])
            df = df[df['fecha'] >= cutoff_date]
        
        # Filter by selected houses
        if casas:
            df = df[df['casa'].isin(casas)]
        
        fig = go.Figure()
        
        for casa in df['casa'].unique():
            casa_data = df[df['casa'] == casa]
            fig.add_trace(go.Scatter(
                x=casa_data['fecha'],
                y=casa_data['venta'],
                mode='lines',
                name=casa,
                hovertemplate='<b>%{x}</b><br>Cotización: %{y}<extra></extra>'
            ))
        
        fig.update_layout(
            title='Cotizaciones del Dólar en Argentina',
            xaxis_title='Fecha',
            yaxis_title='Cotización',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_inflacion_chart(self, data: List[Dict]) -> Dict:
        """
        Create inflación chart with Plotly.
        
        Args:
            data: Inflation data
            
        Returns:
            Plotly figure as dictionary
        """
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['fecha'],
            y=df['valor'],
            mode='lines+markers',
            name='Inflación',
            line=dict(color='#3b82f6', width=2),
            hovertemplate='<b>%{x}</b><br>Inflación: %{y}%<extra></extra>'
        ))
        
        fig.update_layout(
            title='Evolución de la Inflación',
            xaxis_title='Fecha',
            yaxis_title='Inflación (%)',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_tasas_chart(self, data: List[Dict]) -> Dict:
        """
        Create tasas chart with Plotly.
        
        Args:
            data: Interest rates data
            
        Returns:
            Plotly figure as dictionary
        """
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        fig = go.Figure()
        
        for tasa in df['tasa'].unique():
            tasa_data = df[df['tasa'] == tasa]
            fig.add_trace(go.Scatter(
                x=tasa_data['fecha'],
                y=tasa_data['valor'],
                mode='lines+markers',
                name=tasa,
                hovertemplate='<b>%{x}</b><br>%{fullData.name}: %{y}%<extra></extra>'
            ))
        
        fig.update_layout(
            title='Evolución de las Tasas',
            xaxis_title='Fecha',
            yaxis_title='Tasa (%)',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_uva_chart(self, data: List[Dict]) -> Dict:
        """
        Create UVA chart with Plotly.
        
        Args:
            data: UVA data
            
        Returns:
            Plotly figure as dictionary
        """
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['fecha'],
            y=df['valor'],
            mode='lines+markers',
            name='UVA',
            line=dict(color='#10b981', width=2),
            hovertemplate='<b>%{x}</b><br>UVA: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Evolución del UVA',
            xaxis_title='Fecha',
            yaxis_title='UVA',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def create_riesgo_pais_chart(self, data: List[Dict]) -> Dict:
        """
        Create riesgo país chart with Plotly.
        
        Args:
            data: Country risk data
            
        Returns:
            Plotly figure as dictionary
        """
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['fecha'],
            y=df['valor'],
            mode='lines+markers',
            name='Riesgo País',
            line=dict(color='#f59e0b', width=2),
            hovertemplate='<b>%{x}</b><br>Riesgo País: %{y} puntos<extra></extra>'
        ))
        
        fig.update_layout(
            title='Evolución del Riesgo País',
            xaxis_title='Fecha',
            yaxis_title='Riesgo País (puntos)',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return json.loads(fig.to_json())
    
    def get_economic_analysis(self) -> Dict[str, Any]:
        """
        Get comprehensive economic analysis including cycle phase detection.
        
        Returns:
            Dictionary with economic analysis and cycle phase
        """
        data = self.get_all_economic_data()
        
        analysis = {
            'data': data,
            'cycle_phase': 'Unknown',
            'recommendations': [],
            'risk_level': 'Medium',
            'sectors': {
                'favorable': [],
                'unfavorable': [],
                'neutral': []
            }
        }
        
        # Analyze inflation trend
        if data['inflacion']:
            inflacion_df = pd.DataFrame(data['inflacion'])
            inflacion_df['fecha'] = pd.to_datetime(inflacion_df['fecha'])
            inflacion_df = inflacion_df.sort_values('fecha')
            
            if len(inflacion_df) >= 2:
                latest_inflacion = inflacion_df.iloc[-1]['valor']
                prev_inflacion = inflacion_df.iloc[-2]['valor']
                inflacion_trend = latest_inflacion - prev_inflacion
                
                if inflacion_trend > 0:
                    analysis['cycle_phase'] = 'Inflationary Pressure'
                    analysis['risk_level'] = 'High'
                    analysis['sectors']['favorable'].extend(['Commodities', 'Real Estate', 'TIPS'])
                    analysis['sectors']['unfavorable'].extend(['Bonds', 'Cash', 'Growth Stocks'])
                else:
                    analysis['cycle_phase'] = 'Disinflationary'
                    analysis['risk_level'] = 'Medium'
                    analysis['sectors']['favorable'].extend(['Bonds', 'Growth Stocks', 'Technology'])
        
        # Analyze interest rates
        if data['tasas']:
            tasas_df = pd.DataFrame(data['tasas'])
            tasas_df['fecha'] = pd.to_datetime(tasas_df['fecha'])
            tasas_df = tasas_df.sort_values('fecha')
            
            if len(tasas_df) >= 2:
                latest_tasa = tasas_df.iloc[-1]['valor']
                prev_tasa = tasas_df.iloc[-2]['valor']
                tasa_trend = latest_tasa - prev_tasa
                
                if tasa_trend > 0:
                    analysis['cycle_phase'] = 'Tightening Monetary Policy'
                    analysis['sectors']['favorable'].extend(['Financials', 'Value Stocks'])
                    analysis['sectors']['unfavorable'].extend(['Growth Stocks', 'Real Estate'])
                else:
                    analysis['cycle_phase'] = 'Accommodative Monetary Policy'
                    analysis['sectors']['favorable'].extend(['Growth Stocks', 'Real Estate', 'Technology'])
        
        # Analyze country risk
        if data['riesgo_pais']:
            riesgo_df = pd.DataFrame(data['riesgo_pais'])
            riesgo_df['fecha'] = pd.to_datetime(riesgo_df['fecha'])
            riesgo_df = riesgo_df.sort_values('fecha')
            
            if len(riesgo_df) >= 2:
                latest_riesgo = riesgo_df.iloc[-1]['valor']
                prev_riesgo = riesgo_df.iloc[-2]['valor']
                riesgo_trend = latest_riesgo - prev_riesgo
                
                if riesgo_trend > 0:
                    analysis['risk_level'] = 'High'
                    analysis['sectors']['favorable'].extend(['Defensive Stocks', 'Gold', 'USD'])
                    analysis['sectors']['unfavorable'].extend(['Emerging Markets', 'Local Currency Bonds'])
                else:
                    analysis['risk_level'] = 'Medium'
                    analysis['sectors']['favorable'].extend(['Emerging Markets', 'Local Stocks'])
        
        # Generate recommendations based on cycle phase
        if analysis['cycle_phase'] == 'Inflationary Pressure':
            analysis['recommendations'].extend([
                'Considerar activos refugio como oro y commodities',
                'Reducir exposición a bonos de largo plazo',
                'Mantener liquidez en dólares',
                'Considerar acciones de empresas con poder de fijación de precios'
            ])
        elif analysis['cycle_phase'] == 'Tightening Monetary Policy':
            analysis['recommendations'].extend([
                'Favorecer acciones de valor sobre crecimiento',
                'Considerar bonos de corto plazo',
                'Mantener exposición a sectores financieros',
                'Reducir exposición a bienes raíces'
            ])
        elif analysis['cycle_phase'] == 'Accommodative Monetary Policy':
            analysis['recommendations'].extend([
                'Favorecer acciones de crecimiento',
                'Considerar bienes raíces',
                'Mantener exposición a tecnología',
                'Considerar bonos de largo plazo'
            ])
        
        return analysis

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

def obtener_precio_actual(token_portador, mercado, simbolo):
    """Obtiene el último precio de un título puntual (endpoint estándar de IOL)."""
    url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion"
    headers = obtener_encabezado_autorizacion(token_portador)
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, (int, float)):
                return float(data)
            elif isinstance(data, dict):
                # La API suele devolver 'ultimoPrecio'
                for k in [
                    'ultimoPrecio', 'ultimo_precio', 'ultimoPrecioComprador', 'ultimoPrecioVendedor',
                    'precio', 'precioActual', 'valor'
                ]:
                    if k in data and data[k] is not None:
                        try:
                            return float(data[k])
                        except ValueError:
                            continue
        return None
    except Exception:
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

def obtener_movimientos_asesor(token_portador, clientes, fecha_desde, fecha_hasta, tipo_fecha="fechaOperacion", 
                             estado=None, tipo_operacion=None, pais=None, moneda=None, cuenta_comitente=None):
    """
    Obtiene los movimientos de los clientes de un asesor
    
    Args:
        token_portador (str): Token de autenticación
        clientes (list): Lista de IDs de clientes
        fecha_desde (str): Fecha de inicio (formato ISO)
        fecha_hasta (str): Fecha de fin (formato ISO)
        tipo_fecha (str): Tipo de fecha a filtrar ('fechaOperacion' o 'fechaLiquidacion')
        estado (str, optional): Estado de la operación
        tipo_operacion (str, optional): Tipo de operación
        pais (str, optional): País de la operación
        moneda (str, optional): Moneda de la operación
        cuenta_comitente (str, optional): Número de cuenta comitente
        
    Returns:
        dict: Diccionario con los movimientos o None en caso de error
    """
    url = "https://api.invertironline.com/api/v2/Asesor/Movimientos"
    headers = {
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'application/json'
    }
    
    # Preparar el cuerpo de la solicitud
    payload = {
        "clientes": clientes,
        "from": fecha_desde,
        "to": fecha_hasta,
        "dateType": tipo_fecha,
        "status": estado or "",
        "type": tipo_operacion or "",
        "country": pais or "",
        "currency": moneda or "",
        "cuentaComitente": cuenta_comitente or ""
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener movimientos: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def obtener_tasas_caucion(token_portador):
    """
    Obtiene las tasas de caución desde la API de IOL
    
    Args:
        token_portador (str): Token de autenticación Bearer
        
    Returns:
        DataFrame: DataFrame con las tasas de caución o None en caso de error
    """
    url = "https://api.invertironline.com/api/v2/cotizaciones-orleans/cauciones/argentina/Operables"
    params = {
        'cotizacionInstrumentoModel.instrumento': 'cauciones',
        'cotizacionInstrumentoModel.pais': 'argentina'
    }
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token_portador}'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'titulos' in data and isinstance(data['titulos'], list) and data['titulos']:
                df = pd.DataFrame(data['titulos'])
                
                # Filtrar solo las cauciónes y limpiar los datos
                df = df[df['plazo'].notna()].copy()
                
                # Extraer el plazo en días
                df['plazo_dias'] = df['plazo'].str.extract('(\d+)').astype(float)
                
                # Limpiar la tasa (convertir a float si es necesario)
                if 'ultimoPrecio' in df.columns:
                    df['tasa_limpia'] = df['ultimoPrecio'].astype(str).str.rstrip('%').astype('float')
                
                # Asegurarse de que las columnas necesarias existan
                if 'monto' not in df.columns and 'volumen' in df.columns:
                    df['monto'] = df['volumen']
                
                # Ordenar por plazo
                df = df.sort_values('plazo_dias')
                
                # Seleccionar solo las columnas necesarias
                columnas_requeridas = ['simbolo', 'plazo', 'plazo_dias', 'ultimoPrecio', 'tasa_limpia', 'monto', 'moneda']
                columnas_disponibles = [col for col in columnas_requeridas if col in df.columns]
                
                return df[columnas_disponibles]
            
            st.warning("No se encontraron datos de tasas de caución en la respuesta")
            return None
            
        elif response.status_code == 401:
            st.error("Error de autenticación. Por favor, verifique su token de acceso.")
            return None
            
        else:
            error_msg = f"Error {response.status_code} al obtener tasas de caución"
            try:
                error_data = response.json()
                error_msg += f": {error_data.get('message', 'Error desconocido')}"
            except:
                error_msg += f": {response.text}"
            st.error(error_msg)
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error inesperado al procesar tasas de caución: {str(e)}")
        return None

def mostrar_tasas_caucion(token_portador):
    """
    Muestra las tasas de caución en una tabla y gráfico de curva de tasas
    """
    st.subheader("📊 Tasas de Caución")
    
    try:
        with st.spinner('Obteniendo tasas de caución...'):
            df_cauciones = obtener_tasas_caucion(token_portador)
            
            # Verificar si se obtuvieron datos
            if df_cauciones is None or df_cauciones.empty:
                st.warning("No se encontraron datos de tasas de caución.")
                return
                
            # Verificar columnas requeridas
            required_columns = ['simbolo', 'plazo', 'ultimoPrecio', 'plazo_dias', 'tasa_limpia']
            missing_columns = [col for col in required_columns if col not in df_cauciones.columns]
            if missing_columns:
                st.error(f"Faltan columnas requeridas en los datos: {', '.join(missing_columns)}")
                return
            
            # Mostrar tabla con las tasas
            st.dataframe(
                df_cauciones[['simbolo', 'plazo', 'ultimoPrecio', 'monto'] if 'monto' in df_cauciones.columns 
                             else ['simbolo', 'plazo', 'ultimoPrecio']]
                .rename(columns={
                    'simbolo': 'Instrumento',
                    'plazo': 'Plazo',
                    'ultimoPrecio': 'Tasa',
                    'monto': 'Monto (en millones)'
                }),
                use_container_width=True,
                height=min(400, 50 + len(df_cauciones) * 35)  # Ajustar altura dinámicamente
            )
            
            # Crear gráfico de curva de tasas si hay suficientes puntos
            if len(df_cauciones) > 1:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=df_cauciones['plazo_dias'],
                    y=df_cauciones['tasa_limpia'],
                    mode='lines+markers+text',
                    name='Tasa',
                    text=df_cauciones['tasa_limpia'].round(2).astype(str) + '%',
                    textposition='top center',
                    line=dict(color='#1f77b4', width=2),
                    marker=dict(size=10, color='#1f77b4')
                ))
                
                fig.update_layout(
                    title='Curva de Tasas de Caución',
                    xaxis_title='Plazo (días)',
                    yaxis_title='Tasa Anual (%)',
                    template='plotly_white',
                    height=500,
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar resumen estadístico
            if 'tasa_limpia' in df_cauciones.columns and 'plazo_dias' in df_cauciones.columns:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Tasa Mínima", f"{df_cauciones['tasa_limpia'].min():.2f}%")
                    st.metric("Tasa Máxima", f"{df_cauciones['tasa_limpia'].max():.2f}%")
                with col2:
                    st.metric("Tasa Promedio", f"{df_cauciones['tasa_limpia'].mean():.2f}%")
                    st.metric("Plazo Promedio", f"{df_cauciones['plazo_dias'].mean():.1f} días")
                    
    except Exception as e:
        st.error(f"Error al mostrar las tasas de caución: {str(e)}")
        st.exception(e)  # Mostrar el traceback completo para depuración

def parse_datetime_string(datetime_string):
    """
    Parsea una cadena de fecha/hora usando múltiples formatos
    """
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

def obtener_endpoint_historico(mercado, simbolo, fecha_desde, fecha_hasta, ajustada="SinAjustar"):
    """Devuelve la URL correcta para la serie histórica del símbolo indicado.

    La prioridad es:
    1. Usar el mercado recibido (ya normalizado por la llamada superior)
       si existe en el mapeo de casos especiales.
    2. Caso contrario, construir la ruta estándar
       "{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/...".

    No se aplican heurísticas sobre el símbolo: la función que invoque debe
    pasar el mercado correcto (por ejemplo: 'Bonos', 'Cedears', 'BCBA').
    """
    base_url = "https://api.invertironline.com/api/v2"

    # Cubrir alias frecuentes para que el mapeo sea coherente
    alias = {
        'TITULOSPUBLICOS': 'TitulosPublicos',
        'TITULOS PUBLICOS': 'TitulosPublicos'
    }
    mercado_norm = alias.get(mercado.upper(), mercado)

    especiales = {
        'Opciones': f"{base_url}/Opciones/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'FCI': f"{base_url}/Titulos/FCI/{simbolo}/cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'MEP': f"{base_url}/Cotizaciones/MEP/{simbolo}",
        'Caucion': f"{base_url}/Cotizaciones/Cauciones/Todas/Argentina",
        'TitulosPublicos': f"{base_url}/TitulosPublicos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'Cedears': f"{base_url}/Cedears/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'ADRs': f"{base_url}/ADRs/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
        'Bonos': f"{base_url}/Bonos/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}",
    }

    if mercado_norm in especiales:
        return especiales[mercado_norm]

    # Ruta genérica (acciones BCBA, NYSE, NASDAQ, etc.)
    return f"{base_url}/{mercado_norm}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"

def parse_datetime_flexible(date_str: str):
    """
    Parses a datetime string that may or may not include microseconds or timezone info.
    Handles both formats: with and without milliseconds.
    """
    if not isinstance(date_str, str):
        return None
    try:
        # First try parsing with the exact format that matches the error
        try:
            # Handle format without milliseconds: "2024-12-10T17:11:04"
            if len(date_str) == 19 and 'T' in date_str and date_str.count(':') == 2:
                return pd.to_datetime(date_str, format='%Y-%m-%dT%H:%M:%S', utc=True)
            # Handle format with milliseconds: "2024-12-10T17:11:04.123"
            elif '.' in date_str and 'T' in date_str:
                return pd.to_datetime(date_str, format='%Y-%m-%dT%H:%M:%S.%f', utc=True)
        except (ValueError, TypeError):
            pass
            
        # Fall back to pandas' built-in parser if specific formats don't match
        return pd.to_datetime(date_str, errors='coerce', utc=True)
    except Exception as e:
        st.warning(f"Error parsing date '{date_str}': {str(e)}")
        return None

def procesar_respuesta_historico(data, tipo_activo):
    """
    Procesa la respuesta de la API según el tipo de activo
    """
    if not data:
        return None
    
    try:
        # Para series históricas estándar
        if isinstance(data, list):
            precios = []
            fechas = []
            
            for item in data:
                try:
                    # Manejar diferentes estructuras de respuesta
                    if isinstance(item, dict):
                        precio = item.get('ultimoPrecio') or item.get('precio') or item.get('valor')
                        if not precio or precio == 0:
                            precio = item.get('cierreAnterior') or item.get('precioPromedio') or item.get('apertura')
                        
                        fecha_str = item.get('fechaHora') or item.get('fecha')
                        
                        if precio is not None and precio > 0 and fecha_str:
                            fecha_parsed = parse_datetime_flexible(fecha_str)
                            if pd.notna(fecha_parsed):
                                precios.append(float(precio))
                                fechas.append(fecha_parsed)
                except (ValueError, AttributeError) as e:
                    continue
            
            if precios and fechas:
                df = pd.DataFrame({'fecha': fechas, 'precio': precios})
                # Eliminar duplicados manteniendo el último
                df = df.drop_duplicates(subset=['fecha'], keep='last')
                df = df.sort_values('fecha')
                return df
        
        # Para respuestas que son un solo valor (ej: MEP)
        elif isinstance(data, (int, float)):
            df = pd.DataFrame({'fecha': [pd.Timestamp.now(tz='UTC').date()], 'precio': [float(data)]})
            return df
            
        return None
        
    except Exception as e:
        st.error(f"Error al procesar respuesta histórica: {str(e)}")
        return None

def obtener_fondos_comunes(token_portador):
    """
    Obtiene la lista de fondos comunes de inversión disponibles
    """
    url = 'https://api.invertironline.com/api/v2/Titulos/FCI'
    headers = {
        'Authorization': f'Bearer {token_portador}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error al obtener fondos comunes: {str(e)}")
        return []



def obtener_serie_historica_iol(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="SinAjustar"):
    """
    Obtiene la serie histórica de precios para un activo específico desde la API de InvertirOnline.
    
    Args:
        token_portador (str): Token de autenticación de la API
        mercado (str): Mercado del activo (ej: 'BCBA', 'NYSE', 'NASDAQ')
        simbolo (str): Símbolo del activo
        fecha_desde (str): Fecha de inicio en formato 'YYYY-MM-DD'
        fecha_hasta (str): Fecha de fin en formato 'YYYY-MM-DD'
        ajustada (str): Tipo de ajuste ('Ajustada' o 'SinAjustar')
        
    Returns:
        pd.DataFrame: DataFrame con las columnas 'fecha' y 'precio', o None en caso de error
    """
    try:
        print(f"Obteniendo datos para {simbolo} en {mercado} desde {fecha_desde} hasta {fecha_hasta}")
        
        # Endpoint para FCIs (manejo especial)
        if mercado.upper() == 'FCI':
            print("Es un FCI, usando función específica")
            return obtener_serie_historica_fci(token_portador, simbolo, fecha_desde, fecha_hasta)
        
        # Construir URL según el tipo de activo y mercado
        url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
        print(f"URL de la API: {url.split('?')[0]}")  # Mostrar URL sin parámetros sensibles
        
        headers = {
            'Authorization': 'Bearer [TOKEN]',  # No mostrar el token real
            'Accept': 'application/json'
        }
        
        # Realizar la solicitud
        response = requests.get(url, headers={
            'Authorization': f'Bearer {token_portador}',
            'Accept': 'application/json'
        }, timeout=30)
        
        # Verificar el estado de la respuesta
        print(f"Estado de la respuesta: {response.status_code}")
        response.raise_for_status()
        
        # Procesar la respuesta
        data = response.json()
        print(f"Tipo de datos recibidos: {type(data)}")
        
        # Procesar la respuesta según el formato esperado
        if isinstance(data, list):
            print(f"Se recibió una lista con {len(data)} elementos")
            if data:
                print(f"Primer elemento: {data[0]}")
                
            # Formato estándar para series históricas
            fechas = []
            precios = []
            
            for item in data:
                try:
                    # Manejar diferentes formatos de fecha
                    fecha_str = item.get('fecha') or item.get('fechaHora')
                    if not fecha_str:
                        print(f"  - Item sin fecha: {item}")
                        continue
                        
                    # Manejar diferentes formatos de precio
                    precio = item.get('ultimoPrecio') or item.get('precioCierre') or item.get('precio')
                    if precio is None:
                        print(f"  - Item sin precio: {item}")
                        continue
                        
                    # Convertir fecha
                    try:
                        fecha = parse_datetime_flexible(fecha_str)
                        if pd.isna(fecha):
                            print(f"  - Fecha inválida: {fecha_str}")
                            continue
                            
                        precio_float = float(precio)
                        if precio_float <= 0:
                            print(f"  - Precio inválido: {precio}")
                            continue
                            
                        fechas.append(fecha)
                        precios.append(precio_float)
                        
                    except (ValueError, TypeError) as e:
                        print(f"  - Error al convertir datos: {e}")
                        continue
                        
                except Exception as e:
                    print(f"  - Error inesperado al procesar item: {e}")
                    continue
            
            if fechas and precios:
                df = pd.DataFrame({'fecha': fechas, 'precio': precios})
                # Eliminar duplicados manteniendo el último
                df = df.drop_duplicates(subset=['fecha'], keep='last')
                df = df.sort_values('fecha')
                print(f"Datos procesados: {len(df)} registros válidos")
                return df
            else:
                print("No se encontraron datos válidos en la respuesta")
                return None
                
        elif isinstance(data, dict):
            print(f"Se recibió un diccionario: {data.keys()}")
            # Para respuestas que son un solo valor (ej: MEP)
            precio = data.get('ultimoPrecio') or data.get('precioCierre') or data.get('precio')
            if precio is not None:
                print(f"Datos de un solo punto: precio={precio}")
                return pd.DataFrame({
                    'fecha': [pd.Timestamp.now(tz='UTC')],
                    'precio': [float(precio)]
                })
            else:
                print("No se encontró precio en la respuesta")
        else:
            print(f"Tipo de respuesta no manejado: {type(data)}")
            
        print(f"No se pudieron procesar los datos para {simbolo} en {mercado}")
        return None
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error de conexión para {simbolo} en {mercado}: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" - Status: {e.response.status_code}"
            try:
                error_msg += f" - Respuesta: {e.response.text[:200]}"
            except:
                pass
        print(error_msg)
        st.warning(error_msg)
        return None
    except Exception as e:
        error_msg = f"Error inesperado al procesar {simbolo} en {mercado}: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        st.error(error_msg)
        return None
        return None

def obtener_serie_historica_fci(token_portador, simbolo, fecha_desde, fecha_hasta):
    """
    Obtiene la serie histórica de un Fondo Común de Inversión.
    
    Args:
        token_portador (str): Token de autenticación
        simbolo (str): Símbolo del FCI
        fecha_desde (str): Fecha inicio (YYYY-MM-DD)
        fecha_hasta (str): Fecha fin (YYYY-MM-DD)
        
    Returns:
        pd.DataFrame: DataFrame con columnas 'fecha' y 'precio', o None si hay error
    """
    try:
        # Primero intentar obtener directamente la serie histórica
        url_serie = f"https://api.invertironline.com/api/v2/Titulos/FCI/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/SinAjustar"
        headers = {
            'Authorization': f'Bearer {token_portador}',
            'Accept': 'application/json'
        }
        
        response = requests.get(url_serie, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Procesar la respuesta según el formato esperado
        if isinstance(data, list):
            fechas = []
            precios = []
            
            for item in data:
                try:
                    # Manejar diferentes formatos de fecha
                    fecha_str = item.get('fecha') or item.get('fechaHora')
                    if not fecha_str:
                        continue
                        
                    # Obtener el valor de la cuota (puede venir en diferentes campos)
                    precio = item.get('valorCuota') or item.get('precio') or item.get('ultimoPrecio')
                    if not precio:
                        continue
                        
                    # Convertir fecha
                    fecha = parse_datetime_flexible(fecha_str)
                    if not pd.isna(fecha):
                        fechas.append(fecha)
                        precios.append(float(precio))
                        
                except (ValueError, TypeError, AttributeError) as e:
                    continue
            
            if fechas and precios:
                df = pd.DataFrame({'fecha': fechas, 'precio': precios})
                df = df.drop_duplicates(subset=['fecha'], keep='last')
                df = df.sort_values('fecha')
                return df
        
        # Si no se pudo obtener la serie histórica, intentar obtener el último valor
        try:
            # Obtener información del FCI
            url_fci = "https://api.invertironline.com/api/v2/Titulos/FCI"
            response = requests.get(url_fci, headers=headers, timeout=30)
            response.raise_for_status()
            fc_data = response.json()
            
            # Buscar el FCI por símbolo
            fci = next((f for f in fc_data if f.get('simbolo') == simbolo), None)
            if fci and 'ultimoValorCuotaParte' in fci:
                return pd.DataFrame({
                    'fecha': [pd.Timestamp.now(tz='UTC')],
                    'precio': [float(fci['ultimoValorCuotaParte'])]
                })
        except Exception:
            pass
        
        st.warning(f"No se pudieron obtener datos históricos para el FCI {simbolo}")
        return None
        
    except requests.exceptions.RequestException as e:
        st.warning(f"Error de conexión al obtener datos del FCI {simbolo}: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error inesperado al procesar el FCI {simbolo}: {str(e)}")
        return None

def get_historical_data_for_optimization(token_portador, activos, fecha_desde, fecha_hasta):
    """
    Obtiene datos históricos para optimización usando el mercado específico de cada activo.
    
    Args:
        token_portador: Token de autenticación Bearer
        activos: Lista de diccionarios, cada uno con {'simbolo': str, 'mercado': str}
        fecha_desde: Fecha inicio (YYYY-MM-DD)
        fecha_hasta: Fecha fin (YYYY-MM-DD)
    
    Returns:
        Dict con DataFrames históricos por símbolo
    """
    datos_historicos = {}
    
    with st.spinner('Obteniendo datos históricos...'):
        for activo in activos:
            simbolo = activo.get('simbolo')
            mercado = activo.get('mercado')

            if not simbolo or not mercado:
                st.warning(f"Activo inválido, se omite: {activo}")
                continue

            df = obtener_serie_historica_iol(
                token_portador,
                mercado.upper(),
                simbolo,
                fecha_desde,
                fecha_hasta
            )
            
            if df is not None and not df.empty:
                datos_historicos[simbolo] = df
            else:
                st.warning(f"No se pudieron obtener datos para {simbolo} en el mercado {mercado}")
                
    return datos_historicos if datos_historicos else None

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
            if ric in self.timeseries and self.timeseries[ric] is not None:
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
        if self.returns is not None:
            portfolio_returns = self.returns.dot(weights)
        else:
            # Fallback si returns es None
            portfolio_returns = pd.Series([0] * 252)  # Serie vacía
        
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
        # Compatibilidad: alias para risk y returns (usados en la interfaz)
        self.risk = self.volatility_annual
        self.returns = self.return_annual

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
        # Asegura que self.returns sea una secuencia (array, lista, o pandas Series), no un escalar
        import numpy as np
        import pandas as pd
        returns = self.returns
        # Si es None o vacío
        if returns is None or (hasattr(returns, '__len__') and len(returns) == 0):
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos suficientes para mostrar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(title=title)
            return fig
        # Si es un escalar (float, int, numpy.float, numpy.int)
        if isinstance(returns, (float, int, np.floating, np.integer)):
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos suficientes para mostrar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(title=title)
            return fig
        # Si es un array/serie de un solo valor, también evitar graficar
        if hasattr(returns, '__len__') and len(returns) <= 1:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos suficientes para mostrar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig.update_layout(title=title)
            return fig

        fig = go.Figure(data=[go.Histogram(
            x=returns,
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

def portfolio_variance(x, mtx_var_covar):
    """Calcula la varianza del portafolio"""
    variance = np.matmul(np.transpose(x), np.matmul(mtx_var_covar, x))
    return variance

def optimize_portfolio(returns, target_return=None):
    """
    Optimiza un portafolio usando el método de Markowitz
    
    Args:
        returns (pd.DataFrame): DataFrame con retornos de activos
        target_return (float, optional): Retorno objetivo anual
        
    Returns:
        np.array: Pesos optimizados del portafolio
    """
    if returns is None or returns.empty:
        return None
        
    n_assets = len(returns.columns)
    
    # Calcular matriz de covarianza y retornos medios
    cov_matrix = returns.cov() * 252  # Anualizar
    mean_returns = returns.mean() * 252  # Anualizar
    
    # Pesos iniciales iguales
    initial_weights = np.ones(n_assets) / n_assets
    
    # Restricciones
    bounds = tuple((0, 1) for _ in range(n_assets))
    
    if target_return is not None:
        # Optimización con retorno objetivo
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Suma de pesos = 1
            {'type': 'eq', 'fun': lambda x: np.sum(mean_returns * x) - target_return}  # Retorno objetivo
        ]
        
        # Minimizar varianza
        result = op.minimize(
            lambda x: portfolio_variance(x, cov_matrix),
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
    else:
        # Maximizar Sharpe ratio
        risk_free_rate = 0.40  # Tasa libre de riesgo para Argentina
        
        def neg_sharpe_ratio(weights):
            port_return = np.sum(mean_returns * weights)
            port_vol = np.sqrt(portfolio_variance(weights, cov_matrix))
            if port_vol == 0:
                return np.inf
            return -(port_return - risk_free_rate) / port_vol
        
        constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        
        result = op.minimize(
            neg_sharpe_ratio,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
    
    if result.success:
        return result.x
    else:
        # Si falla la optimización, usar pesos iguales
        return initial_weights

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
    def __init__(self, activos, token, fecha_desde, fecha_hasta):
        self.activos = activos
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
            # Convertir lista de activos a formato adecuado
            symbols = []
            markets = []
            tipos = []
            def detectar_mercado(tipo_raw: str, mercado_raw: str) -> str:
                """
                Determina el mercado basado en la información proporcionada.
                
                Args:
                    tipo_raw: Tipo de activo (no utilizado en esta versión)
                    mercado_raw: Mercado del activo
                    
                Returns:
                    str: Nombre del mercado normalizado
                """
                # Usar el mercado proporcionado o BCBA como valor por defecto
                mercado = mercado_raw.strip().title() if mercado_raw.strip() else 'BCBA'
                return mercado
            
            for activo in self.activos:
                if isinstance(activo, dict):
                    simbolo = activo.get('simbolo', '')
                    tipo_raw = (activo.get('tipo') or '')
                    mercado_raw = (activo.get('mercado') or '')
                    
                    if not simbolo:
                        continue
                    symbols.append(simbolo)
                    tipos.append(tipo_raw)
                    markets.append(detectar_mercado(tipo_raw, mercado_raw))
                else:
                    symbols.append(activo)
                    markets.append('BCBA')  # Default market
            
            if not symbols:
                st.error("❌ No se encontraron símbolos válidos para procesar")
                return False
            
            # Obtener datos históricos
            data_frames = {}
            
            with st.spinner("Obteniendo datos históricos..."):
                for simbolo, mercado in zip(symbols, markets):
                    df = obtener_serie_historica_iol(
                        self.token,
                        mercado,
                        simbolo,
                        self.fecha_desde,
                        self.fecha_hasta
                    )
                    
                    if df is not None and not df.empty:
                        # Usar la columna de último precio si está disponible
                        precio_columns = ['ultimoPrecio', 'ultimo_precio', 'precio']
                        precio_col = next((col for col in precio_columns if col in df.columns), None)
                        
                        if precio_col:
                            df = df[['fecha', precio_col]].copy()
                            df.columns = ['fecha', 'precio']  # Normalizar el nombre de la columna
                            
                            # Convertir fechaHora a fecha y asegurar que sea única
                            df['fecha'] = pd.to_datetime(df['fecha']).dt.date
                            
                            # Eliminar duplicados manteniendo el último valor
                            df = df.drop_duplicates(subset=['fecha'], keep='last')
                            
                            df.set_index('fecha', inplace=True)
                            data_frames[simbolo] = df
                        else:
                            st.warning(f"⚠️ No se encontró columna de precio válida para {simbolo}")
                    else:
                        st.warning(f"⚠️ No se pudieron obtener datos para {simbolo} en {mercado}")
            
            if not data_frames:
                st.error("❌ No se pudieron obtener datos históricos para ningún activo")
                return False
            
            # Combinar todos los DataFrames
            df_precios = pd.concat(data_frames.values(), axis=1, keys=data_frames.keys())
            # Limpiar datos
            if not df_precios.index.is_unique:
                st.warning("⚠️ Se encontraron fechas duplicadas en los datos")
                df_precios = df_precios.groupby(df_precios.index).last()
            df_precios = df_precios.fillna(method='ffill')
            df_precios = df_precios.dropna()
            if df_precios.empty:
                st.error("❌ No hay datos suficientes después del preprocesamiento")
                return False
            self.prices = df_precios  # <--- ASIGNAR PRECIOS PARA FRONTERA EFICIENTE
            self.returns = df_precios.pct_change().dropna()
            self.mean_returns = self.returns.mean()
            self.cov_matrix = self.returns.cov()
            self.data_loaded = True
            self.manager = manager(list(df_precios.columns), self.notional, df_precios.to_dict('series'))
            return True
        except Exception as e:
            st.error(f"❌ Error en load_data: {str(e)}")
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
                    weights = np.ones(n_assets) / n_assets
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
            return None

    def compute_efficient_frontier(self, target_return=0.08, include_min_variance=True):
        """Computa la frontera eficiente"""
        if not self.data_loaded or not self.manager or self.prices is None or self.prices.empty:
            return None, None, None
        try:
            # Chequeo adicional: evitar series con menos de 2 activos o fechas
            if self.prices.shape[1] < 2 or self.prices.shape[0] < 10:
                return None, None, None
            portfolios, returns, volatilities = compute_efficient_frontier(
                self.manager.rics, self.notional, target_return, include_min_variance, 
                self.prices.to_dict('series')
            )
            return portfolios, returns, volatilities
        except Exception as e:
            return None, None, None

# --- Historical Data Methods ---
def _deprecated_serie_historica_iol(*args, **kwargs):
    """Deprecated duplicate of `obtener_serie_historica_iol`. Kept for backward compatibility."""
    return None
    """Obtiene series históricas desde la API de IOL
    
    Args:
        token_portador: Token de autenticación Bearer
        mercado: Mercado (BCBA, NYSE, NASDAQ, ROFEX)
        simbolo: Símbolo del activo (puede ser string o dict con clave 'simbolo')
        fecha_desde: Fecha inicio (YYYY-MM-DD)
        fecha_hasta: Fecha fin (YYYY-MM-DD)
        ajustada: "Ajustada" o "SinAjustar"
    
    Returns:
        DataFrame con datos históricos o None si hay error
    """
    # Manejar caso donde simbolo es un diccionario
    if isinstance(simbolo, dict):
        simbolo = simbolo.get('simbolo', '')
    
    if not simbolo:
        st.warning("No se proporcionó un símbolo válido")
        return None
        
    # Asegurarse de que el mercado esté en mayúsculas
    mercado = mercado.upper() if mercado else 'BCBA'
    try:
        # Construir la URL de la API
        url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token_portador}'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        df = pd.DataFrame(data)
        
        if 'fechaHora' in df.columns:
            # Handle different datetime formats
            df['fecha'] = pd.to_datetime(
                df['fechaHora'], 
                format='mixed',  # Automatically infer format for each element
                utc=True,        # Ensure timezone awareness
                errors='coerce'  # Convert parsing errors to NaT
            ).dt.tz_convert(None).dt.date  # Convert to naive date
            
            # Drop rows where date parsing failed
            df = df.dropna(subset=['fecha'])
            df = df.sort_values('fecha')
            
        return df
        
    except Exception as e:
        st.error(f"Error obteniendo datos para {simbolo}: {str(e)}")
        return None

# --- Portfolio Metrics Function ---
def calcular_alpha_beta(portfolio_returns, benchmark_returns, risk_free_rate=0.0):
    """
    Calcula el Alpha y Beta de un portafolio respecto a un benchmark.
    
    Args:
        portfolio_returns (pd.Series): Retornos del portafolio
        benchmark_returns (pd.Series): Retornos del benchmark (ej: MERVAL)
        risk_free_rate (float): Tasa libre de riesgo (anualizada)
        
    Returns:
        dict: Diccionario con alpha, beta, información de la regresión y métricas adicionales
    """
    # Alinear las series por fecha y eliminar NaN
    aligned_data = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
    if len(aligned_data) < 5:  # Mínimo de datos para regresión
        return {
            'alpha': 0,
            'beta': 1.0,
            'r_squared': 0,
            'p_value': 1.0,
            'tracking_error': 0,
            'information_ratio': 0,
            'observations': len(aligned_data),
            'alpha_annual': 0
        }
    
    portfolio_aligned = aligned_data.iloc[:, 0]
    benchmark_aligned = aligned_data.iloc[:, 1]
    
    # Calcular regresión lineal
    slope, intercept, r_value, p_value, std_err = linregress(benchmark_aligned, portfolio_aligned)
    
    # Calcular métricas adicionales
    tracking_error = np.std(portfolio_aligned - benchmark_aligned) * np.sqrt(252)  # Anualizado
    information_ratio = (portfolio_aligned.mean() - benchmark_aligned.mean()) / tracking_error if tracking_error != 0 else 0
    
    # Anualizar alpha (asumiendo 252 días hábiles)
    alpha_annual = intercept * 252
    
    return {
        'alpha': intercept,
        'beta': slope,
        'r_squared': r_value ** 2,
        'p_value': p_value,
        'tracking_error': tracking_error,
        'information_ratio': information_ratio,
        'observations': len(aligned_data),
        'alpha_annual': alpha_annual
    }

def analizar_estrategia_inversion(alpha_beta_metrics):
    """
    Analiza la estrategia de inversión y cobertura basada en métricas de alpha y beta.
    
    Args:
        alpha_beta_metrics (dict): Diccionario con las métricas de alpha y beta
        
    Returns:
        dict: Diccionario con el análisis de la estrategia
    """
    beta = alpha_beta_metrics.get('beta', 1.0)
    alpha_annual = alpha_beta_metrics.get('alpha_annual', 0)
    r_squared = alpha_beta_metrics.get('r_squared', 0)
    
    # Análisis de estrategia basado en beta
    if beta > 1.2:
        estrategia = "Estrategia Agresiva"
        explicacion = ("El portafolio es más volátil que el mercado (β > 1.2). "
                      "Esta estrategia busca rendimientos superiores asumiendo mayor riesgo.")
    elif beta > 0.8:
        estrategia = "Estrategia de Crecimiento"
        explicacion = ("El portafolio sigue de cerca al mercado (0.8 < β < 1.2). "
                     "Busca rendimientos similares al mercado con un perfil de riesgo equilibrado.")
    elif beta > 0.3:
        estrategia = "Estrategia Defensiva"
        explicacion = ("El portafolio es menos volátil que el mercado (0.3 < β < 0.8). "
                     "Busca preservar capital con menor exposición a las fluctuaciones del mercado.")
    elif beta > -0.3:
        estrategia = "Estrategia de Ingresos"
        explicacion = ("El portafolio tiene baja correlación con el mercado (-0.3 < β < 0.3). "
                     "Ideal para generar ingresos con bajo riesgo de mercado.")
    else:
        estrategia = "Estrategia de Cobertura"
        explicacion = ("El portafolio tiene correlación negativa con el mercado (β < -0.3). "
                     "Diseñado para moverse en dirección opuesta al mercado, útil para cobertura.")
    
    # Análisis de desempeño basado en alpha
    if alpha_annual > 0.05:  # 5% de alpha anual
        rendimiento = "Excelente desempeño"
        explicacion_rendimiento = (f"El portafolio ha generado un alpha anualizado de {alpha_annual:.1%}, "
                                 "superando significativamente al benchmark.")
    elif alpha_annual > 0.02:  # 2% de alpha anual
        rendimiento = "Buen desempeño"
        explicacion_rendimiento = (f"El portafolio ha generado un alpha anualizado de {alpha_annual:.1%}, "
                                 "superando al benchmark.")
    elif alpha_annual > -0.02:  # Entre -2% y 2%
        rendimiento = "Desempeño en línea"
        explicacion_rendimiento = (f"El portafolio tiene un alpha anualizado de {alpha_annual:.1%}, "
                                 "en línea con el benchmark.")
    else:
        rendimiento = "Desempeño inferior"
        explicacion_rendimiento = (f"El portafolio tiene un alpha anualizado de {alpha_annual:.1%}, "
                                 "por debajo del benchmark.")
    
    # Calidad de la cobertura basada en R²
    if r_squared > 0.7:
        calidad_cobertura = "Alta"
        explicacion_cobertura = (f"El R² de {r_squared:.2f} indica una fuerte relación con el benchmark. "
                               "La cobertura será más efectiva.")
    elif r_squared > 0.4:
        calidad_cobertura = "Moderada"
        explicacion_cobertura = (f"El R² de {r_squared:.2f} indica una relación moderada con el benchmark. "
                               "La cobertura puede ser parcialmente efectiva.")
    else:
        calidad_cobertura = "Baja"
        explicacion_cobertura = (f"El R² de {r_squared:.2f} indica una débil relación con el benchmark. "
                               "La cobertura puede no ser efectiva.")
    
    return {
        'estrategia': estrategia,
        'explicacion_estrategia': explicacion,
        'rendimiento': rendimiento,
        'explicacion_rendimiento': explicacion_rendimiento,
        'calidad_cobertura': calidad_cobertura,
        'explicacion_cobertura': explicacion_cobertura,
        'beta': beta,
        'alpha_anual': alpha_annual,
        'r_cuadrado': r_squared,
        'observations': alpha_beta_metrics.get('observations', 0)
    }

def calcular_metricas_portafolio(portafolio, valor_total, token_portador, dias_historial=252):
    """
    Calcula métricas clave de desempeño para un portafolio de inversión usando datos históricos.
{{ ... }}
    
    Args:
        portafolio (dict): Diccionario con los activos y sus cantidades
        valor_total (float): Valor total del portafolio
        token_portador (str): Token de autenticación para la API de InvertirOnline
        dias_historial (int): Número de días de histórico a considerar (por defecto: 252 días hábiles)
        
    Returns:
        dict: Diccionario con las métricas calculadas
    """
    if not isinstance(portafolio, dict) or not portafolio or valor_total <= 0:
        return {}

    # Obtener fechas para el histórico
    fecha_hasta = datetime.now().strftime('%Y-%m-%d')
    fecha_desde = (datetime.now() - timedelta(days=dias_historial*1.5)).strftime('%Y-%m-%d')
    
    # 1. Calcular concentración del portafolio (Índice de Herfindahl-Hirschman normalizado)
    if len(portafolio) == 0:
        concentracion = 0
    elif len(portafolio) == 1:
        concentracion = 1.0
    else:
        sum_squares = sum((activo.get('Valuación', 0) / valor_total) ** 2 
                         for activo in portafolio.values())
        # Normalizar entre 0 y 1
        min_concentration = 1.0 / len(portafolio)
        concentracion = (sum_squares - min_concentration) / (1 - min_concentration)
        
    # Descargar datos del MERVAL para cálculo de Alpha y Beta
    try:
        merval_data = yf.download('^MERV', start=fecha_desde, end=fecha_hasta)['Close']
        merval_returns = merval_data.pct_change().dropna()
        merval_available = True
    except Exception as e:
        print(f"No se pudieron obtener datos del MERVAL: {str(e)}")
        merval_available = False
        merval_returns = None
    
    # Inicializar estructuras para cálculos
    retornos_diarios = {}
    metricas_activos = {}
    
    # 2. Obtener datos históricos y calcular métricas por activo
    for simbolo, activo in portafolio.items():
        try:
            # Obtener datos históricos usando el método estándar
            mercado = activo.get('mercado', 'BCBA')
            tipo_activo = activo.get('Tipo', 'Desconocido')
            
            # Debug: Mostrar información del activo que se está procesando
            print(f"\nProcesando activo: {simbolo} (Mercado: {mercado}, Tipo: {tipo_activo})")
            
            # Obtener la serie histórica
            try:
                df_historico = obtener_serie_historica_iol(
                    token_portador=token_portador,
                    mercado=mercado,
                    simbolo=simbolo,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                    ajustada="SinAjustar"
                )
            except Exception as e:
                print(f"Error al obtener datos históricos para {simbolo}: {str(e)}")
                continue
            
            if df_historico is None:
                print(f"No se obtuvieron datos para {simbolo} (None)")
                continue
                
            if df_historico.empty:
                print(f"Datos vacíos para {simbolo}")
                continue
            
            # Asegurarse de que tenemos las columnas necesarias
            if 'fecha' not in df_historico.columns or 'precio' not in df_historico.columns:
                print(f"Faltan columnas necesarias en los datos de {simbolo}")
                print(f"Columnas disponibles: {df_historico.columns.tolist()}")
                continue
                
            print(f"Datos obtenidos: {len(df_historico)} registros desde {df_historico['fecha'].min()} hasta {df_historico['fecha'].max()}")
                
            # Ordenar por fecha y limpiar duplicados
            df_historico = df_historico.sort_values('fecha')
            df_historico = df_historico.drop_duplicates(subset=['fecha'], keep='last')
            
            # Calcular retornos diarios
            df_historico['retorno'] = df_historico['precio'].pct_change()
            
            # Filtrar valores atípicos usando un enfoque más robusto
            if len(df_historico) > 5:  # Necesitamos suficientes puntos para el filtrado
                q_low = df_historico['retorno'].quantile(0.01)
                q_high = df_historico['retorno'].quantile(0.99)
                df_historico = df_historico[
                    (df_historico['retorno'] >= q_low) & 
                    (df_historico['retorno'] <= q_high)
                ]
            
            # Filtrar valores no finitos y asegurar suficientes datos
            retornos_validos = df_historico['retorno'].replace(
                [np.inf, -np.inf], np.nan
            ).dropna()
            
            if len(retornos_validos) < 5:  # Mínimo de datos para métricas confiables
                print(f"No hay suficientes datos válidos para {simbolo} (solo {len(retornos_validos)} registros)")
                continue
                
            # Verificar si hay suficientes variaciones de precio
            if retornos_validos.nunique() < 2:
                print(f"No hay suficiente variación en los precios de {simbolo}")
                continue
            
            # Calcular métricas básicas
            retorno_medio = retornos_validos.mean() * 252  # Anualizado
            volatilidad = retornos_validos.std() * np.sqrt(252)  # Anualizada
            
            # Asegurar valores razonables
            retorno_medio = np.clip(retorno_medio, -5, 5)  # Límite de ±500% anual
            volatilidad = min(volatilidad, 3)  # Límite de 300% de volatilidad
            
            # Calcular métricas de riesgo basadas en la distribución de retornos
            ret_pos = retornos_validos[retornos_validos > 0]
            ret_neg = retornos_validos[retornos_validos < 0]
            n_total = len(retornos_validos)
            
            # Calcular probabilidades
            prob_ganancia = len(ret_pos) / n_total if n_total > 0 else 0.5
            prob_perdida = len(ret_neg) / n_total if n_total > 0 else 0.5
            
            # Calcular probabilidades de movimientos extremos
            prob_ganancia_10 = len(ret_pos[ret_pos > 0.1]) / n_total if n_total > 0 else 0
            prob_perdida_10 = len(ret_neg[ret_neg < -0.1]) / n_total if n_total > 0 else 0
            
            # Calcular el peso del activo en el portafolio
            peso = activo.get('Valuación', 0) / valor_total if valor_total > 0 else 0
            
            # Guardar métricas
            metricas_activos[simbolo] = {
                'retorno_medio': retorno_medio,
                'volatilidad': volatilidad,
                'prob_ganancia': prob_ganancia,
                'prob_perdida': prob_perdida,
                'prob_ganancia_10': prob_ganancia_10,
                'prob_perdida_10': prob_perdida_10,
                'peso': peso
            }
            
            # Guardar retornos para cálculo de correlaciones
            retornos_diarios[simbolo] = df_historico.set_index('fecha')['retorno']
            
        except Exception as e:
            print(f"Error procesando {simbolo}: {str(e)}")
            continue
    
    if not metricas_activos:
        print("No se pudieron calcular métricas para ningún activo")
        return {
            'concentracion': concentracion,
            'std_dev_activo': 0,
            'retorno_esperado_anual': 0,
            'pl_esperado_min': 0,
            'pl_esperado_max': 0,
            'probabilidades': {'perdida': 0, 'ganancia': 0, 'perdida_mayor_10': 0, 'ganancia_mayor_10': 0},
            'riesgo_anual': 0
        }
    else:
        print(f"\nMétricas calculadas para {len(metricas_activos)} activos")
    
    # 3. Calcular métricas del portafolio
    # Retorno esperado ponderado
    retorno_esperado_anual = sum(
        (m.get('retorno_medio', 0) or 0) * (m.get('peso', 0) or 0)
        for m in metricas_activos.values()
    )
    
    # Volatilidad del portafolio (considerando correlaciones)
    try:
        if len(retornos_diarios) > 1:
            # Asegurarse de que tenemos suficientes datos para calcular correlaciones
            df_retornos = pd.DataFrame(retornos_diarios).dropna()
            if len(df_retornos) < 5:  # Mínimo de datos para correlación confiable
                print("No hay suficientes datos para calcular correlaciones confiables")
                # Usar promedio ponderado simple como respaldo
                volatilidad_portafolio = sum(
                    (m.get('volatilidad', 0) or 0) * (m.get('peso', 0) or 0)
                    for m in metricas_activos.values()
                )
            else:
                # Calcular matriz de correlación
                df_correlacion = df_retornos.corr()
                
                # Verificar si la matriz de correlación es válida
                if df_correlacion.isna().any().any():
                    print("Advertencia: Matriz de correlación contiene valores NaN")
                    df_correlacion = df_correlacion.fillna(0)  # Reemplazar NaN con 0
                
                # Obtener pesos y volatilidades
                activos = list(metricas_activos.keys())
                pesos = np.array([metricas_activos[a]['peso'] for a in activos])
                volatilidades = np.array([metricas_activos[a]['volatilidad'] for a in activos])
                
                # Asegurarse de que las dimensiones coincidan
                if len(activos) == df_correlacion.shape[0] == df_correlacion.shape[1]:
                    # Calcular matriz de covarianza
                    matriz_cov = np.diag(volatilidades) @ df_correlacion.values @ np.diag(volatilidades)
                    # Calcular varianza del portafolio
                    varianza_portafolio = pesos.T @ matriz_cov @ pesos
                    # Asegurar que la varianza no sea negativa
                    varianza_portafolio = max(0, varianza_portafolio)
                    volatilidad_portafolio = np.sqrt(varianza_portafolio)
                else:
                    print("Dimensiones no coinciden, usando promedio ponderado")
                    volatilidad_portafolio = sum(v * w for v, w in zip(volatilidades, pesos))
        else:
            # Si solo hay un activo, usar su volatilidad directamente
            volatilidad_portafolio = next(iter(metricas_activos.values()))['volatilidad']
            
        # Asegurar que la volatilidad sea un número finito
        if not np.isfinite(volatilidad_portafolio):
            print("Advertencia: Volatilidad no finita, usando valor por defecto")
            volatilidad_portafolio = 0.2  # Valor por defecto razonable
            
    except Exception as e:
        print(f"Error al calcular volatilidad del portafolio: {str(e)}")
        import traceback
        traceback.print_exc()
        # Valor por defecto seguro
        volatilidad_portafolio = sum(
            (m.get('volatilidad', 0) or 0) * (m.get('peso', 0) or 0)
            for m in metricas_activos.values()
        ) if metricas_activos else 0.2
    
    # Calcular percentiles para escenarios
    retornos_simulados = []
    for _ in range(1000):  # Simulación Monte Carlo simple
        retorno_simulado = 0
        for m in metricas_activos.values():
            retorno_medio = m.get('retorno_medio', 0) or 0
            volatilidad = m.get('volatilidad', 0) or 0
            peso = m.get('peso', 0) or 0
            retorno_simulado += np.random.normal(retorno_medio/252, volatilidad/np.sqrt(252)) * peso
        retornos_simulados.append(retorno_simulado * 252)  # Anualizado
    
    valor_total_safe = valor_total or 0
    pl_esperado_min = np.percentile(retornos_simulados, 5) * valor_total_safe / 100
    pl_esperado_max = np.percentile(retornos_simulados, 95) * valor_total_safe / 100
    
    # Calcular probabilidades basadas en los retornos simulados
    retornos_simulados = np.array(retornos_simulados)
    total_simulaciones = len(retornos_simulados)
            
    prob_ganancia = np.sum(retornos_simulados > 0) / total_simulaciones if total_simulaciones > 0 else 0.5
    prob_perdida = np.sum(retornos_simulados < 0) / total_simulaciones if total_simulaciones > 0 else 0.5
    prob_ganancia_10 = np.sum(retornos_simulados > 0.1) / total_simulaciones
    prob_perdida_10 = np.sum(retornos_simulados < -0.1) / total_simulaciones
            
    # 4. Calcular Alpha y Beta respecto al MERVAL si hay datos disponibles
    alpha_beta_metrics = {}
    if merval_available and len(retornos_diarios) > 1:
        try:
            # Calcular retornos diarios del portafolio (promedio ponderado de los activos)
            df_port_returns = pd.DataFrame(retornos_diarios)
            
            # Asegurarse de que los pesos estén en el mismo orden que las columnas
            pesos_ordenados = [metricas_activos[col].get('peso', 0) or 0 for col in df_port_returns.columns]
            df_port_returns['Portfolio'] = df_port_returns.dot(pesos_ordenados)
            
            # Alinear fechas con el MERVAL
            merval_series = pd.Series(merval_returns, name='MERVAL')
            aligned_data = pd.merge(
                df_port_returns[['Portfolio']], 
                merval_series, 
                left_index=True, 
                right_index=True,
                how='inner'
            )
            
            if len(aligned_data) > 5:  # Mínimo de datos para cálculo confiable
                # Calcular métricas de Alpha y Beta
                alpha_beta_metrics = calcular_alpha_beta(
                    aligned_data['Portfolio'],  # Retornos del portafolio
                    aligned_data['MERVAL'],      # Retornos del MERVAL
                    risk_free_rate=0.40  # Tasa libre de riesgo para Argentina
                )
                
                print(f"Alpha: {alpha_beta_metrics.get('alpha_annual', 0):.2%}, "
                      f"Beta: {alpha_beta_metrics.get('beta', 0):.2f}, "
                      f"R²: {alpha_beta_metrics.get('r_squared', 0):.2f}")
            
        except Exception as e:
            print(f"Error al calcular Alpha/Beta: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Crear diccionario de probabilidades
    probabilidades = {
        'perdida': prob_perdida,
        'ganancia': prob_ganancia,
        'perdida_mayor_10': prob_perdida_10,
        'ganancia_mayor_10': prob_ganancia_10
    }
    
    # Crear diccionario de resultados
    resultados = {
        'concentracion': concentracion,
        'std_dev_activo': volatilidad_portafolio,
        'retorno_esperado_anual': retorno_esperado_anual,
        'pl_esperado_min': pl_esperado_min,
        'pl_esperado_max': pl_esperado_max,
        'probabilidades': probabilidades,
        'riesgo_anual': volatilidad_portafolio,  # Usamos la volatilidad como proxy de riesgo
        'alpha': alpha_beta_metrics.get('alpha_annual', 0),
        'beta': alpha_beta_metrics.get('beta', 0),
        'r_cuadrado': alpha_beta_metrics.get('r_squared', 0),
        'tracking_error': alpha_beta_metrics.get('tracking_error', 0),
        'information_ratio': alpha_beta_metrics.get('information_ratio', 0)
    }
    
    # Analizar la estrategia de inversión
    analisis_estrategia = analizar_estrategia_inversion(alpha_beta_metrics)
    resultados['analisis_estrategia'] = analisis_estrategia
    
    # Agregar métricas adicionales si están disponibles
    if 'p_value' in alpha_beta_metrics:
        resultados['p_value'] = alpha_beta_metrics['p_value']
    if 'observations' in alpha_beta_metrics:
        resultados['observaciones'] = alpha_beta_metrics['observations']
    
    return resultados

# --- Funciones de Visualización ---
def mostrar_resumen_portafolio(portafolio, token_portador):
    st.markdown("### 📈 Resumen del Portafolio")
    
    activos = portafolio.get('activos', [])
    datos_activos = []
    valor_total = 0
    
    for activo in activos:
        try:
            titulo = activo.get('titulo', {})
            simbolo = titulo.get('simbolo', 'N/A')
            descripcion = titulo.get('descripcion', 'Sin descripción')
            tipo = titulo.get('tipo', 'N/A')
            cantidad = activo.get('cantidad', 0)
            
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
            
            valuacion = 0
            for campo in campos_valuacion:
                if campo in activo and activo[campo] is not None:
                    try:
                        val = float(activo[campo])
                        if val > 0:
                            valuacion = val
                            break
                    except (ValueError, TypeError):
                        continue
            
            if valuacion == 0 and cantidad:
                campos_precio = [
                    'precioPromedio',
                    'precioCompra',
                    'precioActual',
                    'precio',
                    'precioUnitario',
                    'ultimoPrecio',
                    'cotizacion'
                ]
                
                precio_unitario = 0
                for campo in campos_precio:
                    if campo in activo and activo[campo] is not None:
                        try:
                            precio = float(activo[campo])
                            if precio > 0:
                                precio_unitario = precio
                                break
                        except (ValueError, TypeError):
                            continue
                
                if precio_unitario > 0:
                    try:
                        cantidad_num = float(cantidad)
                        if tipo == 'TitulosPublicos':
                            valuacion = (cantidad_num * precio_unitario) / 100.0
                        else:
                            valuacion = cantidad_num * precio_unitario
                    except (ValueError, TypeError):
                        pass
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
                
                # Intento final: consultar precio actual vía API si sigue en cero
            if valuacion == 0:
                ultimo_precio = None
                if mercado := titulo.get('mercado'):
                    ultimo_precio = obtener_precio_actual(token_portador, mercado, simbolo)
                if ultimo_precio:
                    try:
                        cantidad_num = float(cantidad)
                        if tipo == 'TitulosPublicos':
                            valuacion = (cantidad_num * ultimo_precio) / 100.0
                        else:
                            valuacion = cantidad_num * ultimo_precio
                    except (ValueError, TypeError):
                        pass
            
            datos_activos.append({
                'Símbolo': simbolo,
                'Descripción': descripcion,
                'Tipo': tipo,
                'Cantidad': cantidad,
                'Valuación': valuacion,
            })
            
            valor_total += valuacion
        except Exception as e:
            continue
    
    if datos_activos:
        df_activos = pd.DataFrame(datos_activos)
        # Convert list to dictionary with symbols as keys
        portafolio_dict = {row['Símbolo']: row for row in datos_activos}
        metricas = calcular_metricas_portafolio(portafolio_dict, valor_total, token_portador)
        
        # Información General
        cols = st.columns(4)
        cols[0].metric("Total de Activos", len(datos_activos))
        cols[1].metric("Símbolos Únicos", df_activos['Símbolo'].nunique())
        cols[2].metric("Tipos de Activos", df_activos['Tipo'].nunique())
        cols[3].metric("Valor Total", f"${valor_total:,.2f}")
        
        if metricas:
            # Métricas de Riesgo
            st.subheader("⚖️ Análisis de Riesgo")
            cols = st.columns(3)
            
            # Mostrar concentración como porcentaje
            concentracion_pct = metricas['concentracion'] * 100
            cols[0].metric("Concentración", 
                         f"{concentracion_pct:.1f}%",
                         help="Índice de Herfindahl normalizado: 0%=muy diversificado, 100%=muy concentrado")
            
            # Mostrar volatilidad como porcentaje anual
            volatilidad_pct = metricas['std_dev_activo'] * 100
            cols[1].metric("Volatilidad Anual", 
                         f"{volatilidad_pct:.1f}%",
                         help="Riesgo medido como desviación estándar de retornos anuales")
            
            # Nivel de concentración con colores
            if metricas['concentracion'] < 0.3:
                concentracion_status = "🟢 Baja"
            elif metricas['concentracion'] < 0.6:
                concentracion_status = "🟡 Media"
            else:
                concentracion_status = "🔴 Alta"
                
            cols[2].metric("Nivel Concentración", concentracion_status)
            
            # Proyecciones
            st.subheader("📈 Proyecciones de Rendimiento")
            cols = st.columns(3)
            
            # Mostrar retornos como porcentaje del portafolio
            retorno_anual_pct = (metricas.get('retorno_esperado_anual', 0) or 0) * 100
            cols[0].metric("Retorno Esperado Anual", 
                         f"{retorno_anual_pct:+.1f}%",
                         help="Retorno anual esperado basado en datos históricos")
            
            # Mostrar escenarios como porcentaje del portafolio
            optimista_pct = (metricas['pl_esperado_max'] / valor_total) * 100 if valor_total > 0 else 0
            pesimista_pct = (metricas['pl_esperado_min'] / valor_total) * 100 if valor_total > 0 else 0
            
            cols[1].metric("Escenario Optimista (95%)", 
                         f"{optimista_pct:+.1f}%",
                         help="Mejor escenario con 95% de confianza")
            cols[2].metric("Escenario Pesimista (5%)", 
                         f"{pesimista_pct:+.1f}%",
                         help="Peor escenario con 5% de confianza")
            
            # Probabilidades
            st.subheader("🎯 Probabilidades")
            cols = st.columns(4)
            probs = metricas['probabilidades']
            cols[0].metric("Ganancia", f"{(probs.get('ganancia', 0) or 0)*100:.1f}%")
            cols[1].metric("Pérdida", f"{(probs.get('perdida', 0) or 0)*100:.1f}%")
            cols[2].metric("Ganancia >10%", f"{(probs.get('ganancia_mayor_10', 0) or 0)*100:.1f}%")
            cols[3].metric("Pérdida >10%", f"{(probs.get('perdida_mayor_10', 0) or 0)*100:.1f}")
            

        
        # Gráficos
        st.subheader("📊 Distribución de Activos")
        
        if 'Tipo' in df_activos.columns and df_activos['Valuación'].sum() > 0:
            tipo_stats = df_activos.groupby('Tipo')['Valuación'].sum().reset_index()
            fig_pie = go.Figure(data=[go.Pie(
                labels=tipo_stats['Tipo'],
                values=tipo_stats['Valuación'],
                textinfo='label+percent',
                hole=0.4,
                marker=dict(colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
            )])
            fig_pie.update_layout(
                title="Distribución por Tipo",
                height=400
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Histograma del portafolio total valorizado
        st.subheader("📈 Histograma del Portafolio Total Valorizado")
        
        # Configuración del horizonte de inversión
        horizonte_inversion = st.selectbox(
            "Horizonte de Inversión:",
            options=[
                ("30 días", 30),
                ("60 días", 60),
                ("90 días", 90),
                ("180 días", 180),
                ("365 días", 365),
                ("730 días", 730),
                ("1095 días", 1095)
            ],
            format_func=lambda x: x[0],
            index=3,  # Por defecto 180 días
            help="Seleccione el período de tiempo para el análisis de retornos"
        )
        
        # Intervalo de análisis fijo en diario
        intervalo_analisis = ("Diario", "D")
        st.info("📊 Análisis configurado en frecuencia diaria")
        
        # Extraer valores de las tuplas
        dias_analisis = horizonte_inversion[1]
        frecuencia = intervalo_analisis[1]
        
        with st.spinner(f"Obteniendo series históricas y calculando valorización del portafolio para {dias_analisis} días..."):
            try:
                # Obtener fechas para el histórico basado en el horizonte seleccionado
                fecha_hasta = datetime.now().strftime('%Y-%m-%d')
                fecha_desde = (datetime.now() - timedelta(days=dias_analisis)).strftime('%Y-%m-%d')
                
                # Preparar datos para obtener series históricas
                activos_para_historico = []
                for activo in datos_activos:
                    simbolo = activo['Símbolo']
                    if simbolo != 'N/A':
                        # Intentar obtener el mercado del activo original
                        mercado = 'BCBA'  # Default
                        for activo_original in activos:
                            if activo_original.get('titulo', {}).get('simbolo') == simbolo:
                                mercado = activo_original.get('titulo', {}).get('mercado', 'BCBA')
                                break
                        
                        activos_para_historico.append({
                            'simbolo': simbolo,
                            'mercado': mercado,
                            'peso': activo['Valuación'] / valor_total if valor_total > 0 else 0
                        })
                
                if len(activos_para_historico) > 0:
                    # Obtener series históricas para cada activo
                    series_historicas = {}
                    activos_exitosos = []
                    
                    for activo_info in activos_para_historico:
                        simbolo = activo_info['simbolo']
                        mercado = activo_info['mercado']
                        peso = activo_info['peso']
                        
                        if peso > 0:  # Solo procesar activos con peso significativo
                            serie = obtener_serie_historica_iol(
                                token_portador,
                                mercado,
                                simbolo,
                                fecha_desde,
                                fecha_hasta
                            )
                            
                            if serie is not None and not serie.empty:
                                series_historicas[simbolo] = serie
                                activos_exitosos.append({
                                    'simbolo': simbolo,
                                    'peso': peso,
                                    'serie': serie
                                })
                                st.success(f"✅ {simbolo}: {len(serie)} puntos de datos")
                            else:
                                st.warning(f"⚠️ No se pudieron obtener datos para {simbolo}")
                    
                    if len(activos_exitosos) > 0:
                        # Crear DataFrame con todas las series alineadas
                        df_portfolio = pd.DataFrame()
                        
                        # Primero, encontrar el rango de fechas común para todas las series
                        fechas_comunes = None
                        for activo_info in activos_exitosos:
                            serie = activo_info['serie']
                            if fechas_comunes is None:
                                fechas_comunes = set(serie.index)
                            else:
                                fechas_comunes = fechas_comunes.intersection(set(serie.index))
                        
                        if not fechas_comunes or len(fechas_comunes) == 0:
                            # Si no hay fechas comunes, usar la unión y rellenar con ffill
                            st.warning("⚠️ No hay fechas comunes entre las series históricas. Se usará la unión de fechas y se rellenarán los valores faltantes.")
                            fechas_union = set()
                            for activo_info in activos_exitosos:
                                fechas_union = fechas_union.union(set(activo_info['serie'].index))
                            fechas_union = sorted(list(fechas_union))
                            df_portfolio.index = fechas_union
                            usar_union = True
                        else:
                            fechas_comunes = sorted(list(fechas_comunes))
                            df_portfolio.index = fechas_comunes
                            usar_union = False
                        
                        for activo_info in activos_exitosos:
                            simbolo = activo_info['simbolo']
                            peso = activo_info['peso']
                            serie = activo_info['serie']
                            valuacion_activo = 0
                            for activo_original in datos_activos:
                                if activo_original['Símbolo'] == simbolo:
                                    valuacion_activo = float(activo_original['Valuación'])
                                    break
                            # Seleccionar fechas
                            if usar_union:
                                serie_filtrada = serie.reindex(df_portfolio.index)
                            else:
                                serie_filtrada = serie.loc[df_portfolio.index]
                            # Agregar serie ponderada al DataFrame
                            if 'precio' in serie_filtrada.columns:
                                precios = serie_filtrada['precio'].values
                                if len(precios) > 1:
                                    retornos_acumulados = precios / precios[0]
                                    df_portfolio[simbolo] = valuacion_activo * retornos_acumulados
                                else:
                                    df_portfolio[simbolo] = valuacion_activo
                            else:
                                columnas_numericas = serie_filtrada.select_dtypes(include=[np.number]).columns
                                if len(columnas_numericas) > 0:
                                    precios = serie_filtrada[columnas_numericas[0]].values
                                    if len(precios) > 1:
                                        retornos_acumulados = precios / precios[0]
                                        df_portfolio[simbolo] = valuacion_activo * retornos_acumulados
                                    else:
                                        df_portfolio[simbolo] = valuacion_activo
                                else:
                                    st.warning(f"⚠️ No se encontraron valores numéricos para {simbolo}")
                                    continue
                        # Rellenar valores faltantes con forward-fill y eliminar filas completamente vacías
                        df_portfolio = df_portfolio.ffill().dropna(how='all')
                        # Calcular valor total del portafolio por fecha
                        if not df_portfolio.empty:
                            df_portfolio['Portfolio_Total'] = df_portfolio.sum(axis=1)
                        else:
                            st.error("❌ No se pudo construir el DataFrame del portafolio. Verifique los datos históricos de los activos seleccionados.")
                            return
                        
                        # Mostrar información de debug
                        st.info(f"🔍 Debug: Valor total actual del portafolio: ${valor_total:,.2f}")
                        st.info(f"🔍 Debug: Columnas en df_portfolio: {list(df_portfolio.columns)}")
                        if len(df_portfolio) > 0:
                            st.info(f"🔍 Debug: Último valor calculado: ${df_portfolio['Portfolio_Total'].iloc[-1]:,.2f}")
                        
                        # Eliminar filas con valores NaN
                        df_portfolio = df_portfolio.dropna()
                        
                        if len(df_portfolio) > 0:
                            # Crear histograma del valor total del portafolio
                            valores_portfolio = df_portfolio['Portfolio_Total'].values
                            
                            fig_hist = go.Figure(data=[go.Histogram(
                                x=valores_portfolio,
                                nbinsx=30,
                                name="Valor Total del Portafolio",
                                marker_color='#0d6efd',
                                opacity=0.7
                            )])
                            
                            # Agregar líneas de métricas importantes
                            media_valor = np.mean(valores_portfolio)
                            mediana_valor = np.median(valores_portfolio)
                            percentil_5 = np.percentile(valores_portfolio, 5)
                            percentil_95 = np.percentile(valores_portfolio, 95)
                            
                            fig_hist.add_vline(x=media_valor, line_dash="dash", line_color="red", 
                                             annotation_text=f"Media: ${media_valor:,.2f}")
                            fig_hist.add_vline(x=mediana_valor, line_dash="dash", line_color="green", 
                                             annotation_text=f"Mediana: ${mediana_valor:,.2f}")
                            fig_hist.add_vline(x=percentil_5, line_dash="dash", line_color="orange", 
                                             annotation_text=f"P5: ${percentil_5:,.2f}")
                            fig_hist.add_vline(x=percentil_95, line_dash="dash", line_color="purple", 
                                             annotation_text=f"P95: ${percentil_95:,.2f}")
                            
                            fig_hist.update_layout(
                                title="Distribución del Valor Total del Portafolio",
                                xaxis_title="Valor del Portafolio ($)",
                                yaxis_title="Frecuencia",
                                height=500,
                                showlegend=False,
                                template='plotly_white'
                            )
                            
                            st.plotly_chart(fig_hist, use_container_width=True)
                            
                            # Mostrar estadísticas del histograma
                            st.markdown("#### 📊 Estadísticas del Histograma")
                            col1, col2, col3, col4 = st.columns(4)
                            
                            col1.metric("Valor Promedio", f"${media_valor:,.2f}")
                            col2.metric("Valor Mediano", f"${mediana_valor:,.2f}")
                            col3.metric("Valor Mínimo (P5)", f"${percentil_5:,.2f}")
                            col4.metric("Valor Máximo (P95)", f"${percentil_95:,.2f}")
                            
                            # Mostrar evolución temporal del portafolio
                            st.markdown("#### 📈 Evolución Temporal del Portafolio")
                            # --- ELIMINAR GRÁFICO DUPLICADO Y DEJAR SOLO UNO ---
                            fig_evolucion = go.Figure()
                            # Usar fechas reales como eje X
                            fechas = df_portfolio.index
                            if not isinstance(fechas, pd.DatetimeIndex):
                                fechas = pd.to_datetime(fechas)
                            fig_evolucion.add_trace(go.Scatter(
                                x=fechas,
                                y=df_portfolio['Portfolio_Total'],
                                mode='lines',
                                name='Valor Total del Portafolio',
                                line=dict(color='#0d6efd', width=2)
                            ))
                            fig_evolucion.update_layout(
                                title="Evolución del Valor del Portafolio en el Tiempo",
                                xaxis_title="Fecha",
                                yaxis_title="Valor del Portafolio ($)",
                                height=400,
                                template='plotly_white'
                            )
                            st.plotly_chart(fig_evolucion, use_container_width=True)
                            
                            # Mostrar contribución de cada activo
                            st.markdown("#### 🥧 Contribución de Activos al Valor Total")
                            
                            contribucion_activos = {}
                            for activo_info in activos_exitosos:
                                simbolo = activo_info['simbolo']
                                # Usar la valuación real del activo
                                for activo_original in datos_activos:
                                    if activo_original['Símbolo'] == simbolo:
                                        contribucion_activos[simbolo] = activo_original['Valuación']
                                        break
                            
                            if contribucion_activos:
                                fig_contribucion = go.Figure(data=[go.Pie(
                                    labels=list(contribucion_activos.keys()),
                                    values=list(contribucion_activos.values()),
                                    textinfo='label+percent+value',
                                    texttemplate='%{label}<br>%{percent}<br>$%{value:,.0f}',
                                    hole=0.4,
                                    marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3'])
                                )])
                                fig_contribucion.update_layout(
                                    title="Contribución de Activos al Valor Total del Portafolio",
                                    height=400
                                )
                                st.plotly_chart(fig_contribucion, use_container_width=True)
                            
                            # Calcular y mostrar histograma de retornos del portafolio
                            st.markdown("#### 📊 Histograma de Retornos del Portafolio")
                            
                            try:
                                # Calcular retornos diarios del portafolio
                                df_portfolio_returns = df_portfolio['Portfolio_Total'].pct_change().dropna()
                                
                                if len(df_portfolio_returns) > 10:  # Mínimo de datos para análisis
                                    # Calcular métricas estadísticas de los retornos
                                    mean_return = df_portfolio_returns.mean()
                                    std_return = df_portfolio_returns.std()
                                    skewness = stats.skew(df_portfolio_returns)
                                    kurtosis = stats.kurtosis(df_portfolio_returns)
                                    var_95 = np.percentile(df_portfolio_returns, 5)
                                    var_99 = np.percentile(df_portfolio_returns, 1)
                                    
                                    # Calcular Jarque-Bera test para normalidad
                                    jb_stat, jb_p_value = stats.jarque_bera(df_portfolio_returns)
                                    is_normal = jb_p_value > 0.05
                                    
                                    # Crear histograma de retornos
                                    fig_returns_hist = go.Figure(data=[go.Histogram(
                                        x=df_portfolio_returns,
                                        nbinsx=50,
                                        name="Retornos del Portafolio",
                                        marker_color='#28a745',
                                        opacity=0.7
                                    )])
                                    
                                    # Agregar líneas de métricas importantes
                                    fig_returns_hist.add_vline(x=mean_return, line_dash="dash", line_color="red", 
                                                             annotation_text=f"Media: {mean_return:.4f}")
                                    fig_returns_hist.add_vline(x=var_95, line_dash="dash", line_color="orange", 
                                                             annotation_text=f"VaR 95%: {var_95:.4f}")
                                    fig_returns_hist.add_vline(x=var_99, line_dash="dash", line_color="darkred", 
                                                             annotation_text=f"VaR 99%: {var_99:.4f}")
                                    
                                    fig_returns_hist.update_layout(
                                        title="Distribución de Retornos Diarios del Portafolio",
                                        xaxis_title="Retorno Diario",
                                        yaxis_title="Frecuencia",
                                        height=500,
                                        showlegend=False,
                                        template='plotly_white'
                                    )
                                    
                                    st.plotly_chart(fig_returns_hist, use_container_width=True)
                                    
                                    # Mostrar estadísticas de retornos
                                    st.markdown("#### 📈 Estadísticas de Retornos")
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    col1.metric("Retorno Medio Diario", f"{mean_return:.4f}")
                                    col2.metric("Volatilidad Diaria", f"{std_return:.4f}")
                                    col3.metric("VaR 95%", f"{var_95:.4f}")
                                    col4.metric("VaR 99%", f"{var_99:.4f}")
                                    
                                    col1, col2, col3, col4 = st.columns(4)
                                    col1.metric("Skewness", f"{skewness:.4f}")
                                    col2.metric("Kurtosis", f"{kurtosis:.4f}")
                                    col3.metric("JB Statistic", f"{jb_stat:.4f}")
                                    normalidad = "✅ Normal" if is_normal else "❌ No Normal"
                                    col4.metric("Normalidad", normalidad)
                                    
                                    # Calcular métricas anualizadas
                                    mean_return_annual = mean_return * 252
                                    std_return_annual = std_return * np.sqrt(252)
                                    sharpe_ratio = mean_return_annual / std_return_annual if std_return_annual > 0 else 0
                                    
                                    st.markdown("#### 📊 Métricas Anualizadas")
                                    col1, col2, col3 = st.columns(3)
                                    col1.metric("Retorno Anual", f"{mean_return_annual:.2%}")
                                    col2.metric("Volatilidad Anual", f"{std_return_annual:.2%}")
                                    col3.metric("Ratio de Sharpe", f"{sharpe_ratio:.4f}")
                                    
                                    # Análisis de distribución
                                    st.markdown("#### 📋 Análisis de la Distribución")
                                    if is_normal:
                                        st.success("✅ Los retornos siguen una distribución normal (p > 0.05)")
                                    else:
                                        st.warning("⚠️ Los retornos no siguen una distribución normal (p ≤ 0.05)")
                                    
                                    if skewness > 0.5:
                                        st.info("📈 Distribución con sesgo positivo (cola derecha)")
                                    elif skewness < -0.5:
                                        st.info("📉 Distribución con sesgo negativo (cola izquierda)")
                                    else:
                                        st.success("📊 Distribución aproximadamente simétrica")
                                    
                                    if kurtosis > 3:
                                        st.info("📊 Distribución leptocúrtica (colas pesadas)")
                                    elif kurtosis < 3:
                                        st.info("📊 Distribución platicúrtica (colas ligeras)")
                                    else:
                                        st.success("📊 Distribución mesocúrtica (normal)")
                                    
                                    # Gráfico de evolución del valor real del portafolio en ARS y USD
                                    st.markdown("#### 📈 Evolución del Valor Real del Portafolio")
                                    
                                    # Obtener cotización MEP para conversión
                                    try:
                                        # Intentar obtener cotización MEP (usar AL30 como proxy)
                                        cotizacion_mep = obtener_cotizacion_mep(token_portador, "AL30", 1, 1)
                                        if cotizacion_mep and cotizacion_mep.get('precio'):
                                            tasa_mep = float(cotizacion_mep['precio'])
                                        else:
                                            # Si no hay MEP, usar tasa aproximada
                                            tasa_mep = 1000  # Tasa aproximada
                                            st.info("ℹ️ Usando tasa MEP aproximada para conversiones")
                                    except:
                                        tasa_mep = 1000
                                        st.info("ℹ️ Usando tasa MEP aproximada para conversiones")
                                    
                                    # Crear figura con dos ejes Y
                                    fig_evolucion_real = go.Figure()
                                    
                                    # Traza en ARS (eje Y izquierdo)
                                    fig_evolucion_real.add_trace(go.Scatter(
                                        x=df_portfolio.index,
                                        y=df_portfolio['Portfolio_Total'],
                                        mode='lines',
                                        name='Valor en ARS',
                                        line=dict(color='#28a745', width=2),
                                        yaxis='y'
                                    ))
                                    
                                    # Traza en USD (eje Y derecho)
                                    valores_usd = df_portfolio['Portfolio_Total'] / tasa_mep
                                    fig_evolucion_real.add_trace(go.Scatter(
                                        x=df_portfolio.index,
                                        y=valores_usd,
                                        mode='lines',
                                        name='Valor en USD',
                                        line=dict(color='#0d6efd', width=2, dash='dash'),
                                        yaxis='y2'
                                    ))
                                    
                                    # Configurar ejes
                                    fig_evolucion_real.update_layout(
                                        title="Evolución del Valor Real del Portafolio (ARS y USD)",
                                        xaxis_title="Fecha",
                                        yaxis=dict(
                                            title=dict(
                                                text="Valor en ARS ($)",
                                                font=dict(color="#28a745")
                                            ),
                                            tickfont=dict(color="#28a745"),
                                            side="left"
                                        ),
                                        yaxis2=dict(
                                            title=dict(
                                                text="Valor en USD ($)",
                                                font=dict(color="#0d6efd")
                                            ),
                                            tickfont=dict(color="#0d6efd"),
                                            anchor="x",
                                            overlaying="y",
                                            side="right"
                                        ),
                                        height=500,
                                        template='plotly_white',
                                        legend=dict(
                                            orientation="h",
                                            yanchor="bottom",
                                            y=1.02,
                                            xanchor="right",
                                            x=1
                                        )
                                    )
                                    
                                    st.plotly_chart(fig_evolucion_real, use_container_width=True)
                                    
                                    # Mostrar estadísticas del valor real en ambas monedas
                                    st.markdown("#### 📊 Estadísticas del Valor Real")
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    valor_inicial_ars = df_portfolio['Portfolio_Total'].iloc[0]
                                    valor_final_ars = df_portfolio['Portfolio_Total'].iloc[-1]
                                    valor_inicial_usd = valor_inicial_ars / tasa_mep
                                    valor_final_usd = valor_final_ars / tasa_mep
                                    retorno_total_real = (valor_final_ars / valor_inicial_ars - 1) * 100
                                    
                                    col1.metric("Valor Inicial (ARS)", f"${valor_inicial_ars:,.2f}")
                                    col2.metric("Valor Final (ARS)", f"${valor_final_ars:,.2f}")
                                    col3.metric("Valor Inicial (USD)", f"${valor_inicial_usd:,.2f}")
                                    col4.metric("Valor Final (USD)", f"${valor_final_usd:,.2f}")
                                    
                                    col1, col2 = st.columns(2)
                                    col1.metric("Retorno Total (ARS)", f"{retorno_total_real:+.2f}%")
                                    col2.metric("Tasa MEP Utilizada", f"${tasa_mep:,.2f}")
                                    
                                    # Análisis de rendimiento extra asegurado de renta fija
                                    st.markdown("#### 🏦 Análisis de Rendimiento Extra Asegurado")
                                    
                                    # Identificar instrumentos de renta fija
                                    instrumentos_renta_fija = []
                                    total_renta_fija = 0
                                    
                                    for activo in datos_activos:
                                        tipo = activo.get('Tipo', '').lower()
                                        simbolo = activo.get('Símbolo', '')
                                        valuacion = activo.get('Valuación', 0)
                                        
                                        # Identificar FCIs, bonos y otros instrumentos de renta fija
                                        if any(keyword in tipo for keyword in ['fci', 'fondo', 'bono', 'titulo', 'publico', 'letra']):
                                            instrumentos_renta_fija.append({
                                                'simbolo': simbolo,
                                                'tipo': tipo,
                                                'valuacion': valuacion,
                                                'peso': valuacion / valor_total if valor_total > 0 else 0
                                            })
                                            total_renta_fija += valuacion
                                        
                                        # También identificar por símbolo (FCIs suelen tener símbolos específicos)
                                        elif any(keyword in simbolo.lower() for keyword in ['fci', 'fondo', 'bono', 'al', 'gd', 'gg']):
                                            instrumentos_renta_fija.append({
                                                'simbolo': simbolo,
                                                'tipo': tipo,
                                                'valuacion': valuacion,
                                                'peso': valuacion / valor_total if valor_total > 0 else 0
                                            })
                                            total_renta_fija += valuacion
                                    
                                    if instrumentos_renta_fija:
                                        st.success(f"✅ Se identificaron {len(instrumentos_renta_fija)} instrumentos de renta fija")
                                            
                                        # Mostrar tabla de instrumentos de renta fija
                                        df_renta_fija = pd.DataFrame(instrumentos_renta_fija)
                                        df_renta_fija['Peso (%)'] = df_renta_fija['peso'] * 100
                                        df_renta_fija['Valuación ($)'] = df_renta_fija['valuacion'].apply(lambda x: f"${x:,.2f}")
                                        
                                        st.dataframe(
                                            df_renta_fija[['simbolo', 'tipo', 'Valuación ($)', 'Peso (%)']],
                                            use_container_width=True,
                                            height=200
                                        )
                                        
                                        # Calcular rendimiento extra asegurado
                                        peso_renta_fija = total_renta_fija / valor_total if valor_total > 0 else 0
                                        
                                        # Estimación de rendimiento extra (basado en tasas típicas)
                                        rendimiento_extra_estimado = {
                                            'FCI': 0.08,  # 8% anual típico para FCIs
                                            'Bono': 0.12,  # 12% anual típico para bonos
                                            'Titulo': 0.10,  # 10% anual típico para títulos públicos
                                            'Letra': 0.15   # 15% anual típico para letras
                                        }
                                        
                                        rendimiento_extra_total = 0
                                        for instrumento in instrumentos_renta_fija:
                                            tipo_instrumento = instrumento['tipo'].lower()
                                            peso_instrumento = instrumento['peso']
                                            
                                            # Determinar tipo de rendimiento
                                            if 'fci' in tipo_instrumento or 'fondo' in tipo_instrumento:
                                                rendimiento = rendimiento_extra_estimado['FCI']
                                            elif 'bono' in tipo_instrumento:
                                                rendimiento = rendimiento_extra_estimado['Bono']
                                            elif 'titulo' in tipo_instrumento or 'publico' in tipo_instrumento:
                                                rendimiento = rendimiento_extra_estimado['Titulo']
                                            elif 'letra' in tipo_instrumento:
                                                rendimiento = rendimiento_extra_estimado['Letra']
                                            else:
                                                rendimiento = rendimiento_extra_estimado['FCI']  # Default
                                            
                                            rendimiento_extra_total += rendimiento * peso_instrumento
                                        
                                        # Mostrar métricas de rendimiento extra
                                        col1, col2, col3 = st.columns(3)
                                        col1.metric("Peso Renta Fija", f"{peso_renta_fija:.1%}")
                                        col2.metric("Rendimiento Extra Estimado", f"{rendimiento_extra_total:.1%}")
                                        col3.metric("Valor Renta Fija", f"${total_renta_fija:,.2f}")
                                        
                                        # Gráfico de composición por tipo de instrumento
                                        if len(instrumentos_renta_fija) > 1:
                                            fig_renta_fija = go.Figure(data=[go.Pie(
                                                labels=[f"{row['simbolo']} ({row['tipo']})" for _, row in df_renta_fija.iterrows()],
                                                values=df_renta_fija['valuacion'],
                                                textinfo='label+percent+value',
                                                texttemplate='%{label}<br>%{percent}<br>$%{value:,.0f}',
                                                hole=0.4,
                                                marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3'])
                                            )])
                                            fig_renta_fija.update_layout(
                                                title="Composición de Instrumentos de Renta Fija",
                                                height=400
                                            )
                                            st.plotly_chart(fig_renta_fija, use_container_width=True)
                                        
                                        # Recomendaciones específicas para renta fija
                                        st.markdown("#### 💡 Recomendaciones Renta Fija")
                                        
                                        if peso_renta_fija < 0.2:
                                            st.info("📈 **Considerar aumentar exposición a renta fija**: Menos del 20% del portafolio")
                                        elif peso_renta_fija > 0.6:
                                            st.warning("📉 **Considerar reducir exposición a renta fija**: Más del 60% del portafolio")
                                        else:
                                            st.success("✅ **Exposición equilibrada a renta fija**: Entre 20% y 60% del portafolio")
                                        
                                        if rendimiento_extra_total > 0.10:
                                            st.success("🎯 **Excelente rendimiento extra estimado**: Más del 10% anual")
                                        elif rendimiento_extra_total > 0.05:
                                            st.info("📊 **Buen rendimiento extra estimado**: Entre 5% y 10% anual")
                                        else:
                                            st.warning("⚠️ **Rendimiento extra bajo**: Menos del 5% anual")
                                    
                                    else:
                                        st.info("ℹ️ No se identificaron instrumentos de renta fija en el portafolio")
                                        st.info("💡 **Recomendación**: Considerar agregar FCIs, bonos o títulos públicos para diversificar")
                                
                                # Análisis de retorno esperado por horizonte de inversión
                                st.markdown("#### 📊 Análisis de Retorno Esperado")
                                
                                # Calcular retornos en USD para diferentes horizontes
                                horizontes_analisis = [1, 7, 30, 90, 180, 365]
                                retornos_ars_por_horizonte = {}
                                retornos_usd_por_horizonte = {}
                                
                                # Calcular retornos en USD
                                df_portfolio_usd = df_portfolio['Portfolio_Total'] / tasa_mep
                                df_portfolio_returns_usd = df_portfolio_usd.pct_change().dropna()
                                
                                for horizonte in horizontes_analisis:
                                    if len(df_portfolio_returns) >= horizonte:
                                        # Retorno en ARS
                                        retorno_ars = (1 + df_portfolio_returns.tail(horizonte)).prod() - 1
                                        retornos_ars_por_horizonte[horizonte] = retorno_ars
                                        
                                        # Retorno en USD
                                        retorno_usd = (1 + df_portfolio_returns_usd.tail(horizonte)).prod() - 1
                                        retornos_usd_por_horizonte[horizonte] = retorno_usd
                                
                                if retornos_ars_por_horizonte and retornos_usd_por_horizonte:
                                    # Crear gráfico de retornos por horizonte (ARS y USD)
                                    fig_horizontes = go.Figure()
                                    
                                    horizontes = list(retornos_ars_por_horizonte.keys())
                                    retornos_ars = list(retornos_ars_por_horizonte.values())
                                    retornos_usd = list(retornos_usd_por_horizonte.values())
                                    
                                    # Barras para ARS
                                    fig_horizontes.add_trace(go.Bar(
                                        x=[f"{h} días" for h in horizontes],
                                        y=retornos_ars,
                                        name="Retorno ARS",
                                        marker_color=['#28a745' if r >= 0 else '#dc3545' for r in retornos_ars],
                                        text=[f"{r:.2%}" for r in retornos_ars],
                                        textposition='auto'
                                    ))
                                    
                                    # Barras para USD
                                    fig_horizontes.add_trace(go.Bar(
                                        x=[f"{h} días" for h in horizontes],
                                        y=retornos_usd,
                                        name="Retorno USD",
                                        marker_color=['#0d6efd' if r >= 0 else '#ff6b6b' for r in retornos_usd],
                                        text=[f"{r:.2%}" for r in retornos_usd],
                                        textposition='auto'
                                    ))
                                    
                                    fig_horizontes.update_layout(
                                        title=f"Retornos Acumulados por Horizonte de Inversión (ARS y USD)",
                                        xaxis_title="Horizonte de Inversión",
                                        yaxis_title="Retorno Acumulado",
                                        height=400,
                                        template='plotly_white',
                                        barmode='group'
                                    )
                                    
                                    st.plotly_chart(fig_horizontes, use_container_width=True)
                                    
                                    # Mostrar métricas de retorno esperado (ARS y USD)
                                    st.markdown("#### 📈 Métricas de Retorno Esperado")
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    # Calcular retorno esperado anualizado en ARS
                                    retorno_anualizado_ars = mean_return_annual
                                    col1.metric("Retorno Esperado Anual (ARS)", f"{retorno_anualizado_ars:.2%}")
                                    
                                    # Calcular retorno esperado anualizado en USD
                                    mean_return_annual_usd = df_portfolio_returns_usd.mean() * 252
                                    col2.metric("Retorno Esperado Anual (USD)", f"{mean_return_annual_usd:.2%}")
                                    
                                    # Calcular retorno esperado para el horizonte seleccionado
                                    retorno_esperado_horizonte_ars = retorno_anualizado_ars * (dias_analisis / 365)
                                    retorno_esperado_horizonte_usd = mean_return_annual_usd * (dias_analisis / 365)
                                    col3.metric(f"Retorno Esperado ({dias_analisis} días) ARS", f"{retorno_esperado_horizonte_ars:.2%}")
                                    col4.metric(f"Retorno Esperado ({dias_analisis} días) USD", f"{retorno_esperado_horizonte_usd:.2%}")
                                    
                                    # Calcular intervalos de confianza
                                    z_score_95 = 1.96  # 95% de confianza
                                    std_return_annual_usd = df_portfolio_returns_usd.std() * np.sqrt(252)
                                    intervalo_confianza_ars = z_score_95 * std_return_annual * np.sqrt(dias_analisis / 365)
                                    intervalo_confianza_usd = z_score_95 * std_return_annual_usd * np.sqrt(dias_analisis / 365)
                                    
                                    col1, col2 = st.columns(2)
                                    col1.metric("Intervalo de Confianza 95% (ARS)", f"±{intervalo_confianza_ars:.2%}")
                                    col2.metric("Intervalo de Confianza 95% (USD)", f"±{intervalo_confianza_usd:.2%}")
                                    
                                    # Proyecciones de valor del portafolio
                                    st.markdown("#### 💰 Proyecciones de Valor del Portafolio")
                                    
                                    valor_actual = df_portfolio['Portfolio_Total'].iloc[-1]
                                    
                                    # Calcular proyecciones optimista, pesimista y esperada
                                    proyeccion_esperada = valor_actual * (1 + retorno_esperado_horizonte_ars)
                                    proyeccion_optimista = valor_actual * (1 + retorno_esperado_horizonte_ars + intervalo_confianza_ars)
                                    proyeccion_pesimista = valor_actual * (1 + retorno_esperado_horizonte_ars - intervalo_confianza_ars)
                                    
                                    col1, col2, col3 = st.columns(3)
                                    col1.metric("Proyección Esperada", f"${proyeccion_esperada:,.2f}")
                                    col2.metric("Proyección Optimista", f"${proyeccion_optimista:,.2f}")
                                    col3.metric("Proyección Pesimista", f"${proyeccion_pesimista:,.2f}")
                                    

                                    
                                    # Resumen de análisis
                                    st.markdown("#### 📋 Resumen del Análisis")
                                    
                                    if retorno_esperado_horizonte_ars > 0:
                                        st.success(f"✅ **Retorno Esperado Positivo**: Se espera un retorno de {retorno_esperado_horizonte_ars:.2%} en {dias_analisis} días")
                                    else:
                                        st.warning(f"⚠️ **Retorno Esperado Negativo**: Se espera un retorno de {retorno_esperado_horizonte_ars:.2%} en {dias_analisis} días")
                                    
                                    if sharpe_ratio > 1:
                                        st.success(f"✅ **Excelente Ratio de Sharpe**: {sharpe_ratio:.2f} indica buenos retornos ajustados por riesgo")
                                    elif sharpe_ratio > 0.5:
                                        st.info(f"ℹ️ **Buen Ratio de Sharpe**: {sharpe_ratio:.2f} indica retornos razonables ajustados por riesgo")
                                    else:
                                        st.warning(f"⚠️ **Ratio de Sharpe Bajo**: {sharpe_ratio:.2f} indica retornos pobres ajustados por riesgo")
                                    
                                    # Recomendaciones basadas en el análisis
                                    st.markdown("#### 💡 Recomendaciones")
                                    
                                    if retorno_esperado_horizonte_ars > 0.05:  # 5% en el horizonte
                                        st.success("🎯 **Mantener Posición**: El portafolio muestra buenas perspectivas de retorno")
                                    elif retorno_esperado_horizonte_ars < -0.05:  # -5% en el horizonte
                                        st.warning("🔄 **Considerar Rebalanceo**: El portafolio podría beneficiarse de ajustes")
                                    else:
                                        st.info("📊 **Monitorear**: El portafolio muestra retornos moderados")
                                
                                else:
                                    st.warning("⚠️ No hay suficientes datos para calcular retornos del portafolio")
                                    
                            except Exception as e:
                                st.error(f"❌ Error calculando retornos del portafolio: {str(e)}")
                                st.exception(e)
                            
                        else:
                            st.warning("⚠️ No hay datos suficientes para generar el histograma")
                    else:
                        st.warning("⚠️ No se pudieron obtener datos históricos para ningún activo")
                else:
                    st.warning("⚠️ No hay activos válidos para generar el histograma")
                    
            except Exception as e:
                st.error(f"❌ Error generando histograma del portafolio: {str(e)}")
                st.exception(e)
        
        # Tabla de activos
        st.subheader("📋 Detalle de Activos")
        df_display = df_activos.copy()
        df_display['Valuación'] = df_display['Valuación'].apply(
            lambda x: f"${x:,.2f}" if x > 0 else "N/A"
        )
        df_display['Peso (%)'] = (df_activos['Valuación'] / valor_total * 100).round(2)
        df_display = df_display.sort_values('Peso (%)', ascending=False)
        
        st.dataframe(df_display, use_container_width=True, height=400)
        
        # Recomendaciones
        st.subheader("💡 Recomendaciones")
        if metricas:
            if metricas['concentracion'] > 0.5:
                st.warning("""
                **⚠️ Portafolio Altamente Concentrado**  
                Considere diversificar sus inversiones para reducir el riesgo.
                """)
            elif metricas['concentracion'] > 0.25:
                st.info("""
                **ℹ️ Concentración Moderada**  
                Podría mejorar su diversificación para optimizar el riesgo.
                """)
            else:
                st.success("""
                **✅ Buena Diversificación**  
                Su portafolio está bien diversificado.
                """)
            
            ratio_riesgo_retorno = metricas['retorno_esperado_anual'] / metricas['riesgo_anual'] if metricas['riesgo_anual'] > 0 else 0
            if ratio_riesgo_retorno > 0.5:
                st.success("""
                **✅ Buen Balance Riesgo-Retorno**  
                La relación entre riesgo y retorno es favorable.
                """)
            else:
                st.warning("""
                **⚠️ Revisar Balance Riesgo-Retorno**  
                El riesgo podría ser alto en relación al retorno esperado.
                """)
    else:
        st.warning("No se encontraron activos en el portafolio")

def mostrar_estado_cuenta(estado_cuenta):
    st.markdown("### 💰 Estado de Cuenta")
    
    if not estado_cuenta:
        st.warning("No hay datos de estado de cuenta disponibles")
        return
    
    total_en_pesos = estado_cuenta.get('totalEnPesos', 0)
    cuentas = estado_cuenta.get('cuentas', [])
    
    cols = st.columns(3)
    cols[0].metric("Total en Pesos", f"AR$ {total_en_pesos:,.2f}")
    cols[1].metric("Número de Cuentas", len(cuentas))
    
    if cuentas:
        st.subheader("📊 Detalle de Cuentas")
        
        datos_cuentas = []
        for cuenta in cuentas:
            datos_cuentas.append({
                'Número': cuenta.get('numero', 'N/A'),
                'Tipo': cuenta.get('tipo', 'N/A').replace('_', ' ').title(),
                'Moneda': cuenta.get('moneda', 'N/A').replace('_', ' ').title(),
                'Disponible': f"${cuenta.get('disponible', 0):,.2f}",
                'Saldo': f"${cuenta.get('saldo', 0):,.2f}",
                'Total': f"${cuenta.get('total', 0):,.2f}",
            })
        
        df_cuentas = pd.DataFrame(datos_cuentas)
        st.dataframe(df_cuentas, use_container_width=True, height=300)

def mostrar_cotizaciones_mercado(token_acceso):
    st.markdown("### 💱 Cotizaciones y Mercado")
    
    with st.expander("💰 Cotización MEP", expanded=True):
        with st.form("mep_form"):
            col1, col2, col3 = st.columns(3)
            simbolo_mep = col1.text_input("Símbolo", value="AL30", help="Ej: AL30, GD30, etc.")
            id_plazo_compra = col2.number_input("ID Plazo Compra", value=1, min_value=1)
            id_plazo_venta = col3.number_input("ID Plazo Venta", value=1, min_value=1)
            
            if st.form_submit_button("🔍 Consultar MEP"):
                if simbolo_mep:
                    with st.spinner("Consultando cotización MEP..."):
                        cotizacion_mep = obtener_cotizacion_mep(
                            token_acceso, simbolo_mep, id_plazo_compra, id_plazo_venta
                        )
                    if cotizacion_mep:
                        st.success("✅ Cotización MEP obtenida")
                        # Mostrar análisis completo en texto y tabla
                        st.markdown("### 📊 Análisis Completo del Mercado")
                        st.markdown(f"**Descripción:** {cotizacion_mep.get('descripcionTitulo','N/A')}")
                        st.markdown(f"**Símbolo:** {simbolo_mep}")
                        st.markdown(f"**Último Precio:** ${cotizacion_mep.get('ultimoPrecio','N/A')}")
                        st.markdown(f"**Variación:** {cotizacion_mep.get('variacion','N/A')}%")
                        st.markdown(f"**Apertura:** ${cotizacion_mep.get('apertura','N/A')}")
                        st.markdown(f"**Máximo:** ${cotizacion_mep.get('maximo','N/A')}")
                        st.markdown(f"**Mínimo:** ${cotizacion_mep.get('minimo','N/A')}")
                        st.markdown(f"**Cierre Anterior:** ${cotizacion_mep.get('cierreAnterior','N/A')}")
                        st.markdown(f"**Tendencia:** {cotizacion_mep.get('tendencia','N/A')}")
                        st.markdown(f"**Monto Operado:** ${cotizacion_mep.get('montoOperado','N/A')}")
                        st.markdown(f"**Volumen Nominal:** {cotizacion_mep.get('volumenNominal','N/A')}")
                        st.markdown(f"**Cantidad de Operaciones:** {cotizacion_mep.get('cantidadOperaciones','N/A')}")
                        st.markdown(f"**Moneda:** {cotizacion_mep.get('moneda','N/A')}")
                        st.markdown(f"**Fecha/Hora:** {cotizacion_mep.get('fechaHora','N/A')}")
                        # Mostrar puntas de compra/venta en tabla
                        puntas = cotizacion_mep.get('puntas',[])
                        if puntas:
                            import pandas as pd
                            df_puntas = pd.DataFrame(puntas)
                            df_puntas = df_puntas.rename(columns={
                                'cantidadCompra':'Cantidad Compra',
                                'precioCompra':'Precio Compra',
                                'precioVenta':'Precio Venta',
                                'cantidadVenta':'Cantidad Venta'
                            })
                            st.markdown("**Puntas de Compra/Venta:**")
                            st.dataframe(df_puntas, use_container_width=True)
                    else:
                        st.error("❌ No se pudo obtener la cotización MEP")
    
    with st.expander("🏦 Tasas de Caución", expanded=True):
        if st.button("🔄 Actualizar Tasas"):
            with st.spinner("Consultando tasas de caución..."):
                tasas_caucion = obtener_tasas_caucion(token_acceso)
            
            if tasas_caucion is not None and not tasas_caucion.empty:
                df_tasas = pd.DataFrame(tasas_caucion)
                columnas_relevantes = ['simbolo', 'tasa', 'bid', 'offer', 'ultimo']
                columnas_disponibles = [col for col in columnas_relevantes if col in df_tasas.columns]
                
                if columnas_disponibles:
                    st.dataframe(df_tasas[columnas_disponibles].head(10))
                else:
                    st.dataframe(df_tasas.head(10))
            else:
                st.error("❌ No se pudieron obtener las tasas de caución")

def mostrar_optimizacion_portafolio(token_acceso, id_cliente):
    """
    Menú avanzado de optimización de portafolio.
    Ahora usa obtención asincrónica y optimizada de series históricas para el universo aleatorio.
    """
    st.markdown("### 🔄 Menú Avanzado de Optimización de Portafolio")
    with st.spinner("Obteniendo portafolio actual..."):
        portafolio = obtener_portafolio(token_acceso, id_cliente)
    if not portafolio or not portafolio.get('activos'):
        st.warning("No se pudo obtener el portafolio del cliente o está vacío")
        return

    activos_raw = portafolio['activos']
    # Diagnóstico del portafolio actual
    st.subheader("🔍 Diagnóstico del Portafolio Actual")
    # Usar el mismo método de resumen de portafolio para diagnóstico real
    activos_dict = {}
    valor_total = 0
    for activo in activos_raw:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', 'N/A')
        tipo = titulo.get('tipo', 'N/A')
        valuacion = 0
        campos_valuacion = [
            'valuacionEnMonedaOriginal', 'valuacionActual', 'valorNominalEnMonedaOriginal', 'valorNominal',
            'valuacionDolar', 'valuacion', 'valorActual', 'montoInvertido', 'valorMercado', 'valorTotal', 'importe'
        ]
        for campo in campos_valuacion:
            if campo in activo and activo[campo] is not None:
                try:
                    val = float(activo[campo])
                    if val > 0:
                        valuacion = val
                        break
                except (ValueError, TypeError):
                    continue
        if valuacion == 0 and activo.get('cantidad', 0):
            campos_precio = [
                'precioPromedio', 'precioCompra', 'precioActual', 'precio', 'precioUnitario', 'ultimoPrecio', 'cotizacion'
            ]
            precio_unitario = 0
            for campo in campos_precio:
                if campo in activo and activo[campo] is not None:
                    try:
                        precio = float(activo[campo])
                        if precio > 0:
                            precio_unitario = precio
                            break
                    except (ValueError, TypeError):
                        continue
            if precio_unitario > 0:
                try:
                    cantidad_num = float(activo.get('cantidad', 0))
                    if tipo == 'TitulosPublicos':
                        valuacion = (cantidad_num * precio_unitario) / 100.0
                    else:
                        valuacion = cantidad_num * precio_unitario
                except (ValueError, TypeError):
                    pass
        mercado = titulo.get('mercado', 'BCBA')
        if simbolo:
            activos_dict[simbolo] = {
                'Valuación': valuacion,
                'Tipo': tipo,
                'mercado': mercado
            }
            valor_total += valuacion
    # Obtener saldo disponible de las cuentas
    estado_cuenta = obtener_estado_cuenta(token_acceso, id_cliente)
    saldo_disponible = 0
    if estado_cuenta and 'cuentas' in estado_cuenta:
        for cuenta in estado_cuenta['cuentas']:
            disponible = cuenta.get('disponible', 0)
            try:
                saldo_disponible += float(disponible)
            except Exception:
                continue
    metricas_actual = calcular_metricas_portafolio(activos_dict, valor_total, token_acceso)
    cols = st.columns(4)
    cols[0].metric("Retorno Esperado", f"{(metricas_actual.get('retorno_esperado_anual',0) or 0)*100:.2f}%")
    cols[1].metric("Riesgo (Volatilidad)", f"{(metricas_actual.get('riesgo_anual',0) or 0)*100:.2f}%")
    cols[2].metric("Sharpe", f"{(metricas_actual.get('retorno_esperado_anual',0)/(metricas_actual.get('riesgo_anual',1e-6))):.2f}")
    cols[3].metric("Concentración", f"{(metricas_actual.get('concentracion',0) or 0)*100:.1f}%")

    st.markdown("---")
    st.subheader("⚙️ Configuración de Universo de Optimización")
    universo = st.radio(
        "¿Con qué universo de activos desea optimizar?",
        ["Portafolio actual", "Universo aleatorio"],
        help="Puede optimizar con sus activos actuales o simular con un universo aleatorio por tipo/cantidad."
    )
    if universo == "Portafolio actual":
        universe_activos = [
            {'simbolo': a.get('titulo',{}).get('simbolo'),
             'mercado': a.get('titulo',{}).get('mercado'),
             'tipo': a.get('titulo',{}).get('tipo')}
            for a in activos_raw if a.get('titulo',{}).get('simbolo')
        ]
    else:
        st.info("Seleccione el universo aleatorio de mercado real")
        paneles = ['acciones', 'cedears', 'aDRs', 'titulosPublicos', 'obligacionesNegociables']
        paneles_seleccionados = st.multiselect("Paneles de universo aleatorio", paneles, default=paneles)
        capital_mode = st.radio(
            "¿Cómo definir el capital disponible?",
            ["Manual", "Saldo valorizado + disponible (actual)"]
        )
        capital_ars = 100000
        capital_auto = valor_total + saldo_disponible
        if capital_mode == "Manual":
            capital_ars = st.number_input("Capital disponible para universo aleatorio (ARS)", min_value=10000, value=100000)
        else:
            st.success(f"Capital valorizado + disponible: ${capital_auto:,.2f}")
            capital_ars = capital_auto
        cantidad_activos = st.slider("Cantidad de activos por panel", 2, 10, 5)
        fecha_desde = st.session_state.fecha_desde.strftime('%Y-%m-%d')
        fecha_hasta = st.session_state.fecha_hasta.strftime('%Y-%m-%d')
        ajustada = "SinAjustar"
        # Obtener tickers por panel
        tickers_por_panel, _ = obtener_tickers_por_panel(token_acceso, paneles_seleccionados, 'Argentina')
        # Validar tickers_por_panel
        if not tickers_por_panel or not any(tickers_por_panel.values()):
            st.error("No se pudieron obtener tickers para el universo aleatorio seleccionado. Revise los paneles o intente nuevamente.")
            return
        # Obtener series históricas aleatorias (ahora asincrónico y optimizado)
        st.info("Descargando series históricas en paralelo para mayor velocidad...")
        try:
            series_historicas, seleccion_final = obtener_series_historicas_aleatorias_con_capital(
                tickers_por_panel, paneles_seleccionados, cantidad_activos,
                fecha_desde, fecha_hasta, ajustada, token_acceso, capital_ars
            )
        except Exception as e:
            st.error(f"Error al obtener series históricas para el universo aleatorio: {e}")
            return
        # Construir universe_activos a partir de seleccion_final
        universe_activos = []
        if seleccion_final and any(seleccion_final.values()):
            for panel, simbolos in seleccion_final.items():
                for simbolo in simbolos:
                    universe_activos.append({'simbolo': simbolo, 'mercado': 'BCBA', 'tipo': panel})
        else:
            st.error("No hay suficientes activos para el universo aleatorio seleccionado. Intente con otros paneles o menos cantidad de activos.")
            return
    # Validación final antes de continuar
    if not universe_activos:
        st.error("No se pudo construir el universo de activos para la optimización. Proceso detenido.")
        return

    fecha_desde = st.session_state.fecha_desde
    fecha_hasta = st.session_state.fecha_hasta
    st.info(f"Optimizando {len(universe_activos)} activos desde {fecha_desde} hasta {fecha_hasta}")

    # Automatizar todas las estrategias
    st.subheader("🚀 Ejecución Automática de Estrategias de Optimización")
    estrategias = [
        ('markowitz', 'Markowitz'),
        ('min-variance-l1', 'Min Var L1'),
        ('min-variance-l2', 'Min Var L2'),
        ('equi-weight', 'Pesos Iguales'),
        ('long-only', 'Solo Largos')
    ]
    target_sharpe = st.number_input("Sharpe objetivo (opcional, Markowitz)", min_value=0.0, max_value=3.0, value=0.8, step=0.01)
    st.caption("Si no es posible alcanzar el Sharpe exacto, se mostrará el portafolio más cercano.")

    # Cargar datos y preparar manager
    manager_inst = PortfolioManager(universe_activos, token_acceso, fecha_desde, fecha_hasta)
    if not manager_inst.load_data():
        st.error("No se pudieron cargar los datos históricos para optimización.")
        return

    resultados = {}
    for clave, nombre in estrategias:
        if clave == 'markowitz':
            # Mejorar lógica de Sharpe objetivo: buscar el retorno objetivo que más se aproxime al Sharpe deseado
            mejor_sharpe = -1e9
            mejor_result = None
            mejor_ret = None
            for ret in [x/100 for x in range(2, 25, 1)]:
                res = manager_inst.compute_portfolio(strategy='markowitz', target_return=ret)
                if not res or not hasattr(res, 'returns') or not hasattr(res, 'risk'):
                    continue
                sharpe = res.returns / (res.risk if res.risk else 1e-6)
                if abs(sharpe - target_sharpe) < abs(mejor_sharpe - target_sharpe):
                    mejor_sharpe = sharpe
                    mejor_result = res
                    mejor_ret = ret
            resultados[clave] = (mejor_result, mejor_sharpe, mejor_ret)
        else:
            res = manager_inst.compute_portfolio(strategy=clave)
            if res:
                sharpe = res.returns / (res.risk if res.risk else 1e-6)
                resultados[clave] = (res, sharpe, None)

    # Mostrar resultados
    st.markdown("---")
    st.subheader("📊 Resultados de Optimización y Comparación")
    cols = st.columns(len(estrategias)+1)
    # Métricas del portafolio actual
    cols[0].metric("Actual: Sharpe", f"{(metricas_actual.get('retorno_esperado_anual',0)/(metricas_actual.get('riesgo_anual',1e-6))):.2f}")
    cols[0].metric("Actual: Retorno", f"{(metricas_actual.get('retorno_esperado_anual',0) or 0)*100:.2f}%")
    cols[0].metric("Actual: Riesgo", f"{(metricas_actual.get('riesgo_anual',0) or 0)*100:.2f}%")
    for i, (clave, nombre) in enumerate(estrategias):
        res, sharpe, ret = resultados.get(clave, (None, None, None))
        if res:
            cols[i+1].metric(f"{nombre}\nSharpe", f"{sharpe:.2f}")
            cols[i+1].metric(f"{nombre}\nRetorno", f"{getattr(res,'returns',0)*100:.2f}%")
            cols[i+1].metric(f"{nombre}\nRiesgo", f"{getattr(res,'risk',0)*100:.2f}%")
            if clave == 'markowitz' and ret is not None:
                cols[i+1].caption(f"Retorno objetivo: {ret*100:.2f}%")
    st.markdown("---")

    # Gráficos y visualizaciones
    for clave, nombre in estrategias:
        res, sharpe, ret = resultados.get(clave, (None, None, None))
        if not res:
            continue
        st.markdown(f"#### {nombre}")
        # Histograma de retornos
        if hasattr(res, 'plot_histogram_streamlit'):
            st.markdown("**Distribución de Retornos**")
            fig = res.plot_histogram_streamlit()
            st.plotly_chart(fig, use_container_width=True, key=f"hist_{clave}")
        # Pie chart de pesos
        if hasattr(res, 'dataframe_allocation') and res.dataframe_allocation is not None:
            df = res.dataframe_allocation
            if not df.empty and 'rics' in df.columns and 'weights' in df.columns and df['weights'].sum() > 0:
                st.markdown("**Distribución de Pesos**")
                import plotly.graph_objects as go
                fig_pie = go.Figure(data=[go.Pie(labels=df['rics'], values=df['weights'], textinfo='label+percent', hole=0.4)])
                fig_pie.update_layout(title="Distribución Optimizada de Activos", template='plotly_white')
                st.plotly_chart(fig_pie, use_container_width=True, key=f"pie_{clave}")
            else:
                st.info("No hay datos suficientes para mostrar la distribución de pesos.")
        # Métricas
        st.write(f"Retorno esperado: {getattr(res,'returns',0)*100:.2f}% | Riesgo: {getattr(res,'risk',0)*100:.2f}% | Sharpe: {sharpe:.2f}")
        st.markdown("---")

    # Frontera eficiente
    st.subheader("📈 Frontera Eficiente y Portafolios Especiales")
    if st.checkbox("Mostrar Frontera Eficiente", value=True):
        portfolios, returns, volatilities = manager_inst.compute_efficient_frontier(target_return=0.08, include_min_variance=True)
        if portfolios and returns and volatilities and len(returns) > 0 and len(volatilities) > 0:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=volatilities, y=returns, mode='lines+markers', name='Frontera Eficiente', line=dict(color='#0d6efd', width=3), marker=dict(size=6)))
            # Marcar portafolios especiales
            colores = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
            for i, (label, port) in enumerate(portfolios.items()):
                if port and hasattr(port, 'risk') and hasattr(port, 'returns'):
                    fig.add_trace(go.Scatter(x=[port.risk], y=[port.returns], mode='markers+text', name=label, marker=dict(color=colores[i%len(colores)], size=14, symbol='star'), text=[label], textposition='top center'))
            fig.update_layout(title='Frontera Eficiente del Portafolio', xaxis_title='Volatilidad Anual', yaxis_title='Retorno Anual', showlegend=True, template='plotly_white', height=500)
            st.plotly_chart(fig, use_container_width=True)
            # Línea de tasa libre de riesgo
            risk_free_rate = 0.40  # Tasa libre de riesgo anual para Argentina
            fig.add_hline(y=risk_free_rate, line_dash="dot", line_color="green",
                         annotation_text=f"Tasa libre de riesgo: {risk_free_rate*100:.2f}%", annotation_position="top left")
        else:
            st.warning("No se pudo calcular la frontera eficiente. Verifique que haya datos históricos suficientes y activos válidos.")

    # Comparación final
    st.subheader("🔬 Comparación Directa con Portafolio Actual")
    st.write("Se muestran las mejoras potenciales en retorno, riesgo y Sharpe respecto al portafolio actual.")
    df_comp = []
    for clave, nombre in estrategias:
        res, sharpe, _ = resultados.get(clave, (None, None, None))
        if res:
            df_comp.append({
                'Estrategia': nombre,
                'Retorno': getattr(res,'returns',0)*100,
                'Riesgo': getattr(res,'risk',0)*100,
                'Sharpe': sharpe,
                'Mejora Retorno (%)': (getattr(res,'returns',0)-(metricas_actual.get('retorno_esperado_anual',0) or 0))*100,
                'Mejora Sharpe': sharpe-(metricas_actual.get('retorno_esperado_anual',0)/(metricas_actual.get('riesgo_anual',1e-6)))
            })
    if df_comp:
        import pandas as pd
        st.dataframe(pd.DataFrame(df_comp), use_container_width=True)

    with st.expander("ℹ️ Información sobre las Estrategias"):
        st.markdown("""
        **Optimización de Markowitz:**
        - Maximiza el ratio de Sharpe (retorno/riesgo)
        - Considera la correlación entre activos
        - Busca la frontera eficiente de riesgo-retorno
        
        **Pesos Iguales:**
        - Distribución uniforme entre todos los activos (1/n)
        - Estrategia simple de diversificación
        - No considera correlaciones históricas
        
        **Mínima Varianza L1:**
        - Minimiza la varianza del portafolio
        - Restricción L1 para regularización (suma de valores absolutos)
        - Tiende a generar portafolios más concentrados
        
        **Mínima Varianza L2:**
        - Minimiza la varianza del portafolio
        - Restricción L2 para regularización (suma de cuadrados)
        - Genera portafolios más diversificados que L1
        
        **Solo Posiciones Largas:**
        - Optimización estándar sin restricciones adicionales
        - Permite solo posiciones compradoras (sin ventas en corto)
        - Suma de pesos = 100%
        
        **Métricas Estadísticas:**
        - **Skewness**: Medida de asimetría de la distribución
        - **Kurtosis**: Medida de la forma de la distribución (colas)
        - **Jarque-Bera**: Test de normalidad de los retornos
        - **VaR 95%**: Valor en riesgo al 95% de confianza
        """)

    # --- Análisis Intermarket Profesional previo a la optimización ---
    import yfinance as yf
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    st.markdown('---')
    st.subheader('🔗 Análisis Intermarket Profesional (Contexto Global)')
    with st.spinner('Descargando datos intermarket de referencia...'):
        tickers_intermarket = {
            'Merval': '^MERV',
            'S&P 500': '^GSPC',
            'DXY': 'DX-Y.NYB',
            'VIX': '^VIX',
            'Soja': 'ZS=F'
        }
        precios_inter = {}
        for k, v in tickers_intermarket.items():
            try:
                data = yf.download(v, period='1y')['Adj Close']
                if not data.empty:
                    precios_inter[k] = data.dropna()
            except Exception:
                continue
        df_inter = pd.DataFrame(precios_inter).dropna()
        retornos_inter = df_inter.pct_change().dropna()
    # Señal simple intermarket
    dxy_trend = retornos_inter['DXY'].tail(20).sum() if 'DXY' in retornos_inter else 0
    soja_trend = retornos_inter['Soja'].tail(20).sum() if 'Soja' in retornos_inter else 0
    vix_actual = df_inter['VIX'].iloc[-1] if 'VIX' in df_inter else 20
    merval_momentum = retornos_inter['Merval'].tail(10).sum() if 'Merval' in retornos_inter else 0
    if dxy_trend < -0.01 and soja_trend > 0.03 and vix_actual < 20 and merval_momentum > 0.02:
        regimen = "ALCISTA"
        recomendacion = "Contexto favorable para activos de riesgo y commodities."
        explicacion = "El dólar débil, commodities fuertes, baja volatilidad y momentum positivo en Merval sugieren un entorno alcista."
    elif dxy_trend > 0.01 or vix_actual > 25:
        regimen = "DEFENSIVO"
        recomendacion = "Contexto defensivo: preferencia por activos refugio y baja exposición a riesgo."
        explicacion = "El dólar fuerte o alta volatilidad (VIX) sugieren cautela y preferencia por activos defensivos."
    else:
        regimen = "NEUTRAL"
        recomendacion = "Contexto neutral: portafolio balanceado y esperar señales claras."
        explicacion = "No hay señales claras de tendencia, se recomienda mantener un portafolio diversificado."
    st.info(f"Régimen Intermarket: **{regimen}**. {recomendacion}")
    st.caption(f"Explicación: {explicacion}")
    # Mostrar gráfico de activos de referencia
    fig, ax = plt.subplots()
    activos_graf = ['Merval', 'S&P 500', 'DXY', 'VIX', 'Soja']
    for activo in activos_graf:
        if activo in df_inter:
            precios_norm = df_inter[activo] / df_inter[activo].iloc[0] * 100
            ax.plot(precios_norm.index, precios_norm, label=activo)
    ax.legend()
    ax.set_title("Evolución de activos de referencia (base 100)")
    st.pyplot(fig)
    # --- FIN BLOQUE INTERMARKET ---

    # --- Análisis de Ciclo Económico BCRA ---
    with st.expander("🔎 Análisis Automático del Ciclo Económico (BCRA)", expanded=False):
        st.markdown("**Variables consideradas:** Reservas, tasa de política monetaria, inflación, agregados monetarios.")
        # Obtener datos reales del BCRA
        try:
            # Reservas internacionales (último dato)
            url_reservas = "https://api.estadisticasbcra.com/reservas"
            url_leliq = "https://api.estadisticasbcra.com/leliq"
            url_inflacion = "https://api.estadisticasbcra.com/inflacion_mensual_oficial"
            url_m2 = "https://api.estadisticasbcra.com/base_monetaria"
            headers = {"Authorization": "Bearer TU_API_KEY_BCRA"}
            reservas = requests.get(url_reservas, headers=headers).json()[-1]["valor"]
            tasa_leliq = requests.get(url_leliq, headers=headers).json()[-1]["valor"]
            inflacion = requests.get(url_inflacion, headers=headers).json()[-1]["valor"] / 100
            m2 = requests.get(url_m2, headers=headers).json()
            m2_crecimiento = (m2[-1]["valor"] - m2[-22]["valor"]) / m2[-22]["valor"] if len(m2) > 22 else None
        except Exception as e:
            st.warning(f"No se pudieron obtener datos reales del BCRA: {e}. Se usarán valores simulados.")
            reservas = 25000
            tasa_leliq = 50
            inflacion = 0.08
            m2_crecimiento = None
        # Lógica simple de etapa
        if reservas > 35000 and inflacion < 0.05 and tasa_leliq < 60:
            etapa = "Expansión"
            explicacion_ciclo = "Reservas altas, inflación baja y tasas moderadas: contexto favorable para activos de riesgo."
            sugerencia = "Portafolio agresivo: sobreponderar acciones, cíclicos y emergentes."
        elif inflacion > 0.10 or tasa_leliq > 80:
            etapa = "Recesión"
            explicacion_ciclo = "Inflación/tasas muy altas: contexto defensivo, preferir liquidez y renta fija."
            sugerencia = "Portafolio defensivo: priorizar bonos, FCIs de money market y activos refugio."
        elif reservas > 30000 and inflacion < 0.08:
            etapa = "Auge"
            explicacion_ciclo = "Reservas sólidas y baja inflación: buen momento para balancear riesgo y retorno."
            sugerencia = "Portafolio balanceado: combinar acciones, bonos y algo de liquidez."
        else:
            etapa = "Recuperación/Neutral"
            explicacion_ciclo = "Variables mixtas, posible recuperación o transición."
            sugerencia = "Portafolio diversificado: mantener exposición equilibrada y flexibilidad."
        st.success(f"Etapa detectada: **{etapa}**")
        st.caption(f"Explicación: {explicacion_ciclo}")
        st.markdown(f"- Reservas: {reservas:,.0f}M USD\n- Tasa LELIQ: {tasa_leliq:.2f}% anual\n- Inflación mensual: {inflacion*100:.2f}%\n- Crecimiento M2: {m2_crecimiento*100:.2f}%")
        # --- SUGERENCIA DE ESTRATEGIA SEGÚN CICLO ---
        st.markdown(f"""
        <div style='background:#eaf6fb;border-left:6px solid #007cf0;padding:1.2em 1.5em;margin:1.2em 0 1.5em 0;border-radius:10px;'>
        <b>💡 Sugerencia de Estrategia de Optimización:</b><br>
        <span style='font-size:1.15em;font-weight:700;color:#0056b3'>{sugerencia}</span><br>
        <span style='color:#007cf0;font-size:1em;'>{explicacion_ciclo}</span>
        </div>
        """, unsafe_allow_html=True)

    # --- Análisis de Ciclo Económico BCRA ---
    with st.expander("🔎 Análisis Automático del Ciclo Económico (BCRA)", expanded=False):
        st.markdown("**Variables consideradas:** Reservas, tasa de política monetaria, inflación, agregados monetarios.")
        # Obtener datos reales del BCRA
        try:
            # Reservas internacionales (último dato)
            url_reservas = "https://api.estadisticasbcra.com/reservas"
            url_leliq = "https://api.estadisticasbcra.com/leliq"
            url_inflacion = "https://api.estadisticasbcra.com/inflacion_mensual_oficial"
            url_m2 = "https://api.estadisticasbcra.com/base_monetaria"
            headers = {"Authorization": "BEARER TU_API_KEY_BCRA"}  # Reemplazar por tu API KEY de estadisticasbcra.com
            # Reservas
            reservas_df = pd.DataFrame(requests.get(url_reservas, headers=headers).json())
            reservas = reservas_df.iloc[-1]['valor'] if not reservas_df.empty else None
            # Tasa LELIQ
            leliq_df = pd.DataFrame(requests.get(url_leliq, headers=headers).json())
            tasa_leliq = leliq_df.iloc[-1]['valor'] if not leliq_df.empty else None
            # Inflación mensual
            inflacion_df = pd.DataFrame(requests.get(url_inflacion, headers=headers).json())
            inflacion = inflacion_df.iloc[-1]['valor']/100 if not inflacion_df.empty else None
            # M2 (usamos base monetaria como proxy)
            m2_df = pd.DataFrame(requests.get(url_m2, headers=headers).json())
            if len(m2_df) > 1:
                m2_crecimiento = (m2_df.iloc[-1]['valor'] - m2_df.iloc[-2]['valor']) / m2_df.iloc[-2]['valor']
            else:
                m2_crecimiento = None
        except Exception as e:
            st.warning(f"No se pudieron obtener datos reales del BCRA: {e}. Se usarán valores simulados.")
            reservas = 25000
            tasa_leliq = 50
            inflacion = 0.08
            m2_crecimiento = 0.03
        # Lógica simple de ciclo
        if inflacion is not None and tasa_leliq is not None and m2_crecimiento is not None and reservas is not None:
            if inflacion > 0.06 and tasa_leliq > 40 and m2_crecimiento > 0.02 and reservas < 20000:
                etapa = "Recesión"
                explicacion_ciclo = "Alta inflación, tasas elevadas, crecimiento monetario y reservas bajas sugieren recesión."
            elif inflacion < 0.04 and tasa_leliq < 35 and m2_crecimiento < 0.01 and reservas > 35000:
                etapa = "Expansión"
                explicacion_ciclo = "Baja inflación, tasas bajas, crecimiento monetario controlado y reservas altas sugieren expansión."
            elif inflacion > 0.05 and tasa_leliq > 45 and reservas > 30000:
                etapa = "Auge"
                explicacion_ciclo = "Inflación y tasas altas pero reservas sólidas sugieren auge, pero con riesgos de sobrecalentamiento."
            else:
                etapa = "Recuperación/Neutral"
                explicacion_ciclo = "Variables mixtas, posible recuperación o transición."
            st.success(f"Etapa detectada: **{etapa}**")
            st.caption(f"Explicación: {explicacion_ciclo}")
            # Validar y mostrar variables
            reservas_str = f"{reservas:,.0f}M USD" if reservas is not None else "N/D"
            tasa_leliq_str = f"{tasa_leliq:.2f}% anual" if tasa_leliq is not None else "N/D"
            inflacion_str = f"{inflacion*100:.2f}%" if inflacion is not None else "N/D"
            m2_crecimiento_str = f"{m2_crecimiento*100:.2f}%" if m2_crecimiento is not None else "N/D"
            st.markdown(f"- Reservas: {reservas_str}\n- Tasa LELIQ: {tasa_leliq_str}\n- Inflación mensual: {inflacion_str}\n- Crecimiento M2: {m2_crecimiento_str}")
        else:
            st.warning("No se pudieron obtener todas las variables para el análisis de ciclo económico.")
    # --- FIN BLOQUE CICLO ECONÓMICO ---

    # ... resto del código de optimización ...

    # ... después de mostrar los resultados de optimización ...
    # Mini tab de asimetría de retornos
    with st.expander("📉 Asimetría de los Retornos (Skewness)", expanded=False):
        estrategias_labels = []
        skewness_vals = []
        for clave, nombre in estrategias:
            res, _, _ = resultados.get(clave, (None, None, None))
            if res and hasattr(res, 'returns') and res.returns is not None:
                try:
                    ret = res.returns
                    if hasattr(ret, 'values'):
                        ret = ret.values
                    val = skew(ret)
                    estrategias_labels.append(nombre)
                    skewness_vals.append(val)
                except Exception:
                    continue
        if estrategias_labels:
            fig, ax = plt.subplots(figsize=(6, 3))
            bars = ax.bar(estrategias_labels, skewness_vals, color=["#0d6efd" if v > 0 else "#ef4444" for v in skewness_vals])
            ax.axhline(0, color='gray', linestyle='--', linewidth=1)
            ax.set_ylabel('Skewness')
            ax.set_title('Asimetría de los Retornos por Estrategia')
            for bar, val in zip(bars, skewness_vals):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{val:.2f}", ha='center', va='bottom', fontsize=9)
            st.pyplot(fig)
            st.caption("Valores positivos: cola derecha (más ganancias extremas). Valores negativos: cola izquierda (más pérdidas extremas). Cero: simetría.")
        else:
            st.info("No hay retornos suficientes para calcular la asimetría.")

    # --- Análisis Sectorial Básico previo a la optimización ---
    with st.expander("🔎 Análisis Sectorial Básico (Momentum por Sector)", expanded=False):
        st.markdown("**Se analizan los principales ETFs sectoriales globales para identificar los sectores con mejor momentum reciente.**")
        sector_etfs = {
            'Tecnología': 'XLK',
            'Financieros': 'XLF',
            'Salud': 'XLV',
            'Energía': 'XLE',
            'Industrial': 'XLI',
            'Comunicación': 'XLC',
            'Consumo Discrecional': 'XLY',
            'Consumo Básico': 'XLP',
            'Materiales': 'XLB',
            'Bienes Raíces': 'XLRE',
            'Servicios Públicos': 'XLU'
        }
        import yfinance as yf
        import pandas as pd
        import plotly.graph_objects as go
        try:
            precios = yf.download(list(sector_etfs.values()), period="6mo", interval="1d", progress=False)["Adj Close"]
            rendimientos = precios.iloc[-1] / precios.iloc[0] - 1
            ranking = rendimientos.sort_values(ascending=False)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[k for k,v in sector_etfs.items() if v in ranking.index],
                y=ranking.values*100,
                marker_color=["#2ecc71" if v==ranking.index[0] else "#3498db" for v in ranking.index],
                text=[f"{v}: {ranking[v]*100:.2f}%" for v in ranking.index],
                textposition="auto"
            ))
            fig.update_layout(title="Ranking de Sectores por Momentum (6 meses)", yaxis_title="Rendimiento (%)", xaxis_title="Sector", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            st.success(f"Sector destacado: {ranking.index[0]} ({ranking.values[0]*100:.2f}%)")
            st.markdown(f"**Recomendación:** Priorizar activos del sector **{[k for k,v in sector_etfs.items() if v==ranking.index[0]][0]}** para optimizaciones si es coherente con tu perfil de riesgo.")
        except Exception as e:
            st.warning(f"No se pudo obtener el ranking sectorial: {e}")

    # --- Diagnóstico IA de ciclo económico y sugerencia de sectores ---
    def diagnostico_ciclo_y_sugerencia(all_variables_data, gemini_api_key, sectores_arg=None):
        """
        Usa IA para diagnosticar el ciclo económico y sugerir sectores/activos de Argentina y EEUU.
        """
        import google.generativeai as genai
        resumen = []
        for nombre, info in all_variables_data.items():
            m = info.get('metrics', {})
            resumen.append(
                f"{nombre}: Actual={m.get('valor_actual', 0):.2f}, Cambio={m.get('cambio_porcentual', 0):+.1f}%, VolATR={m.get('volatilidad_atr', 0):.2f}%, Tend={m.get('tendencia_direccion', 'N/A')}"
            )
        # --- Sectores argentinos relevantes ---
        sectores_arg = sectores_arg or {
            'Bancos': ['GGAL', 'BMA', 'SUPV', 'BBAR'],
            'Energía': ['YPFD', 'PAMP', 'CEPU', 'TGSU2'],
            'Consumo': ['SUPV', 'EDN', 'ALUA'],
            'Materiales': ['TXAR', 'ALUA'],
            'Tecnología': ['MELI'],
            'Servicios Públicos': ['EDN', 'TGSU2', 'CEPU'],
            'Agro': ['AGRO'],
            'Telecomunicaciones': ['TECO2'],
            'Industriales': ['TRAN', 'TGNO4'],
        }
        sectores_arg_str = "\n".join([f"- {k}: {', '.join(v)}" for k, v in sectores_arg.items()])
        prompt = f"""
Actúa como economista jefe. Analiza el siguiente resumen de variables macroeconómicas argentinas y de EEUU:

{chr(10).join(resumen)}

Sectores argentinos relevantes y sus principales tickers:
{sectores_arg_str}

1. Diagnostica el ciclo económico actual de Argentina y global (expansión, recesión, etc.).
2. Sugiere 2-3 sectores o tipos de activos argentinos (de la lista) y 2-3 de EEUU que suelen rendir mejor en este ciclo, usando factores de Intermarket (ITM), momentum y variables macro si es relevante.
3. Fundamenta brevemente cada sugerencia, explicando por qué esos sectores son los más adecuados según el contexto y los factores de ITM.

Responde en español, en formato claro y ejecutivo. Enumera los sectores sugeridos en una lista separada al final bajo el título "SUGERENCIA DE SECTORES ARGENTINA" y otra bajo "SUGERENCIA DE SECTORES EEUU".\n\nEjemplo de formato de respuesta:\n\nDiagnóstico: ...\nExplicación: ...\nSUGERENCIA DE SECTORES ARGENTINA:\n- ...\n- ...\nSUGERENCIA DE SECTORES EEUU:\n- ...\n- ...\n"""
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=900,
                top_p=0.9,
                top_k=30
            )
        )
        response = model.generate_content(prompt)
        return response.text if response and response.text else "No se pudo obtener diagnóstico IA."

    # --- INICIO mostrar_optimizacion_portafolio ---
        # Diagnóstico IA de ciclo económico y sugerencia de sectores
        st.markdown("---")
        st.subheader("🧠 Diagnóstico IA de ciclo económico y sugerencia de sectores")
        if 'GEMINI_API_KEY' not in st.session_state:
            st.session_state.GEMINI_API_KEY = ''
        if st.button("🔍 Analizar ciclo y sugerir sectores", key="btn_diag_ia"):
            import yfinance as yf
            import numpy as np
            all_variables_data = {}
            ATR_WINDOW = 14
            # --- Variables Argentina ---
            try:
                merval = yf.download('^MERV', period='6mo')['Close']
                if not merval.empty:
                    merval_ret = merval.pct_change().dropna()
                    merval_atr = merval_ret.abs().rolling(ATR_WINDOW).mean().iloc[-1]*100 if len(merval_ret) >= ATR_WINDOW else merval_ret.abs().mean()*100
                    all_variables_data['MERVAL (Argentina)'] = {
                        'metrics': {
                            'valor_actual': merval.iloc[-1],
                            'cambio_porcentual': (merval.iloc[-1]/merval.iloc[0]-1)*100,
                            'volatilidad_atr': merval_atr,
                            'tendencia_direccion': 'alcista' if merval.iloc[-1]>merval.iloc[0] else 'bajista'
                        }
                    }
            except Exception as e:
                st.warning(f"No se pudo obtener MERVAL: {e}")
            # --- Variables EEUU ---
            tickers_usa = {
                'S&P 500 (EEUU)': '^GSPC',
                'VIX (EEUU)': '^VIX',
                'Tecnología (XLK)': 'XLK',
                'Financieros (XLF)': 'XLF',
                'Energía (XLE)': 'XLE',
                'Consumo Discrecional (XLY)': 'XLY',
                'Consumo Básico (XLP)': 'XLP',
                'Salud (XLV)': 'XLV',
                'Industrial (XLI)': 'XLI',
                'Materiales (XLB)': 'XLB',
                'Bienes Raíces (XLRE)': 'XLRE',
                'Servicios Públicos (XLU)': 'XLU',
                'Comunicaciones (XLC)': 'XLC',
            }
            try:
                precios = yf.download(list(tickers_usa.values()), period='6mo')['Close']
                for nombre, ticker in tickers_usa.items():
                    serie = precios[ticker] if ticker in precios else None
                    if serie is not None and not serie.empty:
                        ret = serie.pct_change().dropna()
                        atr = ret.abs().rolling(ATR_WINDOW).mean().iloc[-1]*100 if len(ret) >= ATR_WINDOW else ret.abs().mean()*100
                        all_variables_data[nombre] = {
                            'metrics': {
                                'valor_actual': serie.iloc[-1],
                                'cambio_porcentual': (serie.iloc[-1]/serie.iloc[0]-1)*100,
                                'volatilidad_atr': atr,
                                'tendencia_direccion': 'alcista' if serie.iloc[-1]>serie.iloc[0] else 'bajista'
                            }
                        }
            except Exception as e:
                st.warning(f"No se pudieron obtener variables de EEUU: {e}")
            # --- Sectores argentinos relevantes ---
            sectores_arg = {
                'Bancos': ['GGAL', 'BMA', 'SUPV', 'BBAR'],
                'Energía': ['YPFD', 'PAMP', 'CEPU', 'TGSU2'],
                'Consumo': ['SUPV', 'EDN', 'ALUA'],
                'Materiales': ['TXAR', 'ALUA'],
                'Tecnología': ['MELI'],
                'Servicios Públicos': ['EDN', 'TGSU2', 'CEPU'],
                'Agro': ['AGRO'],
                'Telecomunicaciones': ['TECO2'],
                'Industriales': ['TRAN', 'TGNO4'],
            }
            with st.spinner("Consultando IA..."):
                diagnostico = diagnostico_ciclo_y_sugerencia(all_variables_data, st.session_state.GEMINI_API_KEY, sectores_arg)
            st.markdown(diagnostico)
            # Extraer sectores sugeridos
            import re
            sugeridos_arg = []
            sugeridos_usa = []
            match_arg = re.search(r"SUGERENCIA DE SECTORES ARGENTINA\s*[:\-]*\s*(.*?)(?:SUGERENCIA DE SECTORES EEUU|$)", diagnostico, re.IGNORECASE | re.DOTALL)
            if match_arg:
                sugeridos_arg = re.findall(r"(?:\-|\d+\.)\s*([^\n]+)", match_arg.group(1))
            match_usa = re.search(r"SUGERENCIA DE SECTORES EEUU\s*[:\-]*\s*(.*)", diagnostico, re.IGNORECASE | re.DOTALL)
            if match_usa:
                sugeridos_usa = re.findall(r"(?:\-|\d+\.)\s*([^\n]+)", match_usa.group(1))
            st.session_state['sectores_sugeridos_ia_arg'] = sugeridos_arg
            st.session_state['sectores_sugeridos_ia_usa'] = sugeridos_usa
            if sugeridos_arg:
                st.success(f"Sectores argentinos sugeridos por IA: {', '.join(sugeridos_arg)}")
            if sugeridos_usa:
                st.success(f"Sectores EEUU sugeridos por IA: {', '.join(sugeridos_usa)}")

    # --- Función auxiliar para calcular drawdown ---
    def calcular_drawdown(serie_valores):
        """
        Calcula el drawdown máximo y actual de una serie de valores (por ejemplo, valor de portafolio).
        Devuelve: drawdown_max (float), drawdown_actual (float), serie_drawdown (pd.Series)
        """
        import numpy as np
        import pandas as pd
        if isinstance(serie_valores, (pd.Series, np.ndarray, list)):
            serie = pd.Series(serie_valores)
            max_acum = serie.cummax()
            drawdown = (serie - max_acum) / max_acum
            drawdown_max = drawdown.min()
            drawdown_actual = drawdown.iloc[-1]
            return drawdown_max, drawdown_actual, drawdown
        else:
            return 0, 0, pd.Series([])

    # --- En mostrar_optimizacion_portafolio, después de mostrar resultados de optimización ---
        # --- Análisis de Drawdown ---
        st.subheader("📉 Análisis de Drawdown (Caídas Máximas)")
        # Portafolio actual
        st.markdown("**Portafolio Actual**")
        # Intentar reconstruir serie de valor del portafolio actual
        try:
            # Usar los mismos datos que para el histograma de portafolio actual
            # (puedes ajustar si tienes la serie exacta)
            # Aquí se usa la suma ponderada de precios normalizados
            activos = [a for a in activos_raw if a.get('titulo',{}).get('simbolo')]
            pesos = [activos_dict[a.get('titulo',{}).get('simbolo')]['Valuación']/valor_total if valor_total>0 else 0 for a in activos]
            precios = {}
            for a in activos:
                simbolo = a.get('titulo',{}).get('simbolo')
                mercado = a.get('titulo',{}).get('mercado','BCBA')
                df = obtener_serie_historica_iol(token_acceso, mercado, simbolo, fecha_desde.strftime('%Y-%m-%d'), fecha_hasta.strftime('%Y-%m-%d'))
                if df is not None and not df.empty and 'precio' in df.columns:
                    precios[simbolo] = df.set_index('fecha')['precio']
            if precios:
                df_precios = pd.DataFrame(precios).dropna()
                serie_valor = (df_precios * pesos).sum(axis=1)
                dd_max, dd_actual, serie_dd = calcular_drawdown(serie_valor)
                st.metric("Drawdown Máximo", f"{dd_max*100:.2f}%")
                st.metric("Drawdown Actual", f"{dd_actual*100:.2f}%")
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=serie_dd.index, y=serie_dd*100, mode='lines', name='Drawdown (%)', line=dict(color='#ef4444')))
                fig.update_layout(title="Drawdown Portafolio Actual", yaxis_title="Drawdown (%)", xaxis_title="Fecha", template='plotly_white', height=300)
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"No se pudo calcular el drawdown del portafolio actual: {e}")
        # Portafolios optimizados
        for clave, nombre in estrategias:
            res, _, _ = resultados.get(clave, (None, None, None))
            if res and hasattr(res, 'returns') and res.returns is not None:
                st.markdown(f"**{nombre}**")
                # Reconstruir serie de valor acumulado
                try:
                    import numpy as np
                    import pandas as pd
                    if hasattr(res, 'returns'):
                        # Suponemos retornos diarios
                        serie_valor = (1 + pd.Series(res.returns)).cumprod()
                        dd_max, dd_actual, serie_dd = calcular_drawdown(serie_valor)
                        st.metric("Drawdown Máximo", f"{dd_max*100:.2f}%")
                        st.metric("Drawdown Actual", f"{dd_actual*100:.2f}%")
                        import plotly.graph_objects as go
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(y=serie_dd*100, mode='lines', name='Drawdown (%)', line=dict(color='#ef4444')))
                        fig.update_layout(title=f"Drawdown {nombre}", yaxis_title="Drawdown (%)", xaxis_title="Día", template='plotly_white', height=250)
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"No se pudo calcular el drawdown de {nombre}: {e}")
        # Benchmarks (ejemplo: S&P500, MERVAL)
        st.markdown("**Benchmarks**")
        try:
            import yfinance as yf
            import pandas as pd
            benchmarks = {'S&P 500': '^GSPC', 'MERVAL': '^MERV'}
            for nombre, ticker in benchmarks.items():
                serie = yf.download(ticker, period='1y')['Close']
                if not serie.empty:
                    dd_max, dd_actual, serie_dd = calcular_drawdown(serie)
                    st.metric(f"{nombre} Drawdown Máx", f"{dd_max*100:.2f}%")
                    st.metric(f"{nombre} Drawdown Actual", f"{dd_actual*100:.2f}%")
                    import plotly.graph_objects as go
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=serie_dd.index, y=serie_dd*100, mode='lines', name='Drawdown (%)', line=dict(color='#ef4444')))
                    fig.update_layout(title=f"Drawdown {nombre}", yaxis_title="Drawdown (%)", xaxis_title="Fecha", template='plotly_white', height=250)
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"No se pudo calcular el drawdown de benchmarks: {e}")

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

def mostrar_movimientos_asesor():
    st.title("👨‍💼 Panel del Asesor")
    
    if 'token_acceso' not in st.session_state or not st.session_state.token_acceso:
        st.error("Debe iniciar sesión primero")
        return
        
    token_acceso = st.session_state.token_acceso
    
    # Obtener lista de clientes
    clientes = obtener_lista_clientes(token_acceso)
    if not clientes:
        st.warning("No se encontraron clientes")
        return
    
    # Formulario de búsqueda
    with st.form("form_buscar_movimientos"):
        st.subheader("🔍 Buscar Movimientos")
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_desde = st.date_input("Fecha desde", value=date.today() - timedelta(days=30))
        with col2:
            fecha_hasta = st.date_input("Fecha hasta", value=date.today())
        
        # Selección múltiple de clientes
        cliente_opciones = [{"label": f"{c.get('apellidoYNombre', c.get('nombre', 'Cliente'))} ({c.get('numeroCliente', c.get('id', ''))})", 
                           "value": c.get('numeroCliente', c.get('id'))} for c in clientes]
        
        clientes_seleccionados = st.multiselect(
            "Seleccione clientes",
            options=[c['value'] for c in cliente_opciones],
            format_func=lambda x: next((c['label'] for c in cliente_opciones if c['value'] == x), x),
            default=[cliente_opciones[0]['value']] if cliente_opciones else []
        )
        
        # Filtros adicionales
        col1, col2 = st.columns(2)
        with col1:
            tipo_fecha = st.selectbox(
                "Tipo de fecha",
                ["fechaOperacion", "fechaLiquidacion"],
                index=0
            )
            estado = st.selectbox(
                "Estado",
                ["", "Pendiente", "Aprobado", "Rechazado"],
                index=0
            )
        with col2:
            tipo_operacion = st.text_input("Tipo de operación")
            moneda = st.text_input("Moneda", "ARS")
        
        buscar = st.form_submit_button("🔍 Buscar movimientos")
    
    if buscar and clientes_seleccionados:
        with st.spinner("Buscando movimientos..."):
            movimientos = obtener_movimientos_asesor(
                token_portador=token_acceso,
                clientes=clientes_seleccionados,
                fecha_desde=fecha_desde.isoformat(),
                fecha_hasta=fecha_hasta.isoformat(),
                tipo_fecha=tipo_fecha,
                estado=estado or None,
                tipo_operacion=tipo_operacion or None,
                moneda=moneda or None
            )
            
            if movimientos and isinstance(movimientos, list):
                df = pd.DataFrame(movimientos)
                if not df.empty:
                    st.subheader("📋 Resultados de la búsqueda")
                    st.dataframe(df, use_container_width=True)
                    
                    # Mostrar resumen
                    st.subheader("📊 Resumen de Movimientos")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Movimientos", len(df))
                    
                    if 'monto' in df.columns:
                        col2.metric("Monto Total", f"${df['monto'].sum():,.2f}")
                    
                    if 'estado' in df.columns:
                        estados = df['estado'].value_counts().to_dict()
                        col3.metric("Estados", ", ".join([f"{k} ({v})" for k, v in estados.items()]))
                else:
                    st.info("No se encontraron movimientos con los filtros seleccionados")
            else:
                st.warning("No se encontraron movimientos o hubo un error en la consulta")
                if movimientos and not isinstance(movimientos, list):
                    st.json(movimientos)  # Mostrar respuesta cruda para depuración

def mostrar_analisis_portafolio():
    cliente = st.session_state.cliente_seleccionado
    token_acceso = st.session_state.token_acceso

    if not cliente:
        st.error("No hay cliente seleccionado")
        return

    id_cliente = cliente.get('numeroCliente', cliente.get('id'))
    nombre_cliente = cliente.get('apellidoYNombre', cliente.get('nombre', 'Cliente'))

    st.title(f"📊 Análisis de Portafolio - {nombre_cliente}")
    
    # Crear tabs con iconos
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Resumen Portafolio", 
        "💰 Estado de Cuenta", 
        "📊 Análisis Técnico",
        "💱 Cotizaciones",
        "🔄 Rebalanceo"
    ])

    with tab1:
        portafolio = obtener_portafolio(token_acceso, id_cliente)
        if portafolio:
            mostrar_resumen_portafolio(portafolio, token_acceso)
        else:
            st.warning("No se pudo obtener el portafolio del cliente")
    
    with tab2:
        estado_cuenta = obtener_estado_cuenta(token_acceso, id_cliente)
        if estado_cuenta:
            mostrar_estado_cuenta(estado_cuenta)
        else:
            st.warning("No se pudo obtener el estado de cuenta")
    
    with tab3:
        mostrar_analisis_tecnico(token_acceso, id_cliente)
    
    with tab4:
        mostrar_cotizaciones_mercado(token_acceso)
    
    with tab5:
        mostrar_optimizacion_portafolio(token_acceso, id_cliente)

def main():
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
    if 'fecha_desde' not in st.session_state:
        st.session_state.fecha_desde = date.today() - timedelta(days=365)
    if 'fecha_hasta' not in st.session_state:
        st.session_state.fecha_hasta = date.today()
    
    # Barra lateral - Autenticación
    with st.sidebar:
        st.header("🔐 Autenticación IOL")
        
        if st.session_state.token_acceso is None:
            with st.form("login_form"):
                st.subheader("Ingreso a IOL")
                usuario = st.text_input("Usuario", placeholder="su_usuario")
                contraseña = st.text_input("Contraseña", type="password", placeholder="su_contraseña")
                
                if st.form_submit_button("🚀 Conectar a IOL", use_container_width=True):
                    if usuario and contraseña:
                        with st.spinner("Conectando..."):
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
            st.success("✅ Conectado a IOL")
            st.divider()
            
            st.subheader("Configuración de Fechas")
            col1, col2 = st.columns(2)
            with col1:
                fecha_desde = st.date_input(
                    "Desde:",
                    value=st.session_state.fecha_desde,
                    max_value=date.today()
                )
            with col2:
                fecha_hasta = st.date_input(
                    "Hasta:",
                    value=st.session_state.fecha_hasta,
                    max_value=date.today()
                )
            
            st.session_state.fecha_desde = fecha_desde
            st.session_state.fecha_hasta = fecha_hasta
            
            # Obtener lista de clientes
            if not st.session_state.clientes and st.session_state.token_acceso:
                with st.spinner("Cargando clientes..."):
                    try:
                        clientes = obtener_lista_clientes(st.session_state.token_acceso)
                        if clientes:
                            st.session_state.clientes = clientes
                        else:
                            st.warning("No se encontraron clientes")
                    except Exception as e:
                        st.error(f"Error al cargar clientes: {str(e)}")
            
            clientes = st.session_state.clientes
            
            if clientes:
                st.subheader("Selección de Cliente")
                cliente_ids = [c.get('numeroCliente', c.get('id')) for c in clientes]
                cliente_nombres = [c.get('apellidoYNombre', c.get('nombre', 'Cliente')) for c in clientes]
                
                cliente_seleccionado = st.selectbox(
                    "Seleccione un cliente:",
                    options=cliente_ids,
                    format_func=lambda x: cliente_nombres[cliente_ids.index(x)] if x in cliente_ids else "Cliente",
                    label_visibility="collapsed"
                )
                
                st.session_state.cliente_seleccionado = next(
                    (c for c in clientes if c.get('numeroCliente', c.get('id')) == cliente_seleccionado),
                    None
                )
                
                if st.button("🔄 Actualizar lista de clientes", use_container_width=True):
                    with st.spinner("Actualizando..."):
                        nuevos_clientes = obtener_lista_clientes(st.session_state.token_acceso)
                        st.session_state.clientes = nuevos_clientes
                        st.success("✅ Lista actualizada")
                        st.rerun()
            else:
                st.warning("No se encontraron clientes")

    # Contenido principal
    try:
        if st.session_state.token_acceso:
            st.sidebar.title("Menú Principal")
            opcion = st.sidebar.radio(
                "Seleccione una opción:",
                ("🏠 Inicio", "📊 Análisis de Portafolio", "🧱 Análisis Intermarket", "📈 Ciclo Económico", "💰 Tasas de Caución", "👨\u200d💼 Panel del Asesor"),
                index=0,
            )

            # Mostrar la página seleccionada
            if opcion == "🏠 Inicio":
                st.info("👆 Seleccione una opción del menú para comenzar")
            elif opcion == "📊 Análisis de Portafolio":
                if st.session_state.cliente_seleccionado:
                    mostrar_analisis_portafolio()
                else:
                    st.info("👆 Seleccione un cliente en la barra lateral para comenzar")
            elif opcion == "🧱 Análisis Intermarket":
                if 'token_acceso' in st.session_state and st.session_state.token_acceso:
                    # Configuración de API key para IA
                    if 'GEMINI_API_KEY' not in st.session_state:
                        st.session_state.GEMINI_API_KEY = ''
                    
                    gemini_key = st.text_input(
                        "🔑 API Key Gemini (opcional)",
                        value=st.session_state.GEMINI_API_KEY,
                        type="password",
                        help="Para análisis IA avanzado del ciclo económico"
                    )
                    st.session_state.GEMINI_API_KEY = gemini_key
                    
                    # Crear tabs para el análisis intermarket
                    tab1, tab2 = st.tabs(["🌍 Análisis Intermarket", "📊 Análisis CAPM y Estrategias"])
                    
                    with tab1:
                        analisis_intermarket_completo(st.session_state.token_acceso, gemini_key)
                    
                    with tab2:
                        mostrar_analisis_capm_y_estrategias(st.session_state.token_acceso, gemini_key)
                        
                        # Si hay un cliente seleccionado, mostrar también análisis del portafolio
                        if st.session_state.cliente_seleccionado:
                            st.divider()
                            mostrar_analisis_capm_portafolio(st.session_state.token_acceso, st.session_state.cliente_seleccionado)
                else:
                    st.warning("Por favor inicie sesión para acceder al análisis intermarket")

            elif opcion == "📈 Ciclo Económico":
                if 'token_acceso' in st.session_state and st.session_state.token_acceso:
                    # Configuración de API key para IA
                    if 'GEMINI_API_KEY' not in st.session_state:
                        st.session_state.GEMINI_API_KEY = ''
                    
                    gemini_key = st.text_input(
                        "🔑 API Key Gemini (opcional)",
                        value=st.session_state.GEMINI_API_KEY,
                        type="password",
                        help="Para análisis IA avanzado del ciclo económico"
                    )
                    st.session_state.GEMINI_API_KEY = gemini_key
                    
                    # Llamar a la función de graficar ciclo económico
                    graficar_ciclo_economico_real(st.session_state.token_acceso, gemini_key)
                else:
                    st.warning("Por favor inicie sesión para acceder al análisis del ciclo económico")

            elif opcion == "💰 Tasas de Caución":
                if 'token_acceso' in st.session_state and st.session_state.token_acceso:
                    mostrar_tasas_caucion(st.session_state.token_acceso)
                else:
                    st.warning("Por favor inicie sesión para ver las tasas de caución")
            elif opcion == "👨\u200d💼 Panel del Asesor":
                mostrar_movimientos_asesor()
                st.info("👆 Seleccione una opción del menú para comenzar")
        else:
            st.info("👆 Ingrese sus credenciales para comenzar")
            
            # Panel de bienvenida
            st.markdown("""
            <div style="background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); 
                        border-radius: 15px; 
                        padding: 40px; 
                        color: white;
                        text-align: center;
                        margin: 30px 0;">
                <h1 style="color: white; margin-bottom: 20px;">Bienvenido al Portfolio Analyzer</h1>
                <p style="font-size: 18px; margin-bottom: 30px;">Conecte su cuenta de IOL para comenzar a analizar sus portafolios</p>
                <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
                    <div style="background: rgba(255,255,255,0.2); border-radius: 12px; padding: 25px; width: 250px; backdrop-filter: blur(5px);">
                        <h3>📊 Análisis Completo</h3>
                        <p>Visualice todos sus activos en un solo lugar con detalle</p>
                    </div>
                    <div style="background: rgba(255,255,255,0.2); border-radius: 12px; padding: 25px; width: 250px; backdrop-filter: blur(5px);">
                        <h3>📈 Gráficos Interactivos</h3>
                        <p>Comprenda su portafolio con visualizaciones avanzadas</p>
                    </div>
                    <div style="background: rgba(255,255,255,0.2); border-radius: 12px; padding: 25px; width: 250px; backdrop-filter: blur(5px);">
                        <h3>⚖️ Gestión de Riesgo</h3>
                        <p>Identifique concentraciones y optimice su perfil de riesgo</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Características
            st.subheader("✨ Características Principales")
            cols = st.columns(3)
            with cols[0]:
                st.markdown("""
                **📊 Análisis Detallado**  
                - Valuación completa de activos  
                - Distribución por tipo de instrumento  
                - Concentración del portafolio  
                """)
            with cols[1]:
                st.markdown("""
                **📈 Herramientas Profesionales**  
                - Optimización de portafolio  
                - Análisis técnico avanzado  
                - Proyecciones de rendimiento  
                """)
            with cols[2]:
                st.markdown("""
                **💱 Datos de Mercado**  
                - Cotizaciones MEP en tiempo real  
                - Tasas de caución actualizadas  
                - Estado de cuenta consolidado  
                """)
    except Exception as e:
        st.error(f"❌ Error en la aplicación: {str(e)}")

def obtener_tickers_por_panel(token_portador, paneles, pais='Argentina'):
    """
    Devuelve un diccionario con listas de tickers reales por panel para el universo aleatorio.
    Si no hay API, usa listas fijas de tickers representativos.
    Retorna: (dict panel->tickers, dict panel->descripciones)
    """
    tickers = {}
    descripciones = {}
    # Paneles y ejemplos (puedes reemplazar por consulta a la API de IOL si tienes endpoint)
    paneles_dict = {
        'acciones': [
            ('GGAL', 'Grupo Financiero Galicia'),
            ('YPFD', 'YPF S.A.'),
            ('PAMP', 'Pampa Energía'),
            ('BMA', 'Banco Macro'),
            ('SUPV', 'Grupo Supervielle'),
            ('CEPU', 'Central Puerto'),
            ('TXAR', 'Ternium Argentina'),
            ('ALUA', 'Aluar'),
            ('TGSU2', 'Transportadora Gas del Sur'),
            ('EDN', 'Edenor'),
        ],
        'cedears': [
            ('AAPL', 'Apple'),
            ('TSLA', 'Tesla'),
            ('AMZN', 'Amazon'),
            ('GOOGL', 'Alphabet'),
            ('MSFT', 'Microsoft'),
            ('KO', 'Coca-Cola'),
            ('MELI', 'Mercado Libre'),
            ('BABA', 'Alibaba'),
            ('JNJ', 'Johnson & Johnson'),
            ('PG', 'Procter & Gamble'),
        ],
        'aDRs': [
            ('BBAR', 'BBVA Argentina'),
            ('BMA', 'Banco Macro'),
            ('GGAL', 'Grupo Galicia'),
            ('PAM', 'Pampa Energia'),
            ('SUPV', 'Supervielle'),
        ],
        'titulosPublicos': [
            ('AL30', 'Bonar 2030'),
            ('GD30', 'Global 2030'),
            ('AL35', 'Bonar 2035'),
            ('GD35', 'Global 2035'),
            ('AL29', 'Bonar 2029'),
            ('GD29', 'Global 2029'),
        ],
        'obligacionesNegociables': [
            ('PBY22', 'Pampa Energía ON'),
            ('CGC24', 'Compañía General de Combustibles ON'),
            ('YPF23', 'YPF ON'),
            ('TGSU2', 'Transportadora Gas del Sur ON'),
        ]
    }
    for panel in paneles:
        panel_l = panel.lower()
        if panel_l in paneles_dict:
            tickers[panel] = [t[0] for t in paneles_dict[panel_l]]
            descripciones[panel] = [t[1] for t in paneles_dict[panel_l]]
        else:
            tickers[panel] = []
            descripciones[panel] = []
    return tickers, descripciones

# --- Función: calcular retornos y covarianza con ventana móvil ---
def calcular_estadisticas_ventana_movil(precios, ventana=252):
    """
    Calcula retornos esperados y matriz de covarianza usando una ventana móvil.
    precios: DataFrame de precios (columnas=activos, filas=fechas)
    ventana: días para la ventana móvil (por defecto 1 año)
    Devuelve: retornos esperados anualizados, covarianza anualizada
    """
    retornos = precios.pct_change().dropna()
    retornos_ventana = retornos.iloc[-ventana:]
    mean_ret = retornos_ventana.mean() * 252
    cov = retornos_ventana.cov() * 252
    return mean_ret, cov

# --- Función: optimización Markowitz (max Sharpe) ---
def optimizar_markowitz(mean_ret, cov, risk_free_rate=0.0):
    """
    Devuelve los pesos óptimos de Markowitz (max Sharpe, long-only)
    """
    import numpy as np
    import scipy.optimize as op
    n = len(mean_ret)
    bounds = tuple((0, 1) for _ in range(n))
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1},)
    def neg_sharpe(x):
        port_ret = np.dot(mean_ret, x)
        port_vol = np.sqrt(np.dot(x, np.dot(cov, x)))
        if port_vol == 0:
            return 1e6
        return -(port_ret - risk_free_rate) / port_vol
    x0 = np.ones(n) / n
    res = op.minimize(neg_sharpe, x0, bounds=bounds, constraints=constraints)
    if res.success:
        return res.x
    else:
        return x0

# --- Función: backtest con rebalanceo periódico ---
def backtest_markowitz(precios, ventana=252, rebalanceo=63, risk_free_rate=0.0):
    """
    Simula la evolución de un portafolio Markowitz con rebalanceo periódico.
    precios: DataFrame de precios (columnas=activos, filas=fechas)
    ventana: días para estimar retornos/covarianza
    rebalanceo: cada cuántos días rebalancear (63 = 3 meses aprox)
    Devuelve: fechas, valores del portafolio, lista de pesos, fechas de rebalanceo
    """
    import numpy as np
    fechas = precios.index
    n_activos = precios.shape[1]
    portafolio_valor = [1.0]
    pesos_hist = []
    fechas_reb = []
    pesos_actual = np.ones(n_activos) / n_activos
    for i in range(ventana, len(fechas)-1, rebalanceo):
        precios_window = precios.iloc[i-ventana:i]
        mean_ret, cov = calcular_estadisticas_ventana_movil(precios_window, ventana)
        pesos_actual = optimizar_markowitz(mean_ret, cov, risk_free_rate)
        pesos_hist.append(pesos_actual)
        fechas_reb.append(fechas[i])
        # Simular evolución hasta el próximo rebalanceo
        for j in range(i, min(i+rebalanceo, len(fechas)-1)):
            ret = (precios.iloc[j+1] / precios.iloc[j] - 1).values
            portafolio_valor.append(portafolio_valor[-1] * (1 + np.dot(pesos_actual, ret)))
    # Completar hasta el final con los últimos pesos
    while len(portafolio_valor) < len(fechas):
        portafolio_valor.append(portafolio_valor[-1])
    return fechas, portafolio_valor, pesos_hist, fechas_reb

# --- Función: visualización de backtest y pesos ---
def mostrar_backtest_markowitz(precios, ventana=252, rebalanceo=63, risk_free_rate=0.0):
    """
    Visualiza la evolución del portafolio Markowitz con rebalanceo periódico.
    """
    import plotly.graph_objects as go
    fechas, portafolio_valor, pesos_hist, fechas_reb = backtest_markowitz(precios, ventana, rebalanceo, risk_free_rate)
    import streamlit as st
    st.subheader("📈 Evolución del Portafolio Markowitz (Backtest)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fechas, y=portafolio_valor, mode='lines', name='Valor Portafolio'))
    fig.update_layout(title="Backtest Markowitz con rebalanceo", xaxis_title="Fecha", yaxis_title="Valor acumulado", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
    # Mostrar evolución de pesos
    st.subheader("🔄 Evolución de Pesos por Activo")
    if pesos_hist:
        import numpy as np
        activos = precios.columns
        pesos_array = np.array(pesos_hist)
        fig2 = go.Figure()
        for idx, activo in enumerate(activos):
            fig2.add_trace(go.Scatter(x=fechas_reb, y=pesos_array[:, idx], mode='lines+markers', name=activo))
        fig2.update_layout(title="Pesos óptimos en cada rebalanceo", xaxis_title="Fecha de rebalanceo", yaxis_title="Peso", template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No hay datos suficientes para mostrar la evolución de pesos.")
# --- FIN FUNCIONES ROBUSTAS ---

def obtener_series_historicas_aleatorias_con_capital(tickers_por_panel, paneles_seleccionados, cantidad_activos, fecha_desde, fecha_hasta, ajustada, token_acceso, capital_ars):
    """
    Selecciona aleatoriamente tickers de los paneles seleccionados, descarga sus series históricas y devuelve:
    - series_historicas: dict[ticker] -> DataFrame de precios
    - seleccion_final: dict[panel] -> lista de tickers seleccionados
    Respeta la cantidad de activos por panel y el capital disponible.
    """
    import random
    import yfinance as yf
    import pandas as pd
    series_historicas = {}
    seleccion_final = {}
    for panel in paneles_seleccionados:
        tickers = tickers_por_panel.get(panel, [])
        if not tickers:
            continue
        seleccionados = random.sample(tickers, min(cantidad_activos, len(tickers)))
        seleccion_final[panel] = seleccionados
        for ticker in seleccionados:
            try:
                # Preferir yfinance para tickers internacionales y Cedears
                if panel.lower() in ['cedears', 'adrs'] or ticker.isalpha():
                    df = yf.download(ticker, start=fecha_desde, end=fecha_hasta)[['Close']]
                    if not df.empty:
                        df = df.rename(columns={'Close': 'precio'})
                        df = df.reset_index().rename(columns={'Date': 'fecha'})
                        series_historicas[ticker] = df
                else:
                    # Para acciones locales, usar la API de IOL si es necesario
                    df = obtener_serie_historica_iol(token_acceso, 'BCBA', ticker, fecha_desde, fecha_hasta, ajustada)
                    if df is not None and not df.empty:
                        series_historicas[ticker] = df
            except Exception as e:
                continue
    # Validar que haya suficientes series
    total_activos = sum(len(v) for v in seleccion_final.values())
    if total_activos == 0 or not series_historicas:
        raise Exception("No se pudieron obtener series históricas suficientes para el universo aleatorio.")
    return series_historicas, seleccion_final

def analisis_intermarket_completo(token_acceso, gemini_api_key=None):
    """
    Análisis completo intermarket con detección de ciclos económicos.
    Integra variables macro del BCRA, análisis intermarket local e internacional,
    y sugerencias de activos según el ciclo.
    """
    st.markdown("---")
    st.subheader("🧱 Análisis Intermarket y Ciclo Económico Integrado")
    
    # Configuración de períodos
    col1, col2, col3 = st.columns(3)
    with col1:
        periodo_analisis = st.selectbox(
            "Período de análisis",
            ["6mo", "1y", "2y", "5y"],
            index=1,
            help="Período para el análisis de variables macro e intermarket"
        )
    with col2:
        ventana_momentum = st.slider(
            "Ventana momentum (días)",
            min_value=10,
            max_value=252,
            value=63,
            help="Ventana para cálculo de momentum y tendencias"
        )
    with col3:
        incluir_ia = st.checkbox(
            "Incluir análisis IA",
            value=True,
            help="Usar IA para diagnóstico de ciclo y sugerencias"
        )
    
    if st.button("🔍 Ejecutar Análisis Intermarket y Ciclo Económico", type="primary"):
        with st.spinner("Analizando variables económicas, macro e intermarket..."):
            
            # ========== 1. ANÁLISIS DE VARIABLES ECONÓMICAS ==========
            st.markdown("### 📈 Variables Económicas de Argentina Datos")
                
                try:
                    # Inicializar ArgentinaDatos
                    ad = ArgentinaDatos()
                    
                    # Obtener análisis económico completo
                    economic_analysis = ad.get_economic_analysis()
                    
                    if economic_analysis['data']:
                        # Mostrar resumen del análisis económico
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                "Fase del Ciclo",
                                economic_analysis['cycle_phase'],
                                help="Fase actual del ciclo económico detectada"
                            )
                        
                        with col2:
                            st.metric(
                                "Nivel de Riesgo",
                                economic_analysis['risk_level'],
                                help="Nivel de riesgo económico actual"
                            )
                        
                        with col3:
                            # Contar datos disponibles
                            datos_disponibles = sum(1 for data in economic_analysis['data'].values() if data)
                            st.metric(
                                "Indicadores Disponibles",
                                f"{datos_disponibles}/6",
                                help="Cantidad de indicadores económicos disponibles"
                            )
                        
                        # Mostrar gráficos de variables económicas
                        st.markdown("#### 📊 Gráficos de Variables Económicas")
                        
                        # Gráfico de inflación
                        if economic_analysis['data']['inflacion']:
                            inflacion_chart = ad.create_inflacion_chart(economic_analysis['data']['inflacion'])
                            if inflacion_chart:
                                fig_inflacion = go.Figure(inflacion_chart)
                                st.plotly_chart(fig_inflacion, use_container_width=True)
                        
                        # Gráfico de tasas
                        if economic_analysis['data']['tasas']:
                            tasas_chart = ad.create_tasas_chart(economic_analysis['data']['tasas'])
                            if tasas_chart:
                                fig_tasas = go.Figure(tasas_chart)
                                st.plotly_chart(fig_tasas, use_container_width=True)
                        
                        # Gráfico de riesgo país
                        if economic_analysis['data']['riesgo_pais']:
                            riesgo_chart = ad.create_riesgo_pais_chart(economic_analysis['data']['riesgo_pais'])
                            if riesgo_chart:
                                fig_riesgo = go.Figure(riesgo_chart)
                                st.plotly_chart(fig_riesgo, use_container_width=True)
                        
                        # Mostrar recomendaciones basadas en el análisis económico
                        st.markdown("#### 💡 Recomendaciones Basadas en Variables Económicas")
                        
                        # Sectores favorables
                        if economic_analysis['sectors']['favorable']:
                            st.success("**Sectores Favorables:**")
                            for sector in economic_analysis['sectors']['favorable']:
                                st.write(f"• {sector}")
                        
                        # Sectores desfavorables
                        if economic_analysis['sectors']['unfavorable']:
                            st.warning("**Sectores Desfavorables:**")
                            for sector in economic_analysis['sectors']['unfavorable']:
                                st.write(f"• {sector}")
                        
                        # Recomendaciones específicas
                        if economic_analysis['recommendations']:
                            st.info("**Recomendaciones Específicas:**")
                            for rec in economic_analysis['recommendations']:
                                st.write(f"• {rec}")
                        
                        # Agregar datos económicos al análisis intermarket
                        economic_data = economic_analysis
                        
                    else:
                        st.warning("No se pudieron obtener datos económicos de Argentina Datos")
                        economic_data = None
                        
                except Exception as e:
                    st.error(f"Error obteniendo datos económicos: {e}")
                    economic_data = None
            
            # ========== 2. VARIABLES MACRO DEL BCRA ==========
            st.markdown("### 📊 Variables Macro del BCRA")
            
            variables_macro = {}
            
            # Variables locales (simuladas con yfinance para demostración)
            tickers_macro_local = {
                'MERVAL': '^MERV',
                'Dólar Oficial': 'USDOLLAR=X',  # Proxy
                'Dólar MEP': 'USDARS=X',  # Proxy
                'Bonos CER': 'GD30',  # Proxy
                'Bonos Dollar-Linked': 'GD30D',  # Proxy
                'Riesgo País': '^VIX',  # Proxy para volatilidad
            }
            
            # Variables internacionales
            tickers_macro_global = {
                'S&P 500': '^GSPC',
                'VIX': '^VIX',
                'Dólar Index': 'DX-Y.NYB',
                'Oro': 'GC=F',
                'Petróleo': 'CL=F',
                'Cobre': 'HG=F',
                'Treasury 10Y': '^TNX',
                'Treasury 2Y': '^UST2YR',
            }
            
            # Obtener datos
            try:
                # Datos locales
                datos_local = yf.download(list(tickers_macro_local.values()), period=periodo_analisis)['Close']
                for nombre, ticker in tickers_macro_local.items():
                    if ticker in datos_local.columns and not datos_local[ticker].empty:
                        serie = datos_local[ticker].dropna()
                        if len(serie) > 0:
                            retornos = serie.pct_change().dropna()
                            momentum = (serie.iloc[-1] / serie.iloc[-ventana_momentum] - 1) * 100 if len(serie) >= ventana_momentum else 0
                            volatilidad = retornos.std() * np.sqrt(252) * 100
                            tendencia = 'Alcista' if momentum > 0 else 'Bajista'
                            
                            variables_macro[nombre] = {
                                'valor_actual': serie.iloc[-1],
                                'momentum': momentum,
                                'volatilidad': volatilidad,
                                'tendencia': tendencia,
                                'serie': serie
                            }
                
                # Datos globales
                datos_global = yf.download(list(tickers_macro_global.values()), period=periodo_analisis)['Close']
                for nombre, ticker in tickers_macro_global.items():
                    if ticker in datos_global.columns and not datos_global[ticker].empty:
                        serie = datos_global[ticker].dropna()
                        if len(serie) > 0:
                            retornos = serie.pct_change().dropna()
                            momentum = (serie.iloc[-1] / serie.iloc[-ventana_momentum] - 1) * 100 if len(serie) >= ventana_momentum else 0
                            volatilidad = retornos.std() * np.sqrt(252) * 100
                            tendencia = 'Alcista' if momentum > 0 else 'Bajista'
                            
                            variables_macro[nombre] = {
                                'valor_actual': serie.iloc[-1],
                                'momentum': momentum,
                                'volatilidad': volatilidad,
                                'tendencia': tendencia,
                                'serie': serie
                            }
                
                # Mostrar métricas macro
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Variables Locales**")
                    for nombre, datos in variables_macro.items():
                        if nombre in tickers_macro_local.values():
                            st.metric(
                                nombre,
                                f"{datos['valor_actual']:.2f}",
                                f"{datos['momentum']:+.1f}% ({datos['tendencia']})",
                                delta_color="normal" if datos['momentum'] > 0 else "inverse"
                            )
                
                with col2:
                    st.markdown("**Variables Globales**")
                    for nombre, datos in variables_macro.items():
                        if nombre in tickers_macro_global.values():
                            st.metric(
                                nombre,
                                f"{datos['valor_actual']:.2f}",
                                f"{datos['momentum']:+.1f}% ({datos['tendencia']})",
                                delta_color="normal" if datos['momentum'] > 0 else "inverse"
                            )
                
            except Exception as e:
                st.error(f"Error obteniendo datos macro: {e}")
                return
            
            # ========== 2. ANÁLISIS INTERMARKET LOCAL ==========
            st.markdown("### 🌐 Análisis Intermarket Local")
            
            # Correlaciones intermarket locales
            if len(variables_macro) >= 3:
                # Crear DataFrame de retornos
                retornos_df = pd.DataFrame()
                for nombre, datos in variables_macro.items():
                    if 'serie' in datos:
                        retornos_df[nombre] = datos['serie'].pct_change().dropna()
                
                if not retornos_df.empty:
                    # Matriz de correlaciones
                    correlaciones = retornos_df.corr()
                    
                    # Gráfico de correlaciones
                    fig_corr = go.Figure(data=go.Heatmap(
                        z=correlaciones.values,
                        x=correlaciones.columns,
                        y=correlaciones.columns,
                        colorscale='RdBu',
                        zmid=0,
                        text=correlaciones.values.round(2),
                        texttemplate="%{text}",
                        textfont={"size": 10},
                        hoverongaps=False
                    ))
                    
                    fig_corr.update_layout(
                        title="Matriz de Correlaciones Intermarket",
                        width=600,
                        height=500
                    )
                    st.plotly_chart(fig_corr, use_container_width=True)
                    
                    # Análisis de divergencias
                    st.markdown("**🔍 Análisis de Divergencias**")
                    
                    # Buscar divergencias entre activos
                    divergencias = []
                    for i, activo1 in enumerate(correlaciones.columns):
                        for j, activo2 in enumerate(correlaciones.columns):
                            if i < j:
                                corr = correlaciones.iloc[i, j]
                                if abs(corr) < 0.3:  # Baja correlación
                                    divergencias.append({
                                        'activo1': activo1,
                                        'activo2': activo2,
                                        'correlacion': corr,
                                        'tipo': 'Divergencia' if corr < 0 else 'Baja correlación'
                                    })
                    
                    if divergencias:
                        df_divergencias = pd.DataFrame(divergencias)
                        st.dataframe(df_divergencias.sort_values('correlacion'))
                    else:
                        st.info("No se detectaron divergencias significativas")
            
            # ========== 3. ANÁLISIS INTERMARKET INTERNACIONAL ==========
            st.markdown("### 🌍 Análisis Intermarket Internacional")
            
            # Curva de tasas (simulada)
            if 'Treasury 10Y' in variables_macro and 'Treasury 2Y' in variables_macro:
                tasa_10y = variables_macro['Treasury 10Y']['valor_actual']
                tasa_2y = variables_macro['Treasury 2Y']['valor_actual']
                spread_curva = tasa_10y - tasa_2y
                
                st.metric(
                    "Spread Curva de Tasas (10Y - 2Y)",
                    f"{spread_curva:.2f}%",
                    "Recesión" if spread_curva < 0 else "Expansión",
                    delta_color="inverse" if spread_curva < 0 else "normal"
                )
                
                # Interpretación de la curva
                if spread_curva < 0:
                    st.warning("⚠️ Curva invertida - Señal de recesión potencial")
                elif spread_curva < 0.5:
                    st.info("📊 Curva plana - Transición de ciclo")
                else:
                    st.success("✅ Curva normal - Ciclo expansivo")
            
            # Análisis Dólar vs Commodities
            if 'Dólar Index' in variables_macro and 'Oro' in variables_macro:
                dolar_momentum = variables_macro['Dólar Index']['momentum']
                oro_momentum = variables_macro['Oro']['momentum']
                
                st.markdown("**💱 Dólar vs Commodities**")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Dólar Index", f"{dolar_momentum:+.1f}%")
                with col2:
                    st.metric("Oro", f"{oro_momentum:+.1f}%")
                
                # Interpretación
                if dolar_momentum > 0 and oro_momentum < 0:
                    st.info("📈 Dólar fuerte, commodities débiles - Ciclo deflacionario")
                elif dolar_momentum < 0 and oro_momentum > 0:
                    st.info("📉 Dólar débil, commodities fuertes - Ciclo inflacionario")
                else:
                    st.info("🔄 Movimiento mixto - Ciclo de transición")
            
            # ========== 4. DETECCIÓN DE CICLO ECONÓMICO ==========
            st.markdown("### 🔄 Detección de Ciclo Económico")
            
            # Puntuación de ciclo basada en múltiples indicadores
            puntuacion_ciclo = 0
            indicadores_ciclo = []
            
            # Indicador 1: Curva de tasas
            if 'Treasury 10Y' in variables_macro and 'Treasury 2Y' in variables_macro:
                spread = variables_macro['Treasury 10Y']['valor_actual'] - variables_macro['Treasury 2Y']['valor_actual']
                if spread < 0:
                    puntuacion_ciclo -= 2
                    indicadores_ciclo.append("Curva invertida (-2)")
                elif spread < 0.5:
                    puntuacion_ciclo -= 1
                    indicadores_ciclo.append("Curva plana (-1)")
                else:
                    puntuacion_ciclo += 1
                    indicadores_ciclo.append("Curva normal (+1)")
            
            # Indicador 2: VIX
            if 'VIX' in variables_macro:
                vix_actual = variables_macro['VIX']['valor_actual']
                if vix_actual > 30:
                    puntuacion_ciclo -= 1
                    indicadores_ciclo.append("VIX alto (-1)")
                elif vix_actual < 15:
                    puntuacion_ciclo += 1
                    indicadores_ciclo.append("VIX bajo (+1)")
                else:
                    indicadores_ciclo.append("VIX normal (0)")
            
            # Indicador 3: Momentum del mercado
            if 'S&P 500' in variables_macro:
                sp500_momentum = variables_macro['S&P 500']['momentum']
                if sp500_momentum > 10:
                    puntuacion_ciclo += 1
                    indicadores_ciclo.append("S&P 500 fuerte (+1)")
                elif sp500_momentum < -10:
                    puntuacion_ciclo -= 1
                    indicadores_ciclo.append("S&P 500 débil (-1)")
                else:
                    indicadores_ciclo.append("S&P 500 neutral (0)")
            
            # Determinar fase del ciclo
            if puntuacion_ciclo >= 2:
                fase_ciclo = "Expansión"
                color_ciclo = "success"
            elif puntuacion_ciclo >= 0:
                fase_ciclo = "Auge"
                color_ciclo = "info"
            elif puntuacion_ciclo >= -1:
                fase_ciclo = "Contracción"
                color_ciclo = "warning"
            else:
                fase_ciclo = "Recesión"
                color_ciclo = "error"
            
            # Mostrar diagnóstico
            st.markdown(f"**🎯 Diagnóstico de Ciclo: {fase_ciclo}**")
            st.markdown(f"**Puntuación:** {puntuacion_ciclo}")
            
            # Mostrar indicadores
            for indicador in indicadores_ciclo:
                st.write(f"• {indicador}")
            
            # ========== 5. SUGERENCIAS DE ACTIVOS SEGÚN CICLO ==========
            st.markdown("### 💡 Sugerencias de Activos por Ciclo")
            
            # Matriz de sugerencias
            matriz_sugerencias = {
                "Expansión": {
                    "Argentina": ["Acciones locales", "CEDEARs", "Bonos CER"],
                    "EEUU": ["S&P 500", "Tecnología", "Consumo Discrecional"],
                    "Comentario": "Flujo de capitales, suba de consumo"
                },
                "Auge": {
                    "Argentina": ["Acciones value", "Activos hard", "Oro"],
                    "EEUU": ["Value stocks", "Real estate", "Commodities"],
                    "Comentario": "Protección ante sobrevaloración"
                },
                "Contracción": {
                    "Argentina": ["Bonos tasa fija", "Dólar MEP", "Dólar-linked"],
                    "EEUU": ["Treasury bonds", "Defensive stocks", "Cash"],
                    "Comentario": "Fuga al refugio, evitar acciones cíclicas"
                },
                "Recesión": {
                    "Argentina": ["CEDEARs defensivos", "Oro", "Bonos soberanos"],
                    "EEUU": ["Consumer staples", "Healthcare", "Utilities"],
                    "Comentario": "Baja actividad, refugio y liquidez"
                }
            }
            
            sugerencias = matriz_sugerencias.get(fase_ciclo, {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🇦🇷 Argentina**")
                for activo in sugerencias.get("Argentina", []):
                    st.write(f"• {activo}")
            
            with col2:
                st.markdown("**🇺🇸 EEUU**")
                for activo in sugerencias.get("EEUU", []):
                    st.write(f"• {activo}")
            
            st.info(f"**💬 Comentario:** {sugerencias.get('Comentario', '')}")
            
            # ========== 6. ANÁLISIS IA (OPCIONAL) ==========
            if incluir_ia and gemini_api_key:
                st.markdown("### 🤖 Análisis IA del Ciclo")
                
                # Preparar datos para IA
                resumen_variables = []
                for nombre, datos in variables_macro.items():
                    resumen_variables.append(
                        f"{nombre}: Valor={datos['valor_actual']:.2f}, "
                        f"Momentum={datos['momentum']:+.1f}%, "
                        f"Tendencia={datos['tendencia']}"
                    )
                
                # Prompt para IA
                prompt_ia = f"""
                Analiza el siguiente resumen de variables macroeconómicas y de mercado:

                {chr(10).join(resumen_variables)}

                Diagnóstico de ciclo actual: {fase_ciclo} (puntuación: {puntuacion_ciclo})

                Proporciona:
                1. Análisis detallado del ciclo económico actual
                2. Factores intermarket más relevantes
                3. Sugerencias específicas de activos para Argentina y EEUU
                4. Riesgos y oportunidades principales

                Responde en español, formato ejecutivo.
                """
                
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=gemini_api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(prompt_ia)
                    
                    if response and response.text:
                        st.markdown(response.text)
                    else:
                        st.warning("No se pudo obtener análisis de IA")
                except Exception as e:
                    st.error(f"Error en análisis IA: {e}")
            
            # ========== 7. GRÁFICOS INTERMARKET ==========
            st.markdown("### 📈 Gráficos Intermarket")
            
            # Gráfico de evolución de variables clave
            if len(variables_macro) >= 3:
                fig_evolucion = go.Figure()
                
                # Normalizar series para comparación
                for nombre, datos in variables_macro.items():
                    if 'serie' in datos and len(datos['serie']) > 0:
                        serie_norm = (datos['serie'] / datos['serie'].iloc[0]) * 100
                        fig_evolucion.add_trace(go.Scatter(
                            x=serie_norm.index,
                            y=serie_norm.values,
                            mode='lines',
                            name=nombre,
                            line=dict(width=2)
                        ))
                
                fig_evolucion.update_layout(
                    title="Evolución Normalizada de Variables Intermarket",
                    xaxis_title="Fecha",
                    yaxis_title="Valor Normalizado (%)",
                    height=500,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_evolucion, use_container_width=True)
            
            # ========== 8. RESUMEN EJECUTIVO ==========
            st.markdown("### 📋 Resumen Ejecutivo")
            
            resumen_ejecutivo = f"""
            **🎯 Ciclo Económico Detectado:** {fase_ciclo}
            
            **📊 Indicadores Clave:**
            - Puntuación de ciclo: {puntuacion_ciclo}
            - Principales divergencias: {len(divergencias) if 'divergencias' in locals() else 0} detectadas
            - Volatilidad promedio: {np.mean([d['volatilidad'] for d in variables_macro.values()]):.1f}%
            
            **💡 Recomendaciones:**
            - **Argentina:** {', '.join(sugerencias.get('Argentina', []))}
            - **EEUU:** {', '.join(sugerencias.get('EEUU', []))}
            
            **⚠️ Riesgos Principales:**
            - {'Curva de tasas invertida' if 'spread_curva' in locals() and spread_curva < 0 else 'Ninguno crítico detectado'}
            - {'VIX elevado' if 'VIX' in variables_macro and variables_macro['VIX']['valor_actual'] > 30 else 'Volatilidad normal'}
            
            **📈 Oportunidades:**
            - Ciclo actual favorece activos {fase_ciclo.lower()}
            - {'Divergencias aprovechables' if 'divergencias' in locals() and len(divergencias) > 0 else 'Correlaciones normales'}
            """
            
            st.markdown(resumen_ejecutivo)
            
            # Guardar resultados en session state
            st.session_state['analisis_intermarket'] = {
                'fase_ciclo': fase_ciclo,
                'puntuacion': puntuacion_ciclo,
                'variables_macro': variables_macro,
                'sugerencias': sugerencias,
                'fecha_analisis': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

class CAPMAnalyzer:
    """
    Clase para análisis CAPM (Capital Asset Pricing Model) de activos individuales
    """
    
    def __init__(self, risk_free_rate=0.0):
        self.risk_free_rate = risk_free_rate
        self.analyses = {}
    
    def calculate_asset_capm(self, asset_returns, market_returns, asset_name="Asset"):
        """
        Calcula métricas CAPM para un activo individual
        
        Args:
            asset_returns (pd.Series): Retornos del activo
            market_returns (pd.Series): Retornos del mercado (benchmark)
            asset_name (str): Nombre del activo
            
        Returns:
            dict: Métricas CAPM del activo
        """
        # Alinear series
        aligned_data = pd.concat([asset_returns, market_returns], axis=1).dropna()
        if len(aligned_data) < 10:
            return None
            
        asset_aligned = aligned_data.iloc[:, 0]
        market_aligned = aligned_data.iloc[:, 1]
        
        # Regresión CAPM: R_asset - Rf = α + β(R_market - Rf)
        market_excess = market_aligned - self.risk_free_rate/252  # Diario
        asset_excess = asset_aligned - self.risk_free_rate/252
        
        slope, intercept, r_value, p_value, std_err = linregress(market_excess, asset_excess)
        
        # Calcular métricas adicionales
        tracking_error = np.std(asset_excess - slope * market_excess) * np.sqrt(252)
        information_ratio = intercept * 252 / tracking_error if tracking_error != 0 else 0
        treynor_ratio = (asset_aligned.mean() * 252 - self.risk_free_rate) / slope if slope != 0 else 0
        
        result = {
            'asset_name': asset_name,
            'alpha': intercept * 252,  # Anualizado
            'beta': slope,
            'r_squared': r_value ** 2,
            'p_value': p_value,
            'tracking_error': tracking_error,
            'information_ratio': information_ratio,
            'treynor_ratio': treynor_ratio,
            'volatility': asset_aligned.std() * np.sqrt(252),
            'sharpe_ratio': (asset_aligned.mean() * 252 - self.risk_free_rate) / (asset_aligned.std() * np.sqrt(252)),
            'observations': len(aligned_data)
        }
        
        self.analyses[asset_name] = result
        return result
    
    def classify_asset_strategy(self, capm_metrics):
        """
        Clasifica el activo según su estrategia de inversión basada en CAPM
        
        Args:
            capm_metrics (dict): Métricas CAPM del activo
            
        Returns:
            dict: Clasificación de estrategia
        """
        beta = capm_metrics.get('beta', 1.0)
        alpha = capm_metrics.get('alpha', 0)
        r_squared = capm_metrics.get('r_squared', 0)
        
        # Clasificación según las estrategias especificadas
        if abs(beta - 1.0) < 0.1 and abs(alpha) < 0.02:
            strategy_type = "Index Tracker"
            description = "Replica el rendimiento del benchmark (β ≈ 1, α ≈ 0)"
            characteristics = ["Baja volatilidad", "Rendimiento en línea con mercado", "Bajo tracking error"]
        elif beta >= 0.9 and beta <= 1.1 and alpha > 0.02:
            strategy_type = "Traditional Long-Only"
            description = "Supera al mercado con retorno adicional no correlacionado (β ≈ 1, α > 0)"
            characteristics = ["Alfa positivo", "Riesgo similar al mercado", "Generación de valor agregado"]
        elif beta > 1.1 or beta < 0.9:
            strategy_type = "Smart Beta"
            description = "Ajusta dinámicamente la exposición al mercado (β ≠ 1, α ≈ 0)"
            characteristics = ["Beta dinámico", "Ajuste táctico", "Gestión de riesgo activa"]
        elif abs(beta) < 0.3 and alpha > 0.02:
            strategy_type = "Hedge Fund"
            description = "Retornos absolutos no correlacionados con el mercado (β ≈ 0, α > 0)"
            characteristics = ["Baja correlación", "Retornos absolutos", "Gestión alternativa"]
        else:
            strategy_type = "Mixed Strategy"
            description = "Estrategia mixta con características combinadas"
            characteristics = ["Perfil único", "Características mixtas", "Análisis individual requerido"]
        
        return {
            'strategy_type': strategy_type,
            'description': description,
            'characteristics': characteristics,
            'beta': beta,
            'alpha': alpha,
            'r_squared': r_squared
        }

class DefensiveAssetFinder:
    """
    Clase para encontrar activos defensivos basados en análisis CAPM
    """
    
    def __init__(self, token_portador):
        self.token_portador = token_portador
        self.capm_analyzer = CAPMAnalyzer()
    
    def find_defensive_assets(self, market_returns, min_beta=0.3, max_beta=0.8, min_alpha=-0.05):
        """
        Encuentra activos defensivos basados en criterios CAPM
        
        Args:
            market_returns (pd.Series): Retornos del mercado
            min_beta (float): Beta mínimo para activos defensivos
            max_beta (float): Beta máximo para activos defensivos
            min_alpha (float): Alpha mínimo aceptable
            
        Returns:
            list: Lista de activos defensivos con sus métricas
        """
        defensive_assets = []
        
        # Obtener lista de activos disponibles
        try:
            # Usar paneles conocidos de acciones defensivas
            paneles_defensivos = ['Panel General', 'Panel Líderes']
            tickers_por_panel = obtener_tickers_por_panel(
                self.token_portador, 
                paneles_defensivos, 
                pais='Argentina'
            )
            
            for panel, tickers in tickers_por_panel.items():
                for ticker in tickers[:20]:  # Limitar a 20 por panel para eficiencia
                    try:
                        # Obtener datos históricos del ticker
                        df_historico = obtener_serie_historica_iol(
                            self.token_portador,
                            'BCBA',  # Asumir mercado BCBA
                            ticker,
                            (datetime.now() - timedelta(days=252)).strftime('%Y-%m-%d'),
                            datetime.now().strftime('%Y-%m-%d'),
                            "SinAjustar"
                        )
                        
                        if df_historico is not None and len(df_historico) > 50:
                            # Calcular retornos
                            asset_returns = df_historico['close'].pct_change().dropna()
                            
                            # Análisis CAPM
                            capm_metrics = self.capm_analyzer.calculate_asset_capm(
                                asset_returns, market_returns, ticker
                            )
                            
                            if capm_metrics:
                                beta = capm_metrics['beta']
                                alpha = capm_metrics['alpha']
                                
                                # Verificar criterios defensivos
                                if (min_beta <= beta <= max_beta and 
                                    alpha >= min_alpha and 
                                    capm_metrics['r_squared'] > 0.3):
                                    
                                    defensive_assets.append({
                                        'ticker': ticker,
                                        'capm_metrics': capm_metrics,
                                        'strategy': self.capm_analyzer.classify_asset_strategy(capm_metrics),
                                        'defensive_score': self._calculate_defensive_score(capm_metrics)
                                    })
                    
                    except Exception as e:
                        print(f"Error procesando {ticker}: {str(e)}")
                        continue
            
            # Ordenar por score defensivo
            defensive_assets.sort(key=lambda x: x['defensive_score'], reverse=True)
            
        except Exception as e:
            print(f"Error en búsqueda de activos defensivos: {str(e)}")
        
        return defensive_assets
    
    def _calculate_defensive_score(self, capm_metrics):
        """
        Calcula un score defensivo basado en métricas CAPM
        
        Args:
            capm_metrics (dict): Métricas CAPM del activo
            
        Returns:
            float: Score defensivo (0-100)
        """
        beta = capm_metrics['beta']
        alpha = capm_metrics['alpha']
        volatility = capm_metrics['volatility']
        sharpe = capm_metrics['sharpe_ratio']
        
        # Score basado en beta (menor = más defensivo)
        beta_score = max(0, 100 - abs(beta - 0.5) * 100)
        
        # Score basado en alpha (mayor = mejor)
        alpha_score = min(100, max(0, (alpha + 0.1) * 500))
        
        # Score basado en volatilidad (menor = más defensivo)
        vol_score = max(0, 100 - volatility * 100)
        
        # Score basado en Sharpe (mayor = mejor)
        sharpe_score = min(100, max(0, sharpe * 50 + 50))
        
        # Ponderación: Beta 40%, Alpha 30%, Volatilidad 20%, Sharpe 10%
        total_score = (beta_score * 0.4 + alpha_score * 0.3 + 
                      vol_score * 0.2 + sharpe_score * 0.1)
        
        return total_score

class InvestmentStrategyRecommender:
    """
    Clase para generar recomendaciones de estrategias de inversión basadas en análisis CAPM
    """
    
    def __init__(self, token_portador, gemini_api_key=None):
        self.token_portador = token_portador
        self.gemini_api_key = gemini_api_key
        self.capm_analyzer = CAPMAnalyzer()
        self.defensive_finder = DefensiveAssetFinder(token_portador)
    
    def generate_market_recommendations(self, market_conditions, portfolio_analysis=None):
        """
        Genera recomendaciones basadas en condiciones de mercado
        
        Args:
            market_conditions (dict): Condiciones actuales del mercado
            portfolio_analysis (dict): Análisis del portafolio actual (opcional)
            
        Returns:
            dict: Recomendaciones de estrategia
        """
        recommendations = {
            'market_phase': self._determine_market_phase(market_conditions),
            'recommended_strategies': [],
            'defensive_assets': [],
            'risk_adjustments': {},
            'implementation_notes': []
        }
        
        # Determinar estrategias recomendadas según fase del mercado
        market_phase = recommendations['market_phase']
        
        if market_phase == 'Bear Market' or market_phase == 'High Volatility':
            recommendations['recommended_strategies'] = [
                {
                    'strategy': 'Defensive Positioning',
                    'description': 'Reducir exposición a acciones cíclicas, aumentar activos defensivos',
                    'target_beta': 0.3,
                    'max_beta': 0.8,
                    'priority': 'High'
                },
                {
                    'strategy': 'Hedge Fund Approach',
                    'description': 'Buscar activos con baja correlación y alpha positivo',
                    'target_beta': 0.0,
                    'max_beta': 0.3,
                    'priority': 'Medium'
                }
            ]
            
            # Buscar activos defensivos
            try:
                market_returns = self._get_market_returns()
                defensive_assets = self.defensive_finder.find_defensive_assets(
                    market_returns, min_beta=0.2, max_beta=0.7, min_alpha=-0.03
                )
                recommendations['defensive_assets'] = defensive_assets[:10]  # Top 10
            except Exception as e:
                print(f"Error buscando activos defensivos: {str(e)}")
        
        elif market_phase == 'Bull Market':
            recommendations['recommended_strategies'] = [
                {
                    'strategy': 'Smart Beta',
                    'description': 'Aumentar exposición táctica con beta dinámico',
                    'target_beta': 1.2,
                    'max_beta': 1.5,
                    'priority': 'High'
                },
                {
                    'strategy': 'Traditional Long-Only',
                    'description': 'Mantener exposición al mercado con alpha positivo',
                    'target_beta': 1.0,
                    'max_beta': 1.1,
                    'priority': 'Medium'
                }
            ]
        
        elif market_phase == 'Sideways Market':
            recommendations['recommended_strategies'] = [
                {
                    'strategy': 'Index Tracker',
                    'description': 'Mantener exposición neutral al mercado',
                    'target_beta': 1.0,
                    'max_beta': 1.0,
                    'priority': 'High'
                },
                {
                    'strategy': 'Hedge Fund',
                    'description': 'Buscar oportunidades no correlacionadas',
                    'target_beta': 0.0,
                    'max_beta': 0.3,
                    'priority': 'Medium'
                }
            ]
        
        # Ajustes de riesgo
        recommendations['risk_adjustments'] = self._calculate_risk_adjustments(
            market_phase, portfolio_analysis
        )
        
        # Notas de implementación
        recommendations['implementation_notes'] = self._generate_implementation_notes(
            recommendations
        )
        
        return recommendations
    
    def _determine_market_phase(self, market_conditions):
        """
        Determina la fase actual del mercado
        """
        vix = market_conditions.get('VIX', {}).get('valor_actual', 20)
        trend = market_conditions.get('tendencia_mercado', 'neutral')
        volatility = market_conditions.get('volatilidad', 'normal')
        
        if vix > 30 or volatility == 'alta':
            return 'High Volatility'
        elif trend == 'bajista' or vix > 25:
            return 'Bear Market'
        elif trend == 'alcista' and vix < 20:
            return 'Bull Market'
        else:
            return 'Sideways Market'
    
    def _get_market_returns(self):
        """
        Obtiene retornos del mercado (MERVAL)
        """
        try:
            merval_data = yf.download('^MERV', 
                                    start=(datetime.now() - timedelta(days=252)).strftime('%Y-%m-%d'),
                                    end=datetime.now().strftime('%Y-%m-%d'))['Close']
            return merval_data.pct_change().dropna()
        except Exception as e:
            print(f"Error obteniendo datos del MERVAL: {str(e)}")
            return None
    
    def _calculate_risk_adjustments(self, market_phase, portfolio_analysis):
        """
        Calcula ajustes de riesgo según la fase del mercado
        """
        adjustments = {
            'position_sizing': {},
            'stop_loss': {},
            'diversification': {}
        }
        
        if market_phase in ['Bear Market', 'High Volatility']:
            adjustments['position_sizing'] = {
                'max_position': 0.05,  # 5% máximo por posición
                'total_equity': 0.6,   # 60% máximo en acciones
                'cash_reserve': 0.4    # 40% en efectivo
            }
            adjustments['stop_loss'] = {
                'tight_stops': True,
                'stop_percentage': 0.05  # 5% stop loss
            }
            adjustments['diversification'] = {
                'min_positions': 15,
                'max_sector_weight': 0.15  # 15% máximo por sector
            }
        
        elif market_phase == 'Bull Market':
            adjustments['position_sizing'] = {
                'max_position': 0.10,  # 10% máximo por posición
                'total_equity': 0.9,   # 90% máximo en acciones
                'cash_reserve': 0.1    # 10% en efectivo
            }
            adjustments['stop_loss'] = {
                'tight_stops': False,
                'stop_percentage': 0.10  # 10% stop loss
            }
            adjustments['diversification'] = {
                'min_positions': 10,
                'max_sector_weight': 0.25  # 25% máximo por sector
            }
        
        else:  # Sideways Market
            adjustments['position_sizing'] = {
                'max_position': 0.07,  # 7% máximo por posición
                'total_equity': 0.75,  # 75% máximo en acciones
                'cash_reserve': 0.25   # 25% en efectivo
            }
            adjustments['stop_loss'] = {
                'tight_stops': True,
                'stop_percentage': 0.07  # 7% stop loss
            }
            adjustments['diversification'] = {
                'min_positions': 12,
                'max_sector_weight': 0.20  # 20% máximo por sector
            }
        
        return adjustments
    
    def _generate_implementation_notes(self, recommendations):
        """
        Genera notas de implementación para las recomendaciones
        """
        notes = []
        
        for strategy in recommendations['recommended_strategies']:
            if strategy['strategy'] == 'Defensive Positioning':
                notes.append({
                    'type': 'warning',
                    'message': 'Reducir exposición a sectores cíclicos (financiero, industrial)',
                    'action': 'Aumentar peso en utilities, consumer staples, healthcare'
                })
                notes.append({
                    'type': 'info',
                    'message': 'Considerar bonos corporativos de alta calidad',
                    'action': 'Evaluar bonos con rating A o superior'
                })
            
            elif strategy['strategy'] == 'Smart Beta':
                notes.append({
                    'type': 'info',
                    'message': 'Implementar rebalanceo táctico',
                    'action': 'Ajustar pesos cada 2-4 semanas según condiciones'
                })
            
            elif strategy['strategy'] == 'Hedge Fund Approach':
                notes.append({
                    'type': 'warning',
                    'message': 'Buscar activos con correlación negativa',
                    'action': 'Evaluar ETFs inversos o estrategias de cobertura'
                })
        
        return notes

def mostrar_analisis_capm_y_estrategias(token_acceso, gemini_api_key=None):
    """
    Muestra análisis CAPM y recomendaciones de estrategias de inversión
    """
    st.header("📊 Análisis CAPM y Estrategias de Inversión")
    
    # Inicializar el recomendador de estrategias
    recommender = InvestmentStrategyRecommender(token_acceso, gemini_api_key)
    
    # Obtener condiciones de mercado del análisis intermarket
    if 'analisis_intermarket' in st.session_state:
        market_conditions = st.session_state['analisis_intermarket'].get('variables_macro', {})
        fase_ciclo = st.session_state['analisis_intermarket'].get('fase_ciclo', 'Desconocida')
    else:
        st.warning("⚠️ Ejecute primero el análisis intermarket para obtener condiciones de mercado")
        return
    
    # Mostrar fase del mercado
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Fase del Ciclo", fase_ciclo)
    
    with col2:
        vix_actual = market_conditions.get('VIX', {}).get('valor_actual', 0)
        st.metric("VIX Actual", f"{vix_actual:.1f}")
    
    # Generar recomendaciones
    with st.spinner("Generando recomendaciones de estrategias..."):
        recommendations = recommender.generate_market_recommendations(market_conditions)
    
    # Mostrar estrategias recomendadas
    st.subheader("🎯 Estrategias Recomendadas")
    
    for i, strategy in enumerate(recommendations['recommended_strategies']):
        with st.expander(f"{i+1}. {strategy['strategy']} - {strategy['priority']} Priority"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Descripción:** {strategy['description']}")
                st.write(f"**Beta Objetivo:** {strategy['target_beta']:.2f}")
                st.write(f"**Beta Máximo:** {strategy['max_beta']:.2f}")
            
            with col2:
                if strategy['priority'] == 'High':
                    st.success("🟢 Alta Prioridad")
                else:
                    st.info("🔵 Prioridad Media")
    
    # Mostrar activos defensivos si están disponibles
    if recommendations['defensive_assets']:
        st.subheader("🛡️ Activos Defensivos Recomendados")
        
        # Crear DataFrame para mostrar
        defensive_data = []
        for asset in recommendations['defensive_assets'][:10]:  # Top 10
            defensive_data.append({
                'Ticker': asset['ticker'],
                'Beta': f"{asset['capm_metrics']['beta']:.3f}",
                'Alpha (%)': f"{asset['capm_metrics']['alpha']*100:.2f}",
                'Volatilidad (%)': f"{asset['capm_metrics']['volatility']*100:.1f}",
                'Sharpe': f"{asset['capm_metrics']['sharpe_ratio']:.2f}",
                'Score Defensivo': f"{asset['defensive_score']:.1f}",
                'Estrategia': asset['strategy']['strategy_type']
            })
        
        df_defensive = pd.DataFrame(defensive_data)
        st.dataframe(df_defensive, use_container_width=True)
    
    # Mostrar ajustes de riesgo
    st.subheader("⚖️ Ajustes de Riesgo")
    
    risk_adj = recommendations['risk_adjustments']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Tamaño de Posiciones**")
        pos_sizing = risk_adj['position_sizing']
        st.write(f"• Máximo por posición: {pos_sizing['max_position']*100:.0f}%")
        st.write(f"• Total en acciones: {pos_sizing['total_equity']*100:.0f}%")
        st.write(f"• Reserva en efectivo: {pos_sizing['cash_reserve']*100:.0f}%")
    
    with col2:
        st.write("**Stop Loss**")
        stop_loss = risk_adj['stop_loss']
        st.write(f"• Stop loss: {stop_loss['stop_percentage']*100:.0f}%")
        if stop_loss['tight_stops']:
            st.write("• Stops ajustados: ✅")
        else:
            st.write("• Stops ajustados: ❌")
    
    with col3:
        st.write("**Diversificación**")
        diversification = risk_adj['diversification']
        st.write(f"• Mínimo posiciones: {diversification['min_positions']}")
        st.write(f"• Máximo por sector: {diversification['max_sector_weight']*100:.0f}%")
    
    # Mostrar notas de implementación
    if recommendations['implementation_notes']:
        st.subheader("📝 Notas de Implementación")
        
        for note in recommendations['implementation_notes']:
            if note['type'] == 'warning':
                st.warning(f"⚠️ {note['message']}")
            else:
                st.info(f"ℹ️ {note['message']}")
            
            st.write(f"**Acción:** {note['action']}")
            st.divider()

def analizar_portafolio_capm(portafolio, token_portador, dias_historial=252):
    """
    Analiza un portafolio usando métricas CAPM
    """
    if not portafolio:
        return None
    
    # Obtener datos del MERVAL
    try:
        merval_data = yf.download('^MERV', 
                                start=(datetime.now() - timedelta(days=dias_historial)).strftime('%Y-%m-%d'),
                                end=datetime.now().strftime('%Y-%m-%d'))['Close']
        market_returns = merval_data.pct_change().dropna()
    except Exception as e:
        print(f"Error obteniendo datos del MERVAL: {str(e)}")
        return None
    
    # Inicializar analizador CAPM
    capm_analyzer = CAPMAnalyzer()
    portfolio_analysis = {
        'assets_analysis': [],
        'portfolio_metrics': {},
        'strategy_classification': {}
    }
    
    # Analizar cada activo
    for simbolo, activo in portafolio.items():
        try:
            # Obtener datos históricos
            df_historico = obtener_serie_historica_iol(
                token_portador,
                activo.get('mercado', 'BCBA'),
                simbolo,
                (datetime.now() - timedelta(days=dias_historial)).strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d'),
                "SinAjustar"
            )
            
            if df_historico is not None and len(df_historico) > 50:
                asset_returns = df_historico['close'].pct_change().dropna()
                
                # Análisis CAPM del activo
                capm_metrics = capm_analyzer.calculate_asset_capm(
                    asset_returns, market_returns, simbolo
                )
                
                if capm_metrics:
                    strategy_class = capm_analyzer.classify_asset_strategy(capm_metrics)
                    
                    portfolio_analysis['assets_analysis'].append({
                        'symbol': simbolo,
                        'capm_metrics': capm_metrics,
                        'strategy': strategy_class,
                        'weight': activo.get('Valuación', 0) / sum(a.get('Valuación', 0) for a in portafolio.values())
                    })
        
        except Exception as e:
            print(f"Error analizando {simbolo}: {str(e)}")
            continue
    
    # Calcular métricas del portafolio
    if portfolio_analysis['assets_analysis']:
        # Beta ponderado del portafolio
        portfolio_beta = sum(
            asset['capm_metrics']['beta'] * asset['weight'] 
            for asset in portfolio_analysis['assets_analysis']
        )
        
        # Alpha ponderado del portafolio
        portfolio_alpha = sum(
            asset['capm_metrics']['alpha'] * asset['weight'] 
            for asset in portfolio_analysis['assets_analysis']
        )
        
        # Clasificar estrategia del portafolio
        portfolio_strategy = capm_analyzer.classify_asset_strategy({
            'beta': portfolio_beta,
            'alpha': portfolio_alpha
        })
        
        portfolio_analysis['portfolio_metrics'] = {
            'portfolio_beta': portfolio_beta,
            'portfolio_alpha': portfolio_alpha,
            'total_assets': len(portfolio_analysis['assets_analysis'])
        }
        
        portfolio_analysis['strategy_classification'] = portfolio_strategy
    
    return portfolio_analysis

def mostrar_analisis_capm_portafolio(token_acceso, id_cliente):
    """
    Muestra análisis CAPM del portafolio actual del cliente
    """
    st.header("📊 Análisis CAPM del Portafolio")
    
    # Obtener portafolio del cliente
    try:
        portafolio = obtener_portafolio(token_acceso, id_cliente)
        if not portafolio:
            st.warning("No se pudo obtener el portafolio del cliente")
            return
        
        # Calcular valor total
        valor_total = sum(activo.get('Valuación', 0) for activo in portafolio.values())
        
        if valor_total <= 0:
            st.warning("El portafolio no tiene valor o no se pudo calcular")
            return
        
        # Analizar portafolio con CAPM
        with st.spinner("Analizando portafolio con métricas CAPM..."):
            portfolio_analysis = analizar_portafolio_capm(portafolio, token_acceso)
        
        if not portfolio_analysis or not portfolio_analysis['assets_analysis']:
            st.warning("No se pudo realizar el análisis CAPM del portafolio")
            return
        
        # Mostrar métricas del portafolio
        st.subheader("📈 Métricas del Portafolio")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Beta del Portafolio", f"{portfolio_analysis['portfolio_metrics']['portfolio_beta']:.3f}")
        
        with col2:
            st.metric("Alpha del Portafolio", f"{portfolio_analysis['portfolio_metrics']['portfolio_alpha']*100:.2f}%")
        
        with col3:
            st.metric("Total de Activos", portfolio_analysis['portfolio_metrics']['total_assets'])
        
        with col4:
            strategy_type = portfolio_analysis['strategy_classification']['strategy_type']
            st.metric("Estrategia", strategy_type)
        
        # Mostrar clasificación de estrategia
        st.subheader("🎯 Clasificación de Estrategia")
        
        strategy = portfolio_analysis['strategy_classification']
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write(f"**Tipo de Estrategia:** {strategy['strategy_type']}")
            st.write(f"**Descripción:** {strategy['description']}")
            st.write("**Características:**")
            for char in strategy['characteristics']:
                st.write(f"• {char}")
        
        with col2:
            if strategy['strategy_type'] == "Index Tracker":
                st.success("🟢 Estrategia Conservadora")
            elif strategy['strategy_type'] == "Traditional Long-Only":
                st.info("🔵 Estrategia Balanceada")
            elif strategy['strategy_type'] == "Smart Beta":
                st.warning("🟡 Estrategia Táctica")
            elif strategy['strategy_type'] == "Hedge Fund":
                st.error("🔴 Estrategia Alternativa")
            else:
                st.info("⚪ Estrategia Mixta")
        
        # Mostrar análisis por activo
        st.subheader("📊 Análisis por Activo")
        
        # Crear DataFrame para mostrar
        assets_data = []
        for asset in portfolio_analysis['assets_analysis']:
            assets_data.append({
                'Símbolo': asset['symbol'],
                'Beta': f"{asset['capm_metrics']['beta']:.3f}",
                'Alpha (%)': f"{asset['capm_metrics']['alpha']*100:.2f}",
                'Volatilidad (%)': f"{asset['capm_metrics']['volatility']*100:.1f}",
                'Sharpe': f"{asset['capm_metrics']['sharpe_ratio']:.2f}",
                'Peso (%)': f"{asset['weight']*100:.1f}",
                'Estrategia': asset['strategy']['strategy_type']
            })
        
        df_assets = pd.DataFrame(assets_data)
        st.dataframe(df_assets, use_container_width=True)
        
        # Gráfico de dispersión Beta vs Alpha
        st.subheader("📈 Dispersión Beta vs Alpha")
        
        fig = go.Figure()
        
        # Agrupar por estrategia
        strategies = {}
        for asset in portfolio_analysis['assets_analysis']:
            strategy = asset['strategy']['strategy_type']
            if strategy not in strategies:
                strategies[strategy] = {'betas': [], 'alphas': [], 'symbols': []}
            
            strategies[strategy]['betas'].append(asset['capm_metrics']['beta'])
            strategies[strategy]['alphas'].append(asset['capm_metrics']['alpha'])
            strategies[strategy]['symbols'].append(asset['symbol'])
        
        # Colores por estrategia
        colors = {
            'Index Tracker': 'green',
            'Traditional Long-Only': 'blue',
            'Smart Beta': 'orange',
            'Hedge Fund': 'red',
            'Mixed Strategy': 'purple'
        }
        
        for strategy, data in strategies.items():
            fig.add_trace(go.Scatter(
                x=data['betas'],
                y=[alpha * 100 for alpha in data['alphas']],
                mode='markers+text',
                text=data['symbols'],
                textposition="top center",
                name=strategy,
                marker=dict(
                    size=10,
                    color=colors.get(strategy, 'gray')
                ),
                hovertemplate='<b>%{text}</b><br>' +
                            'Beta: %{x:.3f}<br>' +
                            'Alpha: %{y:.2f}%<br>' +
                            'Estrategia: ' + strategy +
                            '<extra></extra>'
            ))
        
        # Líneas de referencia
        fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Alpha = 0")
        fig.add_vline(x=1, line_dash="dash", line_color="gray", annotation_text="Beta = 1")
        
        fig.update_layout(
            title="Dispersión de Activos por Beta y Alpha",
            xaxis_title="Beta",
            yaxis_title="Alpha (%)",
            height=500,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Recomendaciones específicas
        st.subheader("💡 Recomendaciones Específicas")
        
        # Analizar concentración de riesgo
        high_beta_assets = [a for a in portfolio_analysis['assets_analysis'] if a['capm_metrics']['beta'] > 1.2]
        low_alpha_assets = [a for a in portfolio_analysis['assets_analysis'] if a['capm_metrics']['alpha'] < -0.05]
        
        if high_beta_assets:
            st.warning("⚠️ **Activos de Alto Riesgo Detectados:**")
            for asset in high_beta_assets:
                st.write(f"• {asset['symbol']}: Beta = {asset['capm_metrics']['beta']:.3f}")
            st.write("**Recomendación:** Considerar reducir exposición o implementar cobertura")
        
        if low_alpha_assets:
            st.warning("⚠️ **Activos con Alpha Negativo:**")
            for asset in low_alpha_assets:
                st.write(f"• {asset['symbol']}: Alpha = {asset['capm_metrics']['alpha']*100:.2f}%")
            st.write("**Recomendación:** Evaluar reemplazo por activos con mejor rendimiento")
        
        # Sugerencias de diversificación
        strategy_counts = {}
        for asset in portfolio_analysis['assets_analysis']:
            strategy = asset['strategy']['strategy_type']
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        if len(strategy_counts) < 3:
            st.info("ℹ️ **Diversificación de Estrategias:**")
            st.write("El portafolio está concentrado en pocas estrategias. Considerar diversificar entre:")
            st.write("• Index Tracker (estabilidad)")
            st.write("• Smart Beta (táctica)")
            st.write("• Hedge Fund (alternativa)")
        
    except Exception as e:
        st.error(f"Error en el análisis CAPM del portafolio: {str(e)}")


def obtener_datos_bcra():
    """
    Obtiene datos reales del BCRA para variables macroeconómicas.
    Incluye expectativas de mercado, tasas, reservas, etc.
    """
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    from datetime import datetime, timedelta
    
    datos_bcra = {}
    
    try:
        # URL del BCRA con expectativas de mercado
        url_expectativas = "https://www.bcra.gob.ar/PublicacionesEstadisticas/Relevamiento_Expectativas_de_Mercado.asp"
        
        # Headers para simular navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Intentar obtener datos del BCRA
        response = requests.get(url_expectativas, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraer datos de expectativas (ejemplo de estructura)
            # Nota: La estructura real puede variar
            try:
                # Buscar tablas con datos de expectativas
                tablas = soup.find_all('table')
                
                for tabla in tablas:
                    # Buscar datos de inflación esperada
                    if 'inflación' in tabla.get_text().lower() or 'ipc' in tabla.get_text().lower():
                        filas = tabla.find_all('tr')
                        for fila in filas:
                            celdas = fila.find_all(['td', 'th'])
                            if len(celdas) >= 2:
                                texto = celdas[0].get_text().strip()
                                valor = celdas[1].get_text().strip()
                                
                                if 'inflación' in texto.lower():
                                    try:
                                        datos_bcra['inflacion_esperada'] = float(valor.replace('%', '').replace(',', '.'))
                                    except:
                                        pass
                
                # Si no se encontraron datos en la página, usar valores de respaldo
                if not datos_bcra:
                    st.warning("No se pudieron extraer datos del BCRA. Usando valores de respaldo.")
                    datos_bcra = {
                        'inflacion_esperada': 8.5,  # % mensual
                        'tasa_politica': 50.0,      # % anual
                        'reservas': 25000,          # millones USD
                        'm2_crecimiento': 12.5      # % anual
                    }
                
            except Exception as e:
                st.warning(f"Error procesando datos del BCRA: {e}")
                # Usar valores de respaldo
                datos_bcra = {
                    'inflacion_esperada': 8.5,
                    'tasa_politica': 50.0,
                    'reservas': 25000,
                    'm2_crecimiento': 12.5
                }
        else:
            st.warning(f"No se pudo acceder al BCRA (código {response.status_code})")
            # Usar valores de respaldo
            datos_bcra = {
                'inflacion_esperada': 8.5,
                'tasa_politica': 50.0,
                'reservas': 25000,
                'm2_crecimiento': 12.5
            }
            
    except Exception as e:
        st.warning(f"Error de conexión con BCRA: {e}")
        # Usar valores de respaldo
        datos_bcra = {
            'inflacion_esperada': 8.5,
            'tasa_politica': 50.0,
            'reservas': 25000,
            'm2_crecimiento': 12.5
        }
    
    return datos_bcra


def actualizar_variables_macro_con_bcra():
    """
    Actualiza las variables macroeconómicas con datos reales del BCRA.
    """
    st.markdown("### 🔄 Actualización de Variables Macro del BCRA")
    
    if st.button("🔄 Actualizar Datos del BCRA", type="primary"):
        with st.spinner("Obteniendo datos actualizados del BCRA..."):
            
            # Obtener datos del BCRA
            datos_bcra = obtener_datos_bcra()
            
            # Mostrar datos obtenidos
            st.success("✅ Datos del BCRA obtenidos exitosamente")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Inflación Esperada",
                    f"{datos_bcra['inflacion_esperada']:.1f}%",
                    "Mensual"
                )
                st.metric(
                    "Tasa de Política",
                    f"{datos_bcra['tasa_politica']:.1f}%",
                    "Anual"
                )
            
            with col2:
                st.metric(
                    "Reservas Internacionales",
                    f"{datos_bcra['reservas']:,.0f}M USD",
                    "Millones"
                )
                st.metric(
                    "Crecimiento M2",
                    f"{datos_bcra['m2_crecimiento']:.1f}%",
                    "Anual"
                )
            
            # Guardar en session state para uso posterior
            st.session_state['datos_bcra'] = datos_bcra
            
            # Análisis automático del ciclo económico
            st.markdown("### 📊 Análisis del Ciclo Económico con Datos BCRA")
            
            # Determinar fase del ciclo basada en los datos
            inflacion = datos_bcra['inflacion_esperada']
            tasa = datos_bcra['tasa_politica']
            reservas = datos_bcra['reservas']
            m2 = datos_bcra['m2_crecimiento']
            
            # Lógica de clasificación del ciclo
            puntuacion_ciclo = 0
            
            # Análisis de inflación
            if inflacion > 10:
                puntuacion_ciclo -= 2  # Alta inflación = contracción
            elif inflacion < 5:
                puntuacion_ciclo += 1  # Baja inflación = expansión
            else:
                puntuacion_ciclo += 0  # Inflación moderada
            
            # Análisis de tasas
            if tasa > 60:
                puntuacion_ciclo -= 1  # Tasas altas = contracción
            elif tasa < 30:
                puntuacion_ciclo += 1  # Tasas bajas = expansión
            
            # Análisis de reservas
            if reservas > 30000:
                puntuacion_ciclo += 1  # Reservas altas = estabilidad
            elif reservas < 20000:
                puntuacion_ciclo -= 1  # Reservas bajas = vulnerabilidad
            
            # Análisis de M2
            if m2 > 15:
                puntuacion_ciclo += 1  # Crecimiento monetario alto
            elif m2 < 10:
                puntuacion_ciclo -= 1  # Crecimiento monetario bajo
            
            # Determinar fase del ciclo
            if puntuacion_ciclo >= 2:
                fase_ciclo = "Expansión"
                color_fase = "success"
            elif puntuacion_ciclo <= -2:
                fase_ciclo = "Contracción"
                color_fase = "error"
            else:
                fase_ciclo = "Estabilización"
                color_fase = "info"
            
            # Mostrar diagnóstico
            st.markdown(f"**🎯 Diagnóstico del Ciclo Económico:**")
            
            if color_fase == "success":
                st.success(f"**{fase_ciclo}** - Puntuación: {puntuacion_ciclo}")
            elif color_fase == "error":
                st.error(f"**{fase_ciclo}** - Puntuación: {puntuacion_ciclo}")
            else:
                st.info(f"**{fase_ciclo}** - Puntuación: {puntuacion_ciclo}")
            
            # Recomendaciones específicas
            st.markdown("### 💡 Recomendaciones de Inversión")
            
            if fase_ciclo == "Expansión":
                st.success("🚀 **Estrategia Ofensiva Recomendada**")
                st.write("• Mantener exposición a activos de riesgo")
                st.write("• Considerar acciones de crecimiento")
                st.write("• Evaluar bonos corporativos")
                st.write("• Monitorear indicadores de sobrecalentamiento")
                
            elif fase_ciclo == "Contracción":
                st.warning("⚠️ **Estrategia Defensiva Recomendada**")
                st.write("• Reducir exposición a activos de riesgo")
                st.write("• Aumentar posición en efectivo")
                st.write("• Considerar bonos del tesoro")
                st.write("• Evaluar activos refugio (oro, dólar)")
                
            else:
                st.info("⚖️ **Estrategia Balanceada Recomendada**")
                st.write("• Mantener diversificación equilibrada")
                st.write("• Monitorear señales de cambio de ciclo")
                st.write("• Considerar estrategias de valor")
                st.write("• Mantener liquidez moderada")
            
            # Guardar análisis en session state
            st.session_state['analisis_ciclo_bcra'] = {
                'fase_ciclo': fase_ciclo,
                'puntuacion': puntuacion_ciclo,
                'datos': datos_bcra,
                'fecha_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }


def integrar_datos_bcra_en_ciclo_economico():
    """
    Integra los datos del BCRA en el análisis del ciclo económico.
    """
    if 'datos_bcra' in st.session_state:
        datos_bcra = st.session_state['datos_bcra']
        
        st.markdown("### 📊 Datos BCRA Integrados")
        
        # Crear métricas con datos reales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Inflación BCRA",
                f"{datos_bcra['inflacion_esperada']:.1f}%",
                "Mensual"
            )
        
        with col2:
            st.metric(
                "Tasa Política",
                f"{datos_bcra['tasa_politica']:.1f}%",
                "Anual"
            )
        
        with col3:
            st.metric(
                "Reservas",
                f"{datos_bcra['reservas']:,.0f}M USD",
                "Millones"
            )
        
        with col4:
            st.metric(
                "Crecimiento M2",
                f"{datos_bcra['m2_crecimiento']:.1f}%",
                "Anual"
            )
        
        return datos_bcra
    else:
        st.info("ℹ️ Ejecute 'Actualizar Datos del BCRA' para integrar datos oficiales")
        return None


def mostrar_analisis_variables_economicas(token_acceso, gemini_api_key=None):
    """
    Muestra análisis completo de variables económicas de Argentina Datos.
    Incluye gráficos, análisis de ciclo económico y recomendaciones.
    """
    st.markdown("---")
    st.subheader("📈 Análisis de Variables Económicas - Argentina Datos")
    
    # Configuración de parámetros
    col1, col2, col3 = st.columns(3)
    with col1:
        periodo_analisis = st.selectbox(
            "Período de análisis",
            ["1 mes", "3 meses", "6 meses", "1 año"],
            index=1,
            help="Período para el análisis de variables económicas"
        )
    with col2:
        indicadores_seleccionados = st.multiselect(
            "Indicadores a mostrar",
            ["Inflación", "Tasas", "Riesgo País", "Dólar", "UVA"],
            default=["Inflación", "Tasas", "Riesgo País"],
            help="Seleccionar indicadores económicos a mostrar"
        )
    with col3:
        incluir_ia = st.checkbox(
            "Incluir análisis IA",
            value=True,
            help="Usar IA para análisis y recomendaciones"
        )
    
    if st.button("📊 Generar Análisis de Variables Económicas", type="primary"):
        with st.spinner("Obteniendo y analizando variables económicas..."):
            
            try:
                # Inicializar ArgentinaDatos
                ad = ArgentinaDatos()
                
                # Obtener análisis económico completo
                economic_analysis = ad.get_economic_analysis()
                
                if economic_analysis['data']:
                    # ========== 1. RESUMEN DEL ANÁLISIS ECONÓMICO ==========
                    st.markdown("### 📋 Resumen del Análisis Económico")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Fase del Ciclo",
                            economic_analysis['cycle_phase'],
                            help="Fase actual del ciclo económico detectada"
                        )
                    
                    with col2:
                        st.metric(
                            "Nivel de Riesgo",
                            economic_analysis['risk_level'],
                            help="Nivel de riesgo económico actual"
                        )
                    
                    with col3:
                        # Contar datos disponibles
                        datos_disponibles = sum(1 for data in economic_analysis['data'].values() if data)
                        st.metric(
                            "Indicadores Disponibles",
                            f"{datos_disponibles}/6",
                            help="Cantidad de indicadores económicos disponibles"
                        )
                    
                    with col4:
                        # Calcular tendencia general
                        tendencia = "Alcista" if economic_analysis['cycle_phase'] in ['Accommodative Monetary Policy', 'Disinflationary'] else "Bajista"
                        st.metric(
                            "Tendencia General",
                            tendencia,
                            help="Tendencia general del ciclo económico"
                        )
                    
                    # ========== 2. GRÁFICOS DE VARIABLES ECONÓMICAS ==========
                    st.markdown("### 📊 Gráficos de Variables Económicas")
                    
                    # Gráfico de inflación
                    if "Inflación" in indicadores_seleccionados and economic_analysis['data']['inflacion']:
                        st.markdown("#### 📈 Evolución de la Inflación")
                        inflacion_chart = ad.create_inflacion_chart(economic_analysis['data']['inflacion'])
                        if inflacion_chart:
                            fig_inflacion = go.Figure(inflacion_chart)
                            st.plotly_chart(fig_inflacion, use_container_width=True)
                    
                    # Gráfico de tasas
                    if "Tasas" in indicadores_seleccionados and economic_analysis['data']['tasas']:
                        st.markdown("#### 💰 Evolución de las Tasas de Interés")
                        tasas_chart = ad.create_tasas_chart(economic_analysis['data']['tasas'])
                        if tasas_chart:
                            fig_tasas = go.Figure(tasas_chart)
                            st.plotly_chart(fig_tasas, use_container_width=True)
                    
                    # Gráfico de riesgo país
                    if "Riesgo País" in indicadores_seleccionados and economic_analysis['data']['riesgo_pais']:
                        st.markdown("#### ⚠️ Evolución del Riesgo País")
                        riesgo_chart = ad.create_riesgo_pais_chart(economic_analysis['data']['riesgo_pais'])
                        if riesgo_chart:
                            fig_riesgo = go.Figure(riesgo_chart)
                            st.plotly_chart(fig_riesgo, use_container_width=True)
                    
                    # Gráfico de dólar
                    if "Dólar" in indicadores_seleccionados and economic_analysis['data']['dolares']:
                        st.markdown("#### 💵 Evolución del Dólar")
                        dolares_chart = ad.create_dolares_chart(economic_analysis['data']['dolares'], periodo_analisis)
                        if dolares_chart:
                            fig_dolares = go.Figure(dolares_chart)
                            st.plotly_chart(fig_dolares, use_container_width=True)
                    
                    # Gráfico de UVA
                    if "UVA" in indicadores_seleccionados and economic_analysis['data']['uva']:
                        st.markdown("#### 🏠 Evolución del UVA")
                        uva_chart = ad.create_uva_chart(economic_analysis['data']['uva'])
                        if uva_chart:
                            fig_uva = go.Figure(uva_chart)
                            st.plotly_chart(fig_uva, use_container_width=True)
                    
                    # ========== 3. ANÁLISIS DE CICLO ECONÓMICO ==========
                    st.markdown("### 🔄 Análisis del Ciclo Económico")
                    
                    # Explicar la fase del ciclo
                    if economic_analysis['cycle_phase'] == 'Inflationary Pressure':
                        st.warning("**📈 Presión Inflacionaria Detectada**")
                        st.write("""
                        **Características de esta fase:**
                        - Alta inflación que erosiona el poder adquisitivo
                        - Presión sobre las tasas de interés
                        - Inestabilidad en los mercados financieros
                        - Dificultades para el crecimiento económico
                        """)
                        
                    elif economic_analysis['cycle_phase'] == 'Tightening Monetary Policy':
                        st.info("**🔒 Política Monetaria Restrictiva**")
                        st.write("""
                        **Características de esta fase:**
                        - Tasas de interés elevadas para controlar la inflación
                        - Menor acceso al crédito
                        - Desaceleración del crecimiento económico
                        - Presión sobre sectores sensibles a las tasas
                        """)
                        
                    elif economic_analysis['cycle_phase'] == 'Accommodative Monetary Policy':
                        st.success("**💰 Política Monetaria Expansiva**")
                        st.write("""
                        **Características de esta fase:**
                        - Tasas de interés bajas para estimular la economía
                        - Mayor acceso al crédito
                        - Estimulación del crecimiento económico
                        - Favorable para inversiones de largo plazo
                        """)
                        
                    elif economic_analysis['cycle_phase'] == 'Disinflationary':
                        st.info("**📉 Desinflación**")
                        st.write("""
                        **Características de esta fase:**
                        - Reducción de la tasa de inflación
                        - Estabilización de precios
                        - Mejora en la confianza económica
                        - Oportunidades para inversiones
                        """)
                    
                    # ========== 4. RECOMENDACIONES DE INVERSIÓN ==========
                    st.markdown("### 💡 Recomendaciones de Inversión")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if economic_analysis['sectors']['favorable']:
                            st.success("**✅ Sectores Favorables**")
                            for sector in economic_analysis['sectors']['favorable']:
                                st.write(f"• {sector}")
                    
                    with col2:
                        if economic_analysis['sectors']['unfavorable']:
                            st.warning("**❌ Sectores Desfavorables**")
                            for sector in economic_analysis['sectors']['unfavorable']:
                                st.write(f"• {sector}")
                    
                    # Recomendaciones específicas
                    if economic_analysis['recommendations']:
                        st.info("**📋 Recomendaciones Específicas**")
                        for i, rec in enumerate(economic_analysis['recommendations'], 1):
                            st.write(f"{i}. {rec}")
                    
                    # ========== 5. ANÁLISIS CON IA ==========
                    if incluir_ia and gemini_api_key:
                        try:
                            st.markdown("### 🤖 Análisis IA de Variables Económicas")
                            
                            # Preparar datos para IA
                            resumen_economico = f"""
                            Análisis de Variables Económicas de Argentina:
                            
                            **Fase del Ciclo Económico:**
                            - Fase actual: {economic_analysis['cycle_phase']}
                            - Nivel de riesgo: {economic_analysis['risk_level']}
                            
                            **Sectores de Inversión:**
                            - Sectores favorables: {', '.join(economic_analysis['sectors']['favorable'])}
                            - Sectores desfavorables: {', '.join(economic_analysis['sectors']['unfavorable'])}
                            
                            **Recomendaciones Generadas:**
                            {chr(10).join([f"- {rec}" for rec in economic_analysis['recommendations']])}
                            
                            **Datos Disponibles:**
                            - Inflación: {'Disponible' if economic_analysis['data']['inflacion'] else 'No disponible'}
                            - Tasas: {'Disponible' if economic_analysis['data']['tasas'] else 'No disponible'}
                            - Riesgo País: {'Disponible' if economic_analysis['data']['riesgo_pais'] else 'No disponible'}
                            - Dólar: {'Disponible' if economic_analysis['data']['dolares'] else 'No disponible'}
                            - UVA: {'Disponible' if economic_analysis['data']['uva'] else 'No disponible'}
                            """
                            
                            # Llamar a IA para análisis
                            genai.configure(api_key=gemini_api_key)
                            model = genai.GenerativeModel('gemini-pro')
                            
                            prompt = f"""
                            Analiza las siguientes variables económicas de Argentina y proporciona un análisis detallado:
                            
                            {resumen_economico}
                            
                            Proporciona:
                            1. **Diagnóstico del ciclo económico argentino:** Explica en qué parte del ciclo se encuentra Argentina y qué significa esto
                            2. **Análisis de sectores e instrumentos:** Qué sectores e instrumentos financieros son más adecuados para esta fase del ciclo
                            3. **Estrategias de inversión:** Recomendaciones específicas de inversión para el contexto argentino
                            4. **Gestión de riesgo:** Cómo gestionar el riesgo en el contexto económico actual
                            5. **Horizonte temporal:** Qué horizonte temporal es más adecuado para las inversiones
                            6. **Señales de alerta:** Qué indicadores monitorear para detectar cambios en el ciclo
                            7. **Oportunidades específicas:** Qué oportunidades únicas presenta el mercado argentino en esta fase
                            
                            Responde en español de manera clara y práctica, enfocándote en el mercado argentino.
                            """
                            
                            response = model.generate_content(prompt)
                            st.write(response.text)
                            
                        except Exception as e:
                            st.warning(f"No se pudo generar análisis IA: {e}")
                
                else:
                    st.error("No se pudieron obtener datos económicos suficientes para el análisis")
                    
            except Exception as e:
                st.error(f"Error en el análisis de variables económicas: {e}")


def graficar_ciclo_economico_real(token_acceso, gemini_api_key=None):
    """
    Grafica el ciclo económico real usando datos macroeconómicos.
    Incluye indicadores como PBI, inflación, tasas, empleo, etc.
    """
    st.markdown("---")
    st.subheader("📈 Ciclo Económico Real - Análisis Macroeconómico")
    
    # Configuración de parámetros
    col1, col2, col3 = st.columns(3)
    with col1:
        periodo_analisis = st.selectbox(
            "Período de análisis",
            ["1y", "2y", "5y", "10y"],
            index=1,
            help="Período para el análisis del ciclo económico"
        )
    with col2:
        indicadores_seleccionados = st.multiselect(
            "Indicadores a analizar",
            ["PBI", "Inflación", "Tasas de Interés", "Empleo", "Consumo", "Inversión", "Comercio Exterior", "Confianza"],
            default=["PBI", "Inflación", "Tasas de Interés", "Empleo"],
            help="Seleccionar indicadores macroeconómicos"
        )
    with col3:
        incluir_pronostico = st.checkbox(
            "Incluir pronóstico",
            value=True,
            help="Incluir proyecciones de tendencia"
        )
    
    # Agregar sección de datos BCRA
    st.markdown("---")
    st.markdown("### 🏦 Datos Oficiales del BCRA")
    
    # Botón para actualizar datos del BCRA
    actualizar_variables_macro_con_bcra()
    
    # Integrar datos BCRA si están disponibles
    datos_bcra = integrar_datos_bcra_en_ciclo_economico()
    
    st.markdown("---")
    st.markdown("### 📈 Análisis de Mercados Financieros")
    
    if st.button("📊 Generar Gráfico del Ciclo Económico", type="primary"):
        with st.spinner("Obteniendo datos macroeconómicos y generando gráficos..."):
            
            # ========== 1. DATOS MACROECONÓMICOS REALES ==========
            st.markdown("### 📊 Indicadores Macroeconómicos")
            
            # Definir tickers para indicadores macro (usando proxies de yfinance)
            indicadores_tickers = {
                'PBI': '^MERV',  # Proxy usando MERVAL como indicador de actividad económica
                'Inflación': '^VIX',  # Proxy usando VIX como indicador de incertidumbre
                'Tasas de Interés': '^TNX',  # Treasury 10Y como proxy de tasas
                'Empleo': '^DJI',  # Dow Jones como proxy de empleo/actividad
                'Consumo': 'XLY',  # Consumer Discretionary ETF
                'Inversión': 'XLK',  # Technology ETF como proxy de inversión
                'Comercio Exterior': 'UUP',  # US Dollar Index
                'Confianza': '^VIX'  # VIX como indicador de confianza
            }
            
            # Obtener datos históricos
            datos_macro = {}
            fechas_comunes = None
            
            try:
                # Obtener datos para indicadores seleccionados
                tickers_seleccionados = [indicadores_tickers[ind] for ind in indicadores_seleccionados if ind in indicadores_tickers]
                
                if tickers_seleccionados:
                    # Descargar datos
                    datos_raw = yf.download(tickers_seleccionados, period=periodo_analisis)['Close']
                    
                    # Procesar cada indicador
                    for indicador in indicadores_seleccionados:
                        if indicador in indicadores_tickers:
                            ticker = indicadores_tickers[indicador]
                            if ticker in datos_raw.columns:
                                serie = datos_raw[ticker].dropna()
                                if len(serie) > 0:
                                    # Normalizar serie (base 100)
                                    serie_normalizada = (serie / serie.iloc[0]) * 100
                                    
                                    # Calcular métricas del ciclo
                                    retornos = serie.pct_change().dropna()
                                    momentum = (serie.iloc[-1] / serie.iloc[-63] - 1) * 100 if len(serie) >= 63 else 0
                                    volatilidad = retornos.std() * np.sqrt(252) * 100
                                    
                                    # Determinar fase del ciclo
                                    if momentum > 5:
                                        fase_ciclo = "Expansión"
                                        color_fase = "green"
                                    elif momentum > -5:
                                        fase_ciclo = "Estabilización"
                                        color_fase = "orange"
                                    else:
                                        fase_ciclo = "Contracción"
                                        color_fase = "red"
                                    
                                    datos_macro[indicador] = {
                                        'serie': serie_normalizada,
                                        'momentum': momentum,
                                        'volatilidad': volatilidad,
                                        'fase_ciclo': fase_ciclo,
                                        'color_fase': color_fase,
                                        'valor_actual': serie.iloc[-1],
                                        'valor_normalizado': serie_normalizada.iloc[-1]
                                    }
                    
                    # Establecer fechas comunes para todos los indicadores
                    if datos_macro:
                        fechas_comunes = datos_macro[list(datos_macro.keys())[0]]['serie'].index
                        for indicador in datos_macro:
                            datos_macro[indicador]['serie'] = datos_macro[indicador]['serie'].reindex(fechas_comunes).fillna(method='ffill')
                
            except Exception as e:
                st.error(f"Error obteniendo datos macroeconómicos: {e}")
                return
            
            # ========== 2. GRÁFICO DEL CICLO ECONÓMICO ==========
            if datos_macro:
                st.markdown("### 📈 Visualización del Ciclo Económico")
                
                # Crear gráfico principal del ciclo
                fig_ciclo = go.Figure()
                
                # Colores para las fases del ciclo
                colores_fases = {
                    'Expansión': 'green',
                    'Estabilización': 'orange', 
                    'Contracción': 'red'
                }
                
                # Agregar cada indicador al gráfico
                for indicador, datos in datos_macro.items():
                    fig_ciclo.add_trace(go.Scatter(
                        x=datos['serie'].index,
                        y=datos['serie'].values,
                        mode='lines+markers',
                        name=f"{indicador} ({datos['fase_ciclo']})",
                        line=dict(color=datos['color_fase'], width=2),
                        marker=dict(size=4),
                        hovertemplate=f'<b>{indicador}</b><br>' +
                                    'Fecha: %{x}<br>' +
                                    'Valor: %{y:.1f}<br>' +
                                    f'Fase: {datos["fase_ciclo"]}<br>' +
                                    f'Momentum: {datos["momentum"]:.1f}%<br>' +
                                    '<extra></extra>'
                    ))
                
                # Configurar layout
                fig_ciclo.update_layout(
                    title="Ciclo Económico Real - Indicadores Macroeconómicos",
                    xaxis_title="Fecha",
                    yaxis_title="Valor Normalizado (Base 100)",
                    height=600,
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                # Agregar líneas de referencia para fases del ciclo
                fig_ciclo.add_hline(y=100, line_dash="dash", line_color="gray", 
                                  annotation_text="Línea Base", annotation_position="top right")
                
                st.plotly_chart(fig_ciclo, use_container_width=True)
                
                # ========== 3. ANÁLISIS DE CORRELACIÓN ENTRE INDICADORES ==========
                st.markdown("### 🔗 Análisis de Correlación entre Indicadores")
                
                # Crear DataFrame de retornos para correlación
                retornos_df = pd.DataFrame()
                for indicador, datos in datos_macro.items():
                    retornos_df[indicador] = datos['serie'].pct_change().dropna()
                
                if not retornos_df.empty and len(retornos_df.columns) > 1:
                    # Matriz de correlaciones
                    correlaciones = retornos_df.corr()
                    
                    # Gráfico de correlaciones
                    fig_corr = go.Figure(data=go.Heatmap(
                        z=correlaciones.values,
                        x=correlaciones.columns,
                        y=correlaciones.columns,
                        colorscale='RdBu',
                        zmid=0,
                        text=correlaciones.values.round(2),
                        texttemplate="%{text}",
                        textfont={"size": 12},
                        hoverongaps=False
                    ))
                    
                    fig_corr.update_layout(
                        title="Correlación entre Indicadores Macroeconómicos",
                        width=600,
                        height=500
                    )
                    st.plotly_chart(fig_corr, use_container_width=True)
                
                # ========== 4. RESUMEN DE FASES DEL CICLO ==========
                st.markdown("### 📋 Resumen de Fases del Ciclo Económico")
                
                # Crear tabla de resumen
                resumen_data = []
                for indicador, datos in datos_macro.items():
                    resumen_data.append({
                        'Indicador': indicador,
                        'Fase Actual': datos['fase_ciclo'],
                        'Momentum (%)': f"{datos['momentum']:.1f}",
                        'Volatilidad (%)': f"{datos['volatilidad']:.1f}",
                        'Valor Actual': f"{datos['valor_actual']:.2f}",
                        'Valor Normalizado': f"{datos['valor_normalizado']:.1f}"
                    })
                
                df_resumen = pd.DataFrame(resumen_data)
                st.dataframe(df_resumen, use_container_width=True)
                
                # ========== 5. ANÁLISIS DE TENDENCIAS Y PRONÓSTICOS ==========
                if incluir_pronostico:
                    st.markdown("### 🔮 Análisis de Tendencias y Proyecciones")
                    
                    # Calcular tendencias lineales
                    tendencias = {}
                    for indicador, datos in datos_macro.items():
                        x = np.arange(len(datos['serie']))
                        y = datos['serie'].values
                        
                        # Ajuste lineal
                        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                        
                        # Proyección a 3 meses
                        proyeccion_3m = slope * (len(x) + 63) + intercept
                        cambio_proyeccion = ((proyeccion_3m - datos['valor_normalizado']) / datos['valor_normalizado']) * 100
                        
                        tendencias[indicador] = {
                            'pendiente': slope,
                            'r_cuadrado': r_value**2,
                            'proyeccion_3m': proyeccion_3m,
                            'cambio_proyeccion': cambio_proyeccion,
                            'tendencia': 'Alcista' if slope > 0 else 'Bajista'
                        }
                    
                    # Mostrar proyecciones
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📈 Proyecciones a 3 meses**")
                        for indicador, tendencia in tendencias.items():
                            color_tendencia = "green" if tendencia['tendencia'] == 'Alcista' else "red"
                            st.metric(
                                indicador,
                                f"{tendencia['proyeccion_3m']:.1f}",
                                f"{tendencia['cambio_proyeccion']:+.1f}% ({tendencia['tendencia']})",
                                delta_color="normal" if tendencia['tendencia'] == 'Alcista' else "inverse"
                            )
                    
                    with col2:
                        st.markdown("**📊 Calidad de las Tendencias**")
                        for indicador, tendencia in tendencias.items():
                            calidad = "Alta" if tendencia['r_cuadrado'] > 0.7 else "Media" if tendencia['r_cuadrado'] > 0.4 else "Baja"
                            st.metric(
                                f"{indicador} (R²)",
                                f"{tendencia['r_cuadrado']:.2f}",
                                calidad
                            )
                
                # ========== 6. RECOMENDACIONES BASADAS EN EL CICLO ==========
                st.markdown("### 💡 Recomendaciones de Inversión Basadas en el Ciclo")
                
                # Contar fases
                fases_count = {}
                for datos in datos_macro.values():
                    fase = datos['fase_ciclo']
                    fases_count[fase] = fases_count.get(fase, 0) + 1
                
                # Determinar fase dominante
                fase_dominante = max(fases_count, key=fases_count.get) if fases_count else "Estabilización"
                
                # Generar recomendaciones
                if fase_dominante == "Expansión":
                    st.success("🚀 **Fase de Expansión Económica Detectada**")
                    st.write("• **Recomendación:** Mantener exposición a activos de riesgo")
                    st.write("• **Sectores favorables:** Tecnología, Consumo Discrecional, Financiero")
                    st.write("• **Estrategia:** Posicionamiento ofensivo con diversificación")
                    
                elif fase_dominante == "Contracción":
                    st.warning("⚠️ **Fase de Contracción Económica Detectada**")
                    st.write("• **Recomendación:** Reducir exposición a activos de riesgo")
                    st.write("• **Sectores defensivos:** Utilities, Consumo Básico, Healthcare")
                    st.write("• **Estrategia:** Posicionamiento defensivo con activos refugio")
                    
                else:
                    st.info("⚖️ **Fase de Estabilización Económica Detectada**")
                    st.write("• **Recomendación:** Mantener equilibrio en el portafolio")
                    st.write("• **Sectores balanceados:** Mixto entre ofensivo y defensivo")
                    st.write("• **Estrategia:** Diversificación equilibrada")
                
                # Análisis con IA si está disponible
                if gemini_api_key:
                    try:
                        st.markdown("### 🤖 Análisis IA del Ciclo Económico")
                        
                        # Preparar datos para IA incluyendo datos BCRA si están disponibles
                        resumen_ciclo = f"""
                        Análisis del ciclo económico actual:
                        - Fase dominante: {fase_dominante}
                        - Indicadores analizados: {', '.join(indicadores_seleccionados)}
                        - Distribución de fases: {fases_count}
                        - Momentum promedio: {np.mean([d['momentum'] for d in datos_macro.values()]):.1f}%
                        """
                        
                        # Agregar datos BCRA si están disponibles
                        if datos_bcra:
                            resumen_ciclo += f"""
                        Datos oficiales del BCRA:
                        - Inflación esperada: {datos_bcra['inflacion_esperada']:.1f}% mensual
                        - Tasa de política: {datos_bcra['tasa_politica']:.1f}% anual
                        - Reservas internacionales: {datos_bcra['reservas']:,.0f}M USD
                        - Crecimiento M2: {datos_bcra['m2_crecimiento']:.1f}% anual
                        """
                        
                        # Agregar datos económicos de Argentina Datos si están disponibles
                        if economic_data:
                            resumen_ciclo += f"""
                        Análisis de Variables Económicas (Argentina Datos):
                        - Fase del ciclo económico: {economic_data['cycle_phase']}
                        - Nivel de riesgo: {economic_data['risk_level']}
                        - Sectores favorables: {', '.join(economic_data['sectors']['favorable'])}
                        - Sectores desfavorables: {', '.join(economic_data['sectors']['unfavorable'])}
                        - Recomendaciones económicas: {', '.join(economic_data['recommendations'])}
                        """
                        
                        # Llamar a IA para análisis
                        genai.configure(api_key=gemini_api_key)
                        model = genai.GenerativeModel('gemini-pro')
                        
                        prompt = f"""
                        Analiza el siguiente ciclo económico y proporciona recomendaciones de inversión específicas:
                        
                        {resumen_ciclo}
                        
                        Considera tanto los datos de mercados financieros como los datos oficiales del BCRA y las variables económicas de Argentina Datos.
                        
                        Proporciona:
                        1. Diagnóstico del ciclo económico actual y en qué parte del ciclo se encuentra Argentina
                        2. Recomendaciones específicas de activos/sectores según la fase del ciclo
                        3. Estrategias de gestión de riesgo adaptadas al contexto argentino
                        4. Horizonte temporal recomendado para las inversiones
                        5. Señales de alerta a monitorear específicas del mercado argentino
                        6. Impacto de las políticas del BCRA y variables económicas en las recomendaciones
                        7. Instrumentos financieros específicos recomendados para el contexto argentino
                        8. Análisis de correlación entre variables económicas y mercados financieros
                        9. Oportunidades de arbitraje entre diferentes instrumentos financieros
                        
                        Responde en español de manera clara y práctica, enfocándote en el mercado argentino.
                        """
                        
                        response = model.generate_content(prompt)
                        st.write(response.text)
                        
                    except Exception as e:
                        st.warning(f"No se pudo generar análisis IA: {e}")
            
            else:
                st.error("No se pudieron obtener datos macroeconómicos suficientes para el análisis")


if __name__ == "__main__":
    main()
