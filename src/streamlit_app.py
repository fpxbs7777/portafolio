```python
import streamlit as st
from streamlit.runtime.caching import cache_data, cache_resource, cache_resource_singleton
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
import hashlib
from typing import Dict, List, Tuple, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import os
from pathlib import Path
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CACHE_TTL = 3600  # 1 hour in seconds
HISTORICAL_DATA_DAYS = 365  # Default days for historical data
MAX_WORKERS = 5  # Max threads for concurrent API calls
CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True)

# Configure Streamlit
st.set_page_config(
    page_title="Portfolio Manager",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Disable warning about st.cache
st.set_option('deprecation.showfileUploaderEncoding', False)

# Performance optimization
st.cache_data.clear()
st.cache_resource.clear()

# Custom cache decorator with persistent storage
def persistent_cache(ttl: int = 3600, max_entries: int = 100):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a unique key for this function call
            key = f"{func.__name__}_{hashlib.md5((str(args) + str(kwargs)).encode()).hexdigest()}"
            cache_file = CACHE_DIR / f"{key}.pkl"
            
            # Check if we have a cached result
            if cache_file.exists():
                mtime = cache_file.stat().st_mtime
                if (time.time() - mtime) < ttl:
                    with open(cache_file, 'rb') as f:
                        return pickle.load(f)
            
            # If not, compute and cache the result
            result = func(*args, **kwargs)
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
            
            # Clean up old cache files if we have too many
            cache_files = sorted(CACHE_DIR.glob("*.pkl"), key=os.path.getmtime)
            for old_file in cache_files[:-max_entries]:
                try:
                    old_file.unlink()
                except:
                    pass
                    
            return result
        return wrapper
    return decorator

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
    # Load saved session if available
    if 'session_initialized' not in st.session_state:
        st.session_state.clear()
        
        # Try to load from local storage
        try:
            if os.path.exists('session_state.pkl'):
                with open('session_state.pkl', 'rb') as f:
                    saved_state = pickle.load(f)
                    st.session_state.update(saved_state)
                    # Verify token is still valid
                    if st.session_state.get('autenticado') and st.session_state.get('token_acceso'):
                        if not verificar_token_valido(st.session_state['token_acceso']):
                            st.session_state.update({
                                'autenticado': False,
                                'token_acceso': None,
                                'id_cliente': None
                            })
        except Exception as e:
            logger.warning(f"Error loading session: {e}")
        
        # Set default values for any missing keys
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
            'optimization_params': {},
            'cache_buster': 0  # Used to force updates
        }
        
        for key, value in default_state.items():
            if key not in st.session_state:
                st.session_state[key] = value
        
        st.session_state['session_initialized'] = True

    # Save session state periodically
    if 'last_save' not in st.session_state or (time.time() - st.session_state.get('last_save', 0)) > 300:  # Save every 5 minutes
        try:
            with open('session_state.pkl', 'wb') as f:
                save_state = {
                    k: v for k, v in st.session_state.items()
                    if k not in ['_last_runner', '_widget_state', '_session_state', 
                               '_handles', '_main_dg', '_script_run_ctx', 
                               'FormSubmitter:login_form-FormSubmitter']
                }
                pickle.dump(save_state, f)
                st.session_state['last_save'] = time.time()
        except Exception as e:
            logger.warning(f"Error saving session: {e}")

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

@persistent_cache(ttl=300)  # Cache for 5 minutes
def obtener_datos_portafolio(token: str, id_cliente: str) -> Dict:
    """Obtiene los datos del portafolio con manejo de caché y errores."""
    try:
        # Usar una clave única basada en los parámetros
        cache_key = f"portfolio_{id_cliente}_{st.session_state.get('cache_buster', 0)}"
        
        # Verificar caché en memoria primero
        if cache_key in st.session_state:
            return st.session_state[cache_key]
            
        # Si no está en caché, obtener los datos
        datos = obtener_portafolio(token, id_cliente)
        
        # Guardar en caché
        st.session_state[cache_key] = datos
        return datos
        
    except Exception as e:
        logger.error(f"Error al obtener datos del portafolio: {e}")
        return {}

def main() -> None:
    """Función principal de la aplicación."""
    # Inicializar el estado de la sesión
    inicializar_session_state()
    
    # Cargar estilos CSS optimizados
    load_css()
    
    # Manejar autenticación
    if not st.session_state.get('autenticado'):
        mostrar_panel_autenticacion()
        mostrar_pagina_principal()
        return
    
    # Usar columnas para mejorar el rendimiento de renderizado
    col1, col2 = st.columns([1, 4], gap="small")
    
    # Cargar menú de forma asíncrona
    with col1:
        with st.container():
            mostrar_menu_principal()
    
    # Cargar contenido principal con optimización de rendimiento
    with col2:
        with st.container():
            mostrar_contenido_pagina()
    
    # Inyectar JavaScript para mejoras de rendimiento
    st.components.v1.html("""
    <script>
    // Optimización de rendimiento
    document.addEventListener('DOMContentLoaded', () => {
        // Precargar recursos críticos
        const preloadLinks = [
            'https://cdn.plot.ly/plotly-latest.min.js',
            'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'
        ];
        
        preloadLinks.forEach(href => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = href.endsWith('.js') ? 'script' : 'style';
            link.href = href;
            document.head.appendChild(link);
        });
        
        // Mejorar rendimiento de animaciones
        if ('IntersectionObserver' in window) {
            const lazyImages = [].slice.call(document.querySelectorAll('img.lazy'));
            
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            lazyImages.forEach(img => imageObserver.observe(img));
        }
    });
    
    // Mantener viva la sesión de forma eficiente
    let keepAliveTimeout;
    const keepAlive = () => {
        if (document.visibilityState === 'visible') {
            fetch(window.location.href, {
                method: 'HEAD',
                cache: 'no-store',
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            }).catch(console.debug);
        }
        keepAliveTimeout = setTimeout(keepAlive, 4.5 * 60 * 1000);
    };
    
    // Iniciar keep-alive cuando la pestaña está activa
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            if (!keepAliveTimeout) keepAlive();
        } else {
            clearTimeout(keepAliveTimeout);
            keepAliveTimeout = null;
        }
    });
    
    // Iniciar keep-alive inicial
    keepAlive();
    </script>
    """)

if __name__ == "__main__":
    main()
