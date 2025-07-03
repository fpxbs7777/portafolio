```python
import streamlit as st
from streamlit.runtime.caching import cache_data, cache_resource
import requests
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
import functools
import time
from datetime import datetime, timedelta
from arch import arch_model
from scipy.stats import norm
import matplotlib.pyplot as plt
import yfinance as yf
import numpy as np
import json
from typing import Dict, List, Tuple, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CACHE_TTL = 3600  # 1 hour in seconds
HISTORICAL_DATA_DAYS = 365  # Default days for historical data
MAX_WORKERS = 5  # Max threads for concurrent API calls

# ... (rest of the code remains the same)

@cache_data(ttl=CACHE_TTL, show_spinner="Obteniendo datos del portafolio...")
def obtener_portafolio_cached(token_portador: str, id_cliente: str, pais: str = 'Argentina') -> Dict:
    """Obtiene y cachea el portafolio del usuario.
    
    Args:
        token_portador: Token de autenticación
        id_cliente: ID del cliente
        pais: País del portafolio (default: 'Argentina')
        
    Returns:
        Dict con los datos del portafolio
    """
    try:
        return obtener_portafolio(token_portador, id_cliente, pais)
    except Exception as e:
        logger.error(f"Error al obtener portafolio: {str(e)}")
        st.error("Error al cargar el portafolio. Por favor, intente nuevamente.")
        return {}

@cache_data(ttl=1800, show_spinner=False)  # Cache for 30 minutes
def obtener_serie_historica_cached(
    token_portador: str, 
    mercado: str, 
    simbolo: str, 
    fecha_desde: str, 
    fecha_hasta: str, 
    ajustada: str = "SinAjustar"
) -> pd.DataFrame:
    """Obtiene y cachea datos históricos con manejo de errores.
    
    Args:
        token_portador: Token de autenticación
        mercado: Mercado del activo
        simbolo: Símbolo del activo
        fecha_desde: Fecha de inicio (YYYY-MM-DD)
        fecha_hasta: Fecha de fin (YYYY-MM-DD)
        ajustada: Tipo de ajuste (default: "SinAjustar")
        
    Returns:
        DataFrame con los datos históricos
    """
    try:
        return obtener_serie_historica_iol(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada)
    except Exception as e:
        logger.error(f"Error al obtener serie histórica para {simbolo}: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error

def inicializar_session_state() -> None:
    """Inicializa las variables de sesión necesarias con valores por defecto."""
    default_state = {
        'autenticado': False,
        'token_acceso': None,
        'id_cliente': None,
        'fecha_desde': (datetime.now() - timedelta(days=HISTORICAL_DATA_DAYS)).strftime('%Y-%m-%d'),
        'fecha_hasta': datetime.now().strftime('%Y-%m-%d'),
        'ultima_pagina': 'inicio',
        'credenciales_guardadas': False,
        'portfolio_data': None,
        'last_updated': None,
        'optimization_params': {}
    }
    
    for key, value in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = value

def mostrar_panel_autenticacion() -> None:
    """Muestra el panel de autenticación en la barra lateral con manejo de sesión persistente."""
    st.sidebar.title("🔐 Autenticación")
    
    # Intento de autenticación automática con credenciales guardadas
    if not st.session_state.autenticado and st.session_state.credenciales_guardadas and st.session_state.token_acceso:
        with st.spinner("Restaurando sesión..."):
            try:
                # Verificar si el token sigue siendo válido
                if verificar_token_valido(st.session_state.token_acceso):
                    st.session_state.autenticado = True
                    st.experimental_rerun()
                else:
                    st.session_state.token_acceso = None
                    st.session_state.credenciales_guardadas = False
            except Exception as e:
                logger.warning(f"Error al verificar token: {str(e)}")
                st.session_state.token_acceso = None
                st.session_state.credenciales_guardadas = False
    
    # Mostrar botón de cierre de sesión si está autenticado
    if st.session_state.autenticado:
        if st.sidebar.button("Cerrar sesión", key="btn_cerrar_sesion"):
            # Limpiar solo los datos sensibles, mantener preferencias
            st.session_state.update({
                'autenticado': False,
                'token_acceso': None,
                'id_cliente': None,
                'portfolio_data': None,
                'last_updated': None
            })
            st.experimental_rerun()
        return
    
    # Mostrar formulario de inicio de sesión
    with st.sidebar.form("login_form"):
        st.subheader("Iniciar sesión")
        usuario = st.text_input("Usuario", key="input_usuario")
        contraseña = st.text_input("Contraseña", type="password", key="input_contrasena")
        recordar = st.checkbox("Recordar mis credenciales", value=True, key="chk_recordar")
        
        if st.form_submit_button("Iniciar sesión", type="primary"):
            with st.spinner("Verificando credenciales..."):
                try:
                    tokens = obtener_tokens(usuario, contraseña)
                    if tokens and 'access_token' in tokens:
                        st.session_state.update({
                            'token_acceso': tokens['access_token'],
                            'id_cliente': tokens.get('client_user_id'),
                            'autenticado': True,
                            'credenciales_guardadas': recordar,
                            'last_updated': datetime.now().isoformat()
                        })
                        st.experimental_rerun()
                    else:
                        st.sidebar.error("Error en la autenticación. Verifica tus credenciales.")
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error de autenticación: {error_msg}")
                    st.sidebar.error(f"Error al conectar con el servidor: {error_msg}")
                    st.session_state.credenciales_guardadas = False

def mostrar_configuracion_usuario():
    """Muestra la configuración del usuario una vez autenticado."""
    with st.sidebar:
        st.success("✅ Conectado a IOL")
        # ... (rest of the code remains the same)

@st.cache_resource(show_spinner=False)
def load_css() -> None:
    """Carga los estilos CSS personalizados."""
    st.markdown("""
    <style>
        /* Estilos generales */
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        
        /* Mejoras de rendimiento para elementos pesados */
        .stDataFrame, .element-container {
            will-change: transform;
        }
        
        /* Optimización de fuentes */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Roboto', sans-serif;
        }
    </style>
    """, unsafe_allow_html=True)

def verificar_token_valido(token: str) -> bool:
    """Verifica si un token de acceso es válido."""
    try:
        # Intenta hacer una solicitud que requiera autenticación
        response = requests.get(
            "https://api.invertironline.com/api/v2/estadocuenta",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.status_code == 200
    except Exception:
        return False

def main() -> None:
    """Función principal de la aplicación."""
    # Configuración de la página
    st.set_page_config(
        page_title="Portfolio Manager",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Cargar estilos CSS
    load_css()
    
    # Inicializar el estado de la sesión
    inicializar_session_state()
    
    # Mostrar el panel de autenticación
    mostrar_panel_autenticacion()
    
    # Si el usuario no está autenticado, mostrar solo la página de inicio
    if not st.session_state.autenticado:
        mostrar_pagina_principal()
        return
    
    # Si el usuario está autenticado, cargar los datos y mostrar la interfaz
    try:
        # Usar columnas para mejorar el layout
        col1, col2 = st.columns([1, 4])
        
        with col1:
            with st.spinner("Cargando menú..."):
                mostrar_menu_principal()
        
        with col2:
            # Usar un contenedor para el contenido principal
            with st.container():
                with st.spinner("Cargando contenido..."):
                    mostrar_contenido_pagina()
        
        # Añadir script para mantener viva la sesión y mejorar la experiencia
        st.components.v1.html("""
        <script>
        // Mantener viva la sesión con un ping periódico
        const keepAlive = () => {
            fetch(window.location.href, {method: 'HEAD'})
                .catch(err => console.debug('Keep-alive ping failed:', err));
        };
        
        // Ejecutar cada 4.5 minutos (menos que el timeout del servidor)
        setInterval(keepAlive, 4.5 * 60 * 1000);
        
        // Mejorar la experiencia de carga
        document.addEventListener('DOMContentLoaded', () => {
            // Mostrar indicador de carga suave
            const style = document.createElement('style');
            style.textContent = `
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .stApp > div {
                    animation: fadeIn 0.3s ease-out;
                }
            `;
            document.head.appendChild(style);
        });
        </script>
        """)
        
    except Exception as e:
        logger.error(f"Error en la aplicación principal: {str(e)}")
        st.error("Ocurrió un error inesperado. Por favor, recarga la página e inténtalo de nuevo.")
        if st.button("Recargar aplicación"):
            st.experimental_rerun()

if __name__ == "__main__":
    main()
