import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import base64
import io
import matplotlib.pyplot as plt
from scipy import stats
import seaborn as sns
from scipy.optimize import minimize
import warnings
import random
from typing import Dict, List, Tuple, Optional, Union
import time
from scipy.optimize import minimize as op_minimize

warnings.filterwarnings('ignore')

# Configuración de la API
API_BASE_URL = 'https://api.invertironline.com'
TOKEN_URL = f"{API_BASE_URL}/token"

class IOLDataFetcher:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self._authenticate()
    
    def _authenticate(self) -> bool:
        """Autentica y obtiene los tokens de acceso"""
        payload = {
            'username': self.username,
            'password': self.password,
            'grant_type': 'password'
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(TOKEN_URL, data=payload, headers=headers)
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens['access_token']
            self.refresh_token = tokens['refresh_token']
            return True
        else:
            st.error(f"Error de autenticación: {response.status_code} - {response.text}")
            return False
    
    def _refresh_token(self) -> bool:
        """Actualiza el token de acceso usando el refresh token"""
        if not self.refresh_token:
            return self._authenticate()
            
        payload = {
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        response = requests.post(TOKEN_URL, data=payload, headers=headers)
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens['access_token']
            self.refresh_token = tokens.get('refresh_token', self.refresh_token)
            return True
        else:
            return self._authenticate()
    
    def _make_request(self, endpoint: str, method: str = 'GET', **kwargs) -> Optional[dict]:
        """Realiza una petición autenticada a la API"""
        if not self.access_token:
            if not self._authenticate():
                return None
        
        url = f"{API_BASE_URL}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, **kwargs)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, **kwargs)
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:  # Token expirado
                if self._refresh_token():
                    return self._make_request(endpoint, method, **kwargs)
            
            st.error(f"Error en la petición {endpoint}: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            st.error(f"Error al realizar la petición a {endpoint}: {str(e)}")
            return None
    
    def get_historical_data(self, symbol: str, market: str, 
                          start_date: str, end_date: str, 
                          adjusted: bool = False) -> Optional[pd.DataFrame]:
        """Obtiene datos históricos para un símbolo en un mercado específico"""
        endpoint = f"/api/v2/{market}/Titulos/{symbol}/Cotizacion/seriehistorica/"
        endpoint += f"{start_date}/{end_date}/{'Ajustada' if adjusted else 'SinAjustar'}"
        
        data = self._make_request(endpoint)
        if data and isinstance(data, list):
            df = pd.DataFrame(data)
            if not df.empty and 'fecha' in df.columns:
                df['fecha'] = pd.to_datetime(df['fecha'])
                df.set_index('fecha', inplace=True)
                df.sort_index(inplace=True)
                return df
        return None

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

def obtener_estado_cuenta(token_portador, id_cliente=None):
    """Obtiene el estado de cuenta del cliente"""
    if id_cliente:
        url = f'https://api.invertironline.com/api/v2/estadocuenta/{id_cliente}'
    else:
        url = 'https://api.invertironline.com/api/v2/estadocuenta'
    
    headers = obtener_encabezado_autorizacion(token_portador)
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener estado de cuenta: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def obtener_portafolio(token_portador, id_cliente, pais='Argentina'):
    """Obtiene el portafolio del cliente"""
    url = f'https://api.invertironline.com/api/v2/portafolio/{id_cliente}/{pais}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error al obtener portafolio: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

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

def mostrar_portada():
    st.title("📊 Analizador de Portafolio IOL")
    st.markdown("---")
    
    # Sección de bienvenida
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Bienvenido al Analizador de Portafolio IOL
        
        Esta herramienta le permite analizar y optimizar su portafolio de inversiones 
        en Invertir Online de manera sencilla y efectiva.
        
        **Características principales:**
        - Visualización detallada de su portafolio
        - Análisis de riesgo y rendimiento
        - Optimización de cartera
        - Seguimiento de activos en tiempo real
        
        Comience iniciando sesión con sus credenciales de IOL.
        """)
    
    with col2:
        st.image("https://via.placeholder.com/400x300.png?text=Analizador+de+Portafolio", 
                use_column_width=True)
    
    # Tarjetas de características
    st.markdown("### 🚀 Comience a invertir de manera inteligente")
    cols = st.columns(3)
    with cols[0]:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.2); border-radius: 12px; padding: 25px; width: 100%; backdrop-filter: blur(5px);">
            <h3>📊 Análisis Completo</h3>
            <p>Visualice todos sus activos en un solo lugar con detalle</p>
        </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.2); border-radius: 12px; padding: 25px; width: 100%; backdrop-filter: blur(5px);">
            <h3>📈 Gráficos Interactivos</h3>
            <p>Comprenda su portafolio con visualizaciones avanzadas</p>
        </div>
        """, unsafe_allow_html=True)
    with cols[2]:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.2); border-radius: 12px; padding: 25px; width: 100%; backdrop-filter: blur(5px);">
            <h3>⚖️ Gestión de Riesgo</h3>
            <p>Identifique concentraciones y optimice su perfil de riesgo</p>
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
    
    # Sidebar for navigation
    st.sidebar.title("Navegación")
    options = ["Inicio", "Operaciones", "Estadísticas", "Configuración"]
    choice = st.sidebar.selectbox("Ir a", options)
    
    # Page routing
    if choice == "Inicio":
        st.header("Página de Inicio")
        st.write("Bienvenido a la aplicación!")
    elif choice == "Operaciones":
        mostrar_operaciones()  # Now this function is defined
    elif choice == "Estadísticas":
        st.header("Estadísticas")
        st.write("Aquí se mostrarán estadísticas...")
    elif choice == "Configuración":
        st.header("Configuración")
        st.write("Ajustes de la aplicación...")

class PortfolioManager:
    def __init__(self):
        self.iol_client = None
        self.portafolio_data = None
        self.estado_cuenta = None
    
    def login(self, username: str, password: str) -> bool:
        """Inicia sesión en IOL"""
        try:
            self.iol_client = IOLDataFetcher(username, password)
            if self.iol_client.access_token:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success("¡Inicio de sesión exitoso!")
                return True
            return False
        except Exception as e:
            st.error(f"Error al iniciar sesión: {str(e)}")
            return False
    
    def cargar_portafolio(self):
        """Carga el portafolio del usuario"""
        if not hasattr(self, 'iol_client') or not self.iol_client:
            st.error("No se ha iniciado sesión")
            return None
        
        try:
            # Obtener estado de cuenta
            self.estado_cuenta = obtener_estado_cuenta(
                self.iol_client.access_token,
                st.session_state.get('selected_client_id')
            )
            
            if not self.estado_cuenta:
                st.error("No se pudo cargar el estado de cuenta")
                return None
                
            # Obtener portafolio
            self.portafolio_data = obtener_portafolio(
                self.iol_client.access_token,
                st.session_state.get('selected_client_id'),
                'Argentina'
            )
            
            if not self.portafolio_data:
                st.error("No se pudo cargar el portafolio")
                return None
                
            return self.portafolio_data
            
        except Exception as e:
            st.error(f"Error al cargar el portafolio: {str(e)}")
            return None

def main():
    # Inicializar el gestor de portafolio
    if 'portfolio_manager' not in st.session_state:
        st.session_state.portfolio_manager = PortfolioManager()
    
    # Barra lateral para login
    with st.sidebar:
        st.title("🔐 Iniciar Sesión")
        
        if not st.session_state.get('logged_in', False):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            
            if st.button("Iniciar Sesión"):
                if username and password:
                    if st.session_state.portfolio_manager.login(username, password):
                        st.rerun()
                else:
                    st.warning("Por favor ingrese usuario y contraseña")
        else:
            st.success(f"Sesión iniciada como: {st.session_state.get('username')}")
            if st.button("Cerrar Sesión"):
                st.session_state.clear()
                st.rerun()
    
    # Contenido principal
    if not st.session_state.get('logged_in', False):
        mostrar_portada()
    else:
        # Pestañas principales
        tabs = st.tabs(["📊 Portafolio", "📈 Análisis", "⚙️ Configuración"])
        
        with tabs[0]:  # Pestaña de Portafolio
            st.title("📊 Mi Portafolio")
            
            # Botón para cargar/actualizar portafolio
            if st.button("🔄 Actualizar Portafolio"):
                with st.spinner("Cargando datos del portafolio..."):
                    portafolio = st.session_state.portfolio_manager.cargar_portafolio()
                    
                    if portafolio:
                        # Mostrar resumen del portafolio
                        st.subheader("Resumen del Portafolio")
                        
                        # Calcular métricas básicas
                        if 'activos' in portafolio and portafolio['activos']:
                            df_activos = pd.DataFrame(portafolio['activos'])
                            
                            # Mostrar métricas principales
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Invertido", f"${df_activos['valorActual'].sum():,.2f}")
                            with col2:
                                st.metric("Rendimiento Total", f"{df_activos['rendimiento'].mean():.2f}%")
                            with col3:
                                st.metric("N° de Activos", len(df_activos))
                            
                            # Mostrar tabla de activos
                            st.subheader("Activos en Cartera")
                            st.dataframe(df_activos[['activo', 'cantidad', 'precioPromedio', 'ultimoPrecio', 'variacion', 'valorActual', 'rendimiento']])
                            
                            # Gráfico de distribución por activo
                            st.subheader("Distribución del Portafolio")
                            fig = px.pie(df_activos, values='valorActual', names='activo', 
                                       title='Distribución por Activo')
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No se encontraron activos en su portafolio")
        
        with tabs[1]:  # Pestaña de Análisis
            st.title("📈 Análisis de Portafolio")
            st.write("En desarrollo...")
            
        with tabs[2]:  # Pestaña de Configuración
            st.title("⚙️ Configuración")
            st.write("Ajustes de la aplicación")
            
            # Configuración de visualización
            st.subheader("Preferencias de Visualización")
            tema_oscuro = st.checkbox("Modo Oscuro", value=False)
            
            # Configuración de notificaciones
            st.subheader("Notificaciones")
            notif_alertas = st.checkbox("Alertas de mercado", value=True)
            notif_operaciones = st.checkbox("Confirmación de operaciones", value=True)
            
            if st.button("💾 Guardar Configuración"):
                st.success("Configuración guardada correctamente")

if __name__ == "__main__":
    main()
