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
import time
import hashlib
import pickle
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

warnings.filterwarnings('ignore')

# Configuración de caché
CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_cache_key(func_name, *args, **kwargs):
    """Genera una clave única para el caché"""
    key_data = f"{func_name}_{str(args)}_{str(sorted(kwargs.items()))}"
    return hashlib.md5(key_data.encode()).hexdigest()

def load_from_cache(cache_key):
    """Carga datos desde el caché"""
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.pkl")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except:
            pass
    return None

def save_to_cache(cache_key, data):
    """Guarda datos en el caché"""
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.pkl")
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
    except:
        pass

# Configuración de Streamlit para mejor rendimiento
st.set_page_config(
    page_title="Análisis de Portafolio IOL",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de caché de Streamlit
@st.cache_data(ttl=3600)  # 1 hora de caché
def cached_api_call(url, headers, timeout=10):
    """Realiza llamadas API con caché"""
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None

# Configuración de sesión para datos persistentes
if 'cache_enabled' not in st.session_state:
    st.session_state.cache_enabled = True
if 'api_timeout' not in st.session_state:
    st.session_state.api_timeout = 15

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

def configurar_eje_fechas(fig, formato='%d/%m/%Y', angulo=45, nticks=10):
    """
    Configura el eje X de un gráfico para mostrar fechas reales.
    
    Args:
        fig: Figura de Plotly
        formato: Formato de fecha (default: '%d/%m/%Y')
        angulo: Ángulo de rotación de las etiquetas (default: 45)
        nticks: Número de ticks en el eje (default: 10)
    """
    fig.update_xaxes(
        type='date',
        tickformat=formato,
        tickangle=angulo,
        tickmode='auto',
        nticks=nticks
    )
    return fig

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

# --- FUNCIONES PARA GESTIÓN DE CLIENTES Y APERTURA DE CUENTA ---

def crear_usuario_sin_cuenta(token_portador, datos_usuario):
    """
    POST 1. Crear un usuario sin cuenta comitente en la plataforma IOL.
    """
    url = 'https://api.invertironline.com/api/v2/apertura-de-cuenta/registrar'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    try:
        # Validar datos requeridos
        campos_requeridos = ['nombre', 'apellido', 'dni', 'fechaNacimiento', 'sexo']
        for campo in campos_requeridos:
            if campo not in datos_usuario or not datos_usuario[campo]:
                st.error(f"❌ Campo requerido faltante: {campo}")
                return None
        
        # Validar formato de DNI
        dni = str(datos_usuario['dni']).strip()
        if not dni.isdigit() or len(dni) < 7 or len(dni) > 8:
            st.error("❌ DNI inválido. Debe ser un número de 7 u 8 dígitos")
            return None
        
        # Validar formato de fecha
        try:
            fecha = datos_usuario['fechaNacimiento']
            if isinstance(fecha, str):
                # Si es string, validar formato
                if not fecha.endswith('Z'):
                    datos_usuario['fechaNacimiento'] = fecha + 'T00:00:00Z'
        except Exception as e:
            st.error(f"❌ Formato de fecha inválido: {str(e)}")
            return None
        
        # Mostrar datos que se van a enviar (sin información sensible)
        st.info(f"📤 Enviando datos: {datos_usuario['nombre']} {datos_usuario['apellido']} - DNI: {dni[:3]}***{dni[-2:]}")
        
        respuesta = requests.post(url, headers=headers, json=datos_usuario, timeout=30)
        
        if respuesta.status_code == 200:
            resultado = respuesta.json()
            st.success("✅ Usuario creado exitosamente")
            return resultado
        elif respuesta.status_code == 400:
            try:
                error_data = respuesta.json()
                if 'message' in error_data:
                    st.error(f"❌ Error de validación: {error_data['message']}")
                elif 'errors' in error_data:
                    errores = error_data['errors']
                    st.error("❌ Errores de validación:")
                    for campo, mensaje in errores.items():
                        st.error(f"   - {campo}: {mensaje}")
                else:
                    st.error(f"❌ Error 400: {respuesta.text}")
            except:
                st.error(f"❌ Error 400: {respuesta.text}")
            return None
        elif respuesta.status_code == 401:
            st.error("❌ Error de autenticación. Verifique sus credenciales")
            return None
        elif respuesta.status_code == 403:
            st.error("❌ Error de autorización. No tiene permisos para crear usuarios")
            return None
        elif respuesta.status_code == 409:
            st.error("❌ Conflicto: El DNI ya existe en el sistema")
            return None
        elif respuesta.status_code == 500:
            st.error("❌ Error interno del servidor (500). Intente nuevamente en unos minutos")
            try:
                error_data = respuesta.json()
                if 'message' in error_data:
                    st.error(f"Detalle: {error_data['message']}")
            except:
                pass
            return None
        else:
            st.error(f"❌ Error HTTP {respuesta.status_code}: {respuesta.text}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("❌ Timeout: La solicitud tardó demasiado. Intente nuevamente")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Error de conexión: No se pudo conectar con el servidor")
        return None
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
        return None

def cargar_foto_dni_frontal(token_portador, id_cliente, archivo):
    """
    POST 2. Validar, extraer datos y guardar foto DNI frontal.
    """
    url = f'https://api.invertironline.com/api/v2/apertura-de-cuenta/dni-frontal-carga/{id_cliente}'
    headers = {
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'multipart/form-data'
    }
    
    try:
        files = {'imagen': archivo}
        respuesta = requests.post(url, headers=headers, files=files)
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            st.error(f"Error al cargar DNI frontal: {respuesta.status_code}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def cargar_foto_dni_dorsal(token_portador, id_cliente, archivo):
    """
    POST 3. Validar, extraer datos y guardar foto DNI dorsal.
    """
    url = f'https://api.invertironline.com/api/v2/apertura-de-cuenta/dni-dorsal-carga/{id_cliente}'
    headers = {
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'multipart/form-data'
    }
    
    try:
        files = {'imagen': archivo}
        respuesta = requests.post(url, headers=headers, files=files)
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            st.error(f"Error al cargar DNI dorsal: {respuesta.status_code}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def cargar_selfie_neutral(token_portador, id_cliente, archivo):
    """
    POST 4. Validar y guardar foto selfie neutral.
    """
    url = f'https://api.invertironline.com/api/v2/apertura-de-cuenta/selfie-neutral-carga/{id_cliente}'
    headers = {
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'multipart/form-data'
    }
    
    try:
        files = {'imagen': archivo}
        respuesta = requests.post(url, headers=headers, files=files)
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            st.error(f"Error al cargar selfie neutral: {respuesta.status_code}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def cargar_selfie_sonriente(token_portador, id_cliente, archivo):
    """
    POST 5. Validar y guardar foto selfie sonriente.
    """
    url = f'https://api.invertironline.com/api/v2/apertura-de-cuenta/selfie-sonriendo-carga/{id_cliente}'
    headers = {
        'Authorization': f'Bearer {token_portador}',
        'Content-Type': 'multipart/form-data'
    }
    
    try:
        files = {'imagen': archivo}
        respuesta = requests.post(url, headers=headers, files=files)
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            st.error(f"Error al cargar selfie sonriente: {respuesta.status_code}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def cargar_datos_manuales(token_portador, id_cliente, datos_personales):
    """
    POST 6. Carga datos personales esenciales que no se pudieron obtener del DNI.
    """
    url = f'https://api.invertironline.com/api/v2/apertura-de-cuenta/carga-manual-datos/{id_cliente}'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    try:
        respuesta = requests.post(url, headers=headers, json=datos_personales)
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            st.error(f"Error al cargar datos manuales: {respuesta.status_code}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def cargar_datos_adicionales(token_portador, id_cliente, datos_adicionales):
    """
    POST 7. Asociar datos personales y jurídicos de un cliente sin cuenta comitente.
    """
    url = f'https://api.invertironline.com/api/v2/apertura-de-cuenta/carga-datos-adicionales/{id_cliente}'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    try:
        respuesta = requests.post(url, headers=headers, json=datos_adicionales)
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            st.error(f"Error al cargar datos adicionales: {respuesta.status_code}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def aceptar_tyc(token_portador, id_cliente):
    """
    POST. Aceptar los términos y condiciones para el uso de APIs.
    """
    url = f'https://api.invertironline.com/api/v2/Asesores/tyc-apis/{id_cliente}/aceptar'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        respuesta = requests.post(url, headers=headers)
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            st.error(f"Error al aceptar TyC: {respuesta.status_code}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def verificar_estado_apertura(token_portador, id_cliente):
    """
    Verifica el estado actual del proceso de apertura de cuenta.
    """
    url = f'https://api.invertironline.com/api/v2/apertura-de-cuenta/estado/{id_cliente}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        respuesta = requests.get(url, headers=headers, timeout=15)
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            st.warning(f"⚠️ No se pudo verificar el estado: {respuesta.status_code}")
            return None
    except Exception as e:
        st.warning(f"⚠️ Error al verificar estado: {str(e)}")
        return None

def completar_apertura_cuenta(token_portador, id_cliente):
    """
    POST 8. Genera el número de cuenta comitente.
    """
    url = f'https://api.invertironline.com/api/v2/apertura-de-cuenta/completar-apertura/{id_cliente}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        # Validar que el ID del cliente sea válido
        if not id_cliente or id_cliente <= 0:
            st.error("❌ ID de cliente inválido")
            return None
        
        st.info(f"📤 Intentando completar apertura para cliente ID: {id_cliente}")
        
        respuesta = requests.post(url, headers=headers, timeout=30)
        
        if respuesta.status_code == 200:
            resultado = respuesta.json()
            st.success("✅ Apertura de cuenta completada exitosamente")
            return resultado
        elif respuesta.status_code == 400:
            try:
                error_data = respuesta.json()
                if 'message' in error_data:
                    st.error(f"❌ Error de validación: {error_data['message']}")
                elif 'errors' in error_data:
                    errores = error_data['errors']
                    st.error("❌ Errores de validación:")
                    for campo, mensaje in errores.items():
                        st.error(f"   - {campo}: {mensaje}")
                else:
                    st.error(f"❌ Error 400: {respuesta.text}")
            except:
                st.error(f"❌ Error 400: {respuesta.text}")
            
            # Proporcionar información específica sobre errores 400 comunes
            st.info("""
            **💡 Posibles causas del error 400:**
            - Faltan documentos obligatorios (DNI frontal/dorsal)
            - Faltan selfies obligatorias
            - Datos personales incompletos
            - TyC no aceptados
            - Cliente no existe o ID inválido
            - Proceso de apertura ya completado
            """)
            return None
        elif respuesta.status_code == 401:
            st.error("❌ Error de autenticación. Verifique sus credenciales")
            return None
        elif respuesta.status_code == 403:
            st.error("❌ Error de autorización. No tiene permisos para completar aperturas")
            return None
        elif respuesta.status_code == 404:
            st.error("❌ Cliente no encontrado. Verifique el ID del cliente")
            return None
        elif respuesta.status_code == 409:
            st.error("❌ Conflicto: La apertura de cuenta ya fue completada o está en proceso")
            return None
        elif respuesta.status_code == 500:
            st.error("❌ Error interno del servidor (500). Intente nuevamente en unos minutos")
            try:
                error_data = respuesta.json()
                if 'message' in error_data:
                    st.error(f"Detalle: {error_data['message']}")
            except:
                pass
            return None
        else:
            st.error(f"❌ Error HTTP {respuesta.status_code}: {respuesta.text}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("❌ Timeout: La solicitud tardó demasiado. Intente nuevamente")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Error de conexión: No se pudo conectar con el servidor")
        return None
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
        return None

def mostrar_gestion_clientes():
    """
    Interfaz para gestión de clientes y apertura de cuenta.
    """
    st.header("👥 Gestión de Clientes y Apertura de Cuenta")
    
    tab1, tab2, tab3 = st.tabs(["📋 Lista de Clientes", "➕ Alta de Cliente", "📊 Estado de Apertura"])
    
    with tab1:
        st.subheader("📋 Lista de Clientes")
        if st.button("🔄 Actualizar lista de clientes"):
            with st.spinner("Obteniendo clientes..."):
                clientes = obtener_lista_clientes(st.session_state.token_acceso)
                if clientes:
                    st.session_state.clientes = clientes
                    st.success(f"✅ Se encontraron {len(clientes)} clientes")
                else:
                    st.warning("No se encontraron clientes")
        
        if st.session_state.clientes:
            df_clientes = pd.DataFrame(st.session_state.clientes)
            st.dataframe(df_clientes, use_container_width=True)
        else:
            st.info("No hay clientes cargados")
    
    with tab2:
        st.subheader("➕ Alta de Cliente")
        
        # Información de ayuda
        with st.expander("ℹ️ Información sobre la creación de clientes"):
            st.markdown("""
            **📋 Campos Obligatorios:**
            - Nombre y Apellido
            - DNI (7 u 8 dígitos)
            - Fecha de Nacimiento
            - Sexo
            
            **⚠️ Consideraciones:**
            - El DNI debe ser único en el sistema
            - La fecha de nacimiento debe ser válida
            - Los datos se validan en tiempo real
            """)
        
        with st.form("alta_cliente"):
            st.write("**Datos Personales Básicos**")
            
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre *", placeholder="Ej: Juan")
            with col2:
                apellido = st.text_input("Apellido *", placeholder="Ej: Pérez")
            
            dni = st.text_input("DNI *", placeholder="Ej: 12345678", help="Debe ser un número de 7 u 8 dígitos")
            
            col1, col2 = st.columns(2)
            with col1:
                fecha_nacimiento = st.date_input("Fecha de Nacimiento *", 
                                               min_value=date(1900, 1, 1),
                                               max_value=date.today() - timedelta(days=6570),  # 18 años atrás
                                               help="Debe ser mayor de 18 años")
            with col2:
                sexo = st.selectbox("Sexo *", ["Masculino", "Femenino"])
            
            st.write("**Datos Adicionales (Opcionales)**")
            
            col1, col2 = st.columns(2)
            with col1:
                actividad_laboral = st.selectbox("Actividad Laboral", [
                    "Relacion_de_dependencia", "Monotributista", "Autonomo", "Desempleado", "Jubilado"
                ])
            with col2:
                cuil_cuit = st.text_input("CUIL/CUIT", placeholder="Ej: 20-12345678-9")
            
            st.write("**Domicilio (Opcional)**")
            col1, col2, col3 = st.columns(3)
            with col1:
                domicilio_calle = st.text_input("Calle")
            with col2:
                domicilio_numero = st.text_input("Número")
            with col3:
                codigo_postal = st.text_input("Código Postal")
            
            # Validaciones en tiempo real
            errores_validacion = []
            
            if nombre and len(nombre.strip()) < 2:
                errores_validacion.append("El nombre debe tener al menos 2 caracteres")
            
            if apellido and len(apellido.strip()) < 2:
                errores_validacion.append("El apellido debe tener al menos 2 caracteres")
            
            if dni:
                dni_limpio = dni.strip().replace(".", "").replace("-", "")
                if not dni_limpio.isdigit():
                    errores_validacion.append("El DNI debe contener solo números")
                elif len(dni_limpio) < 7 or len(dni_limpio) > 8:
                    errores_validacion.append("El DNI debe tener 7 u 8 dígitos")
            
            if fecha_nacimiento:
                edad = (date.today() - fecha_nacimiento).days / 365.25
                if edad < 18:
                    errores_validacion.append("El cliente debe ser mayor de 18 años")
            
            if errores_validacion:
                st.error("❌ Errores de validación:")
                for error in errores_validacion:
                    st.error(f"   - {error}")
            
            if st.form_submit_button("🚀 Crear Cliente", disabled=bool(errores_validacion)):
                if nombre and apellido and dni and fecha_nacimiento:
                    # Limpiar DNI
                    dni_limpio = dni.strip().replace(".", "").replace("-", "")
                    
                    datos_usuario = {
                        "nombre": nombre.strip(),
                        "apellido": apellido.strip(),
                        "dni": dni_limpio,
                        "fechaNacimiento": fecha_nacimiento.strftime("%Y-%m-%dT00:00:00Z"),
                        "sexo": sexo
                    }
                    
                    # Agregar datos opcionales si están presentes
                    if actividad_laboral:
                        datos_usuario["actividadLaboral"] = actividad_laboral
                    if cuil_cuit:
                        datos_usuario["cuilCuit"] = cuil_cuit.strip()
                    if domicilio_calle and domicilio_numero:
                        datos_usuario["domicilio"] = {
                            "calle": domicilio_calle.strip(),
                            "numero": domicilio_numero.strip(),
                            "codigoPostal": codigo_postal.strip() if codigo_postal else None
                        }
                    
                    with st.spinner("Creando cliente..."):
                        resultado = crear_usuario_sin_cuenta(st.session_state.token_acceso, datos_usuario)
                        if resultado:
                            if resultado.get('ok') or resultado.get('id'):
                                st.success("✅ Cliente creado exitosamente")
                                if resultado.get('id'):
                                    st.info(f"📋 ID del cliente: {resultado['id']}")
                                st.json(resultado)
                                
                                # Actualizar lista de clientes
                                st.session_state.clientes = obtener_lista_clientes(st.session_state.token_acceso)
                            else:
                                st.error("❌ Error al crear cliente")
                        else:
                            st.error("❌ Error al crear cliente")
                else:
                    st.warning("⚠️ Complete todos los campos obligatorios marcados con *")
    
    with tab3:
        st.subheader("📊 Estado de Apertura de Cuenta")
        
        # Información de ayuda
        with st.expander("ℹ️ Información sobre el proceso de apertura"):
            st.markdown("""
            **📋 Pasos para completar la apertura de cuenta:**
            1. **Cargar DNI Frontal** - Foto del frente del documento
            2. **Cargar DNI Dorsal** - Foto del dorso del documento  
            3. **Cargar Selfie Neutral** - Foto del rostro sin expresión
            4. **Cargar Selfie Sonriente** - Foto del rostro sonriendo
            5. **Cargar Datos Adicionales** - Información complementaria
            6. **Aceptar TyC** - Términos y condiciones
            7. **Completar Apertura** - Generar número de cuenta
            
            **⚠️ Requisitos de las fotos:**
            - Formato: JPG, PNG
            - Tamaño máximo: 5MB
            - Calidad: Buena resolución, sin reflejos
            - DNI: Completamente visible y legible
            - Selfies: Rostro bien iluminado y centrado
            """)
        
        # Selección de cliente
        if st.session_state.clientes:
            cliente_ids = [c.get('numeroCliente', c.get('id')) for c in st.session_state.clientes]
            cliente_nombres = [c.get('apellidoYNombre', c.get('nombre', 'Cliente')) for c in st.session_state.clientes]
            
            cliente_seleccionado = st.selectbox(
                "Seleccione un cliente:",
                options=cliente_ids,
                format_func=lambda x: cliente_nombres[cliente_ids.index(x)] if x in cliente_ids else "Cliente",
                key="cliente_apertura"
            )
            
            id_cliente = cliente_seleccionado
        else:
            id_cliente = st.number_input("ID del Cliente", min_value=1, step=1)
        
        if id_cliente:
            st.info(f"📋 Cliente seleccionado: ID {id_cliente}")
            
            # Estado actual del proceso
            st.markdown("### 📊 Estado del Proceso")
            
            # Simular estado del proceso (en una implementación real, esto vendría de la API)
            estado_proceso = {
                'dni_frontal': False,
                'dni_dorsal': False,
                'selfie_neutral': False,
                'selfie_sonriente': False,
                'datos_adicionales': False,
                'tyc_aceptados': False,
                'apertura_completada': False
            }
            
            # Mostrar estado actual
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                estado_icon = "✅" if estado_proceso['dni_frontal'] else "❌"
                st.metric("DNI Frontal", estado_icon)
            with col2:
                estado_icon = "✅" if estado_proceso['dni_dorsal'] else "❌"
                st.metric("DNI Dorsal", estado_icon)
            with col3:
                estado_icon = "✅" if estado_proceso['selfie_neutral'] else "❌"
                st.metric("Selfie Neutral", estado_icon)
            with col4:
                estado_icon = "✅" if estado_proceso['selfie_sonriente'] else "❌"
                st.metric("Selfie Sonriente", estado_icon)
            
            # Carga de fotos
            st.markdown("### 📸 Carga de Documentos")
            
            tab_fotos1, tab_fotos2, tab_fotos3, tab_fotos4 = st.tabs([
                "🆔 DNI Frontal", "🆔 DNI Dorsal", "😐 Selfie Neutral", "😊 Selfie Sonriente"
            ])
            
            with tab_fotos1:
                st.markdown("**🆔 Cargar DNI Frontal**")
                st.info("Suba una foto clara del frente del DNI")
                
                dni_frontal = st.file_uploader(
                    "Seleccionar foto DNI frontal",
                    type=['jpg', 'jpeg', 'png'],
                    key="dni_frontal_uploader"
                )
                
                if dni_frontal:
                    st.image(dni_frontal, caption="DNI Frontal", width=300)
                    
                    if st.button("📤 Subir DNI Frontal", key="btn_dni_frontal"):
                        with st.spinner("Subiendo DNI frontal..."):
                            resultado = cargar_foto_dni_frontal(st.session_state.token_acceso, id_cliente, dni_frontal)
                            if resultado:
                                st.success("✅ DNI frontal cargado exitosamente")
                                estado_proceso['dni_frontal'] = True
                            else:
                                st.error("❌ Error al cargar DNI frontal")
            
            with tab_fotos2:
                st.markdown("**🆔 Cargar DNI Dorsal**")
                st.info("Suba una foto clara del dorso del DNI")
                
                dni_dorsal = st.file_uploader(
                    "Seleccionar foto DNI dorsal",
                    type=['jpg', 'jpeg', 'png'],
                    key="dni_dorsal_uploader"
                )
                
                if dni_dorsal:
                    st.image(dni_dorsal, caption="DNI Dorsal", width=300)
                    
                    if st.button("📤 Subir DNI Dorsal", key="btn_dni_dorsal"):
                        with st.spinner("Subiendo DNI dorsal..."):
                            resultado = cargar_foto_dni_dorsal(st.session_state.token_acceso, id_cliente, dni_dorsal)
                            if resultado:
                                st.success("✅ DNI dorsal cargado exitosamente")
                                estado_proceso['dni_dorsal'] = True
                            else:
                                st.error("❌ Error al cargar DNI dorsal")
            
            with tab_fotos3:
                st.markdown("**😐 Cargar Selfie Neutral**")
                st.info("Suba una foto de su rostro sin expresión")
                
                selfie_neutral = st.file_uploader(
                    "Seleccionar selfie neutral",
                    type=['jpg', 'jpeg', 'png'],
                    key="selfie_neutral_uploader"
                )
                
                if selfie_neutral:
                    st.image(selfie_neutral, caption="Selfie Neutral", width=300)
                    
                    if st.button("📤 Subir Selfie Neutral", key="btn_selfie_neutral"):
                        with st.spinner("Subiendo selfie neutral..."):
                            resultado = cargar_selfie_neutral(st.session_state.token_acceso, id_cliente, selfie_neutral)
                            if resultado:
                                st.success("✅ Selfie neutral cargada exitosamente")
                                estado_proceso['selfie_neutral'] = True
                            else:
                                st.error("❌ Error al cargar selfie neutral")
            
            with tab_fotos4:
                st.markdown("**😊 Cargar Selfie Sonriente**")
                st.info("Suba una foto de su rostro sonriendo")
                
                selfie_sonriente = st.file_uploader(
                    "Seleccionar selfie sonriente",
                    type=['jpg', 'jpeg', 'png'],
                    key="selfie_sonriente_uploader"
                )
                
                if selfie_sonriente:
                    st.image(selfie_sonriente, caption="Selfie Sonriente", width=300)
                    
                    if st.button("📤 Subir Selfie Sonriente", key="btn_selfie_sonriente"):
                        with st.spinner("Subiendo selfie sonriente..."):
                            resultado = cargar_selfie_sonriente(st.session_state.token_acceso, id_cliente, selfie_sonriente)
                            if resultado:
                                st.success("✅ Selfie sonriente cargada exitosamente")
                                estado_proceso['selfie_sonriente'] = True
                            else:
                                st.error("❌ Error al cargar selfie sonriente")
            
            # Datos adicionales
            st.markdown("### 📝 Datos Adicionales")
            
            with st.expander("📋 Cargar Datos Adicionales"):
                with st.form("datos_adicionales_form"):
                    st.write("**Información Personal Adicional**")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        nacionalidad = st.text_input("Nacionalidad", value="Argentina")
                        estado_civil = st.selectbox("Estado Civil", [
                            "Soltero", "Casado", "Divorciado", "Viudo", "Concubinato"
                        ])
                    with col2:
                        ocupacion = st.text_input("Ocupación")
                        ingresos_mensuales = st.selectbox("Ingresos Mensuales", [
                            "Menos de $50.000", "$50.000 - $100.000", 
                            "$100.000 - $200.000", "$200.000 - $500.000",
                            "Más de $500.000"
                        ])
                    
                    st.write("**Información de Contacto**")
                    col1, col2 = st.columns(2)
                    with col1:
                        telefono = st.text_input("Teléfono")
                        email = st.text_input("Email")
                    with col2:
                        celular = st.text_input("Celular")
                        sitio_web = st.text_input("Sitio Web (opcional)")
                    
                    st.write("**Información Financiera**")
                    col1, col2 = st.columns(2)
                    with col1:
                        patrimonio_estimado = st.selectbox("Patrimonio Estimado", [
                            "Menos de $1.000.000", "$1.000.000 - $5.000.000",
                            "$5.000.000 - $10.000.000", "$10.000.000 - $50.000.000",
                            "Más de $50.000.000"
                        ])
                    with col2:
                        experiencia_inversion = st.selectbox("Experiencia en Inversiones", [
                            "Principiante", "Intermedio", "Avanzado", "Experto"
                        ])
                    
                    if st.form_submit_button("📤 Cargar Datos Adicionales"):
                        datos_adicionales = {
                            "nacionalidad": nacionalidad,
                            "estadoCivil": estado_civil,
                            "ocupacion": ocupacion,
                            "ingresosMensuales": ingresos_mensuales,
                            "telefono": telefono,
                            "email": email,
                            "celular": celular,
                            "sitioWeb": sitio_web,
                            "patrimonioEstimado": patrimonio_estimado,
                            "experienciaInversion": experiencia_inversion
                        }
                        
                        with st.spinner("Cargando datos adicionales..."):
                            resultado = cargar_datos_adicionales(st.session_state.token_acceso, id_cliente, datos_adicionales)
                            if resultado:
                                st.success("✅ Datos adicionales cargados exitosamente")
                                estado_proceso['datos_adicionales'] = True
                            else:
                                st.error("❌ Error al cargar datos adicionales")
            
            # Aceptar TyC
            st.markdown("### ✅ Términos y Condiciones")
            
            if st.button("📋 Aceptar Términos y Condiciones"):
                with st.spinner("Aceptando TyC..."):
                    resultado = aceptar_tyc(st.session_state.token_acceso, id_cliente)
                    if resultado:
                        st.success("✅ Términos y condiciones aceptados")
                        estado_proceso['tyc_aceptados'] = True
                    else:
                        st.error("❌ Error al aceptar TyC")
            
            # Completar apertura
            st.markdown("### 🚀 Completar Apertura de Cuenta")
            
            # Verificar estado real del proceso
            if st.button("🔍 Verificar Estado del Proceso", key="btn_verificar_estado"):
                with st.spinner("Verificando estado del proceso..."):
                    estado_real = verificar_estado_apertura(st.session_state.token_acceso, id_cliente)
                    if estado_real:
                        st.info("📊 Estado real del proceso:")
                        st.json(estado_real)
                        
                        # Actualizar estado_proceso basado en la respuesta real
                        if 'documentos' in estado_real:
                            docs = estado_real['documentos']
                            estado_proceso['dni_frontal'] = docs.get('dniFrontal', False)
                            estado_proceso['dni_dorsal'] = docs.get('dniDorsal', False)
                            estado_proceso['selfie_neutral'] = docs.get('selfieNeutral', False)
                            estado_proceso['selfie_sonriente'] = docs.get('selfieSonriente', False)
                        
                        if 'datosAdicionales' in estado_real:
                            estado_proceso['datos_adicionales'] = estado_real['datosAdicionales']
                        
                        if 'tycAceptados' in estado_real:
                            estado_proceso['tyc_aceptados'] = estado_real['tycAceptados']
                        
                        if 'aperturaCompletada' in estado_real:
                            estado_proceso['apertura_completada'] = estado_real['aperturaCompletada']
            
            # Verificar si todos los pasos están completos
            pasos_completos = all(estado_proceso.values())
            
            if pasos_completos:
                st.success("🎉 ¡Todos los pasos están completos! Puede proceder con la apertura de cuenta.")
                
                # Información adicional antes de completar
                with st.expander("ℹ️ Información antes de completar"):
                    st.markdown("""
                    **📋 Verificaciones finales:**
                    - ✅ Todos los documentos cargados
                    - ✅ Datos adicionales completados
                    - ✅ TyC aceptados
                    - ✅ Cliente válido y activo
                    
                    **⚠️ Importante:**
                    - Una vez completada la apertura, no se puede revertir
                    - El número de cuenta será generado automáticamente
                    - El cliente podrá operar inmediatamente
                    """)
                
                if st.button("✅ Completar Apertura de Cuenta", type="primary", key="btn_completar_final"):
                    with st.spinner("Completando apertura de cuenta..."):
                        resultado = completar_apertura_cuenta(st.session_state.token_acceso, id_cliente)
                        if resultado:
                            if resultado.get('numeroCuenta'):
                                st.success(f"🎉 ¡Cuenta creada exitosamente! Número de cuenta: {resultado['numeroCuenta']}")
                                estado_proceso['apertura_completada'] = True
                                
                                # Mostrar información adicional de la cuenta
                                with st.expander("📋 Detalles de la cuenta creada"):
                                    st.json(resultado)
                            else:
                                st.info("ℹ️ Proceso de apertura en curso. La cuenta será generada en breve.")
                                st.json(resultado)
                        else:
                            st.error("❌ Error al completar la apertura de cuenta")
                            
                            # Proporcionar ayuda adicional
                            st.info("""
                            **💡 Si el error persiste:**
                            1. Verifique que todos los documentos estén cargados correctamente
                            2. Asegúrese de que los TyC estén aceptados
                            3. Confirme que el cliente existe y está activo
                            4. Intente nuevamente en unos minutos
                            5. Contacte al soporte técnico si el problema persiste
                            """)
            else:
                pasos_faltantes = [paso for paso, completado in estado_proceso.items() if not completado]
                st.warning(f"⚠️ Faltan completar los siguientes pasos: {', '.join(pasos_faltantes)}")
                
                # Mostrar progreso
                progreso = sum(estado_proceso.values()) / len(estado_proceso) * 100
                st.progress(progreso / 100)
                st.info(f"📊 Progreso: {progreso:.1f}% completado")
                
                # Botón para verificar estado real
                if st.button("🔄 Verificar Estado Real", key="btn_verificar_real"):
                    with st.spinner("Verificando estado real..."):
                        estado_real = verificar_estado_apertura(st.session_state.token_acceso, id_cliente)
                        if estado_real:
                            st.info("📊 Estado real del proceso:")
                            st.json(estado_real)
                        else:
                            st.error("❌ No se pudo verificar el estado real del proceso")
        else:
            st.warning("⚠️ Seleccione un cliente para continuar")

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

def obtener_valor_fci_actual(token_portador, simbolo_fci):
    """
    Obtiene el valor actual de un Fondo Común de Inversión específico
    
    Args:
        token_portador (str): Token de autenticación
        simbolo_fci (str): Símbolo del FCI
        
    Returns:
        float: Valor de la cuota parte o None si no se puede obtener
    """
    try:
        # Intentar obtener el valor desde la API específica del FCI
        url_fci = f"https://api.invertironline.com/api/v2/Titulos/FCI/{simbolo_fci}/Cotizacion"
        headers = {'Authorization': f'Bearer {token_portador}'}
        response = requests.get(url_fci, headers=headers, timeout=10)
        
        if response.status_code == 200:
            fci_data = response.json()
            
            # Buscar el valor de cuota en diferentes campos posibles
            campos_valor = [
                'ultimoValorCuotaParte', 'valorCuotaParte', 'valorCuota', 
                'ultimoOperado', 'valorCuotaActual', 'ultimoValorCuota'
            ]
            
            for campo in campos_valor:
                if campo in fci_data and fci_data[campo] is not None:
                    try:
                        valor = float(fci_data[campo])
                        if valor > 0:
                            print(f"FCI {simbolo_fci}: Valor obtenido desde API[{campo}] = {valor}")
                            return valor
                    except (ValueError, TypeError):
                        continue
            
            print(f"FCI {simbolo_fci}: No se encontró valor válido en la respuesta API")
            return None
            
        else:
            print(f"FCI {simbolo_fci}: Error HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error obteniendo valor FCI {simbolo_fci}: {str(e)}")
        return None



@st.cache_data(ttl=1800)  # 30 minutos de caché
def obtener_serie_historica_iol(token_portador, mercado, simbolo, fecha_desde, fecha_hasta, ajustada="SinAjustar"):
    """
    Obtiene la serie histórica de precios para un activo específico desde la API de InvertirOnline.
    Versión optimizada con caché y mejor manejo de errores.
    
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
        # Endpoint para FCIs (manejo especial)
        if mercado.upper() == 'FCI':
            return obtener_serie_historica_fci(token_portador, simbolo, fecha_desde, fecha_hasta)
        
        # Construir URL según el tipo de activo y mercado
        url = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion/seriehistorica/{fecha_desde}/{fecha_hasta}/{ajustada}"
        
        headers = {
            'Authorization': f'Bearer {token_portador}',
            'Accept': 'application/json'
        }
        
        # Realizar la solicitud con timeout reducido
        timeout = st.session_state.get('api_timeout', 15)
        response = requests.get(url, headers=headers, timeout=timeout)
        
        # Verificar el estado de la respuesta
        if response.status_code != 200:
            return None
        
        # Procesar la respuesta
        data = response.json()
        
        # Procesar la respuesta según el formato esperado
        if isinstance(data, list) and data:
            # Formato estándar para series históricas
            fechas = []
            precios = []
            
            for item in data:
                try:
                    # Manejar diferentes formatos de fecha
                    fecha_str = item.get('fecha') or item.get('fechaHora')
                    if not fecha_str:
                        continue
                        
                    # Manejar diferentes formatos de precio
                    precio = item.get('ultimoPrecio') or item.get('precioCierre') or item.get('precio')
                    if precio is None:
                        continue
                        
                    # Convertir fecha
                    try:
                        fecha = parse_datetime_flexible(fecha_str)
                        if pd.isna(fecha):
                            continue
                            
                        precio_float = float(precio)
                        if precio_float <= 0:
                            continue
                            
                        fechas.append(fecha)
                        precios.append(precio_float)
                        
                    except (ValueError, TypeError):
                        continue
                        
                except Exception:
                    continue
            
            if fechas and precios:
                df = pd.DataFrame({'fecha': fechas, 'precio': precios})
                # Eliminar duplicados manteniendo el último
                df = df.drop_duplicates(subset=['fecha'], keep='last')
                df = df.sort_values('fecha')
                return df
                
        elif isinstance(data, dict):
            # Para respuestas que son un solo valor (ej: MEP)
            precio = data.get('ultimoPrecio') or data.get('precioCierre') or data.get('precio')
            if precio is not None:
                return pd.DataFrame({
                    'fecha': [pd.Timestamp.now(tz='UTC')],
                    'precio': [float(precio)]
                })
            
        return None
        
    except requests.exceptions.RequestException:
        return None
    except Exception:
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
        if self.timeseries is not None:
            for ric in self.rics:
                if ric in self.timeseries and self.timeseries[ric] is not None:
                    prices = self.timeseries[ric]
                    returns_matrix[ric] = np.log(prices / prices.shift(1)).dropna()
        
        # Convertir a DataFrame para alinear fechas
        self.returns = pd.DataFrame(returns_matrix)
        
        # Calcular matriz de covarianza y retornos medios
        if not self.returns.empty:
            self.cov_matrix = self.returns.cov() * 252  # Anualizar
            self.mean_returns = self.returns.mean() * 252  # Anualizar
        else:
            # Crear matrices por defecto si no hay datos
            n_assets = len(self.rics)
            self.cov_matrix = np.eye(n_assets) * 0.1  # Matriz de identidad con volatilidad del 10%
            self.mean_returns = pd.Series([0.05] * n_assets, index=self.rics)  # Retorno del 5%
        
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
        # Atributos para optimización avanzada
        self.returns_data = None
        self.cov_matrix = None
        self.rics = None
    
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
            
            # Obtener datos históricos en paralelo
            data_frames = {}
            
            def load_single_asset(simbolo, mercado):
                """Carga datos para un solo activo"""
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
                        return simbolo, df
                
                return simbolo, None
            
            # Cargar datos en paralelo
            with st.spinner("Obteniendo datos históricos en paralelo..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Usar ThreadPoolExecutor para carga paralela
                with ThreadPoolExecutor(max_workers=min(5, len(symbols))) as executor:
                    # Crear tareas para cada activo
                    future_to_symbol = {
                        executor.submit(load_single_asset, simbolo, mercado): simbolo 
                        for simbolo, mercado in zip(symbols, markets)
                    }
                    
                    completed = 0
                    for future in as_completed(future_to_symbol):
                        simbolo, df = future.result()
                        completed += 1
                        
                        # Actualizar progreso
                        progress = completed / len(symbols)
                        progress_bar.progress(progress)
                        status_text.text(f"Cargando... {completed}/{len(symbols)} activos")
                        
                        if df is not None:
                            data_frames[simbolo] = df
                        else:
                            st.warning(f"⚠️ No se pudieron obtener datos para {simbolo}")
                
                progress_bar.progress(1.0)
                status_text.text("✅ Carga completada")
            
            if not data_frames:
                st.error("❌ No se pudieron obtener datos históricos para ningún activo")
                return False
            
            # Combinar todos los DataFrames
            df_precios = pd.concat(data_frames.values(), axis=1, keys=data_frames.keys())
            
            # Limpiar datos
            # Primero verificar si hay fechas duplicadas
            if not df_precios.index.is_unique:
                st.warning("⚠️ Se encontraron fechas duplicadas en los datos")
                # Eliminar duplicados manteniendo el último valor de cada fecha
                df_precios = df_precios.groupby(df_precios.index).last()
            
            # Luego llenar y eliminar valores faltantes
            df_precios = df_precios.fillna(method='ffill')
            df_precios = df_precios.dropna()
            
            if df_precios.empty:
                st.error("❌ No hay datos suficientes después del preprocesamiento")
                return False
            
            # Calcular retornos
            self.returns = df_precios.pct_change().dropna()
            self.returns_data = self.returns  # Para optimización avanzada
            
            # Calcular estadísticas
            self.mean_returns = self.returns.mean()
            self.cov_matrix = self.returns.cov()
            self.rics = list(df_precios.columns)  # Lista de símbolos
            self.data_loaded = True
            
            # Crear manager para optimización avanzada
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
        if not self.data_loaded or not self.manager:
            return None, None, None
        
        try:
            if self.prices is not None:
                portfolios, returns, volatilities = compute_efficient_frontier(
                    self.manager.rics, self.notional, target_return, include_min_variance, 
                    self.prices.to_dict('series')
                )
            else:
                portfolios, returns, volatilities = None, None, None
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
            'riesgo_anual': 0,
            'alpha': 0,
            'beta': 0,
            'r_cuadrado': 0,
            'tracking_error': 0,
            'information_ratio': 0
        }
    else:
        print(f"\nMétricas calculadas para {len(metricas_activos)} activos")
    
    # 3. Calcular métricas del portafolio
    # Retorno esperado ponderado
    retorno_esperado_anual = sum(
        m['retorno_medio'] * m['peso'] 
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
                    m['volatilidad'] * m['peso'] 
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
            m['volatilidad'] * m['peso'] 
            for m in metricas_activos.values()
        ) if metricas_activos else 0.2
    
    # Calcular percentiles para escenarios
    retornos_simulados = []
    for _ in range(1000):  # Simulación Monte Carlo simple
        retorno_simulado = 0
        for m in metricas_activos.values():
            retorno_simulado += np.random.normal(m['retorno_medio']/252, m['volatilidad']/np.sqrt(252)) * m['peso']
        retornos_simulados.append(retorno_simulado * 252)  # Anualizado
    
    pl_esperado_min = np.percentile(retornos_simulados, 5) * valor_total / 100
    pl_esperado_max = np.percentile(retornos_simulados, 95) * valor_total / 100
    
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
            pesos_ordenados = [metricas_activos[col]['peso'] for col in df_port_returns.columns]
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
    
    # Asegurar que todas las claves necesarias estén presentes
    claves_requeridas = {
        'concentracion': 0,
        'std_dev_activo': 0,
        'retorno_esperado_anual': 0,
        'pl_esperado_min': 0,
        'pl_esperado_max': 0,
        'probabilidades': {'perdida': 0, 'ganancia': 0, 'perdida_mayor_10': 0, 'ganancia_mayor_10': 0},
        'riesgo_anual': 0,
        'alpha': 0,
        'beta': 0,
        'r_cuadrado': 0,
        'tracking_error': 0,
        'information_ratio': 0
    }
    
    # Asegurar que todas las claves estén presentes
    for clave, valor_por_defecto in claves_requeridas.items():
        if clave not in resultados:
            resultados[clave] = valor_por_defecto
    
    return resultados

def mostrar_analisis_portafolio():
    """Función para mostrar análisis detallado del portafolio"""
    st.markdown("### 📊 Análisis Detallado del Portafolio")
    
    # Verificar si hay un cliente seleccionado
    if not st.session_state.cliente_seleccionado:
        st.warning("👆 Seleccione un cliente en la barra lateral para comenzar")
        return
    
    token_portador = st.session_state.token_acceso
    id_cliente = st.session_state.cliente_seleccionado
    
    # Obtener datos del portafolio
    with st.spinner("Obteniendo datos del portafolio..."):
        portafolio = obtener_portafolio(token_portador, id_cliente)
    
    if not portafolio:
        st.error("❌ No se pudo obtener el portafolio del cliente")
        return
    
    activos_raw = portafolio.get('activos', [])
    if not activos_raw:
        st.warning("El portafolio está vacío")
        return
    
    # Convertir a formato esperado por las funciones
    datos_activos = []
    valor_total = 0
    
    for activo in activos_raw:
        titulo = activo.get('titulo', {})
        simbolo = titulo.get('simbolo', 'N/A')
        cantidad = activo.get('cantidad', 0)
        valorizado = activo.get('valorizado', 0)
        
        datos_activos.append({
            'Símbolo': simbolo,
            'Cantidad': cantidad,
            'Valuación': valorizado,
            'Tipo': titulo.get('tipo', 'Desconocido')
        })
        valor_total += valorizado
    
    if valor_total <= 0:
        st.warning("El portafolio no tiene valor")
        return
    
    # Configuración de análisis
    st.markdown("#### ⚙️ Configuración del Análisis")
    col1, col2 = st.columns(2)
    
    with col1:
        dias_analisis = st.selectbox(
            "Horizonte de análisis:",
            options=[30, 60, 90, 180, 365],
            index=2,  # 90 días por defecto
            help="Período de días para el análisis histórico"
        )
    
    with col2:
        st.metric("Valor Total del Portafolio", f"${valor_total:,.2f}")
    
    # Análisis detallado
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
                                # st.success(f"✅ {simbolo}: {len(serie)} puntos de datos")
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
                        
                        if not fechas_comunes:
                            st.warning("⚠️ No hay fechas comunes entre las series históricas")
                            return
                        
                        # Convertir a lista ordenada
                        fechas_comunes = sorted(list(fechas_comunes))
                        df_portfolio.index = fechas_comunes
                        
                        for activo_info in activos_exitosos:
                            simbolo = activo_info['simbolo']
                            peso = activo_info['peso']
                            serie = activo_info['serie']
                            
                            # Encontrar la valuación real del activo en el portafolio
                            valuacion_activo = 0
                            for activo_original in datos_activos:
                                if activo_original['Símbolo'] == simbolo:
                                    valuacion_activo = float(activo_original['Valuación'])
                                    break
                            
                            # Filtrar la serie para usar solo las fechas comunes
                            serie_filtrada = serie.loc[fechas_comunes]
                            
                            # Agregar serie ponderada al DataFrame
                            # Usar la valuación real del activo y aplicar el retorno histórico
                            if 'precio' in serie_filtrada.columns:
                                # Calcular retornos históricos del activo
                                precios = serie_filtrada['precio'].values
                                if len(precios) > 1:
                                    # Calcular retornos acumulados desde el primer precio
                                    retornos_acumulados = precios / precios[0]
                                    # Aplicar retornos a la valuación actual
                                    df_portfolio[simbolo] = valuacion_activo * retornos_acumulados
                                else:
                                    # Si solo hay un precio, usar la valuación actual
                                    df_portfolio[simbolo] = valuacion_activo
                            else:
                                # Si no hay columna 'precio', intentar con la primera columna numérica
                                columnas_numericas = serie_filtrada.select_dtypes(include=[np.number]).columns
                                if len(columnas_numericas) > 0:
                                    precios = serie_filtrada[columnas_numericas[0]].values
                                    if len(precios) > 1:
                                        # Calcular retornos acumulados desde el primer precio
                                        retornos_acumulados = precios / precios[0]
                                        # Aplicar retornos a la valuación actual
                                        df_portfolio[simbolo] = valuacion_activo * retornos_acumulados
                                    else:
                                        # Si solo hay un precio, usar la valuación actual
                                        df_portfolio[simbolo] = valuacion_activo
                                else:
                                    st.warning(f"⚠️ No se encontraron valores numéricos para {simbolo}")
                                    continue
                        
                        # Calcular valor total del portafolio por fecha
                        df_portfolio['Portfolio_Total'] = df_portfolio.sum(axis=1)
                        
                        # Mostrar información de debug
                        # st.info(f"🔍 Debug: Valor total actual del portafolio: ${valor_total:,.2f}")
                        # st.info(f"🔍 Debug: Columnas en df_portfolio: {list(df_portfolio.columns)}")
                        # if len(df_portfolio) > 0:
                        #     st.info(f"🔍 Debug: Último valor calculado: ${df_portfolio['Portfolio_Total'].iloc[-1]:,.2f}")
                        
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
                            
                            fig_evolucion = go.Figure()
                            fig_evolucion.add_trace(go.Scatter(
                                x=df_portfolio.index,
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
                            
                            # Configurar eje X para mostrar fechas reales
                            fig_evolucion = configurar_eje_fechas(fig_evolucion)
                            
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
                                    )
                                    
                                    # Configurar eje X para mostrar fechas reales
                                    fig_evolucion_real = configurar_eje_fechas(fig_evolucion_real)
                                    fig_evolucion_real.update_layout(
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
                                        es_renta_fija = False
                                        
                                        # Primero verificar si es claramente una acción
                                        tipo_lower = tipo.lower()
                                        simbolo_lower = simbolo.lower()
                                        
                                        # Lista de acciones comunes en Argentina
                                        acciones_comunes = [
                                            'alua', 'ypf', 'ggal', 'pamp', 'tenaris', 'acro', 'bma', 'loma', 'txar', 'cresud',
                                            'mirgor', 'siderar', 'petrobras', 'banco macro', 'banco galicia', 'banco santander',
                                            'banco itau', 'banco hsbc', 'banco nacion', 'banco provincia', 'banco ciudad',
                                            'despegar', 'mercadolibre', 'globant', 'despegar', 'tgs', 'pampa energia',
                                            'central puerto', 'edesur', 'edenor', 'metrogas', 'transportadora gas del norte',
                                            'transportadora gas del sur', 'camuzzi gas', 'metrogas', 'edenor', 'edelap'
                                        ]
                                        
                                        # Si es claramente una acción, no es renta fija
                                        if any(accion in simbolo_lower for accion in acciones_comunes):
                                            es_renta_fija = False
                                        elif any(accion in tipo_lower for accion in ['accion', 'stock', 'equity', 'share']):
                                            es_renta_fija = False
                                        else:
                                            # Verificar si es renta fija específicamente
                                            if any(keyword in tipo_lower for keyword in ['fci', 'fondo', 'bono', 'titulo', 'publico', 'letra', 'caucion']):
                                                es_renta_fija = True
                                            elif any(keyword in simbolo_lower for keyword in ['fci', 'fondo', 'bono', 'al', 'gd', 'gg', 'adba', 'prcp', 'caucion']):
                                                es_renta_fija = True
                                            elif 'descripcion' in activo:
                                                descripcion = activo['descripcion'].lower()
                                                if any(keyword in descripcion for keyword in ['fondo', 'fci', 'bono', 'caucion']):
                                                    if not any(accion in descripcion for accion in ['accion', 'stock', 'equity', 'empresa']):
                                                        es_renta_fija = True
                                        
                                        if es_renta_fija:
                                            instrumentos_renta_fija.append({
                                                'simbolo': simbolo,
                                                'tipo': tipo,
                                                'valuacion': valuacion,
                                                'peso': valuacion / valor_total if valor_total > 0 else 0
                                            })
                                            total_renta_fija += valuacion
                                            print(f"Renta fija identificada: {simbolo} ({tipo}) - Valuación: ${valuacion:,.2f}")
                                        else:
                                            print(f"NO es renta fija: {simbolo} ({tipo}) - Valuación: ${valuacion:,.2f}")
                                    
                                    if instrumentos_renta_fija:
                                        st.success(f"✅ Se identificaron {len(instrumentos_renta_fija)} instrumentos de renta fija")
                                        
                                        # Mostrar información detallada de cada instrumento
                                        st.markdown("#### 📋 Detalle de Instrumentos de Renta Fija")
                                        
                                        for instrumento in instrumentos_renta_fija:
                                            simbolo = instrumento['simbolo']
                                            tipo = instrumento['tipo']
                                            valuacion = instrumento['valuacion']
                                            peso = instrumento['peso']
                                            
                                            # Obtener información adicional si es un FCI
                                            if 'fci' in tipo.lower() or 'fondo' in tipo.lower():
                                                valor_actual = obtener_valor_fci_actual(token_portador, simbolo)
                                                if valor_actual:
                                                    st.info(f"**{simbolo}** ({tipo}): ${valuacion:,.2f} - Valor cuota actual: ${valor_actual:.4f}")
                                                else:
                                                    st.warning(f"**{simbolo}** ({tipo}): ${valuacion:,.2f} - No se pudo obtener valor actual")
                                            else:
                                                st.info(f"**{simbolo}** ({tipo}): ${valuacion:,.2f}")
                                            
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
                                        
                                        # Botón para recalcular valuación de FCIs
                                        if st.button("🔄 Recalcular Valuación de FCIs", type="secondary"):
                                            st.info("Recalculando valuación de FCIs...")
                                            total_renta_fija_actualizado = 0
                                            
                                            for instrumento in instrumentos_renta_fija:
                                                simbolo = instrumento['simbolo']
                                                tipo = instrumento['tipo']
                                                
                                                if 'fci' in tipo.lower() or 'fondo' in tipo.lower():
                                                    # Obtener valor actual del FCI
                                                    valor_actual = obtener_valor_fci_actual(token_portador, simbolo)
                                                    if valor_actual:
                                                        # Buscar la cantidad en los datos originales
                                                        cantidad = 0
                                                        for activo in datos_activos:
                                                            if activo['Símbolo'] == simbolo:
                                                                cantidad = float(activo['Cantidad'])
                                                                break
                                                        
                                                        if cantidad > 0:
                                                            valuacion_actualizada = cantidad * valor_actual
                                                            instrumento['valuacion'] = valuacion_actualizada
                                                            total_renta_fija_actualizado += valuacion_actualizada
                                                            st.success(f"✅ {simbolo}: ${valuacion_actualizada:,.2f} (valor actualizado)")
                                                        else:
                                                            total_renta_fija_actualizado += instrumento['valuacion']
                                                    else:
                                                        total_renta_fija_actualizado += instrumento['valuacion']
                                                        st.warning(f"⚠️ {simbolo}: No se pudo obtener valor actual")
                                                else:
                                                    total_renta_fija_actualizado += instrumento['valuacion']
                                            
                                            # Actualizar total de renta fija
                                            total_renta_fija = total_renta_fija_actualizado
                                            peso_renta_fija = total_renta_fija / valor_total if valor_total > 0 else 0
                                            st.success(f"✅ Valuación actualizada: ${total_renta_fija:,.2f}")
                                        
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
                                        
                                        # Mostrar desglose detallado de FCIs
                                        if st.checkbox("📊 Mostrar desglose detallado de FCIs"):
                                            st.markdown("#### 📋 Desglose Detallado de FCIs")
                                            
                                            fcis_detalle = []
                                            for instrumento in instrumentos_renta_fija:
                                                if 'fci' in instrumento['tipo'].lower() or 'fondo' in instrumento['tipo'].lower():
                                                    simbolo = instrumento['simbolo']
                                                    tipo = instrumento['tipo']
                                                    valuacion = instrumento['valuacion']
                                                    
                                                    # Obtener cantidad y valor actual
                                                    cantidad = 0
                                                    for activo in datos_activos:
                                                        if activo['Símbolo'] == simbolo:
                                                            cantidad = float(activo['Cantidad'])
                                                            break
                                                    
                                                    valor_actual = obtener_valor_fci_actual(token_portador, simbolo)
                                                    
                                                    fcis_detalle.append({
                                                        'Símbolo': simbolo,
                                                        'Tipo': tipo,
                                                        'Cantidad': f"{cantidad:,.2f}",
                                                        'Valor Cuota': f"${valor_actual:.4f}" if valor_actual else "N/A",
                                                        'Valuación': f"${valuacion:,.2f}",
                                                        'Peso (%)': f"{instrumento['peso']*100:.1f}%"
                                                    })
                                            
                                            if fcis_detalle:
                                                df_fcis = pd.DataFrame(fcis_detalle)
                                                st.dataframe(df_fcis, use_container_width=True, height=300)
                                            else:
                                                st.info("No se encontraron FCIs en el portafolio")
                                        
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
                                    
                                    # --- NUEVO: Inputs para Monte Carlo ---
                                    st.markdown("#### 📈 Métricas de Retorno Esperado")
                                    col_mc1, col_mc2 = st.columns(2)
                                    with col_mc1:
                                        n_simulaciones = st.number_input(
                                            "Cantidad de simulaciones Monte Carlo",
                                            min_value=1000, max_value=20000, value=5000, step=1000,
                                            help="Cantidad de escenarios simulados para las proyecciones"
                                        )
                                    with col_mc2:
                                        nivel_confianza = st.slider(
                                            "Nivel de confianza (%)",
                                            min_value=90, max_value=99, value=95, step=1,
                                            help="Intervalo de confianza para las proyecciones"
                                        )
                                    
                                    # --- NUEVO: Inputs para volatilidad y métricas de mercado ---
                                    col_mc3, col_mc4 = st.columns(2)
                                    with col_mc3:
                                        ventana_volatilidad = st.number_input(
                                            "Ventana volatilidad histórica (días)",
                                            min_value=10, max_value=100, value=30, step=5,
                                            help="Período para calcular volatilidad histórica móvil"
                                        )
                                    with col_mc4:
                                        incluir_metricas_mercado = st.checkbox(
                                            "Incluir métricas de mercado",
                                            value=True,
                                            help="Usar volumen, monto operado y spread para ajustar predicciones"
                                        )
                                    
                                    # --- Simulación Monte Carlo mejorada ---
                                    if 'Portfolio_Total' in df_portfolio.columns:
                                        valores_portfolio = df_portfolio['Portfolio_Total'].values
                                        retornos_portfolio = pd.Series(valores_portfolio).pct_change().dropna()
                                        mean_return = retornos_portfolio.mean()
                                        valor_actual = valores_portfolio[-1]
                                        n_sim = int(n_simulaciones)
                                        conf = nivel_confianza / 100
                                        
                                        # --- NUEVO: Funciones para Monte Carlo mejorado ---
                                        def calcular_volatilidad_esperada(retornos_historicos, ventana=30):
                                            """Calcula volatilidad esperada usando ventana móvil histórica"""
                                            if len(retornos_historicos) < ventana:
                                                return retornos_historicos.std()
                                            
                                            volatilidad_historica = retornos_historicos.rolling(window=ventana).std()
                                            vol_actual = volatilidad_historica.iloc[-1]
                                            
                                            # Predicción: tendencia + componente estocástico
                                            if len(volatilidad_historica.dropna()) > 1:
                                                tendencia_vol = volatilidad_historica.diff().mean()
                                                vol_esperada = vol_actual * (1 + tendencia_vol + np.random.normal(0, 0.1))
                                            else:
                                                vol_esperada = vol_actual * (1 + np.random.normal(0, 0.1))
                                            
                                            return max(vol_esperada, vol_actual * 0.5)  # Límite mínimo
                                        
                                        def obtener_metricas_mercado_activo(token_portador, simbolo, mercado):
                                            """Obtiene métricas de mercado para un activo usando la API correcta de IOL"""
                                            try:
                                                # Determinar el endpoint correcto basado en el símbolo y mercado
                                                if mercado.upper() == 'FCI':
                                                    # Para fondos comunes de inversión
                                                    url_mercado = f"https://api.invertironline.com/api/v2/Titulos/FCI"
                                                    # Buscar el FCI específico en la lista
                                                    headers = {'Authorization': f'Bearer {token_portador}'}
                                                    response = requests.get(url_mercado, headers=headers, timeout=10)
                                                    if response.status_code == 200:
                                                        fci_list = response.json()
                                                        fci_data = next((fci for fci in fci_list if fci.get('simbolo') == simbolo), None)
                                                        if fci_data:
                                                            ultimo_precio = fci_data.get('ultimoOperado', 0)
                                                            volumen = fci_data.get('volumen', 0)
                                                            return {
                                                                'volumen': volumen,
                                                                'monto_operado': volumen * ultimo_precio if ultimo_precio > 0 else 0,
                                                                'spread': 0.001,  # Spread típico para FCIs
                                                                'liquidez': 0.9,  # Alta liquidez para FCIs
                                                                'ultimo_precio': ultimo_precio,
                                                                'apertura': ultimo_precio,
                                                                'maximo': ultimo_precio,
                                                                'minimo': ultimo_precio
                                                            }
                                                elif mercado.upper() in ['NYSE', 'NASDAQ', 'AMEX']:
                                                    # Para acciones estadounidenses
                                                    url_mercado = f"https://api.invertironline.com/api/v2/{mercado}/Titulos/{simbolo}/Cotizacion"
                                                elif mercado.upper() == 'BCBA':
                                                    # Para acciones argentinas
                                                    url_mercado = f"https://api.invertironline.com/api/v2/BCBA/Titulos/{simbolo}/Cotizacion"
                                                elif mercado.upper() == 'BONOS':
                                                    # Para bonos argentinos
                                                    url_mercado = f"https://api.invertironline.com/api/v2/Bonos/Titulos/{simbolo}/Cotizacion"
                                                else:
                                                    # Intentar con BCBA como fallback
                                                    url_mercado = f"https://api.invertironline.com/api/v2/BCBA/Titulos/{simbolo}/Cotizacion"
                                                
                                                headers = {'Authorization': f'Bearer {token_portador}'}
                                                response = requests.get(url_mercado, headers=headers, timeout=10)
                                                
                                                if response.status_code == 200:
                                                    data = response.json()
                                                    
                                                    # Manejar diferentes estructuras de respuesta
                                                    if isinstance(data, list) and len(data) > 0:
                                                        # Si es una lista, tomar el primer elemento
                                                        data = data[0]
                                                    
                                                    # Asegurarse de que data es un diccionario
                                                    if isinstance(data, dict):
                                                        # Extraer métricas según la estructura de respuesta de IOL
                                                        volumen = data.get('volumen', 0)
                                                        ultimo_precio = data.get('ultimoPrecio', data.get('ultimoOperado', 0))
                                                        apertura = data.get('apertura', ultimo_precio)
                                                        maximo = data.get('maximo', ultimo_precio)
                                                        minimo = data.get('minimo', ultimo_precio)
                                                        
                                                        # Calcular spread aproximado si hay puntas
                                                        spread = 0.01  # Spread por defecto
                                                        if 'puntas' in data:
                                                            puntas = data['puntas']
                                                            if isinstance(puntas, dict):
                                                                precio_compra = puntas.get('precioCompra', 0)
                                                                precio_venta = puntas.get('precioVenta', 0)
                                                                if precio_compra > 0 and precio_venta > 0:
                                                                    spread = (precio_venta - precio_compra) / precio_compra
                                                    
                                                    # Calcular liquidez basada en volumen y precio
                                                    liquidez = 0.8  # Liquidez por defecto
                                                    if ultimo_precio > 0 and volumen > 0:
                                                        # Liquidez basada en volumen relativo al precio
                                                        liquidez = min(volumen / (ultimo_precio * 1000), 1.0)
                                                    
                                                    # Asegurar que los valores sean números válidos
                                                    volumen_val = float(volumen) if volumen is not None else 0
                                                    ultimo_precio_val = float(ultimo_precio) if ultimo_precio is not None and ultimo_precio > 0 else 0
                                                    
                                                    return {
                                                        'volumen': volumen_val,
                                                        'monto_operado': volumen_val * ultimo_precio_val,
                                                        'spread': spread,
                                                        'liquidez': liquidez,
                                                        'ultimo_precio': ultimo_precio_val,
                                                        'apertura': apertura,
                                                        'maximo': maximo,
                                                        'minimo': minimo
                                                    }
                                                else:
                                                    print(f"Error HTTP {response.status_code} para {simbolo} en {mercado}")
                                                    
                                            except Exception as e:
                                                print(f"Error obteniendo métricas para {simbolo} en {mercado}: {str(e)}")
                                            
                                            # Valores por defecto si no se pueden obtener
                                            return {
                                                'volumen': 1000000,
                                                'monto_operado': 500000,
                                                'spread': 0.01,
                                                'liquidez': 0.8,
                                                'ultimo_precio': 0,
                                                'apertura': 0,
                                                'maximo': 0,
                                                'minimo': 0
                                            }
                                        
                                        def calcular_factor_liquidez(metricas_mercado):
                                            """Ajusta retorno esperado basado en liquidez"""
                                            liquidez = metricas_mercado.get('liquidez', 1)
                                            volumen = metricas_mercado.get('volumen', 0)
                                            
                                            # Menor liquidez = mayor riesgo = mayor retorno esperado
                                            factor_volumen = min(volumen / 1000000, 2)  # Normalizar volumen
                                            factor_liquidez = 1 + (1 - liquidez) * 0.2  # Ajuste del 20%
                                            
                                            return factor_volumen * factor_liquidez
                                        
                                        def calcular_volatilidad_ajustada(vol_base, metricas_mercado):
                                            """Ajusta volatilidad por spread y volumen"""
                                            spread = metricas_mercado.get('spread', 0)
                                            volumen = metricas_mercado.get('volumen', 0)
                                            
                                            # Mayor spread = mayor volatilidad
                                            factor_spread = 1 + spread * 10  # Ajuste por spread
                                            factor_volumen = 1 + (1 - min(volumen / 1000000, 1)) * 0.3  # Menor volumen = mayor vol
                                            
                                            return vol_base * factor_spread * factor_volumen
                                        
                                        # --- Simulación Monte Carlo mejorada ---
                                        simulaciones = []
                                        
                                        # Obtener métricas de mercado si está habilitado
                                        metricas_mercado_totales = {}
                                        if incluir_metricas_mercado:
                                            with st.spinner("Obteniendo métricas de mercado..."):
                                                for activo_info in activos_exitosos:
                                                    simbolo = activo_info['simbolo']
                                                    # Determinar mercado basado en el símbolo y tipo de activo
                                                    mercado = 'BCBA'  # Default
                                                    tipo_activo = activo_info.get('tipo', '').lower()
                                                    
                                                    # Detectar mercado por símbolo primero
                                                    simbolo_upper = simbolo.upper()
                                                    if any(keyword in simbolo_upper for keyword in ['GOOGL', 'INTC', 'NVDA', 'AAPL', 'MSFT', 'AMZN', 'TSLA']):
                                                        mercado = 'NYSE'  # Acciones estadounidenses conocidas
                                                    elif any(keyword in simbolo_upper for keyword in ['FCI', 'FONDO', 'ADBA', 'PRCP']):
                                                        mercado = 'FCI'  # Fondos comunes
                                                    elif any(keyword in simbolo_upper for keyword in ['AL', 'GD', 'GG', 'BONO']):
                                                        mercado = 'BONOS'  # Bonos argentinos
                                                    elif any(keyword in tipo_activo for keyword in ['nyse', 'nasdaq', 'amex']):
                                                        mercado = 'NYSE'  # Para acciones estadounidenses
                                                    elif any(keyword in tipo_activo for keyword in ['fci', 'fondo']):
                                                        mercado = 'FCI'  # Para fondos comunes
                                                    elif any(keyword in tipo_activo for keyword in ['bono', 'titulo']):
                                                        mercado = 'BONOS'  # Para bonos
                                                    
                                                    # Intentar obtener métricas con el mercado detectado
                                                    metricas = obtener_metricas_mercado_activo(token_portador, simbolo, mercado)
                                                    
                                                    # Si no hay datos, intentar con BCBA como fallback
                                                    if metricas['ultimo_precio'] == 0 and mercado != 'BCBA':
                                                        print(f"Reintentando {simbolo} con BCBA...")
                                                        metricas = obtener_metricas_mercado_activo(token_portador, simbolo, 'BCBA')
                                                    
                                                    metricas_mercado_totales[simbolo] = metricas
                                                    
                                                    # Mostrar progreso
                                                    if metricas['ultimo_precio'] > 0:
                                                        st.success(f"✅ {simbolo} ({mercado}): ${metricas['ultimo_precio']:.2f} - Vol: {metricas['volumen']:,.0f}")
                                                    else:
                                                        st.warning(f"⚠️ {simbolo} ({mercado}): Sin datos de mercado")
                                        
                                        for _ in range(n_sim):
                                            # 1. Calcular volatilidad esperada
                                            vol_esperada = calcular_volatilidad_esperada(retornos_portfolio, ventana_volatilidad)
                                            
                                            # 2. Ajustar por métricas de mercado si está habilitado
                                            if incluir_metricas_mercado and metricas_mercado_totales:
                                                # Promedio ponderado de métricas de mercado
                                                metricas_promedio = {
                                                    'volumen': np.mean([m['volumen'] for m in metricas_mercado_totales.values()]),
                                                    'miquidez': np.mean([m['liquidez'] for m in metricas_mercado_totales.values()]),
                                                    'spread': np.mean([m['spread'] for m in metricas_mercado_totales.values()])
                                                }
                                                
                                                factor_liquidez = calcular_factor_liquidez(metricas_promedio)
                                                vol_ajustada = calcular_volatilidad_ajustada(vol_esperada, metricas_promedio)
                                                
                                                mean_return_ajustado = mean_return * factor_liquidez
                                                vol_final = vol_ajustada
                                            else:
                                                mean_return_ajustado = mean_return
                                                vol_final = vol_esperada
                                            
                                            # 3. Simular trayectoria con parámetros ajustados
                                            retorno_sim = np.random.normal(mean_return_ajustado, vol_final, dias_analisis)
                                            retorno_acum = np.prod(1 + retorno_sim) - 1
                                            simulaciones.append(retorno_acum)
                                        
                                        simulaciones = np.array(simulaciones)
                                        
                                        # Métricas basadas en Monte Carlo mejorado
                                        retorno_esperado_mc = np.mean(simulaciones)
                                        retorno_anualizado_ars = retorno_esperado_mc * (365 / dias_analisis)
                                        mean_return_annual_usd = df_portfolio_returns_usd.mean() * 252
                                        retorno_esperado_horizonte_ars = retorno_esperado_mc
                                        retorno_esperado_horizonte_usd = mean_return_annual_usd * (dias_analisis / 365)
                                        
                                        # Intervalos de confianza basados en Monte Carlo
                                        percentil_inferior = np.percentile(simulaciones, (1 - conf) * 100)
                                        percentil_superior = np.percentile(simulaciones, conf * 100)
                                        intervalo_confianza_ars = (percentil_superior - percentil_inferior) / 2
                                        intervalo_confianza_usd = intervalo_confianza_ars  # Aproximado
                                        
                                        # Mostrar métricas
                                        col1, col2, col3, col4 = st.columns(4)
                                        col1.metric("Retorno Esperado Anual (ARS)", f"{retorno_anualizado_ars:.2%}")
                                        col2.metric("Retorno Esperado Anual (USD)", f"{mean_return_annual_usd:.2%}")
                                        col3.metric(f"Retorno Esperado ({dias_analisis} días) ARS", f"{retorno_esperado_horizonte_ars:.2%}")
                                        col4.metric(f"Retorno Esperado ({dias_analisis} días) USD", f"{retorno_esperado_horizonte_usd:.2%}")
                                        
                                        col1, col2 = st.columns(2)
                                        col1.metric(f"Intervalo de Confianza {nivel_confianza}% (ARS)", f"±{intervalo_confianza_ars:.2%}")
                                        col2.metric(f"Intervalo de Confianza {nivel_confianza}% (USD)", f"±{intervalo_confianza_usd:.2%}")
                                        
                                        # Proyecciones de valor del portafolio basadas en Monte Carlo mejorado
                                        st.markdown("#### 💰 Proyecciones de Valor del Portafolio")
                                        
                                        # Calcular proyecciones usando percentiles de Monte Carlo
                                        proyeccion_esperada = valor_actual * (1 + retorno_esperado_mc)
                                        proyeccion_optimista = valor_actual * (1 + percentil_superior)
                                        proyeccion_pesimista = valor_actual * (1 + percentil_inferior)
                                        
                                        col1, col2, col3 = st.columns(3)
                                        col1.metric("Proyección Esperada", f"${proyeccion_esperada:,.2f}")
                                        col2.metric("Proyección Optimista", f"${proyeccion_optimista:,.2f}")
                                        col3.metric("Proyección Pesimista", f"${proyeccion_pesimista:,.2f}")
                                        
                                        # --- NUEVO: Mostrar información de métricas de mercado ---
                                        if incluir_metricas_mercado and metricas_mercado_totales:
                                            st.markdown("#### 📊 Métricas de Mercado Utilizadas")
                                            
                                            # Calcular métricas agregadas
                                            metricas_promedio = {
                                                'volumen': np.mean([m['volumen'] for m in metricas_mercado_totales.values()]),
                                                'liquidez': np.mean([m['liquidez'] for m in metricas_mercado_totales.values()]),
                                                'spread': np.mean([m['spread'] for m in metricas_mercado_totales.values()]),
                                                'monto_operado': np.mean([m['monto_operado'] for m in metricas_mercado_totales.values()]),
                                                'ultimo_precio': np.mean([m['ultimo_precio'] for m in metricas_mercado_totales.values()])
                                            }
                                            
                                            # Mostrar métricas principales
                                            col1, col2, col3, col4 = st.columns(4)
                                            col1.metric("Volumen Promedio", f"${metricas_promedio['volumen']:,.0f}")
                                            col2.metric("Monto Operado Promedio", f"${metricas_promedio['monto_operado']:,.0f}")
                                            col3.metric("Precio Promedio", f"${metricas_promedio['ultimo_precio']:.2f}")
                                            col4.metric("Activos Analizados", len(metricas_mercado_totales))
                                            
                                            col1, col2, col3 = st.columns(3)
                                            col1.metric("Liquidez Promedio", f"{metricas_promedio['liquidez']:.2f}")
                                            col2.metric("Spread Promedio", f"{metricas_promedio['spread']:.4f}")
                                            col3.metric("Activos con Datos", sum(1 for m in metricas_mercado_totales.values() if m['ultimo_precio'] > 0))
                                            
                                            # Mostrar tabla detallada de métricas por activo
                                            st.markdown("#### 📋 Detalle de Métricas por Activo")
                                            metricas_detalle = []
                                            for simbolo, metricas in metricas_mercado_totales.items():
                                                metricas_detalle.append({
                                                    'Símbolo': simbolo,
                                                    'Precio': f"${metricas['ultimo_precio']:.2f}" if metricas['ultimo_precio'] > 0 else "N/A",
                                                    'Volumen': f"{metricas['volumen']:,.0f}",
                                                    'Monto Operado': f"${metricas['monto_operado']:,.0f}",
                                                    'Spread': f"{metricas['spread']:.4f}",
                                                    'Liquidez': f"{metricas['liquidez']:.2f}"
                                                })
                                            
                                            if metricas_detalle:
                                                df_metricas = pd.DataFrame(metricas_detalle)
                                                st.dataframe(df_metricas, use_container_width=True, height=200)
                                    

                                    
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
                                
            except Exception as e:
                st.error(f"❌ Error general en el análisis del portafolio: {str(e)}")
                st.exception(e)

def mostrar_optimizacion_portafolio(token_acceso, id_cliente):
    st.markdown("### 🔄 Optimización de Portafolio")
    
    # Configuración de pestañas
    tab1, tab2 = st.tabs(["🎯 Optimización Individual", "🔄 Selección Aleatoria"])
    
    with tab1:
        st.markdown("#### 🎯 Optimización de Portafolio Individual")
        
        with st.spinner("Obteniendo portafolio..."):
            portafolio = obtener_portafolio(token_acceso, id_cliente)
        
        if not portafolio:
            st.warning("No se pudo obtener el portafolio del cliente")
            return
        
        activos_raw = portafolio.get('activos', [])
        if not activos_raw:
            st.warning("El portafolio está vacío")
            return
        
        # Extraer símbolos, mercados y tipos de activo
        activos_para_optimizacion = []
        for activo in activos_raw:
            titulo = activo.get('titulo', {})
            simbolo = titulo.get('simbolo')
            mercado = titulo.get('mercado')
            tipo = titulo.get('tipo')
            if simbolo:
                activos_para_optimizacion.append({'simbolo': simbolo,
                                                  'mercado': mercado,
                                                  'tipo': tipo})
        
        if not activos_para_optimizacion:
            st.warning("No se encontraron activos con información de mercado válida para optimizar.")
            return
        
        fecha_desde = st.session_state.fecha_desde
        fecha_hasta = st.session_state.fecha_hasta
        
        st.info(f"Analizando {len(activos_para_optimizacion)} activos desde {fecha_desde} hasta {fecha_hasta}")
        
        # Configuración de optimización extendida
        col1, col2, col3 = st.columns(3)
        
        with col1:
            metodo_optimizacion = st.selectbox(
                "Método de Optimización:",
                options=['Markowitz (Frontera Eficiente)', 'Mínima Varianza', 'Máximo Sharpe', 'L1 (Lasso)', 'L2 (Ridge)', 'Pesos Iguales'],
                help="Seleccione el método de optimización a aplicar"
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
            ejecutar_optimizacion = st.button("🚀 Ejecutar Optimización", type="primary")
        with col2:
            ejecutar_frontier = st.button("📈 Calcular Frontera Eficiente")
    
    if ejecutar_optimizacion:
        with st.spinner("Ejecutando optimización..."):
            try:
                # Crear manager de portafolio con la lista de activos (símbolo y mercado)
                manager_inst = PortfolioManager(activos_para_optimizacion, token_acceso, fecha_desde, fecha_hasta)
                
                # Cargar datos
                if manager_inst.load_data():
                    # Computar optimización con método avanzado
                    use_target = target_return if metodo_optimizacion == 'Markowitz (Frontera Eficiente)' else None
                    
                    # Usar el método de optimización avanzado
                    if metodo_optimizacion in ['Markowitz (Frontera Eficiente)', 'Mínima Varianza', 'Máximo Sharpe', 'L1 (Lasso)', 'L2 (Ridge)', 'Pesos Iguales']:
                        # Obtener datos de retornos
                        returns_data = manager_inst.returns_data
                        cov_matrix = manager_inst.cov_matrix
                        
                        if returns_data is not None and cov_matrix is not None:
                            # Aplicar optimización avanzada
                            # Función de optimización avanzada
                            def optimizar_portafolio_avanzado(returns_data, cov_matrix, metodo, target_return=None):
                                """Optimización avanzada de portafolio"""
                                try:
                                    if metodo == 'Markowitz (Frontera Eficiente)':
                                        if target_return is not None:
                                            # Optimización con retorno objetivo
                                            constraints = [
                                                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Pesos suman 1
                                                {'type': 'eq', 'fun': lambda x: np.sum(returns_data.mean() * x) - target_return}  # Retorno objetivo
                                            ]
                                        else:
                                            constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
                                        
                                        # Minimizar varianza
                                        result = op.minimize(
                                            lambda x: np.sqrt(np.dot(x.T, np.dot(cov_matrix, x))),
                                            x0=np.array([1/len(returns_data.columns)] * len(returns_data.columns)),
                                            method='SLSQP',
                                            bounds=[(0, 1)] * len(returns_data.columns),
                                            constraints=constraints
                                        )
                                        return result.x
                                    
                                    elif metodo == 'Mínima Varianza':
                                        constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
                                        result = op.minimize(
                                            lambda x: np.sqrt(np.dot(x.T, np.dot(cov_matrix, x))),
                                            x0=np.array([1/len(returns_data.columns)] * len(returns_data.columns)),
                                            method='SLSQP',
                                            bounds=[(0, 1)] * len(returns_data.columns),
                                            constraints=constraints
                                        )
                                        return result.x
                                    
                                    elif metodo == 'Máximo Sharpe':
                                        # Maximizar ratio de Sharpe
                                        risk_free_rate = 0.02  # 2% anual
                                        def neg_sharpe_ratio(weights):
                                            portfolio_return = np.sum(returns_data.mean() * weights)
                                            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                                            return -(portfolio_return - risk_free_rate) / portfolio_vol
                                        
                                        constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
                                        result = op.minimize(
                                            neg_sharpe_ratio,
                                            x0=np.array([1/len(returns_data.columns)] * len(returns_data.columns)),
                                            method='SLSQP',
                                            bounds=[(0, 1)] * len(returns_data.columns),
                                            constraints=constraints
                                        )
                                        return result.x
                                    
                                    elif metodo == 'Pesos Iguales':
                                        return np.array([1/len(returns_data.columns)] * len(returns_data.columns))
                                    
                                    else:
                                        # Fallback a pesos iguales
                                        return np.array([1/len(returns_data.columns)] * len(returns_data.columns))
                                        
                                except Exception as e:
                                    st.error(f"Error en optimización: {str(e)}")
                                    return np.array([1/len(returns_data.columns)] * len(returns_data.columns))
                            
                            # Función para calcular métricas del portafolio optimizado
                            def calcular_metricas_portafolio_optimizado(weights, returns_data, cov_matrix):
                                """Calcula métricas del portafolio optimizado"""
                                try:
                                    portfolio_returns = np.sum(returns_data * weights, axis=1)
                                    
                                    mean_return = portfolio_returns.mean() * 252
                                    volatility = portfolio_returns.std() * np.sqrt(252)
                                    sharpe_ratio = mean_return / volatility if volatility > 0 else 0
                                    
                                    # Métricas de riesgo
                                    var_95 = np.percentile(portfolio_returns, 5)
                                    skewness = stats.skew(portfolio_returns)
                                    kurtosis = stats.kurtosis(portfolio_returns)
                                    
                                    # Test de Jarque-Bera
                                    jb_statistic, jb_p_value = stats.jarque_bera(portfolio_returns)
                                    is_normal = jb_p_value > 0.05
                                    
                                    return {
                                        'mean_return': mean_return,
                                        'volatility': volatility,
                                        'sharpe_ratio': sharpe_ratio,
                                        'var_95': var_95,
                                        'skewness': skewness,
                                        'kurtosis': kurtosis,
                                        'jb_statistic': jb_statistic,
                                        'is_normal': is_normal,
                                        'returns': portfolio_returns
                                    }
                                except Exception as e:
                                    st.error(f"Error calculando métricas: {str(e)}")
                                    return {
                                        'mean_return': 0,
                                        'volatility': 0,
                                        'sharpe_ratio': 0,
                                        'var_95': 0,
                                        'skewness': 0,
                                        'kurtosis': 0,
                                        'jb_statistic': 0,
                                        'is_normal': False,
                                        'returns': None
                                    }
                            
                            weights = optimizar_portafolio_avanzado(
                                returns_data, cov_matrix, metodo_optimizacion, 
                                target_return=use_target
                            )
                            
                            # Calcular métricas del portafolio optimizado
                            metricas = calcular_metricas_portafolio_optimizado(
                                weights, returns_data, cov_matrix
                            )
                            
                            st.success("✅ Optimización completada")
                            
                            # Mostrar resultados
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### 📊 Pesos Optimizados")
                                if hasattr(manager_inst, 'rics'):
                                    weights_df = pd.DataFrame({
                                        'Activo': manager_inst.rics,
                                        'Peso (%)': weights * 100
                                    })
                                    weights_df = weights_df.sort_values('Peso (%)', ascending=False)
                                    st.dataframe(weights_df, use_container_width=True)
                            
                            with col2:
                                st.markdown("#### 📈 Métricas del Portafolio")
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.metric("Retorno Anual", f"{metricas['mean_return']:.2%}")
                                    st.metric("Volatilidad Anual", f"{metricas['volatility']:.2%}")
                                    st.metric("Ratio de Sharpe", f"{metricas['sharpe_ratio']:.4f}")
                                    st.metric("VaR 95%", f"{metricas['var_95']:.4f}")
                                with col_b:
                                    st.metric("Skewness", f"{metricas['skewness']:.4f}")
                                    st.metric("Kurtosis", f"{metricas['kurtosis']:.4f}")
                                    st.metric("JB Statistic", f"{metricas['jb_statistic']:.4f}")
                                    normalidad = "✅ Normal" if metricas['is_normal'] else "❌ No Normal"
                                    st.metric("Normalidad", normalidad)
                            
                            # Gráfico de distribución de retornos
                            if metricas['returns'] is not None:
                                st.markdown("#### 📊 Distribución de Retornos del Portafolio Optimizado")
                                fig = go.Figure()
                                fig.add_histogram(x=metricas['returns'], nbinsx=30)
                                fig.update_layout(
                                    title="Distribución de Retornos del Portafolio Optimizado",
                                    xaxis_title="Retorno",
                                    yaxis_title="Frecuencia",
                                    template='plotly_white'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Gráfico de pesos
                            if hasattr(manager_inst, 'rics'):
                                st.markdown("#### 🥧 Distribución de Pesos")
                                fig_pie = go.Figure(data=[go.Pie(
                                    labels=manager_inst.rics,
                                    values=weights,
                                    textinfo='label+percent',
                                    hole=0.4,
                                    marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3'])
                                )])
                                fig_pie.update_layout(
                                    title="Distribución Optimizada de Activos",
                                    template='plotly_white'
                                )
                                st.plotly_chart(fig_pie, use_container_width=True)
                        else:
                            st.error("❌ No se pudieron obtener los datos de retornos")
                    else:
                        # Usar método original como fallback
                        portfolio_result = manager_inst.compute_portfolio(strategy='markowitz', target_return=use_target)
                        if portfolio_result:
                            st.success("✅ Optimización completada (método original)")
                            # Mostrar resultados básicos...
                        else:
                            st.error("❌ Error en la optimización")
                else:
                    st.error("❌ No se pudieron cargar los datos históricos")
                    
            except Exception as e:
                st.error(f"❌ Error durante la optimización: {str(e)}")
    
    if ejecutar_frontier and show_frontier:
        with st.spinner("Calculando frontera eficiente..."):
            try:
                manager_inst = PortfolioManager(activos_para_optimizacion, token_acceso, fecha_desde, fecha_hasta)
                
                if manager_inst.load_data():
                    portfolios, returns, volatilities = manager_inst.compute_efficient_frontier(
                        target_return=target_return, include_min_variance=True
                    )
                    
                    if portfolios and returns and volatilities:
                        st.success("✅ Frontera eficiente calculada")
                        
                        # Crear gráfico de frontera eficiente
                        fig = go.Figure()
                        
                        # Línea de frontera eficiente
                        fig.add_trace(go.Scatter(
                            x=volatilities, y=returns,
                            mode='lines+markers',
                            name='Frontera Eficiente',
                            line=dict(color='#0d6efd', width=3),
                            marker=dict(size=6)
                        ))
                        
                        # Portafolios especiales
                        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
                        labels = ['Min Var L1', 'Min Var L2', 'Pesos Iguales', 'Solo Largos', 'Markowitz', 'Markowitz Target']
                        
                        for i, (label, portfolio) in enumerate(portfolios.items()):
                            if portfolio is not None:
                                fig.add_trace(go.Scatter(
                                    x=[portfolio.volatility_annual], 
                                    y=[portfolio.return_annual],
                                    mode='markers',
                                    name=labels[i] if i < len(labels) else label,
                                    marker=dict(size=12, color=colors[i % len(colors)])
                                ))
                        
                        fig.update_layout(
                            title='Frontera Eficiente del Portafolio',
                            xaxis_title='Volatilidad Anual',
                            yaxis_title='Retorno Anual',
                            showlegend=True,
                            template='plotly_white',
                            height=500
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Tabla comparativa de portafolios
                        st.markdown("#### 📊 Comparación de Estrategias")
                        comparison_data = []
                        for label, portfolio in portfolios.items():
                            if portfolio is not None:
                                comparison_data.append({
                                    'Estrategia': label,
                                    'Retorno Anual': f"{portfolio.return_annual:.2%}",
                                    'Volatilidad Anual': f"{portfolio.volatility_annual:.2%}",
                                    'Sharpe Ratio': f"{portfolio.sharpe_ratio:.4f}",
                                    'VaR 95%': f"{portfolio.var_95:.4f}",
                                    'Skewness': f"{portfolio.skewness:.4f}",
                                    'Kurtosis': f"{portfolio.kurtosis:.4f}"
                                })
                        
                        if comparison_data:
                            df_comparison = pd.DataFrame(comparison_data)
                            st.dataframe(df_comparison, use_container_width=True)
                    
                    else:
                        st.error("❌ No se pudo calcular la frontera eficiente")
                else:
                    st.error("❌ No se pudieron cargar los datos históricos")
                    
            except Exception as e:
                st.error(f"❌ Error calculando frontera eficiente: {str(e)}")
    
    # Información adicional extendida
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
    
    with tab2:
        st.markdown("#### 🔄 Selección Aleatoria de Activos")
        
        # Obtener portafolio actual
        with st.spinner("Obteniendo portafolio actual..."):
            portafolio_actual = obtener_portafolio(token_acceso, id_cliente)
        
        if not portafolio_actual:
            st.warning("No se pudo obtener el portafolio del cliente")
            return
        
        activos_raw = portafolio_actual.get('activos', [])
        if not activos_raw:
            st.warning("El portafolio está vacío")
            return
        
        # Mostrar información del portafolio actual
        st.info(f"📊 Portafolio actual: {len(activos_raw)} activos")
        
        # Configuración de selección aleatoria
        col1, col2 = st.columns(2)
        
        with col1:
            cantidad_activos = st.number_input(
                "Cantidad de activos a seleccionar:",
                min_value=2, max_value=len(activos_raw), value=min(5, len(activos_raw)),
                help="Número de activos a incluir en el portafolio optimizado"
            )
            
            metodo_optimizacion_aleatoria = st.selectbox(
                "Método de optimización:",
                options=['Markowitz (Frontera Eficiente)', 'Mínima Varianza', 'Máximo Sharpe', 'Pesos Iguales'],
                help="Método de optimización para los activos seleccionados"
            )
        
        with col2:
            saldo_objetivo = st.number_input(
                "Saldo objetivo para rebalanceo (ARS):",
                min_value=1000, value=100000, step=1000,
                help="Saldo objetivo para el rebalanceo del portafolio"
            )
            
            incluir_saldo_disponible = st.checkbox(
                "Incluir saldo disponible en el análisis",
                value=True,
                help="Considerar el saldo disponible como parte del portafolio"
            )
        
        # Mostrar resumen del portafolio actual
        col1, col2, col3 = st.columns(3)
        
        valor_total_portafolio = sum(activo.get('valorizado', 0) for activo in activos_raw)
        cantidad_activos_total = len(activos_raw)
        
        with col1:
            st.metric("Valor Total del Portafolio", f"${valor_total_portafolio:,.2f}")
        with col2:
            st.metric("Cantidad de Activos", cantidad_activos_total)
        with col3:
            st.metric("Saldo Objetivo", f"${saldo_objetivo:,.2f}")
        
        # Mostrar activos disponibles
        with st.expander("📋 Activos disponibles en el portafolio"):
            activos_info = []
            for activo in activos_raw:
                titulo = activo.get('titulo', {})
                simbolo = titulo.get('simbolo', 'N/A')
                tipo = titulo.get('tipo', 'N/A')
                valor = activo.get('valorizado', 0)
                cantidad = activo.get('cantidad', 0)
                
                # Calcular peso en el portafolio
                peso = (valor / valor_total_portafolio * 100) if valor_total_portafolio > 0 else 0
                
                activos_info.append({
                    'Símbolo': simbolo,
                    'Tipo': tipo,
                    'Cantidad': cantidad,
                    'Valor (ARS)': f"${valor:,.2f}" if valor > 0 else "N/A",
                    'Peso (%)': f"{peso:.1f}%"
                })
            
            df_activos = pd.DataFrame(activos_info)
            st.dataframe(df_activos, use_container_width=True)
        
        # Botón para ejecutar selección aleatoria
        ejecutar_seleccion_aleatoria = st.button("🎲 Ejecutar Selección Aleatoria", type="primary")
        
        if ejecutar_seleccion_aleatoria:
            # Mostrar progreso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔄 Seleccionando activos aleatoriamente...")
                progress_bar.progress(25)
                
                # Función para seleccionar activos aleatorios del portafolio
                def seleccionar_activos_aleatorios_del_portafolio(portafolio_actual, cantidad_activos, saldo_objetivo):
                    """Selecciona activos aleatorios del portafolio actual"""
                    try:
                        activos_disponibles = []
                        for activo in portafolio_actual:
                            titulo = activo.get('titulo', {})
                            simbolo = titulo.get('simbolo')
                            mercado = titulo.get('mercado', 'BCBA')
                            tipo = titulo.get('tipo', 'Desconocido')
                            
                            if simbolo and simbolo != 'N/A':
                                activos_disponibles.append({
                                    'simbolo': simbolo,
                                    'mercado': mercado,
                                    'tipo': tipo
                                })
                        
                        if len(activos_disponibles) == 0:
                            return []
                        
                        # Seleccionar aleatoriamente
                        cantidad_seleccionar = min(cantidad_activos, len(activos_disponibles))
                        activos_seleccionados = random.sample(activos_disponibles, cantidad_seleccionar)
                        
                        return activos_seleccionados
                    except Exception as e:
                        st.error(f"Error seleccionando activos: {str(e)}")
                        return []
                
                # Seleccionar activos aleatoriamente del portafolio existente
                activos_para_optimizacion = seleccionar_activos_aleatorios_del_portafolio(
                    portafolio_actual, cantidad_activos, saldo_objetivo
                )
                
                progress_bar.progress(50)
                status_text.text("📊 Cargando datos históricos...")
                
                if activos_para_optimizacion:
                    progress_bar.progress(75)
                    status_text.text("🎯 Optimizando portafolio...")
                    
                    st.success(f"✅ Seleccionados {len(activos_para_optimizacion)} activos aleatoriamente")
                    
                    # Mostrar activos seleccionados
                    st.markdown("#### 📋 Activos Seleccionados Aleatoriamente")
                    activos_seleccionados_info = []
                    for activo in activos_para_optimizacion:
                        activos_seleccionados_info.append({
                            'Símbolo': activo['simbolo'],
                            'Mercado': activo['mercado'],
                            'Tipo': activo['tipo']
                        })
                    
                    df_seleccionados = pd.DataFrame(activos_seleccionados_info)
                    st.dataframe(df_seleccionados, use_container_width=True)
                    
                    # Optimizar portafolio con activos seleccionados
                    manager_inst = PortfolioManager(activos_para_optimizacion, token_acceso, 
                                                 st.session_state.fecha_desde, st.session_state.fecha_hasta)
                    
                    if manager_inst.load_data():
                        progress_bar.progress(90)
                        status_text.text("📈 Calculando métricas...")
                        # Aplicar optimización
                        weights = optimizar_portafolio_avanzado(
                            manager_inst.returns_data, manager_inst.cov_matrix, 
                            metodo_optimizacion_aleatoria
                        )
                        
                        metricas = calcular_metricas_portafolio_optimizado(
                            weights, manager_inst.returns_data, manager_inst.cov_matrix
                        )
                        
                        # Mostrar resultados
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 📊 Pesos del Portafolio Optimizado")
                            if hasattr(manager_inst, 'rics'):
                                weights_df = pd.DataFrame({
                                    'Activo': manager_inst.rics,
                                    'Peso (%)': weights * 100
                                })
                                weights_df = weights_df.sort_values('Peso (%)', ascending=False)
                                st.dataframe(weights_df, use_container_width=True)
                        
                        with col2:
                            st.markdown("#### 📈 Métricas del Portafolio")
                            st.metric("Retorno Anual", f"{metricas['mean_return']:.2%}")
                            st.metric("Volatilidad Anual", f"{metricas['volatility']:.2%}")
                            st.metric("Ratio de Sharpe", f"{metricas['sharpe_ratio']:.4f}")
                            st.metric("VaR 95%", f"{metricas['var_95']:.4f}")
                        
                        # Gráfico de pesos
                        if hasattr(manager_inst, 'rics'):
                            st.markdown("#### 🥧 Distribución de Pesos")
                            fig_pie = go.Figure(data=[go.Pie(
                                labels=manager_inst.rics,
                                values=weights,
                                textinfo='label+percent',
                                hole=0.4,
                                marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3'])
                            )])
                            fig_pie.update_layout(
                                title="Distribución de Activos Seleccionados Aleatoriamente",
                                template='plotly_white'
                            )
                            st.plotly_chart(fig_pie, use_container_width=True)
                        
                        # Mostrar recomendaciones de rebalanceo
                        st.markdown("#### 💡 Recomendaciones de Rebalanceo")
                        
                        # Calcular diferencias con el portafolio actual
                        activos_actuales = {activo['simbolo']: activo.get('valorizado', 0) for activo in activos_raw}
                        valor_total_actual = sum(activos_actuales.values())
                        
                        if valor_total_actual > 0 and manager_inst.rics is not None:
                            recomendaciones = []
                            for i, simbolo in enumerate(manager_inst.rics):
                                peso_optimizado = weights[i] * 100
                                valor_actual = activos_actuales.get(simbolo, 0)
                                peso_actual = (valor_actual / valor_total_actual) * 100 if valor_total_actual > 0 else 0
                                diferencia = peso_optimizado - peso_actual
                                
                                if abs(diferencia) > 1:  # Solo mostrar diferencias significativas
                                    accion = "Comprar" if diferencia > 0 else "Vender"
                                    recomendaciones.append({
                                        'Activo': simbolo,
                                        'Peso Actual (%)': f"{peso_actual:.1f}%",
                                        'Peso Optimizado (%)': f"{peso_optimizado:.1f}%",
                                        'Diferencia (%)': f"{diferencia:+.1f}%",
                                        'Acción': accion
                                    })
                            
                            if recomendaciones:
                                df_recomendaciones = pd.DataFrame(recomendaciones)
                                st.dataframe(df_recomendaciones, use_container_width=True)
                            else:
                                st.success("✅ El portafolio actual está bien balanceado")
                        else:
                            st.warning("No se pudo calcular las recomendaciones de rebalanceo")
                        
                        progress_bar.progress(100)
                        status_text.text("✅ Proceso completado exitosamente!")
                        
                    else:
                        st.error("❌ No se pudieron cargar los datos para optimización")
                else:
                    st.warning("No se pudieron seleccionar activos válidos del portafolio")
                    
            except Exception as e:
                st.error(f"❌ Error en selección aleatoria: {str(e)}")
                progress_bar.progress(0)
                status_text.text("❌ Error en el proceso")

def mostrar_test_inversor():
    st.title("🧠 Test del Inversor")
    st.markdown("### Evaluación de Perfil de Riesgo y Conocimientos")
    
    # Inicializar session state para el test
    if 'test_completado' not in st.session_state:
        st.session_state.test_completado = False
    if 'respuestas_test' not in st.session_state:
        st.session_state.respuestas_test = {}
    if 'puntaje_total' not in st.session_state:
        st.session_state.puntaje_total = 0
    if 'perfil_riesgo' not in st.session_state:
        st.session_state.perfil_riesgo = ""
    
    # Definir las preguntas del test
    preguntas = {
        'perfil_riesgo': {
            'pregunta': '¿Cómo reaccionaría si su portafolio perdiera 20% de su valor en un mes?',
            'opciones': {
                'conservador': 'Vendería todo inmediatamente para evitar más pérdidas',
                'moderado': 'Me preocuparía pero mantendría la estrategia a largo plazo',
                'agresivo': 'Vería esto como una oportunidad para comprar más'
            },
            'puntajes': {'conservador': 1, 'moderado': 2, 'agresivo': 3}
        },
        'horizonte_temporal': {
            'pregunta': '¿Cuál es su horizonte de inversión principal?',
            'opciones': {
                'corto': 'Menos de 2 años',
                'medio': 'Entre 2 y 5 años',
                'largo': 'Más de 5 años'
            },
            'puntajes': {'corto': 1, 'medio': 2, 'largo': 3}
        },
        'conocimiento_mercado': {
            'pregunta': '¿Qué tan familiarizado está con los mercados financieros?',
            'opciones': {
                'principiante': 'Principiante - Apenas comencé a invertir',
                'intermedio': 'Intermedio - Tengo experiencia básica',
                'avanzado': 'Avanzado - Entiendo bien los mercados'
            },
            'puntajes': {'principiante': 1, 'intermedio': 2, 'avanzado': 3}
        },
        'tolerancia_volatilidad': {
            'pregunta': '¿Qué nivel de volatilidad está dispuesto a aceptar?',
            'opciones': {
                'baja': 'Baja - Prefiero inversiones estables',
                'media': 'Media - Acepto algo de volatilidad',
                'alta': 'Alta - Busco mayores retornos aunque sea más volátil'
            },
            'puntajes': {'baja': 1, 'media': 2, 'alta': 3}
        },
        'objetivo_inversion': {
            'pregunta': '¿Cuál es su principal objetivo de inversión?',
            'opciones': {
                'preservacion': 'Preservación de capital',
                'crecimiento': 'Crecimiento moderado',
                'maximizacion': 'Maximización de retornos'
            },
            'puntajes': {'preservacion': 1, 'crecimiento': 2, 'maximizacion': 3}
        },
        'experiencia_crisis': {
            'pregunta': '¿Cómo se comportó durante la crisis de 2020?',
            'opciones': {
                'vendio': 'Vendí mis inversiones por miedo',
                'mantuve': 'Mantuve mis posiciones',
                'compre': 'Compré más aprovechando los precios bajos'
            },
            'puntajes': {'vendio': 1, 'mantuve': 2, 'compre': 3}
        },
        'conocimiento_productos': {
            'pregunta': '¿Qué productos financieros conoce y ha utilizado?',
            'opciones': {
                'basicos': 'Solo cuentas de ahorro y plazo fijo',
                'intermedios': 'Acciones, bonos y FCIs',
                'avanzados': 'Opciones, futuros, ETFs y productos complejos'
            },
            'puntajes': {'basicos': 1, 'intermedios': 2, 'avanzados': 3}
        },
        'capacidad_analisis': {
            'pregunta': '¿Qué tan cómodo se siente analizando estados financieros?',
            'opciones': {
                'incomodo': 'No me siento cómodo - Prefiero asesoramiento',
                'basico': 'Puedo entender conceptos básicos',
                'avanzado': 'Puedo hacer análisis técnico y fundamental'
            },
            'puntajes': {'incomodo': 1, 'basico': 2, 'avanzado': 3}
        }
    }
    
    # Mostrar el test si no está completado
    if not st.session_state.test_completado:
        st.info("📝 Complete el siguiente test para evaluar su perfil de inversor")
        
        with st.form("test_inversor_form"):
            st.markdown("### 📋 Preguntas del Test")
            
            for key, pregunta in preguntas.items():
                st.markdown(f"**{pregunta['pregunta']}**")
                
                respuesta = st.radio(
                    f"Respuesta para: {key}",
                    options=list(pregunta['opciones'].keys()),
                    format_func=lambda x: pregunta['opciones'][x],
                    key=f"radio_{key}",
                    label_visibility="collapsed"
                )
                
                st.session_state.respuestas_test[key] = respuesta
                st.divider()
            
            if st.form_submit_button("📊 Calcular Resultados", use_container_width=True):
                # Calcular puntaje total
                puntaje_total = 0
                for key, respuesta in st.session_state.respuestas_test.items():
                    puntaje_total += preguntas[key]['puntajes'][respuesta]
                
                st.session_state.puntaje_total = puntaje_total
                
                # Determinar perfil de riesgo
                if puntaje_total <= 12:
                    perfil = "Conservador"
                elif puntaje_total <= 18:
                    perfil = "Moderado"
                else:
                    perfil = "Agresivo"
                
                st.session_state.perfil_riesgo = perfil
                st.session_state.test_completado = True
                st.success("✅ Test completado exitosamente!")
                st.rerun()
    
    # Mostrar resultados si el test está completado
    if st.session_state.test_completado:
        st.success("🎉 ¡Test completado!")
        
        # Mostrar puntaje y perfil
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Puntaje Total", st.session_state.puntaje_total)
        with col2:
            st.metric("Perfil de Riesgo", st.session_state.perfil_riesgo)
        with col3:
            max_puntaje = len(preguntas) * 3
            porcentaje = (st.session_state.puntaje_total / max_puntaje) * 100
            st.metric("Porcentaje", f"{porcentaje:.1f}%")
        
        # Análisis detallado del perfil
        st.markdown("### 📊 Análisis del Perfil")
        
        if st.session_state.perfil_riesgo == "Conservador":
            st.info("""
            **🎯 Perfil Conservador**
            
            **Características:**
            - Prefiere inversiones de bajo riesgo
            - Busca preservación del capital
            - Tolerancia baja a la volatilidad
            - Horizonte de inversión corto a medio
            
            **Recomendaciones:**
            - Portafolio con 70-80% en renta fija
            - 20-30% en acciones de empresas grandes y estables
            - Considerar FCIs de renta fija
            - Evitar productos complejos o de alto riesgo
            """)
            
            # Gráfico de distribución recomendada
            fig_conservador = go.Figure(data=[go.Pie(
                labels=['Renta Fija (70%)', 'Acciones Blue Chips (20%)', 'Efectivo (10%)'],
                values=[70, 20, 10],
                textinfo='label+percent',
                hole=0.4,
                marker=dict(colors=['#28a745', '#17a2b8', '#ffc107'])
            )])
            fig_conservador.update_layout(
                title="Distribución Recomendada - Perfil Conservador",
                height=400
            )
            st.plotly_chart(fig_conservador, use_container_width=True)
            
        elif st.session_state.perfil_riesgo == "Moderado":
            st.info("""
            **🎯 Perfil Moderado**
            
            **Características:**
            - Busca equilibrio entre riesgo y retorno
            - Tolerancia media a la volatilidad
            - Horizonte de inversión medio
            - Conocimiento intermedio de mercados
            
            **Recomendaciones:**
            - Portafolio balanceado 50-50
            - 50% en renta fija y FCIs
            - 40% en acciones diversificadas
            - 10% en efectivo para oportunidades
            """)
            
            # Gráfico de distribución recomendada
            fig_moderado = go.Figure(data=[go.Pie(
                labels=['Renta Fija (50%)', 'Acciones (40%)', 'Efectivo (10%)'],
                values=[50, 40, 10],
                textinfo='label+percent',
                hole=0.4,
                marker=dict(colors=['#28a745', '#17a2b8', '#ffc107'])
            )])
            fig_moderado.update_layout(
                title="Distribución Recomendada - Perfil Moderado",
                height=400
            )
            st.plotly_chart(fig_moderado, use_container_width=True)
            
        else:  # Agresivo
            st.info("""
            **🎯 Perfil Agresivo**
            
            **Características:**
            - Busca maximizar retornos
            - Alta tolerancia a la volatilidad
            - Horizonte de inversión largo
            - Conocimiento avanzado de mercados
            
            **Recomendaciones:**
            - Portafolio con mayor peso en renta variable
            - 70% en acciones diversificadas
            - 20% en renta fija para estabilidad
            - 10% en productos alternativos
            """)
            
            # Gráfico de distribución recomendada
            fig_agresivo = go.Figure(data=[go.Pie(
                labels=['Acciones (70%)', 'Renta Fija (20%)', 'Alternativos (10%)'],
                values=[70, 20, 10],
                textinfo='label+percent',
                hole=0.4,
                marker=dict(colors=['#17a2b8', '#28a745', '#dc3545'])
            )])
            fig_agresivo.update_layout(
                title="Distribución Recomendada - Perfil Agresivo",
                height=400
            )
            st.plotly_chart(fig_agresivo, use_container_width=True)
        
        # Mostrar respuestas detalladas
        st.markdown("### 📋 Detalle de Respuestas")
        
        for key, pregunta in preguntas.items():
            respuesta_seleccionada = st.session_state.respuestas_test[key]
            puntaje_pregunta = pregunta['puntajes'][respuesta_seleccionada]
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{pregunta['pregunta']}**")
                st.markdown(f"*Respuesta: {pregunta['opciones'][respuesta_seleccionada]}*")
            with col2:
                st.metric("Puntaje", puntaje_pregunta)
            st.divider()
        
        # Recomendaciones específicas
        st.markdown("### 💡 Recomendaciones Específicas")
        
        if st.session_state.perfil_riesgo == "Conservador":
            st.markdown("""
            **🎯 Estrategia Recomendada:**
            - **FCIs de Renta Fija**: 40% del portafolio
            - **Bonos del Tesoro**: 30% del portafolio
            - **Acciones Blue Chips**: 20% del portafolio (YPF, GGAL, PAMP)
            - **Efectivo**: 10% para oportunidades
            
            **📈 Objetivo de Retorno:** 8-12% anual
            **⚠️ Riesgo Esperado:** Bajo (volatilidad 5-10%)
            """)
            
        elif st.session_state.perfil_riesgo == "Moderado":
            st.markdown("""
            **🎯 Estrategia Recomendada:**
            - **Acciones Diversificadas**: 40% del portafolio
            - **FCIs Mixtos**: 30% del portafolio
            - **Bonos Corporativos**: 20% del portafolio
            - **Efectivo**: 10% para oportunidades
            
            **📈 Objetivo de Retorno:** 15-20% anual
            **⚠️ Riesgo Esperado:** Medio (volatilidad 10-15%)
            """)
            
        else:  # Agresivo
            st.markdown("""
            **🎯 Estrategia Recomendada:**
            - **Acciones de Crecimiento**: 50% del portafolio
            - **Acciones de Valor**: 20% del portafolio
            - **FCIs de Renta Variable**: 20% del portafolio
            - **Productos Alternativos**: 10% del portafolio
            
            **📈 Objetivo de Retorno:** 25-35% anual
            **⚠️ Riesgo Esperado:** Alto (volatilidad 15-25%)
            """)
        
        # Botón para reiniciar el test
        if st.button("🔄 Realizar Test Nuevamente", use_container_width=True):
            st.session_state.test_completado = False
            st.session_state.respuestas_test = {}
            st.session_state.puntaje_total = 0
            st.session_state.perfil_riesgo = ""
            st.rerun()

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
                ("🏠 Inicio", "📊 Análisis de Portafolio", "🧠 Test del Inversor"),
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
            elif opcion == "🧠 Test del Inversor":
                mostrar_test_inversor()
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
                - Análisis técnico avanzado  
                - Estado de cuenta consolidado  
                """)
    except Exception as e:
        st.error(f"❌ Error en la aplicación: {str(e)}")

if __name__ == "__main__":
    main()
