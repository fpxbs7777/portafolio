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

# --- FUNCIONES PARA GESTIÓN DE CLIENTES Y APERTURA DE CUENTA ---

def crear_usuario_sin_cuenta(token_portador, datos_usuario):
    """
    POST 1. Crear un usuario sin cuenta comitente en la plataforma IOL.
    """
    url = 'https://api.invertironline.com/api/v2/apertura-de-cuenta/registrar'
    headers = obtener_encabezado_autorizacion(token_portador)
    headers['Content-Type'] = 'application/json'
    
    try:
        respuesta = requests.post(url, headers=headers, json=datos_usuario)
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            st.error(f"Error al crear usuario: {respuesta.status_code}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
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

def completar_apertura_cuenta(token_portador, id_cliente):
    """
    POST 8. Genera el número de cuenta comitente.
    """
    url = f'https://api.invertironline.com/api/v2/apertura-de-cuenta/completar-apertura/{id_cliente}'
    headers = obtener_encabezado_autorizacion(token_portador)
    
    try:
        respuesta = requests.post(url, headers=headers)
        if respuesta.status_code == 200:
            return respuesta.json()
        else:
            st.error(f"Error al completar apertura: {respuesta.status_code}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
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
        
        with st.form("alta_cliente"):
            st.write("**Datos Personales Básicos**")
            nombre = st.text_input("Nombre")
            apellido = st.text_input("Apellido")
            dni = st.text_input("DNI")
            fecha_nacimiento = st.date_input("Fecha de Nacimiento")
            sexo = st.selectbox("Sexo", ["Masculino", "Femenino"])
            
            st.write("**Datos Adicionales**")
            actividad_laboral = st.selectbox("Actividad Laboral", [
                "Relacion_de_dependecia", "Monotributista", "Autonomo", "Desempleado", "Jubilado"
            ])
            domicilio_calle = st.text_input("Calle")
            domicilio_numero = st.text_input("Número")
            codigo_postal = st.text_input("Código Postal")
            cuil_cuit = st.text_input("CUIL/CUIT")
            
            if st.form_submit_button("🚀 Crear Cliente"):
                if nombre and apellido and dni:
                    datos_usuario = {
                        "nombre": nombre,
                        "apellido": apellido,
                        "dni": dni,
                        "fechaNacimiento": fecha_nacimiento.strftime("%Y-%m-%dT00:00:00Z"),
                        "sexo": sexo
                    }
                    
                    with st.spinner("Creando cliente..."):
                        resultado = crear_usuario_sin_cuenta(st.session_state.token_acceso, datos_usuario)
                        if resultado and resultado.get('ok'):
                            st.success("✅ Cliente creado exitosamente")
                            st.json(resultado)
                        else:
                            st.error("❌ Error al crear cliente")
                else:
                    st.warning("⚠️ Complete todos los campos obligatorios")
    
    with tab3:
        st.subheader("📊 Estado de Apertura de Cuenta")
        id_cliente = st.number_input("ID del Cliente", min_value=1, step=1)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📸 Cargar Fotos"):
                st.info("Funcionalidad para cargar fotos DNI y selfies")
                # Aquí se implementaría la carga de archivos
        
        with col2:
            if st.button("✅ Completar Apertura"):
                with st.spinner("Completando apertura..."):
                    resultado = completar_apertura_cuenta(st.session_state.token_acceso, id_cliente)
                    if resultado:
                        if resultado.get('numeroCuenta'):
                            st.success(f"✅ Cuenta creada: {resultado['numeroCuenta']}")
                        else:
                            st.info("ℹ️ Proceso de apertura en curso")
                        st.json(resultado)

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
            
            # Calcular estadísticas
            self.mean_returns = self.returns.mean()
            self.cov_matrix = self.returns.cov()
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

# --- Funciones de Visualización ---
def mostrar_resumen_portafolio(portafolio, token_portador):
    st.markdown("### 📊 **INFORME AUTOMÁTICO COMPLETO DEL PORTAFOLIO**")
    st.markdown("---")
    
    activos = portafolio.get('activos', [])
    datos_activos = []
    valor_total = 0
    
    # Procesar activos y calcular valuaciones
    for activo in activos:
        try:
            titulo = activo.get('titulo', {})
            simbolo = titulo.get('simbolo', 'N/A')
            descripcion = titulo.get('descripcion', 'Sin descripción')
            tipo = titulo.get('tipo', 'N/A')
            cantidad = activo.get('cantidad', 0)
            
            # Campos de valuación prioritarios
            campos_valuacion = [
                'valuacionEnMonedaOriginal', 'valuacionActual', 'valorNominalEnMonedaOriginal', 
                'valorNominal', 'valuacionDolar', 'valuacion', 'valorActual', 'montoInvertido',
                'valorMercado', 'valorTotal', 'importe'
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
            
            # Corrección para FCIs
            if valuacion == 0 and cantidad and ("fci" in tipo.lower() or "fondo" in tipo.lower()):
                campos_valor_cuota = [
                    'valorCuota', 'valorCuotaparte', 'valorCuotaParte', 'ultimoValorCuotaParte',
                    'valor_cuota', 'valor_cuotaparte', 'valor_cuotaparte_ultimo', 'valorCuotaParte',
                    'ultimoValorCuota', 'valorCuotaUltimo', 'valorCuotaActual'
                ]
                valor_cuota = 0
                
                for campo in campos_valor_cuota:
                    if campo in activo and activo[campo] is not None:
                        try:
                            valor = float(activo[campo])
                            if valor > 0:
                                valor_cuota = valor
                                break
                        except (ValueError, TypeError):
                            continue
                
                if valor_cuota == 0:
                    for campo in campos_valor_cuota:
                        if campo in titulo and titulo[campo] is not None:
                            try:
                                valor = float(titulo[campo])
                                if valor > 0:
                                    valor_cuota = valor
                                    break
                            except (ValueError, TypeError):
                                continue
                
                if valor_cuota == 0:
                    valor_cuota = obtener_valor_fci_actual(token_portador, simbolo)
                
                if valor_cuota is not None and valor_cuota > 0:
                    try:
                        cantidad_num = float(cantidad)
                        valuacion = cantidad_num * valor_cuota
                    except (ValueError, TypeError):
                        pass
            
            # Corrección para otros activos
            if valuacion == 0 and cantidad:
                campos_precio = [
                    'precioPromedio', 'precioCompra', 'precioActual', 'precio',
                    'precioUnitario', 'ultimoPrecio', 'cotizacion'
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
            
            # Intento final con API
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
    
    if not datos_activos:
        st.warning("⚠️ No se encontraron activos en el portafolio")
        return
    
    # Crear DataFrame y diccionario del portafolio
    df_activos = pd.DataFrame(datos_activos)
    portafolio_dict = {row['Símbolo']: row for row in datos_activos}
    
    # Calcular métricas del portafolio
    try:
        metricas = calcular_metricas_portafolio(portafolio_dict, valor_total, token_portador)
        if metricas is None:
            st.warning("⚠️ No se pudieron calcular las métricas del portafolio")
            metricas = {}
    except Exception as e:
        st.error(f"❌ Error al calcular métricas: {str(e)}")
        metricas = {}
    
    # === SECCIÓN 1: RESUMEN GENERAL ===
    st.markdown("## 📊 **RESUMEN GENERAL DEL PORTAFOLIO**")
    
    # Métricas principales en columnas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 **Valor Total**", f"${valor_total:,.2f}")
    with col2:
        st.metric("📈 **Total de Activos**", len(datos_activos))
    with col3:
        st.metric("🎯 **Símbolos Únicos**", df_activos['Símbolo'].nunique())
    with col4:
        st.metric("🏦 **Tipos de Activos**", df_activos['Tipo'].nunique())
    
    st.markdown("---")
    
    # === SECCIÓN 2: DISTRIBUCIÓN Y COMPOSICIÓN ===
    st.markdown("## 📊 **DISTRIBUCIÓN Y COMPOSICIÓN**")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Gráfico de distribución por tipo
        if 'Tipo' in df_activos.columns and df_activos['Valuación'].sum() > 0:
            tipo_stats = df_activos.groupby('Tipo')['Valuación'].sum().reset_index()
            fig_pie = go.Figure(data=[go.Pie(
                labels=tipo_stats['Tipo'],
                values=tipo_stats['Valuación'],
                textinfo='label+percent',
                hole=0.4,
                marker=dict(colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
            )])
            fig_pie.update_layout(
                title="Distribución por Tipo de Activo",
                height=400,
                showlegend=True
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Tabla de distribución
        st.markdown("#### 📋 **Distribución por Tipo**")
        tipo_dist = df_activos.groupby('Tipo').agg({
            'Valuación': ['sum', 'count']
        }).round(2)
        tipo_dist.columns = ['Valor Total', 'Cantidad']
        tipo_dist['Porcentaje'] = (tipo_dist['Valor Total'] / valor_total * 100).round(2)
        tipo_dist = tipo_dist.sort_values('Valor Total', ascending=False)
        
        for tipo, row in tipo_dist.iterrows():
            st.markdown(f"**{tipo}**")
            st.markdown(f"- Valor: ${row['Valor Total']:,.2f}")
            st.markdown(f"- Cantidad: {row['Cantidad']}")
            st.markdown(f"- Peso: {row['Porcentaje']:.1f}%")
            st.markdown("---")
    
    st.markdown("---")
    
    # === SECCIÓN 3: ANÁLISIS DE RIESGO ===
    st.markdown("## ⚖️ **ANÁLISIS DE RIESGO**")
    
    if metricas and isinstance(metricas, dict):
        col1, col2, col3 = st.columns(3)
        
        # Concentración
        concentracion = metricas.get('concentracion', 0)
        concentracion_pct = concentracion * 100
        with col1:
            st.metric("🎯 **Concentración**", 
                     f"{concentracion_pct:.1f}%",
                     help="Índice de Herfindahl normalizado: 0%=muy diversificado, 100%=muy concentrado")
        
        # Volatilidad
        volatilidad = metricas.get('std_dev_activo', 0)
        volatilidad_pct = volatilidad * 100
        with col2:
            st.metric("📊 **Volatilidad Anual**", 
                     f"{volatilidad_pct:.1f}%",
                     help="Riesgo medido como desviación estándar de retornos anuales")
        
        # Nivel de concentración
        if concentracion < 0.3:
            concentracion_status = "🟢 Baja"
        elif concentracion < 0.6:
            concentracion_status = "🟡 Media"
        else:
            concentracion_status = "🔴 Alta"
        
        with col3:
            st.metric("⚠️ **Nivel de Riesgo**", concentracion_status)
        
        # Probabilidades
        st.markdown("#### 🎯 **Probabilidades de Rendimiento**")
        cols = st.columns(4)
        probs = metricas.get('probabilidades', {})
        
        with cols[0]:
            st.metric("📈 **Ganancia**", f"{probs.get('ganancia', 0)*100:.1f}%")
        with cols[1]:
            st.metric("📉 **Pérdida**", f"{probs.get('perdida', 0)*100:.1f}%")
        with cols[2]:
            st.metric("🚀 **Ganancia >10%**", f"{probs.get('ganancia_mayor_10', 0)*100:.1f}%")
        with cols[3]:
            st.metric("⚠️ **Pérdida >10%**", f"{probs.get('perdida_mayor_10', 0)*100:.1f}%")
        
        # Recomendaciones de riesgo
        st.markdown("#### 💡 **Recomendaciones de Riesgo**")
        if concentracion > 0.5:
            st.warning("""
            **⚠️ Portafolio Altamente Concentrado**  
            Considere diversificar sus inversiones para reducir el riesgo.
            """)
        elif concentracion > 0.25:
            st.info("""
            **ℹ️ Concentración Moderada**  
            Podría mejorar su diversificación para optimizar el riesgo.
            """)
        else:
            st.success("""
            **✅ Buena Diversificación**  
            Su portafolio está bien diversificado.
            """)
        
        # Ratio riesgo-retorno
        ratio_riesgo_retorno = metricas.get('retorno_esperado_anual', 0) / metricas.get('riesgo_anual', 1) if metricas.get('riesgo_anual', 0) > 0 else 0
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
    
    st.markdown("---")
    
    # === SECCIÓN 4: PROYECCIONES Y RENDIMIENTO ===
    st.markdown("## 📈 **PROYECCIONES Y RENDIMIENTO**")
    
    if metricas and isinstance(metricas, dict):
        col1, col2, col3 = st.columns(3)
        
        # Retorno esperado
        retorno_esperado = metricas.get('retorno_esperado_anual', 0)
        retorno_anual_pct = retorno_esperado * 100
        with col1:
            st.metric("📊 **Retorno Esperado Anual**", 
                     f"{retorno_anual_pct:+.1f}%",
                     help="Retorno anual esperado basado en datos históricos")
        
        # Escenarios
        pl_max = metricas.get('pl_esperado_max', 0)
        pl_min = metricas.get('pl_esperado_min', 0)
        optimista_pct = (pl_max / valor_total) * 100 if valor_total > 0 else 0
        pesimista_pct = (pl_min / valor_total) * 100 if valor_total > 0 else 0
        
        with col2:
            st.metric("🚀 **Escenario Optimista (95%)**", 
                     f"{optimista_pct:+.1f}%",
                     help="Mejor escenario con 95% de confianza")
        with col3:
            st.metric("⚠️ **Escenario Pesimista (5%)**", 
                     f"{pesimista_pct:+.1f}%",
                     help="Peor escenario con 5% de confianza")
        
        # Proyecciones monetarias
        st.markdown("#### 💰 **Proyecciones Monetarias**")
        cols = st.columns(3)
        
        with cols[0]:
            st.metric("📊 **Proyección Esperada**", f"${valor_total * (1 + retorno_esperado):,.2f}")
        with cols[1]:
            st.metric("🚀 **Proyección Optimista**", f"${valor_total * (1 + optimista_pct/100):,.2f}")
        with cols[2]:
            st.metric("⚠️ **Proyección Pesimista**", f"${valor_total * (1 + pesimista_pct/100):,.2f}")
    
    st.markdown("---")
    
    # === SECCIÓN 5: ANÁLISIS HISTÓRICO ===
    st.markdown("## 📊 **ANÁLISIS HISTÓRICO Y EVOLUCIÓN**")
    
    # Configuración del horizonte
    horizonte_inversion = st.selectbox(
        "**Horizonte de Análisis:**",
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
    
    dias_analisis = horizonte_inversion[1]
    st.info("ℹ️ **Nota**: Los datos se obtienen en frecuencia diaria desde la API de IOL")
    
    with st.spinner(f"🔄 Analizando evolución histórica del portafolio para {dias_analisis} días..."):
        try:
            # Obtener fechas para el histórico
            fecha_hasta = datetime.now().strftime('%Y-%m-%d')
            fecha_desde = (datetime.now() - timedelta(days=dias_analisis)).strftime('%Y-%m-%d')
            
            # Preparar activos para histórico
            activos_para_historico = []
            for activo in datos_activos:
                simbolo = activo['Símbolo']
                if simbolo != 'N/A':
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
                # Obtener series históricas
                series_historicas = {}
                activos_exitosos = []
                
                for activo_info in activos_para_historico:
                    simbolo = activo_info['simbolo']
                    mercado = activo_info['mercado']
                    peso = activo_info['peso']
                    
                    if peso > 0:
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
                        else:
                            st.warning(f"⚠️ No se pudieron obtener datos para {simbolo}")
                
                if len(activos_exitosos) > 0:
                    # Crear DataFrame del portafolio
                    df_portfolio = pd.DataFrame()
                    
                    # Encontrar fechas comunes
                    fechas_comunes = None
                    for activo_info in activos_exitosos:
                        serie = activo_info['serie']
                        if fechas_comunes is None:
                            fechas_comunes = set(serie.index)
                        else:
                            fechas_comunes = fechas_comunes.intersection(set(serie.index))
                    
                    if not fechas_comunes:
                        st.warning("⚠️ No hay fechas comunes entre las series históricas")
                    else:
                        # Convertir a lista ordenada
                        fechas_comunes = sorted(list(fechas_comunes))
                        df_portfolio.index = fechas_comunes
                        
                        for activo_info in activos_exitosos:
                            simbolo = activo_info['simbolo']
                            peso = activo_info['peso']
                            serie = activo_info['serie']
                            
                            # Encontrar valuación del activo
                            valuacion_activo = 0
                            for activo_original in datos_activos:
                                if activo_original['Símbolo'] == simbolo:
                                    valuacion_activo = float(activo_original['Valuación'])
                                    break
                            
                            # Filtrar serie para fechas comunes
                            serie_filtrada = serie.loc[fechas_comunes]
                            
                            # Agregar serie ponderada
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
                        
                        # Calcular valor total del portafolio
                        df_portfolio['Portfolio_Total'] = df_portfolio.sum(axis=1)
                        df_portfolio = df_portfolio.dropna()
                        
                        if len(df_portfolio) > 0:
                            # Histograma del valor total
                            valores_portfolio = df_portfolio['Portfolio_Total'].values
                            
                            fig_hist = go.Figure(data=[go.Histogram(
                                x=valores_portfolio,
                                nbinsx=30,
                                name="Valor Total del Portafolio",
                                marker_color='#0d6efd',
                                opacity=0.7
                            )])
                            
                            # Agregar líneas de métricas
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
                                title="📊 Distribución del Valor Total del Portafolio",
                                xaxis_title="Valor del Portafolio ($)",
                                yaxis_title="Frecuencia",
                                height=500,
                                showlegend=False,
                                template='plotly_white'
                            )
                            
                            st.plotly_chart(fig_hist, use_container_width=True)
                            
                            # Estadísticas del histograma
                            st.markdown("#### 📊 **Estadísticas del Histograma**")
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("📊 **Valor Promedio**", f"${media_valor:,.2f}")
                            with col2:
                                st.metric("📈 **Valor Mediano**", f"${mediana_valor:,.2f}")
                            with col3:
                                st.metric("📉 **Valor Mínimo (P5)**", f"${percentil_5:,.2f}")
                            with col4:
                                st.metric("🚀 **Valor Máximo (P95)**", f"${percentil_95:,.2f}")
                            
                            # Gráfico de evolución temporal
                            fig_evolucion = go.Figure()
                            fig_evolucion.add_trace(go.Scatter(
                                x=df_portfolio.index,
                                y=df_portfolio['Portfolio_Total'],
                                mode='lines',
                                name='Valor del Portafolio',
                                line=dict(color='#0d6efd', width=2)
                            ))
                            
                            fig_evolucion.update_layout(
                                title="📈 Evolución Temporal del Portafolio",
                                xaxis_title="Fecha",
                                yaxis_title="Valor del Portafolio ($)",
                                height=400,
                                template='plotly_white'
                            )
                            
                            st.plotly_chart(fig_evolucion, use_container_width=True)
                            
                            # Contribución de activos
                            if len(activos_exitosos) > 1:
                                fig_contribucion = go.Figure()
                                for activo_info in activos_exitosos:
                                    simbolo = activo_info['simbolo']
                                    if simbolo in df_portfolio.columns:
                                        fig_contribucion.add_trace(go.Scatter(
                                            x=df_portfolio.index,
                                            y=df_portfolio[simbolo],
                                            mode='lines',
                                            name=simbolo,
                                            stackgroup='one'
                                        ))
                                
                                fig_contribucion.update_layout(
                                    title="🥧 Contribución de Activos al Valor Total",
                                    xaxis_title="Fecha",
                                    yaxis_title="Valor ($)",
                                    height=400,
                                    template='plotly_white'
                                )
                                
                                st.plotly_chart(fig_contribucion, use_container_width=True)
                            
                            # Análisis de retornos
                            if len(valores_portfolio) > 1:
                                retornos_portfolio = np.diff(valores_portfolio) / valores_portfolio[:-1]
                                
                                # Estadísticas de retornos
                                retorno_medio_diario = np.mean(retornos_portfolio)
                                volatilidad_diaria = np.std(retornos_portfolio)
                                var_95 = np.percentile(retornos_portfolio, 5)
                                var_99 = np.percentile(retornos_portfolio, 1)
                                
                                # Test de normalidad
                                if len(retornos_portfolio) > 30:
                                    skewness = stats.skew(retornos_portfolio)
                                    kurtosis = stats.kurtosis(retornos_portfolio)
                                    jb_stat, jb_pvalue = stats.jarque_bera(retornos_portfolio)
                                    es_normal = jb_pvalue > 0.05
                                else:
                                    skewness = kurtosis = jb_stat = 0
                                    es_normal = None
                                
                                st.markdown("#### 📊 **Análisis de Retornos**")
                                
                                # Histograma de retornos
                                fig_retornos = go.Figure(data=[go.Histogram(
                                    x=retornos_portfolio,
                                    nbinsx=30,
                                    name="Retornos del Portafolio",
                                    marker_color='#28a745',
                                    opacity=0.7
                                )])
                                
                                fig_retornos.update_layout(
                                    title="📊 Histograma de Retornos del Portafolio",
                                    xaxis_title="Retorno Diario",
                                    yaxis_title="Frecuencia",
                                    height=400,
                                    template='plotly_white'
                                )
                                
                                st.plotly_chart(fig_retornos, use_container_width=True)
                                
                                # Estadísticas de retornos
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("#### 📈 **Estadísticas de Retornos**")
                                    st.metric("📊 **Retorno Medio Diario**", f"{retorno_medio_diario:.4f}")
                                    st.metric("📉 **Volatilidad Diaria**", f"{volatilidad_diaria:.4f}")
                                    st.metric("⚠️ **VaR 95%**", f"{var_95:.4f}")
                                    st.metric("🚨 **VaR 99%**", f"{var_99:.4f}")
                                
                                with col2:
                                    st.markdown("#### 📊 **Métricas Anualizadas**")
                                    retorno_anual = retorno_medio_diario * 252
                                    volatilidad_anual = volatilidad_diaria * np.sqrt(252)
                                    ratio_sharpe = retorno_anual / volatilidad_anual if volatilidad_anual > 0 else 0
                                    
                                    st.metric("📈 **Retorno Anual**", f"{retorno_anual:.2%}")
                                    st.metric("📊 **Volatilidad Anual**", f"{volatilidad_anual:.2%}")
                                    st.metric("⚖️ **Ratio de Sharpe**", f"{ratio_sharpe:.4f}")
                                
                                # Análisis de la distribución
                                if es_normal is not None:
                                    st.markdown("#### 📋 **Análisis de la Distribución**")
                                    
                                    if es_normal:
                                        st.success("✅ Los retornos siguen una distribución normal (p > 0.05)")
                                    else:
                                        st.error("❌ Los retornos no siguen una distribución normal (p ≤ 0.05)")
                                    
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("📊 **Skewness**", f"{skewness:.4f}")
                                    with col2:
                                        st.metric("📈 **Kurtosis**", f"{kurtosis:.4f}")
                                    with col3:
                                        st.metric("📊 **JB Statistic**", f"{jb_stat:.4f}")
                                    
                                    if skewness > 0.5:
                                        st.info("📈 Distribución con sesgo positivo (cola derecha)")
                                    elif skewness < -0.5:
                                        st.info("📉 Distribución con sesgo negativo (cola izquierda)")
                                    else:
                                        st.info("📊 Distribución aproximadamente simétrica")
                                    
                                    if kurtosis > 3:
                                        st.info("📊 Distribución leptocúrtica (colas pesadas)")
                                    elif kurtosis < 3:
                                        st.info("📊 Distribución platicúrtica (colas ligeras)")
                                    else:
                                        st.info("📊 Distribución normal (colas estándar)")
                
        except Exception as e:
            st.error(f"❌ Error al analizar el histórico: {str(e)}")
    
    st.markdown("---")
    
    # === SECCIÓN 6: DETALLE DE ACTIVOS ===
    st.markdown("## 📋 **DETALLE COMPLETO DE ACTIVOS**")
    
    # Preparar DataFrame para mostrar
    df_display = df_activos.copy()
    df_display['Valuación'] = df_display['Valuación'].apply(
        lambda x: f"${x:,.2f}" if x > 0 else "N/A"
    )
    df_display['Peso (%)'] = (df_activos['Valuación'] / valor_total * 100).round(2)
    df_display = df_display.sort_values('Peso (%)', ascending=False)
    
    # Mostrar tabla
    st.dataframe(df_display, use_container_width=True, height=400)
    
    # Resumen de tipos de activos
    st.markdown("#### 📊 **Resumen por Tipo de Activo**")
    tipo_resumen = df_activos.groupby('Tipo').agg({
        'Valuación': ['sum', 'count', 'mean']
    }).round(2)
    tipo_resumen.columns = ['Valor Total', 'Cantidad', 'Valor Promedio']
    tipo_resumen['Porcentaje'] = (tipo_resumen['Valor Total'] / valor_total * 100).round(2)
    tipo_resumen = tipo_resumen.sort_values('Valor Total', ascending=False)
    
    st.dataframe(tipo_resumen, use_container_width=True)
    
    st.markdown("---")
    
    # === SECCIÓN 7: RECOMENDACIONES FINALES ===
    st.markdown("## 💡 **RECOMENDACIONES Y CONCLUSIONES**")
    
    # Análisis general del portafolio
    if metricas and isinstance(metricas, dict):
        retorno_esperado = metricas.get('retorno_esperado_anual', 0)
        concentracion = metricas.get('concentracion', 0)
        volatilidad = metricas.get('std_dev_activo', 0)
        
        # Evaluación general
        st.markdown("#### 📊 **Evaluación General del Portafolio**")
        
        if retorno_esperado > 0.15:  # >15% anual
            st.success("🚀 **Excelente Potencial de Crecimiento** - Su portafolio muestra un retorno esperado muy alto")
        elif retorno_esperado > 0.08:  # >8% anual
            st.success("✅ **Buen Potencial de Crecimiento** - Su portafolio tiene un retorno esperado favorable")
        elif retorno_esperado > 0:  # >0% anual
            st.info("📈 **Potencial de Crecimiento Moderado** - Su portafolio tiene un retorno esperado positivo")
        else:
            st.warning("⚠️ **Retorno Esperado Negativo** - Se espera un retorno negativo en el horizonte seleccionado")
        
        # Recomendaciones específicas
        st.markdown("#### 🎯 **Recomendaciones Específicas**")
        
        if concentracion > 0.6:
            st.warning("""
            **🔴 ALTA CONCENTRACIÓN DETECTADA**
            - **Riesgo**: Su portafolio está muy concentrado en pocos activos
            - **Acción**: Considere diversificar en más instrumentos y sectores
            - **Beneficio**: Reducirá significativamente el riesgo del portafolio
            """)
        elif concentracion > 0.3:
            st.info("""
            **🟡 CONCENTRACIÓN MODERADA**
            - **Riesgo**: Su portafolio tiene una concentración moderada
            - **Acción**: Podría mejorar la diversificación para optimizar el riesgo
            - **Beneficio**: Mejorará el balance riesgo-retorno
            """)
        else:
            st.success("""
            **🟢 BUENA DIVERSIFICACIÓN**
            - **Riesgo**: Su portafolio está bien diversificado
            - **Acción**: Mantenga esta estrategia de diversificación
            - **Beneficio**: Riesgo controlado y mejor estabilidad
            """)
        
        # Recomendaciones de optimización
        st.markdown("#### 🚀 **Recomendaciones de Optimización**")
        
        if volatilidad > 0.25:  # >25% anual
            st.warning("""
            **⚠️ ALTA VOLATILIDAD DETECTADA**
            - **Riesgo**: Su portafolio es muy volátil
            - **Acción**: Considere agregar activos de menor volatilidad (renta fija, FCIs)
            - **Beneficio**: Mayor estabilidad y menor riesgo
            """)
        
        if retorno_esperado < 0.05:  # <5% anual
            st.info("""
            **📊 RETORNO ESPERADO BAJO**
            - **Riesgo**: Retorno esperado por debajo del promedio del mercado
            - **Acción**: Revise la composición y considere activos más dinámicos
            - **Beneficio**: Potencial de mejor rendimiento
            """)
        
        # Recomendaciones de monitoreo
        st.markdown("#### 📊 **Recomendaciones de Monitoreo**")
        
        st.info("""
        **📈 MONITOREO RECOMENDADO**
        - **Frecuencia**: Revise su portafolio al menos mensualmente
        - **Métricas clave**: Concentración, volatilidad y retorno esperado
        - **Rebalanceo**: Considere rebalancear trimestralmente
        - **Diversificación**: Mantenga al menos 5-10 activos diferentes
        """)
    
    # Mensaje final
    st.markdown("---")
    st.success("""
    **🎉 ¡Análisis Completado!**
    
    Este informe proporciona una visión completa y profesional de su portafolio de inversión. 
    Utilice esta información para tomar decisiones informadas y optimizar su estrategia de inversión.
    
    **📞 Para consultas adicionales, contacte a su asesor financiero.**
    """)

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
    
    tab1, tab2, tab3 = st.tabs(["💰 Cotización MEP", "🏦 Tasas de Caución", "📈 Gráficos con Fechas"])
    
    with tab1:
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
                        precio_mep = cotizacion_mep.get('precio', 'N/A')
                        st.metric("Precio MEP", f"${precio_mep}" if precio_mep != 'N/A' else 'N/A')
                    else:
                        st.error("❌ No se pudo obtener la cotización MEP")
    
    with tab2:
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
    
    with tab3:
        st.subheader("📈 Gráficos con Fechas Reales")
        
        # Configuración de paneles
        paneles = {
            "Acciones": ["Panel%20General", "Burcap", "Todas"],
            "Bonos": ["Panel%20General", "Burcap", "Todas"],
            "Opciones": ["Panel%20General", "Burcap", "Todas"],
            "Monedas": ["Panel%20General", "Burcap", "Todas"],
            "Cauciones": ["Panel%20General", "Burcap", "Todas"],
            "CHPD": ["Panel%20General", "Burcap", "Todas"],
            "Futuros": ["Panel%20General", "Burcap", "Todas"],
            "ADRs": ["Panel%20General", "Burcap", "Todas"]
        }
        
        col1, col2 = st.columns(2)
        with col1:
            instrumento = st.selectbox("Instrumento", list(paneles.keys()))
        with col2:
            panel = st.selectbox("Panel", paneles[instrumento])
        
        pais = st.selectbox("País", ["Argentina", "Estados_Unidos"])
        
        if st.button("🔍 Buscar Cotizaciones"):
            with st.spinner("Obteniendo cotizaciones..."):
                try:
                    url = f'https://api.invertironline.com/api/v2/Cotizaciones/{instrumento}/{panel}/{pais}'
                    headers = obtener_encabezado_autorizacion(token_acceso)
                    
                    params = {
                        'panelCotizacion.instrumento': instrumento.lower(),
                        'panelCotizacion.panel': panel,
                        'panelCotizacion.pais': pais.lower()
                    }
                    
                    respuesta = requests.get(url, headers=headers, params=params)
                    
                    if respuesta.status_code == 200:
                        datos = respuesta.json()
                        titulos = datos.get('titulos', [])
                        
                        if titulos:
                            df = pd.DataFrame(titulos)
                            st.success(f"✅ Se encontraron {len(df)} títulos")
                            st.dataframe(df, use_container_width=True)
                            
                            # Gráfico de variación
                            if 'variacionPorcentual' in df.columns:
                                fig = go.Figure()
                                fig.add_trace(go.Bar(
                                    x=df['simbolo'],
                                    y=df['variacionPorcentual'],
                                    marker_color=['green' if x > 0 else 'red' for x in df['variacionPorcentual']]
                                ))
                                fig.update_layout(
                                    title=f"Variación Porcentual - {instrumento}",
                                    xaxis_title="Símbolo",
                                    yaxis_title="Variación (%)",
                                    template='plotly_white'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Gráfico de precios con fechas si están disponibles
                            if 'fecha' in df.columns and 'ultimoPrecio' in df.columns:
                                # Convertir fechas
                                df['fecha'] = pd.to_datetime(df['fecha'])
                                df = df.sort_values('fecha')
                                
                                fig_precios = go.Figure()
                                fig_precios.add_trace(go.Scatter(
                                    x=df['fecha'],
                                    y=df['ultimoPrecio'],
                                    mode='lines+markers',
                                    name='Precio',
                                    line=dict(color='#1f77b4', width=2)
                                ))
                                
                                fig_precios.update_layout(
                                    title=f"Evolución de Precios - {instrumento}",
                                    xaxis_title="Fecha",
                                    yaxis_title="Precio",
                                    template='plotly_white',
                                    height=400
                                )
                                
                                # Configurar eje X para mostrar fechas reales
                                fig_precios.update_xaxes(
                                    tickformat='%d/%m/%Y',
                                    tickangle=45,
                                    tickmode='auto',
                                    nticks=10
                                )
                                
                                st.plotly_chart(fig_precios, use_container_width=True)
                                
                                # Información de fechas
                                st.info(f"📅 Período de datos: {df['fecha'].min().strftime('%d/%m/%Y')} - {df['fecha'].max().strftime('%d/%m/%Y')}")
                        else:
                            st.warning("No se encontraron cotizaciones")
                    else:
                        st.error(f"Error al obtener cotizaciones: {respuesta.status_code}")
                        
                except Exception as e:
                    st.error(f"Error de conexión: {str(e)}")

def mostrar_optimizacion_portafolio(token_acceso, id_cliente):
    st.markdown("### 🔄 Optimización de Portafolio")
    
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
                    # Computar optimización
                    use_target = target_return if estrategia == 'markowitz' else None
                    portfolio_result = manager_inst.compute_portfolio(strategy=estrategia, target_return=use_target)
                    
                    if portfolio_result:
                        st.success("✅ Optimización completada")
                        
                        # Mostrar resultados extendidos
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 📊 Pesos Optimizados")
                            if portfolio_result.dataframe_allocation is not None:
                                weights_df = portfolio_result.dataframe_allocation.copy()
                                weights_df['Peso (%)'] = weights_df['weights'] * 100
                                weights_df = weights_df.sort_values('Peso (%)', ascending=False)
                                st.dataframe(weights_df[['rics', 'Peso (%)']], use_container_width=True)
                        
                        with col2:
                            st.markdown("#### 📈 Métricas del Portafolio")
                            metricas = portfolio_result.get_metrics_dict()
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("Retorno Anual", f"{metricas['Annual Return']:.2%}")
                                st.metric("Volatilidad Anual", f"{metricas['Annual Volatility']:.2%}")
                                st.metric("Ratio de Sharpe", f"{metricas['Sharpe Ratio']:.4f}")
                                st.metric("VaR 95%", f"{metricas['VaR 95%']:.4f}")
                            with col_b:
                                st.metric("Skewness", f"{metricas['Skewness']:.4f}")
                                st.metric("Kurtosis", f"{metricas['Kurtosis']:.4f}")
                                st.metric("JB Statistic", f"{metricas['JB Statistic']:.4f}")
                                normalidad = "✅ Normal" if metricas['Is Normal'] else "❌ No Normal"
                                st.metric("Normalidad", normalidad)
                        
                        # Gráfico de distribución de retornos
                        if portfolio_result.returns is not None:
                            st.markdown("#### 📊 Distribución de Retornos del Portafolio Optimizado")
                            fig = portfolio_result.plot_histogram_streamlit()
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Gráfico de evolución temporal del portafolio
                        if hasattr(portfolio_result, 'dataframe_allocation') and portfolio_result.dataframe_allocation is not None:
                            st.markdown("#### 📈 Evolución Temporal del Portafolio")
                            # Crear fechas reales para el eje X
                            fechas = pd.date_range(start=st.session_state.fecha_desde, end=st.session_state.fecha_hasta, periods=len(portfolio_result.returns))
                            df_evolucion = pd.DataFrame({
                                'Fecha': fechas,
                                'Retorno': portfolio_result.returns
                            })
                            
                            fig_evolucion = go.Figure()
                            fig_evolucion.add_trace(go.Scatter(
                                x=df_evolucion['Fecha'],
                                y=df_evolucion['Retorno'],
                                mode='lines',
                                name='Retorno del Portafolio',
                                line=dict(color='#1f77b4', width=2)
                            ))
                            fig_evolucion.update_layout(
                                title="Evolución de Retornos del Portafolio Optimizado",
                                xaxis_title="Fecha",
                                yaxis_title="Retorno (%)",
                                template='plotly_white',
                                height=400
                            )
                            fig_evolucion.update_xaxes(
                                tickformat='%d/%m/%Y',
                                tickangle=45
                            )
                            st.plotly_chart(fig_evolucion, use_container_width=True)
                        
                        # Gráfico de pesos
                        if portfolio_result.weights is not None:
                            st.markdown("#### 🥧 Distribución de Pesos")
                            if portfolio_result.dataframe_allocation is not None:
                                fig_pie = go.Figure(data=[go.Pie(
                                    labels=portfolio_result.dataframe_allocation['rics'],
                                    values=portfolio_result.weights,
                                    textinfo='label+percent',
                                    hole=0.4,
                                    marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3'])
                                )])
                            else:
                                # Crear gráfico con datos básicos si no hay dataframe_allocation
                                fig_pie = go.Figure(data=[go.Pie(
                                    labels=[f'Activo {i+1}' for i in range(len(portfolio_result.weights))],
                                    values=portfolio_result.weights,
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
    
    # Opciones de visualización
    tipo_visualizacion = st.radio(
        "Tipo de visualización:",
        ["📈 TradingView (Interactivo)", "📊 Gráficos con Datos IOL"],
        horizontal=True
    )
    
    simbolo_seleccionado = st.selectbox(
        "Seleccione un activo para análisis técnico:",
        options=simbolos
    )
    
    if simbolo_seleccionado:
        if tipo_visualizacion == "📈 TradingView (Interactivo)":
            st.info(f"Mostrando gráfico TradingView para: {simbolo_seleccionado}")
            
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
        
        else:
            # Gráficos con datos de IOL y fechas reales
            st.info(f"Mostrando gráficos con datos IOL para: {simbolo_seleccionado}")
            
            # Obtener datos históricos
            fecha_desde = st.session_state.fecha_desde
            fecha_hasta = st.session_state.fecha_hasta
            
            # Buscar el mercado del activo seleccionado
            mercado_activo = None
            for activo in activos:
                titulo = activo.get('titulo', {})
                if titulo.get('simbolo') == simbolo_seleccionado:
                    mercado_activo = titulo.get('mercado', 'BCBA')
                    break
            
            try:
                datos_historicos = obtener_serie_historica_iol(token_acceso, mercado_activo, simbolo_seleccionado, fecha_desde, fecha_hasta)
                
                if datos_historicos and isinstance(datos_historicos, list) and len(datos_historicos) > 0:
                    df = pd.DataFrame(datos_historicos)
                    
                    # Buscar columna de precio
                    col_precio = None
                    for col in ['ultimoPrecio', 'ultimo_precio', 'precio', 'close', 'cierre']:
                        if col in df.columns:
                            col_precio = col
                            break
                    
                    if col_precio and 'fecha' in df.columns:
                        # Convertir fechas
                        df['fecha'] = pd.to_datetime(df['fecha'])
                        df = df.sort_values('fecha')
                        
                        # Gráfico de precios con fechas reales
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df['fecha'],
                            y=df[col_precio],
                            mode='lines',
                            name=f'Precio {simbolo_seleccionado}',
                            line=dict(color='#1f77b4', width=2)
                        ))
                        
                        fig.update_layout(
                            title=f"Evolución de Precios - {simbolo_seleccionado}",
                            xaxis_title="Fecha",
                            yaxis_title="Precio",
                            template='plotly_white',
                            height=400
                        )
                        
                        # Configurar eje X para mostrar fechas reales
                        fig.update_xaxes(
                            tickformat='%d/%m/%Y',
                            tickangle=45,
                            tickmode='auto',
                            nticks=10
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Gráfico de volumen si está disponible
                        if 'volumen' in df.columns:
                            fig_vol = go.Figure()
                            fig_vol.add_trace(go.Bar(
                                x=df['fecha'],
                                y=df['volumen'],
                                name=f'Volumen {simbolo_seleccionado}',
                                marker_color='#ff7f0e'
                            ))
                            
                            fig_vol.update_layout(
                                title=f"Volumen de Operaciones - {simbolo_seleccionado}",
                                xaxis_title="Fecha",
                                yaxis_title="Volumen",
                                template='plotly_white',
                                height=300
                            )
                            
                            fig_vol.update_xaxes(
                                tickformat='%d/%m/%Y',
                                tickangle=45
                            )
                            
                            st.plotly_chart(fig_vol, use_container_width=True)
                        
                        # Métricas básicas
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Precio Actual", f"${df[col_precio].iloc[-1]:.2f}")
                        with col2:
                            st.metric("Precio Máximo", f"${df[col_precio].max():.2f}")
                        with col3:
                            st.metric("Precio Mínimo", f"${df[col_precio].min():.2f}")
                        
                        # Información de fechas
                        st.info(f"📅 Período analizado: {df['fecha'].min().strftime('%d/%m/%Y')} - {df['fecha'].max().strftime('%d/%m/%Y')}")
                        
                    else:
                        st.warning(f"No se encontraron datos de precios para {simbolo_seleccionado}")
                else:
                    st.warning(f"No se pudieron obtener datos históricos para {simbolo_seleccionado}")
                    
            except Exception as e:
                st.error(f"Error al obtener datos para {simbolo_seleccionado}: {str(e)}")

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
    
    # Tab único unificado para el análisis completo del portafolio
    st.markdown("## 📊 **ANÁLISIS COMPLETO Y UNIFICADO DEL PORTAFOLIO**")
    st.markdown("---")
    
    # Obtener datos del portafolio
    portafolio = obtener_portafolio(token_acceso, id_cliente)
    if portafolio:
        mostrar_resumen_portafolio(portafolio, token_acceso)
    else:
        st.warning("No se pudo obtener el portafolio del cliente")
    
    # Información adicional del estado de cuenta
    st.markdown("---")
    st.markdown("## 💰 **ESTADO DE CUENTA COMPLEMENTARIO**")
    estado_cuenta = obtener_estado_cuenta(token_acceso, id_cliente)
    if estado_cuenta:
        mostrar_estado_cuenta(estado_cuenta)
    else:
        st.warning("No se pudo obtener el estado de cuenta")
    
    # Enlaces a herramientas adicionales
    st.markdown("---")
    st.markdown("## 🛠️ **HERRAMIENTAS ADICIONALES DISPONIBLES**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📊 Análisis Técnico**
        - Gráficos interactivos TradingView
        - Indicadores técnicos avanzados
        - Análisis de patrones de precios
        """)
        if st.button("🔍 Ir a Análisis Técnico", key="btn_tecnico"):
            st.session_state.mostrar_tecnico = True
    
    with col2:
        st.markdown("""
        **💱 Cotizaciones de Mercado**
        - Cotizaciones MEP en tiempo real
        - Tasas de caución actualizadas
        - Datos de mercado históricos
        """)
        if st.button("🔍 Ir a Cotizaciones", key="btn_cotizaciones"):
            st.session_state.mostrar_cotizaciones = True
    
    with col3:
        st.markdown("""
        **🧮 Optimización Avanzada**
        - Optimización Markowitz
        - Frontera eficiente
        - Rebalanceo automático
        """)
        if st.button("🔍 Ir a Optimización", key="btn_optimizacion"):
            st.session_state.mostrar_optimizacion = True
    
    # Mostrar herramientas adicionales si se solicitan
    if st.session_state.get('mostrar_tecnico', False):
        st.markdown("---")
        st.markdown("## 📊 **ANÁLISIS TÉCNICO**")
        mostrar_analisis_tecnico(token_acceso, id_cliente)
        if st.button("❌ Cerrar Análisis Técnico"):
            st.session_state.mostrar_tecnico = False
            st.rerun()
    
    if st.session_state.get('mostrar_cotizaciones', False):
        st.markdown("---")
        st.markdown("## 💱 **COTIZACIONES DE MERCADO**")
        mostrar_cotizaciones_mercado(token_acceso)
        if st.button("❌ Cerrar Cotizaciones"):
            st.session_state.mostrar_cotizaciones = False
            st.rerun()
    
    if st.session_state.get('mostrar_optimizacion', False):
        st.markdown("---")
        st.markdown("## 🧮 **OPTIMIZACIÓN AVANZADA**")
        mostrar_optimizacion_portafolio(token_acceso, id_cliente)
        if st.button("❌ Cerrar Optimización"):
            st.session_state.mostrar_optimizacion = False
            st.rerun()

def seleccionar_activos_aleatorios_por_valor(activos, saldo_objetivo, incluir_saldo_disponible, saldo_disponible, cantidad_activos):
    activos_shuffled = activos.copy()
    random.shuffle(activos_shuffled)
    seleccion = []
    total = 0
    for activo in activos_shuffled:
        valor = activo['valorizado']
        if total + valor <= saldo_objetivo and len(seleccion) < cantidad_activos:
            seleccion.append(activo)
            total += valor
        if len(seleccion) >= cantidad_activos or total >= saldo_objetivo:
            break
    return seleccion, total

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
    
    # Variables para herramientas adicionales
    if 'mostrar_tecnico' not in st.session_state:
        st.session_state.mostrar_tecnico = False
    if 'mostrar_cotizaciones' not in st.session_state:
        st.session_state.mostrar_cotizaciones = False
    if 'mostrar_optimizacion' not in st.session_state:
        st.session_state.mostrar_optimizacion = False
    
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
                ("🏠 Inicio", "👥 Gestión de Clientes", "📊 Análisis de Portafolio", "💰 Tasas de Caución", "👨\u200d💼 Panel del Asesor"),
                index=0,
            )

            # Mostrar la página seleccionada
            if opcion == "🏠 Inicio":
                st.info("👆 Seleccione una opción del menú para comenzar")
            elif opcion == "👥 Gestión de Clientes":
                if 'token_acceso' in st.session_state and st.session_state.token_acceso:
                    mostrar_gestion_clientes()
                else:
                    st.warning("Por favor inicie sesión para gestionar clientes")
            elif opcion == "📊 Análisis de Portafolio":
                if st.session_state.cliente_seleccionado:
                    mostrar_analisis_portafolio()
                else:
                    st.info("👆 Seleccione un cliente en la barra lateral para comenzar")
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

if __name__ == "__main__":
    main()
